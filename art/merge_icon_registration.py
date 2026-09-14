#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_icon_registration.py — 把 make_atlas.py 产出的注册片段幂等并入项目

make_atlas.py / convert_art.ps1 只会产出 <atlas>_registration.xml **片段**（设计如此，
不直接改项目文件）。本工具负责把它落到项目里，并且顺手把 XLP 条目补齐——这两步
以前是"由 AI 手工合并"，是漏项高发区：

  * 忘了合并注册片段 → 图标在游戏里完全不出现；
  * 忘了补 XLP 条目 → .dds 存在但不会被打进 UI/Icons 包，游戏里纹理加载不出来；
  * 重复合并 → IconDefinitions 重名，后写的覆盖前写的。

特性：
  * **幂等**：图集行按 (Name, IconSize) 去重、定义行按 Name 去重、XLP 按 m_EntryID 去重；
  * **保格式**：完全保留目标文件的 BOM / 换行风格（CRLF or LF）/ 行尾空格风格，
    只做行插入（含中文的工程文件不会被整篇重写）；
  * **可回滚**：--dry-run 只打印将要插入的内容，不落盘。

用法：
  python merge_icon_registration.py <projectRoot> --fragment <...>_registration.xml
         [--icons <Icons.xml>]        # 缺省 <root>/Data/Icons_RGN.xml
         [--xlp <Icons.xlp>]          # 缺省 <root>/XLPs/Icons.xlp
         [--no-xlp] [--dry-run]
退出码 0 = 成功（含"无需改动"）。
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def read_text_keep(path):
    """返回 (text, bom) —— 文本按 utf-8-sig 解析，bom 单独记下来，写回时按原样加回。"""
    raw = Path(path).read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    return raw.decode("utf-8-sig"), bom


def write_text_keep(path, text, bom):
    Path(path).write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def detect_eol(text):
    return "\r\n" if text.count("\r\n") >= max(1, text.count("\n") - text.count("\r\n")) else "\n"


def indent_of_before(text, anchor):
    """取 anchor 之前最近一个 <Row 行的缩进，用来对齐插入内容的缩进风格。"""
    idx = text.find(anchor)
    head = text[:idx] if idx >= 0 else text
    ms = re.findall(r"([ \t]+)<Row ", head)
    return ms[-1] if ms else "        "


def parse_fragment(path):
    r = ET.parse(path).getroot()
    atlases = [e.attrib for e in ((r.find("IconTextureAtlases") if r.find("IconTextureAtlases") is not None else []))]
    defs = [e.attrib for e in ((r.find("IconDefinitions") if r.find("IconDefinitions") is not None else []))]
    return atlases, defs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projectRoot")
    ap.add_argument("--fragment", required=True)
    ap.add_argument("--icons", default="")
    ap.add_argument("--xlp", default="")
    ap.add_argument("--no-xlp", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.projectRoot)
    icons = Path(args.icons) if args.icons else root / "Data" / "Icons_RGN.xml"
    xlp = Path(args.xlp) if args.xlp else root / "XLPs" / "Icons.xlp"
    frag = Path(args.fragment)
    if not icons.is_file():
        sys.exit(f"找不到 Icons XML: {icons}")
    if not frag.is_file():
        sys.exit(f"找不到注册片段: {frag}")

    atlases, defs = parse_fragment(frag)
    text, bom = read_text_keep(icons)
    eol = detect_eol(text)

    # 逐 <Row .../> 取属性字典，**不依赖属性顺序**（Baseline/Index 等可插在中间）
    have_atlas, have_def = set(), set()
    for m in re.finditer(r'<Row\s+([^>]*?)/>', text):
        attrs = dict(re.findall(r'([A-Za-z_]\w*)="([^"]*)"', m.group(1)))
        if 'Name' in attrs and 'IconSize' in attrs:
            have_atlas.add((attrs['Name'], attrs['IconSize']))
        if 'Name' in attrs and 'Atlas' in attrs:
            have_def.add(attrs['Name'])

    new_atlas = [a for a in atlases if (a.get("Name"), a.get("IconSize")) not in have_atlas]
    new_def = [d for d in defs if d.get("Name") not in have_def]

    def row_line(attr, indent):
        parts = " ".join(f'{k}="{v}"' for k, v in attr.items())
        return f"{indent}<Row {parts}/>"

    if new_atlas:
        ind = indent_of_before(text, "</IconTextureAtlases>")
        block = eol.join(row_line(a, ind) for a in new_atlas)
        text = text.replace("</IconTextureAtlases>", block + eol + ind[:-4] + "</IconTextureAtlases>", 1)
    if new_def:
        ind = indent_of_before(text, "</IconDefinitions>")
        block = eol.join(row_line(d, ind) for d in new_def)
        text = text.replace("</IconDefinitions>", block + eol + ind[:-4] + "</IconDefinitions>", 1)

    print(f"注册片段: {frag.name}")
    print(f"  IconTextureAtlases 新增 {len(new_atlas)} 行（已有 {len(atlases) - len(new_atlas)} 行，跳过）")
    for a in new_atlas:
        print(f"    + {a.get('Name')} @{a.get('IconSize')}  {a.get('Filename')}")
    print(f"  IconDefinitions    新增 {len(new_def)} 行（已有 {len(defs) - len(new_def)} 行，跳过）")
    for d in new_def:
        print(f"    + {d.get('Name')} -> Index {d.get('Index')}")

    xlp_text, xlp_bom = (None, False)
    new_xlp = []
    if not args.no_xlp and xlp.is_file():
        xlp_text, xlp_bom = read_text_keep(xlp)
        have_eid = set(re.findall(r'<m_EntryID text="([^"]+)"', xlp_text))
        # 片段里出现的贴图名：多格图集 Filename 带 .dds 后缀，去掉后缀即 UITexture 名；
        # 1x1 单图集 Filename 不带后缀，它本身就是 UITexture 名（此前被漏掉 → 贴图不进包）
        names = []
        for a in atlases:
            fn = a.get("Filename", "")
            if fn.endswith(".dds"):
                names.append(fn[:-4])
            elif fn:
                names.append(fn)
        for n in names:
            if n and n not in have_eid and n not in new_xlp:
                new_xlp.append(n)
        print(f"  XLP ({xlp.name})                新增 {len(new_xlp)} 条")
        for n in new_xlp:
            print(f"    + {n}")

    if args.dry_run:
        print("\n--dry-run：未写入任何文件")
        return 0

    changed = []
    if new_atlas or new_def:
        write_text_keep(icons, text, bom)
        changed.append(icons)
    if new_xlp and xlp_text is not None:
        xe = detect_eol(xlp_text)
        block = "".join(
            f"\t\t<Element>{xe}\t\t\t<m_EntryID text=\"{n}\"/>{xe}"
            f"\t\t\t<m_ObjectName text=\"{n}\"/>{xe}\t\t</Element>{xe}" for n in new_xlp)
        xlp_text = xlp_text.replace("\t</m_Entries>", block + "\t</m_Entries>", 1)
        write_text_keep(xlp, xlp_text, xlp_bom)
        changed.append(xlp)

    if not changed:
        print("\n无需改动（全部已存在）")
    else:
        for c in changed:
            print(f"  已写入 {c}")
    print("提示：改完跑 art/verify_icon_atlas.py <projectRoot> 复核")
    return 0


if __name__ == "__main__":
    sys.exit(main())
