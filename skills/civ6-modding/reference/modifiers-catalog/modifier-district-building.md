# modifier-district-building -- 区域/建筑产出/生产力/购买类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 基于 DebugGameplay.sqlite 动态分析生成（DynamicModifiers + Modifiers + ModifierArguments + 上游溯源）
> 共 67 个 EffectType

---

### EFFECT_ADD_RELIGIOUS_BUILDING

为宗教解锁额外的宗教建筑（大教堂、谒师所、礼拜堂、清真寺、宝塔、犹太教堂、佛寺、窣堵波、拜火神庙）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_RELIGION_ADD_RELIGIOUS_BUILDING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `BuildingType` | **必写** | BUILDING_CATHEDRAL / BUILDING_GURDWARA / BUILDING_MEETING_HOUSE / BUILDING_MOSQUE / BUILDING_PAGODA / BUILDING_SYNAGOGUE / BUILDING_WAT / BUILDING_STUPA / BUILDING_DAR_E_MEHR 等 |

> **溯源**：所有 9 个官方实例均来自 BeliefModifiers→Beliefs（信徒信条：大教堂、谒师所、礼拜堂、清真寺、宝塔、犹太教堂、佛寺、窣堵波、拜火神庙）。此 EffectType 的唯一用途是在宗教信条（Belief）中为追随者解锁第三级宗教建筑选项。

---

### EFFECT_ADD_RELIGIOUS_BUILDING_MULTIPLIER

为宗教建筑的产出提供倍率加成（可指定产出类型和是否仅创立者有效）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADD_RELIGIOUS_BUILDING_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Founder` | 选写 | `0`=所有追随者 / `1`=仅创立者。官方实例仅用 `1` |
| `Multiplier` | **必写** | 整数。倍率值，官方实例为 `10`（即 +10%） |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_SCIENCE 等 |

> **溯源**：TRAIT_LEADER_RIGHTEOUSNESS_OF_FAITH（萨拉丁--正义的信仰）："阿拉伯可使用平时信仰值的 1/10 购买宗教的祭祀建筑。此种祭祀建筑为拥有它的城市带来科技值、信仰值、文化值+10%。" 此效果用于领袖特质中，使宗教建筑产出获得额外百分比加成。

---

### EFFECT_ADJUST_ACTIVE_BUILDING_PRODUCTION

根据城市当前正在建造的建筑类型调整生产力。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_ACTIVE_BUILDING_PRODUCTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 当前数据库中该 ModifierType 无已配置的 ModifierId 实例 |

> **注意事项**：DynamicModifiers 中存在但无实际 Modifiers 实例，属于预留但未使用的 EffectType。

---

### EFFECT_ADJUST_ADJACENT_CITY_RIVER_BUILDING_PRODUCTION

为毗邻河流的城市调整建筑生产力（固定值加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_ADJACENT_RIVER_BUILDING_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `50`（+50% 生产力） |

> **溯源**：TRAIT_CIVILIZATION_PEARL_DANUBE（匈牙利--多瑙河之珠）："与河流相邻的城市建造区域和建筑时+50%生产力。" 此效果与 EFFECT_ADJUST_ADJACENT_CITY_RIVER_DISTRICT_PRODUCTION 配对使用，共同实现匈牙利UA中沿河城市的生产力加成。两者参数结构完全相同（均为 Amount=50）。

---

### EFFECT_ADJUST_ADJACENT_CITY_RIVER_DISTRICT_PRODUCTION

为毗邻河流的城市调整区域生产力（固定值加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_ADJACENT_RIVER_DISTRICT_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `50`（+50% 生产力） |

> **溯源**：TRAIT_CIVILIZATION_PEARL_DANUBE（匈牙利--多瑙河之珠）：同上 EFFECT_ADJUST_ADJACENT_CITY_RIVER_BUILDING_PRODUCTION，共同实现匈牙利UA。

---

### EFFECT_ADJUST_ALL_BUILDING_PRODUCTION_MODIFIER

调整城市所有建筑的生产力百分比加成（可限定是否仅作用于奇观）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_BUILDING_PRODUCTION_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION_MODIFIER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例：`-30` / `15` / `25` |
| `IsWonder` | 选写 | `0`=不限 / `1`=仅奇观。仅 PLAYER_CITIES 版本有此参数 |

> **溯源**：
> - BUILDING_KILWA_KISIWANI（基尔瓦基斯瓦尼）：对 SINGLE_CITY 版本，使所在城市所有建筑+15%生产力（含奇观）。对 PLAYER_CITIES 版本，根据城邦宗主数量提供帝国范围内+15%至+25%建筑生产力。
> - TRAIT_CIVILIZATION_MALI_GOLD_DESERT（马里--杰利之歌）：使用 Amount=-30，使马里建造建筑时-30%生产力（惩罚）。

> **注意事项**：SINGLE_CITY 版本无 `IsWonder` 参数（全局作用于所有建筑）；PLAYER_CITIES 版本通过 `IsWonder=0` 限定非奇观建筑。

---

### EFFECT_ADJUST_ALL_DISTRICT_PRODUCTION_MODIFIER

调整城市所有区域的生产力百分比加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_DISTRICT_PRODUCTION_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION_MODIFIER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例：SINGLE_CITY `15`/`25`/`100`；PLAYER_CITIES `15`/`25`/`30`/`50` |

> **溯源**：
> - BUILDING_KILWA_KISIWANI（基尔瓦基斯瓦尼）：使所在城市所有区域+15%生产力（SINGLE_CITY）；帝国范围内按宗主数量+15%~+30%（PLAYER_CITIES）。
> - TRAIT_LEADER_FOUNDER_CARTHAGE（狄多--迦太基建国者）：拥有U型港的城市建造区域时+50%生产力。
> - POLICY_VETERANCY（经验）：为军营和港口区的建筑+30%生产力（此处用于搭配）。

> **注意事项**：与 EFFECT_ADJUST_DISTRICT_PRODUCTION（固定值）的区别：此为百分比修饰，后者为固定值加成。两者的 MODIFIER 变体名称以 `_MODIFIER` 结尾。

---

### EFFECT_ADJUST_BUILDING_FEATURE_YIELD_CHANGE

根据建筑所在地貌类型调整建筑的产出（固定值）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_FEATURE_YIELD_CHANGE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |
| `FeatureType` | 选写 | FEATURE_FOREST / FEATURE_JUNGLE / FEATURE_MARSH |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：TRAIT_CIVILIZATION_VIETNAM（越南--九龙江三角洲）："越南陆地特色区域只能建造在雨林、树林、沼泽单元格上。建造在这些地貌上的建筑将获得额外收益：" -- 树林+1文化值、雨林+1科技值、沼泽+1生产力。此效果根据建筑所在地貌为建筑产出附加额外收益，用法独特，需要结合地貌条件使用。

---

### EFFECT_ADJUST_BUILDING_HOUSING

调整建筑提供的住房值（固定值）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_BUILDING_HOUSING` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_HOUSING` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_OWNER_ADJUST_BUILDING_HOUSING` | `COLLECTION_OWNER_CITY` |
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_BUILDING_HOUSING` | `COLLECTION_PLAYER_CAPITAL_CITY` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`10` |

> **溯源**：
> - BUILDING_LIGHTHOUSE（灯塔）→ `CITY_OWNER` 版：拥有灯塔的城市建筑+2住房。
> - TRAIT_LEADER_KUPES_VOYAGE（库佩--库佩的航行）→ `PLAYER_CAPITAL_CITY` 版：首都建造建筑后+3住房。
> - BUILDING_ANGKOR_WAT（吴哥窟）→ `PLAYER_CITIES` 版：所有城市建筑+1住房。

> **注意事项**：四个 ModifierType 的作用范围不同：SINGLE_CITY 作用于单城，CITY_OWNER 作用于建筑所在城市的拥有者，PLAYER_CITIES 作用于所有城市，PLAYER_CAPITAL_CITY 仅作用于首都。

---

### EFFECT_ADJUST_BUILDING_PRODUCTION

调整特定建筑或指定区域内建筑的建造生产力（固定值）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_CITIES_ADJUST_BUILDING_PRODUCTION` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_BUILDING_PRODUCTION` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例：`20`~`200` |
| `BuildingType` | 选写 | BUILDING_ 枚举。SINGLE_CITY 和 PLAYER_CITIES 版本有此参数；ALL_CITIES 版本无 |
| `DistrictType` | 选写 | DISTRICT_ 枚举。仅 PLAYER_CITIES 版本有此参数 |

> **溯源**：
> - POLICY_LIMES（边界）：为防御建筑+100%生产力（ALL_CITIES，无 BuildingType/DistrictType 参数，可能通过条件限制）。
> - POLICY_VETERANCY（经验）：为军营和港口区的建筑+30%生产力。
> - TRAIT_CIVILIZATION_GOLDEN_AGE_QUESTS（格鲁吉亚--团结就是力量）：黄金时代建造城墙类建筑+50%生产力。
> - TRAIT_CIVILIZATION_GROTE_RIVIEREN（荷兰--大河地带）：沿河时建造学院、剧院广场、工业区建筑获得加成。
> - TRAIT_CIVILIZATION_INDUSTRIAL_REVOLUTION（英国--世界工厂）：建造工业区建筑+20%生产力。
> - TRAIT_LEADER_SHANA_MUI_MANN（夏娜-穆伊曼--结构加固）：建造城墙建筑+100%生产力。

> **注意事项**：与 EFFECT_ADJUST_ALL_BUILDING_PRODUCTION_MODIFIER（百分比修饰）的区别：此效果用于指定特定建筑类型（BuildingType）或特定区域（DistrictType）内的建筑加成。参数 BuildingType 和 DistrictType 均支持单个值，不支持逗号分隔多个值，但可通过多个 ModifierId 分别指定。

---

### EFFECT_ADJUST_BUILDING_PURCHASE_COST

调整特定建筑的购买费用。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PURCHASE_COST` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例为 `50`（即 50% 费用） |
| `BuildingType` | **必写** | BUILDING_ 枚举。官方实例：BUILDING_WALLS / BUILDING_CASTLE / BUILDING_STAR_FORT |

