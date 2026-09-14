# Civ6 Modifier / Effect / Requirement 速查表

> **规则: 写 SQL Modifier 前先扫此表确认类型存在。不在表中的 → `SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'` (DebugGameplay.sqlite)**
> 覆盖日常模组开发 95% 场景。

## 常用 Modifier 类型

### Player 级（影响所有城市/单位）

| ModifierType | 用途 |
|-------------|------|
| `MODIFIER_PLAYER_ADJUST_PROPERTY` | 设玩家 Property |
| `MODIFIER_PLAYER_ADJUST_PLOT_YIELD` | 玩家地块产出 |
| `MODIFIER_PLAYER_ADJUST_YIELD_ADJACENCY` | 产出相邻加成 |
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION` | 城市单位生产力（Amount=固定值, UnitType=筛选类型·可选） |
| `MODIFIER_PLAYER_CITIES_ENABLE_BUILDING_FAITH_PURCHASE` | 建筑信仰购买 |
| `MODIFIER_PLAYER_CITIES_ENABLE_UNIT_FAITH_PURCHASE` | 单位信仰购买 |
| `MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` | 单位战斗力 |
| `MODIFIER_PLAYER_UNITS_ADJUST_MOVEMENT` | 单位移动力 |
| `MODIFIER_PLAYER_UNITS_GRANT_ABILITY` | 赋予 Ability |
| **`MODIFIER_PLAYER_UNITS_ADJUST_PROPERTY`** | **设单位 Property** |
| `MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER` | 给单位附加子修饰器 |
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD` | 商路产出 |
| `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER` | 城市附加修饰器 |
| `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER` | 所有玩家附加修饰器 |
| `MODIFIER_ALL_CITIES_ATTACH_MODIFIER` | 所有城市附加修饰器 |
| `MODIFIER_ALL_UNITS_ATTACH_MODIFIER` | 所有单位附加修饰器 |

### Unit 级（影响单个单位）

