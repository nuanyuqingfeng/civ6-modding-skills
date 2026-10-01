# modifier-religion -- 宗教类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 覆盖 42 个宗教相关 EffectType。按字母序排列，每个效果均从游戏数据库溯源至上游主体（信条/特质/建筑/政策/总督/城邦等）。

---

### EFFECT_ADD_BELIEF

为玩家新增一条信条（直接添加到宗教信条列表中）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADD_BELIEF` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BeliefType` | **必写** | `BELIEF_CHURCH_PROPERTY` 等，引用 [Beliefs.BeliefType] |

> **溯源**：DynamicModifiers 定义于 `Modifiers.xml`，游戏中无活跃 DB 实例。效果是直接给玩家挂载一条信条，与宗教信条选择面板解耦，常用于文明/领袖特质绕过正常信条获取流程。

---

### EFFECT_ADD_PLAYER_BELIEF_YIELD

根据信念产出模式，为拥有该宗教的玩家添加产出（与 `EFFECT_ADD_RELIGIOUS_BELIEF_YIELD` 共享同一套 `BeliefYieldType` 体系，但参数更简洁）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADD_PLAYER_BELIEF_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出量 |
| `BeliefYieldType` | **必写** | `BELIEF_YIELD_PER_CITY` / `BELIEF_YIELD_PER_FOLLOWER` / `BELIEF_YIELD_PER_FOREIGN_FOLLOWER` / `BELIEF_YIELD_PER_DISTRICT` / `BELIEF_YIELD_PER_FOREIGN_CITY` / `BELIEF_YIELD_PER_CITY_WITH_WONDER` |
| `PerXItems` | **必写** | 整数，每 X 个单位触发一次（如每 1 个外国城市、每 4 个信徒） |
| `YieldType` | **必写** | `YIELD_FAITH` / `YIELD_GOLD` / `YIELD_CULTURE` / `YIELD_SCIENCE` 等，引用 [Yields.YieldType] |

> **溯源**：阿拉伯 — 最后的预言家（`TRAIT_CIVILIZATION_LAST_PROPHET`）— 每个信奉阿拉伯宗教的外国城市 +1 科技值（`BeliefYieldType=BELIEF_YIELD_PER_FOREIGN_CITY`, `Amount=1`, `YieldType=YIELD_SCIENCE`）。与 `EFFECT_ADD_RELIGIOUS_BELIEF_YIELD` 类似但参数模型不同，此版本无 `DistrictType` 参数。

---

### EFFECT_ADD_RELIGIOUS_BELIEF_YIELD

为拥有该宗教的玩家添加一种信条产出，覆盖全部六种 `BELIEF_YIELD_*` 模式。是信条产出体系中最核心的 EffectType。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADD_RELIGIOUS_BELIEF_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出量 |
| `BeliefYieldType` | **必写** | `BELIEF_YIELD_PER_CITY` / `BELIEF_YIELD_PER_FOLLOWER` / `BELIEF_YIELD_PER_FOREIGN_FOLLOWER` / `BELIEF_YIELD_PER_DISTRICT` / `BELIEF_YIELD_PER_FOREIGN_CITY` / `BELIEF_YIELD_PER_CITY_WITH_WONDER` |
| `DistrictType` | `PER_DISTRICT` 时**必写** | `DISTRICT_HOLY_SITE` / `DISTRICT_THEATER` / `DISTRICT_CAMPUS` / `DISTRICT_COMMERCIAL_HUB`，引用 [Districts.DistrictType] |
| `PerXItems` | **必写** | 整数，每 X 个单位触发一次（如每 1 个城市、每 4 个信徒） |
| `YieldType` | **必写** | `YIELD_FAITH` / `YIELD_GOLD` / `YIELD_CULTURE` / `YIELD_SCIENCE` 等，引用 [Yields.YieldType] |

> **溯源**（DB 中 17 个活跃实例，均为信条）：
> - **教会财产**（`BELIEF_CHURCH_PROPERTY`，创立者信条）— 每座信奉此宗教的城市 +2 金币（`PER_CITY`）
> - **什一税**（`BELIEF_TITHE`，创立者信条）— 每 4 个信徒 +1 金币（`PER_FOLLOWER`，原版）；每座城市 +3 金币（`PER_CITY`，DLC 调整版）
> - **普世教会**（`BELIEF_WORLD_CHURCH`，创立者信条）— 其他文明每 5 个信徒 +1 文化值（`PER_FOREIGN_FOLLOWER`）；每 4 个信徒 +1 文化值（`PER_FOLLOWER`）
> - **跨文化对话**（`BELIEF_CROSS_CULTURAL_DIALOGUE`，创立者信条）— 其他文明每 5 个信徒 +1 科技值（`PER_FOREIGN_FOLLOWER`）；每 4 个信徒 +1 科技值（`PER_FOLLOWER`）
> - **朝圣**（`BELIEF_PILGRIMAGE`，创立者信条）— 每个外国信奉城市 +2 信仰值（`PER_FOREIGN_CITY`）；每座城市 +2 信仰值（`PER_CITY`）
> - **民间宗教团**（`BELIEF_LAY_MINISTRY`，信徒信条）— 圣地 +1 信仰值（`PER_DISTRICT`, `DISTRICT_HOLY_SITE`）；剧院广场 +1 文化值（`PER_DISTRICT`, `DISTRICT_THEATER`）
> - **管理工作**（`BELIEF_STEWARDSHIP`，信徒信条）— 学院 +1 科技值（`PER_DISTRICT`, `DISTRICT_CAMPUS`）；商业中心 +1 金币（`PER_DISTRICT`, `DISTRICT_COMMERCIAL_HUB`）
> - **神圣之地**（`BELIEF_SACRED_PLACES`，信徒信条）— 拥有奇观的城市 +2 信仰值/文化值/科技值/金币（`PER_CITY_WITH_WONDER`，四种产出各一个 Modifier）

