# -*- coding: utf-8 -*-
r"""new_project.py — 从零生成 Civ6 ModBuddy 工程骨架（`.civ6proj` + 目录 + 版本控制骨架）

## 为什么需要它

本 skill 原先**只有"改已有工程"的能力**：`modinfo_build.py` 的输入必须是**已存在的**
`.civ6proj`（它负责 `.civ6proj` → `.modinfo` 的派生），而"工程本身从哪来"没有工具，
只能照 `project-setup.md` 手抄骨架 —— 易漏 CDATA 块、易漏 Content 条目、易抄错 GUID。

本工具把 `project-setup.md` 里已写明的骨架**参数化生成**，并在生成后立刻调
`modinfo_build.py` 产出 `.modinfo` 自检，做到"一条命令出一个可构建的工程"。

## 生成物（★ 两层布局，与 ModBuddy 一致）

```
<目标目录>/                      ← 工作区根（.civ6sln 在这一层）
├── <Name>.civ6sln             解决方案文件
└── <Name>/                     ← 工程根（.civ6proj 在这一层）
    ├── <Name>.civ6proj        骨架（5 个 CDATA 块 + ItemGroup 清单）
    ├── .gitignore             「默认忽略一切、只放行源文件」白名单
    ├── .gitattributes         换行分层铁律（资产类 LF、代码/配置类 CRLF）
    ├── Data/<Name>_Data.sql   gameplay 数据库占位（UpdateDatabase）
    ├── Data/Config_<Name>.sql 前端/配置占位（FrontEnd UpdateDatabase）
    ├── Text/Text_<Name>.sql   游戏内文本占位（UpdateText）
    └── workspace/             ★ 除 mod 成品以外的一切都放这里
        ├── _tools/build.py    构建与校验入口（check/modinfo/stage/verify/deploy）
        ├── gen/               派生产物（.modinfo、Mods 暂存副本）
        ├── src/               设计文档、资料等源材料
        └── tmp/               一次性中间产物

```

> ★ **为什么是两层**：ModBuddy 的固定处理方式 —— 解决方案放工作区根，工程放**同名子目录**。
> 只建一层（把 .civ6proj 直接放目标目录）就没地方放 .civ6sln；多建几层（外层再套同名目录）
> 则会让 `<源工程根>\<ModName>` 这条路径解析不到工程。**恰好两层，内层与 mod 同名。**

> ★ **落盘边界**：工程根只放 mod 成品（Data/Text 里的 SQL·XML + .civ6proj 等）；构建产物
> （.modinfo、Cooked/、Build/）不进工程根；其余一切（脚本、日志、文档、中间产物）都在
> `workspace/`，它已被 .gitignore 忽略。日常迭代走 `build.py stage` + `verify`，产物全部
> 落在 `workspace/gen/`，不碰游戏目录。

> ⚠ **只建本次确实要写文件的目录**。空目录会随整树拷贝进 Mods 副本，也会在 ModBuddy
> 解决方案树里挂一排空节点。`ArtDefs/` `XLPs/` `Textures/` 用 `--with-art` 预建，
> `Scripts/` `UI/` `ImportFiles/` 用 `--extra-dirs` 预建，或者等你真正放文件时自建。
> **AssetEditor 自动生成的目录**（`Animations/`、`Assets/`、`Behaviors/`、`Geometries/`、
> `Materials/`、`Lights/`、`ParticleEffects/` 等）同样不预建。
>
> `<UpdateArt>` 只在 `--with-art` 时写入：它引用的 `<ModName>.dep` 由 cooker 依
> `*.Art.xml` 产出，无美术工程写它必然悬空。

## 工程目录位置（硬性）

**工程目录不得位于游戏 Mods 加载目录之内**（本机由 `_paths.py` 解析，见 SKILL.md 的 P2）。
游戏会递归扫描 Mods 全树，工程里的构建产物 `<ModName>.modinfo` 会被当成第二个 mod 收录，
同一 GUID 出现两条记录，「额外内容」界面显示两份同名 mod。命中即退出码 2，不写任何文件。

## GUID 安全（对应 gotchas「modinfo GUID 唯一真源」）

- 默认生成**全新** uuid4。
- `--guid` 显式指定时，会**扫描本机既有工程**（ModBuddy 工程根 + Mods 加载目录）里是否已存在
  该 GUID；**命中即拒绝**（除非 `--force`），避免复制示例 GUID 造成工坊条目互相覆盖。

## 用法

    python new_project.py "<源工程根>\MyMod" --name MyMod
    python new_project.py <目录> --name MyMod --title-en "My Mod" --title-zh "我的模组"
    python new_project.py <目录> --name MyMod --guid <已有GUID>      # 会先做全网查重
    python new_project.py <目录> --name MyMod --deploy               # 建完直接部署到 Mods

`<目录>` 是**工作区根**：工程会建在 `<目录>\<Name>\`，解决方案放 `<目录>\<Name>.civ6sln`。
生成后 `<目录>\<Name>` 即「工程根」，后续所有工具（modinfo_build / check_* / cook_*）都指向它。

退出码：0 成功 / 1 失败 / 2 已存在同名工程或目标位于 Mods 树内（需换目录）
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AUTHOR_DEFAULT = "千与千寻瀑"          # 项目固定约定（AGENTS.md「modinfo 作者署名」）
GS_GUID = "4873eb62-8ccc-4574-b784-dda455e74e68"        # Expansion: Gathering Storm

# 目录骨架：只建"本次确实要写文件"的目录 —— 空目录会随整树拷贝进 Mods 副本，
# 也会让 ModBuddy 解决方案树里挂一排空节点。美术类目录（ArtDefs/XLPs/Textures）
# 由 --with-art 显式开启，Scripts/UI/ImportFiles 等你真正放文件时自建。
DIRS = ["Data", "Text"]
ART_DIRS = ["ArtDefs", "XLPs", "Textures", "Scripts", "UI", "ImportFiles"]

GITIGNORE = """# 默认忽略一切，只放行可管理的源文件
*
!*/
!.gitignore
!.gitattributes
!*.civ6proj
!*.civ6sln
!*.xlp
!*.artdef
!*.sql
!*.xml
!*.lua
!*.md

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

