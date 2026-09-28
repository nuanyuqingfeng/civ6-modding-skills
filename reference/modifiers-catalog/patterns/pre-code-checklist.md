# 修改器实现前清单

适用于手写修改器 SQL 与自定义 SQL 补丁。先读本目录 [INDEX](INDEX.md) 与
[通用技巧](../modifier-techniques.md)；参数签名用 `database/scripts/query_effect_args.py` 查，
原版实现用 `database/scripts/search_impl.py` 反查。

## 1 查证来源

- [ ] 已读最接近的 [模式](INDEX.md) 或 [案例](../cases/INDEX.md)，说明本任务沿用什么、改变什么。
- [ ] ModifierType 按 [资料依据](../../../SOURCES.md)「类型与枚举」口径（`source_index.sqlite` 行级来源）核实为原版；其他 Mod 中使用过只能作为线索，不能当作原版依据。
- [ ] 新类型确有必要，CollectionType/EffectType 已核实，并确认随 Mod 提供 `Types`/`DynamicModifiers` 注册行。
- [ ] RequirementType 与参数已按 [资料依据](../../../SOURCES.md) 核实；搜索无结果时没有直接编造类型。

## 2 建立链路

- [ ] 列出外层/内层 Modifier、条件集、Ability 及挂载表；ATTACH 的 ModifierId 和 GrantAbility 的 AbilityType 指向真实条目。
- [ ] 分别说明 owner / subject 指向哪个游戏对象，玩家、城市、地块条件使用正确上下文。
- [ ] 事件类 Requirement 按真实语义填写 Triggered；不把 Inverse 与 Triggered 当作可互换的列。
- [ ] SQL 显式写列名并对照表结构；工程登记走 `UpdateDatabase` 类动作（划分与 LoadOrder 纪律见 `civ6-modding/reference/action-splitting.md`）。

## 3 文本与验证

- [ ] 每个 `EFFECT_ADJUST_PLAYER_STRENGTH_MODIFIER` 必写 `ModifierStrings`（Preview）；同批提供对应 LOC 文本行。
- [ ] 占位符 `{1_Amount}`（固定数值）/ `{Property}`（Key 属性）正确，不能照抄旧模板的 `{Amount}`。
- [ ] 其他效果不机械添加 ModifierStrings；支持范围见 [通用技巧](../modifier-techniques.md)。
- [ ] 标准验证顺序（`check_sql_exec` / `check_types_kinds` / `rgn_validate`，见 `scripts/README.md`）已执行；结构校验与游戏内效果分别说明。
