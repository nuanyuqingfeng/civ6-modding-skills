# Civ6 Database — 带示例值的注解表结构

> 数据来源：`DebugGameplay.sqlite` 实时查询（列名、类型、NOT NULL、默认值、示例行、枚举值）。
>
> **不常见的表** → 用 `sqlite3 DebugGameplay.sqlite "PRAGMA table_info(TableName)"` 实时查询列结构，
> 再用 `SELECT * FROM TableName LIMIT 1` 看真实示例行。

### PRAGMA table_info 速查模板

```powershell
# 必须手填的列（NOT NULL 且无默认值）
sqlite3 $db "SELECT name, type FROM pragma_table_info('TableName') WHERE [notnull]=1 AND dflt_value IS NULL;"

# 已有默认值的列
sqlite3 $db "SELECT name, dflt_value FROM pragma_table_info('TableName') WHERE [notnull]=1 AND dflt_value IS NOT NULL;"
```

## 目录

| 表 | 行号 | 说明 |
|---|------|------|
| **P0 — 必填核心** | | |
| Types | 42 | Type 全局注册（Kind 必填） |
| Units | 55 | 67 列 — 单位定义（战斗/移动/成本/晋升） |
| Buildings | 109 | 46 列 — 建筑定义（科技/区域/成本/奇观） |
| Districts | 155 | 40 列 — 区域定义（位置/成本/掠夺/域） |
| Improvements | 189 | 49 列 — 改良定义（科技/生产力/住房） |
| Resources | 212 | 15 列 — 资源定义（类别/频率/时代） |
| Projects | 230 | 21 列 — 项目定义（成本/区域/太空竞赛） |
| **P1 — 核心逻辑** | | |
| Modifiers | 252 | 10 列 — Modifier 定义（Owner/Subject 条件） |
| ModifierArguments | 267 | 6 列 — Modifier 参数（Name/Value） |
| Requirements | 281 | 9 列 — Requirement 定义（Inverse/Persistent） |
| RequirementArguments | 295 | 6 列 — Requirement 参数（Name/Value） |
| RequirementSets | 309 | 2 列 — 条件集定义（ALL/ANY） |
| RequirementSetRequirements | 316 | 2 列 — 条件集-条件关联 |
| DynamicModifiers | 325 | 3 列 — 自定义 ModifierType（Collection/Effect） |
| ModifierStrings | 333 | 3 列 — Modifier 文本 |
| **P2 — 文明/领袖/政策** | | |
| Civilizations | 345 | 7 列 — 文明定义（等级/民族） |
| Leaders | 357 | 8 列 — 领袖定义（继承/性别） |
| Traits | 366 | 4 列 — 特性定义 |
| Policies | 375 | 8 列 — 政策定义（槽位/前置） |
| UnitAbilities | 386 | 6 列 — 单位能力定义 |
| UnitPromotions | 397 | 7 列 — 单位晋升定义（等级/树列） |
| **P3 — 关联桥表** | 410 | 2-3 列桥表，无需详细标注 |

---

## P0 — 必填核心（Type 表）

### Types

`Type` 全局注册表，新增任何 `Type` 必须先在此注册。

| 列名 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| Type | TEXT | **YES** | — | 唯一标识，全局唯一 |
| Kind | TEXT | **YES** | — | 类型分类 |

值：`KIND_TRAIT`, `KIND_UNIT`, `KIND_BUILDING`, `KIND_DISTRICT`, `KIND_IMPROVEMENT`, `KIND_RESOURCE`, `KIND_PROJECT`, `KIND_POLICY`, `KIND_ABILITY`, `KIND_MODIFIER`, `KIND_REQUIREMENT`, `KIND_PROMOTION`, `KIND_PROMOTION_CLASS`, `KIND_GOVERNOR_PROMOTION`, `KIND_DIPLOMATIC_ACTION` ...

---

