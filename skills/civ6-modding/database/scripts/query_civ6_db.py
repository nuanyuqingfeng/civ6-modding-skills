#!/usr/bin/env python3
"""Civilization VI Mod Database Query Tool — SQLite CLI wrapper."""

import argparse
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(SKILL_ROOT, "database")
DB_PATH = os.path.join(DATA_DIR, "DebugGameplay.sqlite")
LOC_DB_PATH = os.path.join(DATA_DIR, "DebugLocalization.sqlite")
README_PATH = os.path.join(DATA_DIR, "README.md")


def _db_missing_msg(db_path):
    return (
        "[错误] 缺少离线参考库：%s\n"
        "  该库是官方 gameplay 库快照（约 58 MiB），体积大且原则上可重建，"
        "已被 .gitignore 排除，不随 skill 仓库分发。\n"
        "  三种补齐方式（详见 %s 第二节/第四节）：\n"
        "    1) 从可信来源取得一份官方 gameplay 库快照，直接放到 %s\n"
        "    2) 手上有官方 gameplay SQL dump（DebugGameplay_ALL_MODES.sql）时，按 README 第四节导入\n"
        "    3) 库放在别处：加 --db <你的 DebugGameplay.sqlite 绝对路径> 指定（本次查询即可用）\n"
        "  补齐后建议先跑结构自检：python %s\n"
        % (db_path, README_PATH, DB_PATH, os.path.join(DATA_DIR, "scripts", "audit_schema_drift.py")))


def _require_db():
    """库缺失时明确报错，并以非 0 退出（exit 2：与 --check-id 命中冲突的 exit 1 区分）。"""
    if os.path.isfile(DB_PATH):
        return
    sys.stderr.write(_db_missing_msg(DB_PATH))
    sys.exit(2)


def _apply_db_override(db_arg):
    """--db 覆盖基础库；同目录下存在 DebugLocalization.sqlite 时一并切换（供 --type-name）。"""
    global DB_PATH, LOC_DB_PATH
    DB_PATH = os.path.abspath(db_arg)
    sibling = os.path.join(os.path.dirname(DB_PATH), "DebugLocalization.sqlite")
    if os.path.isfile(sibling):
        LOC_DB_PATH = sibling


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _query(db_path, sql, params=()):
    conn = _connect(db_path)
    rows = [dict(r) for r in conn.execute(sql, params)]
    conn.close()
    return rows


def search_modifiertypes(keyword, limit=50):
    return _query(DB_PATH,
        "SELECT ModifierType FROM Modifiers WHERE ModifierType LIKE ? "
        "GROUP BY ModifierType ORDER BY ModifierType LIMIT ?",
        (f"%{keyword}%", limit))

def search_effects(keyword, limit=50):
    return _query(DB_PATH,
        "SELECT DISTINCT EffectType FROM DynamicModifiers WHERE EffectType LIKE ? "
        "ORDER BY EffectType LIMIT ?",
        (f"%{keyword}%", limit))

def search_requirements(keyword, limit=50):
    return _query(DB_PATH,
        "SELECT RequirementType FROM Requirements WHERE RequirementType LIKE ? "
        "GROUP BY RequirementType ORDER BY RequirementType LIMIT ?",
        (f"%{keyword}%", limit))

def search_collections(keyword, limit=50):
    return _query(DB_PATH,
        "SELECT DISTINCT CollectionType FROM DynamicModifiers WHERE CollectionType LIKE ? "
        "ORDER BY CollectionType LIMIT ?",
        (f"%{keyword}%", limit))

def get_modifier_args(modifier_type):
    return _query(DB_PATH,
        "SELECT m.ModifierType, a.Name, a.Value, a.Type FROM ModifierArguments a "
        "JOIN Modifiers m ON a.ModifierId = m.ModifierId WHERE m.ModifierType = ? "
        "ORDER BY a.Name",
        (modifier_type,))

def search_dynamic_modifiers(keyword, limit=50):
    return _query(DB_PATH,
        "SELECT ModifierType, CollectionType, EffectType FROM DynamicModifiers "
        "WHERE ModifierType LIKE ? OR CollectionType LIKE ? OR EffectType LIKE ? "
        "ORDER BY ModifierType LIMIT ?",
        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))

