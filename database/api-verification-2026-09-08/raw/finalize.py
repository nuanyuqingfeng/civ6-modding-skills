#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终归并：首轮扫描 + 补测 + 三层恢复 -> 桌面交付物（CSV + 中文报告）。"""
from __future__ import annotations

import csv
import io
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

# 需要「活体实例」的类：无实例即不可判（而非不存在）
PROVIDER_CLASSES = {"Player", "City", "Unit", "Plot", "Notification", "Game", "Control"}
# 需要特定运行条件才能取到实例的类
CONDITIONAL = {
    "Notification": "需玩家当前有未读通知（本局本地玩家通知列表为空）",
    "DiplomacyDeal": "需进行中的外交交易会话（DealManager 取出 Deal 实例）",
    "DiplomacyDealItem": "需进行中的外交交易会话（Deal 内条目）",
    "InputStruct": "需输入事件回调实参（UI 输入处理器触发时才有）",
    "MapPinConfiguration": "需地图钉编辑 UI 上下文（MapPinManager 内）",
    "WorldBuilderResourceGenerator": "需世界生成器会话（WorldBuilder.ResourceGenerator）",
    "FreeCities": "需存在自由城市实例（CityManager.GetFreeCityAt）",
    "Fractal": "需 Fractal.Create(...) 参数化构造（世界生成期）",
    "DirtyComponents": "仅部分 UI 状态可见（CityBannerManager / UnitFlagManager）",
}
CODEBUDDY = {"CodeBuddyFuncs", "CodeBuddyFuncsRaw"}


def san(s):
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def expr_for(r):
    tbl, fn, sub = r["table_name"], r["func_name"], r["sub_func_name"]
    dot = r["invoke"].startswith("Dot")
    if dot:
        if not fn:
            if r["type"] == "QUERY" and r["id"].startswith("Q-GameInfo"):
                return "GameInfo." + tbl, None, "gameinfo"
            return tbl, "GameInfo." + tbl, "namespace"
        return ".".join([tbl] + [p for p in (fn, sub) if p]), tbl, "dot"
    if sub:
        return ("__SC.C_%s_P_%s.%s" % (san(tbl), san(fn), sub),
                "__SC.C_%s_P_%s" % (san(tbl), san(fn)), "colon-sub")
    if fn:
        return ("__SC.C_%s.%s" % (san(tbl), fn), "__SC.C_%s" % san(tbl), "colon")
    return "__SC.C_%s" % san(tbl), None, "colon-obj"


def parse_l3(path):
    """解析三层恢复转储：{容器键: {方法名: 类型}}"""
    out = {}
    if not Path(path).exists():
        return out
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("L3K|"):
            p = ln.split("|", 3)
            names = {}
            if not p[3].startswith("<"):
                for it in p[3].split(","):
                    if ":" in it:
                        k, v = it.rsplit(":", 1)
                        names[k] = v
            out[p[1] + "_L3"] = names
    return out