### Units

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| UnitType | TEXT | — | — | `UNIT_SETTLER` |
| Name | TEXT | **YES** | — | `LOC_UNIT_SETTLER_NAME` |
| BaseSightRange | INTEGER | **YES** | — | `3` |
| BaseMoves | INTEGER | **YES** | — | `2` |
| Combat | INTEGER | — | `0` | `0`（平民），`20`（勇士）|
| RangedCombat | INTEGER | — | `0` | `15`（弓箭手）|
| Range | INTEGER | — | `0` | `1`（近战），`2`（远程）|
| Bombard | INTEGER | — | `0` | 攻城远程攻击力 |
| Domain | TEXT | **YES** | — | `DOMAIN_LAND` / `DOMAIN_SEA` / `DOMAIN_AIR` |
| FormationClass | TEXT | **YES** | — | `FORMATION_CLASS_CIVILIAN` / `FORMATION_CLASS_LAND_COMBAT` / `FORMATION_CLASS_NAVAL` / `FORMATION_CLASS_SUPPORT` / `FORMATION_CLASS_AIR` |
| Cost | INTEGER | **YES** | — | `80`（移民），`40`（侦察兵）|
| PopulationCost | INTEGER | — | — | `1`（移民创建城市消耗人口）|
| FoundCity | BOOLEAN | — | `0` | `1`（移民）|
| FoundReligion | BOOLEAN | — | `0` | `1`（先知）|
| MakeTradeRoute | BOOLEAN | — | `0` | `1`（商人）|
| EvangelizeBelief | BOOLEAN | — | `0` | `1`（使徒）|
| LaunchInquisition | BOOLEAN | — | `0` | `1`（审判官）|
| BuildCharges | INTEGER | — | `0` | `3`（建造者）|
| ReligiousStrength | INTEGER | — | `0` | 宗教战力 |
| SpreadCharges | INTEGER | — | `0` | 传教次数 |
| ExtractsArtifacts | BOOLEAN | — | `0` | `1`（考古学家）|
| Description | TEXT | — | — | `LOC_UNIT_SETTLER_DESCRIPTION` |
| CanCapture | BOOLEAN | — | `1` | `0`（平民不可捕获）|
| TraitType | TEXT | — | — | `TRAIT_CIVILIZATION_UNIT_AMERICAN_P51` |
| CostProgressionModel | TEXT | — | `NO_COST_PROGRESSION` | `COST_PROGRESSION_PREVIOUS_COPIES` / `COST_PROGRESSION_GAME_PROGRESS` |
| CostProgressionParam1 | INTEGER | — | `0` | 成本递增参数 |
| PromotionClass | TEXT | — | — | `PROMOTION_CLASS_MELEE` / `PROMOTION_CLASS_RECON` / `PROMOTION_CLASS_RANGED` ... |
| InitialLevel | INTEGER | — | `1` | 初始等级 |
| NumRandomChoices | INTEGER | — | `0` | `1` 允许随机选晋升 |
| PrereqTech | TEXT | — | — | `TECH_MINING` |
| PrereqCivic | TEXT | — | — | `CIVIC_CODE_OF_LAWS` |
| PrereqDistrict | TEXT | — | — | `DISTRICT_ENCAMPMENT` |
| StrategicResource | TEXT | — | — | `RESOURCE_HORSES` / `RESOURCE_IRON` / `RESOURCE_NITER` |
| PurchaseYield | TEXT | — | — | `YIELD_GOLD` / `YIELD_FAITH` |
| MustPurchase | BOOLEAN | — | `0` | `1`（仅能购买不能训练）|
| Maintenance | INTEGER | — | `0` | 每回合金币维护费 |
| Stackable | BOOLEAN | — | `0` | `1`（传教士可堆叠）|
| ZoneOfControl | BOOLEAN | — | `0` | 是否拥有 ZOC |
| AntiAirCombat | INTEGER | — | `0` | 对空战力 |
| Spy | BOOLEAN | — | `0` | `1`（间谍）|
| PseudoYieldType | TEXT | — | — | `PSEUDOYIELD_UNIT_SETTLER` / `PSEUDOYIELD_UNIT_TRADE` / `PSEUDOYIELD_UNIT_RELIGIOUS` / `PSEUDOYIELD_UNIT_NAVAL_COMBAT` / `PSEUDOYIELD_UNIT_AIR_COMBAT` ... |
| ObsoleteTech | TEXT | — | — | 科技过期后无法训练 |
| ObsoleteCivic | TEXT | — | — | 市政过期后无法训练 |
| AdvisorType | TEXT | — | — | `ADVISOR_GENERIC` / `ADVISOR_CONQUEST` ... |

