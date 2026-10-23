# -*- coding: utf-8 -*-
"""取代对象的子表取料 —— 把被取代对象在基础库各处的行原样取出，供写入阶段逐表复刻。

为什么需要它：`BuildingReplaces` / `DistrictReplaces` / `UnitReplaces` 只登记取代映射，
被取代对象在各子表里的行**不会被引擎继承**。特色对象在某张子表里一行都没有时，
该子表承载的行为静默丢失、加载期零报错 —— 症状是特色建筑不享受原版的产出、伟人点数、
巨作槽、相邻加成，或建造资格判定缺项。

判据是「整类缺失」：被取代对象在某张表的某个主体列里有行、特色对象在同一位置零行。
数值不同不属缺陷（信仰 4 点取代 1 点是设计）。

计数在**快照**上做：把基础库复制到临时文件，再把工程 SQL 逐文件灌进去，
然后比对两侧行数。基础库本身不含工程行，直接在原库上计数会把每个特色对象都算成零行。

触发时机只有两处，其余时刻不跑：
  1. 本次写入的 SQL 里出现取代表 —— 写完映射、写子表之前跑一次 `--diff`；
  2. 用户点名「补全 xx 的全部表格」—— 用 `--object xx` 直接取原版行。
手动删除子表行属持久意图，本工具只报告，不恢复。

用法：
    python replacement_subtables.py <工程根> [--object TYPE] [--diff] [--sql] [--db <库>]

参数：
    --object  跳过工程取代映射解析，直接查该 Type 出现的全部位置
    --diff    只保留「被取代有行、特色零行」的项；有未覆盖项时退出码 1
    --sql     把行打成可照抄的 INSERT；映射模式下主体列换写成特色 Type
    --db      基础库（默认 <本skill>/database/DebugGameplay.sqlite）

退出码：0 = 无未覆盖项（或仅报告）；1 = `--diff` 下存在未覆盖项；2 = 参数或环境错误。

列的分类：列名以 `Prereq` 开头的属**反向引用**（该行的意思是"我要求某个对象存在"），
复刻它会把别的对象的门槛搬过来，所以只列出、不计入未覆盖项。
"""
import argparse
import os
import shutil
import sqlite3
import sys
import tempfile

import check_sql_antipatterns as csa

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DB = os.path.normpath(os.path.join(HERE, "..", "database", "DebugGameplay.sqlite"))

# 类型注册、文本与三张取代表不属子表内容，整表跳过
SKIP_TABLES = {"Types", "LocalizedText", "DistrictReplaces", "BuildingReplaces", "UnitReplaces"}

# 表名族前缀：`<前缀>...` 且列名以 Type 结尾时才算「该表的行挂在这个对象上」
SUBJECT_PREFIXES = ("Building", "District", "Unit", "Project", "Improvement")

# 少数子表用裸主体列而非 `<族>Type`；只登记这两张，其余带裸列的表
# （StartingBuildings / MajorStartingUnits / MutuallyExclusiveDistricts 等）是别人的表，
# 对象在那里只是被引用的值，复刻过去等于把起始配给与互斥关系搬错位置。
BARE_SUBJECTS = {"BuildingPrereqs": {"Building"}, "Unit_BuildingPrereqs": {"Unit"}}

# 基础库缺引擎专属表 / 前端表导致的执行错误，与项目缺陷无关
ENV_ERR = ("no such table", "no such column", "no such module", "already exists",
           "has no column named", "cannot modify", "unable to open",
           "unique constraint failed: types.hash")


def quote(val):
    """把单元格还原成 SQL 字面量。"""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return repr(val)
    return "'" + str(val).replace("'", "''") + "'"


