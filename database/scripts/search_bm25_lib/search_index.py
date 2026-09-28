"""BM25 检索层：中文 bigram + 领域词典 + 字段权重（纯标准库，无 PyQt）。

移植来源：ModTools 5.4（MIT，Copyright (c) 2026 Siqi）`ModTools_5_4/db/search_index.py`，
2026-09-28 原样复制；改动仅限本行标注。类型口径以 civ6-modding/database/ 为准。

替代原先"整句连续子串 + 46 词效果字典"的匹配方式——那种做法对自然语言查询
（如"通往你城市的贸易路线加产出"）几乎必然 0 命中，且命中结果没有相关性排序。

算法：
1. **分词**（`tokenize`）
   - 中文：字符 bigram（"贸易路线" → 贸易/易路/路线）——无需分词库
   - 领域术语：词典整词 → 归一化 token（`术语:TRADE_ROUTE`），权重天然更高（IDF 高）
   - 英文/Type：按 `_` 与非字母数字切分，小写归一
2. **打分**：BM25（k1=1.2, b=0.75）× 字段权重
   - 对象名称 3.0 / 对象 Type 2.5 / 效果文本（ModifierStrings）2.0 / 对象描述 1.5 /
     效果与条件 Id·Type·参数 1.0
3. **对象级聚合**：词条文档（modifier/requirement）按绑定关系回溯到对象，
   同一对象下所有命中文档的分数相加，因此"名字命中"与"能力实现命中"可同台排序。

语料（对象名/描述、ModifierStrings 中文、Modifier Id/Type/参数、Requirement 文本与参数）
全部经 `db.loc_text` 解析（含嵌套 `{LOC_...}`），因此中文检索能命中引用链文本。

缓存：`get_index()` 按数据库文件 mtime 缓存（同一进程内复用，首次构建 ~0.4 秒）。
"""
from __future__ import annotations

import math
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .loc_text import make_sqlite_fetcher

