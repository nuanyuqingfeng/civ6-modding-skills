# modifier-yield — 产出修改类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

---

## EFFECT_ADD_PLAYER_BELIEF_YIELD

为玩家的已创立宗教附加一条信条产出效果。玩家创立宗教后，该文明自动获得该信条类型的产出，等同于该宗教额外拥有了一条指定类型的信条。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ADD_PLAYER_BELIEF_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BeliefYieldType` | **必写** | 信条产出类型。`BELIEF_YIELD_PER_FOREIGN_CITY` / `BELIEF_YIELD_PER_CITY` / `BELIEF_YIELD_PER_FOLLOWER` 等（值来自数据库 Beliefs 表的 BeliefYieldType 列） |
| `YieldType` | **必写** | 产出类型，单值，不支持逗号分隔 |
| `Amount` | **必写** | 每触发单位的产出值（整数） |
| `PerXItems` | **必写** | 每 X 个单位计一次产出（通常为 1） |

> **溯源**：阿拉伯文明"最后的先知" — 每座信仰阿拉伯宗教的外国城市为阿拉伯提供 +1 科技（`TRAIT_SCIENCE_PER_FOREIGN_CITY_FOLLOWING_RELIGION` → TraitModifiers → `TRAIT_CIVILIZATION_LAST_PROPHET`）。参数组合：`BeliefYieldType=BELIEF_YIELD_PER_FOREIGN_CITY`，`YieldType=YIELD_SCIENCE`，`Amount=1`，`PerXItems=1`。

---

## EFFECT_ADJUST_CITY_ALL_YIELDS_CHANGE

为城市的所有六种产出统一加上固定值。无需指定 YieldType，一次性修改全部。受 `SubjectRequirementSetId` 控制可限定目标城市（如首都、有特定建筑的城）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_ALL_YIELDS_CHANGE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 产出值（整数），同时加给六种产出 |

> **溯源**：独裁政体 — 首都 +1 全产出、第一级政府区建筑所在城市 +1 全产出（`AUTOCRACY_CAPITAL` / `AUTOCRACY_TIER1` → GovernmentModifiers → `GOVERNMENT_AUTOCRACY`；同时也在 PolicyModifiers → `POLICY_GOV_AUTOCRACY` 以提供传承卡效果）。参数：`Amount=1`，分别搭配 `SubjectRequirementSetId=BUILDING_IS_PALACE` 或 `BUILDING_IS_TIER1`。

---

## EFFECT_ADJUST_CITY_YIELD_CHANGE

调整城市单项产出（**绝对值**）。产出直接加在城市面板上，玩家可见。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_YIELD_CHANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_ALL_CITIES_ADJUST_CITY_YIELD_CHANGE` | `COLLECTION_ALL_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型。可逗号分隔写多个（此时 `Amount` 也需对应逗号分隔）；**嵌套（ATTACH 链内层）必须拆多条，见下方警告** |
| `Amount` | **必写** | 产出值（整数）。多个 YieldType 时一一对应逗号分隔 |

> **溯源**：
> - 政策"城市规划" — 所有城市 +1 生产力（`URBAN_PLANNING_ALLCITYPRODUCTION` → PolicyModifiers → `POLICY_URBAN_PLANNING`）
> - 政策"君权神授" — 首都 +1 金币、+1 信仰（`GOD_KING_GOLD` / `GOD_KING_FAITH` → PolicyModifiers → `POLICY_GOD_KING`）
> - 建筑"纪念碑" — 满忠诚度时额外 +1 文化（`MONUMENT_CULTURE_AT_FULL_LOYALTY` → BuildingModifiers → `BUILDING_MONUMENT`）
>
> **逗号分隔实例（DB 验证）**：`MODIFIER_POLICY_SIQI_TOP_AUTHORITY_CITY_YIELDS_CHANGE_HAS_PALACE` 使用 `YieldType=YIELD_SCIENCE, YIELD_CULTURE, YIELD_GOLD, YIELD_FAITH, YIELD_PRODUCTION, YIELD_FOOD` 配合 `Amount=2, 2, 2, 2, 2, 2`。
>
> ⚠️ **实测（0052 花太郎）：逗号连写在直接挂载时可用，但嵌套在 ATTACH 链内层时（`ATTACH → MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_CHANGE`，`YieldType='YIELD_FOOD,YIELD_PRODUCTION'` + 单个 `Amount=4`）只生效第一个产出（食物），疑似底层嵌套上下文解析问题**。规范：嵌套/ATTACH 内层必须拆成多条 Modifier 分开写（0052 最终形态：`ATTACH_PER_CITY_FOOD_4` / `ATTACH_PER_CITY_PRODUCTION_4` 两个外层 + 各带单一 YieldType 的内层）。

---

## EFFECT_ADJUST_CITY_YIELD_MODIFIER

调整城市单项产出（**百分比加成**）。百分比基于产出总面板值计算。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型。支持逗号分隔写多个，此时 `Amount` 也需对应逗号分隔 |
| `Amount` | **必写** | 百分比值（20 = +20%）。负数表示衰减 |

> **溯源**：
> - 建筑"百老汇" — 所在城市 +20% 文化（`BROADWAY_ADDCULTUREYIELD` → BuildingModifiers → `BUILDING_BROADWAY`）
> - 建筑"牛津大学" — 所在城市 +20% 科技（`OXFORD_ADDSCIENCEYIELD` → BuildingModifiers → `BUILDING_OXFORD_UNIVERSITY`）
> - 政策"殖民地税收" — 所有城市 +25% 金币（`COLONIALTAXES_FOREIGNGOLD` → PolicyModifiers → `POLICY_COLONIAL_TAXES`）
> - 总督"图书管理员" — 所在城市 +15% 科技（`LIBRARIAN_SCIENCE_YIELD_BONUS` → GovernorPromotionModifiers → `GOVERNOR_PROMOTION_EDUCATOR_LIBRARIAN`）
> - 玛雅领袖"穆塔尔城邦之女" — 首都 6 格内城市全产出 +10%，6 格外 -15%（`TRAIT_LEADER_NEARBY_CITIES_GAIN/LOSE_YIELDS` → TraitModifiers → `TRAIT_LEADER_MUTAL`）。逗号分隔：`YieldType=YIELD_PRODUCTION, YIELD_FOOD, YIELD_SCIENCE, YIELD_CULTURE, YIELD_GOLD, YIELD_FAITH`，`Amount=10, 10, 10, 10, 10, 10`。
>
> `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_CITY_YIELD_MODIFIER`（`COLLECTION_PLAYER_CAPITAL_CITY`）在 Modifiers.xml 中定义了类型，但**数据库和官方 XML 中无任何实例使用**。无原生的 `MODIFIER_ALL_CITIES_ADJUST_CITY_YIELD_MODIFIER`。

---

## EFFECT_ADJUST_FOLLOWER_YIELD_MODIFIER

信条效果：每座信仰该宗教的城市为该宗教创立者提供产出百分比加成。不是按人口或信徒数，而是按信仰城市数叠加。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_FOLLOWER_YIELD_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每城市的百分比值（1 = +1% 每座信仰城市） |

> **溯源**：信条"职业道德" — 每座信仰该宗教的城市 +1% 生产力（`WORK_ETHIC_FOLLOWER_PRODUCTION_MODIFIER` → 由 `WORK_ETHIC_FOLLOWER_PRODUCTION`（`MODIFIER_ALL_CITIES_ATTACH_MODIFIER`）以 ModifierId 参数挂载 → BeliefModifiers → `BELIEF_WORK_ETHIC`）。注意：这是一个**两步挂载**模式——信条表挂载父级 Attach 修饰符，父级再通过 ModifierId 参数附加上这个实际效果修饰符。

---

## EFFECT_ADJUST_PLAYER_ADD_CHOP_YIELD

调整移除地貌/资源时额外获得的产出（百分比）。仅风云变幻（Gathering Storm）及以上版本可用。注意 CollectionType 为 `COLLECTION_MAJOR_PLAYERS`。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYERS_ADD_CHOP_YIELD` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 百分比值（100 = +100%） |

