# modifier-resource -- 资源/奢侈/战略/电力类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

### EFFECT_ADJUST_ADD_AMENITY_PER_ADJACENT_LUXURY

城市每拥有一条相邻奢侈资源即增加宜居度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADD_AMENITY_PER_ADJACENT_LUXURY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AddAmenity` | **必写** | `true` / `1`（Boolean） |

> **溯源**：玛雅文明特性 `TRAIT_CIVILIZATION_MAYAB` → `TRAIT_ADD_AMENITY_PER_ADJACENT_LUXURY` — 所有城市每相邻一处奢侈资源 +1 宜居度（AddAmenity=true）。

---

### EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION

城市每回合额外累积所有可累积型资源的数量（通用版，不限资源种类）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_ACCUMULATION` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_EXTRA_ACCUMULATION` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_CITIES_ADJUST_EXTRA_ACCUMULATION` | `COLLECTION_EMERGENCY_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1` |

> **溯源**：
> - `COMMUNISM` 政体 → `CORPORATE_LIBERTARIANISM_RESOURCE_EXTRACTION`（`PLAYER_CITIES` 版，Amount=1）— 所有城市每回合 +1 全部战略资源累积。
> - 总督"资源管理员"三级能力 `GOVERNOR_PROMOTION_RESOURCE_MANAGER_INDUSTRIALIST`（`SINGLE_CITY` 版）— 该城市每回合 +1 全部战略资源累积。

---

### EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION_FOR_STRATEGIC_DIVERSITY

根据城市拥有战略资源种类多样性，每多一种额外增加每回合累积量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_EXTRA_ACCUMULATION_FOR_STRATEGIC_DIVERSITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1` |

> **溯源**：大巴扎建筑 `BUILDING_GRAND_BAZAAR` → `GRANDBAZAAR_ACCUMULATION_STRATEGICS`（Amount=1）— 城市每种改良的战略资源 +1 每回合累积量。

---

### EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION_SPECIFIC_RESOURCE

指定城市对指定资源增加每回合累积量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_ACCUMULATION_SPECIFIC_RESOURCE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1`、`2` |
| `ResourceType` | **必写** | `RESOURCE_ALUMINUM` / `RESOURCE_COAL` / `RESOURCE_IRON` / `RESOURCE_URANIUM` / ... |

> **溯源**：见于资料片中特定政体/能力使用。与 `EFFECT_ADJUST_PLAYER_RESOURCE_ACCUMULATION_MODIFIER` 的区别：此效果作用于城市级别（`PLAYER_CITIES`），后者作用于玩家级别。

---

### EFFECT_ADJUST_CITY_EXTRA_AMENITY_FOR_LUXURY_DIVERSITY

根据城市拥有奢侈资源种类多样性增加宜居度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_EXTRA_AMENITY_FOR_LUXURY_DIVERSITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1` |

> **溯源**：大巴扎建筑 `BUILDING_GRAND_BAZAAR` → `GRANDBAZAAR_AMENITIES_LUXURIES`（Amount=1）— 城市每种改良的奢侈资源 +1 宜居度。

---

### EFFECT_ADJUST_CITY_FREE_POWER

为城市提供免费电力（绝对值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_FREE_POWER` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_FREE_POWER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `2`、`6` |
| `SourceType` | **必写** | `FREE_POWER_SOURCE_MISC` / `FREE_POWER_SOURCE_GEOTHERMAL` / `FREE_POWER_SOURCE_SOLAR` / `FREE_POWER_SOURCE_WATER` / `FREE_POWER_SOURCE_WIND` |

> **溯源**：
> - `PLAYER_CITIES` 版：加的夫城邦宗主权 → `MINOR_CIV_CARDIFF_POWER_LIGHTHOUSE`（Amount=2, SourceType=`FREE_POWER_SOURCE_MISC`）— 拥有灯塔的城市 +2 免费电力。同样模式用于船坞/海港。
> - `SINGLE_CITY` 版：水电站坝 `BUILDING_HYDROELECTRIC_DAM` → `HYDROELECTRIC_DAM_FREE_POWER`（Amount=6, SourceType=`FREE_POWER_SOURCE_WATER`）。配合总督"可再生能源"能力 → `MERCHANT_RENEWABLE_ENERGY_HYDROELECTRIC_DAM_FREE_POWER`（Amount=2, SourceType=`FREE_POWER_SOURCE_WATER`）。

