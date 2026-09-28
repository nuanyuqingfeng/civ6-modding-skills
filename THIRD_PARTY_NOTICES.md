# 第三方来源与采用范围（civ6-modding）

| 来源 | 许可 | 采用内容 | 位置 | 边界 |
|---|---|---|---|---|
| ModTools 5.4（MIT，Copyright (c) 2026 Siqi） | MIT | BM25 自然语言检索层：`search_index.py`（中文 bigram + 领域词典 + 字段权重）、`loc_text.py`（LOC 嵌套解析）——原样复制，仅加来源标注行 | `database/scripts/search_bm25_lib/` | 由 `search_impl.py` 消费；类型口径以本机 `database/` 快照为准，不引用 ModTools 的类型数字口径（家族 FAMILY_INDEX §八 D7） |
| ModTools 5.4 知识库（同上） | MIT | modifiers 分域参考、patterns、官方 UI 面板对照（改写吸收，逐篇篇头标注） | `reference/modifiers-catalog/`、`reference/ui-panels/`（2026-09-28 吸收） | ExposedMembers 示例按家族口径（context-matrix.md）改写；命名表述以本机 conventions.md 为准 |

说明：
- `search_impl.py` 本体是家族自有实现（思路借鉴自 ModTools `db/ability_search.py`，未拷贝其代码）；
  2026-09-28 仅并入上述两个算法模块与 technology/civic 类别补齐。
- 家族其他成员的第三方来源登记在各自仓库：`civ6-art-unpack/THIRD_PARTY_NOTICES.md`（千川白浪移交包 / ModTools art-unpack）、
  `civ6-html-ui/`（自带 MIT LICENSE，Copyright (c) 2026 Siqi）。
