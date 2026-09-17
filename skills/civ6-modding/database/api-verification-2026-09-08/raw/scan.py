#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Civ6 全量 API 的 UI/GP 范围存在性扫描（FireTuner 通道）。

策略
----
1. 从 civ6-modding 的 api.sqlite 取出全部 API 行（4857 条），按调用形态生成运行时表达式：
   - Dot (Global)   -> `<命名空间>[.<func>][.<sub>]`；GameInfo 子表 -> `GameInfo.<表名>`
   - Colon(Instance)-> `__SC.C_<类>[.<func>]`；嵌套 -> `__SC.C_<类>_P_<父>.<子>`
2. 每个上下文（gamecore=GP / ingame=UI）先跑 setup：登记实例提供者到全局 `__SC`，
   打印每个类的解析途径（instance / global / include / none）。
3. 分批（默认 600 条/批）用 `loadstring + pcall` 只读索引，回传 `R|<expr>|<type>`。
4. 附带枚举转储：可枚举全局的键、实例方法表键、GameInfo 全库表存在性。

只读约束：仅做「索引」，唯一例外是文档标注的零参 Get* 父方法（用于取子对象方法表），
以及 Territories:GetTerritoryAt(0) / MapRoutes.GetIndexedPortal(0) 两个只读查询。
不调用任何写操作，不结束回合，不改游戏状态。
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

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------
TUNER_SKILL = Path(r"%USERPROFILE%\.agents\skills\civ6-tuner")
MOD_SKILL = Path(r"%USERPROFILE%\.agents\skills\civ6-modding")
API_DB = MOD_SKILL / "database" / "api.sqlite"
GAMEPLAY_DB = MOD_SKILL / "database" / "DebugGameplay.sqlite"
WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")
OUTROOT = WORK / "out"

# include 白名单：已逐文件确认「加载期无顶层副作用调用」的 UI 模块。
# 明确排除 TunerUtilities —— 其文件末尾执行 UIManager:SetGlobalInputHandler(...)，
# 会顶掉 InGame 的全局输入处理器，属于会改变运行时行为的副作用。
SAFE_INCLUDES = ["InstanceManager", "PopupDialog", "ToolTipHelper"]

CHUNK = 600
TIMEOUT = 90.0

# ---------------------------------------------------------------------------
# tuner 通道
# ---------------------------------------------------------------------------
spec = importlib.util.spec_from_file_location("tuner_exec", TUNER_SKILL / "scripts" / "tuner_exec.py")
tx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tx)


class Channel:
    def __init__(self, host="127.0.0.1", port=4318):
        self.host, self.port = host, port
        self.sock = None
        self.states: dict[str, int] = {}
        self.identity = ""
        self.calls = 0
        self.connect()

    def connect(self):
        self.sock = tx.connect(self.host, self.port)
        self.identity, self.states = tx.handshake(self.sock)
        return self.states

    def run(self, ctx: str, code: str, timeout: float = TIMEOUT, retries: int = 2):
        key = "GameCore_Tuner" if ctx == "gp" else "InGame"
        idx = self.states.get(key)
        if idx is None:
            raise RuntimeError(f"缺少状态 {key}（是否已退出对局？）")
        last = None
        for attempt in range(retries + 1):
            try:
                self.calls += 1
                return tx.execute(self.sock, idx, code, timeout=timeout)
            except (tx.LuaError, TimeoutError, OSError) as e:
                last = e
                try:
                    self.sock.close()
                except Exception:
                    pass
                time.sleep(0.6)
                try:
                    self.connect()
                except OSError:
                    time.sleep(1.5)
                    self.connect()
        raise RuntimeError(f"{ctx} 执行失败（已重试）：{last}")


