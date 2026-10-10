#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_schema_drift.py - guard the civ6-modding reference DB against
hand-edited schema drift.

Why this exists
---------------
`database/DebugGameplay.sqlite` is used by `rgn_validate_runner.mjs` as the
ground truth for reference-integrity checks. If the DB gains a column the game
does not have (e.g. the historical `DynamicModifiers.IsDlcDependency`), the
validator can no longer catch invalid mod SQL, and the error only shows up at
game load time as:

    ERROR: table DynamicModifiers has no column named IsDlcDependency

This script rebuilds the official schema from the installed game files and
compares it against the reference DB. Any structural drift -> exit 1.

Official sources (relative to the game install)
-----------------------------------------------
  Base/Assets/Gameplay/Data/Schema/01_GameplaySchema.sql
  DLC/Expansion1/Data/Expansion1_Schema.sql
  DLC/Expansion2/Data/Expansion2_Schema.sql
  Base/Assets/Gameplay/Data/Schema/Color_Tables.xml
  Base/Assets/Gameplay/Data/Schema/Diplomacy_Tables.xml
  Base/Assets/Gameplay/Data/Schema/Leader_Tables.xml

Usage
-----
  python database/scripts/audit_schema_drift.py
  python database/scripts/audit_schema_drift.py --game "F:/Steam/.../Sid Meier's Civilization VI"
  python database/scripts/audit_schema_drift.py --db database/DebugGameplay.sqlite --verbose

Exit codes: 0 = clean, 1 = structural drift, 2 = environment/setup problem.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DEFAULT_DB = os.path.join(SKILL_DIR, "database", "DebugGameplay.sqlite")
DEFAULT_GAME = r"F:\Steam\steamapps\common\Sid Meier's Civilization VI"

GAMEPLAY_SQL = [
    r"Base/Assets/Gameplay/Data/Schema/01_GameplaySchema.sql",
    r"DLC/Expansion1/Data/Expansion1_Schema.sql",
    r"DLC/Expansion2/Data/Expansion2_Schema.sql",
    # Runtime ColorManager schema: PlayerColors here carries Alt1/2/3Primary/Secondary
    # columns that Color_Tables.xml omits. Columns are merged as a union, so the
    # reference DB must satisfy both the XML schema and the runtime color schema.
    r"Base/Assets/Database/ColorManager.sql",
]
GAMEPLAY_XML = [
    r"Base/Assets/Gameplay/Data/Schema/Color_Tables.xml",
    r"Base/Assets/Gameplay/Data/Schema/Diplomacy_Tables.xml",
    r"Base/Assets/Gameplay/Data/Schema/Leader_Tables.xml",
]
CONSTRAINT_STARTS = ("PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT")
# Skill-owned annotation objects are intentionally not part of the official
# schema. They must never be named like a game table and must not leak columns
# into game tables.
SKILL_OWNED_PREFIXES = ("SkillAnnotation_",)
SKILL_OWNED_SUFFIXES = ("_Annotated",)


def is_skill_owned(name: str) -> bool:
    return name.startswith(SKILL_OWNED_PREFIXES) or name.endswith(SKILL_OWNED_SUFFIXES)