def list_tables(con):
    return [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def list_columns(con, table):
    return [r[1] for r in con.execute('PRAGMA table_info("%s")' % table)]


def count_at(con, table, col, value):
    sql = 'SELECT COUNT(*) FROM "%s" WHERE "%s" = ?' % (table, col)
    return con.execute(sql, (value,)).fetchone()[0]


def is_subject(table, col):
    """该列是否把整行挂在这个对象上。

    `Building_YieldChanges.BuildingType` 这类（族前缀 + Type 后缀）算；
    `BuildingPrereqs.Building` / `Unit_BuildingPrereqs.Unit` 这两张裸列子表算。
    `ModifierArguments.Value`、`StartingBuildings.Building` 这类不算。
    """
    if col in BARE_SUBJECTS.get(table, ()):
        return True
    return col.endswith("Type") and table.startswith(SUBJECT_PREFIXES)


def find_refs(con, value):
    """返回 [(表, 列, 行数)]：该对象作为主体出现的全部位置。"""
    out = []
    for table in list_tables(con):
        if table in SKIP_TABLES:
            continue
        for col in list_columns(con, table):
            if not is_subject(table, col):
                continue
            n = count_at(con, table, col, value)
            if n:
                out.append((table, col, n))
    return out


def dump_rows(con, table, col, value, subject):
    """把命中行打成 INSERT 语句；`subject` 指定的主体列换写成它，其余列原样。"""
    cols = list_columns(con, table)
    sql = 'SELECT * FROM "%s" WHERE "%s" = ?' % (table, col)
    out = []
    for row in con.execute(sql, (value,)).fetchall():
        cells = []
        for name, cell in zip(cols, row):
            cells.append(quote(subject) if (subject and name == col) else quote(cell))
        out.append("INSERT INTO %s (%s) VALUES (%s);"
                   % (table, ", ".join(cols), ", ".join(cells)))
    return out


SKIP_DIRS = {"workspace", ".git", "Cooked", "node_modules"}


def project_sql(root):
    """列出工程内的 .sql。

    按**目录名**剪枝，不按整条路径的子串判断 —— 工程副本常常就落在
    `<解决方案根>/workspace/tmp/` 之下，按子串判断会把整棵副本一起漏掉。
    """
    paths = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(fn):
            if f.lower().endswith(".sql"):
                paths.append(os.path.join(dp, f))
    return sorted(paths)


def snapshot(base_db, sql_paths):
    """把基础库复制到临时文件并灌入工程 SQL，返回 (连接, 临时文件路径)。"""
    tmp = os.path.join(tempfile.gettempdir(), "rgn_subtables.sqlite")
    shutil.copyfile(base_db, tmp)
    con = sqlite3.connect(tmp)
    con.execute("CREATE TABLE IF NOT EXISTS LocalizedText (Tag TEXT NOT NULL, Language TEXT NOT NULL, "
                "Text TEXT, PRIMARY KEY (Tag, Language))")
    con.commit()
    env = 0
    for path in sql_paths:
        src = open(path, encoding="utf-8", errors="replace").read()
        try:
            con.executescript(src)
        except sqlite3.Error as e:
            if any(k in str(e).lower() for k in ENV_ERR):
                env += 1
            else:
                print("  ! 执行失败 %s: %s" % (os.path.basename(path), e))
    return con, tmp, env


def collect_mappings(root):
    """扫工程 SQL 取取代映射（复用 check_sql_antipatterns 的解析器）。"""
    return csa.collect_replacements(project_sql(root))


def show_object(con, value, want_sql):
    refs = find_refs(con, value)
    if not refs:
        print("基础库里没有值等于 %s 的行" % value)
        return
    print("=== %s 出现的全部位置 ===" % value)
    for table, col, n in refs:
        mark = "反向引用" if col.lower().startswith("prereq") else "主体列"
        print("  %-34s %-18s %5d  %s" % (table, col, n, mark))
        if want_sql and mark == "主体列":
            for stmt in dump_rows(con, table, col, value, None):
                print("    " + stmt)


def diff_mappings(con, mappings, want_diff, want_sql):
    """逐个映射比对行数，返回未覆盖项数量。"""
    missing = 0
    for uniq, (cat, old) in sorted(mappings.items()):
        refs = find_refs(con, old)
        if not refs:
            print("== %s ← %s（%s）：基础库里查不到该对象的子表行" % (uniq, old, cat))
            continue
        rows = []
        for table, col, n_old in refs:
            reverse = col.lower().startswith("prereq")
            n_new = count_at(con, table, col, uniq)
            if reverse:
                status = "反向引用"
            elif n_new:
                status = "已覆盖"
            else:
                status = "未覆盖"
                missing += 1
            rows.append((table, col, n_old, n_new, status))
        if want_diff:
            rows = [r for r in rows if r[4] == "未覆盖"]
        if not rows:
            continue
        print("== %s ← %s（%s）" % (uniq, old, cat))
        for table, col, n_old, n_new, status in rows:
            print("  %-34s %-18s 原版 %5d  特色 %5d  %s"
                  % (table, col, n_old, n_new, status))
            if want_sql and status == "未覆盖":
                for stmt in dump_rows(con, table, col, old, uniq):
                    print("    " + stmt)
    return missing


def main():
    ap = argparse.ArgumentParser(description="取代对象的子表取料")
    ap.add_argument("root", nargs="?", default=os.getcwd(), help="工程根目录")
    ap.add_argument("--object", help="直接查该 Type，跳过工程取代映射解析")
    ap.add_argument("--diff", action="store_true", help="只保留未覆盖项；有未覆盖项时退出码 1")
    ap.add_argument("--sql", action="store_true", help="输出可照抄的 INSERT 语句")
    ap.add_argument("--db", default=SKILL_DB, help="基础库（默认 skill 自带 DebugGameplay.sqlite）")
    args = ap.parse_args()

    if not os.path.isfile(args.db):
        print("ERROR: 基础库不存在: %s" % args.db)
        return 2

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: 目录不存在: %s" % root)
        return 2

    paths = project_sql(root)
    con, tmp, env = snapshot(args.db, paths)
    print("工程 SQL 文件: %d（环境性跳过 %d）" % (len(paths), env))
    try:
        if args.object:
            show_object(con, args.object, args.sql)
            return 0

        mappings = collect_mappings(root)
        print("取代映射条目: %d" % len(mappings))
        missing = diff_mappings(con, mappings, args.diff, args.sql)
        print()
        if args.diff:
            print("未覆盖项: %d" % missing)
        else:
            print("未覆盖项（仅统计主体列）: %d" % missing)
        return 1 if (args.diff and missing) else 0
    finally:
        con.close()
        os.remove(tmp)


if __name__ == "__main__":
    sys.exit(main())
