# modifier-diplomacy -- 外交/影响力/使者/不满/议程类 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 历史 CSV 来源未随包分发；推定参数和历史可用范围须按 [资料依据](../../SOURCES.md) 核实，不能直接作为已验证结论。

共 ~85 个 EffectType，分为 10 大类：
- **外交行动**: 禁用/偏好/覆盖外交行为
- **外交产出修正**: 因外交事件获得外交产出 buff/debuff
- **外交能见度**: 外交能见度等级及战斗加成
- **外交支持**: Favor 点数获取、调整、倍率
- **外交分数**: 外交胜利计分调整
- **不满值/战争狂**: Grievance/Warmonger 相关
- **影响力/使者**: Influence Token 和 Envoy 相关
- **议程**: 领袖议程相关的双边关系修正
- **外交状态**: 双边关系的动态变化 (承诺/违约/间谍/定居/战争等)

> **注意**: 标记 `[未在数据库中活跃使用]` 的 EffectType 表示在当前 DebugGameplay.sqlite 的 Modifiers 表中无实例，但 EffectType 本身存在于 Effects.csv 且可在 Mod 中使用。标记 `[无官方使用示例，但 Mod 中可用]` 的 EffectType 为 Modding Companion 的 USER ADDED 条目，ModifierType 存在但无官方数据库实例，非 Firaxis 原生效果，使用时需自行测试。

---

## 外交行动

### EFFECT_ADD_DIPLOMATIC_ACTION_OVERRIDE

允许玩家执行原本不可用的外交行动（如通过市政解锁特殊宣战理由）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_DIPLOMATIC_ACTION_OVERRIDE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `CivicType` | 来源指定 | `CIVIC_*` — 触发该覆盖的市政 |
| `DiplomaticAction` | **必写** | `DIPLOACTION_*` — 允许执行的外交行动 |

> 原版示例：通过 `CIVIC_DEFENSIVE_TACTICS` 解锁 `DIPLOACTION_DECLARE_LIBERATION_WAR`。
>
> 可选值来自 `DiplomaticActions` 表（`DiplomaticActionType` 列），含宣战理由、联盟、使馆、边界开放、交易等 45 种行动，不限于宣战类。

---

### EFFECT_ADJUST_DIPLOMATIC_ACTION_PREFERENCE

调整AI对外交行动的偏好（倾向/回避某类行动）。支持逗号分隔多个外交行动。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ADJUST_DIPLOMATIC_ACTION_PREFERENCE` | `COLLECTION_ALL_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Action` | **必写** | `DIPLOACTION_*` — 可多个以逗号分隔 |
| `Favored` | **必写** | `0` = 回避, `1` = 倾向 |

> 数据库中有活跃使用（如 `TRAIT_BEFRIEND_MINOR_CIV_HOME_CONTINENT`），确认支持逗号分隔多个外交行动。

---

### EFFECT_ADJUST_BANNED_DIPLOMATIC_ACTIONS

禁止某一类外交行动。数据库中有活跃使用（如禁止突袭战争）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_BANNED_DIPLOMATIC_ACTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Banned` | **必写** | `true` = 禁止, `false` = 允许 |
| `DiplomaticActionType` | **必写** | `DiplomaticActions.DiplomaticActionType` — 如 `DIPLOACTION_DECLARE_SURPRISE_WAR` |

> 引用 `DiplomaticActions` 表的 `DiplomaticActionType` 列。注意与 #1 `EFFECT_ADD_DIPLOMATIC_ACTION_OVERRIDE` 的参数名不同（`DiplomaticActionType` vs `DiplomaticAction`），但引用同一张表。

---

### EFFECT_ADJUST_BANNED_DIPLOMATIC_ACTIONS_SPECIFIC_CIVILIZATION

禁止对特定文明执行某类外交行动。数据库中有活跃使用（如 Siqi Myrtle 文明之间的突袭战争限制）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_BANNED_DIPLOMATIC_ACTION_SPECIFIC_CIVILIZATION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `CivilizationType` | **必写** | `Civilizations.CivilizationType` — 目标文明 |
| `DiplomaticActionType` | **必写** | `DiplomaticActions.DiplomaticActionType` — 被禁的外交行动类型 |

---

## 外交产出修正

### EFFECT_ADD_DIPLOMATIC_COMBAT_MODIFIER

因外交事件（如发动领土扩张战争）获得外交战斗加成。

> 此 EffectType 存在于 Effects.csv 中，但在游戏 C++ 逻辑中定义，数据库中无参数结构可查。以下参数为从实际使用实例（`TRAIT_TERRITORIAL_WAR_COMBAT`）搜集推定。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_DIPLOMATIC_COMBAT_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 战斗加成值 |
| `DiplomaticYieldSource` | **必写** | `TERRITORIAL_EXPANSION_WAR_INITIATED` / `SURPRISE_WAR_INITIATED` / `CITY_CAPTURED` 等 |
| `ReligiousOnly` | 可选 | `0` = 所有单位, `1` = 仅宗教单位 |
| `TurnsActive` | **必写** | 整数 — 持续回合数 |

---

### EFFECT_ADD_DIPLOMATIC_MOVEMENT_MODIFIER

因外交事件获得外交移动力加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_DIPLOMATIC_MOVEMENT_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 移动力加成值 |
| `DiplomaticYieldSource` | **必写** | 同 `EFFECT_ADD_DIPLOMATIC_COMBAT_MODIFIER` |
| `TurnsActive` | **必写** | 整数 — 持续回合数 |

---

### EFFECT_ADD_DIPLOMATIC_YIELD_MODIFIER

因外交事件获得产出加成（如占领城市后 +20% 生产力）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_DIPLOMATIC_YIELD_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 产出加成百分比 |
| `DiplomaticYieldSource` | **必写** | 同 `EFFECT_ADD_DIPLOMATIC_COMBAT_MODIFIER` |
| `StackWithOtherDiploYieldModifiers` | 可选 | `0` = 不可叠加, `1` = 可叠加 |
| `TurnsActive` | **必写** | 整数 — 持续回合数 |
| `YieldType` | **必写** | `YIELD_PRODUCTION` / `YIELD_GOLD` / `YIELD_SCIENCE` 等 |

---

## 外交能见度

### EFFECT_ADD_DIPLO_VISIBILITY

增加外交能见度等级。每个能见度等级在战斗时提供 +3 战斗力（随等级差浮动）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_DIPLO_VISIBILITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 能见度等级增量。示例值: `1`（商路驿站特质）, `2`（印刷术科技） |
| `Source` | **必写** | 标识来源。官方值: `SOURCE_ALLY` / `SOURCE_DELEGATE` / `SOURCE_GREAT_PERSON_JOURNALISM` / `SOURCE_SPY` / `SOURCE_TECH` / `SOURCE_TRADER` / `SOURCE_TRADING_POST_TRAIT` / `SOURCE_TRAIT`。可自定义，但需在新表（`DiploVisibilitySources`）定义其文本 |
| `SourceType` | **必写** | `DIPLO_SOURCE_ALL_NAMES` / `DIPLO_SOURCE_FEMALE_ONLY` — 固定二选一 |

> `Source` 参数如使用自定义值，须参考 Core Mod 写法，在 `DiploVisibilitySources` 表中新增条目并提供 `LOC_` 文本。

---

### EFFECT_ADJUST_UNIT_DIPLO_VISIBILITY_COMBAT_MODIFIER

