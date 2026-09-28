# modifier-improvement-plot -- 改良/地块/地形类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

### EFFECT_ADJUST_CITY_ALLOWED_IMPROVEMENT

允许本城市建造指定改良设施（解锁改良）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_ALLOWED_IMPROVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，要解锁的改良 |

> **溯源**：总督梁（测量员）— `AQUACULTURE_CAN_BUILD_FISHERY` 解锁渔场；总督瑞娜（园艺家）— `PARKS_RECREATION_CAN_BUILD_CITY_PARK` 解锁城市公园。`MODIFIER_CITY_ADJUST_ALLOWED_IMPROVEMENT` 首次定义于 `Expansion1_Modifiers.xml`（R&F）。

---

### EFFECT_ADJUST_CITY_APPEAL

调整城市魅力值（Appeal）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_APPEAL` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_APPEAL` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，魅力变化值 |

> **溯源**：`MODIFIER_SINGLE_CITY_ADJUST_CITY_APPEAL` — 大工程师"增加城市魅力"（`GREATPERSON_CITY_APPEAL_SMALL`/`LARGE`，Base `GreatPeople_Engineers.xml`）、金门大桥（`GOLDENGATE_CITYAPPEAL`，GS `Expansion2_Buildings_Major.xml`）。`MODIFIER_PLAYER_CITIES_ADJUST_CITY_APPEAL` — 玩家级全体城市魅力调整，定义于 Base `Modifiers.xml`。两者均只有 `Amount` 一个参数。

---

### EFFECT_ADJUST_CITY_IMPROVEMENT_TOURISM

城市内改良设施产出旅游业绩（Tourism）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_IMPROVEMENT_TOURISM` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_IMPROVEMENT_TOURISM` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，旅游业绩百分比加成（`100` = +100% = 翻倍） |

> **溯源**：金门大桥 — `GOLDENGATE_IMPROVEMENT_TOURISM`（GS `Expansion2_Buildings_Major.xml`），`Amount=100` 意为城市内所有改良旅游业绩翻倍。注意：此 Effect **无** `ImprovementType` 参数 — 作用于城市内所有改良。如需限定特定改良，配合 `SubjectRequirementSetId`（如 `REQUIREMENT_PLOT_IMPROVEMENT_TYPE_MATCHES`）。

---

### EFFECT_ADJUST_CITY_TOURISM_PER_FEATURE

城市中所有具有地貌的地块产出旅游业绩。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_TOURISM_PER_FEATURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每地块旅游业绩值 |

> **溯源**：毛利会堂（Marae）— `MARAE_TOURISM_FEATURES`（GS `Expansion2_Buildings_Major.xml`），`Amount=1`，配合 `SubjectRequirementSetId=MAORI_MARAE_FLIGHT_REQUIREMENT`（飞行科技后生效）。注意：此 Effect **无** `FeatureType` 参数 — 默认对所有地貌生效。限定特定地貌需通过 `SubjectRequirementSetId` 实现。

---

### EFFECT_ADJUST_CITY_YIELD_PER_TERRAIN_CLASS_CITIES_IMPROVEMENT

城市中指定改良设施所在的地块，按其地形类型给予产出加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_YIELD_FOR_TERRAIN_CLASS_CITIES_IMPROVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数，产出加成量 |
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，指定改良 |

> **溯源**：瑞典露天博物馆 — `OPEN_AIR_MUSEUM_CULTURE_FOR_TERRAIN_CLASS_CITIES`（GS `Expansion2_Improvements_Major.xml`），`ImprovementType=IMPROVEMENT_OPEN_AIR_MUSEUM`，`YieldType=YIELD_CULTURE`，`Amount=2`。地形类型筛选由 Requirement 控制（分别对雪地、冻土等挂载），不在 Effect 参数中指定。首次定义于 `Expansion2_Modifiers.xml`。

---

### EFFECT_ADJUST_CITY_YIELD_PER_TERRAIN_TYPE

城市中指定地形类型的地块产出加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_CITY_YIELD_PER_TERRAIN_TYPE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数或小数，产出加成量 |
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，指定地形 |