> **选用指南**：作用于全体城市用 `PLAYER_CITIES` 版（通常配合 `FREE_POWER_SOURCE_MISC`）；作用于特定城市/建筑用 `SINGLE_CITY` 版（配合对应能源类型：水坝→`WATER`，地热裂隙→`GEOTHERMAL`，太阳能→`SOLAR`，风能→`WIND`）。

---

### EFFECT_ADJUST_CITY_IGNORE_STRATEGIC_RESOURCE_REQUIREMENTS

城市忽略战略资源需求，可无条件训练/建造需要战略资源的单位和建筑。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_IGNORE_STRATEGIC_RESOURCE_REQUIREMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Ignore` | **可选** | `true`（Boolean，通常不写即为忽略） |

> **溯源**：总督"资源管理员"能力 `GOVERNOR_PROMOTION_RESOURCE_MANAGER_BLACK_MARKETEER` → `BLACK_MARKETEER_IGNORE_STRATEGIC_RESOURCE_REQUIREMENT` — 该城市建造单位/建筑无需战略资源。

---

### EFFECT_ADJUST_CITY_REQUIRED_POWER

调整城市所需电力阈值（影响电力满意度判定）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_REQUIRED_POWER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，正值增加所需，负值减少所需 |

> **溯源**：用于特定领袖能力或城邦效果，减少城市电力需求以提高电力满意度。

---

### EFFECT_ADJUST_CITY_RESOURCE_HARVEST_BONUS

调整收割/移除资源（砍树、收石头等）时的产出加成百分比。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_RESOURCE_HARVEST_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比整数，如 `50`（+50%）、`100`（+100%） |

> **溯源**：总督"资源管理员"能力 `GOVERNOR_PROMOTION_RESOURCE_MANAGER_GROUNDBREAKER` → `GROUNDBREAKER_BONUS_HARVEST_YIELDS`（Amount=50）— 该城市收割资源时 +50% 产出。

---

### EFFECT_ADJUST_CITY_STRATEGIC_RESOURCE_REQUIREMENT_MODIFIER

调整城市建造单位所需战略资源的消耗量（百分比折扣）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_STRATEGIC_RESOURCE_REQUIREMENT_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比整数，如 `50`（五折）、`80`（八折）、`-20`（减少 20% 消耗） |

> **溯源**：见于特定军事政策卡或文明特性。Amount 含义为"折扣后百分比"，即 `50` = 原消耗的 50%（半价）。

---

### EFFECT_ADJUST_FULL_ACCESS_ONE_STRATEGIC

使玩家获得一种战略资源的完全使用权，无需改良即可使用（但不计入交易库存）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FULL_ACCESS_ONE_STRATEGIC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Access` | **必写** | `true` / `1`（Boolean） |

> **溯源**：见于大商人能力 — 激活后获得指定战略资源的完全使用权。

---

### EFFECT_ADJUST_MOST_ADVANCED_STRATEGIC_RESOURCE_COUNT

调整从村庄/遗址获得的最高级战略资源数量（受游戏速度缩放）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_MOST_ADVANCED_STRATEGIC_RESOURCE_COUNT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `20`。Type=`ScaleByGameSpeed`（受游戏速度缩放） |

> **溯源**：特定文明特性 — 进入新时代后获得当前可解锁的最高级战略资源。注意此参数的 Argument Type 为 `ScaleByGameSpeed`，非默认 `ARGTYPE_IDENTITY`。
>
> **注意**：Effects.csv 中此 EffectType 标记为 USER ADDED（Y 列）。[无官方使用示例，但 Mod 中可用]

---

### EFFECT_ADJUST_MODIFIED_FREE_POWER_IN_CITY

按百分比调整城市免费电力总量（对已有免费电力进行百分比加成）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_MODIFIED_FREE_POWER_MODIFIER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比整数，如 `200`（+200%） |

> **溯源**：生物圈奇观 `BUILDING_BIOSPHERE` → `BIOSPHERE_MODIFIED_FREE_POWER`（Amount=200）— 所有城市的可再生能源设施（水坝、风车、太阳能等）提供的免费电力 +200%。

