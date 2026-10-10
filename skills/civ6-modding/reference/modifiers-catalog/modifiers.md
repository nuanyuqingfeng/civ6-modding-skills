# Modifiers

> **核心规则**：每个 ModifierType 必须从子文件或 Effects.csv 中查到才可写入 SQL。**禁止凭记忆或推测 ModifierType 名。**
>
> **案例参考**：不知道某种模式怎么写？先查 **[cases/INDEX.md](modifiers/cases/INDEX.md)** — 从 40+ 个 Mod 中提取的真实案例，按 Grant Ability / Yield / ATTACH / 自定义 / SELECT生成 / Req 分类。


---

## 一、概念映射

游戏术语和日常描述不一致。**先用概念找 EffectType，再走查证流程**，不要直接搜自然语言。

### 单位战斗

| 你想做 | EffectType | 参数要点 |
|--------|-----------|---------|
| 战斗力增减 | `EFFECT_ADJUST_UNIT_COMBAT_STRENGTH` | `Amount` |
| 每回合回血（驻扎回血/自动回血） | `EFFECT_ADJUST_UNIT_DAMAGE` | `Amount`（负值=负伤害=治疗，例如 `-100` 回满），需 `REQUIREMENT_PLAYER_TURN_STARTED` Triggered |
| 击杀后回血（战后回血） | `EFFECT_ADJUST_UNIT_HEAL_FROM_COMBAT` | `Amount`（百分比） |
| 受伤不减战力 | `EFFECT_ADJUST_UNIT_NO_REDUCTION_DAMAGE` | `NoReduction` |
| 移动力 | `EFFECT_ADJUST_UNIT_MOVEMENT` | `Amount` |
| 视野 | `EFFECT_ADJUST_UNIT_SIGHT` | `Amount` |
| 隐匿（潜行/隐身） | `EFFECT_ADJUST_UNIT_HIDDEN_VISIBILITY` | `Hidden` |
| 穿地形视野（看穿山） | `EFFECT_ADJUST_UNIT_SEE_THROUGH_TERRAIN` | `CanSee` |
| 穿地貌视野（看穿森林） | `EFFECT_ADJUST_UNIT_SEE_THROUGH_FEATURES` | `CanSee` |
| 无地形移动惩罚（自由移动） | `EFFECT_ADJUST_UNIT_IGNORE_TERRAIN_COST` | `Ignore`, `Type='ALL'` |
| 无视控制区（忽视ZOC） | `EFFECT_ADJUST_UNIT_IGNORE_ZOC` | `Ignore` |
| 攻击次数 | `EFFECT_ADJUST_UNIT_NUM_ATTACKS` | `Amount` |
| 攻击射程 | `EFFECT_ADJUST_UNIT_ATTACK_RANGE` | `Amount` |
| 经验值加成 | `EFFECT_ADJUST_UNIT_EXPERIENCE_MODIFIER` | `Amount`（%） |
| 进攻经验加成 | `EFFECT_ADJUST_UNIT_ATTACK_EXPERIENCE_MODIFIER` | `Amount`（%） |
| 建造者使用次数 | `EFFECT_ADJUST_UNIT_BUILD_CHARGES` | `Amount` |
| 跳跃/空降 | `EFFECT_ADJUST_UNIT_JUMP_DISTANCE` | `Range` |
| 支援加成% | `EFFECT_ADJUST_UNIT_SUPPORT_BONUS_MODIFIER` | `Amount` |
| 夹击加成% | `EFFECT_ADJUST_UNIT_FLANKING_BONUS_MODIFIER` | `Amount` |
| 授予能力（给单位加Buff） | `EFFECT_GRANT_ABILITY` | 标准类型 `MODIFIER_PLAYER_UNITS_GRANT_ABILITY`，见 **[cases/case-grant-ability.md](modifiers/cases/case-grant-ability.md)** |

### 产出