根据与对手的外交能见度等级差，额外调整单位战斗力。游戏默认机制：每级能见度差提供 +3 战斗力，此效果设置 `Amount=3` 即在此基础上翻倍（每级差共 +6）。`Amount=6` 则为三倍。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_UNITS_ADJUST_DIPLO_VISIBILITY_COMBAT_MODIFIER` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_ALL_UNITS_ADJUST_DIPLO_VISIBILITY_COMBAT_MODIFIER` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每级能见度差的额外战斗力。注意：游戏默认 +3，`Amount=3` 相当于x2（总 +6/级），`Amount=6` 相当于x3。示例值: `3` |

> `DeltaWithOpponent` 在 Effects.csv 中无记录，一般不写。蒙古特色能力即使用此效果（骑兵按能见度差获得战斗力）。

---

## 外交支持 (Favor)

### EFFECT_ADD_PLAYER_FAVOR

直接给予玩家外交支持点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADD_FAVOR` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_PLAYERS_ADD_FAVOR` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 数量。示例值: `50` (市政), `100` (紧急事件参与者) |

---

### EFFECT_ADJUST_PLAYER_EXTRA_FAVOR_PER_TURN

每回合额外获得外交支持点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_EXTRA_FAVOR_PER_TURN` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_FAVOR_PER_TURN` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每回合 Favor 增量。示例值: `1`~`3` |

---

### EFFECT_ADJUST_PLAYER_DIPLOMATIC_VICTORY_POINTS

调整外交胜利点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_DIPLOMATIC_VICTORY_POINTS` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_PLAYERS_ADJUST_DIPLOMATIC_VICTORY_POINTS` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 外交胜利点数值。示例值: `1`~`4` |
| `Tooltip` | 可选 | `LOC_*` — 来源说明文本 |
| `VictoryResolution` | 可选 | `1` = 通过决议获得, `0` = 非决议来源 |

> 文本示例（在 ModifierStrings 表中用 `Preview` 上下文）:
> ```
> INSERT INTO ModifierStrings (ModifierId, Context, Text)
> VALUES ('MY_DIPLO_VICTORY_POINTS', 'Preview', 'LOC_DIPLO_VICTORY_POINTS_PREVIEW_TEXT');
> ```
> 常用于奇观（自由女神像、摩诃菩提寺、布达拉宫）和计分竞赛。

---

### EFFECT_ADJUST_PLAYER_EMERGENCY_FAVOR_MODIFIER

调整从紧急事件中获得的外交支持倍率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_EMERGENCY_FAVOR_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 百分比修正值。示例值: `100` (即 x2) |
| `Member` | 可选 | `0` = 通用, `1` = 仅针对紧急事件成员身份 |

> 数据库活跃实例: `TRAIT_EMERGENCY_FAVOR_MODIFIER`（Amount=100, Member=1）。见于 Gathering Storm / New Frontier。

---

### EFFECT_ADJUST_PLAYER_FAVOR_REFUND_FOR_SUCCESSFUL_RESOLUTION

对成功的世界议会决议退还部分外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FAVOR_REFUND_FOR_SUCCESSFUL_RESOLUTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Percent` | **必写** | 整数 — 退还百分比。示例值: `50` (退还 50%) |
| `ResolutionType` | **必写** | `WC_RES_*` — 指定的决议类型 |
| `WhichEffect` | 可选 | 整数 — 决议中的第几项效果 |

---

### EFFECT_ADJUST_PLAYER_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR

根据政体槽位类型提供外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GOVERNMENT_SLOT_TYPE_GRANT_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每个对应槽位提供的 Favor 数 |
| `GovernmentSlotType` | **必写** | `SLOT_WILDCARD` / `SLOT_MILITARY` / `SLOT_ECONOMIC` / `SLOT_DIPLOMATIC` |

> 数据库活跃实例: `TRAIT_WILD_CARD_FAVOR`（美国政府首脑特质，每个 `SLOT_WILDCARD` 通配符槽位 +1 Favor）。见于 Gathering Storm / New Frontier。

---

### EFFECT_ADJUST_PLAYER_GOVERNOR_FAVOR

任命/晋升指定总督时获得外交支持。设 `Neutralize=1` 则改为抵消该总督类型的负面效果。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_GOVERNOR_FAVOR` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `FavorAmount` | **必写** | 整数 — 每次晋升获得的 Favor 量。示例值: `3` |
| `GovernorType` | **必写** | `Governors.GovernorType` — 指定总督类型。示例值: `GOVERNOR_THE_EDUCATOR` |
| `Neutralize` | 可选 | `0` = 不抵消, `1` = 抵消指定总督类型的负面效果 |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_GOVERNOR_FAVOR 行（Gathering Storm / New Frontier / Black Death / War Machine）。当前数据库中无活跃 Modifier 实例。

---

### EFFECT_ADJUST_PLAYER_GREATPERSON_FAVOR_MODIFIER

调整招募伟人时获得的外交支持倍率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GREATPERSON_FAVOR_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 百分比修正。示例值: `50` (+50%) |

> 数据库活跃实例: `TRAIT_GREATPERSON_FAVOR_MODIFIER`（Amount=50）。见于 Gathering Storm / New Frontier。

---

### EFFECT_ADJUST_PLAYER_POLICY_FAVOR

调整政策卡提供的外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_POLICY_FAVOR` | `COLLECTION_OWNER` |
| `MODIFIER_MAJOR_PLAYERS_ADJUST_POLICY_FAVOR` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 修正量 (ESTIMATED) |
| `PolicyType` | **必写** | `Policies.PolicyType` — 指定政策卡 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_POLICY_FAVOR 行（Gathering Storm）。数据库中无活跃 Modifier 实例。

---

### EFFECT_ADJUST_PLAYER_SUZERAIN_FAVOR_MULTIPLIER

调整城邦宗主国外交支持倍率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_SUZERAIN_FAVOR_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 百分比倍率。示例值: `100` (即 x2，如匈牙利议会大厦) |

> 数据库活跃实例: `ORSZAGHAZ_DOUBLE_FAVOR_SUZERAIN`（Amount=100）。见于 Gathering Storm。

---

### EFFECT_ADJUST_PLAYER_SUZERAIN_FAVOR_BY_BONUS_TYPE

根据城邦类型调整宗主国外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_SUZERAIN_FAVOR_BY_BONUS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BonusType` | **必写** | 城邦类型标识。可选项参考 `reference/csv-export/Enumerations.csv` 中 `GovernmentBonusTypes` 表（如 `GOVERNMENTBONUS_ENVOYS` / `GOVERNMENTBONUS_FAITH_PURCHASES` 等）(ESTIMATED) |
| `Amount` | **必写** | 整数 — Favor 修正值 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_SUZERAIN_FAVOR_BY_BONUS_TYPE 行（Gathering Storm / New Frontier）。数据库中无活跃 Modifier 实例，参数为推定值。

---

### EFFECT_ADJUST_PLAYER_TOURISM_FAVOR

根据旅游业绩提供外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_TOURISM_INTO_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Favor` | **必写** | 整数 — 每单位 Tourism 对应的 Favor 值。示例值: `1` |
| `Tourism` | **必写** | 整数 — Tourism 阈值。示例值: `100` |

> 数据库活跃实例: `TRAIT_TOURISM_INTO_FAVOR`（Tourism=100, Favor=1）。见于 Gathering Storm / New Frontier。

---

### EFFECT_ADJUST_PLAYER_BUILDING_FAVOR

根据建造的指定建筑提供外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_BUILDING_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BuildingType` | **必写** | `Buildings.BuildingType` — 指定建筑。示例值: `BUILDING_BROADCAST_CENTER` |
| `Favor` | **必写** | 整数 — Favor 值。示例值: `3` |