| ModifierType | 用途 |
|-------------|------|
| **`MODIFIER_UNIT_ADJUST_PROPERTY`** | 设单单位 Property，参数：`Key` + `Amount` |
| **`MODIFIER_PLAYER_ADJUST_PROPERTY`** | 设玩家级 Property，参数：`Key` + `Amount` |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` | 单位战斗力 |
| `MODIFIER_UNIT_ADJUST_MOVEMENT` | 单位移动力 |
| `MODIFIER_UNIT_ADJUST_SIGHT` | 单位视野 |
| `MODIFIER_UNIT_ADJUST_NUM_ATTACKS` | 攻击次数 |
| `MODIFIER_UNIT_ADJUST_HEAL_PER_TURN` | 每回合回复 |
| `MODIFIER_UNIT_ADJUST_IGNORE_TERRAIN_COST` | 忽略地形消耗 |
| `MODIFIER_UNIT_ADJUST_BUILDER_CHARGES` | 建造者次数 |
| `MODIFIER_UNIT_ADJUST_GRANT_EXPERIENCE` | 给予经验 |

### City / Building 级

| ModifierType | 用途 |
|-------------|------|
| `MODIFIER_SINGLE_CITY_ADJUST_AMENITIES` | 单城宜居度 |
| `MODIFIER_SINGLE_CITY_ADJUST_HOUSING` | 单城住房 |
| `MODIFIER_SINGLE_CITY_ADJUST_IDENTITY_PER_TURN` | 单城忠诚度 |
| `MODIFIER_SINGLE_CITY_ADJUST_YIELD_CHANGE` | 单城产出 |
| `MODIFIER_SINGLE_CITY_TRAIN_UNIT_TAG` | 允许训练标签单位 |
| `MODIFIER_SINGLE_CITY_ADJUST_UNIT_PRODUCTION` | 单城单位生产力 |
| `MODIFIER_SINGLE_CITY_GRANT_ABILITY_FOR_TRAINED_UNITS` | 训练的单位获得 Ability |
| `MODIFIER_SINGLE_CITY_ADJUST_UNIT_PURCHASE_COST` | 单城单位购买花费 |
| `MODIFIER_SINGLE_CITY_ADJUST_ALL_UNITS_PURCHASE_COST` | 单城所有单位购买花费 |
| `MODIFIER_CITY_ENABLE_UNIT_FAITH_PURCHASE` | 城市单位信仰购买 |
| `MODIFIER_CITY_TRAINED_UNITS_ATTACH_MODIFIER` | 训练单位附加修饰器 |
| `MODIFIER_CITY_TRAINED_UNITS_ADJUST_MOVEMENT` | 训练单位移动力 |
| `MODIFIER_BUILDING_YIELD_CHANGE` | 建筑产出 |
| `MODIFIER_CITY_PLOT_YIELDS_ADJUST_PLOT_YIELD` | 城市地块产出 |

### Plot / District 级

| ModifierType | 用途 |
|-------------|------|
| `MODIFIER_PLAYER_CITIES_ADJUST_WATER_HOUSING` | 水域住房 |
| `MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION` | 区域生产力 |
| `MODIFIER_CITY_DISTRICTS_ADJUST_DISTRICT_AMENITY` | 区域宜居度 |
| `MODIFIER_CITY_DISTRICTS_ADJUST_DISTRICT_HOUSING` | 区域住房 |
| `MODIFIER_SINGLE_PLOT_ADJUST_PROPERTY` | 地块 Property |

### Governor 级

| ModifierType | 用途 |
|-------------|------|
| `MODIFIER_GOVERNOR_ADJUST_CITY_AMENITY` | 总督城市宜居度 |
| `MODIFIER_GOVERNOR_ADJUST_CITY_CULTURE` | 总督城市文化 |
| `MODIFIER_GOVERNOR_ADJUST_CITY_GROWTH` | 总督城市增长 |
| `MODIFIER_GOVERNOR_ADJUST_IDENTITY_PRESSURE` | 总督忠诚压力 |

## 常用 Requirement 类型

| RequirementType | 参数 | 用途 |
|----------------|------|------|
| `REQUIREMENT_PLOT_TERRAIN_TYPE_MATCHES` | TerrainType | 地块地形匹配 |
| `REQUIREMENT_PLOT_FEATURE_TYPE_MATCHES` | FeatureType | 地块地貌匹配 |
| `REQUIREMENT_PLOT_IS_ADJACENT_TO_OWNER` | MinDistance, MaxDistance | 地块相邻所有者 |
| `REQUIREMENT_UNIT_TYPE_MATCHES` | UnitType | 单位类型匹配 |
| `REQUIREMENT_UNIT_TAG_MATCHES` | Tag | 单位标签匹配 |
| `REQUIREMENT_UNIT_DOMAIN_MATCHES` | Domain | 单位领域匹配 (DOMAIN_LAND/SEA/AIR) |
| `REQUIREMENT_UNIT_PROMOTION_MATCHES` | UnitPromotion | 单位晋升匹配 |
| `REQUIREMENT_PLAYER_TYPE_MATCHES` | CivilizationType, LeaderType | 玩家文明/领袖匹配 |
| `REQUIREMENT_PLAYER_ERA_AT_LEAST` | EraType | 玩家时代 ≥ |
| `REQUIREMENT_PLAYER_ERA_AT_MOST` | EraType | 玩家时代 ≤ |
| `REQUIREMENT_CITY_HAS_BUILDING` | BuildingType | 城市有建筑 |
| `REQUIREMENT_CITY_HAS_DISTRICT` | DistrictType | 城市有区域 |
| `REQUIREMENT_CITY_FOLLOWS_RELIGION` | ReligionType | 城市信仰宗教 |
| `REQUIREMENT_PLOT_HAS_ANY_DISTRICT` | MustBeFunctioning | 地块有任意区域 |
| `REQUIREMENT_PLOT_IMPROVEMENT_TYPE_MATCHES` | ImprovementType | 地块改良设施匹配 |
| `REQUIREMENT_PLOT_PROPERTY_MATCHES` | PropertyName, PropertyMinimum | 地块 Property 值 |
| `REQUIREMENT_PLOT_RESOURCE_TYPE_MATCHES` | ResourceType | 地块资源匹配 |
| `REQUIREMENT_PLOT_IS_COASTAL_LAND` | — | 沿海陆地 |
| `REQUIREMENT_PLOT_IS_FRESH_WATER` | — | 淡水 |
| `REQUIREMENT_GAME_ERA_AT_LEAST` | MinGameEra | 游戏时代 ≥ |
| `REQUIREMENT_TEAM_HAS_MOST_PROMOTION_CLASS` | PromotionClass | 队伍最多晋升类型 |
| `REQUIREMENT_REQUIREMENTSET_IS_MET` | RequirementSetId | 子条件组合满足 |
| `REQUIREMENT_COLLECTION_COUNT_ATLEAST` | CollectionType, Count | 集合计数 ≥ |
| `REQUIREMENT_COLLECTION_COUNT_EQUALS` | CollectionType, Count | 集合计数 = |

## 常用 Collection 类型

| CollectionType | 作用域 |
|---------------|--------|
| `COLLECTION_OWNER` | 所有者 |
| `COLLECTION_PLAYER_CITIES` | 玩家城市 |
| `COLLECTION_PLAYER_UNITS` | 玩家单位 |
| `COLLECTION_ALL_PLAYERS` | 所有玩家 |
| `COLLECTION_ALL_CITIES` | 所有城市 |
| `COLLECTION_ALL_UNITS` | 所有单位 |
| `COLLECTION_MAJOR_PLAYERS` | 主要文明 |
| `COLLECTION_PLAYER_CAPITAL_CITY` | 首都 |
| `COLLECTION_PLAYER_DISTRICTS` | 玩家区域 |
| `COLLECTION_PLAYER_IMPROVEMENTS` | 玩家改良设施 |
| `COLLECTION_CITY_OWNER` | 城市所有者 |
| `COLLECTION_CITY_PLOT_YIELDS` | 城市地块产出 |

## 自定义 DynamicModifier

自注册 ModifierType 有两大目的：

| 目的 | 说明 | 场景 |
|------|------|------|
| **改作用域** | 相同 Effect 换 CollectionType | 如 `UNIT`→`OWNER`、`CITY`→`CITIES` |
| **消除 DLC 依赖** | 引擎 ModifierType 定义在 Mode/Scenario DLC 中，直接引用可能在缺失 DLC/模式时静默失效 | 查 `source_index.sqlite` 的 `dlc_dependency`（或 JSON 清单）标注为 1 时**必须自注册** |

### 注册模板

```sql
INSERT OR REPLACE INTO Types (Type, Kind) VALUES
('MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION_MYMOD', 'KIND_MODIFIER');