> **溯源**：世界议会决议"禁止砍伐森林条约" — 砍伐收益 +100% 金币（`WC_RES_DEFORESTATION_GOLD` → ResolutionEffects 表 → `WC_RES_DEFORESTATION_TREATY`）。参数：`YieldType=YIELD_GOLD`，`Amount=100`。

---

## EFFECT_ADJUST_PLAYER_COUNTER_SPY_YIELD_AWARD_PER_LEVEL

反间谍成功后，按被反间谍的等级给予一次性产出奖励。仅埃塞俄比亚包及以上版本可用。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_COUNTER_SPY_AWARD_YIELD_PER_LEVEL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每等级的产出值（整数） |
| `PerXLevels` | **必写** | 每 X 级给一份 Amount（通常为 1） |

> **溯源**：建筑"外交办" — 反间谍成功时按间谍等级获得 +50 科技/级（`CHANCERY_COUNTERYSPY_SCIENCE` → BuildingModifiers → `BUILDING_CHANCERY`）。参数：`YieldType=YIELD_SCIENCE`，`Amount=50`，`PerXLevels=1`。3 级间谍被反制 = 150 科技。

---

## EFFECT_ADJUST_PLAYER_YIELD_CHANGE

调整玩家全局产出（**绝对值**）。作用于玩家级别，不走城市面板，直接加入总产出。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_CHANGE` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_PLAYERS_YIELD_PER_TURN` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值（DB 中未发现逗号分隔实例） |
| `Amount` | **必写** | 产出值（整数） |