> **溯源**：城邦瓦莱塔宗主加成（`MINOR_CIV_VALLETTA`）——所有城市可用信仰购买市中心建筑和城墙建筑，费用 -50%（`Amount=-50`，`BuildingType=BUILDING_WALLS / BUILDING_CASTLE / BUILDING_STAR_FORT`）。此效果瓦莱塔专属，使城墙建筑信仰购买半价。

---

### EFFECT_ADJUST_BUILDING_SPREAD_CHARGES

调整宗教单位的传教次数。虽然 EffectType 名称含 "BUILDING"，但实际作用于宗教单位的传教/传播能力。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_RELIGIOUS_SPREADS` | `COLLECTION_CITY_TRAINED_UNITS` |
| `MODIFIER_PLAYER_UNITS_RELIGIOUS_SPREADS` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_SINGLE_UNIT_RELIGIOUS_SPREADS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_TRAINED_UNITS_ADJUST_RELIGIOUS_CHARGES` | `COLLECTION_PLAYER_TRAINED_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。表示传教次数增量。官方实例：`1` / `2` |

> **溯源**：
> - BUILDING_MOSQUE（清真寺）→ SINGLE_CITY_RELIGIOUS_SPREADS：在此城市训练的宗教单位+1传教次数。
> - TRAIT_CIVILIZATION_DHARMA（印度--达摩）：所有宗教单位+2传教次数（PLAYER_UNITS）。
> - ABILITY_QIN_MELEE_UNITS（三十六计）→ SINGLE_UNIT：指定单位+1传教次数。

> **注意事项**：四个 ModifierType 的作用维度不同。SINGLE_CITY 对城市内训练的单位生效，PLAYER_UNITS 对所有已有单位生效，SINGLE_UNIT 对指定单位生效，PLAYER_TRAINED_UNITS 对未来训练的单位生效。名称中的 "BUILDING" 指代的是建筑解锁的宗教单位能力。

---

### EFFECT_ADJUST_BUILDING_YIELD_CHANGE

调整特定建筑的产出值（固定值增量）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_BUILDING_YIELD_CHANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`6` |
| `BuildingType` | **必写** | BUILDING_ 枚举 |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_FOOD / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |
| `CityStatesOnly` | 选写 | `0`=否 / `1`=是。仅 PLAYER_CITIES 版本有此参数 |

> **溯源**：
> - BUILDING_ELECTRONICS_FACTORY / BUILDING_TSIKHE → MODIFIER_BUILDING_YIELD_CHANGE：建筑自身产出的固定加成。
> - GOVERNOR_PROMOTION_RESOURCE_MANAGER_INDUSTRIALIST（实业家）、GOVERNOR_PROMOTION_MERCHANT_RENEWABLE_ENERGY（再生资源补贴）→ 总督能力固定产出提升。
> - GREAT_PERSON 系列（列奥纳多·达·芬奇、詹姆斯·瓦特、希帕蒂娅、艾萨克·牛顿、阿尔伯特·爱因斯坦）→ 伟人使用效果为指定建筑+产出。
> - POLICY_THIRD_ALTERNATIVE（第三选择）→ 每座研究实验室、军事学院和发电厂+4金币。
> - POLICY_MILITARY_RESEARCH（军事研究）→ 军事学院和马厩+1科技值。
> - TRAIT_CIVILIZATION_DISTRICT_IKANDA（祖鲁）→ 军营区特有建筑产出。
> - TRAIT_LEADER_SUSSURRO（深度治疗）→ 建筑产出随生命值恢复增长。

> **注意事项**：MODIFIER_BUILDING_YIELD_CHANGE 作用于单个建筑自身（COLLECTION_OWNER），而 MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE 作用于玩家所有城市。后者多了 `CityStatesOnly` 参数，用于限制仅城邦有效。

---

### EFFECT_ADJUST_BUILDING_YIELD_MODIFIER

调整特定建筑的产出百分比加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_MODIFIER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例为 `100`（即 +100%，双倍） |
| `BuildingType` | **必写** | BUILDING_ 枚举。实例：BUILDING_MONUMENT / BUILDING_SHRINE / BUILDING_TEMPLE |
| `YieldType` | **必写** | YIELD_ 枚举 |

> **溯源**：TRAIT_CIVILIZATION_DOUBLE_CULTURE_BUILDINGS（双倍文化建筑）：文化类建筑（纪念碑、神社、寺庙）的文化值产出+100%。此效果直接翻倍特定建筑的产出，而非像 EFFECT_ADJUST_BUILDING_YIELD_MODIFIERS_FOR_DISTRICT 那样作用于区域级别。

---

### EFFECT_ADJUST_BUILDING_YIELD_MODIFIERS_FOR_DISTRICT

调整指定区域内所有建筑的产出百分比加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_YIELD_MODIFIERS_FOR_DISTRICT` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例为 `50`（即 +50%） |
| `DistrictType` | **必写** | DISTRICT_CAMPUS / DISTRICT_COMMERCIAL_HUB / DISTRICT_HOLY_SITE / DISTRICT_THEATER |
| `YieldType` | **必写** | YIELD_ 枚举 |

> **溯源**：
> - POLICY_FREE_MARKET（自由市场）：商业中心区建筑金币产出+100%。
> - POLICY_GRAND_OPERA（大歌剧）：剧院广场区建筑文化值产出+100%。
> - POLICY_RATIONALISM（理性主义）：学院区建筑科技值产出+100%。
> - POLICY_SIMULTANEUM（共享教堂）：圣地区建筑信仰值产出+100%。

> **注意事项**：此效果与 EFFECT_ADJUST_BUILDING_YIELD_MODIFIER 的区别在于作用粒度：前者针对单一建筑类型，后者针对整个区域内的所有建筑。对于政策卡翻倍区域建筑产出的场景，应使用此效果。

---

### EFFECT_ADJUST_CITY_HOUSING_PER_DISTRICT

根据城市中的区域数量调整住房。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_HOUSING_PER_DISTRICT` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 当前数据库中该 ModifierType 无已配置的 ModifierId 实例 |

> **注意事项**：DynamicModifiers 中存在但无实际使用实例。可能是基于每个区域自动计算住房的占位效果。

---

### EFFECT_ADJUST_CITY_PRODUCTION_BUILDING

根据文明特性调整建筑生产力（固定值加成，具体逻辑取决于具体 ModifierType 实现）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_BUILDING_PRODUCTION` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_BUILDING_PRODUCTION` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION_CHANGE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_CITIES_ADJUST_BUILDING_PRODUCTION_CHANGE_ETHIOPIA` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`3` |

> **注意事项**：名称中的 "CHANGE" 而非 "MODIFIER" 表示此效果为固定值（非百分比）加成。_ETHIOPIA 后缀版本为埃塞俄比亚专属实现。所有变体均无上游溯源主体（直接内置于文明 DLL 中）。该效果与 EFFECT_ADJUST_CITY_PRODUCTION_DISTRICT 配对使用，多个 ModifierType 分别作用于首都/区域/城市/文明专属维度。

---

### EFFECT_ADJUST_CITY_PRODUCTION_DISTRICT