def main():
    d = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    sup = json.loads((OUT / "supplement.json").read_text(encoding="utf-8"))
    meta = json.loads((OUT / "scan_meta.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(str(API_DB)); con.row_factory = sqlite3.Row
    rows = [dict(x) for x in con.execute("select * from api_functions")]; con.close()
    gcon = sqlite3.connect(str(GAMEPLAY_DB))
    dbt = [x[0] for x in gcon.execute("select name from sqlite_master where type='table' order by name")]
    gcon.close()

    l3 = {"gp": parse_l3(OUT / "l3_gp.txt"), "ui": parse_l3(OUT / "l3_ui.txt")}
    # 子对象解析结果：{ctx: {"Class.Parent": how}}
    subhow = {}
    for ctx in ("gp", "ui"):
        m = {}
        for ln in d[ctx]["sub_lines"]:
            if ln.startswith("SUB|"):
                q = ln.split("|")
                m[q[1]] = q[2]
        subhow[ctx] = m
    manual = json.loads((OUT / "manual_patch.json").read_text(encoding="utf-8"))         if (OUT / "manual_patch.json").exists() else {}

    def runtime_keys(ctx, r):
        """该行所在容器的运行时键集合（用于给出近似名建议）。"""
        tbl, fn, sub = r["table_name"], r["func_name"], r["sub_func_name"]
        if r["invoke"].startswith("Colon") or (sub and r["invoke"].startswith("Dot")):
            key = "C_%s_P_%s" % (san(tbl), san(fn)) if sub else "C_%s" % san(tbl)
            ks = d[ctx]["enum_methods"].get(key)
            if ks:
                return {x.split(":")[0] for x in ks}
            return set()
        g = d[ctx]["enum_globals"].get(tbl.split(".")[0])
        if g and g.get("keys"):
            return {x.split(":")[0] for x in g["keys"]}
        return set()

    def suggest(ctx, r, name):
        if not name:
            return ""
        ks = runtime_keys(ctx, r)
        if not ks:
            return ""
        cand = {k for k in ks if (k.startswith(name) or name.startswith(k) or name in k or k in name)
                and k != name and not k.startswith("__")}
        cand |= {k for k in ks if k == name + "1"}
        return " ".join(sorted(cand, key=lambda x: (len(x), x))[:4])
    # 补测结果索引
    fix = {ctx: sup["states"][ctx]["probe"] for ctx in ("gp", "ui")}
    cand_hits = {}   # id -> {ctx: (真名, 类型, 表达式)}
    for ctx in ("gp", "ui"):
        for rid, cname, expr in sup["states"][ctx]["cand_expr"]:
            st = fix[ctx].get(expr)
            if st in EXIST:
                cand_hits.setdefault(rid, {})[ctx] = (cname, st, expr)
    extra_states = [k for k in sup["states"] if k not in ("gp", "ui") and "error" not in sup["states"][k]]
    extra_hit = collections.defaultdict(dict)   # expr -> {state: type}
    for st in extra_states:
        for e, t in sup["states"][st].get("hits", {}).items():
            extra_hit[e][st] = t

    dyn = {}
    for ctx in ("gp", "ui"):
        dyn[ctx] = {e.split(".")[0] for e, s in d["dynamic_sentinel"][ctx].items() if s == "table"}

    # 三层压平识别：sub = 父名单数形 + 真名，且该单数形本身是二层对象的方法
    def l3_true_name(r, ctx):
        tbl, fn, sub = r["table_name"], r["func_name"], r["sub_func_name"]
        if not sub or not fn or not fn.endswith("s"):
            return None
        prefix = fn[:-1]
        if not sub.startswith(prefix) or len(sub) <= len(prefix):
            return None
        rest = sub[len(prefix):]
        if not rest[0].isupper():
            return None
        key = "C_%s_P_%s" % (san(tbl), san(fn))
        # 二层对象必须真有 prefix 这个方法（如 CityDistricts:GetDistrict）
        lvl2 = None
        em = d[ctx]["enum_methods"].get(key)
        if em:
            lvl2 = {x.split(":")[0] for x in em}
        if lvl2 is not None and prefix not in lvl2:
            return None
        return prefix, rest, key + "_L3"

    # ---------------- 逐行判定 ----------------
    detail = []
    for r in rows:
        expr, container, kind = expr_for(r)
        tbl = r["table_name"]
        rec = {"id": r["id"], "类型": r["type"], "命名空间/类": tbl, "方法": r["func_name"],
               "子方法": r["sub_func_name"] or "", "调用形态": r["invoke"],
               "文档可用性": r["availability"], "来源": r["source"],
               "路径类别": kind, "探测表达式": expr, "参数": r["args_flat"], "返回": r["returns_flat"]}
        notes = {}
        for ctx, label in (("gp", "GP"), ("ui", "UI")):
            probe = d[ctx]["probe"]
            clsres = d[ctx]["class_resolution"]
            st = probe.get(expr, "NOPROBE")
            note = ""
            ok = None

            # dot 带子方法：首轮表达式错误（索引函数），用补测修正值
            if kind == "dot" and r["sub_func_name"]:
                fx = "__SC.C_%s_P_%s.%s" % (san(tbl), san(r["func_name"]), r["sub_func_name"])
                st2 = fix[ctx].get(fx)
                if st2 is not None:
                    st = st2
                    rec["修正表达式"] = fx
                    note = "首轮表达式为「索引函数」，已用子对象容器修正"

            # 事件动态代理
            if tbl in dyn[ctx]:
                ok, note = None, "动态代理：任意名均返回 table，存在性不可判"
            elif tbl in CODEBUDDY:
                ok = False if st not in EXIST else True
                note = "文档转储命名空间：运行时不存在该全局"
            elif kind == "gameinfo":
                ok = st in EXIST
                note = "GameInfo 子表" + ("可达" if ok else "不存在")
            elif kind == "namespace":
                if st in EXIST:
                    ok, note = True, "命名空间存在"
                else:
                    alt = probe.get("GameInfo." + tbl)
                    ok = False
                    note = ("运行时全局不存在（GameInfo.%s 可达）" % tbl) if alt in EXIST else "命名空间在该上下文不存在"
            elif kind == "dot":
                base = probe.get(container, "NOPROBE")
                if base not in EXIST:
                    ok, note = False, f"命名空间 {container} 在该上下文不存在"
                elif st in EXIST:
                    ok, note = True, ""
                elif st == "CF":
                    ok, note = None, "表达式不可编译（文档为 C++ 签名串）"
                else:
                    ok, note = False, "命名空间存在但无此成员"
            else:  # colon*
                res = clsres.get(tbl, "?")
                cont = probe.get(container, "NOPROBE") if container else st
                if kind == "colon-sub" and cont not in EXIST:
                    how = subhow[ctx].get("%s.%s" % (san(tbl), san(r["func_name"])))
                    if res.startswith("none"):
                        ok, note = None, f"类 {tbl} 在该上下文无实例通道（{res}）"
                    elif how == "type:nil":
                        ok = False
                        note = (f"父方法 {r['func_name']} 在该上下文不存在 → 子方法必然不存在"
                                f"（运行时该方法面见 GP_UI方法面差异.csv）")
                    elif how is None:
                        ok, note = None, "父对象未参与解析（如需参数的构造器）"
                    else:
                        ok, note = None, f"父对象未解析（{how}）——子方法不可验证"
                elif tbl in CONDITIONAL and res.startswith("none"):
                    ok = None
                    note = "无实例通道：" + CONDITIONAL[tbl]
                elif res.startswith("none") and tbl not in PROVIDER_CLASSES:
                    ok = False
                    note = "该上下文既无同名模块/全局，也无实例通道"
                elif res.startswith("none"):
                    ok, note = None, f"类 {tbl} 无活体实例（{res}）"
                elif st in EXIST:
                    ok, note = True, f"经 {res} 检出"
                elif st == "CF":
                    ok, note = None, "表达式不可编译（文档为 C++ 签名串）"
                else:
                    ok, note = False, f"经 {res} 检查：无此方法"

            # 三层压平恢复
            t3 = l3_true_name(r, ctx)
            if t3 and ok is not True:
                prefix, rest, l3key = t3
                names = l3[ctx].get(l3key)
                if names is None:
                    note += f"｜三层压平：真路径需 {prefix}(i) 取对象，本次未取到该层实例"
                elif rest in names:
                    ok = True
                    note = f"文档三层压平：真名 {rest}（经 {prefix}(i) 取对象后存在）"
                    rec[f"{label}真名"] = rest
                else:
                    note += f"｜三层压平候选 {rest} 在 {prefix}(i) 对象上亦不存在"
            rec[f"{label}真名"] = rec.get(f"{label}真名", "")

            # 损坏名 / 候选真名（二层命中）
            if rid_hit := cand_hits.get(r["id"], {}).get(ctx):
                cname, ctype, cexpr = rid_hit
                if ok is not True:
                    ok = True
                    note = f"文档名损坏：真名 {cname} 在运行时存在"
                rec[f"{label}真名"] = cname

            # 其它 UI 状态命中
            if ctx == "ui" and ok is not True:
                hits = extra_hit.get(expr) or extra_hit.get(rec.get("修正表达式", ""))
                if hits:
                    note += "｜其它 UI 状态可见：" + ",".join(sorted(hits))
                    rec["其它UI状态"] = ",".join(sorted(hits))
                    ok = True
            rec["其它UI状态"] = rec.get("其它UI状态", "")

            # 手工核验补丁（如 UI.GetGameParameters 的 Get 前缀拼接名）
            mk = f"{ctx}|{tbl}|{r['func_name']}|{r['sub_func_name']}"
            if mk in manual:
                info = manual[mk]
                if info["exists"] and ok is not True:
                    ok = True
                    note = f"文档名拼接：真名 {info['true_name']}（手工核验命中）"
                    rec[f"{label}真名"] = info["true_name"]
                elif not info["exists"]:
                    note = (f"文档名拼接：去前缀候选 {info['true_name']} 亦不存在"
                            f"（该对象运行时仅 5 法：Add/Get/GetValue/Remove/SetValue）")

            # 运行时近似名建议（仅对"确实不存在"的行给出）
            if ok is False:
                sg = suggest(ctx, r, r["sub_func_name"] or r["func_name"] or r["table_name"])
                if sg:
                    rec[f"{label}近似名"] = sg

            rec[f"{label}状态"] = st
            rec[f"{label}存在"] = {True: "是", False: "否", None: "不可判"}[ok]
            rec[f"{label}备注"] = note
            rec[f"_{ctx}"] = ok
            notes[ctx] = note

        # 一致性判定
        g, u = rec["_gp"], rec["_ui"]
        doc = r["availability"]
        if tbl in CODEBUDDY:
            verdict = "文档转储（非运行时命名空间）"
        elif tbl in dyn["gp"] or tbl in dyn["ui"]:
            verdict = "动态事件代理（不可判）"
        elif g is None and u is None:
            reason = CONDITIONAL.get(tbl)
            verdict = "无法验证：" + reason if reason else "无法验证：无实例通道"
        elif doc == "Both":
            verdict = ("一致" if g and u else
                       "文档偏宽：双端均未见" if (g is False and u is False) else
                       "文档偏宽：GP 未见" if g is False else
                       "文档偏宽：UI 未见" if u is False else "部分不可验证")
        elif doc == "UI":
            verdict = ("一致" if u and g is False else
                       "文档偏窄：GP 亦可见" if u and g else
                       "文档存疑：UI 未见" if u is False else
                       "一致（GP 侧不可验证）" if u else "部分不可验证")
        elif doc == "GamePlay":
            verdict = ("一致" if g and u is False else
                       "文档偏窄：UI 亦可见" if g and u else
                       "文档存疑：GP 未见" if g is False else
                       "一致（UI 侧不可验证）" if g else "部分不可验证")
        else:
            verdict = "?"
        rec["一致性判定"] = verdict
        pair = (g is True, u is True)
        rec["实际范围"] = ("双端" if pair == (True, True) else "仅GP" if pair == (True, False)
                     else "仅UI" if pair == (False, True) else "双端未见" if pair == (False, False)
                     else "含不可判")
        detail.append(rec)

    # ---------------- 输出目录 ----------------
    stamp = time.strftime("%Y%m%d")
    dest = DESKTOP / f"Civ6_API_UI-GP范围验证_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "raw").mkdir(exist_ok=True)

    cols = ["id", "类型", "命名空间/类", "方法", "子方法", "调用形态", "文档可用性", "来源", "路径类别",
            "探测表达式", "修正表达式", "GP状态", "GP存在", "GP真名", "GP近似名", "GP备注",
            "UI状态", "UI存在", "UI真名", "UI近似名", "UI备注", "其它UI状态", "实际范围", "一致性判定", "参数", "返回"]

    def wcsv(path, recs, columns):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            for x in recs:
                w.writerow(x)
        return len(recs)

    for c in cols:
        for x in detail:
            x.setdefault(c, "")

    n_full = wcsv(dest / "api_scope_full.csv", detail, cols)
    bad = [x for x in detail if x["一致性判定"].startswith(("文档偏宽", "文档偏窄", "文档存疑"))]
    n_bad = wcsv(dest / "api_scope_文档与运行时不符.csv", bad, cols)
    unver = [x for x in detail if x["一致性判定"].startswith(("无法验证", "部分不可验证", "动态事件代理"))]
    n_unver = wcsv(dest / "api_scope_无法验证.csv", unver, cols)
    nameissue = [x for x in detail if x["GP真名"] or x["UI真名"] or "三层压平" in x["GP备注"] + x["UI备注"]]
    n_name = wcsv(dest / "api_scope_文档名异常.csv", nameissue, cols)
    cb = [x for x in detail if x["命名空间/类"] in CODEBUDDY]
    n_cb = wcsv(dest / "api_scope_CodeBuddy转储.csv", cb, cols)

    # 命名空间汇总
    ns = collections.defaultdict(collections.Counter)
    nsdoc, nsform = {}, {}
    for x in detail:
        k = x["命名空间/类"]
        nsdoc[k], nsform[k] = x["文档可用性"], x["调用形态"]
        c = ns[k]
        c["条目数"] += 1
        c["GP存在"] += x["GP存在"] == "是"
        c["UI存在"] += x["UI存在"] == "是"
        c["GP不可判"] += x["GP存在"] == "不可判"
        c["UI不可判"] += x["UI存在"] == "不可判"
        c[x["实际范围"]] += 1
        c[x["一致性判定"]] += 1
    nsrows = []
    for k in sorted(ns, key=lambda z: -ns[z]["条目数"]):
        c = ns[k]
        nsrows.append({
            "命名空间/类": k, "调用形态": nsform[k], "文档可用性": nsdoc[k], "条目数": c["条目数"],
            "GP存在": c["GP存在"], "UI存在": c["UI存在"], "GP不可判": c["GP不可判"], "UI不可判": c["UI不可判"],
            "双端": c["双端"], "仅GP": c["仅GP"], "仅UI": c["仅UI"], "双端未见": c["双端未见"],
            "一致": c["一致"] + c["一致（GP 侧不可验证）"] + c["一致（UI 侧不可验证）"],
            "文档偏窄": c["文档偏窄：GP 亦可见"] + c["文档偏窄：UI 亦可见"],
            "文档偏宽": c["文档偏宽：双端均未见"] + c["文档偏宽：GP 未见"] + c["文档偏宽：UI 未见"],
            "文档存疑": c["文档存疑：UI 未见"] + c["文档存疑：GP 未见"],
            "无法验证": sum(v for kk, v in c.items() if str(kk).startswith("无法验证：")) + c["部分不可验证"],
            "文档转储": c["文档转储（非运行时命名空间）"],
            "动态代理": c["动态事件代理（不可判）"],
        })
    wcsv(dest / "命名空间汇总.csv", nsrows, list(nsrows[0].keys()))

    # GameInfo 库表可达性
    gi = [{"库表": t, "GP": d["gp"]["probe"].get("GameInfo." + t, "NOPROBE"),
           "UI": d["ui"]["probe"].get("GameInfo." + t, "NOPROBE")} for t in dbt]
    wcsv(dest / "GameInfo库表可达性.csv", gi, ["库表", "GP", "UI"])
    gi_ok = sum(1 for x in gi if x["GP"] in EXIST and x["UI"] in EXIST)

    # CodeBuddy 归属面
    cbrows = []
    for label, key in (("CodeBuddyFuncs", "codebuddyfuncs"), ("CodeBuddyFuncsRaw(归一化)", "raw_normalized")):
        hu, hg = d["codebuddy"]["ui"][key], d["codebuddy"]["gp"][key]
        names = d["codebuddy_names"] if key == "codebuddyfuncs" else d["codebuddy_raw_norm"]
        for n in names:
            su = sorted({e.rsplit(".", 1)[0] for e in hu if e.endswith("." + n)})
            sg = sorted({e.rsplit(".", 1)[0] for e in hg if e.endswith("." + n)})
            cbrows.append({"清单": label, "名称": n, "UI命中面数": len(su), "GP命中面数": len(sg),
                           "UI命中面": ", ".join(su), "GP命中面": ", ".join(sg)})
    wcsv(dest / "CodeBuddy归属面.csv", cbrows, ["清单", "名称", "UI命中面数", "GP命中面数", "UI命中面", "GP命中面"])
    cb_ui_hit = len({r["名称"] for r in cbrows if r["清单"] == "CodeBuddyFuncs" and r["UI命中面数"]})
    cb_gp_hit = len({r["名称"] for r in cbrows if r["清单"] == "CodeBuddyFuncs" and r["GP命中面数"]})
    raw_ui_hit = len({r["名称"] for r in cbrows if r["清单"] != "CodeBuddyFuncs" and r["UI命中面数"]})
    # CodeBuddyFuncs 名称按归属面统计
    cb_surface = collections.Counter()
    for r in cbrows:
        if r["清单"] == "CodeBuddyFuncs":
            for s in [x for x in r["UI命中面"].split(", ") if x]:
                cb_surface[s] += 1

    # GP/UI 方法面差异
    diffrows = []
    for key in sorted(set(d["gp"]["enum_methods"]) | set(d["ui"]["enum_methods"])):
        gk = [x.split(":")[0] for x in d["gp"]["enum_methods"].get(key, []) if not x.startswith("<")]
        uk = [x.split(":")[0] for x in d["ui"]["enum_methods"].get(key, []) if not x.startswith("<")]
        gn, un = set(gk) - {"__instances"}, set(uk) - {"__instances"}
        if not gn and not un:
            continue
        diffrows.append({"对象/命名空间": key, "GP方法数": len(gn), "UI方法数": len(un),
                         "共有": len(gn & un), "仅GP": len(gn - un), "仅UI": len(un - gn),
                         "仅GP清单": " ".join(sorted(gn - un)), "仅UI清单": " ".join(sorted(un - gn))})
    wcsv(dest / "GP_UI方法面差异.csv", diffrows,
         ["对象/命名空间", "GP方法数", "UI方法数", "共有", "仅GP", "仅UI", "仅GP清单", "仅UI清单"])

    # 全局命名空间存在性对照
    globrows = []
    for n in sorted({r["table_name"] for r in rows}):
        g = d["gp"]["probe"].get(n, "NOPROBE")
        u = d["ui"]["probe"].get(n, "NOPROBE")
        ge = d["gp"]["enum_globals"].get(n, {})
        ue = d["ui"]["enum_globals"].get(n, {})
        globrows.append({"命名空间": n, "GP类型": g, "UI类型": u,
                         "GP可见": "是" if g in EXIST else "否", "UI可见": "是" if u in EXIST else "否",
                         "GP键数": ge.get("nkeys", ""), "UI键数": ue.get("nkeys", ""),
                         "GP受保护元表": "是" if ge.get("protected") else "", "UI受保护元表": "是" if ue.get("protected") else ""})
    wcsv(dest / "命名空间可见性.csv", globrows,
         ["命名空间", "GP类型", "UI类型", "GP可见", "UI可见", "GP键数", "UI键数", "GP受保护元表", "UI受保护元表"])

    stat = {
        "总条目": len(detail),
        "判定分布": dict(collections.Counter(x["一致性判定"] for x in detail).most_common()),
        "实际范围分布": dict(collections.Counter(x["实际范围"] for x in detail).most_common()),
        "文档可用性分布": dict(collections.Counter(x["文档可用性"] for x in detail).most_common()),
        "GP状态分布": dict(collections.Counter(x["GP状态"] for x in detail).most_common()),
        "UI状态分布": dict(collections.Counter(x["UI状态"] for x in detail).most_common()),
    }
    json.dump({"stat": stat, "meta": meta, "ns": nsrows, "diff": diffrows,
               "dynamic": {k: sorted(v) for k, v in dyn.items()},
               "gi_ok": gi_ok, "gi_total": len(gi),
               "cb": {"rows": len(cb), "ui_hit": cb_ui_hit, "gp_hit": cb_gp_hit, "raw_ui_hit": raw_ui_hit,
                      "surface_top": cb_surface.most_common(12)},
               "extra_states": extra_states,
               "name_issue": len(nameissue)},
              io.open(dest / "统计.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 原始材料
    for f in OUT.iterdir():
        if f.is_file():
            (dest / "raw" / f.name).write_bytes(f.read_bytes())
    for f in [WORK / "scan.py", WORK / "report.py", WORK / "supplement.py", WORK / "finalize.py"]:
        if f.exists():
            (dest / "raw" / f.name).write_bytes(f.read_bytes())
    for f in (WORK / "lua").iterdir():
        if f.is_file():
            (dest / "raw" / ("lua_" + f.name)).write_bytes(f.read_bytes())

    print(json.dumps(stat, ensure_ascii=False, indent=2))
    print("GameInfo 可达：%d/%d" % (gi_ok, len(gi)))
    print("CodeBuddy 行 %d；UI 命中名 %d；GP 命中名 %d" % (len(cb), cb_ui_hit, cb_gp_hit))
    print("文档名异常行 %d；不符 %d；无法验证 %d" % (len(nameissue), len(bad), len(unver)))
    print("交付目录：", dest)
    return dest, detail, stat, nsrows, diffrows, globrows, locals()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
