"""LOC 文本解析的**单一实现**（纯标准库，无 PyQt / 无 settings 依赖）。

移植来源：ModTools 5.4（MIT，Copyright (c) 2026 Siqi）`ModTools_5_4/db/loc_text.py`，
2026-09-28 原样复制；改动仅限本行标注。

背景：游戏文本大量使用引用链——文本里嵌 `{LOC_XXX}`，被引用的文本还可能再嵌一层。
历史上仓库里有四份各自为政的解析实现（其中两份不支持嵌套，导致能力搜索显示/检索
都拿到带 `{LOC_...}` 的原文）。本模块是唯一权威实现，其余调用点一律委托到这里。

规则：
- 只解析 `{LOC_...}` 花括号引用；`{1_Amount}` 等数值占位符原样保留；
- 迭代解析（默认最多 12 轮），`visited` 防环——自引用/循环引用不会死循环；
- 查不到的 tag 保留原样（回退语义由调用方通过 `resolve_tag_or_original` 决定）；
- 语言默认 `zh_Hans_CN`，查不到时可选回退任意语言（与原 GUI 行为一致）。

用法：
    conn = sqlite3.connect(text_db)
    fetch = make_sqlite_fetcher(conn)
    resolve_tag_or_original(fetch, "LOC_TRAIT_X_DESCRIPTION")

    # 或直接复用已有连接查询
    ability_search.resolve_loc(loc_conn, tag)   # 内部委托本模块
"""
from __future__ import annotations

import re
import sqlite3
from typing import Callable, Optional

# `{LOC_XXX}` 引用（允许花括号内空白，与游戏文本实际写法兼容）
LOC_REF_PATTERN = re.compile(r"\{\s*(LOC_[A-Za-z0-9_]+)\s*\}")

DEFAULT_LANGUAGE = "zh_Hans_CN"
DEFAULT_MAX_DEPTH = 12

Fetcher = Callable[[str], Optional[str]]


def make_sqlite_fetcher(
    conn: sqlite3.Connection,
    *,
    language: str = DEFAULT_LANGUAGE,
    fallback_any_language: bool = True,
    cache_size: int = 20000,
) -> Fetcher:
    """构造 tag → 文本 的查询函数（文本库 LocalizedText 表，内置查询缓存）。"""
    normalized_language = str(language or "").strip().lower()
    cache: dict[str, Optional[str]] = {}

    def fetch(tag: str) -> Optional[str]:
        key = str(tag or "").strip()
        if not key:
            return None
        if key in cache:
            return cache[key]
        value = _query_tag(conn, key, normalized_language, fallback_any_language)
        if len(cache) < max(0, cache_size):
            cache[key] = value
        return value

    return fetch


def _query_tag(
    conn: sqlite3.Connection,
    tag: str,
    normalized_language: str,
    fallback_any_language: bool,
) -> Optional[str]:
    try:
        row = conn.execute(
            "SELECT Text FROM LocalizedText WHERE Tag = ? AND lower(Language) = ? LIMIT 1",
            (tag, normalized_language),
        ).fetchone()
    except sqlite3.Error:
        return None
    if row is None and fallback_any_language:
        try:
            row = conn.execute(
                "SELECT Text FROM LocalizedText WHERE Tag = ? LIMIT 1",
                (tag,),
            ).fetchone()
        except sqlite3.Error:
            return None
    if row is None:
        return None
    value = str(row[0] or "").strip()
    return value or None


def resolve_tag(fetch: Fetcher, tag: str, *, max_depth: int = DEFAULT_MAX_DEPTH) -> Optional[str]:
    """解析单个 tag（含嵌套引用展开）。tag 不存在返回 None。"""
    normalized = str(tag or "").strip()
    if not normalized:
        return None
    value = fetch(normalized)
    if value is None:
        return None
    return resolve_text(fetch, value, max_depth=max_depth)


def resolve_tag_or_original(
    fetch: Fetcher,
    tag: str,
    *,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> str:
    """解析 tag；查不到时返回原 tag（调用方用 `result != tag` 判断是否命中）。"""
    normalized = str(tag or "").strip()
    if not normalized:
        return normalized
    resolved = resolve_tag(fetch, normalized, max_depth=max_depth)
    return resolved if resolved is not None else normalized


def resolve_text(
    fetch: Fetcher,
    text: str,
    *,
    max_depth: int = DEFAULT_MAX_DEPTH,
    strip_reference_newlines: bool = False,
) -> str:
    """展开文本中的 `{LOC_...}` 引用（多层、防环）；未解析的引用保留原样。

    strip_reference_newlines=True 时去掉**被引用文本**里的换行（保留旧版文本预览行为）。
    """
    result = str(text or "")
    if not result:
        return result

    visited: set[str] = set()
    for _ in range(max(1, max_depth)):
        matches = LOC_REF_PATTERN.findall(result)
        if not matches:
            return result

        pending = [tag for tag in matches if tag.upper() not in visited]
        if not pending:
            return result

        changed = False
        for tag in pending:
            visited.add(tag.upper())
            replacement = fetch(tag)
            if replacement is None:
                continue
            if strip_reference_newlines and "\n" in replacement:
                replacement = replacement.replace("\n", "")
            # 替换所有该 tag 的出现（同一层内可能重复引用）
            new_result = LOC_REF_PATTERN.sub(
                lambda match: replacement
                if match.group(1).upper() == tag.upper()
                else match.group(0),
                result,
            )
            if new_result != result:
                result = new_result
                changed = True
        if not changed:
            return result
    return result


def looks_like_tag(value: object) -> bool:
    """判断一个值是否是 LOC tag（用于"是 tag 才解析"的调用点）。"""
    return str(value or "").strip().upper().startswith("LOC_")


def contains_ref(value: object) -> bool:
    """判断文本里是否含未展开的 `{LOC_...}` 引用。"""
    return bool(LOC_REF_PATTERN.search(str(value or "")))
