# Grant Ability 案例

> **这是最重要的模式。** AI 最容易遗漏的是：Grant Ability 不仅需要 `MODIFIER_PLAYER_UNITS_GRANT_ABILITY`，还必须先注册 Ability 本身（Types → TypeTags → UnitAbilities → UnitAbilityModifiers → 子 Modifiers → 子 ModifierArguments）。**5 层链路缺一不可。**

> `MODIFIER_PLAYER_UNITS_GRANT_ABILITY` 和 `MODIFIER_ALL_UNITS_GRANT_ABILITY` 都是标准 ModifierType，**无需 DynamicModifiers 注册**。

## 链路模板

```
TraitModifiers
  → Modifiers(ModifierType=MODIFIER_PLAYER_UNITS_GRANT_ABILITY)
    → ModifierArguments(AbilityType=ABILITY_xxx)
      → Types(KIND_ABILITY)          ← 注册 Ability Type
        → TypeTags(Tag=CLASS_xxx)    ← 哪些单位获得
          → UnitAbilities(定义)       ← Ability 本身
            → UnitAbilityModifiers   ← Ability 下挂什么效果
              → Modifiers(子效果)     ← 实际生效的子 Modifier
                → ModifierArguments  ← 子效果参数
```

## 变体 1：简单版 — 全战斗单位 +7 战力（最简）

**来源**：Siqi_Leaders_0046

```sql
-- 1. 注册 Ability
INSERT INTO Types (Type, Kind) VALUES
('ABILITY_SIQI_L0046_COMBAT', 'KIND_ABILITY');

-- 2. TypeTags
INSERT INTO TypeTags (Type, Tag) VALUES
('ABILITY_SIQI_L0046_COMBAT', 'CLASS_ALL_COMBAT_UNITS');

-- 3. UnitAbilities
INSERT INTO UnitAbilities (UnitAbilityType, Name, Description, Inactive, Permanent) VALUES
('ABILITY_SIQI_L0046_COMBAT', NULL, NULL, 1, 1);

-- 4. UnitAbilityModifiers
INSERT INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_SIQI_L0046_COMBAT', 'MODIFIER_SIQI_0046_L0046_COMBAT_STRENGTH_12');

-- 5. 子 Modifier + 参数
INSERT INTO Modifiers(ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0046_L0046_COMBAT_STRENGTH_12', 'MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH', 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0046_L0046_COMBAT_STRENGTH_12', 'Amount', 12);

-- 6. GRANT_ABILITY 外层
INSERT INTO Modifiers(ModifierId, ModifierType, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0046_GRANT_ABILITY_L0046_COMBAT', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY', 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0046_GRANT_ABILITY_L0046_COMBAT', 'AbilityType', 'ABILITY_SIQI_L0046_COMBAT');

-- 7. 挂载
INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_LEADER_SIQI_L0046_1', 'MODIFIER_SIQI_0046_GRANT_ABILITY_L0046_COMBAT');
```

---

## 变体 2：多效 — 全战斗单位 +7 战力 + 每回合治疗 100

**来源**：Siqi_Leaders_0040（UnitAbility 下挂 2 个子 Modifier）

```sql
-- Ability 挂 2 个效果
INSERT INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_SIQI_A0040_2', 'MODIFIER_SIQI_0040_COMBAT_STRENGTH_7'),
('ABILITY_SIQI_A0040_2', 'MODIFIER_SIQI_0040_UNIT_DAMAGE_HEAL_100');

-- 治疗需要 OwnerRequirementSetId 绑定回合触发
INSERT INTO Modifiers (ModifierId, ModifierType, OwnerRequirementSetId) VALUES
('MODIFIER_SIQI_0040_UNIT_DAMAGE_HEAL_100', 'MODIFIER_PLAYER_UNIT_ADJUST_DAMAGE',
 'REQSET_SIQI_0040_PLAYER_TURN_STARTED');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0040_UNIT_DAMAGE_HEAL_100', 'Amount', -100);

-- RequirementSet：回合触发 + Triggered=1
INSERT INTO RequirementSets (RequirementSetId, RequirementSetType) VALUES
('REQSET_SIQI_0040_PLAYER_TURN_STARTED', 'REQUIREMENTSET_TEST_ALL');

INSERT INTO Requirements (RequirementId, RequirementType, Triggered) VALUES
('REQ_SIQI_0040_PLAYER_TURN_STARTED', 'REQUIREMENT_PLAYER_TURN_STARTED', 1);

INSERT INTO RequirementSetRequirements (RequirementSetId, RequirementId) VALUES
('REQSET_SIQI_0040_PLAYER_TURN_STARTED', 'REQ_SIQI_0040_PLAYER_TURN_STARTED');
```

---

## 变体 3：全日青7效 — 隐匿/视野/移动/穿地形/穿地貌/无视河流

