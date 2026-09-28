# 模式 D：建城一次性效果

## 适用场景
- 建城时额外扩张地块（俄罗斯模式）
- 建城时赠送人口
- 建城时赠送单位（魔王）

## 标准 ModifierType（无需 DynamicModifiers）

| ModifierType | EffectType | CollectionType | 参数 |
|-------------|-----------|----------------|------|
| `MODIFIER_PLAYER_ADJUST_CITY_TILES` | `EFFECT_ADJUST_PLAYER_CITY_TILES` | `COLLECTION_OWNER` | `Amount` — 额外地块数 |
| `MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_POPULATION` | `EFFECT_ADJUST_CITY_POPULATION` | `COLLECTION_PLAYER_BUILT_CITIES` | `Amount` — 人口数 |
| `MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL` | 赠送单位 | `COLLECTION_OWNER` | `UnitType`, `Amount`, `AllowUniqueOverride` |
| `MODIFIER_PLAYER_CITIES_ADJUST_POLICY_HOUSING` | 住房 | `COLLECTION_PLAYER_CITIES` | `Amount` |

## 代码示例

### +30 地块（即额外获得 3 环）
```sql
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_CITY_TILES_30',
 'MODIFIER_PLAYER_ADJUST_CITY_TILES',
 NULL, 0, 1);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_CITY_TILES_30', 'Amount', '30');

INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_CIVILIZATION_SIQI_C0045_1', 'MODIFIER_SIQI_0045_ADJUST_CITY_TILES_30');
```

### +3 人口
```sql
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_POPULATION_3',
 'MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_POPULATION',
 NULL, 0, 1);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_POPULATION_3', 'Amount', '3');
```

### 首都赠送魔王（条件：城市数 < 2）
```sql
INSERT INTO Requirements (RequirementId, RequirementType, Inverse) VALUES
('REQ_SIQI_0045_HAS_NOT_CITIES_2', 'REQUIREMENT_PLAYER_HAS_AT_LEAST_NUMBER_CITIES', 1);

INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_0045_HAS_NOT_CITIES_2', 'Amount', 2);

INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_GRANT_UNIT_IN_CITY_U0045_1_1_HAS_NOT_CITIES_2',
 'MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL',
 'REQSET_SIQI_0045_HAS_NOT_CITIES_2', 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_GRANT_UNIT_IN_CITY_U0045_1_1_HAS_NOT_CITIES_2', 'AllowUniqueOverride', 1),
('MODIFIER_SIQI_0045_GRANT_UNIT_IN_CITY_U0045_1_1_HAS_NOT_CITIES_2', 'Amount', 1),
('MODIFIER_SIQI_0045_GRANT_UNIT_IN_CITY_U0045_1_1_HAS_NOT_CITIES_2', 'UnitType', 'UNIT_SIQI_U0045_1');
```

### +3 住房
```sql
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_POLICY_HOUSING_3',
 'MODIFIER_PLAYER_CITIES_ADJUST_POLICY_HOUSING',
 NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_POLICY_HOUSING_3', 'Amount', '3');
```

## 常见错误

1. **用 Lua `GameEvents.CityBuilt` 代替 SQL** — SQL 能处理的建城效果不需要 Lua
2. **忘了 `Inverse=1` 做 "小于N" 判断** — `REQUIREMENT_PLAYER_HAS_AT_LEAST_NUMBER_CITIES` + `Inverse=1` = "城市数小于N"
3. **赠送单位忘了 `AllowUniqueOverride=1`** — 特色单位不设置则不会赠送