> **与 `EFFECT_ADJUST_CITY_FREE_POWER` 的区别**：此效果对已有的免费电力进行**百分比倍增**（如生物圈使水坝的 6 电力变为 18），而非直接给予免费电力绝对值。

---

### EFFECT_ADJUST_OWNED_BONUS_RESOURCE_EXTRA_AMENITIES

每座城市拥有的加成资源额外提供宜居度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_OWNED_BONUS_RESOURCE_EXTRA_AMENITIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1` |

> **溯源**：玩家级效果，每座城市拥有的每种加成资源按 Amount 值提供额外宜居度。

---

### EFFECT_ADJUST_OWNED_LUXURY_EXTRA_AMENITIES

玩家拥有的每种奢侈资源额外提供宜居度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_OWNED_LUXURY_EXTRA_AMENITIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1`、`2` |

> **溯源**：玩家级效果，拥有的每种奢侈资源按 Amount 值提供额外宜居度（叠加在标准 +1 之上）。

---

### EFFECT_ADJUST_PLAYER_BAN_RESOURCE

禁止玩家使用指定资源。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_BAN_RESOURCE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ResourceType` | **必写** | `RESOURCE_URANIUM` / ... |

> **溯源**：资源类型通过 `ResourceType` 参数直接指定，作用于所有主要文明玩家（`COLLECTION_MAJOR_PLAYERS`），用于情境/剧本禁用特定资源。

---

### EFFECT_ADJUST_PLAYER_FREE_RESOURCE_IMPORT

玩家每回合免费获得指定资源（计入进口统计）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FREE_RESOURCE_IMPORT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1` |
| `ResourceType` | **必写** | `RESOURCE_ALUMINUM` / `RESOURCE_COAL` / `RESOURCE_HORSES` / `RESOURCE_IRON` / `RESOURCE_NITER` / `RESOURCE_CINNAMON` / `RESOURCE_CLOVES` / ... |

> **溯源**：见于大商人伟人效果 — 激活后每回合获得指定资源的进口量。资源报告中显示为"进口"来源。

---

### EFFECT_ADJUST_PLAYER_FREE_RESOURCE_IMPORT_EXTRACTION

玩家每回合免费获得指定资源（计入开采统计）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FREE_RESOURCE_IMPORT_EXTRACTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `2` |
| `ResourceType` | **必写** | `RESOURCE_ALUMINUM` / `RESOURCE_COAL` / `RESOURCE_HORSES` / ... |

> **溯源**：见于伟人或纪念效果 — 资源报告中显示为"开采自"来源。

> **与 `EFFECT_ADJUST_PLAYER_FREE_RESOURCE_IMPORT` 的区别**：`_EXTRACTION` 版计入开采，普通版计入进口。两种效果的实际资源获得量相同，区别仅在于资源报告的显示分类。

---

### EFFECT_ADJUST_PLAYER_NO_CAP_RESOURCE

使玩家持有的指定资源不受上限限制（可超量存储）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_NO_CAP_RESOURCE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| （无内置参数 — 资源类型通过 `RequirementSetId` 指定） | — | — |

> **溯源**：环境效应/情境效果，作用于所有主要文明。与 `EFFECT_ADJUST_PLAYER_BAN_RESOURCE` 同为 `COLLECTION_MAJOR_PLAYERS`。

---

### EFFECT_ADJUST_PLAYER_PREVENT_HARVEST_RESOURCE

阻止玩家收割/移除资源。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_PREVENT_HARVEST_RESOURCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `true` / `1`（启用阻止） |

> **溯源**：特定情境/剧本中用于保护有限资源不被移除。

---

### EFFECT_ADJUST_PLAYER_RESOURCE_ACCUMULATION_MODIFIER