> 数据库存在 1 个活跃 Modifier 实例。见于场景包（Black Death / War Machine 等）。

---

### EFFECT_ADJUST_PLAYER_ANYONE_TRADE_TO_FAVOR

建立贸易路线时获得外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ANYONE_TRADE_TO_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 值 (ESTIMATED，来自 `reference/csv-export/Effects.csv`) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_ANYONE_TRADE_TO_FAVOR 行（Gathering Storm / New Frontier）。数据库中无活跃 Modifier 实例。

---

### EFFECT_ADJUST_PLAYER_ANYONE_PLUNDER_FAVOR

掠夺时获得外交支持（资料片/场景可用）。

| ModifierType | CollectionType |
|-------------|----------------|
| （未在数据库中活跃使用） | |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 值 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_ANYONE_PLUNDER_FAVOR 行（Gathering Storm / New Frontier / 部分场景）。数据库中无活跃 Modifier 实例。

---

### EFFECT_ADJUST_PLAYER_ANYONE_PLUNDER_TO_FAVOR

掠夺时获得外交支持（原版可用版本）。`[未在数据库中活跃使用]`

| ModifierType | CollectionType |
|-------------|----------------|
| （未在数据库中活跃使用） | |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 值 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_ANYONE_PLUNDER_TO_FAVOR 行。仅原版 (Vanilla) 可用，数据库中无活跃 Modifier 实例。与 `EFFECT_ADJUST_PLAYER_ANYONE_PLUNDER_FAVOR` 是不同 EffectType。

---

### EFFECT_ADJUST_RELIGION_ANYONE_CONDEMNS_FAVOR

因异端谴责获得外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_RELIGION_ADJUST_ANYONE_CONDEMNS_FAVOR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每次谴责获得的 Favor 量。示例值: `25` |

> 数据库活跃实例: `ANYONE_CONDEMNS_FOR_FAVOR`（Amount=25）。见于 Gathering Storm。

---

### EFFECT_PLAYER_ADJUST_FAVOR_FROM_DELEGATIONS `[无官方使用示例，但 Mod 中可用]`

调整来自代表团的每回合外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FAVOR_FROM_DELEGATIONS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每个代表团额外获得的 Favor/回合 |

---

### EFFECT_PLAYER_ADJUST_FAVOR_FROM_EMBASSIES `[无官方使用示例，但 Mod 中可用]`

调整来自大使馆的每回合外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_FAVOR_FROM_EMBASSIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每个大使馆额外获得的 Favor/回合 |

---

### EFFECT_ADJUST_PLAYER_SEND_TRADE_ROUTE_FAVOR_BY_BONUS_TYPE

根据城邦类型调整发送贸易路线时获得的外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_SEND_TRADE_ROUTE_FAVOR_BY_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 值 (ESTIMATED，来自 `reference/csv-export/Effects.csv`) |
| `BonusType` | **必写** | 城邦类型标识。可选项参考 `reference/csv-export/Enumerations.csv` 中 `GovernmentBonusTypes` 表 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_SEND_TRADE_ROUTE_FAVOR_BY_BONUS_TYPE 行（Gathering Storm / New Frontier）。数据库中无活跃 Modifier 实例，参数为推定值。

---

## 外交分数

### EFFECT_ADJUST_DIPLOMATIC_SCORE `[无官方使用示例，但 Mod 中可用]`

调整外交分数。

| ModifierType | CollectionType |
|-------------|----------------|
| （未在数据库中活跃使用） | |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 外交分数修正值 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_DIPLOMATIC_SCORE 行。非官方效果，当前无活跃数据库实例。

---

## 不满值 / 战争狂 (Grievance / Warmonger)

### EFFECT_ADJUST_PLAYER_GRIEVANCE_DECAY

加速/减缓不满值衰减速率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GRIEVANCE_DECAY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 衰减速率修正百分比。示例值: `100` (+100% 即双倍衰减速度) |

---

### EFFECT_ADJUST_PLAYER_GRIEVANCE_GENERATION

调整不满值生成倍率。数据库中活跃使用（如宣战时减少不满值生成）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_GRIEVANCE_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 百分比修正。示例值: `-50` (减少 50% 不满值生成), `100` (双倍) |

> 与 `EFFECT_ADJUST_PLAYER_GRIEVANCE_DECAY` 不同，此为生成倍率调整而非衰减速率。

---

### EFFECT_DISABLE_PLAYER_GRIEVANCE_DECAY

完全禁用不满值衰减（如网络战争效果）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DISABLE_GRIEVANCE_DECAY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Disable` | **必写** | `1` — 禁用衰减 |

> 与 `EFFECT_ADJUST_PLAYER_GRIEVANCE_DECAY` 不同，此为完全禁用而非速率调整。

---

### EFFECT_DIPLOMACY_WARMONGER

新战争狂 — 根据对方造成的整体不满值产生外交惩罚。

| ModifierType | CollectionType |
|-------------|----------------|
| （未在数据库中活跃使用） | |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `LowerLimit` | **必写** | 整数 — 最低修正值下限 (ESTIMATED) |
| `PercentOfGrievances` | **必写** | 整数 — 不满值百分比转化为外交惩罚 (ESTIMATED) |
| `ReductionTurns` | **必写** | 整数 — 衰减间隔回合 (ESTIMATED) |
| `ReductionValue` | **必写** | 整数 — 每次衰减值 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_DIPLOMACY_WARMONGER 行。仅存在于 New Frontier / War Machine / Black Death 等后期 DLC 中，**不在 Vanilla / Rise and Fall / Gathering Storm 中可用**。CSV 中此 EffectType 的参数字段为空，以上参数为从同系列效果推断。

---

### EFFECT_ADJUST_PLAYER_WARMONGER_MULTIPLIER

调整战争狂不满值倍率。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_WARMONGER_MULTIPLIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 百分比倍率。示例值: `0` (完全取消战争狂惩罚) |

> 数据库活跃实例: `NONAGENDA_IGNORE_WARMONGERING`（Amount=0，完全无视战争狂惩罚）。

---

### EFFECT_ADJUST_PLAYER_MAX_WARMONGER_PERCENT

调整最大战争狂惩罚百分比上限。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_MAX_WARMONGER_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `MaxPercent` | **必写** | 整数 — 最大百分比上限。示例值: `100` |

> 数据库活跃实例: `TRAIT_FALLBABYLON_WARMONGER_MAX`（MaxPercent=100，将战争狂惩罚上限设为 100%）。见于 New Frontier。

---

## 影响力 / 使者 (Influence / Envoy)

### EFFECT_ADJUST_DISABLE_INFLUENCE

禁用影响力产出（如成为叛军状态）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DISABLE_INFLUENCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Disable` | **必写** | `0` = 启用, `1` = 禁用 |

---

### EFFECT_ADJUST_DUPLICATE_FIRST_INFLUENCE_TOKEN

向城邦首次派遣使者时获得双倍使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_DUPLICATE_FIRST_INFLUENCE_TOKEN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | `1` — 额外获得的使者数。原版固定为 1 |

---

### EFFECT_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_RIVAL_GOVERNMENT

