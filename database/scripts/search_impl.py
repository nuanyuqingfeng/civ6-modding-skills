#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""search_impl.py — 反查「某个游戏对象/效果，原版是怎么实现的」

## 为什么需要它

`rgn_validate` 管的是**引用闭不闭合**（静态校验）；但在**动手写之前**你更需要的是
「原版有没有同类效果、它用了哪个 ModifierType、参数填了什么、挂在什么条件下」。
凭记忆拼 ModifierType + 参数是本项目最容易踩空的一环——引擎不报错，只是不生效。

本工具把官方库里的现成实现**正向查出来**，让你「先搜再抄」，避免「先猜再试」。

## 查询能力

| 入口 | 干什么 |
|------|--------|
| `--object <词或 Type>` | 给对象（文明/领袖/区域/建筑/单位/改良/政策/总督/伟人…），列出它**全部** Modifier 链 |
| `--modifier <词或 Type>` | 按 ModifierType / EffectType 关键词，找**谁用了它** + 该 Modifier 的完整定义 |
| `--effect <EffectType>` | 按 Effect 精确查：哪些 ModifierType 指向它、哪些对象在用它 |

## 「对象 → Modifier」的绑定路径（本工具的核心抽象）

不同对象的 Modifier 挂载位置**不一样**，硬编码会变成十几段 if-else。这里显式建模为
**6 种绑定 kind**（新增对象只加一条注册项）：

| kind | 路径 | 用在 |
|------|------|------|
| `direct` | `XxxModifiers(XxxType, ModifierId)` | 区域/建筑/改良/项目/政策/单位能力/单位晋升/总督/总督晋升 |
| `via_trait` | 对象表 `TraitType` → `TraitModifiers` | 单位/区域/建筑/改良（特色变体走 Trait） |
| `via_table` | 中间表（`CivilizationTraits`/`LeaderTraits`）→ `TraitModifiers` | 文明/领袖 |
| `governor_promotion` | 中间表 `GovernorPromotionSets(GovernorType, GovernorPromotion)` → `GovernorPromotionModifiers` | 总督（晋升树） |
| `gp_action` | `GreatPersonIndividualActionModifiers` | 伟人（激活效果） |
| `gp_birth` | `GreatPersonIndividualBirthModifiers` | 伟人（诞生效果） |

## 递归展开（两条必须防环的分支）

- **嵌套 Modifier**：`ModifierType` 命中 `ATTACH_MODIFIER` 或 `EffectType == EFFECT_ATTACH_MODIFIER`
  → 取参数 `ModifierId` 递归；
- **授予能力**：命中 `GRANT_ABILITY` → 取参数 `AbilityType` → 查 `UnitAbilities` 拿中文名
  → 遍历 `UnitAbilityModifiers` 把该能力**下属全部** Modifier 展开。

> ⚠️ 官方数据里 ATTACH 链**存在成环/自引用**，递归**必须**同时具备
> `visited` 集合与 `MAX_NEST_DEPTH` 限深，否则会挂死。

条件同样递归：`RequirementId` 以 `REQSET_` 开头的是**嵌套条件集**，要继续展开。

## 用法

    python search_impl.py --object 农场
    python search_impl.py --object TRAIT_CIVILIZATION_KHMER_BARAYS
    python search_impl.py --modifier ADJUST_PLOT_YIELD
    python search_impl.py --effect EFFECT_ADJUST_PLOT_YIELD
    python search_impl.py --list-objects              # 列出支持的对象类别
    python search_impl.py --object 农场 --json        # 机读输出

退出码：0 = 有结果；1 = 无结果；2 = 用法错误。

## 与其它工具的分工

- **写前**「原版怎么实现」→ 本工具；
- **写时**「这个 Effect 的参数能填什么」→ `query_effect_args.py`；
- **写后**「引用有没有悬空」→ `rgn_validate_runner.mjs`。

> 思路借鉴自 ModTools 5.4（Siqi，MIT）的 `db/ability_search.py`；
> 本实现为独立重写（纯标准库、对接本 skill 自带库、按本项目规范输出），未拷贝其代码。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from typing import Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(SKILL_DIR, "database", "DebugGameplay.sqlite")
DEFAULT_LOC = os.path.join(SKILL_DIR, "database", "DebugLocalization.sqlite")

