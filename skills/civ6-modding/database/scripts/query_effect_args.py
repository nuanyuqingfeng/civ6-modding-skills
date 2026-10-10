#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""query_effect_args.py — 查「某个 EffectType / ModifierType 该填哪些参数、参数能填什么值」

## 为什么需要它

写 Modifier 时最容易踩空的一环是 `ModifierArguments.Value` **到底能填什么**：
`MODIFIER_ARGUMENTS.md` 只给了参数名的分类说明与少数枚举，没有逐 Effect 的取值域；
而填错的后果是**静默失败**（引擎不报错，效果不生效）。

本工具把三份数据合起来给出答案：

| 来源 | 提供什么 | 权威性 |
|------|---------|--------|
| `DebugGameplay.sqlite` 的 `GameEffectArguments` | 参数名 / 类型 / 默认值 / Required / Min-Max / **DatabaseKind** | 引擎自带声明（部分 Effect 缺） |
| `DebugGameplay.sqlite` 的 `Types` + `DatabaseKind` | **该参数可取的全部具体值**（如 KIND_YIELD → 6 个 YIELD_*） | 权威全集 |
| `DebugGameplay.sqlite` 实际 `ModifierArguments` 用法 | 官方实际填过什么值（观测样本，用于对照） | 经验值 |

**取值域的两级口径**（重要，别混用）：

- `DatabaseKind` → `Types` 是**全集**（官方声明的合法取值范围）；
- 实际 `ModifierArguments` 是**官方用过的子集**（全集里有些组合官方没用过，不代表非法）。
  两者都会打印，别把"官方没用过"当成"不能用"。

## 用法

    # 查一个 Effect 的参数签名 + 取值域
    python query_effect_args.py --effect EFFECT_ADJUST_PLOT_YIELD

    # 查一个 ModifierType（自动解析到它的 EffectType）
    python query_effect_args.py --modifier MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE

    # 模糊搜参数名 / Effect 名
    python query_effect_args.py --search Yield
    python query_effect_args.py --search YIELD --only-effect

    # 只看某参数在各 Effect 里的取值域
    python query_effect_args.py --arg YieldType

    # 导出全量 JSON（供别的脚本消费）
    python query_effect_args.py --dump-json <out.json>

退出码：0 = 有结果；1 = 无结果；2 = 参数错误。
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(SKILL_DIR, "database", "DebugGameplay.sqlite")

# GameEffectArguments.ArgumentType 的可读化
TYPE_NOTE = {
    "int": "整数",
    "bool": "布尔（true/false）",
    "float": "浮点",
    "database": "数据库 Type（见 DatabaseKind 列出的全集）",
    "string": "字符串",
}


def connect(db_path: str) -> sqlite3.Connection:
    if not os.path.isfile(db_path):
        raise SystemExit("找不到基础库：%s" % db_path)
    con = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"), uri=True)
    con.row_factory = sqlite3.Row
    return con


def kind_values(con: sqlite3.Connection, kind: str) -> list[str]:
    """DatabaseKind → Types 表里该 Kind 的全部具体值（权威全集）。"""
    if not kind:
        return []
    try:
        return [r[0] for r in con.execute(
            "SELECT Type FROM Types WHERE Kind = ? ORDER BY Type", (kind,))]
    except sqlite3.Error:
        return []


def infer_kinds(con: sqlite3.Connection, name: str) -> list[str]:
    """按参数名反查 DatabaseKind（同一参数名在别的 Effect 里声明过就沿用）。

    解决「该 Effect 引擎没声明参数，但参数名是全库通用的」这一情况
    （如 YieldType 在 EFFECT_ADJUST_CITY_YIELD_CHANGE 无声明，但别处声明为 KIND_YIELD）。
    """
    try:
        return sorted({r[0] for r in con.execute(
            "SELECT DISTINCT DatabaseKind FROM GameEffectArguments "
            "WHERE Name = ? AND DatabaseKind IS NOT NULL AND DatabaseKind <> ''", (name,))})
    except sqlite3.Error:
        return []


def declared_args(con: sqlite3.Connection, effect: str) -> list[sqlite3.Row]:
    """GameEffectArguments 里该 Effect 的声明（引擎自带，可能为空）。"""
    return list(con.execute(
        "SELECT Name, ArgumentType, DefaultValue, Required, MinValue, MaxValue, DatabaseKind, Description "
        "FROM GameEffectArguments WHERE Type = ? ORDER BY Required DESC, Name", (effect,)))


def observed_args(con: sqlite3.Connection, effect: str) -> dict[str, list[str]]:
    """官方实际用法：该 Effect 下每个参数填过的值（按出现次数降序）。

    关联链：ModifierArguments.ModifierId → Modifiers.ModifierType
            → DynamicModifiers.ModifierType → EffectType
    """
    out: dict[str, list[str]] = {}
    q = """
        SELECT ma.Name, ma.Value, COUNT(*) AS n
        FROM ModifierArguments ma
        JOIN Modifiers m        ON m.ModifierId   = ma.ModifierId
        JOIN DynamicModifiers d ON d.ModifierType = m.ModifierType
        WHERE d.EffectType = ?
        GROUP BY ma.Name, ma.Value
        ORDER BY ma.Name, n DESC
    """
    try:
        for r in con.execute(q, (effect,)):
            out.setdefault(r["Name"], []).append(r["Value"])
    except sqlite3.Error:
        pass
    return out


