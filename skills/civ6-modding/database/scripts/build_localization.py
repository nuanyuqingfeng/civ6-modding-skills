#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_localization.py — 从**本机游戏安装**按分层规则合成本地化文本库

## 为什么需要它

`database/DebugLocalization.sqlite` 是**基础游戏**的本地化快照（15,237 tag × 12 语言），
**不含任何 DLC / 资料片文本**（实测 `LOC_LEADER_MANSA_MUSA_NAME`、`LOC_DISTRICT_PRESERVE_NAME`
全部缺席）。这直接违反 SKILL.md §4.1 第 4 条「先查原版有没有现成 tag」——
查 DLC 内容时必然查不到。

本工具按**权威分段 + 分层覆盖**合成两个库：

| 库 | 内容 | 覆盖规则 |
|----|------|---------|
| **主文本库** | 基础游戏 + EXP1 + EXP2 + 全部领袖/文明 DLC | `EXP2 > EXP1 > base`；其它领袖包**只补缺不覆盖** |
| **模式文本库** | Mode 类玩法（蛮族氏族/行业与公司/秘密结社/英雄/风云变幻/天启/塔防/树随机） | **只加不覆盖** |

情景（Scenario）文本**排除**。

## 分段判据（权威，实测两种 .modinfo schema 都要支持）

1. **新式**：`<InGameActions><UpdateText criteria="X"><File>…</File>`，
   判据在 `<ActionCriteria><Criteria id="X">` 的
   `<ConfigurationValueMatches><ConfigurationId>GAMEMODE_*</ConfigurationId>`；
2. **旧式**（实测仅 `VikingsScenario`）：`<Components><LocalizedText><Properties><RuleSet>`，
   情景判据为 `RuleSet` 含 `RULESET_SCENARIO_*`。

> 权威模式清单在 **`DebugConfiguration.sqlite → GameModeItems`（8 行）**，
> **不在** Gameplay 库（实测 Gameplay 无 `Modes` 表、`Types` 里 `GAMEMODE%` 为 0 行）。

## 硬性边界

1. **绝不删除任何既有行**；`SkillAnnotation_Colors` / `SkillAnnotation_Icons` 侧表原样保留；
2. **不应用 `<Delete Tag>`**：删除是**加载域作用域**（只在该 DLC/模式启用时生效），
   静态合成时应用会误删其它环境下仍有效的文本（实测 599 个删除项、分布在 21 个目录）；
3. **不动 schema**：只往 `LocalizedText` 加/改行，`audit_schema_drift.py` 仍通过；
4. **数据来源是本机游戏安装**（用户自己的 Steam 副本），不引入第三方数据；
5. **默认只加不改**：改写既有值需显式 `--apply-rewrites`。

## 解析细节（实测）

- **两种语言承载**：目录名定语言（`Text/<lang>/…`，`<Row Tag><Text>`）
  与属性定语言（`*Translations*`，`<Replace Tag Language><Text>`）——都要认，否则漏一半语言；
- **`<File Priority="N">` 参与排序**（★ **数值越大越先执行**，与直觉相反；见 `gotchas.md` §11）。
  实测判据：`Expansion2.modinfo` 给 `RemoveText.xml` 用 `Priority="2"`、给 `Translations_Text.xml` 用无 Priority；
  `RemoveText` 删掉的 tag 被 `Translations` 重新定义后**在引擎库中依然存在** ⇒ `Priority=2` 先跑。
- **首尾空白归一**：引擎落盘会 `.strip()`，比对时需归一，否则 1,116 行噪声会被误判为改写；
- 统计口径：`<Row>` 插入 / `<Replace>` 覆盖，两者语义不同。

## 用法

    # 1) 只读报告：分段 + 分层 + 与既有库差异（推荐先跑）
    python build_localization.py --report

    # 2) 合成两个库到指定文件（不动现有库）
    python build_localization.py --build-main <主库.sqlite> --build-mode <模式库.sqlite>

    # 3) 就地补全现有库（只加 + 可选 EXP2 覆盖）
    python build_localization.py --augment-main --dry-run
    python build_localization.py --augment-main --apply-rewrites

退出码：0 = 成功；1 = 有问题；2 = 用法错误。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(SKILL_DIR, "tools"))
try:
    import _paths  # type: ignore
