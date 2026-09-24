# 议程与领袖 AI 行为编写（Agenda & Leader AI Authoring）

> 何时读：要给领袖写议程（好感/偏好行为）、写外交好感修饰符、或补齐领袖 AI 偏好（造兵/奇观/科技优先级）时。
> 本文全部结论来自原版 XML + `DebugGameplay.sqlite` 实测核对，非推测。

## 一、决策先行

```
要加议程 / 领袖 AI？
├─ 只要名字 + 描述（纯风味）        → 只注册 Agendas（不写 Modifiers）
├─ 要好感行为（喜欢/讨厌某类文明）  → Agendas → AgendaTraits → TraitModifiers → Modifiers
└─ 要 AI 决策偏好（造兵/奇观/科技） → AiListTypes + AiLists + AiFavoredItems
                                      （与上面正交，两套可同时写，互不依赖）
```

## 二、机制链

```
Agendas(AgendaType)
  └─ AgendaTraits(AgendaType → TraitType)
       └─ TraitModifiers(TraitType → ModifierId)
            └─ Modifiers(ModifierId, ModifierType, SubjectRequirementSetId)
                 └─ ModifierArguments(InitialValue / StatementKey / SimpleModifierDescription / HiddenAgenda ...)
                      └─ RequirementSets → RequirementSetRequirements → Requirements → RequirementArguments
```

**唯一需要的 ModifierType**：`MODIFIER_PLAYER_DIPLOMACY_SIMPLE_MODIFIER`（base 内置，原版 156 条议程在用）。
EffectType=`EFFECT_PLAYER_DIPLOMACY_SIMPLE_MODIFIER`，CollectionType=`COLLECTION_MAJOR_PLAYERS`。

| ModifierArguments | 作用 | 取值惯例 |
|---|---|---|
| `InitialValue` | 好感（正）/ 恶感（负） | **原版主流 ±6**；±8 属个别特例 |
| `StatementKey` | 触发哪句外交辞令 | `LOC_DIPLO_KUDO_*` / `LOC_DIPLO_WARNING_*` |
| `SimpleModifierDescription` | 外交界面显示的理由 | `LOC_DIPLO_MODIFIER_DESCRIPTION_*` |
| `HiddenAgenda` | `1` = 隐藏议程（不显示名字/描述） | 显式议程则省略 |
| `ReductionTurns` / `ReductionValue` | 每 N 回合衰减 M 点 | 事件型议程（如「解放城市」）用 |

## 三、第一步永远是查原版原型

禁止凭空设计。先找到语义最接近的原版议程，读它的完整链：

```sql
-- 1) 议程挂什么特性
SELECT TraitType FROM AgendaTraits WHERE AgendaType='AGENDA_XXX';
-- 2) 特性挂哪些修饰符
SELECT ModifierId FROM TraitModifiers WHERE TraitType='TRAIT_AGENDA_XXX';
-- 3) 修饰符类型 + 需求集 + 全部参数
SELECT ModifierType, SubjectRequirementSetId, OwnerRequirementSetId FROM Modifiers WHERE ModifierId='...';
SELECT Name, Value FROM ModifierArguments WHERE ModifierId='...';
-- 4) 需求集内部（每一层都要看）
SELECT * FROM RequirementSetRequirements WHERE RequirementSetId='...';
SELECT * FROM Requirements WHERE RequirementId='...';
SELECT Name, Value FROM RequirementArguments WHERE RequirementId='...';
```

**原版文件位置**：`Base/Assets/Gameplay/Data/Agendas.xml`（议程本体）、`Leaders.xml`（领袖级）、`DiplomaticActions.xml`（外交行为偏好）、`DLC/Expansion1|2/Data/Expansion*_Agendas.xml`。

**DLC 依赖识别**：某议程/需求集若只出现在 `DLC/<某包>/` 下，就是该 DLC 专属 —— 不可直接引用。常见踩坑：`AGENDA_PERPETUALLY_ON_GUARD`(澳)、`AGENDA_SAINT`(波兰)、`AGENDA_AMBIORIX_ARMY`(拜占庭高卢)、`PLAYER_NOT_AT_WAR_WITH_NEIGHBORS`(R&F/Expansion1)。

## 四、需求集（reqset）规则 —— 最硬的一条

| 情况 | 做法 |
|---|---|
| 原版 reqset 组成**完全符合**所需条件 | 直接复用 |
| 组成**多一条**条件（如原版强制 `REQUIRES_MET_30_TURNS_AGO`） | **自建** `REQSET_<模块>_<作用>` |
| 原版 reqset 属 **R&F(Expansion1) 或 DLC** | **必须自建**（否则隐式 DLC 依赖） |

