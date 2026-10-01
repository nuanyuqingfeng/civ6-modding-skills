# Modifier 通用技巧

> 本文档收录跨 EffectType 的通用 Schema 模式、常见陷阱和最佳实践。每个 EffectType 的参数详见同目录下 `modifier-*.md` 子文件。

---

## 技巧 1：Ability 的 TypeTags 过滤机制

**核心原则**：Ability 通过 TypeTags 绑定的 CLASS Tag **本身就是匹配过滤器**，不论 Inactive=0 还是 Inactive=1。

- `Inactive=0`：同 Tag 单位**自动获得**能力（无需任何 Modifier）
- `Inactive=1`：需 `EFFECT_GRANT_ABILITY` Modifier 手动授予，但**仍然受 Tag 过滤**——只有同 Tag 的单位才能被授予

**应用**：给特定兵种授予能力时，**不需要在 GRANT_ABILITY Modifier 上写 SubjectRequirementSet 按 PROMOTION_CLASS 筛选**。只需给 Ability 绑定对应 CLASS Tag，Tag 本身就会过滤。

**示例 — 只给远程+攻城单位授予能力**：

```sql
-- Ability 绑 Tag（Tag 过滤）
INSERT INTO TypeTags (Type, Tag) VALUES
('ABILITY_SIQI_RANGE_POWER', 'CLASS_RANGED'),
('ABILITY_SIQI_RANGE_POWER', 'CLASS_SIEGE');

-- Ability 设 Inactive=1
INSERT INTO UnitAbilities (...) VALUES
('ABILITY_SIQI_RANGE_POWER', NULL, '...', 1, 1);

-- 领袖特质授予，无需 SubjectRequirementSet
INSERT INTO Modifiers (ModifierId, ModifierType) VALUES
('MODIFIER_SIQI_GRANT_RANGE_POWER', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY');
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_GRANT_RANGE_POWER', 'AbilityType', 'ABILITY_SIQI_RANGE_POWER');
INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_LEADER_SIQI_xxx', 'MODIFIER_SIQI_GRANT_RANGE_POWER');
```

---

## 技巧 2：用 PLOTS 上下文检测战斗距离

**问题**：COMBATS 上下文中没有任何带 MinRange/MaxRange 的 RequirementType，无法直接检测"攻击者与目标的距离"。

**解决**：战斗 Modifier（`COLLECTION_UNIT_COMBAT`）中，Subject 是目标单位，其所在地块也是"地块"。因此可以用 **PLOTS 上下文的 RequirementType** 挂到 `SubjectRequirementSetId` 上。

**关键 RequirementType**：`REQUIREMENT_PLOT_ADJACENT_TO_OWNER`（参数 `MinDistance` / `MaxDistance`）

- Owner = 攻击方单位，Owner 所在地块 = 攻击起点
- Subject 地块 = 目标所在地块 = 攻击落点
- 两个地块的距离 = 攻击距离

**示例 — 攻击距离为 N 时战斗力 +N×3**：

```sql
-- 距离=5 时 +15 战斗力（10组硬编码，MinDist=MaxDist 精确匹配）
INSERT INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId) VALUES
('MODIFIER_DIST_5_COMBAT', 'MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH', 'REQSET_PLOT_DIST_5');

-- 条件：目标地块距离 Owner = 5
INSERT INTO Requirements (RequirementId, RequirementType) VALUES
('REQ_PLOT_DIST_5', 'REQUIREMENT_PLOT_ADJACENT_TO_OWNER');
INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_PLOT_DIST_5', 'MinDistance', 5),
('REQ_PLOT_DIST_5', 'MaxDistance', 5);
```

> **为什么 MinDist = MaxDist？** 范围条件（如 MinDist=1 MaxDist=5）会导致符合条件的多个 Modifier 同时生效、预览文本出现多条。精确匹配保证每次只有一个 Modifier 命中，预览干净。

---

## 技巧 3：ModifierStrings（效果预览文本）—— 战斗力类**必写**

**结论**：整条链路上**只有 `EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` 一种效果器支持预览文本**（Context 固定 `Preview`）。
凡是 EffectType 为它的 modifier（`MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH`、`MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_STRENGTH`、`MODIFIER_PLAYER_UNITS_ADJUST_COMBAT_DIFFICULTY` 等），
**必须写 `ModifierStrings`**：不写**不会报错、不会崩**，但**战斗预览面板看不到这层加成的来源**——典型的"沉默失效"，最容易整批漏掉。