# ── 领域词典：中文术语 → 英文 Type 片段 ────────────────────────────
# 作用：把"人话"映射到游戏实现里的英文片段（TRADE_ROUTE / YIELD / ADJUST …），
# 使中文自然语言查询能直接命中 MODIFIER_*_TRADE_ROUTE_YIELD_* 这类实现。
TERM_MAP: dict[str, str] = {
    # 产出与数值
    "产出": "YIELD", "加成": "ADJUST", "增益": "ADJUST", "减益": "ADJUST",
    "金币": "GOLD", "金钱": "GOLD", "生产力": "PRODUCTION", "产能": "PRODUCTION",
    "科技": "SCIENCE", "科技值": "SCIENCE", "文化": "CULTURE", "文化值": "CULTURE",
    "信仰": "FAITH", "信仰值": "FAITH", "食物": "FOOD", "住房": "HOUSING",
    "宜居": "AMENITY", "宜居度": "AMENITY", "旅游": "TOURISM", "旅游业绩": "TOURISM",
    "忠诚": "LOYALTY", "忠诚度": "LOYALTY", "伟人点": "GREAT_PERSON_POINT",
    "百分比": "PERCENT", "每回合": "PER_TURN", "额外": "EXTRA",
    # 贸易
    "贸易路线": "TRADE_ROUTE", "商路": "TRADE_ROUTE", "贸易": "TRADE",
    "贸易站": "TRADING_POST", "商人": "TRADER", "目的地": "DESTINATION",
    "起源": "ORIGIN", "通往": "TO", "国际贸易": "INTERNATIONAL",
    "国内贸易": "DOMESTIC", "贸易路线容量": "TRADE_ROUTE_CAPACITY",
    # 军事
    "宣战": "WAR", "战争": "WAR", "和平": "PEACE", "战斗力": "STRENGTH",
    "远程": "RANGED", "近战": "MELEE", "海军": "NAVAL", "陆军": "LAND",
    "空军": "AIR", "移动力": "MOVEMENT", "掠夺": "PLUNDER", "围攻": "SIEGE",
    "防御": "DEFENSE", "治疗": "HEAL", "经验": "EXPERIENCE", "升级": "UPGRADE",
    # 城市与区域
    "城市": "CITY", "首都": "CAPITAL", "人口": "POPULATION", "区域": "DISTRICT",
    "市中心": "CITY_CENTER", "建筑": "BUILDING", "奇观": "WONDER",
    "自然奇观": "NATURAL_WONDER", "改良": "IMPROVEMENT", "改良设施": "IMPROVEMENT",
    "地块": "PLOT", "单元格": "PLOT", "领土": "TERRITORY", "边界": "BORDER",
    "相邻": "ADJACEN", "魅力": "APPEAL", "电力": "POWER", "资源": "RESOURCE",
    "奢侈品": "LUXURY", "战略资源": "STRATEGIC", "加成资源": "BONUS",
    "住房上限": "HOUSING", "专家": "SPECIALIST", "生产队列": "PRODUCTION_QUEUE",
    # 单位与能力
    "单位": "UNIT", "平民": "CIVILIAN", "军用": "MILITARY", "建造者": "BUILDER",
    "开拓者": "SETTLER", "商人单位": "TRADER", "能力": "ABILITY",
    "晋升": "PROMOTION", "单位晋升": "PROMOTION", "治疗速率": "HEAL_RATE",
    "视野": "SIGHT", "射程": "RANGE", "夹击": "FLANKING", "支援": "SUPPORT",
    # 外交与政体
    "城邦": "CITY_STATE", "宗主": "SUZERAIN", "宗主国": "SUZERAIN",
    "盟友": "ALLIANCE", "同盟": "ALLIANCE", "外交": "DIPLOMATIC",
    "外交能见度": "DIPLOMATIC_VISIBILITY", "好感": "RELATIONSHIP",
    "议程": "AGENDA", "政策": "POLICY", "政策卡": "POLICY", "政体": "GOVERNMENT",
    "总督": "GOVERNOR", "信仰": "FAITH", "宗教": "RELIGION", "万神殿": "PANTHEON",
    # 科技与市政
    "科技树": "TECH", "市政": "CIVIC", "时代": "ERA", "黄金时代": "GOLDEN_AGE",
    "黑暗时代": "DARK_AGE", "英雄时代": "HEROIC_AGE", "伟人": "GREAT_PERSON",
    "大科学家": "GREAT_SCIENTIST", "大工程师": "GREAT_ENGINEER",
    "大将军": "GREAT_GENERAL", "大商人": "GREAT_MERCHANT", "大预言家": "GREAT_PROPHET",
    # 其他
    "蛮族": "BARBARIAN", "间谍": "SPY", "遗物": "RELIC", "巨作": "GREAT_WORK",
    "项目": "PROJECT", "事件": "EVENT", "灾害": "DISASTER", "气候": "CLIMATE",
    "忠诚度压力": "LOYALTY_PRESSURE", "厌战": "WAR_WEARINESS", "满意度": "AMENITY",
    # 改良设施（modgen search 常用中文关键词）
    "农场": "FARM", "牧场": "PASTURE", "矿山": "MINE", "矿场": "MINE",
    "种植园": "PLANTATION", "营地": "CAMP", "渔场": "FISHING_BOATS",
    "伐木场": "LUMBER_MILL", "采石场": "QUARRY", "要塞": "FORT",
    "绿洲": "OASIS", "水渠": "AQUEDUCT", "港口": "HARBOR", "学院": "CAMPUS",
    "圣地": "HOLY_SITE", "商业中心": "COMMERCIAL_HUB", "工业区": "INDUSTRIAL_ZONE",
    "剧院广场": "THEATER", "军营": "ENCAMPMENT", "市政广场": "GOVERNMENT_PLAZA",
}

