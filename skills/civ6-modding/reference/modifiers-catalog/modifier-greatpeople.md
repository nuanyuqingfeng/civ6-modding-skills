# modifier-greatpeople — 伟人/巨作类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

### EFFECT_ADD_EXPENDED_GREAT_PERSON_TILES

消耗任意伟人时，城市扩张指定数量的地块。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADD_EXPENDED_GREAT_PERSON_TILES` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 扩张地块数（整数，例：`1`） |

> **溯源**：俄罗斯文明能力「**拉夫拉修道院**」——拥有拉夫拉修道院的城市每消耗一位伟人，城市边界扩张 1 格（`Amount=1`，SubjectRequirementSetId=`REQUIREMENTS_CITY_HAS_LAVRA`）。

---

### EFFECT_ADJUST_ALL_GREAT_WORKS_TOURISM_MODIFIER

所有巨作完成主题化后获得的旅游业绩加成（百分比）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_THEMED_TOURISM` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比值（例：`100` = +100%）。仅对已完成主题化的巨作生效 |

> **溯源**：克里斯蒂娜领袖能力「**北方的弥涅耳瓦**」——拥有 3 个以上巨作槽位的建筑填满后自动主题化，且主题化巨作的旅游业绩 +100%（`Amount=100`）。

---

### EFFECT_ADJUST_ALL_GREAT_WORKS_YIELDS_MODIFIER

所有巨作完成主题化后获得的全部产出加成（百分比）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_THEMED_ALL_YIELDS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比值（例：`100` = +100%）。仅对已完成主题化的巨作生效 |

> **溯源**：克里斯蒂娜领袖能力「**北方的弥涅耳瓦**」——填满巨作槽位自动主题化后，主题化巨作的所有基础产出 +100%（`Amount=100`）。与上一个 Effect 共同构成该能力的完整效果。

---

### EFFECT_ADJUST_CITY_AMENITIES_FROM_GREAT_PEOPLE

按城市中已消耗的伟人数量提供宜居度加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_AMENITIES_FROM_GREAT_PEOPLE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每消耗一位伟人提供的宜居度（整数，例：`1`、`3`） |

> **溯源**：大工程师「**约翰·罗布尔**」激活效果——该城市每消耗一位伟人 +1 宜居度（`Amount=1`）。大工程师「**简·德鲁**」激活效果——该城市每消耗一位伟人 +3 宜居度（`Amount=3`）。两位伟人均作用于当前所在城市，不区分伟人类型。

---

### EFFECT_ADJUST_CITY_GREATWORK_YIELD

城市中特定类型的巨作提供产出（每件巨作累加）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_GREATWORK_YIELD` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_GREATWORK_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `GreatWorkObjectType` | **必写** | 巨作对象类型。`GREATWORKOBJECT_WRITING / PORTRAIT / LANDSCAPE / SCULPTURE / RELIGIOUS / ARTIFACT / MUSIC / RELIC`（[GreatWorkObjectType.txt](../../SOURCES.md#类型与枚举)） |
| `YieldType` | **必写** | 产出类型。`YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`（YieldType.txt） |
| `YieldChange` | **必写** | 每件巨作的基础产出值（整数，与 `ScalingFactor` 配合使用） |
| `ScalingFactor` | **可选** | 产量倍率（整数，除以 100）。例：`ScalingFactor=300` + `YieldChange=2` → 每件巨作 +6 产出。不写时等同于 100（×1） |

> **溯源**：
> - 刚果文明能力「**精神实体**」——雕塑/文物/遗物分别提供 +2 食物、+2 生产力、+4 金币、+1 信仰（`YieldChange` 直接指定，无 `ScalingFactor`）
> - 城邦康提——遗物产出 +50% 信仰（`ScalingFactor=150`，无 `YieldChange`，DLL 内置基础值 × 1.5）
> - 领袖能力「**索格伦**」（松迪亚塔·凯塔）——巨作文字 +4 金币、+2 生产力
> - 领袖能力「**立陶宛联邦**」——遗物 +2 信仰、+2 文化、+4 金币
> - 政策卡「**手工艺品**」（Mod 自定）——多种巨作类型产出的 `ScalingFactor=300`（×3 倍）
> - 创立者信条「**圣物箱**」——遗物产出 ×3 信仰（`ScalingFactor=300`）

---

### EFFECT_ADJUST_CITY_GREAT_PERSON_POINTS_MODIFIER

调整城市伟人点数获取速率（百分比加成，不影响基础值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_INCREASE_GREAT_PERSON_POINT_BONUS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_GREAT_PERSON_POINT_BONUS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比值（例：`100` = +100%，`-50` = -50%） |

> **溯源**：
> - 平伽拉总督晋升「**拨款**」——所在城市伟人点数 +100%（`Amount=100`）
> - 政策卡「**集体主义**」——所有城市伟人点数 -50%（`Amount=-50`）
> 
> 注意：`CITY_INCREASE_GREAT_PERSON_POINT_BONUS` 作用于单城，`PLAYER_CITIES_ADJUST_GREAT_PERSON_POINT_BONUS` 作用于所有城市。此 Effect 调整的是"城市伟人点数总额"的百分比加成，不区分伟人类型。

---

### EFFECT_ADJUST_CITY_HAPPINESS_GREAT_PERSON

按城市中已消耗的特定伟人类型数量，在达到指定幸福度等级后提供额外幸福度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_HAPPINESS_GREAT_PERSON` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 幸福度值（整数，例：`1`、`2`） |
| `GreatPersonClassType` | **必写** | 伟人类型。`GREAT_PERSON_CLASS_SCIENTIST / ENGINEER / ...`（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |
| `HappinessType` | **必写** | 幸福度等级。`HAPPINESS_ECSTATIC / HAPPY / CONTENT / DISPLEASED / UNHAPPY`（HappinessType.txt） |