- 原版数据：`EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` 共 226 个实例，**221 个都写了** Preview。
- 作者既有工程 0043–0054 的每个战斗力 modifier（含 Property 读出口）也都写了。
- 该效果类型的 `ModifierStrings`（Preview）建议必写；交付前自查 `Modifiers` 表对应行是否配了 Preview 文本。

### 三种 Context（别混用）

| Context | 作用 | 何时必须写 | 实例 |
|---|---|---|---|
| `Preview` | 战斗预览面板的加成行 | EffectType = `EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` | `LOC_ABILITY_STRONG_WHEN_ATTACKING_DESCRIPTION` = `进攻时+{1_Amount} [ICON_Strength] 战斗力` |
| `Summary` | 伟人面板的效果摘要 | 伟人「诞生时」类 modifier（`GreatPersonIndividualBirthModifiers`） | `01-core-tables/greatperson.md` |
| `Sample` | 外交面板的简短原因 | 议程 modifier | `01-core-tables/agenda.md` |

### 写什么（占位符）

| 参数形态 | 模板 | 例 |
|---|---|---|
| `Amount`（数值） | `+{1_Amount} [ICON_Strength] 战斗力（来源）` | `+{1_Amount} [ICON_Strength] 战斗力（恶魔的助威）` |
| `Key`（Property 读出口） | `+{Property} [ICON_Strength] 战斗力（来源）` | `+{Property} [ICON_Strength] 战斗力（来自魔界电视台）` |
| 百分比 | `+{1_Amount}% …（来源）` | `+{1_Amount}% 掠夺产出` |

- 占位符**统一用 `{1_Amount}`**：工具模版（`_handle_gen_modifier_preview_text`）与绝大多数原版能力文本都是 `{1_Amount}`。
  （`{Amount}` 也能被引擎解析——原版仅个别文本如 `LOC_COMBAT_DIFFICULTY_SCALING` 用它——但**同一工程里混用两种写法没有好处**，且老 skill 模板里的 `{Amount}` 已统一改为 `{1_Amount}`。）
- 预览行要**短**：只讲"加多少 + 来源"。整段能力描述不要塞进来（会被战斗面板截断且难读）。

### 在工程里的落地

- 对应字段：`ModifierStrings.Text`（`Context` 固定为 `Preview`；按参数骨架手写 `+{1_Amount} 来自` / `+{Property} 来自`）。
- 导出时**生成两行，缺一不可**：
  1. `modifier_workspace` → `INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES ('MOD_X','Preview','LOC_MOD_X_PREVIEW');`
  2. `workspace_page._modifier_strength_preview_text_rows()` → `('zh_Hans_CN','LOC_MOD_X_PREVIEW','<preview_text 原文>');`
- **两行都以 `preview_text` 非空为前提**：留空则这一对**静默跳过**（既无 ModifierStrings 行，也无 LOC 文本）。

### 自检

- [ ] 每个 EffectType = `EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` 的 modifier 都有 `ModifierStrings` 行
- [ ] 对应 `LOC_{ModifierId}_PREVIEW` 在 Text SQL 里有中文文本
- [ ] 占位符是 `{1_Amount}` / `{Property}`，不是 `{Amount}`
- [ ] 数值型与 `Key` 型用了对应的模板（不要给 Property 读出口写 `{1_Amount}`）

---

## 技巧 4：世界奇观的效果要挂 `BuildingModifiers`，**不要**挂 `DistrictModifiers(DISTRICT_WONDER)`

**实机结论（0055 实测）**：奇观在**选区落位时**就会先生成一个虚拟的 `DISTRICT_WONDER` 区域，
因此把 modifier 挂到 `DistrictModifiers` 的 `DISTRICT_WONDER` 上，**奇观还没造完就已经生效**（提前吃加成）。

| 挂载点 | 触发时机 | 结论 |
|---|---|---|
| `DistrictModifiers` / `DISTRICT_WONDER` | 奇观**落位**（虚拟区域一存在即生效） | ❌ 提前生效 |
| `BuildingModifiers` / 各奇观建筑（`IsWonder=1`） | 奇观**建成**（建筑进入城市） | ✅ 正确 |

