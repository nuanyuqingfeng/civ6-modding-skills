# -*- coding: utf-8 -*-
"""从 .civ6proj 派生 .modinfo（等价 ModBuddy 的构建动作），并可选部署到游戏 Mods 目录。

为什么需要它：ModBuddy（VS 扩展）不便在无 GUI 环境调用，而 `.modinfo` 完全可以由
`.civ6proj` 机械派生 —— 本项目所有新 mod 都走这条路，无需每次手写 modinfo。

用法：
    python modinfo_build.py <X.civ6proj>                 # 只生成到 <proj目录>/Build/X.modinfo
    python modinfo_build.py <X.civ6proj> --deploy        # cook 美术产物 + 复制 Content + 写 modinfo
    python modinfo_build.py <X.civ6proj> --deploy --mods-root <目录>
    python modinfo_build.py <X.civ6proj> --deploy --no-cook   # 跳过 cook（没有 Art.xml 的工程）

与美术产物（BLP / ArtDef / .dep）的顺序关系：
    `--deploy` 在拷贝 Content 之前会先调 `tools/cook_assets.py` 重放 ModBuddy 的
    ArtDef 与 XLP 分区 —— 否则 Mods 副本里的 BLP 与 `.dep` 停留在上一次构建，
    游戏读到的是旧包。cook 失败（产物缺失、退出码无法解释）时 `--deploy` 立即返回 1，
    不做部分部署。cook 收尾会把源工程 `ArtDefs/*.artdef` 覆盖进副本以保住完好的
    引用链，故 `sync_artdefs` 放在自检最后一步、且对内容相同的文件不再写盘。

产出与自检：
    · modinfo 结构（对齐 ModBuddy 产物）：Properties / Dependencies / ActionCriteria /
      FrontEndActions / InGameActions / (LocalizedText) / Files；UTF-8 BOM + CRLF
    · 动作片段按 XML 解析重新序列化——兼容 ModBuddy 默认的单行 CDATA 与逐行 CDATA
      （旧实现逐行过滤会把单行 CDATA 整段跳过，导致 InGameActions 全空）
    · 生成后做 XML 良构解析 + FrontEnd/InGameActions 内全部 <File> 引用存在性检查（悬空即 exit 1）
    · 部署末尾把源工程 ArtDefs/*.artdef 强制同步进 Mods 副本（见 sync_artdefs 的说明）
    · Content Include 是拷贝清单（ModBuddy 只拷 Content 条目 —— 只写在 InGameActions 里
      而漏进 Content 的文件不会被部署，是踩过的坑）；去重在分隔符规范化之后，
      反斜杠/斜杠两种写法不会产生重复 <File> 项

退出码：0 成功 / 1 失败
"""
from __future__ import annotations

import argparse
import filecmp
import glob
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NS = {"msb": "http://schemas.microsoft.com/developer/msbuild/2003"}

# ModBuddy 在 .civ6proj 的 <UpdateArt> 里写的字面占位符（见 Civ6.Tasks.dll）。
# 它只在 .civ6proj 里合法：ModBuddy 构建期会把它替换成真实 <ModName>.dep。
# 本工具等价实现该替换 —— 否则游戏报 "Invalid file reference in action ... in <Files>?"，
# 且该 mod 的 UpdateArt 不会被加载（ModArtLoader 无记录）→ 全部美术/图标静默空白。
ART_DEP_PLACEHOLDER = "(Mod Art Dependency File)"

# 动作段里 <File> 的匹配（必须容忍 Priority 属性，否则带 Priority 的文件被整条漏掉）
FILE_IN_ACTION_RE = re.compile(r'<File(?:\s+Priority="\d+")?\s*>(.*?)</File>')


