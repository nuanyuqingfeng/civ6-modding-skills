# 实现模式索引

> 每个模式包含完整表链路、列序、标准 ModifierType 清单、与已有 Mod 的对照示例。
> 写代码前先查对应模式，**复制链结构，只改 Type 名和数值**，不要凭理解重写。

## 模式速查

| # | 模式 | 适用场景 | 已有参考 Mod |
|---|------|---------|-------------|
| A | [通用Trait ATTACH → 动态效果](pattern-attach-generic-trait.md) | 每存活文明/城邦/城市 的战斗力/移动力/产出 | 0045, 0032 |
| B | [Property → 战斗力/Move via Grant Ability](pattern-property-combat.md) | Property 累加后转为战斗力或移动力 | 0032 |
| C | [手动遍历多层次 ATTACH](pattern-tiered-traversal.md) | 按人口/时代/城市数 分档给不同效果 | 0045, 0032 |
| D | [建城一次性效果](pattern-city-founding.md) | 建城+地块/+人口 | 0045 |
| E | [区域效果（槽位/生产/替换）](pattern-district-effects.md) | 区域建筑生产力/政策槽位增减/槽位替换 | 0045 |
| F | [UnitAbility → 多层 Modifier](../cases/case-grant-ability.md) | 单位光环/战斗Buff/治疗/禁止攻击（5层链路详解见 case） | 0045, 0032 |
| G | [送单位（建城/首都/区域/补员）](pattern-grant-unit.md) | 送单位/获得单位/建城送/首都送/首城送/区域建成送/补员 | 0039, 0043, 0046, 0053 |

## 通用规则（所有模式适用）

- Modifiers 列序：`(ModifierId, ModifierType, SubjectRequirementSetId, RunOnce, Permanent)`
- Requirements 列序：`(RequirementId, RequirementType, Inverse)`
- ModifierId 命名：`MODIFIER_SIQI_00XX_` 前缀，描述效果和条件
- 写任何 INSERT 前验证 ModifierType 是否已在 DynamicModifiers 中存在

## 写码前检查清单

- **[pre-code-checklist.md](pre-code-checklist.md)** — 逐项确认列序/标准Type/参数名（写 Modifier SQL 前必过）
