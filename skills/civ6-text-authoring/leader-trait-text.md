# 类 1 —— 领袖与文明等 trait 能力文本规范

> 覆盖 `LOC_LEADER_*` `LOC_CIVILIZATION_*` `LOC_TRAIT_*` `LOC_ABILITY_*` `LOC_AGENDA_*`
> `LOC_GOVERNOR_*` `LOC_CIVINFO_*` `LOC_UNIQUE_*`（语料 1,946 条）
> 语料：`reference/catalog/leader_trait.tsv` ｜ 查询：`zh_corpus.sqlite` `WHERE Category='leader_trait'`

## 1. 数据链（写文本前必须对上对象）

Civ6 的「能力」由三层构成，LOC tag 各自挂在不同层，**不可混用**：

```
Leaders.LeaderType
   ├─ LeaderTraits ─────────► TraitType(领袖特质) ─ TraitModifiers ─► Modifier
   │     LOC_TRAIT_LEADER_<TRAIT>_NAME / _DESCRIPTION
   └─ Agendas ─────────────► AgendaType
         LOC_AGENDA_<AGENDA>_NAME / _DESCRIPTION

Civilizations.CivilizationType
   └─ CivilizationTraits ──► TraitType(文明特质) ─ TraitModifiers ─► Modifier
         LOC_TRAIT_CIVILIZATION_<TRAIT>_NAME / _DESCRIPTION

Abilities.AbilityType / ModifierType
   LOC_ABILITY_<X>_NAME / _DESCRIPTION      （引擎能力，常由 trait 授予）

Governors / GovernorPromotions
   LOC_GOVERNOR_<GOV>_NAME / _DESCRIPTION
   LOC_GOVERNOR_PROMOTION_<PROMO>_NAME / _DESCRIPTION
```

> ⚠️ 领袖特质用 `LOC_TRAIT_LEADER_*`，**不是** `LOC_LEADER_TRAIT_*`。
> `LOC_LEADER_TRAIT_<X>_NAME` 在官方语料里是指**城邦宗主国加成**（如「阿卡德宗主国加成」），
> 不要拿它当领袖特质 tag 用。

## 2. 命名规范（tag 后缀）

| 后缀 | 用途 | 官方范式 |
|---|---|---|
| `_NAME` | 能力名（短，2–6 字，头条风格） | `LOC_TRAIT_CIVILIZATION_ALL_ROADS_TO_ROME_NAME` = 条条大路通罗马 |
| `_DESCRIPTION` | 能力效果说明（面向玩家的规则句） | `LOC_TRAIT_CIVILIZATION_ADJACENT_DISTRICTS_DESCRIPTION` = 当区域与区域相邻时，所有区域获得一个额外的标准相邻加成。 |
| `_DESCRIPTION`（**文明级**，即 `LOC_CIVILIZATION_<CIV>_DESCRIPTION`） | ⚠ **不是效果说明，而是该文明的正式全名 / 别称**（与 `_NAME` 同为专名，两者可以不同）；城邦写「<名>城邦」 | 官方：英国 `_NAME`=「英国」、`_DESCRIPTION`=「大英帝国」；中国 `_NAME`=「中国」、`_DESCRIPTION`=「中华帝国」；美国 `_DESCRIPTION`=「美利坚帝国」；城邦 `LOC_CIVILIZATION_AMSTERDAM_DESCRIPTION` =「阿姆斯特丹城邦」。**不要在这里写能力说明或风味社论**——该 tag 由文明条目的名称位消费，写成长句会直接显示成「文明描述」 |
| `_EXPANSION1_DESCRIPTION` / `_EXPANSION2_DESCRIPTION` | **规则集变体**：同一能力在不同资料片下的不同效果（全语料 33 / 100 条） | 见 §4 |
| `_FRONTEND_NAME` | 选人界面用短名（如 `LOC_CIVILIZATION_AMERICA_FRONTEND_NAME`） | 选人界面显示名 |
| `_ADJECTIVE` | 文明形容词（「美国的」「阿卡德的」），用于「{1_CivName}的……」拼接 | `LOC_CIVILIZATION_AMERICA_ADJECTIVE` |
| `_NAME_ALT` / `_SHORT_NAME` | 备用/短名（依对象而定） | — |