def resolve_modifier(con: sqlite3.Connection, modifier: str):
    """ModifierType → (EffectType, CollectionType)；找不到返回 (None, None)。"""
    r = con.execute(
        "SELECT EffectType, CollectionType FROM DynamicModifiers WHERE ModifierType = ?",
        (modifier,)).fetchone()
    return (r["EffectType"], r["CollectionType"]) if r else (None, None)


def print_effect(con: sqlite3.Connection, effect: str, show_all_kind: bool = False) -> bool:
    decl = declared_args(con, effect)
    obs = observed_args(con, effect)

    # 该 Effect 被哪些 ModifierType 使用（给"我要写哪个 ModifierType"用）
    mts = [r[0] for r in con.execute(
        "SELECT DISTINCT ModifierType FROM DynamicModifiers WHERE EffectType = ? ORDER BY ModifierType",
        (effect,))]

    if not decl and not obs and not mts:
        return False

    print("=" * 78)
    print("EffectType : %s" % effect)
    if mts:
        print("ModifierType(%d): %s" % (len(mts), ", ".join(mts[:8]) + (" ..." if len(mts) > 8 else "")))
    kinds = sorted({r["DatabaseKind"] for r in decl if r["DatabaseKind"]})
    print("声明来源   : GameEffectArguments %d 条%s" % (
        len(decl), "" if decl else "  ← 引擎未声明，仅观测值可用"))
    print()

    # 参数全集 = 声明 ∪ 观测
    names: list[str] = []
    for r in decl:
        if r["Name"] not in names:
            names.append(r["Name"])
    for n in obs:
        if n not in names:
            names.append(n)

    if not names:
        print("  （无参数）")
        return True

    for n in names:
        d = next((r for r in decl if r["Name"] == n), None)
        vals = obs.get(n, [])
        line = "  • %s" % n
        meta = []
        if d:
            at = d["ArgumentType"] or "?"
            meta.append(TYPE_NOTE.get(at, at))
            if d["Required"]:
                meta.append("必填")
            else:
                meta.append("可选")
            if d["DefaultValue"] not in (None, ""):
                meta.append("默认=%s" % d["DefaultValue"])
            if d["MinValue"] is not None or d["MaxValue"] is not None:
                meta.append("范围=[%s, %s]" % (d["MinValue"], d["MaxValue"]))
        if meta:
            line += "  (%s)" % ", ".join(meta)
        print(line)

        if d and d["Description"]:
            print("      说明: %s" % d["Description"])

        # 权威全集
        kind = d["DatabaseKind"] if d else None
        if kind:
            kv = kind_values(con, kind)
            print("      全集 [%s] %d 个: %s" % (
                kind, len(kv), ", ".join(kv[:12]) + (" ..." if len(kv) > 12 else "")))
            if show_all_kind and kv:
                for v in kv:
                    print("          %s" % v)
        elif d and (d["ArgumentType"] == "database"):
            print("      全集: ← 声明为 database 但未给出 DatabaseKind（按同参数名其它 Effect 推断）")
            # 用同名参数在别的 Effect 里的 DatabaseKind 兜底
            for k in infer_kinds(con, n):
                kv = kind_values(con, k)
                print("         [%s] %d 个: %s" % (k, len(kv), ", ".join(kv[:12])))
        elif not d:
            # 未声明：按同参数名反查推断取值域（标注为推断，避免与引擎声明混淆）
            for k in infer_kinds(con, n):
                kv = kind_values(con, k)
                print("      全集 [%s] %d 个（按同参数名推断）: %s" % (
                    k, len(kv), ", ".join(kv[:12]) + (" ..." if len(kv) > 12 else "")))
                if show_all_kind and kv:
                    for v in kv:
                        print("          %s" % v)

        # 官方观测值
        if vals:
            shown = ", ".join(str(v) for v in vals[:10])
            print("      官方用过 %d 种: %s%s" % (
                len(vals), shown, " ..." if len(vals) > 10 else ""))
        else:
            print("      官方用过 0 种（该 Effect 在官方库里无实际用例 —— 写前建议用 civ6-tuner 实测）")
    print()
    return True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="查 Effect/Modifier 的参数签名与取值域（含 DatabaseKind→Types 全集）")
    ap.add_argument("--db", default=DEFAULT_DB, help="基础库（默认 skill 自带 DebugGameplay.sqlite）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--effect", help="EffectType（如 EFFECT_ADJUST_PLOT_YIELD）")
    g.add_argument("--modifier", help="ModifierType（自动解析其 EffectType）")
    g.add_argument("--arg", help="按参数名查：列出所有用它的 Effect 与该参数的取值域")
    g.add_argument("--search", help="模糊搜 EffectType / 参数名")
    g.add_argument("--dump-json", metavar="OUT", help="导出全量参数取值域 JSON")
    ap.add_argument("--only-effect", action="store_true", help="--search 只搜 EffectType")
    ap.add_argument("--list-kind", action="store_true", help="打印 DatabaseKind 全集（不截断）")
    args = ap.parse_args()

    con = connect(args.db)

    if args.dump_json:
        payload = {}
        for r in con.execute(
                "SELECT DISTINCT Type FROM GameEffectArguments WHERE Type LIKE 'EFFECT_%' "
                "UNION SELECT DISTINCT EffectType FROM DynamicModifiers WHERE EffectType LIKE 'EFFECT_%'"):
            eff = r[0]
            if not eff:
                continue
            decl = declared_args(con, eff)
            obs = observed_args(con, eff)
            item = {"declared": {}, "observed": {k: v for k, v in obs.items()}}
            for d in decl:
                e = {"type": d["ArgumentType"], "required": bool(d["Required"]),
                     "default": d["DefaultValue"], "min": d["MinValue"], "max": d["MaxValue"]}
                if d["DatabaseKind"]:
                    e["databaseKind"] = d["DatabaseKind"]
                    e["values"] = kind_values(con, d["DatabaseKind"])
                item["declared"][d["Name"]] = e
            if item["declared"] or item["observed"]:
                payload[eff] = item
        with open(args.dump_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=True)
        print("已导出 %d 个 EffectType → %s" % (len(payload), args.dump_json))
        return 0

    if args.effect:
        if not any((declared_args(con, args.effect), observed_args(con, args.effect))):
            print("无结果：%s" % args.effect)
            print("提示：用 `python search_impl.py --effect %s` 看原版哪些 ModifierType/对象用了它；" % args.effect)
            print("      或用 `python search_impl.py --modifier <关键词>` 从关键词反查。")
            return 1
        return 0 if print_effect(con, args.effect, args.list_kind) else _miss(args.effect)

    if args.modifier:
        eff, coll = resolve_modifier(con, args.modifier)
        if not eff:
            return _miss(args.modifier, what="ModifierType")
        print("ModifierType : %s" % args.modifier)
        print("Collection   : %s" % (coll or "(未声明)"))
        print()
        print_effect(con, eff, args.list_kind)
        return 0

    if args.arg:
        rows = list(con.execute(
            "SELECT DISTINCT Type, Name, ArgumentType, DatabaseKind FROM GameEffectArguments "
            "WHERE Name = ? ORDER BY Type", (args.arg,)))
        if not rows:
            # 退化：只按观测用法
            obs = list(con.execute(
                "SELECT DISTINCT d.EffectType FROM ModifierArguments ma "
                "JOIN Modifiers m ON m.ModifierId=ma.ModifierId "
                "JOIN DynamicModifiers d ON d.ModifierType=m.ModifierType "
                "WHERE ma.Name=? ORDER BY 1", (args.arg,)))
            if not obs:
                return _miss(args.arg, what="参数名")
            print("参数 %s：引擎未声明，观测到 %d 个 Effect 在用" % (args.arg, len(obs)))
        for r in rows:
            kv = kind_values(con, r["DatabaseKind"])
            print("%-70s %-10s %s" % (r["Type"], r["ArgumentType"] or "?",
                                      ("%s (%d) %s" % (r["DatabaseKind"], len(kv), ", ".join(kv[:8]))) if kv else ""))
        return 0

    if args.search:
        kw = "%" + args.search + "%"
        hits = []
        if not args.only_effect:
            hits = [("ARG  ", r[0]) for r in con.execute(
                "SELECT DISTINCT Name FROM GameEffectArguments WHERE Name LIKE ? ORDER BY Name", (kw,))]
        hits += [("EFF  ", r[0]) for r in con.execute(
            "SELECT DISTINCT Type FROM GameEffectArguments WHERE Type LIKE ? ORDER BY Type", (kw,))]
        hits += [("MOD  ", r[0]) for r in con.execute(
            "SELECT DISTINCT ModifierType FROM DynamicModifiers WHERE ModifierType LIKE ? ORDER BY ModifierType", (kw,))]
        seen, uniq = set(), []
        for tag, v in hits:
            if v and (tag, v) not in seen:
                seen.add((tag, v))
                uniq.append((tag, v))
        if not uniq:
            return _miss(args.search)
        for tag, v in uniq[:120]:
            print("%s %s" % (tag, v))
        if len(uniq) > 120:
            print("... 另 %d 条" % (len(uniq) - 120))
        return 0

    return 2


def _miss(q: str, what: str = "EffectType") -> int:
    print("无结果：%s 『%s』" % (what, q))
    print("提示：用 --search <关键词> 模糊搜；或确认基础库是否含该内容。")
    print("      查「原版谁在用它」→ `python search_impl.py --modifier <关键词>`。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