对政体不同的城邦派遣使者时双倍。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_RIVAL_GOVERNMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | `1` — 额外使者数 |

---

### EFFECT_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_SAME_RELIGION

向同宗教城邦派遣使者时双倍。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_SAME_RELIGION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | `1` — 额外使者数 |

---

### EFFECT_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_TRADE_ROUTE_TO

对已建立贸易路线的城邦派遣使者时获得额外使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_DUPLICATE_INFLUENCE_TOKEN_WHEN_TRADE_ROUTE_TO` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 额外使者数。示例值: `1` |

---

### EFFECT_ADJUST_INFLUENCE_POINTS_PER_TURN

调整每回合获得的影响力点数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_INFLUENCE_POINTS_PER_TURN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每回合影响力增量。示例值: `3` |

---

### EFFECT_ADJUST_PLAYER_ADJUST_ENVOYS_NON_SPECIALTY `[无官方使用示例，但 Mod 中可用]`

非特色区域建成时获得额外使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_PLAYER_ENVOYS_NON_SPECIALTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 获得使者数。示例值: `1` |

---

### EFFECT_ADJUST_PLAYER_OPEN_BORDERS_FROM_INFLUENCE

根据影响力自动开放边界（炮舰外交）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ADJUST_OPEN_BORDERS_FROM_INFLUENCE` | `COLLECTION_ALL_PLAYERS` |

> 无额外参数。触发后根据影响力值自动对所有玩家开放边界。

---

### EFFECT_ADJUST_PLAYER_YIELD_CHANGE_PER_USED_INFLUENCE_TOKEN

根据已派遣的使者数量提供产出加成。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_YIELD_CHANGE_PER_USED_INFLUENCE_TOKEN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 每个使者提供的产出量。示例值: `1` |
| `YieldType` | **必写** | `YIELD_GOLD` / `YIELD_SCIENCE` / `YIELD_CULTURE` / `YIELD_FAITH` |

> 原版示例：商业城邦宗主国加成，每派遣 1 名使者 +1 金币。

---

### EFFECT_ADJUST_PLAYER_SEND_INFLUENCE_TOKEN_FAVOR_BY_BONUS_TYPE

根据城邦类型调整派遣使者时获得的外交支持。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_SEND_INFLUENCE_TOKEN_FAVOR_BY_BONUS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — Favor 值 (ESTIMATED，来自 `reference/csv-export/Effects.csv`) |
| `BonusType` | **必写** | 城邦类型标识。可选项参考 `reference/csv-export/Enumerations.csv` 中 `GovernmentBonusTypes` 表 (ESTIMATED) |

> 来源: `reference/csv-export/Effects.csv` EFFECT_ADJUST_PLAYER_SEND_INFLUENCE_TOKEN_FAVOR_BY_BONUS_TYPE 行（Gathering Storm / New Frontier）。数据库中无活跃 Modifier 实例，参数为推定值。

---

### EFFECT_GRANT_CITY_OWNER_INFLUENCE_TOKEN_WONDER

建造奇观时获得使者（等同于 `MODIFIER_PLAYER_GRANT_INFLUENCE_TOKEN_FROM_CITY_WONDER`）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_INFLUENCE_TOKEN_FROM_CITY_WONDER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 使者数量。示例值: `2` |

---

### EFFECT_GRANT_FREE_ENVOYS_HERE `[无官方使用示例，但 Mod 中可用]`

直接在该城邦赋予免费使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CITY_GRANT_FREE_ENVOYS_HERE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 使者数量。示例值: `3` |

> `COLLECTION_OWNER` 指 Modifier 附着对象的"所有者"——当附着于城邦时，即该城邦获得使者。

---

### EFFECT_GRANT_INFLUENCE_TOKEN

直接给予玩家使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_GRANT_INFLUENCE_TOKEN` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_GRANT_INFLUENCE_TOKEN_FROM_CITY_WONDER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 使者数量。示例值: `2` |

---

### EFFECT_GRANT_INFLUENCE_TOKEN_LEVY_MILITARY

征用城邦军队时获得使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_ADJUST_ENVOYS_FROM_LEVIED_CITY_STATES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 使者数量。示例值: `2` |

---

### EFFECT_ENABLE_RELIGION_AWARDS_ENVOY

启用宗教奖励使者机制。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ENABLE_AWARDS_ENVOY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Enable` | **必写** | `0` = 禁用, `1` = 启用 |

---

### EFFECT_ENABLE_RELIGION_AWARDS_ENVOY_RELIGIOUS_PRESSURE

根据宗教压力奖励使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_RELIGION_ENABLE_AWARDS_ENVOY_RELIGIOUS_PRESSURE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 宗教压力阈值。示例值: `200` |

---

### EFFECT_ADJUST_PLAYER_SPECIFIC_DISTRICT_GRANT_ENVOYS

建成特定区域时获得使者。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_SPECIFIC_DISTRICT_GRANT_ENVOYS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `Amount` | **必写** | 整数 — 使者数量。示例值: `1` |
| `DistrictType` | **必写** | `Districts.DistrictType` — 指定区域类型。示例值: `DISTRICT_GOVERNMENT` |

---

## 议程 (Agenda)

> **统一说明**: 以下 `EFFECT_DIPLOMACY_AGENDA_*` 为各领袖的定制议程效果，其核心逻辑由 C++ DLL 固化了具体规则，Mod 中**文本无法自定义**（无法更改议程描述和对白），因此在实际 Mod 中不易用于新领袖。创建自定义议程应优先考虑 `EFFECT_DIPLOMACY_SIMPLE_EFFECT`。

议程类 EffectType 统一使用 `COLLECTION_MAJOR_PLAYERS`（对主要文明生效）或 `COLLECTION_ALL_PLAYERS`。

---

### EFFECT_DIPLOMACY_AGENDA_ANGEVIN_EMPIRE

安茹帝国议程 — 根据对方人口高低增减外交态度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_ANGEVIN_EMPIRE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomRankingDiploMod` | **必写** | 整数 — 对低人口的惩罚。示例值: `-8` |
| `HighPopulationThreshold` | **必写** | 整数 — 高人口阈值。示例值: `110` |
| `LowPopulationThreshold` | **必写** | 整数 — 低人口阈值。示例值: `70` |
| `StatementKey` | **必写** | `LOC_*` — 议程提示文本 |
| `TopRankingDiploMod` | **必写** | 整数 — 对高人口的奖励。示例值: `8` |

---

### EFFECT_DIPLOMACY_AGENDA_ARCHIPELAGIC_STATE

群岛国家议程 — 根据对方拥有大型岛屿（大陆）面积增减态度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_ARCHIPELAGIC_STATE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AcceptableIslandPercentage` | 可选 | 整数 — 可接受的岛屿百分比。示例值: `20` |
| `MaxNegativeModifier` | **必写** | 整数 — 最大负面修正。示例值: `-8` |
| `MaxPositiveModifier` | **必写** | 整数 — 最大正面修正。示例值: `8` |
| `MaxTilesLargeIsland` | **必写** | 整数 — 大型岛屿最大格数。示例值: `37` |
| `MaxTilesMediumIsland` | **必写** | 整数 — 中型岛屿最大格数。示例值: `19` |
| `MaxTilesSmallIsland` | **必写** | 整数 — 小型岛屿最大格数。示例值: `7` |
| `ReductionTurns` | 可选 | 整数 — 衰减回正所需回合 |
| `StatementKey` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_AGENDA_AYYUBID_DYNASTY