# ---------------------------------------------------------------------------
# Lua 片段
# ---------------------------------------------------------------------------
LUA_PRELUDE = r"""
local function rslv(e)
  local f = loadstring("return (" .. e .. ")")
  if not f then return nil end
  local ok, r = pcall(f)
  if not ok then return nil end
  return r
end
local function cnt(v)
  if type(v) ~= "table" then return -1 end
  local ok, c = pcall(function()
    local k = 0
    for _ in pairs(v) do k = k + 1 if k > 4000 then break end end
    return k
  end)
  return ok and c or -2
end
local function sortedkeys(v)
  local out = {}
  pcall(function() for k, val in pairs(v) do out[#out + 1] = tostring(k) .. ":" .. type(val) end end)
  table.sort(out)
  return out
end
local function ixtable(inst)
  if type(inst) ~= "table" then return nil end
  local mt = getmetatable(inst)
  if type(mt) ~= "table" then return nil end
  if type(mt.__index) == "table" then return mt.__index end
  return nil
end
"""

# setup：登记 __SC（类 -> 实例/替身对象）+ 打印类解析途径 + 全局存在性
SETUP_TMPL = LUA_PRELUDE + r"""
__SC = {}
__SCINFO = {}
local function reg(cls, val, how)
  if val == nil then
    __SCINFO[cls] = "none|nil"
    print("CLS|" .. tostring(cls) .. "|none|nil")
    return
  end
  __SC["C_" .. cls] = val
  __SCINFO[cls] = tostring(how) .. "|" .. type(val)
  local ixn = "fn/na"
  local ixt = ixtable(val)
  if ixt ~= nil then ixn = tostring(cnt(ixt)) end
  local parts = {"CLS", tostring(cls), tostring(how), type(val), "ix=" .. ixn, "pairs=" .. tostring(cnt(val))}
  print(table.concat(parts, "|"))
end

local IS_UI = __IS_UI__

-- include 白名单（仅 UI；已核实加载期无副作用的模块）
-- 先登记「include 前不存在」的全局，收尾时按此清单复原，避免污染 InGame 状态
__SCAN_ADDED = __SCAN_ADDED or {}
local watch = {"InstanceManager", "PopupDialog", "ToolTipHelper", "TunerUtilities",
               "TechAndCivicUnlockables", "TechAndCivicUnlockables_", "SupportFunctions"}
for i = 1, #watch do
  local n = watch[i]
  if rslv(n) == nil then __SCAN_ADDED[n] = true end
end
if IS_UI and type(include) == "function" then
  local mods = __INCLUDES__
  for i = 1, #mods do
    local ok, err = pcall(function() include(mods[i]) end)
    print("INC|" .. mods[i] .. "|" .. tostring(ok) .. "|" .. tostring(rslv(mods[i]) ~= nil))
  end
  for i = 1, #watch do
    local n = watch[i]
    print("WATCH|" .. n .. "|before_nil=" .. tostring(__SCAN_ADDED[n] == true) .. "|now=" .. type(rslv(n)))
  end
end

-- 实例提供者
local function firstPlayer()
  local lp = rslv("Game.GetLocalPlayer and Game.GetLocalPlayer()")
  if type(lp) == "number" and rslv("Players[" .. lp .. "]") ~= nil then
    return rslv("Players[" .. lp .. "]"), "local#" .. lp
  end
  for i = 0, 63 do
    local p = rslv("Players[" .. i .. "]")
    if type(p) == "table" then return p, "first#" .. i end
  end
  return rslv("Players[0]"), "fallback#0"
end
local function firstMember(obj, getter)
  local out = nil
  if obj == nil then return nil end
  pcall(function()
    local m = obj[getter]
    if type(m) ~= "function" then return end
    local container = m(obj)
    if type(container) ~= "table" then return end
    for i, v in container:Members() do if out == nil then out = v end end
  end)
  return out
end

local pl, plhow = firstPlayer()
reg("Player", pl, "instance:" .. plhow)
reg("City", firstMember(pl, "GetCities"), "instance:player-cities")
reg("Unit", firstMember(pl, "GetUnits"), "instance:player-units")
reg("Notification", firstMember(pl, "GetNotifications"), "instance:player-notifications")
reg("Plot", rslv("Map.GetPlotByIndex(0)") or rslv("Map.GetPlot(0,0)"), "instance:Map.GetPlotByIndex")
reg("Game", rslv("Game"), "global:Game")

if IS_UI then
  local ctrl = nil
  pcall(function()
    for k, v in pairs(Controls) do
      if ctrl == nil and type(v) == "table" then
        local mt = getmetatable(v)
        if type(mt) == "table" and tostring(mt.CTypeName) == "ControlBase" then ctrl = v end
      end
    end
  end)
  if ctrl == nil then
    pcall(function() for k, v in pairs(Controls) do if ctrl == nil and type(v) == "table" then ctrl = v end end end)
  end
  reg("Control", ctrl, "instance:Controls(ControlBase)")
end

-- 其余类：同名全局 -> 替身（Civ6 中大量“实例类”实为模块表/代理表）
local classes = __CLASSES__
for i = 1, #classes do
  local c = classes[i]
  if __SC["C_" .. c] == nil then
    local v = rslv(c)
    if v ~= nil then reg(c, v, "global-as-instance")
    else print("CLS|" .. c .. "|none|nil") end
  end
end
print("SETUP_DONE|__SC=" .. cnt(__SC))
print("---END---")
"""