**完整 PromotionClass 值：**
`PROMOTION_CLASS_APOSTLE`, `PROMOTION_CLASS_INQUISITOR`, `PROMOTION_CLASS_MONK`, `PROMOTION_CLASS_SPY`, `PROMOTION_CLASS_RECON`, `PROMOTION_CLASS_MELEE`, `PROMOTION_CLASS_RANGED`, `PROMOTION_CLASS_LIGHT_CAVALRY`, `PROMOTION_CLASS_HEAVY_CAVALRY`, `PROMOTION_CLASS_NAVAL_MELEE`, `PROMOTION_CLASS_ANTI_CAVALRY`, `PROMOTION_CLASS_SUPPORT`, `PROMOTION_CLASS_SIEGE`, `PROMOTION_CLASS_NAVAL_RANGED`, `PROMOTION_CLASS_NAVAL_RAIDER`, `PROMOTION_CLASS_AIR_FIGHTER`, `PROMOTION_CLASS_AIR_BOMBER`, `PROMOTION_CLASS_NAVAL_CARRIER`, `PROMOTION_CLASS_GIANT_DEATH_ROBOT`, `PROMOTION_CLASS_ROCK_BAND`, `PROMOTION_CLASS_NIHANG`

---

### Buildings

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| BuildingType | TEXT | — | — | `BUILDING_MONUMENT` |
| Name | TEXT | **YES** | — | `LOC_BUILDING_MONUMENT_NAME` |
| PrereqTech | TEXT | — | — | `TECH_WRITING` |
| PrereqCivic | TEXT | — | — | `CIVIC_DRAMA_POETRY` |
| Cost | INTEGER | **YES** | — | `60`（纪念碑），`290`（大学）|
| MaxPlayerInstances | INTEGER | — | `-1` | `-1`（不限），`1`（奇观唯一）|
| MaxWorldInstances | INTEGER | — | `-1` | `1`（世界奇观）|
| Capital | BOOLEAN | — | `0` | `1`（宫殿）|
| PrereqDistrict | TEXT | — | — | `DISTRICT_CITY_CENTER` / `DISTRICT_CAMPUS` |
| AdjacentDistrict | TEXT | — | — | 必须相邻的区（较少用）|
| Description | TEXT | — | — | `LOC_BUILDING_MONUMENT_DESCRIPTION` |
| RequiresPlacement | BOOLEAN | — | `0` | 需要放置？ |
| RequiresRiver | BOOLEAN | — | `0` | 需要河流？ |
| OuterDefenseHitPoints | INTEGER | — | — | 城墙血量 |
| Housing | INTEGER | — | `0` | 住房 |
| Entertainment | INTEGER | — | `0` | 娱乐 |
| AdjacentResource | TEXT | — | — | 需要相邻资源 |
| Coast | BOOLEAN | — | — | 是否需要海岸 |
| EnabledByReligion | BOOLEAN | — | `0` | 是否被宗教启用 |
| AllowsHolyCity | BOOLEAN | — | `0` | `1`（圣地允许圣城）|
| PurchaseYield | TEXT | — | `YIELD_GOLD` | 购买类型 |
| MustPurchase | BOOLEAN | — | `0` | 仅能购买 |
| Maintenance | INTEGER | — | `0` | 每回合维护费 |
| IsWonder | BOOLEAN | — | `0` | `1`（奇观）|
| TraitType | TEXT | — | — | 文明专属建筑 trait |
| CitizenSlots | INTEGER | — | — | 公民槽位 |
| MustBeLake | BOOLEAN | — | `0` | 必须湖泊 |
| MustNotBeLake | BOOLEAN | — | `0` | 不能湖泊 |
| RegionalRange | INTEGER | — | `0` | 区域范围（`6`=区域效应）|
| AdjacentToMountain | BOOLEAN | — | `0` | 需要邻山 |
| ObsoleteEra | TEXT | — | `NO_ERA` | 过时时 |
| OuterDefenseStrength | INTEGER | — | `0` | 城墙防御力 |
| GrantFortification | INTEGER | — | `0` | 驻军加成 |
| DefenseModifier | INTEGER | — | `0` | 防御修正 |
| InternalOnly | BOOLEAN | — | `0` | 仅内部建造 |
| AdvisorType | TEXT | — | — | `ADVISOR_*` |
| AdjacentImprovement | TEXT | — | — | 需要相邻改良 |
| AdjacentCapital | BOOLEAN | — | `0` | 需要邻首都 |
| GovernmentTierRequirement | TEXT | — | — | `Tier1` / `Tier2` / `Tier3` |

