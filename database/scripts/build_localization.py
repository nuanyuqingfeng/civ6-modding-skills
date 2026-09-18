#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_localization.py — 从**本机游戏安装**补全本地化文本库（含 DLC/资料片）

## 为什么需要它

`database/DebugLocalization.sqlite` 是**基础游戏**的本地化快照（15,237 个 tag × 12 语言）。
它**不含任何 DLC / 资料片文本** —— 实测 `LOC_LEADER_MANSA_MUSA_NAME`（马里·曼萨穆萨）、
`LOC_DISTRICT_PRESERVE_NAME`（保护区）、`LOC_GOVERNOR_THE_STEWARD_NAME`（总督马格努斯）等
**全部缺席**。这直接违反 SKILL.md §4.1 的第 4 条「先查原版有没有现成 tag」——
查 DLC 内容时必然查不到，只能去游戏目录翻文件。

本工具把 DLC/资料片文本也纳入查询范围，且**只加不改**：

| 模式 | 行为 | 风险 |
|------|------|------|
| `--report`（默认） | 只读扫描，报告缺口（多少 tag/语言缺失） | 零 |
| `--build <out>` | 由游戏安装**新建**一个完整库到新文件 | 不动现有库 |
| `--augment` | 向现有库**只插入缺失行**（已存在的 (Language, Tag) 一律不动） | 不改/不删任何既有行 |

## 边界（本工具的硬性约束）

1. **绝不删除、绝不覆盖**既有行：`--augment` 用 `INSERT OR IGNORE`，现有 15,237 tag × 12 语言
   与 `SkillAnnotation_Colors` / `SkillAnnotation_Icons` 人工标注侧表**原样保留**；
2. **不动 schema**：只往 `LocalizedText` 加行，不建表不改列 —— `audit_schema_drift.py` 仍通过；
3. **数据来源是本机游戏安装**（用户自己的 Steam 副本），**不是**第三方打包的库，
   不引入任何第三方数据或许可问题。

## 解析的两种形态（官方两种写法都要认）

- **形态 A**：`<Xxx>/<lang>/File.xml`，语言在**目录名**里，元素是
  `<EnglishText>/<BaseGameText>/…` 下的 `<Row Tag=".."><Text>..</Text></Row>`；
- **形态 B**：`*Translations*.xml`，语言在**属性**里，元素是
  `<Replace Tag=".." Language=".."><Text>..</Text><Gender>..</Gender><Plurality>..</Plurality></Replace>`。

`Gender` / `Plurality` 只有形态 B 提供（与本库既有列一致）。

## 用法

    # 1) 先看缺口（只读，推荐先跑）
    python build_localization.py --report

    # 2) 新建一个完整库到别的路径（不碰现有库）
    python build_localization.py --build workspace/localization_full.sqlite

    # 3) 向现有库补全缺失行（只加不改）
    python build_localization.py --augment --dry-run     # 先看会加多少行
    python build_localization.py --augment               # 实际写入

退出码：0 = 成功；1 = 有问题（找不到游戏/库、或 --report 发现缺口时为 0）；2 = 用法错误。
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sqlite3
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SKILL_DIR, "tools"))
try:
    import _paths  # type: ignore
except Exception:
    _paths = None

DEFAULT_DB = os.path.join(SKILL_DIR, "database", "DebugLocalization.sqlite")

# 本库既有的 12 语言（与 DebugLocalization.sqlite.Languages 一致）
OUR_LANGS = {"en_US", "zh_Hans_CN", "zh_Hant_HK", "ja_JP", "ko_KR",
             "de_DE", "es_ES", "fr_FR", "it_IT", "pl_PL", "pt_BR", "ru_RU"}

# 官方文本里出现的语言写法 → 本库规范名
LANG_ALIAS = {
    "zh_Hans": "zh_Hans_CN", "zh_Hant": "zh_Hant_HK",
    "zh_CN": "zh_Hans_CN", "zh_TW": "zh_Hant_HK",
    "en": "en_US", "ja": "ja_JP", "ko": "ko_KR", "de": "de_DE",
    "es": "es_ES", "fr": "fr_FR", "it": "it_IT", "pl": "pl_PL",
    "pt": "pt_BR", "ru": "ru_RU",
}

_ROW_RE = re.compile(r'<Row\s+Tag="([^"]+)"\s*>(.*?)</Row>', re.S)
_REP_RE = re.compile(r'<Replace\s+Tag="([^"]+)"\s+Language="([^"]+)"\s*>(.*?)</Replace>', re.S)
_TEXT_RE = re.compile(r"<Text>(.*?)</Text>", re.S)
_GENDER_RE = re.compile(r"<Gender>(.*?)</Gender>", re.S)
_PLUR_RE = re.compile(r"<Plurality>(.*?)</Plurality>", re.S)
_LANGDIR_RE = re.compile(r"^[a-z]{2}_[A-Za-z]{2,}$")