PROBE_TMPL = r"""
local E = {
__EXPRS__
}
if type(__SC) ~= "table" then
  print("FATAL|__SC missing")
else
  for i = 1, #E do
    local e = E[i]
    local f = loadstring("return (" .. e .. ")")
    local r = "CF"
    if f then
      local ok, v = pcall(f)
      if not ok then r = "ERR"
      elseif v == nil then r = "nil"
      else r = type(v) end
    end
    print("R|" .. e .. "|" .. r)
  end
end
print("---END---")
"""

SUBRESOLVE_TMPL = LUA_PRELUDE + r"""
-- 解析嵌套父对象：先按字段索引，其次零参 Get* 调用（只读），最后带参只读查询
local jobs = {
__JOBS__
}
for i = 1, #jobs do
  local key, parent, args = jobs[i][1], jobs[i][2], jobs[i][3]
  local inst = __SC["C_" .. key]
  local sub, how = nil, "unresolved"
  if inst == nil then
    how = "noinst"
  else
    local v = nil
    local ok = pcall(function() v = inst[parent] end)
    if ok and type(v) == "table" then
      sub, how = v, "field"
    elseif ok and type(v) == "function" then
      local ok2, r2 = pcall(v, inst)
      if not ok2 or type(r2) ~= "table" then
        local ok3, r3 = pcall(v)
        if ok3 and type(r3) == "table" then ok2, r2 = ok3, r3 end
      end
      if ok2 and type(r2) == "table" then
        sub, how = r2, "call0"
      elseif args then
        local ok4, r4 = pcall(v, inst, args[1])
        if ok4 and type(r4) == "table" then sub, how = r4, "call1" end
      end
    elseif not ok then
      how = "index-err"
    else
      how = "type:" .. type(v)
    end
  end
  if sub ~= nil then
    local newkey = "C_" .. key .. "_P_" .. parent
    __SC[newkey] = sub
    local ix = ixtable(sub)
    print("SUB|" .. key .. "." .. parent .. "|" .. how .. "|" .. type(sub) ..
          "|pairs=" .. cnt(sub) .. "|ix=" .. (ix and cnt(ix) or "fn/na"))
  else
    print("SUB|" .. key .. "." .. parent .. "|" .. how .. "|nil")
  end
end
print("---END---")
"""

ENUM_TMPL = LUA_PRELUDE + r"""
local names = {
__NAMES__
}
for i = 1, #names do
  local n = names[i]
  local v = rslv(n)
  local t = type(v)
  local mt = getmetatable(v)
  local mtt = type(mt)
  local prot = (mtt == "boolean") and 1 or 0
  if t == "table" then
    local ks = prot and {} or sortedkeys(v)
    print("EK|" .. n .. "|" .. t .. "|prot=" .. prot .. "|mt=" .. mtt .. "|" .. #ks .. "|" .. table.concat(ks, ","))
  else
    print("EK|" .. n .. "|" .. t .. "|prot=" .. prot .. "|mt=" .. mtt .. "|0|")
  end
end
if type(__SC) == "table" then
  local keys = {}
  for k in pairs(__SC) do keys[#keys + 1] = k end
  table.sort(keys)
  for i = 1, #keys do
    local obj = __SC[keys[i]]
    local ix = ixtable(obj)
    if ix then
      local ks = sortedkeys(ix)
      print("MK|" .. keys[i] .. "|" .. #ks .. "|" .. table.concat(ks, ","))
    else
      local mt = getmetatable(obj)
      local ct = (type(mt) == "table") and tostring(mt.CTypeName) or "n/a"
      print("MK|" .. keys[i] .. "|0|<non-enumerable CTypeName=" .. ct .. " pairs=" .. cnt(obj) .. ">")
    end
  end
end
print("---END---")
"""