**每个已改良的对应资源地块**每回合额外产出 +X（按改良地块数叠加），**不是**玩家每回合直接 +X。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_RESOURCE_ACCUMULATION_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1`（每个已改良的对应资源地块每回合 +1） |
| `ResourceType` | **可选** | `RESOURCE_HORSES` / `RESOURCE_IRON` / `RESOURCE_OIL` / ...。**不填则对所有可累积资源生效** |

> **溯源**：
> - 政策卡 `POLICY_EQUESTRIAN_ORDERS` → `EQUESTRIAN_ORDERS_ADDITIONAL_HORSES_EXTRACTION`（Amount=1, ResourceType=`RESOURCE_HORSES`）以及 `_ADDITIONAL_IRON_EXTRACTION`（Amount=1, ResourceType=`RESOURCE_IRON`）。
> - 政策卡 `POLICY_DRILL_MANUALS` → `DRILL_MANUALS_ADDITIONAL_NITER_EXTRACTION`（Amount=1, ResourceType=`RESOURCE_NITER`）以及 `_ADDITIONAL_COAL_EXTRACTION`（Amount=1, ResourceType=`RESOURCE_COAL`）。
> - 政策卡 `POLICY_RESOURCE_MANAGEMENT` → `RESOURCE_MANAGEMENT_ADDITIONAL_ALUMINUM_EXTRACTION`（Amount=1, ResourceType=`RESOURCE_ALUMINUM`）以及 `_ADDITIONAL_OIL_EXTRACTION`（Amount=1, ResourceType=`RESOURCE_OIL`）。

> **⚠️ 实测（0052 花太郎）**：此效果的作用对象是**已改良的对应资源地块**（如已建油井的石油地块），每块 +X 每回合；玩家没有对应资源的改良地块时**不加任何东西**。要"凭空每回合 +X 战略资源"应改用城市级累积系列（`EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION_*`）——官方仅注册 `PLAYER_CITIES` 版；挂改良/建筑需城市单点效果时，自定义 `COLLECTION_OWNER` 版（0052 石像产油方案，2 行注册 + 挂 ImprovementModifiers）。

---

### EFFECT_ADJUST_PLAYER_RESOURCE_STOCKPILE_CAP

调整玩家战略资源储备上限。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_RESOURCE_STOCKPILE_CAP` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_RESOURCE_STOCKPILE_CAP` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `10`、`20`、`50` |

> **溯源**：
> - `PLAYER` 版（`COLLECTION_OWNER`）：玩家级效果，常用于文明特性或大科学家能力，直接增加全局储备上限。
> - `PLAYER_CITIES` 版（`COLLECTION_PLAYER_CITIES`）：每座城市增加上限，如军营建筑 `BUILDING_BARRACKS` → `BARRACKS_ADJUST_RESOURCE_STOCKPILE_CAP`（Amount=10）。

---

### EFFECT_ADJUST_RESOURCE_YIELD_BY_COUNT

根据城市拥有的资源总数产生产出（按资源种类计数，无需改良）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_RESOURCE_YIELD_BY_COUNT` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_FAITH` / `YIELD_CULTURE` / `YIELD_GOLD` / `YIELD_PRODUCTION` / `YIELD_SCIENCE` / `YIELD_FOOD` |
| `Amount` | **必写** | 整数，如 `1`（每种资源 +1 对应产出） |
| `ResourceType` | **可选** | 指定单一资源类型；不填则对城市所有资源种类计数 |
| `MinimumCount` | **可选** | 整数，资源最低数量阈值，低于此数不计入 |

> **溯源**：埃塞俄比亚文明特性 `TRAIT_CIVILIZATION_ETHIOPIA` → `TRAIT_FAITH_RESOURCES`（YieldType=`YIELD_FAITH`, Amount=1）— 每座城市每种改良后的资源 +1 信仰。用法中未指定 ResourceType，因此对城市拥有的所有资源类型都计数。
>
> **注意**：Effects.csv 中此 EffectType 标记为 UNTESTED，全部参数（`ResourceType`/`MinimumCount`/`YieldType`/`Amount`）均标记为 ESTIMATED。以上参数以官方埃塞俄比亚实例为准验证。
>
> **与 `EFFECT_ADJUST_YIELD_BY_NUMBER_OF_RESOURCES` 的区别**：此效果按城市拥有的**每种资源**分别计数产出；后者按玩家**改良的资源种类总数**统一产出。

---

### EFFECT_ADJUST_YIELD_BY_NUMBER_OF_RESOURCES

根据玩家改良的资源种类数量调整产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_YIELD_BY_NUMBER_RESOURCES` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_PRODUCTION` / `YIELD_FAITH` / `YIELD_CULTURE` / `YIELD_GOLD` / `YIELD_SCIENCE` / `YIELD_FOOD` |
| `Amount` | **必写** | 整数，如 `1`（每改良一种资源 +N 产出） |

> **溯源**：约翰内斯堡城邦宗主权 `MINOR_CIV_JOHANNESBURG_TRAIT` → `MINOR_CIV_JOHANNESBURG_PRODUCTION_RESOURCES`（YieldType=`YIELD_PRODUCTION`, Amount=1）— 所有城市每改良一种资源类型 +1 生产力。后期版 `MINOR_CIV_JOHANNESBURG_PRODUCTION_RESOURCES_LATE`（附需求 "已研究工业化"）效果叠加。
>
> **注意**：Effects.csv 中此 EffectType 标记为 UNTESTED。以上参数以官方约翰内斯堡城邦实例为准验证。
>
> **与 `EFFECT_ADJUST_RESOURCE_YIELD_BY_COUNT` 的区别**：此效果按改良资源**种类总数**统一产出（所有城市获得相同加成），而 `_BY_COUNT` 按**每座城市各自的资源数量**分别产出（不同城市加成不同）。

---

### EFFECT_CITY_GRANT_RANDOM_RESOURCE_PRODUCT

在城市中随机获得一种资源产品（化妆品、牛仔裤、香水等伟人奢侈产品）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_RANDOM_RESOURCE_PRODUCT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| （无参数 — 从可用产品池中随机选取） | — | — |

> **溯源**：大商人伟人效果（如雅诗兰黛、可可·香奈儿等）— 激活后在该城市生成一个随机奢侈品资源（如化妆品 RESOURCE_COSMETICS、牛仔裤 RESOURCE_JEANS、香水 RESOURCE_PERFUME、玩具 RESOURCE_TOYS 等）。

---

### EFFECT_GRANT_FREE_RESOURCE_EXTRACTED

城市免费获得指定资源的开采产出（城市级，持续/永久）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_FREE_RESOURCE_EXTRACTION` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_CITIES_GRANT_FREE_RESOURCE_IN_CITY` | `COLLECTION_EMERGENCY_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | `SINGLE_CITY` 版 **必写**；`EMERGENCY` 版 无 | 整数，如 `3` |
| `ResourceType` | `SINGLE_CITY` 版 **必写**；`EMERGENCY` 版 无 | `RESOURCE_OIL` / `RESOURCE_IRON` / ... |