except Exception:
    _paths = None

DEFAULT_DB = os.path.join(SKILL_DIR, "database", "DebugLocalization.sqlite")
# 模式文本库（Mode 类玩法单独成库）；与主库同目录，**同样不入库**（可从游戏文件重建）
MODE_DB_NAME = "Localization_Mode.sqlite"

# 本库 12 语言（与 DebugLocalization.sqlite.Languages 一致）
OUR_LANGS = {"en_US", "zh_Hans_CN", "zh_Hant_HK", "ja_JP", "ko_KR",
             "de_DE", "es_ES", "fr_FR", "it_IT", "pl_PL", "pt_BR", "ru_RU"}

LANG_ALIAS = {
    "zh_Hans": "zh_Hans_CN", "zh_Hant": "zh_Hant_HK",
    "zh_CN": "zh_Hans_CN", "zh_TW": "zh_Hant_HK",
    "en": "en_US", "ja": "ja_JP", "ko": "ko_KR", "de": "de_DE",
    "es": "es_ES", "fr": "fr_FR", "it": "it_IT", "pl": "pl_PL",
    "pt": "pt_BR", "ru": "ru_RU",
}

_ROW_RE = re.compile(r'<Row\s+Tag="([^"]+)"\s*>(.*?)</Row>', re.S)
_REP_RE = re.compile(r'<Replace\s+Tag="([^"]+)"\s+Language="([^"]+)"\s*>(.*?)</Replace>', re.S)
# ★ 同时匹配 `<Text>…</Text>` 与自闭合 `<Text/>`（后者表示空值）。
#   官方用 `<Text/>` 声明"该 tag 存在但内容为空"（如 en_US 的
#   LOC_DIPLO_KUDO_EXIT_ANY_ANY）；只认成对标签会**丢掉这些行**（实测少 2 行）。
_TEXT_RE = re.compile(r"<Text\s*/>|<Text>(.*?)</Text>", re.S)
_GENDER_RE = re.compile(r"<Gender>(.*?)</Gender>", re.S)
_PLUR_RE = re.compile(r"<Plurality>(.*?)</Plurality>", re.S)
_LANGDIR_RE = re.compile(r"^[a-z]{2}_[A-Za-z]{2,}$")


def _text_of(block: str) -> str | None:
    """从元素体里取 `<Text>`：自闭合 → `''`；成对 → 内容；都没有 → `None`。"""
    m = _TEXT_RE.search(block)
    if not m:
        return None
    return "" if m.group(1) is None else m.group(1)

# 层级 rank：越小越先加载（越容易被后面覆盖）
RANK_BASE, RANK_EXP1, RANK_EXP2, RANK_DLC = 0, 1, 2, 3
RANK_NAME = {RANK_BASE: "base", RANK_EXP1: "exp1", RANK_EXP2: "exp2", RANK_DLC: "dlc"}