def lua_str_list(items):
    return "".join('"%s",\n' % s for s in items)


def san(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


# ---------------------------------------------------------------------------
# 计划构建
# ---------------------------------------------------------------------------
def load_rows():
    con = sqlite3.connect(str(API_DB))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("select * from api_functions")]
    con.close()
    return rows


def db_tables():
    con = sqlite3.connect(str(GAMEPLAY_DB))
    names = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name")]
    con.close()
    return names


def build_plan(rows):
    """为每行 API 生成探测表达式（分 dot / colon / gameinfo 三类）。"""
    plan = []
    for r in rows:
        tbl, fn, sub = r["table_name"], r["func_name"], r["sub_func_name"]
        dot = r["invoke"].startswith("Dot")
        item = dict(r)
        item["san_table"] = san(tbl)
        if dot:
            if not fn:
                if r["type"] == "QUERY" and r["id"].startswith("Q-GameInfo"):
                    item["kind"] = "gameinfo"
                    item["member_path"] = []
                    item["expr_tmpl"] = "GameInfo." + tbl
                else:  # CONTEXT / OBJECT：命名空间本身是否存在
                    item["kind"] = "namespace"
                    item["member_path"] = []
                    item["expr_tmpl"] = tbl
                    item["alt_expr"] = "GameInfo." + tbl
            else:
                item["kind"] = "dot"
                item["member_path"] = [p for p in (fn, sub) if p]
                item["expr_tmpl"] = ".".join([tbl] + item["member_path"])
                item["base_expr"] = tbl if "." not in tbl else tbl
        else:
            item["kind"] = "colon"
            item["member_path"] = [p for p in (fn, sub) if p]
            if sub:
                item["expr_tmpl"] = "__SC.C_%s_P_%s.%s" % (san(tbl), san(fn), sub)
                item["container_expr"] = "__SC.C_%s_P_%s" % (san(tbl), san(fn))
            else:
                item["expr_tmpl"] = "__SC.C_%s.%s" % (san(tbl), fn) if fn else "__SC.C_%s" % san(tbl)
                item["container_expr"] = "__SC.C_%s" % san(tbl)
            item["base_expr"] = item.get("container_expr", "__SC.C_%s" % san(tbl))
        plan.append(item)
    return plan


def nested_parents(rows):
    """(类, 父方法) -> 是否有子方法；返回需要解析子对象的作业列表。"""
    parents = defaultdict(set)
    for r in rows:
        if r["sub_func_name"]:
            parents[(r["table_name"], r["func_name"])].add(r["sub_func_name"])
    jobs = []
    argmap = {"Territories.GetTerritoryAt": 0, "MapRoutes.GetIndexedPortal": 0}
    for (tbl, fn), subs in sorted(parents.items()):
        if fn == "Create":  # Fractal.Create 需要参数，跳过
            continue
        args = argmap.get(f"{tbl}.{fn}")
        jobs.append((tbl, fn, args, sorted(subs)))
    return jobs


