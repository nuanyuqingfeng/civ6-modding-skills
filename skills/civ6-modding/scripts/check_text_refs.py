import argparse
import fnmatch
import glob
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "art"))
import iconify_text  # noqa: E402

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BASE_DB = os.path.join(SKILL_DIR, "database", "DebugLocalization.sqlite")
LOC_RE = re.compile(r"\{LOC_([A-Za-z0-9_]+)\}")

NON_TEXT_PATTERNS = [
    "Data/**/*.sql",
    "Data/**/*.xml",
    "Scripts/**/*.lua",
    "ImportFiles/**/*.lua",
    "UI/**/*.lua",
    "UI/**/*.xml",
    "*.civ6proj",
    "*.Art.xml",
]


def line_of(content, pos):
    return content.count("\n", 0, pos) + 1


def load_base_loc_tags(base):
    tags = set()
    if not base or not os.path.isfile(base):
        print("WARN 本地化基础库缺失（%s），{LOC_x} 只按工程内定义核对" % base, file=sys.stderr)
        return tags
    con = sqlite3.connect(base)
    try:
        for (tag,) in con.execute("SELECT DISTINCT Tag FROM LocalizedText"):
            tags.add(tag)
    finally:
        con.close()
    return tags


def load_project_loc_tags(root):
    tags = set()
    if not root:
        return tags
    for p in iconify_text.find_text_files(root):
        content = iconify_text.read_text_file(p)[0]
        parsed = iconify_text.parse_sql_entries(content) if p.lower().endswith(".sql") else iconify_text.parse_xml_entries(content)
        for e in parsed:
            tags.add(e["tag"])
    return tags


def find_non_text_files(root):
    out = []
    for pat in NON_TEXT_PATTERNS:
        out += glob.glob(os.path.join(root, pat), recursive=True)
    return sorted(set(out))


def collect_file_references(root):
    blob = []
    for p in find_non_text_files(root):
        try:
            blob.append(open(p, encoding="utf-8", errors="ignore").read())
        except OSError:
            continue
    return "\n".join(blob)


def check_file(path, known_icons, known_loc, ref_blob, only_config_orphans):
    problems = []
    content, _enc = iconify_text.read_text_file(path)
    parsed = iconify_text.parse_sql_entries(content) if path.lower().endswith(".sql") else iconify_text.parse_xml_entries(content)
    if not parsed:
        parsed = [{"tag": "", "text": content, "start": 0, "end": len(content)}]
    for e in parsed:
        for name in iconify_text.collect_icons(e["text"]):
            if name.casefold() not in known_icons:
                problems.append((line_of(content, e["start"]), "[ICON_%s] 解析不到（文本往图标定义的悬空）" % name))
        for m in LOC_RE.finditer(e["text"]):
            tag = m.group(1)
            if tag not in known_loc:
                line = line_of(content, e["start"] + m.start())
                problems.append((line, "%s 解析不到（文本往回指向的本地化定义缺失）" % m.group(0)))
    if not only_config_orphans and "config" in os.path.basename(path).lower():
        for e in parsed:
            if e["tag"] and e["tag"] not in ref_blob:
                problems.append((line_of(content, e["start"]), "%s 未被任何工程文件引用（配置孤儿 tag）" % e["tag"]))
    return problems


def main():
    ap = argparse.ArgumentParser(description="文本引用双向闭合检查：图标/LOC 占位符可解析，配置文本无孤儿 tag")
    ap.add_argument("root", nargs="?", help="工程根目录（含 Text/）")
    ap.add_argument("--file", action="append", default=[], help="只检查指定文本文件（可重复）")
    ap.add_argument("--base", default=DEFAULT_BASE_DB, help="本地化基础库（DebugLocalization.sqlite）")
    ap.add_argument("--no-config-orphans", action="store_true", help="跳过配置孤儿 tag 检查")
    args = ap.parse_args()

    if not args.root and not args.file:
        ap.error("需要给工程根目录，或用 --file 指定文件")

    known_icons = set(iconify_text.load_vanilla_icons())
    pdefs, patlases = iconify_text.load_project_icons(args.root) if args.root else (set(), set())
    known_icons |= pdefs | patlases
    known_loc = load_base_loc_tags(args.base)
    known_loc |= load_project_loc_tags(args.root)
    ref_blob = collect_file_references(args.root) if args.root else ""

    files = list(args.file) if args.file else iconify_text.find_text_files(args.root)
    if not files:
        print("未找到 Text/ 下的 .sql / .xml")
        return 0
    print("图标名来源：官方全表 %d 个 + 工程 IconDefinitions %d 个 + 图集 %d 个；LOC 来源：基础库 %d 个 + 工程 %d 个"
          % (len(iconify_text.load_vanilla_icons()), len(pdefs), len(patlases),
             len(load_base_loc_tags(args.base)), len(load_project_loc_tags(args.root))))

    bad = []
    for p in files:
        try:
            problems = check_file(p, known_icons, known_loc, ref_blob, args.no_config_orphans)
        except UnicodeDecodeError as e:
            print("WARN 非 UTF-8 跳过 %s：%s" % (p, e))
            continue
        for line, msg in problems:
            bad.append("%s:%d  %s" % (os.path.relpath(p, args.root or "."), line, msg))
    if bad:
        print("\n=== 文本引用问题（悬空 / 孤儿） ===")
        for item in sorted(set(bad)):
            print("  %s" % item)
        print("\nFAIL: %d 处" % len(set(bad)))
        return 1
    print("\n全部文本引用双向闭合：无悬空、无孤儿。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