根据文明特性调整区域生产力（固定值加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_DISTRICT_PRODUCTION` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_DISTRICT_PRODUCTION` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION_CHANGE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION_CHANGE_ETHIOPIA` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`3` |

> **注意事项**：与 EFFECT_ADJUST_CITY_PRODUCTION_BUILDING 配对使用，区别在于 BUILDING（建筑生产力）vs DISTRICT（区域生产力）。_ETHIOPIA 后缀版本为埃塞俄比亚专属。同样无上游溯源主体。

---

### EFFECT_ADJUST_CITY_STATE_TRADE_ROUTE_DISTRICT_YIELD

调整通往城邦的贸易路线中区域带来的额外产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_STATE_TRADE_ROUTE_DISTRICT_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`、`2`、`3` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_GOLD |

> **溯源**：TRAIT_LEADER_ELIZABETH（伊丽莎白一世--德瑞克的遗产）："通往城邦的贸易路线中，每个特色区域提供+3金币、+1文化值。"（注意：该效果可能与其他修饰叠加，实际数值为 Amount 参数）。

> **注意事项**：CollectionType 为 `COLLECTION_OWNER`（作用于单个城市），但通过叠加实现玩家整体效果。

---

### EFFECT_ADJUST_CITY_YIELD_FROM_POWERED_BUILDING

调整已通电建筑（Power Plant 等提供电力的建筑）提供的额外产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_YIELD_FROM_POWERED_BUILDINGS` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `4` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FOOD / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：TRAIT_CIVILIZATION_INDUSTRIAL_REVOLUTION（英国--世界工厂）："拥有通电建筑时，建筑提供额外+4全部产出。" 此效果用于在建筑通电后额外提升产出，适用于发电厂、工厂等通电建筑。

---

### EFFECT_ADJUST_CITY_YIELD_PER_DISTRICT

城市中每个区域提供额外产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_PER_DISTRICT` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_ADJUST_CITY_YIELD_PER_DISTRICT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数/小数。官方实例：`1`、`2` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH |

> **溯源**：
> - GOVERNMENT_DIGITAL_DEMOCRACY（数字化民主）：城市中每个区域提供+2文化值（PLAYER_CITIES 版，国会政体效果）。
> - GOVERNOR_PROMOTION_CARDINAL_BISHOP（大主教）：此城市每有一个区域+2信仰值（SINGLE_CITY 版）。

---

### EFFECT_ADJUST_DISTRICT_ADJACENT_NATURAL_WONDER_PRODUCTION

为毗邻自然奇观的城市调整区域生产力。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_CITIES_ADJUST_DISTRICT_ADJACENT_NATURAL_WONDER_PRODUCTION` | `COLLECTION_ALL_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例为 `50` |
| `FeatureType` | **必写** | FEATURE_IKKIL（伊基尔天坑，官方 GS 天然奇观）。自然奇观在游戏中以 Feature 形式存在（`FEATURE_` 前缀），官方实例中此参数必填 |

> **溯源**：GS 资料片伊基尔天坑（Ik-kil Cenote）的建造效果——所有城市毗邻伊基尔天坑时，区域建造生产力 +50%（`Amount=50`，`FeatureType=FEATURE_IKKIL`）。注意：天然奇观在游戏中均以 `FEATURE_NATURAL_WONDER` 类型或其专属 `FEATURE_*` 子类型存在，非 mod 内容。

---

### EFFECT_ADJUST_DISTRICT_AMENITY

调整区域提供的宜居度（全局宜居度）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_CITY_DISTRICTS_ADJUST_DISTRICT_AMENITY` | `COLLECTION_CITY_DISTRICTS` |
| `MODIFIER_PLAYER_DISTRICT_ADJUST_DISTRICT_AMENITY` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_DISTRICT_AMENITY` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_ADJUST_AMENITIES_IN_DISTRICT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`3`；mod 内容 `-1`~`-64` 等 |

> **溯源**：
> - DISTRICT_AQUEDUCT（水渠）/ DISTRICT_BATH（浴场）→ PLAYER_DISTRICT 版：水渠区域提供+1宜居度。
> - GOVERNOR_PROMOTION_WATER_WORKS（自来水工程）→ CITY_DISTRICTS 版：城市每个水渠和浴场+1宜居度。
> - TRAIT_LEADER_LINCOLN（林肯--解放黑奴宣言）→ PLAYER_DISTRICTS 版：工业区+2宜居度。
> - GREAT_PERSON_INDIVIDUAL_IBN_KHALDUN（伊本-赫勒敦）→ ADJUST_AMENITIES_IN_DISTRICT 版：指定区域+1宜居度。

> **注意事项**：与 EFFECT_ADJUST_DISTRICT_EXTRA_ENTERTAINMENT（本地娱乐）和 EFFECT_ADJUST_DISTRICT_EXTRA_REGIONAL_ENTERTAINMENT（区域辐射娱乐）的区别：AMENITY 为全局宜居度，后者分别为本地和区域辐射宜居度。

---

### EFFECT_ADJUST_DISTRICT_ATTACK_RANGE

调整区域对城市攻击范围的影响。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_DISTRICT_ADJUST_CITY_ATTACK_RANGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 当前数据库中该 ModifierType 无已配置的 ModifierId 实例 |

> **注意事项**：DynamicModifiers 中存在但无实际使用实例。可能用于军事区域（如军营）扩展城市攻击范围。

---

### EFFECT_ADJUST_DISTRICT_BASE_YIELD_CHANGE

调整区域的基础产出值（影响区域地基产出，区别于后期加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_BASE_YIELD_CHANGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`4` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_FOOD / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：
> - DISTRICT_ROYAL_NAVY_DOCKYARD（皇家海军船坞）→ 英国特色港口，基础产出+4金币。
> - DISTRICT_MBANZA（姆班赞）→ 刚果特色区域，基础产出+2食物、+4金币。

> **与 EFFECT_ADJUST_DISTRICT_YIELD_CHANGE 的关键区别**：BASE_YIELD_CHANGE 的产出属于**相邻加成**，可被政策卡翻倍（如自然哲学、海军基建等）。DISTRICT_YIELD_CHANGE 的产出不会被翻倍。

---

### EFFECT_ADJUST_DISTRICT_BUILDING_PRODUCTION

调整区域内所有建筑的生产力（全局加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_CITIES_ADJUST_DISTRICT_BUILDING_PRODUCTION` | `COLLECTION_ALL_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例为 `100` |

> **注意事项**：无上游溯源主体。此效果为全局加成（COLLECTION_ALL_CITIES），对所有城市的区域建筑生效，区别于 EFFECT_ADJUST_BUILDING_PRODUCTION（可指定特定建筑或区域）。

---

### EFFECT_ADJUST_DISTRICT_EXTRA_ENTERTAINMENT

调整区域提供的额外本地宜居度（仅对区域所在城市生效）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_EXTRA_ENTERTAINMENT` | `COLLECTION_PLAYER_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`16`；也有 `-2`（惩罚） |

> **溯源**：
> - TRAIT_CIVILIZATION_KHMER_BARAYS（高棉--大人工湖）：拥有水渠的城市改良设施提供宜居度+1。
> - TRAIT_CIVILIZATION_INDONESIA_NUSANTARA（印度尼西亚--伟大千岛之国）：邻接海岸/湖泊单元格的娱乐设施+1宜居度。
> - Mod 内容（蜜莓、苏苏洛、桃金娘、小刻画图写话等）：用于自定义文明的特殊宜居度调整。

> **注意事项**：与 EFFECT_ADJUST_DISTRICT_AMENITY 的区别：EXTRA_ENTERTAINMENT 是区域对所在城市的本地宜居度加值（影响城市本地娱乐值），而 AMENITY 是全局宜居度（影响整个帝国的宜居度计算）。与 EXTRA_REGIONAL_ENTERTAINMENT 的区别：后者影响一定范围内的其他城市。

---

### EFFECT_ADJUST_DISTRICT_EXTRA_REGIONAL_ENTERTAINMENT

调整区域提供的额外区域辐射宜居度（影响一定范围内的其他城市）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_EXTRA_REGIONAL_ENTERTAINMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |

> **溯源**：GREAT_PERSON_INDIVIDUAL_JOSEPH_PAXTON（约瑟夫-帕克斯顿，大工程师）：使用后指定区域+1区域辐射宜居度（使该区域的娱乐设施向周边城市辐射额外宜居度）。

---

### EFFECT_ADJUST_DISTRICT_EXTRA_REGIONAL_RANGE

调整区域宜居度/娱乐设施的影响范围（格数）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_EXTRA_REGIONAL_RANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_EXTRA_REGIONAL_RANGE` | `COLLECTION_PLAYER_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `3`（即影响范围+3格） |

> **溯源**：
> - GREAT_PERSON_INDIVIDUAL_JOSEPH_PAXTON（约瑟夫-帕克斯顿）：使区域娱乐辐射范围+3。
> - GREAT_PERSON_INDIVIDUAL_NIKOLA_TESLA（尼古拉-特斯拉）：使区域影响范围+3（也用于工业区范围扩展）。

---

### EFFECT_ADJUST_DISTRICT_EXTRA_REGIONAL_YIELD