---

### Districts

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| DistrictType | TEXT | — | — | `DISTRICT_CITY_CENTER` |
| Name | TEXT | **YES** | — | `LOC_DISTRICT_*_NAME` |
| PrereqTech | TEXT | — | — | `TECH_CURRENCY`（商业）|
| PrereqCivic | TEXT | — | — | `CIVIC_DRAMA_POETRY`（剧院）|
| Coast | BOOLEAN | — | `0` | 需要海岸（港口）|
| Cost | INTEGER | — | `0` | 基础锤成本 |
| RequiresPlacement | BOOLEAN | **YES** | — | `1`（需要选地块）|
| RequiresPopulation | BOOLEAN | — | `1` | 需要人口 |
| NoAdjacentCity | BOOLEAN | **YES** | — | 不可邻市中心 |
| CityCenter | BOOLEAN | — | `0` | `1`（市中心）|
| Aqueduct | BOOLEAN | **YES** | — | `1`（水渠）|
| InternalOnly | BOOLEAN | **YES** | — | 仅能建在自己领土 |
| HitPoints | INTEGER | — | `0` | `200`（市中心有血量）|
| CaptureRemovesBuildings | BOOLEAN | **YES** | — | 被占领后建筑是否保留 |
| CaptureRemovesCityDefenses | BOOLEAN | **YES** | — | 被占领后城防是否移除 |
| PlunderType | TEXT | **YES** | — | `NO_PLUNDER` / `PLUNDER_GOLD` / `PLUNDER_FAITH` / `PLUNDER_SCIENCE` / `PLUNDER_CULTURE` / `PLUNDER_HEAL` |
| PlunderAmount | INTEGER | — | `0` | 掠夺量 |
| MilitaryDomain | TEXT | **YES** | — | `NO_DOMAIN` / `DOMAIN_LAND` / `DOMAIN_SEA` / `DOMAIN_AIR` |
| CostProgressionModel | TEXT | — | `NO_COST_PROGRESSION` | `COST_PROGRESSION_NUM_UNDER_AVG_PLUS_TECH` / `COST_PROGRESSION_GAME_PROGRESS` |
| CostProgressionParam1 | INTEGER | — | `0` | 成本递增参数 |
| TraitType | TEXT | — | — | 文明专属区 TraitType |
| Appeal | INTEGER | — | `0` | 魅力值 |
| Housing | INTEGER | — | `0` | 住房 |
| Entertainment | INTEGER | — | `0` | 娱乐 |
| OnePerCity | BOOLEAN | — | `1` | 每城限一个 |
| CitizenSlots | INTEGER | — | — | 公民槽位 |
| AdvisorType | TEXT | — | — | `ADVISOR_CULTURE` 等 |

---

### Improvements

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ImprovementType | TEXT | — | — | `IMPROVEMENT_FARM` |
| Name | TEXT | **YES** | — | `LOC_IMPROVEMENT_FARM_NAME` |
| PrereqTech | TEXT | — | — | `TECH_MINING` / `TECH_IRRIGATION` ... |
| PrereqCivic | TEXT | — | — | `CIVIC_CRAFTSMANSHIP` ... |
| Buildable | BOOLEAN | — | `0` | 建造者可否建造 |
| PlunderType | TEXT | **YES** | — | `NO_PLUNDER` / `PLUNDER_HEAL` / `PLUNDER_GOLD` / `PLUNDER_FAITH` |
| Icon | TEXT | **YES** | — | `ICON_IMPROVEMENT_FARM` |
| TraitType | TEXT | — | — | 专属文明改良 |
| Housing | INTEGER | — | `0` | 住房 |
| TilesRequired | INTEGER | — | `1` | 占据格数 |
| SameAdjacentValid | BOOLEAN | — | `1` | 同类相邻是否有效 |
| RequiresRiver | INTEGER | — | `0` | 需要河流 |
| Domain | TEXT | — | `DOMAIN_LAND` | — |
| Workable | BOOLEAN | — | `1` | 市民可否工作 |
| Removable | BOOLEAN | — | `1` | 可否移除 |
| Capturable | BOOLEAN | — | `1` | 可否被占领 |

