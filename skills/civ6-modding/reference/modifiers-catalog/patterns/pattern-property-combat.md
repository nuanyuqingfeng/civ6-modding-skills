# 模式 B：Property → 战斗力 via Grant Ability + Key

## 适用场景
- Property 值需要转换为实际战斗力
- 任何"用 Property 做中间存储，最后转为战斗力"的场景

> **注**：Property 只能转战斗力（`MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` + `Key`）。移动力用 `MODIFIER_PLAYER_UNITS_ADJUST_MOVEMENT` + `Amount` 直接实现，无需 Property 中转。

## 核心思路

**两步走**：
1. **累加 Property**：用 `MODIFIER_XXX_UNITS_ADJUST_PROPERTY`（Key + Amount）——⚠️ **没有标准类型，必须自定义**，见下文"累加 Property 的自定义注册"
2. **读 Property → 战斗力**：用 `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH`（Key 参数，非 Amount）

`MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` 有 `Key` 参数时，直接读取单位上该 Key 的 Property 值作为战斗力加成。**不需要写 Amount。**

Step 2 需要通过 **Grant Ability** 中转，因为 `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` 的 CollectionType 是 `COLLECTION_UNIT_COMBAT`（单位级），不能直接从 Player 层挂。

## 表链路

```
TraitModifiers (文明特质)
  → MODIFIER_PLAYER_UNITS_GRANT_ABILITY
    → ABILITY_SIQI_A00XX_1
      → UnitAbilityModifiers
        → MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH (Key=Property名)
```

## 完整代码示例

### Step 1 — 累加 Property（自定义注册 + 使用）

⚠️ **`MODIFIER_PLAYER_UNITS_ADJUST_PROPERTY` 不是标准类型**（DB 实测：标准库只有 `MODIFIER_PLAYER_ADJUST_PROPERTY`/`MODIFIER_SINGLE_CITY_ADJUST_PROPERTY`/`MODIFIER_UNIT_ADJUST_PROPERTY`）。要给"所有单位"累加 Property，必须自定义（0045/0032 均如此）：

```sql
-- ① 注册自定义类型（Types + DynamicModifiers）
INSERT INTO Types (Type, Kind) VALUES
('MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY', 'KIND_MODIFIER');

INSERT INTO DynamicModifiers (ModifierType, EffectType, CollectionType) VALUES
('MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY',
 'EFFECT_ADJUST_UNIT_PROPERTY', 'COLLECTION_PLAYER_UNITS');

-- ② 然后才能作为 ModifierType 使用（示例：每存活文明 +5 Property）
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_PROPERTY_5',
 'MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY',  -- 自定义类型，非标准！
 NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_PROPERTY_5', 'Key',    'Siqi0045_Combat_From_Civ'),
('MODIFIER_SIQI_0045_ADJUST_PROPERTY_5', 'Amount', '5');
```

> Property Key 示例：`'Siqi0045_Combat_From_Civ'`（见模式 A 完整示例）。

### Step 2 — Grant Ability 给所有单位
```sql
INSERT INTO Types (Type, Kind) VALUES
('ABILITY_SIQI_A0045_1', 'KIND_ABILITY');

INSERT INTO TypeTags (Type, Tag) VALUES
('ABILITY_SIQI_A0045_1', 'CLASS_ALL_COMBAT_UNITS');

INSERT INTO UnitAbilities (UnitAbilityType, Name, Description, Inactive, Permanent) VALUES
('ABILITY_SIQI_A0045_1', NULL, NULL, 0, 1);

INSERT INTO TraitModifiers (TraitType, ModifierId) VALUES
('TRAIT_CIVILIZATION_SIQI_C0045_1', 'MODIFIER_SIQI_0045_GRANT_ABILITY_A0045');

INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_GRANT_ABILITY_A0045',
 'MODIFIER_PLAYER_UNITS_GRANT_ABILITY',
 NULL, 0, 0);

INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_GRANT_ABILITY_A0045',
 'AbilityType', 'ABILITY_SIQI_A0045_1');
```

### Step 3 — Property → Combat（UnitAbilityModifiers）
```sql
INSERT INTO Modifiers(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent) VALUES
('MODIFIER_SIQI_0045_ADJUST_STRENGTH_',
 'MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH',
 NULL, 0, 0);

-- 关键：用 Key 参数，非 Amount！
INSERT INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MODIFIER_SIQI_0045_ADJUST_STRENGTH_', 'Key', 'Siqi0045_Combat_From_Civ');

INSERT INTO UnitAbilityModifiers (UnitAbilityType, ModifierId) VALUES
('ABILITY_SIQI_A0045_1', 'MODIFIER_SIQI_0045_ADJUST_STRENGTH_');
```

## 标准 ModifierType（无需 DynamicModifiers）

| ModifierType | CollectionType | 参数 |
|-------------|----------------|------|
| `MODIFIER_PLAYER_UNITS_GRANT_ABILITY` | `COLLECTION_PLAYER_UNITS` | `AbilityType` |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` | `COLLECTION_UNIT_COMBAT` | `Key`（读Property）或 `Amount`（固定值） |

## 必须自定义的类型（无标准版）

| 逻辑用途 | 自定义方式 | 参考实现 |
|---------|-----------|---------|
| 玩家所有单位累加 Property | `Types + DynamicModifiers`，EffectType=`EFFECT_ADJUST_UNIT_PROPERTY`，CollectionType=`COLLECTION_PLAYER_UNITS` | `MODIFIER_SIQI0045_PLAYER_UNITS_ADJUST_PROPERTY`（0045）<br>`MODIFIER_SIQI0032_PLAYER_UNITS_ADJUST_PROPERTY`（0032） |

## 参考代码位置

- `Siqi_Leaders_0032/Data/Siqi_Leaders_0032_Modifiers.sql` 行 621 + 1088
  - `MODIFIER_SIQI_G0032_4_AURA_COMBAT_READER` → Key = `SIQI_G0032_4_Combat`
- `Siqi_Leaders_0032/Data/Siqi_Leaders_0032_Modifiers.sql` 行 1723 + 1729
  - `MODIFIER_SIQI_P0032_TRAVELER_ERA_COMBAT_READER` → Key = `SIQI_P0032_TRAVELER_EraCombat`

## 常见错误

1. **Key 写成 Amount** — 固定值用 `Amount`，读 Property 用 `Key`。两者互斥
2. **跳过 Grant Ability，直接从 TraitModifiers 挂 Combat Reader** — `COLLECTION_UNIT_COMBAT` 需要单位级 Owner，Player 层挂不上去
3. **以为 `MODIFIER_PLAYER_UNITS_ADJUST_PROPERTY` 是标准类型直接使用** — ⚠️ **不存在**（DB 实测）。必须先自定义（Types + DynamicModifiers，见 Step 1）。历史教训：旧版本文件曾错误标注为标准类型，已修正
4. **Ability TypeTag 用自定义 CLASS** — 用 `CLASS_ALL_COMBAT_UNITS`（标准）即可