> **溯源**：
> - 毛利领袖"库佩的远航" — 开局定居前每回合 +2 科技、+2 文化（`SCIENCE_PRESETTLEMENT` / `CULTURE_PRESETTLEMENT` → TraitModifiers → `TRAIT_LEADER_KUPES_VOYAGE`）
> - 紧急事件"定居紧急" — 成员每回合 +1 金币（`SETTLEMENT_EMERGENCY_MEMBER_GPT_REWARD` → 使用 `MODIFIER_EMERGENCY_PLAYERS_YIELD_PER_TURN`，CollectionType 为 `COLLECTION_EMERGENCY_PLAYERS`）
>
> 与 `EFFECT_ADJUST_CITY_YIELD_CHANGE` 的区别：本效果是**玩家级别**全局加成，不在城市面板显示；`_CITY_YIELD_CHANGE` 是城市级别，面板可见。

---

## EFFECT_ADJUST_PLAYER_YIELD_CHANGE_PER_TRIBUTARY

每个宗主城邦提供额外产出（**绝对值**）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_CHANGE_PER_TRIBUTARY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值。复数产出需多条 Modifier |
| `Amount` | **必写** | 每宗主城邦的产出值（整数） |

> **溯源**：政策"统治" — 每宗主城邦 +2 金币（`RAJ_GOLDPERTRIBUTARY` → PolicyModifiers → `POLICY_RAJ`）。同政策还有 `RAJ_FAITHPERTRIBUTARY`（+2 信仰）、`RAJ_SCIENCEPERTRIBUTARY`（+2 科技）、`RAJ_CULTUREPERTRIBUTARY`（+2 文化），分别用四条 Modifier 实现四种产出。

---

## EFFECT_ADJUST_PLAYER_YIELD_MODIFIER_PER_TRIBUTARY

每个宗主城邦提供产出**百分比加成**。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_MODIFIER_PER_TRIBUTARY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 百分比值（5 = +5% 每宗主城邦） |

