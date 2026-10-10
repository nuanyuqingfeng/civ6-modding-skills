# 文明6 Mod开发 - ModifierArguments参数类型参考

> 📖 这是详细参考文档。快速查阅请查看 [SKILL.md](../SKILL.md)
>
> ⚠️ **本文档是「按参数名分类」的速查表，不是逐 Effect 的权威定义。**
> 要查**某个具体 EffectType / ModifierType 的参数签名与取值域**（含 `DatabaseKind`→`Types`
> 的权威取值全集、必填性、Min/Max、官方实际用过的值），用：
>
> ```bash
> python database/scripts/query_effect_args.py --effect EFFECT_ADJUST_PLOT_YIELD
> python database/scripts/query_effect_args.py --modifier MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE
> python database/scripts/query_effect_args.py --arg YieldType      # 反查：谁在用这个参数、能填什么
> ```
>
> 本文档下面的表可作为「参数名 → 大致用途」的第一眼参考，但**具体填值以工具输出为准**。

---

## 概述

本文档提供ModifierArguments表中所有参数的数据类型说明，帮助编写Mod时正确设置参数。

## 数据类型说明

| 数据类型 | 说明 | 使用场景 |
|----------|------|----------|
| **ARGTYPE_IDENTITY** | 标识符类型（字符串） | 绝大多数参数 |
| **ScaleByGameSpeed** | 随游戏速度缩放 | 数值类参数 |
| **LinearScaleFromDefaultHandicap** | 随难度线性缩放 | 数值类参数 |

> **注意**: 95%+ 的参数使用 `ARGTYPE_IDENTITY`，即使是数字值也用这个类型。

## 参数分类速查

### 1. Yield/产出相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `Amount` | ARGTYPE_IDENTITY | `"5"`, `"-1"`, `"100"` | 数值（正/负） |
| `YieldType` | ARGTYPE_IDENTITY | `YIELD_SCIENCE`, `YIELD_CULTURE` | 产出类型 |
| `Percent` | ARGTYPE_IDENTITY | `"50"`, `"100"` | 百分比 |
| `YieldChange` | ARGTYPE_IDENTITY | `"2"` | 产出变化量 |
| `BeliefYieldType` | ARGTYPE_IDENTITY | `YIELD_FAITH` | 信仰产出类型 |

**YieldType可选值**:
- `YIELD_FOOD` - 食物
- `YIELD_PRODUCTION` - 生产力
- `YIELD_GOLD` - 金币
- `YIELD_SCIENCE` - 科技值
- `YIELD_CULTURE` - 文化值
- `YIELD_FAITH` - 信仰值

### 2. Unit/单位相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `UnitType` | ARGTYPE_IDENTITY | `UNIT_WARRIOR`, `UNIT_ARCHER` | 单位类型 |
| `UnitPromotionClass` | ARGTYPE_IDENTITY | `PROMOTION_CLASS_MELEE` | 晋升类别 |
| `UnitDomain` | ARGTYPE_IDENTITY | `DOMAIN_LAND`, `DOMAIN_SEA` | 单位领域 |
| `PromotionClass` | ARGTYPE_IDENTITY | `PROMOTION_CLASS_RANGED` | 晋升类别 |
| `UnitPromotionClassType` | ARGTYPE_IDENTITY | - | 单位晋升类别 |
| `UnitClassType` | ARGTYPE_IDENTITY | - | 单位类别 |

**UnitDomain可选值**:
- `DOMAIN_LAND` - 陆地
- `DOMAIN_SEA` - 海上
- `DOMAIN_AIR` - 空中

### 3. Building/建筑相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `BuildingType` | ARGTYPE_IDENTITY | `BUILDING_MONUMENT` | 建筑类型 |
| `LocationBuildingType` | ARGTYPE_IDENTITY | - | 位置建筑类型 |
| `IsWonder` | ARGTYPE_IDENTITY | `true`, `false` | 是否为奇观 |
| `IsWorldWonder` | ARGTYPE_IDENTITY | `true`, `false` | 是否为世界奇观 |
| `WonderType` | ARGTYPE_IDENTITY | - | 奇观类型 |