def _sn(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def _is_text_rel(rel: str) -> bool:
    """★ rel 是**相对**路径（如 `Text\\en_US\\X.xml`），开头没有反斜杠，
    所以不能用 `\\Text\\` 判定，否则全部漏掉。"""
    low = rel.lower()
    return (os.sep + "text" + os.sep) in low or low.startswith("text" + os.sep)


# ====================================================================== 分段

class Segment:
    """把游戏安装的本地化文本文件分成 main / mode / scenario 三类。"""

    def __init__(self, game_root: str):
        self.game = game_root
        self.dlc_root = os.path.join(game_root, "DLC")
        self.base_text_root = os.path.join(game_root, "Base", "Assets", "Text")
        self.crit_gamemodes: dict[str, set] = {}
        self.assign: dict[tuple[str, str], str] = {}      # (dlc|__base__, rel) -> class
        self.why: dict[tuple[str, str], str] = {}
        self.priority: dict[tuple[str, str], int] = {}
        self._build()

    # -- 解析每个 DLC 的 .modinfo -------------------------------------
    def _parse_modinfo(self, mi: str, dlc: str, raw: list):
        try:
            root = ET.parse(mi).getroot()
        except ET.ParseError:
            return
        for child in root:
            tag = _sn(child.tag)
            if tag == "ActionCriteria":
                for cr in child:
                    if _sn(cr.tag) != "Criteria":
                        continue
                    info = self.crit_gamemodes.setdefault(cr.get("id") or "", set())
                    for sub in cr.iter():
                        if _sn(sub.tag) == "ConfigurationId" and (sub.text or "").startswith("GAMEMODE"):
                            info.add((sub.text or "").strip())
            elif tag == "InGameActions":
                for act in child:
                    cid = act.get("criteria") or ""
                    for f in act:
                        if _sn(f.tag) != "File":
                            continue
                        rel = (f.text or "").strip().replace("/", os.sep)
                        if rel.lower().endswith(".xml") and _is_text_rel(rel):
                            pr = f.get("Priority")
                            raw.append((dlc, rel, cid, int(pr) if pr and pr.isdigit() else 0))
            elif tag in ("Components", "Settings"):
                # 旧式：RuleSet 在 <Properties> 里
                for comp in child:
                    rule = ""
                    for sub in comp.iter():
                        if _sn(sub.tag) == "RuleSet":
                            rule = (sub.text or "").strip()
                    for f in comp.iter():
                        if _sn(f.tag) != "File":
                            continue
                        rel = (f.text or "").strip().replace("/", os.sep)
                        if rel.lower().endswith(".xml") and _is_text_rel(rel):
                            pr = f.get("Priority")
                            raw.append((dlc, rel, "RuleSet=" + rule,
                                        int(pr) if pr and pr.isdigit() else 0))

    def _build(self):
        raw: list = []
        if os.path.isdir(self.dlc_root):
            for d in sorted(os.listdir(self.dlc_root)):
                fp = os.path.join(self.dlc_root, d)
                if not os.path.isdir(fp):
                    continue
                for mi in glob.glob(os.path.join(fp, "*.modinfo")):
                    self._parse_modinfo(mi, d, raw)

        for dlc, rel, why, pr in raw:
            if why.startswith("RuleSet="):
                rule = why[len("RuleSet="):]
                if re.search(r"RULESET_SCENARIO", rule, re.I):
                    cls = "scenario"
                elif re.search(r"scenario", dlc, re.I):
                    cls = "scenario"
                else:
                    cls = "main"
            elif why and self.crit_gamemodes.get(why):
                cls = "mode"
            elif re.search(r"scenario", dlc, re.I):
                cls = "scenario"
            else:
                cls = "main"
            self.assign[(dlc, rel)] = cls
            self.why[(dlc, rel)] = why or "(无 criteria)"
            self.priority[(dlc, rel)] = pr

        # 磁盘上存在但没被任何 modinfo 引用的文件（兜底，避免静默漏掉）
        for f in glob.glob(os.path.join(self.dlc_root, "**", "*.xml"), recursive=True):
            if os.sep + "Text" + os.sep not in f:
                continue
            d = os.path.relpath(f, self.dlc_root).split(os.sep)[0]
            rel = os.path.relpath(f, os.path.join(self.dlc_root, d))
            if (d, rel) in self.assign:
                continue
            base = os.path.basename(f).upper()
            if re.search(r"scenario", d, re.I):
                cls = "scenario"
            elif "_MODE" in base:
                cls = "mode"
            else:
                cls = "main"
            self.assign[(d, rel)] = cls
            self.why[(d, rel)] = "兜底(未被 modinfo 引用)"
            self.priority[(d, rel)] = 0

    # -- 采集磁盘上真实存在的文件 -------------------------------------
    def disk_files(self, cls: str) -> list[tuple[str, str, int]]:
        """→ [(kind, rel, priority)]，kind='__base__' 或 DLC 目录名；只含磁盘存在的。"""
        out = []
        for (dlc, rel), c in self.assign.items():
            if c != cls:
                continue
            if os.path.isfile(os.path.join(self.dlc_root, dlc, rel)):
                out.append((dlc, rel, self.priority.get((dlc, rel), 0)))
        if cls == "main":
            for f in glob.glob(os.path.join(self.base_text_root, "**", "*.xml"), recursive=True):
                out.append(("__base__", os.path.relpath(f, self.base_text_root), 0))
        return out

    def file_path(self, dlc: str, rel: str) -> str:
        root = self.base_text_root if dlc == "__base__" else os.path.join(self.dlc_root, dlc)
        return os.path.join(root, rel)

    def tier_of(self, dlc: str) -> int:
        if dlc == "__base__":
            return RANK_BASE
        if dlc == "Expansion1":
            return RANK_EXP1
        if dlc == "Expansion2":
            return RANK_EXP2
        return RANK_DLC

    def report(self) -> None:
        c = Counter(self.assign.values())
        print("  磁盘分段（按 .modinfo criteria / RuleSet 权威判定）：")
        for k in ("main", "mode", "scenario"):
            n = len([1 for (d, r), cc in self.assign.items()
                     if cc == k and os.path.isfile(self.file_path(d, r))])
            print("     %-9s %4d 个 .xml" % (k, n))


# ====================================================================== 解析文本

def parse_file(path: str) -> list[tuple[str, str, str, str, str]]:
    """→ [(tag, language, text, gender, plurality)]。两种形态都解析（含自闭合 `<Text/>`）。"""
    out: list[tuple[str, str, str, str, str]] = []
    try:
        s = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return out
    if "Text" not in s:
        return out
    for m in _REP_RE.finditer(s):
        t = _text_of(m.group(3))
        if t is None:
            continue
        lang = LANG_ALIAS.get(m.group(2).strip(), m.group(2).strip())
        g = _GENDER_RE.search(m.group(3))
        p = _PLUR_RE.search(m.group(3))
        out.append((m.group(1).strip(), lang, t,
                    (g.group(1).strip() if g else None),
                    (p.group(1).strip() if p else None)))
    lang_dir = os.path.basename(os.path.dirname(path))
    if _LANGDIR_RE.match(lang_dir):
        lang = LANG_ALIAS.get(lang_dir, lang_dir)
        for m in _ROW_RE.finditer(s):
            t = _text_of(m.group(2))
            if t is None:
                continue
            out.append((m.group(1).strip(), lang, t, None, None))
    return out


def load_layered(seg: Segment, cls: str) -> dict[tuple[str, str], tuple[str, str, str, int, str]]:
    """按 (排序键) 加载某一类，返回 {(lang,tag): (text, gender, plur, rank, dlc)}。

    排序键 = (rank, -priority, path)：rank 决定 EXP2>EXP1>base>dlc；
    priority **越大越先执行**（引擎实测，见模块 docstring），故按 **降序** 遍历、
    后写覆盖先写 ⇒ 最终生效的是 **priority 较小（或无 Priority）** 的文件，与引擎一致。
    路径作稳定 tie-break。

    ★ 2026-09-22 修正：此前按 priority **升序** 遍历（last-write-wins ⇒ 大 priority 胜），
      与引擎相反。官方数据中未观测到「同 tag 跨 priority 值冲突」的样本（故对官方主库无差异），
      但方向本身是错的，第三方 mod 场景会取到错误的文本。
    """
    files = []
    for dlc, rel, pr in seg.disk_files(cls):
        files.append((seg.tier_of(dlc), pr, rel, dlc))
    # priority 降序：越大越先执行；后写覆盖先写 ⇒ 小 priority 生效（与引擎一致）
    files.sort(key=lambda t: (t[0], -t[1], t[2]))

    rows: dict[tuple[str, str], tuple[str, str, str, int, str]] = {}
    for rank, pr, rel, dlc in files:
        for tag, lang, text, gender, plur in parse_file(seg.file_path(dlc, rel)):
            if lang not in OUR_LANGS:
                continue
            key = (lang, tag)
            prev = rows.get(key)
            # 主库：rank 更高（或同 rank 更晚）才覆盖；DLC 层只在"无值"时补缺
            if prev is not None and cls == "main" and prev[3] == RANK_EXP2 and rank == RANK_DLC:
                continue
            rows[key] = (text, gender, plur, rank, dlc)
    return rows


def load_existing(db: str) -> dict[tuple[str, str], tuple[str, str, str]]:
    if not os.path.isfile(db):
        return {}
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    try:
        return {(r[0], r[1]): (r[2] or "", r[3], r[4]) for r in
                con.execute("SELECT Language,Tag,Text,Gender,Plurality FROM LocalizedText")}
    finally:
        con.close()


def diff_report(name: str, new: dict, old: dict) -> dict:
    """→ 差异统计 dict。空白归一后判定，避免引擎 strip 噪声。"""
    only = set(new) - set(old)
    both = set(new) & set(old)
    changed_real, ws_only = [], []
    for k in both:
        a = (new[k][0] or "")
        b = (old[k][0] or "")
        if a == b:
            continue
        (ws_only if a.strip() == b.strip() else changed_real).append(k)
    same = len(both) - len(changed_real) - len(ws_only)
    print("   ── %s" % name)
    print("       新增（既有库没有）: %8d 行 / %6d tag" % (len(only), len({t for _l, t in only})))
    print("       与既有库相同      : %8d 行" % same)
    print("       仅首尾空白差异    : %8d 行（归一后跳过）" % len(ws_only))
    print("       实质不同          : %8d 行" % len(changed_real))
    by_rank = Counter(new[k][3] for k in changed_real)
    if changed_real:
        print("          └ 来源分层: " + ", ".join(
            "%s=%d" % (RANK_NAME.get(r, r), by_rank[r]) for r in sorted(by_rank)))
    return {"only": only, "same": same, "ws": ws_only, "changed": changed_real}


# ====================================================================== 落库

SCHEMA = """
CREATE TABLE IF NOT EXISTS LocalizedText (
    'Language' TEXT NOT NULL, 'Tag' TEXT NOT NULL, 'Text' TEXT,
    'Gender' TEXT, 'Plurality' TEXT, PRIMARY KEY (Language, Tag));
CREATE INDEX IF NOT EXISTS idx_localized_language ON LocalizedText(Language);
"""

SIDE_TABLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS SkillAnnotation_Icons  ('Name' TEXT PRIMARY KEY, 'Remark' TEXT);
CREATE TABLE IF NOT EXISTS SkillAnnotation_Colors ('Type' TEXT PRIMARY KEY, 'Remark' TEXT);
"""

# 侧表的随包备份（`DebugLocalization.sqlite` 不入库，人工成果靠它跨机器存活）
SIDE_JSON = os.path.join(SKILL_DIR, "database", "annotations", "localization_side_tables.json")
# 辅助注册表 + 视图的随包备份（保证换机器重建后仍是 10 表 + 3 视图）
AUX_JSON = os.path.join(SKILL_DIR, "database", "annotations", "localization_aux_tables.json")


def create_full_schema(db: str) -> tuple[int, int]:
    """在库中建出官方本地化库的**完整** schema（辅助表 + 视图），缺则建、有则跳。

    仅靠 `SCHEMA` 会只得到 `LocalizedText` 一张表，而官方库有 10 表 + 3 视图
    （`Languages` / `LanguagePriorities` / `FontStyleSheets` / `EnglishText` 视图等）。
    这些是**语言注册与字体样式**的查询基础，缺了会让相关工具失效。
    → (建成/校验的表数, 视图数)；缺 JSON 时返回 (0, 0) 并提示。
    """
    if not os.path.isfile(AUX_JSON):
        return 0, 0
    with open(AUX_JSON, encoding="utf-8") as f:
        payload = json.load(f)
    con = sqlite3.connect(db)
    try:
        existing = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        n_t = n_v = 0
        for t, spec in (payload.get("tables") or {}).items():
            if t in existing:
                continue
            con.execute(spec["ddl"])
            cols = spec.get("columns") or []
            rows = spec.get("rows") or []
            if rows and cols:
                con.executemany(
                    "INSERT OR IGNORE INTO %s (%s) VALUES (%s)"
                    % (t, ",".join(cols), ",".join("?" * len(cols))), rows)
            n_t += 1
        have_v = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        for v, spec in (payload.get("views") or {}).items():
            if v in have_v:
                continue
            con.execute(spec["ddl"])
            n_v += 1
        con.commit()
    finally:
        con.close()
    return n_t, n_v


def restore_side_tables(db: str) -> tuple[int, int, int]:
    """从随包 JSON 还原：两张人工标注侧表 + 「非官方来源」的行（extraRows）。

    `DebugLocalization.sqlite` 不入 git，因此这些**不可再生**的内容必须靠随包 JSON 存活：
      · `SkillAnnotation_Icons` / `SkillAnnotation_Colors`（人工标注侧表）
      · `extraRows`：库中「游戏安装里没有」的行（本项目自造 tag，实测 64 行）

    全部用 `INSERT OR IGNORE`（不覆盖既有）。
    → (icons, colors, extra)；缺 JSON 时返回 (-1, -1, -1)。
    """
    if not os.path.isfile(SIDE_JSON):
        return -1, -1, -1
    with open(SIDE_JSON, encoding="utf-8") as f:
        payload = json.load(f)
    tabs = payload.get("tables") or {}
    extra = payload.get("extraRows") or []
    con = sqlite3.connect(db)
    try:
        con.executescript(SCHEMA)
        con.executescript(SIDE_TABLES_SCHEMA)
        n_i = n_c = 0
        for row in tabs.get("icons") or []:
            k = row.get("name") or row.get("Name")
            if k:
                con.execute("INSERT OR IGNORE INTO SkillAnnotation_Icons (Name, Remark) VALUES (?,?)",
                            (k, row.get("remark")))
                n_i += 1
        for row in tabs.get("colors") or []:
            k = row.get("type") or row.get("Type")
            if k:
                con.execute("INSERT OR IGNORE INTO SkillAnnotation_Colors (Type, Remark) VALUES (?,?)",
                            (k, row.get("remark")))
                n_c += 1
        n_e = 0
        for r in extra:
            if not r.get("tag") or not r.get("language"):
                continue
            con.execute("INSERT OR IGNORE INTO LocalizedText "
                        "(Language,Tag,Text,Gender,Plurality) VALUES (?,?,?,?,?)",
                        (r["language"], r["tag"], r.get("text"), r.get("gender"), r.get("plurality")))
            n_e += 1
        con.commit()
    finally:
        con.close()
    return n_i, n_c, n_e


def write_db(out: str, main_rows: dict, mode_rows: dict | None, mode_action: str) -> None:
    """写库。mode_action='replace' 时重建 LocalizedText（仅用于新建文件）。

    ★ **写入前 strip 首尾空白**（实测口径，勿改）：
      游戏源文件常带尾随空格（如 `de_DE LOC_ABILITY_CAPTIVE_WORKERS_DESCRIPTION`
      源文件结尾是 `. `、`LOC_CITIZEN_ETHIOPIA_FEMALE_7` 是 `'Taytu  '`），
      但**引擎落盘时会 strip** —— 游戏运行时缓存里这两个值都没有尾随空格。
      既有参考库来自该缓存，所以也是 strip 过的。
      若不 strip，新写入的行会与库内既有的 182,812 行**口径不一致**
      （实测产生 1,116 行「仅首尾空白」的内部不一致）。
    `None` 归一为 `''`。
    """
    def norm(v):
        return "" if v is None else v.strip()

    con = sqlite3.connect(out)
    try:
        con.executescript(SCHEMA)
        if mode_action == "replace":
            con.execute("DELETE FROM LocalizedText")
        data = [(l, t, norm(v[0]), v[1], v[2]) for (l, t), v in main_rows.items()]
        con.executemany("INSERT OR REPLACE INTO LocalizedText "
                        "(Language,Tag,Text,Gender,Plurality) VALUES (?,?,?,?,?)", data)
        if mode_rows:
            mdata = [(l, t, norm(v[0]), v[1], v[2]) for (l, t), v in mode_rows.items()]
            con.executemany("INSERT OR IGNORE INTO LocalizedText "
                            "(Language,Tag,Text,Gender,Plurality) VALUES (?,?,?,?,?)", mdata)
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM LocalizedText").fetchone()[0]
        tg = con.execute("SELECT COUNT(DISTINCT Tag) FROM LocalizedText").fetchone()[0]
    finally:
        con.close()
    print("   写入 %s：%d 行 / %d tag" % (os.path.basename(out), n, tg))


# ====================================================================== 主流程

def main() -> int:
    ap = argparse.ArgumentParser(
        description="从本机游戏安装按分层规则合成本地化文本库（主库 / 模式库）")
    ap.add_argument("--game", default=None, help="游戏安装根（默认按 _paths.py 的 game 键）")
    ap.add_argument("--db", default=DEFAULT_DB, help="既有库（兜底/比对基准）")
    ap.add_argument("--report", action="store_true", help="只读报告（默认）")
    ap.add_argument("--build-main", metavar="OUT", help="合成主文本库到 OUT")
    ap.add_argument("--build-mode", metavar="OUT", help="合成模式文本库到 OUT")
    ap.add_argument("--augment-main", action="store_true", help="向既有库补全主库内容")
    ap.add_argument("--rebuild", action="store_true",
                    help="★ 一键按规范重建两个库：就地补全 %s + 重建 %s"
                         % (os.path.basename(DEFAULT_DB), MODE_DB_NAME))
    ap.add_argument("--apply-rewrites", action="store_true",
                    help="应用「实质不同」的覆盖（默认只加不改）")
    ap.add_argument("--dry-run", action="store_true", help="只统计不写盘")
    ap.add_argument("--list-seg", action="store_true", help="列出分段明细")
    args = ap.parse_args()

    # --rebuild 等价于规范的两步；--apply-rewrites 在重建场景下默认开启
    # （主库要 EXP2 优先，就必须覆盖既有 base 值）
    if args.rebuild:
        args.augment_main = True
        args.apply_rewrites = True
        args.build_mode = args.build_mode or os.path.join(SKILL_DIR, "database", MODE_DB_NAME)
        print("=== --rebuild：按规范重建两个库 ===")
        print("   主库  : %s（就地补全，保留侧表）" % DEFAULT_DB)
        print("   模式库: %s（新建）" % args.build_mode)
        print()

    game = args.game
    if not game and _paths is not None:
        game = _paths.get("game")
    if not game or not os.path.isdir(game):
        print("ERROR: 找不到游戏安装目录（用 --game 指定）")
        return 2

    print("=== 分段 ===")
    seg = Segment(game)
    seg.report()
    if args.list_seg:
        for cls in ("main", "mode", "scenario"):
            print("\n  [%s]" % cls)
            for dlc, rel, pr in sorted(seg.disk_files(cls)):
                print("    %-26s %-58s prio=%d  %s" % (dlc, rel, pr, seg.why.get((dlc, rel), "")))
    print()

    print("=== 加载分层文本 ===")
    main_new = load_layered(seg, "main")
    mode_new = load_layered(seg, "mode")
    print("   主库（EXP2>EXP1>base + 领袖包补缺）: %d 行 / %d tag"
          % (len(main_new), len({t for _l, t in main_new})))
    print("   模式库（只加不覆盖）              : %d 行 / %d tag"
          % (len(mode_new), len({t for _l, t in mode_new})))
    print()

    old = load_existing(args.db)
    print("=== 与既有库比对（兜底基准）===")
    print("   既有库: %d 行 / %d tag" % (len(old), len({t for _l, t in old})))
    dm = diff_report("主库", main_new, old)
    print()
    dmod = diff_report("模式库", mode_new, old)
    print()

    if args.report and not (args.build_main or args.build_mode or args.augment_main):
        print("=== 落库规模预估 ===")
        print("   ① 主文本库 : 既有 %d + 新增 %d = 约 %d 行"
              % (len(old), len(dm["only"]), len(old) + len(dm["only"])))
        print("   ② 模式文本库: 独立新建 %d 行" % len(mode_new))
        print()
        print("   改写候选（%d 行主库 + %d 行模式库）：默认不应用，"
              "加 --apply-rewrites 才覆盖。" % (len(dm["changed"]), len(dmod["changed"])))
        return 0

    # ---------------- 就地补全主库（既有库） ----------------
    if args.augment_main:
        # 库不存在 = 换机器/首次：直接从游戏文件全量合成（"兜底"部分靠随包 JSON 还原）
        if not os.path.isfile(args.db):
            print("=== 既有库不存在 → 从游戏文件全量合成（首次/换机器）===")
            if args.dry_run:
                print("   [dry-run] 会新建 %s（%d 行）" % (args.db, len(main_new)))
            else:
                write_db(args.db, main_new, None, "replace")
                n_t, n_v = create_full_schema(args.db)
                if n_t or n_v:
                    print("   辅助注册表/视图已建: 表=%d 视图=%d（源: annotations/%s）"
                          % (n_t, n_v, os.path.basename(AUX_JSON)))
                n_i, n_c, n_e = restore_side_tables(args.db)
                if n_i < 0:
                    print("   ⚠ 侧表备份 JSON 缺失（%s）——人工标注可能丢失"
                          % os.path.basename(SIDE_JSON))
                else:
                    print("   侧表与自造行已还原: Icons=%d Colors=%d extraRows=%d（源: annotations/%s）"
                          % (n_i, n_c, n_e, os.path.basename(SIDE_JSON)))
            if not (args.build_main or args.build_mode):
                return 0
        else:
            add = {k: v for k, v in main_new.items() if k not in old}
            # 改写判定按 **strip 后** 比较：引擎落盘会 strip，源文件常有尾随空格；
            # 只差首尾空白不算「实质改写」，否则会误报上千条。
            chg = {k: v for k, v in main_new.items()
                   if k in old and (v[0] or "").strip() != (old[k][0] or "").strip()}
            print("=== 就地补全主库 ===")
            print("   待新增: %d 行" % len(add))
            print("   待改写: %d 行（%s）" % (len(chg), "会应用" if args.apply_rewrites else "跳过"))
            if args.dry_run:
                print("   [dry-run] 未写盘。")
            else:
                con = sqlite3.connect(args.db)
                try:
                    before = con.execute("SELECT COUNT(*) FROM LocalizedText").fetchone()[0]
                    tabs_b = {r[0] for r in con.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")}
                    # ★ 新增行同样 strip，保证与库内既有行（源自引擎缓存、已 strip）同口径
                    con.executemany("INSERT OR IGNORE INTO LocalizedText "
                                    "(Language,Tag,Text,Gender,Plurality) VALUES (?,?,?,?,?)",
                                    [(l, t, (v[0] or "").strip(), v[1], v[2])
                                     for (l, t), v in add.items()])
                    if args.apply_rewrites:
                        con.executemany("UPDATE LocalizedText SET Text=?, Gender=?, Plurality=? "
                                        "WHERE Language=? AND Tag=?",
                                        [((v[0] or "").strip(), v[1], v[2], l, t)
                                         for (l, t), v in chg.items()])
                    con.commit()
                    after = con.execute("SELECT COUNT(*) FROM LocalizedText").fetchone()[0]
                    tabs_a = {r[0] for r in con.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")}
                finally:
                    con.close()
                print("   %d 行 → %d 行（+%d）" % (before, after, after - before))
                print("   侧表/表集合保留: %s" % ("是" if tabs_b == tabs_a else "*** 变化！***"))
            # 侧表还原（换机器时库里没有这两张表 → 从随包 JSON 灌回）
            if not args.dry_run:
                n_i, n_c, n_e = restore_side_tables(args.db)
                if n_i < 0:
                    print("   ⚠ 侧表备份 JSON 缺失（%s）——人工标注可能丢失"
                          % os.path.basename(SIDE_JSON))
                else:
                    print("   SkillAnnotation_* 与自造行已就位: Icons=%d Colors=%d extraRows=%d（源: annotations/%s）"
                          % (n_i, n_c, n_e, os.path.basename(SIDE_JSON)))
            if not (args.build_main or args.build_mode):
                return 0

    # ---------------- 合成主库到新文件（游戏文件权威 + 既有库兜底）----------------
    if args.build_main:
        if args.dry_run:
            print("[dry-run] 未写盘。")
        else:
            merged = dict(main_new)
            filled = 0
            for k, v in old.items():
                if k not in merged:
                    merged[k] = v
                    filled += 1
            print("=== 写主文本库（游戏文件权威 + 既有库兜底）===")
            print("   游戏分层值 %d + 既有库补缺 %d → 合计 %d"
                  % (len(main_new), filled, len(merged)))
            write_db(args.build_main, merged, None, "replace")

    # ---------------- 合成模式库（独立成库，只加不覆盖）----------------
    if args.build_mode:
        if args.dry_run:
            print("[dry-run] 未写盘。")
        else:
            print("=== 写模式文本库（独立成库）===")
            write_db(args.build_mode, mode_new, None, "replace")

    return 0


if __name__ == "__main__":
    sys.exit(main())