> **溯源**：
> - 领袖特性"荣耀之围" — 每宗主城邦 +5% 文化（`TRAIT_CULTURE_PER_CITY_STATE_TRIBUTARY` → TraitModifiers → `TRAIT_LEADER_SURROUNDED_BY_GLORY`）
> - 政策"集体行动主义" — 每宗主城邦 +5% 文化（`COLLECTIVEACTIVISM_CULTUREPERTRIBUTARY` → PolicyModifiers → `POLICY_COLLECTIVE_ACTIVISM`）
> - 政策"国际宇航局" — 每宗主城邦 +5% 科技（`INTERNATIONALSPACEAGENCY_SCIENCEPERTRIBUTARY` → PolicyModifiers → `POLICY_INTERNATIONAL_SPACE_AGENCY`）

---

## EFFECT_ADJUST_WONDER_YIELD_CHANGE

调整建造在该城市的奇观提供的产出（**绝对值**）。本效果命名为 `_CHANGE`，表示绝对值加成，而非百分比。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_ADJUST_WONDER_YIELD_CHANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_WONDER_YIELD_CHANGE` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 产出值（整数） |

> **溯源**：信条"神圣启示" — 每座奇观 +4 信仰（`DIVINE_INSPIRATION_WONDER_FAITH_MODIFIER` → 由 `DIVINE_INSPIRATION_WONDER_FAITH`（`MODIFIER_ALL_CITIES_ATTACH_MODIFIER`）以 ModifierId 参数挂载 → BeliefModifiers → `BELIEF_DIVINE_INSPIRATION`）。同样是**两步挂载**：信条挂 Attach 修饰符，Attach 修饰符再挂实际效果。

---

## EFFECT_GRANT_YIELD

一次性授予玩家一笔产出。通常配合 `RunOnce="true"` `Permanent="true"` 使用，或用于伟人一次性激活效果。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_YIELD` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_PLAYERS_GRANT_YIELD` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 产出值（整数）。可带 `Type="ScaleByGameSpeed"` 属性，按游戏速度缩放 |
| `Scale` | 选写 | 布尔值（`true`），按游戏速度缩放 Amount。与 `Amount.Type="ScaleByGameSpeed"` 是**互斥**的两种缩放方式 |

> **溯源**：
> - 部落村庄大奖 — 一次性 +120 金币（`GOODY_GOLD_LARGE_MODIFIER`）。使用 `Scale=true`（Boolean 参数方式缩放）
> - 伟人"科莱欧斯"激活 — 一次性 +100 信仰（`GREATPERSON_FAITH_SMALL` → GreatPersonIndividualActionModifiers → `GREAT_PERSON_INDIVIDUAL_COLAEUS`）。使用 `Amount=100, Type=ScaleByGameSpeed`（参数级别类型标记方式缩放）
> - 伟人"雅各布·富格尔"激活 — 一次性 +200 金币（`GREATPERSON_GOLD_SMALL` → GreatPersonIndividualActionModifiers → `GREAT_PERSON_INDIVIDUAL_JAKOB_FUGGER`）。使用 `Amount=200, Type=ScaleByGameSpeed`
>
> `Scale=true` 和 `Amount.Type="ScaleByGameSpeed"` 本质都按游戏速度缩放（联机速度 33%、马拉松 300%），但实现路径不同。实际使用中二选一，**官方从不同时使用**。`MODIFIER_EMERGENCY_PLAYERS_GRANT_YIELD` 用于紧急事件中一次性发放产出。

---

## EFFECT_GRANT_YIELD_BASED_ON_CURRENT_YIELD_RATE

以玩家当前的某项**产出速率**为基准，一次性发放另一项产出。计算公式：发放量 = 当前产出速率 x Multiplier。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_YIELD_BASED_ON_CURRENT_YIELD_RATE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldToGrant` | **必写** | 要发放的产出类型（注意：不是 `YieldType`） |
| `YieldToBaseOn` | **必写** | 依据的产出类型（取玩家当前该产出速率） |
| `Multiplier` | 选写 | 倍率（整数，默认 1） |

