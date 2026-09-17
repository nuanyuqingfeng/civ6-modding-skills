#!/usr/bin/env python3
"""Civ6 API Query Tool — 主源 api.sqlite（含子项 sub_func_name 与运行时核验字段），
api_enhanced.json 仅作 --show 的示例/注释富化源（sqlite 无 exampleCode/notes 列）。

用法:
  python query_api.py --search <关键词>              # 搜 表名/函数名/子项名/真名/id（子项一并命中）
  python query_api.py --search <关键词> --sub-only   # 只看"本身是子项"的条目
  python query_api.py --show Player.GetReligion      # 父项详情 + 列出其全部子项
  python query_api.py --show Player.GetReligion.GetHolyCityID   # 精确查子项
  python query_api.py --object Player                # 列出整张表
  python query_api.py --object Player.GetReligion    # 列出该父方法下的全部子项
  python query_api.py --search Key --verified        # 只看已核验（另有 --suspect / --pending）
"""

import argparse
import json
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SQLITE_PATH = os.path.join(SKILL_ROOT, "database", "api.sqlite")
JSON_PATH = os.path.join(SKILL_ROOT, "reference", "api_enhanced.json")

# verify_status 三档（2026-09-08 FireTuner 全量实测口径）
VS_VERIFIED = "已核验"
VS_SUSPECT = "存疑"
VS_PENDING = ""  # 空 = 本次无法实测，标记留空（见 audit_priority='待补测'）

INVOKE_NOTE = {
    "Dot (Global)": "通过命名空间调用：Object.Method()",
    "Colon (Instance)": "通过实例调用：instance:Method()",
}


# ──────────────────────────── 数据加载 ────────────────────────────

def load_db():
    """打开 api.sqlite（主源，4857 条）。"""
    if not os.path.exists(SQLITE_PATH):
        sys.exit("api.sqlite 不存在：%s" % SQLITE_PATH)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_json_index():
    """id -> JSON 富化条目。JSON 是 sqlite 的子集（3435/4857），按 id 对齐，缺失则无富化。"""
    index = {}
    try:
        with open(JSON_PATH, encoding="utf-8") as f:
            objs = json.load(f)["objects"]
    except Exception:
        return index
    for _obj, methods in objs.items():
        for mid, m in methods.items():
            if isinstance(m, dict):
                index[m.get("id", mid)] = m
    return index


# ──────────────────────────── 字段呈现 ────────────────────────────

def verify_tag(row):
    """核验标记；空状态在 sqlite 中表现为 verify_status=''（待补测）。"""
    vs = row["verify_status"] or ""
    if vs:
        return vs
    return "待补测" if (row["audit_priority"] or "") == "待补测" else ""


def is_sub(row):
    """是否为子项（挂在其父方法下的二级/三级方法）。"""
    return bool((row["sub_func_name"] or "").strip())


def leaf_name(row):
    """子项的运行时真名优先（true_name 修正过拼接损坏的情况）。"""
    return (row["true_name"] or "").strip() or (row["sub_func_name"] or "").strip()


def full_path(row):
    """完整调用路径：Table.Func 或 Table.Func.Sub。"""
    tbl = (row["table_name"] or "").strip()
    fn = (row["func_name"] or "").strip()
    sub = leaf_name(row)
    if sub:
        return "%s.%s.%s" % (tbl, fn, sub)
    return "%s.%s" % (tbl, fn)


def display_name(row):
    """人类可读调用式，按 invoke 决定 : 还是 . 连接。"""
    tbl = (row["table_name"] or "").strip()
    fn = (row["func_name"] or "").strip()
    sub = leaf_name(row)
    head = "instance:%s()" % fn if row["invoke"] == "Colon (Instance)" else "%s.%s()" % (tbl, fn)
    return head + ": %s()" % sub if sub else head