### 4. District/区域相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `DistrictType` | ARGTYPE_IDENTITY | `DISTRICT_CAMPUS` | 区域类型 |
| `IsUniqueDistrict` | ARGTYPE_IDENTITY | `true`, `false` | 是否为特色区域 |
| `IsCityCenter` | ARGTYPE_IDENTITY | `true`, `false` | 是否为市中心 |

**DistrictType可选值**:
- `DISTRICT_CITY_CENTER` - 市中心
- `DISTRICT_CAMPUS` - 学院
- `DISTRICT_HOLY_SITE` - 圣地
- `DISTRICT_COMMERCIAL_HUB` - 商业中心
- `DISTRICT_INDUSTRIAL_ZONE` - 工业区
- `DISTRICT_ENCAMPMENT` - 军营
- `DISTRICT_HARBOR` - 港口
- `DISTRICT_AERODROME` - 机场
- `DISTRICT_NEIGHBORHOOD` - 社区
- `DISTRICT_SPACEPORT` - 航天中心
- `DISTRICT_ENTERTAINMENT_COMPLEX` - 娱乐中心
- `DISTRICT_AQUEDUCT` - 水渠
- `DISTRICT_BATH` - 浴场（罗马特色）
- `DISTRICT_ACROPOLIS` - 卫城（希腊特色）
- `DISTRICT_HANSA` - 汉萨同盟（德国特色）
- `DISTRICT_LAVRA` - 拉夫拉修道院（俄罗斯特色）

### 5. Civilization/Leader/文明领袖相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `CivilizationType` | ARGTYPE_IDENTITY | `CIVILIZATION_CHINA` | 文明类型 |
| `LeaderType` | ARGTYPE_IDENTITY | `LEADER_QIN` | 领袖类型 |
| `TraitType` | ARGTYPE_IDENTITY | `TRAIT_*` | 特性类型 |

### 6. Technology/Civic/科技市政相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `TechnologyType` | ARGTYPE_IDENTITY | `TECH_BRONZE_WORKING` | 科技类型 |
| `CivicType` | ARGTYPE_IDENTITY | `CIVIC_CODE_OF_LAWS` | 市政类型 |
| `EraType` | ARGTYPE_IDENTITY | `ERA_ANCIENT`, `ERA_CLASSICAL` | 时代类型 |
| `StartEraType` | ARGTYPE_IDENTITY | - | 起始时代 |
| `EndEraType` | ARGTYPE_IDENTITY | - | 结束时代 |
| `StartEra` | ARGTYPE_IDENTITY | - | 起始时代 |

**EraType可选值**:
- `ERA_ANCIENT` - 远古时代
- `ERA_CLASSICAL` - 古典时代
- `ERA_MEDIEVAL` - 中世纪
- `ERA_RENAISSANCE` - 文艺复兴
- `ERA_INDUSTRIAL` - 工业时代
- `ERA_MODERN` - 现代
- `ERA_ATOMIC` - 原子能时代
- `ERA_INFORMATION` - 信息时代

### 7. Resource/资源相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `ResourceType` | ARGTYPE_IDENTITY | `RESOURCE_IRON`, `RESOURCE_OIL` | 资源类型 |
| `ResourceClassType` | ARGTYPE_IDENTITY | - | 资源类别 |
| `ResourceAmount` | ARGTYPE_IDENTITY | - | 资源数量 |

### 8. Terrain/Feature/地形特征相关参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `TerrainType` | ARGTYPE_IDENTITY | `TERRAIN_GRASSLAND` | 地形类型 |
| `FeatureType` | ARGTYPE_IDENTITY | `FEATURE_FOREST` | 地貌特征 |
| `IsHills` | ARGTYPE_IDENTITY | `true`, `false` | 是否为丘陵 |
| `IsWater` | ARGTYPE_IDENTITY | `true`, `false` | 是否为水域 |