**来源**：Siqi_Leaders_0040 + Siqi_Leaders_0046

```sql
-- TypeTags: CLASS_ALL_UNITS（非战斗单位也获得）
INSERT INTO TypeTags (Type, Tag) VALUES
('ABILITY_SIQI_A0040_3', 'CLASS_ALL_UNITS');

-- UnitAbilityModifiers: 6-8 个效果挂一个 Ability
INSERT INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_SIQI_A0040_3', 'MODIFIER_SIQI_0040_HIDDEN_VISIBILITY_HIDDEN'),
('ABILITY_SIQI_A0040_3', 'MODIFIER_SIQI_0040_MOVEMENT_4'),
('ABILITY_SIQI_A0040_3', 'MODIFIER_SIQI_0040_SIGHT_4'),
('ABILITY_SIQI_A0040_3', 'MODIFIER_SIQI_0040_SEE_THROUGH_FEATURES_CANSEE'),
('ABILITY_SIQI_A0040_3', 'MODIFIER_SIQI_0040_SEE_THROUGH_TERRAIN_CANSEE'),
('ABILITY_SIQI_A0040_3', 'MODIFIER_SIQI_0040_IGNORE_TERRAIN_COST_IGNORE');

-- 各子 Modifier 的 ModifierArguments
-- Hidden:       Hidden=1
-- Movement:     Amount=2
-- Sight:        Amount=2
-- SeeThrough:   CanSee=1
-- IgnoreCost:   Ignore=1, Type='ALL'
```

---

## 变体 4：双标签 — 战斗单位 + 建造者各获得不同效果

**来源**：Siqi_Leaders_0042

```sql
-- TypeTags 双标签（战斗单位 AND 建造者同时获得）
INSERT INTO TypeTags (Type, Tag) VALUES
('ABILITY_SIQI_L0042_EXTRA_CHARGE', 'CLASS_ALL_COMBAT_UNITS'),
('ABILITY_SIQI_L0042_EXTRA_CHARGE', 'CLASS_BUILDER');

-- 建造者 +1 劳动力
INSERT INTO Modifiers(ModifierId, ModifierType) VALUES
('MODIFIER_SIQI_L0042_EXTRA_CHARGE', 'MODIFIER_UNIT_ADJUST_BUILDER_CHARGES');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_L0042_EXTRA_CHARGE', 'Amount', 1);
```

---

## 变体 5：距离分层 — 1~10 层每层独立战斗力加成

**来源**：Siqi_Leaders_0042

```sql
-- 10 个距离层 × 1 Ability = 10 个 UnitAbilityModifiers
INSERT INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_SIQI_L0042_RANGE_POWER', 'MODIFIER_SIQI_L0042_DIST_1_COMBAT'),
('ABILITY_SIQI_L0042_RANGE_POWER', 'MODIFIER_SIQI_L0042_DIST_2_COMBAT'),
-- ... DIST_3 到 DIST_10 类似

-- 每层带独立 SubjectRequirementSetId（MinDistance/MaxDistance 区分）
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId) VALUES
('MODIFIER_SIQI_L0042_DIST_1_COMBAT', 'MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH',
 'REQSET_SIQI_L0042_PLOT_DIST_1');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_L0042_DIST_1_COMBAT', 'Amount', 3);    -- 距离1=+3
-- ... DIST_10_COMBAT 'Amount', 30                    -- 距离10=+30

-- 每层 RequirementSet
INSERT INTO Requirements (RequirementId, RequirementType) VALUES
('REQ_SIQI_L0042_PLOT_DIST_1', 'REQUIREMENT_PLOT_ADJACENT_TO_OWNER');

INSERT INTO RequirementArguments (RequirementId, Name, Value) VALUES
('REQ_SIQI_L0042_PLOT_DIST_1', 'MinDistance', 1),
('REQ_SIQI_L0042_PLOT_DIST_1', 'MaxDistance', 1);
```

---

## 变体 6：条件过滤版 — Grant 时带 SubjectRequirementSetId

**来源**：SIQI_LEADERS_0006 + Siqi_Leaders_0043

两种写法：

### 6a：条件写在外层 GRANT_ABILITY（同 Ability 不同条件用多个外层）

```sql
-- 三个 GRANT_ABILITY，各带不同地形条件
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId) VALUES
('MODIFIER_SIQI_0006_10_GRANT_ABILITY_SIQI_L0006_10_1', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY', 'SIQI_0006_IS_HILLS'),   -- 丘陵
('MODIFIER_SIQI_0006_10_GRANT_ABILITY_SIQI_L0006_10_2', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY', 'SIQI_0006_IS_FEATURE_JUNGLE'), -- 雨林
('MODIFIER_SIQI_0006_10_GRANT_ABILITY_SIQI_L0006_10_3', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY', 'SIQI_0006_IS_FEATURE_FOREST'); -- 森林
```