def extract_cdata(raw: str, tag: str) -> str:
    m = re.search(r"<%s><!\[CDATA\[(.*?)\]\]></%s>" % (tag, tag), raw, re.S)
    return m.group(1) if m else ""


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _emit_element(el, indent: int) -> list[str]:
    """把 XML 元素序列化为多行（属性保文档序；空元素自闭合）——对齐 ModBuddy 产出的观感。"""
    pad = " " * indent
    attrs = "".join(' %s="%s"' % (k, _esc(v or "")) for k, v in el.attrib.items())
    children = list(el)
    text = (el.text or "").strip()
    if not children and not text:
        return ["%s<%s%s />" % (pad, el.tag, attrs)]
    if not children:
        return ["%s<%s%s>%s</%s>" % (pad, el.tag, attrs, _esc(text), el.tag)]
    lines = ["%s<%s%s>" % (pad, el.tag, attrs)]
    for c in children:
        lines.extend(_emit_element(c, indent + 2))
    lines.append("%s</%s>" % (pad, el.tag))
    return lines


def split_actions(xml_text: str, wrapper: str) -> list[str]:
    """把 <Wrapper>…</Wrapper> 动作片段拆成「一行一个子动作」的多行文本。

    兼容两种 CDATA 书写风格：ModBuddy 默认的**单行**（整段在一行，旧实现会因
    首行以 <Wrapper 开头被整体跳过 → 动作全丢）与逐行书写。实现上剥掉外层
    Wrapper 后按 XML 片段解析，再逐个子元素重新序列化，与输入换行无关。
    """
    s = (xml_text or "").strip()
    m = re.match(r"^<%s>(.*)</%s>$" % (wrapper, wrapper), s, re.S)
    if m:
        s = m.group(1).strip()
    if not s:
        return []
    frag = ET.fromstring("<_Root>%s</_Root>" % s)
    lines: list[str] = []
    for child in frag:
        lines.extend(_emit_element(child, 4))
    return lines


def extract_dependencies(raw: str) -> list[str]:
    """从 AssociationData CDATA 提取 <Dependency>，转成 modinfo 的 <Mod id title/> 行。"""
    assoc = extract_cdata(raw, "AssociationData").strip()
    if not assoc:
        return []
    out = []
    try:
        root = ET.fromstring(assoc)
    except ET.ParseError:
        return []
    for dep in root.iter("Dependency"):
        dep_id, title = dep.get("id", ""), dep.get("title", "")
        if dep_id:
            out.append('    <Mod id="%s"%s />' % (_esc(dep_id), ' title="%s"' % _esc(title) if title else ""))
    return out


def indent_localized(localized: str) -> list[str]:
    """把 CDATA 里的 <LocalizedText>…</LocalizedText> 重新缩进为 modinfo 的层级。"""
    out = []
    for line in localized.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("<LocalizedText") or s.startswith("</LocalizedText"):
            out.append("  " + s)
        elif s.startswith("<Text ") or s.startswith("</Text"):
            out.append("    " + s)
        else:
            out.append("      " + s)
    return out


