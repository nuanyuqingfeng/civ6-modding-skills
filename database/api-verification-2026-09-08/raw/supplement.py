#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补测：修正首轮扫描的三类盲区（仍严格只读）。

1. dot 型父对象容器未登记（Map / MapRoutes / Network / UI / Territories ...）
   -> 轻量 setup 把所有可解析的同名全局登记进 __SC，再跑子对象解析。
2. dot 型带子方法的行首轮用了 `Game.GetHistoryManager.HasX` 这种「索引函数」表达式（必然 ERR）
   -> 改用 `__SC.C_<类>_P_<父>.<子>` 重测。
3. 文档子方法名疑似拼接/损坏（如 GetDistricts->GetDistrictGetAirSlots、Q-MapGetCityPlotsGetX）
   -> 生成候选真名重测。
4. 文档声称某上下文可用、但 InGame 根上下文未见的条目
   -> 在其它 UI 状态（WorldInput / TopPanel_TT / CityBannerManager ...）复测。

不做任何写操作；每个状态跑完即 `__SC=nil` 清理；不 include 任何模块。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")
OUT = WORK / "out"
API_DB = Path(r"%USERPROFILE%\.agents\skills\civ6-modding\database\api.sqlite")

spec = importlib.util.spec_from_file_location("scan", WORK / "scan.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

EXTRA_UI_STATES = ["WorldInput", "StrategicView", "TopPanel_TT", "ARXManager", "CityBannerManager",
                   "PlotToolTip", "MapPinManager", "GovernorPanel", "HistoricMoments",
                   "UnitFlagManager", "PowerLensManager", "TutorialUIRoot"]

LIGHT_SETUP = scan.LUA_PRELUDE + r"""
__SC = {}
local function reg(k, v) if v ~= nil then __SC["C_" .. k] = v end end
local names = __NAMES__
for i = 1, #names do
  local n = names[i]
  local v = rslv(n)
  if v ~= nil then reg(n:gsub("[^%w_]", "_"), v) end
end
-- 实例通道
local function firstPlayer()
  local lp = rslv("Game.GetLocalPlayer and Game.GetLocalPlayer()")
  if type(lp) == "number" and rslv("Players[" .. lp .. "]") ~= nil then return rslv("Players[" .. lp .. "]") end
  for i = 0, 63 do local p = rslv("Players[" .. i .. "]") if type(p) == "table" then return p end end
  return nil
end
local function firstMember(obj, getter)
  local out = nil
  if obj == nil then return nil end
  pcall(function()
    local m = obj[getter]
    if type(m) ~= "function" then return end
    local c = m(obj)
    if type(c) ~= "table" then return end
    for i, v in c:Members() do if out == nil then out = v end end
  end)
  return out
end
local pl = firstPlayer()
reg("Player", pl)
reg("City", firstMember(pl, "GetCities"))
reg("Unit", firstMember(pl, "GetUnits"))
reg("Notification", firstMember(pl, "GetNotifications"))
reg("Plot", rslv("Map.GetPlotByIndex(0)"))
local ctrl = nil
pcall(function()
  for k, v in pairs(Controls) do
    if ctrl == nil and type(v) == "table" then
      local mt = getmetatable(v)
      if type(mt) == "table" and tostring(mt.CTypeName) == "ControlBase" then ctrl = v end
    end
  end
end)
reg("Control", ctrl)
local cnt = 0
for _ in pairs(__SC) do cnt = cnt + 1 end
print("LIGHTSETUP|" .. cnt)
print("---END---")
"""

PROBE = scan.PROBE_TMPL


def san(s):
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def load_rows():
    con = sqlite3.connect(str(API_DB))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("select * from api_functions")]
    con.close()
    return rows