### 6b：时代/科技/市政条件 — 写在 GRANT_ABILITY 层

> **规范**：玩家状态条件（黑暗时代/黄金时代/有某科技/有某市政/领袖匹配）优先写在 GRANT_ABILITY 的 `OwnerRequirementSetId` 上。虽然大部分子 Modifier 也能接受这些条件，但 `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` + 时代条件结合是已知会导致游戏崩溃的特例。为统一避免此类 Bug，**玩家级别判断尽可能在 GRANT_ABILITY 层完成**。

```sql
-- 正确写法：条件在 GRANT_ABILITY 层（OwnerRequirementSetId 判断玩家是否处于黑暗时代）
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId) VALUES
('MODIFIER_SIQI_0039_ABILITY_A0039_PLAYER_HAS_DARK_AGE', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY',
 'REQSET_SIQI_0039_PLAYER_HAS_DARK_AGE');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0039_ABILITY_A0039_PLAYER_HAS_DARK_AGE', 'AbilityType', 'ABILITY_SIQI_A0039_1');

-- 子 Modifier 不写条件
INSERT INTO Modifiers(ModifierId, ModifierType) VALUES
('MODIFIER_SIQI_0039_COMBAT_STRENGTH_DARK', 'MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0039_COMBAT_STRENGTH_DARK', 'Amount', 7);

-- 黄金时代同理：另一个 GRANT_ABILITY + 另一个 Ability
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId) VALUES
('MODIFIER_SIQI_0039_ABILITY_A0039_PLAYER_HAS_GOLDEN_AGE', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY',
 'REQSET_SIQI_0039_PLAYER_HAS_GOLDEN_AGE');
```

**条件放哪层规则**：

| 条件类型                            | 必须放哪层                                                                         | 示例                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------- |
| 玩家状态（时代/科技/市政/领袖）     | **GRANT_ABILITY 的 OwnerRequirementSetId**                                   | `REQUIREMENT_PLAYER_HAS_DARK_AGE`       |
| 地块状态（地形/地貌/改良/距离）     | 子 Modifier 的 SubjectRequirementSetId 或 GRANT_ABILITY 的 SubjectRequirementSetId | `REQUIREMENT_PLOT_TERRAIN_TYPE_MATCHES` |
| 单位自身状态（是否进攻方/是否满血） | 子 Modifier 的 SubjectRequirementSetId                                             | `UNIT_IS_ATTACKING`                     |

---

## 变体 7：政策卡版 — PolicyModifiers 替代 TraitModifiers

**来源**：Siqi_Leaders_0040（政策卡「邪恶凝视」）

```sql
-- 用 PolicyModifiers 而不是 TraitModifiers
INSERT INTO PolicyModifiers (PolicyType, ModifierId) VALUES
('POLICY_SIQI_0040_1', 'MODIFIER_SIQI_0040_POLICY_GRANT_ABILITY');

-- 其余链路完全一样：Types(KIND_ABILITY) → TypeTags → UnitAbilities → UnitAbilityModifiers → 子 Modifiers → ModifierArguments
-- 唯一区别：Ability 的 Permanent=0（政策取消后 Ability 移除）
INSERT INTO UnitAbilities (UnitAbilityType, Name, Description, Inactive, ShowFloatTextWhenEarned, Permanent) VALUES
('ABILITY_SIQI_A0040_4', 'LOC_ABILITY_SIQI_A0040_4_NAME', NULL, 1, 0, 0);
```

---

## 变体 8：信仰版 — BeliefModifiers → ALL_PLAYERS_ATTACH → GRANT_ABILITY

**来源**：Siqi_Leaders_0007

```sql
-- INSERT ... SELECT 遍历所有 Follower 信仰
INSERT INTO BeliefModifiers (BeliefType, ModifierId)
SELECT BeliefType, 'MODIFIER_SIQI_L0007_ATTACH_MODIFIER'
FROM Beliefs WHERE BeliefClassType = 'BELIEF_CLASS_FOLLOWER';

-- 上级 ATTACH：ALL_PLAYERS_ATTACH → 对创立宗教的玩家生效
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId) VALUES
('MODIFIER_SIQI_L0007_ATTACH_MODIFIER', 'MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER',
 'PLAYER_FOUNDED_RELIGION_REQUIREMENTS');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_L0007_ATTACH_MODIFIER', 'ModifierId', 'MODIFIER_SIQI_L0007_UNITS_GRANT_ABILITY');

-- 下级 GRANT_ABILITY：限制特定领袖
INSERT INTO Modifiers(ModifierId, ModifierType, OwnerRequirementSetId) VALUES
('MODIFIER_SIQI_L0007_UNITS_GRANT_ABILITY', 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY',
 'SIQI_0007_IS_LEADER_SIQI_L0007');
```