调整区域额外提供给周边城市的产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_EXTRA_REGIONAL_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `2` |
| `YieldType` | **必写** | YIELD_PRODUCTION（官方实例） |

> **溯源**：GREAT_PERSON_INDIVIDUAL_NIKOLA_TESLA（尼古拉-特斯拉）：使指定区域向周边城市辐射+2生产力。此效果作用于特定区域，为周边一定范围内的城市提供区域产出加成。

---

### EFFECT_ADJUST_DISTRICT_GREAT_PERSON_POINTS

调整区域提供的伟人点数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_SINGLE_CITY_DISTRICTS_ADJUST_GREAT_PERSON_POINTS` | `COLLECTION_CITY_DISTRICTS` |
| `MODIFIER_ALLIANCE_DISTRICTS_ADJUST_GREAT_POINTS` | `COLLECTION_ALLIANCE_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1` / `2` |
| `GreatPersonClassType` | 选写 | GREAT_PERSON_CLASS_ 枚举。PLAYER_DISTRICTS 和 SINGLE_CITY_DISTRICTS 版本有此参数 |

> **溯源**：
> - BUILDING_ORACLE（神谕）→ SINGLE_CITY 版：此城市中各区域+2对应类型的伟人点数。
> - TRAIT_CIVILIZATION_BYZANTIUM（拜占庭--天授规矩）→ PLAYER_DISTRICTS 版：圣地区域+1大预言家点数。
> - ALLIANCE_DISTRICTS 版：用于同盟加成（联盟区域提供额外伟人点数）。

---

### EFFECT_ADJUST_DISTRICT_HOUSING

调整区域提供的住房值。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_HOUSING` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_CITY_DISTRICTS_ADJUST_DISTRICT_HOUSING` | `COLLECTION_CITY_DISTRICTS` |
| `MODIFIER_ADJUST_HOUSING_IN_DISTRICT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`2` / `3` |

> **溯源**：
> - TRAIT_LEADER_MONASTERIES_KING（阇耶跋摩七世--国王的修道院）：圣地位于河流之上时+2住房（PLAYER_DISTRICTS）。
> - GOVERNOR_PROMOTION_WATER_WORKS（自来水工程）→ CITY_DISTRICTS 版：城市每个水渠+2住房。
> - GREAT_PERSON_INDIVIDUAL_IBN_KHALDUN（伊本-赫勒敦）→ ADJUST_HOUSING_IN_DISTRICT 版：指定区域+2住房。

---

### EFFECT_ADJUST_DISTRICT_PREREQ

变更区域的科技或市政前置条件（使区域可通过不同科技/市政解锁）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_DISTRICT_UNLOCK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | **必写** | DISTRICT_ 枚举（如 DISTRICT_CANAL） |
| `TechType` | 选写 | TECH_ 枚举（如 TECH_MASONRY） |

> **溯源**：FIRST_EMPEROR_TRAIT（秦始皇--秦始皇/天命者）：该领袖特质使用此效果使运河可通过砌砖科技提前解锁（原本运河需更晚的科技）。"可以比其他文明更早地用砌砖解锁运河区域。"

> **注意事项**：TechType 可为空（仅解锁不需科技），或指定具体的科技/市政枚举。此效果改变的是区域解锁的科技/市政前置条件，不改变区域本身的其他属性。

---

### EFFECT_ADJUST_DISTRICT_PRODUCTION

调整特定区域的生产力（固定值/百分比加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_DISTRICT_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比/固定值，取决于上下文）。官方实例：`30`~`500` |
| `DistrictType` | **必写** | DISTRICT_ 枚举。官方实例涵盖：DISTRICT_CAMPUS / DISTRICT_COMMERCIAL_HUB / DISTRICT_DAM / DISTRICT_DIPLOMATIC_QUARTER / DISTRICT_ENCAMPMENT / DISTRICT_GOVERNMENT / DISTRICT_HARBOR / DISTRICT_HOLY_SITE 等 |

> **溯源**：
> - 城邦特质（科技/宗教/贸易/文化/军事/工业城邦）：各类城邦的宗主加成，使特定区域建造速度提升（通常 Amount=30 到 50）。
> - POLICY_VETERANCY（经验）：为军营和港口区建造+30%生产力。
> - TRAIT_LEADER_DIVINE_WIND（北条时宗--神风）：在非丘陵陆地单元格上的军营、圣地和剧院广场建造速度+50%（即和平时期1.5倍速）。
> - TRAIT_CIVILIZATION_GROTE_RIVIEREN（荷兰--大河地带）：沿河流时学院、剧院广场和工业区建造获得加成。

> **注意事项**：与 EFFECT_ADJUST_ALL_DISTRICT_PRODUCTION_MODIFIER 的区别：此效果可指定 DistrictType 针对特定区域类型加成。城邦宗主加成和领袖特质是此效果最大的实际应用场景。

---

### EFFECT_ADJUST_DISTRICT_TOURISM_ADJACENCY_YIELD_MOFIFIER

将区域的相邻加成产出按比例转化为旅游业绩（"MOFIFIER" 为 Firaxis 原始拼写错误，实为 MODIFIER）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_CITY_DISTRICTS_ADJUST_TOURISM_ADJACENCY_YIELD_MOFIFIER` | `COLLECTION_CITY_DISTRICTS` |
| `MODIFIER_PLAYER_DISTRICT_ADJUST_TOURISM_ADJACENCY_YIELD_MOFIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_TOURISM_ADJACENCY_YIELD_MOFIFIER` | `COLLECTION_PLAYER_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（转化百分比）。官方实例：`50` / `100`（即 50% 或 100% 的相邻加成产出转化为旅游业绩） |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：
> - TRAIT_LEADER_LUDWIG（路德维希二世--童话国王）：所有区域的 [ICON_CULTURE] 文化值相邻加成提供旅游业绩（PLAYER_DISTRICTS 版，Amount=100，完整转化）。
> - GREAT_PERSON_INDIVIDUAL_KENZO_TANGE（丹下健三）：每个城市区域的文化值/信仰值/金币/生产力/科技值相邻加成均转化为旅游业绩（CITY_DISTRICTS 版，Amount=50~100）。
> - DISTRICT_THANH（越南特色区域--城池）：该区域的文化值相邻加成转化为旅游业绩（PLAYER_DISTRICT 单区域版）。

> **注意事项**：命名中的 "MOFIFIER" 是 Firaxis 的原始拼写错误（应为 MODIFIER），在 Mod 中引用时必须使用原拼写。此效果是文化胜利策略的核心效果之一，实现"相邻加成产出 = 旅游业绩"的转化。

---

### EFFECT_ADJUST_DISTRICT_TOURISM_CHANGE

调整区域提供的旅游业绩（直接增加旅游业绩值）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_TOURISM_CHANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_TOURISM_CHANGE` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_CITY_DISTRICTS_ADJUST_TOURISM_CHANGE` | `COLLECTION_CITY_DISTRICTS` |
| `MODIFIER_EMERGENCY_DISTRICTS_ADJUST_TOURISM_CHANGE` | `COLLECTION_EMERGENCY_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`20` |

> **溯源**：
> - BUILDING_FERRIS_WHEEL（摩天轮）/ BUILDING_SHOPPING_MALL（购物商场）/ BUILDING_STADIUM（体育场）/ BUILDING_THERMAL_BATH（温泉浴场）→ PLAYER_DISTRICT 版：特定建筑提供旅游业绩值。
> - BUILDING_AQUATICS_CENTER（水上运动中心）→ CITY_DISTRICTS 版：城市区域的旅游业绩。
> - CIVIC_CONSERVATION（保护地球）：所有区域+2旅游业绩（随全球化时代政策变化）。
> - TRAIT_CIVILIZATION_BUILDING_PRASAT（高棉--高棉庙堂）：高棉特色建筑提供旅游业绩。
> - TRAIT_LEADER_TOKUGAWA（德川家康--幕藩）：每有一个区域+1旅游业绩。
> - GREAT_PERSON_INDIVIDUAL_MASARU_IBUKA（井深大）/ JAMSETJI_TATA（贾姆希德吉-塔塔）→ 伟人效果。

> **注意事项**：与 EFFECT_ADJUST_DISTRICT_TOURISM_ADJACENCY_YIELD_MOFIFIER 的区别：此效果直接提供旅游业绩数值，而后者是将相邻加成产出按百分比转化。此效果更常用于建筑自带旅游业绩（如摩天轮、购物商场），以及文明/领袖特质的旅游业绩加成。

---

### EFFECT_ADJUST_DISTRICT_WITHIN_ONE_HEX_ESPIONAGE_DEFENSE_BONUS

为一格内有该区域的所有城市提供间谍防御加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_DISTRICT_ADJUST_WITHIN_ONE_HEX_ESPIONAGE_DEFENSE_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `2` |

> **溯源**：DISTRICT_DIPLOMATIC_QUARTER（外交区）：外交区区域在其一格内为所有城市提供+2间谍防御等级。此效果使得外交区成为反间谍关键区域。

---

### EFFECT_ADJUST_DISTRICT_YIELD_BASED_ON_ADJACENCY_BONUS

将区域的某种相邻加成按比例复制/转化为另一种产出（核心效果：相邻加成镜像）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_DISTRICTS_ADJUST_YIELD_BASED_ON_ADJACENCY_BONUS` | `COLLECTION_ALL_DISTRICTS` |
| `MODIFIER_PLAYER_DISTRICT_ADJUST_YIELD_BASED_ON_ADJACENCY_BONUS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_YIELD_BASED_ON_ADJACENCY_BONUS` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_YIELD_BASED_ON_ADJACENCY_BONUS_BUILDER` | `COLLECTION_PLAYER_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | 选写 | DISTRICT_ 枚举（ALL_DISTRICTS 和 BUILDER 版本无此参数） |
| `YieldTypeToGrant` | **必写** | YIELD_ 枚举。要授予的目标产出类型 |
| `YieldTypeToMirror` | **必写** | YIELD_ 枚举。要复制的源相邻加成产出类型 |

