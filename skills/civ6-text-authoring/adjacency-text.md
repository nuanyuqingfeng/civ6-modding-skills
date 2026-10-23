# 类 5 —— 相邻加成写法规范

> 跨类集合（语料 440 条，`IsAdjacency=1`）：含「相邻」或 `+N：每个…` 句式。
> 语料：`zh_corpus.sqlite` `WHERE IsAdjacency=1` ｜ 校验器：`civ6-modding/scripts/check_adjacency_text.py`

## 1. 三种落点（先分清写哪一处）

| 落点 | tag / 数据位 | 用途 | 是否强制 `{1_num}` |
|---|---|---|---|
| **A. 加成描述（数据）** | `Adjacency_YieldChanges.Description` → LOC tag | 引擎计算相邻加成时替换 `{1_num}` | **是**（必须含 `[ICON_x]` + `{1_num}`） |
| **B. 区域面板** | `LOC_<DISTRICT>_DESCRIPTION_ADJACENCY` | 区域详情面板的「相邻加成」区块 | 否（整段展示） |
| **C. 百科说明** | `LOC_PEDIA_*` | 文明百科的解释段落 | 否 |

> ⚠️ A 与 B 用途不同**不可混写**：把面板长句塞进 `Adjacency_YieldChanges.Description` → 引擎替换 `{1_num}` 失败、数值错乱。

## 2. A 类（数据描述）强制格式

`check_adjacency_text.py` 的机械判据：**文本必须同时包含 `[ICON_x]` 与 `{1_num}`**。

```
LOC_DISTRICT_COMMERCIAL_HUB_DESCRIPTION_ADJACENCY 风格（B 类，面板）：
  相邻：每个相邻港口，或单元格边缘有河流的区域获得大额 [ICON_Gold] 金币加成。相邻区域单元格获得小额 [ICON_Gold] 金币加成。

A 类（Adjacency_YieldChanges.Description）应为可替换数值的短句，例：
  与河流相邻时+{1_num} [ICON_Gold] 金币
```

## 3. 句式库（官方范式）

### 3.1 产出相邻（区域 / 改良）
- **区域面板**：`每个相邻<对象>获得<大额|标准|小额> [ICON_Y] <产出>加成`
  ```
  LOC_DISTRICT_SUGUBA_DESCRIPTION_ADJACENCY = 相邻：每个相邻圣地获得大量 [ICON_Gold] 金币加成。…
  ```
- **从单元格**：`<区域>从相邻<地貌/资源>单元格+1 [ICON_Y] <产出>`
  ```
  LOC_BELIEF_DANCE_OF_THE_AURORA_DESCRIPTION = 圣地区域从相邻冻土单元格+1 [ICON_Faith] 信仰值 。
  ```

### 3.2 战斗相邻（最规范的三式）
```
每 个 相 邻 的 <单位> 提 供 +{1_Amount} [ICON_Strength] 战斗力     ← 计数式
LOC_ABILITY_LLANERO_ADJACENCY_STRENGTH_DESCRIPTION = 每个相邻的牛仔骑兵提供+2 [ICON_Strength] 战斗力。

与 <对象> 相 邻 时 +{1_Amount} [ICON_Strength] 战斗力              ← 条件式
LOC_ABILITY_HOPLITE_NEIGHBOR_COMBAT_MODIFIER_DESCRIPTION = 与另一个重装步兵相邻时+{1_Amount} [ICON_Strength] 战斗力

在 己 方 <X> 相 邻 单 元 格 中 的 <单位> ……                        ← 位置式
LOC_ABILITY_TRADER_PROTECTED_BY_MANDEKALU_DESCRIPTION = 在己方曼德卡鲁骑兵相邻陆地单元格中的贸易单位可免遭掠夺。
```

### 3.3 百科清单式（多来源枚举）
```
+N：每个相邻<A>、<B>、<C>，或<D>          ← 枚举用「、」分隔，尾项用「，或」
LOC_PEDIA_CONCEPTS_PAGE_CITIES_11_CHAPTER_CONTENT_PARA_10 = +1：每个相邻圣地、剧院广场、娱乐中心、运河、堤坝，或奇观
LOC_PEDIA_CONCEPTS_PAGE_CITIES_11_CHAPTER_CONTENT_PARA_15 = -1：每个相邻工业区、军营、机场，或宇航中心
```

## 4. 数值档位词表（固定译法）

| 英文档 | 官方中文 |
|---|---|
| major | **大额** |
| standard | **标准** |
| minor | **小额** |
| （具体数值式） | 直接用 `+N [ICON_Y] <产出>` |

> 产出名固定：`[ICON_Gold] 金币` / `[ICON_Faith] 信仰值` / `[ICON_Culture] 文化值` /
> `[ICON_Science] 科技值` / `[ICON_Production] 生产力` / `[ICON_FOOD] 食物` / `[ICON_Strength] 战斗力`。

## 5. 常见错误

| 错误 | 后果 | 正确 |
|---|---|---|
| A 类描述漏 `{1_num}` | 数值不显示或替换失败 | 补 `{1_num}` |
| A 类描述漏 `[ICON_x]` | 无图标，判为不合规 | 补图标 |
| 把 B 类长句写进 `Adjacency_YieldChanges.Description` | 面板与实机文案串味 | A/B 分写 |
| 相邻对象用 tag 名而非中文 | 显示原文 | 用中文对象名 |
| 混用「相邻」与「相邻的」（计数式需「每个相邻的X」，条件式需「与X相邻时」） | 句义含糊 | 按 §3.2 三式择一 |
| 负值未加 `[COLOR_RED]…[ENDCOLOR]` | 负数不醒目 | `[COLOR_RED]-N …[ENDCOLOR]` |

## 6. 校验清单

- [ ] `Adjacency_YieldChanges.Description` 文本含 `[ICON_x]` + `{1_num}`
- [ ] 区域有 `_DESCRIPTION_ADJACENCY`（B 类）且与 A 类不混写
- [ ] 档位词用 大额/标准/小额；产出名用官方词表
- [ ] 跑 `python <civ6-modding>\scripts\check_adjacency_text.py <工程根>`（0 问题）