def search_type_name(keyword, limit=50, lang="en"):
    """Search type names: game tables live in DebugGameplay.sqlite,
    LocalizedText in DebugLocalization.sqlite (ATTACH for the cross-DB join)."""
    kw = f"%{keyword}%"
    results = []
    language = "zh_Hans_CN" if lang == "zh" else "en_US"
    col_label = "Name_CN" if lang == "zh" else "Name_EN"

    tables = {
        "UNITS": ("UnitType", "Units"),
        "BUILDINGS": ("BuildingType", "Buildings"),
        "DISTRICTS": ("DistrictType", "Districts"),
        "CIVILIZATIONS": ("CivilizationType", "Civilizations"),
        "LEADERS": ("LeaderType", "Leaders"),
        "IMPROVEMENTS": ("ImprovementType", "Improvements"),
        "POLICIES": ("PolicyType", "Policies"),
        "TRAITS": ("TraitType", "Traits"),
    }

    conn = _connect(DB_PATH)
    try:
        conn.execute("ATTACH DATABASE ? AS loc", (LOC_DB_PATH,))
        for category, (col, table_name) in tables.items():
            rows = [dict(r) for r in conn.execute(
                f"SELECT t.{col} AS Type, l.Text AS {col_label} FROM main.{table_name} t "
                "JOIN loc.LocalizedText l ON t.Name = l.Tag "
                "WHERE l.Language = ? AND (t." + col + " LIKE ? OR l.Text LIKE ?) "
                "LIMIT ?",
                (language, kw, kw, limit))]
            for r in rows:
                r["Category"] = category
                r["Lang"] = lang
                results.append(r)
    finally:
        conn.close()

    return results[:limit]


def check_ids(type_ids):
    """Check whether candidate Types already exist in the game's Types table
    (DebugGameplay.sqlite). A hit = conflict for a NEW custom type."""
    placeholders = ", ".join("?" for _ in type_ids)
    rows = _query(DB_PATH,
        f"SELECT Type FROM Types WHERE Type IN ({placeholders}) ORDER BY Type",
        tuple(type_ids))
    existing = {r["Type"] for r in rows}
    report = []
    for t in type_ids:
        report.append({
            "Type": t,
            "Exists": t in existing,
            "Verdict": "CONFLICT (already a game built-in type)" if t in existing else "OK (no clash)",
        })
    return report


def print_results(title, items, fmt=str):
    if not items:
        print(f"No results found for {title}.")
        return
    print(f"=== {title} ({len(items)} results) ===")
    for i in items:
        print(fmt(i))
    print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Convenience CLI for SQLite queries.")
    parser.add_argument("--modifiertype", "-mt", help="Search ModifierTypes")
    parser.add_argument("--effect", "-e", help="Search Effects")
    parser.add_argument("--requirement", "-r", help="Search Requirements")
    parser.add_argument("--collection", "-c", help="Search Collections")
    parser.add_argument("--dynamic", "-d", help="Search DynamicModifiers")
    parser.add_argument("--args", "-a", metavar="MODIFIER_TYPE", help="Show ModifierType arguments")
    parser.add_argument("--type-name", "-tn", help="Search type names via DebugLocalization")
    parser.add_argument("--check-id", "-ci", nargs="+", metavar="TYPE",
        help="Check candidate Type ids against game built-in Types (hit = conflict)")
    parser.add_argument("--lang", choices=["en", "zh"], default="en",
        help="Output language for --type-name (default: en; zh for display to user)")
    parser.add_argument("--limit", "-l", type=int, default=50)
    parser.add_argument("--db", default=None,
        help="基础库路径（默认 database/DebugGameplay.sqlite；库不随仓库分发，缺失时见 database/README.md）")

    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)
    if args.db:
        _apply_db_override(args.db)
    _require_db()

    if args.modifiertype:
        r = search_modifiertypes(args.modifiertype, args.limit)
        print_results("ModifierTypes", r, lambda x: x["ModifierType"])
    if args.effect:
        r = search_effects(args.effect, args.limit)
        print_results("Effects", r, lambda x: x["EffectType"])
    if args.requirement:
        r = search_requirements(args.requirement, args.limit)
        print_results("Requirements", r, lambda x: x["RequirementType"])
    if args.collection:
        r = search_collections(args.collection, args.limit)
        print_results("Collections", r, lambda x: x["CollectionType"])
    if args.dynamic:
        r = search_dynamic_modifiers(args.dynamic, args.limit)
        print_results("DynamicModifiers", r,
            lambda x: f"{x['ModifierType']} | {x['CollectionType']} | {x['EffectType']}")
    if args.args:
        r = get_modifier_args(args.args)
        if r:
            print(f"=== Arguments for {args.args} ===")
            for a in r:
                print(f"  {a['Name']} = {a['Value']}  ({a['Type']})")
            print()
        else:
            print(f"No arguments found for '{args.args}'.")
    if args.type_name:
        r = search_type_name(args.type_name, args.limit, lang=args.lang)
        name_col = "Name_CN" if args.lang == "zh" else "Name_EN"
        print_results("Type Names", r,
            lambda x: f"[{x['Category']}] {x['Type']} | {'CN' if x['Lang'] == 'zh' else 'EN'}: {x[name_col]}")
    if args.check_id:
        r = check_ids(args.check_id)
        conflicts = [x for x in r if x["Exists"]]
        print(f"=== check-id ({len(r)} candidates, {len(conflicts)} conflicts) ===")
        for x in r:
            mark = "X" if x["Exists"] else " "
            print(f"  [{mark}] {x['Type']}: {x['Verdict']}")
        if conflicts:
            sys.exit(1)


if __name__ == "__main__":
    main()