阿尤布王朝议程。数据库中活跃使用。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_AYYUBID_DYNASTY` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_AGENDA_BLACK_QUEEN

黑皇后议程（法国凯瑟琳）— 对缺乏间谍的文明不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_BLACK_QUEEN` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `AGENDA_BLACK_QUEEN_WARNING` |

---

### EFFECT_DIPLOMACY_AGENDA_BULL_MOOSE

公牛驼鹿议程（美国泰迪·罗斯福）— 根据对方是否在同一大陆发动战争。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_BULL_MOOSE` | `COLLECTION_ALL_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `LOC_PLACEHOLDER` |

---

### EFFECT_DIPLOMACY_AGENDA_BUSHIDO

武士道议程（日本北条时宗）— 对有强大军事和文化的文明尊敬、对两者都弱者蔑视。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_BUSHIDO` | `COLLECTION_ALL_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `AGENDA_BUSHIDO_WARNING` |

---

### EFFECT_DIPLOMACY_AGENDA_CANADIAN_EXPEDITIONARY

加拿大远征议程 — 对参与紧急事件和竞赛积极的文明友好。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_CANADIAN_EXPEDITIONARY` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 对表现低于此百分位的惩罚阈值。示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 低排名修正值。示例值: `-8` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 对表现高于此百分位的奖励阈值。示例值: `65` |
| `TopRankingDiploMod` | **必写** | 整数 — 高排名修正值。示例值: `8` |

---

### EFFECT_DIPLOMACY_AGENDA_END_TO_SUFFERING

止苦议程 — 根据对方建设圣地/大城市的宗教/城区建设。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_END_TO_SUFFERING` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DisappointingHolySitePercentage` | **必写** | 整数 — 圣地偏少阈值。示例值: `25` |
| `DisappointingLargeCityPercentage` | **必写** | 整数 — 大城市偏少阈值。示例值: `35` |
| `MaxNegativeModifier` | **必写** | 整数 — 最大负面修正。示例值: `-8` |
| `MaxPositiveModifier` | **必写** | 整数 — 最大正面修正。示例值: `8` |
| `StatementKey` | **必写** | `LOC_*` |
| `TargetHolySitePercentage` | **必写** | 整数 — 目标圣地比例。示例值: `50` |
| `TargetLargeCityPercentage` | **必写** | 整数 — 目标大城市比例。示例值: `65` |

---

### EFFECT_DIPLOMACY_AGENDA_ENVIRONMENT

环保议程 — 根据对方保护/破坏自然环境的程度（种树/建国家公园 vs 砍伐地貌）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_ENVIRONMENT` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ForestPlacedValue` | **必写** | 整数 — 每植树的分数 |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏 |
| `HighThreshold` | **必写** | 整数 — 高分阈值 |
| `IncrementValue` | **必写** | 整数 — 每次递增修正值 |
| `InitialValue` | **必写** | 整数 — 初始值 |
| `LowThreshold` | **必写** | 整数 — 低分阈值 |
| `MaxDiploModifierMagnitude` | **必写** | 整数 — 最大修正幅度 |
| `NationalParkConstructionValue` | **必写** | 整数 — 每建国家公园的分数 |
| `PlotFeatureRemovedValue` | **必写** | 整数 — 每移除地貌的惩罚分数 |
| `ScoreAllowancePerEra` | 可选 | 整数 — 每时代的容忍度 |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_AGENDA_ETHIOPIAN_HIGHLANDS

埃塞俄比亚高原议程 — 根据对方在山脉/丘陵区域的建城情况。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_ETHIOPIAN_HIGHLANDS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `LOC_PLACEHOLDER` |

---

### EFFECT_DIPLOMACY_AGENDA_EXPLOITATIVE

剥削议程（罗斯福·进步党）— 对地貌改良过多不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_EXPLOITATIVE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏。示例值: `1` |
| `HighScoreThreshold` | **必写** | 整数 — 高分阈值。示例值: `15` |
| `IncrementValue` | **必写** | 整数 — 增量值。示例值: `0` |
| `InitialValue` | **必写** | 整数 — 初始值。示例值: `0` |
| `LowScoreThreshold` | **必写** | 整数 — 低分阈值。示例值: `-15` |
| `MaxDiploModifierMagnitude` | **必写** | 整数 — 最大修正幅度。示例值: `10` |
| `NationalParkConstructionValue` | **必写** | 整数 — 建国家公园的分数。示例值: `10` |
| `PlotFeatureRemovalValue` | **必写** | 整数 — 移除地貌的惩罚。示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |
| `TileImprovementHighThreshold` | **必写** | 整数 — 改良过多阈值。示例值: `75` |
| `TileImprovementLowThreshold` | **必写** | 整数 — 改良较少阈值。示例值: `35` |
| `TileImprovementPreferenceValue` | **必写** | 整数 — 改良偏好评分。示例值: `9` |

---

### EFFECT_DIPLOMACY_AGENDA_FLAT_EARTHER

地平说议程 — 对进行航天项目/建设航天中心的文明不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_FLAT_EARTHER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DiploModForCircumnavigation` | **必写** | 整数 — 环游世界惩罚。示例值: `-2` |
| `DiploModPerSpaceProject` | **必写** | 整数 — 每个航天项目惩罚。示例值: `-1` |
| `DiploModPerSpaceport` | **必写** | 整数 — 每个航天中心惩罚。示例值: `-1` |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏。示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopRankingDiploMod` | **必写** | 整数 — 最高正面修正。示例值: `8` |

---

### EFFECT_DIPLOMACY_AGENDA_HORN_CHEST_LOINS

角胸甲议程（斯基泰托米丽司）— 根据对方是否有军团/军队编制。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_HORN_CHEST_LOINS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-7` |
| `CantBuildDiploMod` | **必写** | 整数 — 无法编制时的修正。示例值: `-3` |
| `CorpsPrereqCivic` | **必写** | `CIVIC_*` — 编制军团所需市政。示例值: `CIVIC_NATIONALISM` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `70` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `6` |

---

### EFFECT_DIPLOMACY_AGENDA_HORSE_LORD

马背之王议程（蒙古成吉思汗）— 看重对方骑兵数量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_HORSE_LORD` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 低骑兵比例的正面修正。示例值: `7` |
| `PromotionClass1` | **必写** | `PROMOTION_CLASS_HEAVY_CAVALRY` |
| `PromotionClass2` | **必写** | `PROMOTION_CLASS_LIGHT_CAVALRY` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `70` |
| `TopRankingDiploMod` | **必写** | 整数 — 高骑兵比例的负面修正。示例值: `-6` |

---

### EFFECT_DIPLOMACY_AGENDA_KAITIAKITANGA

守护理事会议程（毛利）— 对未受战争破坏的环境文明友好。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_KAITIAKITANGA` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 示例值: `40` |
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-6` |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏。示例值: `1` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `60` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `6` |

---

### EFFECT_DIPLOMACY_AGENDA_KUBLAI_PAX

忽必烈和平议程 — 根据对方是否使用通配符政策。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_KUBLAI_PAX` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `AGENDA_KUBLAI_PAX_KUDO_AND_WARNING` |

---

### EFFECT_DIPLOMACY_AGENDA_LAST_VIKING_KING