> **溯源**：苏格兰文明能力「**苏格兰启蒙运动**」——拥有学院的快乐城市每招募一位大科学家 +1 幸福度（`HappinessType=HAPPY`，`Amount=1`）；欣喜若狂时 +2（`HappinessType=ECSTATIC`，`Amount=2`）。拥有工业区的快乐城市每招募一位大工程师同理。用法：仅在该城市已达到指定 `HappinessType` 等级时，按该城市消耗的指定类型伟人数 × Amount 提供额外幸福度。

---

### EFFECT_ADJUST_CITY_HOUSING_FROM_GREAT_PEOPLE

按城市中已消耗的所有伟人数量提供住房（累积型）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_HOUSING_FROM_GREAT_PEOPLE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每消耗一位伟人提供的住房（整数，例：`1`、`2`、`4`） |

> **溯源**：大工程师「**约翰·罗布尔**」激活效果——该城市每消耗一位伟人 +2 住房（`Amount=2`）。大工程师「**简·德鲁**」激活效果——该城市每消耗一位伟人 +4 住房（`Amount=4`）。另有未关联上游的 `GREATPERSON_CITY_HOUSING_SMALL` 提供 +1 住房。不区分伟人类型，累加所有已消耗伟人数量。

---

### EFFECT_ADJUST_CITY_HOUSING_FROM_GREAT_WORKS

按城市中存放的「产品」类巨作数量提供住房。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_HOUSING_FROM_GREAT_WORKS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| — | 无参数 | 效果内置，DLL 硬编码。不传参 |

> **溯源**：此 EffectType 虽名含 `GREAT_WORKS`，实际用于《垄断与公司》游戏模式的产品系统。产品（可可、盐、糖、蜂蜜等）通过 `GreatWorkModifiers` 表挂载到城市，每件产品提供固定住房量（DLL 内置逻辑，不在 ModifierArguments 中传参）。
> 
> 官方用法：`PRODUCT_CITY_GROWTH_HOUSING_COCOA` / `SALT` / `SUGAR` / `HONEY`，均挂载到对应的 `GREATWORK_PRODUCT_*` 巨作类型上，`SubjectStackLimit=1`。

---

### EFFECT_ADJUST_DISTRICT_GREAT_PERSON_POINTS