# ---------------------------------------------------------------------------
# 扫描
# ---------------------------------------------------------------------------
def scan_context(ch: Channel, ctx: str, plan, rows, jobs, dbt):
    is_ui = ctx == "ui"
    classes = sorted({r["table_name"] for r in rows if r["invoke"].startswith("Colon")})
    setup = (SETUP_TMPL
             .replace("__IS_UI__", "true" if is_ui else "false")
             .replace("__INCLUDES__", "{" + ", ".join('"%s"' % m for m in SAFE_INCLUDES) + "}" if is_ui else "{}")
             .replace("__CLASSES__", "{" + lua_str_list(classes) + "}"))
    print(f"[{ctx}] setup ...", flush=True)
    setup_lines = ch.run(ctx, setup, timeout=TIMEOUT)

    cls_res = {}
    for ln in setup_lines:
        if ln.startswith("CLS|"):
            p = ln.split("|")
            cls_res[p[1]] = p[2] if len(p) > 2 else "?"

    # 子对象解析（在探测之前，探测表达式依赖 __SC 的 C_x_P_y 键）
    joblua = []
    for tbl, fn, args, subs in jobs:
        a = "nil" if args is None else "{%d}" % args
        joblua.append('{"%s","%s",%s},' % (san(tbl), san(fn), a))
    sub_lines = []
    if joblua:
        print(f"[{ctx}] 解析 {len(joblua)} 个嵌套父对象 ...", flush=True)
        sub_lines = ch.run(ctx, SUBRESOLVE_TMPL.replace("__JOBS__", "\n".join(joblua)), timeout=TIMEOUT)

    # 表达式清单
    exprs = []
    seen = set()

    def add(e):
        if e and e not in seen:
            seen.add(e)
            exprs.append(e)

    for it in plan:
        add(it["expr_tmpl"])
        if it.get("alt_expr"):
            add(it["alt_expr"])
        add(it.get("base_expr"))
        if it["kind"] == "colon":
            add(it.get("container_expr"))
    # 命名空间/全局存在性
    for n in sorted({r["table_name"] for r in rows}):
        add(n)
    # 附加：GameInfo 全库表存在性（超出文档范围的加值项）
    gi = ["GameInfo." + t for t in dbt]

    print(f"[{ctx}] 探测 {len(exprs)} 条表达式 + {len(gi)} 张 GameInfo 表 ...", flush=True)
    probe_lines = []
    all_exprs = exprs + gi
    for i in range(0, len(all_exprs), CHUNK):
        batch = all_exprs[i:i + CHUNK]
        code = PROBE_TMPL.replace("__EXPRS__", lua_str_list(batch))
        probe_lines += ch.run(ctx, code, timeout=TIMEOUT)
        print(f"  [{ctx}] batch {i // CHUNK + 1}/{(len(all_exprs) + CHUNK - 1) // CHUNK} -> {len(probe_lines)} 行", flush=True)

    # 枚举转储（加值：真实方法面 vs 文档）
    enum_names = sorted({r["table_name"].split(".")[0] for r in rows} |
                        {"GameInfo", "Players", "Controls", "ContextPtr", "GlobalParameters", "GameEffects"})
    print(f"[{ctx}] 枚举转储 {len(enum_names)} 个命名空间 ...", flush=True)
    enum_lines = []
    for i in range(0, len(enum_names), 120):
        batch = enum_names[i:i + 120]
        enum_lines += ch.run(ctx, ENUM_TMPL.replace("__NAMES__", lua_str_list(batch)), timeout=TIMEOUT)

    res = {}
    for ln in probe_lines:
        if ln.startswith("R|"):
            p = ln.split("|")
            if len(p) >= 3:
                res[p[1]] = p[2]

    enum_globals, enum_methods = {}, {}
    for ln in enum_lines:
        if ln.startswith("EK|"):
            p = ln.split("|", 6)
            keys = p[6].split(",") if len(p) > 6 and p[6] else []
            nk = int(p[5]) if len(p) > 5 and p[5].isdigit() else len(keys)
            enum_globals[p[1]] = {"type": p[2], "protected": p[3] == "prot=1", "mt": p[4],
                                  "nkeys": nk, "keys": keys}
        elif ln.startswith("MK|"):
            p = ln.split("|", 3)
            keys = p[3].split(",") if len(p) > 3 and p[3] else []
            enum_methods[p[1]] = keys

    return {
        "ctx": ctx,
        "setup_lines": setup_lines,
        "class_resolution": cls_res,
        "sub_lines": sub_lines,
        "probe": res,
        "probe_lines": probe_lines,
        "enum_globals": enum_globals,
        "enum_methods": enum_methods,
        "enum_lines": enum_lines,
    }


