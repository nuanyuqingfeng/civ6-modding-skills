# Civilization VI Workshop Patterns

Advanced techniques used by real workshop mods.

---

## Bulk SQL Generation

Generate hundreds of similar modifiers with `SELECT` against game tables.

```sql
-- Generate an era-gated modifier for every era
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
SELECT 'MODIFIER_SCIENCE_BOOST_' || EraType, 'MODIFIER_PLAYER_ADJUST_YIELD_CHANGE',
       'REQSET_ERA_' || EraType
FROM Eras WHERE EraType != 'ERA_ANCIENT';

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_SCIENCE_BOOST_' || EraType, 'YieldType', 'YIELD_SCIENCE'
FROM Eras WHERE EraType != 'ERA_ANCIENT'
UNION ALL
SELECT 'MODIFIER_SCIENCE_BOOST_' || EraType, 'Amount', '20'
FROM Eras WHERE EraType != 'ERA_ANCIENT';

-- Generate requirements for all eras
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
SELECT 'REQSET_ERA_' || EraType, 'REQUIREMENTSET_TEST_ALL' FROM Eras;

INSERT INTO Requirements (RequirementId, RequirementType)
SELECT 'REQ_ERA_' || EraType, 'REQUIREMENT_GAME_ERA_ATLEAST_EXPANSION' FROM Eras;

INSERT INTO RequirementArguments (RequirementId, Name, Value)
SELECT 'REQ_ERA_' || EraType, 'EraType', EraType FROM Eras;
```

## Recursive CTE for Property Scales

Use `WITH RECURSIVE` to generate power-of-two property requirements.

```sql
-- Generate requirement sets for property values 1, 2, 4, 8 ... 4096
WITH RECURSIVE NumSeq AS (
    SELECT 1 AS i UNION ALL SELECT i * 2 FROM NumSeq WHERE i < 4096
)
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
SELECT 'REQSET_PROPERTY_VALUE_' || i, 'REQUIREMENTSET_TEST_ALL' FROM NumSeq;
```

## Custom DynamicModifiers

When base-game `ModifierType`s are insufficient, create your own.

```sql
-- 1. Register the type
INSERT INTO Types (Type, Kind) VALUES
('MODIFIER_MY_CAPITAL_ATTACH_MODIFIER', 'KIND_MODIFIER');

-- 2. Define collection + effect
INSERT INTO DynamicModifiers (ModifierType, CollectionType, EffectType) VALUES
('MODIFIER_MY_CAPITAL_ATTACH_MODIFIER', 'COLLECTION_PLAYER_CAPITAL_CITY', 'EFFECT_ATTACH_MODIFIER');

-- 3. Use it like any other modifier
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MY_WRAPPER', 'MODIFIER_MY_CAPITAL_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MY_WRAPPER', 'ModifierId', 'MY_SUB_MODIFIER');
```

Common custom patterns:
- `COLLECTION_PLAYER_CAPITAL_CITY` + `EFFECT_ATTACH_MODIFIER` — attach to capital only
- `COLLECTION_PLAYER_DISTRICTS` + `EFFECT_ATTACH_MODIFIER` — attach to all districts
- `COLLECTION_PLAYER_GOVERNORS` + `EFFECT_ATTACH_MODIFIER` — attach to governor cities
- `COLLECTION_CITY_TRAINED_UNITS` + `EFFECT_ATTACH_MODIFIER` — attach to units trained in city

## Property State System

Properties are invisible numeric flags stored on players, cities, or plots.

```sql
-- Set a player property
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('SET_MY_PROPERTY', 'MODIFIER_PLAYER_ADJUST_PROPERTY');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('SET_MY_PROPERTY', 'Key', 'PROPERTY_MY_FLAG'),
       ('SET_MY_PROPERTY', 'Amount', '1');

-- Check a plot property in a requirement
INSERT INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_HAS_MY_FLAG', 'REQUIREMENT_PLOT_PROPERTY_MATCHES');
INSERT INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_HAS_MY_FLAG', 'PropertyName', 'PROPERTY_MY_FLAG'),
       ('REQ_HAS_MY_FLAG', 'PropertyMinimum', '1');
```