def candidates_for(r):
    """为可疑的子方法名生成候选真名。"""
    sub, par, tbl = r["sub_func_name"], r["func_name"], r["table_name"]
    if not sub:
        return []
    out = []
    # a) 前缀 = 父方法名（GetBuildings + GetBuildingsAtLocation 之类拼接）
    if par and sub.startswith(par) and len(sub) > len(par):
        out.append(sub[len(par):])
    # b) 前缀 = 父方法名的单数形（GetDistricts -> GetDistrict|GetAirSlots）
    if par and par.endswith("s") and sub.startswith(par[:-1]) and len(sub) > len(par) - 1:
        out.append(sub[len(par) - 1:])
    # c) 前缀 = 文档 id 残留（Q-MapGetCityPlotsGetPurchasedByCity）
    m = re.match(r"^[A-Z]-(.+)$", sub)
    if m:
        rest = m.group(1)
        for pre in (tbl + (par or ""), tbl, par or ""):
            if pre and rest.startswith(pre) and len(rest) > len(pre):
                out.append(rest[len(pre):])
                break
        else:
            out.append(rest)
    # d) 名称中夹带 id 片段（GetWorkingCityIDQ-MapGetCityPlots）
    m2 = re.match(r"^([A-Za-z_]\w*?)[A-Z]-", sub)
    if m2:
        out.append(m2.group(1))
    return [c for c in dict.fromkeys(out) if c and re.match(r"^[A-Za-z_]\w*$", c) and c != sub]


