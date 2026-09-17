#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 scan.py 的运行时探测结果与 api.sqlite 文档清单合并，产出 CSV + 中文报告。

判定模型（只判存在性）
----------------------
每行 API 在 GP(gamecore) / UI(ingame) 各得一个状态：
  function/table/userdata/number/string/boolean/thread -> 存在
  nil   -> 容器可达但成员不存在（= 该上下文不提供）
  ERR   -> 索引失败：命名空间不存在 / 无实例 / 子对象未解析
  CF    -> 表达式无法编译（CodeBuddyFuncsRaw 的 C++ 签名串）
再与文档 availability(Both/UI/GamePlay) 比对，给出一致性判定。
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
import time
import collections
from pathlib import Path

WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")
OUT = WORK / "out"
API_DB = Path(r"%USERPROFILE%\.agents\skills\civ6-modding\database\api.sqlite")
GAMEPLAY_DB = Path(r"%USERPROFILE%\.agents\skills\civ6-modding\database\DebugGameplay.sqlite")
DESKTOP = Path(r"<作者机桌面>")

EXIST = {"function", "table", "userdata", "number", "string", "boolean", "thread"}


def san(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def load():
    d = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    meta = json.loads((OUT / "scan_meta.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(str(API_DB))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("select * from api_functions")]
    con.close()
    gcon = sqlite3.connect(str(GAMEPLAY_DB))
    dbt = [r[0] for r in gcon.execute("select name from sqlite_master where type='table' order by name")]
    gcon.close()
    return d, meta, rows, dbt


def parse_subs(lines):
    out = {}
    for ln in lines:
        if not ln.startswith("SUB|"):
            continue
        p = ln.split("|")
        # SUB|<Class>.<Parent>|<how>|<type or nil>[|pairs=..|ix=..]
        out[p[1]] = {"how": p[2], "type": p[3], "pairs": p[4] if len(p) > 4 else "",
                     "ix": p[5] if len(p) > 5 else ""}
    return out


def expr_for(r):
    """与 scan.build_plan 保持一致的表达式推导。"""
    tbl, fn, sub = r["table_name"], r["func_name"], r["sub_func_name"]
    dot = r["invoke"].startswith("Dot")
    if dot:
        if not fn:
            if r["type"] == "QUERY" and r["id"].startswith("Q-GameInfo"):
                return "GameInfo." + tbl, None, "gameinfo"
            return tbl, "GameInfo." + tbl, "namespace"
        e = ".".join([tbl] + [p for p in (fn, sub) if p])
        return e, tbl, "dot"
    if sub:
        return ("__SC.C_%s_P_%s.%s" % (san(tbl), san(fn), sub),
                "__SC.C_%s_P_%s" % (san(tbl), san(fn)), "colon-sub")
    if fn:
        return ("__SC.C_%s.%s" % (san(tbl), fn), "__SC.C_%s" % san(tbl), "colon")
    return "__SC.C_%s" % san(tbl), None, "colon-obj"


def dynamic_surfaces(d):
    """哨兵探测：哪些事件面会自动生成任意名（存在性检查对其无效）。"""
    out = {}
    for ctx in ("gp", "ui"):
        s = set()
        for expr, st in d["dynamic_sentinel"][ctx].items():
            base = expr.split(".")[0]
            if st in ("table",):
                s.add(base)
        out[ctx] = s
    return out


def evaluate(r, probe, clsres, subs, dyn):
    """返回 (status, exists, note)。exists: True/False/None(无法验证)"""
    expr, container, kind = expr_for(r)
    st = probe.get(expr, "NOPROBE")
    tbl = r["table_name"]

    # 事件动态代理
    if tbl in dyn:
        return st, None, "动态代理：任意名均返回 table，存在性不可判"

    if kind == "gameinfo":
        if st in EXIST:
            return st, True, "GameInfo 子表可达"
        return st, False, "GameInfo 无此表"

    if kind == "namespace":
        if st in EXIST:
            return st, True, "命名空间存在"
        alt = probe.get("GameInfo." + tbl)
        if alt in EXIST:
            return st, False, f"运行时全局不存在（但 GameInfo.{tbl} 可达）"
        return st, False, "命名空间在该上下文不存在"

    if kind == "dot":
        base_st = probe.get(container, "NOPROBE")
        if base_st not in EXIST:
            return st, False, f"命名空间 {container} 在该上下文不存在"
        if st in EXIST:
            return st, True, ""
        if st == "CF":
            return st, None, "表达式不可编译（文档为 C++ 签名串）"
        return st, False, "命名空间存在但无此成员"

    # colon / colon-sub / colon-obj
    cls = tbl
    if container is None:
        cont_st = st
    else:
        cont_st = probe.get(container, "NOPROBE")
    res = clsres.get(cls, "?")
    if kind == "colon-sub":
        key = f"{san(cls)}.{san(r['func_name'])}"
        # subs 的 key 用的是 san 后的类名/父名
        info = subs.get(key) or subs.get(f"{cls}.{r['func_name']}")
        if cont_st not in EXIST:
            if res.startswith("none"):
                return st, None, f"类 {cls} 无实例（{res}）"
            why = info["how"] if info else "unresolved"
            return st, None, f"父对象未解析（{why}）——子方法不可验证"
        if st in EXIST:
            return st, True, f"父对象经 {info['how'] if info else '?'} 解析"
        return st, False, "父对象存在但无此子方法"
    # colon / colon-obj
    if res.startswith("none"):
        return st, None, f"类 {cls} 在该上下文无实例可检（{res}）"
    if cont_st not in EXIST and kind == "colon":
        return st, None, f"类 {cls} 实例缺失"
    if st in EXIST:
        return st, True, f"经 {res} 检出"
    if st == "CF":
        return st, None, "表达式不可编译（文档为 C++ 签名串）"
    return st, False, f"经 {res} 检查：无此方法"


def consistency(doc, gp_ok, ui_ok):
    """doc: Both/UI/GamePlay；gp_ok/ui_ok: True/False/None"""
    if gp_ok is None and ui_ok is None:
        return "无法验证"
    if doc == "Both":
        if gp_ok and ui_ok:
            return "一致"
        if gp_ok is False and ui_ok is False:
            return "文档偏宽：双端均未见"
        if gp_ok is False:
            return "文档偏宽：GP 未见"
        if ui_ok is False:
            return "文档偏宽：UI 未见"
        return "部分不可验证"
    if doc == "UI":
        if ui_ok and gp_ok is False:
            return "一致"
        if ui_ok and gp_ok:
            return "文档偏窄：GP 亦可见"
        if ui_ok is False:
            return "文档存疑：UI 未见"
        if ui_ok and gp_ok is None:
            return "一致（GP 侧不可验证）"
        return "部分不可验证"
    if doc == "GamePlay":
        if gp_ok and ui_ok is False:
            return "一致"
        if gp_ok and ui_ok:
            return "文档偏窄：UI 亦可见"
        if gp_ok is False:
            return "文档存疑：GP 未见"
        if gp_ok and ui_ok is None:
            return "一致（UI 侧不可验证）"
        return "部分不可验证"
    return "?"


def main():
    d, meta, rows, dbt = load()
    dyn = dynamic_surfaces(d)
    parsed = {}
    for ctx in ("gp", "ui"):
        parsed[ctx] = {
            "probe": d[ctx]["probe"],
            "clsres": d[ctx]["class_resolution"],
            "subs": parse_subs(d[ctx]["sub_lines"]),
            "dyn": dyn[ctx],
        }

    stamp = time.strftime("%Y%m%d")
    dest = DESKTOP / f"Civ6_API_UI-GP范围验证_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    # ---------------- 明细 ----------------
    detail = []
    for r in rows:
        expr, container, kind = expr_for(r)
        rec = {
            "id": r["id"], "类型": r["type"], "命名空间/类": r["table_name"],
            "方法": r["func_name"], "子方法": r["sub_func_name"] or "",
            "调用形态": r["invoke"], "文档可用性": r["availability"],
            "来源": r["source"], "参数": r["args_flat"], "返回": r["returns_flat"],
            "探测表达式": expr, "路径类别": kind,
        }
        for ctx, label in (("gp", "GP"), ("ui", "UI")):
            p = parsed[ctx]
            st, ok, note = evaluate(r, p["probe"], p["clsres"], p["subs"], p["dyn"])
            rec[f"{label}状态"] = st
            rec[f"{label}存在"] = {True: "是", False: "否", None: "不可判"}[ok]
            rec[f"{label}备注"] = note
            rec[f"_{ctx}_ok"] = ok
        rec["一致性判定"] = consistency(r["availability"], rec["_gp_ok"], rec["_ui_ok"])
        both = (rec["_gp_ok"] is True, rec["_ui_ok"] is True)
        rec["实际范围"] = ("双端" if both == (True, True) else
                       "仅GP" if both == (True, False) else
                       "仅UI" if both == (False, True) else
                       "双端未见" if both == (False, False) else "含不可判")
        detail.append(rec)

    cols = ["id", "类型", "命名空间/类", "方法", "子方法", "调用形态", "文档可用性", "来源",
            "路径类别", "探测表达式", "GP状态", "GP存在", "GP备注", "UI状态", "UI存在", "UI备注",
            "实际范围", "一致性判定", "参数", "返回"]

    def write_csv(path, recs, columns):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            for rec in recs:
                w.writerow(rec)

    write_csv(dest / "api_scope_full.csv", detail, cols)
    mism = [r for r in detail if r["一致性判定"] not in ("一致", "无法验证", "部分不可验证",
                                                         "一致（GP 侧不可验证）", "一致（UI 侧不可验证）")]
    write_csv(dest / "api_scope_文档与运行时不符.csv", mism, cols)
    unver = [r for r in detail if r["一致性判定"] in ("无法验证", "部分不可验证")]
    write_csv(dest / "api_scope_无法验证.csv", unver, cols)

    # ---------------- 命名空间汇总 ----------------
    ns = collections.defaultdict(lambda: collections.Counter())
    nsdoc = {}
    for rec in detail:
        k = rec["命名空间/类"]
        nsdoc[k] = rec["文档可用性"]
        ns[k]["总数"] += 1
        ns[k]["GP存在"] += rec["GP存在"] == "是"
        ns[k]["UI存在"] += rec["UI存在"] == "是"
        ns[k]["GP不可判"] += rec["GP存在"] == "不可判"
        ns[k]["UI不可判"] += rec["UI存在"] == "不可判"
        ns[k]["双端未见"] += rec["实际范围"] == "双端未见"
        ns[k][rec["一致性判定"]] += 1
        ns[k]["调用形态"] = rec["调用形态"]
    nsrows = []
    for k in sorted(ns, key=lambda x: -ns[x]["总数"]):
        c = ns[k]
        nsrows.append({
            "命名空间/类": k, "调用形态": c["调用形态"], "文档可用性": nsdoc[k], "条目数": c["总数"],
            "GP存在": c["GP存在"], "UI存在": c["UI存在"],
            "GP不可判": c["GP不可判"], "UI不可判": c["UI不可判"],
            "仅GP": c["GP存在"] - c["UI存在"] if c["GP存在"] >= c["UI存在"] else 0,
            "双端未见": c["双端未见"],
            "一致": c["一致"], "文档偏窄": c["文档偏窄：GP 亦可见"] + c["文档偏窄：UI 亦可见"],
            "文档偏宽": c["文档偏宽：双端均未见"] + c["文档偏宽：GP 未见"] + c["文档偏宽：UI 未见"],
            "文档存疑": c["文档存疑：UI 未见"] + c["文档存疑：GP 未见"],
            "无法验证": c["无法验证"] + c["部分不可验证"],
        })
    write_csv(dest / "命名空间汇总.csv", nsrows, list(nsrows[0].keys()))

    # ---------------- GameInfo 库表可达性 ----------------
    gi = []
    for t in dbt:
        e = "GameInfo." + t
        gi.append({"库表": t,
                   "GP": d["gp"]["probe"].get(e, "NOPROBE"),
                   "UI": d["ui"]["probe"].get(e, "NOPROBE")})
    write_csv(dest / "GameInfo库表可达性.csv", gi, ["库表", "GP", "UI"])

    # ---------------- CodeBuddy 归属面 ----------------
    cbrows = []
    for label, key in (("CodeBuddyFuncs", "codebuddyfuncs"), ("CodeBuddyFuncsRaw(归一化)", "raw_normalized")):
        hits_ui = d["codebuddy"]["ui"][key]
        hits_gp = d["codebuddy"]["gp"][key]
        names = d["codebuddy_names"] if key == "codebuddyfuncs" else d["codebuddy_raw_norm"]
        for n in names:
            cbrows.append({"清单": label, "名称": n,
                           "UI命中面": ", ".join(sorted({expr.rsplit(".", 1)[0] for expr in hits_ui if expr.endswith("." + n)})),
                           "GP命中面": ", ".join(sorted({expr.rsplit(".", 1)[0] for expr in hits_gp if expr.endswith("." + n)}))})
    write_csv(dest / "CodeBuddy归属面.csv", cbrows, ["清单", "名称", "UI命中面", "GP命中面"])

    # ---------------- GP/UI 方法面差异（枚举转储） ----------------
    diffrows = []
    for key in sorted(set(d["gp"]["enum_methods"]) | set(d["ui"]["enum_methods"])):
        gk = d["gp"]["enum_methods"].get(key, [])
        uk = d["ui"]["enum_methods"].get(key, [])
        gn = {x.split(":")[0] for x in gk if x and not x.startswith("<")}
        un = {x.split(":")[0] for x in uk if x and not x.startswith("<")}
        if not gn and not un:
            continue
        diffrows.append({"对象/命名空间": key, "GP方法数": len(gn), "UI方法数": len(un),
                         "共有": len(gn & un), "仅GP": len(gn - un), "仅UI": len(un - gn),
                         "仅GP清单": " ".join(sorted(gn - un)), "仅UI清单": " ".join(sorted(un - gn))})
    write_csv(dest / "GP_UI方法面差异.csv", diffrows,
              ["对象/命名空间", "GP方法数", "UI方法数", "共有", "仅GP", "仅UI", "仅GP清单", "仅UI清单"])

    # ---------------- 统计 ----------------
    stat = {
        "总条目": len(detail),
        "判定分布": dict(collections.Counter(r["一致性判定"] for r in detail)),
        "实际范围分布": dict(collections.Counter(r["实际范围"] for r in detail)),
        "文档可用性分布": dict(collections.Counter(r["文档可用性"] for r in detail)),
        "GP状态分布": dict(collections.Counter(r["GP状态"] for r in detail)),
        "UI状态分布": dict(collections.Counter(r["UI状态"] for r in detail)),
    }
    (dest / "统计.json").write_text(json.dumps(
        {"stat": stat, "meta": meta, "dynamic_surfaces": {k: sorted(v) for k, v in dyn.items()},
         "class_resolution": {c: d[c]["class_resolution"] for c in ("gp", "ui")},
         "diff": diffrows, "ns": nsrows}, ensure_ascii=False, indent=2), encoding="utf-8")

    # 原始材料随报告一并交付
    for f in OUT.iterdir():
        if f.is_file() and f.name not in ("results.json",):
            (dest / f.name).write_bytes(f.read_bytes())
    (dest / "results.json").write_bytes((OUT / "results.json").read_bytes())
    (dest / "scan.py").write_bytes((WORK / "scan.py").read_bytes())

    print(json.dumps(stat, ensure_ascii=False, indent=2))
    print("交付目录：", dest)
    return dest, detail, stat, diffrows, nsrows, d, meta, dyn


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
