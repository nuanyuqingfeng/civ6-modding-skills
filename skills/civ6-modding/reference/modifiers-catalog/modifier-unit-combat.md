# modifier-unit-combat -- 单位战斗/属性/移动/经验/间谍/旅游/宗教等 EffectType

> 类型来源：本页为历史参数与实例参考，可能含其他 Mod 的自定义 ModifierType。使用前按 `civ6-modding/database/README.md` 的来源口径（`source_index.sqlite` 行级来源）核实，不因表中列出便跳过注册。

> 预览文本支持范围以 [通用技巧](modifier-techniques.md) 为准；已清理旧生成模板对其他效果统一标“需要 ModifierStrings”的提示。历史样例仅作来源线索。

> 共 165 个 EffectType（来自 DynamicModifiers 表），按子类别分组。参数值来自 ModifierArguments 表中真实使用示例。
> 每个条目通过溯源法生成：DynamicModifiers -> ModifierType -> ModifierId -> 上游主体 -> LOC 中文描述 -> 反推效果含义。

## 目录

1. [战斗力/属性](#战斗力属性)
2. [移动力](#移动力)
3. [经验/等级](#经验等级)
4. [回血/治疗](#回血治疗)
5. [生产/购买](#生产购买)
6. [间谍](#间谍)
7. [宗教传播](#宗教传播)
8. [掠夺/劫掠](#掠夺劫掠)
9. [旅游/摇滚乐队](#旅游摇滚乐队)
10. [视野/可见性](#视野可见性)
11. [其他](#其他)

---

## 战斗力/属性

### EFFECT_ADJUST_ADJACENT_LEVIED_UNIT_COMBAT_BONUS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_COMBAT_FOR_ADJACENT_LEVIED_UNITS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `3` |

**效果**：调整相邻征召单位的近战战斗力（绝对值加成）
> **溯源**：单位能力 — 匈牙利黑军（`ABILITY_BLACK_ARMY`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_NUMBER_ALLIES_UNIT_COMBAT_BONUS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_COMBAT_FOR_NUMBER_ALLIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `3` |

**效果**：根据相邻友军数量调整单位近战战斗力
> **溯源**：单位能力 — 克鲁兹起义军（`ABILITY_HUSZAR`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_AGAINST_DISTRICT_COMBAT_BONUS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_GOVERNOR_ADJUST_DISTRICT_COMBAT_BONUS` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `10` |

**效果**：调整单位对区域攻击时的战斗力加成
> **溯源**：总督晋升 — 塞拉斯克尔（`GOVERNOR_PROMOTION_SERASKER`） — 赋予总督晋升能力

---

### EFFECT_ADJUST_UNIT_ANTI_AIR_STRENGTH

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_ANTI_AIR_STRENGTH_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `40` |

**效果**：调整单位的防空战斗力
> **溯源**：单位晋升 — 无人机防空（`PROMOTION_GDR_AA_DEFENSE`） — 赋予单位晋升效果（无人机防空）

---

### EFFECT_ADJUST_UNIT_ATTACK_RANGE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_ATTACK_RANGE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_ATTACK_RANGE` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2` |

**效果**：调整单位的攻击范围（射程）
> **溯源**：单位能力 — ABILITY_RECEIVE_RANGE_BONUS（`ABILITY_RECEIVE_RANGE_BONUS`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 前方观察员（`PROMOTION_FORWARD_OBSERVERS`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 副油箱（`PROMOTION_DROP_TANKS`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 远程（`PROMOTION_LONG_RANGE`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 测距一致（`PROMOTION_COINCIDENCE_RANGEFINDING`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ADVANCED_COASTAL_RAID

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ADVANCED_COASTAL_RAID` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UseAdvancedCoastalRaid` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位高级海岸劫掠能力
> **溯源**：单位能力 — 海盗（`ABILITY_CORSAIR`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_ADVANCED_PILLAGING

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ADVANCED_PILLAGING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UseAdvancedPillaging` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位高级掠夺能力
> **溯源**：单位晋升 — 掠夺（`PROMOTION_DEPREDATION`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 超级堡垒（`PROMOTION_SUPERFORTRESS`） — 赋予单位晋升效果
> **溯源**：单位能力 — ABILITY_MAPUCHE_MALON_RAIDER（`ABILITY_MAPUCHE_MALON_RAIDER`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_BARBARIAN_COMBAT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_BARBARIAN_COMBAT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `15`、`5` |

**效果**：调整单位对蛮族的战斗力
> **溯源**：政策 — 纪律（`POLICY_DISCIPLINE`） — 通过政策卡提供加成
> **溯源**：文明/领袖特性 — 我来，我见，我征服（`TRAIT_LEADER_CAESAR`） — 文明或领袖特性效果


---

### EFFECT_ADJUST_UNIT_BYPASS_COMBAT_UNIT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_BYPASS_COMBAT_UNIT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Bypass` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许单位绕过敌方战斗单位移动
> **溯源**：单位能力 — 针对性攻击（`ABILITY_BYPASS_COMBAT_UNIT`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_BYPASS_WALLS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_BYPASS_WALLS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Enable` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许近战单位绕过城墙直接攻击市中心
> **溯源**：单位能力 — 绕开城墙（`ABILITY_BYPASS_WALLS`） — 赋予单位特殊能力（允许近战单位绕开城墙。）

---

### EFFECT_ADJUST_UNIT_BYPASS_WALLS_PROMOTION_CLASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_BYPASS_WALLS_PROMOTION_CLASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `PromotionClass` | 是 | `PROMOTION_CLASS_ANTI_CAVALRY`、`PROMOTION_CLASS_MELEE` |

**效果**：允许指定晋升类别的单位绕开城墙
> **溯源**：单位能力 — ABILITY_BYPASS_WALLS_PROMOTION_CLASS（`ABILITY_BYPASS_WALLS_PROMOTION_CLASS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_CANNOT_ATTACK

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_CANNOT_ATTACK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Disable` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：禁止单位发动攻击
> **溯源**：单位能力 — 和平卫士（`ABILITY_RELIGIOUS_CANNOT_ATTACK`） — 赋予单位特殊能力（阻止单位攻击。）

---

### EFFECT_ADJUST_UNIT_COMBAT_CAPTURE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_COMBAT_CAPTURE` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：调整单位在战斗中俘获敌方单位的能力
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_COMBAT_STRENGTH

调整单位的**基础战斗力**（直接加在 Combat/RangedCombat 属性上，UI 中显示为基础值变化）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_BASE_COMBAT_STRENGTH` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数，绝对值加成 |
| `Type` | 可选 | `MELEE`=近战（Combat）/ `RANGED`=远程（RangedCombat）/ `ANTIAIR`=防空（AntiAirCombat）/ `BOMBARD`=轰炸（Bombard）。不填默认 MELEE |

```sql
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_UNIT_BASE_STRENGTH', 'Amount', '5'),
('MODIFIER_SIQI_UNIT_BASE_STRENGTH', 'Type', 'RANGED');
```

**效果**：直接修改单位面板上的基础战斗力，叠加在 Combat 或 RangedCombat 字段上。
> **溯源**：官方无 Modifiers 实例，工坊广泛使用。
> **不需要 ModifierStrings**（基础值变化直接在单位面板可见，无需额外 UI）

---

### EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER

调整单位在战斗中的**实际战斗力**（战斗上下文中生效，不影响基础面板值）。

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` | `COLLECTION_UNIT_COMBAT` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | **必写** | 整数，绝对值加成 |

**两种写法：**

| 写法 | 参数 | ModifierStrings | 说明 |
|------|------|----------------|------|
| **固定值** | `Amount='4'` | `+{1_Amount} [ICON_Strength] 战斗力` | `{1_Amount}` 解析为该 Modifier 的 Amount 值 |
| **变化值** | `Key='PROP_KEY'` | `+{Property} [ICON_Strength] 战斗力（来源）` | 战斗力取该 Property 当前值 |

Property 赋值方式（**二选一，不能混用**）：
- `EFFECT_ADJUST_UNIT_PROPERTY`（`Key='PROP_KEY'`，Amount=数值）
- Lua `UnitManager.SetProperty(unitId, 'PROP_KEY', value)`

```sql
-- 固定值写法（官方标准）
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_COMBAT_FIXED', 'Amount', '5');
-- 模式 A：LOC 引用 + {1_Amount}（数值动态读取）
INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES
('MODIFIER_SIQI_COMBAT_FIXED', 'Preview', 'LOC_COMBAT_FIXED_PREVIEW');
-- LOC_COMBAT_FIXED_PREVIEW = "进攻时+{1_Amount} [ICON_Strength] 战斗力"
-- UI 显示：进攻时+5 战斗力
-- 负值写法（设计意图为减益时）："防御时{1_Amount} [ICON_Strength] 战斗力"（不带 +）

-- 模式 B：晋升内联模板（数量多时统一格式，不建 LOC）
INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES
('MODIFIER_SIQI_COMBAT_FIXED', 'Preview', '+{1_Amount} {LOC_PROMOTION_SIQI_NAME} {LOC_PROMOTION_DESCRIPTOR_PREVIEW_TEXT}');
-- UI 显示：+5 思琪战吼 战斗力

-- 变化值写法（用 {Property} 显示属性值）
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_COMBAT_VAR', 'Key', 'PROP_COMBAT_BONUS');
INSERT INTO ModifierStrings (ModifierId, Context, Text) VALUES
('MODIFIER_SIQI_COMBAT_VAR', 'Preview', 'LOC_COMBAT_VAR_PREVIEW');
-- LOC_COMBAT_VAR_PREVIEW = "{Property} [ICON_Strength] 战斗力"
-- Property 值可为正或负，不加 + 前缀，负值时自动显示为 -5
```

> **溯源**：DEFENDER_OF_FAITH_COMBAT_BONUS_MODIFIER（守护者信仰，Amount=5）/ OLIGARCHY_MELEE_BUFF（寡头政体，Amount=4）/ ANTI_SPEAR（反骑兵晋升，Amount=10）等 20 个官方固定值实例。变化值（Key=Property 名）见工坊。
---

### EFFECT_ADJUST_UNIT_COMBAT_UNIT_CAPTURE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_COMBAT_UNIT_CAPTURE` | `COLLECTION_UNIT_COMBAT` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanCapture` | 是 | `1`（`1`=是 / `0`=否） |
| `UnitType` | 是 | `UNIT_BUILDER` |

**效果**：允许俘虏特定类型的敌方单位
> **溯源**：单位能力 — 被俘船（`ABILITY_PRIZE_SHIPS`） — 赋予单位特殊能力
> **溯源**：单位能力 — 俘获工人（`ABILITY_CAPTIVE_WORKERS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_CONVERTS_BARBARIANS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_CONVERTS_BARBARIANS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Converts` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位转化蛮族为己方单位的能力
> **溯源**：单位晋升 — 异教徒信仰转变（`PROMOTION_HEATHEN_CONVERSION`） — 赋予单位晋升效果
> **溯源**：单位能力 — ABILITY_QIN_MELEE_UNITS（`ABILITY_QIN_MELEE_UNITS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_DAMAGE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_DAMAGE` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_DAMAGE` | `COLLECTION_OWNER` |
| `MODIFIER_WORLD_UNITS_ADJUST_DAMAGE` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-100`、`30` |

**效果**：对单位造成直接伤害（正数=伤害，负数=治疗）
> **溯源**：伟人能力 — 安东尼奥·何塞·苏克雷（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_JOSE_DE_SUCRE`）
> **溯源**：伟人能力 — 弗朗西斯科·德保拉·桑坦德尔（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_PAULA_SANTANDER`）
> **溯源**：伟人能力 — 何塞·安东尼奥·派斯（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_ANTONIO_PAEZ`）
> **溯源**：伟人能力 — 拉斐尔·乌达内塔（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_URDANETA`）
> **溯源**：伟人能力 — 圣地亚哥·马里诺（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_MARINO`）

---

### EFFECT_ADJUST_UNIT_DIPLO_VISIBILITY_COMBAT_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_DIPLO_VISIBILITY_COMBAT_MODIFIER` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_ALL_UNITS_ADJUST_DIPLO_VISIBILITY_COMBAT_MODIFIER` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2`、`3` |
| `DeltaWithOpponent` | 是 | `1` |

**效果**：根据外交能见度差距提供战斗力加成
> **溯源**：文明/领袖特性 — 驿站（`TRAIT_CIVILIZATION_MONGOLIAN_ORTOO`） — 文明或领袖特性效果
> **溯源**：文明/领袖特性 — TRAIT_LEADER_MAJOR_CIV（`TRAIT_LEADER_MAJOR_CIV`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ENABLE_WALL_ATTACK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Enable` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许近战单位攻击城墙
> **溯源**：单位能力 — 启用城墙攻击（`ABILITY_ENABLE_WALL_ATTACK`） — 赋予单位特殊能力（允许近战单位攻击城墙。）

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_PROMOTION_CLASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ENABLE_WALL_ATTACK_PROMOTION_CLASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `PromotionClass` | 是 | `PROMOTION_CLASS_ANTI_CAVALRY`、`PROMOTION_CLASS_MELEE` |

**效果**：允许指定晋升类别的单位攻击城墙
> **溯源**：单位能力 — ABILITY_ENABLE_WALL_ATTACK_PROMOTION_CLASS（`ABILITY_ENABLE_WALL_ATTACK_PROMOTION_CLASS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_PROMOTION_CLASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_ENABLE_WALL_ATTACK_WHOLE_GAME_PROMOTION_CLASS` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `PromotionClass` | 是 | `PROMOTION_CLASS_ANTI_CAVALRY`、`PROMOTION_CLASS_MELEE`、`PROMOTION_CLASS_RANGED` |

**效果**：全局允许指定晋升类别的单位攻击城墙
> **溯源**：文明/领袖特性 — 里人格（`TRAIT_CIVILIZATION_NIGHTMARE`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：全局允许相同宗教文明的单位攻击城墙

---

### EFFECT_ADJUST_UNIT_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION_PROMOTION_CLASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_ENABLE_WALL_ATTACK_WHOLE_GAME_SAME_RELIGION_PROMOTION_CLASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `PromotionClass` | 是 | `PROMOTION_CLASS_HEAVY_CAVALRY`、`PROMOTION_CLASS_LIGHT_CAVALRY` |

**效果**：全局允许同宗教文明指定晋升类别的单位攻击城墙
> **溯源**：文明/领袖特性 — 生于紫室（`TRAIT_LEADER_BASIL`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_ERA_STRENGTH_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ERA_STRENGTH_MODIFIER` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：根据时代差异调整单位战斗力
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_EVICT_PERCENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_EVICT_PERCENT` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_EVICT_PERCENT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `25`、`50` |

**效果**：调整宗教单位驱逐敌方宗教的压力百分比
> **溯源**：单位晋升 — 劝导者（`PROMOTION_PROSELYTIZER`） — 赋予单位晋升效果
> **溯源**：文明/领袖特性 — 艾思科里亚（`TRAIT_LEADER_EL_ESCORIAL`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_EXERT_ZOC

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_EXERT_ZOC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Exert` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予/移除单位的控制区（ZOC）能力
> **溯源**：单位晋升 — 压制（`PROMOTION_SUPPRESSION`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_FIGHT_WHILE_EMBARKED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_FIGHT_WHILE_EMBARKED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanFight` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许单位在登船状态下发动战斗
> **溯源**：单位能力 — ABILITY_UNIT_FIGHT_WHILE_EMBARKED（`ABILITY_UNIT_FIGHT_WHILE_EMBARKED`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_FLANKING_BONUS_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_FLANKING_BONUS_MODIFIER` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_FLANKING_BONUS_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Percent` | 是 | `100`、`50` |

**效果**：调整单位的侧翼夹击加成倍率
> **溯源**：单位能力 — ABILITY_HORATIO_NELSON_FLANKING_BONUS（`ABILITY_HORATIO_NELSON_FLANKING_BONUS`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_GEORGY_ZHUKOV_FLANKING_BONUS（`ABILITY_GEORGY_ZHUKOV_FLANKING_BONUS`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 两翼包围（`PROMOTION_DOUBLE_ENVELOPMENT`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 无影拳（`PROMOTION_MONK_SHADOW_STRIKE`） — 赋予单位晋升效果
> **溯源**：单位能力 — ABILITY_ZULU_IMPI（`ABILITY_ZULU_IMPI`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_FORCE_RETREAT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_FORCE_RETREAT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `ForceRetreat` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位强制击退敌方单位的能力
> **溯源**：单位能力 — ABILITY_PUSHBACK（`ABILITY_PUSHBACK`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_FRIENDLY_TERRITORY_COMBAT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_FRIENDLY_TERRITORY_COMBAT` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_FRIENDLY_TERRITORY_COMBAT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `15`、`35` |

**效果**：调整单位在友方领土中的战斗力
> **溯源**：单位能力 — 友好领土优势（`ABILITY_FRIENDLY_TERRITORY_RELIGIOUS`） — 赋予单位特殊能力（在友方领土中时获得 [ICON_Strength] 战斗力加成。）
> **溯源**：单位能力 — 宗教审讯（`ABILITY_INQUISITION_FRIENDLY_TERRITORY_BONUS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_HOLY_CITIES_COMBAT_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_COMBAT_FOR_NUMBER_HOLY_CITIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `3` |

**效果**：根据圣城数量调整单位战斗力
> **溯源**：单位能力 — 圣城之战（`ABILITY_BYZANTIUM_COMBAT_UNITS`） — 赋予单位特殊能力
> **溯源**：单位能力 — 圣城宗教战斗力（`ABILITY_BYZANTIUM_RELIGIOUS_UNITS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_IGNORE_CLIFF_WALLS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_CLIFF_WALLS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许单位忽略悬崖移动限制
> **溯源**：单位晋升 — 突击队（`PROMOTION_COMMANDO`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_IGNORE_RANGED_VS_DISTRICT_PENALTY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_IGNORE_RANGED_VS_DISTRICT_PENALTY` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_IGNORE_RANGED_VS_DISTRICT_PENALTY` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：忽略远程单位对区域攻击的减伤惩罚
> **溯源**：单位晋升 — 粒子束攻城巨炮（`PROMOTION_GDR_SIEGE_LASER`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_IGNORE_RESOURCE_MAINTENANCE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_RESOURCE_MAINTENANCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：免除单位的战略资源维护需求
> **溯源**：单位能力 — ABILITY_LINCOLN_MELEE_UNITS（`ABILITY_LINCOLN_MELEE_UNITS`） — 赋予单位特殊能力
> **溯源**：伟人能力 — 安东尼奥·何塞·苏克雷（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_JOSE_DE_SUCRE`）
> **溯源**：单位能力 — 跑马场（`ABILITY_FREE_RESOURCE_MAITENANCE_HIPPODROME`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_IGNORE_STRATEGIC_RESOURCE_LEVIED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_LEVIED_UNIT_IGNORE_STRATEGIC_RESOURCE` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：免除征召单位的战略资源维护需求

---

### EFFECT_ADJUST_UNIT_IGNORE_ZOC

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_ZOC` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位忽略敌方控制区（ZOC）的能力
> **溯源**：单位能力 — 忽略控制区（`ABILITY_IGNORE_ZOC`） — 赋予单位特殊能力（未受控制区影响）

---

### EFFECT_ADJUST_UNIT_MILITARY_FORMATION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_MILITARY_FORMATION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `MilitaryFormationType` | 是 | `ARMY_MILITARY_FORMATION`、`CORPS_MILITARY_FORMATION` |

**效果**：将单位升级为军团/军队等编队形态
> **溯源**：伟人能力 — 盖尤斯·杜伊路斯（`GREAT_PERSON_INDIVIDUAL_GAIUS_DUILIUS`）（由一个军事海军单位形成一支舰队。）
> **溯源**：伟人能力 — 圣·克鲁斯（`GREAT_PERSON_INDIVIDUAL_SANTA_CRUZ`）（由一个军事海军单位形成一支无敌舰队。）
> **溯源**：伟人能力 — 艾尔·熙德（`GREAT_PERSON_INDIVIDUAL_EL_CID`）（把一个军事陆地单位变成军团。）
> **溯源**：伟人能力 — 拿破仑·波拿巴（`GREAT_PERSON_INDIVIDUAL_NAPOLEON_BONAPARTE`）（把一个军事陆地单位变成军队。）

---

### EFFECT_ADJUST_UNIT_MILITARY_POLICIES_COMBAT_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_PER_MILITARY_POLICIES_COMBAT_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：根据已启用军事政策槽位数量提供战斗力加成
> **溯源**：单位能力 — ABILITY_GORGO_POLICY_SLOT_COMBAT_BONUS（`ABILITY_GORGO_POLICY_SLOT_COMBAT_BONUS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_NEIGHBOR_COMBAT_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_COMBAT_FOR_NUMBER_NEIGHBORS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `2` |

**效果**：根据相邻己方单位数量调整战斗力
> **溯源**：单位能力 — 安比奥里克斯（`ABILITY_AMBIORIX_NEIGHBOR_COMBAT_BONUS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_NO_REDUCTION_DAMAGE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_NO_REDUCTION_DAMAGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `NoReduction` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：移除单位受伤后的战斗力惩罚
> **溯源**：单位能力 — 武士（`ABILITY_SAMURAI`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 锁子甲（`PROMOTION_NIHANG_NO_WOUNDED_PENALTY`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_NUM_ATTACKS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_NUM_ATTACKS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`3` |

**效果**：调整单位每回合的攻击次数
> **溯源**：单位晋升 — 精英卫队（`PROMOTION_ELITE_GUARD`） — 赋予单位晋升效果
> **溯源**：单位能力 — ABILITY_EXPERT_MARKSMAN（`ABILITY_EXPERT_MARKSMAN`） — 赋予单位特殊能力（如果单位没有移动，每回合+1额外攻击。）
> **溯源**：单位晋升 — 神枪手（`PROMOTION_EXPERT_MARKSMAN`） — 赋予单位晋升效果（如果单位没有移动，每回合+1额外攻击。）
> **溯源**：单位晋升 — 突破（`PROMOTION_BREAKTHROUGH`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 狼群战术（`PROMOTION_WOLFPACK`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_PER_LUXURY_ATTACK_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_PER_LUXURY_ATTACK_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_PER_LUXURY_ATTACK_MODIFIER` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：根据拥有奢侈品数量提供战斗力加成
> **溯源**：单位能力 — ABILITY_MONTEZUMA_COMBAT_BONUS_PER_LUXURY（`ABILITY_MONTEZUMA_COMBAT_BONUS_PER_LUXURY`） — 赋予单位特殊能力（奢侈品提供+{1_Amount} [ICON_Strength] 战斗力。（蒙特祖玛））

---

### EFFECT_ADJUST_UNIT_PER_UNUSED_MOVEMENT_COMBAT_BONUS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_COMBAT_FOR_UNUSED_MOVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `3` |

**效果**：根据未使用移动力提供战斗力加成
> **溯源**：单位能力 — 向前冲（`ABILITY_CAROLEAN`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_POST_COMBAT_YIELD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_POST_COMBAT_YIELD` | `COLLECTION_UNIT_COMBAT` |
| `MODIFIER_PLAYER_UNITS_ADJUST_POST_COMBAT_YIELD` | `COLLECTION_PLAYER_COMBAT` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `OnlyWhenDefeatedEarlierEraUnit` | 是 | `1`（`1`=是 / `0`=否） |
| `PercentDefeatedStrength` | 是 | `100`、`150`、`50` |
| `YieldType` | 是 | `YIELD_CULTURE`、`YIELD_FAITH`、`YIELD_GOLD`、`YIELD_SCIENCE` |

**效果**：战斗胜利后获得指定产出
> **溯源**：单位能力 — 泰迪的莽骑兵（`ABILITY_ROUGH_RIDER`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 登船（`PROMOTION_BOARDING`） — 赋予单位晋升效果
> **溯源**：单位能力 — 赠金者（`ABILITY_MANDEKALU`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_LEVIED_HARALD（`ABILITY_LEVIED_HARALD`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 三叉戟（`PROMOTION_NIHANG_FAITH_FOR_VICTORIES`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_PROPERTY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_PROPERTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-5`、`1`、`2`、`20`、`3`、`4` ... (共 10 种值) |
| `Key` | 是 | 自定义属性标识（由MOD定义） |

**效果**：调整单位自定义属性值（Key参数决定具体属性）
> **溯源**：单位能力 — ABILITY_SHAMARE_UU_GRANT（`ABILITY_SHAMARE_UU_GRANT`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_RAIDING

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_RAIDING` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Bonus` | 是 | `50` |
| `CanRaid` | 是 | `1` |

**效果**：赋予单位海岸劫掠能力及劫掠产出加成
> **溯源**：单位能力 — 海岸扫荡（`ABILITY_COASTAL_RAID`） — 赋予单位特殊能力
> **溯源**：单位能力 — 雷霆海岸扫荡（`ABILITY_MELEE_COASTAL_RAID`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 掠夺（`PROMOTION_LOOT`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_RELIC_UPON_DEATH

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_RELIC_UPON_DEATH` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `RelicSource` | 是 | `RELIC_SOURCE_RELIGIOUS_UNIT` |

**效果**：宗教单位死亡时产生遗物
> **溯源**：单位能力 — ABILITY_MARTYR（`ABILITY_MARTYR`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 殉道者（`PROMOTION_MARTYR`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_STRENGTH_FROM_CITY_CULTURAL_IDENTITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_STRENGTH_FROM_CITY_CULTURAL_IDENTITY` | `COLLECTION_PLAYER_COMBAT` |

| *(无参数)* | | |
|---|---|---|

**效果**：根据城市文化身份调整单位战斗力
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_STRENGTH_REDUCTION_FOR_DAMAGE_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_STRENGTH_REDUCTION_FOR_DAMAGE_MODIFIER` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `50` |

**效果**：调整受伤单位的战斗力削减幅度
> **溯源**：政策 — 国家认同（`POLICY_NATIONAL_IDENTITY`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_SUPPORT_BONUS_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SUPPORT_BONUS_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Percent` | 是 | `100`、`50` |

**效果**：调整单位的支援加成倍率
> **溯源**：单位晋升 — 方阵（`PROMOTION_SQUARE`） — 赋予单位晋升效果
> **溯源**：单位能力 — ABILITY_HYPASPIST（`ABILITY_HYPASPIST`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 米格鲁（`PROMOTION_RESERVE_OPERATOR_TEAM_A1_R2`） — 赋予单位晋升效果
> **溯源**：单位能力 — ABILITY_SALADIN_FLANKING_UNITS（`ABILITY_SALADIN_FLANKING_UNITS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_WATER_DAMAGE_PROTECTION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_WATER_DAMAGE_RESISTANCE` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：保护单位免受水灾伤害
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_WMD_PROTECTION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_WMD_RESISTANCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Blast` | 是 | `50` |
| `Fallout` | 是 | `100` |

**效果**：保护单位免受核武器伤害及辐射影响
> **溯源**：单位能力 — ABILITY_UNIT_WMD_RESISTANCE（`ABILITY_UNIT_WMD_RESISTANCE`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNITS_RELIGIOUS_STRENGTH_BY_RELIGION_TYPE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_MAJOR_PLAYERS_ADJUST_UNITS_RELIGIOUS_STRENGTH_BY_RELIGION_TYPE` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `10` |

**效果**：根据宗教类型调整宗教单位的宗教战斗力
> **溯源**：世界议会决议 — "世界宗教"（`WC_RES_WORLD_RELIGION`） — 世界议会议案效果

---

### EFFECT_GRANT_STRENGTH_PER_ADJACENT_UNIT_TYPE

| ModifierType | CollectionType |
|---|---|
| `GRANT_STRENGTH_PER_ADJACENT_UNIT_TYPE` | `COLLECTION_UNIT_COMBAT` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `2` |
| `UnitType` | 是 | `UNIT_COLOMBIAN_LLANERO` |

**效果**：根据相邻指定单位类型数量提供战斗力加成
> **溯源**：单位能力 — ABILITY_LLANERO_ADJACENCY_STRENGTH（`ABILITY_LLANERO_ADJACENCY_STRENGTH`） — 赋予单位特殊能力（相邻的牛仔骑兵提供+{CalculatedAmount} [ICON_Strength] 战斗力。）

---

## 移动力

### EFFECT_ADJUST_PLAYER_EMBARKED_UNIT_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_EMBARKED_MOVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2` |

**效果**：调整所有登船单位的移动力
> **溯源**：建筑 — 大灯塔（`BUILDING_GREAT_LIGHTHOUSE`）
> **溯源**：科技 — 横帆装置（`TECH_SQUARE_RIGGING`）
> **溯源**：科技 — 蒸汽动力（`TECH_STEAM_POWER`）
> **溯源**：科技 — 内燃机（`TECH_COMBUSTION`）
> **溯源**：纪念活动 — COMMEMORATION_EXPLORATION（`COMMEMORATION_EXPLORATION`）

---

### EFFECT_ADJUST_PLAYER_EMBARK_UNIT_PASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_EMBARK_UNIT_PASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitType` | 是 | `UNIT_TRADER` |

**效果**：允许指定单位类型登船通行
> **溯源**：文明/领袖特性 — 印度之家（`TRAIT_CIVILIZATION_PORTUGAL`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_ATTACK_AND_MOVE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ATTACK_AND_MOVE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanMove` | 是 | `1`、`True`（`1`=是 / `0`=否） |

**效果**：允许单位攻击后再移动
> **溯源**：单位能力 — 静静的顿河（`ABILITY_COSSACK`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 游击队（`PROMOTION_GUERRILLA`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 精英卫队（`PROMOTION_ELITE_GUARD`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 突破（`PROMOTION_BREAKTHROUGH`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 风舞拳（`PROMOTION_MONK_SWEEPING_WIND`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_CLEAR_TERRAIN_START_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_CLEAR_TERRAIN_START_MOVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2` |

**效果**：若回合开始时位于开阔地形，增加移动力
> **溯源**：单位能力 — 重型战车（`ABILITY_HEAVY_CHARIOT`） — 赋予单位特殊能力（初始处于开阔地貌时+1 [ICON_Movement] 移动力。）
> **溯源**：单位能力 — 轻战车（`ABILITY_LIGHT_CHARIOT`） — 赋予单位特殊能力（初始处于开阔地貌时+2 [ICON_Movement] 移动力。）

---

### EFFECT_ADJUST_UNIT_ENTER_FOREIGN_LANDS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ENTER_FOREIGN_LANDS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Enter` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许单位进入外国领土（无视封闭边界）
> **溯源**：单位能力 — 进入外国领土。（`ABILITY_ARCHAEOLOGIST_ENTER_FOREIGN_LANDS`） — 赋予单位特殊能力
> **溯源**：单位能力 — 忽略边界（`ABILITY_RELIGIOUS_ENTER_FOREIGN_LANDS`） — 赋予单位特殊能力
> **溯源**：单位能力 — 进入外国领土（`ABILITY_ROCK_BAND_ENTER_FOREIGN_LANDS`） — 赋予单位特殊能力
> **溯源**：伟人 — 周达观（`GREAT_PERSON_INDIVIDUAL_ZHOU_DAGUAN`）（此伟人将无视封闭的边界。）
> **溯源**：伟人 — 马休·佩里（`GREAT_PERSON_INDIVIDUAL_MATTHEW_PERRY`）（此伟人将无视封闭的边界。）

---

### EFFECT_ADJUST_UNIT_ENEMY_TERRITORY_START_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_ENEMY_TERRITORY_START_MOVEMENT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：若回合开始时位于敌方领土，增加移动力
> **溯源**：政策 — 综合攻击后勤保障（`POLICY_FUTURE_VICTORY_DOMINATION`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_ESCAPE_BOOST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ESCAPE_BOOST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `4` |

**效果**：增加间谍逃脱时的移动力
> **溯源**：单位晋升 — 王牌驾驶员（`PROMOTION_SPY_ACE_DRIVER`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ESCORT_MOBILITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_ESCORT_MOBILITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `EscortMobility` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位护卫其他单位的机动能力
> **溯源**：单位能力 — ABILITY_JONG（`ABILITY_JONG`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_MONGOLIAN_KESHIG（`ABILITY_MONGOLIAN_KESHIG`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 护卫队机动性（`PROMOTION_ESCORT_MOBILITY`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_FRIENDLY_TERRITORY_START_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_FRIENDLY_TERRITORY_START_MOVEMENT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：若回合开始时位于友方领土，增加移动力
> **溯源**：政策 — 后勤（`POLICY_LOGISTICS`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_IGNORE_RIVERS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_IGNORE_RIVERS` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_RIVERS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：单位移动时忽略河流消耗
> **溯源**：单位能力 — 忽略穿越河流的消耗（`ABILITY_IGNORE_CROSSING_RIVERS_COST`） — 赋予单位特殊能力（穿越河流忽略移动力消耗。）
> **溯源**：单位能力 — 空中漫步（`ABILITY_RELIGIOUS_IGNORE_TERRAIN_COST`） — 赋予单位特殊能力（穿越河流忽略移动力消耗。）
> **溯源**：单位晋升 — 水陆两栖（`PROMOTION_AMPHIBIOUS`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_IGNORE_SHORES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_SHORES` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_IGNORE_SHORES` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：单位登船/下船时忽略移动力消耗
> **溯源**：单位能力 — 全球性军队（`ABILITY_REDCOAT`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_KNARR_IGNORE_EMBARK_DISEMBARK_COST（`ABILITY_KNARR_IGNORE_EMBARK_DISEMBARK_COST`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 水陆两栖（`PROMOTION_AMPHIBIOUS`） — 赋予单位晋升效果
> **溯源**：单位能力 — 地中海殖民地（`ABILITY_MEDITERRANEAN_COLONIES`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_IGNORE_TERRAIN_COST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_TERRAIN_COST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Ignore` | 是 | `1`、`true`（`1`=是 / `0`=否） |
| `Type` | 是 | `ALL`、`FEATURE_JUNGLE`、`FEATURE_MARSH`、`FOREST`、`HILLS` |

**效果**：单位移动时忽略地形/地貌的移动力消耗
> **溯源**：单位能力 — 忽略地形消耗（`ABILITY_IGNORE_TERRAIN_COST`） — 赋予单位特殊能力（所有地形消耗1个 [ICON_Movement] 移动力。）
> **溯源**：单位能力 — 空中漫步（`ABILITY_RELIGIOUS_IGNORE_TERRAIN_COST`） — 赋予单位特殊能力（所有地形消耗1个 [ICON_Movement] 移动力。）
> **溯源**：单位能力 — 高原训练（`ABILITY_ALTITUDE_TRAINING`） — 赋予单位特殊能力
> **溯源**：单位能力 — 森林斗士（`ABILITY_NAGAO`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 游骑兵（`PROMOTION_RANGER`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_JUMP_ABILITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_JUMP_DISTANCE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Range` | 是 | `4`、`5`、`6` |

**效果**：赋予/调整单位的跳跃（空降/传送）距离
> **溯源**：单位晋升 — 增强机动（`PROMOTION_GDR_BONUS_MOVEMENT`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_MOVEMENT` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_UNITS_ADJUST_MOVEMENT` | `COLLECTION_EMERGENCY_UNITS` |
| `MODIFIER_ALLIANCE_UNIT_MOVEMENT` | `COLLECTION_ALLIANCE_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-1`、`-2`、`-4`、`-8`、`1`、`2` |

**效果**：调整单位的移动力（绝对值）
> **溯源**：纪念活动 — COMMEMORATION_INFRASTRUCTURE（`COMMEMORATION_INFRASTRUCTURE`）
> **溯源**：纪念活动 — COMMEMORATION_RELIGIOUS（`COMMEMORATION_RELIGIOUS`）
> **溯源**：政策 — 私掠许可证（`POLICY_LETTERS_OF_MARQUE`） — 通过政策卡提供加成
> **溯源**：单位能力 — ABILITY_GRANT_MOVEMENT_BONUS（`ABILITY_GRANT_MOVEMENT_BONUS`） — 赋予单位特殊能力
> **溯源**：单位晋升 — "和谐"（`PROMOTION_SPECIAL_POPUKAR_R2`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_MOVE_AND_ATTACK

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_MOVE_AND_ATTACK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanAttack` | 是 | `0`、`1`（`1`=是 / `0`=否） |

**效果**：控制单位是否能在移动后攻击
> **溯源**：单位能力 — 无法移动射击（`ABILITY_NO_MOVE_AND_SHOOT`） — 赋予单位特殊能力（无法在移动后进行攻击。）
> **溯源**：单位晋升 — 专家组（`PROMOTION_EXPERT_CREW`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_PARADROP_ABILITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_PARADROP_ABILITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanDrop` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予/移除单位的伞降能力
> **溯源**：单位能力 — ABILITY_PARADROP（`ABILITY_PARADROP`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_PROMOTE_NO_FINISH_MOVES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_PROMOTE_NO_FINISH_MOVES` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `NoFinishMoves` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：单位晋升后不结束回合（仍可移动/攻击）
> **溯源**：文明/领袖特性 — 爱国军（`TRAIT_CIVILIZATION_EJERCITO_PATRIOTA`） — 文明或领袖特性效果


---

### EFFECT_ADJUST_UNIT_SEA_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_CITY_TRAINED_UNITS_ADJUST_MOVEMENT` | `COLLECTION_CITY_TRAINED_UNITS` |
| `MODIFIER_PLAYER_UNITS_ADJUST_SEA_MOVEMENT` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_SEA_MOVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2` |

**效果**：调整单位的海洋移动力
> **溯源**：科技 — 数学（`TECH_MATHEMATICS`）
> **溯源**：纪念活动 — COMMEMORATION_EXPLORATION（`COMMEMORATION_EXPLORATION`）
> **溯源**：单位能力 — 长船移动力（`ABILITY_LONGSHIP_MOVEMENT`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_ROYAL_NAVY_DOCKYARD_MOVEMENT_BONUS（`ABILITY_ROYAL_NAVY_DOCKYARD_MOVEMENT_BONUS`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_GREAT_LIGHTHOUSE_MOVEMENT（`ABILITY_GREAT_LIGHTHOUSE_MOVEMENT`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_TRADE_ROUTE_PLUNDER_IMMUNITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TRADE_ROUTE_PLUNDER_IMMUNITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DomainType` | 是 | `DOMAIN_LAND`、`DOMAIN_SEA` |

**效果**：赋予贸易路线单位免于被掠夺的免疫能力
> **溯源**：单位能力 — 海上掠夺豁免（`ABILITY_TRADE_ROUTE_PLUNDER_IMMUNITY_SEA`） — 赋予单位特殊能力
> **溯源**：单位能力 — 经济黄金时代（`ABILITY_ECONOMIC_GOLDEN_AGE_PLUNDER_IMMUNITY`） — 赋予单位特殊能力
> **溯源**：单位能力 — 双层桨座战船商人保护（`ABILITY_TRADER_PROTECTED_BY_BIREME`） — 赋予单位特殊能力
> **溯源**：单位能力 — 曼德卡鲁骑兵商人保护（`ABILITY_TRADER_PROTECTED_BY_MANDEKALU`） — 赋予单位特殊能力

---

### EFFECT_RESTORE_UNIT_MOVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_RESET_MOVES` | `COLLECTION_PLAYER_UNITS` |

| *(无参数)* | | |
|---|---|---|

**效果**：恢复单位的全部移动力
> **溯源**：伟人能力 — 拉斐尔·乌达内塔（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_URDANETA`）（2单元格内的所有陆地战斗单位重新获得全额 [ICON_Movement] 移动力和攻击力。）

---

## 经验/等级

### EFFECT_ADJUST_CITY_UNIT_MAX_LEVEL

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_MAX_LEVEL` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_CITY_UNIT_MAX_LEVEL` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：提升城市训练单位的最大等级上限
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_ATTACK_EXPERIENCE_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_UNIT_ATTACK_EXPERIENCE_MODIFIER` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100` |

**效果**：调整单位攻击获得的经验倍率
> **溯源**：城邦 — 喀布尔（`MINOR_CIV_KABUL`） — 城邦宗主国加成

---

### EFFECT_ADJUST_UNIT_EXPERIENCE_LEVEL

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_EXPERIENCE_LEVEL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `2` |

**效果**：直接提升单位的经验等级
> **溯源**：单位能力 — ABILITY_UNIT_AUTO_VETERANCY（`ABILITY_UNIT_AUTO_VETERANCY`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_EXPERIENCE_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_UNIT_EXPERIENCE_MODIFIER` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_UNIT_EXPERIENCE_MODIFIER` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_CITY_TRAINED_UNITS_ADJUST_XP_BONUS` | `COLLECTION_CITY_TRAINED_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-100`、`0`、`10`、`100`、`200`、`25` ... (共 9 种值) |

**效果**：调整单位获取经验的倍率
> **溯源**：单位能力 — 军官（`ABILITY_MUSTANG`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_BARRACKS_TRAINED_UNIT_XP（`ABILITY_BARRACKS_TRAINED_UNIT_XP`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_STABLE_TRAINED_UNIT_XP（`ABILITY_STABLE_TRAINED_UNIT_XP`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_ARMORY_TRAINED_UNIT_XP（`ABILITY_ARMORY_TRAINED_UNIT_XP`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_MILITARY_ACADEMY_TRAINED_UNIT_XP（`ABILITY_MILITARY_ACADEMY_TRAINED_UNIT_XP`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_GRANT_EXPERIENCE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALLIANCE_TRAINED_UNITS_FREE_UPGRADE` | `COLLECTION_ALLIANCE_TRAINED_UNITS` |
| `MODIFIER_CITY_TRAINED_UNITS_ADJUST_GRANT_EXPERIENCE` | `COLLECTION_CITY_TRAINED_UNITS` |
| `MODIFIER_UNITS_ADJUST_GRANT_EXPERIENCE` | `COLLECTION_ALL_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_GRANT_EXPERIENCE` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_GRANT_EXPERIENCE` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-1`、`20` |

**效果**：赠予单位指定数量的经验值
> **溯源**：总督晋升 — 射击孔（`GOVERNOR_PROMOTION_EMBRASURE`） — 赋予总督晋升能力
> **溯源**：伟人能力 — 阿尔特米西亚（`GREAT_PERSON_INDIVIDUAL_ARTEMISIA`）（为军事海军单位赠予1次强化等级。）
> **溯源**：伟人能力 — 拉斯喀瑞尼亚·鲍勃里斯（`GREAT_PERSON_INDIVIDUAL_LASKARINA_BOUBOULINA`）
> **溯源**：伟人能力 — 谢尔盖·戈尔什科夫（`GREAT_PERSON_INDIVIDUAL_SERGEY_GORSHKOV`）
> **溯源**：伟人能力 — 克兰西·费尔南多（`GREAT_PERSON_INDIVIDUAL_CLANCY_FERNANDO`）

---

### EFFECT_ADJUST_UNIT_NO_BARB_XP_LIMIT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_UNIT_NO_BARB_XP_LIMIT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `NoLimit` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：移除单位从蛮族获得的经验上限
> **溯源**：文明/领袖特性 — 我来，我见，我征服（`TRAIT_LEADER_CAESAR`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_UPGRADE_GOODY_HUT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_UPGRADE_GOODY_HUT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：允许单位从部落村庄中升级
> **溯源**：部落村庄 — 军事升级（`GOODYHUT_GRANT_UPGRADE`） — 部落村庄奖励效果

---

## 回血/治疗

### EFFECT_ADJUST_RANDOM_EVENT_NO_UNIT_DAMAGE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_RANDOM_EVENT_NO_UNIT_DAMAGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `NoDamage` | 是 | `1`（`1`=是 / `0`=否） |
| `RandomEventType` | 是 | `RANDOM_EVENT_BLIZZARD_CRIPPLING`、`RANDOM_EVENT_BLIZZARD_SIGNIFICANT`、`RANDOM_EVENT_DROUGHT_EXTREME`、`RANDOM_EVENT_DROUGHT_MAJOR`、`RANDOM_EVENT_DUST_STORM_GRADIENT`、`RANDOM_EVENT_DUST_STORM_HABOOB` ... (共 27 种值) |

**效果**：保护单位免受指定随机环境事件的伤害
> **溯源**：文明/领袖特性 — 俄罗斯母亲（`TRAIT_CIVILIZATION_MOTHER_RUSSIA`） — 文明或领袖特性效果
> **溯源**：文明/领袖特性 — 神风（`TRAIT_LEADER_DIVINE_WIND`） — 文明或领袖特性效果
> **溯源**：文明/领袖特性 — 平安祈愿（`TRAIT_LEADER_GU_NINGNING`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_HEAL

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100` |

**效果**：直接治疗单位指定血量
> **溯源**：部落村庄 — 军事治疗（`GOODYHUT_HEAL`） — 部落村庄奖励效果

---

### EFFECT_ADJUST_UNIT_HEALING_MODIFIERS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_UNITS_ADJUST_HEALING` | `COLLECTION_EMERGENCY_UNITS` |
| `MODIFIER_ALL_UNITS_ADJUST_HEAL_PER_TURN` | `COLLECTION_ALL_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_PER_TURN` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_HEAL_PER_TURN` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `10`、`100`、`20`、`30`、`5`、`50` |
| `Type` | 是 | `ALL`、`ENEMY`、`FRIENDLY`、`NEUTRAL` |

**效果**：调整单位每回合的生命值回复量
> **溯源**：单位能力 — 中立地区恢复（`ABILITY_HEAL_NEUTRAL_TERRITORY`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 辅助船（`PROMOTION_AUXILIARY_SHIPS`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 船舰补给（`PROMOTION_SUPPLY_FLEET`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 超级航空母舰（`PROMOTION_SUPER_CARRIER`） — 赋予单位晋升效果
> **溯源**：单位能力 — 桃大将军的鼓舞（`ABILITY_UNIT_PEACH_MYRTLE_COMBAT_AND_MOVE`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_HEALING_RELIGION_MODIFIERS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_RELIGION_PER_TURN` | `COLLECTION_OWNER` |
| `MODIFIER_ALL_UNITS_ADJUST_HEAL_RELIGION_PER_TURN` | `COLLECTION_ALL_UNITS` |
| `MODIFIER_PLAYER_UNITS_ADJUST_HEAL_RELIGION_PER_TURN` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `10` |
| `Type` | 是 | `ALL` |

**效果**：调整宗教单位在特定宗教领土中的回复量
> **溯源**：万神/信条 — "圣水"（`BELIEF_HOLY_WATERS`） — 宗教单位在己方圣水领土中回血量增加

---

### EFFECT_ADJUST_UNIT_POST_COMBAT_HEAL

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_FROM_COMBAT` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_HEAL_FROM_COMBAT` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `20`、`30` |

**效果**：单位战斗后回复指定血量
> **溯源**：单位能力 — ABILITY_TOMYRIS_HEAL_AFTER_DEFEATING_UNIT（`ABILITY_TOMYRIS_HEAL_AFTER_DEFEATING_UNIT`） — 赋予单位特殊能力
> **溯源**：建筑 — 作战部（`BUILDING_GOV_MILITARY`）

---

## 生产/购买

### EFFECT_ADJUST_ALL_UNITS_PURCHASE_COST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_ALL_UNITS_PURCHASE_COST` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_UNITS_PURCHASE_COST` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-100`、`20`、`30` |
| `IncludeCivilian` | 是 | `0`、`1`（`1`=是 / `0`=否） |
| `UnitDomain` | 是 | `DOMAIN_ALL`、`DOMAIN_LAND` |

**效果**：调整所有单位的购买费用
> **溯源**：区域 — 曼丁哥市场（`DISTRICT_SUGUBA`）
> **溯源**：政策 — 权力归花儿（`POLICY_FLOWER_POWER`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_ALL_UNIT_PRODUCTION_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION_MODIFIER` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_UNIT_PRODUCTION_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-100`、`-30`、`15` |

**效果**：调整所有单位的生产力产出倍率
> **溯源**：建筑 — 基尔瓦基斯瓦尼（`BUILDING_KILWA_KISIWANI`）
> **溯源**：政策 — 权力归花儿（`POLICY_FLOWER_POWER`） — 通过政策卡提供加成
> **溯源**：文明/领袖特性 — 杰利之歌（`TRAIT_CIVILIZATION_MALI_GOLD_DESERT`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_CITY_ALL_MILITARY_UNITS_PRODUCTION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_MILITARY_UNITS_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_MILITARY_UNITS_PRODUCTION` | `COLLECTION_OWNER` |
| `MODIFIER_GOVERNOR_ADJUST_CITY_MILITARY_UNIT_PRODUCTION` | `COLLECTION_OWNER` |
| `MODIFIER_ALLIANCE_CITIES_MILITARY_UNIT_PRODUCTION` | `COLLECTION_ALLIANCE_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `15`、`20`、`200`、`25`、`5`、`50` |
| `EndEra` | 是 | `ERA_CLASSICAL` |
| `PromotionClass` | 是 | `PROMOTION_CLASS_NAVAL_RAIDER`、`PROMOTION_CLASS_NAVAL_RANGED` |
| `StartEra` | 是 | `ERA_ANCIENT` |

**效果**：调整城市军事单位的生产力产出倍率
> **溯源**：伟人能力 — 德怀特·艾森豪威尔（`GREAT_PERSON_INDIVIDUAL_DWIGHT_EISENHOWER`）（为军事单位+5% [ICON_Production] 生产力。）
> **溯源**：文明/领袖特性 — MINOR_CIV_DEFAULT_TRAIT（`MINOR_CIV_DEFAULT_TRAIT`）
> **溯源**：纪念活动 — COMMEMORATION_MILITARY（`COMMEMORATION_MILITARY`）
> **溯源**：伟人能力 — 切斯特·尼米兹（`GREAT_PERSON_INDIVIDUAL_CHESTER_NIMITZ`）
> **溯源**：伟人能力 — 特米斯托克力（`GREAT_PERSON_INDIVIDUAL_THEMISTOCLES`）

---

### EFFECT_ADJUST_CITY_POPULATION_UNIT_CREATED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_CHANGE_POPULATION_CREATE_UNIT` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-1` |
| `UnitType` | 是 | `UNIT_SULEIMAN_JANISSARY` |

**效果**：训练指定单位时消耗城市人口
> **溯源**：文明/领袖特性 — TRAIT_LEADER_UNIT_SULEIMAN_JANISSARY（`TRAIT_LEADER_UNIT_SULEIMAN_JANISSARY`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_CITY_PRODUCTION_UNIT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CAPITAL_CITY_ADJUST_UNIT_PRODUCTION` | `COLLECTION_PLAYER_CAPITAL_CITY` |
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION_CHANGE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_PLAYER_DISTRICTS_ADJUST_UNIT_PRODUCTION` | `COLLECTION_PLAYER_DISTRICTS` |
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION_CHANGE_ETHIOPIA` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2`、`3` |

**效果**：调整城市特定条件下的单位生产力基础产出
> **溯源**：城邦 — 军事城邦（`MINOR_CIV_MILITARISTIC`） — 城邦宗主国加成（首都/兵营/军营/军事学院等军事建筑提供）

---

### EFFECT_ADJUST_PLAYER_BAN_UNIT_PRODUCTION_YIELD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYERS_ADJUST_UNIT_BAN_PRODUCTION_YIELD` | `COLLECTION_MAJOR_PLAYERS` |

| *(无参数)* | | |
|---|---|---|

**效果**：禁止使用特定产出类型生产单位

---

### EFFECT_ADJUST_PLAYER_BLOCK_UNIT_ENTRY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_BLOCK_UNIT_ENTRY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitType` | 是 | `UNIT_ROCK_BAND` |

**效果**：阻止指定单位类型进入己方领土
> **溯源**：政策 — 音乐审查制度（`POLICY_MUSIC_CENSORSHIP`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_PLAYER_BUFF_UNIT_PRODUCTION_YIELD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYERS_ADJUST_UNIT_BUFF_PRODUCTION_YIELD` | `COLLECTION_MAJOR_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-100`、`50` |

**效果**：调整使用特定产出类型生产单位时的效率
> **溯源**：世界议会决议 — "雇佣兵公司"（`WC_RES_MERCENARY_COMPANIES`） — 世界议会议案效果

---

### EFFECT_ADJUST_PLAYER_LEVIED_UNIT_UPGRADE_DISCOUNT_PERCENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_LEVIED_UNIT_UPGRADE_DISCOUNT_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `75` |

**效果**：降低征召单位的升级费用百分比
> **溯源**：文明/领袖特性 — 渡鸦之王（`TRAIT_LEADER_RAVEN_KING`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_PLAYER_UNIT_BUILD_DISABLED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_BUILD_DISABLED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitType` | 是 | `UNIT_SETTLER` |

**效果**：禁止建造指定单位类型
> **溯源**：政策 — 孤立主义（`POLICY_ISOLATIONISM`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_PLAYER_UNIT_DISTRICT_PERCENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_UNIT_DISTRICT_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `20` |

**效果**：根据已建区域数量加速单位建造
> **溯源**：文明/领袖特性 — 五个太阳的传说（`TRAIT_CIVILIZATION_LEGEND_FIVE_SUNS`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_PLAYER_UNIT_PROJECT_PERCENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_UNIT_PROJECT_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `2` |

**效果**：根据已建项目数量加速单位建造
> **溯源**：建筑 — 皇家学会（`BUILDING_GOV_SCIENCE`）

---

### EFFECT_ADJUST_PLAYER_UNIT_UPGRADE_DISCOUNT_PERCENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_UNIT_UPGRADE_DISCOUNT_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100`、`50` |

**效果**：降低单位升级费用百分比
> **溯源**：文明/领袖特性 — MINOR_CIV_DEFAULT_TRAIT（`MINOR_CIV_DEFAULT_TRAIT`）
> **溯源**：政策 — 职业军队（`POLICY_PROFESSIONAL_ARMY`） — 通过政策卡提供加成
> **溯源**：政策 — 军队现代化（`POLICY_FORCE_MODERNIZATION`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_PLAYER_UNIT_UPGRADE_RESOURCE_COST_DISCOUNT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_UNIT_UPGRADE_RESOURCE_COST_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `50` |

**效果**：降低单位升级的战略资源费用
> **溯源**：政策 — 贴身随从（`POLICY_RETINUES`） — 通过政策卡提供加成
> **溯源**：政策 — 军队现代化（`POLICY_FORCE_MODERNIZATION`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_PLAYER_UNIT_WONDER_PERCENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_UNIT_WONDER_PERCENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `15` |

**效果**：根据奇观建造进度加速单位建造
> **溯源**：文明/领袖特性 — FIRST_EMPEROR_TRAIT（`FIRST_EMPEROR_TRAIT`）

---

### EFFECT_ADJUST_PLAYER_VALID_UNIT_BUILD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_VALID_UNIT_BUILD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitType` | 是 | `UNIT_LAHORE_NIHANG` |

**效果**：允许建造指定的特殊单位类型
> **溯源**：城邦 — 拉合尔（`MINOR_CIV_LAHORE`） — 城邦宗主国可建造尼杭战士

---

### EFFECT_ADJUST_UNIT_DOMAIN_PRODUCTION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_CITY_ADJUST_UNIT_DOMAIN_PRODUCTION` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `25`、`50` |
| `Domain` | 是 | `DOMAIN_SEA` |

**效果**：调整指定领域单位的生产力产出
> **溯源**：区域 — U型港（`DISTRICT_COTHON`）
> **溯源**：建筑 — 航海学校（`BUILDING_NAVIGATION_SCHOOL`）

---

### EFFECT_ADJUST_UNIT_MAINTENANCE_DISCOUNT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_UNIT_MAINTENANCE_DISCOUNT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-2`、`1`、`2`、`5` |

**效果**：降低单位的维护费用
> **溯源**：政策 — 征兵（`POLICY_CONSCRIPTION`） — 通过政策卡提供加成
> **溯源**：政策 — 全民动员（`POLICY_LEVEE_EN_MASSE`） — 通过政策卡提供加成
> **溯源**：政策 — 精兵政策（`POLICY_ELITE_FORCES`） — 通过政策卡提供加成
> **溯源**：文明/领袖特性 — 勤俭节约（`TRAIT_LEADER_SNOWSANT`） — 文明或领袖特性效果
> **溯源**：文明/领袖特性 — 北欧卫队（`TRAIT_LEADER_HARALD_ALT`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_UNIT_PRODUCTION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_ADJUST_UNIT_PRODUCTION` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_UNIT_PRODUCTION` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100`、`200`、`30`、`50` |
| `UnitType` | 是 | `UNIT_BUILDER`、`UNIT_GIANT_DEATH_ROBOT`、`UNIT_MILITARY_ENGINEER`、`UNIT_NIGHTMARE_SHADOW`、`UNIT_SETTLER`、`UNIT_SPY` |

**效果**：调整特定单位类型的生产力消耗倍率
> **溯源**：文明/领袖特性 — TRAIT_CIVILIZATION_INEXPENSIVE_BUILDERS（`TRAIT_CIVILIZATION_INEXPENSIVE_BUILDERS`） — 文明或领袖特性效果
> **溯源**：文明/领袖特性 — MINOR_CIV_DEFAULT_TRAIT（`MINOR_CIV_DEFAULT_TRAIT`）
> **溯源**：政策 — 殖民（`POLICY_COLONIZATION`） — 通过政策卡提供加成
> **溯源**：政策 — 征收（`POLICY_EXPROPRIATION`） — 通过政策卡提供加成
> **溯源**：政策 — 服役（`POLICY_ILKUM`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_PURCHASE_COST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_PURCHASE_COST` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_EMERGENCY_CITIES_ADJUST_UNIT_PURCHASE_COST` | `COLLECTION_EMERGENCY_CITIES` |
| `MODIFIER_SINGLE_CITY_ADJUST_UNIT_PURCHASE_COST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100`、`20`、`30`、`50` |
| `UnitType` | 是 | `UNIT_AIRCRAFT_CARRIER`、`UNIT_AMERICAN_P51`、`UNIT_AMERICAN_ROUGH_RIDER`、`UNIT_APOSTLE`、`UNIT_ARABIAN_MAMLUK`、`UNIT_ARCHER` ... (共 146 种值) |

**效果**：调整特定单位类型的购买费用
> **溯源**：纪念活动 — COMMEMORATION_INFRASTRUCTURE（`COMMEMORATION_INFRASTRUCTURE`）
> **溯源**：政策 — 权力归花儿（`POLICY_FLOWER_POWER`） — 通过政策卡提供加成
> **溯源**：建筑 — 米纳克希神庙（`BUILDING_MEENAKSHI_TEMPLE`）
> **溯源**：文明/领袖特性 — 连击，甜品与猫猫！（`TRAIT_LEADER_MOUSSE`） — 文明或领袖特性效果


---

### EFFECT_ADJUST_UNIT_TAG_ERA_PRODUCTION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_UNIT_TAG_ERA_PRODUCTION` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100`、`30`、`50` |
| `EraType` | 是 | `ERA_ANCIENT`、`ERA_ATOMIC`、`ERA_CLASSICAL`、`ERA_FUTURE`、`ERA_INDUSTRIAL`、`ERA_INFORMATION` ... (共 10 种值) |
| `UnitPromotionClass` | 是 | `PROMOTION_CLASS_AIR_BOMBER`、`PROMOTION_CLASS_AIR_FIGHTER`、`PROMOTION_CLASS_ANTI_CAVALRY`、`PROMOTION_CLASS_HEAVY_CAVALRY`、`PROMOTION_CLASS_LIGHT_CAVALRY`、`PROMOTION_CLASS_MELEE` ... (共 13 种值) |

**效果**：调整指定时代/晋升类别单位的生产力消耗倍率
> **溯源**：文明/领袖特性 — TRAIT_LEADER_MELEE_COASTAL_RAIDS（`TRAIT_LEADER_MELEE_COASTAL_RAIDS`） — 文明或领袖特性效果
> **溯源**：政策 — 斯巴达教育（`POLICY_AGOGE`） — 通过政策卡提供加成
> **溯源**：政策 — 封建契约（`POLICY_FEUDAL_CONTRACT`） — 通过政策卡提供加成
> **溯源**：政策 — 大军团（`POLICY_GRANDE_ARMEE`） — 通过政策卡提供加成
> **溯源**：政策 — 先军政策（`POLICY_MILITARY_FIRST`） — 通过政策卡提供加成

---

### EFFECT_ENABLE_UNIT_FAITH_PURCHASE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ENABLE_UNIT_FAITH_PURCHASE` | `COLLECTION_PLAYER_CITIES` |
| `MODIFIER_CITY_ENABLE_UNIT_FAITH_PURCHASE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Tag` | 是 | `CLASS_AIR_FIGHTER`、`CLASS_ANTI_CAVALRY`、`CLASS_ARCHAEOLOGIST`、`CLASS_GIANT_DEATH_ROBOT`、`CLASS_HEAVY_CAVALRY`、`CLASS_HEAVY_CHARIOT` ... (共 20 种值) |

**效果**：允许使用信仰购买指定类别的单位
> **溯源**：文明/领袖特性 — 三界的崇高女神（`TRAIT_LEADER_EXALTED_GODDESS`） — 文明或领袖特性效果
> **溯源**：建筑 — 骑士团长礼拜堂（`BUILDING_GOV_FAITH`）

---

### EFFECT_GRANT_CITY_YIELD_PERCENT_UNIT_CREATED_COST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_CITY_GRANT_YIELD_PER_UNIT_COST` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_CITIES_GRANT_YIELD_PER_UNIT_COST` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitProductionPercent` | 是 | `20`、`25` |
| `YieldType` | 是 | `YIELD_CULTURE`、`YIELD_SCIENCE` |

**效果**：训练单位时按生产力消耗百分比获得额外产出
> **溯源**：建筑 — 皇家学堂（`BUILDING_BASILIKOI_PAIDES`）
> **溯源**：文明/领袖特性 — 厄勃隆尼斯之王（`TRAIT_LEADER_AMBIORIX`） — 文明或领袖特性效果

---

### EFFECT_GRANT_PLAYER_YIELD_PERCENT_UNIT_COST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_YIELD_PERCENT_UNIT_COST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitCostPercent` | 是 | `50` |
| `YieldType` | 是 | `YIELD_GOLD` |

**效果**：训练单位时按消耗百分比返还指定产出
> **溯源**：伟人能力 — 格雷格尔·麦克格雷格尔（`GREAT_PERSON_INDIVIDUAL_COMMANDANTE_MACGREGOR`）

---

## 间谍

### EFFECT_ADJUST_UNIT_BOOST_ALL_SPIES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_BOOST_ALL_SPIES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |
| `Defense` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：提升所有间谍的有效等级
> **溯源**：单位晋升 — 军需官（`PROMOTION_SPY_QUARTERMASTER`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 测谎仪（`PROMOTION_SPY_POLYGRAPH`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_SPY_COUNTERSPY_ADJACENT_LEVEL_BOOST

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_SPY_COUNTERSPY_ADJACENT_LEVEL_BOOST` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：反间谍时提升相邻单元格友方间谍的等级
> **溯源**：单位晋升 — 监视（`PROMOTION_SPY_SURVEILLANCE`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_SPY_COUNTERSPY_ENTIRE_CITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_SPY_COUNTERSPY_ENTIRE_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `EntireCity` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：反间谍时保护整个城市的所有区域
> **溯源**：单位晋升 — 监视（`PROMOTION_SPY_SURVEILLANCE`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_SPY_ESTABLISH_TIME

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SPY_ESTABLISH_TIME` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_SPY_ESTABLISH_TIME` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `ReductionPercent` | 是 | `100` |

**效果**：减少间谍在目标城市建立据点的回合数
> **溯源**：单位晋升 — 掩饰（`PROMOTION_SPY_DISGUISE`） — 赋予单位晋升效果
> **溯源**：纪念活动 — COMMEMORATION_ESPIONAGE（`COMMEMORATION_ESPIONAGE`）

---

### EFFECT_ADJUST_UNIT_SPY_OFFENSIVE_OPERATION_TIME

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_SPY_OFFENSIVE_OPERATION_TIME` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `ReductionPercent` | 是 | `25` |

**效果**：减少间谍进攻性行动所需回合数
> **溯源**：纪念活动 — COMMEMORATION_ESPIONAGE（`COMMEMORATION_ESPIONAGE`）
> **溯源**：政策 — 权术主义（`POLICY_MACHIAVELLIANISM`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_SPY_OPERATION_CHANCE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SPY_OPERATION_CHANCE` | `COLLECTION_OWNER` |
| `MODIFIER_EMERGENCY_UNITS_ADJUST_SPYING_EFFICIENCY` | `COLLECTION_EMERGENCY_UNITS` |
| `MODIFIER_ALL_UNITS_ADJUST_SPYING_EFFICIENCY` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-10`、`2` |
| `Offensive` | 是 | `0`、`1`（`1`=是 / `0`=否） |
| `OperationType` | 是 | `UNITOPERATION_SPY_BREACH_DAM`、`UNITOPERATION_SPY_DISRUPT_ROCKETRY`、`UNITOPERATION_SPY_FABRICATE_SCANDAL`、`UNITOPERATION_SPY_FOMENT_UNREST`、`UNITOPERATION_SPY_GREAT_WORK_HEIST`、`UNITOPERATION_SPY_NEUTRALIZE_GOVERNOR` ... (共 10 种值) |

**效果**：调整间谍行动的成功率
> **溯源**：单位晋升 — 技术专家（`PROMOTION_SPY_TECHNOLOGIST`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 飞贼（`PROMOTION_SPY_CAT_BURGLAR`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 爆破兵（`PROMOTION_SPY_DEMOLITIONS`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 骗子（`PROMOTION_SPY_CON_ARTIST`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 游击队领袖（`PROMOTION_SPY_GUERILLA_LEADER`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_SPY_OPERATION_TIME

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SPY_OPERATION_TIME` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_SPY_OPERATION_TIME` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `OperationType` | 是 | `UNITOPERATION_SPY_DISRUPT_ROCKETRY`、`UNITOPERATION_SPY_GAIN_SOURCES`、`UNITOPERATION_SPY_GREAT_WORK_HEIST`、`UNITOPERATION_SPY_RECRUIT_PARTISANS`、`UNITOPERATION_SPY_SABOTAGE_PRODUCTION`、`UNITOPERATION_SPY_SIPHON_FUNDS` |
| `ReductionPercent` | 是 | `25` |

**效果**：减少特定间谍行动类型所需回合数
> **溯源**：单位晋升 — 语言学家（`PROMOTION_SPY_LINGUIST`） — 赋予单位晋升效果

---

## 宗教传播

### EFFECT_ADD_RELIGIOUS_UNIT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_RELIGION_ADD_RELIGIOUS_UNIT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitType` | 是 | `UNIT_WARRIOR_MONK` |

**效果**：解锁可购买的宗教单位类型
> **溯源**：信条 — 武僧（`BELIEF_WARRIOR_MONKS`）

---

### EFFECT_ADJUST_UNIT_FOREIGN_SPREAD_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_FOREIGN_SPREAD_MODIFIER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `200` |

**效果**：调整宗教单位在外国领土的传播强度
> **溯源**：单位晋升 — 翻译员（`PROMOTION_TRANSLATOR`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_LAND_VICTORY_SPREAD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_LAND_VICTORY_SPREAD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `LandVictorySpread` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：陆地单位击杀敌方时自动传播己方宗教
> **溯源**：单位晋升 — 弟子（`PROMOTION_MONK_DISCIPLES`） — 赋予单位晋升效果
> **溯源**：单位能力 — 圣城之战（`ABILITY_BYZANTIUM_COMBAT_UNITS`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_NO_FOREIGN_SPREAD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_NO_FOREIGN_SPREAD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `NoSpread` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：禁止宗教单位在外国领土传教
> **溯源**：单位能力 — 国内传播（`ABILITY_NO_FOREIGN_SPREAD`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_SPREAD_CHARGES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SPREAD_CHARGES` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_SPREAD_CHARGES` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2` |

**效果**：调整宗教单位的传教次数
> **溯源**：单位晋升 — 演说者（`PROMOTION_ORATOR`） — 赋予单位晋升效果
> **溯源**：建筑 — 圣索菲亚大教堂（`BUILDING_HAGIA_SOPHIA`）
> **溯源**：文明/领袖特性 — 艾思科里亚（`TRAIT_LEADER_EL_ESCORIAL`） — 文明或领袖特性效果

---

## 掠夺/劫掠

### EFFECT_ADJUST_UNIT_FAITH_ON_DISTRICT_PLUNDER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_FAITH_ON_DISTRICT_PILLAGE` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `30` |

**效果**：掠夺区域时额外获得信仰
> **溯源**：建筑 — 骑士团长礼拜堂（`BUILDING_GOV_FAITH`）

---

### EFFECT_ADJUST_UNIT_FAITH_ON_IMPROVEMENT_PLUNDER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_FAITH_ON_IMPROVEMENT_PILLAGE` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `15` |

**效果**：掠夺改良设施时额外获得信仰
> **溯源**：建筑 — 骑士团长礼拜堂（`BUILDING_GOV_FAITH`）

---

### EFFECT_ADJUST_UNIT_PILLAGE_DISTRICT_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_DISTRICT_PILLAGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `50` |

**效果**：调整掠夺区域获得的产出倍率
> **溯源**：政策 — 扫荡（`POLICY_RAID`） — 通过政策卡提供加成
> **溯源**：政策 — 全面战争（`POLICY_TOTAL_WAR`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_PILLAGE_IMPROVEMENT_MODIFIER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_IMPROVEMENT_PILLAGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `50` |

**效果**：调整掠夺改良设施获得的产出倍率
> **溯源**：政策 — 扫荡（`POLICY_RAID`） — 通过政策卡提供加成
> **溯源**：政策 — 全面战争（`POLICY_TOTAL_WAR`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_PLUNDER_YIELDS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_PLUNDER_YIELDS` | `COLLECTION_PLAYER_UNITS` |
| `MODIFIER_PLAYER_UNIT_ADJUST_PLUNDER_YIELDS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100`、`40`、`50`、`60` |

**效果**：调整单位掠夺时获得的总产出倍率
> **溯源**：政策 — 全面战争（`POLICY_TOTAL_WAR`） — 通过政策卡提供加成
> **溯源**：政策 — 私掠许可证（`POLICY_LETTERS_OF_MARQUE`） — 通过政策卡提供加成
> **溯源**：单位能力 — ABILITY_RAJENDRA_CHOLA_PLUNDER_BONUS（`ABILITY_RAJENDRA_CHOLA_PLUNDER_BONUS`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_FRANCIS_DRAKE_PLUNDER_BONUS（`ABILITY_FRANCIS_DRAKE_PLUNDER_BONUS`） — 赋予单位特殊能力
> **溯源**：单位能力 — ABILITY_CHING_SHIH_PLUNDER_BONUS（`ABILITY_CHING_SHIH_PLUNDER_BONUS`） — 赋予单位特殊能力

---

## 旅游/摇滚乐队

### EFFECT_ADJUST_PLAYER_ROCK_BAND_UNIT_ALBUM_SALES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_EMERGENCY_PLAYERS_ADJUST_ROCK_BAND_UNIT_ALBUM_SALES` | `COLLECTION_EMERGENCY_PLAYERS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `25`、`50`、`75` |

**效果**：调整摇滚乐队演出后的专辑销售旅游业绩
> **溯源**：紧急情况 — 诺贝尔文学奖（`EMERGENCY_NOBEL_PRIZE_LITERATURE`） — 紧急情况奖励效果

---

### EFFECT_ADJUST_UNIT_POST_TOURISM_BOMB_LOYALTY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_SINGLE_UNIT_ADJUST_POST_TOURISM_BOMB_LOYALTY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-40` |

**效果**：摇滚乐队演出后降低目标城市的忠诚度
> **溯源**：单位晋升 — 独立摇滚（`PROMOTION_INDIE`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ROCK_BAND_LEVEL_DISTRICT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ROCK_BAND_LEVEL_DISTRICT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1`、`2` |
| `DistrictType` | 是 | `DISTRICT_ACROPOLIS`、`DISTRICT_CAMPUS`、`DISTRICT_COTHON`、`DISTRICT_ENTERTAINMENT_COMPLEX`、`DISTRICT_HARBOR`、`DISTRICT_HIPPODROME` ... (共 15 种值) |

**效果**：摇滚乐队在指定区域演出时获得额外等级
> **溯源**：单位晋升 — 太空摇滚（`PROMOTION_SPACE_ROCK`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 专辑封面（`PROMOTION_ALBUM_COVER_ART`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 舞台摇滚（`PROMOTION_ARENA_ROCK`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 华丽摇滚（`PROMOTION_GLAM_ROCK`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 雷鬼音乐（`PROMOTION_REGGAE_ROCK`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ROCK_BAND_LEVEL_IMPROVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ROCK_BAND_LEVEL_IMPROVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |
| `ImprovementType` | 是 | `IMPROVEMENT_BEACH_RESORT` |

**效果**：摇滚乐队在指定改良设施上演出时获得额外等级
> **溯源**：单位晋升 — 冲浪摇滚（`PROMOTION_SURF_ROCK`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ROCK_BAND_LEVEL_NATIONAL_PARK

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ROCK_BAND_LEVEL_NATIONAL_PARK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：摇滚乐队在国家公园演出时获得额外等级
> **溯源**：单位晋升 — 音乐节（`PROMOTION_MUSIC_FESTIVAL`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ROCK_BAND_LEVEL_NATURAL_WONDER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_ROCK_BAND_LEVEL_NATURAL_WONDER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：摇滚乐队在自然奇观演出时获得额外等级
> **溯源**：单位晋升 — 音乐节（`PROMOTION_MUSIC_FESTIVAL`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_ROCK_BAND_TOURISM_BOMB_VALUE_PEACE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_ROCK_BAND_TOURISM_BOMB_VALUE_PEACE` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `200`、`50` |

**效果**：调整和平时期摇滚乐队的旅游业绩爆发值
> **溯源**：政策 — 权力归花儿（`POLICY_FLOWER_POWER`） — 通过政策卡提供加成

---

### EFFECT_ADJUST_UNIT_TOURISM_BOMB_CONVERT_CITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_CONVERT_CITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Convert` | 是 | `1` |

**效果**：摇滚乐队演出后转化目标城市的信仰宗教
> **溯源**：单位晋升 — 宗教摇滚（`PROMOTION_RELIGIOUS_ROCK`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_TOURISM_BOMB_DISTRICT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_DISTRICT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `500` |
| `DistrictType` | 是 | `DISTRICT_CAMPUS`、`DISTRICT_COTHON`、`DISTRICT_HARBOR`、`DISTRICT_OBSERVATORY`、`DISTRICT_ROYAL_NAVY_DOCKYARD`、`DISTRICT_SEOWON` |

**效果**：摇滚乐队在指定区域演出时额外获得旅游业绩
> **溯源**：单位晋升 — 太空摇滚（`PROMOTION_SPACE_ROCK`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 冲浪摇滚（`PROMOTION_SURF_ROCK`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_TOURISM_BOMB_IMPROVEMENT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_IMPROVEMENT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `500` |
| `ImprovementType` | 是 | `IMPROVEMENT_BEACH_RESORT` |

**效果**：摇滚乐队在指定改良设施上演出时额外获得旅游业绩
> **溯源**：单位晋升 — 冲浪摇滚（`PROMOTION_SURF_ROCK`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_TOURISM_BOMB_NATIONAL_PARK

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_NATIONAL_PARK` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1000` |

**效果**：摇滚乐队在国家公园演出时额外获得旅游业绩
> **溯源**：单位晋升 — 音乐节（`PROMOTION_MUSIC_FESTIVAL`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_TOURISM_BOMB_NATURAL_WONDER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_NATURAL_WONDER` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1000` |

**效果**：摇滚乐队在自然奇观演出时额外获得旅游业绩
> **溯源**：单位晋升 — 音乐节（`PROMOTION_MUSIC_FESTIVAL`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_TOURISM_BOMB_RANGE

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_RANGE` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Modifier` | 是 | `-50` |
| `Range` | 是 | `10` |

**效果**：调整摇滚乐队旅游业绩爆发的有效范围
> **溯源**：单位晋升 — 音量爆表（`PROMOTION_GOES_TO`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_YIELD_PER_TOURISM_BOMB

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_TOURISM_BOMB_ADDITIONAL_YIELD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-75` |
| `YieldType` | 是 | `YIELD_GOLD` |

**效果**：摇滚乐队旅游爆发时额外获得指定产出
> **溯源**：单位晋升 — 流行巨星（`PROMOTION_POP`） — 赋予单位晋升效果

---

## 视野/可见性

### EFFECT_ADJUST_UNIT_HIDDEN_VISIBILITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_HIDDEN_VISIBILITY` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Hidden` | 是 | `1`、`true`（`1`=是 / `0`=否） |

**效果**：赋予单位隐身能力（对敌方不可见）
> **溯源**：单位能力 — 隐形（`ABILITY_STEALTH`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 伪装（`PROMOTION_CAMOUFLAGE`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 迷魂幕（`PROMOTION_MONK_TWILIGHT_VEIL`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_SEE_HIDDEN

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SEE_HIDDEN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `SeeHidden` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位探测隐身单位的能力
> **溯源**：单位能力 — 反隐形（`ABILITY_SEE_HIDDEN`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_SEE_THROUGH_FEATURES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SEE_THROUGH_FEATURES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanSee` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许单位看穿地貌
> **溯源**：单位能力 — 开阔视野（`ABILITY_UNOBSTRUCTED_VIEW`） — 赋予单位特殊能力（一览无余的视野）
> **溯源**：单位能力 — 森林斗士（`ABILITY_NAGAO`） — 赋予单位特殊能力
> **溯源**：单位晋升 — 哨兵（`PROMOTION_SENTRY`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 很干的面包（`PROMOTION_SPECIAL_CEOBE_R1`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_SEE_THROUGH_TERRAIN

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SEE_THROUGH_TERRAIN` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `CanSee` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：允许单位看穿地形
> **溯源**：单位能力 — 开阔视野（`ABILITY_UNOBSTRUCTED_VIEW`） — 赋予单位特殊能力

---

### EFFECT_ADJUST_UNIT_SIGHT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_SIGHT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-1`、`1`、`10`、`2`、`3` |

**效果**：调整单位的视野范围
> **溯源**：单位晋升 — 望远镜（`PROMOTION_SPYGLASS`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 航线海图（`PROMOTION_RUTTER`） — 赋予单位晋升效果（航线海图）
> **溯源**：单位晋升 — 侦察飞机（`PROMOTION_SCOUT_PLANES`） — 赋予单位晋升效果
> **溯源**：单位晋升 — 观察（`PROMOTION_OBSERVATION`） — 赋予单位晋升效果
> **溯源**：单位能力 — 雷夫·埃里克森（`ABILITY_ERIKSON_NAVAL_SIGHT`） — 赋予单位特殊能力

---

## 其他

### EFFECT_ADJUST_NUM_UNITS_SUPPORTED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_CITIES_ADJUST_NUM_UNITS_SUPPORTED` | `COLLECTION_PLAYER_CITIES` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |
| `BuildingType` | 是 | `BUILDING_MUSEUM_ARTIFACT` |

**效果**：调整可支持的单位数量（如考古学家）
> **溯源**：文明/领袖特性 — 大英博物馆（`TRAIT_CIVILIZATION_DOUBLE_ARCHAEOLOGY_SLOTS`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_PLAYER_DISTRICT_AND_BUILDINGS_CREATE_UNIT_WITH_ABILITY_BY_CLASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_ADJUST_PLAYER_DISTRICT_AND_BUILDINGS_CREATE_UNIT_WITH_ABILITY_BY_CLASS_GREAT_NEGOTIATORS` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_DISTRICT_ADJUST_PLAYER_DISTRICT_AND_BUILDINGS_CREATE_UNIT_WITH_ABILITY_BY_CLASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | 是 | `DISTRICT_HIPPODROME`、`DISTRICT_INDUSTRIAL_ZONE` |
| `UnitAbilityType` | 是 | `ABILITY_FREE_RESOURCE_MAITENANCE_HIPPODROME`、`ABILITY_LINCOLN_MELEE_UNITS` |
| `UnitPromotionClass` | 是 | `PROMOTION_CLASS_HEAVY_CAVALRY`、`PROMOTION_CLASS_MELEE` |

**效果**：建造区域及建筑时生成携带指定能力的单位
> **溯源**：文明/领袖特性 — 解放黑奴宣言（`TRAIT_LEADER_LINCOLN`） — 文明或领袖特性效果
> **溯源**：文明/领袖特性 — TRAIT_CIVILIZATION_DISTRICT_HIPPODROME（`TRAIT_CIVILIZATION_DISTRICT_HIPPODROME`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_PLAYER_DISTRICT_CREATE_UNIT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_DISTRICT_CREATE_UNIT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | 是 | `DISTRICT_MBANZA`、`DISTRICT_THEATER` |
| `UnitType` | 是 | `UNIT_APOSTLE` |

**效果**：完成区域建造时生成指定单位
> **溯源**：文明/领袖特性 — 宗教转换（`TRAIT_LEADER_RELIGIOUS_CONVERT`） — 文明或领袖特性效果

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_NON_BARBARIAN_UNIT_KILLED_BY_GDR

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_NON_BARBARIAN_UNIT_KILLED_BY_GDR` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：GDR击杀非蛮族单位时获得时代分数
> **溯源**：纪念活动 — COMMEMORATION_AUTOMATON（`COMMEMORATION_AUTOMATON`）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_NON_BARBARIAN_UNIT_SEA_KILLED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PLAYER_ERA_SCORE_PER_NON_BARBARIAN_NAVAL_UNIT_KILLED` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：海军单位击杀非蛮族单位时获得时代分数
> **溯源**：纪念活动 — COMMEMORATION_EXPLORATION（`COMMEMORATION_EXPLORATION`）

---

### EFFECT_ADJUST_PLAYER_ERA_SCORE_PER_UNIT_PROMOTION_EARNED

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_PLAYERS_ADJUST_ERA_SCORE_PER_UNIT_PROMOTION_EARNED` | `COLLECTION_MAJOR_PLAYERS` |

| *(无参数)* | | |
|---|---|---|

**效果**：单位晋升时获得时代分数
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_BUILD_CHARGES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_BUILDER_CHARGES` | `COLLECTION_OWNER` |
| `MODIFIER_CEOBE_PLAYER_UNIT_ADJUST_BUILDER_CHARGES` | `COLLECTION_OWNER` |
| `MODIFIER_SINGLE_CITY_BUILDER_CHARGES` | `COLLECTION_CITY_TRAINED_UNITS` |
| `MODIFIER_PLAYER_TRAINED_UNITS_ADJUST_BUILDER_CHARGES` | `COLLECTION_PLAYER_TRAINED_UNITS` |
| `MODIFIER_PLAYER_UNITS_ADJUST_BUILDER_CHARGES` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `-1`、`1`、`2`、`3` |

**效果**：调整建造者/工兵的使用次数
> **溯源**：政策 — 公共工程（`POLICY_PUBLIC_WORKS`） — 通过政策卡提供加成
> **溯源**：政策 — 农奴制（`POLICY_SERFDOM`） — 通过政策卡提供加成
> **溯源**：奇观 — 金字塔（`BUILDING_PYRAMIDS`） — 奇观效果
> **溯源**：文明/领袖特性 — 始皇帝（`FIRST_EMPEROR_TRAIT`） — 文明或领袖特性效果
---

### EFFECT_ADJUST_UNIT_DISASTER_CHARGES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_UNIT_ADJUST_DISASTER_CHARGES` | `COLLECTION_OWNER` |

| *(无参数)* | | |
|---|---|---|

**效果**：调整单位应对灾害的使用次数
> **溯源**：该 EffectType 仅在 DynamicModifiers 中注册，官方数据库中无实际 Modifier 使用记录

---

### EFFECT_ADJUST_UNIT_EXTRACT_SEA_ARTIFACTS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_EXTRACT_SEA_ARTIFACTS` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Extract` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：赋予单位提取海洋文物的能力
> **溯源**：市政 — 文化遗产（`CIVIC_CULTURAL_HERITAGE`）

---

### EFFECT_ADJUST_UNIT_GREAT_PERSON_CHARGES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_GREAT_PERSON_CHARGES` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：调整伟人的使用次数
> **溯源**：建筑 — 摩索拉斯王陵墓（`BUILDING_HALICARNASSUS_MAUSOLEUM`）

---

### EFFECT_ADJUST_UNIT_INITIATION_YIELD

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_INITIATION_GOLD` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `100` |
| `YieldType` | 是 | `YIELD_GOLD` |

**效果**：宗教单位首次传教时获得指定产出
> **溯源**：单位晋升 — 赎罪卷小贩（`PROMOTION_INDULGENCE_VENDOR`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_INITIATION_YIELD_POPULATION

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_INITIATION_YIELD_POPULATION` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `20` |
| `YieldType` | 是 | `YIELD_SCIENCE` |

**效果**：宗教单位按目标城市人口传教时获得指定产出
> **溯源**：城邦 — 菲斯（`MINOR_CIV_FEZ`） — 城邦宗主国加成

---

### EFFECT_ADJUST_UNIT_NATURAL_WONDER_DEFERRED_CHARGES

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_NATURAL_WONDER_DEFERRED_CHARGES` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `3` |

**效果**：宗教单位在自然奇观旁传教不消耗次数
> **溯源**：单位晋升 — 朝圣者（`PROMOTION_PILGRIM`） — 赋予单位晋升效果

---

### EFFECT_ADJUST_UNIT_OWNER

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNITS_ADJUST_OWNER` | `COLLECTION_ALL_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `NewOwner` | 是 | `Player` |

**效果**：转移单位的所有权给当前玩家
> **溯源**：伟人能力 — 布狄卡（`GREAT_PERSON_INDIVIDUAL_BOUDICA`）（把相邻蛮族转到您的控制之下。）

---

### EFFECT_ADJUST_UNIT_VALID_TERRAIN

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_UNIT_ADJUST_VALID_TERRAIN` | `COLLECTION_OWNER` |
| `MODIFIER_PLAYER_UNITS_ADJUST_VALID_TERRAIN` | `COLLECTION_PLAYER_UNITS` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `TerrainType` | 是 | `TERRAIN_OCEAN` |
| `Valid` | 是 | `1`（`1`=是 / `0`=否） |

**效果**：设置单位可通行的地形类型
> **溯源**：文明/领袖特性 — 龙骨船（`TRAIT_CIVILIZATION_EARLY_OCEAN_NAVIGATION`） — 文明或领袖特性效果
> **溯源**：伟人能力 — 雷夫·埃里克森（`GREAT_PERSON_INDIVIDUAL_LEIF_ERIKSON`）
> **溯源**：科技 — 制图学（`TECH_CARTOGRAPHY`）
> **溯源**：文明/领袖特性 — 玛那（`TRAIT_CIVILIZATION_MAORI_MANA`） — 文明或领袖特性效果

---

### EFFECT_CHANGE_UNIT_OPERATION_AVAILABILITY

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_ALL_UNITS_DISABLE_OPERATION` | `COLLECTION_ALL_UNITS` |

| *(无参数)* | | |
|---|---|---|

**效果**：禁用/启用单位的特定行动操作
> **溯源**：世界议会决议 — "间谍协定"（`WC_RES_ESPIONAGE_PACT`） — 世界议会议案效果

---

### EFFECT_DISTRICT_ADD_NAVAL_UNIT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_DISTRICT_ADD_NAVAL_UNIT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `DistrictType` | 是 | `DISTRICT_ROYAL_NAVY_DOCKYARD` |

**效果**：完成区域建造时获得一艘海军单位
> **溯源**：文明/领袖特性 — 英国强权下的和平（`TRAIT_LEADER_PAX_BRITANNICA`） — 文明或领袖特性效果

---

### EFFECT_GRANT_FREE_RESOURCE_FROM_UNIT_PLOT

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_GRANT_FREE_RESOURCE_FROM_UNIT_PLOT` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `Amount` | 是 | `1` |

**效果**：赠予单位所在单元格的奢侈品资源
> **溯源**：伟人能力 — 柯莱欧司（`GREAT_PERSON_INDIVIDUAL_COLAEUS`）（赠予{Amount}份该单元格上的奢侈品资源给您的 [ICON_Capital] 首都城市。）
> **溯源**：伟人能力 — 斐迪南·麦哲伦（`GREAT_PERSON_INDIVIDUAL_FERDINAND_MAGELLAN`）

---

### EFFECT_SETTLED_FOREIGN_CONTINENT_UNIT_CLASS

| ModifierType | CollectionType |
|---|---|
| `MODIFIER_PLAYER_ADJUST_SETTLE_FOREIGN_CONTINENT_UNIT_CLASS` | `COLLECTION_OWNER` |

| 参数 | 写不写 | 值/引用 |
|---|---|---|
| `UnitPromotionClassType` | 是 | `PROMOTION_CLASS_MELEE` |

**效果**：在其他大陆建立城市时赠送指定兵种类别的单位
> **溯源**：文明/领袖特性 — 英国强权下的和平（`TRAIT_LEADER_PAX_BRITANNICA`） — 文明或领袖特性效果

---

## 注意事项

### 统计
- 总计 165 个通过 DynamicModifiers 注册的 EffectType
- 0 个 EffectType 在 DB 中无记录（可能为 MOD 专属或已废弃）

### SPECIAL: EFFECT_ADJUST_UNIT_PROPERTY

`EFFECT_ADJUST_UNIT_PROPERTY` 是通用单位属性修改 EffectType，其行为完全由 `Key` 参数决定。

该 EffectType 在官方数据库中无实际使用记录，Key 值由 MOD 自定义定义。

### SPECIAL: GRANT_STRENGTH_PER_ADJACENT_UNIT_TYPE

`GRANT_STRENGTH_PER_ADJACENT_UNIT_TYPE` 是少数**不带 `MODIFIER_` 前缀**的 ModifierType（直接以 `GRANT_` 开头），
用于根据相邻指定单位类型提供战斗力加成。参数：`Amount`（每单位加成量）、`UnitType`（指定单位类型）。

### 战斗力类效果的 ModifierStrings

`EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` 必须填写预览文本，详见 [通用技巧](modifier-techniques.md)。不要按“战斗力/属性类”的名字把这条规则推广到其他 EffectType；基础战斗力效果与战斗上下文加成应区分。

### 常见枚举值速查

| 参数 | 枚举类型 | 常用值 |
|---|---|---|
| `UnitType` | Units | `UNIT_BUILDER`, `UNIT_SETTLER`, `UNIT_APOSTLE` |
| `PromotionClass` | UnitPromotionClasses | `PROMOTION_CLASS_MELEE`, `PROMOTION_CLASS_ANTI_CAVALRY`, `PROMOTION_CLASS_HEAVY_CAVALRY` |
| `UnitDomain` | `SELECT DISTINCT Domain FROM Units` | `DOMAIN_LAND`, `DOMAIN_SEA`, `DOMAIN_ALL` |
| `MilitaryFormationType` | MilitaryFormations | `CORPS_MILITARY_FORMATION`, `ARMY_MILITARY_FORMATION` |
| `YieldType` | Yields | `YIELD_GOLD`, `YIELD_FAITH`, `YIELD_CULTURE`, `YIELD_SCIENCE` |
| `OperationType` | UnitOperations | `UNITOPERATION_SPY_GREAT_WORK_HEIST`, `UNITOPERATION_SPY_RECRUIT_PARTISANS` |
| `Type` (回血) | — | `ALL`, `FRIENDLY`, `NEUTRAL`, `ENEMY` |