MAX_NEST_DEPTH = 8
_ATTACH_RE = re.compile(r"ATTACH_MODIFIER")
_GRANT_ABILITY_RE = re.compile(r"GRANT_ABILITY")

# ------------------------------------------------------------------ 绑定注册表
# 每项：table/type_col/name_col（+ 可选 desc_col）与一组 binding_sources。
# binding_sources 的 kind 语义见模块 docstring 的表。
OBJECT_TYPES: dict[str, dict[str, Any]] = {
    "civilization": {
        "label": "文明", "table": "Civilizations",
        "type_col": "CivilizationType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "CivilizationTraits→TraitModifiers", "kind": "via_table",
             "via_table": "CivilizationTraits", "via_obj_col": "CivilizationType", "trait_col": "TraitType"},
        ],
    },
    "leader": {
        "label": "领袖", "table": "Leaders",
        "type_col": "LeaderType", "name_col": "Name", "desc_col": None,
        "binding_sources": [
            {"label": "LeaderTraits→TraitModifiers", "kind": "via_table",
             "via_table": "LeaderTraits", "via_obj_col": "LeaderType", "trait_col": "TraitType"},
        ],
    },
    "trait": {
        "label": "特质", "table": "Traits",
        "type_col": "TraitType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "TraitModifiers", "kind": "direct",
             "table": "TraitModifiers", "obj_col": "TraitType", "mod_col": "ModifierId"},
        ],
    },
    "district": {
        "label": "区域", "table": "Districts",
        "type_col": "DistrictType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "DistrictModifiers", "kind": "direct",
             "table": "DistrictModifiers", "obj_col": "DistrictType", "mod_col": "ModifierId"},
            {"label": "TraitType→TraitModifiers", "kind": "via_trait", "trait_col": "TraitType"},
        ],
    },
    "building": {
        "label": "建筑", "table": "Buildings",
        "type_col": "BuildingType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "BuildingModifiers", "kind": "direct",
             "table": "BuildingModifiers", "obj_col": "BuildingType", "mod_col": "ModifierId"},
            {"label": "TraitType→TraitModifiers", "kind": "via_trait", "trait_col": "TraitType"},
        ],
    },
    "unit": {
        "label": "单位", "table": "Units",
        "type_col": "UnitType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "TraitType→TraitModifiers", "kind": "via_trait", "trait_col": "TraitType"},
        ],
    },
    "improvement": {
        "label": "改良设施", "table": "Improvements",
        "type_col": "ImprovementType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "ImprovementModifiers", "kind": "direct",
             "table": "ImprovementModifiers", "obj_col": "ImprovementType", "mod_col": "ModifierId"},
            {"label": "TraitType→TraitModifiers", "kind": "via_trait", "trait_col": "TraitType"},
        ],
    },
    "project": {
        "label": "项目", "table": "Projects",
        "type_col": "ProjectType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "ProjectCompletionModifiers", "kind": "direct",
             "table": "ProjectCompletionModifiers", "obj_col": "ProjectType", "mod_col": "ModifierId"},
        ],
    },
    "policy": {
        "label": "政策卡", "table": "Policies",
        "type_col": "PolicyType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "PolicyModifiers", "kind": "direct",
             "table": "PolicyModifiers", "obj_col": "PolicyType", "mod_col": "ModifierId"},
        ],
    },
    "governor": {
        "label": "总督", "table": "Governors",
        "type_col": "GovernorType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "GovernorModifiers", "kind": "direct",
             "table": "GovernorModifiers", "obj_col": "GovernorType", "mod_col": "ModifierId"},
            {"label": "GovernorPromotionSets→GovernorPromotionModifiers", "kind": "governor_promotion"},
            {"label": "TraitType→TraitModifiers", "kind": "via_trait", "trait_col": "TraitType"},
        ],
    },
    "governor_promotion": {
        "label": "总督晋升", "table": "GovernorPromotions",
        "type_col": "GovernorPromotionType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "GovernorPromotionModifiers", "kind": "direct",
             "table": "GovernorPromotionModifiers", "obj_col": "GovernorPromotionType", "mod_col": "ModifierId"},
        ],
    },
    "great_person": {
        "label": "伟人", "table": "GreatPersonIndividuals",
        "type_col": "GreatPersonIndividualType", "name_col": "Name", "desc_col": None,
        "binding_sources": [
            {"label": "GreatPersonIndividualActionModifiers", "kind": "gp_action"},
            {"label": "GreatPersonIndividualBirthModifiers", "kind": "gp_birth"},
        ],
    },
    "unit_ability": {
        "label": "单位能力", "table": "UnitAbilities",
        "type_col": "UnitAbilityType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "UnitAbilityModifiers", "kind": "direct",
             "table": "UnitAbilityModifiers", "obj_col": "UnitAbilityType", "mod_col": "ModifierId"},
        ],
    },
    "unit_promotion": {
        "label": "单位晋升", "table": "UnitPromotions",
        "type_col": "UnitPromotionType", "name_col": "Name", "desc_col": "Description",
        "binding_sources": [
            {"label": "UnitPromotionModifiers", "kind": "direct",
             "table": "UnitPromotionModifiers", "obj_col": "UnitPromotionType", "mod_col": "ModifierId"},
        ],
    },
}

