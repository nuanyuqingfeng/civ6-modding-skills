# -*- coding: utf-8 -*-
r"""new_project.py — 从零生成 Civ6 ModBuddy 工程骨架（`.civ6proj` + 目录 + 版本控制骨架）

## 为什么需要它

本 skill 原先**只有"改已有工程"的能力**：`modinfo_build.py` 的输入必须是**已存在的**
`.civ6proj`（它负责 `.civ6proj` → `.modinfo` 的派生），而"工程本身从哪来"没有工具，
只能照 `project-setup.md` 手抄骨架 —— 易漏 CDATA 块、易漏 Content 条目、易抄错 GUID。

本工具把 `project-setup.md` 里已写明的骨架**参数化生成**，并在生成后立刻调
`modinfo_build.py` 产出 `.modinfo` 自检，做到"一条命令出一个可构建的工程"。

## 生成物

```
<目标目录>/
├── <Name>.civ6proj        骨架（5 个 CDATA 块 + ItemGroup 清单）
├── <Name>.modinfo         由 modinfo_build.py 从 civ6proj 派生（--no-modinfo 可跳过）
├── .gitignore             「默认忽略一切、只放行源文件」白名单
├── .gitattributes         换行分层铁律（资产类 LF、代码/配置类 CRLF）
├── Data/<Name>_Data.sql   gameplay 数据库占位（UpdateDatabase）
├── Data/Config_<Name>.sql 前端/配置占位（FrontEnd UpdateDatabase）
├── Text/Text_<Name>.sql   游戏内文本占位（UpdateText）
├── Scripts/ UI/ ArtDefs/ XLPs/ Textures/ ImportFiles/
```

> ⚠ **AssetEditor 自动生成的目录**（`Animations/`、`Assets/`、`Behaviors/`、`Geometries/`、
> `Materials/`、`Lights/`、`ParticleEffects/` 等）**不预建** —— 它们由 AssetEditor 在你首次
> cook 时创建；预建空目录只会污染仓库。

## GUID 安全（对应 gotchas「modinfo GUID 唯一真源」）

- 默认生成**全新** uuid4。
- `--guid` 显式指定时，会**扫描本机既有工程**（ModBuddy 工程根 + Mods 加载目录）里是否已存在
  该 GUID；**命中即拒绝**（除非 `--force`），避免复制示例 GUID 造成工坊条目互相覆盖。

## 用法

    python new_project.py "D:\documents\Firaxis ModBuddy\Civilization VI\MyMod" --name MyMod
    python new_project.py <目录> --name MyMod --title-en "My Mod" --title-zh "我的模组"
    python new_project.py <目录> --name MyMod --guid <已有GUID>      # 会先做全网查重

退出码：0 成功 / 1 失败 / 2 已存在同名工程（需 --force）
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _paths  # noqa: E402
except Exception:                                   # pragma: no cover
    _paths = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AUTHOR_DEFAULT = "千与千寻瀑"          # 项目固定约定（AGENTS.md「modinfo 作者署名」）
GS_GUID = "4873eb62-8ccc-4574-b784-dda455e74e68"        # Expansion: Gathering Storm

# 目录骨架：只含"人或脚本会写东西"的目录；cook 产物目录交给 AssetEditor 自建
DIRS = ["Data", "Text", "Scripts", "UI", "ArtDefs", "XLPs", "Textures", "ImportFiles"]

GITIGNORE = """# 默认忽略一切，只放行可管理的源文件
*
!*/
!.gitignore
!*.civ6proj
!*.civ6sln
!*.xlp
!*.artdef
!*.sql
!*.xml
!*.lua

# 专用的 agent/素材工作区（中间产物、源素材，统一不入库）
workspace/

# 可再生的贴图（由脚本生成）
*.tex
*.dds

# 安全网：常见中间/临时产物显式忽略（防止被白名单放行）
*.bak_*
*.log
*.tmp

