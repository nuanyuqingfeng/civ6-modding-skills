"""landmark_lib —— 静态地标（TileBase AST）组合与校验的算法层。

移植来源：ModTools 5.4（MIT，Copyright (c) 2026 Siqi）`ModTools_5_4/project/landmarks.py`
（原样复制，两处标注内适配见模块 docstring）。纯标准库；SDK Assets 为只读输入。
与 .CIV 工程通道完全解耦：落地到 ModBuddy 工程由 `landmark_tool.py install` 承担。
许可见 civ6-modding/THIRD_PARTY_NOTICES.md。
"""
from .landmarks import (  # noqa: F401
    SDKIndex,
    LocalResourceIndex,
    compose,
    load_bundle,
    validate_assets,
    validate_local_sources,
    merge_artdef,
    bind_entry,
    text_at,
    xml_text,
)