def split_flat(flat):
    """把 args_flat/returns_flat 的 'name:::type, name:::type' 解析成 [(name, type)]。

    注意：返回类型里可能含花括号元组（如 '{type: number, player: number, id: number} componentIDs:::table'），
    其中的逗号不是分隔符 —— 故只在花括号深度为 0 时按逗号切分。
    """
    if not flat:
        return []
    items, buf, depth = [], [], 0
    for ch in flat:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            items.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    items.append("".join(buf))

    out = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        parts = item.split(":::")
        out.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""))
    return out


def build_signature(row, enrich=None):
    """签名：优先用 JSON 的现成 signature（覆盖 3435 条），否则由 args/returns_flat 拼。"""
    if enrich and enrich.get("signature"):
        return enrich["signature"]
    fn = (row["func_name"] or "").strip()
    label = leaf_name(row) or fn
    args = split_flat(row["args_flat"])
    rets = split_flat(row["returns_flat"])
    argtxt = ", ".join("%s: %s" % (n, t.lstrip(":")) if t else n for n, t in args)
    sig = "%s(%s)" % (label, argtxt)
    if rets:
        n, t = rets[0]
        sig += (" -> %s: %s" % (n, t.lstrip(":"))) if t else (" -> %s" % n)
    return sig


# ──────────────────────────── 查询 ────────────────────────────

def match_verify(row, verify):
    if not verify:
        return True
    vs = row["verify_status"] or ""
    if verify == "verified":
        return vs == VS_VERIFIED
    if verify == "suspect":
        return vs == VS_SUSPECT
    if verify == "pending":
        return vs == VS_PENDING
    return True


def search(conn, keyword, type_filter=None, verify=None, sub_only=False, limit=30):
    """搜 表名 / 函数名 / 子项名 / 真名 / id —— 子项与父项都命中。"""
    kw = "%" + keyword + "%"
    sql = (
        "SELECT * FROM api_functions WHERE ("
        " table_name LIKE ? OR func_name LIKE ? OR sub_func_name LIKE ?"
        " OR ifnull(true_name,'') LIKE ? OR id LIKE ?)"
    )
    params = [kw] * 5
    if type_filter:
        sql += " AND type = ?"
        params.append(type_filter)
    sql += " ORDER BY table_name, func_name, sub_func_name"
    rows = [r for r in conn.execute(sql, params) if match_verify(r, verify)]
    if sub_only:
        rows = [r for r in rows if is_sub(r)]

    # 相关性排序：叶子名精确 > 叶子名前缀 > 其余；同级再按路径
    k = keyword.lower()

    def score(r):
        leaf = leaf_name(r).lower() or (r["func_name"] or "").lower()
        if leaf == k:
            return (0, full_path(r))
        if leaf.startswith(k):
            return (1, full_path(r))
        if k in leaf:
            return (2, full_path(r))
        return (3, full_path(r))

    rows.sort(key=score)
    return rows[:limit]


def find_exact(conn, table, func, sub=None):
    """按 表 / 函数 / (可选)子项 精确定位一条。"""
    if sub:
        rows = conn.execute(
            "SELECT * FROM api_functions WHERE table_name=? AND func_name=? AND"
            " (sub_func_name=? OR ifnull(true_name,'')=?)",
            (table, func, sub, sub)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM api_functions WHERE table_name=? AND func_name=? AND"
            " (sub_func_name IS NULL OR sub_func_name='')",
            (table, func)).fetchall()
    return rows[0] if rows else None


def sub_rows(conn, table, func, verify=None):
    rows = conn.execute(
        "SELECT * FROM api_functions WHERE table_name=? AND func_name=? AND"
        " sub_func_name IS NOT NULL AND sub_func_name<>'' ORDER BY sub_func_name",
        (table, func)).fetchall()
    return [r for r in rows if match_verify(r, verify)]


def parse_path(text):
    """把用户输入解析为 (table, func, sub)；容忍 : 与 () 写法。"""
    t = text.replace("()", "")
    t = t.replace(":", ".")
    parts = [p for p in t.split(".") if p]
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], parts[1], None
    return (parts[0] if parts else ""), None, None