City properties use `REQUIREMENT_PLOT_PROPERTY_MATCHES` (city center plot holds the property).

### Binary Bitfield Pattern

Use N modifiers with 2ⁿ-权重 property keys to represent any integer value dynamically. Lua sets the plot properties via `SetProperty` to control which modifiers are active.

SQL — register N weighted bits:
```sql
-- Bit 1 (value 1)
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MOD_BIT_VALUE_1', 'MODIFIER_ALL_CITIES_ADJUST_CITY_YIELD_CHANGE', 'REQSET_BIT_VALUE_1');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MOD_BIT_VALUE_1', 'YieldType', 'YIELD_SCIENCE'),
       ('MOD_BIT_VALUE_1', 'Amount', '1');
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_BIT_VALUE_1', 'REQUIREMENTSET_TEST_ALL');
INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES ('REQSET_BIT_VALUE_1', 'REQ_BIT_VALUE_1');
INSERT INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_BIT_VALUE_1', 'REQUIREMENT_PLOT_PROPERTY_MATCHES');
INSERT INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_BIT_VALUE_1', 'PropertyName', 'PROPERTY_BITFLAG_1'),
       ('REQ_BIT_VALUE_1', 'PropertyMinimum', '1');

-- Bit 2 (value 2) — same pattern with PROPERTY_BITFLAG_2, Amount=2
-- Bit 4 (value 4) — same pattern with PROPERTY_BITFLAG_4, Amount=4
-- ...
```

Lua — set value with old-value comparison to minimize writes:
```lua
local BINARY_BITS = {1, 2, 4, 8, 16, 32, 64}

-- Read current binary state from plot property keys
function GetBitfield(plot, prefix)
    local bits = {}
    for i = 1, #BINARY_BITS do
        bits[i] = plot:GetProperty(prefix .. BINARY_BITS[i]) or 0
    end
    return bits
end

-- Write new value, only touching changed bits
function SetBitfield(plot, prefix, newBits)
    local oldBits = GetBitfield(plot, prefix)
    for i = 1, #newBits do
        if newBits[i] ~= oldBits[i] then
            plot:SetProperty(prefix .. BINARY_BITS[i], newBits[i])
        end
    end
end

-- Convert number to bit array
function NumToBits(num, n)
    local result, bits = {}, {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}
    for i = n, 1, -1 do
        table.insert(result, num >= bits[i] and 1 or 0)
        if num >= bits[i] then num = num - bits[i] end
    end
    -- Reverse
    local out = {}
    for i = 1, #result do out[i] = result[#result - i + 1] end
    return out
end
```

## Multi-Layer Attach Chains

Chain 2–3 attachment modifiers to reach the correct collection scope.

**Pattern: All Players → Cities → Districts**
```sql
-- Layer 1: Distribute to all players who have a pantheon
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('L1_ALL_PLAYERS', 'MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER', 'PLAYER_HAS_PANTHEON_REQUIREMENTS');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('L1_ALL_PLAYERS', 'ModifierId', 'L2_CITIES');

-- Layer 2: Distribute to each of that player's cities
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('L2_CITIES', 'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('L2_CITIES', 'ModifierId', 'L3_DISTRICTS');

-- Layer 3: Actual effect on Harbor districts only
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('L3_DISTRICTS', 'MODIFIER_CITY_DISTRICTS_ADJUST_DISTRICT_AMENITY', 'REQSET_CITY_HAS_HARBOR');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('L3_DISTRICTS', 'Amount', '1');
```

## Modifying and Removing Base Game Data

