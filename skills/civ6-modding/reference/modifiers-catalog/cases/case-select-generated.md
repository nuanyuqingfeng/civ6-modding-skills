# SELECT 动态生成 案例

> 用 `INSERT ... SELECT FROM` 从游戏表中动态生成 Modifier，避免逐行手写重复代码。
> 标准 ModifierType + 动态生成 → 每个实例自动获得对应的 RequirementSet + RequirementArguments。

---

## 链条模板

```sql
-- 对标准 ModifierType：Traits → Modifiers → ModifierArguments → Req → ReqArgs 逐表 SELECT
-- 对自定义 ModifierType：先 Types → DynamicModifiers，再 SELECT 后续表

INSERT INTO TraitModifiers (TraitType, ModifierId)
SELECT 'TRAIT_xxx', 'MODIFIER_PREFIX_' || column FROM game_table;

INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId)
SELECT 'MODIFIER_PREFIX_' || column, 'MODIFIER_xxx', 'REQSET_PREFIX_' || column FROM game_table;

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_PREFIX_' || column, 'ParamName', column FROM game_table;

INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
SELECT 'REQSET_PREFIX_' || column, 'REQUIREMENTSET_TEST_ALL' FROM game_table;

INSERT INTO Requirements (RequirementId, RequirementType)
SELECT 'REQ_PREFIX_' || column, 'REQUIREMENT_xxx' FROM game_table;

INSERT INTO RequirementArguments (RequirementId, Name, Value)
SELECT 'REQ_PREFIX_' || column, 'ParamName', column FROM game_table;

INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId)
SELECT 'REQSET_PREFIX_' || column, 'REQ_PREFIX_' || column FROM game_table;
```

---

## 案例 C1：遍历所有地形 → 产出加成

**来源**：Siqi_Leaders_0028（自定义 Terrain_YieldChanges 驱动表）

```sql
-- TraitModifiers
INSERT INTO TraitModifiers (TraitType, ModifierId)
SELECT 'TRAIT_LEADER_SIQI_L0028_L1',
       'MODIFIER_SIQI_C0028_C1_ADJUST_PLOT_' || YieldType || '_' || TerrainType
FROM Terrain_YieldChanges;

-- Modifiers
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId)
SELECT 'MODIFIER_SIQI_C0028_C1_ADJUST_PLOT_' || YieldType || '_' || TerrainType,
       'MODIFIER_PLAYER_ADJUST_PLOT_YIELD',
       'SIQI0028_DISTRICT_CANAL_' || TerrainType
FROM Terrain_YieldChanges;

-- ModifierArguments（双参数 UNION）
INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_SIQI_C0028_C1_ADJUST_PLOT_' || YieldType || '_' || TerrainType, 'Amount', YieldChange
FROM Terrain_YieldChanges
UNION SELECT 'MODIFIER_SIQI_C0028_C1_ADJUST_PLOT_' || YieldType || '_' || TerrainType, 'YieldType', YieldType
FROM Terrain_YieldChanges;
```

---

## 案例 C2：遍历所有科技/市政 → 城市产出

**来源**：Siqi_Leaders_0043

```sql
-- 科技部分
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId)
SELECT 'MODIFIER_SIQI_0043_TECH_PRODUCTION_' || TechnologyType,
       'MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE',
       'REQSET_SIQI_0043_TECH_' || TechnologyType
FROM Technologies;

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_SIQI_0043_TECH_PRODUCTION_' || TechnologyType, 'YieldType', 'YIELD_PRODUCTION'
FROM Technologies;

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_SIQI_0043_TECH_PRODUCTION_' || TechnologyType, 'Amount', '2'
FROM Technologies;

INSERT INTO RequirementSets (RequirementSetId, RequirementSetType)
SELECT 'REQSET_SIQI_0043_TECH_' || TechnologyType, 'REQUIREMENTSET_TEST_ALL'
FROM Technologies;

INSERT INTO Requirements (RequirementId, RequirementType, Inverse)
SELECT 'REQ_SIQI_0043_TECH_' || TechnologyType, 'REQUIREMENT_PLAYER_HAS_TECHNOLOGY', 0
FROM Technologies;

INSERT INTO RequirementArguments (RequirementId, Name, Value)
SELECT 'REQ_SIQI_0043_TECH_' || TechnologyType, 'TechnologyType', TechnologyType
FROM Technologies;

INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId)
SELECT 'REQSET_SIQI_0043_TECH_' || TechnologyType, 'REQ_SIQI_0043_TECH_' || TechnologyType
FROM Technologies;

-- 市政部分：把 TechnologyType 换成 CivicType，Technologies 换成 Civics 即可
```

---

## 案例 C3：遍历所有专业化区域 → 攻击射程+1

**来源**：Siqi_Leaders_0042

