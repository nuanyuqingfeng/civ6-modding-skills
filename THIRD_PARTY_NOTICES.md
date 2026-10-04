# 第三方来源与采用范围（civ6-modding）

| 来源 | 许可 | 采用内容 | 位置 | 边界 |
|---|---|---|---|---|
| ModTools 5.4（MIT，Copyright (c) 2026 Siqi） | MIT | BM25 自然语言检索层：`search_index.py`（中文 bigram + 领域词典 + 字段权重）、`loc_text.py`（LOC 嵌套解析）——原样复制，仅加来源标注行 | `database/scripts/search_bm25_lib/` | 由 `search_impl.py` 消费；类型口径以本机 `database/` 快照为准，不引用 ModTools 的类型数字口径（家族 FAMILY_INDEX §八 D7） |
| ModTools 5.4（同上） | MIT | 静态地标算法层 `landmarks.py`（SDK TileBase 组合/校验/合并）——原样复制 + 模板路径参数化；`verify_bundle`/`cook_bundle` 移植自 `modgen/landmark.py` | `tools/landmark_lib/`、`tools/landmark_tool.py` | 与 .CIV 工程通道解耦（不移植 import/merger/civ6proj_generator）；Landmarks.artdef 模板取自 SDK pantry 官方文件 |
| ModTools 5.4 知识库（同上） | MIT | modifiers 分域参考、patterns、官方 UI 面板对照（改写吸收，逐篇篇头标注） | `reference/modifiers-catalog/`、`reference/ui-panels/`（2026-09-28 吸收） | ExposedMembers 示例按家族口径（context-matrix.md）改写；命名表述以本机 conventions.md 为准 |

说明：
- `search_impl.py` 本体是家族自有实现（思路借鉴自 ModTools `db/ability_search.py`，未拷贝其代码）；
  2026-09-28 仅并入上述两个算法模块与 technology/civic 类别补齐。
- 家族其他成员的第三方来源登记在各自仓库：`civ6-art-unpack/THIRD_PARTY_NOTICES.md`（千川白浪移交包 / ModTools art-unpack）、
  `civ6-html-ui/`（自带 MIT LICENSE，Copyright (c) 2026 Siqi）、`civ6-landmarks/THIRD_PARTY_NOTICES.md`（文档改写自 ModTools 知识库）。

## ModTools 5.4 上游与许可全文（MIT）

- 上游仓库：<https://github.com/SiQi-1/ModTools5.4>（MIT，Copyright (c) 2026 Siqi）；
- 上表所列代码复制与知识改写均出自该仓库。MIT 要求版权声明与本许可声明随"实质性部分"一并保留，故随分发附带原文如下。

```
MIT License

Copyright (c) 2026 Siqi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
