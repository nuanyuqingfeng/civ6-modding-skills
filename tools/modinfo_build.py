# -*- coding: utf-8 -*-
"""从 .civ6proj 派生 .modinfo（等价 ModBuddy 的构建动作），并可选部署到游戏 Mods 目录。

为什么需要它：ModBuddy（VS 扩展）不便在无 GUI 环境调用，而 `.modinfo` 完全可以由
`.civ6proj` 机械派生 —— 本项目所有新 mod 都走这条路，无需每次手写 modinfo。

用法：
    python modinfo_build.py <X.civ6proj>                 # 只生成到 <proj目录>/Build/X.modinfo
    python modinfo_build.py <X.civ6proj> --deploy        # 复制 Content 文件 + 写 modinfo 到 Mods/<X>/
    python modinfo_build.py <X.civ6proj> --deploy --mods-root <目录>

产出与自检：
    · modinfo 结构四段：Properties / InGameActions / LocalizedText / Files
    · 生成后做 XML 良构解析 + `InGameActions` 内全部 <File> 引用存在性检查（悬空即 exit 1）
    · `<Content Include>` 是拷贝清单（ModBuddy 只拷 Content 条目 —— 只写在 InGameActions 里
      而漏进 Content 的文件不会被部署，是踩过的坑）

退出码：0 成功 / 1 失败
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
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


def extract_cdata(raw: str, tag: str) -> str:
    m = re.search(r"<%s><!\[CDATA\[(.*?)\]\]></%s>" % (tag, tag), raw, re.S)
    return m.group(1) if m else ""


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
    localized = extract_cdata(raw, "LocalizedTextData").strip()
    ingame = extract_cdata(raw, "InGameActionData").strip()
    if not guid:
        raise SystemExit("工程缺少 <Guid>（mod 身份唯一真源，禁止从其它 mod 复制）")
    if not ingame:
        raise SystemExit("工程缺少 <InGameActionData>")

    content = sorted({i.get("Include") for i in tree.getroot().findall("msb:ItemGroup/msb:Content", NS)
                      if i.get("Include")})
    content = [c.replace("\\", "/") for c in content]

    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<Mod id="%s" version="%s">' % (guid, version),
           "  <Properties>",
           "    <Name>%s</Name>" % g("Name"),
           "    <Description>%s</Description>" % g("Description"),
           "    <Created>%d</Created>" % int(time.time()),
           "    <Teaser>%s</Teaser>" % g("Teaser"),
           "    <Authors>%s</Authors>" % g("Authors"),
           "    <CompatibleVersions>%s</CompatibleVersions>" % (g("CompatibleVersions") or "1.2,2.0"),
           "  </Properties>",
           "  <InGameActions>"]
    for line in ingame.splitlines():
        s = line.strip()
        if s.startswith("<InGameActions") or s.startswith("</InGameActions") or not s:
            continue
        out.append("    " + s)
    out.append("  </InGameActions>")
    out.extend(indent_localized(localized))
    out.append("  <Files>")
    out.extend("    <File>%s</File>" % f for f in content)
    out.append("  </Files>")
    out.append("</Mod>")
    text = "\n".join(out) + "\n"
    ET.fromstring(text)  # 良构自检
    return text, os.path.splitext(os.path.basename(proj_path))[0]


def action_files(modinfo_text: str) -> list[str]:
    return re.findall(r"<File>(.*?)</File>", modinfo_text)


def main() -> int:
    ap = argparse.ArgumentParser(description="从 .civ6proj 派生 .modinfo（等价 ModBuddy 构建）")
    ap.add_argument("project", help="X.civ6proj 路径")
    ap.add_argument("--deploy", action="store_true", help="复制 Content 文件并写 modinfo 到 Mods/<ModName>/")
    ap.add_argument("--mods-root", default=None, help="Mods 根目录（默认自动解析本机路径）")
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    if not os.path.isfile(proj):
        raise SystemExit("找不到工程文件：%s" % proj)
    proj_dir = os.path.dirname(proj)

    text, mod_name = build_modinfo(proj)
    content = re.findall(r"<File>(.*?)</File>", text.split("<Files>")[1])

    if not args.deploy:
        dest_dir = os.path.join(proj_dir, "Build")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, mod_name + ".modinfo")
        open(dest, "w", encoding="utf-8", newline="\r\n").write(text.replace("\r\n", "\n"))
        print("OK  ->  %s" % dest)
        print("    （未部署；加 --deploy 才会复制到 Mods 目录）")
        return 0

    mods_root = args.mods_root or _paths.get("mods")
    if not mods_root:
        raise SystemExit("找不到 Mods 目录，请用 --mods-root 指定")
    mod_dir = os.path.join(mods_root, mod_name)
    os.makedirs(mod_dir, exist_ok=True)

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
    open(dest, "w", encoding="utf-8", newline="\r\n").write(text.replace("\r\n", "\n"))
    print("OK  ->  %s" % dest)

    bad = [f for f in action_files(text.split("<Files>")[0])
           if not os.path.isfile(os.path.join(mod_dir, f.replace("/", os.sep)))]
    if bad:
        print("FAIL 悬空引用（modinfo 声明但 Mods 副本里没有）：%s" % bad)
        return 1
    print("OK  modinfo 引用的动作文件全部存在（%d 个）" % len(action_files(text.split("<Files>")[0])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