> **溯源**：
> - `SINGLE_CITY` 版：大商人约翰·洛克菲勒 `GREAT_PERSON_INDIVIDUAL_JOHN_ROCKEFELLER` → `GREATPERSON_GRANT_3_OIL_PER_TURN`（ResourceType=`RESOURCE_OIL`, Amount=3, RunOnce=true, Permanent=true）— 激活后所在城市永久每回合 +3 石油。
> - `EMERGENCY` 版：用于紧急事件/援助场景，参数由事件配置外部驱动。

---

### EFFECT_GRANT_FREE_RESOURCE_IN_CITY

在城市中免费获得指定资源（不依赖改良设施）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_GRANT_RESOURCE_IN_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1`、`2` |
| `ResourceType` | **必写** | `RESOURCE_COSMETICS` / `RESOURCE_IRON` / `RESOURCE_JEANS` / `RESOURCE_OIL` / `RESOURCE_PERFUME` / `RESOURCE_TOYS` / ... |

> **溯源**：大商人伟人效果 — 激活后在所在城市创建指定奢侈品资源（如化妆品、牛仔裤等），与 `EFFECT_CITY_GRANT_RANDOM_RESOURCE_PRODUCT` 不同，此效果需显式指定 ResourceType。

---

### EFFECT_GRANT_FREE_RESOURCE_VISIBILITY

免费揭示/可见指定资源（无需科技即可在地图上看到该资源）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_FREE_RESOURCE_VISIBILITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ResourceType` | **必写** | `RESOURCE_OIL` / `RESOURCE_ALUMINUM` / `RESOURCE_URANIUM` / ... |

> **溯源**：见于大科学家或特定伟人效果 — 提前揭示指定战略资源的分布位置。