def scan_codebuddy_surfaces(ch: Channel, ctx: str, names):
    """CodeBuddyFuncs / CodeBuddyFuncsRaw 的归属面探测（这些命名空间运行时不存在）。"""
    surfaces = (["__SC.C_Control", "__SC.C_ContextPtr", "__SC.C_UIManager", "UI", "UIManager",
                 "InstanceManager", "PopupDialog", "ToolTipHelper", "PopupDialogInGame",
                 "Locale", "Game", "Players", "Map", "GameEffects", "Network", "Input",
                 "UILens", "Options", "Steam", "UserConfiguration", "GameConfiguration",
                 "PlayerConfiguration", "Modding", "AssetPreview", "NotificationManager",
                 "TouchManager", "TTManager", "IconManager", "EffectsManager",
                 "UITutorialManager", "serialize", "Cities", "Units", "CityManager",
                 "UnitManager", "PlayerOperations", "GameCapabilities", "CombatManager",
                 "WorldView", "Territories", "SimUnitSystem", "DiplomacyManager",
                 "DealManager", "GameSummary", "MapConfiguration", "ReportingEvents",
                 "TunerUtilities", "UITree", "g_ToolTipGenerators", "json", "Tools"]
                if ctx == "ui" else
                ["Game", "Players", "Map", "GameEffects", "Cities", "Units", "CityManager",
                 "UnitManager", "PlayerManager", "Automation", "GameConfiguration",
                 "PlayerConfiguration", "WorldBuilder", "TerrainBuilder", "RiverManager",
                 "MapFeatureManager", "StartPositioner", "AutoplayManager", "GameRandomEvents",
                 "MapRoutes", "ResourceBuilder", "RouteBuilder", "ImprovementBuilder",
                 "AreaBuilder", "TerrainManager", "PlayerVisibility", "Fractal", "GameSummary",
                 "CombatManager", "DealManager", "NotificationManager", "Locale",
                 "GlobalParameters", "serialize", "ReportingEvents", "PlayerOperations",
                 "GameCapabilities", "PlayerVisibilityManager", "Territories", "Areas",
                 "GameClimate", "FeatureGenerator", "NaturalWonderGenerator"])
    surfaces = list(dict.fromkeys(surfaces))
    exprs = []
    for s in surfaces:
        for n in names:
            exprs.append(f"{s}.{n}")
    out = {}
    print(f"[{ctx}] CodeBuddy 归属面探测：{len(names)} 名 × {len(surfaces)} 面 = {len(exprs)}", flush=True)
    for i in range(0, len(exprs), CHUNK):
        batch = exprs[i:i + CHUNK]
        lines = ch.run(ctx, PROBE_TMPL.replace("__EXPRS__", lua_str_list(batch)), timeout=TIMEOUT)
        for ln in lines:
            if ln.startswith("R|"):
                p = ln.split("|")
                if len(p) >= 3 and p[2] not in ("nil", "ERR", "CF"):
                    out[p[1]] = p[2]
    return out


def normalize_raw_name(raw: str) -> str | None:
    """从 CodeBuddyFuncsRaw 的 C++ 签名串里抽出候选 Lua 名。"""
    m = re.match(r"^CFunction:\s*([A-Za-z_]\w*)", raw)
    if m:
        return m.group(1)
    m = re.search(r"([A-Za-z_]\w*)\s*\(", raw)
    if m:
        return m.group(1)
    return None