def find_game_text_files(game_root: str) -> list[str]:
    """游戏安装下全部本地化 XML（Base/Assets/Text + DLC/**/Text）。"""
    out: list[str] = []
    for pat in ("Base/Assets/Text/**/*.xml", "DLC/**/Text/**/*.xml"):
        out += glob.glob(os.path.join(game_root, *pat.split("/")), recursive=True)
    return sorted(set(out))


def parse_file(path: str) -> list[tuple[str, str, str, str, str]]:
    """→ [(tag, language, text, gender, plurality)]。两种形态都解析。"""
    out: list[tuple[str, str, str, str, str]] = []
    try:
        s = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return out
    if "<LocalizedText" not in s and "Text>" not in s:
        return out

    # 形态 B：<Replace Tag=.. Language=..>
    for m in _REP_RE.finditer(s):
        t = _TEXT_RE.search(m.group(3))
        if not t:
            continue
        lang = LANG_ALIAS.get(m.group(2).strip(), m.group(2).strip())
        g = _GENDER_RE.search(m.group(3))
        p = _PLUR_RE.search(m.group(3))
        out.append((m.group(1).strip(), lang, t.group(1),
                    (g.group(1).strip() if g else None),
                    (p.group(1).strip() if p else None)))

    # 形态 A：语言来自目录名
    lang_dir = os.path.basename(os.path.dirname(path))
    if _LANGDIR_RE.match(lang_dir):
        lang = LANG_ALIAS.get(lang_dir, lang_dir)
        for m in _ROW_RE.finditer(s):
            t = _TEXT_RE.search(m.group(2))
            if t:
                out.append((m.group(1).strip(), lang, t.group(1), None, None))
    return out


def scan(game_root: str) -> tuple[dict, Counter, Counter]:
    """→ (rows, per_lang, per_tag)。同 (lang,tag) 后出现的覆盖先出现的（模拟加载顺序）。"""
    files = find_game_text_files(game_root)
    rows: dict[tuple[str, str], tuple[str, str, str]] = {}
    per_lang: Counter = Counter()
    tags: set[str] = set()
    for p in files:
        for tag, lang, text, gender, plur in parse_file(p):
            if lang not in OUR_LANGS:
                continue
            rows[(lang, tag)] = (text, gender, plur)
            per_lang[lang] += 1
            tags.add(tag)
    return rows, per_lang, Counter({t: 1 for t in tags})


def read_ours(db: str) -> set[tuple[str, str]]:
    if not os.path.isfile(db):
        return set()
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    try:
        return {(r[0], r[1]) for r in con.execute("SELECT Language, Tag FROM LocalizedText")}
    finally:
        con.close()


def report(game_root: str, db: str) -> int:
    rows, per_lang, _ = scan(game_root)
    ours = read_ours(db)
    our_tags = {t for _l, t in ours}
    new_tags = {t for _l, t in rows} - our_tags
    new_pairs = set(rows) - ours

    print("=== 本地化文本覆盖报告 ===")
    print("  游戏安装   : %s" % game_root)
    print("  现有库     : %s" % db)
    print()
    print("  现有库     : %d 行 / %d tag / %d 语言" % (len(ours), len(our_tags), len({l for l, _ in ours})))
    print("  游戏安装   : %d 行 / %d tag" % (len(rows), len({t for _l, t in rows})))
    print()
    print("  可补全     : %d 行 / %d 个新 tag（现有库缺失）" % (len(new_pairs), len(new_tags)))
    print()
    print("  按语言新增行数：")
    add_by_lang = Counter(l for l, _t in new_pairs)
    for l in sorted(OUR_LANGS):
        if add_by_lang.get(l):
            print("     %-14s +%d" % (l, add_by_lang[l]))
    print()
    # 抽样展示缺失的知名 DLC 内容（三种状态必须分清，否则会误导）
    samples = ["LOC_LEADER_MANSA_MUSA_NAME", "LOC_DISTRICT_PRESERVE_NAME",
               "LOC_LEADER_HAMMURABI_NAME", "LOC_GOVERNOR_THE_DEFENDER_NAME"]
    print("  典型 DLC tag 状态：")
    for t in samples:
        if t in new_tags:
            state = "现有库缺 → 可补全"
        elif t in our_tags:
            state = "现有库已有"
        else:
            state = "游戏安装里也没有（tag 名可能不同，需另行核对）"
        print("     %-34s %s" % (t, state))
    print()
    print("  提示：`--augment --dry-run` 看写入量；`--augment` 只加不改地补全。")
    return 0