**遍历方式用 `INSERT...SELECT`，不要手抄清单**（奇观清单随资料片/DLC/其他 Mod 变化，硬编码必漏）：

```sql
-- 存为工程数据 SQL：Data/<工程名>_Wonders.sql（登记走 UpdateDatabase 动作，见 action-splitting.md）
INSERT INTO BuildingModifiers (BuildingType, ModifierId)
SELECT BuildingType, 'MODIFIER_SIQI_0055_WONDER_SCIENCE_100'
FROM Buildings WHERE IsWonder = 1;
```

- Modifier 本体（`Modifiers` / `ModifierArguments` / RequirementSet）写在工程数据 SQL（数据类 `UpdateDatabase` 动作；加载动作划分与 `LoadOrder` 纪律见 `civ6-modding/reference/action-splitting.md`）；
  自定义 SQL 只补**挂载行**（`INSERT...SELECT` 是合法模式）。
- **两种"给城市的百分比产出"类型，原版都在用（挂建筑上都成立）**：

  | ModifierType | 集合 | 原版建筑挂载实例 |
  |---|---|---|
  | `MODIFIER_SINGLE_CITY_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_OWNER`（= 拥有该建筑的**那一座**城市） | 奇观：`BROADWAY_ADDCULTUREYIELD` / `OXFORD_ADDSCIENCEYIELD` / `RUHRVALLEY_ADDPRODUCTIONYIELD` / `KILWA_SINGLE_*` |
  | `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_MODIFIER` | `COLLECTION_PLAYER_CITIES`（= 该玩家所有城市，靠 subject reqset 过滤） | `AMUNDSEN_SCOTT_*` / `KILWA_PLAYERCITIES_*` / `CASA_DE_CONTRATACION_*`（原版共 153 条） |

  **本工程统一用 cities 版**（需求分工明确：玩家级挂 owner、城市级挂 subject；与 0050 的既有写法一致）。

### ⚠ 需求上下文：`Subject` 是城市，`Owner` 是挂载对象 / 其拥有者玩家

这是最容易写错的一步（0055 踩过两轮）：**`SubjectRequirementSetId` 不是"这个建筑"，而是"效果作用的对象"**。

| 需求想说什么 | 写哪一侧 | 原版/工程先例 |
|---|---|---|
| 城市/地块自身条件（有驻军、有某区域、有某地形、相邻某物） | **subject**（= 城市；地块按**城市地块 = 市中心格**求值） | `AMUNDSEN_SNOW_ADDSCIENCEYIELD`（`REQUIREMENT_CITY_HAS_X_TERRAIN_TYPE`）、`CITY_HAS_HOLY_SITE`、`STATUELIBERTY_CITIES_ALWAYS_LOYAL` |
| 玩家/领袖级条件（本文明限定、某领袖） | **owner**（= 挂载对象的拥有者玩家） | 0050 `REQSET_SIQI_0050_IS_LEADER`（`REQUIREMENT_PLAYER_LEADER_TYPE_MATCHES`）挂在 **owner** 侧 ×20 条建筑挂载；0055 遗物 modifier 同 |
| 同上，但写在 subject 侧 | 也能跑（引擎按"城市的拥有者玩家"求值） | `KILWA_*` 的 `REQUIREMENT_PLAYER_IS_SUZERAIN_X_TYPE` 就在 subject 侧 reqset 里 —— 原版两种都有人用，**本工程统一走 owner 侧** |

`REQUIREMENT_PLOT_ADJACENT_TO_OWNER` 里的 **owner = 挂载对象**（modifier 的来源实例），**不是玩家**：

- `NAZCA_LINE_ADJACENCY_FAITH`（`ImprovementModifiers` + 玩家级集合 `COLLECTION_PLAYER_PLOTS`）用 `ADJACENT_TO_OWNER`（无参数，默认 1 环）
  = "与该改良设施相邻的格"；`AOE_REQUIRES_OWNER_ADJACENCY{Min=0,Max=2}` 用于伟人光环 = "与该伟人 2 格内的单位"。
- 挂在奇观建筑上时 owner 就是**那一座奇观**；每座奇观各有一条挂载行，所以"城市相邻的奇观数"能自然叠加。距离惯例：**恰好 N 环 = `Min=N, Max=N`**；**N 环内 = `Min=0, Max=N`**。