```sql
-- Direct table updates
UPDATE Units SET BaseMoves = 3, CostProgressionParam1 = 40 WHERE UnitType = 'UNIT_SETTLER';
UPDATE Improvements SET MovementChange = 1 WHERE ImprovementType = 'IMPROVEMENT_GREAT_WALL';
UPDATE GlobalParameters SET Value = -40 WHERE Name = 'CIVIC_COST_PERCENT_CHANGE_BEFORE_GAME_ERA';

-- Remove unwanted vanilla modifiers from a trait
DELETE FROM TraitModifiers
WHERE TraitType = 'TRAIT_LEADER_ANTIQUES_AND_PARKS'
  AND ModifierId = 'MODIFIER_TRAIT_LEADER_ANTIQUES_AND_PARKS_GRANT_UNIT';

-- Update an existing modifier argument
UPDATE ModifierArguments SET Value = '1'
WHERE ModifierId = 'TRAIT_NATIONAL_PARK_APPEAL_BONUS' AND Name = 'Amount';
```

## Modifier Timing Flags

| Flag | Meaning | Typical Use |
|------|---------|-------------|
| `RunOnce` | Executes only once when first applied | One-time yield grants, unit spawns |
| `Permanent` | Persists even if requirement later fails | Property sets, one-time bonuses |
| `NewOnly` | Only applies to objects created after modifier is active | Rarely used |

```sql
-- One-time capital unit grant (RunOnce=1, Permanent=1)
INSERT INTO Modifiers (ModifierId, ModifierType, RunOnce, Permanent)
VALUES ('GRANT_SCOUT_ONCE', 'MODIFIER_PLAYER_GRANT_UNIT_IN_CAPITAL', 1, 1);
```

## Special Argument Types

Some `ModifierArguments` support `Type` column for special behavior:

```sql
-- Scale value by game speed
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_GP_POINTS', 'Amount', 'ScaleByGameSpeed', '10');
```

## Complex Attachment Example

All Warriors get +5 Movement and ignore terrain cost **before turn 10**:

```sql
-- Requirement: turn < 10 (Inverse=1 on turn >= 10)
INSERT INTO Requirements (RequirementId, RequirementType, Inverse)
VALUES ('REQ_TURN_AT_LEAST_10', 'REQUIREMENT_GAME_TURN_ATLEAST', 1);
INSERT INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_TURN_AT_LEAST_10', 'MinGameTurn', '10');

-- Requirement: unit is Warrior
INSERT INTO Requirements (RequirementId, RequirementType)
VALUES ('REQ_UNIT_IS_WARRIOR', 'REQUIREMENT_UNIT_TYPE_MATCHES');
INSERT INTO RequirementArguments (RequirementId, Name, Value)
VALUES ('REQ_UNIT_IS_WARRIOR', 'UnitType', 'UNIT_WARRIOR');

-- Combine requirements
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
VALUES ('REQSET_WARRIOR_BEFORE_TURN_10', 'REQUIREMENTSET_TEST_ALL');
INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId)
VALUES 
    ('REQSET_WARRIOR_BEFORE_TURN_10', 'REQ_TURN_AT_LEAST_10'),
    ('REQSET_WARRIOR_BEFORE_TURN_10', 'REQ_UNIT_IS_WARRIOR');

-- Sub-modifiers (single-unit scope)
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_WARRIOR_MOVEMENT_5', 'MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT', 'REQSET_WARRIOR_BEFORE_TURN_10');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_WARRIOR_MOVEMENT_5', 'Amount', '5');

INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
VALUES ('MODIFIER_WARRIOR_IGNORE_TERRAIN', 'MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_TERRAIN_COST', 'REQSET_WARRIOR_BEFORE_TURN_10');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES 
    ('MODIFIER_WARRIOR_IGNORE_TERRAIN', 'Ignore', '1'),
    ('MODIFIER_WARRIOR_IGNORE_TERRAIN', 'Type', 'ALL');

-- Attachment modifiers (distribute to all units)
INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_ATTACH_WARRIOR_MOVEMENT', 'MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_ATTACH_WARRIOR_MOVEMENT', 'ModifierId', 'MODIFIER_WARRIOR_MOVEMENT_5');

INSERT INTO Modifiers (ModifierId, ModifierType)
VALUES ('MODIFIER_ATTACH_WARRIOR_TERRAIN', 'MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER');
INSERT INTO ModifierArguments (ModifierId, Name, Value)
VALUES ('MODIFIER_ATTACH_WARRIOR_TERRAIN', 'ModifierId', 'MODIFIER_WARRIOR_IGNORE_TERRAIN');

-- Bind to all major civs
INSERT INTO TraitModifiers (TraitType, ModifierId)
VALUES 
    ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_ATTACH_WARRIOR_MOVEMENT'),
    ('TRAIT_LEADER_MAJOR_CIV', 'MODIFIER_ATTACH_WARRIOR_TERRAIN');
```