- 自建内部**只用 base RequirementType**（`REQUIREMENT_CIVILIZATION_LEVEL` / `REQUIREMENT_PLAYER_MET_X_TURNS_AGO` / `REQUIREMENT_PLAYER_AT_WAR_WITH_NEIGHBOR` / `REQUIREMENT_CITY_LIBERATED` / `REQUIREMENT_CITY_OCCUPIED` / `REQUIREMENT_PLAYER_YIELD_LEAD` / `REQUIREMENT_PLAYER_MILITARY_STRENGTH_LEAD` 等）。
- 只抄「需求项」四张表：`RequirementSets` + `RequirementSetRequirements` + `Requirements` + `RequirementArguments`。
  **不需要**再 `INSERT INTO Types` —— RequirementType 是引擎枚举，非注册对象。
- 取反用 `Inverse=1`（例：`REQUIREMENT_PLAYER_AT_WAR_WITH_NEIGHBOR` + `Inverse=1` = 不与邻国交战）。

常用 base reqset 速查（可直接复用）：

| reqset | 判据 | 常用参数 |
|---|---|---|
| `PLAYER_CITY_LIBERATED` | 解放过城市 | `OnlyOwnersCity=0`，`Triggered=1` |
| `PLAYER_CITY_OCCUPIED` | 有占领城市 | — |
| `PLAYER_HAS_HIGH/LOW_STANDING_ARMY` | 陆军强度领先/落后 | `DomainType=DOMAIN_LAND`, `MinimumDelta=5`, `StrengthRatio=±1.2` |
| `PLAYER_HAS_HIGH/LOW_CULTURE` | 文化领先/落后 | `YieldType=YIELD_CULTURE`, `YieldRatio=±1.15` |
| `PLAYER_HAS_HIGH/LOW_FAITH` | 信仰领先/落后 | `YieldType=YIELD_FAITH` |
| `PLAYER_IS_MAJOR_CIV` / `_KNOWN_10_TURNS` / `_KNOWN_30_TURNS` | 主要文明 + 已见面 N 回合 | — |

## 五、注册顺序（全部 `INSERT OR REPLACE`，幂等）

> ⚠️ **这里的「顺序」指同一个 SQL 文件内 `INSERT` 语句的先后（表内插入序），不是加载动作的顺序。**
> 加载动作的划分与排序是另一回事 —— 见 `reference/action-splitting.md`。

写 `.civ6proj` 的 `UpdateDatabase` 清单也在其中：

1. `Types` — 新 Trait 需 `('TRAIT_X','KIND_TRAIT')`；新 Agenda 通常只注册 Trait 的 Kind
2. `Traits` — `('TRAIT_X', NULL, NULL)`
3. `Agendas` — `(AgendaType, Name, Description)`
4. `AgendaTraits` — 议程 → 特性
5. `HistoricalAgendas` — `(LeaderType, AgendaType)`，**主键只有 LeaderType**（一个领袖一条）
6. `TraitModifiers` — 特性 → ModifierId
7. `Modifiers` — `(ModifierId, ModifierType, SubjectRequirementSetId)`
8. `ModifierArguments` — 逐条 `(ModifierId, Name, Value)`
9. `ModifierStrings` — `(ModifierId, 'Sample', 'LOC_TOOLTIP_SAMPLE_DIPLOMACY_ALL')`
10. reqset 四表（自建时）
11. `.civ6proj` → `<UpdateDatabase>` 加 `<File>Data/Xxx_RGN.sql</File>`

## 六、文案规范

对齐原版 `议程表(绝大部分).xlsx` 模板风格（**这就是原版 Agendas 描述的真实句式**）：

- **直陈「喜欢…，讨厌…」**，单句或双句。**不要写成文学段落**（原版最长约 2 句）。
- 通用理由**直接复用 base**：`LOC_DIPLO_MODIFIER_DESCRIPTION_HIGH/LOW_CULTURE`、`_HIGH/LOW_FAITH`、`_HIGH_STANDING_ARMY`、`LOC_DIPLO_MODIFIER_LIBERATED_CITY` …（句式「他们…」）
- 无对应概念才自写，**沿用同一「他们…」句式**。
- **辞令（StatementKey）必须按领袖各写** —— base 辞令带原版角色第一/二人称口吻（如「愿您永享和平」），跨角色复用会串味。
- 文本落到**该领袖自己的文本文件**，用**元组级替换**，**只增不覆**既有外交文本。

## 七、领袖 AI 偏好（28 个 System）

`AiLists(LeaderType=<领袖特性>, System=<系统名>)` + `AiFavoredItems(ListType, Item, Favored, Value)`。
**锚点是「领袖特性」** —— 引擎按领袖拥有的 Trait 解析，`LeaderType` 不参与匹配。

常用 10 个 System 与 Item 前缀：