> **溯源**：
> - BELIEF_WORK_ETHIC（职业道德，信徒信条）：将区域的信仰相邻加成镜像为生产力加成（ALL_DISTRICTS 版）。"追随该宗教的城市每个信仰值相邻加成使生产力+1%。"
> - TRAIT_LEADER_MONASTERIES_KING（阇耶跋摩七世--国王的修道院）：圣地的文化相邻加成转化为食物加成。
> - TRAIT_LEADER_THEODORA（狄奥多拉--悔改）：圣地的文化值相邻加成同时提供文化值（BUILDER 版，文化→文化自身镜像）。
> - GREAT_PERSON_INDIVIDUAL_HILDEGARD_OF_BINGEN（宾根的希尔德加德）：指定区域的信仰相邻加成转化为科技值。

> **注意事项**：此效果的核心机制是"读取区域已有的相邻加成值（YieldTypeToMirror），然后等量或以一定比例转化为另一种产出（YieldTypeToGrant）"。需同时填写两个 Yield 参数。仅对有相邻加成的区域类型有效。ALL_DISTRICTS 版本（如职业道德）对所有区域生效，其余版本可指定 DistrictType 限定区域类型。

---

### EFFECT_ADJUST_DISTRICT_YIELD_BASED_ON_APPEAL

根据区域所在单元格的魅力值提供额外产出（魅力门槛机制）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_YIELD_BASED_ON_APPEAL` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Description` | 选写 | LOC_ 字符串，用于 UI 显示加成来源描述 |
| `DistrictType` | **必写** | DISTRICT_ 枚举：DISTRICT_CAMPUS / DISTRICT_COMMERCIAL_HUB / DISTRICT_HOLY_SITE / DISTRICT_THEATER |
| `RequiredAppeal` | **必写** | 整数。魅力门槛值：`0`=无要求，`2`=迷人，`4`=惊艳，`6`=叹为观止 |
| `YieldChange` | **必写** | 整数。产出变化量（注意：参数名为 YieldChange 而非 Amount） |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_GOLD / YIELD_SCIENCE |

> **溯源**：
> - TRAIT_CIVILIZATION_LAND_DOWN_UNDER（澳大利亚--南方大陆）：根据魅力值为学院/商业中心/圣地/剧院提供额外产出。魅力迷人（2）时+1，惊艳（4）时+3。
> - TRAIT_CIVILIZATION_NIGHTMARE（夜魔--里人格）、TRAIT_DISTRICT_WANDERERS_CLUB（罗德岛闲逛部--闲逛部）等 mod 内容。

> **注意事项**：此效果的参数名为 `YieldChange` 而非通常的 `Amount`，这是此效果的特殊之处。Description 参数用于在 UI 中动态显示"因xxx魅力获得+xxx产出"的描述文本。RequiredAppeal 为门槛值而非精确匹配值（如 RequiredAppeal=2 表示魅力>=2时生效）。

---

### EFFECT_ADJUST_DISTRICT_YIELD_CHANGE

调整区域的产出值（固定值增量）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_YIELD_CHANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_YIELD_CHANGE` | `COLLECTION_PLAYER_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1`~`12` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_FOOD / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：
> - TRAIT_LEADER_EXALTED_GODDESS（特丽布瓦娜--三界的崇高女神）：邻接海岸/湖泊单元格的区域+2信仰值。
> - POLICY_PUBLIC_TRANSPORT（公共交通）：社区区域取替农场时每个单元格获+50金币。

> **与 EFFECT_ADJUST_DISTRICT_BASE_YIELD_CHANGE 的区别**：CHANGE 产出不会被政策卡翻倍，BASE 产出属于相邻加成可以被翻倍。
> **与 EFFECT_ADJUST_DISTRICT_YIELD_MODIFIER 的区别**：CHANGE 为固定值，MODIFIER 为百分比。

---

### EFFECT_ADJUST_DISTRICT_YIELD_MODIFIER

调整区域的产出百分比加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_YIELD_MODIFIER` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_CITY_DISTRICTS_ADJUST_YIELD_MODIFIER` | `COLLECTION_CITY_DISTRICTS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（百分比）。官方实例：`50` / `100` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：
> - POLICY_NATURAL_PHILOSOPHY（自然哲学）：学院区相邻加成+100%（产出百分比双倍）。
> - POLICY_SCRIPTURE（经文）：圣地区相邻加成+100%。
> - POLICY_NAVAL_INFRASTRUCTURE（海军基础设施）：港口区相邻加成+100%。
> - POLICY_TOWN_CHARTERS（城镇特许状）：商业中心区相邻加成+100%。
> - POLICY_CRAFTSMEN（工匠）：工业区相邻加成+100%。
> - POLICY_AESTHETICS（美学）：剧院广场区相邻加成+100%。
> - POLICY_FIVE_YEAR_PLAN（五年计划）：学院区和工业区相邻加成+100%。
> - POLICY_ECONOMIC_UNION（经济同盟）：商业中心和港口区相邻加成+100%。
> - POLICY_SPORTS_MEDIA（体育传媒）：剧院广场区+100%，体育场+1宜居度。
> - POLICY_COLLECTIVISM（集体主义）：工业区相邻加成+100%。
> - GOVERNOR_PROMOTION_MERCHANT_HARBORMASTER（大投资商）：商业中心和港口相邻加成翻倍（CITY_DISTRICTS 版）。

> **注意事项**：此效果是游戏中大量经济/军事政策卡的核心机制，用于双倍区域的相邻加成产出。POLICY 版本的典型用法是 Amount=100（+100%，即双倍），配合特定区域类型和产出类型。CITY_DISTRICTS 版本作用于单个城市的区域。

---

### EFFECT_ADJUST_PLAYER_AUTO_THEMED_BUILDING

使特定建筑（如考古博物馆）自动完成主题化（无需手动搭配巨作）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_AUTO_THEMED_BUILDING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `BuildingType` | **必写** | BUILDING_ 枚举。官方实例：BUILDING_MUSEUM_ARTIFACT（考古博物馆） |

> **溯源**：TRAIT_CIVILIZATION_DOUBLE_ARCHAEOLOGY_SLOTS（英国--大英博物馆）："每个考古博物馆可保存6个文物而非3个。建造后可供当前所有考古学家调用。当6个文物填满后，考古博物馆自动主题化。" 此效果使英国UA中的考古博物馆填满6个文物后自动完成主题化，获得主题化加成。

---

### EFFECT_ADJUST_PLAYER_BUILDING_FAVOR

调整建筑提供的外交支持。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_BUILDING_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `BuildingType` | **必写** | BUILDING_BROADCAST_CENTER（官方实例为广播中心） |
| `Favor` | **必写** | 整数。官方实例为 `3` |

> **溯源**：POLICY_DISINFORMATION_CAMPAIGN（抹黑行动）："每拥有1个广播中心，每回合获得外交支持+3。" 此效果的参数名为 Favor 而非 Amount。

> **注意事项**：参数名为 `Favor` 而非 `Amount`，填写时需注意参数名的差异。

---

### EFFECT_ADJUST_PLAYER_DISTRICT_AIR_SLOTS