## Building-Distributed Ability with Per-Building Scaling

**场景**: 每个建筑建成后，给特定单位类型的全图单位添加增益；多个同类建筑建成后，增益按建筑数量叠加。

**方案**: ABILITY 分发（不叠加） + PROPERTY 计数（自动叠加）。

为什么不用 ATTACH_MODIFIER：ATTACH 每触发一次就叠一层 modifier，多个建筑会导致 modifier 层数累积异常。ABILITY 天然不叠加，同名 ABILITY 单位只持有一层，多建筑调用 GRANT_ABILITY 安全。

### 完整 SQL 模板

以下以"起源信标"（取代纪念碑的建筑，使所有声骸单位 +3 战斗力/座、+2 移动力）为例：

```sql
-- ============================================
-- Step 1: 创建 ABILITY（Inactive=1，隐藏不可手动移除）
-- ============================================
INSERT INTO Types (Type, Kind) VALUES
('ABILITY_GENESIS_ECHO_BUFF_TMP', 'KIND_ABILITY');

INSERT INTO UnitAbilities (UnitAbilityType, Description, Inactive) VALUES
('ABILITY_GENESIS_ECHO_BUFF_TMP', 'LOC_ABILITY_GENESIS_ECHO_BUFF_TMP_DESCRIPTION', 1);

-- TypeTags: 限定 ABILITY 作用的目标单位范围
INSERT INTO TypeTags (Type, Tag) VALUES
('ABILITY_GENESIS_ECHO_BUFF_TMP', 'CLASS_ECHO_TMP');

-- ============================================
-- Step 2: 具体效果 modifier（纳入 ABILITY 内）
-- ============================================
-- 战斗力跟随 PROPERTY 自动叠加（每座建筑 +3）
INSERT INTO Modifiers (ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MOD_GENESIS_ECHO_COMBAT', 'MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH', 0, 1);
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MOD_GENESIS_ECHO_COMBAT', 'Key', 'PROPERTY_GENESIS_COUNT_TMP');

-- 移动力 +2（固定值，不跟随建筑数量）
INSERT INTO Modifiers (ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MOD_GENESIS_ECHO_MOVE', 'MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT', 0, 1);
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MOD_GENESIS_ECHO_MOVE', 'Amount', 2);

-- 将效果绑定到 ABILITY
INSERT INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_GENESIS_ECHO_BUFF_TMP', 'MOD_GENESIS_ECHO_COMBAT'),
('ABILITY_GENESIS_ECHO_BUFF_TMP', 'MOD_GENESIS_ECHO_MOVE');

-- ModifierStrings 预览（{Property} 占位符显示实际数值）
INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES
('MOD_GENESIS_ECHO_COMBAT', 'Preview', 'LOC_MOD_GENESIS_ECHO_COMBAT_TMP_PREVIEW'),
('MOD_GENESIS_ECHO_MOVE',    'Preview', 'LOC_MOD_GENESIS_ECHO_MOVE_TMP_PREVIEW');

-- ============================================
-- Step 3: 建筑绑定 — 计数 + 分发
-- ============================================
-- (A) 每个建筑建成给玩家 PROPERTY +N（N=每座建筑的战斗力增益值）
INSERT INTO BuildingModifiers (BuildingType, ModifierId) VALUES
('BUILDING_GENESIS_TMP', 'MOD_GENESIS_PROP_COUNT');

INSERT INTO Modifiers (ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MOD_GENESIS_PROP_COUNT', 'MODIFIER_PLAYER_ADJUST_PROPERTY', 0, 1);
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MOD_GENESIS_PROP_COUNT', 'PropertyName', 'PROPERTY_GENESIS_COUNT_TMP'),
('MOD_GENESIS_PROP_COUNT', 'Amount', 3);  -- 每座+3，战斗力的 Key 会自动乘此值

-- (B) 每个建筑建成给全图单位分发 ABILITY（ABILITY 不叠加，多建筑安全）
INSERT INTO BuildingModifiers (BuildingType, ModifierId) VALUES
('BUILDING_GENESIS_TMP', 'MOD_GENESIS_GRANT_ABILITY');

INSERT INTO Modifiers (ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MOD_GENESIS_GRANT_ABILITY', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY', 0, 1);
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MOD_GENESIS_GRANT_ABILITY', 'AbilityType', 'ABILITY_GENESIS_ECHO_BUFF_TMP');
```