def build_modinfo(proj_path: str) -> tuple[str, str]:
    """返回 (modinfo 文本, mod 名)。"""
    raw = open(proj_path, encoding="utf-8").read()
    tree = ET.parse(proj_path)
    pg = tree.getroot().find("msb:PropertyGroup", NS)
    if pg is None:
        raise SystemExit("工程缺少 <PropertyGroup>：%s" % proj_path)

    def g(tag: str) -> str:
        el = pg.find("msb:" + tag, NS)
        return (el.text or "").strip() if el is not None and el.text else ""

    guid, version = g("Guid"), g("ModVersion") or "1"
    mod_name = os.path.splitext(os.path.basename(proj_path))[0]
    localized = extract_cdata(raw, "LocalizedTextData").strip()
    ingame = extract_cdata(raw, "InGameActionData").strip()
    frontend = extract_cdata(raw, "FrontEndActionData").strip()
    criteria = extract_cdata(raw, "ActionCriteriaData").strip()
    # ★ ModBuddy 占位符替换 —— 等价于 ModBuddy 构建期行为。
    #   `.civ6proj` 里 <UpdateArt> 写的是 `(Mod Art Dependency File)`（人类可读占位符），
    #   派生到 .modinfo 时必须换成真实 <ModName>.dep —— 否则游戏报：
    #     ERROR: Invalid file reference in action, did you forgot to add it in <Files>? - (Mod Art Dependency File)
    #   且该 mod 的 UpdateArt 不会被加载（ModArtLoader 无记录）→ 全部美术/图标静默空白。
    #   （实测对照：Black_Shores_Pack.civ6proj 写占位符，其 ModBuddy 产物是真名 .dep）
    ingame = ingame.replace(ART_DEP_PLACEHOLDER, mod_name + ".dep")
    frontend = frontend.replace(ART_DEP_PLACEHOLDER, mod_name + ".dep")
    if not guid:
        raise SystemExit("工程缺少 <Guid>（mod 身份唯一真源，禁止从其它 mod 复制）")
    if not ingame:
        raise SystemExit("工程缺少 <InGameActionData>")

    # ★ 两个清单用途不同，必须分开（曾混用导致 .dep 触发「源文件不存在」误报）：
    #   · content      = <Content Include> 拷贝清单（ModBuddy 只拷这些；.dep 不在其中）
    #   · files_decl   = .modinfo 顶层 <Files> 声明清单（= content + cook 产物如 .dep）
    content = sorted({i.get("Include").replace("\\", "/")
                      for i in tree.getroot().findall("msb:ItemGroup/msb:Content", NS)
                      if i.get("Include")})
    files_decl = list(content)
    # <UpdateArt> 引用的 <ModName>.dep 必须同时出现在顶层 <Files>，否则游戏报
    # "Invalid file reference in action, did you forgot to add it in <Files>?"。
    # .dep 是 cook 产物（源工程本就没有），ModBuddy 会自动补进 <Files>；本工具等价处理。
    # 注意：占位符已在上面替换为 <ModName>.dep，故这里检查替换后的名字。
    dep_name = mod_name + ".dep"
    if (dep_name in ingame or dep_name in frontend) and dep_name not in files_decl:
        files_decl = sorted(files_decl + [dep_name])

    # 段落顺序对齐 ModBuddy 产物：Properties → Dependencies → ActionCriteria
    #   → FrontEndActions → InGameActions → (LocalizedText) → Files
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<Mod id="%s" version="%s">' % (guid, version),
           "  <Properties>",
           "    <Name>%s</Name>" % g("Name"),
           "    <Description>%s</Description>" % g("Description"),
           "    <Created>%d</Created>" % int(time.time()),
           "    <Teaser>%s</Teaser>" % g("Teaser"),
           "    <Authors>%s</Authors>" % g("Authors"),
           "    <CompatibleVersions>%s</CompatibleVersions>" % (g("CompatibleVersions") or "1.2,2.0"),
           "  </Properties>"]

    deps = extract_dependencies(raw)
    if deps:
        out.append("  <Dependencies>")
        out.extend(deps)
        out.append("  </Dependencies>")

    criteria_lines = split_actions(criteria, "ActionCriteria")
    if criteria_lines:
        out.append("  <ActionCriteria>")
        out.extend(criteria_lines)
        out.append("  </ActionCriteria>")

    frontend_lines = split_actions(frontend, "FrontEndActions")
    if frontend_lines:
        out.append("  <FrontEndActions>")
        out.extend(frontend_lines)
        out.append("  </FrontEndActions>")

    ingame_lines = split_actions(ingame, "InGameActions")
    if not ingame_lines:
        raise SystemExit("InGameActionData 解析不出任何动作（CDATA 格式？）：%s" % proj_path)
    out.append("  <InGameActions>")
    out.extend(ingame_lines)
    out.append("  </InGameActions>")

    out.extend(indent_localized(localized))
    out.append("  <Files>")
    out.extend("    <File>%s</File>" % f for f in files_decl)
    out.append("  </Files>")
    out.append("</Mod>")
    text = "\n".join(out) + "\n"
    ET.fromstring(text)  # 良构自检
    return text, mod_name, content