---

## MODIFIER_ALL_UNITS_GRANT_ABILITY 的特殊用法

`MODIFIER_ALL_UNITS_GRANT_ABILITY` 的 Subject 是**地块上的所有单位**（不是玩家单位）。必须配合 SubjectRequirementSetId 限制哪些地块的单位获得 Ability，通常通过 ATTACH 链挂到城市上使用。

```sql
-- 内层（被 ATTACH 触发，限制 3 环内地块上的单位）
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId) VALUES
('MODIFIER_SIQI_0040_ABILITY_A0040', 'MODIFIER_ALL_UNITS_GRANT_ABILITY',
 'REQSET_SIQI_0040_PLOT_ADJACENT_TO_OWNER_3');

-- 外层（挂到每个城市）
INSERT INTO Modifiers(ModifierId, ModifierType) VALUES
('MODIFIER_SIQI_0040_MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER_A0040',
 'MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER');

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0040_MODIFIER_PLAYER_CITIES_ATTACH_MODIFIER_A0040',
 'ModifierId', 'MODIFIER_SIQI_0040_ABILITY_A0040');
```

---

## 常用 TypeTag 值

| Tag                        | 覆盖范围                                   |
| -------------------------- | ------------------------------------------ |
| `CLASS_ALL_COMBAT_UNITS` | 所有战斗单位                               |
| `CLASS_ALL_UNITS`        | 所有单位（含平民）                         |
| `CLASS_RECON`            | 侦察单位                                   |
| `CLASS_MELEE`            | 近战                                       |
| `CLASS_RANGED`           | 远程                                       |
| `CLASS_SIEGE`            | 攻城                                       |
| `CLASS_HEAVY_CAVALRY`    | 重骑兵                                     |
| `CLASS_LIGHT_CAVALRY`    | 轻骑兵                                     |
| `CLASS_RANGED_CAVALRY`   | 远程骑兵                                   |
| `CLASS_NAVAL_MELEE`      | 海军近战                                   |
| `CLASS_NAVAL_RANGED`     | 海军远程                                   |
| `CLASS_BUILDER`          | 建造者                                     |
| 自定义                     | `CLASS_SIQI_xxx`（在 TypeTags 表中注册） |

## 常用子 ModifierType

| 子 ModifierType                                                  | 参数                               | 用途               |
| ---------------------------------------------------------------- | ---------------------------------- | ------------------ |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH`                         | `Amount` (正=加)                 | 战斗力             |
| `MODIFIER_PLAYER_UNIT_ADJUST_DAMAGE`                           | `Amount` (-100=治疗)             | 治疗/伤害          |
| `MODIFIER_PLAYER_UNIT_ADJUST_HEAL_FROM_COMBAT`                 | `Amount`                         | 战后回血%          |
| `MODIFIER_PLAYER_UNIT_ADJUST_MOVEMENT`                         | `Amount`                         | 移动力             |
| `MODIFIER_PLAYER_UNIT_ADJUST_SIGHT`                            | `Amount`                         | 视野               |
| `MODIFIER_PLAYER_UNIT_ADJUST_HIDDEN_VISIBILITY`                | `Hidden` (0/1)                   | 隐匿               |
| `MODIFIER_PLAYER_UNIT_ADJUST_SEE_THROUGH_FEATURES`             | `CanSee` (0/1)                   | 穿透地貌           |
| `MODIFIER_PLAYER_UNIT_ADJUST_SEE_THROUGH_TERRAIN`              | `CanSee` (0/1)                   | 穿透地形           |
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_TERRAIN_COST`              | `Ignore` (0/1), `Type` ('ALL') | 无地形惩罚         |
| `MODIFIER_PLAYER_UNIT_ADJUST_IGNORE_ZOC`                       | `Ignore` (0/1)                   | 无视 ZOC           |
| `MODIFIER_UNIT_ADJUST_BUILDER_CHARGES`                         | `Amount`                         | 建造者劳动力       |
| `MODIFIER_PLAYER_UNIT_ADJUST_UNIT_EXPERIENCE_MODIFIER`         | `Amount`                         | 经验加成%          |
| `MODIFIER_PLAYER_UNITS_ADJUST_UNIT_ATTACK_EXPERIENCE_MODIFIER` | `Amount`                         | 进攻经验%          |
| `MODIFIER_UNIT_ADJUST_NUM_ATTACKS`                             | `Amount`                         | 攻击次数           |
| `MODIFIER_SINGLE_UNIT_ADJUST_JUMP_DISTANCE`                    | `Range`                          | 跳跃距离           |
| `MODIFIER_PLAYER_UNIT_ADJUST_NO_REDUCTION_DAMAGE`              | `NoReduction` (0/1)              | 受伤不减战力       |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` (带 Key)                | `Key` (Property名)               | 从 Property 读战力 |