_ASCII_TOKEN_RE = re.compile(r"[a-z0-9]{2,}")
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_MARKUP_RE = re.compile(r"\[[A-Za-z_]+(?::[^\]]*)?\]")

# 字段权重（文档级）
WEIGHT_NAME = 3.0
WEIGHT_TYPE = 2.5
WEIGHT_MODIFIER_TEXT = 2.0
WEIGHT_DESCRIPTION = 1.5
WEIGHT_ABILITY_KEY = 1.0

# 覆盖度加成：命中查询词越多的文档越靠前（0.6 = 最多 +60%）
COVERAGE_BOOST = 0.6

# 对象级聚合阻尼：best 分 + DAMPING × 其余文档分（避免"文档多"变成"排名高"）
OBJECT_AGGREGATION_DAMPING = 0.18

# 效果词扩展（中文 → 英文 Type 片段）在检索中的权重（低于查询本身的 1.0）
EXPANSION_BOOST_WEIGHT = 0.35

# 对象级覆盖度加成：对象全部证据合计命中的查询概念越多，排名提升越大（1.0 = 最多 +100%）
OBJECT_COVERAGE_BOOST = 1.0

# 精确匹配晋级：查询等于对象 Type/名称时，分数至少提升到最高分的该倍数
EXACT_MATCH_FACTOR = 1.4


def _weighted_tokens(text: str, weight: float) -> list[tuple[str, float]]:
    """分词并按权重配对（同一 token 多次出现只保留一次，避免重复计分）。"""
    seen: set[str] = set()
    pairs: list[tuple[str, float]] = []
    for token in tokenize(text):
        if token in seen:
            continue
        seen.add(token)
        pairs.append((token, weight))
    return pairs


def _promote_exact_matches(
    aggregated: list[tuple[tuple[str, str], float, tuple[float, str, str]]],
    query: str,
    object_meta: dict[tuple[str, str], dict[str, Any]],
) -> list[tuple[tuple[str, str], float, tuple[float, str, str]]]:
    """查询与对象 Type/名称完全相等时，把该对象提到首位。

    用户输入完整 Type（如 DISTRICT_HARBOR）或精确名称时的期望是"直接打开它"，
    不应被聚合分更高的多 Modifier 对象挤到后面。
    """
    raw_query = str(query or "").strip()
    if not raw_query:
        return aggregated
    exact_type = {raw_query.upper(), raw_query.upper().replace(" ", "_")}
    exact_name = raw_query.upper()
    top_score = aggregated[0][1] if aggregated else 0.0

    promoted: list[tuple[tuple[str, str], float, tuple[float, str, str]]] = []
    for target, score, best in aggregated:
        meta = object_meta.get(target, {})
        name = str(meta.get("name") or "").strip().upper()
        is_exact = target[1].upper() in exact_type or (name and name == exact_name)
        if is_exact:
            promoted.append((target, max(score, top_score * EXACT_MATCH_FACTOR), best))
        else:
            promoted.append((target, score, best))
    promoted.sort(key=lambda item: item[1], reverse=True)
    return promoted