---

### EFFECT_GRANT_PLAYER_FREE_RESOURCE_EXTRACTED

玩家免费获得指定资源的开采产出（玩家级，每回合）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FREE_RESOURCE_EXTRACTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，如 `1`、`2`、`3` |
| `ResourceType` | **必写** | `RESOURCE_ALUMINUM` / `RESOURCE_COAL` / `RESOURCE_HORSES` / `RESOURCE_IRON` / `RESOURCE_NITER` / ... |

> **溯源**：
> - 大商人约翰·洛克菲勒 → `GREATPERSON_GRANT_1_OIL_PER_TURN`（Amount=1, ResourceType=`RESOURCE_OIL`, RunOnce=1, Permanent=1）— 永久每回合 +1 石油。
> - 大军事家/大提督伟人效果 — 每回合无条件获得指定数量的战略资源（计入开采）。
> - 时代纪念"自动机" → `COMMEMORATION_AUTOMATON_GA_FREE_URANIUM`（Amount=3, ResourceType=`RESOURCE_URANIUM`，条件=黄金时代）。
> - Siqi 0047 → `MODIFIER_SIQI_0047_IRON_PER_TURN_2`（Amount=2, ResourceType=`RESOURCE_IRON`, RunOnce=0, Permanent=0）。
> - Siqi 0052 石像产油 → 挂 `ImprovementModifiers`（Amount=1, ResourceType=`RESOURCE_OIL`），每座改良实例独立一份、叠加成 N×Amount。

> **选用指南（0052 实测）**：要"每回合凭空 +X 指定战略资源"（与地块/改良无关）→ **用本类型**；`EFFECT_ADJUST_PLAYER_RESOURCE_ACCUMULATION_MODIFIER` 是"每个已改良的对应资源地块每回合+X"，语义不同勿混用；`EFFECT_GRANT_FREE_RESOURCE_IN_CITY` 是一次性。挂改良/建筑时每份附件独立触发，可叠加。
> **与 `EFFECT_GRANT_FREE_RESOURCE_EXTRACTED`（`SINGLE_CITY` 版）的区别**：此效果作用于**玩家级别**，属于 `COLLECTION_OWNER`，无需指定城市；后者作用于特定城市。

---

### EFFECT_GRANT_FREE_RESOURCE_FROM_UNIT_PLOT

根据单位所在地块产出免费资源。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_FREE_RESOURCE_FROM_UNIT_PLOT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 |

> **溯源**：见于特定单位能力，从单位所在地块提取资源产出。

---

## 注意事项

### FREE_POWER 系列区分

| 效果 | 作用 | 参数 | 典型用例 |
|------|------|------|----------|
| `EFFECT_ADJUST_CITY_FREE_POWER` | 给予免费电力绝对值 | Amount + SourceType | 水电站坝(6,WATER)、加的夫宗主权(2,MISC) |
| `EFFECT_ADJUST_MODIFIED_FREE_POWER_IN_CITY` | 对已有免费电力百分比加成 | Amount（百分比） | 生物圈(+200%) |
| `EFFECT_ADJUST_CITY_REQUIRED_POWER` | 调整所需电力阈值 | Amount | 特定领袖能力 |

### 资源免费获取系列对比

| 效果 | 级别 | 参数 | 计入统计 |
|------|------|------|----------|
| `EFFECT_ADJUST_PLAYER_FREE_RESOURCE_IMPORT` | 玩家 | Amount + ResourceType | 进口 |
| `EFFECT_ADJUST_PLAYER_FREE_RESOURCE_IMPORT_EXTRACTION` | 玩家 | Amount + ResourceType | 开采 |
| `EFFECT_GRANT_PLAYER_FREE_RESOURCE_EXTRACTED` | 玩家 | Amount + ResourceType | 开采 |
| `EFFECT_GRANT_FREE_RESOURCE_EXTRACTED` | 城市 | Amount + ResourceType | 开采 |
| `EFFECT_GRANT_FREE_RESOURCE_IN_CITY` | 城市 | Amount + ResourceType | 不依赖改良 |
| `EFFECT_ADJUST_PLAYER_RESOURCE_ACCUMULATION_MODIFIER` | 玩家 | Amount + 可选ResourceType | 按已改良资源地块数 × Amount 每回合 |