def main():
    OUTROOT.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    plan = build_plan(rows)
    jobs = nested_parents(rows)
    dbt = db_tables()
    print(f"API 行 {len(rows)}；探测计划 {len(plan)}；嵌套父 {len(jobs)}；GameInfo 库表 {len(dbt)}")

    ch = Channel()
    print("已连接：", ch.identity)
    print("状态：gamecore=%s ingame=%s" % (ch.states.get("GameCore_Tuner"), ch.states.get("InGame")))

    results = {}
    for ctx in ("gp", "ui"):
        results[ctx] = scan_context(ch, ctx, plan, rows, jobs, dbt)
        (OUTROOT / f"raw_{ctx}_probe.txt").write_text(
            "\n".join(results[ctx]["setup_lines"] + results[ctx]["sub_lines"] + results[ctx]["probe_lines"]),
            encoding="utf-8")
        (OUTROOT / f"raw_{ctx}_enum.txt").write_text("\n".join(results[ctx]["enum_lines"]), encoding="utf-8")

    # CodeBuddy 归属面探测
    cb_names = sorted({r["func_name"] for r in rows if r["table_name"] == "CodeBuddyFuncs" and r["func_name"]})
    raw_names = sorted({r["func_name"] for r in rows if r["table_name"] == "CodeBuddyFuncsRaw" and r["func_name"]})
    raw_norm = sorted({n for n in (normalize_raw_name(x) for x in raw_names) if n})
    cb = {}
    for ctx in ("ui", "gp"):
        cb[ctx] = {
            "codebuddyfuncs": scan_codebuddy_surfaces(ch, ctx, cb_names),
            "raw_normalized": scan_codebuddy_surfaces(ch, ctx, raw_norm),
        }
    results["codebuddy"] = cb
    results["codebuddy_names"] = cb_names
    results["codebuddy_raw_norm"] = raw_norm

    # 事件类动态代理哨兵探测（自动 vivify 检测）
    dyn = {}
    for ctx in ("gp", "ui"):
        lines = ch.run(ctx, PROBE_TMPL.replace("__EXPRS__", lua_str_list([
            "Events.ZZ_NOT_A_REAL_EVENT_1", "GameEvents.ZZ_NOT_A_REAL_EVENT_1",
            "LuaEvents.ZZ_NOT_A_REAL_EVENT_1", "ReportingEvents.ZZ_NOT_A_REAL_EVENT_1"])), timeout=30)
        dyn[ctx] = {ln.split("|")[1]: ln.split("|")[2] for ln in lines if ln.startswith("R|")}
    results["dynamic_sentinel"] = dyn

    # 收尾复原：移除扫描期新增的全局；若 TunerUtilities 曾被载入，复原全局输入处理器
    cleanup_lua = r"""
local removed = {}
if type(__SCAN_ADDED) == "table" then
  for n in pairs(__SCAN_ADDED) do
    local f = loadstring(n .. " = nil")
    if f then pcall(f) removed[#removed + 1] = n end
  end
end
if __SCAN_ADDED and __SCAN_ADDED["TunerUtilities"] then
  pcall(function() UIManager:SetGlobalInputHandler(function() return false end) end)
  removed[#removed + 1] = "<GlobalInputHandler:reset-noop>"
end
__SC = nil
__SCINFO = nil
__SCAN_ADDED = nil
table.sort(removed)
print("CLEANED|" .. #removed .. "|" .. table.concat(removed, ","))
print("---END---")
"""
    for ctx in ("gp", "ui"):
        try:
            for ln in ch.run(ctx, cleanup_lua, timeout=30):
                print(f"[{ctx}] {ln}")
        except Exception as e:
            print("cleanup warn:", e)

    meta = {
        "identity": ch.identity,
        "states": ch.states,
        "calls": ch.calls,
        "n_rows": len(rows),
        "n_plan": len(plan),
        "n_jobs": len(jobs),
        "n_dbtables": len(dbt),
        "safe_includes": SAFE_INCLUDES,
        "excluded_includes": ["TunerUtilities（加载期 UIManager:SetGlobalInputHandler 副作用）"],
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (OUTROOT / "scan_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTROOT / "results.json").write_text(json.dumps(
        {k: v for k, v in results.items() if k != "codebuddy"} | {"codebuddy": results["codebuddy"]},
        ensure_ascii=False), encoding="utf-8")
    print("扫描完成，tuner 调用次数 =", ch.calls)
    print("输出目录：", OUTROOT)
    ch.sock.close()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