**TerrainType可选值**:
- `TERRAIN_GRASSLAND` - 草原
- `TERRAIN_PLAINS` - 平原
- `TERRAIN_DESERT` - 沙漠
- `TERRAIN_TUNDRA` - 冻土
- `TERRAIN_SNOW` - 雪原
- `TERRAIN_COAST` - 海岸
- `TERRAIN_OCEAN` - 海洋

### 9. 数值/计数参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `TurnsActive` | ARGTYPE_IDENTITY | `"10"` | 持续回合数 |
| `ReductionTurns` | ARGTYPE_IDENTITY | - | 减少回合数 |
| `IncrementTurns` | ARGTYPE_IDENTITY | - | 增加回合数 |
| `Range` | ARGTYPE_IDENTITY | - | 范围 |
| `Level` | ARGTYPE_IDENTITY | - | 等级 |
| `Radius` | ARGTYPE_IDENTITY | - | 半径 |
| `Count` | ARGTYPE_IDENTITY | - | 数量 |
| `Duration` | ARGTYPE_IDENTITY | - | 持续时间 |
| `Max` | ARGTYPE_IDENTITY | - | 最大值 |
| `Min` | ARGTYPE_IDENTITY | - | 最小值 |
| `Scalar` | ARGTYPE_IDENTITY | - | 标量/倍数 |

### 10. Tag/文本/描述参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `SimpleModifierDescription` | ARGTYPE_IDENTITY | `LOC_*` | 描述标签 |
| `StatementKey` | ARGTYPE_IDENTITY | `LOC_*` | 声明键 |
| `Description` | ARGTYPE_IDENTITY | `LOC_*` | 描述 |
| `Tag` | ARGTYPE_IDENTITY | - | 标签 |
| `Key` | ARGTYPE_IDENTITY | - | 键名 |
| `Text` | ARGTYPE_IDENTITY | - | 文本 |

### 11. 其他常用参数

| 参数名 | 数据类型 | 示例值 | 说明 |
|--------|----------|--------|------|
| `ModifierId` | ARGTYPE_IDENTITY | - | Modifier的ID |
| `AbilityType` | ARGTYPE_IDENTITY | `ABILITY_*` | 能力类型 |
| `GreatPersonClassType` | ARGTYPE_IDENTITY | `GREAT_PERSON_CLASS_*` | 伟人类别 |
| `GovernmentType` | ARGTYPE_IDENTITY | `GOVERNMENT_*` | 政体类型 |
| `ProjectType` | ARGTYPE_IDENTITY | `PROJECT_*` | 项目类型 |
| `ReligionType` | ARGTYPE_IDENTITY | `RELIGION_*` | 宗教类型 |
| `RouteType` | ARGTYPE_IDENTITY | `ROUTE_*` | 道路类型 |
| `ImprovementType` | ARGTYPE_IDENTITY | `IMPROVEMENT_*` | 改良设施类型 |
| `InitialValue` | ARGTYPE_IDENTITY | `"0"` | 初始值 |
| `IncrementValue` | ARGTYPE_IDENTITY | - | 增量值 |
| `HiddenAgenda` | ARGTYPE_IDENTITY | `true`, `false` | 是否为隐藏议程 |

## ModifierType参数模板

### 产出类Modifier示例

**MODIFIER_PLAYER_ADJUST_SCIENCE_PER_TURN**
```sql
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_SCIENCE_MOD', 'Amount', 'ARGTYPE_IDENTITY', '5');
```

**MODIFIER_PLAYER_CITIES_ADJUST_YIELD**
```sql
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_YIELD_MOD', 'YieldType', 'ARGTYPE_IDENTITY', 'YIELD_CULTURE');

INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_YIELD_MOD', 'Amount', 'ARGTYPE_IDENTITY', '2');
```

**MODIFIER_CITY_ADJUST_YIELD_PER_POPULATION**
```sql
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_POP_YIELD', 'YieldType', 'ARGTYPE_IDENTITY', 'YIELD_SCIENCE');

INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_POP_YIELD', 'Amount', 'ARGTYPE_IDENTITY', '1');
```

### 单位类Modifier示例

**MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH**
```sql
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_COMBAT_MOD', 'Amount', 'ARGTYPE_IDENTITY', '5');
```