> **溯源**：葡萄牙航海学校 — `NAVIGATION_SCHOOL_NAVAL_COAST_SCIENCE`（Portugal DLC `Portugal_Buildings.xml`），`TerrainType=TERRAIN_COAST`，`YieldType=YIELD_SCIENCE`，`Amount=0.5`。注意 `Amount` 支持小数（每个海岸 +0.5 科技）。`MODIFIER_CITY_ADJUST_CITY_YIELD_PER_TERRAIN_TYPE` 定义于 `Portugal_Modifiers.xml`。

---

### EFFECT_ADJUST_EXTRA_ACCUMALATION_TERRAIN

指定地形上战略资源的额外累积速度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_ACCUMALATION_TERRAIN` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，额外累积量 |
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，指定地形 |

> **溯源**：加拿大领袖（威尔弗里德·劳雷尔）能力"最后的西部净土"— `TUNDRA_RESOURCE_EXTRACTION`（GS `Expansion2_Leaders_Major.xml`），对冻土、冻土丘陵、雪地、雪地丘陵各挂一条，`Amount=1`。首次定义于 `Expansion2_Modifiers.xml`。
>
> **注意**：效果名中 `ACCUMALATION` 为游戏保留拼写（正确拼写应为 ACCUMULATION），Mod 中引用时需使用原拼写。

---

### EFFECT_ADJUST_FEATURE_APPEAL_MODIFIER

调整城市内特定地貌的魅力值加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_FEATURE_APPEAL_MODIFIER` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_ADJUST_FEATURE_APPEAL_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `FeatureType` | **必写** | [Features.FeatureType](../../SOURCES.md#类型与枚举)，指定地貌 |
| `Amount` | **必写** | 整数，魅力变化值 |

> **溯源**：巴西文明能力"亚马逊"— `TRAIT_AMAZON_RAINFOREST_EXTRA_APPEAL`（Base `Civilizations.xml`），`FeatureType=FEATURE_JUNGLE`，`Amount=2`（雨林 +2 魅力）。`MODIFIER_PLAYER_CITIES_ADJUST_FEATURE_APPEAL_MODIFIER` 为原版定义；`MODIFIER_CITY_ADJUST_FEATURE_APPEAL_MODIFIER` 定义于 `Byzantium_Gaul_Modifiers.xml`（拜占庭/高卢 DLC），作用于单城。

---

### EFFECT_ADJUST_FEATURE_PREREQ

解除特定地貌的建造前置条件（如允许在非该地貌地块上种植该地貌）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FEATURE_UNLOCK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `FeatureType` | **必写** | [Features.FeatureType](../../SOURCES.md#类型与枚举)，要解锁前置条件的地貌 |
| `CivicType` | **必写** | 与该前置关联的人文。`CIVIC_MEDIEVAL_FAIRES / ...`（值来自数据库 Civics 表） |

> **溯源**：越南文明能力"九龙江平原"— `TRAIT_PLANT_MEDIEVAL_WOODS`（KublaiKhan_Vietnam DLC `KublaiKhan_Vietnam_Civilizations.xml`），`FeatureType=FEATURE_FOREST`，`CivicType=CIVIC_MEDIEVAL_FAIRES`。效果：无需等到中世纪集市即可在任何地块（不仅是雨林旁）种植树林。无 `Amount` 参数 — 纯解锁开关。注意：EffectType 名为 `EFFECT_ADJUST_FEATURE_PREREQ` 但 ModifierType 名为 `MODIFIER_PLAYER_ADJUST_FEATURE_UNLOCK`（非对称命名）。`MODIFIER_PLAYER_ADJUST_FEATURE_UNLOCK` 定义于 `KublaiKhan_Vietnam_Modifiers.xml`。
>
> **注意**：Effects.csv 中此 EffectType 标记为 UNTESTED 且未记录参数（`FeatureType`/`CivicType`）；以上参数以官方越南实例为准。

---

### EFFECT_ADJUST_IMPROVEMENT_AMENITY

调整改良设施提供的宜居度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_IMPROVEMENT_AMENITY` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_IMPROVEMENT_AMENITY` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_OWNER_ADJUST_IMPROVEMENT_AMENITY` | `COLLECTION_OWNER_CITY` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宜居度变化值 |

> **溯源**：`MODIFIER_CITY_OWNER_ADJUST_IMPROVEMENT_AMENITY` — 卡霍基亚土堆（`MOUND_AMENITY_MAX_ONE`，GS `Expansion2_Improvements.xml`），配合 `SubjectStackLimit=1` 限制每个城市最多 +1 宜居度；滑雪场（`SKI_RESORT_AMENITY`，同文件）。此 Effect 无 `ImprovementType` 参数，作用于城市范围内所有该改良。限定特定改良应通过 `SubjectRequirementSetId` 实现。

---

### EFFECT_ADJUST_IMPROVEMENT_GOODY_HUT

将指定改良设施标记为村庄（Goody Hut），允许单位踩踏获得奖励。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_IMPROVEMENT_GOODY_HUT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，要标记为村庄的改良 |
| `GoodyHutImprovementType` | 可选 | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，替换的村庄类型，通常填 `IMPROVEMENT_GOODY_HUT` |

> **溯源**：苏美尔领袖能力"史诗任务"— `TRAIT_BARBARIAN_CAMP_GOODY`（Base `Civilizations.xml`），`ImprovementType=IMPROVEMENT_BARBARIAN_CAMP`，`GoodyHutImprovementType=IMPROVEMENT_GOODY_HUT`。定义于 Base `Modifiers.xml`。

---

### EFFECT_ADJUST_IMPROVEMENT_HOUSING

调整改良设施提供的住房。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_IMPROVEMENT_HOUSING` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_IMPROVEMENT_HOUSING` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数（通常 `1` = 1 房）或小数（`0.5` = 半房） |
| `ImprovementType` | 可选 | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，限定特定改良。不填则影响所有改良 |

> **溯源**：印尼甘榜屋 — `KAMPUNG_HOUSING`（Indonesia_Khmer DLC），挂载于 `IMPROVEMENT_KAMPUNG` 本身，`Amount=1`。基尔瓦基斯瓦尼 — `KILWA_IMPROVEMENT_HOUSING`（GS），`Amount=1`。`MODIFIER_SINGLE_CITY_ADJUST_IMPROVEMENT_HOUSING` 定义于 Base `Modifiers.xml`；`MODIFIER_PLAYER_CITIES_ADJUST_IMPROVEMENT_HOUSING` 定义于 GS。Effects.csv 中 `ImprovementType` 参数标记为 ESTIMATED — 实际官方使用中多数不填此参数，改用 SubjectRequirementSetId 或由改良自身挂载。

---

### EFFECT_ADJUST_IMPROVEMENT_VALID_TERRAIN

允许指定改良设施建造在新增的地形类型上。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_IMPROVEMENT_VALID_TERRAIN` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，指定改良 |
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，新增允许的地形 |

> **溯源**：`MODIFIER_PLAYER_CITIES_ADJUST_IMPROVEMENT_VALID_TERRAIN` 定义于 `Expansion2_Modifiers.xml`（GS）。注意：不存在 `MODIFIER_SINGLE_CITY_ADJUST_IMPROVEMENT_VALID_TERRAIN` — 仅玩家级城市集合版本可用。

---

### EFFECT_ADJUST_PLAYER_TERRAIN_WORK_IMPASSABLE_MODIFIER

控制特定地形是否可由市民工作（解除不可通行/不可改良限制）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_TERRAIN_WORKABLE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，指定地形 |
| `Ignore` | **必写** | 整数（`1` = 忽略不可通行，`0` = 恢复不可通行）。注意：不是 `true`/`false` |

> **溯源**：印加文明能力"米塔制度"— `TRAIT_WORK_GRASS_MOUNTAIN` 等五条（GS `Expansion2_Civilizations_Major.xml`），分别对五种山脉子类型（`GRASS/PLAINS/DESERT/TUNDRA/SNOW_MOUNTAIN`）设置 `Ignore=1`，使山脉变为可工作可改良（配合梯田改良）。`MODIFIER_PLAYER_ADJUST_TERRAIN_WORKABLE` 定义于 `Expansion2_Modifiers.xml`。

---

### EFFECT_ADJUST_PLAYER_VALID_IMPROVEMENT

允许玩家建造指定改良设施（全局解锁，玩家级）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_VALID_IMPROVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，要解锁的改良 |

> **溯源**：Base `Modifiers.xml` 定义。与 `EFFECT_ADJUST_CITY_ALLOWED_IMPROVEMENT` 的区别：本 Effect 作用于 `COLLECTION_OWNER`（玩家级），后者作用于 `COLLECTION_OWNER` 的城市 Modifier（如总督指派）。通常挂载于 CivilizationTrait 或 LeaderTrait 全局解锁改良。

---

### EFFECT_ADJUST_PLOT_PURCHASE_COST

调整购买地块的金币花费百分比。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_PLOT_PURCHASE_COST` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_PLOT_PURCHASE_COST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数（百分比），`-20` = 8 折，正值 = 加价 |

> **溯源**：Base `Policies.xml` 政策卡"土地测量员"— `LAND_SURVEYORS_PLOT_PURCHASE_COST`，`Amount=-20`（地块购置费用降低 20%）。`MODIFIER_PLAYER_CITIES_ADJUST_PLOT_PURCHASE_COST` 定义于 Base `Modifiers.xml`；`MODIFIER_SINGLE_CITY_ADJUST_PLOT_PURCHASE_COST` 定义于 `Expansion2_Modifiers.xml`。

---

### EFFECT_ADJUST_PLOT_PURCHASE_COST_TERRAIN

按地形类型调整购买地块的金币花费（仅影响购买了该地形的格子）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_PLOT_PURCHASE_COST_TERRAIN` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数（百分比） |
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，受折扣影响的地形 |

> **溯源**：加拿大领袖能力 — `TUNDRA_PLOT_COST`、`TUNDRA_HILLS_PLOT_COST`、`SNOW_PLOT_COST`、`SNOW_HILLS_PLOT_COST`（GS `Expansion2_Leaders_Major.xml`），均 `Amount=-50`（冻土、雪地购地半价）。`MODIFIER_PLAYER_CITIES_ADJUST_PLOT_PURCHASE_COST_TERRAIN` 定义于 `Expansion2_Modifiers.xml`。

---

### EFFECT_ADJUST_PLOT_YIELD

调整地块产出（最常用的地块产出修改 Effect）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_PLOT_YIELDS_ADJUST_PLOT_YIELD` | `COLLECTION_CITY_PLOT_YIELDS` |
| `MODIFIER_PLAYER_ADJUST_PLOT_YIELD` | `COLLECTION_PLAYER_PLOT_YIELDS` |
| `MODIFIER_SINGLE_PLOT_ADJUST_PLOT_YIELDS` | `COLLECTION_SINGLE_PLOT_YIELDS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt，支持逗号分隔多个 |
| `Amount` | **必写** | 整数。多个 YieldType 时按顺序对应填入多个值（逗号分隔），或填单个值 = 所有产出均加此值 |

> **溯源**：水磨 — `WATERMILL_ADDRICEFOOD`（Base `Buildings.xml`），`MODIFIER_CITY_PLOT_YIELDS_ADJUST_PLOT_YIELD`，`COLLECTION_CITY_PLOT_YIELDS`，`SubjectRequirementSetId=RESOURCE_IS_RICE`，`YieldType=YIELD_FOOD`，`Amount=1`（米麦地块 +1 粮）。最广泛的用法：建筑/政策通过 RequirementSet 筛选特定地块（改良、资源、地貌等），为符合条件的格子加产出。
>
> **CollectionType 选择指南**：
> - `COLLECTION_CITY_PLOT_YIELDS` — 单城的所有地块（建筑/区域 Modifier 常用）
> - `COLLECTION_PLAYER_PLOT_YIELDS` — 玩家全国地块（领袖/文明 Trait 必用）
> - `COLLECTION_SINGLE_PLOT_YIELDS` — 单个地块（单位放置或特定一次性事件）

---

### EFFECT_ADJUST_TERRAIN_YIELD_FROM_ADJACENT_IMPROVEMENTS

指定地形上的地块，根据相邻的指定改良设施数量，获得产出加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_TERRAIN_YIELD_FROM_ADJACENT_IMPROVEMENTS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数，每相邻一个指定改良的产出加成 |
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，受加成的地形（被加成的本体） |
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，相邻触发的改良（触发源） |

> **溯源**：印加梯田 — `TRAIT_TERRACE_GRASS_MOUNTAIN` 等五条（GS `Expansion2_Civilizations_Major.xml`），`TerrainType=TERRAIN_GRASS_MOUNTAIN`（五种山脉子类型各一条），`ImprovementType=IMPROVEMENT_TERRACE_FARM`，`YieldType=YIELD_FOOD`，`Amount=1`。效果：草地山脉每相邻一个梯田 +1 粮。注意：山脉有五种子类型，需全部列出。`MODIFIER_PLAYER_CITIES_ADJUST_TERRAIN_YIELD_FROM_ADJACENT_IMPROVEMENTS` 定义于 `Expansion2_Modifiers.xml`。
>
> **与三种相邻加成 Effect 的区别**：本 Effect 是 **被加成地块 = 特定地形，触发源 = 特定改良**，产出加在 **地块本身**；而 `EFFECT_IMPROVEMENT_ADJACENCY` / `EFFECT_TERRAIN_ADJACENCY` / `EFFECT_FEATURE_ADJACENCY` 是加在 **区域** 上。

---

### EFFECT_ADJUST_VALID_FEATURES_DISTRICTS

允许指定区域建造在新增的地貌上（解除地貌放置限制）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_VALID_FEATURES_DISTRICTS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DistrictType` | **必写** | [Districts.DistrictType](../../SOURCES.md#类型与枚举)，指定区域 |
| `FeatureType` | **必写** | [Features.FeatureType](../../SOURCES.md#类型与枚举)，新增允放的地貌 |

> **溯源**：埃及文明能力"尼罗河的赠礼"— `TRAIT_FLOODPLAINS_VALID_HOLY_SITE` 等九条（Base `Civilizations.xml`），覆盖所有专业区域 + 水渠 + 航空港 + 航天基地 + 社区，`FeatureType=FEATURE_FLOODPLAINS`。定义于 Base `Modifiers.xml`。

---

### EFFECT_ADJUST_VALID_FEATURES_WONDERS

允许奇观建造在新增的地貌上（解除地貌放置限制）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_VALID_FEATURES_WONDERS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `FeatureType` | **必写** | [Features.FeatureType](../../SOURCES.md#类型与枚举)，新增允放的地貌 |

> **溯源**：埃及能力 — `TRAIT_FLOODPLAINS_VALID_WONDER`（Base `Civilizations.xml`），`FeatureType=FEATURE_FLOODPLAINS`。与 `EFFECT_ADJUST_VALID_FEATURES_DISTRICTS` 的区别：本 Effect 无 `DistrictType` 参数，作用于 **所有奇观**。定义于 Base `Modifiers.xml`。

---

### EFFECT_FEATURE_ADJACENCY

根据相邻指定地貌为区域提供相邻加成（半级 = 每 N 格触发 1 次）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_CITIES_FEATURE_ADJACENCY` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_PLAYER_CITIES_FEATURE_ADJACENCY` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_FEATURE_ADJACENCY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数，产出加成量 |
| `FeatureType` | **必写** | [Features.FeatureType](../../SOURCES.md#类型与枚举)，相邻地貌 |
| `DistrictType` | **必写** | [Districts.DistrictType](../../SOURCES.md#类型与枚举)，获得加成的区域 |
| `Description` | **必写** | `LOC_` 文本键 |
| `TilesRequired` | 可选 | 整数，默认 `1`。每 N 格触发 1 次加成（例如 `2` = 每 2 格 +1，即"半级"相邻加成） |

> **溯源**：三种 CollectionType 均定义于 Base `Modifiers.xml`。`EFFECT_FEATURE_ADJACENCY` 与 `Adjacency_YieldChanges` 表的 `AdjacentFeature` 列功能等同 — 区别在于 Modifier 版本可挂载 `SubjectRequirementSetId` 实现动态条件（如仅在特定科技/人文后生效）。**无动态条件需求时优先使用 Adjacency_YieldChanges 表**，性能更好、配置更简洁。
>
> 示例：圣地邻接自然奇观 +2 信仰 → `FeatureType=FEATURE_NATURAL_WONDER, DistrictType=DISTRICT_HOLY_SITE, YieldType=YIELD_FAITH, Amount=2`。

---

### EFFECT_GRANT_PLAYER_FAITH_FROM_REMOVE_FEATURE

清除地貌时获得信仰值（砍树/收割沼泽得信仰）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_FAITH_FROM_REMOVE_FEATURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，获得信仰值 |

> **溯源**：定义于 Base `Modifiers.xml`。无 `FeatureType` 参数 — 对所有地貌生效。如需限定特定地貌，挂载 `SubjectRequirementSetId`。
>
> **注意**：Effects.csv 将此 EffectType 标记为 USER ADDED（Y 列），与 Base XML 中存在定义矛盾，存疑。[无官方使用示例，但 Mod 中可用]

---

### EFFECT_GRANT_PLOT

将当前地块所有权授予玩家（直接吞并地块，无需金币购买）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_UNIT_GRANT_PLOT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| （无参数） | -- | 此 Effect 无 `ModifierArguments` |

> **溯源**：大商人"授予地块"能力 — `GREATPERSON_GRANT_PLOT`（Base `GreatPeople_Merchants.xml`），`RunOnce=true`，`Permanent=true`。无 ModifierArguments — 地块选择由 `COLLECTION_OWNER` + 单位所在位置自动决定。定义于 Base `Modifiers.xml`。注意：Modifier 不挂载参数，直接由单位所在格或上下文决定吞并目标。

---

### EFFECT_GRANT_YIELD_PER_FEATURE_IN_CITY

城市范围内按指定地貌类型每格给予产出（不是按种类计数，是按地块数量）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_GRANT_YIELD_PER_FEATURE_TYPE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `FeatureType` | **必写** | [Features.FeatureType](../../SOURCES.md#类型与枚举)，指定地貌 |
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数，每格产出量 |

> **溯源**：生物圈（Biosphere）— `BIOSPHERE_GRANT_SCIENCE_PER_RAINFOREST`（Byzantium_Gaul DLC `Byzantium_Gaul_Buildings.xml`），`FeatureType=FEATURE_JUNGLE`，`YieldType=YIELD_SCIENCE`，`Amount=100`。同时对雨林、沼泽、树林各挂一条。注意：Effects.csv 标记为 UNTESTED，但官方实际使用确认存在。效果是按地块数乘算（城市有 3 个雨林 = +300 科技），不是按地貌种类数。`MODIFIER_CITY_GRANT_YIELD_PER_FEATURE_TYPE` 定义于 `Byzantium_Gaul_Modifiers.xml`。

---

### EFFECT_IMPROVEMENT_ADJACENCY

根据相邻指定改良设施为区域提供相邻加成（半级 = 每 N 格触发 1 次）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_IMPROVEMENT_ADJACENCY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数，产出加成量 |
| `ImprovementType` | **必写** | [Improvements.ImprovementType](../../SOURCES.md#类型与枚举)，相邻触发改良 |
| `DistrictType` | **必写** | [Districts.DistrictType](../../SOURCES.md#类型与枚举)，获得加成的区域 |
| `Description` | **必写** | `LOC_` 文本键 |
| `TilesRequired` | 可选 | 整数，默认 `1`（每格 +1）。`2` = 每 2 格 +1 = "半级"加成 |

> **溯源**：高卢文明能力 — `TRAIT_CIVILIZATION_GAUL_HOLYSITE_ADJACENCYFAITH`（Byzantium_Gaul DLC `Byzantium_Gaul_Civilizations.xml`），`DistrictType=DISTRICT_HOLY_SITE`，`ImprovementType=IMPROVEMENT_MINE`，`YieldType=YIELD_FAITH`，`Amount=1`，`TilesRequired=2`（圣地每相邻 2 个矿场 +1 信仰）。共六条覆盖全部专业区域。
>
> `MODIFIER_PLAYER_CITIES_IMPROVEMENT_ADJACENCY` 定义于 `Byzantium_Gaul_Modifiers.xml`。与 `Adjacency_YieldChanges` 的 `AdjacentImprovement` 列功能等同 — **无动态条件需求时优先使用 Adjacency_YieldChanges 表**。注意：不存在 `MODIFIER_ALL_CITIES_IMPROVEMENT_ADJACENCY` 或 `MODIFIER_SINGLE_CITY_IMPROVEMENT_ADJACENCY`，仅此一个 ModifierType 可用。

---

### EFFECT_TERRAIN_ADJACENCY

根据相邻指定地形为区域提供相邻加成（半级 = 每 N 格触发 1 次）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_CITIES_TERRAIN_ADJACENCY` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_PLAYER_CITIES_TERRAIN_ADJACENCY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | YieldType.txt |
| `Amount` | **必写** | 整数，产出加成量 |
| `TerrainType` | **必写** | [Terrains.TerrainType](../../SOURCES.md#类型与枚举)，相邻地形 |
| `DistrictType` | **必写** | [Districts.DistrictType](../../SOURCES.md#类型与枚举)，获得加成的区域 |
| `Description` | **必写** | `LOC_` 文本键 |
| `TilesRequired` | 可选 | 整数，默认 `1`（每格 +1） |

> **溯源**：马里文明能力 — `TRAIT_DESERT_CITY_CENTER_FAITH`（GS `Expansion2_Civilizations_Major.xml`），`DistrictType=DISTRICT_CITY_CENTER`，`TerrainType=TERRAIN_DESERT`，`YieldType=YIELD_FAITH`。三种 CollectionType 均定义于 Base `Modifiers.xml`。
>
> 与 `Adjacency_YieldChanges` 的 `AdjacentTerrain` 列功能等同 — **无动态条件需求时优先使用 Adjacency_YieldChanges 表**。注意：不存在 `MODIFIER_SINGLE_CITY_TERRAIN_ADJACENCY` — 仅 `ALL_CITIES` 和 `PLAYER_CITIES` 两种可用。山脉有五种子类型（`GRASS/PLAINS/DESERT/TUNDRA/SNOW_MOUNTAIN`），需全部列出才能覆盖所有山脉。

---

## 注意事项

### 三种相邻加成 Effect vs Adjacency_YieldChanges 表

| 维度 | `EFFECT_FEATURE_ADJACENCY` | `EFFECT_IMPROVEMENT_ADJACENCY` | `EFFECT_TERRAIN_ADJACENCY` | `Adjacency_YieldChanges` 表 |
|------|---------------------------|-------------------------------|---------------------------|----------------------------|
| 触发源 | 地貌 | 改良设施 | 地形 | 地貌/改良/地形（对应三列） |
| ModifierType 数量 | 3 种（ALL/PLAYER/SINGLE） | 1 种（PLAYER_CITIES） | 2 种（ALL/PLAYER） | N/A（纯数据表） |
| 动态条件 | 支持（RequirementSetId） | 支持 | 支持 | 不支持 |
| 性能 | 较低 | 较低 | 较低 | 高 |
| 推荐场景 | 需条件判断时 | 需条件判断时 | 需条件判断时 | 固定加成（首选） |

**结论**：固定不变的相邻加成优先用 `Adjacency_YieldChanges` 表；需要动态条件（如科技/人文解锁后才生效）时使用 Modifier 版本。

### 参数细节

- `Ignore` 参数：值为整数 `1`/`0`，**不是** `true`/`false`（Effects.csv 虽标注为 Boolean 类型，但 XML 实际使用整数值）
- `Amount` 小数支持：`EFFECT_ADJUST_CITY_YIELD_PER_TERRAIN_TYPE` 和 `EFFECT_ADJUST_IMPROVEMENT_HOUSING` 的 `Amount` 支持小数（如 `0.5`）
- `Description` 参数：三种相邻加成 Effect 必须填 `LOC_` 文本键，用于游戏内显示相邻加成来源提示

### 不存在的 ModifierType

以下 ModifierType 在数据库中不存在，请勿使用：
- `MODIFIER_ALL_CITIES_IMPROVEMENT_ADJACENCY`
- `MODIFIER_SINGLE_CITY_IMPROVEMENT_ADJACENCY`
- `MODIFIER_SINGLE_CITY_TERRAIN_ADJACENCY`
- `MODIFIER_SINGLE_CITY_ADJUST_IMPROVEMENT_VALID_TERRAIN`

### Effects.csv 标记说明

- `EFFECT_ADJUST_CITY_YIELD_PER_TERRAIN_TYPE`：Effects.csv 中 DLC 覆盖率有限，`Amount` 支持小数（实际验证无误）
- `EFFECT_GRANT_YIELD_PER_FEATURE_IN_CITY`：Effects.csv 标记为 UNTESTED，但官方已使用（生物圈），参数为 `FeatureType` + `YieldType` + `Amount`
- `EFFECT_ADJUST_IMPROVEMENT_HOUSING`：Effects.csv 中 `ImprovementType` 标记为 ESTIMATED，官方实际使用中多数不填此参数