| System | Item 前缀 | 典型值 / 条数 |
|---|---|---|
| `Strategies` | `VICTORY_STRATEGY_{CULTURAL,RELIGIOUS,MILITARY,SCIENCE,DIPLOMATIC}_VICTORY` | `Favored=1` |
| `Yields` | `YIELD_*` | `±20 / ±25` |
| `PseudoYields` | `PSEUDOYIELD_*` | `±25 / 50 / 100` |
| `Technologies` / `Civics` | `TECH_*` / `CIVIC_*` | 各 5–6 条 |
| `Buildings`（奇观） / `Districts` / `Units` | `BUILDING_*` / `DISTRICT_*` / `UNIT_*` | `Favored=0` 表规避 |
| `Discussions` | `WC_EMERGENCY_*` | 世会议题取向 |
| `Alliances` | `DIPLOACTION_ALLIANCE_*` | 同盟类型 |

其余 System（了解即可）：`Resolutions`、`PlotEvaluations`、`SettlementPreferences`、`CityEvents`、`AiOperationTypes`、`PerWarOperationTypes`、`Homeland`、`Commemorations`、`Tactics`、`TechBoosts`、`SavingTypes`、`UnitPromotionClasses`、`AiBuildSpecializations`、`AiScoutUses`、`Projects`、`YieldSensitivities`、`TriggeredTrees`、`DiplomaticActions`、`Agendas`。

**复用原版胜利路线偏好**：直接给领袖 `LeaderTraits` 挂 base 特性即可，无需自建 ListType：

| 特性 | 效果 |
|---|---|
| `TRAIT_LEADER_CULTURAL_MAJOR_CIV` | 偏好文化胜利 |
| `TRAIT_LEADER_RELIGIOUS_MAJOR_CIV` | 偏好宗教胜利 |
| `TRAIT_LEADER_SCIENCE_MAJOR_CIV` | 偏好科技胜利 |
| `TRAIT_LEADER_PURSUE_DIPLOMATIC_VICTORY` | 偏好外交胜利 |
| `TRAIT_LEADER_AGGRESSIVE_MILITARY` | 军力伪产出加权 |
| `TRAIT_LEADER_EXPANSIONIST` | 扩张定居偏好 |
| `TRAIT_LEADER_LOW_RELIGIOUS_PREFERENCE` | 压低宗教倾向 |

**「见面即可宣布友谊」**：不是议程效果，而是外交行为偏好（原版吉尔伽美什写法）：

```sql
INSERT OR REPLACE INTO AiListTypes (ListType) VALUES ('XxxDiplomacy');
INSERT OR REPLACE INTO AiLists (ListType, AgendaType, System)
  VALUES ('XxxDiplomacy', 'TRAIT_AGENDA_XXX', 'DiplomaticActions');
INSERT OR REPLACE INTO AiFavoredItems (ListType, Item, Favored, Value)
  VALUES ('XxxDiplomacy', 'DIPLOACTION_DECLARE_FRIENDSHIP', 1, 0);
```
注意 `AiLists` 主键为 `(ListType, LeaderType, AgendaType)` —— **一个 ListType 只能绑一个 AgendaType**，多领袖需各建一个 ListType。

## 八、验证（缺一不可）

```bash
node scripts/rgn_validate_runner.mjs <工程目录>/Data "*.sql" true   # 悬空引用必须 0
```

外加三项自查：

1. **Item 存在性** — 每个 `AiFavoredItems.Item` 必须在对应 base 表存在（`Technologies`/`Civics`/`Buildings`/`Districts`/`Units`/`PseudoYields`/`Yields`）。
2. **文本闭合** — 每个 `LOC_*` 引用的 tag 有定义（工程内或 base）。
3. **文件规范** — CRLF；既有内容逐字节未变（追加后 `assert new.startswith(old)`）。

## 九、踩过的坑（实测血泪）

1. **绝不用 heredoc / 编辑器直接批量写含中文的 SQL** —— 实测会被静默改写（丢整行、削掉收尾引号）。用 **Python 脚本生成**，并**立刻回读校验**。
2. **同表已有注册块时勿重复写**；但**删除旧块前务必确认新块已含全部行** —— 曾因搬走 `HistoricalAgendas` 顺带删掉 5 条 `Agendas` 本体，导致**静默断链**（`INSERT OR REPLACE` 不报错）。
3. `INSERT OR REPLACE` 是**元组级覆盖**，同名 tag 会**静默改写**既有行 —— 改文本前先 `diff`。
4. **议程注册容易散落**：`Agendas`/`AgendaTraits`/`HistoricalAgendas` 常被写在 `Leaders_*.sql` 里；新增时应集中到一个 `Agendas_*.sql`，避免两份定义打架（尤其 `HistoricalAgendas` 主键只有 `LeaderType`，后加载者覆盖前者）。
5. **枚举名极易记错**：`BUILDING_TEMPLE_ARTEMIS`（非 `_OF_`）、`BUILDING_STATUE_LIBERTY`（非 `_OF_`）；`DRAMA_POETRY` 是 **Civic** 不是 Tech。写前必须查表。
6. **数值不要自创**：好感用 ±6、Yields 用 ±20/25、PseudoYields 用 ±25/50/100 —— 都是原版在用的档位。