| 你想做 | EffectType | 参数要点 |
|--------|-----------|---------|
| 地块产出（全市范围） | `EFFECT_ADJUST_PLOT_YIELD` | `YieldType`, `Amount` |
| 单地块产出 | `EFFECT_ADJUST_PLOT_YIELDS` | `YieldType`, `Amount` |
| 城市产出绝对值 | `EFFECT_ADJUST_CITY_YIELD_CHANGE` | `YieldType`, `Amount` |
| 城市产出百分比 | `EFFECT_ADJUST_CITY_YIELD_MODIFIER` | `YieldType`, `Amount`（20=+20%） |
| 城市全六种产出 | `EFFECT_ADJUST_CITY_ALL_YIELDS_CHANGE` | `Amount`（六产出统一值），**需自定义 DynamicModifier** |

### 城市/区域/建筑

| 你想做 | EffectType | 参数要点 |
|--------|-----------|---------|
| 边界扩张速度 | `EFFECT_ADJUST_CITY_CULTURE_BORDER_EXPANSION` | `Amount`（%），**需自定义** |
| 住房加成 | `EFFECT_ADJUST_IMPROVEMENT_HOUSING` / `EFFECT_ADJUST_CITY_HOUSING_FROM_GREAT_PEOPLE` | `Amount`，**需自定义** |
| 宜居度 | `EFFECT_ADJUST_CITY_AMENITIES` | `Amount` |
| 忠诚度 | `EFFECT_ADJUST_CITY_IDENTITY_PER_TURN` | `Amount` |
| 城市+人口 | `EFFECT_ADJUST_CITY_POPULATION` | `Amount` |
| 奇观生产力% | `EFFECT_ADJUST_WONDER_PRODUCTION` | `Amount` |
| 区域生产力% | `EFFECT_ADJUST_DISTRICT_PRODUCTION` | `Amount` |
| 额外巨作槽位 | `EFFECT_ADJUST_CITY_EXTRA_GREAT_WORK_SLOTS` | `Amount`, `BuildingType`, `GreatWorkSlotType` |
| 区域基础产出 | `EFFECT_ADJUST_DISTRICT_BASE_YIELD_CHANGE` | `YieldType`, `Amount`，**需自定义** |
| 城市防御 | `EFFECT_ADJUST_CITY_INNER_DEFENSE` | `Amount`，**需自定义** |
| 永远满忠诚 | `EFFECT_ADJUST_CITY_ALWAYS_LOYAL` | 无参数，**需自定义** |

### 特殊机制

| 你想做 | EffectType | 参数要点 |
|--------|-----------|---------|
| 文化炸弹 | `EFFECT_ADJUST_CULTURE_BOMB_TRIGGER` | `ImprovementType`, `CaptureOwnedTerritory` |
| 赠送科技 | `EFFECT_GRANT_SPECIFIC_TECHNOLOGY` | `TechType` |
| 总督防灾害 | `EFFECT_ADJUST_PREVENT_STRUCTURAL_DAMAGE` | `Prevent`，**需自定义** |
| 免单位灾害伤害 | `EFFECT_ADJUST_RANDOM_EVENT_NO_UNIT_DAMAGE` | `NoDamage`, `RandomEventType` |
| 无视河流 | `EFFECT_ADJUST_UNIT_IGNORE_RIVERS` | `Ignore` |
| 旅游业绩% | `EFFECT_ADJUST_TOURISM` | `Amount` |
| 商路产出 | `EFFECT_ADJUST_TRADE_ROUTE_YIELD` | `YieldType`, `Amount` |

### 链式机制

| 你想做 | EffectType | 参数要点 |
|--------|-----------|---------|
| 附加效果到城市 | `EFFECT_ATTACH_MODIFIER` | `ModifierId`（指向内层），标准类型 `MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER` |

> 上表只列最常见概念。遇到表里没有的，去对应子文件中搜索。标注"**需自定义**"的需走 Types + DynamicModifiers 注册流程。

---

## 二、从哪里开始

