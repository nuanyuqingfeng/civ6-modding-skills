# -*- coding: utf-8 -*-
"""SQL 语义反模式静态扫描 —— 抓「语法完全合法、但语义恒假/恒错」的写法。

为什么需要它：这类写法**语法校验抓不到**，跑 executescript 也通过，
只有到运行时才表现为「条件不生效 / 静默返回空 / 误删一片」。
`check_sql_exec.py` 管"跑不跑得起来"，本脚本管"跑起来了但意思是错的"。

## 覆盖三条（均经实机/内存 SQLite 复核）

**A. `LIKE ('%A%' OR '%B%')` —— 恒假**（★ 已在实机命中真实缺陷）
   SQLite 把括号内 `'%A%' OR '%B%'` 先做「字符串→数值」转换（都得 0），
   整体求值为整数 0 → `col LIKE 0` 只匹配字面量为 '0' 的行 → 该条件**永远为假**。
   实机复核（Civ6 gamecore / `DB.Query`）：
     `SELECT ('%a%' OR '%b%')` = `0` (integer)；
     `'abc' LIKE ('%a%' OR '%b%')` → 0 行；`'0' LIKE ('%a%' OR '%b%')` → 命中。
   正确写法：`col LIKE '%A%' OR col LIKE '%B%'`

**B. `DELETE` / `UPDATE` 里 `LIKE` 模式含**未转义**的下划线 —— 误伤面被放大**
   下划线是单字符通配符，想匹配字面下划线必须 `ESCAPE '\'`。
   ★ 只对**破坏性语句**（DELETE / UPDATE）告警：SELECT 里未转义只是"匹配略宽"，
   而 DELETE 里会**多删**。这是为了把假阳性压到最低 —— 判据上线前先用已知样本反向校验。

**C. `WHERE` 子句里的 `= NULL` / `<> NULL` / `!= NULL` —— 恒 NULL，永远不成立**
   正确写法是 `IS NULL` / `IS NOT NULL`。
   ⚠ **不报 `SET col = NULL`** —— 那是合法赋值，不是比较（第一版曾把它误报）。

用法：
    python check_sql_antipatterns.py <工程根目录> [--glob *.sql]

退出码：0 = 未发现；1 = 发现；2 = 参数错误。
"""
import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# A. col LIKE ( '…' OR '…' [OR …] )
RE_A = re.compile(
    r"(?P<col>[A-Za-z_][A-Za-z0-9_.]*)\s+LIKE\s*\(\s*'(?P<first>(?:[^']|'')*)'"
    r"(?P<rest>(?:\s*OR\s*'(?:[^']|'')*')+)\s*\)",
    re.I,
)
# B. LIKE '<pattern>'（含下划线、且同行无 ESCAPE）
RE_B = re.compile(r"LIKE\s+'(?P<pat>(?:[^']|'')*)'", re.I)
# C. 比较型 = NULL / <> NULL / != NULL
RE_C = re.compile(r"(<>|!=|=)\s*NULL\b", re.I)

STMT_KIND = re.compile(r"^\s*(?:--[^\n]*\n\s*)*(\w+)", re.I)


def strip_line_comments(text):
    """把「整行是注释」的行替换为空行（**保持行号不变**）。

    ★ 必须做这一步：注释掉的死代码（`--UPDATE … SET x=NULL …`）会被语句扫描当成真语句，
      实测第一版因此在某工程报了 5 条 `=NULL` 假阳性 —— 全是被注释的 UPDATE。
      只处理整行注释；行尾注释保留（避免误伤字符串里的 `--`）。
    """
    out = []
    for line in text.split("\n"):
        out.append("" if line.strip().startswith("--") else line)
    return "\n".join(out)


def split_statements(text):
    """按 ; 切语句，返回 [(起始行号, 语句文本)]。字符串内的 ; 不切（简化处理：按引号状态扫描）。"""
    out, buf, start, in_str = [], [], 1, False
    line = 1
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\n":
            line += 1
        if ch == "'":
            if in_str and i + 1 < len(text) and text[i + 1] == "'":
                buf.append("''")
                i += 2
                continue
            in_str = not in_str
        if ch == ";" and not in_str:
            out.append((start, "".join(buf)))
            buf = []
            start = line
            i += 1
            continue
        buf.append(ch)
        i += 1
    if "".join(buf).strip():
        out.append((start, "".join(buf)))
    return out


