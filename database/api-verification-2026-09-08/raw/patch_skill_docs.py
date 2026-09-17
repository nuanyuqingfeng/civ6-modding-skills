#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 API 核验字段写进 skill 文档与查询工具（保持各文件原有换行风格与编码）。

- SKILL.md（CRLF）：二问查询块 / 铁律补注 / 数据查询表 / 数据库文件表 / 新增「API 核验字段」小节
- database/scripts/query_api.py（LF）：列表与详情显示核验标记 + --verified/--suspect/--pending 过滤
"""
from __future__ import annotations

import pathlib
import sys

SKILL = pathlib.Path(r"%USERPROFILE%\.agents\skills\civ6-modding")


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def eol_of(s):
    return "\r\n" if "\r\n" in s else "\n"


def to_eol(text, eol):
    return text.replace("\r\n", "\n").replace("\n", eol)


def patch_skill_md():
    p = SKILL / "SKILL.md"
    s = read(p)
    eol = eol_of(s)
    n0 = len(s)

    # 1) 二问查询块
    old = to_eol("""       需要示例/注释 → grep "FuncName" reference/api_enhanced.json
```""", eol)
    new = to_eol("""       需要示例/注释 → grep "FuncName" reference/api_enhanced.json
       需要「运行时是否真有 / UI 还是 GP」→ 看 verify_status + verify_scope + runtime_gp/runtime_ui（见「API 核验字段」）
```""", eol)
    assert old in s, "patch1 anchor missing"
    s = s.replace(old, new, 1)

    # 2) 铁律后补注
    old2 = to_eol("""**铁律：严禁凭经验猜测 API 名称或参数** — `database\\api.sqlite` 有 5075 个函数，猜错即返工。""", eol)
    new2 = to_eol("""**铁律：严禁凭经验猜测 API 名称或参数** — `database\\api.sqlite` 有 4857 行 API，猜错即返工。

> **核验优先（2026-09-08 FireTuner 全量实测已实装）**：`verify_status='已核验'` 3256 行可放心引用；
> `='存疑'` 1434 行是**文档自身不对**（availability 标错 / 名称路径错 / 运行时确无此名 / CodeBuddy 文档转储），
> 必须按 `verify_note`、`true_name`、`true_path` 改用真身，勿照抄；
> `=''`（留空）167 行是**本次无法实测**（缺实例通道），不代表有错，也别当已验证。""", eol)
    assert old2 in s, "patch2 anchor missing"
    s = s.replace(old2, new2, 1)

    # 3) 数据查询表
    old3 = to_eol("""| API 参数详情 | `SELECT a.* FROM api_args a JOIN api_functions f ON ...` (database\\api.sqlite) |""", eol)
    new3 = to_eol("""| API 参数详情 | `SELECT a.* FROM api_args a JOIN api_functions f ON ...` (database\\api.sqlite) |
| API 运行时是否真有 / UI-GP 范围 | `SELECT id,availability,verify_status,verify_scope,runtime_gp,runtime_ui,true_path FROM api_functions WHERE func_name LIKE '%Key%'` |
| 只取已核验 API | `... WHERE verify_status='已核验' AND availability IN ('Both','UI')` |
| 查存疑项与真身 | `SELECT id,availability,suspect_type,true_name,true_path,verify_note FROM api_functions WHERE verify_status='存疑' AND table_name='X'` |
| 命令行查（含核验标记） | `python database/scripts/query_api.py --search Key [--verified|--suspect|--pending]` |""", eol)
    assert old3 in s, "patch3 anchor missing"
    s = s.replace(old3, new3, 1)

    # 4) 数据库文件表 + 新增小节
    old4 = to_eol("""| `database/api.sqlite` | 1.5 MB | Lua API (5075 函数) |
| `database/DebugLocalization.sqlite` | 64.9 MB | 中英文文本 |
| `database/DebugConfiguration.sqlite` | — | FrontEnd 配置数据 |
""", eol)
    new4 = to_eol("""| `database/api.sqlite` | 2.5 MB | Lua API（4857 行；含 2026-09-08 FireTuner 实测核验列，见下节） |
| `database/DebugLocalization.sqlite` | 64.9 MB | 中英文文本 |
| `database/DebugConfiguration.sqlite` | — | FrontEnd 配置数据 |

### API 核验字段（2026-09-08 FireTuner 全量实测 · UI/GP 范围存在性）

对 `api.sqlite` 全部 4857 行在**运行中的对局**里逐条做过存在性验证（GP=`GameCore_Tuner`、UI=`InGame`，
另在 12 个其它 UI 状态复查；手法为 `loadstring`+`pcall` **只索引不调用**），结果已实装进本 skill。