---

### EFFECT_ADD_RELIGIOUS_BUILDING

允许拥有该宗教的玩家在圣地中建造指定的宗教建筑。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADD_RELIGIOUS_BUILDING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BuildingType` | **必写** | `BUILDING_CATHEDRAL` / `BUILDING_GURDWARA` / `BUILDING_MEETING_HOUSE` / `BUILDING_MOSQUE` / `BUILDING_PAGODA` / `BUILDING_SYNAGOGUE` / `BUILDING_WAT` / `BUILDING_STUPA` / `BUILDING_DAR_E_MEHR`，引用 [Buildings.BuildingType] |

> **溯源**（DB 中 9 个实例，均为崇拜信条 `BELIEF_CLASS_WORSHIP`）：
> - **大教堂**（`BELIEF_CATHEDRAL`）— +3 信仰值，1 个宗教艺术槽位
> - **谒师所**（`BELIEF_GURDWARA`）— +3 信仰值，+2 食物
> - **礼拜堂**（`BELIEF_MEETING_HOUSE`）— +3 信仰值，+2 生产力
> - **清真寺**（`BELIEF_MOSQUE`）— +3 信仰值，传教士/使徒传播次数 +1
> - **宝塔**（`BELIEF_PAGODA`）— +3 信仰值，+1 住房
> - **犹太教堂**（`BELIEF_SYNAGOGUE`）— +5 信仰值
> - **佛寺**（`BELIEF_WAT`）— +3 信仰值，+2 科技值
> - **窣堵波**（`BELIEF_STUPA`）— +3 信仰值，+1 宜居度
> - **拜火神庙**（`BELIEF_DAR_E_MEHR`）— +3 信仰值，每个时代额外 +1 信仰值

---

### EFFECT_ADD_RELIGIOUS_BUILDING_MULTIPLIER

对宗教建筑的产出施加百分比倍率加成（用于特质而非信条）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADD_RELIGIOUS_BUILDING_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Founder` | **可选** | `1` = 仅对创立者信条相关建筑生效，`0` 或不写 = 对所有相关建筑生效 |
| `Multiplier` | **必写** | 整数（百分比），产出倍率加成。`10` = +10% |
| `YieldType` | **必写** | `YIELD_CULTURE` / `YIELD_FAITH` / `YIELD_SCIENCE`，引用 [Yields.YieldType] |

> **溯源**：萨拉丁 — 正义的信仰（`TRAIT_LEADER_RIGHTEOUSNESS_OF_FAITH`）— 宗教建筑的文化值/信仰值/科技值 +10%（三个 Modifier，各对一种产出）。

---

### EFFECT_ADD_RELIGIOUS_UNIT

允许拥有该宗教的玩家训练指定的宗教单位。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADD_RELIGIOUS_UNIT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `UnitType` | **必写** | `UNIT_WARRIOR_MONK` 等，引用 [Units.UnitType] |

> **溯源**：武僧（`BELIEF_WARRIOR_MONKS`，信徒信条）— 可花费信仰值训练武僧，中世纪陆地战斗单位，拥有独特晋升树，只能在有寺庙的城市购买。

---

### EFFECT_ADJUST_CITY_AMENITIES_FROM_RELIGION

调整城市因拥有宗教而获得的宜居度加成（基础为每个宗教 +1 宜居度）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_AMENITIES_FROM_RELIGION` | `COLLECTION_OWNER` |
| `MODIFIER_CITY_DISTRICTS_ADJUST_CITY_AMENITIES_FROM_RELIGION` | `COLLECTION_CITY_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | `SINGLE_CITY` 版本**必写** | 整数，宜居度加成量。`CITY_DISTRICTS` 版本无此参数，按区域自动计算 |

> **溯源**（DB 中 2 个实例）：
> - **禅修**（`BELIEF_ZEN_MEDITATION`，信徒信条）— 拥有 2 个特色区域的城市 +1 宜居度（`SINGLE_CITY`, `Amount=1`）
> - **Podenco 社区**（`DISTRICT_NEIGHBORHOOD` 上的 `MODIFIER_PODENCO_NEIGHBORHOOD_AMENITIES`）— 社区 +3 宜居度（`SINGLE_CITY`, `Amount=3`，Siqi Mod 扩展内容）

---

### EFFECT_ADJUST_CITY_RELIGION_EXTRA_PROMOTIONS