---

### Resources

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ResourceType | TEXT | — | — | `RESOURCE_BANANAS` |
| Name | TEXT | **YES** | — | `LOC_RESOURCE_BANANAS_NAME` |
| ResourceClassType | TEXT | **YES** | — | `RESOURCECLASS_BONUS` / `RESOURCECLASS_LUXURY` / `RESOURCECLASS_STRATEGIC` / `RESOURCECLASS_ARTIFACT` |
| Happiness | INTEGER | — | `0` | 奢侈品快乐度 |
| Frequency | INTEGER | — | `0` | 生成频率 |
| Clumped | BOOLEAN | — | `0` | 是否成片生成 |
| PrereqTech | TEXT | — | — | 揭露科技 |
| PrereqCivic | TEXT | — | — | 揭露市政 |
| PeakEra | TEXT | — | `NO_ERA` | 峰值时代 |
| RevealedEra | INTEGER | — | `1` | 揭露时代（1=远古）|
| LakeEligible | BOOLEAN | — | `1` | 可否产于湖中 |

---

### Projects

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ProjectType | TEXT | — | — | `PROJECT_REPAIR_OUTER_DEFENSES` |
| Name | TEXT | **YES** | — | `LOC_*_NAME` |
| ShortName | TEXT | **YES** | — | `LOC_*_SHORT_NAME` |
| Cost | INTEGER | **YES** | — | `0` 或具体数值 |
| CostProgressionModel | TEXT | — | `NO_PROGRESSION_MODEL` | `COST_PROGRESSION_GAME_PROGRESS` |
| PrereqTech | TEXT | — | — | `TECH_ROCKETRY` |
| PrereqCivic | TEXT | — | — | — |
| PrereqDistrict | TEXT | — | — | `DISTRICT_SPACEPORT` |
| PrereqResource | TEXT | — | — | 需要资源 |
| MaxPlayerInstances | INTEGER | — | — | 玩家上限 |
| AdvisorType | TEXT | — | — | `ADVISOR_GENERIC` 等 |
| SpaceRace | BOOLEAN | — | `0` | 太空竞赛项目 |
| WMD | BOOLEAN | — | `0` | 核武器项目 |

---

## P1 — 核心逻辑（Modifier / Requirement 系统）

### Modifiers

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ModifierId | TEXT | — | — | `AGENDA_ALLY_OF_ENKIDU_FRIEND` |
| ModifierType | TEXT | **YES** | — | `MODIFIER_PLAYER_DIPLOMACY_SIMPLE_MODIFIER` |
| RunOnce | BOOLEAN | — | `0` | 仅执行一次 |
| NewOnly | BOOLEAN | — | `0` | 仅对新对象生效 |
| Permanent | BOOLEAN | — | `0` | 永久生效 |
| Repeatable | BOOLEAN | — | `0` | 可重复 |
| OwnerRequirementSetId | TEXT | — | — | 使用者条件 |
| SubjectRequirementSetId | TEXT | — | — | 目标条件 |
| OwnerStackLimit | INTEGER | — | — | 所有者叠加上限 |
| SubjectStackLimit | INTEGER | — | — | 目标叠加上限 |

### ModifierArguments

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ModifierId | TEXT | — | — | — |
| Name | TEXT | — | — | `Amount` / `YieldType` / `BuildingType` / `Percent` ... |
| Type | TEXT | — | `ARGTYPE_IDENTITY` | `ARGTYPE_IDENTITY` / `ScaleByGameSpeed` / `LinearScaleFromDefaultHandicap` |
| Value | TEXT | **YES** | — | `10` / `YIELD_CULTURE` / `BUILDING_MONUMENT` |
| Extra | TEXT | — | — | 扩展参数 |
| SecondExtra | TEXT | — | — | 第二扩展参数 |


---