OBJECT_ORDER = ["civilization", "leader", "trait", "district", "building", "unit",
                "improvement", "project", "policy", "governor", "governor_promotion",
                "great_person", "unit_ability", "unit_promotion"]


# ------------------------------------------------------------------ 低层封装

def _rows(con: sqlite3.Connection, sql: str, args: tuple = ()) -> list[dict]:
    try:
        cur = con.execute(sql, args)
    except sqlite3.Error:
        return []
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _one(con: sqlite3.Connection, sql: str, args: tuple = ()) -> Optional[dict]:
    r = _rows(con, sql, args)
    return r[0] if r else None


def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    return bool(_one(con, "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)))


def _columns(con: sqlite3.Connection, table: str) -> list[str]:
    try:
        return [d[1] for d in con.execute("PRAGMA table_info('%s')" % table).fetchall()]
    except sqlite3.Error:
        return []


def _mod_col(con: sqlite3.Connection, table: str, want: str = "ModifierId") -> Optional[str]:
    """解析绑定表里 modifier 列的真实写法（官方混用 `ModifierId` / `ModifierID`）。"""
    for c in _columns(con, table):
        if c.lower() == want.lower():
            return c
    return None


def _obj_col(con: sqlite3.Connection, table: str, want: str) -> Optional[str]:
    for c in _columns(con, table):
        if c.lower() == want.lower():
            return c
    return None


class Loc:
    """官方文本解析（zh_Hans_CN 优先，回退 en_US）。"""

    def __init__(self, con: Optional[sqlite3.Connection]):
        self.con = con
        self._cache: dict[str, str] = {}

    def resolve(self, tag: Any) -> str:
        if not tag:
            return ""
        s = str(tag)
        if s in self._cache:
            return self._cache[s]
        out = ""
        if self.con is not None:
            for lang in ("zh_Hans_CN", "en_US"):
                r = _one(self.con,
                         "SELECT Text FROM LocalizedText WHERE Tag=? AND Language=? LIMIT 1", (s, lang))
                if r and r.get("Text"):
                    out = str(r["Text"]).replace("[NEWLINE]", " ")
                    break
        self._cache[s] = out or s
        return self._cache[s]


# ------------------------------------------------------------------ 递归展开

def expand_modifier(g: sqlite3.Connection, loc: Loc, mid: str,
                    visited: set, depth: int) -> Optional[dict]:
    """展开一个 Modifier（含嵌套 ATTACH / GRANT_ABILITY 与条件集）。"""
    if not mid or depth > MAX_NEST_DEPTH or mid in visited:
        return None
    visited.add(mid)

    m = _one(g, "SELECT * FROM Modifiers WHERE ModifierId=?", (mid,))
    if not m:
        return None
    mtype = str(m.get("ModifierType") or "").strip()
    dyn = _one(g, "SELECT * FROM DynamicModifiers WHERE ModifierType=?", (mtype,))
    effect = str(dyn.get("EffectType") or "") if dyn else ""
    coll = str(dyn.get("CollectionType") or "") if dyn else ""

    args = [{"name": str(r.get("Name") or ""), "value": r.get("Value")}
            for r in _rows(g, "SELECT Name, Value FROM ModifierArguments WHERE ModifierId=?", (mid,))
            if r.get("Name")]

    reqsets = []
    for role in ("SubjectRequirementSetId", "OwnerRequirementSetId"):
        rs = str(m.get(role) or "").strip()
        if rs:
            reqsets.append(expand_reqset(g, loc, role, rs, set(), 0))

    flags = []
    for col, lab in (("Permanent", "永久"), ("RunOnce", "仅一次"),
                     ("NewOnly", "仅新对象"), ("Repeatable", "可重复")):
        try:
            if int(m.get(col) or 0):
                flags.append(lab)
        except (TypeError, ValueError):
            pass
    for col, lab in (("OwnerStackLimit", "所有者上限"), ("SubjectStackLimit", "对象上限")):
        try:
            v = int(m.get(col) or 0)
            if v:
                flags.append("%s %d" % (lab, v))
        except (TypeError, ValueError):
            pass

    node: dict[str, Any] = {
        "modifier_id": mid, "modifier_type": mtype, "effect_type": effect,
        "collection_type": coll, "args": args, "reqsets": reqsets,
        "flags": flags, "nested": [], "nested_kind": "", "ability_type": "", "ability_name": "",
    }

    # ATTACH_MODIFIER：嵌套 Modifier
    is_attach = bool(_ATTACH_RE.search(mtype)) or effect == "EFFECT_ATTACH_MODIFIER"
    if is_attach:
        for a in args:
            if a["name"] == "ModifierId" and a["value"]:
                child = expand_modifier(g, loc, str(a["value"]).strip(), visited, depth + 1)
                if child:
                    node["nested"].append(child)
        if node["nested"]:
            node["nested_kind"] = "attach"

    # GRANT_ABILITY：AbilityType → UnitAbilities → UnitAbilityModifiers
    if bool(_GRANT_ABILITY_RE.search(mtype)) or effect == "EFFECT_GRANT_ABILITY":
        for a in args:
            if a["name"] == "AbilityType" and a["value"]:
                at = str(a["value"]).strip()
                if not at:
                    continue
                ab = _one(g, "SELECT * FROM UnitAbilities WHERE UnitAbilityType=?", (at,))
                node["ability_type"] = at
                node["ability_name"] = loc.resolve(ab.get("Name")) if ab else at
                mcol = _mod_col(g, "UnitAbilityModifiers") or "ModifierId"
                for br in _rows(g, "SELECT %s AS mid FROM UnitAbilityModifiers WHERE UnitAbilityType=?" % mcol, (at,)):
                    child = expand_modifier(g, loc, str(br.get("mid") or ""), visited, depth + 1)
                    if child:
                        node["nested"].append(child)
                if node["nested"]:
                    node["nested_kind"] = "ability"
    return node


def expand_reqset(g: sqlite3.Connection, loc: Loc, role: str, rsid: str,
                  visited: set, depth: int) -> dict:
    """展开条件集；`RequirementId` 以 `REQSET_` 开头的是嵌套条件集，继续递归。"""
    out: dict[str, Any] = {"role": role, "reqset_id": rsid, "requirements": []}
    if not rsid or depth > MAX_NEST_DEPTH or rsid in visited:
        return out
    visited.add(rsid)

    rs = _one(g, "SELECT * FROM RequirementSets WHERE RequirementSetId=?", (rsid,))
    out["logic"] = (rs or {}).get("RequirementSetType", "")

    for rr in _rows(g, "SELECT RequirementId FROM RequirementSetRequirements WHERE RequirementSetId=?", (rsid,)):
        rid = str(rr.get("RequirementId") or "").strip()
        if not rid:
            continue
        if rid.startswith("REQSET_"):
            out["requirements"].append({
                "requirement_id": rid, "requirement_type": "REQSET（嵌套）",
                "args": [], "nested": expand_reqset(g, loc, role, rid, visited, depth + 1)})
            continue
        rq = _one(g, "SELECT * FROM Requirements WHERE RequirementId=?", (rid,))
        if not rq:
            continue
        rargs = ["%s=%s" % (r.get("Name"), r.get("Value"))
                 for r in _rows(g, "SELECT Name, Value FROM RequirementArguments WHERE RequirementId=?", (rid,))
                 if r.get("Name")]
        if str(rq.get("Inverse") or 0) not in ("0", "", "None"):
            rargs.append("INVERSE(取反)")
        out["requirements"].append({
            "requirement_id": rid, "requirement_type": str(rq.get("RequirementType") or ""),
            "args": rargs, "nested": None})
    return out


# ------------------------------------------------------------------ 对象绑定解析

def find_objects(g: sqlite3.Connection, loc: Loc, keyword: str, limit: int = 40) -> list[dict]:
    """按 Type 子串或本地化名子串找对象（跨全部已注册类别）。"""
    kw = keyword.strip()
    if not kw:
        return []
    kwl = kw.lower()
    out: list[dict] = []
    for key in OBJECT_ORDER:
        spec = OBJECT_TYPES[key]
        t, tc, nc = spec["table"], spec["type_col"], spec["name_col"]
        if not _table_exists(g, t):
            continue
        cols = _columns(g, t)
        if tc not in cols:
            continue
        sel = "%s AS type_v, %s AS name_v" % (tc, nc if nc in cols else tc)
        # Type 精确/子串
        for r in _rows(g, "SELECT %s FROM %s WHERE %s LIKE ? LIMIT ?" % (sel, t, tc), ("%" + kw + "%", limit)):
            out.append({"kind": key, "label": spec["label"], "type": r["type_v"],
                        "name": loc.resolve(r["name_v"]) if nc in cols else r["type_v"],
                        "hit": "Type"})
        # 本地化名子串（需经文本库）
        if nc in cols:
            seen = {o["type"] for o in out if o["kind"] == key}
            for r in _rows(g, "SELECT %s FROM %s LIMIT 20000" % (sel, t)):
                ty = r["type_v"]
                if ty in seen:
                    continue
                nm = loc.resolve(r["name_v"])
                if kwl in str(nm).lower():
                    out.append({"kind": key, "label": spec["label"], "type": ty,
                                "name": nm, "hit": "名称"})
                    seen.add(ty)
    # 去重（同 kind+type）
    dedup: dict[tuple, dict] = {}
    for o in out:
        dedup.setdefault((o["kind"], o["type"]), o)
    return list(dedup.values())


def object_modifiers(g: sqlite3.Connection, loc: Loc, kind: str, obj_type: str) -> list[dict]:
    """按注册表解析某对象的全部 (绑定来源, ModifierId)。"""
    spec = OBJECT_TYPES.get(kind)
    if not spec:
        return []
    found: list[dict] = []
    t = spec["table"]
    row = _one(g, "SELECT * FROM %s WHERE %s=?" % (t, spec["type_col"]), (obj_type,))
    if not row:
        return []

    for src in spec["binding_sources"]:
        k = src["kind"]
        if k == "direct":
            bt, oc = src["table"], src["obj_col"]
            if not _table_exists(g, bt):
                continue
            oc_real = _obj_col(g, bt, oc)
            mc = _mod_col(g, bt, src.get("mod_col", "ModifierId"))
            if not oc_real or not mc:
                continue
            for r in _rows(g, "SELECT %s AS mid FROM %s WHERE %s=?" % (mc, bt, oc_real), (obj_type,)):
                found.append({"source": src["label"], "modifier_id": r["mid"]})
        elif k == "via_trait":
            trait = str(row.get(src.get("trait_col", "TraitType")) or "").strip()
            if not trait:
                continue
            mc = _mod_col(g, "TraitModifiers")
            for r in _rows(g, "SELECT %s AS mid FROM TraitModifiers WHERE TraitType=?" % mc, (trait,)):
                found.append({"source": "%s [Trait=%s]" % (src["label"], trait), "modifier_id": r["mid"]})
        elif k == "via_table":
            vt, voc, tcol = src["via_table"], src["via_obj_col"], src["trait_col"]
            if not _table_exists(g, vt):
                continue
            mc = _mod_col(g, "TraitModifiers")
            for vr in _rows(g, "SELECT %s AS tr FROM %s WHERE %s=?" % (tcol, vt, voc), (obj_type,)):
                trait = str(vr.get("tr") or "").strip()
                if not trait:
                    continue
                for r in _rows(g, "SELECT %s AS mid FROM TraitModifiers WHERE TraitType=?" % mc, (trait,)):
                    found.append({"source": "%s [Trait=%s]" % (src["label"], trait), "modifier_id": r["mid"]})
        elif k == "governor_promotion":
            # 真实链路是**中间表 GovernorPromotionSets(GovernorType, GovernorPromotion)**，
            # 不是 `GovernorPromotions.GovernorType`（该项目列在本库 schema 里根本不存在；
            # 本库 GovernorPromotions 只有 Type/Name/Desc/Level/Column/BaseAbility）。
            if not _table_exists(g, "GovernorPromotionSets"):
                continue
            mc = _mod_col(g, "GovernorPromotionModifiers")
            for pr in _rows(g, "SELECT GovernorPromotion AS pt FROM GovernorPromotionSets WHERE GovernorType=?",
                            (obj_type,)):
                pt = pr.get("pt")
                for r in _rows(g, "SELECT %s AS mid FROM GovernorPromotionModifiers WHERE GovernorPromotionType=?" % mc,
                               (pt,)):
                    found.append({"source": "晋升 %s" % pt, "modifier_id": r["mid"]})
        elif k in ("gp_action", "gp_birth"):
            bt = src["table"] if "table" in src else (
                "GreatPersonIndividualActionModifiers" if k == "gp_action"
                else "GreatPersonIndividualBirthModifiers")
            if not _table_exists(g, bt):
                continue
            mc = _mod_col(g, bt)
            for r in _rows(g, "SELECT %s AS mid FROM %s WHERE GreatPersonIndividualType=?" % (mc, bt), (obj_type,)):
                found.append({"source": src["label"], "modifier_id": r["mid"]})

    # 去重保序
    seen, uniq = set(), []
    for f in found:
        key = (f["source"], f["modifier_id"])
        if key not in seen and f["modifier_id"]:
            seen.add(key)
            uniq.append(f)
    return uniq


# ------------------------------------------------------------------ 输出

def _fmt_args(args: list[dict]) -> str:
    return ", ".join("%s=%s" % (a["name"], a["value"]) for a in args) or "-"


def _print_node(node: dict, indent: int = 1, loc: Loc = None) -> None:
    pad = "    " * indent
    flags = ("  [" + "/".join(node["flags"]) + "]") if node.get("flags") else ""
    print("%s%s [%s]  参数: %s%s" % (
        pad, node["modifier_id"], node.get("effect_type") or node.get("modifier_type") or "?",
        _fmt_args(node.get("args") or []), flags))
    if node.get("collection_type"):
        print("%s    作用域: %s" % (pad, node["collection_type"]))
    for rs in node.get("reqsets") or []:
        _print_reqset(rs, indent + 1)
    if node.get("nested_kind") == "ability":
        print("%s    授予能力: %s (%s) → %d 个 Modifier" % (
            pad, node.get("ability_name"), node.get("ability_type"), len(node["nested"])))
    for ch in node.get("nested") or []:
        _print_node(ch, indent + 1, loc)


def _print_reqset(rs: dict, indent: int) -> None:
    pad = "    " * indent
    print("%s条件集(%s) %s%s" % (pad, rs.get("role", ""), rs.get("reqset_id", ""),
                                 ("  [" + str(rs.get("logic")) + "]") if rs.get("logic") else ""))
    for rq in rs.get("requirements") or []:
        a = ("  args=[%s]" % "; ".join(rq["args"])) if rq.get("args") else ""
        print("%s    - %s [%s]%s" % (pad, rq["requirement_id"], rq["requirement_type"], a))
        if rq.get("nested"):
            _print_reqset(rq["nested"], indent + 2)


def _connect(path: str) -> Optional[sqlite3.Connection]:
    if not path or not os.path.isfile(path):
        return None
    try:
        return sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True)
    except sqlite3.Error:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="反查游戏对象/效果的现成 Modifier 实现（先搜再抄）")
    ap.add_argument("--db", default=DEFAULT_DB, help="游戏库（默认 skill 自带 DebugGameplay.sqlite）")
    ap.add_argument("--loc", default=DEFAULT_LOC, help="文本库（默认 DebugLocalization.sqlite）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--object", help="对象关键词或 Type（文明/领袖/区域/建筑/单位/改良/政策/总督/伟人/能力/晋升）")
    g.add_argument("--modifier", help="ModifierType / EffectType 关键词：谁在用它")
    g.add_argument("--effect", help="EffectType 精确查：哪些 ModifierType 指向它")
    g.add_argument("--list-objects", action="store_true", help="列出支持的对象类别")
    ap.add_argument("--json", action="store_true", help="机读 JSON 输出")
    ap.add_argument("--limit", type=int, default=20, help="--modifier/--effect 最多列多少个实现（默认 20）")
    args = ap.parse_args()

    if args.list_objects:
        print("支持的对象类别（kind / 标签 / 绑定路径）:")
        for k in OBJECT_ORDER:
            s = OBJECT_TYPES[k]
            paths = ", ".join(b["kind"] for b in s["binding_sources"])
            print("  %-18s %-8s %s  ← %s" % (k, s["label"], s["table"], paths))
        return 0

    gcon = _connect(args.db)
    if gcon is None:
        raise SystemExit("找不到游戏库：%s" % args.db)
    loc = Loc(_connect(args.loc))

    # ---- 模式 1：按对象
    if args.object:
        hits = find_objects(gcon, loc, args.object)
        if not hits:
            print("未找到与「%s」相关的对象。" % args.object)
            print("提示：用 --list-objects 看支持的类别；或直接给完整 Type（如 IMPROVEMENT_FARM）。")
            return 1
        payload = []
        shown = 0
        for o in hits[:args.limit]:
            mods = object_modifiers(gcon, loc, o["kind"], o["type"])
            if not mods and o["hit"] != "Type":
                continue
            payload.append({"object": o, "modifiers": mods})
            if not args.json:
                print("[%s] %s (%s) — 命中: %s" % (o["label"], o["name"], o["type"], o["hit"]))
                if not mods:
                    print("    （无 Modifier —— 该对象不走注册表里的绑定路径）")
                for m in mods:
                    node = expand_modifier(gcon, loc, str(m["modifier_id"]), set(), 0)
                    if node:
                        print("  %s:" % m["source"])
                        _print_node(node, 2, loc)
                    else:
                        print("  %s: %s （Modifiers 表里查不到该 ModifierId）" % (m["source"], m["modifier_id"]))
                print()
            shown += 1
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=1))
        if shown == 0:
            print("找到对象但都没有 Modifier 实现。")
            return 1
        return 0

    # ---- 模式 2：按 Effect（精确）
    if args.effect:
        eff = args.effect.strip()
        mts = _rows(gcon,
                    "SELECT DISTINCT ModifierType, CollectionType FROM DynamicModifiers WHERE EffectType=?", (eff,))
        if not mts:
            print("无结果：没有 ModifierType 指向 %s" % eff)
            print("提示：用 `python query_effect_args.py --effect %s` 看该 Effect 的参数签名。" % eff)
            return 1
        print("EffectType: %s" % eff)
        print("指向它的 ModifierType 共 %d 个：" % len(mts))
        for m in mts[:args.limit]:
            print("  %-62s %s" % (m["ModifierType"], m["CollectionType"]))
        print()
        print("参考实现（官方实际用例，最多 %d 条）：" % args.limit)
        for m in mts[:args.limit]:
            ex = _one(gcon, "SELECT ModifierId FROM Modifiers WHERE ModifierType=? LIMIT 1", (m["ModifierType"],))
            if not ex:
                continue
            node = expand_modifier(gcon, loc, str(ex["ModifierId"]), set(), 0)
            if node:
                _print_node(node, 1, loc)
                print()
        return 0

    # ---- 模式 3：按关键词找 Modifier / Effect
    if args.modifier:
        kw = "%" + args.modifier.strip() + "%"
        hits = _rows(gcon, """
            SELECT DISTINCT d.ModifierType, d.EffectType, d.CollectionType
            FROM DynamicModifiers d
            WHERE d.ModifierType LIKE ? OR d.EffectType LIKE ?
            ORDER BY d.EffectType, d.ModifierType LIMIT ?""", (kw, kw, args.limit))
        if not hits:
            print("未找到匹配「%s」的 ModifierType / EffectType。" % args.modifier)
            print("提示：换个关键词（如 YIELD_PRODUCTION / PLOT_YIELD / ATTACH）；"
                  "或用 `--object <对象>` 从对象侧反查。")
            return 1
        payload = []
        print("匹配到 %d 个 ModifierType（含官方用途示例）：" % len(hits))
        for h in hits:
            ex = _one(gcon, "SELECT ModifierId FROM Modifiers WHERE ModifierType=? LIMIT 1", (h["ModifierType"],))
            payload.append({"modifier_type": h["ModifierType"], "effect_type": h["EffectType"],
                            "collection_type": h["CollectionType"],
                            "example_modifier": (ex or {}).get("ModifierId")})
            if not args.json:
                print()
                print("  %s  [%s]  %s" % (h["ModifierType"], h["EffectType"], h["CollectionType"]))
                if ex:
                    node = expand_modifier(gcon, loc, str(ex["ModifierId"]), set(), 0)
                    if node:
                        _print_node(node, 2, loc)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