> **溯源**：
> - 项目"登月计划"完成 — 基于当前科技产出速率，一次性获得 10 倍的文化（`PROJECT_COMPLETION_GRANT_CULTURE_BASED_ON_SCIENCE_RATE` → ProjectCompletionModifiers → `PROJECT_LAUNCH_MOON_LANDING`）。参数：`YieldToGrant=YIELD_CULTURE`，`YieldToBaseOn=YIELD_SCIENCE`，`Multiplier=10`
> - 朝鲜领袖"世宗" — 古典时代起完成科技时获得 2 倍的文化（`SEJONG_CLASSICAL_SCIENCE_INTO_CULTURE` 等 → TraitModifiers → `TRAIT_LEADER_SEJONG`）。参数：`YieldToGrant=YIELD_CULTURE`，`YieldToBaseOn=YIELD_SCIENCE`，`Multiplier=2`

---

## EFFECT_GRANT_YIELD_PER_EXCESS_LUXURIES

每拥有一种多余奢侈资源，一次性发放产出。仅凯瑟琳美第奇 DLC 及以上版本可用。通常搭配 `RunOnce="true"` `Permanent="true"` 用于项目完成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_YIELD_PER_EXCESS_LUXURIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每多余奢侈资源的产出值（整数） |

> **溯源**：项目"宫廷盛宴"完成 — 每种多余奢侈资源提供 +50 文化（`PROJECT_COMPLETION_GRANT_CULTURE_BASED_ON_EXCESS_LUXURIES` → ProjectCompletionModifiers → `PROJECT_COURT_FESTIVAL`）。参数：`YieldType=YIELD_CULTURE`，`Amount=50`。

---

## EFFECT_GRANT_YIELD_PER_FEATURE_IN_CITY

城市范围内按**指定地貌类型**的地块数量，一次性发放产出。首次出现于拜占庭/高卢 DLC。通常搭配 `RunOnce="true"` `Permanent="true"`。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_GRANT_YIELD_PER_FEATURE_TYPE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每块该地貌地块的产出值（整数） |
| `FeatureType` | **必写** | 统计的地貌类型：`FEATURE_JUNGLE` / `FEATURE_MARSH` / `FEATURE_FOREST` 等（FeatureType.txt） |

> **溯源**：建筑"生物圈" — 城市内每块雨林/沼泽/森林 +100 科技（`BIOSPHERE_GRANT_SCIENCE_PER_RAINFOREST` 等 → BuildingModifiers → `BUILDING_BIOSPHERE`）。每种地貌用一条独立的 Modifier：`FeatureType=FEATURE_JUNGLE` 及 `YieldType=YIELD_SCIENCE`、`Amount=100`。

---

## EFFECT_GRANT_YIELD_PER_GREAT_WORK_IN_CITY

城市内每有一个指定类型的巨作，提供一次性产出。通常搭配 `RunOnce="true"` `Permanent="true"` 或用于伟人激活。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_SINGLE_CITY_GRANT_YIELD_PER_GREAT_WORK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每巨作的产出值（整数）。可带 `Type="ScaleByGameSpeed"` |
| `GreatWorkObjectType` | **必写** | 限定巨作类型：`GREATWORKOBJECT_WRITING` / `PORTRAIT` / `LANDSCAPE` / `SCULPTURE` / `RELIGIOUS` / `ARTIFACT` / `MUSIC` / `RELIC`（GreatWorkObjectType.txt） |

> **溯源**：伟人"玛丽·利基"激活 — 每件文物 +350 科技（`GREATPERSON_ARTIFACT_SCIENCE` → GreatPersonIndividualActionModifiers → `GREAT_PERSON_INDIVIDUAL_MARY_LEAKEY`）。参数：`YieldType=YIELD_SCIENCE`，`Amount=350(ScaleByGameSpeed)`，`GreatWorkObjectType=GREATWORKOBJECT_ARTIFACT`。

---

## EFFECT_PLAYER_ADJUST_YIELD_FROM_DELEGATIONS