城市中训练或购买的宗教单位获得额外免费晋升次数。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_RELIGION_EXTRA_PROMOTIONS` | `COLLECTION_OWNER` |
| `MODIFIER_SINGLE_CITY_RELIGION_EXTRA_PROMOTIONS_SCENARIO` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | 主版本**必写** | 整数，额外晋升次数。`SCENARIO` 版本无参数 |

> **溯源**：
> - 主版本 — **红衣主教：守护圣人**（`GOVERNOR_PROMOTION_CARDINAL_PATRON_SAINT`）— 此城训练的使徒/武僧初始获得 1 次额外晋升（`Amount=1`）
> - `_SCENARIO` 变体 — DB 无实例，专为剧本模式保留，不设参数

---

### EFFECT_ADJUST_CITY_RELIGION_IGNORE_COMBAT

该城市的宗教单位免疫敌方宗教单位的神学战斗（无法被攻击）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_RELIGION_IGNORE_COMBAT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用免疫 / `0` 禁用 |

> **溯源**：**红衣主教：神之堡垒**（`GOVERNOR_PROMOTION_CARDINAL_CITADEL_OF_GOD`）— 此总督所在城市免疫外教的战斗和压力（与 `IGNORE_PRESSURE` 成对使用，共同实现"宗教禁区"城市）。

---

### EFFECT_ADJUST_CITY_RELIGION_IGNORE_PRESSURE

该城市免疫外来宗教压力（其他宗教无法被动传播至此城）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_RELIGION_IGNORE_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用免疫 / `0` 禁用 |

> **溯源**：**红衣主教：神之堡垒**（`GOVERNOR_PROMOTION_CARDINAL_CITADEL_OF_GOD`）— 与 `IGNORE_COMBAT` 成对挂载，该总督所在城市成为宗教安全区。

---

### EFFECT_ADJUST_CITY_RELIGION_ON_CAPTURE

单位攻占城市时，强制城市转换为占领方的主流宗教。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_UNIT_ADJUST_CITY_ON_CAPTURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用 |

> **溯源**：**征服者**（`ABILITY_CONQUISTADOR`，西班牙特色单位能力）— 攻占城市时，该城市自动转换为西班牙主流宗教。

---

### EFFECT_ADJUST_CITY_RELIGION_PRESSURE

调整城市输出的宗教压力值（基准为 100）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_RELIGION_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，城市压力输出值变化量（`100` = 基础值，`+100` = 翻倍） |

> **溯源**：**红衣主教：主教**（`GOVERNOR_PROMOTION_CARDINAL_BISHOP`）— 此城向其他城市释放的宗教压力翻倍（`Amount=100`）。

---

### EFFECT_ADJUST_CITY_RELIGIOUS_COMBAT_BONUS

调整城市中宗教单位的神学战斗加成。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_RELIGIOUS_COMBAT_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宗教战斗力加成值 |

> **溯源**：**红衣主教：大审判官**（`GOVERNOR_PROMOTION_CARDINAL_GRAND_INQUISITOR`）— 此城境内的宗教单位神学战斗 +10 宗教战斗力（`Amount=10`）。

---

### EFFECT_ADJUST_CITY_RELIGIOUS_HEAL

调整城市中宗教单位每回合恢复量。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_SINGLE_CITY_RELIGIOUS_HEAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每回合额外恢复量 |

> **溯源**：**红衣主教：按手礼**（`GOVERNOR_PROMOTION_CARDINAL_LAYING_ON_OF_HANDS`）— 此总督所在城市境内宗教单位 1 回合后完全恢复（`Amount=100`）。

---

### EFFECT_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_SAME_RELIGION

向城邦派遣使者时，若该城邦主流宗教与玩家相同，则该使者视为双倍计数。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_SAME_RELIGION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | `1`（重复计数 = 每个使者计算为 2） |

> **溯源**：**世界、宗教和里斯本公约**（`TRAIT_LEADER_RELIGION_CITY_STATES`，葡萄牙若昂三世特质的一部分）— 同宗教城邦每个使者计为 2 个（`Amount=1`）。

---

### EFFECT_ADJUST_GAINS_ALL_FOLLOWER_BELIEFS

玩家获得其主流宗教所拥有的全部信徒信条加成（即使该玩家并非创立者）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_GAINS_ALL_FOLLOWER_BELIEFS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用 |

> **溯源**：**达摩**（`TRAIT_CIVILIZATION_DHARMA`，印度文明特质）— 从城市的每个宗教获得信徒信条加成（`Enable=1`）。

---

### EFFECT_ADJUST_GAINS_FOUNDER_BELIEF_MAJORITY_RELIGION

玩家获得其多数宗教的创立者信条加成（即使该玩家并非该宗教的创立者）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_GAINS_FOUNDER_BELIEF_MAJORITY_RELIGION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用 |

> **溯源**：**宗教皈依者**（`TRAIT_LEADER_RELIGIOUS_CONVERT`，刚果姆本巴·恩津加特质）— 无法创建宗教，但获得己方多数宗教的创立者信条加成（`Enable=1`）。

---

### EFFECT_ADJUST_INQUISITION_START_CHARGES

调整审判官初始充能次数（默认为 1 次）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_INQUISITION_START_CHARGES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，额外充能次数（`1` = 共 2 次充能） |

> **溯源**：**宗教审讯**（`POLICY_INQUISITION`，外交政策卡）— 审判官初始充能 +1（`Amount=1`），同时启动宗教审讯（可审判清除异教）。

---

### EFFECT_ADJUST_PLAYER_ALWAYS_FULL_RELIGIOUS_TOURISM

玩家始终获得全部宗教旅游业绩，不受不同宗教的 -50% 惩罚影响。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ALWAYS_FULL_RELIGIOUS_TOURISM` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用完全宗教旅游业绩 |