def main():
    rows = load_rows()
    d = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    ch = scan.Channel()
    print("已连接：", ch.identity.strip())
    allnames = sorted({r["table_name"] for r in rows} | {"Players", "Controls", "ContextPtr", "GameInfo"})
    jobs = scan.nested_parents(rows)
    joblua = []
    argmap = {"Territories.GetTerritoryAt": 0, "MapRoutes.GetIndexedPortal": 0}
    for tbl, fn, args, subs in jobs:
        a = "nil" if args is None else "{%d}" % args
        joblua.append('{"%s","%s",%s},' % (san(tbl), san(fn), a))
    sublua = scan.SUBRESOLVE_TMPL.replace("__JOBS__", "\n".join(joblua))

    # ---- 待补测集合 ----
    import csv, io
    cands_dir = sorted([q for q in Path(r"<作者机桌面>").iterdir()
                        if q.is_dir() and q.name.startswith("Civ6_API_UI-GP范围验证_")])
    if not cands_dir:
        raise SystemExit("未找到首轮交付目录")
    full = list(csv.DictReader(io.open(cands_dir[-1] / "api_scope_full.csv", encoding="utf-8-sig")))
    byid = {r["id"]: r for r in full}
    print("首轮明细：", cands_dir[-1] / "api_scope_full.csv", len(full), "行")

    pending_ui, pending_gp, fixexpr = [], [], []
    malformed = []
    for r in rows:
        rec = byid.get(r["id"])
        if rec is None:
            continue
        expr, container, kind = scan_expr(r)
        # 2) dot 型带子方法 -> 修正表达式
        if kind == "dot" and r["sub_func_name"]:
            fx = "__SC.C_%s_P_%s.%s" % (san(r["table_name"]), san(r["func_name"]), r["sub_func_name"])
            fixexpr.append((r["id"], fx))
        # 3) 名称损坏候选
        cands = candidates_for(r)
        if cands:
            malformed.append((r["id"], r["table_name"], r["func_name"], r["sub_func_name"], cands))
        # 4) 文档声称可用但未见
        claim_ui = r["availability"] in ("UI", "Both")
        claim_gp = r["availability"] in ("GamePlay", "Both")
        if claim_ui and rec["UI存在"] != "是":
            pending_ui.append((r["id"], expr))
        if claim_gp and rec["GP存在"] != "是":
            pending_gp.append((r["id"], expr))

    print(f"待补测：UI {len(pending_ui)} 条 / GP {len(pending_gp)} 条；dot 子方法修正 {len(fixexpr)}；名称候选 {len(malformed)}")

    result = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "states": {}, "malformed": malformed,
              "fixexpr": fixexpr, "calls": 0}

    def probe_batch(ctx_state_idx, exprs, tag):
        res = {}
        for i in range(0, len(exprs), scan.CHUNK):
            batch = exprs[i:i + scan.CHUNK]
            lines = ch.run_ctx(ctx_state_idx, PROBE.replace("__EXPRS__", scan.lua_str_list(batch)), timeout=90)
            result["calls"] += 1
            for ln in lines:
                if ln.startswith("R|"):
                    p = ln.split("|")
                    if len(p) >= 3:
                        res[p[1]] = p[2]
        return res

    # 给 Channel 加一个按索引执行的便捷方法
    def run_idx(idx, code, timeout=90.0):
        ch.calls += 1
        return scan.tx.execute(ch.sock, idx, code, timeout=timeout)

    ch.run_ctx = run_idx

    # ---- 主两上下文：修正表达式 + 候选名 ----
    for ctx, key in (("gp", "GameCore_Tuner"), ("ui", "InGame")):
        idx = ch.states[key]
        setup = LIGHT_SETUP.replace("__NAMES__", "{" + scan.lua_str_list(allnames) + "}")
        lines = run_idx(idx, setup)
        print(f"[{ctx}] light setup:", lines[:1])
        sublines = run_idx(idx, sublua)
        oksubs = [l for l in sublines if l.startswith("SUB|") and "|nil" not in l]
        print(f"[{ctx}] 子对象解析成功 {len(oksubs)}/{len(jobs)}")
        exprs = [e for _, e in fixexpr]
        # 候选名表达式（基于修正后的容器）
        cand_expr = []
        for rid, tbl, fn, sub, cands in malformed:
            r = next(x for x in rows if x["id"] == rid)
            base = ("__SC.C_%s_P_%s" % (san(tbl), san(fn))) if r["invoke"].startswith("Colon") or r["sub_func_name"] else None
            if r["invoke"].startswith("Dot") and not r["sub_func_name"]:
                base = tbl
            if base is None:
                base = "__SC.C_%s_P_%s" % (san(tbl), san(fn)) if r["sub_func_name"] else "__SC.C_%s" % san(tbl)
            for c in cands:
                cand_expr.append((rid, c, f"{base}.{c}"))
        exprs += [e for _, _, e in cand_expr]
        # 待补测（在本上下文再确认一次，light setup 后容器更全）
        exprs += [e for _, e in (pending_gp if ctx == "gp" else pending_ui)]
        exprs = list(dict.fromkeys(exprs))
        res = probe_batch(idx, exprs, ctx)
        result["states"][ctx] = {
            "probe": res,
            "sub_ok": [l.split("|")[1] for l in oksubs],
            "cand_expr": [[rid, c, e] for rid, c, e in cand_expr],
            "setup": lines[:1],
        }
        run_idx(idx, "__SC=nil print('CLEAN') print('---END---')", timeout=20)

    # ---- 其它 UI 状态 ----
    for st in EXTRA_UI_STATES:
        idx = ch.states.get(st)
        if idx is None:
            print(f"[{st}] 状态不存在，跳过")
            continue
        try:
            setup = LIGHT_SETUP.replace("__NAMES__", "{" + scan.lua_str_list(allnames) + "}")
            lines = run_idx(idx, setup, timeout=60)
            sublines = run_idx(idx, sublua, timeout=60)
            exprs = [e for _, e in pending_ui] + [e for _, e in fixexpr]
            exprs = list(dict.fromkeys(exprs))
            res = probe_batch(idx, exprs, st)
            EX = ("function", "table", "userdata", "number", "string", "boolean", "thread")
            hits = {k: v for k, v in res.items() if v in EX}
            result["states"][st] = {"probe": res, "hits": hits,
                                    "setup": lines[:1],
                                    "sub_ok": [l.split("|")[1] for l in sublines if l.startswith("SUB|") and "|nil" not in l]}
            print(f"[{st}] 探测 {len(exprs)}，命中 {len(hits)}")
            run_idx(idx, "__SC=nil print('CLEAN') print('---END---')", timeout=20)
        except Exception as e:
            print(f"[{st}] 跳过（{type(e).__name__}: {str(e)[:80]}）")
            result["states"][st] = {"error": str(e)[:200]}

    result["calls"] = ch.calls
    (OUT / "supplement.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print("补测完成，tuner 调用 =", ch.calls, "-> ", OUT / "supplement.json")
    ch.sock.close()


def scan_expr(r):
    """复用 scan.build_plan 的表达式推导（单行版）。"""
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


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