def build(game_root: str, out: str) -> int:
    """新建一个完整库到 out（自建 schema，不动现有库）。"""
    rows, per_lang, _ = scan(game_root)
    if os.path.exists(out):
        print("目标已存在，先删除再重建：%s" % out)
        os.remove(out)
    con = sqlite3.connect(out)
    con.executescript("""
        CREATE TABLE LocalizedText (
            'Language' TEXT NOT NULL, 'Tag' TEXT NOT NULL, 'Text' TEXT,
            'Gender' TEXT, 'Plurality' TEXT, PRIMARY KEY (Language, Tag));
        CREATE INDEX idx_localized_language ON LocalizedText(Language);
    """)
    con.executemany(
        "INSERT OR REPLACE INTO LocalizedText (Language, Tag, Text, Gender, Plurality) VALUES (?,?,?,?,?)",
        [(l, t, v[0], v[1], v[2]) for (l, t), v in rows.items()])
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM LocalizedText").fetchone()[0]
    con.close()
    print("已生成 %s" % out)
    print("  行数 %d / tag %d / 语言 %d" % (n, len({t for _l, t in rows}), len(per_lang)))
    return 0


def augment(game_root: str, db: str, dry_run: bool) -> int:
    """向现有库**只插入缺失行**（INSERT OR IGNORE，不删不改）。"""
    if not os.path.isfile(db):
        raise SystemExit("找不到现有库：%s" % db)
    rows, _per_lang, _ = scan(game_root)
    ours = read_ours(db)
    add = {k: v for k, v in rows.items() if k not in ours}

    print("=== 补全（只加不改）===")
    print("  现有行数   : %d" % len(ours))
    print("  待插入     : %d 行" % len(add))
    if not add:
        print("  无需补全。")
        return 0

    # 安全校验：确认我们没有覆盖任何既有行
    overlap = set(add) & ours
    assert not overlap, "内部错误：待插入集合与既有行有交集 %d" % len(overlap)
    print("  覆盖既有行 : 0（已断言）")

    if dry_run:
        print("\n[--dry-run] 未写入。去掉 --dry-run 执行。")
        before = os.path.getsize(db)
        print("  预估：当前 %.1f MB，写入 %d 行" % (before / 1048576, len(add)))
        return 0

    con = sqlite3.connect(db)
    try:
        # 写入前记录既有行数，写后核对「只增不减」
        before_n = con.execute("SELECT COUNT(*) FROM LocalizedText").fetchone()[0]
        before_tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        con.executemany(
            "INSERT OR IGNORE INTO LocalizedText (Language, Tag, Text, Gender, Plurality) VALUES (?,?,?,?,?)",
            [(l, t, v[0], v[1], v[2]) for (l, t), v in add.items()])
        con.commit()
        after_n = con.execute("SELECT COUNT(*) FROM LocalizedText").fetchone()[0]
        after_tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        con.close()

    print("\n  写入前 %d 行 → 写入后 %d 行（+%d）" % (before_n, after_n, after_n - before_n))
    print("  侧表保留   : %s" % ("是" if before_tables == after_tables else "*** 表集合变化！***"))
    print("\n  ⚠ 请复核这两点保持通过：")
    print("    python database/scripts/audit_schema_drift.py")
    print("    侧表行数：SELECT COUNT(*) FROM SkillAnnotation_Icons / SkillAnnotation_Colors")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="从本机游戏安装补全本地化文本库（含 DLC）")
    ap.add_argument("--game", default=None, help="游戏安装根（默认按 _paths.py 的 game 键解析）")
    ap.add_argument("--db", default=DEFAULT_DB, help="现有库（--augment 的目标）")
    ap.add_argument("--report", action="store_true", help="只报告缺口（默认）")
    ap.add_argument("--build", metavar="OUT", help="新建完整库到 OUT（不碰现有库）")
    ap.add_argument("--augment", action="store_true", help="向现有库只插入缺失行")
    ap.add_argument("--dry-run", action="store_true", help="配合 --augment：只统计不写入")
    args = ap.parse_args()

    game = args.game
    if not game and _paths is not None:
        game = _paths.get("game")
    if not game or not os.path.isdir(game):
        raise SystemExit(
            "找不到游戏安装目录。用 --game <路径> 指定，或检查 tools/_paths.py 的 game 键。")

    if args.build:
        return build(game, args.build)
    if args.augment:
        return augment(game, args.db, args.dry_run)
    return report(game, args.db)


if __name__ == "__main__":
    sys.exit(main())