### 建筑类Modifier示例

**MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION**
```sql
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_BUILDING_PROD', 'BuildingType', 'ARGTYPE_IDENTITY', 'BUILDING_MONUMENT');

INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_BUILDING_PROD', 'Amount', 'ARGTYPE_IDENTITY', '25');
```

### 区域类Modifier示例

**MODIFIER_PLAYER_DISTRICTS_ADJUST_GREAT_PERSON_POINTS**
```sql
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_GPP_MOD', 'DistrictType', 'ARGTYPE_IDENTITY', 'DISTRICT_CAMPUS');

INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_GPP_MOD', 'GreatPersonClassType', 'ARGTYPE_IDENTITY', 'GREAT_PERSON_CLASS_SCIENTIST');

INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_GPP_MOD', 'Amount', 'ARGTYPE_IDENTITY', '2');
```

## 常用ModifierType参数速查

| ModifierType | 必需参数 | 可选参数 |
|--------------|----------|----------|
| `MODIFIER_PLAYER_ADJUST_*_PER_TURN` | `Amount` | - |
| `MODIFIER_PLAYER_CITIES_ADJUST_YIELD` | `YieldType`, `Amount` | - |
| `MODIFIER_CITY_ADJUST_YIELD_PER_POPULATION` | `YieldType`, `Amount` | - |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` | `Amount` | `Key`, `Max` |
| `MODIFIER_UNIT_ADJUST_BASE_COMBAT_STRENGTH` | `Amount` | `Type`（见下方专节） |
| `MODIFIER_UNIT_ADJUST_MOVEMENT` | `Amount` | - |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION` | `BuildingType`, `Amount` | - |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_GREAT_PERSON_POINTS` | `DistrictType`, `GreatPersonClassType`, `Amount` | - |
| `MODIFIER_CITY_ADJUST_AMENITIES` | `Amount` | - |
| `MODIFIER_CITY_ADJUST_HOUSING` | `Amount` | - |
| `MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` | `Amount` | `UnitType` |

## `MODIFIER_UNIT_ADJUST_BASE_COMBAT_STRENGTH` 的 `Type` 参数

> 本节依据引擎层逆向结果记录（非 `Types` 表可查的取值域，`ModifierArguments` 也无独立枚举表）。

`Type` 用于限定「基础战斗力」加成生效的战斗场景，**可选项**：

| `Type` 取值 | 生效场景 |
|---|---|
| `MELEE` | 近战 |
| `ANTIAIR` | 对空 |
| `RANGED` | 远程 |
| `BOMBARD` | 攻城 / 轰击 |
| *（留空 / 不写该参数）* | **所有场景**，即无差别加基础战斗力 |

```sql
-- 只在近战时生效 +10
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_MOD', 'Type', 'ARGTYPE_IDENTITY', 'MELEE');
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_MOD', 'Amount', 'ARGTYPE_IDENTITY', '10');

-- 所有场景 +10（留空 Type）
INSERT INTO ModifierArguments (ModifierId, Name, Type, Value)
VALUES ('MY_MOD', 'Amount', 'ARGTYPE_IDENTITY', '10');
```

> 注意：不要与 `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` 混淆——后者的 `Type` 无此语义，
> 它的 `Key` / `Max` 是「从单位 Property 读取加成」用的。

## 数据来源

- **数据库**: `DebugGameplay.sqlite`
- **表**: `ModifierArguments` / `GameEffectArguments` / `DynamicModifiers` / `Types`
- **总记录数**: 约10,000+条
- **不同参数名**: 328个（实测）
- **不同 ModifierType**: 995种（实测，`DynamicModifiers`）
- **逐 Effect 取值域**: 用 `database/scripts/query_effect_args.py` 实时查（勿把本文档当定义源）

---

*文档版本: v1.1*
*数据提取时间: 2026-04-15；2026-09-18 补注「本文是分类速查、非权威定义源」并指向 `query_effect_args.py`；2026-09-20 补 `MODIFIER_UNIT_ADJUST_BASE_COMBAT_STRENGTH` 的 `Type` 取值域（引擎逆向）*