调整区域提供的空军槽位数量（增加机场/机库的飞机驻扎容量）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_GRANT_AIR_SLOTS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1`（+1个空军槽位） |

> **溯源**：
> - BUILDING_HANGAR（机库）：航空港区域+1空军槽位。
> - BUILDING_AIRPORT（机场）：航空港区域+2空军槽位。
> - GREAT_PERSON_INDIVIDUAL_MARINA_RASKOVA（玛丽娜-拉斯科娃，大科学家）：+1空军槽位。

---

### EFFECT_ADJUST_PLAYER_DISTRICT_CREATE_YIELD

在城市区域单元格上创建改良设施并产生相应产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_CREATE_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `100`（百分比/固定值，取决于具体实现） |
| `DistrictType` | **必写** | DISTRICT_ 枚举。官方实例：DISTRICT_NEIGHBORHOOD（社区） |
| `ImprovementType` | 选写 | IMPROVEMENT_ 枚举。官方实例：IMPROVEMENT_FARM（农场） |
| `MustReplaceImprovement` | 选写 | `0`=否 / `1`=是。是否必须替换已有改良设施。官方实例为 `1` |
| `YieldBasedOnAppeal` | 选写 | `0`=否 / `1`=是。产出是否基于魅力值。官方实例为 `1` |
| `YieldType` | **必写** | YIELD_ 枚举 |

> **溯源**：POLICY_PUBLIC_TRANSPORT（公共交通）："社区取替农场时单元格+50金币。" 此效果在社区区域单元格上创建农场改良设施，并根据魅力值提供金币产出。

> **注意事项**：这是一个极特殊的 EffectType，参数组合非常罕见。它不仅在区域单元格上应用改良设施的产出逻辑，还提供了 MustReplaceImprovement（是否替换已有设施）和 YieldBasedOnAppeal（是否基于魅力值计算产出）等独特参数。一般用于"将区域单元格转化为可产出资源的改良设施"这类场景。

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_AERODROME_BUILDING_CONSTRUCTED

每建造一个航空港区域建筑时获得时代得分。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_AERODROME_BUILDING_CONSTRUCTED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |

> **溯源**：纪念时刻系统（`COMMEMORATION_AERONAUTICAL` 等）——黄金时代/普通时代期间，每建造一个航空港建筑 +1 时代得分（`Amount=1`）。与同系列其他 4 个 EffectType 均为纪念时刻系统的时代得分奖励效果，参数结构完全相同（仅 Amount），差异仅在命名上限制生效的建筑类型范围。

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CULTURE_BUILDING_CONSTRUCTED

每建造一个文化区建筑时获得时代得分。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_CULTURE_BUILDING_CONSTRUCTED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_DISTRICT_CONSTRUCTED

每建造一个区域时获得时代得分。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_DISTRICT_CONSTRUCTED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_INDUSTRIAL_BUILDING_CONSTRUCTED

每建造一个工业区建筑时获得时代得分。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_INDUSTRIAL_BUILDING_CONSTRUCTED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_SCIENCE_BUILDING_CONSTRUCTED

每建造一个学院区建筑时获得时代得分。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_SCIENCE_BUILDING_CONSTRUCTED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |

---

### EFFECT_ADJUST_PLAYER_FREE_BUILDING_WHEN_SPECIALTY_DISTRICT_CONSTRUCTED

首次建造每种专业区域时，在该区域中免费赠送最低生产力的建筑（汉谟拉比UA核心效果）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_FREE_BUILDING_WHEN_SPECIALTY_DISTRICT_CONSTRUCTED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 该效果通过内置逻辑自动选择该区域中生产力最低的建筑赠送 |

> **溯源**：TRAIT_LEADER_HAMMURABI（汉谟拉比--尼鲁-伊路-辛鲁）："首次建成每一种特色区域时，获得当前可建造的、所需生产力最低的建筑。" 此效果是汉谟拉比UA的核心，配合 _EXCEPT 版本排除政府区。

---

### EFFECT_ADJUST_PLAYER_FREE_BUILDING_WHEN_SPECIALTY_DISTRICT_CONSTRUCTED_EXCEPT

首次建造每种专业区域时免费赠送最低生产力建筑，但排除指定区域类型（汉谟拉比UA配套效果）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_FREE_BUILDING_WHEN_SPECIALTY_DISTRICT_CONSTRUCTED_EXCEPT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | **必写** | DISTRICT_ 枚举。官方实例：DISTRICT_GOVERNMENT（政府区） |

> **溯源**：TRAIT_LEADER_HAMMURABI（汉谟拉比--尼鲁-伊路-辛鲁）：排除政府区，因为政府区本身无第一级建筑。此效果配合不含 _EXCEPT 的版本使用，确保政府区不会触发空赠送。

---

### EFFECT_ADJUST_PLAYER_SPECIALTY_DISTRICT_CANNOT_BE_BUILT_ADJACENT_TO_CITY

禁止专业区域毗邻市中心建造（高卢UA核心限制）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_SPECIALTY_DISTRICT_CANNOT_BE_BUILT_ADJACENT_TO_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 无参数，通过内置逻辑实现限制 |

> **溯源**：TRAIT_CIVILIZATION_GAUL（高卢--哈尔施塔特文化）："专业区域无法毗邻市中心，也无法从其他区域的相邻中获得加成。" 此效果实现高卢UA中"专业区域不能毗邻市中心"的建筑限制。

---

### EFFECT_ADJUST_PLAYER_SPECIFIC_DISTRICT_GRANT_ENVOYS

建造特定区域时获得使者（汉谟拉比UA配套效果）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_SPECIFIC_DISTRICT_GRANT_ENVOYS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1` |
| `DistrictType` | **必写** | DISTRICT_ 枚举。官方实例：DISTRICT_GOVERNMENT（政府区） |

> **溯源**：TRAIT_LEADER_HAMMURABI（汉谟拉比--尼鲁-伊路-辛鲁）："首次建成非特色区域（政府区）时，获得1名使者。" 此效果与上述 FREE_BUILDING 效果共同组成汉谟拉比UA的完整实现。

---

### EFFECT_ADJUST_PLAYER_VALID_BUILDING

使特定建筑对玩家可用（解锁建筑的建造权限）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_VALID_BUILDING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 当前数据库中该 ModifierType 无已配置的 ModifierId 实例 |

> **注意事项**：DynamicModifiers 中存在但无实际使用实例。此效果可能用于"使某文明可以使用原本无法建造的建筑"场景（如让非宗教文明使用宗教建筑）。

---

### EFFECT_ADJUST_RELIGION_BUILDING_DISCOUNT

