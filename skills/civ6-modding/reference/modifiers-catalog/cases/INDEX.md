# Modifier 案例索引

> 所有案例均从 0001~0046 及 Arknights 系列 Mod 的实际 SQL 中提取，未经修改。

## 按模式查找

| 模式 | 文件 | 案例数 | 适用场景 |
|------|------|--------|---------|
| **Grant Ability** | [case-grant-ability.md](case-grant-ability.md) | 17 | 给单位加能力(战力/移动/隐匿/经验等) |
| **Yield / 简单效果** | [case-yield.md](case-yield.md) | 44+ | 地块产出/城市加成/赠送科技 |
| **ATTACH 链** | [case-attach-chain.md](case-attach-chain.md) | 7 | 外层挂内层效果(城市→地块/单位) |
| **自定义 DynamicModifier** | [case-custom-modifier.md](case-custom-modifier.md) | 7 | 标准类型不支持的自定义效果 |
| **SELECT 动态生成** | [case-select-generated.md](case-select-generated.md) | 9 | 批量生成 Modifier(遍历科技/区域/产出) |
| **复杂 RequirementSet** | [case-complex-req.md](case-complex-req.md) | 5 | 多条件组合(TEST_ALL/TEST_ANY) |

## 按 ModifierType 查找

| ModifierType | 案例文件 | 重要程度 |
|-------------|---------|---------|
| `MODIFIER_PLAYER_UNITS_GRANT_ABILITY` | grant-ability | ★★★★★ 最重要 |
| `MODIFIER_ALL_UNITS_GRANT_ABILITY` | grant-ability | ★★★★ |
| `MODIFIER_PLAYER_ADJUST_PLOT_YIELD` | yield | ★★★★★ |
| `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER` | attach-chain | ★★★★ |
| `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER` | attach-chain | ★★★ |
| `MODIFIER_PLAYER_GRANT_SPECIFIC_TECHNOLOGY` | yield | ★★★★ |
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_YIELD_MODIFIER` | yield | ★★★ |
| `MODIFIER_SINGLE_PLOT_ADJUST_PLOT_YIELDS` | yield | ★★★ |
| `MODIFIER_PLAYER_ADD_CULTURE_BOMB_TRIGGER` | yield | ★★ |
| `MODIFIER_PLAYER_CITIES_ADJUST_WONDER_PRODUCTION` | yield | ★★ |
| `MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` | yield | ★★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_FROM_COMBAT` | yield | ★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT` | yield | ★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_SIGHT` | yield | ★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_HIDDEN_VISIBILITY` | yield | ★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_TERRAIN_COST` | yield | ★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_ZOC` | yield | ★ |
| `MODIFIER_PLAYER_UNIT_ADJUST_DAMAGE` | yield | ★ |
| `MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` | yield | ★ |
| `MODIFIER_SINGLE_CITY_CULTURE_BORDER_EXPANSION` | custom-modifier | ★ |
| `MODIFIER_SINGLE_CITY_ADJUST_EXTRA_GREAT_WORK_SLOTS` | yield | ★ |
| `MODIFIER_PLAYER_ADJUST_RANDOM_EVENT_NO_UNIT_DAMAGE` | select-generated | ★★ |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE` | select-generated | ★★ |
| `MODIFIER_PLAYER_ADJUST_TOURISM` | select-generated | ★ |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE` | select-generated | ★ |
| 自定义 (Types+DynamicModifiers) | custom-modifier | ★★★ |

## 参考 Mod 项目

| Mod | 代表作 | 特点 |
|-----|--------|------|
| Siqi_Leaders_0040 | 贞子 | Grant Ability + ATTACH + PlotYield 经典组合 |
| Siqi_Leaders_0042 | 莱伊 | 距离分层战斗力 + 双标签 Ability + SELECT 遍历区域 |
| Siqi_Leaders_0045 | 特蕾西娅 | ALL_PLAYERS_ATTACH + 人口阈值 ×66 |
| Siqi_Leaders_0032 | 原神系列 | 8个自定义 DynamicModifier + 复数领袖 |
| SIQI_LEADERS_0006 | 早期 | 17个 Grant Ability 变体(含条件/Property/双标签) |
| Siqi_Leaders_0026 | 早期 | OwnerRequirementSetId + SubjectRequirementSetId 叠条件 |

## 其他参考入口

- [战斗资料的历史来源补充](case-legacy-combat-sources.md)