最后维京王议程（挪威哈拉尔）— 看重海军实力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_LAST_VIKING_KING` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BetterMilitaryBonus` | **必写** | 整数 — 军力稍弱的奖励。示例值: `4` |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏。示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopMilitaryBonus` | **必写** | 整数 — 军力最强的奖励。示例值: `6` |

---

### EFFECT_DIPLOMACY_AGENDA_LAWGIVER

立法者议程（巴比伦汉谟拉比）— 根据对方是否建造了各区类型。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_LAWGIVER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BonusIfNotOriginalOwner` | **必写** | 整数 — 如对方不是原始所有者时的加成。示例值: `50` |
| `BottomPercentage` | **必写** | 整数 — 示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-8` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `65` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `8` |

---

### EFFECT_DIPLOMACY_AGENDA_LORD_OF_MINES

矿主议程 — 根据对方采矿/采石场数量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_LORD_OF_MINES` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-8` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `65` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `8` |

---

### EFFECT_DIPLOMACY_AGENDA_MAGNIFICENCES

辉煌议程（法国路易十四）— 根据对方奇观/巨作数量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_MAGNIFICENCES` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `LOC_PLACEHOLDER` |

---

### EFFECT_DIPLOMACY_AGENDA_OPPORTUNIST

机会主义者议程（马其顿亚历山大）— 对和平状态不满，喜欢交战文明。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_OPPORTUNIST` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `EachSurpriseWarBonus` | **必写** | 整数 — 每场突袭战争的奖励。示例值: `1` |
| `NeverSurpriseWarPenalty` | **必写** | 整数 — 从未发动突袭的惩罚。示例值: `-6` |
| `RecentSurpriseWarBonus` | **必写** | 整数 — 近期突袭的奖励。示例值: `15` |
| `StatementKey` | **必写** | `AGENDA_BACKSTABBER` |
| `SurpriseWarDegradeTurns` | **必写** | 整数 — 突袭加分衰减回合。示例值: `3` |

---

### EFFECT_DIPLOMACY_AGENDA_OPTIMUS_PRINCEPS

贤君议程（罗马图拉真）— 看重领土面积。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_OPTIMUS_PRINCEPS` | `COLLECTION_ALL_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BetterTerritoryBonus` | **必写** | 整数 — 示例值: `4` |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏。示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopTerritoryBonus` | **必写** | 整数 — 示例值: `6` |

---

### EFFECT_DIPLOMACY_AGENDA_PARANOID

偏执议程 — 仅 `StatementKey` 参数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_PARANOID` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `AGENDA_PARANOID_WARNING` |

---

### EFFECT_DIPLOMACY_AGENDA_PATRON_OF_ARTS

艺术赞助人议程 — 对缺乏巨作/艺术品的文明不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_PATRON_OF_ARTS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `8` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `65` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `-8` |

---

### EFFECT_DIPLOMACY_AGENDA_PERPETUALLY_ON_GUARD

永不卸防议程（澳大利亚约翰·科廷）— 对占领敌方城市不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_PERPETUALLY_ON_GUARD` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `PenaltyPerOccupiedCity` | **必写** | 整数 — 每占领城市的惩罚。示例值: `-2` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_AGENDA_QUEEN_OF_NILE

尼罗河女王议程（埃及克利奥帕特拉）— 仅 `StatementKey` 参数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_QUEEN_OF_NILE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `StatementKey` | **必写** | `AGENDA_QUEEN_OF_NILE_WARNING` |

---

### EFFECT_DIPLOMACY_AGENDA_RAVEN_BANNER

渡鸦旗帜议程（挪威/维京）— 根据海军实力。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_RAVEN_BANNER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomPercentage` | **必写** | 整数 — 示例值: `30` |
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-8` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopPercentage` | **必写** | 整数 — 示例值: `65` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `8` |

---

### EFFECT_DIPLOMACY_AGENDA_SHORT_LIFE_GLORY

生短荣长议程（苏美尔吉尔伽美什）— 根据对方是否在战争中。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_SHORT_LIFE_GLORY` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `EachWarDeclaredBonus` | **必写** | 整数 — 每场宣战奖励。示例值: `1` |
| `MajorWarBonus` | **必写** | 整数 — 主要战争奖励。示例值: `5` |
| `MaxWarDeclaredBonus` | **必写** | 整数 — 最大宣战奖励。示例值: `5` |
| `NotAtWarPenalty` | **必写** | 整数 — 不在战争中的惩罚。示例值: `-6` |
| `SinceWarPenaltyTurns` | **必写** | 整数 — 多少回合内无战争开始惩罚。示例值: `40` |
| `StatementKey` | **必写** | `AGENDA_SHORT_LIFE_GLORY` |

---

### EFFECT_DIPLOMACY_AGENDA_SIMON_BOLIVAR

玻利瓦尔议程 — 根据对方有晋升的单位数量。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_SIMON_BOLIVAR` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `MinPromotedUnits` | **必写** | 整数 — 最小晋升单位数。示例值: `5` |
| `NumSteps` | **必写** | 整数 — 评分阶梯数。示例值: `4` |
| `PercentageDifferencePerStep` | **必写** | 整数 — 每阶梯百分比差。示例值: `10` |
| `ScorePerStep` | **必写** | 整数 — 每阶梯评分。示例值: `3` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_AGENDA_TRIEU_DEFENDER `[无官方使用示例，但 Mod 中可用]`

赵氏守护议程（越南征氏姐妹）— 根据对方是否喜欢在植被区域建造。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_TRIEU_DEFENDER` | `COLLECTION_MAJOR_PLAYERS` |

> 数据库示例中无显式参数（参数可能全由 DLL 逻辑处理）。

---

### EFFECT_DIPLOMACY_AGENDA_TURTLER

龟缩议程（中国秦始皇）— 看重奇观建造。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_TURTLER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-6` |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏。示例值: `1` |
| `SimpleModifierDescription` | 可选 | `LOC_*` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `4` |

---

### EFFECT_DIPLOMACY_AGENDA_WITH_SHIELD_OR_ON_IT

或持盾归议程（希腊戈尔戈）— 对从未在战争中放弃/赔款的文明友好。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_WITH_SHIELD_OR_ON_IT` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AvoidedWarPenalty` | **必写** | 整数 — 避战惩罚。示例值: `-4` |
| `AvoidedWarPenaltyTurnsToRampUp` | **必写** | 整数 — 避战惩罚爬升回合。示例值: `15` |
| `HighThreshold` | **必写** | 整数 — 示例值: `4` |
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `LowThreshold` | **必写** | 整数 — 示例值: `-1` |
| `MaxDiploModifierMagnitude` | **必写** | 整数 — 示例值: `12` |
| `PaidForPeacePenalty` | **必写** | 整数 — 赔款求和惩罚。示例值: `-8` |
| `PaidForPeacePenaltyTurnsToFadeOut` | **必写** | 整数 — 赔款惩罚消退回合。示例值: `30` |
| `ReductionTurns` | **必写** | 整数 — 衰减回合。示例值: `2` |
| `ReductionValue` | **必写** | 整数 — 每次衰减值。示例值: `0` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |
| `StatementKey` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_AGENDA_ZEALOT