> **溯源**：**基督像**（`BUILDING_CRISTO_REDENTOR`，奇观建筑）— 圣遗物的旅游业绩值不会被启蒙运动等削减，宗教旅游业绩翻倍且不受不同宗教惩罚（`Enable=1`）。

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CITY_RELIGION_CONVERSION

调整玩家通过宗教转换城市获得的时代得分。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_CITY_RELIGION_CONVERSION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每次转换的额外时代得分 |

> **溯源**：**宗教任务**（`COMMEMORATION_RELIGIOUS_QUEST`，纪念时刻/黄金时代着力点）— 每次转换城市宗教额外获得 +2 时代得分（`Amount=2`）。此 Modifier 位于 `Modifiers` 表中但未出现在任何标准参考表（BeliefModifiers 等）中，通过纪念时刻系统间接引用。

---

### EFFECT_ADJUST_PLAYER_RELIGIOUS_TOURISM_REDUCTION

调整玩家因宗教差异遭受的旅游业绩削减百分比。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_RELIGIOUS_TOURISM_REDUCTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Modifier` | **必写** | 整数（百分比），旅游削减的调整值。**注意**：参数名为 `Modifier` 而非 `Amount` |

> **溯源**：**启蒙运动**（`CIVIC_THE_ENLIGHTENMENT`，市政）— 与不同宗教的文明间宗教旅游业绩削减 50%（`Modifier=50`）。

---

### EFFECT_ADJUST_PLAYER_TRADE_ROUTE_RELIGIOUS_PRESSURE

玩家的商路施加宗教压力。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_RELIGIOUS_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宗教压力值 |
| `Destination` | **必写** | `1` = 对商路目的地施加压力，`0` = 不施加 |
| `Origin` | **必写** | `1` = 对商路起始地施加压力，`0` = 不施加 |

> **溯源**：**达摩**（`TRAIT_CIVILIZATION_DHARMA`，印度文明特质）— 商路对出发地和目的地均施加 100 宗教压力（`Amount=100`, `Destination=1`, `Origin=1`）。

---

### EFFECT_ADJUST_RELIGION_AMENITIES_FOR_MINIMUM_FOLLOWERS

城市中达到最低信徒数量时，为该城市提供宜居度。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_RELIGION_AMENITIES_FOR_MINIMUM_FOLLOWERS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amenities` | **必写** | 整数，提供的宜居度数量 |
| `Followers` | **必写** | 整数，所需的最低信徒数阈值 |

> **溯源**：**达摩**（`TRAIT_CIVILIZATION_DHARMA`，印度文明特质）— 城市每有 1 个至少 1 名信徒的宗教，便 +1 宜居度（`Amenities=1`, `Followers=1`）。

---

### EFFECT_ADJUST_RELIGION_ANYONE_CONDEMNS_FAVOR

允许任何文明（不论宗教）对该宗教使用审判官谴责，并获取外交支持。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_RELIGION_ADJUST_ANYONE_CONDEMNS_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，谴责获得的外交支持数量 |

> **溯源**：**世界宗教**（`WC_RES_WORLD_RELIGION`，世界议会决议）— 任何文明都可谴责此宗教的宗教单位，每次谴责获得 25 外交支持（`Amount=25`）。此效果通过 `ResolutionEffects` 表链接到世界议会系统。

---

### EFFECT_ADJUST_RELIGION_BUILDING_DISCOUNT

该宗教的宗教建筑获得建造折扣（信仰值或生产力折扣）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_RELIGION_BUILDING_DISCOUNT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Discount` | **必写** | 整数（百分比），折扣力度。`90` = 一折（仅需 10% 费用） |

> **溯源**：**正义的信仰**（`TRAIT_LEADER_RIGHTEOUSNESS_OF_FAITH`，萨拉丁特质）— 宗教建筑仅需 10% 的常规费用（`Discount=90`），即可用信仰值以极低折扣购买。

---

### EFFECT_ADJUST_RELIGION_CONDEMN_PROHIBITED

禁止该宗教被审判官谴责。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_RELIGION_ADJUST_CONDEMN_PROHIBITED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Prohibited` | **必写** | `1` 禁止谴责。**注意**：参数名为 `Prohibited` 而非 `Enable` |

> **溯源**：DynamicModifiers 在 GS / NF / BD / WAR 中注册，但游戏中无活跃 DB 实例。此效果与 `EFFECT_ADJUST_RELIGION_ANYONE_CONDEMNS_FAVOR` 对应（一个禁止谴责，一个鼓励谴责）。使用前需充分测试。

---

### EFFECT_ADJUST_RELIGIOUS_COMBAT_LOSS

调整宗教单位在神学战斗中失败时的宗教压力损失。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADJUST_COMBAT_LOSS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ReductionPercent` | **必写** | 整数（百分比），损失减少比例。`100` = 完全免疫战斗失败惩罚 |

> **溯源**：**与世隔绝**（`BELIEF_MONASTIC_ISOLATION`，信徒信条）— 宗教压力不会因神学战斗失败而减少（`ReductionPercent=100`）。

---

### EFFECT_ADJUST_RELIGIOUS_SPREAD_DISTANCE

调整宗教压力传播距离。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADJUST_RELIGIOUS_SPREAD_DISTANCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DistanceChange` | **必写** | 整数，传播距离改变量（正数增加格数） |

> **溯源**：**巡回传教士**（`BELIEF_ITINERANT_PREACHERS`，增强信条）— 宗教传播距离增加 30%（`DistanceChange=3`）。