# 对象 → Modifier 绑定（对象列, 对象类型列, 分类 key, Modifier 列）
DIRECT_BINDINGS: tuple[tuple[str, str, str, str], ...] = (
    ("TraitModifiers", "TraitType", "trait", "ModifierId"),
    ("DistrictModifiers", "DistrictType", "district", "ModifierId"),
    ("BuildingModifiers", "BuildingType", "building", "ModifierId"),
    ("ImprovementModifiers", "ImprovementType", "improvement", "ModifierID"),
    ("ProjectCompletionModifiers", "ProjectType", "project", "ModifierId"),
    ("PolicyModifiers", "PolicyType", "policy", "ModifierId"),
    ("TechnologyModifiers", "TechnologyType", "technology", "ModifierId"),
    ("CivicModifiers", "CivicType", "civic", "ModifierId"),
    ("GovernorModifiers", "GovernorType", "governor", "ModifierId"),
    ("GovernorPromotionModifiers", "GovernorPromotionType", "governor_promotion", "ModifierId"),
    ("UnitAbilityModifiers", "UnitAbilityType", "unit_ability", "ModifierId"),
    ("UnitPromotionModifiers", "UnitPromotionType", "unit_promotion", "ModifierId"),
    ("GreatPersonIndividualActionModifiers", "GreatPersonIndividualType", "great_person", "ModifierId"),
    ("GreatPersonIndividualBirthModifiers", "GreatPersonIndividualType", "great_person", "ModifierId"),
)
# 经中间表（对象 → TraitType → TraitModifiers）
VIA_TRAIT_TABLES: tuple[tuple[str, str, str], ...] = (
    ("CivilizationTraits", "CivilizationType", "civilization"),
    ("LeaderTraits", "LeaderType", "leader"),
)
# 对象自带 TraitType 列
SELF_TRAIT_TABLES: tuple[tuple[str, str, str], ...] = (
    ("Districts", "DistrictType", "district"),
    ("Buildings", "BuildingType", "building"),
    ("Units", "UnitType", "unit"),
    ("Improvements", "ImprovementType", "improvement"),
)


def strip_markup(text: str) -> str:
    """去掉游戏文本标记（[ICON_X]/[NEWLINE]/[COLOR:…]）与残留 LOC 引用括号，供检索用。"""
    cleaned = _MARKUP_RE.sub(" ", str(text or ""))
    return cleaned.replace("{", " ").replace("}", " ")


def tokenize(text: str, *, term_map: Optional[dict[str, str]] = None) -> list[str]:
    """中英混合分词：领域术语 + 英文/Type 词 + 中文 bigram。"""
    source = str(text or "")
    if not source.strip():
        return []
    mapping = TERM_MAP if term_map is None else term_map
    tokens: list[str] = []
    for cn, en in mapping.items():
        if cn in source:
            tokens.append(f"术语:{en}")
    lowered = source.lower()
    tokens.extend(_ASCII_TOKEN_RE.findall(lowered))
    for run in _CJK_RUN_RE.findall(source):
        if len(run) == 1:
            tokens.append(run)
            continue
        for index in range(len(run) - 1):
            tokens.append(run[index:index + 2])
    return tokens


@dataclass(slots=True)
class _Document:
    kind: str                 # name / type / desc / ability / condition
    payload_key: Any          # 对象 key(category,type) 或 modifier_id / requirement_id
    text: str
    weight: float


@dataclass(slots=True)
class _IndexData:
    documents: list[_Document] = field(default_factory=list)
    lengths: list[int] = field(default_factory=list)
    postings: dict[str, list[tuple[int, int]]] = field(default_factory=lambda: defaultdict(list))
    document_frequency: Counter = field(default_factory=Counter)