### 数据流

```
BUILDING_GENESIS_TMP (每座建成时)
│
├─ BuildingModifiers → MODIFIER_PLAYER_ADJUST_PROPERTY (玩家 PROPERTY +3)
│   └─ 每建1座玩家 PROPERTY 累加，N座 = N×3
│
└─ BuildingModifiers → MODIFIER_PLAYER_UNITS_GRANT_ABILITY (分发 ABILITY)
    └─ 因 ABILITY 不叠加，N座也只分发1次，单位只持有一层

ABILITY_GENESIS_ECHO_BUFF_TMP (单位获得后)
│
├─ UnitAbilityModifiers → MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH (Key=PROPERTY)
│   └─ 自动读玩家 PROPERTY 值 → 战斗力 = PROPERTY 值本身
│
└─ UnitAbilityModifiers → MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT (Amount=2)
    └─ 固定 +2，不跟随建筑数量
```

### 关键决策点

| 需求 | 错误方案 | 正确方案 |
|------|---------|---------|
| 建筑给单位增益 | ATTACH_MODIFIER（叠加，多建筑失控） | ABILITY（不叠加，多建筑安全） |
| 每座建筑叠加数值 | Lua 统计建筑数量 | BuildingModifiers + PROPERTY 自动计数 |
| PROPERTY 转为战斗力 | Lua 读 PROPERTY 再写 modifier | `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` + `Key`（引擎内置桥接） |
| 限定目标单位种类 | GRANT_ABILITY + SubjectReqSet | TypeTags + CLASS 标签（设定 ABILITY 作用于哪些单位类） |
| 限定条件（距离/状态等） | Ability 内部 modifier + SubjectReqSet | GRANT_ABILITY + SubjectReqSet（引擎自动 toggle 整组 ABILITY） |
| ABILITY 生命周期 | Permanent=1（自动赋予、不可移除） | Inactive=1（隐藏，由建筑 GRANT_ABILITY 激活，不可手动移除） |

### SubjectRequirementSetId 放置规则

`SubjectRequirementSetId` **只应该放在 GRANT_ABILITY 的 Modifier 上**，不放在 Ability 内部的 modifier 上。引擎自动在条件满足/不满足时授予/收回整组 Ability：

```
GRANT_ABILITY Modifier (SubjectReqSet: 距离/状态条件)     ← 条件写在这里
  └─ AbilityType: ABILITY_AURA_BUFF                          ← 引擎 toggle 整组
       └─ UnitAbilityModifiers → MODIFIER_... (无条件)      ← 内部不设 AnyReqSet
```

例外：**Lua `AttachAbilityToUnit`** 手动附加时，无 GRANT toggle，需 modifier 自行控制。

### 零 Lua

此模式完全由 SQL 驱动：属性写入（PROPERTY）、数值读出（combat Key）、单位分发（ABILITY）均为引擎内置机制。仅当需要运行时复杂条件判断时才需要 Lua 介入。