狂热者议程（西班牙菲利普二世）— 根据对方是否同宗教。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_ZEALOT` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `BottomRankingDiploMod` | **必写** | 整数 — 示例值: `-6` |
| `StatementKey` | **必写** | `LOC_*` |
| `TopRankingDiploMod` | **必写** | 整数 — 示例值: `6` |

---

### EFFECT_PLAYER_DIPLOMACY_AGENDA_COMPARE_ARMY_SIZE

比较军力大小的议程（安比奥里克斯/高卢议程）。数据库中活跃使用。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_AMBIORIX_ARMY` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AdjustPerStep` | **必写** | 整数 — 每阶梯修正值。示例值: `4` |
| `DeltaUnits` | **必写** | 整数 — 单位数差额。示例值: `5` |
| `MaxSteps` | **必写** | 整数 — 最大阶梯数。示例值: `4` |
| `MinUnitsNeeded` | **必写** | 整数 — 所需最小单位数。示例值: `5` |
| `StatementKey` | **必写** | `AGENDA_AMBIORIX` |

---

## 外交状态

以下 EffectType 控制双边外交关系的动态变化（承诺/违约/间谍/定居/政府差异等）。

核心参数模式（大部分共用）：

| 通用参数 | 说明 |
|----------|------|
| `IncrementValue` | 每回合自动变化量（正值=关系变好） |
| `IncrementTurns` | 每隔多少回合触发递增 |
| `InitialValue` | 初始外交修正值 |
| `ReductionTurns` | 衰减修正所需的回合数 |
| `ReductionValue` | 每次衰减的变化量 |
| `SimpleModifierDescription` | 外交修正的说明文本 LOC |
| `StatementKey` | 弹出对话框的文本键 |
| `MessageThrottle` | 弹出信息间隔（回合） |
| `HiddenAgenda` | 是否隐藏议程（`0` = 显示 / `1` = 隐藏） |
| `DiplomacyKey` | 外交警告键（如 `WARNING_DONT_SETTLE_NEAR_ME`） |

---

### EFFECT_DIPLOMACY_ARCHAEOLOGY

考古争议 — 对在己方领土内挖掘遗迹的文明产生不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_ARCHAEOLOGY` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DiplomacyKey` | **必写** | `WARNING_STOP_DIGGING_UP_ARTIFACTS` |
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `MessageThrottle` | **必写** | 整数 — 示例值: `20` |
| `ModifierPerTransgression` | **必写** | 整数 — 每次挖掘惩罚。示例值: `-5` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_BROKEN_PLEDGE

违背誓言 — 对方违反了对你的承诺（如在边境集结后仍宣战）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_BROKEN_PLEDGE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `ModifierPerTransgression` | **必写** | 整数 — 每次违约惩罚。示例值: `-6` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `15` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_BROKEN_PROMISE

违背承诺 — 对方违反了对你的口头承诺（非正式誓言）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_BROKEN_PROMISE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `ModifierPerTransgression` | **必写** | 整数 — 每次违约惩罚。示例值: `-6` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `15` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

> 与 `BROKEN_PLEDGE` 的区别：Pledge 为正式誓言（如"不在边境集结军队"），Promise 为口头承诺（如"不要在我附近定居"）。

---

### EFFECT_DIPLOMACY_CULTURAL_ID

文化认同外交修正 — 根据对方夺取城市获取/失去文化认同。用于劳塔罗/马普切"图卡佩尔之魂"议程。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_AGENDA_SPIRIT_OF_TUCAPEL` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `CityGainLowerBound` | **必写** | 整数 — 获得城市的下限。示例值: `0` |
| `CityGainUpperBound` | **必写** | 整数 — 获得城市的上限。示例值: `3` |
| `ScorePerCity` | **必写** | 整数 — 每城市的评分。示例值: `3` |
| `SimpleModifierDescription` | **必写** | `LOC_*` — 示例值: `LOC_DIPLO_MODIFIER_SPIRIT_OF_TUCAPEL_GAINING_CITIES` |
| `StatementKey` | **必写** | `LOC_*` — 示例值: `LOC_DIPLO_KUDO_LEADER_LAUTARO_REASON_ANY` |

> 在 Rise and Fall / Gathering Storm 及部分场景中可用。

---

### EFFECT_DIPLOMACY_ESPIONAGE

间谍活动 — 对在己方进行间谍活动的文明产生不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_ESPIONAGE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DiplomacyKey` | **必写** | `WARNING_STOP_SPYING_ON_ME` |
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `MessageThrottle` | **必写** | 整数 — 示例值: `20` |
| `ModifierPerTransgression` | **必写** | 整数 — 每次被发现惩罚。示例值: `-5` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `15` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_FORCE_INCURSION

因军事入侵产生的外交修正。主要资料片+场景可用。

| ModifierType | CollectionType |
|-------------|----------------|
| （未在数据库中活跃使用） | |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 递增修正值 |
| `InitialValue` | **必写** | 整数 — 初始修正值 |
| `ReductionValue` | **必写** | 整数 — 衰减修正值 |

> 在 Vanilla + Rise and Fall + Gathering Storm 及多数场景中可用。参数信息来自 `reference/csv-export/Effects.csv`。

---

### EFFECT_DIPLOMACY_GOVERNMENTS

政府差异 — 根据双方政体差异产生的外交修正。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_GOVERNMENTS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementTurns` | **必写** | 整数 — 示例值: `1` |
| `IncrementValue` | **必写** | 整数 — 每回合增量（负值表示恶化）。示例值: `-1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_KEPT_PLEDGE

遵守誓言 — 对方遵守了对你的正式承诺，关系变好。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_KEPT_PLEDGE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `ModifierPerKeptPledge` | **必写** | 整数 — 每次遵守奖励。示例值: `4` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `15` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_KEPT_PROMISE

遵守承诺 — 对方遵守了口头承诺，关系变好。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_KEPT_PROMISE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `ModifierPerKeptPromise` | **必写** | 整数 — 每次遵守奖励。示例值: `4` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `15` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_NEW_WARMONGER

新战争狂 — 根据对方造成的不满值产生外交惩罚。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_NEW_WARMONGER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `LowerLimit` | **必写** | 整数 — 最低修正值（下限）。示例值: `-60` |
| `PercentOfGrievances` | **必写** | 整数 — 不满值百分比转化为外交惩罚。示例值: `20` |
| `ReductionTurns` | **必写** | 整数 — 衰减间隔回合。示例值: `2` |
| `ReductionValue` | **必写** | 整数 — 每次衰减值。示例值: `-1` |

> 数据库活跃实例: `STANDARD_DIPLOMATIC_WARMONGER`（LowerLimit=-60, PercentOfGrievances=20, ReductionTurns=2, ReductionValue=-1）。此为游戏的核心战争狂系统。

---

### EFFECT_DIPLOMACY_NO_PLEDGE

无誓言 — 对方拒绝做出正式承诺。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_NO_PLEDGE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `ModifierPerTransgression` | **必写** | 整数 — 每次拒绝惩罚。示例值: `-3` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `10` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_NO_PROMISE

无承诺 — 对方拒绝做出口头承诺。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_NO_PROMISE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `ModifierPerTransgression` | **必写** | 整数 — 每次拒绝惩罚。示例值: `-3` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `10` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_RANDOM

随机外交修正 — 开局时给予一个随机的初始外交态度。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_RANDOM` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DifficultyOffset` | 可选 | 整数 — 难度偏移量 |
| `ReductionTurns` | **必写** | 整数 — 示例值: `10` |
| `ReductionValue` | **必写** | 整数 — 示例值: `1` |

---

### EFFECT_DIPLOMACY_SETTLED_CITIES

定居争议 — 对在己方附近建城的文明产生不满。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_SETTLED_CITIES` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `DiplomacyKey` | **必写** | `WARNING_DONT_SETTLE_NEAR_ME` |
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `MessageThrottle` | **必写** | 整数 — 示例值: `20` |
| `ReductionTurns` | **必写** | 整数 — 示例值: `10` |
| `ReductionValue` | **必写** | 整数 — 示例值: `-1` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_SIMPLE_EFFECT