class SearchIndex:
    """倒排索引 + BM25 打分（对象级聚合）。"""

    def __init__(self) -> None:
        self._data = _IndexData()
        self._modifier_objects: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self._requirement_objects: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self._object_meta: dict[tuple[str, str], dict[str, Any]] = {}

    # ── 构建 ────────────────────────────────────────────────
    def add_document(self, kind: str, payload_key: Any, text: str, weight: float) -> None:
        cleaned = strip_markup(text)
        if not cleaned.strip():
            return
        tokens = tokenize(cleaned)
        if not tokens:
            return
        index = len(self._data.documents)
        self._data.documents.append(_Document(kind=kind, payload_key=payload_key, text=cleaned, weight=weight))
        self._data.lengths.append(len(tokens))
        for token, frequency in Counter(tokens).items():
            self._data.postings[token].append((index, frequency))
            self._data.document_frequency[token] += 1

    def bind_modifier(self, modifier_id: str, obj_key: tuple[str, str]) -> None:
        if modifier_id:
            self._modifier_objects[str(modifier_id)].add(obj_key)

    def bind_requirement(self, requirement_id: str, obj_key: tuple[str, str]) -> None:
        if requirement_id:
            self._requirement_objects[str(requirement_id)].add(obj_key)

    def set_object_meta(self, obj_key: tuple[str, str], meta: dict[str, Any]) -> None:
        self._object_meta[obj_key] = meta

    @property
    def document_count(self) -> int:
        return len(self._data.documents)

    @property
    def term_count(self) -> int:
        return len(self._data.postings)

    # ── 检索 ────────────────────────────────────────────────
    def search(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        limit: int = 200,
        boost_query: str = "",
        boost_weight: float = 0.35,
    ) -> list[dict[str, Any]]:
        """查询 → 对象级结果（按 BM25 聚合分排序）。

        打分 = BM25(k1=1.2,b=0.75) × 字段权重 × 覆盖度加成，再做**饱和聚合**：

        - `boost_query`：附加查询（如中文查询经效果词扩展出的英文 Type 片段），
          以 `boost_weight` 降权参与打分——命中游戏实现是加分项，但不应压过
          人类可读文本的匹配；
        - 对象级聚合用 `best + DAMPING × 其余`（饱和），避免"拥有上百个 Modifier
          的文明特质"仅因文档数量多而排名虚高；
        - 覆盖度加成（`COVERAGE_BOOST`）压制"只命中一个常见词且文档很短"的长尾。

        返回 [{category, type, score, hit, summary, description}]。
        """
        query_tokens = _weighted_tokens(query, 1.0)
        query_tokens += _weighted_tokens(boost_query, boost_weight)
        if not query_tokens:
            return []
        data = self._data
        total_docs = len(data.documents)
        if not total_docs:
            return []
        average_length = sum(data.lengths) / total_docs

        query_token_set = {token for token, _w in query_tokens}
        raw_scores: dict[int, float] = defaultdict(float)
        matched_tokens: dict[int, set[str]] = defaultdict(set)
        for token, token_weight in query_tokens:
            postings = data.postings.get(token)
            if not postings:
                continue
            df = data.document_frequency[token]
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            if idf <= 0:
                continue
            for doc_index, frequency in postings:
                length = data.lengths[doc_index] or 1
                denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * length / average_length)
                raw_scores[doc_index] += (
                    token_weight * idf * frequency * 2.2 / denominator * data.documents[doc_index].weight
                )
                matched_tokens[doc_index].add(token)

        if not raw_scores:
            return []

        scores: dict[int, float] = {}
        for doc_index, raw_score in raw_scores.items():
            coverage = len(matched_tokens[doc_index]) / len(query_token_set)
            scores[doc_index] = raw_score * (1.0 + COVERAGE_BOOST * coverage)

        # 文档分 → 对象分（饱和聚合 + 对象级覆盖度）
        object_doc_scores: dict[tuple[str, str], list[tuple[float, str, str]]] = defaultdict(list)
        object_tokens: dict[tuple[str, str], set[str]] = defaultdict(set)
        for doc_index, score in scores.items():
            document = data.documents[doc_index]
            if document.kind in ("name", "type", "desc"):
                targets = (document.payload_key,)
            elif document.kind == "ability":
                targets = tuple(self._modifier_objects.get(document.payload_key, ()))
            else:
                targets = tuple(self._requirement_objects.get(document.payload_key, ()))
            for target in targets:
                if category and target[0] != category:
                    continue
                object_doc_scores[target].append((score, document.kind, document.text))
                object_tokens[target] |= matched_tokens[doc_index]

        aggregated: list[tuple[tuple[str, str], float, tuple[float, str, str]]] = []
        for target, entries in object_doc_scores.items():
            entries.sort(key=lambda item: item[0], reverse=True)
            best = entries[0]
            rest = sum(item[0] for item in entries[1:])
            base = best[0] + OBJECT_AGGREGATION_DAMPING * rest
            # 对象级覆盖度：该对象的全部证据合计命中了多少查询概念
            object_coverage = len(object_tokens.get(target, ())) / len(query_token_set)
            aggregated.append((target, base * (1.0 + OBJECT_COVERAGE_BOOST * object_coverage), best))
        aggregated.sort(key=lambda item: item[1], reverse=True)

        # 精确匹配晋级：查询等于对象 Type 或名称时置顶
        # （否则"拥有大量相关 Modifier 的对象"可能靠聚合分压过精确命中）
        aggregated = _promote_exact_matches(aggregated, query, self._object_meta)

        results: list[dict[str, Any]] = []
        for target, score, best in aggregated[:limit]:
            _best_score, best_kind, best_text = best
            meta = self._object_meta.get(target, {})
            results.append({
                "category": target[0],
                "label": meta.get("label", target[0]),
                "name": meta.get("name", target[1]),
                "type": target[1],
                "score": round(score, 3),
                "hit": _HIT_LABELS.get(best_kind, "匹配"),
                "summary": best_text[:120],
                "description": meta.get("description", ""),
            })
        return results

    def object_meta(self, obj_key: tuple[str, str]) -> dict[str, Any]:
        return self._object_meta.get(obj_key, {})