# 例外：音频 bank 产物要入库
!Platforms/Windows/Audio/*.bnk
!Platforms/Windows/Audio/*.txt
!Platforms/Windows/Audio/*.ini
"""

GITATTRIBUTES = """# ★ 换行分层铁律（唯一真源：gotchas.md §68）：资产类 LF、代码/配置类 CRLF
# 本机 core.autocrlf 常见为 true，checkout 会把仓库里的 LF 写成工作区 CRLF；
# 不一刀切、不写反方向，否则会制造新的「源 ↔ Mods 副本」伪不一致。
*.artdef  text eol=lf
*.xlp     text eol=lf
*.txt     text eol=lf
*.lua     text eol=crlf
*.sql     text eol=crlf
*.xml     text eol=crlf
*.modinfo text eol=crlf
*.civ6proj text eol=crlf

# 美术二进制资产：禁止任何换行/编码转换
*.dds -text -diff -merge binary
*.tex -text -diff -merge binary
*.ast -text -diff -merge binary
*.mtl -text -diff -merge binary
*.geo -text -diff -merge binary
*.blp -text -diff -merge binary
"""


def w(path, text, eol):
    """写文本；eol ∈ {'crlf','lf'}。显式控制，避免平台默认把 CRLF 写成 LF。"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = text.replace("\r\n", "\n")
    if eol == "crlf":
        data = data.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data)


def scan_guid(guid):
    """在本机既有工程里查该 GUID 是否已被占用 → [(路径, 命中的文件)]。"""
    hits = []
    roots = []
    if _paths:
        for key in ("modbuddy", "mods"):
            p = _paths.get(key, must_exist=False)
            if p:
                roots.append(p)
    pat = re.compile(re.escape(guid), re.I)
    exts = (".civ6proj", ".modinfo")
    for root in roots:
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in ("workspace", ".git", "__pycache__", "Cooked")]
            for f in fn:
                if not f.lower().endswith(exts):
                    continue
                p = os.path.join(dp, f)
                try:
                    if pat.search(open(p, encoding="utf-8-sig", errors="replace").read()):
                        hits.append((root, p))
                except OSError:
                    continue
    return hits


def civ6proj(name, guid, title, teaser, desc, author, has_config, has_text):
    """按 project-setup.md 的 Skeleton + 各 CDATA 最小样例生成 .civ6proj。"""
    title_loc = "LOC_%s_MOD_TITLE" % name.upper()
    teaser_loc = "LOC_%s_MOD_TEASER" % name.upper()
    desc_loc = "LOC_%s_MOD_DESCRIPTION" % name.upper()
    data_file = "Data/%s_Data.sql" % name
    cfg_file = "Data/Config_%s.sql" % name
    text_file = "Text/Text_%s.sql" % name

    ingame = [
        '  <UpdateDatabase id="%s_Data">' % name,
        '    <Properties><LoadOrder>200</LoadOrder></Properties>',
        '    <File>%s</File>' % data_file,
        '  </UpdateDatabase>',
    ]
    if has_text:
        ingame += [
            '  <UpdateText id="%s_Text">' % name,
            '    <Properties><LoadOrder>30000</LoadOrder></Properties>',
            '    <File>%s</File>' % text_file,
            '  </UpdateText>',
        ]
    ingame += ['  <UpdateArt id="Art"><File>(Mod Art Dependency File)</File></UpdateArt>']

    front = []
    if has_config:
        front += ['  <UpdateDatabase id="Config"><File>%s</File></UpdateDatabase>' % cfg_file]
    if has_text:
        front += ['  <UpdateText id="Text_Config"><File>%s</File></UpdateText>' % text_file]
    front += ['  <UpdateArt id="Art"><File>(Mod Art Dependency File)</File></UpdateArt>']

    content = ['    <Content Include="%s"><SubType>Content</SubType></Content>' % data_file]
    if has_config:
        content.append('    <Content Include="%s"><SubType>Content</SubType></Content>' % cfg_file)
    if has_text:
        content.append('    <Content Include="%s"><SubType>Content</SubType></Content>' % text_file)
    folders = "\n".join('    <Folder Include="%s\\" />' % d for d in DIRS)

    return """<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="12.0" DefaultTargets="Default" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup>
    <Configuration Condition=" '$(Configuration)' == '' ">Default</Configuration>
    <Name>{title_loc}</Name>
    <Guid>{{{guid}}}</Guid>
    <ProjectGuid>{{{pguid}}}</ProjectGuid>
    <ModVersion>1</ModVersion>
    <Teaser>{teaser_loc}</Teaser>
    <Description>{desc_loc}</Description>
    <Authors>{author}</Authors>
    <AffectsSavedGames>true</AffectsSavedGames>
    <SupportsSinglePlayer>true</SupportsSinglePlayer>
    <SupportsMultiplayer>true</SupportsMultiplayer>
    <SupportsHotSeat>true</SupportsHotSeat>
    <CompatibleVersions>1.2,2.0</CompatibleVersions>
    <AssemblyName>{name}</AssemblyName>
    <RootNamespace>{name}</RootNamespace>

    <AssociationData><![CDATA[<Associations>
  <Dependency type="Dlc" title="Expansion: Gathering Storm"
              id="{gs}" />
  <Reference type="Dlc" title="Expansion: Gathering Storm"
              id="{gs}" />
</Associations>]]></AssociationData>

    <LocalizedTextData><![CDATA[<LocalizedText>
    <Text id="{title_loc}">
        <en_US>{title}</en_US>
        <zh_Hans_CN>{title}</zh_Hans_CN>
    </Text>
    <Text id="{teaser_loc}"><en_US>{teaser}</en_US><zh_Hans_CN>{teaser}</zh_Hans_CN></Text>
    <Text id="{desc_loc}"><en_US>{desc}</en_US><zh_Hans_CN>{desc}</zh_Hans_CN></Text>
</LocalizedText>]]></LocalizedTextData>

    <ActionCriteriaData><![CDATA[<ActionCriteria>
  <Criteria id="Expansion2"><GameCoreInUse>Expansion2</GameCoreInUse></Criteria>
</ActionCriteria>]]></ActionCriteriaData>

    <FrontEndActionData><![CDATA[<FrontEndActions>
{front}
</FrontEndActions>]]></FrontEndActionData>

    <InGameActionData><![CDATA[<InGameActions>
{ingame}
</InGameActions>]]></InGameActionData>
  </PropertyGroup>
  <PropertyGroup Condition=" '$(Configuration)' == 'Default' ">
    <OutputPath>.</OutputPath>
  </PropertyGroup>
  <ItemGroup>
{folders}
  </ItemGroup>
  <ItemGroup>
{content}
  </ItemGroup>
  <Import Project="$(MSBuildLocalExtensionPath)Civ6.targets" />
</Project>
""".format(title_loc=title_loc, guid=guid, pguid=str(uuid.uuid4()), teaser_loc=teaser_loc,
           desc_loc=desc_loc, author=author, name=name, gs=GS_GUID,
           title=title, teaser=teaser, desc=desc,
           folders=folders, content="\n".join(content),
           front="\n".join(front), ingame="\n".join(ingame))


def main() -> int:
    ap = argparse.ArgumentParser(description="从零生成 Civ6 ModBuddy 工程骨架")
    ap.add_argument("target", help="工程目录（其下直接放 <Name>.civ6proj）")
    ap.add_argument("--name", required=True, help="工程/Mod 名（ASCII，与 .civ6proj 同名）")
    ap.add_argument("--guid", default=None, help="显式指定 mod GUID（默认生成 uuid4；会先查重）")
    ap.add_argument("--title-en", default=None, help="mod 标题（英文）")
    ap.add_argument("--title-zh", default=None, help="mod 标题（中文）")
    ap.add_argument("--teaser", default="", help="副标题/Teaser")
    ap.add_argument("--description", default="", help="描述")
    ap.add_argument("--author", default=AUTHOR_DEFAULT, help="署名（默认 %s）" % AUTHOR_DEFAULT)
    ap.add_argument("--no-config", action="store_true", help="不生成 Config_<Name>.sql / 前端动作")
    ap.add_argument("--no-text", action="store_true", help="不生成 Text/<Name>.sql / UpdateText")
    ap.add_argument("--no-modinfo", action="store_true", help="不调 modinfo_build.py 派生 .modinfo")
    ap.add_argument("--deploy", action="store_true", help="派生 modinfo 后同时部署到 Mods")
    ap.add_argument("--force", action="store_true", help="目标已存在/GUID 命中时仍继续")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", args.name):
        print("FAIL --name 必须是 ASCII 字母开头的标识符（不用空格/中文/连字符）")
        return 1
    target = os.path.abspath(args.target)
    proj = os.path.join(target, args.name + ".civ6proj")
    if os.path.exists(proj) and not args.force:
        print("FAIL 目标已有 %s —— 换目录或加 --force" % proj)
        return 2

    guid = args.guid
    if guid:
        if not re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", guid):
            print("FAIL --guid 不是合法 GUID（8-4-4-4-12）")
            return 1
        hits = scan_guid(guid)
        if hits:
            print("FAIL ★ GUID 已被本机既有工程占用（禁止一 GUID 多用：工坊条目会互相覆盖）：")
            for root, p in hits[:8]:
                print("   %s" % p)
            if not args.force:
                print("   如确认是同一 mod 的迁移，加 --force；否则让工具生成新 GUID。")
                return 1
            print("   （--force 已指定，继续）")
    else:
        guid = str(uuid.uuid4())

    title_en = args.title_en or args.name
    title_zh = args.title_zh or title_en
    display = title_zh if title_zh == title_en else "%s / %s" % (title_en, title_zh)

    for d in DIRS:
        os.makedirs(os.path.join(target, d), exist_ok=True)

    has_cfg = not args.no_config
    has_text = not args.no_text

    w(proj, civ6proj(args.name, guid, display, args.teaser, args.description,
                     args.author, has_cfg, has_text), "crlf")
    w(os.path.join(target, ".gitignore"), GITIGNORE, "lf")
    w(os.path.join(target, ".gitattributes"), GITATTRIBUTES, "lf")
    w(os.path.join(target, "Data", "%s_Data.sql" % args.name),
      "-- %s —— gameplay 数据库（UpdateDatabase, LoadOrder 200）\n"
      "-- 新内容按 database.md / xml-templates.md 写；改动后跑 rgn_validate 校验引用闭合。\n"
      % args.name, "crlf")
    if has_cfg:
        w(os.path.join(target, "Data", "Config_%s.sql" % args.name),
          "-- Config_%s.sql —— 前端/配置库（Config 表：PlayerItems 等，FrontEnd UpdateDatabase）\n"
          % args.name, "crlf")
    if has_text:
        w(os.path.join(target, "Text", "Text_%s.sql" % args.name),
          "-- Text_%s.sql —— 游戏内文本（必须经 UpdateText 加载；modinfo 的 LocalizedText 只管\n"
          "-- 「选择 mod」界面，见 gotchas「游戏内文本必须走 UpdateText」）\n"
          "INSERT OR REPLACE INTO LocalizedText (Language, Tag, Text) VALUES\n"
          "  ('en_US', 'LOC_%s_MOD_NAME', '%s'),\n"
          "  ('zh_Hans_CN', 'LOC_%s_MOD_NAME', '%s');\n"
          % (args.name, args.name.upper(), title_en, args.name.upper(), title_zh), "crlf")

    print("已生成工程：%s" % target)
    print("   .civ6proj  %s" % os.path.basename(proj))
    print("   mod GUID   {%s}" % guid)
    print("   目录       %s" % ", ".join(DIRS))

    if not args.no_modinfo:
        import subprocess
        mb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modinfo_build.py")
        cmd = [sys.executable, mb, proj] + (["--deploy"] if args.deploy else [])
        print("\n派生 .modinfo：%s" % " ".join(cmd))
        rc = subprocess.call(cmd)
        if rc != 0:
            print("FAIL modinfo_build.py 返回 %d —— 工程骨架已生成，请按上方输出修复后重跑该命令" % rc)
            return 1
    else:
        print("\n跳过 modinfo 派生（--no-modinfo）。手动跑：python %s %s" % ("modinfo_build.py", proj))

    print("\n下一步：")
    print("   1) 写 Data/Text 内容 → python tools/modinfo_build.py <civ6proj> --deploy")
    print("   2) 校验：scripts/ 下 check_proj_content / check_sql_exec / rgn_validate")
    print("   3) 美术：civ6-asset-forge（图标/立绘）；3D 引用：civ6-art-reference")
    print("   4) 发布：release.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