指定区域提供每回合伟人点数（绝对值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALLIANCE_DISTRICTS_ADJUST_GREAT_POINTS` | `COLLECTION_ALLIANCE_DISTRICTS` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_PLAYER_DISTRICT_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_OWNER` |
| `MODIFIER_SINGLE_CITY_DISTRICTS_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_CITY_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每回合伟人点数（整数，例：`1`、`2`） |
| `GreatPersonClassType` | **可选** | 伟人类型。不写则对所有伟人类型生效（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：
> - 同盟效果——与盟友贸易路线相连的城市区域 +1 伟人点数（`COLLECTION_ALLIANCE_DISTRICTS`）
> - 拜占庭文明能力「**天授规矩**」——圣地 +1 大预言家点数（`GreatPersonClassType=GREAT_PERSON_CLASS_PROPHET`）
> - 万神殿信条「**神圣之光**」——对应区域 +1 对应伟人点数（如学院 +1 大科学家、剧院广场 +1 大作家）
> - 奇观「**神谕**」——该城市各区域 +2 对应伟人点数（`COLLECTION_CITY_DISTRICTS`）
> - 政策卡「**人事管理**」（Mod 自定）——各区域 +1 对应伟人点数

---

### EFFECT_ADJUST_EXTRA_GREAT_WORK_SLOTS

为指定建筑增加巨作槽位。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_GREAT_WORK_SLOTS` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_EXTRA_GREAT_WORK_SLOTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 增加的槽位数（整数，例：`1`、`2`、`3`、`4`） |
| `BuildingType` | **必写** | 目标建筑。`BUILDING_PALACE / AMPHITHEATER / MARKET / MUSEUM_ARTIFACT / BANK / ...`（[BuildingType.txt](../../SOURCES.md#类型与枚举)） |
| `GreatWorkSlotType` | **必写** | 槽位类型。`GREATWORKSLOT_PALACE / WRITING / ARTIFACT / ART / MUSIC / CATHEDRAL / RELIC`（[GreatWorkSlotType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：
> - 英国文明能力「**大英博物馆**」——考古博物馆 +3 文物槽位（`BuildingType=BUILDING_MUSEUM_ARTIFACT`，`GreatWorkSlotType=GREATWORKSLOT_ARTIFACT`，`Amount=3`）
> - 刚果文明能力「**精神实体**」——宫殿 +4 通用槽位（`BuildingType=BUILDING_PALACE`，`GreatWorkSlotType=GREATWORKSLOT_PALACE`，`Amount=4`）
> - 大商人「**乔凡尼·德·美第奇**」激活效果——银行 +2 通用槽位（`BuildingType=BUILDING_BANK`，`GreatWorkSlotType=GREATWORKSLOT_PALACE`，`Amount=2`）
> - 领袖能力「**索格伦**」（松迪亚塔·凯塔）——市场 +2 著作槽位（`BuildingType=BUILDING_MARKET`，`GreatWorkSlotType=GREATWORKSLOT_WRITING`，`Amount=2`）
> 
> `BuildingType` + `GreatWorkSlotType` 组合决定新增槽位挂到哪个建筑的哪种槽位类型。自定义 `GreatWorkSlotType` 需注意 UI 兼容性。

---

### EFFECT_ADJUST_GREAT_PEOPLE_POINTS_PER_KILL

单位击杀敌人后获得伟人点数（固定值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNIT_ADJUST_GREAT_PEOPLE_POINTS_PER_KILL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每次击杀获得的伟人点数（整数，例：`5`、`10`） |
| `GreatPersonClassType` | **可选** | 伟人类型。不写则对所有伟人类型生效（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：法国单位「**帝国卫队**」——击杀敌人 +10 陆军统帅伟人点数（`Amount=10`，`GreatPersonClassType=GREAT_PERSON_CLASS_GENERAL`）。马其顿单位「**伙友骑兵**」——击杀敌人 +5 陆军统帅伟人点数（`Amount=5`）。CollectionType 为 `COLLECTION_OWNER`（玩家），但效果实际作用于玩家的单位，通常配合 `SubjectRequirementSetId` 限定单位类型。

---

### EFFECT_ADJUST_GREAT_PEOPLE_POINTS_PER_KILL_BY_DEFEATED_STRENGTH

击杀敌人后，根据被击杀单位的战斗力按比例获得伟人点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_UNITS_GREAT_PEOPLE_POINTS_PER_KILL_BY_DEFEATED_STRENGTH` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **可选** | 百分比倍率（整数，例：`25` = 25%，`100` = 100%） |
| `GreatPersonClassType` | **可选** | 伟人类型。不写则对所有伟人类型生效（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：
> - 维京单位「**沃林**」——击杀敌人后按战斗力 25% 获得陆军统帅/海军统帅伟人点数（`Amount=25`）
> - 单位能力「**特遣队**」——击杀敌人后按战斗力 100% 获得大科学家/陆军统帅/大工程师伟人点数（`Amount=100`）
> 
> 例：击杀战斗力 40 的敌人，`Amount=25` → 获得 40 × 0.25 = 10 伟人点数。

---

### EFFECT_ADJUST_GREAT_PERSON_GUARANTEE

保证指定时代的指定类型伟人必然出现（不受伟人点数竞争影响，直接"锁定"）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_PERSON_GUARANTEE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `EraType` | **可选** | 时代。`ERA_ANCIENT / CLASSICAL / MEDIEVAL / RENAISSANCE / INDUSTRIAL / MODERN / ATOMIC / INFORMATION / FUTURE`（[EraType.txt](../../SOURCES.md#类型与枚举)）。不写则仅一次性生效 |
| `GreatPersonClassType` | **必写** | 伟人类型（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：
> - 阿拉伯文明能力「**最后的预言家**」——确保在最后一个大预言家被招募时必然获得一位大预言家（只传 `GreatPersonClassType=GREAT_PERSON_CLASS_PROPHET`，不传 `EraType`）
> - 大哥伦比亚领袖能力「**荣耀之战**」——古典到未来每个时代均保证出现一位总指挥（`EraType` 从 `ERA_CLASSICAL` 到 `ERA_FUTURE` 逐条配置）
> 
> 每个时代每种伟人类型只能 guarantee 一次。`EraType` 不传时效果为一次性（仅在当前可招募伟人池中锁定）。

---

### EFFECT_ADJUST_GREAT_PERSON_PATRONAGE_DISCOUNT_PERCENT

降低用信仰/金币购买伟人的赞助费用（百分比折扣）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_PERSON_PATRONAGE_DISCOUNT_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 折扣百分比（整数，例：`20` = 20% 折扣，`25` = 25% 折扣） |
| `YieldType` | **可选** | 限定折扣适用的货币类型。`YIELD_FAITH / YIELD_GOLD`。不写则两种货币均打折 |

> **溯源**：
> - 奇观「**神谕**」——信仰购买伟人费用 -25%（`Amount=25`，`YieldType=YIELD_FAITH`）
> - 领袖能力「**索格伦**」（松迪亚塔·凯塔）——金币购买伟人费用 -20%（`Amount=20`，`YieldType=YIELD_GOLD`）

---

### EFFECT_ADJUST_GREAT_PERSON_POINTS

每回合获得指定类型的伟人点数（绝对值）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_GREAT_PERSON_POINT` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_CITIES_ADJUST_GREAT_PERSON_POINT_BASE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_GREAT_PERSON_POINT` | `COLLECTION_OWNER` |
| `MODIFIER_ALL_PLAYERS_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_ALL_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每回合伟人点数（整数，例：`1`、`2`、`4`） |
| `GreatPersonClassType` | **可选** | 伟人类型。不写则对所有伟人类型生效（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源（广泛使用）**：
> - 政策卡（玩家级 `COLLECTION_OWNER`）：「**文学传统**」→ +2 大作家点数；「**鼓舞**」→ +2 大科学家点数；「**启示**」→ +2 大预言家点数；「**将军**」→ +2 陆军统帅点数；「**航海**」→ +2 海军统帅点数；「**旅行商人**」→ +2 大商人点数；「**不干涉主义**」→ +4 大商人点数；「**军事组织**」→ +4 陆军统帅点数；「**诺贝尔奖**」→ +4 大科学家点数；「**交响曲**」→ +4 大音乐家点数；「**发明**」→ +4 大工程师点数；「**壁画**」→ +2 大艺术家点数
> - 纪念时刻：「**宗教纪念**」（黄金时代）→ +4 大预言家点数（`OwnerRequirementSetId=PLAYER_HAS_GOLDEN_AGE`）
> - 世界奇观「**张掖丹霞**」→ 所有玩家 +2 陆军统帅/大商人伟人点数（`COLLECTION_ALL_PLAYERS`，受邻近区域条件限制）
> - 城邦斯德哥尔摩/博洛尼亚——对应建筑 +1 对应伟人点数（`COLLECTION_PLAYER_CITIES`，每城生效）
> - 政策卡进阶用法（附加建筑条件）：如「**壁画**」+ 艺术博物馆 → +2 大艺术家点数；「**交响曲**」+ 广播中心 → +4 大音乐家点数；「**不干涉主义**」+ 银行 → +2 大商人点数；「**诺贝尔奖**」+ 研究实验室 → +4 大科学家点数
> - 俄罗斯文明能力「**拉夫拉修道院**」（`POINT_BASE`）——神社 +1 大作家、寺庙 +1 大艺术家、三级宗教建筑 +1 大音乐家（基础值加成，`SubjectRequirementSetId` 限定建筑）
> - 万神殿信条「**神圣之光**」——对应建筑 +1 大科学家/大作家点数（`COLLECTION_OWNER`，`SINGLE_CITY` 作用域）
>
> **四者区别**：
> - `COLLECTION_OWNER`（玩家级）：全局加，总额外点数
> - `COLLECTION_PLAYER_CITIES`（每城）：每座城市都加
> - `POINT_BASE`：加的是城市基础伟人点数（受百分比加成影响）
> - `POINT`：直接叠加，不受百分比加成影响

---

### EFFECT_ADJUST_GREAT_PERSON_POINTS_PERCENT

调整伟人点数获取速率（百分比，玩家级）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_PERSON_POINTS_PERCENT` | `COLLECTION_OWNER` |
| `MODIFIER_MAJOR_PLAYERS_ADJUST_GREAT_PERSON_POINTS_PERCENT` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比值（整数，例：`50` = +50%，`100` = +100%） |
| `GreatPersonClassType` | **可选** | 伟人类型。不写则对所有类型生效（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：
> - 世界议会决议「**赞助**」——所有主要文明伟人点数 +100%/+50%/-50%（`COLLECTION_MAJOR_PLAYERS`）
> - 刚果文明能力「**精神实体**」——大艺术家/大音乐家/大商人点数 +50%（`GreatPersonClassType` 分别指定）
>
> 与 `EFFECT_ADJUST_GREAT_PERSON_POINTS` 的区别：前者是绝对值（+N 点/回合），这个是百分比（+N% 速率）。

---

### EFFECT_ADJUST_GREAT_PERSON_POINTS_REFUND_PERCENT

招募伟人后返还部分伟人点数（百分比）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_PERSON_POINTS_REFUND_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 返还百分比（整数，例：`20` = 返还 20% 已消耗伟人点数） |

> **溯源**：巴西领袖能力「**宽宏大量**」（佩德罗二世）——招募伟人后返还 20% 伟人点数（`Amount=20`）。

---

### EFFECT_ADJUST_GREAT_WORK_OBJECT_NO_TOURISM

禁止巨作产生旅游业绩（开关型效果）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_WORK_OBJECT_NO_TOURISM` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `NoTourism` | **必写** | `1` = 禁止产生旅游业绩 |

> **溯源**：世界议会决议「**文化遗产组织**」——所有巨作的旅游业绩归零（`NoTourism=1`）。这是决议 A 面的效果。与 `EFFECT_ADJUST_GREAT_WORK_OBJECT_TOURISM_MODIFIER`（B 面效果）为同一决议的两种表决结果。

---

### EFFECT_ADJUST_GREAT_WORK_OBJECT_TOURISM_MODIFIER

调整巨作旅游业绩加成（百分比）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREAT_WORK_OBJECT_TOURISM` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比值（例：`100` = +100%） |

> **溯源**：世界议会决议「**文化遗产组织**」——所有巨作旅游业绩 +100%（`Amount=100`）。这是决议 B 面的效果（A 面为完全禁止旅游业绩）。不区分巨作类型，对所有巨作全局生效。

---

### EFFECT_ADJUST_IDENTITY_PER_TURN_FROM_NEARBY_GREAT_WORKS

每回合按附近外国城市的巨作数量提供忠诚度压力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_IDENTITY_PER_TURN_FROM_NEARBY_GREAT_WORKS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每件巨作提供的忠诚度压力值（整数，例：`1`） |
| `ForeignCities` | **可选** | `1` = 仅计算外国城市巨作 |
| `DomesticCities` | **可选** | `1` = 仅计算本国城市巨作 |

> **溯源**：埃莉诺领袖能力「**爱之法庭**」——附近外国城市的每件巨作 -1 忠诚度/回合（`Amount=1`，`ForeignCities=1`）。`ForeignCities` 和 `DomesticCities` 互斥（二选一）。

---

### EFFECT_ADJUST_LOYALTY_FROM_GREAT_WORKS_CITIZENS

按城市中巨作数量调整忠诚度压力（从公民产出）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_ADJUST_LOYALTY_FROM_GREAT_WORKS_CITIZENS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | 按需 | 忠诚度修正值（整数）。效果由 DLL 内置逻辑决定 |

> **溯源**：此 EffectType 在官方 XML 中仅定义了 `DynamicModifiers` 条目，**无任何官方 Modifier 使用**。效果逻辑由 DLL 硬编码，参数需通过 DLL 源码或实验确定。ModifierType 名含双 `ADJUST_ADJUST`（官方命名冗余）。实际使用时建议先检查官方后续 DLC/游戏模式是否有使用该 EffectType 的实例。

---

### EFFECT_ADJUST_NO_GREAT_PERSON_POINTS

禁止获得伟人点数（开关型效果）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_NO_GREAT_PERSON_POINTS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| — | 无参数 | 效果为开关：有该 Modifier 则伟人点数产出归零 |

> **溯源**：世界议会决议「**赞助**」——表决结果可使所有主要文明伟人点数清零（无参数，纯开关逻辑）。与同一决议的 `EFFECT_ADJUST_GREAT_PERSON_POINTS_PERCENT` 为三种表决结果中的一种。

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_GREAT_PERSON_EARNED

每次获得伟人时额外获得时代得分。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_GREAT_PERSON_EARNED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每获得一位伟人额外获得的时代得分（整数，例：`1`） |

> **溯源**：纪念时刻「**航空纪念**」——非黄金时代期间，每招募一位伟人 +1 时代得分（`Amount=1`，`SubjectRequirementSetId` 限定非黄金时代和允许纪念任务中）。用于鼓励追赶的文明通过招募伟人提升时代得分。

---

### EFFECT_ADJUST_PLAYER_FREE_GREAT_PERSON_POINTS

每回合获得免费伟人点数（绝对值），可自由分配到任意伟人类型。不受城市建筑产出的伟人点数加成影响。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FREE_GREAT_PERSON_POINTS` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_PLAYERS_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每回合伟人点数（整数，例：`100`） |

> **溯源**：
> - 大科学家「**阿尔弗雷德·诺贝尔**」激活效果——每回合 +100 伟人点数，可自由分配到任意伟人类型（`Amount=100`）
> - 紧急事件「**世界博览会**」——第一名获得每回合 +100 伟人点数（`COLLECTION_EMERGENCY_PLAYERS`，`SubjectRequirementSetId` 限定第一名玩家）

---

### EFFECT_ADJUST_PLAYER_GREATPERSON_FAVOR_MODIFIER

招募伟人时获得额外外交支持（百分比）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREATPERSON_FAVOR_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 百分比值（整数，例：`50` = +50% 外交支持产出） |

> **溯源**：瑞典文明能力「**诺贝尔奖**」——招募伟人时额外获得 +50% 外交支持（`Amount=50`）。注意这是调整外交支持产出量的百分比，而非每次招募固定获得 N 点。

---

### EFFECT_ADJUST_PLAYER_YIELD_MODIFIER_PER_EARNED_GREAT_PERSON

每招募一位伟人，获得特定产出百分比加成（累积型）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_MODIFIER_PER_EARNED_GREAT_PERSON` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每位伟人提供的百分比加成（整数，例：`2` = 每招募一位伟人 +2% 产出） |
| `YieldType` | **必写** | 产出类型。`YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`（YieldType.txt） |

> **溯源**：城邦「**安塔那那利佛**」宗主国加成——每招募一位伟人 +2% 文化产量（`Amount=2`，`YieldType=YIELD_CULTURE`）。效果为累积型：招募 N 位伟人后 = +N × Amount %。不区分伟人类型。

---

### EFFECT_ADJUST_UNIT_GREAT_PERSON_CHARGES

调整伟人单位的使用次数（充能数）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNITS_ADJUST_GREAT_PERSON_CHARGES` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 增加的充能数（整数，例：`1`） |

> **溯源**：奇观「**摩索拉斯王陵墓**」——大工程师 +1 使用次数（`Amount=1`，`SubjectRequirementSetId=UNIT_IS_ENGINEER` 限定仅大工程师生效）。注意此 EffectType 作用于玩家所有单位的充能，通常配合 `SubjectRequirementSetId` 限定特定伟人类型。

---

### EFFECT_GRANT_BOOST_WITH_GREAT_PERSON

招募指定类型伟人时，为所有玩家（或仅自己）提供随机科技尤里卡。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_BOOST_WITH_GREAT_PERSON` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `GreatPersonClass` | **必写** | 伟人类型（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)）。**注意：参数名为 `GreatPersonClass`（非 `GreatPersonClassType`）** |
| `TechBoost` | **必写** | `0` = 市政尤里卡，`1` = 科技尤里卡 |
| `OtherPlayers` | **可选** | `1` = 为所有其他玩家也提供尤里卡 |

> **溯源**：奇观「**大图书馆**」——其他玩家招募大科学家时，你获得一个随机科技尤里卡（`GreatPersonClass=GREAT_PERSON_CLASS_SCIENTIST`，`OtherPlayers=1`，`TechBoost=1`）。注意：`OtherPlayers=1` 时，效果在其他玩家招募伟人时触发，但尤里卡发放给**你自己**。

---

### EFFECT_GRANT_GREAT_PERSON_CLASS_IN_CITY

在城市中生成一个指定类型的伟人。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_GRANT_GREAT_PERSON_CLASS_IN_CITY` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_CAPITAL_CITIES_GRANT_GREAT_PERSON_CLASS_IN_CITY` | `COLLECTION_EMERGENCY_CAPITAL_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 生成伟人数量（整数，例：`1`） |
| `GreatPersonClassType` | **必写** | 伟人类型（[GreatPersonClassType.txt](../../SOURCES.md#类型与枚举)） |

> **溯源**：
> - 奇观「**巨石阵**」——免费获得一位大预言家（`Amount=1`，`GreatPersonClassType=GREAT_PERSON_CLASS_PROPHET`，受 `STONEHENGE_PROPHET_REQUIREMENTS` 限制：仅当玩家可招募大预言家时生效）
> - 紧急事件「**诺贝尔和平奖**」——前三名分别在首都获得大音乐家/大科学家/大工程师/大艺术家（`COLLECTION_EMERGENCY_CAPITAL_CITIES`，搭配名次条件）
> 
> 生成的伟人从当前可用的伟人池中随机抽取。若该类型无可招募的伟人，则生成失败。

---

### EFFECT_GRANT_PLAYER_RELIGIOUS_PRESSURE_GREAT_PERSON_ACTIVATED

激活伟人时，向周围城市施加宗教压力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_RELIGIOUS_PRESSURE_GREAT_PERSON_ACTIVATED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 宗教压力值（整数，例：`400`） |

> **溯源**：城邦「**梵蒂冈城**」宗主国加成——激活伟人时，向 10 格内所有城市施加 400 宗教压力（`Amount=400`）。用于宗教胜利辅助，每次激活任意伟人均触发。

---

### EFFECT_GRANT_PLAYER_SPECIFIC_TECH_BOOST_GREAT_PERSON

激活伟人时，为该玩家提供指定科技的尤里卡（Eureka），可在已有尤里卡时直接完成科技。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_SPECIFIC_TECH_BOOST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `TechType` | **必写** | 目标科技。`TECH_WRITING / MATHEMATICS / ENGINEERING / ROCKETRY / ...`（完整列表查数据库 Technologies 表） |
| `GrantTechIfBoosted` | **可选** | `1` = 科技已有尤里卡时直接授予该科技（跳过尤里卡，直接完成） |

> **溯源**：
> - 大科学家「**爱达·勒芙蕾丝**」——激活后获得「计算机」科技的尤里卡（`TechType=TECH_COMPUTERS`）
> - 大科学家「**毕昇**」——激活后获得「印刷术」科技的尤里卡（`TechType=TECH_PRINTING`）
> - 大科学家「**欧几里得**」——激活后获得「数学」科技的尤里卡（`TechType=TECH_MATHEMATICS`）
> - 大科学家「**罗伯特·哥达德**」——激活后获得「火箭学」科技的尤里卡（`TechType=TECH_ROCKETRY`）
> - 大科学家「**德米特里·门捷列夫**」——激活后获得「化学」科技的尤里卡（`TechType=TECH_CHEMISTRY`）
> - 大科学家「**张衡**」——激活后获得「数学」「天文导航」「工程」的尤里卡（三行参数，且 `GrantTechIfBoosted=1`：若科技已有尤里卡则直接完成科技）
> - 纪念时刻「**航空纪念**」——黄金时代时获得指定科技的尤里卡（`OwnerRequirementSetId=PLAYER_HAS_GOLDEN_AGE_*`）
> - 腓尼基文明能力「**地中海殖民地**」——获得「文字」科技的尤里卡（`TechType=TECH_WRITING`）
>
> 可多行指定多个 `TechType`（每个 `TechType` 一行参数）。若科技已完成，则跳过。与 `EFFECT_GRANT_BOOST_WITH_GREAT_PERSON` 的区别：后者发放随机尤里卡槽位，此 Effect 指定具体科技。

---

### EFFECT_GRANT_YIELD_PER_GREAT_WORK_IN_CITY

城市中每件指定类型的巨作提供一次性产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_GRANT_YIELD_PER_GREAT_WORK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 每件巨作提供的一次性产出值（整数，例：`350`） |
| `GreatWorkObjectType` | **必写** | 巨作对象类型。`GREATWORKOBJECT_ARTIFACT / WRITING / ...`（[GreatWorkObjectType.txt](../../SOURCES.md#类型与枚举)） |
| `YieldType` | **必写** | 产出类型。`YIELD_SCIENCE / CULTURE / GOLD / FAITH / PRODUCTION / FOOD`（YieldType.txt） |

> **溯源**：大科学家「**玛丽·利基**」激活效果——所在城市每件文物提供 350 科技（`Amount=350`，`GreatWorkObjectType=GREATWORKOBJECT_ARTIFACT`，`YieldType=YIELD_SCIENCE`）。注意：此为**一次性产出**（Grant），非每回合持续产出。触发时机为伟人激活的瞬间，数量按城市当时拥有的指定巨作数量计算。

---

## 注意事项

### 参数命名不一致

| 问题 | 详情 |
|------|------|
| `GreatPersonClass` vs `GreatPersonClassType` | 仅 `EFFECT_GRANT_BOOST_WITH_GREAT_PERSON` 使用参数名 `GreatPersonClass`（不带 `Type` 后缀），其余所有 Effect 均用 `GreatPersonClassType`。写参数时务必注意区分 |
| `MODIFIER_PLAYER_CITIES_ADJUST_ADJUST_LOYALTY...` | 官方 ModifierType 名含双 `ADJUST` 冗余，为官方命名错误，使用时按原名填写 |

### 相似效果对比

| 效果 A | 效果 B | 区别 |
|--------|--------|------|
| `EFFECT_ADJUST_GREAT_PERSON_POINTS` | `EFFECT_ADJUST_GREAT_PERSON_POINTS_PERCENT` | 前者是绝对值（+N 点/回合），后者是百分比（+N% 速率） |
| `EFFECT_ADJUST_GREAT_PERSON_POINTS` | `EFFECT_ADJUST_PLAYER_FREE_GREAT_PERSON_POINTS` | 前者受城市建筑加成影响，后者是"自由点数"（不受建筑加成），可自由分配到任意伟人类型 |
| `EFFECT_ADJUST_GREAT_PEOPLE_POINTS_PER_KILL` | `EFFECT_ADJUST_GREAT_PEOPLE_POINTS_PER_KILL_BY_DEFEATED_STRENGTH` | 前者是固定值，后者按被击杀单位战斗力比例 |
| `EFFECT_ADJUST_GREAT_WORK_OBJECT_NO_TOURISM` | `EFFECT_ADJUST_GREAT_WORK_OBJECT_TOURISM_MODIFIER` | 前者是完全屏蔽旅游业绩（开关），后者是调整百分比（同属世界议会「文化遗产组织」决议的 A/B 面） |
| `EFFECT_GRANT_BOOST_WITH_GREAT_PERSON` | `EFFECT_GRANT_PLAYER_SPECIFIC_TECH_BOOST_GREAT_PERSON` | 前者发放随机尤里卡槽位，后者指定具体科技（并可选择直接完成） |
| `EFFECT_ADJUST_GREAT_PERSON_POINTS`（玩家级） | `EFFECT_ADJUST_DISTRICT_GREAT_PERSON_POINTS` | 前者作用于玩家全局，后者作用于特定区域（需 `SubjectRequirementSetId` 限定区域类型） |

### 无 Modifier 实例的 EffectType

以下 EffectType 在官方 XML 中仅定义了 DynamicModifiers 条目，无任何实际 Modifier 使用实例：

| EffectType | 说明 |
|------------|------|
| `EFFECT_ADJUST_LOYALTY_FROM_GREAT_WORKS_CITIZENS` | 仅 `DynamicModifiers` 中定义，无实际使用。ModifierType 名含双 `ADJUST` 冗余。DLL 硬编码逻辑 |

### 特殊参数说明

| 参数 | 所属 Effect | 说明 |
|------|------------|------|
| `ScalingFactor` | `EFFECT_ADJUST_CITY_GREATWORK_YIELD` | 倍率参数，除以 100 后乘以 `YieldChange`。`ScalingFactor=300` + `YieldChange=2` = 每件巨作 +6 产出。不写时默认 100（×1） |
| `NoTourism` | `EFFECT_ADJUST_GREAT_WORK_OBJECT_NO_TOURISM` | 开关型布尔参数，设为 `1` 即完全屏蔽旅游业绩 |
| `GrantTechIfBoosted` | `EFFECT_GRANT_PLAYER_SPECIFIC_TECH_BOOST_GREAT_PERSON` | 若目标科技已有尤里卡，设为 `1` 则直接完成该科技 |
| `GreatPersonClass` | `EFFECT_GRANT_BOOST_WITH_GREAT_PERSON` | 注意尾部无 `Type` 后缀，与其余所有 Effect 不同 |

### 枚举引用索引

| 枚举文件 | 在此文件中被引用的 EffectType 数量 |
|----------|----------------------------------|
| [GreatPersonClassType 查询依据](../../SOURCES.md#类型与枚举) | 11 个 EffectType |
| [GreatWorkObjectType 查询依据](../../SOURCES.md#类型与枚举) | 3 个 EffectType |
| [GreatWorkSlotType 查询依据](../../SOURCES.md#类型与枚举) | 1 个 EffectType |
| [BuildingType 查询依据](../../SOURCES.md#类型与枚举) | 1 个 EffectType |
| [EraType 查询依据](../../SOURCES.md#类型与枚举) | 1 个 EffectType |
| 数据库 Yields 表 | 4 个 EffectType |