def sync_artdefs(proj_dir: str, mod_dir: str) -> tuple[int, int]:
    """把源工程 ArtDefs/*.artdef 同步进 Mods 副本，返回 (写入数, 总数)。

    为什么需要单独一步：ArtDefs 不在 .civ6proj 的 <Content Include> 清单里（该清单只放
    XML/SQL/Lua 与音频 bank，359 条 Content 中 artdef 为 0），所以 --deploy 的拷贝循环
    从不写它 —— Mods 副本里留着的始终是上一次 cook 的产物。cook 会把 pantry 解析不到的
    引用归一化成空值，而本工程这些引用的来源包 KublaiKhan_Vietnam 没有 pantry
    Art.xml，无法用 .Art.xml 的 <requiredGameArtIDs> 声明，于是每次部署之后源与
    Mods 的 artdef 都不一致。此处逐字节覆盖，消除该差异。
    artdef 属资产类文本（LF），copy2 原样搬运，不做任何换行或编码转换。
    """
    src_dir = os.path.join(proj_dir, "ArtDefs")
    if not os.path.isdir(src_dir):
        return 0, 0
    names = sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".artdef"))
    dst_dir = os.path.join(mod_dir, "ArtDefs")
    synced = 0
    for fn in names:
        s, d = os.path.join(src_dir, fn), os.path.join(dst_dir, fn)
        if os.path.isfile(d) and filecmp.cmp(s, d, shallow=False):
            continue
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(s, d)
        synced += 1
        print("SYNC ArtDefs/%-30s %8d B（源 → Mods）" % (fn, os.path.getsize(d)))
    return synced, len(names)


def run_cook(proj_dir: str, mods_root: str) -> int:
    """调用同目录的 cook_assets.py 重放 ArtDef / XLP 分区，返回其退出码。

    用 sys.executable + 脚本绝对路径的 argv 列表（不经 shell，路径含空格也安全）。
    子进程输出直接继承本进程的 stdout/stderr —— 受限宿主禁止管道捕获。
    """
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cook_assets.py")
    if not os.path.isfile(script):
        print("FAIL 找不到 cook_assets.py：%s" % script)
        return 1
    print()
    print("=== cook 美术产物（cook_assets.py --quiet）===")
    return subprocess.run([sys.executable, script, proj_dir, "--mods-root", mods_root,
                           "--quiet"]).returncode


def action_files(modinfo_text: str) -> list[str]:
    # 注意必须容忍 <File Priority="N">：旧正则 <File>(.*?)</File> 会漏掉全部带 Priority 的文件
    return FILE_IN_ACTION_RE.findall(modinfo_text)


