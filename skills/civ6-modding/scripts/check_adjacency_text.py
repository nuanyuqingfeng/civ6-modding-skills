import argparse
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "art"))
import iconify_text  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOC_DB = os.path.join(SKILL_DIR, "database", "DebugLocalization.sqlite")
ADJ_INSERT_RE = re.compile(
    r"INSERT\s+(?:OR\s+(?:REPLACE|IGNORE)\s+)?INTO\s+Adjacency_YieldChanges\s*\(([^)]*)\)",
    re.I)
LOC_KEY_RE = re.compile(r"LOC_[A-Za-z0-9_]+")
ICON_RE = re.compile(r"\[ICON_[A-Za-z0-9_]+\]", re.I)
NUM_RE = re.compile(r"\{1_num\}", re.I)


def line_of(content, pos):
    return content.count("\n", 0, pos) + 1


def mask_line_comments(text):
    """整行注释替换为等长空格，保留行号与偏移，避免把注释掉的 INSERT 当真行。"""
    out = []
    for line in text.split("\n"):
        if line.strip().startswith("--"):
            out.append(" " * len(line))
        else:
            out.append(line)
    return "\n".join(out)


def load_base_loc_texts(base):
    items = {}
    if not base or not os.path.isfile(base):
        print("WARN 本地化基础库缺失（%s），只按工程内文本核对" % base, file=sys.stderr)
        return items
    con = sqlite3.connect(base)
    try:
        for lang, tag, text in con.execute(
                "SELECT Language, Tag, Text FROM LocalizedText WHERE Text IS NOT NULL"):
            items.setdefault(tag, {})[lang] = text
    finally:
        con.close()
    return items


def load_project_loc_texts(root):
    items = {}
    if not root:
        return items
    for p in iconify_text.find_text_files(root):
        content = iconify_text.read_text_file(p)[0]
        if p.lower().endswith(".sql"):
            parsed = iconify_text.parse_sql_entries(content)
        else:
            parsed = iconify_text.parse_xml_entries(content)
        for e in parsed:
            if e.get("language") and e.get("tag"):
                items.setdefault(e["tag"], {})[e["language"]] = e["text"]
    return items


def collect_adjacency_descriptions(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    content = mask_line_comments(raw)
    out = []
    for m in ADJ_INSERT_RE.finditer(content):
        tail = content[m.end():]
        vals = re.search(r"\bVALUES\b", tail, re.I)
        if not vals:
            continue
        i = iconify_text._skip_ws_comments(content, m.end() + vals.end())
        while i < len(content) and content[i] == "(":
            got = iconify_text._read_paren_group(content, i)
            if not got:
                break
            group, after = got
            for value, start, _end in iconify_text._split_sql_literals(group):
                if LOC_KEY_RE.fullmatch(value):
                    out.append((line_of(content, i + start), value))
            j = iconify_text._skip_ws_comments(content, after)
            if j < len(content) and content[j] == ",":
                i = iconify_text._skip_ws_comments(content, j + 1)
            else:
                break
    return out


def main():
    ap = argparse.ArgumentParser(description="相邻加成本地化文本检查：Description 文本缺图标或 {1_num} 时拦截")
    ap.add_argument("root", nargs="?", default=os.getcwd(), help="工程根目录")
    ap.add_argument("--base", default=DEFAULT_LOC_DB, help="本地化基础库（DebugLocalization.sqlite）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    targets = []
    for dirpath, dirnames, filenames in os.walk(root):
        if any(x in dirpath for x in ("workspace", ".git", "node_modules")):
            continue
        for fn in filenames:
            if fn.endswith(".sql") and ".bak" not in fn:
                targets.append(os.path.join(dirpath, fn))
    targets.sort()

    loc = load_base_loc_texts(args.base)
    for tag, langs in load_project_loc_texts(root).items():
        loc.setdefault(tag, {}).update(langs)

    rows = []
    for p in targets:
        rel = os.path.relpath(p, root)
        for line, key in collect_adjacency_descriptions(p):
            rows.append((rel, line, key))

    print("待检查 SQL 文件: %d" % len(targets))
    print("相邻加成 Description 键: %d 个" % len(rows))
    if not rows:
        print("未发现 Adjacency_YieldChanges 行")
        return 0

    problems = []
    seen = set()
    for rel, line, key in rows:
        lang_map = loc.get(key)
        if not lang_map:
            if key not in seen:
                seen.add(key)
                problems.append((rel, line, "%s 文本缺失" % key))
            continue
        for lang, text in lang_map.items():
            dedup = (key, lang)
            if dedup in seen:
                continue
            seen.add(dedup)
            missing = []
            if not ICON_RE.search(text):
                missing.append("[ICON_*]")
            if not NUM_RE.search(text):
                missing.append("{1_num}")
            if missing:
                problems.append((rel, line, "%s (%s) 缺少 %s" % (key, lang, " / ".join(missing))))

    if problems:
        print("\n=== 相邻加成本地化问题 ===")
        for rel, line, msg in problems:
            print("  %s:%d  %s" % (rel, line, msg))
        print("\nFAIL: %d 处" % len(problems))
        return 1
    print("全部相邻加成 Description 文本含图标与 {1_num}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
