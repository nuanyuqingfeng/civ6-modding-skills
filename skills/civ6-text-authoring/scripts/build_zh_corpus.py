#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_zh_corpus.py — 把有效 zh 文本整理成结构化语料库

输入：`reference/zh_effective.json`（常规）或 `reference/zh_mode_effective.json`（模式），
由 `scripts/export_zh_text.py` 产出。
输出：
    常规（--class main，默认）：reference/zh_corpus.sqlite + reference/catalog/*.tsv
        （六大分类 + 相邻/图标标记，分类口径见 SKILL.md §1）
    模式（--class mode）      ：reference/zh_mode_corpus.sqlite + reference/catalog/mode.tsv
        （按 LOC 二级 token 分类 + TranslationMissing 标记；仅「模式模块」使用，见 mode-text.md）

用法：
    python scripts/build_zh_corpus.py [--class {main,mode}] [--dir <reference 目录>]
退出码：0 = 成功；2 = 缺口输入。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(SKILL_ROOT, "reference")

# ---- 常规类分类：按 LOC_ 二级 token 精确匹配（避免 UNITOPERATION 被当成 UNIT）----
C1 = {"LEADER", "CIVILIZATION", "CIVINFO", "TRAIT", "ABILITY", "AGENDA", "GOVERNOR", "UNIQUE"}
C2 = {"DISTRICT", "BUILDING", "UNIT", "UNITNAME", "IMPROVEMENT", "PROJECT", "PROMOTION",
      "RESOURCE", "FEATURE", "WONDER", "POLICY", "BELIEF", "RELIGION", "GREAT",
      "GREATPERSON", "GREATWORK", "GOVERNMENT", "GOVT", "CIVIC", "TECH", "BOOST",
      "CORPORATIONNAME"}
C3 = {"ERA"}

# 类3「开幕颂词」= 领袖加载介绍词（LOC_LOADING_INFO_LEADER_*，主）+ 时代旁白（LOC_ERA_*，辅）
OPENING_LEADER_PREFIX = "LOC_LOADING_INFO_LEADER_"
C4 = {"DIPLO", "DIPLOMACY", "DIPLOACTION", "GOSSIP", "EMERGENCY"}

ADJ_RE = re.compile(r"相邻")
ADJ_ALT_RE = re.compile(r"^\+[0-9]+.*?：?每")
ICON_RE = re.compile(r"\[ICON_[A-Za-z0-9_]+\]")


def category_main(tag: str) -> str:
    # 类3 开幕颂词：领袖加载介绍词优先（前缀匹配，token 规则兜不住）
    if tag.startswith(OPENING_LEADER_PREFIX):
        return "opening_ode"
    m = re.match(r"LOC_([A-Z0-9]+)($|_)", tag)
    tok = m.group(1) if m else None
    if tok in C1:
        return "leader_trait"
    if tok in C2:
        return "item"
    if tok in C3:
        return "opening_ode"
    if tok in C4:
        return "diplomacy"
    return "other"


def category_mode(tag: str) -> str:
    """模式类：按 LOC 二级 token 直接当分类（GAMEMODE/BARBARIAN/HERO/...）。"""
    m = re.match(r"LOC_([A-Z0-9]+)($|_)", tag)
    return (m.group(1) if m else "OTHER").lower()


def main() -> int:
    ap = argparse.ArgumentParser(description="构建 zh 结构化语料库")
    ap.add_argument("--class", dest="cls", choices=("main", "mode"), default="main")
    ap.add_argument("--dir", default=DEFAULT_DIR, help="reference 目录")
    args = ap.parse_args()
    cls = args.cls
    src_name = "zh_effective.json" if cls == "main" else "zh_mode_effective.json"
    out_name = "zh_corpus.sqlite" if cls == "main" else "zh_mode_corpus.sqlite"
    src = os.path.join(args.dir, src_name)
    if not os.path.isfile(src):
        print("ERROR: 缺 %s（先跑 scripts/export_zh_text.py --class %s）" % (src, cls))
        return 2

    d = json.load(open(src, encoding="utf-8"))
    catdir = os.path.join(args.dir, "catalog")
    os.makedirs(catdir, exist_ok=True)
    rows = []
    stat = collections.Counter()
    adj_cnt = icon_cnt = miss_cnt = 0
    per_cat = collections.defaultdict(list)
    for tag, v in d.items():
        text = v.get("text") or ""
        missing = 1 if "TRANSLATION MISSING" in text else 0
        cat = category_mode(tag) if cls == "mode" else category_main(tag)
        is_adj = 1 if (ADJ_RE.search(text) or ADJ_ALT_RE.search(text.strip())) else 0
        has_icon = 1 if ICON_RE.search(text) else 0
        stat[cat] += 1
        adj_cnt += is_adj
        icon_cnt += has_icon
        miss_cnt += missing
        rows.append((tag, cat, text, v.get("gender"), v.get("plurality"),
                     v.get("tier"), v.get("src"), is_adj, has_icon, missing))
        per_cat[cat].append((tag, text))

    outdb = os.path.join(args.dir, out_name)
    con = sqlite3.connect(outdb)
    # 视图原先名（`zh_era_ode` 为类3 改名前的旧名），一并 DROP 以清理历史残留
    for v in ("zh_era_ode", "zh_leader_trait", "zh_item", "zh_opening_ode",
              "zh_diplomacy", "zh_adjacency", "zh_icon", "zh_mode"):
        con.execute("DROP VIEW IF EXISTS %s" % v)
    con.execute("DROP TABLE IF EXISTS LocalizedText")
    con.execute("""CREATE TABLE LocalizedText(
        Tag TEXT PRIMARY KEY, Category TEXT, Text TEXT, Gender TEXT, Plurality TEXT,
        Tier TEXT, Source TEXT, IsAdjacency INTEGER, HasIcon INTEGER,
        TranslationMissing INTEGER)""")
    con.executemany("INSERT INTO LocalizedText VALUES(?,?,?,?,?,?,?,?,?,?)", rows)
    if cls == "main":
        con.executescript("""
            CREATE VIEW zh_leader_trait AS SELECT * FROM LocalizedText WHERE Category='leader_trait';
            CREATE VIEW zh_item        AS SELECT * FROM LocalizedText WHERE Category='item';
            CREATE VIEW zh_opening_ode AS SELECT * FROM LocalizedText WHERE Category='opening_ode';
            CREATE VIEW zh_diplomacy   AS SELECT * FROM LocalizedText WHERE Category='diplomacy';
            CREATE VIEW zh_adjacency   AS SELECT * FROM LocalizedText WHERE IsAdjacency=1;
            CREATE VIEW zh_icon        AS SELECT * FROM LocalizedText WHERE HasIcon=1;
        """)
    else:
        con.execute("CREATE VIEW zh_mode AS SELECT * FROM LocalizedText;")
    con.commit()
    con.close()

    cat_file = "mode.tsv" if cls == "mode" else None
    for cat, items in per_cat.items():
        name = cat_file if cls == "mode" else (cat + ".tsv")
        with open(os.path.join(catdir, name), "w", encoding="utf-8") as f:
            for t, x in sorted(items):
                f.write("%s\t%s\n" % (t, (x or "").replace("\n", "\\n")))

    lines = ["zh 语料分类统计（%s，总 %d tag）" % (cls, len(rows)), "=" * 40]
    if cls == "main":
        for k in ("leader_trait", "item", "opening_ode", "diplomacy", "other"):
            lines.append("  %-14s %6d" % (k, stat[k]))
    else:
        for k, n in stat.most_common(20):
            lines.append("  %-14s %6d" % (k, n))
    lines.append("  %-14s %6d" % ("is_adjacency", adj_cnt))
    lines.append("  %-14s %6d" % ("has_icon", icon_cnt))
    if cls == "mode":
        lines.append("  %-14s %6d" % ("translation_missing", miss_cnt))
    rep = "\n".join(lines)
    print(rep)
    open(os.path.join(args.dir, "zh_corpus_stats.txt" if cls == "main" else "zh_mode_corpus_stats.txt"),
         "w", encoding="utf-8").write(rep + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
