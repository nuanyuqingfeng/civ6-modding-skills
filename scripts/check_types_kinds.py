# -*- coding: utf-8 -*-
"""Types.Kind 合法性检查 —— 复现游戏加载期的 `Invalid Reference on Types.Kind`。

`INSERT INTO Types (Type, Kind) VALUES ('X', 'KIND_Y')` 里，Kind 必须是引擎 `Kinds` 表
已有的枚举值（不是你可以自由发明的字符串）。写错不会在打包时报错，而是在游戏加载时丢弃该行
或报 Invalid Reference —— 症状往往是"内容完全不出现"。

用法：
    python check_types_kinds.py [--root <工程根目录>] [--db <基础库>] [--dirs Data,Mod_Adaptation]

参数：
    --root  工程根目录（默认当前工作目录）
    --db    基础库快照（默认 <本skill>/database/DebugGameplay.sqlite）
    --dirs  只扫描这些子目录（逗号分隔，默认 Data,Mod_Adaptation）

退出码：0 = 无非法 Kind；1 = 发现非法 Kind。

局限（已知）：
    正则 `pat_pair` 只匹配同一行内相邻的两个字面量，因此
      - 跨行书写的元组
      - `INSERT ... SELECT '字面量' || 列` 这类动态拼接
    会**漏检**。动态拼接场景请改用 rgn_validate 的实跑模式。
"""
import argparse
import glob
import os
import re
import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DB = os.path.normpath(os.path.join(HERE, "..", "database", "DebugGameplay.sqlite"))

pat_pair = re.compile(r"\(\s*'([^']+)'\s*,\s*'(KIND_[A-Z0-9_]+)'\s*\)")
pat_types_insert = re.compile(r"INSERT[^;]*?INTO\s+Types\b[^;]*;", re.I | re.S)


def main():
    ap = argparse.ArgumentParser(description="Types.Kind 合法性检查")
    ap.add_argument("--root", default=os.getcwd(), help="工程根目录")
    ap.add_argument("--db", default=SKILL_DB, help="基础库快照（默认 skill 自带 DebugGameplay.sqlite）")
    ap.add_argument("--dirs", default="Data,Mod_Adaptation", help="扫描的子目录，逗号分隔")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isfile(args.db):
        print(f"ERROR: 基础库不存在: {args.db}")
        return 2

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    try:
        kinds = {r[0] for r in con.execute("SELECT Kind FROM Kinds").fetchall()}
    except sqlite3.Error as e:
        print(f"ERROR: 读 Kinds 表失败: {e}")
        return 2
    finally:
        con.close()
    if not kinds:
        print("ERROR: Kinds 表为空，基础库可能损坏")
        return 2

    files = []
    for sub in [s.strip() for s in args.dirs.split(",") if s.strip()]:
        files += glob.glob(os.path.join(root, sub, "**", "*.sql"), recursive=True)
    files = sorted(set(files))

    bad, good = [], 0
    for path in files:
        try:
            txt = open(path, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"  ! 读取失败 {path}: {e}")
            continue
        for m in pat_types_insert.finditer(txt):
            stmt = m.group(0)
            line0 = txt[: m.start()].count("\n") + 1
            for tm in pat_pair.finditer(stmt):
                type_name, kind = tm.group(1), tm.group(2)
                if kind in kinds:
                    good += 1
                else:
                    lineno = line0 + stmt[: tm.start()].count("\n")
                    bad.append((os.path.relpath(path, root), lineno, type_name, kind))

    print("=== Types.Kind 检查 ===")
    print(f"  扫描 SQL 文件 : {len(files)}")
    print(f"  合法 Kind 行  : {good}")
    print(f"  非法 Kind 行  : {len(bad)}")
    for rel, line, t, k in bad:
        print(f"  ✗ {rel}:{line}  {t} -> {k}（Kinds 中不存在）")
    if bad:
        print("\n提示：Kind 必须是引擎枚举。完整取值见 schema-annotated.md 的 Types 表一节，")
        print("      或 `SELECT DISTINCT Kind FROM Kinds;`（基础库 DebugGameplay.sqlite）。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
