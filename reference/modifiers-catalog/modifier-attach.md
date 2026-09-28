# modifier-attach -- ATTACH_MODIFIER 链式机制

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

ATTACH_MODIFIER 系列 EffectType 是整个 Modifier 系统的**链式枢纽**。一个"外层"Modifier（使用这些 EffectType）将另一个"内层"Modifier（由 `ModifierId` 参数指定）挂载到指定集合的每个成员上。这是实现"先圈范围，再挂效果"的核心模式。

典型场景：
- 政策卡给所有单位加战斗力 -- 外层 `MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER`，内层 `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH`
- 万神殿给所有城市挂产出 -- 外层 `MODIFIER_ALL_CITIES_ATTACH_MODIFIER`，内层 `MODIFIER_CITY_PLOT_YIELDS_ADJUST_PLOT_YIELD`

---

### EFFECT_ATTACH_MODIFIER

ATTACH 系列最基础的 EffectType。将指定的 Modifier 挂载到 Collection 的每个成员上。仅有一个参数。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER` | `COLLECTION_ALL_PLAYERS` |
| `MODIFIER_ALL_CITIES_ATTACH_MODIFIER` | `COLLECTION_ALL_CITIES` |
| `MODIFIER_ALL_DISTRICTS_ATTACH_MODIFIER` | `COLLECTION_ALL_DISTRICTS` |
| `MODIFIER_ALL_UNITS_ATTACH_MODIFIER` | `COLLECTION_ALL_UNITS` |
| `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_CAPTURED_CITY_ATTACH_MODIFIER` | `COLLECTION_PLAYER_CAPTURED_CITIES` |
| `MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_SINGLE_UNIT_ATTACH_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_SINGLE_CITY_ATTACH_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_MAJOR_PLAYERS_ATTACH_MODIFIER` | `COLLECTION_MAJOR_PLAYERS` |
| `MODIFIER_PLAYER_ALLIANCES_ATTACH_MODIFIER` | `COLLECTION_PLAYER_ALLIANCES` |
| `MODIFIER_PLAYER_CITYSTATEUNITS_ATTACH_MODIFIER` | `COLLECTION_PLAYER_CITY_STATE_UNITS` |
| `MODIFIER_EMERGENCY_PLAYERS_ATTACH_MODIFIER` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ModifierId` | **必写** | 要挂载的"内层"ModifierId。可以是任意类型的 Modifier |

> **CollectionType 选择指南**：选哪一行取决于你的外层 Modifier 挂载在谁身上，以及你想把效果扩散到谁身上：
> - 外层挂 Leader/Trait → 用 `PLAYER_*` 系列扩散到该玩家的所有城市/单位
> - 外层挂 Policy → 用 `ALL_*` 或 `PLAYER_*` 系列
> - 外层挂 Building → 用 `ALL_CITIES_ATTACH_MODIFIER`（带 SubjectRequirementSetId 过滤拥有该建筑的城市）
> - 外层挂 UnitAbility → 用 `SINGLE_UNIT_ATTACH_MODIFIER` 给该单位自己加效果
> - `COLLECTION_OWNER`（即 `SINGLE_*` 两个）直接作用于施体自身，不扩散到集合
>
> **内层 Modifier 挂载位置**：内层 Modifier 的 Owner 自动指向外层 Collection 的每个成员。例如 `MODIFIER_PLAYER_UNITS_ATTACH_MODIFIER` 将内层 Modifier 挂到每个单位上，内层做 `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` 时作用对象就是那个单位。
>
> **⚠️ 劫掠/修复 Bug**：被 ATTACH 的 Modifier 在以下情况会永久失效：
> - 区域/建筑/改良被**劫掠**后修复 → ATTACH 的 Modifier **不会恢复**（对比：DistrictModifiers/BuildingModifiers 直接挂的会恢复）
> - 总督**换城市** → 过程本身令 ATTACH 的 Modifier 暂时失效，换完后**不会恢复**
>
> 给这些实体 ATTACH Modifier 时必须考虑此 Bug。该 Bug 对 Unit 类作用者无影响。

---

### EFFECT_ATTACH_MODIFIER_IF_PROMOTION_CLASS_MATCHES

将 Modifier 挂载到符合特定 **UnitPromotionClass** 的单位上。相当于带过滤条件的 ATTACH_MODIFIER。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_ALL_UNITS_APPLY_MODIFIER_IF_PROMOTION_CLASS_MATCHES` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ModifierId` | **必写** | 要挂载的内层 ModifierId |
| `Amount` | **必写** | 整数。当内层 Modifier 需要数值时传入。如果内层已自带 Amount，此处可传 0 |
| `UnitPromotionClassType` | **必写** | 筛选的晋升类。值引用 `UnitPromotionClasses.UnitPromotionClassType`，如 `PROMOTION_CLASS_MELEE`、`PROMOTION_CLASS_HEAVY_CAVALRY`、`PROMOTION_CLASS_RECON` 等 |