# ---------------------------------------------------------------- resolution
def resolve_game_dir(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value if os.path.isdir(cli_value) else None
    env = os.environ.get("CIV6_GAME_DIR")
    if env and os.path.isdir(env):
        return env
    paths_file = os.path.join(SKILL_DIR, "local_paths.json")
    if os.path.isfile(paths_file):
        try:
            data = json.load(open(paths_file, encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        for key in ("game", "gameDir", "P3", "game_install", "civ6", "gamePath"):
            val = data.get(key)
            if isinstance(val, str) and os.path.isdir(val):
                return val
    return DEFAULT_GAME if os.path.isdir(DEFAULT_GAME) else None


# ------------------------------------------------------------------- parsing
def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return re.sub(r"--[^\n]*", "", sql)


def split_top_level(body: str, sep: str = ","):
    parts, depth, cur, quote, i = [], 0, [], None, 0
    while i < len(body):
        c = body[i]
        if quote:
            cur.append(c)
            if c == quote:
                if i + 1 < len(body) and body[i + 1] == quote:
                    cur.append(body[i + 1])
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if c in "\"'`":
            quote = c
            cur.append(c)
        elif c == "(":
            depth += 1
            cur.append(c)
        elif c == ")":
            depth -= 1
            cur.append(c)
        elif c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    if cur:
        parts.append("".join(cur))
    return parts


CREATE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?'
    r'("([^"]+)"|\'([^\']+)\'|`([^`]+)`|\[([^\]]+)\]|(\w+))\s*\(', re.I)


def parse_sql_schema(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    text = strip_comments(text)
    for m in CREATE_RE.finditer(text):
        name = next(g for g in m.groups()[1:] if g is not None)
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        cols = []
        for seg in split_top_level(text[m.end():i]):
            head = re.match(
                r'^\s*("([^"]+)"|`([^`]+)`|\[([^\]]+)\]|\'([^\']+)\'|(\w+))', seg)
            if not head:
                continue
            col = next(g for g in head.groups()[1:] if g is not None)
            if col.upper() in CONSTRAINT_STARTS:
                continue
            if col not in cols:
                cols.append(col)
        out.setdefault(name, [])
        for c in cols:
            if c not in out[name]:
                out[name].append(c)
    return out


def parse_xml_schema(path: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    root = ET.parse(path).getroot()
    for table in root.iter("Table"):
        name = table.get("name")
        if not name:
            continue
        out.setdefault(name, [])
        for col in table.findall("Column"):
            cname = col.get("name")
            if cname and cname not in out[name]:
                out[name].append(cname)
    return out


def load_official(game_dir: str) -> dict[str, list[str]]:
    schema: dict[str, list[str]] = {}
    for rel in GAMEPLAY_SQL:
        path = os.path.join(game_dir, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        for table, cols in parse_sql_schema(open(path, encoding="utf-8", errors="replace").read()).items():
            entry = schema.setdefault(table, [])
            for c in cols:
                if c not in entry:
                    entry.append(c)
    for rel in GAMEPLAY_XML:
        path = os.path.join(game_dir, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        for table, cols in parse_xml_schema(path).items():
            entry = schema.setdefault(table, [])
            for c in cols:
                if c not in entry:
                    entry.append(c)
    return schema


# --------------------------------------------------------------------- diff
def main() -> int:
    ap = argparse.ArgumentParser(description="Civ6 reference-DB schema drift guard")
    ap.add_argument("--game", help="Civ6 install dir (default: local_paths.json / CIV6_GAME_DIR / known path)")
    ap.add_argument("--db", default=DEFAULT_DB, help="reference DB (default: database/DebugGameplay.sqlite)")
    ap.add_argument("--verbose", action="store_true", help="print per-table details")
    args = ap.parse_args()

    game_dir = resolve_game_dir(args.game)
    if not game_dir:
        print("[setup] Civ6 install not found. Pass --game <path> or set CIV6_GAME_DIR.", file=sys.stderr)
        return 2
    if not os.path.isfile(args.db):
        print("[setup] reference DB not found: %s" % args.db, file=sys.stderr)
        return 2

    try:
        official = load_official(game_dir)
    except (OSError, ET.ParseError) as exc:
        print("[setup] cannot read official schema: %s" % exc, file=sys.stderr)
        return 2

    db = sqlite3.connect(args.db)
    db_tables = [r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    db_cols = {}
    for t in db_tables:
        try:
            db_cols[t] = [r[1] for r in db.execute('PRAGMA table_info("%s")' % t.replace('"', '""'))]
        except sqlite3.Error:
            db_cols[t] = []

    print("Civ6 schema drift audit")
    print("  game install   : %s" % game_dir)
    print("  official tables: %d" % len(official))
    print("  reference DB   : %s (%d tables)" % (args.db, len(db_tables)))
    print()

    failures, warnings, skill_owned = [], [], []
    for t in db_tables:
        if t not in official:
            if is_skill_owned(t):
                skill_owned.append(t)
            else:
                failures.append("table %s: exists in reference DB but NOT in official gameplay schema" % t)
            continue
        extra = [c for c in db_cols[t] if c not in official[t]]
        missing = [c for c in official[t] if c not in db_cols[t]]
        if extra:
            failures.append("table %s: EXTRA column(s) %s (official: %s)"
                            % (t, ", ".join(extra), ", ".join(official[t])))
        if missing:
            failures.append("table %s: MISSING column(s) %s" % (t, ", ".join(missing)))

    for t in official:
        if t not in db_cols:
            warnings.append("official table %s is absent from the reference DB" % t)

    if args.verbose:
        for t in sorted(official):
            if t in db_cols:
                print("  [ok]   %-38s %d cols" % (t, len(db_cols[t])))
        for t in sorted(set(db_cols) - set(official)):
            print("  [extra] %-37s %d cols" % (t, len(db_cols[t])))

    ann_db = os.path.join(os.path.dirname(args.db), "source_index.sqlite")
    ann_rows = None
    if os.path.isfile(ann_db):
        try:
            adb = sqlite3.connect(ann_db)
            ann_rows = adb.execute("SELECT count(*) FROM dlc_dependency").fetchone()[0]
            adb.close()
        except sqlite3.Error:
            warnings.append("annotation mirror missing: source_index.sqlite / dlc_dependency")
    else:
        warnings.append("annotation mirror DB not found: %s" % ann_db)
    print("  skill-owned objects in reference DB: %s" % (", ".join(skill_owned) or "(none)"))
    print("  annotation mirror: source_index.sqlite / dlc_dependency (%s rows)"
          % ("?" if ann_rows is None else ann_rows))

    if failures:
        print("FAIL: %d structural drift item(s)" % len(failures))
        for f in failures:
            print("  - %s" % f)
    else:
        print("OK: reference DB matches the official gameplay schema (0 structural drift)")
    if warnings:
        print("\nWARN: %d official table(s) not present in this gameplay-only DB "
              "(front-end/modding tables are expected to be absent)" % len(warnings))
        for w in warnings:
            print("  - %s" % w)

    db.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
