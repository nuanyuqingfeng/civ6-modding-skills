# 模式 A：通用Trait ATTACH → 动态效果

## 适用场景
- 每存活主要文明 +5战斗力
- 每宗主城邦 +2移动力
- 任何"每拥有N个X，获得Y效果"的场景，X是玩家/城邦等独立实体

## 核心思路

**不写 Lua 计数。** 利用每个实体已有的通用 Trait，在该 Trait 上挂 ATTACH Modifier。每个实体独立触发一次 ATTACH，N 个实体 = N 次效果叠加。

- 主要文明 → `TRAIT_LEADER_MAJOR_CIV`
- 城邦 → `MINOR_CIV_DEFAULT_TRAIT`

当实体灭亡/失去宗主时，其 Trait 失效 → ATTACH 链断裂 → 效果消失。

## 表链路

```
TraitModifiers
  (TraitType, ModifierId)
    ↓
Modifiers (外层 ATTACH)
  (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent)
    ↓
ModifierArguments (外层)
  (ModifierId, 'ModifierId', 内层ModifierId)
    ↓
Modifiers (内层 — 给目标玩家的效果)
  (ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent)
    ↓
ModifierArguments (内层)
  (ModifierId, Name, Value)  -- Amount/Key 等
```

## 完整代码示例：每存活主要文明 +5战斗力(Property)

### Step 1 — TraitModifiers
```sql
INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_SIQI_0045_ATTACH_MODIFIER_LEADER_L0045');
```

### Step 2 — 外层 ATTACH Modifier
```sql
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ATTACH_MODIFIER_LEADER_L0045',
 'MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER',
 'REQSET_SIQI_0045_LEADER_L0045',  -- 只 ATTACH 到目标领袖的玩家
 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ATTACH_MODIFIER_LEADER_L0045',
 'ModifierId',
 'MODIFIER_SIQI_0045_ADJUST_PROPERTY_5');  -- 链到内层
```

### Step 3 — 内层效果（Property 累加）
> ⚠️ **`MODIFIER_PLAYER_UNITS_ADJUST_PROPERTY` 不是标准类型**（DB 实测），必须先自定义（Types + DynamicModifiers），0045 的做法：
```sql
INSERT INTO Types (Type, Kind) VALUES
('MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY', 'KIND_MODIFIER');

INSERT INTO DynamicModifiers (ModifierType, EffectType, CollectionType) VALUES
('MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY',
 'EFFECT_ADJUST_UNIT_PROPERTY', 'COLLECTION_PLAYER_UNITS');

INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_PROPERTY_5',
 'MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY',  -- 自定义类型，非标准！
 NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_PROPERTY_5', 'Key',    'Siqi0045_Combat_From_Civ'),
('MODIFIER_SIQI_0045_ADJUST_PROPERTY_5', 'Amount', '5');
```

### Step 4 — RequirementSet
```sql
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType) VALUES
('REQSET_SIQI_0045_LEADER_L0045', 'REQUIREMENTSET_TEST_ALL');

INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId) VALUES
('REQSET_SIQI_0045_LEADER_L0045', 'REQ_SIQI_0045_LEADER_L0045');

INSERT INTO Requirements (RequirementId, RequirementType, Inverse) VALUES
('REQ_SIQI_0045_LEADER_L0045', 'REQUIREMENT_PLAYER_LEADER_TYPE_MATCHES', 0);

INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_0045_LEADER_L0045', 'LeaderType', 'LEADER_SIQI_L0045_1');
```

## 完整代码示例：每宗主城邦 +2移动力

```sql
-- TraitModifiers
INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('MINOR_CIV_DEFAULT_TRAIT', 'MODIFIER_SIQI_0045_ATTACH_MODIFIER_SUZERAIN_AND_L0045');

-- 外层 ATTACH
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ATTACH_MODIFIER_SUZERAIN_AND_L0045',
 'MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER',
 'REQSET_SIQI_0045_SUZERAIN_AND_L0045', 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ATTACH_MODIFIER_SUZERAIN_AND_L0045',
 'ModifierId', 'MODIFIER_SIQI_0045_ADJUST_MOVEMENT_2');

-- 内层效果
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_MOVEMENT_2',
 'MODIFIER_PLAYER_UNITS_ADJUST_MOVEMENT',  -- 标准类型
 NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_MOVEMENT_2', 'Amount', '2');

-- RequirementSet：宗主国 + 领袖匹配
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType) VALUES
('REQSET_SIQI_0045_SUZERAIN_AND_L0045', 'REQUIREMENTSET_TEST_ALL');

INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId) VALUES
('REQSET_SIQI_0045_SUZERAIN_AND_L0045', 'REQ_SIQI_0045_IS_SUZERAIN'),
('REQSET_SIQI_0045_SUZERAIN_AND_L0045', 'REQ_SIQI_0045_LEADER_L0045');

INSERT INTO Requirements (RequirementId, RequirementType, Inverse) VALUES
('REQ_SIQI_0045_IS_SUZERAIN', 'REQUIREMENT_PLAYER_IS_SUZERAIN', 0);
```

## 标准 ModifierType（此模式用到的，无需 DynamicModifiers）

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER` | `COLLECTION_ALL_PLAYERS` |
| `MODIFIER_PLAYER_UNITS_ADJUST_MOVEMENT` | `COLLECTION_PLAYER_UNITS` |

> ⚠️ 曾在此表误列 `MODIFIER_PLAYER_UNITS_ADJUST_PROPERTY` 为标准类型——**不存在**，必须自定义（见 Step 3）。

## 通用 Trait 清单（直接用于 TraitModifiers）

| TraitType | 持有者 | 何时失效 |
|-----------|--------|---------|
| `TRAIT_LEADER_MAJOR_CIV` | 每个主要文明 | 文明灭亡 |
| `MINOR_CIV_DEFAULT_TRAIT` | 每个城邦 | 城邦被征服 |

## 常见错误

1. **用 `MODIFIER_MAJOR_PLAYERS_ATTACH_MODIFIER` 代替 `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER`** — 后者更通用，SubjectRequirementSetId 做筛选即可
2. **创建自定义 DynamicModifier 替代标准类型** — 先验证标准型是否存在
3. **把 SubjectRequirementSetId 放到 OwnerRequirementSetId 位置** — Modifiers 表列序为 `(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent)`
4. **怀疑 REQUIREMENT_PLAYER_IS_SUZERAIN 在城邦 Trait ATTACH 中的行为** — 已验证可用
