# modifier-city — 城市（成长/住房/宜居度/忠诚度/人口）类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

### EFFECT_ADD_PLAYER_UPGRADE_MILITARY_FORMATION_ON_CITY_CONQUEST

占领城市时将单位升级为军团/军队。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_UPGRADE_MILITARY_FORMATION_ON_CITY_CONQUEST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现，无需参数 |

> 仅此一个 EffectType / ModifierType，无需 CollectionType 选择。

---

### EFFECT_ADJUST_CITY_AIR_DEFENSE_BONUS

调整城市对空防御力（防空值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_AIR_DEFENSE_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 防空值（整数）。原版示例值：`25` |

---

### EFFECT_ADJUST_CITY_ALLOWED_INCOMING_REGIONAL_STACKING

允许城市接收多个区域建筑的同类加成叠加（如多个工厂叠加生产力）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_ALLOWED_INCOMING_REGIONAL_STACKING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`。原版示例值：`YIELD_PRODUCTION` |

---

### EFFECT_ADJUST_CITY_ALL_YIELDS_CHANGE

调整城市所有产出（绝对值，六个产出统一调整）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_ALL_YIELDS_CHANGE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 产出值（整数），同时影响六种产出。原版示例值：`1` |

> 与 `EFFECT_ADJUST_CITY_YIELD_CHANGE` 的区别：`_ALL_YIELDS_CHANGE` 一次修改六种产出，`_YIELD_CHANGE` 需指定 `YieldType`。

---

### EFFECT_ADJUST_CITY_ALWAYS_LOYAL

使城市永远保持满忠诚度（不会独立）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_ALWAYS_LOYAL` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AlwaysLoyal` | **必写** | `true` 或 `1` |

---

### EFFECT_ADJUST_CITY_AMENITIES_FROM_CITY_STATES

调整城市从城邦获得的宜居度加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_AMENITIES_FROM_CITY_STATES` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 宜居度值（整数）。原版示例值：`1` |

> 宜居度/住房效果器仅 UI 来源标注不同，实际效果一致，用哪个都一样（`AMENITIES_FROM_CITY_STATES` / `AMENITIES_FROM_GOVERNORS` / `AMENITIES_FROM_GREAT_PEOPLE` / `AMENITIES_FROM_RELIGION` 等均为同类效果器，`HOUSING_FROM_GREAT_PEOPLE` / `HOUSING_PER_DISTRICT` / `HOUSING_FROM_GREAT_WORKS` 等同理）。

---

### EFFECT_ADJUST_CITY_ATTACKS_PER_TURN

调整城市每回合攻击次数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_ATTACKS_PER_TURN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 攻击次数（整数）。原版示例值：`1` |

---

### EFFECT_ADJUST_CITY_CAN_PURCHASE_DISTRICTS

允许城市用金币购买区域。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_CAN_PURCHASE_DISTRICTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `CanPurchase` | **必写** | `1` = 允许金币买区域。原版示例值：`1` |

---

### EFFECT_ADJUST_CITY_COMBAT_BONUS

调整城市战斗力（远程攻击伤害加成）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_CITY_COMBAT_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 战斗力加成值（整数）。原版示例值：`5` |

---

### EFFECT_ADJUST_CITY_CORPS_ARMY_PRODUCTION