按你想要的效果类型，打开对应子文件找 EffectType：

| 要做什么 | 打开子文件 |
|---------|-----------|
| 改产出（地块/城市/商路/百分比） | [modifier-yield.md](modifiers/modifier-yield.md) |
| 改单位属性（战斗力/移动/视野/回血/经验） | [modifier-unit-combat.md](modifiers/modifier-unit-combat.md) |
| 生成/复制单位、授予 Ability | [modifier-unit-spawn.md](modifiers/modifier-unit-spawn.md) |
| 链式 ATTACH_MODIFIER | [modifier-attach.md](modifiers/modifier-attach.md) |
| 城市（住房/宜居度/忠诚/人口/边界扩张） | [modifier-city.md](modifiers/modifier-city.md) |
| 区域/建筑（生产力/购买/槽位） | [modifier-district-building.md](modifiers/modifier-district-building.md) |
| 改良/地块/地形 | [modifier-improvement-plot.md](modifiers/modifier-improvement-plot.md) |
| 商路 | [modifier-trade.md](modifiers/modifier-trade.md) |
| 外交/使者 | [modifier-diplomacy.md](modifiers/modifier-diplomacy.md) |
| 宗教 | [modifier-religion.md](modifiers/modifier-religion.md) |
| 伟人/巨作 | [modifier-greatpeople.md](modifiers/modifier-greatpeople.md) |
| 总督 | [modifier-governor.md](modifiers/modifier-governor.md) |
| 政策卡/政体 | [modifier-policy-government.md](modifiers/modifier-policy-government.md) |
| 同盟 | [modifier-alliance.md](modifiers/modifier-alliance.md) |
| 资源/奢侈/战略 | [modifier-resource.md](modifiers/modifier-resource.md) |
| 以上都不匹配 | [modifier-misc.md](modifiers/modifier-misc.md) |

---

## 三、查找 ModifierType——强制流程

### 第一步：定位效果与参数

使用 `civ6-modding` 的 `database/scripts/search_impl.py` 反查真实实现（整句自然语言可走 BM25 兜底）、`query_effect_args.py` 查参数签名；入口见 [资料依据](../../SOURCES.md)。本页 SQL 是关系参考。

### 第二步：核实类型来源

参考表中的 ModifierType 可能来自其他 Mod，不能因它出现在技能或本机缓存就认定原版。按 [资料依据](../../SOURCES.md)「类型与枚举」节的口径核实（`source_index.sqlite` 行级来源）：符合语义的原版类型优先复用；确认是自定义类型的，必须随 Mod 自带 `Types` / `DynamicModifiers` 注册行，换机才不因缺注册而加载失败。

### 第三步：必要时创建类型

确认没有符合语义的原版 ModifierType，且 CollectionType / EffectType 已有真实定义，再由 generate-modifier 建立骨架，填写参数并校验。不要因一次搜索无结果就新造类型或判断必须使用 Lua；先核对相关模式、数据来源与能力边界。

---

## 四、完整 INSERT 链路（关系参考）

下表用于检查挂载链是否完整，不规定所有环境的执行顺序。主内容遵循生成器；自定义 SQL 按实际外键依赖与加载方式排序，并在目标 schema 下验证。

```
1. TraitModifiers / DistrictModifiers / UnitAbilityModifiers / …  ← 挂载
2. Types（仅自定义 ModifierType 时需要）
3. DynamicModifiers（仅自定义 ModifierType 时需要）
4. Modifiers
5. ModifierArguments
6. ModifierStrings（目标战斗效果的 Preview 必写；其他 Context 核实后使用）
7. RequirementSets（按需）
8. RequirementSetRequirements（按需）
9. Requirements（按需）
10. RequirementArguments（按需）
```

### 3.1 挂载（必须形成完整链）

```sql
INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_LEADER_SIQI_L0042_1', 'MODIFIER_SIQI_0042_GRANT_TECH_MINING');
```

