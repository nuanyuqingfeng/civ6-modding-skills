"""effect_search_lib —— BM25 效果实现检索的算法层。

移植自 ModTools 5.4（MIT，Copyright (c) 2026 Siqi）：
- `search_index.py` ← `ModTools_5_4/db/search_index.py`（原样复制，仅加来源标注）
- `loc_text.py`     ← `ModTools_5_4/db/loc_text.py`（原样复制，仅加来源标注）
- 本文件的 `search_objects_bm25` 语义对齐 `modgen/mt_bridge.py` 同名函数（去掉 ModTools 仓库壳层）。

许可见 `civ6-modding/THIRD_PARTY_NOTICES.md`。
"""
from __future__ import annotations

from typing import Any, Optional

from . import search_index
from . import loc_text

DEFAULT_LANGUAGE = loc_text.DEFAULT_LANGUAGE

TERM_MAP = search_index.TERM_MAP


def search_objects_bm25(
    game_conn: Any,
    loc_conn: Optional[Any],
    object_types: dict[str, dict[str, Any]],
    keyword: str,
    *,
    category: Optional[str] = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """BM25 对象检索：中文查询经领域词典扩展英文 Type 片段作为降权加分项。"""
    kw = str(keyword or "").strip()
    if not kw:
        return []
    index = search_index.get_index(game_conn, loc_conn, object_types)
    boost_terms = list(search_index.iter_matched_terms(kw))
    return index.search(
        kw,
        category=category,
        limit=limit,
        boost_query=" ".join(boost_terms),
        boost_weight=search_index.EXPANSION_BOOST_WEIGHT,
    )