- tag 主体 `<X>` 用**全大写下划线**，与 `TraitType` / `AgendaType` / `AbilityType` 同名去掉前缀。

## 3. 描述写法规范

1. **一句一效果，用 `[NEWLINE][ICON_Bullet]` 分条**（多条效果时）：
   ```
   LOC_ABILITY_CONQUISTADOR_DESCRIPTION
   与宗教单位处于同一格位时+10 [ICON_Strength] 战斗力。[NEWLINE][ICON_Bullet]如果该单位占领城市……
   ```
2. **数值前置 + 图标紧跟数值**：`+3 [ICON_Strength] 战斗力`（战斗）、`+1 [ICON_Culture] 文化值`（产出）。
   正负号用半角 `+`/`-`，负值需 `[COLOR_RED]…[ENDCOLOR]` 包裹：
   ```
   LOC_ABILITY_AIR_BOMBER_ATTACK_UNIT_DEBUFF_DESCRIPTION = 对抗单位时 [COLOR_RED]-17 [ICON_Bombard][ENDCOLOR] 轰炸攻击力。
   ```
3. **条件前置**：先写触发条件（「当…时」「与…相邻时」「位于…」），后写结果。
4. **参数化**：可复用文案用 `{1_Amount}` 占位，不要写死数字（便于 modifier 传参）。
5. **议程**：用**第三人称描述 AI 偏好**（不是对玩家说话）：
   ```
   LOC_AGENDA_AMBIORIX_ARMY_DESCRIPTION = 喜欢拥有大量战斗单位的文明。讨厌军队规模小的文明。
   ```
   句式固定为「喜欢…。讨厌…。」两段式，与 AI 好感链（`agonize`/好感 Modifier）一一对应。
6. **文风**：能力名走「古典/意象」路线（明治维新、条条大路通罗马、政事论），描述走「规则句」路线；两者不混。

## 4. 规则集变体（风云变幻口径）

同一能力在 Expansion1/Expansion2 下效果不同时，**另开 `_EXPANSION1_DESCRIPTION` / `_EXPANSION2_DESCRIPTION`**，
基础 `_DESCRIPTION` 保持本体值 —— 引擎按启用的资料片选择对应 tag。

```
LOC_BELIEF_FEED_THE_WORLD_DESCRIPTION            （本体版）
LOC_BELIEF_FEED_THE_WORLD_EXPANSION2_DESCRIPTION = 每座神社和寺庙提供的 [ICON_FOOD] 食物+3、[ICON_HOUSING] 住房+2。
```

> 本 skill 语料已按 `EXP2>EXP1>base` 裁决；写新能力时若需兼容多资料片，照此三分法建 tag。

## 5. 校验清单

- [ ] 领袖特质 → `LOC_TRAIT_LEADER_*`；文明特质 → `LOC_TRAIT_CIVILIZATION_*`（勿把 `LOC_LEADER_TRAIT_*` 当领袖特质）
- [ ] `TraitType` 已在 `Types` 表注册（`KIND_TRAIT`），且 `LocalizedText` 的 tag 与其同名去前缀
- [ ] `_NAME` 与 `_DESCRIPTION` 成对存在，缺失 → 界面显示 tag 原文
- [ ] 多资料片效果差异已建 `_EXPANSION1/2_DESCRIPTION`
- [ ] `[ICON_x]` 名字合法（→ [icon-reference.md](icon-reference.md)）
- [ ] 跑 `python <civ6-modding>\scripts\check_text_refs.py <工程根>`