通用简单外交效果 — 可自定义几乎所有参数的外交状态变化模板。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_SIMPLE_MODIFIER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `IncrementTurns` | **必写** | 整数 — 递增间隔 |
| `IncrementValue` | **必写** | 整数 — 每次递增的变化量 |
| `InitialValue` | **必写** | 整数 — 初始值 |
| `MaxValue` | 可选 | 整数 — 上限值 |
| `ReductionTurns` | 可选 | 整数 — 衰减间隔 |
| `ReductionValue` | 可选 | 整数 — 每次衰减值 |
| `SimpleModifierDescription` | 可选 | `LOC_*` |
| `StatementKey` | 可选 | `LOC_*` |
| `HiddenAgenda` | 可选 | `0` = 显示, `1` = 隐藏 |
| `DiplomacyKey` | 可选 | 外交警告键 |
| `MessageThrottle` | 可选 | 整数 — 信息间隔 |
| `Accumulates` | 可选 | `0` = 不累积, `1` = 累积 |
| `OnlyOwnersCity` | 可选 | `0` = 全局, `1` = 仅己方城市 |

> 外交议程的核心修改器。数据库中多达 176 个活跃实例，涵盖标准外交态度（宣称友好、谴责、边境警告、解放城市等）和领袖议程（高低科学/文化/信仰/军力等）。具体用法将在议程文件详述。此处仅列参数。
>
> 在 Vanilla + Rise and Fall + Gathering Storm 及多数场景中可用。

---

### EFFECT_DIPLOMACY_THIRD_PARTY_EFFECTS

第三方外交效果 — 因对方与你的敌人/盟友的关系产生修正。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_THIRD_PARTY_EFFECTS` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `AmountPerIncident` | **必写** | 整数 — 每事件修正。示例值: `-8` |
| `EffectType` | **必写** | `AlliedWithEnemy` / `FriendsWithEnemy` 等 |
| `IncrementValue` | **必写** | 整数 — 示例值: `0` |
| `InitialValue` | **必写** | 整数 — 示例值: `0` |
| `MaxEffectMagnitude` | **必写** | 整数 — 最大累积修正幅度。示例值: `8` |
| `SimpleModifierDescription` | **必写** | `LOC_*` |

---

### EFFECT_DIPLOMACY_THIRD_PARTY_WARMONGER

第三方战争狂 — 因对方对第三方发动战争产生的外交惩罚。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_PLAYER_DIPLOMACY_THIRD_PARTY_WARMONGER` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `LowerLimit` | **必写** | 整数 — 最小修正值。示例值: `-40` |
| `PercentOfGrievancesDelta` | **必写** | 整数 — 不满值百分比转为修正。示例值: `10` |

> 数据库活跃实例: `STANDARD_DIPLOMATIC_THIRD_PARTY_WARMONGER`（LowerLimit=-40, PercentOfGrievancesDelta=10）。此为游戏核心的第三方战争狂系统。

---

## 相似效果对比

| 效果组 | 差异 |
|--------|------|
| `BROKEN_PLEDGE` vs `BROKEN_PROMISE` | Pledge 为正式誓言（更重惩罚 -6），Promise 为口头承诺（-6） |
| `KEPT_PLEDGE` vs `KEPT_PROMISE` | Pledge 奖励 +4，Promise 奖励 +4 |
| `NO_PLEDGE` vs `NO_PROMISE` | Pledge 拒绝 -3，Promise 拒绝 -3，衰减回合都是 10 |
| `DUPLICATE_FIRST_INFLUENCE_TOKEN` vs `DUPLICATE_INFLUENCE_TOKEN_WHEN_RIVAL_GOVERNMENT` vs `DUPLICATE_INFLUENCE_TOKEN_WHEN_SAME_RELIGION` vs `DUPLICATE_INFLUENCE_TOKEN_WHEN_TRADE_ROUTE_TO` | 触发条件不同：首次 vs 异政体 vs 同宗教 vs 贸易路线 |
| `ADJUST_PLAYER_GRIEVANCE_DECAY` vs `DISABLE_PLAYER_GRIEVANCE_DECAY` vs `GRIEVANCE_GENERATION` | 衰减速率 vs 完全禁用 vs 生成倍率 |
| `NEW_WARMONGER` vs `THIRD_PARTY_WARMONGER` vs `DIPLOMACY_WARMONGER` | 对己方宣战 vs 对第三方宣战 vs 通用战争狂惩罚 |
| `FAVOR_FROM_DELEGATIONS` vs `FAVOR_FROM_EMBASSIES` | 代表团 vs 大使馆 |
| `EXTRA_FAVOR_PER_TURN`（城市级） vs `EXTRA_FAVOR_PER_TURN`（玩家级） | CollectionType 不同: `COLLECTION_PLAYER_CITIES` vs `COLLECTION_OWNER` |
| `ANYONE_PLUNDER_FAVOR` vs `ANYONE_PLUNDER_TO_FAVOR` | 前者用于资料片/场景, 后者用于原版 — 两个不同 EffectType |

## 特殊参数注意

- `DiplomaticYieldSource` 枚举值来自游戏 DLL，常见值: `TERRITORIAL_EXPANSION_WAR_INITIATED`, `SURPRISE_WAR_INITIATED`, `CITY_CAPTURED`, `EMERGENCY_JOINED` 等
- `DiplomaticAction` / `DiplomaticActionType` 值来自 `DiplomaticActions` 表
- `GovernmentSlotType` 枚举: `SLOT_MILITARY`, `SLOT_ECONOMIC`, `SLOT_DIPLOMATIC`, `SLOT_WILDCARD`
- `StatementKey` 通常使用 `AGENDA_*` 系列的 LOC 文本键（不含 `LOC_` 前缀），少数为 `LOC_*` 格式
- `EffectType` 参数（在 `EFFECT_DIPLOMACY_THIRD_PARTY_EFFECTS` 中）是字符串枚举，不是 EffectType 引用
- 议程系列中 `HiddenAgenda = 1` 表示该议程不在外交面板显示，为隐藏议程
- CollectionType 区分: `COLLECTION_MAJOR_PLAYERS`（仅主要文明） vs `COLLECTION_ALL_PLAYERS`（含城邦和自由城市）
- `Source` 参数（`EFFECT_ADD_DIPLO_VISIBILITY` 中）标识能见度来源: `SOURCE_GREAT_PERSON_JOURNALISM`, `SOURCE_TRADING_POST_TRAIT`, `SOURCE_TECH`, `SOURCE_TRAIT` 等
- `SourceType` 参数过滤适用范围: `DIPLO_SOURCE_ALL_NAMES`（全部）, `DIPLO_SOURCE_FEMALE_ONLY`（仅女性领袖）
- 标记 `[无官方使用示例，但 Mod 中可用]` 的 EffectType 来自 Modding Companion 的 USER ADDED 条目，ModifierType 存在但无官方数据库实例，使用时需自行测试（这不意味着效果无效，只是没有官方参考实现）
- 标记 `[未在数据库中活跃使用]` 的 EffectType 在当前游戏数据库中无 Modifier 实例，但 EffectType 已注册可在 Mod 中使用