def main() -> int:
    ap = argparse.ArgumentParser(description="从 .civ6proj 派生 .modinfo（等价 ModBuddy 构建）")
    ap.add_argument("project", help="X.civ6proj 路径")
    ap.add_argument("--deploy", action="store_true", help="复制 Content 文件并写 modinfo 到 Mods/<ModName>/")
    ap.add_argument("--mods-root", default=None, help="Mods 根目录（默认自动解析本机路径）")
    ap.add_argument("--no-cook", action="store_true",
                    help="--deploy 时跳过 cook_assets.py（没有 *.Art.xml 的工程用）")
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    if not os.path.isfile(proj):
        raise SystemExit("找不到工程文件：%s" % proj)
    proj_dir = os.path.dirname(proj)

    # content = <Content Include> 拷贝清单（只拷这些；不含 .dep 这类 cook 产物）
    text, mod_name, content = build_modinfo(proj)

    if not args.deploy:
        dest_dir = os.path.join(proj_dir, "Build")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, mod_name + ".modinfo")
        open(dest, "w", encoding="utf-8", newline="\r\n").write("\ufeff" + text.replace("\r\n", "\n"))
        print("OK  ->  %s" % dest)
        print("    （未部署；加 --deploy 才会复制到 Mods 目录）")
        return 0

    mods_root = args.mods_root or _paths.get("mods")
    if not mods_root:
        raise SystemExit("找不到 Mods 目录，请用 --mods-root 指定")
    mod_dir = os.path.join(mods_root, mod_name)
    os.makedirs(mod_dir, exist_ok=True)

    # ★ cook 必须排在 Content 拷贝之前：BLP / ArtDef / .dep 是游戏实际加载的美术产物，
    #   它们不进 <Content Include>，只能由 cook 写进副本。放在拷贝之后会让本次部署
    #   携带「新数据 + 旧美术」，而 .dep 缺失时下面的硬拦还会误报成配置错误。
    if args.no_cook:
        print("SKIP cook（--no-cook）")
    else:
        art_xml = glob.glob(os.path.join(proj_dir, "*.Art.xml"))
        if not art_xml:
            print("SKIP cook（工程里没有 *.Art.xml）")
        else:
            rc = run_cook(proj_dir, mods_root)
            if rc != 0:
                print("FAIL cook_assets.py 退出码 %d，部署中止（未拷贝任何 Content）。" % rc)
                return 1

    missing_src = []
    for rel in content:
        s = os.path.join(proj_dir, rel.replace("/", os.sep))
        d = os.path.join(mod_dir, rel.replace("/", os.sep))
        if not os.path.isfile(s):
            missing_src.append(rel)
            continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
        print("COPY %-46s %7d B" % (rel, os.path.getsize(d)))
    if missing_src:
        print("FAIL <Content Include> 指向的文件不存在：%s" % missing_src)
        return 1

    dest = os.path.join(mod_dir, mod_name + ".modinfo")
    # .modinfo 属配置类文本 → CRLF（换行分层铁律，见 gotchas.md §68）。
    # 原先写 LF，而 ModBuddy 构建/部署出的 modinfo 是 CRLF（实测线上 Ragunna_Pack.modinfo
    # CRLF=1114 / LF=0）——两者混用会让「工具产物 vs ModBuddy 产物」出现伪不一致。
    open(dest, "w", encoding="utf-8", newline="\r\n").write("\ufeff" + text.replace("\r\n", "\n"))
    print("OK  ->  %s" % dest)

    action_part = text.split("<Files>")[0]
    # ① 占位符残留 = 硬错误（替换在上面已做；若仍出现说明替换没生效）
    if ART_DEP_PLACEHOLDER in action_part:
        print("FAIL modinfo 残留占位符 %r（应替换为 %s.dep）" % (ART_DEP_PLACEHOLDER, mod_name))
        return 1

    # ② <UpdateArt> 必须指向真实 <ModName>.dep，且该文件存在于 Mods 副本。
    #    .dep 由 cooker 生成（--mode Dependency 或任意 cook 模式的副产物）；
    #    缺失时游戏只写一行 ERROR 然后美术全空，属静默失效，故在这里硬拦。
    if re.search(r"<UpdateArt[^>]*>\s*<File>([^<]+)</File>", action_part):
        dep_rel = mod_name + ".dep"
        dep_abs = os.path.join(mod_dir, dep_rel)
        if not os.path.isfile(dep_abs):
            print("FAIL <UpdateArt> 需要 %s，但 Mods 副本里没有该文件。" % dep_rel)
            print("     生成方式（无需 ModBuddy GUI）：")
            print("       Civ6AssetCooker_FinalRelease.exe --absolute_paths --no_mt \\")
            print("         --mode Dependency --platform Windows \\")
            print("         --pantry <源工程> --dependency_root <源工程> \\")
            print("         --config <SDK>\\AssetModTools\\Cooker\\Civ6.cfg \\")
            print("         <源工程>\\<ModName>.Art.xml")
            print("     然后把生成的 %s 复制到 %s" % (dep_rel, mod_dir))
            return 1
        # 判定要落在**顶层 <Files> 段**（content 只是 <Content Include> 拷贝清单，不含 .dep）
        files_part = text.split("<Files>", 1)[1] if "<Files>" in text else ""
        if ("<File>%s</File>" % dep_rel) not in files_part:
            print("WARN %s 未登记进顶层 <Files>（游戏会报 'did you forgot to add it in <Files>?'）" % dep_rel)

    bad = [f for f in action_files(action_part)
           if not os.path.isfile(os.path.join(mod_dir, f.replace("/", os.sep)))]
    if bad:
        print("FAIL 悬空引用（modinfo 声明但 Mods 副本里没有）：%s" % bad)
        return 1
    print("OK  modinfo 引用的动作文件全部存在（%d 个）" % len(action_files(action_part)))

    # ③ ArtDefs 强制同步（放在自检最后一步，见 sync_artdefs 的说明）
    n_sync, n_total = sync_artdefs(proj_dir, mod_dir)
    if n_total == 0:
        print("OK  ArtDefs 同步：源工程无 artdef，跳过")
    elif n_sync:
        print("OK  ArtDefs 强制同步 %d / %d 个（源 → Mods 副本）" % (n_sync, n_total))
    else:
        print("OK  ArtDefs 已一致（%d 个）" % n_total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
