# modifier-governor -- 总督类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 覆盖 15 个总督相关 EffectType。按字母序排列。

---

### EFFECT_ADJUST_CITY_AMENITIES_FROM_GOVERNORS

根据城市内是否有总督（或其就任状态），调整城市宜居度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_AMENITIES_FROM_GOVERNORS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_AMENITIES_FROM_GOVERNORS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宜居度调整值。正值增加宜居度，负值减少 |

> **溯源**：`BUILDING_GOV_TALL`（谒见厅）— 市政广场一级建筑，"有总督的城市+2宜居度"。`MODIFIER_PLAYER_CITIES_ADJUST_AMENITIES_FROM_GOVERNORS` 用于含总督的城市通用效果；`MODIFIER_SINGLE_CITY_ADJUST_AMENITIES_FROM_GOVERNORS` 用于单城作用域。

---

### EFFECT_ADJUST_CITY_YIELD_MODIFIER_PER_GOVERNOR_TITLE

根据该玩家拥有的总督总头衔数（晋升次数），按百分比提高城市产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_MODIFIER_PER_GOVERNOR_TITLE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | `YIELD_SCIENCE` / `YIELD_CULTURE` / `YIELD_GOLD` / `YIELD_FAITH` / `YIELD_PRODUCTION` / `YIELD_FOOD` |
| `Amount` | **必写** | 整数，每个总督头衔提供的百分比加成。如 `3` = 每个头衔 +3% |

> **溯源**：`TRAIT_LEADER_HWARANG`（善德女王—花郎）— "总督在城市中就职后，每次升级（包括首次升级）都将提供+3%文化值和科技值。"实际运作方式：每个总督头衔（全局）提供 Amount% 产出加成，两个实例分别针对 `YIELD_CULTURE` 和 `YIELD_SCIENCE`，Amount 各为 3。

---

### EFFECT_ADJUST_EXTRA_HEAL_GOVERNOR

大幅提升总督所在城市内单位每回合恢复量（实现快速完全治愈）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_HEAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每回合恢复量。原版 `100` 实现一回合满血 |

> **溯源**：`GOVERNOR_PROMOTION_CARDINAL_LAYING_ON_OF_HANDS`（莫克夏—按手礼）— "总督的宗教单位在此城的单元格中1回合即可完全恢复体力。"Amount=100 即可实现一回合满血。

---

### EFFECT_ADJUST_FEATURE_NO_IMPROVEMENT_APPEAL_GOVERNOR

提升总督所在城市中无改良设施地貌格子的魅力值。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_FEATURE_NO_IMPROVEMENT_APPEAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每格魅力加成值。原版 `1` |

> **溯源**：`GOVERNOR_PROMOTION_MERCHANT_FORESTRY_MANAGEMENT`（瑞娜—林业管理）— "该城市中与未改良地貌相邻的单元格可获得+1魅力。"注意：同一晋升还通过另一个 ModifierType（`MODIFIER_CITY_ADJUST_FEATURE_YIELD`）提供未改良地貌的 +2 金币产出。

---

### EFFECT_ADJUST_GOVERNOR_ALLIANCE_POINTS

提升总督在盟友首都就职时，盟友的同盟点数累积速度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_ALLIANCE_POINTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，同盟点数额外加成值。原版 `2`（折合每回合约 +0.5） |

> **溯源**：`GOVERNOR_PROMOTION_KHASS_ODA_BASHI`（阿玛妮—卡斯-奥达-巴什）— "在外国盟友的首都就职时，此盟友的同盟点数每回合额外增加0.5。"DB 中 Amount 为 2，游戏内引擎自行换算为每回合增量。

---

### EFFECT_ADJUST_GOVERNOR_GRIEVENCE_SCORE