**0055 天界天使学校实战定型**（每有一奇观与市中心相邻，有该校的城市 +100% 科文）：

```
modifier: modifier_type = MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_MODIFIER (COLLECTION_PLAYER_CITIES)
          owner_reqset   = REQSET_SIQI_0055_IS_OUR_CIV              -- 玩家级 → owner 侧
          subject_reqset = REQSET_SIQI_0055_CITY_ADJ_WONDER_SCHOOL  -- 城市级 → subject 侧（TEST_ALL）
              ├ REQUIREMENT_PLOT_ADJACENT_TO_OWNER{MinDistance=1, MaxDistance=1}  -- 该城市与这座奇观相邻 1 环
              └ REQUIREMENT_CITY_HAS_DISTRICT{DistrictType=DISTRICT_SIQI_D0055_2} -- 该城市有特色学院
挂载：INSERT INTO BuildingModifiers SELECT BuildingType, '<ModifierId>' FROM Buildings WHERE IsWonder = 1;
```

| 想表达 | 正确写法 | 错误写法 |
|---|---|---|
| 该奇观与**这座**城市相邻 1 环 | `REQUIREMENT_PLOT_ADJACENT_TO_OWNER{MinDistance=1, MaxDistance=1}`（owner=挂载对象即该奇观，subject=城市） | — |
| 城市相邻任意奇观 | `REQUIREMENT_PLOT_ADJACENT_TO_WONDER`（无参数，1 环；原版只用于改良设施，`CHATEAU_WONDERADJACENCY_CULTURE`） | — |
| 城市 N 格内有某建筑 | `REQUIREMENT_PLOT_ADJACENT_BUILDING_TYPE_MATCHES{BuildingType=…, MinRange=0, MaxRange=N}`（原版 `REQUIRES_PLOT_HAS_LIBERTY_WITHIN_6` 等 3 例） | — |
| 城市有某区域 | `REQUIREMENT_CITY_HAS_DISTRICT{DistrictType=…}` + `inverse=true` 表示"没有" | — |
| ❌ "城市相邻市中心" | — | `PLOT_ADJACENT_DISTRICT_TYPE_MATCHES{DistrictType=DISTRICT_CITY_CENTER}` —— subject 是城市，等于问"城市是否相邻市中心"，**自指恒假** |

- 想用 `PLOT_ADJACENT_BUILDING_TYPE_MATCHES` 表达"相邻**这一座**奇观"是做不到的（参数是**类型**）——
  一个 ModifierId 挂到全部奇观时无法区分是哪一座，只能用 `PLOT_ADJACENT_TO_OWNER` + 逐奇观挂载。

### 加载顺序：自定义文件要独立顺序，必须给独立动作 id

- 自定义 SQL 走 `UpdateDatabase` 类动作时，动作 id 默认就是该类型名（默认 LoadOrder 10000）；
- 注册按 **(type, id)** 合并 —— 同 id 会并进已有那一组，**拿不到自己的顺序**；
- 要独立顺序：新增一条动作并给**不同 id**（如 `UpdateDatabaseWonders`）+ 明确 `LoadOrder`，
  同时确认该文件**没有**同时留在原组里（否则会执行两次 → 主键冲突）。
  奇观类 SQL 需要 199999：确保执行时 `Buildings` 表已被原版/资料片/其他 Mod 填满。

```xml
<UpdateDatabase id="UpdateDatabase"><Properties><LoadOrder>9999</LoadOrder></Properties>…生成数据…</UpdateDatabase>
<UpdateDatabase id="UpdateDatabaseWonders"><Properties><LoadOrder>199999</LoadOrder></Properties>
  <File>Data/Siqi_Leaders_0055_Wonders.sql</File>
</UpdateDatabase>
```

---

## 技巧 5：发遗物 / 放巨作前，建筑必须先在 `Building_GreatWorks` 里「登记」槽位

**实机问题（0055 神社遗物）**：`MODIFIER_PLAYER_GRANT_RELIC`（`EFFECT_GRANT_RELIC`）发遗物时，
引擎要找一个**能存放遗物的建筑**，判据是 `Building_GreatWorks` 里有没有该建筑的槽位行。
神社（`BUILDING_SHRINE`）本体一个巨作槽都没有 → 识别不通过 → 遗物发不出去。
而本 Mod 的"神社 +1 遗物槽"是 **Modifier** 给的（`EFFECT_ADJUST_EXTRA_GREAT_WORK_SLOTS`）——
**Modifier 给的槽不算"登记"**，两者互相不认。