# 解决方案文件模板。ModBuddy 的固定布局：.civ6sln 在工作区根，工程在同名子目录。
# ModBuddy 的工程类型 GUID 恒为此值（全部官方与社区 .civ6sln 一致），ProjectGuid 为本工程独有。
CIV6SLN = """
Microsoft Visual Studio Solution File, Format Version 12.00
# ModBuddy Solution File, Format Version 12.00
VisualStudioVersion = 12.0.21005.1
MinimumVisualStudioVersion = 10.0.40219.1
Project("{{5DAE07AF-E217-45C1-8DE7-FF99D6011E8A}}") = "{name}", "{name}\\{name}.civ6proj", "{{{pguid}}}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Default|Civ6 = Default|Civ6
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{{{pguid}}}.Default|Civ6.ActiveCfg = Default|Civ6
		{{{pguid}}}.Default|Civ6.Build.0 = Default|Civ6
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
EndGlobal
"""

# workspace/ 骨架：除 mod 成品以外的一切都落在这里（.gitignore 已忽略整个目录）
WS_DIRS = ["_tools", "gen", "src", "tmp"]

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


def civ6proj(name, guid, pguid, title, teaser, desc, author, has_config, has_text, has_art, dirs):
    """按 project-setup.md 的 Skeleton + 各 CDATA 最小样例生成 .civ6proj。

    `has_art` 为假时不写 <UpdateArt>：该动作引用 <ModName>.dep，而 .dep 只在工程
    存在 *.Art.xml（cooker 的输入）时才会产出，无美术工程写它就是一条必然悬空的引用。
    `dirs` 是本次实际创建并写入文件的目录清单，<Folder Include> 只声明这些。
    """
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
    if has_art:
        # 写真实 <Name>.dep —— 不要写 '(Mod Art Dependency File)' 占位符：
        # 那是 ModBuddy 内部 token，若原样进 .modinfo 会导致 UpdateArt 静默失效（美术全空）。
        ingame += ['  <UpdateArt id="Art"><File>%s.dep</File></UpdateArt>' % name]

    front = []
    if has_config:
        front += ['  <UpdateDatabase id="Config"><File>%s</File></UpdateDatabase>' % cfg_file]
    if has_text:
        front += ['  <UpdateText id="Text_Config"><File>%s</File></UpdateText>' % text_file]
    if has_art:
        front += ['  <UpdateArt id="Art"><File>%s.dep</File></UpdateArt>' % name]

    content = ['    <Content Include="%s"><SubType>Content</SubType></Content>' % data_file]
    if has_config:
        content.append('    <Content Include="%s"><SubType>Content</SubType></Content>' % cfg_file)
    if has_text:
        content.append('    <Content Include="%s"><SubType>Content</SubType></Content>' % text_file)
    folders = "\n".join('    <Folder Include="%s\\" />' % d for d in dirs)

    return """<?xml version="1.0" encoding="utf-8"?>
<Project ToolsVersion="12.0" DefaultTargets="Default" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup>
    <Configuration Condition=" '$(Configuration)' == '' ">Default</Configuration>
    <Name>{title_loc}</Name>
    <Guid>{guid}</Guid>
    <ProjectGuid>{pguid}</ProjectGuid>
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
""".format(title_loc=title_loc, guid=guid, pguid=pguid, teaser_loc=teaser_loc,
           desc_loc=desc_loc, author=author, name=name, gs=GS_GUID,
           title=title, teaser=teaser, desc=desc,
           folders=folders, content="\n".join(content),
           front="\n".join(front), ingame="\n".join(ingame))