def resolve_show(conn, text):
    """按 Table.Func[.Sub] 定位；子项名允许只给一部分（包含匹配兜底）。"""
    table, func, sub = parse_path(text)
    if not func:
        return None
    row = find_exact(conn, table, func, sub)
    if row or not sub:
        return row
    # 兜底：sub 只给了一部分（长子项名手打易漏），按包含匹配取最短者
    rows = conn.execute(
        "SELECT * FROM api_functions WHERE table_name=? AND func_name=? AND"
        " (sub_func_name LIKE ? OR ifnull(true_name,'') LIKE ?)"
        " ORDER BY length(sub_func_name)",
        (table, func, "%" + sub + "%", "%" + sub + "%")).fetchall()
    return rows[0] if rows else None


# ──────────────────────────── 输出 ────────────────────────────

HDR = "%-22s %-28s %-34s %-8s %-16s %-8s"


def print_list(rows):
    if not rows:
        print("No results.")
        return
    print(HDR % ("Table", "Function", "Sub(子项)", "Type", "Availability", "核验"))
    print("-" * 122)
    for r in rows:
        avail = r["availability"] or ""
        if r["corrected_from"]:
            avail += "(原%s)" % r["corrected_from"]
        print(HDR % (
            (r["table_name"] or "")[:22],
            (r["func_name"] or "")[:28],
            (leaf_name(r) or "-")[:34],
            (r["type"] or "")[:8],
            avail[:16],
            verify_tag(r)[:8],
        ))
    print("\n%d result(s). 详查：--show <Table.Func.Sub>（子项名也可直接 --search）" % len(rows))


def print_detail(row, enrich):
    print("\n" + "=" * 64)
    print("  %s" % full_path(row))
    print("=" * 64)
    print("  Table:       %s" % (row["table_name"] or ""))
    if is_sub(row):
        print("  父方法:      %s.%s" % (row["table_name"] or "", row["func_name"] or ""))
        print("  子项:        %s" % leaf_name(row))
        if row["true_name"] and row["true_name"] != row["sub_func_name"]:
            print("  真名修正:    %s -> %s" % (row["sub_func_name"], row["true_name"]))
    print("  Type:        %s" % (row["type"] or ""))
    print("  Availability: %s" % (row["availability"] or ""))
    if row["corrected_from"]:
        print("  已修正:      availability %s -> %s" % (row["corrected_from"], row["availability"]))
    print()
    print("  Signature:   %s" % build_signature(row, enrich))
    print()
    # sqlite 的扁平参数/返回（JSON 无此条时的兜底）
    if not enrich:
        args = split_flat(row["args_flat"])
        if args:
            print("  Args:        %s" % ", ".join(
                "%s %s" % (n, t) if t else n for n, t in args))
        rets = split_flat(row["returns_flat"])
        if rets:
            print("  Returns:     %s" % ", ".join(
                "%s %s" % (n, t) if t else n for n, t in rets))
        if args or rets:
            print()

    invoke = row["invoke"] or ""
    if invoke:
        print("  Invoke:      %s" % invoke)
        note = INVOKE_NOTE.get(invoke)
        if note:
            print("  Invoke Note: %s" % note)
        print()

    # JSON 富化（sqlite 无 exampleCode / notes / 结构化参数描述）
    if enrich:
        args = enrich.get("argsA") or []
        if args:
            print("  Args:")
            for a in args:
                desc = a.get("description") or ""
                print("    %-18s %-10s %s" % (a.get("name", ""), a.get("type", ""), desc))
            print()
        rets = enrich.get("returns") or []
        if rets:
            print("  Returns:")
            for a in rets:
                desc = a.get("description") or ""
                print("    %-18s %-10s %s" % (a.get("name", ""), a.get("type", ""), desc))
            print()

    # ---- 运行时核验 ----
    tag = verify_tag(row)
    if tag or row["runtime_gp"] or row["runtime_ui"]:
        print("  Verification:")
        print("    状态:      %s" % (tag or "（未标记）"))
        if row["verify_at"]:
            print("    核验日期:  %s   范围: %s" % (row["verify_at"], row["verify_scope"] or ""))
        print("    实测类型:  GP=%s  UI=%s" % (row["runtime_gp"] or "-", row["runtime_ui"] or "-"))
        if row["true_path"]:
            print("    运行时真身: %s" % row["true_path"])
        if row["suspect_type"]:
            print("    存疑类型:  %s（优先级 %s）" % (row["suspect_type"], row["audit_priority"] or ""))
        note = row["verify_note"]
        if note:
            print("    备注:      %s" % note)
        print()

    if enrich:
        example = enrich.get("exampleCode")
        if example:
            print("  Example:")
            for line in example.split("\n"):
                print("    %s" % line)
            print()
        for line in (enrich.get("notes") or []):
            print("  Note:        %s" % line)
        if enrich.get("notes"):
            print()