> 此 EffectType 仅在 **Gathering Storm (Expansion2)** 中可用。
>
> **`UnitPromotionClassType` 参数说明**：Effects.csv 中此参数标记为 `ESTIMATED`。官方实例未使用此参数——引擎可能通过上下文注入 UnitPromotionClassType。若显式传入，值引用 `UnitPromotionClasses.UnitPromotionClassType`，如 `PROMOTION_CLASS_MELEE`、`PROMOTION_CLASS_HEAVY_CAVALRY`、`PROMOTION_CLASS_RECON` 等。
>
> **与 EFFECT_ATTACH_MODIFIER 的区别**：`EFFECT_ATTACH_MODIFIER` 给 Collection 的**全体**成员挂内层 Modifier；本 EffectType 只给符合 PromotionClass 的单位挂。当你想针对某一类兵种加效果时使用，如"近战单位 +5 战斗力"。

---

### EFFECT_ATTACH_MODIFIER_TO_MINORCIVBONUSTYPE

将 Modifier 挂载到匹配特定 **MinorCivBonusType**（城邦类型）的玩家上。主要用于世界议会决议系统。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CONGRESS_ATTACH_MODIFIER_TO_MINORCIVBONUSTYPE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ModifierId` | **必写** | 要挂载的内层 ModifierId |

> 此 EffectType 仅 **Gathering Storm** 可用。**仅限世界议会使用**，自定义 Mod 不建议使用。

---

### EFFECT_ATTACH_MODIFIER_TO_PLAYERTYPE

将 Modifier 挂载到特定 **PlayerType** 的玩家上。主要用于世界议会决议系统。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_CONGRESS_ATTACH_MODIFIER_TO_PLAYERTYPE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ModifierId` | **必写** | 要挂载的内层 ModifierId |

> 此 EffectType 仅 **Gathering Storm** 可用。**仅限世界议会使用**，自定义 Mod 不建议使用。

---

### EFFECT_ATTACH_UNIT_MODIFIER

在**战斗结算后**将 Modifier 挂载到参与战斗的单位上。典型用途是单位击杀后获得永久增强（如"击杀单位后 +5 战斗力"）。

| ModifierType | CollectionType |
|-------------|----------------|
| `MODIFIER_COMBAT_RESULTS_ATTACH_UNIT_MODIFIER` | `COLLECTION_COMBAT_RESULTS` |

| 参数 | 写不写 | 值/引用 |
|------|--------|---------|
| `ModifierId` | **必写** | 要挂载到战斗单位上的内层 ModifierId |

> **不建议使用**。`EFFECT_ATTACH_MODIFIER` 已可通过 `SINGLE_UNIT_ATTACH_MODIFIER` / `PLAYER_UNITS_ATTACH_MODIFIER` 为单位挂载 Modifier，不需要此效果。

---

## 注意事项

1. **ATTACH MODIFIER 劫掠/修复 Bug**：被 ATTACH 的 Modifier 在区域/建筑/改良被劫掠修复后，或总督换城市后，**不会恢复**。必须考虑此 Bug。

2. **单位效果优先用 Ability**：给单位批量加效果时，优先使用 `EFFECT_GRANT_ABILITY` 授予 `UnitAbility`，而非用 `EFFECT_ATTACH_MODIFIER` 直接把效果挂到单位上。原因：① 官方 155 个实例均采用此模式；② Ability 在单位面板有 UI 显示；③ Tag 过滤机制比 RequirementSet 更简洁可靠；④ Ability 生命周期由引擎管理，存档/升级更安全。详见 `unit.md` 第二部分。

3. **EFFECT_ATTACH_MODIFIER vs EFFECT_ATTACH_MODIFIER_IF_PROMOTION_CLASS_MATCHES 混淆风险**：前者给 Collection 全体挂效果，后者只给匹配 PromotionClass 的单位挂。命名类似（`_ATTACH_MODIFIER` vs `_APPLY_MODIFIER_IF_PROMOTION_CLASS_MATCHES`），容易用错。

4. **COLLECTION_OWNER 的 SINGLE_* ModifierType**：`MODIFIER_SINGLE_UNIT_ATTACH_MODIFIER` 和 `MODIFIER_SINGLE_CITY_ATTACH_MODIFIER` 将内层挂到施体自身，不扩散到集合。与 `PLAYER_UNITS_ATTACH_MODIFIER`（扩散到所有单位）形成对比。

5. **RunOnce / Permanent / NewOnly 在链式中的行为**：外层和内层独立控制。常见模式：外层 `RunOnce=true`（只挂一次），内层 `Permanent=true`（效果持续）。

6. **EFFECT_ATTACH_MODIFIER_TO_MINORCIVBONUSTYPE / TO_PLAYERTYPE**：仅限世界议会，自定义 Mod 不可用。

7. **EFFECT_ATTACH_UNIT_MODIFIER**：已定义但无官方使用，`EFFECT_ATTACH_MODIFIER` 已可覆盖同类需求，不建议使用。