调整每份来自其他文明的**代表团**所提供的产出加成（绝对值）。仅埃塞俄比亚包及以上版本可用。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_FROM_DELEGATIONS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每份代表团的产出值（整数） |

> **溯源**：区域"外交区" — 每份代表团 +1 文化（`DIPLOMATIC_QUARTER_DELEGATION_CULTURE` → DistrictModifiers → `DISTRICT_DIPLOMATIC_QUARTER`）。参数：`YieldType=YIELD_CULTURE`，`Amount=1`。

---

## EFFECT_PLAYER_ADJUST_YIELD_FROM_EMBASSIES

调整每份来自其他文明的**大使馆**所提供的产出加成（绝对值）。仅埃塞俄比亚包及以上版本可用。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_FROM_EMBASSIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `YieldType` | **必写** | 产出类型，单值 |
| `Amount` | **必写** | 每份大使馆的产出值（整数） |

> **溯源**：区域"外交区" — 每份大使馆 +1 文化（`DIPLOMATIC_QUARTER_EMBASSY_CULTURE` → DistrictModifiers → `DISTRICT_DIPLOMATIC_QUARTER`）。参数：`YieldType=YIELD_CULTURE`，`Amount=1`。与 `EFFECT_PLAYER_ADJUST_YIELD_FROM_DELEGATIONS` 结构完全相同，仅作用对象不同。

---

## 注意事项

### _CHANGE 与 _MODIFIER 的准确区分

通过上游主体用法反推，命名中的后缀含义如下：

| 后缀 | 含义 | 示例 |
|------|------|------|
| `_CHANGE` | **绝对值**（+3 科技） | `EFFECT_ADJUST_CITY_YIELD_CHANGE` — 城市规划 +1 生产力 |
| `_MODIFIER` | **百分比**（+20% 科技） | `EFFECT_ADJUST_CITY_YIELD_MODIFIER` — 牛津大学 +20% 科技 |

例外：`EFFECT_ADJUST_WONDER_YIELD_CHANGE` 名为 `_CHANGE` 但只对奇观产出生效，容易被误认为"奇观产出百分比"。实际上它是绝对值：神圣启示 +4 信仰/奇观。

### YieldType 逗号分隔支持情况

以下 EffectType 在数据库中有**已验证**的逗号分隔多 YieldType 用法（同时 Amount 也需逗号分隔对应）：

| EffectType | 验证实例 |
|-----------|---------|
| `EFFECT_ADJUST_CITY_YIELD_CHANGE` | `MODIFIER_POLICY_SIQI_TOP_AUTHORITY_CITY_YIELDS_CHANGE_HAS_PALACE` — 六种产出逗号分隔 |
| `EFFECT_ADJUST_CITY_YIELD_MODIFIER` | `TRAIT_LEADER_NEARBY_CITIES_GAIN_YIELDS` — 六种产出逗号分隔 |

以下 EffectType 在数据库和官方 XML **未发现**逗号分隔实例：

- `EFFECT_ADJUST_PLAYER_YIELD_CHANGE` — 无逗号分隔实例
- `EFFECT_ADJUST_PLAYER_YIELD_CHANGE_PER_TRIBUTARY` — 官方用多条 Modifier 分别实现
- `EFFECT_ADJUST_PLAYER_YIELD_MODIFIER_PER_TRIBUTARY` — 无逗号分隔实例
- `EFFECT_ADJUST_WONDER_YIELD_CHANGE` — 无逗号分隔实例
- `EFFECT_GRANT_YIELD` — 无逗号分隔实例

以下 EffectType 参数结构不兼容逗号分隔：

- `EFFECT_GRANT_YIELD_BASED_ON_CURRENT_YIELD_RATE` — 参数名为 `YieldToGrant` / `YieldToBaseOn`，单值设计
- `EFFECT_ADD_PLAYER_BELIEF_YIELD` — 依赖 `BeliefYieldType` 引用，单值设计

### EFFECT_GRANT_YIELD 的两种缩放方式