_HIT_LABELS = {
    "name": "名称",
    "type": "Type",
    "desc": "描述",
    "ability": "能力",
    "condition": "条件",
}


# ── 语料构建 ───────────────────────────────────────────────────────
def _rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[tuple]:
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.Error:
        return []


def _load_object_bindings(conn: sqlite3.Connection) -> dict[tuple[str, str], set[str]]:
    """批量装载 对象 → ModifierId 绑定关系。"""
    bindings: dict[tuple[str, str], set[str]] = defaultdict(set)

    for table, obj_col, category, mod_col in DIRECT_BINDINGS:
        for obj_type, modifier_id in _rows(conn, f"SELECT {obj_col}, {mod_col} FROM {table}"):
            if obj_type and modifier_id:
                bindings[(category, str(obj_type))].add(str(modifier_id))

    # 对象 → TraitType → TraitModifiers
    trait_modifiers: dict[str, set[str]] = defaultdict(set)
    for trait_type, modifier_id in _rows(conn, "SELECT TraitType, ModifierId FROM TraitModifiers"):
        if trait_type and modifier_id:
            trait_modifiers[str(trait_type)].add(str(modifier_id))

    for via_table, obj_col, category in VIA_TRAIT_TABLES:
        for obj_type, trait_type in _rows(conn, f"SELECT {obj_col}, TraitType FROM {via_table}"):
            if not obj_type or not trait_type:
                continue
            for modifier_id in trait_modifiers.get(str(trait_type), ()):
                bindings[(category, str(obj_type))].add(modifier_id)

    for table, obj_col, category in SELF_TRAIT_TABLES:
        for obj_type, trait_type in _rows(conn, f"SELECT {obj_col}, TraitType FROM {table}"):
            if not obj_type or not trait_type:
                continue
            for modifier_id in trait_modifiers.get(str(trait_type), ()):
                bindings[(category, str(obj_type))].add(modifier_id)

    # 总督晋升 → 总督
    promotion_governors: dict[str, set[str]] = defaultdict(set)
    for governor_type, promotion_type in _rows(
        conn, "SELECT GovernorType, GovernorPromotionType FROM GovernorPromotions"
    ):
        if governor_type and promotion_type:
            promotion_governors[str(promotion_type)].add(str(governor_type))
    for promotion_type, modifiers in list(bindings.items()):
        if promotion_type[0] != "governor_promotion":
            continue
        for governor_type in promotion_governors.get(promotion_type[1], ()):
            bindings[("governor", governor_type)].update(modifiers)

    return bindings