def main() -> int:
    ap = argparse.ArgumentParser(description="从零生成 Civ6 ModBuddy 工程骨架")
    ap.add_argument("target", help="工作区根；工程建在其下的同名子目录（ModBuddy 两层布局）")
    ap.add_argument("--name", required=True, help="工程/Mod 名（ASCII，与 .civ6proj 同名）")
    ap.add_argument("--guid", default=None, help="显式指定 mod GUID（默认生成 uuid4；会先查重）")
    ap.add_argument("--title-en", default=None, help="mod 标题（英文）")
    ap.add_argument("--title-zh", default=None, help="mod 标题（中文）")
    ap.add_argument("--teaser", default="", help="副标题/Teaser")
    ap.add_argument("--description", default="", help="描述")
    ap.add_argument("--author", default=AUTHOR_DEFAULT, help="署名（默认 %s）" % AUTHOR_DEFAULT)
    ap.add_argument("--no-config", action="store_true", help="不生成 Config_<Name>.sql / 前端动作")
    ap.add_argument("--no-text", action="store_true", help="不生成 Text/<Name>.sql / UpdateText")
    ap.add_argument("--with-art", action="store_true",
                    help="同时预建 ArtDefs/ XLPs/ Textures/（工程将带美术素材时才需要）")
    ap.add_argument("--extra-dirs", default="",
                    help="额外预建目录（逗号分隔，如 Scripts,UI,ImportFiles）")
    ap.add_argument("--no-modinfo", action="store_true", help="不调 modinfo_build.py 派生 .modinfo")
    ap.add_argument("--deploy", action="store_true", help="派生 modinfo 后同时部署到 Mods")
    ap.add_argument("--force", action="store_true", help="目标已存在/GUID 命中时仍继续")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", args.name):
        print("FAIL --name 必须是 ASCII 字母开头的标识符（不用空格/中文/连字符）")
        return 1
    root = os.path.abspath(args.target)          # 工作区根
    target = os.path.join(root, args.name)       # 工程根（ModBuddy 两层布局的内层）
    # ★ 工程落在 Mods 加载树内会让构建产物被游戏当成第二个 mod（同一 GUID 两条记录）。
    #   判定必须在创建任何文件之前；工作区根与工程根都要判，两者都可能在 Mods 树里。
    _paths.assert_source_tree(root, "工作区根")
    _paths.assert_source_tree(target)
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

    has_cfg = not args.no_config
    has_text = not args.no_text
    # 目录清单 = 本次确实要写文件的目录；其余目录等真正放文件时自建。
    # 空目录既会随整树拷贝进 Mods 副本，也会在 ModBuddy 解决方案树里挂一排空节点。
    dirs = [d for d in DIRS if d != "Text" or has_text]
    if args.with_art:
        dirs += [d for d in ART_DIRS if d in ("ArtDefs", "XLPs", "Textures")]
    for extra in (x.strip() for x in args.extra_dirs.split(",")):
        if extra and extra not in dirs:
            dirs.append(extra)
    has_art = args.with_art or any(d in dirs for d in ("ArtDefs", "XLPs", "Textures"))

    for d in dirs:
        os.makedirs(os.path.join(target, d), exist_ok=True)
    # workspace/ 骨架：除 mod 成品以外的一切都落这里（.gitignore 已忽略整个目录）。
    # 预建四个子目录，避免每个新工程都靠手搓 —— 手搓时最容易多套一层同名目录。
    for d in WS_DIRS:
        os.makedirs(os.path.join(target, "workspace", d), exist_ok=True)

    pguid = str(uuid.uuid4())
    w(proj, civ6proj(args.name, guid, pguid, display, args.teaser, args.description,
                     args.author, has_cfg, has_text, has_art, dirs), "crlf")
    # .civ6sln 放工作区根（.civ6proj 的上一层），与 ModBuddy 约定一致
    w(os.path.join(root, args.name + ".civ6sln"),
      CIV6SLN.format(name=args.name, pguid=pguid), "crlf")
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

    # workspace/_tools/build.py：构建与校验入口。模板与本工程无关（全部路径从脚本自身
    # 位置推导），直接照搬即可，免得每个新工程各写一份、彼此分叉。
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "workspace_build.py")
    if os.path.isfile(tpl):
        w(os.path.join(target, "workspace", "_tools", "build.py"),
          open(tpl, encoding="utf-8").read(), "lf")
    else:
        print("WARN 缺少模板 %s —— 未生成 workspace/_tools/build.py" % tpl)

    print("已生成工程：%s" % target)
    print("   解决方案   %s" % os.path.join(root, args.name + ".civ6sln"))
    print("   .civ6proj  %s" % os.path.basename(proj))
    print("   mod GUID   %s" % guid)
    print("   workspace  %s" % ", ".join("workspace/" + d for d in WS_DIRS) + "（含 _tools/build.py）")
    print("   目录       %s" % ", ".join(dirs))

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
        print("   （.modinfo 是构建产物，不进工程根；要留一份写进 workspace/gen/）")

    print("\n下一步（在工程根 %s 下操作）：" % target)
    print("   1) 写 Data/Text 内容 → python workspace/_tools/build.py check")
    print("   2) 迭代：build.py stage + verify（产物落 workspace/gen/，不碰游戏目录）")
    print("   3) 进游戏：build.py deploy")
    print("   4) 美术：civ6-asset-forge（图标/立绘）；3D 引用：civ6-art-reference")
    print("   5) 发布：release.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