---

### EFFECT_ADJUST_RELIGIOUS_SPREAD_STRENGTH

调整宗教传播力度（含市政/科技加成）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADJUST_RELIGIOUS_SPREAD_STRENGTH` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `EnhancingTechType` | **必写** | `TECH_PRINTING` 等，引用 [Technologies.TechnologyType]。该科技将触发额外传播加成 |
| `SpreadMultiplier` | **必写** | 整数（百分比），基础传播倍率加成 |
| `TechEnabledSpreadMultiplier` | **必写** | 整数（百分比），拥有 `EnhancingTechType` 科技后的额外倍率加成 |

> **溯源**：**经文**（`BELIEF_SCRIPTURE`，增强信条）— 邻近城市宗教传播压力 +25%。研发印刷术后提升至 +50%（`SpreadMultiplier=25`, `TechEnabledSpreadMultiplier=25`, `EnhancingTechType=TECH_PRINTING`）。

---

### EFFECT_ADJUST_UNITS_RELIGIOUS_STRENGTH_BY_RELIGION_TYPE

全局调整所有文明的宗教单位战斗力（常用于世界议会决议）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_UNITS_RELIGIOUS_STRENGTH_BY_RELIGION_TYPE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，所有文明宗教单位战斗力加成值 |

> **溯源**：世界议会决议 — 所有主要文明的宗教单位 +10 宗教战斗力（`Amount=10`）。注意此 ModifierType 作用于 `COLLECTION_MAJOR_PLAYERS`，会同时影响所有文明。

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION

允许玩家的近战/骑兵单位攻击城墙（条件：与目标城市同宗教）。无参数版本。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| （无） | — | 无参数，直接使用 `ABILITY_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION` 能力 |

> **溯源**：DB 中有一个实例（`TRAIT_ABILITY_ENABLE_WALL_ATTACK_SAME_RELIGION`）存在于 `Modifiers` 表，但未在任何参考表中找到。可能与同宗教攻城特质有关。使用前需确认上游挂载路径。

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION_PROMOTION_CLASS

允许指定的晋升兵种类型攻击城墙（条件：目标城市同宗教）。可指定具体的兵种类别。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION_PROMOTION_CLASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `PromotionClass` | **必写** | `PROMOTION_CLASS_LIGHT_CAVALRY` / `PROMOTION_CLASS_HEAVY_CAVALRY` 等，引用 [UnitPromotionClasses.PromotionClassType] |

> **溯源**：**巴兹尔二世**（`TRAIT_LEADER_BASIL`，拜占庭特质）— 轻骑兵和重骑兵均可攻击与拜占庭同宗教的城市的城墙（两个 Modifier 各指定一个 `PromotionClass`）。

---

### EFFECT_ADJUST_UNIT_HEALING_RELIGION_MODIFIERS

在圣地区域或相邻单元格中调整单位每回合恢复量（宗教单位限定）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_ALL_UNITS_ADJUST_HEAL_RELIGION_PER_TURN` | `COLLECTION_ALL_UNITS` |
| `MODIFIER_PLAYER_UNITS_ADJUST_HEAL_RELIGION_PER_TURN` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_RELIGION_PER_TURN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，每回合额外恢复量 |
| `Type` | **必写** | `ALL` = 所有单位均适用 |

> **溯源**：
> - 有实例：**神圣水域**（`BELIEF_HOLY_WATERS`，信徒信条）— 圣地区域或相邻单元格的宗教单位生命值回复 +10（`Amount=10`, `Type=ALL`，使用 `COLLECTION_ALL_UNITS`）
> - `COLLECTION_PLAYER_UNITS` / `COLLECTION_OWNER` 版本在 DB 中无实例，保留供自定义使用

---

### EFFECT_ADOPT_ALLY_FOUNDED_RELIGIONS

