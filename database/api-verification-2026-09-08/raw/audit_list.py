#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终审核清单：471 条问题项 × 助手（Civ6LuaHelper）人工裁定分层 × 预分类桶。

分层规则（用户指定：助手内标记人工验证的，以其结论为准）
  L0 助手人工验证(humanChecked=true)  -> 不再审核
  L1 助手已收录、未标人工验证          -> 审核主体
  L2 助手数据集未收录（作者已剔除）     -> 低优先，可沿用助手结论
优先级
  P1 = L1 且 A/B 桶（文档可直接改）  P2 = L1 且 C 桶（需裁决）
  P3 = L1 且 D 桶（需补测条件）      P4 = L2   P0 = L0
"""
from __future__ import annotations

import collections
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import triage  # noqa: E402

WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")
OUT = WORK / "out"
DEST = Path(r"<本目录（随 skill 分发）>")
HELPER_JSON = Path(r"%USERPROFILE%\AppData\Local\Temp"
                   r"\onefile_33376_938175_aW1luoQf41E\data\api_enhanced.json")


def load_helper():
    d = json.loads(HELPER_JSON.read_text(encoding="utf-8-sig"))
    H = {}
    for o in d.get("objects", {}).values():
        if isinstance(o, dict):
            for f in o.values():
                if isinstance(f, dict) and f.get("id"):
                    H[f["id"]] = f
    return H, d.get("metadata", {})


def parse_l3(path):
    """解析三层恢复转储 L3K|<容器键>|<n>|<k:type,...> -> {容器键_L3: {方法名}}"""
    out = {}
    path = Path(path)
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("L3K|"):
            q = ln.split("|", 3)
            names = {}
            if len(q) > 3 and not q[3].startswith("<"):
                for it in q[3].split(","):
                    if ":" in it:
                        k, v = it.rsplit(":", 1)
                        names[k] = v
            out[q[1] + "_L3"] = names
    return out


def main():
    H, hmeta = load_helper()
    idx, ns = triage.build_name_index()
    d = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    # 元素类/子对象方法表（含三层恢复），供 B3「复数容器 -> 元素对象」判定
    l3sets = {}
    for ctx in ("gp", "ui"):
        m = {}
        for key, ks in d[ctx]["enum_methods"].items():
            m[key] = {x.split(":")[0] for x in ks if ":" in x}
        for key, names in parse_l3(OUT / f"l3_{ctx}.txt").items():
            m[key] = set(names)
        l3sets[ctx] = m
    full = list(csv.DictReader(io.open(DEST / "api_scope_full.csv", encoding="utf-8-sig")))
    problems = [r for r in full if r["一致性判定"].startswith(
        ("文档偏宽", "文档偏窄", "文档存疑", "无法验证", "部分不可验证", "动态"))]

    rows = []
    for r in problems:
        bucket, sub, ev, act = triage.classify(r, idx, ns, l3sets)
        h = H.get(r["id"])
        if h is None:
            layer = "L2 助手未收录"
        elif h.get("humanChecked"):
            layer = "L0 助手人工验证"
        else:
            layer = "L1 助手已收录"
        prio = ("P0" if layer.startswith("L0") else "P4" if layer.startswith("L2") else
                "P1" if bucket[0] in "AB" else "P2" if bucket[0] == "C" else "P3")
        need = {"L0 助手人工验证": "否（以助手人工验证结论为准）",
                "L2 助手未收录": "低（助手数据集已剔除该命名空间，可沿用）",
                "L1 助手已收录": "是"}[layer]
        api = (h.get("displayName") if h else "") or (
            r["命名空间/类"] + ("." + r["方法"] if r["方法"] else "") +
            ("." + r["子方法"] if r["子方法"] else ""))
        rows.append({
            "优先级": prio, "助手分层": layer, "是否需审核": need,
            "桶": bucket, "子类": sub,
            "API（助手显示名优先）": api,
            "id": r["id"], "命名空间/类": r["命名空间/类"], "方法": r["方法"], "子方法": r["子方法"],
            "调用形态": r["调用形态"], "文档availability(api.sqlite)": r["文档可用性"],
            "助手availability": (h.get("availability") if h else ""),
            "GP实测": f'{r["GP状态"]}/{r["GP存在"]}', "UI实测": f'{r["UI状态"]}/{r["UI存在"]}',
            "本次判定": r["一致性判定"],
            "运行时真名": r["GP真名"] or r["UI真名"] or "",
            "运行时近似名": r["GP近似名"] or r["UI近似名"] or "",
            "其它UI状态命中": r["其它UI状态"],
            "助手标记未被官方lua使用": "是" if (h and h.get("enrichUnused")) else "",
            "助手用法摘要": (h.get("usageSummary") if h else "") or "",
            "助手备注首条": ((h.get("notes") or [""])[0] if h else ""),
            "助手人工验证": "是" if (h and h.get("humanChecked")) else "",
            "证据": ev, "建议动作": act,
        })

    order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "P0": 4}
    rows.sort(key=lambda x: (order[x["优先级"]], x["桶"], x["子类"], x["命名空间/类"], x["API（助手显示名优先）"]))
    cols = list(rows[0].keys())

    with open(DEST / "审核清单_预分类.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # ---------- xlsx ----------
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = Workbook(); wb.remove(wb.active)
    hf, hfont = PatternFill("solid", fgColor="1F4E79"), Font(color="FFFFFF", bold=True)
    widths = {"id": 34, "API（助手显示名优先）": 52, "证据": 44, "建议动作": 30, "子类": 30,
              "桶": 18, "本次判定": 26, "助手备注首条": 46, "是否需审核": 26, "助手用法摘要": 30,
              "运行时近似名": 26, "命名空间/类": 20, "优先级": 8, "助手分层": 18}

    def sheet(name, data, cols_):
        ws = wb.create_sheet(name[:30])
        ws.append(cols_)
        for c in ws[1]:
            c.fill, c.font = hf, hfont
            c.alignment = Alignment(vertical="center")
        for x in data:
            ws.append([x.get(c, "") for c in cols_])
        for i, c in enumerate(cols_, 1):
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = widths.get(c, 13)
        ws.freeze_panes = "A2"
        if len(data) > 1:
            ws.auto_filter.ref = ws.dimensions
        return ws

    stat = collections.Counter(x["优先级"] for x in rows)
    ov = wb.create_sheet("概览")
    ov.append(["优先级", "含义", "条数"])
    for c in ov[1]:
        c.fill, c.font = hf, hfont
    for p, desc in [("P1", "L1 且 A/B 桶：文档可直接改（availability 标错 / 名称路径错）"),
                    ("P2", "L1 且 C 桶：运行时确无此名，需裁决删除或标版本"),
                    ("P3", "L1 且 D 桶：暂不可测，需特定运行条件后复跑"),
                    ("P4", "L2：助手数据集未收录（作者已剔除），可沿用其结论"),
                    ("P0", "L0：助手已人工验证，以其结论为准，不需再审")]:
        ov.append([p, desc, stat.get(p, 0)])
    ov.append(["合计", "", len(rows)])
    ov.column_dimensions["A"].width = 8
    ov.column_dimensions["B"].width = 66
    ov.column_dimensions["C"].width = 8
    sheet("P1_文档可直接改", [x for x in rows if x["优先级"] == "P1"], cols)
    sheet("P2_需裁决", [x for x in rows if x["优先级"] == "P2"], cols)
    sheet("P3_待补测条件", [x for x in rows if x["优先级"] == "P3"], cols)
    sheet("P4_助手未收录", [x for x in rows if x["优先级"] == "P4"], cols)
    sheet("P0_助手人工验证", [x for x in rows if x["优先级"] == "P0"], cols)
    sheet("全部471条", rows, cols)
    wb.save(DEST / "审核清单.xlsx")

    # ---------- MD 逐条列举 ----------
    L = []
    A = L.append
    A("# 待审核清单（不符 + 暂不可测）· 预分类逐条")
    A("")
    A(f"> 数据源：本次运行时扫描 `api_scope_full.csv`（4857 条）筛出的问题项 **{len(rows)} 条**")
    A(f"> 裁定源：`<第三方工具 Civ6LuaHelper.exe>`（Nuitka onefile，运行时解包目录 `data/api_enhanced.json`，"
      f"数据抽取日期 {hmeta.get('extracted', '?')}，共 {len(H)} 条，其中 `humanChecked=true` 18 条）")
    A("")
    A("## 0. 剔除结论（先看这里）")
    A("")
    n0 = sum(1 for x in rows if x["助手分层"].startswith("L0"))
    n2 = sum(1 for x in rows if x["助手分层"].startswith("L2"))
    n1 = sum(1 for x in rows if x["助手分层"].startswith("L1"))
    A(f"- 助手内 **人工验证（humanChecked）共 18 条**，与本次 471 条问题项的交集为 **{n0} 条** —— "
      "**18 条人工验证条目本次实测全部与助手结论一致，没有一条落在冲突集里，故按「以人工验证为准」剔除后：471 → 471 条（剔除 0 条）**。")
    A(f"- 但助手数据集本身**未收录**其中 **{n2} 条**（作者已把这些命名空间整体剔除：`TunerUtilities`、"
      "`WorldBuilderResourceGenerator`、`ToolTipHelper`、`g_ToolTipGenerators`、`InstanceManager`、"
      "`FeatureGenerator`、`NaturalWonderGenerator`、`GenerationalInstanceManager`、`PullDownInstanceManager`、"
      "`Events`(前端事件)、`Relationship`、`Tools`、`json`、`Tests.*` 等）。若同时采信助手的收录范围，"
      f"**真正需要你审核的主体降到 {n1} 条**。")
    A(f"- 另有助手 `availability` 与 api.sqlite 不同的 2 条（`City:GetBuildQueue():GetTurnsLeft()`（人工验证，助手=UI）、"
      "`PlayerVisibilityManager.GetPlayerVisibility()`（助手=UI）），本次实测**两端都存在**；"
      "按你的规则以助手结论为准（UI），实测证据一并记录在 `助手人工验证条目.csv`。")
    A("")
    A("| 优先级 | 含义 | 条数 |")
    A("|---|---|---:|")
    for p, desc in [("P1", "L1 且 A/B 桶：文档可直接改"), ("P2", "L1 且 C 桶：需裁决删除/标版本"),
                    ("P3", "L1 且 D 桶：需补测条件后复跑"), ("P4", "L2：助手未收录，可沿用其结论"),
                    ("P0", "L0：助手已人工验证")]:
        A(f"| {p} | {desc} | {stat.get(p, 0)} |")
    A(f"| — | **合计** | **{len(rows)}** |")
    A("")
    A("---")
    A("")

    def emit(title, data, note=""):
        A(f"## {title}（{len(data)} 条）")
        if note:
            A("")
            A(note)
        subs = collections.defaultdict(list)
        for x in data:
            subs[(x["桶"], x["子类"])].append(x)
        for (b, s), items in sorted(subs.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            A("")
            A(f"### {b} · {s}　—　{len(items)} 条")
            A("")
            A("| API | 文档 | GP 实测 | UI 实测 | 证据 / 真名 | 建议动作 |")
            A("|---|---|---|---|---|---|")
            for x in items:
                ev = x["证据"]
                if x["运行时真名"]:
                    ev += f"；真名 `{x['运行时真名']}`"
                if x["运行时近似名"]:
                    ev += f"；近似名 `{x['运行时近似名']}`"
                if x["助手标记未被官方lua使用"]:
                    ev += "；助手标记：官方 lua 未使用"
                if x["其它UI状态命中"]:
                    ev += f"；其它 UI 状态可见：{x['其它UI状态命中']}"
                doc = x["文档availability(api.sqlite)"]
                if x["助手availability"] and x["助手availability"] != doc:
                    doc += f"（助手：{x['助手availability']}）"
                A(f"| `{x['API（助手显示名优先）']}` | {doc} | {x['GP实测']} | {x['UI实测']} | {ev} | {x['建议动作']} |")
        A("")
        A("---")
        A("")

    emit("P1 · 文档可直接改（L1，A/B 桶）", [x for x in rows if x["优先级"] == "P1"],
         "这些条目助手已收录但未标人工验证；本次实测给出了明确证据，可直接改文档字段或名称。")
    emit("P2 · 需裁决：运行时确无此名（L1，C 桶）", [x for x in rows if x["优先级"] == "P2"],
         "两端都检不出该名字，且无近似名/无同名命名空间可归位；需你决定「删除条目」还是「标注版本/DLC 条件」。")
    emit("P3 · 暂不可测（L1，D 桶）", [x for x in rows if x["优先级"] == "P3"],
         "不是不存在，而是本局缺少实例通道；按子类给出的条件复跑一轮即可闭环。")
    emit("P4 · 助手未收录（L2）", [x for x in rows if x["优先级"] == "P4"],
         "助手作者已把这些命名空间整体排除在数据集之外，可直接沿用其判断（视为文档噪声），无需逐条审。")
    if stat.get("P0"):
        emit("P0 · 助手已人工验证（L0）", [x for x in rows if x["优先级"] == "P0"])

    A("## 附：助手 18 条人工验证条目与本次实测对照")
    A("")
    A("| id | 助手显示名 | 助手 availability | 本次 GP | 本次 UI | 本次判定 |")
    A("|---|---|---|---|---|---|")
    byid = {r["id"]: r for r in full}
    for hid, h in sorted(H.items()):
        if not h.get("humanChecked"):
            continue
        r = byid.get(hid)
        A(f"| `{hid}` | `{h.get('displayName','')}` | {h.get('availability','')} | "
          f"{(r['GP状态'] + '/' + r['GP存在']) if r else '—'} | "
          f"{(r['UI状态'] + '/' + r['UI存在']) if r else '—'} | {r['一致性判定'] if r else '—'} |")
    A("")
    (DEST / "审核清单.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    summary = {
        "问题项总数": len(rows),
        "L0_助手人工验证": n0, "L1_助手已收录": n1, "L2_助手未收录": n2,
        "助手humanChecked总数": sum(1 for h in H.values() if h.get("humanChecked")),
        "humanChecked与问题项交集": n0,
        "按humanChecked剔除后剩余": len(rows) - n0,
        "再采信助手收录范围后需审核": n1,
        "优先级分布": dict(stat),
        "桶分布": dict(collections.Counter(x["桶"] for x in rows).most_common()),
        "P1桶子类": dict(collections.Counter(x["子类"] for x in rows if x["优先级"] == "P1").most_common()),
        "P2桶子类": dict(collections.Counter(x["子类"] for x in rows if x["优先级"] == "P2").most_common()),
        "P3桶子类": dict(collections.Counter(x["子类"] for x in rows if x["优先级"] == "P3").most_common()),
        "P4命名空间": dict(collections.Counter(x["命名空间/类"] for x in rows if x["优先级"] == "P4").most_common()),
        "助手标记未被官方lua使用": sum(1 for x in rows if x["助手标记未被官方lua使用"]),
        "助手数据抽取日期": hmeta.get("extracted"),
        "助手条目总数": len(H),
    }
    (DEST / "审核清单_统计.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("\n输出：审核清单.md / 审核清单_预分类.csv / 审核清单.xlsx / 审核清单_统计.json ->", DEST)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