| 概念 | 作用 | 写法 |
|---|---|---|
| **槽容量** | 让建筑能装几个巨作（手动放置有效） | `MODIFIER_PLAYER_CITIES_ADJUST_EXTRA_GREAT_WORK_SLOTS`，参数 `BuildingType` / `GreatWorkSlotType` / `Amount`（原版 `TRAIT_DOUBLE_ARCHAEOLOGY_SLOTS`、`TRAIT_EXTRA_PALACE_SLOTS`、`SUNDIATA_KEITA_MARKET_GREAT_WRITING_SLOTS` 同款） |
| **槽登记** | 让引擎知道"这种建筑可以装这种巨作"（0 槽也写一行） | `Building_GreatWorks` 插行，`NumSlots` 可写 **0** |

> **为什么"容量够"还不够**：原版马里（桑迪亚塔）给市场 +2 写作槽，而 `BUILDING_MARKET` 在
> `Building_GreatWorks` 里**根本没有行** —— 说明 Modifier 给的槽对手动放置/容量统计是有效的。
> 但 `EFFECT_GRANT_RELIC` 这种"引擎自己找空槽位"的发放走的是**登记表**（作者 0055 实测：
> 只靠 Modifier 给槽时遗物发不出来），所以原版建筑要补一行登记。

**冲突安全的登记 SQL**（走自定义文件通道，独立动作 id + 尽量晚的 `LoadOrder`）：

```sql
INSERT OR IGNORE INTO Building_GreatWorks (BuildingType, GreatWorkSlotType, NumSlots)
SELECT 'BUILDING_SHRINE', 'GREATWORKSLOT_RELIC', 0
WHERE NOT EXISTS (
    SELECT 1 FROM Building_GreatWorks
    WHERE BuildingType = 'BUILDING_SHRINE' AND GreatWorkSlotType = 'GREATWORKSLOT_RELIC'
);
```

- 主键 = `(BuildingType, GreatWorkSlotType)`；`NumSlots` 有默认值 **1**，所以要 0 槽必须显式写 0；
- `INSERT OR IGNORE`：主键撞车不报错、**不覆盖**别人的数值；`WHERE NOT EXISTS`：即使该表没有主键约束也不会插重复行；
- **只 INSERT 不 UPDATE**：别的 Mod 若已给该建筑登记（甚至给了 1 槽），整条跳过，保持对方数值；
- **加载顺序尽量晚**（0055 用 `LoadOrder 200000`，比奇观补丁的 199999 更晚）：让别人的登记行先落地才跳得掉。
  唯一残留风险是"比我们还晚、且用**裸 INSERT** 的 Mod"会撞主键 —— 任何登记补丁都躲不掉，晚加载是唯一缓解。

**相关事实**：`GREATWORKSLOT_*` 共 7 种（`ART`/`ARTIFACT`/`CATHEDRAL`/`MUSIC`/`PALACE`/`RELIC`/`WRITING`）；
原版有遗物槽的建筑只有 5 个：`BUILDING_TEMPLE`(1)、`BUILDING_PRASAT`(1)、`BUILDING_STAVE_CHURCH`(1)、
`BUILDING_MONT_ST_MICHEL`(2)、`BUILDING_ST_BASILS_CATHEDRAL`(3)。
⚠ **遗物必须用 `GREATWORKSLOT_RELIC`** —— 写成 `GREATWORKSLOT_PALACE` 时槽位在 UI 上照样显示，但遗物进不去（0055 踩过）。

- 现成实现参考：原版发遗物只有 3 处 —— 部落村庄 `GOODY_CULTURE_GRANT_ONE_RELIC`（带 `RelicSource`）、
  贞德激活 `GREATPERSON_JOAN_OF_ARC_ACTIVE`、宗教紧急事件奖励；坎迪（Kandy）那条不是"发"而是
  `EFFECT_ADJUST_NATURAL_WONDER_RELIC`（改自然奇观触发时获得的遗物数量）。
  也就是说：**"把遗物塞进某个指定建筑"这种效果原版没有**，能做的只是"发 1 个遗物，由引擎自己找空槽位"。