def _load_modifier_requirement_sets(conn: sqlite3.Connection) -> dict[str, set[str]]:
    """ModifierId → {RequirementSetId}（Owner/Subject 两侧）。"""
    mapping: dict[str, set[str]] = defaultdict(set)
    for modifier_id, owner_set, subject_set in _rows(
        conn, "SELECT ModifierId, OwnerRequirementSetId, SubjectRequirementSetId FROM Modifiers"
    ):
        if not modifier_id:
            continue
        for reqset in (owner_set, subject_set):
            if reqset:
                mapping[str(modifier_id)].add(str(reqset))
    return mapping


def _load_reqset_requirements(conn: sqlite3.Connection) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    for reqset_id, requirement_id in _rows(
        conn, "SELECT RequirementSetId, RequirementId FROM RequirementSetRequirements"
    ):
        if reqset_id and requirement_id:
            mapping[str(reqset_id)].add(str(requirement_id))
    return mapping


def build_index(
    game_conn: sqlite3.Connection,
    loc_conn: Optional[sqlite3.Connection],
    object_types: dict[str, dict[str, Any]],
) -> SearchIndex:
    """构建检索索引（对象 + 效果 + 条件语料，全部经 LOC 解析）。"""
    index = SearchIndex()
    fetch = make_sqlite_fetcher(loc_conn) if loc_conn is not None else (lambda _tag: None)

    def resolve(value: object) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if text.upper().startswith("LOC_"):
            resolved = fetch(text)
            return str(resolved) if resolved else text
        return text

    # 1) 对象名称 / Type / 描述
    for category, meta in object_types.items():
        type_col = meta["type_col"]
        name_col = meta.get("name_col")
        desc_col = meta.get("desc_col")
        columns = [type_col]
        columns.append(name_col or "NULL")
        columns.append(desc_col or "NULL")
        sql = f"SELECT {', '.join(columns)} FROM {meta['table']}"
        for row in _rows(game_conn, sql):
            obj_type = str(row[0] or "").strip()
            if not obj_type or obj_type.startswith("NO_"):
                continue
            obj_key = (category, obj_type)
            name_cn = resolve(row[1])
            desc_cn = resolve(row[2])
            index.set_object_meta(
                obj_key,
                {
                    "label": meta.get("label", category),
                    "name": name_cn or obj_type,
                    "description": desc_cn,
                },
            )
            index.add_document("name", obj_key, name_cn or obj_type, WEIGHT_NAME)
            index.add_document("type", obj_key, obj_type.replace("_", " "), WEIGHT_TYPE)
            if desc_cn:
                index.add_document("desc", obj_key, desc_cn, WEIGHT_DESCRIPTION)

    # 2) 绑定关系
    bindings = _load_object_bindings(game_conn)
    for obj_key, modifier_ids in bindings.items():
        for modifier_id in modifier_ids:
            index.bind_modifier(modifier_id, obj_key)

    # 3) Modifier 语料（Id/Type/参数 + ModifierStrings 中文）
    modifier_text: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for modifier_id, modifier_type in _rows(game_conn, "SELECT ModifierId, ModifierType FROM Modifiers"):
        if modifier_id:
            key = str(modifier_id)
            modifier_text[key].append((f"{key} {modifier_type or ''}", WEIGHT_ABILITY_KEY))
    for modifier_id, name, value in _rows(
        game_conn, "SELECT ModifierId, Name, Value FROM ModifierArguments"
    ):
        if modifier_id and value is not None and str(value).strip():
            modifier_text[str(modifier_id)].append((f"{name} {value}", WEIGHT_ABILITY_KEY))
    for modifier_id, text in _rows(game_conn, "SELECT ModifierId, Text FROM ModifierStrings"):
        if modifier_id and str(text or "").strip():
            resolved_text = resolve(text)
            if resolved_text:
                modifier_text[str(modifier_id)].append((resolved_text, WEIGHT_MODIFIER_TEXT))
    for modifier_id, entries in modifier_text.items():
        if modifier_id not in index._modifier_objects:  # noqa: SLF001 - 仅索引内部对象可见
            continue
        for text, weight in entries:
            index.add_document("ability", modifier_id, text, weight)

    # 4) Requirement 语料（Id/Type/参数 + RequirementStrings）+ 条件 → 对象
    modifier_reqsets = _load_modifier_requirement_sets(game_conn)
    reqset_requirements = _load_reqset_requirements(game_conn)
    modifier_objects = dict(index._modifier_objects)  # noqa: SLF001
    for modifier_id, reqset_ids in modifier_reqsets.items():
        objects = modifier_objects.get(modifier_id)
        if not objects:
            continue
        for reqset_id in reqset_ids:
            for requirement_id in reqset_requirements.get(reqset_id, ()):
                for obj_key in objects:
                    index.bind_requirement(requirement_id, obj_key)

    requirement_text: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for requirement_id, requirement_type in _rows(
        game_conn, "SELECT RequirementId, RequirementType FROM Requirements"
    ):
        if requirement_id:
            key = str(requirement_id)
            requirement_text[key].append((f"{key} {requirement_type or ''}", WEIGHT_ABILITY_KEY))
    for requirement_id, name, value in _rows(
        game_conn, "SELECT RequirementId, Name, Value FROM RequirementArguments"
    ):
        if requirement_id and value is not None and str(value).strip():
            requirement_text[str(requirement_id)].append((f"{name} {value}", WEIGHT_ABILITY_KEY))
    for requirement_id, text in _rows(game_conn, "SELECT RequirementId, Text FROM RequirementStrings"):
        if requirement_id and str(text or "").strip():
            resolved_text = resolve(text)
            if resolved_text:
                requirement_text[str(requirement_id)].append((resolved_text, WEIGHT_MODIFIER_TEXT))
    for requirement_id, entries in requirement_text.items():
        if requirement_id not in index._requirement_objects:  # noqa: SLF001
            continue
        for text, weight in entries:
            index.add_document("condition", requirement_id, text, weight)

    return index