def print_subs(rows):
    if not rows:
        return
    print("  ── 子项（%d 个）──" % len(rows))
    print("  " + HDR % ("Table", "Function", "Sub(子项)", "Type", "Availability", "核验"))
    for r in rows:
        print("  " + HDR % (
            (r["table_name"] or "")[:22],
            (r["func_name"] or "")[:28],
            (leaf_name(r) or "-")[:34],
            (r["type"] or "")[:8],
            (r["availability"] or "")[:16],
            verify_tag(r)[:8],
        ))


# ──────────────────────────── 入口 ────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Civ6 API Query Tool（主源 api.sqlite；子项与父项均可查）")
    parser.add_argument("--search", "-s", help="搜索：表名/函数名/子项名/真名/id")
    parser.add_argument("--show", "-S", help="详查：Table.Func 或 Table.Func.Sub")
    parser.add_argument("--object", "-o", help="列出一张表；或 Table.Func 列出其子项")
    parser.add_argument("--type", "-t", choices=["ACTION", "QUERY", "CONTEXT", "OBJECT"],
                        help="按类型过滤（配合 --search）")
    parser.add_argument("--sub-only", action="store_true", help="--search 时只看子项条目")
    parser.add_argument("--limit", "-l", type=int, default=30)
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--verified", action="store_const", const="verified", dest="verify_filter",
                   help="只看已核验")
    g.add_argument("--suspect", action="store_const", const="suspect", dest="verify_filter",
                   help="只看存疑（文档自身有误）")
    g.add_argument("--pending", action="store_const", const="pending", dest="verify_filter",
                   help="只看待补测")
    args = parser.parse_args()

    if not any([args.search, args.show, args.object]):
        parser.print_help()
        return

    conn = load_db()
    enrich_index = load_json_index()

    if args.search:
        rows = search(conn, args.search, args.type, args.verify_filter,
                      args.sub_only, args.limit)
        print_list(rows)

    if args.show:
        row = resolve_show(conn, args.show)
        if not row:
            print("Not found: %s" % args.show)
            print("提示：子项需给全路径，或用 --search <子项名> 定位。")
            return
        table = row["table_name"]
        func = row["func_name"]
        print_detail(row, enrich_index.get(row["id"]))
        if not is_sub(row):
            print_subs(sub_rows(conn, table, func, args.verify_filter))

    if args.object:
        table, func, _ = parse_path(args.object)
        if func:
            base = find_exact(conn, table, func)
            if not base:
                print("Not found: %s" % args.object)
                return
            print_detail(base, enrich_index.get(base["id"]))
            print_subs(sub_rows(conn, table, func, args.verify_filter))
        else:
            rows = conn.execute(
                "SELECT * FROM api_functions WHERE table_name=? ORDER BY func_name, sub_func_name",
                (table,)).fetchall()
            rows = [r for r in rows if match_verify(r, args.verify_filter)]
            if not rows:
                print("Table '%s' not found or empty. 可用表名：" % table)
                names = [r[0] for r in conn.execute(
                    "SELECT DISTINCT table_name FROM api_functions ORDER BY 1")]
                width = max(len(n) for n in names) + 2
                for i in range(0, len(names), 3):
                    print("  " + "".join(n.ljust(width) for n in names[i:i + 3]).rstrip())
                return
            print("\n=== %s (%d functions) ===" % (table, len(rows)))
            print_list(rows)


if __name__ == "__main__":
    main()