允许玩家采用盟友创立的宗教（即使自己未创立）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_ADOPT_ALLY_FOUNDED_RELIGIONS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Adopt` | **必写** | `1` 允许采用 |

> **溯源**：**耶路撒冷**（`MINOR_CIV_JERUSALEM`，宗教城邦）— 作为其宗主国，可自动采用盟友创立的宗教（`Adopt=1`）。

---

### EFFECT_ALLIANCE_PRESSURE_FROM_NO_ALLY_RELIGION

在盟友领土内施加宗教压力（不论盟友是否信奉你的宗教）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_RELIGIOUS_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，施加的宗教压力值 |

> **溯源**：**宗教联盟 3 级效果**（联盟系统）— 对盟友领土施加 20 宗教压力（`Amount=20`），不论盟友是否信仰你的宗教。

---

### EFFECT_ALLIANCE_YIELD_INCOME_FROM_ALLY_RELIGION

从追随你宗教的盟友城市中获得产出。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_ALLIANCE_PLAYERS_YIELD_FROM_FOLLOWERS_OF_ALLY_RELIGIONS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，产出数量 |
| `YieldType` | **必写** | `YIELD_FAITH` 等，引用 [Yields.YieldType] |

> **溯源**：**宗教联盟 3 级效果**（联盟系统）— 从追随你宗教的盟友城市中每位信徒获得 +1 信仰值（`Amount=1`, `YieldType=YIELD_FAITH`）。

---

### EFFECT_CITY_REMOVE_OTHER_RELIGIONS

移除城市中除当前宗教外的所有其他宗教。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_CITY_REMOVE_OTHER_RELIGIONS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| （无） | — | 无参数，执行时直接清除城市中所有非主流宗教 |

> **溯源**：此 EffectType 在 Effects.csv 中标记为 `USER ADDED` + `UNTESTED`，游戏中无活跃 DB 实例。使用前需充分测试。

---

### EFFECT_ENABLE_RELIGION_AUTO_SPREAD

启用宗教的自动传播（建立新城时该城自动获得此宗教）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ENABLE_AUTO_SPREAD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用自动传播 |

> **溯源**：**宗教殖民**（`BELIEF_RELIGIOUS_COLONIZATION`，增强信条）— 以此宗教为主流宗教的玩家建立新城后，城市初始便拥有此宗教（`Enable=1`）。

---

### EFFECT_ENABLE_RELIGION_AWARDS_ENVOY

城邦首次皈依此宗教时，玩家获得城邦使者。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ENABLE_AWARDS_ENVOY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `1` 启用使者奖励 |

> **溯源**：**宗教统一**（`BELIEF_RELIGIOUS_UNITY`，创立者信条）— 城邦首次皈依此宗教时额外获得 1 名使者（`Enable=1`）。

---

### EFFECT_ENABLE_RELIGION_AWARDS_ENVOY_RELIGIOUS_PRESSURE

城邦首次皈依此宗教时，对该城邦施加宗教压力爆发（附带使者奖励逻辑的上层效果）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ENABLE_AWARDS_ENVOY_RELIGIOUS_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，施加的宗教压力值 |

> **溯源**：**教皇权威**（`BELIEF_PAPAL_PRIMACY`，创立者信条）— 城邦首次皈依时对该城邦施加 200 宗教压力（`Amount=200`），同时从该城邦获得的加成增加 50%。

---

### EFFECT_GRANT_PLAYER_RELIGIOUS_PRESSURE_GREAT_PERSON_ACTIVATED

伟人激活时对周围城市施加宗教压力爆发。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_PLAYER_GRANT_RELIGIOUS_PRESSURE_GREAT_PERSON_ACTIVATED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宗教压力值。`400` 约为一次标准传教 |

> **溯源**：**梵蒂冈城**（`MINOR_CIV_VATICAN_CITY`，宗教城邦）— 伟人激活时对周围城市施加 400 宗教压力（`Amount=400`）。仅在 **New Frontier (Expansion2_DLC)** 中可用。

---

### EFFECT_GRANT_RELIGIOUS_PRESSURE_BURST

对一组城市施加一次宗教压力爆发（常用于紧急事件奖励）。

| ModifierType | CollectionType |
|--------------|----------------|
| `MODIFIER_EMERGENCY_CITIES_EXERT_RELIGIOUS_PRESSURE` | `COLLECTION_EMERGENCY_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数，宗教压力值 |
| `Range` | **必写** | 整数，影响范围（格数） |

> **溯源**：**宗教紧急事件奖励**（紧急事件系统）— 目标城市向 9 格范围内的城市施加 250 宗教压力（`Amount=250`, `Range=9`）。此效果依赖 `COLLECTION_EMERGENCY_CITIES`，仅在紧急事件上下文中生效。

---

## 溯源速查表