- **Boolean 参数 `Scale`**：在 ModifierArguments 中添加 `Scale=true`。官方用于 GOODY_*（部落村庄）系列
- **Amount 列 `Type="ScaleByGameSpeed"`**：在 `Amount` 参数的 Type 属性标记。官方用于 GREATPERSON_*（伟人激活）系列
- **互斥**：两种方式从未在同一 Modifier 中混用，实际开发中应二选一

### 效果选择快速参考

| 场景 | 用这个 | 而非 |
|------|--------|------|
| 城市面板可见的绝对值加成 | `EFFECT_ADJUST_CITY_YIELD_CHANGE` | `EFFECT_ADJUST_PLAYER_YIELD_CHANGE`（后者玩家级，不显示在城市面板） |
| 百分比加成 | `EFFECT_ADJUST_CITY_YIELD_MODIFIER` | `EFFECT_ADJUST_CITY_YIELD_CHANGE` |
| 一次性发放 | `EFFECT_GRANT_YIELD` | `EFFECT_ADJUST_PLAYER_YIELD_CHANGE`（后者持续性） |
| 所有六种产出统一修改 | `EFFECT_ADJUST_CITY_ALL_YIELDS_CHANGE` | `EFFECT_ADJUST_CITY_YIELD_CHANGE` x 6（前者一条即可） |
| 基于产出速率发放 | `EFFECT_GRANT_YIELD_BASED_ON_CURRENT_YIELD_RATE` | `EFFECT_GRANT_YIELD`（前者动态计算） |
| 按信条产出类型附加 | `EFFECT_ADD_PLAYER_BELIEF_YIELD` | `EFFECT_ADD_RELIGIOUS_BELIEF_YIELD`（姊妹效果，本 Effect 用于领袖/文明，后者用于信条自身） |
| 信条-每城市百分比 | `EFFECT_ADJUST_FOLLOWER_YIELD_MODIFIER` | `EFFECT_ADJUST_CITY_YIELD_MODIFIER`（前者按信仰城市数量叠加） |
| 奇观产出绝对值 | `EFFECT_ADJUST_WONDER_YIELD_CHANGE` | `EFFECT_ADJUST_CITY_YIELD_CHANGE`（后者不限定奇观） |
| 砍伐加成 | `EFFECT_ADJUST_PLAYER_ADD_CHOP_YIELD` | — |
| 反间谍奖励 | `EFFECT_ADJUST_PLAYER_COUNTER_SPY_YIELD_AWARD_PER_LEVEL` | — |
| 每宗主城邦绝对值 | `EFFECT_ADJUST_PLAYER_YIELD_CHANGE_PER_TRIBUTARY` | `EFFECT_ADJUST_PLAYER_YIELD_MODIFIER_PER_TRIBUTARY`（后者为百分比） |
| 每宗主城邦百分比 | `EFFECT_ADJUST_PLAYER_YIELD_MODIFIER_PER_TRIBUTARY` | `EFFECT_ADJUST_PLAYER_YIELD_CHANGE_PER_TRIBUTARY`（前者为百分比） |
| 按巨作数量给产出 | `EFFECT_GRANT_YIELD_PER_GREAT_WORK_IN_CITY` | `EFFECT_GRANT_YIELD`（前者按巨作数量叠加） |
| 按地貌地块数给产出 | `EFFECT_GRANT_YIELD_PER_FEATURE_IN_CITY` | `EFFECT_ADJUST_CITY_YIELD_CHANGE`（前者动态计数） |
| 按多余奢侈资源给产出 | `EFFECT_GRANT_YIELD_PER_EXCESS_LUXURIES` | `EFFECT_GRANT_YIELD`（前者动态计数） |
| 代表团/大使馆产出 | `EFFECT_PLAYER_ADJUST_YIELD_FROM_DELEGATIONS` / `_EMBASSIES` | `EFFECT_ADJUST_PLAYER_YIELD_CHANGE`（前者按外交关系数量叠加） |
