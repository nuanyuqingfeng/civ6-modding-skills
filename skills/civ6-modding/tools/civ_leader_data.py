# -*- coding: utf-8 -*-
r"""civ_leader_data.py — 新文明 / 新领袖的**数据与文本机械推导**（规格 JSON → SQL）

## 解决什么

新文明/新领袖要往 10+ 张表里写行、还要把每条文本翻成 8 种语言 —— 手工写极易**漏表**
（漏 `CivilizationLeaders` 就进不了选人界面）、**漏语言**、**tag 拼错**（拼错即静默显示
`LOC_XXX` 原文）。本工具把这些**机械推导**收敛成一处：从一份规格 JSON 出三个 SQL。

## 列名来源（**全部实测，禁止凭记忆**）

`database/DebugGameplay.sqlite`（gameplay 库）：
  Civilizations(7)            CivilizationType, Name, Description, Adjective,
                              RandomCityNameDepth, StartingCivilizationLevelType, Ethnicity
  Leaders(8)                  LeaderType, Name, OperationList, IsBarbarianLeader,
                              InheritFrom, SceneLayers, Sex, SameSexPercentage
  CivilizationTraits(2)       CivilizationType, TraitType
  LeaderTraits(2)             LeaderType, TraitType
  CivilizationLeaders(3)      LeaderType, CivilizationType, CapitalName
  CivilizationInfo(4)         CivilizationType, Header, Caption, SortIndex
  CityNames(6)                ID, CivilizationType, LeaderType, ContinentType, CityName, SortIndex
  CivilizationCitizenNames(4) CivilizationType, CitizenName, Female, Modern
  CivilizationAudioTags(2)    CivilizationType, MusicOverride
  StartBiasTerrains(3)        CivilizationType, TerrainType, Tier
  LeaderQuotes(3)             LeaderType, Quote, QuoteAudio

`database/DebugConfiguration.sqlite`（Config 库；`Players` 属前端配置，**不在 gameplay 库**）：
  Players(18)   Domain, CivilizationType, LeaderType, LeaderName, LeaderIcon,
                CivilizationName, CivilizationIcon, LeaderAbilityName, LeaderAbilityDescription,
                LeaderAbilityIcon, CivilizationAbilityName, CivilizationAbilityDescription,
                CivilizationAbilityIcon, Portrait, PortraitBackground, PlayerColor,
                HumanPlayable, SortIndex
  PlayerItems(8) Domain, CivilizationType, LeaderType, Type, Name, Description, Icon, SortIndex

> `Players.Portrait` / `PortraitBackground` 是**自由字符串列**，指向 XLP 条目名；
> 第三方选人界面适配（如 Suk）正是 UPDATE 这两列，见 civ6-asset-forge。

## 用法

    python civ_leader_data.py <spec.json> --project <工程根>          # 预演（不写盘）
    python civ_leader_data.py <spec.json> --project <工程根> --write
    python civ_leader_data.py <spec.json> --check                     # 只校验规格

产出（写到工程内，需自行在 `.civ6proj` 注册；本工具会打印该注册什么）：
    Data/CivLeader_<Slug>.sql     gameplay：Civilizations/Leaders/Traits/Leaders 关联/城市名…
    Data/Config_<Slug>.sql        Config：Players + PlayerItems（选人界面与游戏设置）
    Text/Text_<Slug>.sql          8 语言 UpdateText（**游戏内文本必须走这条**）

退出码：0 成功 / 1 规格或写入错误 / 2 规格有告警（可继续）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 8 语言（与工程既有 Text/ 目录一致）
LANGS = ["en_US", "zh_Hans_CN", "zh_Hant_HK", "ja_JP", "ko_KR", "de_DE", "es_ES", "fr_FR"]
DEFAULT_DOMAIN = "Players:Expansion2_Players"
CITYNAME_BASE = 1000000        # CityNames.ID 起始值（避免与官方冲突）


def q(v):
    """SQL 字面量。None → NULL；数字原样；其余单引号转义。"""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s.upper() in ("NULL",):
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


_ROWS = []          # [(table, rowdict)] —— 生成时记账，末尾做 NOT NULL 自检


def ins(table, cols, row):
    _ROWS.append((table, row))
    return "INSERT OR REPLACE INTO %s (%s) VALUES (%s);" % (
        table, ", ".join(cols), ", ".join(q(row.get(c)) for c in cols))


def _notnull_map():
    """→ {表名: [NOT NULL 且无默认值的列]}。库缺失时返回 {}（跳过该项校验）。

    ★ 这张表是**从库实测**来的，不是猜的：例如实测 Civilizations.StartingCivilizationLevelType
    与 CivilizationLeaders.CapitalName 都是 NOT NULL —— 漏了它们，生成的 SQL 会在
    游戏加载时报 `NOT NULL constraint failed`，而**在工具侧静默通过**。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    for name in ("DebugGameplay.sqlite", "DebugConfiguration.sqlite"):
        p = os.path.join(os.path.dirname(here), "database", name)
        if not os.path.isfile(p):
            continue
        try:
            con = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)
            for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                cols = [r[1] for r in con.execute("PRAGMA table_info(%s)" % t)
                        if (r[3] or r[5]) and r[4] is None]
                if cols:
                    out[t] = cols
            con.close()
        except Exception:
            continue
    return out