### Requirements

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| RequirementId | TEXT | — | — | `REQUIRES_PLAYER_DECLARED_SURPRISE_WAR` |
| RequirementType | TEXT | **YES** | — | `REQUIREMENT_PLAYER_DECLARED_WAR` |
| Likeliness | INTEGER | — | `0` | 可能性 |
| Impact | INTEGER | — | `0` | 影响 |
| Inverse | BOOLEAN | — | `0` | 反转条件 |
| Reverse | BOOLEAN | — | `0` | 逆向判断 |
| Persistent | BOOLEAN | — | `0` | 持久化 |
| ProgressWeight | INTEGER | — | `1` | 进度权重 |
| Triggered | BOOLEAN | — | `0` | 触发式 |

### RequirementArguments

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| RequirementId | TEXT | — | — | — |
| Name | TEXT | — | — | `YieldType` / `Amount` / `UnitType` ... |
| Type | TEXT | — | `ARGTYPE_IDENTITY` | `ARGTYPE_IDENTITY` |
| Value | TEXT | **YES** | — | `YIELD_CULTURE` / `10` / `SURPRISE_WAR` |
| Extra | TEXT | — | — | — |
| SecondExtra | TEXT | — | — | — |


---

### RequirementSets

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| RequirementSetId | TEXT | — | — | `PLAYER_DECLARES_SURPRISE_WAR` |
| RequirementSetType | TEXT | **YES** | — | `REQUIREMENTSET_TEST_ALL` / `REQUIREMENTSET_TEST_ANY` |

### RequirementSetRequirements

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| RequirementSetId | TEXT | — | — | `PLAYER_DECLARES_SURPRISE_WAR` |
| RequirementId | TEXT | — | — | `REQUIRES_PLAYER_DECLARED_SURPRISE_WAR` |

---

### DynamicModifiers

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ModifierType | TEXT | — | — | `MODIFIER_PLAYERS_ADJUST_WMD_STOCKPILE`（自定义时注册到此表） |
| CollectionType | TEXT | **YES** | — | `COLLECTION_OWNER` / `COLLECTION_PLAYER_CITIES` / `COLLECTION_ALL_UNITS` / `COLLECTION_ALL_PLAYERS` / `COLLECTION_ALL_CITIES` / `COLLECTION_ALL_DISTRICTS` / `COLLECTION_PLAYER_CAPITAL_CITY` / `COLLECTION_CITY_PLOT_YIELDS` / `COLLECTION_PLAYER_CAPTURED_CITIES` |
| EffectType | TEXT | **YES** | — | `EFFECT_ATTACH_MODIFIER` / `EFFECT_ADJUST_CITY_YIELD_CHANGE` / `EFFECT_ADJUST_UNIT_HEALING_MODIFIERS` ... |

### ModifierStrings

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| ModifierId | TEXT | — | — | — |
| Context | TEXT | — | — | `Preview` / `Sample` / `Summary` |
| Text | TEXT | **YES** | — | `LOC_TOOLTIP_*` |

Context 各值适用场景：

| Context | 适用场景 | 示例 |
|---------|---------|------|
| `Preview` | 战斗力/移动力等数值型 modifier 预览 | `+5 [ICON_STRENGTH] 战斗力` |
| `Sample` | 外交好感度变化描述 | 外交回合中的增减说明 |
| `Summary` | 伟人能力激活描述 | 伟人被动/主动效果摘要 |
| 不填写 | 通用/默认情况 | 大多数 modifier 无需 ModifierStrings |

---

## P2 — 文明 / 领袖 / 政策系统

### Civilizations

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| CivilizationType | TEXT | — | — | `CIVILIZATION_AMERICA` |
| Name | LocalizedText | **YES** | — | `LOC_CIVILIZATION_AMERICA_NAME` |
| Description | TEXT | — | — | `LOC_CIVILIZATION_AMERICA_DESCRIPTION` |
| Adjective | TEXT | **YES** | — | `LOC_CIVILIZATION_AMERICA_ADJECTIVE` |
| RandomCityNameDepth | INTEGER | — | `1` | 随机城市名深度 |
| StartingCivilizationLevelType | TEXT | **YES** | — | `CIVILIZATION_LEVEL_FULL_CIV` / `CIVILIZATION_LEVEL_CITY_STATE` / `CIVILIZATION_LEVEL_TRIBE` / `CIVILIZATION_LEVEL_FREE_CITIES` |
| Ethnicity | TEXT | — | — | `ETHNICITY_EURO` / `ETHNICITY_ASIAN` / `ETHNICITY_AFRICAN` / `ETHNICITY_MEDIT` / `ETHNICITY_SOUTHAM` |