调整宗教建筑的信仰购买折扣。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_RELIGION_BUILDING_DISCOUNT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Discount` | **必写** | 整数（百分比折扣）。官方实例为 `90`（即 90% 折扣 = 仅花费 10% 信仰值） |

> **溯源**：TRAIT_LEADER_RIGHTEOUSNESS_OF_FAITH（萨拉丁--正义的信仰）："阿拉伯可使用平时信仰值的 1/10 购买宗教的祭祀建筑。" 此效果实现萨拉丁UA中宗教建筑购买享有 90% 折扣（即 1/10 价格）。

> **注意事项**：参数名为 `Discount` 而非 `Amount`，填写时需注意。与 EFFECT_ADD_RELIGIOUS_BUILDING_MULTIPLIER 同为萨拉丁UA的一部分（前者提供产出加成，此效果提供购买折扣）。

---

### EFFECT_ADJUST_RIVER_DISTRICT_PRODUCTION

为沿河城市调整区域生产力（固定百分比加成）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_RIVER_DISTRICT_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数（游戏中表现为百分比加成，官方实例为 `15` = +15% 生产力）。**注意**：效果名无 `_MODIFIER` 后缀（通常 `_MODIFIER` 后缀对应百分比，无后缀对应绝对值），此为 Firaxis 命名不一致。需 DLL 验证实际为绝对值还是百分比 |

> **溯源**：TRAIT_CIVILIZATION_ITERU（埃及--古尼罗河）："区域和奇观可建在泛滥平原上，如建在河边+15%生产力。" 此效果实现埃及UA中沿河区域建造的生产力加成。效果名虽无 `_MODIFIER` 后缀，但官方描述和游戏表现为百分比加成。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_DOMESTIC

国内贸易路线中，目的城市每个专业区域为贸易路线提供额外产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_DOMESTIC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数/小数。官方实例：`0.5` / `1` / `2` / `3` |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_GOLD / YIELD_SCIENCE |

> **溯源**：
> - TRAIT_LEADER_TOKUGAWA（德川家康--幕藩）：国内贸易路线中目的城市每有一个专业区域提供+1文化值、+2金币、+1科技值。
> - GREAT_PERSON_INDIVIDUAL_RAJA_TODAR_MAL（拉贾-托达-马尔）：国内贸易路线中每个专业区域提供额外产出。

> **注意事项**：此效果专用于国内贸易路线（DOMESTIC），Parameter Amount 支持小数值（如 0.5）。

---

### EFFECT_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_INTERNATIONAL

国际贸易路线中，目的城市每个专业区域为贸易路线提供额外产出。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TRADE_ROUTE_YIELD_PER_SPECIALTY_DISTRICT_FOR_INTERNATIONAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `3` |
| `YieldType` | **必写** | YIELD_GOLD |

> **注意事项**：专用于国际贸易路线（INTERNATIONAL），与 DOMESTIC 版本配对使用。无官方溯源实例，参数由 Effects.csv 记录。

---

### EFFECT_DISTRICT_ADJACENCY

设置区域之间的相邻加成（区域A对区域B的产出加成，基于相邻关系）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_DISTRICT_ADJACENCY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例：`1` / `2` |
| `Description` | 选写 | LOC_ 字符串，用于 UI 显示加成来源描述 |
| `DistrictType` | **必写** | DISTRICT_ 枚举（如 DISTRICT_CAMPUS / DISTRICT_COMMERCIAL_HUB / DISTRICT_HARBOR / DISTRICT_HOLY_SITE / DISTRICT_INDUSTRIAL_ZONE / DISTRICT_THEATER / DISTRICT_WONDER） |
| `TilesRequired` | 选写 | 整数。通常为 `1`（相邻所需地块数） |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |

> **溯源**：
> - TRAIT_CIVILIZATION_ADJACENT_DISTRICTS（日本--明治维新）："所有区域与另一个区域相邻时获得与平常一样的相邻加成（而不只是+1）。" 日本UA使区域间相邻提供与标准相邻相同的加成。
> - TRAIT_LEADER_LITHUANIAN_UNION（雅德维加--立陶宛联邦）：圣地区域可从邻接的其他区域获得加成（+2信仰值、+2文化值、+4金币）。
> - TRAIT_LEADER_LUDWIG（路德维希二世--童话国王）：区域间的相邻加成（与旅游业绩转化搭配）。

> **注意事项**：此效果是核心的"区域相邻加成"机制。Description 参数用于在游戏中显示"因与其他区域相邻而获得+1xxx"的文本。与 `District_Adjacencies` 表（静态配置）不同，此效果通过 Modifier 系统动态追加相邻加成关系。

---

### EFFECT_ENABLE_BUILDING_FAITH_PURCHASE

允许用信仰购买指定区域内的建筑。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_CITY_ENABLE_BUILDING_FAITH_PURCHASE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ENABLE_BUILDING_FAITH_PURCHASE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | **必写** | DISTRICT_ 枚举 |

> **溯源**：
> - CITY_ENABLE 版：学院区和剧院广场区（无上游主体，可能为特定建筑/奇迹效果）。
> - PLAYER_CITIES 版：TRAIT_CIVILIZATION_MALI_GOLD_DESERT（马里--杰利之歌）：允许使用信仰值购买商业中心建筑。TRAIT_CIVILIZATION_ROSE_SALT（瑰盐--好生活）：允许使用信仰值购买市中心、商业中心、军营等区域建筑（mod内容）。

> **注意事项**：此效果仅开启信仰购买权限，不改变价格。若需改变信仰购买价格，需配合其他效果（如 EFFECT_ADJUST_BUILDING_PURCHASE_COST）。

---

### EFFECT_ENABLE_SPECIFIC_BUILDING_FAITH_PURCHASE

允许用信仰购买指定的单个建筑（而非整个区域类型下的所有建筑）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ENABLE_SPECIFIC_BUILDING_FAITH_PURCHASE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `BuildingType` | **必写** | BUILDING_ 枚举。官方实例：BUILDING_MUSEUM_ARTIFACT（考古博物馆） |

> **溯源**：TRAIT_CIVILIZATION_ETHIOPIA（埃塞俄比亚--阿克苏姆的遗产）：允许用信仰值购买考古博物馆。

> **注意事项**：与 EFFECT_ENABLE_BUILDING_FAITH_PURCHASE 的区别：前者按区域类型（DistrictType）解锁区域内所有建筑的信仰购买，后者按具体建筑类型（BuildingType）解锁单个建筑。粒度不同。

---

### EFFECT_GRANT_BUILDING_IN_CITY

在城市中免费赠送建筑（需满足前置条件，如必须先有一级建筑才能送二级）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_GRANT_BUILDING_IN_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| _(无参数记录)_ | — | 当前数据库中该 ModifierType 无已配置的 ModifierId 实例 |

> **注意事项**：DynamicModifiers 中存在但无实际使用实例。与 IGNORE 版本的区别：此版本需要满足建筑前置条件（如必须先有图书馆才能送大学），而 IGNORE 版本可跳过前置条件。

---

### EFFECT_GRANT_BUILDING_IN_CITY_IGNORE

在城市中免费赠送建筑（无视前置条件，可直接赠送高级建筑）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_GRANT_BUILDING_IN_CITY_IGNORE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `BuildingType` | **必写** | BUILDING_ 枚举。官方实例涵盖：BUILDING_BANK / BUILDING_CASTLE / BUILDING_FACTORY / BUILDING_LIBRARY / BUILDING_LIGHTHOUSE / BUILDING_MARKET / BUILDING_SHIPYARD / BUILDING_UNIVERSITY 等 |

> **溯源**：多位大工程师（圣乔治-詹姆斯、詹姆斯-瓦特、乔凡尼-德-美第奇、希帕蒂娅、艾萨克-牛顿、霍雷肖-纳尔逊）的伟人使用效果均使用此 EffectType，在城市中直接赠送一座无视前置条件的建筑。

> **注意事项**：与不含 IGNORE 的版本相比，此效果可以跳过建筑前置条件直接赠送。这是大工程师"赠送免费建筑"效果的标准实现方式。典型用法：牛顿赠送大学（无需图书馆前置），瓦特赠送工厂（无需工坊前置）。

---

### EFFECT_GRANT_CHEAPEST_BUILDING_IN_CITY

在城市中赠送当前可建造的最低生产力建筑。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_GRANT_CHEAPEST_BUILDING_IN_CITY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数。官方实例为 `1`（赠送1个建筑） |

> **溯源**：
> - BUILDING_TORRE_DE_BELEM（贝伦塔）："建造后，非首都且位于另一大陆的城市将直接获得当前可建造的最低生产力建筑。" 此效果实现贝伦塔的跨大陆赠送机制。
> - TRAJANS_COLUMN_TRAIT（图拉真--图拉真圆柱）：所有新建城市获得一座免费建筑（通常是纪念碑）。

> **注意事项**：命名中的"CHEAPEST"指"生产力需求最低的建筑"而非"价格最便宜"。此效果自动计算当前科技/市政条件下该城市可建造的所需生产力最低的建筑并赠送。

---

### EFFECT_GRANT_CITY_YIELD_PERCENT_BUILDING_CREATED_COST

建造建筑时按建造费用的一定比例返还指定产出（"建筑返利"效果）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_GRANT_YIELD_PER_BUILDING_COST` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_GRANT_YIELD_PER_BUILDING_COST` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_GRANT_YIELD_PER_BUILDING_COST_GRANCOLOMBIA_MAYA` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_GRANT_YIELD_PER_BUILDING_COST_SAHARA` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `BuildingProductionPercent` | **必写** | 整数（百分比）。官方实例：`-15` / `-50` / `10` / `25` / `30` / `50` |
| `IncludeWonder` | 选写 | `0`=否 / `1`=是。是否包含奇观 |
| `YieldType` | **必写** | YIELD_CULTURE / YIELD_FAITH / YIELD_GOLD / YIELD_SCIENCE |

> **溯源**：
> - TRAIT_LEADER_RAMSES（拉美西斯二世--阿布辛贝）：建造建筑时获得等同于建造费用 15% 的文化值（BuildingProductionPercent=15，YieldType=CULTURE）。建造奇观时获得等同于建造费用 30% 的文化值（BuildingProductionPercent=30，IncludeWonder=1）。
> - GOVERNOR_PROMOTION_CARDINAL_CITADEL_OF_GOD（神之堡垒）：建造建筑时返还 25% 费用的信仰值。

> **注意事项**：参数名是 `BuildingProductionPercent` 而非 `Amount`，这是此效果的特殊之处。该参数取值为百分比值，正数表示返还，负数（如 -15、-50）表示额外花费惩罚。_SAHARA 和 _GRANCOLOMBIA_MAYA 后缀版本为特定文明/情景的专属实现。

---

### EFFECT_PLAYER_DIPLOMACY_AGENDA_DISTRICT_SPREAD

外交议程：基于区域多样性的评价系统（汉谟拉比议程）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_HAMMURABI_DISTRICTS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `SimpleModifierDescription` | 选写 | LOC_ 字符串。用于 UI 显示简化描述 |
| `StatementKey` | 选写 | LOC_ 字符串。议程语句键名 |

> **溯源**：TRAIT_AGENDA_HAMMURABI_DISTRICTS（汉谟拉比议程）：汉谟拉比的AI议程偏好——喜欢建造多种不同区域的文明，讨厌只建造少数几种区域的文明。

> **注意事项**：这是唯一使用 `COLLECTION_MAJOR_PLAYERS` 的 EffectType 在此文档中，参数为外交 UI 专用（SimpleModifierDescription 和 StatementKey）。此效果用于定义AI领袖的外交行为偏好，而非影响游戏数值。

---

## 相似效果对比

| 效果组 | EffectTypes | 关键差异 |
|---|---|---|
| 建筑生产力（固定值） | `EFFECT_ADJUST_BUILDING_PRODUCTION` / `EFFECT_ADJUST_CITY_PRODUCTION_BUILDING` | 前者按 BuildingType+DistrictType 指定目标，后者按文明特性（首都/区域/城市/文明专属）自动计算 |
| 建筑生产力（百分比） | `EFFECT_ADJUST_ALL_BUILDING_PRODUCTION_MODIFIER` | 百分比修饰，可限 IsWonder |
| 区域生产力（固定值） | `EFFECT_ADJUST_DISTRICT_PRODUCTION` / `EFFECT_ADJUST_CITY_PRODUCTION_DISTRICT` | 前者可指定 DistrictType，后者按文明特性计算 |
| 区域生产力（百分比） | `EFFECT_ADJUST_ALL_DISTRICT_PRODUCTION_MODIFIER` | 百分比修饰，作用于所有区域 |
| 区域产出（固定值） | `EFFECT_ADJUST_DISTRICT_YIELD_CHANGE` / `EFFECT_ADJUST_DISTRICT_BASE_YIELD_CHANGE` | BASE 修改区域基础产出，CHANGE 附加产出变化 |
| 区域产出（百分比） | `EFFECT_ADJUST_DISTRICT_YIELD_MODIFIER` | 百分比翻倍，政策卡核心机制 |
| 建筑产出（固定值） | `EFFECT_ADJUST_BUILDING_YIELD_CHANGE` | 按 BuildingType 指定建筑的固定产出增量 |
| 建筑产出（百分比） | `EFFECT_ADJUST_BUILDING_YIELD_MODIFIER` / `EFFECT_ADJUST_BUILDING_YIELD_MODIFIERS_FOR_DISTRICT` | 前者按建筑类型，后者按区域类型，粒度不同 |
| 宜居度 | `EFFECT_ADJUST_DISTRICT_AMENITY` / `EXTRA_ENTERTAINMENT` / `EXTRA_REGIONAL_ENTERTAINMENT` | AMENITY=全局宜居度，ENTERTAINMENT=本地娱乐值，REGIONAL=区域辐射 |
| 旅游业绩 | `EFFECT_ADJUST_DISTRICT_TOURISM_CHANGE` / `TOURISM_ADJACENCY_YIELD_MOFIFIER` | 前者直接加旅游业绩值，后者将相邻加成按比例转化 |
| 时代得分 | `EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_*_CONSTRUCTED`（5 个变体） | 参数完全相同（仅 Amount），差异仅在命名限制生效范围 |
| 免费建筑 | `EFFECT_GRANT_BUILDING_IN_CITY` / `EFFECT_GRANT_BUILDING_IN_CITY_IGNORE` | IGNORE 版本无视前置条件（如牛顿无需图书馆即可赠送大学） |
| 贸易路线（国内vs国际） | `FOR_DOMESTIC` / `FOR_INTERNATIONAL` | 专用于不同类型的贸易路线产出加成 |

---

## 特殊参数提醒

| EffectType | 特殊参数名 | 说明 |
|---|---|---|
| `EFFECT_ADJUST_DISTRICT_YIELD_BASED_ON_ADJACENCY_BONUS` | `YieldTypeToGrant` + `YieldTypeToMirror` | 需同时填写两个参数，仅复制已有相邻加成不为 0 的产出 |
| `EFFECT_ADJUST_DISTRICT_YIELD_BASED_ON_APPEAL` | `YieldChange` | 参数名非 `Amount`，配合 `RequiredAppeal` 门槛值使用 |
| `EFFECT_ADJUST_DISTRICT_PREREQ` | `TechType` 为空 | 仅解锁不需科技，或指定具体科技 |
| `EFFECT_ADJUST_PLAYER_DISTRICT_CREATE_YIELD` | `MustReplaceImprovement` / `YieldBasedOnAppeal` | 极特殊参数组合，用于区域上创建改良设施 |
| `EFFECT_ADJUST_PLAYER_BUILDING_FAVOR` | `Favor` | 参数名非 `Amount` |
| `EFFECT_ADJUST_RELIGION_BUILDING_DISCOUNT` | `Discount` | 参数名非 `Amount` |
| `EFFECT_GRANT_CITY_YIELD_PERCENT_BUILDING_CREATED_COST` | `BuildingProductionPercent` | 参数名非 `Amount`，百分比值 |
| `EFFECT_PLAYER_DIPLOMACY_AGENDA_DISTRICT_SPREAD` | `SimpleModifierDescription` / `StatementKey` | 外交 UI 专用参数 |
| `EFFECT_ADJUST_DISTRICT_TOURISM_ADJACENCY_YIELD_MOFIFIER` | MOFIFIER 拼写 | Firaxis 原始拼写错误，引用时必须使用原拼写 |
| `EFFECT_ADJUST_BUILDING_SPREAD_CHARGES` | Amount 含义 | Amount 表示"传教次数增量"而非产量 |

---

## 枚举引用清单

| 参数 | 枚举前缀 | 参考来源 |
|---|---|---|
| `BuildingType` | `BUILDING_` | DebugGameplay.sqlite Buildings 表 |
| `DistrictType` | `DISTRICT_` | DebugGameplay.sqlite Districts 表 |
| `YieldType` | `YIELD_` | YIELDS: YIELD_CULTURE / YIELD_FAITH / YIELD_FOOD / YIELD_GOLD / YIELD_PRODUCTION / YIELD_SCIENCE |
| `FeatureType` | `FEATURE_` | DebugGameplay.sqlite Features 表 |
| `GreatPersonClassType` | `GREAT_PERSON_CLASS_` | 如 GREAT_PERSON_CLASS_SCIENTIST / ENGINEER / MERCHANT / PROPHET / WRITER / ARTIST / MUSICIAN / GENERAL / ADMIRAL |
| `ImprovementType` | `IMPROVEMENT_` | DebugGameplay.sqlite Improvements 表 |
| `TechType` | `TECH_` | DebugGameplay.sqlite Technologies 表 |

---

## 命名审查

- **EFFECT_ADJUST_CITY_PRODUCTION_BUILDING vs EFFECT_ADJUST_CITY_PRODUCTION_DISTRICT**：前者调整建筑生产力，后者调整区域生产力，BUILDING/DISTRICT 区分明确。
- **EFFECT_ADJUST_DISTRICT_TOURISM_ADJACENCY_YIELD_MOFIFIER**：拼写错误 "MOFIFIER"（应为 MODIFIER），系 Firaxis 原始命名。Mod 中引用时需使用原拼写。
- **EFFECT_ADJUST_BUILDING_SPREAD_CHARGES**：效果实际作用于宗教单位传教次数，名称中 BUILDING 指"建筑解锁的相关宗教能力"，非直接调整建筑。
- **EFFECT_ADJUST_PLAYER_FREE_BUILDING_WHEN_SPECIALTY_DISTRICT_CONSTRUCTED 与 _EXCEPT 版本**：后者多排除参数（DistrictType=GOVERNMENT），共同组成汉谟拉比UA。
- **EFFECT_GRANT_CHEAPEST_BUILDING_IN_CITY**："CHEAPEST" 特指"所需生产力最低的建筑"（非金币价格），用于贝伦塔、图拉真圆柱等。
- **EFFECT_ADJUST_ALL_BUILDING_PRODUCTION_MODIFIER**：参数 IsWonder=1 时仅作用于奇观，IsWonder=0 时仅作用于普通建筑。两个版本（SINGLE_CITY / PLAYER_CITIES）的参数略有不同。

---

## 无官方实例的 EffectType

以下 EffectType 在 DynamicModifiers 中注册，但在 Modifiers 表中无任何已配置的 ModifierId 实例：

| EffectType | 可能用途 |
|---|---|
| `EFFECT_ADJUST_ACTIVE_BUILDING_PRODUCTION` | 根据当前建造的建筑类型动态调整生产力 |
| `EFFECT_ADJUST_CITY_HOUSING_PER_DISTRICT` | 根据城市区域数量提供住房 |
| `EFFECT_ADJUST_DISTRICT_ATTACK_RANGE` | 扩展城市攻击范围（军事区域效果） |
| `EFFECT_ADJUST_PLAYER_VALID_BUILDING` | 解锁建筑的建造权限 |
| `EFFECT_GRANT_BUILDING_IN_CITY`（非 IGNORE 版） | 需前置条件的免费赠送建筑 |

这些 EffectType 可能为预留接口、DLC/情景专属内容，或在 GameEffects 表（非 Modifiers 表）中有其他引用方式。

---