def check_notnull(problems):
    """按库实测的 NOT NULL 约束校验已记账的行。"""
    schema = _notnull_map()
    if not schema:
        return False                       # 库不可用 → 跳过，不误报
    seen = set()
    for table, row in _ROWS:
        for c in schema.get(table, []):
            if row.get(c) is None:
                key = (table, c)
                if key not in seen:
                    seen.add(key)
                    problems.append("%s.%s 是 NOT NULL（实测约束），规格里必须给出" % (table, c))
    return True


def build(spec):
    """→ (gameplay_sql, config_sql, text_sql, problems, warns, tags)"""
    problems, warns = [], []
    _ROWS.clear()
    civ = spec.get("civilization") or {}
    leaders = spec.get("leaders") or []
    text = spec.get("text") or {}
    if not civ.get("type"):
        problems.append("civilization.type 必填（如 CIVILIZATION_RGN_X）")
    if not leaders:
        problems.append("leaders 至少一项")
    for i, ld in enumerate(leaders):
        if not ld.get("type"):
            problems.append("leaders[%d].type 必填" % i)

    cid = civ.get("type")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", (cid or "Mod").replace("CIVILIZATION_", "")).strip("_") or "Mod"
    domain = spec.get("domain") or DEFAULT_DOMAIN

    # ---- 文本 tag 闭包：所有被引用的 tag 必须有文本块 ----
    all_tags = []

    def need(tag, why):
        if not tag:
            return
        all_tags.append(tag)
        if tag not in text:
            problems.append("缺文本块：%s（%s）" % (tag, why))

    civ_name = civ.get("name") or (("LOC_%s_NAME" % cid) if cid else None)
    civ_adj = civ.get("adjective")
    civ_desc = civ.get("description")
    need(civ_name, "Civilizations.Name")
    need(civ_adj, "Civilizations.Adjective")
    need(civ_desc, "Civilizations.Description")
    for ld in leaders:
        lt = ld.get("type")
        need(ld.get("name") or ("LOC_%s_NAME" % lt), "%s Leaders.Name" % lt)
        need(ld.get("quote"), "%s LeaderQuotes.Quote" % lt)

    # ---- gameplay ----
    g = ["-- %s —— gameplay 数据（由 civ_leader_data.py 生成，勿手改）" % slug,
         "-- 列名来源：database/DebugGameplay.sqlite 实测", ""]
    if cid:
        g.append(ins("Civilizations",
                     ["CivilizationType", "Name", "Description", "Adjective",
                      "RandomCityNameDepth", "StartingCivilizationLevelType", "Ethnicity"],
                     {"CivilizationType": cid, "Name": civ_name, "Description": civ_desc,
                      "Adjective": civ_adj,
                      "RandomCityNameDepth": civ.get("random_city_name_depth"),
                      "StartingCivilizationLevelType": civ.get("starting_level"),
                      "Ethnicity": civ.get("ethnicity")}))
        for t in (civ.get("traits") or []):
            g.append(ins("CivilizationTraits", ["CivilizationType", "TraitType"],
                         {"CivilizationType": cid, "TraitType": t}))
        # ★ MusicOverride 是 **0/1 布尔标记**，不是音乐 tag 字符串！
        # 实测：官方 CivilizationAudioTags 全表 15 行、MusicOverride 取值只有 1；
        # 该列有 CHECK (MusicOverride IN (0,1))，写字符串会被库直接拒绝。
        # 真正的 BGM（音乐切换/bank）走 Wwise + Audio 库，见 civ6-audio-pipeline skill。
        if civ.get("music_override") is not None:
            g.append(ins("CivilizationAudioTags", ["CivilizationType", "MusicOverride"],
                         {"CivilizationType": cid,
                          "MusicOverride": 1 if civ["music_override"] else 0}))
        for b in (civ.get("start_bias_terrains") or []):
            g.append(ins("StartBiasTerrains", ["CivilizationType", "TerrainType", "Tier"],
                         {"CivilizationType": cid, "TerrainType": b.get("terrain"),
                          "Tier": b.get("tier")}))
        if civ.get("info"):
            g.append(ins("CivilizationInfo",
                         ["CivilizationType", "Header", "Caption", "SortIndex"],
                         {"CivilizationType": cid, "Header": civ["info"].get("header"),
                          "Caption": civ["info"].get("caption"),
                          "SortIndex": civ["info"].get("sort_index")}))
        for i, cn in enumerate(civ.get("cities") or []):
            g.append(ins("CityNames",
                         ["ID", "CivilizationType", "LeaderType", "ContinentType",
                          "CityName", "SortIndex"],
                         {"ID": civ.get("city_id_base", CITYNAME_BASE) + i,
                          "CivilizationType": cid, "LeaderType": None,
                          "ContinentType": None, "CityName": cn, "SortIndex": i + 1}))
        for cn in (civ.get("citizens") or []):
            if isinstance(cn, dict):
                g.append(ins("CivilizationCitizenNames",
                             ["CivilizationType", "CitizenName", "Female", "Modern"],
                             {"CivilizationType": cid, "CitizenName": cn.get("name"),
                              "Female": cn.get("female"), "Modern": cn.get("modern")}))
            else:
                g.append(ins("CivilizationCitizenNames",
                             ["CivilizationType", "CitizenName", "Female", "Modern"],
                             {"CivilizationType": cid, "CitizenName": cn,
                              "Female": 0, "Modern": 0}))
        for t in (civ.get("named_places") or []):
            tbl = t.get("table")
            if not tbl:
                warns.append("named_places 项缺 table（如 NamedMountainCivilizations），已跳过")
                continue
            # ★ 列名**不是** `Name`：实测为 `Named<Kind>Type`
            #   NamedMountainCivilizations → NamedMountainType；NamedRiverCivilizations →
            #   NamedRiverType；7 张表（Mountain/River/Volcano/Desert/Lake/Ocean/Sea）同构。
            col = t.get("column")
            if not col:
                base = tbl[:-len("Civilizations")] if tbl.endswith("Civilizations") else tbl
                col = base + "Type"
            g.append(ins(tbl, ["CivilizationType", col],
                         {"CivilizationType": cid, col: t.get("name")}))

    for ld in leaders:
        lt = ld["type"]
        g.append(ins("Leaders",
                     ["LeaderType", "Name", "OperationList", "IsBarbarianLeader",
                      "InheritFrom", "SceneLayers", "Sex", "SameSexPercentage"],
                     {"LeaderType": lt, "Name": ld.get("name") or ("LOC_%s_NAME" % lt),
                      "OperationList": ld.get("operation_list"),
                      "IsBarbarianLeader": ld.get("is_barbarian"),
                      "InheritFrom": ld.get("inherit_from"),
                      "SceneLayers": ld.get("scene_layers"),
                      "Sex": ld.get("sex"),
                      "SameSexPercentage": ld.get("same_sex_percentage")}))
        for t in (ld.get("traits") or []):
            g.append(ins("LeaderTraits", ["LeaderType", "TraitType"],
                         {"LeaderType": lt, "TraitType": t}))
        civ_link = ld.get("civilization") or cid
        if not civ_link:
            problems.append("%s 无法确定所属文明（leaders[].civilization 或 civilization.type）" % lt)
        else:
            g.append(ins("CivilizationLeaders",
                         ["LeaderType", "CivilizationType", "CapitalName"],
                         {"LeaderType": lt, "CivilizationType": civ_link,
                          "CapitalName": ld.get("capital")}))
        if ld.get("quote"):
            g.append(ins("LeaderQuotes", ["LeaderType", "Quote", "QuoteAudio"],
                         {"LeaderType": lt, "Quote": ld["quote"],
                          "QuoteAudio": ld.get("quote_audio")}))
        if ld.get("civilization") and cid and ld["civilization"] != cid:
            warns.append("%s 挂到 %s（非本规格的 %s）—— 确认这是「leader-only 挂已有文明」"
                         % (lt, ld["civilization"], cid))

    # ---- Config（Players / PlayerItems）----
    c = ["-- %s —— Config 数据（前端/选人界面；由 civ_leader_data.py 生成）" % slug,
         "-- 列名来源：database/DebugConfiguration.sqlite 实测（Players 属 Config，不在 gameplay 库）", ""]
    for i, ld in enumerate(leaders):
        lt = ld["type"]
        civ_link = ld.get("civilization") or cid
        c.append(ins("Players",
                     ["Domain", "CivilizationType", "LeaderType", "LeaderName", "LeaderIcon",
                      "CivilizationName", "CivilizationIcon", "LeaderAbilityName",
                      "LeaderAbilityDescription", "LeaderAbilityIcon",
                      "CivilizationAbilityName", "CivilizationAbilityDescription",
                      "CivilizationAbilityIcon", "Portrait", "PortraitBackground",
                      "PlayerColor", "HumanPlayable", "SortIndex"],
                     {"Domain": domain, "CivilizationType": civ_link, "LeaderType": lt,
                      "LeaderName": ld.get("name") or ("LOC_%s_NAME" % lt),
                      "LeaderIcon": ld.get("icon"), "CivilizationName": civ_name,
                      "CivilizationIcon": civ.get("icon"),
                      "LeaderAbilityName": ld.get("ability_name"),
                      "LeaderAbilityDescription": ld.get("ability_description"),
                      "LeaderAbilityIcon": ld.get("ability_icon"),
                      "CivilizationAbilityName": civ.get("ability_name"),
                      "CivilizationAbilityDescription": civ.get("ability_description"),
                      "CivilizationAbilityIcon": civ.get("ability_icon"),
                      "Portrait": ld.get("portrait"), "PortraitBackground": ld.get("portrait_background"),
                      "PlayerColor": ld.get("player_color"), "HumanPlayable": 1,
                      "SortIndex": ld.get("sort_index", i + 1)}))
        # 两张 XLP/资产条目名（自由字符串）——提醒别忘登记，否则界面空白。
        # ★ 原版 FrontEnd 下这两列是**必需**的，且**留空 ≠ 安全**：
        #   引擎会回退到 <LeaderType>_NEUTRAL / _BACKGROUND（PlayerSetupLogic.lua:807-829）；
        #   mod 领袖通常没有这两个回退名 → 控件空白且**前端不报错**。
        #   规格与自建/别名两条路见 civ6-asset-forge/reference/frontend-portrait.md。
        for kind, fallback in (("portrait", "_NEUTRAL"), ("portrait_background", "_BACKGROUND")):
            if ld.get(kind):
                warns.append("%s 的 %s=%s 必须在 UITexture 类 XLP 里登记，否则不进 BLP（界面空白）"
                             % (lt, kind, ld[kind]))
            else:
                warns.append("%s 未提供 %s → Players.%s 为空，引擎将回退到 %s%s；"
                             "该回退名在工程里通常不存在 → 原版选人界面控件**空白且不报错**。"
                             "要么自建（竖版背景 328×935），要么用 civ6-asset-forge 的 "
                             "pick_vanilla_background.py 产 XLP 别名复用官方贴图。"
                             % (lt, kind, "Portrait" if kind == "portrait" else "PortraitBackground",
                                lt, fallback))
        for it in (ld.get("player_items") or []):
            c.append(ins("PlayerItems",
                         ["Domain", "CivilizationType", "LeaderType", "Type", "Name",
                          "Description", "Icon", "SortIndex"],
                         {"Domain": domain, "CivilizationType": civ_link, "LeaderType": lt,
                          "Type": it.get("type"), "Name": it.get("name"),
                          "Description": it.get("description"), "Icon": it.get("icon"),
                          "SortIndex": it.get("sort_index")}))

    # ---- Text ----
    t = ["-- %s —— 游戏内文本（8 语言；必须经 UpdateText 加载）" % slug,
         "-- 由 civ_leader_data.py 生成。modinfo 的 LocalizedText 只管「选择 mod」界面。", ""]
    seen = set()
    for tag in all_tags:
        if tag in seen:
            continue
        seen.add(tag)
        blk = text.get(tag) or {}
        langs = [l for l in LANGS if blk.get(l)]
        if not langs:
            continue
        rows = ",\n  ".join("(%s, %s, %s)" % (q(l), q(tag), q(blk[l])) for l in langs)
        t.append("INSERT OR REPLACE INTO LocalizedText (Language, Tag, Text) VALUES\n  %s;" % rows)
    extra = [k for k in text if k not in seen]
    if extra:
        rows = []
        for tag in extra:
            for l in LANGS:
                if text[tag].get(l):
                    rows.append("(%s, %s, %s)" % (q(l), q(tag), q(text[tag][l])))
        if rows:
            t.append("INSERT OR REPLACE INTO LocalizedText (Language, Tag, Text) VALUES\n  %s;"
                     % ",\n  ".join(rows))
    # 语言齐缺自检
    for tag in sorted(set(all_tags) | set(text)):
        blk = text.get(tag) or {}
        miss = [l for l in LANGS if not blk.get(l)]
        if miss and blk:
            warns.append("文本 %s 缺 %d 种语言：%s" % (tag, len(miss), ",".join(miss)))
        elif not blk:
            warns.append("文本 %s 完全没有内容（会显示原始 tag）" % tag)

    check_notnull(problems)
    return ("\n".join(g) + "\n", "\n".join(c) + "\n", "\n".join(t) + "\n",
            problems, warns, sorted(set(all_tags) | set(text)))