### Leaders

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| LeaderType | TEXT | — | — | `LEADER_ABRAHAM_LINCOLN` |
| Name | TEXT | **YES** | — | `LOC_LEADER_*_NAME` |
| InheritFrom | TEXT | — | — | `LEADER_DEFAULT` / `LEADER_MINOR_CIV_DEFAULT` |
| Sex | TEXT | — | `Male` | `Male` / `Female` |

### Traits

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| TraitType | TEXT | — | — | `TRAIT_AGENDA_ALLY_OF_ENKIDU` |
| Name | LocalizedText | — | — | `LOC_TRAIT_*_NAME` |
| Description | LocalizedText | — | — | `LOC_TRAIT_*_DESCRIPTION` |
| InternalOnly | BOOLEAN | — | `0` | 内部使用，不对玩家显示 |

### Policies

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| PolicyType | TEXT | — | — | `POLICY_DISCIPLINE` |
| Name | TEXT | **YES** | — | `LOC_POLICY_DISCIPLINE_NAME` |
| Description | TEXT | — | — | `LOC_POLICY_DISCIPLINE_DESCRIPTION` |
| PrereqCivic | TEXT | — | — | `CIVIC_CODE_OF_LAWS` |
| PrereqTech | TEXT | — | — | — |
| GovernmentSlotType | TEXT | **YES** | — | `SLOT_MILITARY` / `SLOT_ECONOMIC` / `SLOT_DIPLOMATIC` / `SLOT_GREAT_PERSON` / `SLOT_WILDCARD` |

### UnitAbilities

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| UnitAbilityType | TEXT | — | — | `ABILITY_ANTI_CAVALRY` |
| Name | LocalizedText | — | — | `LOC_ABILITY_*_NAME` |
| Description | LocalizedText | — | — | `LOC_ABILITY_*_DESCRIPTION` |
| Inactive | BOOLEAN | — | `0` | 被动隐藏能力 |
| ShowFloatTextWhenEarned | BOOLEAN | — | `0` | 获得时显示浮动文字 |
| Permanent | BOOLEAN | — | `1` | 永久能力 |

### UnitPromotions

| 列名 | 类型 | 必填 | 默认值 | 示例值 |
|------|------|------|--------|--------|
| UnitPromotionType | TEXT | — | — | `PROMOTION_RANGER` |
| Name | LocalizedText | **YES** | — | `LOC_PROMOTION_RANGER_NAME` |
| Description | LocalizedText | **YES** | — | `LOC_PROMOTION_RANGER_DESCRIPTION` |
| Level | INTEGER | **YES** | — | `1` / `2` / `3` / `4` |
| PromotionClass | TEXT | — | — | `PROMOTION_CLASS_RECON` 等 |
| Column | INTEGER | — | `0` | 树形位置（列） |

---

## P3 — 关联桥表（多对多 Mapping）

这些表通常是 `{Type}+{ModifierId/RequirementId}` 两列的桥接结构，填表时只需 Type 键值。

### TypeTags
`Type` + `Tag`，用于给任意 Type 打标签（如给地块特征分类）。

### UnitReplaces
`CivUniqueUnitType` + `ReplacesUnitType` — 文明特色单位替换的基础单位。

### UnitUpgrades
`Unit` + `UpgradeUnit` — 单位升级链。

### BuildingPrereqs
`Building` + `PrereqBuilding` — 建筑前置建筑链。

### UnitAbilityModifiers
`UnitAbilityType` + `ModifierId` — 能力绑定的 Modifier。

### BuildingModifiers
`BuildingType` + `ModifierId` — 建筑绑定的 Modifier。

### TraitModifiers
`TraitType` + `ModifierId` — 特性绑定的 Modifier。

### GameModifiers
仅 `ModifierId` 一列 — 全局 Modifier。

### TraitModifiers
`TraitType` + `ModifierId` — 特性绑定的 Modifier。