其他挂载表的写法同此模式：
- `DistrictModifiers (DistrictType, ModifierId)`
- `BuildingModifiers (BuildingType, ModifierId)`
- `ImprovementModifiers (ImprovementType, ModifierId)`
- `UnitAbilityModifiers (UnitAbilityType, ModifierId)`
- `PolicyModifiers (PolicyType, ModifierId)`

### 3.2 Modifiers

基础列 `(ModifierId, ModifierType)`。根据效果需求扩展：

```sql
INSERT INTO Modifiers (ModifierId, ModifierType) VALUES
('MODIFIER_SIQI_0042_GRANT_TECH_MINING', 'MODIFIER_PLAYER_GRANT_SPECIFIC_TECHNOLOGY');
```

列扩展规则：

| 需求 | 加的列 | 示例值 |
|------|--------|--------|
| 限制 Owner 条件（不满足=不触发） | `OwnerRequirementSetId` | `'REQSET_SIQI_0042_TURN_STARTED'` |
| 限制 Subject 条件（不满足=跳过该 Subject） | `SubjectRequirementSetId` | `'REQSET_SIQI_0042_IS_CAMPUS'` |
| 只运行一次 | `RunOnce` | `1` |
| 永久 | `Permanent` | `1` |
| 同一对象最多叠加 N 次 | `SubjectStackLimit` / `OwnerStackLimit` | `1` |

> **评估时机**：效果在"附加时 + 条件变化时"被评估。条件驱动（RunOnce=0+Permanent=0）在条件翻转时重新执行。

#### RunOnce 专门解释（误解代价最高，0039 两次翻车）

**字面**：只运行一次。**但"运行"发生在哪一刻，是误解的根源**：

- **真实语义**：modifier **附加时**（trait 挂载 = 游戏初始化；ATTACH/区域/建筑挂载 = 对应建成时）立即评估条件，**条件满足就执行一次并锁定**——之后条件变化也不再执行。
- **常见误解**："条件首次满足时触发"（等建城后再触发）——**错**。条件在附加那一刻就评估，不等待。
- **执行失败也锁定**：附加时条件满足但执行目标不存在（如开局无城市）→ 生成失败 → **RunOnce 已消耗 → 永久无效**。

**什么时候安全**：
- 附加时条件**不满足**，之后条件才满足（官方 `UNIQUE_LEADER_ADD_SPY_UNIT`：开局无城堡科技 → 研究后触发一次 ✓）
- 附加时**目标已存在**（城市级 GRANT 被 ATTACH/DistrictModifiers 附加到已建成的城市 → 立即生成 ✓，0053/0043 模式）

**什么时候禁用**：开局条件就满足 + 执行目标开局不存在（如"首都送单位"配"城市≤1"条件——0 城时条件已满足、无城市可送）。→ 改用**条件驱动**（RunOnce=0 + Permanent=0 + 会翻转的条件，如"≤1 城"），见 [pattern-grant-unit](modifiers/patterns/pattern-grant-unit.md)。

完整示例（带所有可选列）：

```sql
INSERT INTO Modifiers (ModifierId, ModifierType, OwnerRequirementSetId, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0042_ATTACH_TURN', 'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER', 'REQSET_SIQI_0042_TURN_STARTED', NULL, 1, 1);
```

### 3.3 ModifierArguments

参数名和值**严格从子文件条目中复制**，不自己编。

```sql
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0042_GRANT_TECH_MINING', 'TechType', 'TECH_MINING');
```

一个 ModifierId 可能有多个参数行；区分必填与可选参数，对照当前 schema 和真实实例，不机械填写所有参考参数。

### 3.4 ModifierStrings（Preview 支持范围）

> **仅 `EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` 支持 Preview**。该效果类型（`MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH`、`MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH` 等）**必须写**，
> 否则战斗预览面板看不到加成来源 —— **不报错、静默失效**，最容易整批漏掉。
> 完整规则（三种 Context、占位符、生成器链路、自检清单）见 **[modifier-techniques.md 技巧 3](modifier-techniques.md)**。