| EffectType | 主要上游 | 上游类型 | 实例数 |
|-----------|---------|---------|-------|
| `EFFECT_ADD_BELIEF` | — | Modifiers.xml 定义 | 0 |
| `EFFECT_ADD_PLAYER_BELIEF_YIELD` | 最后的预言家 | 阿拉伯文明特质 | 1 |
| `EFFECT_ADD_RELIGIOUS_BELIEF_YIELD` | 教会财产/什一税/朝圣等 | 创立者/信徒信条 | 17 |
| `EFFECT_ADD_RELIGIOUS_BUILDING` | 大教堂/谒师所等 | 崇拜信条 | 9 |
| `EFFECT_ADD_RELIGIOUS_BUILDING_MULTIPLIER` | 正义的信仰 | 萨拉丁领袖特质 | 3 |
| `EFFECT_ADD_RELIGIOUS_UNIT` | 武僧 | 信徒信条 | 1 |
| `EFFECT_ADJUST_CITY_AMENITIES_FROM_RELIGION` | 禅修 | 信徒信条 | 2 |
| `EFFECT_ADJUST_CITY_RELIGION_EXTRA_PROMOTIONS` | 守护圣人 | 红衣主教晋升 | 1 |
| `EFFECT_ADJUST_CITY_RELIGION_IGNORE_COMBAT` | 神之堡垒 | 红衣主教晋升 | 1 |
| `EFFECT_ADJUST_CITY_RELIGION_IGNORE_PRESSURE` | 神之堡垒 | 红衣主教晋升 | 1 |
| `EFFECT_ADJUST_CITY_RELIGION_ON_CAPTURE` | 征服者 | 西班牙单位能力 | 1 |
| `EFFECT_ADJUST_CITY_RELIGION_PRESSURE` | 主教 | 红衣主教晋升 | 1 |
| `EFFECT_ADJUST_CITY_RELIGIOUS_COMBAT_BONUS` | 大审判官 | 红衣主教晋升 | 1 |
| `EFFECT_ADJUST_CITY_RELIGIOUS_HEAL` | 按手礼 | 红衣主教晋升 | 1 |
| `EFFECT_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_SAME_RELIGION` | 世界公约 | 葡萄牙特质 | 1 |
| `EFFECT_ADJUST_GAINS_ALL_FOLLOWER_BELIEFS` | 达摩 | 印度文明特质 | 1 |
| `EFFECT_ADJUST_GAINS_FOUNDER_BELIEF_MAJORITY_RELIGION` | 宗教皈依者 | 刚果领袖特质 | 1 |
| `EFFECT_ADJUST_INQUISITION_START_CHARGES` | 宗教审讯 | 外交政策卡 | 1 |
| `EFFECT_ADJUST_PLAYER_ALWAYS_FULL_RELIGIOUS_TOURISM` | 基督像 | 奇观建筑 | 1 |
| `EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CITY_RELIGION_CONVERSION` | 宗教任务 | 纪念时刻 | 1 |
| `EFFECT_ADJUST_PLAYER_RELIGIOUS_TOURISM_REDUCTION` | 启蒙运动 | 市政 | 1 |
| `EFFECT_ADJUST_PLAYER_TRADE_ROUTE_RELIGIOUS_PRESSURE` | 达摩 | 印度文明特质 | 1 |
| `EFFECT_ADJUST_RELIGION_AMENITIES_FOR_MINIMUM_FOLLOWERS` | 达摩 | 印度文明特质 | 1 |
| `EFFECT_ADJUST_RELIGION_ANYONE_CONDEMNS_FAVOR` | 世界宗教 | 世界议会决议 | 1 |
| `EFFECT_ADJUST_RELIGION_BUILDING_DISCOUNT` | 正义的信仰 | 萨拉丁领袖特质 | 1 |
| `EFFECT_ADJUST_RELIGION_CONDEMN_PROHIBITED` | — | 无活跃实例 | 0 |
| `EFFECT_ADJUST_RELIGIOUS_COMBAT_LOSS` | 与世隔绝 | 信徒信条 | 1 |
| `EFFECT_ADJUST_RELIGIOUS_SPREAD_DISTANCE` | 巡回传教士 | 增强信条 | 1 |
| `EFFECT_ADJUST_RELIGIOUS_SPREAD_STRENGTH` | 经文 | 增强信条 | 1 |
| `EFFECT_ADJUST_UNITS_RELIGIOUS_STRENGTH_BY_RELIGION_TYPE` | 世界议会决议 | 世界议会 | 1 |
| `EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION` | — | 特质能力 | 1 |
| `EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION_PROMOTION_CLASS` | 巴兹尔二世 | 拜占庭领袖特质 | 2 |
| `EFFECT_ADJUST_UNIT_HEALING_RELIGION_MODIFIERS` | 神圣水域 | 信徒信条 | 1 |
| `EFFECT_ADOPT_ALLY_FOUNDED_RELIGIONS` | 耶路撒冷 | 宗教城邦 | 1 |
| `EFFECT_ALLIANCE_PRESSURE_FROM_NO_ALLY_RELIGION` | 宗教联盟 3 级 | 联盟系统 | 1 |
| `EFFECT_ALLIANCE_YIELD_INCOME_FROM_ALLY_RELIGION` | 宗教联盟 3 级 | 联盟系统 | 1 |
| `EFFECT_CITY_REMOVE_OTHER_RELIGIONS` | — | 用户添加，未测试 | 0 |
| `EFFECT_ENABLE_RELIGION_AUTO_SPREAD` | 宗教殖民 | 增强信条 | 1 |
| `EFFECT_ENABLE_RELIGION_AWARDS_ENVOY` | 宗教统一 | 创立者信条 | 1 |
| `EFFECT_ENABLE_RELIGION_AWARDS_ENVOY_RELIGIOUS_PRESSURE` | 教皇权威 | 创立者信条 | 1 |
| `EFFECT_GRANT_PLAYER_RELIGIOUS_PRESSURE_GREAT_PERSON_ACTIVATED` | 梵蒂冈城 | 宗教城邦 | 1 |
| `EFFECT_GRANT_RELIGIOUS_PRESSURE_BURST` | 紧急事件奖励 | 紧急事件系统 | 1 |

---

## 注意事项

### 命名特殊

- `EFFECT_ADJUST_CITY_RELIGIOUS_HEAL` -- 拼写为 `HEAL` 而非 `HEALING`，为游戏内部约定
- `EFFECT_ADJUST_PLAYER_RELIGIOUS_TOURISM_REDUCTION` -- 参数名 `Modifier` 而非通用的 `Amount`，编写时注意
- `EFFECT_ADJUST_RELIGION_CONDEMN_PROHIBITED` -- 参数名 `Prohibited` 而非 `Enable`，与同类布尔开关效果不一致
- `EFFECT_ADJUST_RELIGIOUS_COMBAT_LOSS` -- 参数名 `ReductionPercent` 而非 `Amount`
- `EFFECT_ADJUST_RELIGIOUS_SPREAD_DISTANCE` -- 参数名 `DistanceChange` 而非 `Amount`
- `EFFECT_ADJUST_RELIGION_BUILDING_DISCOUNT` -- 参数名 `Discount` 而非 `Amount`
- `EFFECT_ADJUST_RELIGION_AMENITIES_FOR_MINIMUM_FOLLOWERS` -- 参数名 `Amenities` / `Followers` 而非 `Amount`

### 相似效果对比