### 战略资源累积系列对比

| 效果 | 范围 | 参数 | 计数方式 |
|------|------|------|----------|
| `EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION` | 所有可累积资源 | Amount | 绝对值（通用） |
| `EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION_FOR_STRATEGIC_DIVERSITY` | 战略资源 | Amount | 按种类多样性 |
| `EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION_SPECIFIC_RESOURCE` | 指定资源 | Amount + ResourceType | 城市级指定 |
| `EFFECT_ADJUST_PLAYER_RESOURCE_ACCUMULATION_MODIFIER` | 指定/全部资源 | Amount + 可选ResourceType | 玩家级（按已改良地块数叠加，非凭空+X） |

### 宜居度与奢侈资源系列

| 效果 | 触发条件 | 参数 |
|------|----------|------|
| `EFFECT_ADJUST_ADD_AMENITY_PER_ADJACENT_LUXURY` | 相邻奢侈资源数量 | AddAmenity |
| `EFFECT_ADJUST_CITY_EXTRA_AMENITY_FOR_LUXURY_DIVERSITY` | 奢侈资源种类多样性 | Amount |
| `EFFECT_ADJUST_OWNED_LUXURY_EXTRA_AMENITIES` | 拥有的每种奢侈资源 | Amount |
| `EFFECT_ADJUST_OWNED_BONUS_RESOURCE_EXTRA_AMENITIES` | 拥有的每种加成资源 | Amount |

### 产出按资源计数

| 效果 | 计数口径 | 参数 | 典型用例 |
|------|----------|------|----------|
| `EFFECT_ADJUST_RESOURCE_YIELD_BY_COUNT` | 每座城市各自的资源种类数 | YieldType + Amount + 可选ResourceType/MinimumCount | 埃塞俄比亚(+1信仰/每种资源) |
| `EFFECT_ADJUST_YIELD_BY_NUMBER_OF_RESOURCES` | 玩家改良的资源种类总数 | YieldType + Amount | 约翰内斯堡(+1生产力/每种资源) |

### 无参数 EffectType（通过 RequirementSetId 指定目标）

- `EFFECT_ADJUST_PLAYER_NO_CAP_RESOURCE` — 资源类型通过 `RequirementSetId` 指定
- `EFFECT_CITY_GRANT_RANDOM_RESOURCE_PRODUCT` — 随机选取，无法指定

### 含直接 ResourceType 参数的 EffectType（修正：此前文档误标为无参数）

- `EFFECT_ADJUST_PLAYER_BAN_RESOURCE` — `ResourceType` 参数直接在 `ModifierArguments` 中指定（非 Requirement）
- `EFFECT_ADJUST_CITY_IGNORE_STRATEGIC_RESOURCE_REQUIREMENTS` — 可选 `Ignore` 参数

### 特殊 Argument Type

- `EFFECT_ADJUST_MOST_ADVANCED_STRATEGIC_RESOURCE_COUNT` 的 `Amount` 参数 Type 为 `ScaleByGameSpeed`，写入 SQL 时 `ModifierArguments` 表的 `Type` 列需填 `ScaleByGameSpeed`（非默认 `ARGTYPE_IDENTITY`）。

### 多 ModifierType 的 EffectType（全部来自官方 DynamicModifiers 表）

- `EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION` — 3 个（`PLAYER_CITIES` + `SINGLE_CITY` + `EMERGENCY_CITIES`）
- `EFFECT_ADJUST_CITY_FREE_POWER` — 2 个（`PLAYER_CITIES` + `SINGLE_CITY`）
- `EFFECT_ADJUST_CITY_RESOURCE_HARVEST_BONUS` — 1 个（`CITY`）
- `EFFECT_ADJUST_CITY_STRATEGIC_RESOURCE_REQUIREMENT_MODIFIER` — 1 个（`CITY`）
- `EFFECT_ADJUST_PLAYER_RESOURCE_STOCKPILE_CAP` — 2 个（`PLAYER` + `PLAYER_CITIES`）
- `EFFECT_GRANT_FREE_RESOURCE_EXTRACTED` — 2 个（`SINGLE_CITY` + `EMERGENCY_CITIES`）