```sql
-- 数值型（Amount）
INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES
('MODIFIER_SIQI_0055_MIL_STRENGTH_5', 'Preview', 'LOC_MODIFIER_SIQI_0055_MIL_STRENGTH_5_PREVIEW');
-- 对应中文（写在 Text SQL 里）：
-- ('zh_Hans_CN','LOC_MODIFIER_SIQI_0055_MIL_STRENGTH_5_PREVIEW','+{1_Amount} [ICON_Strength] 战斗力（恶魔的助威）')

-- Property（Key）读出口
INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES
('MODIFIER_SIQI_0055_MAKAI_TV_STRENGTH_READER', 'Preview', 'LOC_MODIFIER_SIQI_0055_MAKAI_TV_STRENGTH_READER_PREVIEW');
-- ('zh_Hans_CN','LOC_MODIFIER_SIQI_0055_MAKAI_TV_STRENGTH_READER_PREVIEW','+{Property} [ICON_Strength] 战斗力（来自魔界电视台）')
```

- 占位符：数值型 `{1_Amount}`、Property 型 `{Property}` —— **不要写 `{Amount}`**。
- LOC tag 约定：`LOC_{ModifierId}_PREVIEW`（按此约定在工程的文本 SQL 中生成）。
- 其他 Context：伟人「诞生时」用 `Summary`，议程用 `Sample`。

### 3.5 RequirementSets → Requirements → RequirementArguments

条件链的固定顺序：

```sql
-- 1. 定义条件集
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType) VALUES
('REQSET_SIQI_0042_TURN_STARTED', 'REQUIREMENTSET_TEST_ALL');

-- 2. 定义条件
INSERT INTO Requirements (RequirementId, RequirementType, Inverse, Triggered) VALUES
('REQ_SIQI_0042_TURN_STARTED', 'REQUIREMENT_PLAYER_TURN_STARTED', 0, 1);

-- 3. 条件加入条件集
INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId) VALUES
('REQSET_SIQI_0042_TURN_STARTED', 'REQ_SIQI_0042_TURN_STARTED');

-- 4. 条件参数（按需）
INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_0042_IS_CAMPUS', 'DistrictType', 'DISTRICT_CAMPUS');
```

> `REQUIREMENTSET_TEST_ALL` = 全部满足（AND），`REQUIREMENTSET_TEST_ANY` = 任一满足（OR）。
>
> 事件类 Requirement（如 `REQUIREMENT_PLAYER_TURN_STARTED`）必须写 `Triggered=1`，否则只触发一次。

---

## 五、核心概念（参考）

### Owner vs Subject

| 概念 | 含义 |
|------|------|
| **Owner** | Modifier 的"主体"——谁拥有这个 Modifier。通过 TraitModifiers 挂载时，Owner = 该玩家 |
| **Subject** | 被 Modifier 实际影响的对象，由 ModifierType 的 CollectionType 决定 |

| 条件列 | 检查对象 | 不满足时 |
|--------|---------|---------|
| `OwnerRequirementSetId` | Owner | Modifier **根本不触发** |
| `SubjectRequirementSetId` | 各 Subject | 不满足的 Subject **被跳过** |

### 层级与自动溯源（核心！）

**对象层级链**：`单位 → 地块 → 城市 → 玩家`

- **单位**可解析层级：地块（所在地块）、单位、玩家 —— **没有城市上级**（单位绑定城市级 Modifier/条件无效）
- **区域/建筑/改良**：所在城市 → 玩家
- **地块**：所在城市 → 玩家

**CollectionType 行为**：
| 集合 | 行为 |
|------|------|
| `COLLECTION_OWNER` | **唯一自动溯源 Owner** 的集合：区域→城市（城市级效果）；区域/建筑→玩家（玩家级效果）；单位→玩家（玩家级效果） |
| 其他集合（`PLAYER_UNITS`/`PLAYER_CITIES`/`CITY_DISTRICTS`/`ALL_UNITS`/`ALL_CITIES` 等） | **不溯源 Owner**，按集合语义直接解析：PLAYER_UNITS=挂载者所属玩家的单位；CITY_DISTRICTS=挂载者所属城市的所有区域 |