| 效果组 | 说明 |
|--------|------|
| `IGNORE_COMBAT` vs `IGNORE_PRESSURE` | 同为 `SINGLE_CITY` + `Enable` 模式，一个防神学战斗、一个防被动传播。总督"神之堡垒"同时挂载二者实现"宗教禁区" |
| `SPREAD_DISTANCE` vs `SPREAD_STRENGTH` | 同为 `PLAYER_RELIGION` 作用域。前者改距离（格数），后者改强度（百分比倍率）。后者多一个 `EnhancingTechType` 参数联动科技 |
| `BELIEF_YIELD` 两个变体 | `ADD_RELIGIOUS_BELIEF_YIELD` (17 实例, 有 `DistrictType`) vs `ADD_PLAYER_BELIEF_YIELD` (1 实例, 无 `DistrictType`) -- 功能相似但参数模型不同，大多数情况用前者 |
| `GRANT_*_PRESSURE` 两个 | `GREAT_PERSON_ACTIVATED` 作用于 `COLLECTION_OWNER`（依赖伟人激活），`BURST` 作用于 `COLLECTION_EMERGENCY_CITIES`（依赖紧急事件）。触发上下文不同，选型时需匹配 |
| `WALL_ATTACK` 两个 | `WHOLE_GAME` 版本无参数（无条件启用），`PROMOTION_CLASS` 版本按兵种类型过滤。巴兹尔二世同时使用两个变体 |
| `_SCENARIO` 变体 | `MODIFIER_SINGLE_CITY_RELIGION_EXTRA_PROMOTIONS_SCENARIO` 不设参数，专为剧本模式。正常 Mod 使用带 `Amount` 参数的主版本 |

### 信条体系分类

信条按 `BeliefClassType` 分为四类，不同类使用不同 EffectType：

| 信条类别 | 常用 EffectType | 实例 |
|---------|----------------|------|
| **创立者信条** | `EFFECT_ADD_RELIGIOUS_BELIEF_YIELD` | 教会财产、什一税、朝圣、普世教会、跨文化对话、宗教统一、教皇权威 |
| **信徒信条** | `EFFECT_ADD_RELIGIOUS_BELIEF_YIELD` / `EFFECT_ADJUST_*` | 民间宗教团、管理工作、神圣之地、武僧、禅修、神圣水域、与世隔绝 |
| **崇拜信条** | `EFFECT_ADD_RELIGIOUS_BUILDING` | 大教堂、谒师所、礼拜堂、清真寺、宝塔、犹太教堂、佛寺、窣堵波、拜火神庙 |
| **增强信条** | `EFFECT_ADJUST_RELIGIOUS_SPREAD_*` / `EFFECT_ENABLE_RELIGION_AUTO_SPREAD` | 经文、巡回传教士、宗教殖民 |

### 总督红衣主教体系

以下 6 个 EffectType 全部来自总督红衣主教的晋升树：

| 晋升 | EffectType | 效果 |
|------|-----------|------|
| 主教 | `EFFECT_ADJUST_CITY_RELIGION_PRESSURE` | 宗教压力翻倍 |
| 大审判官 | `EFFECT_ADJUST_CITY_RELIGIOUS_COMBAT_BONUS` | 神学战斗 +10 |
| 神之堡垒 | `EFFECT_ADJUST_CITY_RELIGION_IGNORE_COMBAT` + `IGNORE_PRESSURE` | 免疫外教战斗/压力 |
| 按手礼 | `EFFECT_ADJUST_CITY_RELIGIOUS_HEAL` | 1 回合完全恢复 |
| 守护圣人 | `EFFECT_ADJUST_CITY_RELIGION_EXTRA_PROMOTIONS` | 初始 +1 晋升 |

### 枚举引用

- **BeliefYieldType**：`BELIEF_YIELD_PER_CITY` / `BELIEF_YIELD_PER_FOLLOWER` / `BELIEF_YIELD_PER_FOREIGN_FOLLOWER` / `BELIEF_YIELD_PER_DISTRICT` / `BELIEF_YIELD_PER_FOREIGN_CITY` / `BELIEF_YIELD_PER_CITY_WITH_WONDER`
- **DistrictType**（当前游戏中使用到的）：`DISTRICT_HOLY_SITE` / `DISTRICT_THEATER` / `DISTRICT_CAMPUS` / `DISTRICT_COMMERCIAL_HUB`（可扩展至任何区域类型）
- **YieldType**（信条产出体系）：`YIELD_FAITH` / `YIELD_GOLD` / `YIELD_CULTURE` / `YIELD_SCIENCE`（可扩展至 `YIELD_PRODUCTION` / `YIELD_FOOD`）
- **BuildingType**（崇拜信条建筑）：`BUILDING_CATHEDRAL` / `BUILDING_GURDWARA` / `BUILDING_MEETING_HOUSE` / `BUILDING_MOSQUE` / `BUILDING_PAGODA` / `BUILDING_SYNAGOGUE` / `BUILDING_WAT` / `BUILDING_STUPA` / `BUILDING_DAR_E_MEHR`
- **PromotionClass**（攻城兵种过滤）：`PROMOTION_CLASS_LIGHT_CAVALRY` / `PROMOTION_CLASS_HEAVY_CAVALRY`（可扩展至 `PROMOTION_CLASS_MELEE` / `PROMOTION_CLASS_ANTI_CAVALRY` 等）
- **EnhancingTechType**：`TECH_PRINTING`（唯一已知实例，可扩展至任何科技）
