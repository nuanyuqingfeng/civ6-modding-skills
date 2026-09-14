# -*- coding: utf-8 -*-
"""全工程 SQL 执行排查 —— 抓「整条语句报废」类错误（非法转义 / 字符错位）。

为什么需要它（与 rgn_validate 互补）：
  - `rgn_validate` 查的是 **引用完整性**（悬空 ModifierId / Type / RequirementSetId）；
  - 本脚本查的是 **可执行性** —— 一条 `INSERT` 因 `\\'` 这类非法转义整条报废时，
    那批数据根本没进库，引用自然也不会悬空，`rgn_validate` 看不到。

  ★ 上一版漏报原因（务必保留这条教训）：`sqlite3.complete_statement` 对「未闭合字符串」
  **永不返回 True**，于是整条 INSERT 被吞进残留缓冲却报 OK。
  本版两道关：
    A. 整文件 `executescript` —— 非法转义这类字符错位会当场报错，并逐行试探定位；
    B. 逐语句执行 —— 统计「基础库缺表/列」导致的环境跳过，与真错误分开。

典型真实症状：中英文共用同一条 INSERT 时，英文行的 `'knight\\'s story!'`（应为 `''`）
让**整条语句报废** → 中文行也一起丢失 → 游戏按 LanguagePriorities 回退 en_US
→ **中文环境显示英文**。

用法：
    python check_sql_exec.py [--root <工程根目录>] [--base <基础库>]

参数：
    --root  工程根目录（默认当前工作目录）
    --base  基础库快照（默认 <本skill>/database/DebugGameplay.sqlite；原库只读，先复制到临时文件）

退出码：0 = 无语法错误；1 = 有语法错误（可用于 CI / 提交前钩子）。
"""
import os, shutil, sqlite3, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DB = os.path.normpath(os.path.join(HERE, '..', 'database', 'DebugGameplay.sqlite'))

ROOT = os.getcwd()
BASE = SKILL_DB
if '--root' in sys.argv:
    ROOT = sys.argv[sys.argv.index('--root') + 1]
if '--base' in sys.argv:
    BASE = sys.argv[sys.argv.index('--base') + 1]
ROOT = os.path.abspath(ROOT)

if not os.path.isfile(BASE):
    print('ERROR: 基础库不存在: %s' % BASE)
    sys.exit(2)

targets = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if any(x in dirpath for x in ('workspace', '.git', 'node_modules')):
        continue
    for fn in filenames:
        if fn.endswith('.sql') and '.bak' not in fn:
            targets.append(os.path.join(dirpath, fn))
targets.sort()

tmpfile = os.path.join(tempfile.gettempdir(), 'rgn_sqlcheck.sqlite')
shutil.copyfile(BASE, tmpfile)
con = sqlite3.connect(tmpfile)
con.execute('CREATE TABLE IF NOT EXISTS LocalizedText (Tag TEXT NOT NULL, Language TEXT NOT NULL, '
            'Text TEXT, PRIMARY KEY (Tag, Language))')
con.commit()

ENV_ERR = ('no such table', 'no such column', 'no such module', 'already exists',
           'has no column named', 'cannot modify', 'unable to open',
           # Types.Hash 由引擎自定义函数填充；普通 sqlite 下 DEFAULT 0 会让第二行起撞 UNIQUE
           'unique constraint failed: types.hash')


def classify(msg):
    low = msg.lower()
    if any(k in low for k in ENV_ERR):
        return 'env'
    if ('syntax error' in low or 'unrecognized token' in low or 'incomplete input' in low
            or 'near "' in low or 'unterminated' in low):
        return 'syntax'
    return 'other'


# 词内撇号：字母 ' 字母 —— SQL 里正确写法是 ''（两个单引号），\' 与单个 ' 都会让整条语句报废。
# 这是本项目最高频的「整条 INSERT 报废」成因，所以单独给出精确行号。
import re as _re
_APOS = _re.compile(r"[A-Za-z\u00C0-\u024F]'[A-Za-z\u00C0-\u024F]")


def scan_apostrophes(lines):
    """返回 [(行号, 该行片段)]，命中 SQL 未转义的词内撇号。"""
    out = []
    for i, l in enumerate(lines, 1):
        if _APOS.search(l):
            out.append((i, l.strip()[:150]))
    return out


print('待检查 SQL 文件: %d' % len(targets))
syntax, other, env, okfiles = [], [], 0, 0
apos_report = {}   # rel -> [(行号, 片段)]，仅在语法失败时填充

for p in targets:
    rel = os.path.relpath(p, ROOT)
    src = open(p, encoding='utf-8', newline='').read()
    lines = src.split('\n')
    failed = False
    try:
        con.executescript(src)
    except sqlite3.Error as e:
        kind = classify(str(e))
        # 逐行试探：注意「截断到语句中途」必然报 incomplete input / unterminated，
        # 那不是真错误，必须跳过；否则会把行号误报成语句首行（曾误报为 L3）。
        ln = 1
        for i in range(1, len(lines) + 1):
            try:
                con.executescript('\n'.join(lines[:i]))
            except sqlite3.Error as e2:
                low2 = str(e2).lower()
                if 'incomplete input' in low2 or 'unterminated' in low2:
                    continue
                if classify(str(e2)) == 'syntax':
                    ln = i
                    break
        rec = (rel, ln, str(e), lines[ln - 1].strip()[:150])
        if kind == 'syntax':
            syntax.append(rec)
            failed = True
            hits = scan_apostrophes(lines)
            if hits:
                apos_report[rel] = hits
        elif kind == 'other':
            other.append(rec)
            failed = True
        else:
            env += 1
    if not failed:
        okfiles += 1
    buf = ''
    for raw in lines:
        buf += raw + '\n'
        if sqlite3.complete_statement(buf):
            st = buf.strip()
            if st and not st.startswith('--'):
                try:
                    con.execute(st)
                except sqlite3.Error as e:
                    if classify(str(e)) == 'env':
                        env += 1
            buf = ''
con.close()
try:
    os.remove(tmpfile)
except Exception:
    pass

print('整文件执行通过: %d / %d' % (okfiles, len(targets)))
print('环境跳过语句（基础库缺表/列）: %d' % env)
print()
print('=== 语法错误 %d 条 ===' % len(syntax))
for rel, ln, msg, frag in syntax:
    print('  %s:%s\n     %s\n     %s' % (rel, ln, msg, frag))
if apos_report:
    print()
    print('=== ★ 未转义的词内撇号（最高频成因，指出真实行号）===')
    print("    SQL 字符串里的 ' 必须写成 ''（两个单引号）；\\' 与单个 ' 都会让整条 INSERT 报废。")
    for rel in sorted(apos_report):
        for ln, frag in apos_report[rel]:
            print('  %s:%s\n     %s' % (rel, ln, frag))
print()
print('=== 其它错误 %d 条 ===' % len(other))
for rel, ln, msg, frag in other[:40]:
    print('  %s:%s\n     %s\n     %s' % (rel, ln, msg, frag))
print()
print('结论:', 'PASS' if not syntax and not other else 'FAIL')
sys.exit(1 if (syntax or other) else 0)