**Requirement 自动溯源 Subject**：条件会根据对象自动溯源到合适层级——
- 玩家层级条件（`REQUIREMENT_PLAYER_LEADER_TYPE_MATCHES`/`PLAYER_TURN_STARTED`/`PLAYER_HAS_CIVIC`）→ 溯源到所属玩家
- 地块层级条件（`REQUIREMENT_PLOT_FEATURE_TYPE_MATCHES`/`PLOT_PROPERTY_MATCHES`）→ 溯源到单位所在地块 / 城市市中心地块

**ADJACENT_TO_OWNER(_AT_WAR) 是双对象距离判定（勿混！）**：
- **sub**（动态）= collection 集合中遍历的每个对象，位置取 sub 自身（单位=所在地块、城市=市中心、地块=自身）
- **owner**（固定）= 修饰符挂载者（区域/建筑/改良/单位/地块均可）
- 判定 = sub 与 owner 的距离在 `[MinDistance, MaxDistance]`（AT_WAR 变体另需与 owner 交战）
- 典型：单位能力挂 `ALL_UNITS` + 该条件(1,1) → 相邻单位；挂 `ALL_CITIES` + 该条件(1,1) → 相邻城市（如夜归军-7防）；区域挂 `PLAYER_CITIES` + 该条件(0,6) → 6环城市光环

**OwnerReq 判定 Owner 自身**：单位 Owner 的 OwnerReq 判单位自身（含溯源）；玩家 Owner 判玩家。玩家级条件放 OwnerReq 时自动溯源到玩家。

**常见应用**：
- 单位绑定地块级效果（隐匿/禁疗/光环）→ SubjectReq 放地块条件，自动溯源单位所在地块
- 单位绑定玩家级集合贡献（每单位给全城产出）→ Ability 内挂 PLAYER_CITIES/PLAYER_UNITS，集合自动按所属玩家解析
- 区域绑定城市级效果 → COLLECTION_OWNER 溯源到城市（如 MODIFIER_SINGLE_CITY_* 挂 DistrictModifiers）
- 区域绑定玩家级效果 → COLLECTION_OWNER 溯源到玩家（如 MODIFIER_PLAYER_ADJUST_* 挂 DistrictModifiers）

### 挂载路径

```
TraitModifiers（间接，最常用）
  实体 → TraitType → TraitModifiers → Modifiers

EntityModifiers（直接，用于政策卡/科技/建筑/单位能力）
  EntityType → EntityModifiers → Modifiers
```

### Permanent 传递规则

`Trait → Modifier_A → Modifier_B(ATTACH) → GrantAbility`

源头（Trait）消失 → 其下所有 Attach、Grant Ability 效果全部消失，**除非写了 `Permanent=1`**。

### Attach 劫掠 Bug

被 ATTACH 的 Modifier 在区域/建筑/改良被劫掠修复后不会恢复。给这些实体 ATTACH 时需注意。

---

## 六、复杂模式

跨多个表联动的组合效果参考：**[patterns/INDEX.md](modifiers/patterns/INDEX.md)** — 7 种已验证模式（含"送单位"：建城/首都/区域/补员）。

写代码前对照检查清单：**[patterns/pre-code-checklist.md](modifiers/patterns/pre-code-checklist.md)**

---

## 七、引用文件

| 文件 | 用途 |
|------|------|
| [参数查询依据](../../SOURCES.md#类型与枚举) | EffectType 参数速查 |
| [参数查询依据](../../SOURCES.md#类型与枚举) | RequirementType 参数速查 |
| [CollectionType 查询依据](../../SOURCES.md#类型与枚举) | ~40 个 CollectionType |