| `verify_status` | 含义 | 行数 | 怎么用 |
|---|---|---|---|
| `已核验` | 实测过关（与文档 availability 一致），或 P1 已实装修正 / 已核出真身 | 3256 | 可直接引用 |
| `存疑` | **文档自身不对**：availability 标错、名称/路径错、运行时确无此名、CodeBuddy 文档转储 | 1434 | 按 `verify_note` + `true_name`/`true_path` 改用真身；未删除任何条目 |
| `''` 留空 | **本次无法实测**（缺实例通道或事件动态代理），既不判过关也不挂嫌疑 | 167 | 待具备条件复测（外交会话/未读通知/已任命总督/世界生成器/输入回调/地图钉/自由城市/Fractal） |

新增列（`api_functions`）：`verify_status` `verify_scope` `verify_note` `verify_at` `runtime_gp` `runtime_ui`
`audit_priority` `suspect_type` `corrected_from` `true_name` `true_path`

- `verify_scope`：实测范围 = 双端 / 仅GP / 仅UI / 双端未见 / 含不可判
- `runtime_gp`、`runtime_ui`：实测类型（`function`/`table`/`userdata`/`string`/`nil`/`ERR`/`CF`）；
  `ERR` = 命名空间或实例在该上下文根本不存在，`nil` = 容器可达但无此成员
- `audit_priority`：`P1`（已实装）/ `P2`（需裁决）/ `P4`（Civ6LuaHelper 未收录）/ `转储` / `待补测`
- `corrected_from`：**已实装修正的 53 条 availability 原值**（Both→GamePlay 28、UI→Both 20、Both→UI 5）
- `true_name`（44 条）/ `true_path`（7 条）：文档名有误时的运行时真名与真身路径
  （例：`Player:GetUnits():SetMilitaryFormation` 真身 `Unit:SetMilitaryFormation()`；
  `Map.GetImprovementBuilder` 真身全局 `ImprovementBuilder`；`Player:SetScoringScenario` 实为 `SetScoringScenario1/2/3`）

`reference/api_enhanced.json`（5.1 MB）同步标记：已核验 → `humanChecked:true` + `verifiedAt`/`verifiedScope`/
`runtimeGP`/`runtimeUI` + `[核验]` 备注行（3214 条）；存疑 → `suspect:true` + `suspectType`/`suspectPriority`
+ `[存疑]` 备注行（76 条）；无法实测 → 仅 `pendingTest:true` + `pendingReason`，**不挂核验/存疑标记、不加备注行**（143 条）。
`Civ6LuaHelper.exe` 内置的 18 条 `humanChecked` 已并入（另记 `helperHumanChecked`/`helperAvailability` 留痕）。

> ⚠ 唯一一条人工结论与实测冲突：`City:GetBuildQueue():GetTurnsLeft()`（助手人工验证 = UI，本次实测 GP/UI 两端都存在）。
> 按实测保留 `Both`，冲突详情写在该行 `verify_note`，需要改回 UI 时以人工结论为准即可。