```sql
-- 只遍历 RequiresPopulation=1 的区域（13 种专业化区域）
INSERT INTO Modifiers (ModifierId, ModifierType, OwnerRequirementSetId, RunOnce, Permanent)
SELECT 'MODIFIER_SIQI_L0042_RANGE_' || REPLACE(DistrictType, 'DISTRICT_', ''),
       'MODIFIER_PLAYER_UNITS_ADJUST_ATTACK_RANGE',
       'REQSET_SIQI_L0042_HAS_' || REPLACE(DistrictType, 'DISTRICT_', ''),
       0, 1
FROM Districts WHERE RequiresPopulation = 1;

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_SIQI_L0042_RANGE_' || REPLACE(DistrictType, 'DISTRICT_', ''), 'Amount', 1
FROM Districts WHERE RequiresPopulation = 1;

INSERT INTO Requirements (RequirementId, RequirementType, Triggered)
SELECT 'REQ_SIQI_L0042_HAS_' || REPLACE(DistrictType, 'DISTRICT_', ''),
       'REQUIREMENT_PLAYER_HAS_DISTRICT', 0
FROM Districts WHERE RequiresPopulation = 1;

INSERT INTO RequirementArguments (RequirementId, Name, Value)
SELECT 'REQ_SIQI_L0042_HAS_' || REPLACE(DistrictType, 'DISTRICT_', ''), 'DistrictType', DistrictType
FROM Districts WHERE RequiresPopulation = 1;
```

---

## 案例 C4：遍历全 Yields 表 → 全产出加成

**来源**：Siqi_Leaders_0022

```sql
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId)
SELECT 'MODIFIER_SIQI_0022_ADJACENT_PLOT_' || YieldType, 'MODIFIER_PLAYER_ADJUST_PLOT_YIELD', 'SIQI_0022_ADJACENT'
FROM Yields;

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT       'MODIFIER_SIQI_0022_ADJACENT_PLOT_' || YieldType, 'Amount', 1 FROM Yields
UNION SELECT 'MODIFIER_SIQI_0022_ADJACENT_PLOT_' || YieldType, 'YieldType', YieldType FROM Yields;
```

---

## 案例 C5：遍历 RandomEvents → 防灾害

**来源**：Siqi_Leaders_0041

```sql
INSERT INTO TraitModifiers (TraitType, ModifierId)
SELECT 'TRAIT_LEADER_SIQI_L0041_1',
       'MODIFIER_SIQI_0041_PLAYER_ADJUST_' || RandomEventType || '_NO_UNIT_DAMAGE'
FROM RandomEvents WHERE EffectOperatorType != 'SEA_LEVEL';

INSERT INTO Modifiers(ModifierId, ModifierType, Permanent)
SELECT 'MODIFIER_SIQI_0041_PLAYER_ADJUST_' || RandomEventType || '_NO_UNIT_DAMAGE',
       'MODIFIER_PLAYER_ADJUST_RANDOM_EVENT_NO_UNIT_DAMAGE', 0
FROM RandomEvents WHERE EffectOperatorType != 'SEA_LEVEL';

INSERT INTO ModifierArguments (ModifierId, Name, Value)
SELECT 'MODIFIER_SIQI_0041_PLAYER_ADJUST_' || RandomEventType || '_NO_UNIT_DAMAGE', 'NoDamage', 1
FROM RandomEvents WHERE EffectOperatorType != 'SEA_LEVEL'
UNION SELECT 'MODIFIER_SIQI_0041_PLAYER_ADJUST_' || RandomEventType || '_NO_UNIT_DAMAGE', 'RandomEventType', RandomEventType
FROM RandomEvents WHERE EffectOperatorType != 'SEA_LEVEL';
```

---

## 案例 C6：笛卡尔积 ×300 — 人口×区域产出

**来源**：Siqi_Leaders_0035

```sql
-- 建辅助表
CREATE TABLE Siqi_0035_DistrictYieldSupport (DistrictType TEXT, YieldType TEXT);
CREATE TABLE Siqi_0035_NumberSupport (i INTEGER);

-- 填充
INSERT INTO Siqi_0035_DistrictYieldSupport (DistrictType, YieldType) VALUES
('DISTRICT_CAMPUS', 'YIELD_SCIENCE'), ('DISTRICT_HOLY_SITE', 'YIELD_FAITH'), ...; -- 6行

INSERT INTO Siqi_0035_NumberSupport
WITH RECURSIVE Numbers(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM Numbers WHERE i<50)
SELECT i FROM Numbers;  -- 50行

-- 笛卡尔积 6×50=300 对
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId)
SELECT 'MODIFIER_SIQI0035_' || DistrictType || '_' || YieldType || '_ADJUST_' || i || 'POP_ATTACH',
       'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER',
       'SIQI0035_HAS_' || i || '_POP'
FROM Siqi_0035_DistrictYieldSupport, Siqi_0035_NumberSupport;
```

---

## 常用游戏表（可作为 SELECT FROM 源）

| 表 | 用途 |
|----|------|
| `Technologies` | 遍历所有科技 |
| `Civics` | 遍历所有市政 |
| `Districts` (WHERE RequiresPopulation=1) | 遍历专业化区域 |
| `Buildings` (WHERE IsWonder=0) | 遍历非奇观建筑 |
| `Yields` | 遍历 6 种产出 |
| `RandomEvents` | 遍历随机事件/灾害 |
| `Resources` | 遍历资源 |
| `Terrains` | 遍历地形 |
| `Features` | 遍历地貌 |
