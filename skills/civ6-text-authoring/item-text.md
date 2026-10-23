# 类 2 —— 区域 / 建筑 / 单位等「可被 trait 关联的物品」文本规范

> 覆盖 `LOC_DISTRICT_*` `LOC_BUILDING_*` `LOC_UNIT_*` `LOC_UNITNAME_*` `LOC_IMPROVEMENT_*`
> `LOC_PROJECT_*` `LOC_PROMOTION_*` `LOC_RESOURCE_*` `LOC_FEATURE_*` `LOC_POLICY_*` `LOC_BELIEF_*`
> `LOC_GREAT*` `LOC_GOVT_*` `LOC_CIVIC_*` `LOC_TECH_*` `LOC_BOOST_*`（语料 4,682 条）
> 语料：`reference/catalog/item.tsv` ｜ 查询：`zh_corpus.sqlite` `WHERE Category='item'`

> 「可被 trait 关联」= 这些对象能经 `TraitModifiers` / `CivilizationTraits` / `BuildingModifiers` /
> `DistrictModifiers` / `UnitAbilityModifiers` 等绑定表挂到文明/领袖特质上。写它们的文本时，
> **效果文案必须与它承载的 Modifier 链一致**（数值、条件、范围口径一致）。

## 1. 命名规范（tag 骨架）

```
LOC_<KIND>_<X>_NAME             显示名
LOC_<KIND>_<X>_DESCRIPTION      效果/规则描述
LOC_<KIND>_<X>_SHORT_NAME       短名（区域/项目常配）
LOC_<KIND>_<X>_DESCRIPTION_ADJACENCY   ← 区域专用：相邻加成面板（见 类5）
LOC_<KIND>_<X>_EXPANSION1_DESCRIPTION / _EXPANSION2_DESCRIPTION   ← 规则集变体
LOC_<KIND>_<X>_QUOTE / _QUOTE_1 / _QUOTE_2    ← 科技/市政/奇观名言（见 类3 引申）
LOC_<KIND>_<X>_BOOST_* / LOC_BOOST_*_DESCRIPTION   ← 尤里卡/鼓舞触发条件
```

| KIND | 对应游戏对象 | 典型 tag |
|---|---|---|
| `DISTRICT` | 区域 | `LOC_DISTRICT_ACROPOLIS_NAME` 卫城 |
| `BUILDING` | 建筑 | `LOC_BUILDING_ALHAMBRA_NAME` 阿尔罕布拉宫 |
| `UNIT` | 单位 | `LOC_UNIT_AIRCRAFT_CARRIER_NAME` 航空母舰 |
| `UNITNAME` | 单位番号（随机名池） | `LOC_UNITNAME_*_PREFIX/SUFFIX` |
| `IMPROVEMENT` | 改良设施 | `LOC_IMPROVEMENT_ALCAZAR_NAME` 阿卡萨城堡 |
| `PROJECT` | 项目 | `LOC_PROJECT_BREAD_AND_CIRCUSES_NAME` 面包和马戏 |
| `PROMOTION` | 晋升 | `LOC_PROMOTION_*_NAME / _DESCRIPTION` |
| `RESOURCE` / `FEATURE` | 资源 / 地貌 | `LOC_RESOURCE_*` / `LOC_FEATURE_*` |
| `POLICY` / `BELIEF` | 政策卡 / 信条 | `LOC_POLICY_*_NAME/_DESCRIPTION` |
| `GREAT_PERSON` / `GREATWORK` | 伟人 / 巨作 | `LOC_GREAT_PERSON_*` |

## 2. 描述写法规范

1. **效果描述与 Modifier 链同口径**：`+N [ICON_Y] 产出`、`+N% [ICON_Production] 生产力`、
   `+N [ICON_Strength] 战斗力`。数值必须等于 `ModifierArguments.Value`，否则界面与实机不符。
2. **条件显式化**：「在拥有 X 的城市中……」不要省略前提（否则玩家无法判断生效条件）。
3. **产出名按官方词表**：住房 `[ICON_Housing] 住房`、宜居度 `[ICON_Amenities] 宜居度`、
   魅力 `[ICON_Appeal] 魅力`、忠诚度 `忠诚度`。
4. **区域另配 `_DESCRIPTION_ADJACENCY`**（面板专用，措辞见 [adjacency-text.md](adjacency-text.md)）。
5. **单位名称不译**：`LOC_UNIT_AMERICAN_P51_NAME` = P-51战斗机（型号保留英文+中文类属）。
6. **规则集变体**：同一对象在不同资料片下效果不同 → `_EXPANSION1_DESCRIPTION` / `_EXPANSION2_DESCRIPTION`
   另开（全语料 33 / 100 条）。**风云变幻口径**：启用了 EXP2 时引擎取 `_EXPANSION2_DESCRIPTION`，
   `_DESCRIPTION` 视为本体版；不要改动本体值去"迎合"资料片。
   ```
   LOC_BELIEF_CROSS_CULTURAL_DIALOGUE_DESCRIPTION            = 其他文明中每出现5个信仰该宗教的信徒，则+1 [ICON_Science] 科技值。
   LOC_BELIEF_CROSS_CULTURAL_DIALOGUE_EXPANSION2_DESCRIPTION = 该宗教每有4个信徒则+1 [ICON_SCIENCE] 科技值。
   ```

## 3. 与 trait 关联时的文本落点

| 关联方式 | 文本落点 |
|---|---|
| 文明/领袖特质解锁的专属物品（UB/UU/UD/UI） | `LOC_<KIND>_<X>_*`，并在特质 `_DESCRIPTION` 中提到该物品 |
| 物品自带能力 | `LOC_ABILITY_<X>_*`（→ 类1），由 `UnitAbilityModifiers` / `BuildingModifiers` 绑 |
| 政策/信条给物品加成 | `LOC_POLICY/BELIEF_*_DESCRIPTION`，描述里点明被加成的物品 |

> 物品清单准入（哪些物品有资格进 `PlayerItems`）：见 `civ6-modding/leader-authoring.md`「PlayerItems 准入规则」——
> 限**有实质 TRAIT 链**的区域/建筑/单位/改良，资源不入列。

## 4. 校验清单

- [ ] `_NAME` / `_DESCRIPTION` 成对；区域含 `_DESCRIPTION_ADJACENCY`
- [ ] 描述数值 == Modifier 参数（对照 `ModifierArguments`）
- [ ] `[ICON_x]` 合法、产出名用官方词表
- [ ] 多资料片差异已拆 `_EXPANSION1/2_DESCRIPTION`
- [ ] 跑 `check_text_refs.py` + `check_adjacency_text.py`