加速衰减其他文明对玩家的不满值（需总督在外国首都就职时生效）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_GRIEVENCE_SCORE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Score` | **必写** | 整数，每周期衰减的不满值点数。原版 `1` |
| `Turns` | **必写** | 整数，衰减周期（回合数）。原版 `1`（即每回合衰减 Score 点不满值） |

> **溯源**：`GOVERNOR_PROMOTION_CAPOU_AGHA`（阿玛妮—卡普阿迦）— "在外国首都就职时，此文明对您的不满每回合多降低1点。"参数 Score=1, Turns=1 即每回合额外衰减 1 点不满值。

> **拼写警告**：EffectType 名称中 `GRIEVENCE` 为 Firaxis 原始拼写错误（正确应为 `GRIEVANCE`）。ModifierType 同为 `MODIFIER_GOVERNOR_ADJUST_GRIEVENCE_SCORE`，使用时需原样引用。

---

### EFFECT_ADJUST_GOVERNOR_IDENTITY_PRESSURE

调整总督对周围城市施加的忠诚度压力值。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_GOVERNOR_IDENTITY_PRESSURE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_GOVERNORS_ADJUST_GOVERNOR_IDENTITY_PRESSURE` | `COLLECTION_PLAYER_GOVERNORS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，忠诚度压力值 |
| `ForeignCities` | `Foreign/Domestic` 二选一**必写** | `1` 表示仅对外国城市施加压力 |
| `DomesticCities` | `Foreign/Domestic` 二选一**必写** | `1` 表示仅对本国城市施加压力 |
| `OncePerCity` | 选写 | `1` 表示每座城市最多生效一次（防止多总督叠加） |

> **溯源**：
> - `GOVERNOR_PROMOTION_GARRISON_COMMANDER`（维克多—驻军司令）— `MODIFIER_GOVERNOR_ADJUST_GOVERNOR_IDENTITY_PRESSURE`，DomesticCities=1，Amount=4。对内施加忠诚度压力。
> - `GOVERNOR_PROMOTION_AMBASSADOR_EMISSARY`（阿玛妮—使者）— `MODIFIER_GOVERNOR_ADJUST_GOVERNOR_IDENTITY_PRESSURE`，ForeignCities=1，Amount=2。对外城施加忠诚度减损。
> - `TRAIT_CIVILIZATION_MAPUCHE_TOQUI`（马普切—托奇）— `MODIFIER_PLAYER_GOVERNORS_ADJUST_GOVERNOR_IDENTITY_PRESSURE`，同时使用 ForeignCities 和 DomesticCities 两个独立实例，各 Amount=4，OncePerCity=1。
>
> 两个 ModifierType 的区分：`MODIFIER_GOVERNOR_ADJUST_GOVERNOR_IDENTITY_PRESSURE`（`COLLECTION_OWNER`）作用于单个总督；`MODIFIER_PLAYER_GOVERNORS_ADJUST_GOVERNOR_IDENTITY_PRESSURE`（`COLLECTION_PLAYER_GOVERNORS`）对所有总督生效，效果可随总督数量叠加（通常搭配 `OncePerCity` 防止堆叠）。

---

### EFFECT_ADJUST_PLAYER_GOVERNOR_FAVOR

调整所有主要文明按其总督头衔数量获得的外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_GOVERNOR_FAVOR` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| （游戏内无活跃实例） | — | Firaxis 在 `Expansion2_Modifiers.xml` 中定义此 ModifierType，但截至 GS 版本末未在任何表（Modifiers / ModifierArguments）中使用。参数名及值格式需自行推测测试 |

> **溯源**：定义于 `DLC/Expansion2/Data/Expansion2_Modifiers.xml` 的 DynamicModifiers 和 Types 中，为世界议会相关 EffectType 预留。与 `EFFECT_ADJUST_PLAYER_POLICY_FAVOR` 并列，同属 `COLLECTION_MAJOR_PLAYERS`。**UNUSED** — 游戏内无实例，使用时需充分测试。

---

### EFFECT_ADJUST_PLAYER_GOVERNOR_POINTS