INSERT OR REPLACE INTO DynamicModifiers (ModifierType, EffectType, CollectionType) VALUES
('MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION_MYMOD', 'EFFECT_ADJUST_UNIT_PRODUCTION', 'COLLECTION_PLAYER_CITIES');
```

> ⚠️ 官方 `DynamicModifiers` **只有 3 列**（`ModifierType` / `CollectionType` / `EffectType`）。`IsDlcDependency` 只是 skill 元数据（`source_index.sqlite` 的 `dlc_dependency` 表）里的标注，**不是游戏列**——**禁止写进 mod SQL**，否则游戏加载会报 `table DynamicModifiers has no column named IsDlcDependency`。

用相同 EffectType + CollectionType 但不同 ModifierType 名 = 互不干扰的多份独立实例。

### 常用 EffectType 搭配

| EffectType | CollectionType 建议 | 参数 |
|-----------|---------------------|------|
| `EFFECT_ADJUST_UNIT_PRODUCTION` | `COLLECTION_PLAYER_CITIES` | Amount, UnitType |
| `EFFECT_ADJUST_ALL_UNIT_PRODUCTION_MODIFIER` | `COLLECTION_PLAYER_CITIES` | Amount（百分比） |
| `EFFECT_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_PLAYER_CITIES` | Amount, YieldType |

> **查询提示（DLC/模式依赖）：** 官方表只有 3 列；DLC 标注在元数据库 `database/source_index.sqlite` 的 `dlc_dependency` 表里：
> `SELECT * FROM dlc_dependency WHERE ModifierType LIKE '%keyword%';`  
> 其中 `IsDlcDependency=1` 表示该 ModifierType 定义在 Mode/Scenario DLC 中，缺失对应 DLC/模式时会静默失效，应自行注册同 Effect+Collection 的新类型，不要直接引用。

## RequirementSet 类型

| Type | 逻辑 |
|------|------|
| `REQUIREMENTSET_TEST_ALL` | 所有条件 AND |
| `REQUIREMENTSET_TEST_ANY` | 任一条件 OR |
| `REQUIREMENT_REQUIREMENTSET_IS_MET` | 子 ReqSet 满足 |

## 关键绑定表

| 表 | 用途 |
|----|------|
| `TraitModifiers` | 特质 → 修饰器 |
| `BuildingModifiers` | 建筑 → 修饰器 |
| `DistrictModifiers` | 区域 → 修饰器 |
| `UnitAbilityModifiers` | Ability → 修饰器（Permanent=1 的 Ability 自动生效） |
| `BeliefModifiers` | 信条 → 修饰器 |
| `GovernorModifiers` | 总督 → 修饰器 |
| `PolicyModifiers` | 政策 → 修饰器 |
| `ImprovementModifiers` | 改良设施 → 修饰器 |
| `ProjectCompletionModifiers` | 项目完成 → 修饰器 |

> **💡 `TRAIT_LEADER_MAJOR_CIV`** 是引擎内置的"主流文明"默认特质。绑定到 `TraitModifiers` + `TRAIT_LEADER_MAJOR_CIV` = 所有主流文明玩家生效，无需为每个文明注册特质。用户提到"主流文明"时优先用它。