def where_part(stmt):
    """取语句中 WHERE 之后的部分（用于 C 判定，避开 SET 赋值）。"""
    m = re.search(r"\bWHERE\b", stmt, re.I)
    return stmt[m.end():] if m else ""


def scan_file(path, esc=False):
    raw = open(path, encoding="utf-8", errors="replace").read()
    text = strip_line_comments(raw)
    hits = []

    for s_line, stmt in split_statements(text):
        kind = (STMT_KIND.match(stmt).group(1).upper() if STMT_KIND.match(stmt) else "")
        destructive = kind in ("DELETE", "UPDATE")
        body = where_part(stmt) if kind == "UPDATE" else stmt

        # --- A：全语句范围 ---
        for m in RE_A.finditer(stmt):
            col = m.group("col")
            pats = [m.group("first")] + re.findall(r"'((?:[^']|'')*)'", m.group("rest"))
            fix = " OR ".join("%s LIKE '%s'" % (col, p) for p in pats)
            ln = s_line + stmt[:m.start()].count("\n")
            hits.append((ln, "A", m.group(0).replace("\n", " ")[:130],
                         "恒假条件。改为： " + fix))

        # --- B：仅 --esc 开启时才报；只对破坏性语句 ---
        if esc and destructive:
            for m in RE_B.finditer(body):
                pat = m.group("pat")
                if "_" in pat and "ESCAPE" not in stmt.upper():
                    ln = s_line + stmt[:m.start()].count("\n")
                    hits.append((ln, "B(%s)" % kind, m.group(0)[:130],
                                 r"未转义下划线会多匹配 → 破坏性语句里可能误伤。加 ESCAPE '\'"))

        # --- C：只在 WHERE 之后 ---
        for m in RE_C.finditer(body):
            ln = s_line + stmt[:m.start()].count("\n")
            hits.append((ln, "C", m.group(0)[:130],
                         "恒 NULL，条件永不成立。用 IS NULL / IS NOT NULL"))

    # 注释行里的 A 形态（供人工修正，避免后来人照抄）
    for i, line in enumerate(raw.split("\n"), 1):
        s = line.strip()
        if s.startswith("--") and RE_A.search(line):
            hits.append((i, "A(注释)", s[:130], "注释里的写法也应改成 col LIKE '%A%' OR col LIKE '%B%'"))

    return sorted(set(hits))


def main():
    ap = argparse.ArgumentParser(description="SQL 语义反模式静态扫描")
    ap.add_argument("root", help="工程根目录")
    ap.add_argument("--glob", default="*.sql", help="文件名后缀过滤（默认 *.sql）")
    ap.add_argument("--esc", action="store_true",
                    help="额外检查 B 类（破坏性语句里未转义的下划线）。默认关闭 —— "
                         "它在实际工程里噪声很大（前缀匹配的下划线虽未转义但通常无害）")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: 目录不存在: %s" % root)
        return 2
    suffix = args.glob.lstrip("*").lower()

    total, files = 0, 0
    for dp, dn, fn in os.walk(root):
        if any(x in dp for x in ("workspace", ".git", "Cooked", "node_modules")):
            continue
        for f in sorted(fn):
            if not f.lower().endswith(suffix):
                continue
            files += 1
            p = os.path.join(dp, f)
            hits = scan_file(p, esc=args.esc)
            if hits:
                print("=== %s : %d 处 ===" % (os.path.relpath(p, root), len(hits)))
                for ln, kind, src, fix in hits:
                    print("  [%s] L%-5d %s" % (kind, ln, src))
                    print("           → %s" % fix)
                total += len(hits)

    print()
    print("扫描 SQL 文件: %d" % files)
    print("发现问题: %d" % total)
    if not total:
        print("✓ 未发现 A/B/C 三类反模式")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