调整玩家的总督点（总督头衔）数量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GOVERNOR_POINTS` | `COLLECTION_OWNER` |
| `MODIFIER_ALL_PLAYERS_ADJUST_GOVERNOR_POINTS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Delta` | **必写** | 整数，总督点数。如 `1` = +1 总督头衔 |

> **溯源**：
> - `MODIFIER_PLAYER_ADJUST_GOVERNOR_POINTS`（`COLLECTION_OWNER`）：对单一玩家生效。上游来源多样：市政树（`CIVIC_STATE_WORKFORCE` 等每级市政）、`BUILDING_CASA_DE_CONTRATACION`（西印度交易所，Delta=3）、`TRAIT_LEADER_SULEIMAN_GOVERNOR`（苏莱曼—大维齐尔，Delta=1）、伟人（艾琳女王/亚当·斯密）、部落村庄（外交）、大哥伦比亚指挥官伟人等。
> - `MODIFIER_ALL_PLAYERS_ADJUST_GOVERNOR_POINTS`（`COLLECTION_MAJOR_PLAYERS`）：对所有主要文明生效。市政广场一级建筑（谒见厅、祠堂、军阀宝座、外交部、骑士团长礼拜堂、情报局、作战部、皇家学会、国家历史博物馆）建成后，通过 `GameModifiers` 表授予所有玩家 +1 总督头衔（Delta=1）。
>
> **参数名注意**：本效果使用 `Delta` 而非多数效果的 `Amount`。

---

### EFFECT_ADJUST_RESOURCE_POWER_PROVIDED_GOVERNOR

提升总督所在城市中战略资源提供的电力产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_RESOURCE_POWER_PROVIDED_GOVERNOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每种战略资源额外提供的电力值。原版 `1` |

> **溯源**：`GOVERNOR_PROMOTION_RESOURCE_MANAGER_INDUSTRIALIST`（马格努斯—实业家）— "城市中每处战略资源每回合+1生产力。"需注意：此晋升同时包含 4 个 Modifier：3 个 `MODIFIER_BUILDING_YIELD_CHANGE`（分别针对煤/油/核电厂的 +2 产能）和本效果（战略资源电力 +1）。中文描述未提及电力部分，但效果实际生效于电力产出。

---

### EFFECT_GOVERNOR_ADJUST_CITY_COPY_LUXURIES_FOR_IMPORT

总督所在城邦/城市拥有的奢侈资源可复制至本文明（效果为无参数开关型）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_CITY_COPY_LUXURIES_FOR_IMPORT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| **（无参数）** | — | 该 ModifierType 无 ModifierArguments，Modifier 存在即生效 |

> **溯源**：`GOVERNOR_PROMOTION_AMBASSADOR_AFFLUENCE`（阿玛妮—富裕）— "派遣到城邦后将获得该城邦的奢侈品资源。"仅需将 Modifier 挂到总督晋升上即可，无需任何参数。

---

### EFFECT_GOVERNOR_ADJUST_CITY_COPY_STRATEGICS_FOR_IMPORT

总督所在城邦/城市拥有的战略资源可复制至本文明（效果为无参数开关型）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_CITY_COPY_STRATEGICS_FOR_IMPORT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| **（无参数）** | — | 该 ModifierType 无 ModifierArguments，Modifier 存在即生效 |

> **溯源**：`GOVERNOR_PROMOTION_AMBASSADOR_FOREIGN_INVESTOR`（阿玛妮—外国投资者）— "在城邦中就职后将储备该城邦的战略资源。成为宗主国后，获得的战略资源储备将加倍。"仅需将 Modifier 挂到总督晋升上即可，战略资源复制为全自动。

---

### EFFECT_GOVERNOR_ADJUST_CITY_TOKENS_GRANTED

总督所在城市向城邦派遣使者时，额外赠送固定数量的使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_CITY_ENVOYS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，额外赠送的使者数量。原版 `2`（即派遣一个使者时实际获得 1+2=3 个使者席位） |

> **溯源**：`GOVERNOR_PROMOTION_AMBASSADOR_MESSENGER`（阿玛妮—信使）— "可派遣至城邦，效力等同于2名使者。"EffectType 名称中用 `TOKENS`，对应 ModifierType 中用 `ENVOYS`（Token 是内部对使者的通用称呼）。

---

### EFFECT_GOVERNOR_ADJUST_CITY_TOKENS_GRANTED_MODIFIER

总督所在城市向城邦派遣使者时，按百分比增加使者效力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_GOVERNOR_ADJUST_CITY_ENVOYS_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Percent` | **必写** | 整数，百分比加成。原版 `100`（即派遣的使者数量翻倍） |

> **溯源**：`GOVERNOR_PROMOTION_AMBASSADOR_PUPPETEER`（阿玛妮—幕后主脑）— "派遣到城邦后使当地的使者数量加倍。"Percent=100 表示 +100%，即派遣使者数量 x2。参数名为 `Percent` 而非通用的 `Amount`。

---

### EFFECT_GOVERNOR_ADJUST_IDENITITY_PER_TITLE

根据每位总督拥有的头衔数量（晋升次数），按各头衔提供忠诚度压力加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GOVERNORS_ADJUST_IDENTITY_PER_TITLE` | `COLLECTION_PLAYER_GOVERNORS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每个总督头衔提供的忠诚度压力值。原版 `1`（源自 COMMUNICATIONS_OFFICE） |

> **溯源**：`POLICY_COMMUNICATIONS_OFFICE`（政策卡—联络处）— "总督每拥有一次升级，其所在城市每回合的忠诚度便+1。"本 ModifierType 作用于 `COLLECTION_PLAYER_GOVERNORS`，对所有总督生效，每个总督依其头衔数（晋升次数）提供忠诚度加成。

