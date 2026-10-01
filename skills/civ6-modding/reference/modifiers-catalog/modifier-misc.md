# modifier-misc — 其余杂项类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 共 133 个 EffectType，按子类别分组。使用溯源法：DynamicModifiers → ModifierType → ModifierId → 上游主体（TraitModifiers/BuildingModifiers/PolicyModifiers 等）→ LOC 中文描述 → 反推效果含义。

## 分组索引

- [环境与生态](#环境与生态)（8 个）
- [间谍与外交能见度](#间谍与外交能见度)（5 个）
- [紧急事件](#紧急事件)（1 个）
- [时代与时代得分](#时代与时代得分)（11 个）
- [随机事件与蛮族/村庄](#随机事件与蛮族村庄)（5 个）
- [科技与文化](#科技与文化)（14 个）
- [旅游与文化胜利](#旅游与文化胜利)（5 个）
- [忠诚度与身份压力](#忠诚度与身份压力)（6 个）
- [战争与好战](#战争与好战)（9 个）
- [战斗与单位](#战斗与单位)（12 个）
- [宗教与信仰](#宗教与信仰)（7 个）
- [城市与人口](#城市与人口)（7 个）
- [区域与建筑](#区域与建筑)（10 个）
- [奇观](#奇观)（4 个）
- [自然奇观](#自然奇观)（2 个）
- [经济与黄金](#经济与黄金)（6 个）
- [科学与胜利](#科学与胜利)（2 个）
- [贸易与路线](#贸易与路线)（4 个）
- [公民与总督](#公民与总督)（1 个）
- [特殊文明加成](#特殊文明加成)（10 个）
- [奖励授予](#奖励授予)（2 个）
- [特殊/系统](#特殊系统)（2 个）

---

## 环境与生态

### EFFECT_ACTIVATE_VOLCANOES

激活游戏中所有火山为活跃状态（天启模式内容，由 MODIFIER_GAME_SET_ACTIVE_VOLCANOES 在游戏模式选择时触发）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GAME_SET_ACTIVE_VOLCANOES` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：天启模式（MEGADISASTERS_MODE）— `GranColombia_Maya_RandomEvents_MODE.xml`，无数据库 ModifierId 实例

---

### EFFECT_ADJUST_CO2_GENERATION_REDUCTION

减少特定资源消耗方式产生的CO2排放量百分比。`Amount=50` 表示减少50%排放。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_CO2_GENERATION_REDUCTION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50` |
| `ResourceUsageType` | `RESOURCE_USAGE_UNIT` |

> **溯源**：通用效果（`UNIT_CO2_REDUCTION` ModifierId）；另见于政策「二次攻击能力」

---

### EFFECT_ADJUST_GLOBAL_WMD_STOCKPILE

调整全球大规模杀伤武器储备量。`PLAYERS_EQUALIZE_WMD_COUNTS` 平衡所有玩家；`PLAYER_TARGET_WMD_BAN`（`TargetOnly=1, Amount=0`）禁止特定目标持有WMD。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYERS_ADJUST_WMD_STOCKPILE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `0` |
| `TargetOnly` | `1` |

> **溯源**：紧急事件系统（难民援助/军事援助请求）

---

### EFFECT_ADJUST_PLAYER_WMD_COUNT

为玩家创建指定类型的WMD。`Type=WMD_NUCLEAR_DEVICE` 创建核装置，`Type=WMD_THERMONUCLEAR_DEVICE` 创建热核装置。项目完成时触发。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CREATE_WMD` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |
| `Type` | `WMD_NUCLEAR_DEVICE` / `WMD_THERMONUCLEAR_DEVICE` |

> **溯源**：ProjectCompletionModifiers — 项目「建造核装置」/「建造热核装置」

---

### EFFECT_ADJUST_PLAYER_WMD_MAINTENANCE_MODIFIER

调整WMD维护费用的百分比。`Amount=50` 表示维护费降低50%。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_WMD_MAINTENANCE_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50` |

> **溯源**：PolicyModifiers — 政策「二次攻击能力」（POLICY_SECOND_STRIKE_CAPABILITY）

---

### EFFECT_ADJUST_PREVENT_STRUCTURAL_DAMAGE

防止建筑和区域因自然灾害（洪水、火山等）受到结构性损坏。`Prevent=1` 启用。注意 ModifierType 中 `PREVENET` 为游戏保留的拼写错误。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GOVERNOR_ADJUST_PREVENET_STRUCTURAL_DAMAGE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Prevent` | `1` |

> **溯源**：GovernorPromotionModifiers — 总督「加固者」（防损专员晋升）

---

### EFFECT_MAP_REMOVE_CLIFFS_IN_DIRECTION

在指定半径内移除悬崖地形，使海军单位可穿越。`Radius=1` 表示1格半径。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_MAP_REMOVE_CLIFFS_IN_DIRECTION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Radius` | `1` |

> **溯源**：BuildingModifiers — 建筑「航海学校」（BUILDING_NAVIGATION_SCHOOL，葡萄牙特色）

---

### EFFECT_ADD_PLAYER_SEQUESTERED_CARBON

为玩家添加封存碳的量（抵消CO2排放）。`Amount=50000` 表示一次性封存50000碳。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADD_SEQUESTERED_CARBON` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50000` |

> **溯源**：ProjectCompletionModifiers — 项目「碳捕集」（PROJECT_CARBON_RECAPTURE）

---


## 间谍与外交能见度

### EFFECT_ADD_DIPLO_VISIBILITY

增加对指定来源目标的外交能见度等级。`Source` 标记来源类型（特性/科技/商站等），`SourceType` 指定来源范围（全体或仅女性领袖）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADD_DIPLO_VISIBILITY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` |
| `Source` | `SOURCE_GREAT_PERSON_JOURNALISM` / `SOURCE_TECH` / `SOURCE_TRADING_POST_TRAIT` / `SOURCE_TRAIT` |
| `SourceType` | `DIPLO_SOURCE_ALL_NAMES` / `DIPLO_SOURCE_FEMALE_ONLY` |

> **溯源**：TraitModifiers（成吉思汗、黑王后等）; PolicyModifiers; TechnologyModifiers（印刷术）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_SPY_SUCCESSFUL_MISSION

每次间谍成功执行任务时获得时代得分。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_SPY_SUCCESSFUL_MISSION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：PolicyModifiers — 政策「权术政治」（POLICY_MACHIAVELLIANISM）

---

### EFFECT_ADJUST_PLAYER_SPY_BONUS

调整间谍任务的成功率/效率加成。`Offense=1`=进攻任务，`Offense=0`=防御/反间谍。`Amount=1/2/3` 为等级加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_SPY_BONUS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` / `3` |
| `Offense` | `0` / `1` / `false` |

> **溯源**：TraitModifiers（黑王后、法国等）; PolicyModifiers; GovernorPromotionModifiers（语言学家等）

---

### EFFECT_ADJUST_PLAYER_STEAL_TECH_BOOSTS

允许间谍窃取科技时额外获得尤里卡。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_STEAL_TECH_BOOSTS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：PolicyModifiers — 政策「核间谍」（POLICY_NUCLEAR_ESPIONAGE）

---

### EFFECT_GRANT_SPY

免费获得一个间谍单位（间谍容量+1）。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_SPY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers（黑王后凯瑟琳等）; CivicModifiers（民族主义、意识形态等市政）

---


## 紧急事件

### EFFECT_PLAYER_SEND_GOLD_TO_EMERGENCIES_OF_TYPE

向指定类型的紧急事件自动发送金钱援助。`EmergencyType` 可选 `EMERGENCY_SEND_AID`（援助金）或 `EMERGENCY_SEND_MILITARY_AID`（军事援助）。`Amount=200`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_SEND_GOLD_TO_EMERGENCIES_OF_TYPE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `200` |
| `EmergencyType` | `EMERGENCY_SEND_AID` / `EMERGENCY_SEND_MILITARY_AID` |

> **溯源**：PolicyModifiers — 政策「提供援助」（POLICY_SEND_AID）

---


## 时代与时代得分

### EFFECT_ADJUST_PLAYER_ALWAYS_ALLOW_COMMEMORATION_QUEST_COUNT

固定可完成的纪念任务数量。`Amount=1` 表示额外增加1个纪念任务。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ALWAYS_ALLOW_COMMEMORATION_QUEST_COUNT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers — 塔玛丽（格鲁吉亚文明「团结多种力量」）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_ARMY_KILLED

每击杀一个敌方军队（Army，3单位合并）时获得时代得分。`Amount=2`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_ARMY_KILLED` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `2` |

> **溯源**：PolicyModifiers — 政策「全民动员」（POLICY_TOTAL_MOBILIZATION）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_ARTIFACT_EXTRACTED

考古学家每提取一个文物时获得时代得分。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_ARTIFACT_EXTRACTED` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：CommemorationModifiers — 纪念「愿您安息」（COMMEMORATION_IN_MEMORIAM）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CIVIC_BOOST

每次触发市政鼓舞时获得时代得分。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_CIVIC_BOOST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：CommemorationModifiers — 纪念「启蒙运动」（COMMEMORATION_ENLIGHTENMENT）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CONTINENT_DISCOVERED

每发现一个新大陆时获得时代得分。`Amount=3`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_CONTINENT_DISCOVERED` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `3` |

> **溯源**：TraitModifiers — 毛利文明「人船合一」（TRAIT_CIVILIZATION_MAORI_MANA）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CORPS_KILLED

每击杀一个敌方军团（Corps，2单位合并）时获得时代得分。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_CORPS_KILLED` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：PolicyModifiers — 政策「全民动员」（POLICY_TOTAL_MOBILIZATION）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CURRENT_CIVIC

完成与当前时代相同或更早的市政时额外获得时代得分（仅黑暗时代可触发，用于追赶）。无参数，由时代系统全局生效。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_PLAYERS_ADJUST_ERA_SCORE_PER_CURRENT_CIVIC` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Expansion1/2 DLC — `Expansion1_Modifiers.xml` / `Expansion2_Modifiers.xml` 声明，无数据库实例

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CURRENT_TECH

完成与当前时代相同或更早的科技时额外获得时代得分（仅黑暗时代可触发，用于追赶）。无参数，由时代系统全局生效。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_PLAYERS_ADJUST_ERA_SCORE_PER_CURRENT_TECH` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Expansion1/2 DLC — `Expansion1_Modifiers.xml` / `Expansion2_Modifiers.xml` 声明，无数据库实例

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_NATURAL_WONDER_DISCOVERED

每发现一个自然奇观时获得时代得分。`Amount=3`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_NATURAL_WONDER_DISCOVERED` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `3` |

> **溯源**：TraitModifiers — 毛利文明「人船合一」

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_PRIDE_MOMENT

每个光荣时刻获得额外时代得分。`MinScore=2` 表示基础分>=2 的光荣时刻才适用。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_PRIDE_MOMENT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |
| `MinScore` | `2` |

> **溯源**：BuildingModifiers — 泰姬陵奇观（BUILDING_TAJ_MAHAL）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_TECH_BOOST

每次触发科技尤里卡时获得时代得分。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_TECH_BOOST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：CommemorationModifiers — 纪念「自由探索」（COMMEMORATION_FREE_INQUIRY）

---


## 随机事件与蛮族/村庄

### EFFECT_ADJUST_GAME_REALISM_SETTING

设置游戏的真实感/灾难等级（`REALISM_SETTING_MEGADISASTERS` 大灾变或 `REALISM_SETTING_APOCALYPSE` 天启模式）。由游戏模式选择时触发。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GAME_SET_REALISM_SETTING` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：天启模式（MEGADISASTERS_MODE）— `GranColombia_Maya_RandomEvents_MODE.xml`，无数据库实例

---

### EFFECT_ADJUST_PLAYER_RANDOM_CIVIC_BOOST_GOODY_HUT

从村庄/被征服城市获得随机市政鼓舞。`Source=CAPTURED_CITY` 表示来源为征服城市。`Amount=1/2`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_CIVIC_BOOST_GOODY_HUT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` |
| `Source` | `CAPTURED_CITY` |

> **溯源**：无固定上游（通过 Lua 脚本或特定文明特性触发）

---

### EFFECT_ADJUST_PLAYER_RANDOM_EVENT_AVOID

避免特定类型的随机事件/自然灾害发生在自己的领土上。`RandomEventType` 指定要避开的灾害类型。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_AVOID_RANDOM_EVENT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `RandomEventType` | `RANDOM_EVENT_FLOOD_1000_YEAR` / `RANDOM_EVENT_FLOOD_MAJOR` / `RANDOM_EVENT_FLOOD_MODERATE` |

> **溯源**：BuildingModifiers — 建筑「大浴场」（BUILDING_GREAT_BATH），避免洪水事件

---

### EFFECT_ADJUST_PLAYER_RANDOM_TECHNOLOGY_BOOST_GOODY_HUT

从村庄/被征服城市获得随机科技尤里卡。`Source=CAPTURED_CITY`。`Amount=1/2`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_TECHNOLOGY_BOOST_GOODY_HUT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` |
| `Source` | `CAPTURED_CITY` |

> **溯源**：无固定上游（通用效果）

---

### EFFECT_ADJUST_RANDOM_EVENT_MODIFIED_DAMAGE_OPPOSING_PLAYER

调整特定随机事件对敌方玩家造成的伤害。`Amount=100` 表示+100%伤害。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_RANDOM_EVENT_MODIFIED_DAMAGE_OPPOSING_PLAYER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` |
| `RandomEventType` | `RANDOM_EVENT_BLIZZARD_CRIPPLING` / `RANDOM_EVENT_BLIZZARD_SIGNIFICANT` / `RANDOM_EVENT_HURRICANE_CAT_4` / `RANDOM_EVENT_HURRICANE_CAT_5` |

> **溯源**：TraitModifiers — 努比亚（TA_SETI）/ 俄罗斯（MOTHER_RUSSIA）领袖特性

---


## 科技与文化

### EFFECT_ADJUST_CIVIC_BOOST

调整市政鼓舞的触发进度百分比。`Amount=-40` 表示只需完成60%即可触发；`Amount=20` 表示触发后额外获得20%进度（超100%）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_CIVIC_BOOST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-40` / `10` / `20` / `25` |

> **溯源**：TraitModifiers（秦始皇、罗马等）; PolicyModifiers（政策「启蒙运动」）

---

### EFFECT_ADJUST_FREE_CIVIC_BOOST_FIRST_TRADING_POST_EACH_CIV

首次在每个文明的城市建立商站时，免费触发一次市政鼓舞。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FREE_CIVIC_BOOST_FIRST_TRADING_POST_EACH_CIV` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers — 蒙古文明「驿站」（TRAIT_CIVILIZATION_MONGOLIAN_ORDU）

---

### EFFECT_ADJUST_FREE_CIVIC_BOOST_WONDER_ERA

建造非当前时代奇观时，免费触发一次市政鼓舞。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FREE_CIVIC_BOOST_WONDER_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers — 秦始皇（LEADER_QIN_MANDATE_OF_HEAVEN）

---

### EFFECT_ADJUST_FREE_TECH_BOOST_FIRST_TRADING_POST_EACH_CIV

首次在每个文明的城市建立商站时，免费触发一次科技尤里卡。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FREE_TECH_BOOST_FIRST_TRADING_POST_EACH_CIV` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers — 蒙古文明「驿站」

---

### EFFECT_ADJUST_FREE_TECH_BOOST_WONDER_ERA

建造非当前时代奇观时，免费触发一次科技尤里卡。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FREE_TECH_BOOST_WONDER_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers — 秦始皇

---

### EFFECT_ADJUST_TECHNOLOGY_BOOST

调整科技尤里卡的触发进度百分比。`Amount=-40` 表示只需60%即可触发；`Amount=100` 表示直接完成该科技。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TECHNOLOGY_BOOST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-40` / `10` / `100` / `20` / `25` |

> **溯源**：TraitModifiers（巴比伦「Enuma Anu Enlil」、秦始皇、朝鲜等）; PolicyModifiers（政策「自由探索」）

---

### EFFECT_GRANT_ALL_TECHNOLOGY_BOOST_BY_ERA

免费获得指定时代范围内所有科技的尤里卡（不随机，全给）。`StartEraType`/`EndEraType` 划定范围。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_ALL_TECHNOLOGY_BOOST_BY_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `EndEraType` | `ERA_CLASSICAL` / `ERA_INFORMATION` |
| `StartEraType` | `ERA_ANCIENT` / `ERA_INFORMATION` |

> **溯源**：ProjectCompletionModifiers — 项目「登月计划」（PROJECT_LAUNCH_MOON_LANDING）

---

### EFFECT_GRANT_PLAYER_RANDOM_CIVIC

免费获得一项随机市政（直接完成）。`Amount=1/2`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_CIVIC` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` |

> **溯源**：BuildingModifiers — 莫斯科大剧院奇观（BUILDING_BOLSHOI_THEATRE）

---

### EFFECT_GRANT_PLAYER_RANDOM_TECHNOLOGY

免费获得一项随机科技（直接完成）。`Amount=1/2`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_TECHNOLOGY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` |

> **溯源**：BuildingModifiers — 牛津大学奇观（BUILDING_OXFORD_UNIVERSITY）

---

### EFFECT_GRANT_PLAYER_SPECIFIC_TECHNOLOGY

免费获得一项指定的特定科技（直接完成）。`TechType` 指定科技。`MODIFIER_PLAYER_GRANT_SPECIFIC_TECHNOLOGY_GAUL` 为高卢专属。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_SPECIFIC_TECHNOLOGY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `TechType` | `TECH_ANIMAL_HUSBANDRY` / `TECH_ASTROLOGY` / `TECH_CURRENCY` / `TECH_FLIGHT` / `TECH_MASONRY` / `TECH_MINING` / `TECH_POTTERY` / `TECH_SAILING` / `TECH_SHIPBUILDING` / `TECH_WRITING` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_SPECIFIC_TECHNOLOGY_GAUL` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `TechType` | `TECH_APPRENTICESHIP` |

> **溯源**：TraitModifiers（巴比伦/毛利/高卢文明）

---

### EFFECT_GRANT_RANDOM_CIVIC_BOOST_BY_ERA

随机获得指定时代范围内的 N 次市政鼓舞。`Amount=99` 表示尽可能多地给。紧急事件版本奖励参与玩家。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_CIVIC_BOOST_BY_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `99` |
| `EndEraType` | `ERA_ATOMIC` / `ERA_CLASSICAL` / `ERA_FUTURE` / `ERA_RENAISSANCE` |
| `StartEraType` | `ERA_ANCIENT` / `ERA_ATOMIC` / `ERA_MEDIEVAL` / `ERA_RENAISSANCE` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_PLAYERS_GRANT_RANDOM_CIVIC_BOOST_BY_ERA` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` |
| `EndEraType` | `ERA_INFORMATION` |
| `StartEraType` | `ERA_INDUSTRIAL` |

> **溯源**：TraitModifiers; EmergencyRewards（世界博览会等）

---

### EFFECT_GRANT_RANDOM_CIVIC_BOOST_ON_NEW_ERA

进入新时代时获得随机市政鼓舞。`Amount=0, ApplyImmediately=1` 表示进入新时代后立即触发。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_CIVIC_BOOST_ON_NEW_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `0` |
| `ApplyImmediately` | `1` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_GRANT_RANDOM_TECHNOLOGY_BOOST_BY_ERA

随机获得指定时代范围内的 N 次科技尤里卡。紧急事件版本奖励参与玩家。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_TECHNOLOGY_BOOST_BY_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` / `3` / `99` |
| `EndEraType` | `ERA_ATOMIC` / `ERA_CLASSICAL` / `ERA_FUTURE` / `ERA_INDUSTRIAL` / `ERA_INFORMATION` / `ERA_MEDIEVAL` / `ERA_MODERN` / `ERA_RENAISSANCE` |
| `StartEraType` | `ERA_ANCIENT` / `ERA_ATOMIC` / `ERA_CLASSICAL` / `ERA_INDUSTRIAL` / `ERA_MEDIEVAL` / `ERA_MODERN` / `ERA_RENAISSANCE` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_PLAYERS_GRANT_RANDOM_TECHNOLOGY_BOOST_BY_ERA` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |
| `EndEraType` | `ERA_FUTURE` / `ERA_INFORMATION` |
| `StartEraType` | `ERA_INDUSTRIAL` |

> **溯源**：TraitModifiers; EmergencyRewards（国际宇航空间站等）

---

### EFFECT_GRANT_RANDOM_TECHNOLOGY_BOOST_ON_NEW_ERA

进入新时代时获得随机科技尤里卡。`Amount=0/1, ApplyImmediately=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RANDOM_TECHNOLOGY_BOOST_ON_NEW_ERA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `0` / `1` |
| `ApplyImmediately` | `1` |

> **溯源**：无特定上游（通用效果）

---


## 旅游与文化胜利

### EFFECT_ADJUST_PLAYER_OVERALL_TOURISM_REDUCTION

调整整体旅游业绩效的衰减比例（不同政体/意识形态会减少对他文明的旅游输出）。`Modifier=20` 表示降低20%衰减。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_OVERALL_TOURISM_REDUCTION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Modifier` | `20` |

> **溯源**：PolicyModifiers — 政策「线上社群」（POLICY_ONLINE_COMMUNITIES）

---

### EFFECT_ADJUST_PLAYER_TOURISM

调整玩家的总旅游业绩效值（百分比）。影响对他文明的文化压力。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TOURISM` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-10` / `100` / `25` |

> **溯源**：TraitModifiers（罗斯福、法国等）; GovernmentModifiers（政体加成）

---

### EFFECT_ADJUST_PLAYER_TOURISM_FROM_NATIONAL_PARKS

调整国家公园提供的旅游业绩效百分比。`Amount=100` 表示翻倍。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TOURISM_FROM_NATIONAL_PARKS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` |

> **溯源**：CommemorationModifiers — 纪念「愿您安息」

---

### EFFECT_ADJUST_TRAIT_AMENITY

调整城市宜居度（来自领袖/文明特性）。虽然名含 `TRAIT`，但可通用于任何来源。`Amount=1/2/3`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_TRAIT_AMENITY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `2` / `3` |

> **溯源**：TraitModifiers（蒙特祖玛、佩德罗二世、亚历山大等领袖特性）

---

### EFFECT_GRANT_TOURISM_PER_EXCESS_LUXURIES

每种多余的奢侈资源提供额外旅游业绩效。`Amount=50` 表示每种多余奢侈资源+50%旅游业绩效。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_TOURISM_PER_EXCESS_LUXURIES` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50` |

> **溯源**：BuildingModifiers — 马拉卡纳体育场奇观（BUILDING_MARACANA）

---


## 忠诚度与身份压力

### EFFECT_ADJUST_IGNORE_IDENTITY_PRESSURE

使所在城市忽略来自其他文明的身份压力（忠诚度不受外部文化影响）。`Ignore=1` 启用。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GOVERNOR_ADJUST_IGNORE_CULTURAL_IDENTITY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Ignore` | `1` |

> **溯源**：GovernorPromotionModifiers — 总督「维克多」的晋升能力

---

### EFFECT_ADJUST_PLAYER_ALWAYS_LOYAL_COASTAL_HOME_CONTINENT

使首都大陆上的沿海城市永久保持满忠诚度。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ALWAYS_LOYAL_COASTAL_HOME_CONTINENT` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：TraitModifiers — 腓尼基文明「地中海殖民地」（TRAIT_CIVILIZATION_PHOENICIA_MEDITERRANEAN_COLONIES）

---

### EFFECT_ADJUST_PLAYER_CULTURAL_IDENTITY_PRESSURE_RADIUS_FROM_CAPITAL

调整首都向外传播身份压力的半径。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_CULTURAL_IDENTITY_PRESSURE_RADIUS_FROM_CAPITAL` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Expansion1/2 DLC — 仅 XML 声明，无数据库实例

---

### EFFECT_ADJUST_PLAYER_LOYALTY_MARTIAL_LAW_MODIFIER

调整戒严令驻军的忠诚度加成值。`Amount=5` 表示驻军额外+5忠诚度。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_LOYALTY_ADJUST_MARTIAL_LAW_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-3` / `5` / `7` |

> **溯源**：PolicyModifiers — 政策「限制令」（POLICY_LIMITANEI，巴比伦特性）

---

### EFFECT_ADJUST_PLAYER_POST_COMBAT_LOYALTY

战斗胜利后降低敌方城市的忠诚度。`Amount=-20`；`AdditionalGoldenAge=-20` 黄金时代额外再降。`AffectLocal=0` 仅影响战斗城市。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_POST_COMBAT_LOYALTY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `AdditionalGoldenAge` | `-20` |
| `AffectLocal` | `0` |
| `Amount` | `-20` |

> **溯源**：TraitModifiers — 奥斯曼文明「迅捷之鹰」（TRAIT_CIVILIZATION_OTTOMAN_SULEIMAN）

---

### EFFECT_ADJUST_PLAYER_POST_PILLAGE_LOYALTY

掠夺敌方地块后降低敌方城市的忠诚度。`Amount=-5`。`AffectLocal=0`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_POST_PILLAGE_LOYALTY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `AffectLocal` | `0` |
| `Amount` | `-5` |

> **溯源**：无固定上游（通用效果）

---


## 战争与好战

### EFFECT_ADJUST_PLAYER_ALLIED_WAR_DISCOUNT

调整发起同盟战争的折扣。`Discount=150` 表示成本降低150。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ALLIED_WAR_DISCOUNT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Discount` | `150` |

> **溯源**：TraitModifiers — 加拿大文明「和平秩序」（TRAIT_CIVILIZATION_CANADA_PEACE_ORDER）

---

### EFFECT_ADJUST_PLAYER_ENFORCE_BORDERS

强制拒绝所有开放边境请求。`Enable=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ENFORCE_BORDERS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Enable` | `1` |

> **溯源**：PolicyModifiers — 政策「帝国卫队」（POLICY_IMPERIAL_GUARD）

---

### EFFECT_ADJUST_PLAYER_JOINTWAR_EXPERIENCE

联合作战中我方单位战斗获得额外经验。`Range=5` 表示5格范围内有效。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_JOINTWAR_EXPERIENCE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Range` | `5` |

> **溯源**：TraitModifiers — 加拿大文明「和平秩序」

---

### EFFECT_ADJUST_PLAYER_JOINTWAR_PLUNDER

联合作战中掠夺收益倍数调整。`Multiplier=100` 表示+100%。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_JOINTWAR_PLUNDER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Multiplier` | `100` |

> **溯源**：TraitModifiers — 加拿大文明「和平秩序」

---

### EFFECT_ADJUST_PLAYER_LEVY_DISCOUNT_PERCENT

调整征募城邦单位的金币折扣百分比。`Percent=50`（半价）/`75`（二五折）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_LEVY_DISCOUNT_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Percent` | `50` / `75` |

> **溯源**：PolicyModifiers（外交政策）; BuildingModifiers（马丘比丘等）

---

### EFFECT_ADJUST_PLAYER_MAX_WARMONGER_PERCENT

调整最大好战程度的上限百分比。`MaxPercent=100`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_MAX_WARMONGER_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `MaxPercent` | `100` |

> **溯源**：PolicyModifiers — 政策「限制令」

---

### EFFECT_ADJUST_PLAYER_NO_OCCUPATION_PENALTIES

取消占领城市的生产力/科研/文化惩罚。`NoPenalties=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_NO_OCCUPATION_PENALTIES` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `NoPenalties` | `1` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_PLAYER_WARMONGER_MULTIPLIER

调整好战惩罚的倍率。`Amount=0` 表示完全免疫好战惩罚。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_WARMONGER_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `0` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_WAR_WEARINESS

调整厌战情绪的累积量。`Domestic=1` 影响国内厌战，`Enemy=1` 影响敌方厌战，`Overall=1` 影响总厌战。正值增加厌战（不利），负值减少厌战（有利）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_WAR_WEARINESS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-100` / `-25` / `100` / `20` |
| `Domestic` | `1` |
| `Enemy` | `1` |
| `Overall` | `1` / `true` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_PLAYERS_ADJUST_WAR_WEARINESS` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50` |
| `Overall` | `1` |

> **溯源**：TraitModifiers（亚历山大、居鲁士、托米丽司、成吉思汗等）; PolicyModifiers; EmergencyRewards

---


## 战斗与单位

### EFFECT_ADJUST_ATTACKER_STRENGTH_MODIFIER

在紧急事件中调整所有参与方攻击时的战斗力。仅用于 `COLLECTION_EMERGENCY_COMBATS`。`Amount=2` 增强攻击方。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_COMBATS_ADJUST_ATTACKER_STRENGTH` | `COLLECTION_EMERGENCY_COMBATS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-2` / `-3` / `2` |

> **溯源**：EmergencyBuffs — 紧急事件加成系统

---

### EFFECT_ADJUST_CORPS_ARMY_MODIFIED_STRENGTH

调整军团/军队的额外战斗力加成。`Corps=1`=军团（2单位合并），`Corps=0`=军队（3单位合并）。`DOMAIN_LAND` 限定陆军。`Amount=5`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CORPS_ARMY_MODIFIED_STRENGTH` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `5` |
| `Corps` | `0` / `1` |
| `Domain` | `DOMAIN_LAND` |

> **溯源**：PolicyModifiers — 政策「军事传统」（POLICY_MILITARY_TRADITION）

---

### EFFECT_ADJUST_CORPS_ARMY_PREREQ

调整军团/军队所需的前置科技/市政（提前解锁合并功能）。`Corps=1`=军团/`0`=军队。`Domain` 区分陆军/海军。`CivicType` 指定解锁市政。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CORPS_ARMY_PREREQ` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `CivicType` | `CIVIC_MERCANTILISM` / `CIVIC_MERCENARIES` / `CIVIC_NATIONALISM` |
| `Corps` | `0` / `1` |
| `Domain` | `DOMAIN_LAND` / `DOMAIN_SEA` |

> **溯源**：TraitModifiers（祖鲁「部落荣耀」）; CivicModifiers（军事传统/民族主义等）

---

### EFFECT_ADJUST_DEFENDER_STRENGTH_MODIFIER

在紧急事件中调整所有参与方防守时的战斗力。仅用于 `COLLECTION_EMERGENCY_COMBATS`。`Amount=-2/-3`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_COMBATS_ADJUST_DEFENDER_STRENGTH` | `COLLECTION_EMERGENCY_COMBATS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-2` / `-3` |

> **溯源**：EmergencyBuffs — 紧急事件加成系统

---

### EFFECT_ADJUST_DISABLE_HEALING

禁用单位的生命恢复。`Disable=1` 禁止恢复，`Foreign=1` 禁止在外国领土恢复。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISABLE_HEALING` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Disable` | `1` |
| `Foreign` | `0` / `1` |

> **溯源**：UnitAbilityModifiers — 单位能力「暮光之幕」（ABILITY_TWILIGHT_VEIL）

---

### EFFECT_ADJUST_HEAL_CHARGES

调整单位的治疗次数/充能数（如宗教单位的传播次数）。`Amount` 为充能数调整量。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_CHARGES` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | 整数，充能数调整量 |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_HEAL_SPREADS` | `COLLECTION_CITY_TRAINED_UNITS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | 整数，充能数调整量 |

> **溯源**：DynamicModifiers 定义（Base `Modifiers.xml`），游戏中无活跃 DB 实例

---

### EFFECT_ADJUST_PLAYER_HEALING_FROM_DISPERSAL

清除蛮族营地时玩家所有单位获得治疗。`Amount=100` 表示完全恢复。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_HEALING_FROM_DISPERSAL` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` |

> **溯源**：无特定上游（通用蛮族清除效果）

---

### EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER

调整玩家单位在战斗中的战斗力加成。`Amount` 为加成值（正值增强，负值削弱）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` | `COLLECTION_PLAYER_COMBAT` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-5` / `-3` / `3` / `5` / `7` / `10` 等，整数 |

> **溯源**：TraitModifiers（红胡子、成吉思汗等）; UnitAbilityModifiers; PolicyModifiers

---

### EFFECT_GRANT_COMBAT_ADJACENCY

授予战斗相邻加成（支援/夹击系统）。`Enable=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_COMBAT_ADJACENCY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Enable` | `1` |

> **溯源**：CivicModifiers — 市政「军事传统」（CIVIC_MILITARY_TRADITION）

---

### EFFECT_GRANT_HEAL_AFTER_ACTION

单位行动后自动恢复生命值（移动/攻击后回复固定血量）。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_GRANT_HEAL_AFTER_ACTION` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_GRANT_HEAL_AFTER_ACTION` | `COLLECTION_PLAYER_UNITS` |

| 参数 |
|---|
| （无参数） |

> **溯源**：UnitPromotionModifiers（多种战斗晋升）; UnitAbilityModifiers; PolicyModifiers

---

### EFFECT_GRANT_PROMOTION

直接授予指定类型晋升。`PromotionType` 可选 GDR 升级晋升或殉道者晋升等。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_GRANT_PROMOTION` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 值/引用 |
|---|---|
| `PromotionType` | `PROMOTION_GDR_AA_DEFENSE` / `PROMOTION_GDR_ARMOR_UPGRADE` / `PROMOTION_GDR_BONUS_MOVEMENT` / `PROMOTION_GDR_SIEGE_LASER` / `PROMOTION_MARTYR` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNITS_GRANT_PROMOTION` | `COLLECTION_ALL_UNITS` |

| 参数 |
|---|
| （无参数） |

> **溯源**：BuildingModifiers — 圣米歇尔山奇观（BUILDING_MONT_ST_MICHEL），新建传教单位赠送殉道者晋升

---

### EFFECT_GRANT_RANDOM_BASE_PROMOTION

授予一项随机基础晋升。对全体主要玩家或指定玩家生效。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_GRANT_RANDOM_BASE_PROMOTION` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_MAJOR_PLAYERS_GRANT_BASE_PROMOTION` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Base + GranColombia DLC — 多个文明/领袖特性（如大哥伦比亚）使用

---


## 宗教与信仰

### EFFECT_ADD_BELIEF

为玩家创建的宗教额外添加信条（超过常规数量限制，与宗教信条选择面板解耦）。`BeliefType` 指定要添加的信条类型，`Amount` 为添加数量。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADD_BELIEF` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `BeliefType` | `BELIEF_CHURCH_PROPERTY` 等，引用 [Beliefs.BeliefType] |
| `Amount` | 整数，添加的信条数量 |

> **溯源**：DynamicModifiers 定义（Base `Modifiers.xml`），游戏中无活跃 DB 实例。效果是直接给玩家挂载一条信条，与宗教信条选择面板解耦，常用于文明/领袖特质绕过正常信条获取流程。

---

### EFFECT_ADJUST_CAN_FAITH_PURCHASE_DISTRICTS

允许所在城市使用信仰购买区域。`CanPurchase=1`。由总督能力提供。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GOVERNOR_ADJUST_CAN_FAITH_PURCHASE_DISTRICTS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `CanPurchase` | `1` |

> **溯源**：GovernorPromotionModifiers — 总督「莫克夏」晋升

---

### EFFECT_ADJUST_DISABLE_PATRONAGE

禁用伟人赞助（不能用金币/信仰直接购买伟人）。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISABLE_PATRONAGE` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Expansion1/2 DLC — 仅 XML 声明，无数据库实例

---

### EFFECT_ADJUST_GAINS_ALL_FOLLOWER_BELIEFS

获得所有信教文明的信徒信条效果（你的宗教在外国城市中享有的信徒信条也为你生效）。`Enable=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GAINS_ALL_FOLLOWER_BELIEFS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Enable` | `1` |

> **溯源**：TraitModifiers — 印度文明「达摩」（TRAIT_CIVILIZATION_INDIA_DHARMA）

---

### EFFECT_ADJUST_PLAYER_FAITH_FROM_DISPERSAL

清除蛮族营地时获得信仰。`Amount=50`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FAITH_FROM_DISPERSAL` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_PLAYER_FAITH_PEACEFUL_FOUNDERS

和平创立者信仰加成（每座信仰你的宗教的外国城市提供额外信仰产出）。`Amount=5`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FAITH_PEACEFUL_FOUNDERS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `5` |

> **溯源**：BeliefModifiers — 信条「圣巴斯弟盎受难」（BELIEF_PEACEFUL_FOUNDERS）

---

### EFFECT_GRANT_PLAYER_FAITH_FROM_HARVEST

收获资源/移除地貌时获得信仰。`Amount=100`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_FAITH_FROM_HARVEST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` |

> **溯源**：Effects.csv 标记 USER ADDED — [无官方使用示例，但 Mod 中可用]

---


## 城市与人口

### EFFECT_ADJUST_CITIES_FRESHWATER_HOUSING_BONUS

为有淡水水源的城市提供额外住房加成。`HasBonus=1` 所有淡水城市都获得。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_CITIES_FRESHWATER_HOUSING_BONUS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `HasBonus` | `1` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_CITIES_HAS_URBAN_DEFENSES

使城市自动获得城墙防御（无需建造城墙建筑）。`DefenseValue=400`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_CITIES_URBAN_DEFENSES` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `DefenseValue` | `400` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_EXTRA_STARTING_POPULATION_OFF_HOME_CONTINENT

非首都大陆新建城市的初始额外人口。`Amount=3` 表示初始为4人口。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_EXTRA_STARTING_POPULATION_OFF_HOME_CONTINENT` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `3` |

> **溯源**：TraitModifiers — 毛利文明「人船合一」

---

### EFFECT_ADJUST_NO_FRESH_WATER_HOUSING

调整无水城市的基础住房。`NoHousing=1` 表示无水城市无基础住房。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_NO_FRESH_WATER_HOUSING` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `NoHousing` | `1` |

> **溯源**：TraitModifiers — 澳大利亚文明「南方大陆」

---

### EFFECT_ADJUST_PLAYER_FEAUTE_REQUIRED_FOR_SPECIALTY_DISTRICTS

调整建造专属区域所需的地貌条件。`FeatureType` 指定地形（森林/雨林/沼泽）。注意 `FEAUTE`=法语拼写遗留。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FEAUTE_REQUIRED_FOR_SPECIALTY_DISTRICTS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `FeatureType` | `FEATURE_FOREST` / `FEATURE_JUNGLE` / `FEATURE_MARSH` |

> **溯源**：TraitModifiers — 巴西文明「亚马逊」（TRAIT_CIVILIZATION_BRAZIL_AMAZON）

---

### EFFECT_ADJUST_POPULATION_AFTER_CONQUEST

调整征服后城市剩余人口比例。`Percent=100` 表示人口不变。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_POPULATION_AFTER_CONQUEST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Percent` | `100` |

> **溯源**：BuildingModifiers — 奇观「兵马俑」（BUILDING_TERRACOTTA_ARMY）

---

### EFFECT_ADJUST_WATER_HOUSING

调整沿海/临水城市的基础住房。`Amount=3` 表示额外+3住房。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_WATER_HOUSING` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `3` |

> **溯源**：TraitModifiers — 澳大利亚文明「南方大陆」

---


## 区域与建筑

### EFFECT_ADD_CULTURE_BOMB_TRIGGER

添加文化炸弹触发条件：建造指定区域或改良设施时自动吞并周围地块。`DistrictType`/`ImprovementType` 二选一。`CaptureOwnedTerritory=0` 不吞并已有归属地块。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADD_CULTURE_BOMB_TRIGGER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `CaptureOwnedTerritory` | `0` |
| `DistrictType` | `DISTRICT_AMBUSH_ZONE` / `DISTRICT_ENCAMPMENT` / `DISTRICT_HARBOR` / `DISTRICT_HOLY_SITE` / `DISTRICT_INDUSTRIAL_ZONE` / `DISTRICT_UNVEILING_OF_DEVOTION` / `DISTRICT_VICTORIA_HIGHER_ED` |
| `ImprovementType` | `IMPROVEMENT_FARM` / `IMPROVEMENT_FISHING_BOATS` / `IMPROVEMENT_FORT` / `IMPROVEMENT_MINE` / `IMPROVEMENT_PASTURE` / `IMPROVEMENT_QUARRY` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_PLAYERS_ADD_CULTURE_BOMB_TRIGGER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `CaptureOwnedTerritory` | `0` |
| `DistrictType` | `DISTRICT_PRESERVE` |

> **溯源**：TraitModifiers（毛利、澳大利亚、印加等文明）; BuildingModifiers

---

### EFFECT_ADD_PLAYER_PROJECT_AVAILABILITY

使玩家可以使用特定项目（如文明专属项目、紧急事件项目、退役电厂等）。`ProjectType` 指定。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_PLAYERS_MAKE_PROJECT_AVAILABLE` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `ProjectType` | `PROJECT_DECOMMISSION_COAL_POWER_PLANT` / `PROJECT_DECOMMISSION_NUCLEAR_POWER_PLANT` / `PROJECT_DECOMMISSION_OIL_POWER_PLANT` / `PROJECT_SEND_AID` / `PROJECT_TRAIN_ASTRONAUTS` / `PROJECT_TRAIN_ATHLETES` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ALLOW_PROJECT_CHINA` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `ProjectType` | `PROJECT_LIJIA_FAITH` / `PROJECT_LIJIA_FOOD` / `PROJECT_LIJIA_GOLD` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ALLOW_PROJECT_CATHERINE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `ProjectType` | `PROJECT_COURT_FESTIVAL` |

> **溯源**：TraitModifiers（凯瑟琳华丽派对等）; EmergencyRewards

---

### EFFECT_ADJUST_ALL_BUILDINGS_PURCHASE_COST

调整所有建筑的购买费用百分比。`Amount=20` 表示降价20%。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_ALL_BUILDINGS_PURCHASE_COST` | `COLLECTION_PLAYER_CITIES` |

| 参数 |
|---|
| （无参数） |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_ALL_BUILDINGS_PURCHASE_COST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `20` |

> **溯源**：BuildingModifiers — 建筑「大市场」（BUILDING_SUKIENNICE）

---

### EFFECT_ADJUST_ALL_DISTRICTS_CULTURE_BOMB

使所有区域建造都能触发文化炸弹（全局效果）。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ALL_DISTRICTS_CULTURE_BOMB` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_ALL_DISTRICTS_PRODUCTION

调整所有区域的生产力消耗百分比。`Amount=20/25/30/50`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_ALL_DISTRICTS_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `20` / `25` / `30` / `50` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_CITY_INCREASE_DISTRICT_PRODUCTION_RATE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `20` |

> **溯源**：TraitModifiers（多个文明领袖特性）; CivicModifiers（市政「城市化」等）

---

### EFFECT_ADJUST_ALL_DISTRICTS_PURCHASE_COST

调整所有区域的购买费用百分比。`Amount=20`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_ALL_DISTRICTS_PURCHASE_COST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `20` |

> **溯源**：BuildingModifiers — 建筑「大市场」

---

### EFFECT_ADJUST_ALL_PROJECTS_PRODUCTION

调整所有项目的生产力消耗百分比。`Amount=5/20/30`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_ALL_PROJECTS_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `20` / `30` / `5` |

> **溯源**：TraitModifiers（罗斯福进步党）; GovernmentModifiers（政体加成）

---

### EFFECT_ADJUST_AUTO_THEMED_BUILDINGS_WITH_X_SLOTS

自动主题化指定槽位数量的建筑。`Amount`=槽位数阈值，`IsWonder` 区分奇观/普通建筑。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_AUTO_THEME_BUILDINGS_WITH_X_SLOTS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `2` / `3` |
| `IsWonder` | `0` / `1` |

> **溯源**：BuildingModifiers — 奇观「冬宫博物馆」（BUILDING_HERMITAGE）

---

### EFFECT_ADJUST_PROJECT_PRODUCTION

调整特定项目的生产力消耗。`ProjectType` 指定项目。`Amount=100` 翻倍速度，`Amount=-50` 减慢一半。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_PROJECT_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` / `50` |
| `ProjectType` | `PROJECT_BUILD_NUCLEAR_DEVICE` / `PROJECT_BUILD_THERMONUCLEAR_DEVICE` / `PROJECT_MANHATTAN_PROJECT` / `PROJECT_OPERATION_IVY` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_PROJECT_PRODUCTION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `30` |
| `ProjectType` | `PROJECT_BUILD_NUCLEAR_DEVICE` / `PROJECT_BUILD_THERMONUCLEAR_DEVICE` / `PROJECT_MANHATTAN_PROJECT` / `PROJECT_OPERATION_IVY` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_CITIES_ADJUST_PROJECT_PRODUCTION` | `COLLECTION_ALL_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `-50` / `100` |

> **溯源**：PolicyModifiers（曼哈顿计划、常春藤行动等）; EmergencyRewards

---

### EFFECT_ADJUST_SPACE_RACE_PROJECTS_PRODUCTION

调整所有太空竞赛项目的生产力消耗。`Amount=15/20/30/100`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_SPACE_RACE_PROJECTS_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` / `15` / `20` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_SPACE_RACE_PROJECTS_PRODUCTION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `30` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_CITIES_ADJUST_SPACE_RACE_PROJECTS_PRODUCTION` | `COLLECTION_EMERGENCY_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `20` / `40` |

> **溯源**：PolicyModifiers — 政策「一体化空间站」; EmergencyRewards

---


## 奇观

### EFFECT_ADJUST_RIVER_WONDER_PRODUCTION

临河城市建造奇观时获得生产力加成。`Amount=15` 表示+15%。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_RIVER_WONDER_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `15` |

> **溯源**：BuildingModifiers — 奇观「大浴场」

---

### EFFECT_ADJUST_WONDER_ADJACENT_NATURAL_WONDER_PRODUCTION

邻近特定自然奇观时建造奇观获得生产力加成。`FeatureType=FEATURE_IKKIL`（伊基尔天坑）。`Amount=50`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_CITIES_ADJUST_WONDER_ADJACENT_NATURAL_WONDER_PRODUCTION` | `COLLECTION_ALL_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `50` |
| `FeatureType` | `FEATURE_IKKIL` |

> **溯源**：All Cities 范围 — 由自然奇观自身（FEATURE_IKKIL）提供

---

### EFFECT_ADJUST_WONDER_ERA_PRODUCTION

建造其他时代（非当前时代）的奇观时获得生产力加成。`StartEra`/`EndEra` 划定时代范围。`IsWonder=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_WONDER_ERA_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `10` / `15` / `20` |
| `EndEra` | `ERA_CLASSICAL` / `ERA_FUTURE` / `ERA_INDUSTRIAL` / `ERA_INFORMATION` / `ERA_RENAISSANCE` |
| `IsWonder` | `1` |
| `StartEra` | `ERA_ANCIENT` / `ERA_INDUSTRIAL` / `ERA_MEDIEVAL` |

> **溯源**：TraitModifiers（法国、埃及、中国等文明）; BuildingModifiers（多个奇观）

---

### EFFECT_ADJUST_WONDER_PRODUCTION

调整奇观生产力消耗（通用加成，无时代限制）。`Amount=10/15/30/100`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_WONDER_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `10` / `15` / `30` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_WONDER_PRODUCTION` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` |

> **溯源**：TraitModifiers（多个文明领袖特性）; PolicyModifiers（哥特式建筑等）

---


## 自然奇观

### EFFECT_ADJUST_NATURAL_WONDER_AMENITY

调整自然奇观为所在城市提供的宜居度。`Amount=1` 所有城市。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_CITIES_ADJUST_NATURAL_WONDER_AMENITY` | `COLLECTION_ALL_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_NATURAL_WONDER_RELIC

发现自然奇观时获得一个圣遗物。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_NATURAL_WONDER_RELIC` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：无特定上游（通用效果）

---


## 经济与黄金

### EFFECT_ADJUST_BONUS_RATE

调整政体加成资源的基础倍率。`BonusRate` 为倍率值，`BonusType` 指定加成种类，`CityStatesOnly`（UNTESTED）限定仅对城邦生效。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GOVERNMENT_ADJUST_BONUS_RATE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `BonusRate` | 整数，倍率值 |
| `BonusType` | 引用 [GovernmentBonusNames.GovernmentBonusType] |
| `CityStatesOnly` | `0` / `1`，UNTESTED Boolean |

> **溯源**：DynamicModifiers 定义（Base `Modifiers.xml`），游戏中无活跃 DB 实例，由政体系统使用

---

### EFFECT_ADJUST_FLAT_BONUS

调整政体固定加成的数值。`BonusType` 指定加成种类（战斗经验/区域生产力/使者/信仰折扣/金币折扣/伟人点/商路/单位生产力/奇观建造），`Amount` 指定数值。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GOVERNMENT_FLAT_BONUS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `10` / `100` / `15` / `20` / `30` / `50` |
| `BonusType` | `GOVERNMENTBONUS_COMBAT_EXPERIENCE` / `GOVERNMENTBONUS_DISTRICT_PRODUCTION` / `GOVERNMENTBONUS_ENVOYS` / `GOVERNMENTBONUS_FAITH_PURCHASES` / `GOVERNMENTBONUS_GOLD_PURCHASES` / `GOVERNMENTBONUS_GREAT_PEOPLE` / `GOVERNMENTBONUS_UNIT_PRODUCTION` / `GOVERNMENTBONUS_WONDER_CONSTRUCTION` |

> **溯源**：PolicyModifiers（精英统治、古典共和、君主制、神权政治、共产主义等多种政策）

---

### EFFECT_ADJUST_GOLD_DISPERSAL

调整清除蛮族营地获得的金钱。`Improvement=IMPROVEMENT_BARBARIAN_CAMP` 限定蛮族营地。`Amount=0/200/300/400`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_GOLD_DISPERSAL` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `0` / `200` / `300` / `400` |
| `Improvement` | `IMPROVEMENT_BARBARIAN_CAMP` |

> **溯源**：PolicyModifiers — 政策「军事纪律」（POLICY_DISCIPLINE）

---

### EFFECT_ADJUST_MULTIPLY_TREASURY

调整国库金币总量的乘数因子。`Amount=100` 翻倍，`Amount=50` 增加50%。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_MULTIPLY_TREASURY` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `100` / `30` / `50` |

> **溯源**：CivicModifiers — 市政「重商主义」（CIVIC_MERCANTILISM）

---

### EFFECT_ADJUST_PLAYER_BID_COST_MODIFIER

调整玩家在世博会/国际项目等竞标中的费用（外交支持花费折扣）。`Amount` 为费用调整量。ESTIMATED 级别参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_BID_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | 整数，ESTIMATED |

> **溯源**：Expansion2 DLC — `Expansion2_Modifiers.xml` 声明，世博会竞标系统

---

### EFFECT_ADJUST_PLAYER_GOLD_INTEREST_PERCENT

调整国库资金的利率（每回合金币增长百分比）。无参数，由经济系统硬编码。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_GOLD_INTEREST_PERCENT` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Base XML — 无数据库实例，经济系统自动应用

---


## 科学与胜利

### EFFECT_ADJUST_PLAYER_SCIENCE_VICTORY_POINTS

调整科技胜利进度点数（用于推进系外行星探索等太空项目）。`Amount` 为一次性增加的点数。ESTIMATED 级别参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_SCIENCE_VICTORY_POINTS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | 整数，ESTIMATED |

> **溯源**：Expansion2 DLC — `Expansion2_Modifiers.xml` 声明，科技胜利系统

---

### EFFECT_ADJUST_PLAYER_SCIENCE_VICTORY_POINTS_PER_TURN

调整每回合自动获得的科技胜利点数。`Amount=1/3`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_SCIENCE_VICTORY_POINTS_PER_TURN` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` / `3` |

> **溯源**：ProjectCompletionModifiers — 太空竞赛项目（发射卫星/登月/火星殖民后的持续效果）

---


## 贸易与路线

### EFFECT_ADJUST_FORBID_LAND_ROUTE

禁止陆上贸易路线。`Domestic=0` 禁止对内陆上路线。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_FORBID_LAND_ROUTE` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Domestic` | `0` |

> **溯源**：TraitModifiers — 印度尼西亚文明「黄金群岛」

---

### EFFECT_ADJUST_PLAYER_IMMEDIATE_TRADING_POST

在贸易路线目标城市当回合立即建立商站。`ImmediateTradingPost=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_IMMEDIATE_TRADING_POST` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `ImmediateTradingPost` | `1` |

> **溯源**：TraitModifiers — 蒙古文明「驿站」

---

### EFFECT_ADJUST_PLAYER_IMPROVED_ROUTE_LEVEL

提升境内道路的基础等级。`ImprovedRouteLevel=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_IMPROVED_ROUTE_LEVEL` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `ImprovedRouteLevel` | `1` |

> **溯源**：TraitModifiers — 波斯文明「总督辖区」（TRAIT_CIVILIZATION_PERSIA_SATRAPIES）

---

### EFFECT_GRANT_ROUTE_IN_RADIUS

在指定半径内自动铺设道路。`RouteType=ROUTE_MODERN_ROAD`，`Radius=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GRANT_ROUTE_IN_RADIUS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Radius` | `1` |
| `RouteType` | `ROUTE_MODERN_ROAD` |

> **溯源**：BuildingModifiers — 建筑「航海学校」

---


## 公民与总督

### EFFECT_ADJUST_ACCUMULATING_BONUS

调整政体累积加成的效果（如每回合积累的使者/外交支持增量）。`BonusType` 指定加成种类，`Increment` 为每次累积量，`Interval` 为累积间隔（回合数）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GOVERNMENT_ACCUMULATING_BONUS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `BonusType` | `GOVERNMENTBONUS_ENVOYS` / `GOVERNMENTBONUS_FAITH_PURCHASES` / `GOVERNMENTBONUS_GOLD_PURCHASES` / `GOVERNMENTBONUS_GREAT_PEOPLE` / `GOVERNMENTBONUS_TRADE_ROUTES` 等，引用 [GovernmentBonusNames.GovernmentBonusType] |
| `Increment` | 整数，每次累积量 |
| `Interval` | 整数，累积间隔回合数 |

> **溯源**：DynamicModifiers 定义（Base `Modifiers.xml`），游戏中无活跃 DB 实例，由政体系统使用

---


## 特殊文明加成

### EFFECT_ADJUST_ADDITIONAL_PILLAGING

调整掠夺特定改良设施时的额外收益。`PlunderType` 指定收益类型（文化/科技），`ImprovementType` 指定改良设施。`Amount=15`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ADDITIONAL_PILLAGING` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `15` |
| `ImprovementType` | `IMPROVEMENT_CAMP` / `IMPROVEMENT_MINE` / `IMPROVEMENT_PASTURE` / `IMPROVEMENT_PLANTATION` / `IMPROVEMENT_QUARRY` |
| `PlunderType` | `PLUNDER_CULTURE` / `PLUNDER_SCIENCE` |

> **溯源**：TraitModifiers — 挪威文明「维京突袭」

---

### EFFECT_ADJUST_DISABLE_SETTLING

禁用开拓者建造新城市。`Disabled=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISABLE_SETTLING` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Disabled` | `1` |

> **溯源**：DistrictModifiers — 区域「政府特区」（DISTRICT_GOVERNMENT_QUARTER）

---

### EFFECT_ADJUST_PLAYER_BAN_CHOP

禁止砍伐森林/雨林或收获资源。`NoRemove=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYERS_ADJUST_CHOP_BAN` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `NoRemove` | `1` |

> **溯源**：PolicyModifiers — 政策「森林管理公约」

---

### EFFECT_ADJUST_PLAYER_CAPITAL

允许通过完成指定项目变更首都位置。`ProjectType=PROJECT_COTHON_CAPITAL_MOVE`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_CAPITAL` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `ProjectType` | `PROJECT_COTHON_CAPITAL_MOVE` |

> **溯源**：DistrictModifiers — 腓尼基特色区域「科通」（DISTRICT_COTHON）

---

### EFFECT_ADJUST_PLAYER_PROPERTY

调整自定义玩家属性值（键值对属性系统）。通过 Lua 读写可实现复杂自定义效果追踪。`PropertyName` 为自定义属性名。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PROPERTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Key` | **必写** | 自定义字符串，Property 名（Lua 用 `GetProperty(key)` 读取） |
| `Amount` | **必写** | 通常为 `1`（Marker 标记） |

```sql
INSERT INTO Modifiers (ModifierId, ModifierType) VALUES
('MODIFIER_SIQI_{SHORT}_PROPERTY', 'MODIFIER_PLAYER_ADJUST_PROPERTY');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_{SHORT}_PROPERTY', 'Key', 'SIQI_{SHORT}_MARKER'),
('MODIFIER_SIQI_{SHORT}_PROPERTY', 'Amount', '1');
```

> **用途**：政体/领袖/文明等挂载后设置 Player Property 标记，Lua 侧通过 `pPlayer:GetProperty('SIQI_{SHORT}_MARKER')` 读取判断。政体切换时 Modifier 自动卸载，Property 归 nil，无需额外清理。
>
> **溯源**：DB 中 58 个活跃实例（Siqi_Leaders_0032 广泛使用）。

---

### EFFECT_ADJUST_PLAYER_SUZERAIN_BONUS_DISABLED

禁用城邦宗主国加成。无参数，完全移除所有宗主国加成。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_SUZERAIN_BONUS_DISABLED` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：无特定上游（通用效果）

---

### EFFECT_ADJUST_PLAYER_TOKEN_ON_FIRST_MEETING

首次遇见城邦时自动获得额外使者（无需完成城邦任务）。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_TOKEN_ON_FIRST_MEETING` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Portugal DLC — 葡萄牙文明「印度之家」（若昂三世）使用

---

### EFFECT_EXPLORE_ENTIRE_MAP

揭示整个地图（立即消除全部战争迷雾）。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_EXPLORE_ENTIRE_MAP` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：ProjectCompletionModifiers — 项目「发射卫星」（PROJECT_LAUNCH_EARTH_SATELLITE）

---

### EFFECT_MOUNTAIN_PORTAL

山脉传送门——允许单位穿越山脉格子（山脉视为可通行地形）。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_MOUNTAIN_PORTAL` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：TraitModifiers — 印加文明「印加路网」/ 巴基斯坦「山岳通道」

---

### EFFECT_RIVER_ADJACENCY

为临河区域提供指定产出相邻加成。`DistrictType`=受影响的区域，`YieldType`=加成产出类型，`Description`=自定义本地化描述。`Amount=2`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_RIVER_ADJACENCY` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `2` |
| `Description` | `LOC_DISTRICT_RIVER_CULTURE` / `LOC_DISTRICT_RIVER_FAITH` / `LOC_DISTRICT_RIVER_PRODUCTION` / `LOC_DISTRICT_RIVER_SCIENCE` |
| `DistrictType` | `DISTRICT_CAMPUS` / `DISTRICT_HOLY_SITE` / `DISTRICT_INDUSTRIAL_ZONE` / `DISTRICT_THEATER` |
| `YieldType` | `YIELD_CULTURE` / `YIELD_FAITH` / `YIELD_PRODUCTION` / `YIELD_SCIENCE` |

> **溯源**：BuildingModifiers（纳斯卡线条）; DistrictModifiers（仪式场地等自定义区域）

---


## 奖励授予

### EFFECT_GRANT_AIR_SLOTS

授予单位额外航空槽位。`Amount=1`。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_GRANT_AIR_SLOTS` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：UnitPromotionModifiers（航母/机场晋升）; BuildingModifiers（机库/机场等建筑）

---

### EFFECT_GRANT_RELIC

授予一个圣遗物。`RelicSource=RELIC_SOURCE_TRIBAL_VILLAGE`（标记来源）。另有紧急事件版本。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_RELIC` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |
| `RelicSource` | `RELIC_SOURCE_TRIBAL_VILLAGE` |

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_PLAYERS_GRANT_RELIC` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 值/引用 |
|---|---|
| `Amount` | `1` |

> **溯源**：TraitModifiers — 波兰文明「立陶宛联邦」; EmergencyRewards

---


## 特殊/系统

### EFFECT_DO_NOTHING

什么都不做——空占位效果。用于需要填 ModifierType 但不产生效果的情况。无参数。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALLIANCE_DO_NOTHING` | `COLLECTION_OWNER` |

| 参数 |
|---|
| （无参数） |

> **溯源**：Alliances 表 — 联盟占位效果（MODIFIER_ALLIANCE_DO_NOTHING）

---

### EFFECT_TRIGGER_GAME_MECHANIC

触发游戏全局机制。`MechanicName=GenerateLandAntiquities` 生成陆地文物；`=GenerateSeaAntiquities` 生成海洋文物。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GAME_TRIGGER_MECHANIC` | `COLLECTION_OWNER` |

| 参数 | 值/引用 |
|---|---|
| `MechanicName` | `GenerateLandAntiquities` / `GenerateSeaAntiquities` |

> **溯源**：CivicModifiers — 市政「文化遗产」/「自然历史」，完成市政后触发文物生成

---



## 注意事项

### 命名特例

- **`EFFECT_ADJUST_PREVENT_STRUCTURAL_DAMAGE`** — ModifierType 拼写为 `MODIFIER_GOVERNOR_ADJUST_PREVENET_STRUCTURAL_DAMAGE`（`PREVENT` 误拼为 `PREVENET`），为游戏内部保留错误，引用时需原样使用。
- **`EFFECT_ADJUST_PLAYER_FEAUTE_REQUIRED_FOR_SPECIALTY_DISTRICTS`** — `FEAUTE` 实为 `FEATURE` 的法语拼写遗留，参数名正确为 `FeatureType`，但 EffectType/ModifierType 名称保持游戏原始拼写。
- **布尔型参数命名多样**：`Disable` / `Disabled` / `Enable` / `NoPenalties` / `NoRemove` / `NoHousing` / `HasBonus` / `CanPurchase` / `Prevent` / `ImmediateTradingPost`，用途相似但命名不同，使用时需查看具体实例中的参数名。
- **`EFFECT_ADJUST_TRAIT_AMENITY`** — 名含 `TRAIT` 但实际可通用于任何来源的宜居度调整，不限于领袖特性。

### 无数据库实例的 EffectType

以下 EffectType 在 DynamicModifiers 中注册但 Modifiers 表中无实例（效果由游戏硬编码或 Lua 调用）：

| EffectType | 声明位置 | 说明 |
|---|---|---|
| `EFFECT_ACTIVATE_VOLCANOES` | GranColombia_Maya DLC | 天启模式激活火山 |
| `EFFECT_ADJUST_GAME_REALISM_SETTING` | GranColombia_Maya DLC | 天启模式灾难等级设定 |
| `EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CURRENT_CIVIC` | Expansion1/2 DLC | 黑暗时代追赶 |
| `EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_CURRENT_TECH` | Expansion1/2 DLC | 黑暗时代追赶 |
| `EFFECT_ADJUST_PLAYER_CULTURAL_IDENTITY_PRESSURE_RADIUS_FROM_CAPITAL` | Expansion1/2 DLC | 身份压力半径 |
| `EFFECT_ADJUST_HEAL_CHARGES` | Base + DLC | 治疗/传播充能 |
| `EFFECT_GRANT_RANDOM_BASE_PROMOTION` | Base + GranColombia DLC | 随机基础晋升 |
| `EFFECT_ADD_BELIEF` | Base | 添加信条（Lua 调用） |
| `EFFECT_ADJUST_DISABLE_PATRONAGE` | Expansion1/2 DLC | 禁用伟人赞助 |
| `EFFECT_ADJUST_BONUS_RATE` | Base | 政体加成倍率 |
| `EFFECT_ADJUST_PLAYER_BID_COST_MODIFIER` | Expansion2 DLC | 世博会竞标费用 |
| `EFFECT_ADJUST_PLAYER_GOLD_INTEREST_PERCENT` | Base | 国库利率 |
| `EFFECT_ADJUST_PLAYER_SCIENCE_VICTORY_POINTS` | Expansion2 DLC | 科技胜利点数 |
| `EFFECT_ADJUST_ACCUMULATING_BONUS` | Base | 政体积蓄加成 |

### 相似效果对比

| 效果组 | 说明 |
|---|---|
| `ADJUST_TECHNOLOGY_BOOST` vs `ADJUST_CIVIC_BOOST` | 镜像效果，参数完全相同（`Amount`），前者尤里卡，后者鼓舞 |
| `*_WONDER_ERA` 系列 | 建造其他时代奇观给鼓舞/尤里卡/生产力加成三组不同效果 |
| `GRANT_RANDOM_*_BOOST_BY_ERA` vs `GRANT_RANDOM_*_BOOST_ON_NEW_ERA` | 前者可指定时代范围，后者进入新时代时触发 |
| `GRANT_PLAYER_RANDOM_TECHNOLOGY` vs `GRANT_PLAYER_SPECIFIC_TECHNOLOGY` | 前者随机，后者指定 `TechType` |
| `GRANT_ALL_TECHNOLOGY_BOOST_BY_ERA` vs `GRANT_RANDOM_TECHNOLOGY_BOOST_BY_ERA` | 前者全给，后者随机 N 个 |
| `ERA_SCORE_PER_*` 系列 | 全用 `Amount` 参数，仅触发条件不同 |
| `ADJUST_ATTACKER/DEFENDER_STRENGTH_MODIFIER` | 镜像效果，仅用于紧急事件 |
| `ADJUST_CORPS_ARMY_MODIFIED_STRENGTH` vs `ADJUST_CORPS_ARMY_PREREQ` | 前者战斗力加成，后者前置解锁，共用 `Corps`/`Domain` |
| `ADJUST_WAR_WEARINESS` | `Domestic`/`Enemy`/`Overall` 三个布尔参数分别控制 |

### 游戏模式（MODE）发现

- **天启模式（Apocalypse）** — `GranColombia_Maya` DLC：新增 `EFFECT_ACTIVATE_VOLCANOES`、`EFFECT_ADJUST_GAME_REALISM_SETTING`
- **秘密结社（Secret Societies）** — `Ethiopia` DLC：定义于 `Ethiopia_SecretSocieties_MODE.xml`，包含吸血鬼、炼金术士、夜莺、密涅瓦猫头鹰四个结社
- **英雄传说（Heroes）** — `Babylon` DLC：定义于 `Babylon_Heroes_MODE.xml`
- **戏剧时代（Dramatic Ages）** — `Byzantium_Gaul` DLC：定义于 `Byzantium_Gaul_DramaticAges_MODE.xml`
- **僵尸防御（Zombie Defense）** — `Portugal` DLC：定义于 `Portugal_GameEffects_MODE.xml`

### 特殊参数索引

| 参数 | Enum/来源 | 使用于 |
|---|---|---|
| `BonusType` | GovernmentBonus 枚举 | `EFFECT_ADJUST_FLAT_BONUS` |
| `EmergencyType` | EmergencyAlliances 枚举 | `EFFECT_PLAYER_SEND_GOLD_TO_EMERGENCIES_OF_TYPE` |
| `MechanicName` | 硬编码字符串 | `EFFECT_TRIGGER_GAME_MECHANIC` |
| `RandomEventType` | RandomEvents 枚举 | 随机事件相关效果 |
| `ResourceUsageType` | ResourceUsageType 枚举 | `EFFECT_ADJUST_CO2_GENERATION_REDUCTION` |
| `RouteType` | Routes.RouteType | `EFFECT_GRANT_ROUTE_IN_RADIUS` |
| `Source` / `SourceType` | 外交能见度来源枚举 | `EFFECT_ADD_DIPLO_VISIBILITY` |
| `PlunderType` | `PLUNDER_CULTURE` / `PLUNDER_SCIENCE` | `EFFECT_ADJUST_ADDITIONAL_PILLAGING` |
| `Corps` | `1`=军团 / `0`=军队 | 军团/军队相关效果 |
| `Domain` | `DOMAIN_LAND` / `DOMAIN_SEA` | 军团/军队相关效果 |
| `Offense` | `0`=防御 / `1`=进攻 | `EFFECT_ADJUST_PLAYER_SPY_BONUS` |
| `Description` | LOC 字符串 | `EFFECT_RIVER_ADJACENCY` |

### GovernmentBonus 类型完整列表

| BonusType | 含义 |
|---|---|
| `GOVERNMENTBONUS_COMBAT_EXPERIENCE` | 战斗经验 |
| `GOVERNMENTBONUS_DISTRICT_PRODUCTION` | 区域生产力 |
| `GOVERNMENTBONUS_ENVOYS` | 使者 |
| `GOVERNMENTBONUS_FAITH_PURCHASES` | 信仰购买折扣 |
| `GOVERNMENTBONUS_GOLD_PURCHASES` | 金币购买折扣 |
| `GOVERNMENTBONUS_GREAT_PEOPLE` | 伟人点数 |
| `GOVERNMENTBONUS_TRADE_ROUTES` | 商路容量 |
| `GOVERNMENTBONUS_UNIT_PRODUCTION` | 单位生产力 |
| `GOVERNMENTBONUS_WONDER_CONSTRUCTION` | 奇观建造 |

### EraType 标准值

`ERA_ANCIENT` / `ERA_CLASSICAL` / `ERA_MEDIEVAL` / `ERA_RENAISSANCE` / `ERA_INDUSTRIAL` / `ERA_MODERN` / `ERA_ATOMIC` / `ERA_INFORMATION` / `ERA_FUTURE`

### RandomEventType 已知值

`RANDOM_EVENT_FLOOD_1000_YEAR` / `RANDOM_EVENT_FLOOD_MAJOR` / `RANDOM_EVENT_FLOOD_MODERATE` / `RANDOM_EVENT_BLIZZARD_CRIPPLING` / `RANDOM_EVENT_BLIZZARD_SIGNIFICANT` / `RANDOM_EVENT_HURRICANE_CAT_4` / `RANDOM_EVENT_HURRICANE_CAT_5`

### WMD 类型

`WMD_NUCLEAR_DEVICE`（核装置） / `WMD_THERMONUCLEAR_DEVICE`（热核武器）

### PlunderType

`PLUNDER_CULTURE`（掠夺文化） / `PLUNDER_SCIENCE`（掠夺科技）

### RouteType

`ROUTE_ANCIENT_ROAD`（古道） / `ROUTE_MEDIEVAL_ROAD`（中世纪道路） / `ROUTE_INDUSTRIAL_ROAD`（工业道路） / `ROUTE_MODERN_ROAD`（现代道路）
