# 模式 C：手动遍历多层次 ATTACH

## 适用场景
- 按人口/城市数/时代 等 分多档触发不同效果
- 每档的**效果目标不同**（如 1环+科技、2环+金币）
- 无法用一个动态 Amount 表达式覆盖所有情况

## 核心思路

**能用手动遍历就不要追求"优雅"。** 1个 Modifier 是一行 SQL，30个 Modifier 也是 SQL。游戏 DB 不嫌行多，Lua 不嫌行多。正确的多行比"精巧"的单行好。

## 0045 实例：人口 1-31 → 6 种地块产出

领袖文本描述：
> 从1开始，城市每拥有3人口，距离市中心 1环：+1科技+1文化 / 2环：+1金币+1信仰 / 3环：+1生产力+1食物，最多计入31人口

**方案**：每个城市遍历人口阈值（1,4,7,10,13,16,19,22,25,28,31），用 ATTACH + CityHasXPopulation Requirement 决定是否触发。

### 链结构
```
TraitModifiers (领袖特质 TRAIT_LEADER_SIQI_L0045_1)
  → N 个 ATTACH_MODIFIER（每个入口阈值一个）
    → MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER
    → SubjectRequirementSetId = REQSET_CITY_HAS_X_POPULATION
      → 内层：MODIFIER_PLAYER_ADJUST_PLOT_YIELD
        → 地格产出（固定 YieldType + Amount + MinDistance/MaxDistance）
```

### 6 种产出对应的距离

| 产出 | 环 | MinDistance | MaxDistance |
|------|----|-------------|-------------|
| 科技 +1 | 1环 | 1 | 1 |
| 文化 +1 | 1环 | 1 | 1 |
| 金币 +1 | 2环 | 2 | 2 |
| 信仰 +1 | 2环 | 2 | 2 |
| 生产力 +1 | 3环 | 3 | 3 |
| 食物 +1 | 3环 | 3 | 3 |

每档人口（1,4,7,10,13,16,19,22,25,28,31）都触发这 6 种产出。
总计：11 档 × 6 产出 = **66 个 ATTACH Modifier + 6 个产出 Modifier + 11 个 RequirementSet**

### 产出 Modifier（6 个，内层效果，复用）
```sql
-- 1环科技
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_PLOT_YIELD_SCIENCE_1_PLOT_ADJACENT_TO_OWNER',
 'MODIFIER_PLAYER_ADJUST_PLOT_YIELD',
 'REQSET_SIQI_0045_PLOT_ADJACENT_TO_OWNER', 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_PLOT_YIELD_SCIENCE_1_PLOT_ADJACENT_TO_OWNER', 'Amount', 1),
('MODIFIER_SIQI_0045_ADJUST_PLOT_YIELD_SCIENCE_1_PLOT_ADJACENT_TO_OWNER', 'YieldType', 'YIELD_SCIENCE');

-- 其余 5 个同理：Culture/Gold/Faith/Production/Food
-- 对应的 REQSET 用不同 MinDistance/MaxDistance
```

### 地块距离 Requirement（3 个，复用）
```sql
INSERT INTO Requirements (RequirementId, RequirementType, Inverse) VALUES
('REQ_SIQI_0045_PLOT_ADJACENT_TO_OWNER', 'REQUIREMENT_PLOT_ADJACENT_TO_OWNER', 0);

INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_0045_PLOT_ADJACENT_TO_OWNER', 'MinDistance', 1),
('REQ_SIQI_0045_PLOT_ADJACENT_TO_OWNER', 'MaxDistance', 1);

-- REQSET_SIQI_0045_PLOT_ADJACENT_TO_OWNER2: MinDistance=2, MaxDistance=2
-- REQSET_SIQI_0045_PLOT_ADJACENT_TO_OWNER3: MinDistance=3, MaxDistance=3
```

### 人口阈值 RequirementSet（11 个）
```sql
INSERT INTO Requirements (RequirementId, RequirementType, Inverse) VALUES
('REQ_SIQI_0045_CITY_HAS_1_POPULATION', 'REQUIREMENT_CITY_HAS_X_POPULATION', 0);

INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_0045_CITY_HAS_1_POPULATION', 'Amount', 1);

INSERT INTO RequirementSets (RequirementSetId, RequirementSetType) VALUES
('REQSET_SIQI_0045_CITY_HAS_1_POPULATION', 'REQUIREMENTSET_TEST_ALL');

-- 重复 11 次，Amount = 1,4,7,10,13,16,19,22,25,28,31
```

### ATTACH Modifier（66 个）
```sql
-- 每档人口 6 个 ATTACH，链到对应产出
-- 例：人口≥1 → 1环文化
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ATTACH_MODIFIER_CITY_HAS_1_POPULATION',
 'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER',
 'REQSET_SIQI_0045_CITY_HAS_1_POPULATION', 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ATTACH_MODIFIER_CITY_HAS_1_POPULATION',
 'ModifierId', 'MODIFIER_SIQI_0045_ADJUST_PLOT_YIELD_CULTURE_1_PLOT_ADJACENT_TO_OWNER');

-- 可写脚本生成 66 行 SQL，但手动 INSERT 完全可行
```

## 标准 ModifierType（无需 DynamicModifiers）

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_ADJUST_PLOT_YIELD` | 地块产出 |

## 常见 RequirementType

| RequirementType | 参数 | 用途 |
|-----------------|------|------|
| `REQUIREMENT_CITY_HAS_X_POPULATION` | `Amount` | 城市人口 ≥ X |
| `REQUIREMENT_PLOT_ADJACENT_TO_OWNER` | `MinDistance`, `MaxDistance` | 地块距离市中心范围 |

## 参考代码位置

- `Siqi_Leaders_0045/Data/Siqi_Leaders_0045_Modifiers.sql` 行 5-71 (TraitModifiers, 66 个 ATTACH)
- `Siqi_Leaders_0045/Data/Siqi_Leaders_0045_Modifiers.sql` 行 125-310 (产出 Modifier + 参数)

## 常见错误

1. **试图用 Lua 动态计算替代手动遍历** — 首选 SQL 遍历，Lua 留到最后
2. **认为行太多不好维护** — 66 行明确 SQL 比 20 行 Lua + SQL 混合更容易排查
3. **复用内层 Modifier 时忘了每个 ATTACH 都要单独链** — 每个 ATTACH 的 ModifierArguments 都写明 ModifierId