> **拼写警告**：EffectType 名称中 `IDENITITY` 为 Firaxis 原始拼写错误（少了一个 `T`，标准拼写为 `IDENTITY`）。对应 ModifierType 为 `MODIFIER_PLAYER_GOVERNORS_ADJUST_IDENTITY_PER_TITLE`（拼写正确）。使用时 EffectType 需原样引用 `IDENITITY`。

---

## 注意事项

### 拼写问题

| EffectType | 错误 | 说明 |
|-----------|------|------|
| `EFFECT_ADJUST_GOVERNOR_GRIEVENCE_SCORE` | `GRIEVENCE` 少 `A` | 标准拼写为 `GRIEVANCE`。ModifierType 同为 `GRIEVENCE` |
| `EFFECT_GOVERNOR_ADJUST_IDENITITY_PER_TITLE` | `IDENITITY` 少 `T` | 标准拼写为 `IDENTITY`。ModifierType 拼写正确 |

### 命名不一致

- `EFFECT_GOVERNOR_ADJUST_CITY_TOKENS_GRANTED` 和 `EFFECT_GOVERNOR_ADJUST_CITY_TOKENS_GRANTED_MODIFIER` 的 EffectType 用 `TOKENS`，但对应 ModifierType（`MODIFIER_GOVERNOR_ADJUST_CITY_ENVOYS` / `MODIFIER_GOVERNOR_ADJUST_CITY_ENVOYS_MODIFIER`）用 `ENVOYS`。搜索时需注意交叉引用。
- `EFFECT_ADJUST_PLAYER_GOVERNOR_POINTS` 的参数名为 `Delta`，不同于多数效果使用的 `Amount`。
- `EFFECT_GOVERNOR_ADJUST_CITY_TOKENS_GRANTED_MODIFIER` 的参数名为 `Percent`，也不同于通用的 `Amount`。

### 无参数效果（开关型）

`EFFECT_GOVERNOR_ADJUST_CITY_COPY_LUXURIES_FOR_IMPORT` 和 `EFFECT_GOVERNOR_ADJUST_CITY_COPY_STRATEGICS_FOR_IMPORT` 无任何 ModifierArguments。Modifier 一旦挂到总督晋升上即自动生效，无需参数配置。

### CollectionType 差异

- **`COLLECTION_OWNER`**：效果仅对拥有该 Modifier 的单个总督生效。适用于大部分总督晋升效果。
- **`COLLECTION_PLAYER_CITIES`**：效果对玩家的所有城市生效（如 `EFFECT_ADJUST_CITY_AMENITIES_FROM_GOVERNORS` 的全局版、`EFFECT_ADJUST_CITY_YIELD_MODIFIER_PER_GOVERNOR_TITLE`）。
- **`COLLECTION_PLAYER_GOVERNORS`**：效果对玩家拥有的所有总督生效（多总督可叠加）。适用于 `EFFECT_ADJUST_GOVERNOR_IDENTITY_PRESSURE` 和 `EFFECT_GOVERNOR_ADJUST_IDENITITY_PER_TITLE` 的全局版本。
- **`COLLECTION_MAJOR_PLAYERS`**：效果对所有主要文明生效。用于市政广场建筑发放全局总督点（`EFFECT_ADJUST_PLAYER_GOVERNOR_POINTS`）和外交支持（`EFFECT_ADJUST_PLAYER_GOVERNOR_FAVOR`）。

### Identity Pressure 两种 ModifierType 对比

`EFFECT_ADJUST_GOVERNOR_IDENTITY_PRESSURE` 支持两种 ModifierType：

| ModifierType | CollectionType | 叠加 | 典型场景 |
|-------------|----------------|------|---------|
| `MODIFIER_GOVERNOR_ADJUST_GOVERNOR_IDENTITY_PRESSURE` | `COLLECTION_OWNER` | 否 | 单个总督晋升效果（如维克多驻军司令、阿玛妮使者） |
| `MODIFIER_PLAYER_GOVERNORS_ADJUST_GOVERNOR_IDENTITY_PRESSURE` | `COLLECTION_PLAYER_GOVERNORS` | 是 | 文明特性全局效果（如马普切托奇，搭配 OncePerCity 防止堆叠） |

### 未使用效果

`EFFECT_ADJUST_PLAYER_GOVERNOR_FAVOR` 在 `Expansion2_Modifiers.xml` 中定义，Type 已注册，DynamicModifiers 中有条目，但截至 GS 版本末游戏内无任何实例（ModifierArguments 和 Modifiers 表中均无记录）。使用前需自行构造 ModifierArguments 并充分测试。