def main() -> int:
    ap = argparse.ArgumentParser(description="新文明/新领袖：规格 JSON → 数据与文本 SQL")
    ap.add_argument("spec", help="规格 JSON（UTF-8）")
    ap.add_argument("--project", default=None, help="工程根（--write 时必填）")
    ap.add_argument("--write", action="store_true", help="写盘（默认仅预演）")
    ap.add_argument("--check", action="store_true", help="只校验规格，不生成")
    args = ap.parse_args()

    try:
        spec = json.load(open(args.spec, encoding="utf-8"))
    except Exception as e:
        print("FAIL 读取规格失败：%s" % e)
        return 1

    g, c, t, problems, warns, tags = build(spec)

    cid = (spec.get("civilization") or {}).get("type") or "Mod"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", cid.replace("CIVILIZATION_", "")).strip("_") or "Mod"

    print("规格：%s" % args.spec)
    print("  文明     %s" % ((spec.get("civilization") or {}).get("type") or "(未指定)"))
    print("  领袖     %s" % ", ".join(l.get("type", "?") for l in (spec.get("leaders") or [])))
    print("  文本 tag %d 个" % len(tags))
    print("  gameplay 语句 %d 条 / Config 语句 %d 条 / 文本语句 %d 条"
          % (g.count("INSERT"), c.count("INSERT"), t.count("INSERT")))

    if problems:
        print("\n规格问题（必须先修）：")
        for p in problems:
            print("   ✗ %s" % p)
    if warns:
        print("\n告警：")
        for w in warns:
            print("   ! %s" % w)

    if args.check or not args.write:
        if not args.write and not args.check:
            print("\n[预演] 未写盘。加 --write 实际生成。")
        return 1 if problems else (2 if warns else 0)

    if not args.project or not os.path.isdir(args.project):
        print("FAIL --write 需要有效的 --project <工程根>")
        return 1
    if problems:
        print("FAIL 规格有问题，拒绝写盘（先修上面的 ✗）")
        return 1

    outs = [(os.path.join(args.project, "Data", "CivLeader_%s.sql" % slug), g),
            (os.path.join(args.project, "Data", "Config_%s.sql" % slug), c),
            (os.path.join(args.project, "Text", "Text_%s.sql" % slug), t)]
    for path, content in outs:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # .sql 属代码/配置类 → CRLF（换行分层铁律）
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(content.replace("\r\n", "\n"))
        print("写出  %s  %d B" % (path, os.path.getsize(path)))

    print("\n★ 还需手动在 .civ6proj 注册（本工具不动工程文件）：")
    print("   InGameActions  → UpdateDatabase: Data/CivLeader_%s.sql" % slug)
    print("                    UpdateText:     Text/Text_%s.sql" % slug)
    print("   FrontEndActions→ UpdateDatabase: Data/Config_%s.sql" % slug)
    print("                    UpdateText:     Text/Text_%s.sql" % slug)
    print("   并补 <Content Include> 三条（漏了不会被部署）")
    print("\n下一步校验：python tools/modinfo_build.py <civ6proj> --deploy")
    print("            node scripts/rgn_validate_runner.mjs <Data 目录>")
    return 2 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