降低城市内军团/军队单位的生产费用（折扣）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_CORPS_ARMY_ADJUST_DISCOUNT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 折扣百分比（25 = 打 75 折）。原版示例值：`25` |
| `UnitDomain` | 选写 | `DOMAIN_LAND / DOMAIN_SEA` 等（[MilitaryDomain.txt](../../SOURCES.md#类型与枚举)）。限定生效域，不写则全生效 |

> ⚠️ 打折同时捆绑了直接生产/购买军团军队的能力。即使用此效果提供打折，也会同时解锁该城市的军团/军队生产/购买权限。

---

### EFFECT_ADJUST_CITY_CULTURE_BORDER_EXPANSION

调整城市文化边界扩张速率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_CITIES_CULTURE_BORDER_EXPANSION` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_SINGLE_CITY_CULTURE_BORDER_EXPANSION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 扩张速率值（百分比）。原版示例值：`15`、`20` |

---

### EFFECT_ADJUST_CITY_ENTERTAINMENT

调整城市娱乐值（宜居度来源之一）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_ENTERTAINMENT` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_SINGLE_CITY_ADJUST_ENTERTAINMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 娱乐值（整数，可为负）。原版示例值：`1`、`2` |

---

### EFFECT_ADJUST_CITY_ENTERTAINMENT_FROM_WONDER_ADJACENT_TO_LAKE

从每个相邻湖泊获得宜居度（_ENTERTAINMENT 语义明确为湖泊相邻提供娱乐值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_LAKE_ENTERTAINMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BuildingType` | **必写** | 提供该效果的奇观建筑（如 `BUILDING_HUEY_TEOCALLI`） |

> 仅此一个 ModifierType，实际为休伊神庙专属效果。其他奇观如需类似效果，需另行实现。此效果与 AMENITIES 系列本质不同，不可混用。
>

---

### EFFECT_ADJUST_CITY_EXTRA_ACCUMULATION

调整所有产出的溢出累积上限（用于战略资源等）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_EMERGENCY_CITIES_ADJUST_EXTRA_ACCUMULATION` | `COLLECTION_EMERGENCY_CITIES` |
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_ACCUMULATION` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_EXTRA_ACCUMULATION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 额外累积上限值（整数）。原版示例值：`1` |

---

### EFFECT_ADJUST_CITY_EXTRA_DISTRICTS

增加城市的可建造区域数量上限（突破人口限制）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_EXTRA_DISTRICT` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_EXTRA_DISTRICT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 额外区域数（整数）。原版示例值：`1`、`2` |

---

### EFFECT_ADJUST_CITY_FRIENDLY_COMBAT_BONUS

调整城市对友方单位的战斗支援加成（友军在城市领土内的战斗力）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_CITY_FRIENDLY_COMBAT_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 战斗力加成值（整数）。原版示例值：`5` |

> 完整规则（三种 Context、占位符 `{1_Amount}` / `{Property}`、Preview 链路）见 [modifier-techniques.md 技巧 3](modifier-techniques.md)。

---

### EFFECT_ADJUST_CITY_GOLD_FROM_CITIZENS

调整每个公民产出的金币。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_CITIZEN_GOLD_PER_TURN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每个公民的金币产出（绝对值）。原版示例值：`2` |

> 与 `EFFECT_ADJUST_CITY_YIELD_PER_POPULATION` 指定 `YieldType=YIELD_GOLD` 效果相同。

---

### EFFECT_ADJUST_CITY_GREEN_ENERGY_TOURISM

调整绿色能源带来的旅游业绩加成（百分比）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_GREEN_ENERGY_TOURISM_MODIFIER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比加成（100 = +100%）。原版示例值：`100` |

---

### EFFECT_ADJUST_CITY_GROWTH

调整城市人口增长速度（余粮转化率）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_CITIES_ADJUST_CITY_GROWTH` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_GROWTH` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_GROWTH` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_GROWTH` | `COLLECTION_PLAYER_CAPITAL_CITY` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 增长速率百分比（20 = +20% 速度，-20 = -20% 速度）。原版示例值：`10`、`15`、`20`、`-20` |

---

### EFFECT_ADJUST_CITY_HAPPINESS_YIELD

根据城市幸福度等级提供产出加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_HAPPINESS_YIELD` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`。无多产出实例，不支持逗号分隔 |
| `Amount` | **必写** | 产出值（绝对值） |
| `HappinessType` | **必写** | 触发条件：`HAPPINESS_ECSTATIC`（欣喜若狂）或 `HAPPINESS_HAPPY`（快乐）。无多值实例，不支持逗号分隔 |

> `HappinessType` 为游戏内幸福度等级枚举。原版示例：Happy 时 +10% 科技/文化，Ecstatic 时 +10% 生产力/科技。参考文件：`E:\SteamLibrary\steamapps\common\Sid Meier's Civilization VI\DLC\Babylon\Data\Babylon_GreatPeople.xml`（伊本赫勒敦伟人，每种产出+幸福度各写一条 Modifier）。

---

### EFFECT_ADJUST_CITY_HIT_POINTS

调整城市生命值上限。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_HIT_POINTS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 生命值增量（整数） |

> ⚠️ 无官方使用实例，有效性存疑。

---

### EFFECT_ADJUST_CITY_IDENTITY_PER_CITIZEN

调整每人口产生的忠诚度压力（人口压力系数）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_IDENTITY_PER_CITIZEN` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每人口的忠诚度值（可为负，支持小数）。原版示例值：`0.5`、`-0.5` |

---

### EFFECT_ADJUST_CITY_IDENTITY_PER_TURN

调整每回合产生的忠诚度（直接加减值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_IDENTITY_PER_TURN` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_IDENTITY_PER_TURN` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_TARGET_CITY_GRANT_LOYALTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每回合忠诚度值（整数，可为负）。原版示例值：`-5`、`2`、`3` |

> `MODIFIER_EMERGENCY_TARGET_CITY_GRANT_LOYALTY` 用于紧急事件中给目标城邦/城市加忠诚度。

---

### EFFECT_ADJUST_CITY_IDENTITY_PRESSURE

调整城市对外施加的忠诚度压力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_IDENTITY_PRESSURE_FROM_EMERGENCIES` | `COLLECTION_EMERGENCY_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_IDENTITY_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 忠诚度压力值（可为负）。原版示例值：`-1`（紧急事件用） |

> `MODIFIER_SINGLE_CITY_ADJUST_IDENTITY_PRESSURE` 游戏中无现成 Modifiers 条目，需自行使用。

---

### EFFECT_ADJUST_CITY_INNER_DEFENSE

调整城市内城防御值（内城防御 = 城市本体防御力，非城墙）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_INNER_DEFENSE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 防御值（整数）。原版示例值：`5`、`3` |

> 内城防御 = 城市本体，外城防御 = 城墙防御力。两者独立计算，互不影响。
>

---

### EFFECT_ADJUST_CITY_NATIONAL_PARK_TOURISM

调整国家公园的旅游业绩加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_NATIONAL_PARK_TOURISM` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 旅游业绩值（百分比，100 = +100%）。原版示例值：`100` |

---

### EFFECT_ADJUST_CITY_NO_CULTURE_BORDER_EXPANSION

禁止城市通过文化自动扩张边界。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_NO_CULTURE_BORDER_EXPANSION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果为禁止文化扩张，无需参数 |

---

### EFFECT_ADJUST_CITY_OUTER_DEFENSE

调整城市外层防御值（外城防御 = 城墙耐久度/城防值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_OUTER_DEFENSE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 城墙耐久度值（整数）。原版示例值：`5`、`6`、`10` |

> 内城防御 = 城市本体，外城防御 = 城墙防御力。两者独立计算，互不影响。
>

---

### EFFECT_ADJUST_CITY_POPULATION

增加城市人口（直接加点，非增长率）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_BUILT_CITIES_GRANT_FREE_POPULATION` | `COLLECTION_PLAYER_BUILT_CITIES` |
| `MODIFIER_PLAYER_CITIES_ADD_POPULATION` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_NEAREST_CITY_ADD_POPULATION` | `COLLECTION_UNIT_NEAREST_OWNER_CITY` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 增加的人口数（整数）。原版示例值：`1` |

> `MODIFIER_PLAYER_NEAREST_CITY_ADD_POPULATION` 的 `COLLECTION_UNIT_NEAREST_OWNER_CITY` 用于单位触发效果，给单位最近的城市加人口。

---

### EFFECT_ADJUST_CITY_PREVENT_BYPASS_OUTER_DEFENSES

禁止无视城墙直接攻击城市（需先破城才能攻击市中心）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_PREVENT_BYPASS_OUTER_DEFENSE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现 |

---

### EFFECT_ADJUST_CITY_PREVENT_MELEE_ATTACK_OUTER_DEFENSES

禁止近战单位攻击城墙（只有远程/攻城单位可攻击城墙）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_PREVENT_MELEE_ATTACK_OUTER_DEFENSES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现 |

---

### EFFECT_ADJUST_CITY_PROPERTY

调整城市自定义属性值（键值存储，用于跨效果传递数据或跟踪状态）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_PROPERTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Key` | **必写** | 属性名称（自定义字符串，由 Lua 或后续 Modifier 引用） |
| `Amount` | **必写** | 属性值（整数或实数） |

> 常用于复杂的 Lua 联动或跨回合数据跟踪。`Key` 是自定义字符串，无官方枚举。

---

### EFFECT_ADJUST_CITY_RANGED_STRIKE

调整城市远程攻击力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_RANGED_STRIKE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 远程攻击力值（整数）。原版示例值：`5`、`10` |

---

### EFFECT_ADJUST_CITY_SETTLER_CONSUME_POP

控制生产开拓者时是否消耗人口。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_SETTLER_CONSUME_POPULATION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enabled` | **必写** | `0` = 不消耗人口，`1` = 消耗人口。原版示例值：`0` |

---

### EFFECT_ADJUST_CITY_SIEGE_PROTECTION

调整城市是否免疫围城（围城状态下不减回血）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_SIEGE_PROTECTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Protected` | **必写** | `1` = 免疫围城。原版示例值：`1` |

---

### EFFECT_ADJUST_CITY_SPY_BONUS

调整城市内间谍行动等级加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_ADJUST_SPY_BONUS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_SPY_BONUS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 间谍等级加成（整数，对己方为防御加成，对敌方为进攻加成）。原版示例值：`1`、`3` |

---

### EFFECT_ADJUST_CITY_TOURISM

调整城市旅游业绩产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_TOURISM` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_TOURISM` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ScalingFactor` | **必写** | 旅游业绩缩放系数（百分比，100 = 原始值，300 = 3 倍）。原版示例值：`150`、`200`、`300` |
| `BoostsWonders` | 选写 | `1` = 加成作用于奇观旅游业绩 |
| `GreatWorkObjectType` | 选写 | 限定巨作类型：`GREATWORKOBJECT_WRITING / PORTRAIT / LANDSCAPE / SCULPTURE / RELIGIOUS / ARTIFACT / MUSIC / RELIC`（[GreatWorkObjectType.txt](../../SOURCES.md#类型与枚举)）。可逗号分隔多个 |
| `ImprovementType` | 选写 | 限定改良设施类型，如 `IMPROVEMENT_BEACH_RESORT`。仅对指定改良的旅游业绩生效 |
| `Religious` | 选写 | `1` = 加成作用于宗教旅游业绩 |

> `BoostsWonders`、`GreatWorkObjectType`、`ImprovementType`、`Religious` 为选写参数，可组合使用以限定加成范围。

---

### EFFECT_ADJUST_CITY_TOURISM_LATE_ERAS

调整城市旅游业绩在后续时代的加成（到达某时代后翻倍）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_TOURISM_LATE_ERAS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `MinimumEra` | **必写** | 起始时代，如 `ERA_MODERN`（[EraType.txt](../../SOURCES.md#类型与枚举)） |
| `Modifier` | **必写** | 百分比加成（100 = +100%，即翻倍）。原版示例值：`100` |

---

### EFFECT_ADJUST_CITY_YIELD_CHANGE

调整城市产出（**绝对值**）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_CITIES_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_YIELD_CHANGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`。可逗号连写多个（如 `'YIELD_GOLD, YIELD_FAITH'`），**但仅限直接挂载；嵌套（ATTACH 链内层）必须拆多条 Modifier** |
| `Amount` | **必写** | 产出值（整数或实数）。多个 YieldType 共享同一个 Amount；也可逗号分隔分别指定：`'-2, 3'` |

> ⚠️ **实测（0052 花太郎，2026）：逗号连写在直接挂载时可用（原版黑死病剧本 `YIELD_GOLD, YIELD_FAITH` 实例），但嵌套在 ATTACH 链内层时（`ATTACH → MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE`）只有第一个产出生效，疑似底层嵌套上下文解析问题**。规范：嵌套/ATTACH 内层一律拆成多条 Modifier（每条一个 YieldType；0052 最终形态：`ATTACH_PER_CITY_FOOD_4` / `ATTACH_PER_CITY_PRODUCTION_4` 两个外层 + 各带单一 YieldType 的内层）。
> 与 `EFFECT_ADJUST_CITY_YIELD_MODIFIER` 的区别：`_CHANGE` = 绝对值（+3 科技），`_MODIFIER` = 百分比（+20% 科技）。

---

### EFFECT_ADJUST_CITY_YIELD_MODIFIER

调整城市产出（**百分比加成**）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`。支持逗号分隔写多个：`'YIELD_SCIENCE, YIELD_CULTURE'` |
| `Amount` | **必写** | 百分比值（20 = +20%，-15 = -15%）。多个 YieldType 对应多个值：`'15, 15'` |

> 与 `EFFECT_ADJUST_CITY_YIELD_CHANGE` 的区别：`_CHANGE` = 绝对值（+3 科技），`_MODIFIER` = 百分比（+20% 科技）。原版实例：GreatWarlords_Expansion2.xml 中苏莱曼用 `YIELD_SCIENCE, YIELD_CULTURE`（逗号分隔多产出）。

---

### EFFECT_ADJUST_CITY_YIELD_MODIFIER_FROM_FAITH

根据信仰产出值按百分比加成另一种产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_YIELD_MODIFIER_FROM_FAITH` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 被加成的目标产出类型。无多产出实例，不支持逗号分隔。原版示例值：`YIELD_CULTURE`、`YIELD_SCIENCE` |
| `Amount` | **必写** | 百分比，信仰产出的 N% 加到目标产出。原版示例值：`15`（信仰 15% 加到文化/科技） |

---

### EFFECT_ADJUST_CITY_YIELD_PER_FLOOD

根据泛滥次数提供产出加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_YIELD_FOR_FLOOD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`。无多产出实例，不支持逗号分隔。原版示例值：`YIELD_FAITH` |
| `Amount` | **必写** | 每次泛滥增加的产出值。原版示例值：`1` |

---

### EFFECT_ADJUST_CITY_YIELD_PER_POPULATION

按城市人口提供产出（每人 N 点产出）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_PER_POPULATION` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_YIELD_PER_POPULATION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`。无多产出实例，不支持逗号分隔。原版示例值：`YIELD_CULTURE`、`YIELD_FAITH` |
| `Amount` | **必写** | 每人口产出值（实数，支持小数）。原版示例值：`0.5`、`1`、`2` |

---

### EFFECT_ADJUST_CULTURE_BOMB_CONVERTS_CITY

文化炸弹夺取格子时是否同时占领城市。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_CULTURE_BOMB_CONVERTS_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ConvertsCity` | **必写** | `1` = 文化炸弹可夺取城市。原版示例值：`1` |

---

### EFFECT_ADJUST_PLAYER_BAN_CITY_PRODUCTION

禁止所有城市生产区域建筑（用于特殊状态/危机）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_BANNED_CITY_PRODUCTION` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BanDistrictBuildings` | **必写** | `1` / `true` = 禁止生产所有区域建筑 |
| `DistrictType` | 选写 | 隐藏参数。指定区域类型（如 `DISTRICT_INDUSTRIAL_ZONE`），禁止生产该区域的所有建筑。无官方实例，来源：Modding Companion |
| `BuildingType` | 选写 | ⚠️ 未验证，存疑。理论上指定建筑类型直接禁用。无官方实例 |

---

### EFFECT_ADJUST_PLAYER_CITY_TILES

调整新建立城市时获得的免费格子数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_CITY_TILES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 额外获得的格子数（整数）。原版示例值：`5` |

---

### EFFECT_ADJUST_PLAYER_SKIP_FREE_CITY_STEP

跳过自由城市阶段（刚征服的城市直接归玩家，不经过自由城市状态）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_SKIP_FREE_CITY_STEP` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Skip` | **必写** | `1` = 跳过自由城市阶段。原版示例值：`1` |

---

### EFFECT_ADJUST_PLAYER_TARGET_CITY_SPY_YIELD_PERCENT

间谍在目标城市窃取产出时的百分比加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_TARGET_CITY_SPY_YIELD_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Percent` | **必写** | 窃取百分比（100 = 窃取 100% 目标产出）。原版示例值：`100` |
| `YieldType` | **必写** | 可窃取的产出类型。无多产出实例，不支持逗号分隔。原版示例值：`YIELD_SCIENCE`、`YIELD_CULTURE`、`YIELD_FAITH` |

---

### EFFECT_BECOME_CITY_SUZERAIN

提供足够数量的使者成为此城邦的宗主国，并移除所有其他玩家的使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_UNIT_BECOME_CITY_SUZERAIN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `RemoveOthers` | **必写** | `1` / `true` = 移除所有其他玩家的使者。原版示例值：`True` |

---

### EFFECT_CITY_RECOMMISSION_REACTOR

重启城市核电站（完成项目后恢复核电站运作）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_RECOMMISSION_REACTOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现 |

---

### EFFECT_GRANT_CITY_LOYALTY

一次性给予城市忠诚度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_GRANT_LOYALTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 忠诚度值（整数）。原版示例值：`20` |

> 与 `EFFECT_ADJUST_CITY_IDENTITY_PER_TURN` 的区别：`_GRANT_CITY_LOYALTY` 是一次性给予，`_IDENTITY_PER_TURN` 是每回合持续生效。

---

### EFFECT_GRANT_CITY_ROAD_TO_CAPITAL

自动在城市与首都之间修建道路。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_GRANT_ROAD_TO_CAPITAL` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现 |

---

### EFFECT_GRANT_CITY_TRADING_POST

自动在所有城市建立贸易站。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_GRANT_TRADING_POST` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现 |

---

### EFFECT_GRANT_PRODUCTION_IN_CITY

一次性给予城市生产力（立即推进当前生产项目）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_GRANT_PRODUCTION_IN_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 生产力值（不受游戏速度缩放，固定值）。原版示例值：`1500`（伟人大工最后一锤） |
| `KeepOverflow` | 选写 | `0` = 不保留溢出（默认），`1` = 保留溢出生产力 |

> `Amount` 的类型为 `ScaleByGameSpeed`（在 ModifierArguments 中 Type 列标为 `ScaleByGameSpeed`），原版会适配游戏速度，但新写 Modifier 时需手动适配。

---

### EFFECT_KILL_EMERGENCY_TARGET_SPIES_IN_CITY

消灭紧急事件目标城市内的所有间谍。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_EMERGENCY_CITIES_KILL_ALL_EMERGENCY_TARGET_SPIES` | `COLLECTION_EMERGENCY_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现 |

---

### EFFECT_PURCHASE_PRODUCTION_IN_CITY

花费两倍金币为目标（通常是奇观）投入对应生产力。金币不够也能投，只是无法完成建造。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_PURCHASE_PRODUCTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| 无参数 | — | 效果由 ModifierType 自身实现，与 `EFFECT_GRANT_PRODUCTION_IN_CITY` 搭配使用 |

> 此 EffectType 本身无参数，购买价格（金币）由大伟人单位的 `PurchaseCost` 或 Lua 逻辑决定。通常与 `EFFECT_GRANT_PRODUCTION_IN_CITY` 搭配使用（如伟人大工）。

---

### EFFECT_TREAT_CAPITAL_AS_HOLY_CITY

将首都视为圣城。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_TREAT_CAPITAL_AS_HOLY_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Value` | **必写** | `1` = 视为圣城。原版示例值：`1` |

> 只是视为圣城（有宗教压力等），并非真正的圣城。

---

### EFFECT_TREAT_HOLY_SITE_AS_HOLY_CITY

将圣地区域视为圣城。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_TREAT_HOLY_SITES_AS_HOLY_CITIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Value` | **必写** | `1` = 视为圣城。原版示例值：`1` |

---

## 注意事项

1. **命名一致性**：`EFFECT_ADJUST_CITY_IDENTITY_*` 系列使用 `IDENTITY`（游戏内部命名），但 UI 中显示为"忠诚度（Loyalty）"。注意 `MODIFIER_EMERGENCY_TARGET_CITY_GRANT_LOYALTY` 使用了 `LOYALTY` 而非 `IDENTITY`，属命名不一致但实际效果相同。

2. **`EFFECT_ADJUST_CITY_PROPERTY`**：仅 `MODIFIER_SINGLE_CITY_ADJUST_PROPERTY` 可用（`MODIFIER_PLAYER_CITIES_ADJUST_PROPERTY` 和 `MODIFIER_DISTRICTS_ADJUST_CITY_PROPERTY` 不存在）。`Key` 参数为自定义字符串，无官方枚举约束。使用时需确保 Lua 或后续逻辑能正确读取该 Key。

3. **`EFFECT_GRANT_PRODUCTION_IN_CITY` vs `EFFECT_PURCHASE_PRODUCTION_IN_CITY`**：
   - `_GRANT_` = 给免费生产力（一次性注入进度）
   - `_PURCHASE_` = 允许用金币购买（本身不给生产力，花费两倍金币）
   - 两者通常搭配使用（如伟人大工）。

4. **`EFFECT_ADJUST_PLAYER_BAN_CITY_PRODUCTION`**：`DistrictType` 隐藏参数来源为 Modding Companion，暂无官方实例。`BuildingType` 参数未经验证，有效性存疑。

5. **`EFFECT_ADJUST_CITY_HAPPINESS_YIELD`**：`HappinessType` 枚举值 `HAPPINESS_ECSTATIC` / `HAPPINESS_HAPPY` 无独立 .txt 枚举文件，仅可通过数据库查询或 Modding Companion 校验。