# ── 缓存 ───────────────────────────────────────────────────────────
_INDEX_CACHE: dict[tuple, SearchIndex] = {}
_MAX_CACHE_ENTRIES = 4


def _db_file(conn: Optional[sqlite3.Connection]) -> str:
    if conn is None:
        return ""
    for _seq, name, path in _rows(conn, "PRAGMA database_list"):
        if str(name) == "main":
            return str(path or "")
    return ""


def _mtime(path: str) -> float:
    if not path:
        return 0.0
    try:
        import os

        return os.path.getmtime(path)
    except OSError:
        return 0.0


def get_index(
    game_conn: sqlite3.Connection,
    loc_conn: Optional[sqlite3.Connection],
    object_types: dict[str, dict[str, Any]],
) -> SearchIndex:
    """取（按数据库 mtime 缓存的）检索索引；库文件变化时自动重建。"""
    game_path = _db_file(game_conn)
    text_path = _db_file(loc_conn)
    key = (
        game_path,
        _mtime(game_path),
        text_path,
        _mtime(text_path),
        tuple(sorted(object_types.keys())),
    )
    cached = _INDEX_CACHE.get(key)
    if cached is not None:
        return cached
    index = build_index(game_conn, loc_conn, object_types)
    if len(_INDEX_CACHE) >= _MAX_CACHE_ENTRIES:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[key] = index
    return index


def clear_cache() -> None:
    _INDEX_CACHE.clear()


def iter_matched_terms(query: str) -> Iterable[str]:
    """查询命中的领域术语（供提示"已理解的效果词"）。"""
    source = str(query or "")
    for cn, en in TERM_MAP.items():
        if cn in source:
            yield en