完整报告与逐条清单：桌面 `Civ6_API_UI-GP范围验证_20260908\\`
（`API范围验证报告.md` · `审核清单.xlsx/md/csv`（P1/P2/P3/P4 分档） · `GP_UI方法面差异.csv` · `raw\\` 原始回传与脚本）
""", eol)
    assert old4 in s, "patch4 anchor missing"
    s = s.replace(old4, new4, 1)

    write(p, s)
    print(f"SKILL.md 已更新：{n0:,} -> {len(s):,} 字符（EOL={'CRLF' if eol == chr(13)+chr(10) else 'LF'}）")


def patch_query_api():
    p = SKILL / "database" / "scripts" / "query_api.py"
    s = read(p)
    eol = eol_of(s)
    n0 = len(s)

    def R(old, new):
        nonlocal s
        o, nw = to_eol(old, eol), to_eol(new, eol)
        assert o in s, f"anchor missing: {old[:60]!r}"
        s = s.replace(o, nw, 1)

    R('''def search(objs, keyword, type_filter=None):
    kw = keyword.lower()
    results = []
    for obj_name, methods in objs.items():
        for mid, m in methods.items():
            if not isinstance(m, dict):
                continue
            if type_filter and m.get("type") != type_filter:
                continue''',
      '''def verify_tag(m):
    """核验标记：已核验(humanChecked) / 存疑(suspect) / 待补测(pendingTest) / 空。"""
    if m.get("humanChecked"):
        return "已核验"
    if m.get("suspect"):
        return "存疑"
    if m.get("pendingTest"):
        return "待补测"
    return ""


def match_verify(m, verify):
    if not verify:
        return True
    return verify_tag(m) == {"verified": "已核验", "suspect": "存疑", "pending": "待补测"}[verify]


def search(objs, keyword, type_filter=None, verify=None):
    kw = keyword.lower()
    results = []
    for obj_name, methods in objs.items():
        for mid, m in methods.items():
            if not isinstance(m, dict):
                continue
            if type_filter and m.get("type") != type_filter:
                continue
            if not match_verify(m, verify):
                continue''')

    R('''    print(f"{'Object':22s} {'Function':30s} {'Type':10s} {'Availability':15s}")
    print("-" * 80)
    for obj_name, mid, m in results:
        func = m.get("functionA", "")
        typ = m.get("type", "")
        avail = m.get("availability", "")
        print(f"{obj_name:22s} {func:30s} {typ:10s} {avail:15s}")''',
      '''    print(f"{'Object':22s} {'Function':30s} {'Type':10s} {'Availability':15s} {'核验':8s}")
    print("-" * 90)
    for obj_name, mid, m in results:
        func = m.get("functionA", "")
        typ = m.get("type", "")
        avail = m.get("availability", "")
        if m.get("availabilityCorrectedFrom"):
            avail += f"(原{m['availabilityCorrectedFrom']})"
        print(f"{obj_name:22s} {func:30s} {typ:10s} {avail:15s} {verify_tag(m):8s}")''')

    R('''    notes = m.get("notes")
    if notes:
        print(f"  Notes:       {notes}\\n")''',
      '''    # ---- 运行时核验（2026-09-08 FireTuner 全量实测）----
    tag = verify_tag(m)
    if tag or m.get("runtimeGP") or m.get("runtimeUI"):
        print("  Verification:")
        print(f"    状态:      {tag or '（未标记）'}")
        if m.get("verifiedAt"):
            print(f"    核验日期:  {m['verifiedAt']}   范围: {m.get('verifiedScope', '')}")
        print(f"    实测类型:  GP={m.get('runtimeGP', '-')}  UI={m.get('runtimeUI', '-')}")
        if m.get("availabilityCorrectedFrom"):
            print(f"    已修正:    availability {m['availabilityCorrectedFrom']} -> {m.get('availability')}")
        if m.get("trueName"):
            print(f"    运行时真名: {m['trueName']}")
        if m.get("truePath"):
            print(f"    运行时真身: {m['truePath']}")
        if m.get("suspectType"):
            print(f"    存疑类型:  {m['suspectType']}（优先级 {m.get('suspectPriority', '')}）")
        if m.get("pendingReason"):
            print(f"    待补测:    {m['pendingReason']}")
        if m.get("helperHumanChecked"):
            print(f"    助手人工验证: 是（Civ6LuaHelper availability={m.get('helperAvailability', '')}）")
        print()

    notes = m.get("notes")
    if notes:
        for line in notes:
            print(f"  Note:        {line}")
        print()''')

    R('''        print(f"\\n=== {args.object} ({len(methods)} functions) ===")
        print(f"{'Function':35s} {'Type':10s} {'Availability':15s}")
        print("-" * 65)
        for mid, m in methods:
            func = m.get("functionA", mid)
            typ = m.get("type", "")
            avail = m.get("availability", "")
            print(f"{func:35s} {typ:10s} {avail:15s}")''',
      '''        print(f"\\n=== {args.object} ({len(methods)} functions) ===")
        print(f"{'Function':35s} {'Type':10s} {'Availability':15s} {'核验':8s}")
        print("-" * 75)
        for mid, m in methods:
            if not match_verify(m, args.verify_filter):
                continue
            func = m.get("functionA", mid)
            typ = m.get("type", "")
            avail = m.get("availability", "")
            print(f"{func:35s} {typ:10s} {avail:15s} {verify_tag(m):8s}")''')

    R('''    parser.add_argument("--limit", "-l", type=int, default=30)
    args = parser.parse_args()''',
      '''    parser.add_argument("--limit", "-l", type=int, default=30)
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--verified", action="store_const", const="verified", dest="verify_filter",
                   help="只看已核验（humanChecked，实测过关/已修正）")
    g.add_argument("--suspect", action="store_const", const="suspect", dest="verify_filter",
                   help="只看存疑（文档自身有误：availability/名称/路径/确无此名/文档转储）")
    g.add_argument("--pending", action="store_const", const="pending", dest="verify_filter",
                   help="只看待补测（本次无法实测，标记留空）")
    args = parser.parse_args()''')

    R('''        results = search(objs, args.search, args.type)''',
      '''        results = search(objs, args.search, args.type, args.verify_filter)''')

    write(p, s)
    print(f"query_api.py 已更新：{n0:,} -> {len(s):,} 字符（EOL={'CRLF' if eol == chr(13)+chr(10) else 'LF'}）")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    patch_skill_md()
    patch_query_api()
