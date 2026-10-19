# Leader Authoring — 新领袖编写指南

> 本文只讲**领袖**这一内容类型。文明见 `civilization-authoring.md`；
> 议程与领袖 AI 见 `agenda-authoring.md`；玩法逻辑见 `gameplay-lua.md`。

## 你要写哪几张表

列名**全部取自 `database/DebugGameplay.sqlite` / `database/DebugConfiguration.sqlite` 实测**：

| 表 | 库 | 全列 | 必需 |
|---|---|---|---|
| `Leaders` | gameplay | `LeaderType`, `Name`, `OperationList`, `IsBarbarianLeader`, `InheritFrom`, `SceneLayers`, `Sex`, `SameSexPercentage` | `LeaderType` / `Name` |
| `LeaderTraits` | gameplay | `LeaderType`, `TraitType` | 至少 1 行（领袖能力） |
| `CivilizationLeaders` | gameplay | `LeaderType`, `CivilizationType`, `CapitalName` | ★ **必需**——领袖与文明的关联就在这张表 |
| `LeaderQuotes` | gameplay | `LeaderType`, `Quote`, `QuoteAudio` | 可选（首次见面的名言） |
| `Players` | **Config** | 见下表 | ★ 选人界面/游戏设置界面靠它 |
| `PlayerItems` | **Config** | `Domain`, `CivilizationType`, `LeaderType`, `Type`, `Name`, `Description`, `Icon`, `SortIndex` | 特色项列表（★ 准入规则见下方小节） |

### `Players` 全列（Config 库，18 列）

```
Domain, CivilizationType, LeaderType, LeaderName, LeaderIcon,
CivilizationName, CivilizationIcon,
LeaderAbilityName, LeaderAbilityDescription, LeaderAbilityIcon,
CivilizationAbilityName, CivilizationAbilityDescription, CivilizationAbilityIcon,
Portrait, PortraitBackground, PlayerColor, HumanPlayable, SortIndex
```

★ `Domain` 常见值 `Players:Expansion2_Players`（对应 `ActionCriteriaData` 里的
`<LeaderPlayable>Players:Expansion2_Players::LEADER_X</LeaderPlayable>`）。

### `PlayerItems` 准入规则（选人界面特色物品清单，Config 库）

只收有实质 TRAIT 链的特色物品，三个条件缺一不可：

1. **主体限四类**——`Type` 填 `Districts` / `Units` / `Buildings` / `Improvements`
   四张主表里的行。原版全表实测（`database/DebugConfiguration.sqlite → PlayerItems`，
   113 条去重 `Type`）只有这四类，没有任何 RESOURCE 等其它主体。
2. **InGame 有实质 TRAIT 链**，二选一：
   - `物品-TRAIT-文明-领袖`：主表 `TraitType` → `CivilizationTraits` 关联到文明，
     领袖经 `CivilizationLeaders` 挂该文明即继承；
   - `物品-TRAIT-领袖`：主表 `TraitType` → `LeaderTraits` 直接挂在领袖身上
     （多领袖共享的通用特色单位也走这条）。
   - 主表 `TraitType` 必须指向衍生 trait（如 `TRAIT_CIVILIZATION_X_IMPROVEMENT`），
     文明/领袖能力主体的主 trait 禁止作为特色物品的 `TraitType`；衍生 trait 的
     `Traits.Name / Description` 一律 `NULL`。
3. **链路在 InGame（gameplay）库成立**——`CivilizationTraits` / `LeaderTraits` 都是
   gameplay 表；Config 侧的 `PlayerItems` 行只是前端展示，写错不报错，
   后果是选人界面出现不该出现的条目（或指向悬空）。

不符合的不入列：资源（`Resources` 表无 `TraitType` 列，无法成链——初始赠送资源靠
Modifier 实现，属于能力效果，不属于特色物品）、**项目（`Projects` 表无 `TraitType` 列，同理无法成链，
官方 421 行 `PlayerItems` 的 `KIND_PROJECT` 计数为 0）**、纯修饰符产物、无主表行的抽象概念。

本规则已机械化为 `scripts/rgn_validate_runner.mjs` 的「FrontEnd 清单资格」一节：它在 Config 库副本上
清空 `PlayerItems`、重放项目 SQL、把 Gameplay 快照的 `TraitType` / `LeaderTraits` / `CivilizationTraits`
复制进来做跨库查询，逐行判定主体类型、`TraitType` 是否为空、是否关联到本行领袖或文明。违规时退出码 1。

实测范例（今州文明包，链路逐件核验过）：眠龙庭 / 岁先知 / 黄岚建筑 / 早市改良走
`TraitType=TRAIT_CIVILIZATION_JINZHOU_*` → `CivilizationTraits`；阿漂（漂泊者通用单位）
走 `TraitType=TRAIT_ROVER_QYQXP` → `LeaderTraits`。同一文明的多领袖各自维护一份
`PlayerItems` 行集，共享套装重复列出属正常做法。

## 命名规则：领袖变量必须带项目级后缀

`LEADER_*` 与 `AGENDA_*`、领袖专属 `TRAIT_*` 的末尾段必须带项目级后缀（如 _SNZ），
防止与其他 mod 的领袖 Type 冲突；领袖的 tag（人名、加载语、百科、外交语音槽位）完整继承该后缀。

| 示例 | 说明 |
|---|---|
| `LEADER_RGN_Y` | 领袖 Type |
| `LOC_LEADER_RGN_Y_NAME` | 领袖名 tag（选人界面 `Players.LeaderName`） |
| `LOC_LOADING_INFO_LEADER_RGN_Y` | 加载界面领袖语 |
| `LOC_PEDIA_LEADERS_PAGE_LEADER_RGN_Y_QUOTE` | 领袖百科名言 |
| `LOC_DIPLO_FIRST_MEET_LEADER_RGN_Y_ANY` | 外交语音槽位 |
| `AGENDA_RGN_Z` / `LOC_AGENDA_RGN_Z_NAME` | 议程 Type 与其 tag |

- 项目另有领袖/文明变量后缀约定的，以本项目 **AGENTS.md** 为准。
- AI **不参与**领袖 Type 本身的格式纠正（见 AGENTS.md「用户自拟命名空间」）；只保证定义-引用闭合。
- 同文明多领袖共享一个文明后缀，各领袖后缀各自独立（如 `LEADER_RGN_Y` 与 `LEADER_RGN_Z`）。

## 「挂新文明」vs「leader-only 挂已有文明」

两者**差别只在 `CivilizationLeaders.CivilizationType` 指向谁**：

| 情形 | `CivilizationType` 指向 | 还要额外做什么 |
|---|---|---|
| 领袖 + 新文明（同一 mod） | 本 mod 新建的 `CIVILIZATION_*` | 另写文明那套表（见 `civilization-authoring.md`） |
| **leader-only**（挂到游戏已有文明，如中国） | 官方既有 `CIVILIZATION_CHINA` | **不要**写 `Civilizations` 行；只写 `Leaders` + `LeaderTraits` + `CivilizationLeaders` + `Players` |

leader-only 时 `Leaders.InheritFrom` 常指向该文明的原版领袖（或 `LEADER_DEFAULT`），
用于继承默认行为；具体取哪个以原版同文明领袖为准，**不要凭猜**。

## `Portrait` / `PortraitBackground`（★ 本类最容易误伤的两列）

这两列是**自由字符串**，指向 XLP 条目名（贴图名），**没有任何格式要求**；
留空合法，但**会触发引擎回退**（见下）——留空 ≠ 安全。

- **原版环境（必需）**：`PlayerSetupLogic.lua:807-829` 读这两列交给 `LeaderImage` / `LeaderBG`：
  `Portrait` 空 → 回退 `<LeaderType>_NEUTRAL`；`PortraitBackground` 空 → 回退 `<LeaderType>_BACKGROUND`。
  **mod 领袖通常没有这两个回退名 → 控件空白且前端不报错**（最常见的静默失败）。
  自建写 `PORTRAIT_<KEY>_BACKGROUND`（竖版 328×935，控件尺寸），
  或别名复用原版 `LEADER_<别的领袖>_BACKGROUND`（见下）。
  ★ **素材本身即 1:2.85 竖条**（placard 形，与 `LeaderBG` 控件 328×935 同比）时，
  `Portrait` 写**显式空串 `''`**（空白前景 + 铺满背景）；此规则**只管环境 A**，
  加载界面（B）的 `ForegroundImage` 不受影响，仍取 `LEADER_<KEY>_NEUTRAL`。
  ★ **完整规格（含 328×935 推导、加载界面、色调近似选型）见
  `civ6-asset-forge/reference/frontend-portrait.md`。**
- **第三方 2D 选人界面适配（可选分支）**（如 Sukritact's Civ Selection Screen）：
  界面同样读这两列，但只在 Suk 启用时生效（`Criteria` 门控）。
  **Suk 是可选分支；原版 FrontEnd 才是必需。** 适配做法是
  `UPDATE Players SET Portrait=…, PortraitBackground=…`（挂在 FrontEndActions）。

★ **命名铁律**：第三方界面适配素材**不得借用官方模板前缀**
（`FALLBACK_` = 官方 3D 回退 = `Leader_Fallback` 类）。走独立命名空间
`<适配对象短名>_UI_<KIND>_<KEY>`，例如 `SUK_UI_PORTRAIT_<KEY>` / `SUK_UI_BACKGROUND_<KEY>`。
理由、改名的实测前提与迁移工具见 `civ6-asset-forge/reference/ui-leader-portrait.md` §4.4。

★ 改这两列后**贴图必须在 `UITexture` 类 XLP 里登记**，否则不进 BLP → 界面空白
（cook 不报错）。校验：
- 原版环境（A 选人 + B 加载界面）：`civ6-asset-forge/scripts/verify_frontend_portrait.py --project <工程根>`
- Suk 分支：`civ6-asset-forge/scripts/verify_suk_portrait.py --project <工程根>`

★ **环境归属**：`Players` 属 **Config 库** → 写进 `FrontEndActions → UpdateDatabase`；
而加载界面的 `LoadingInfo`（`ForegroundImage` / `BackgroundImage`）属 **Gameplay 库** →
写进 `InGameActions → UpdateDatabase`。写错段会 `no such table`。
FrontEnd 动作的门控只挂 `ModInUse`，**勿挂 `GameCoreInUse`**——FrontEnd 下恒不成立，
动作静默跳过，症状就是选人界面看不到领袖（`gotchas.md` §74）。
三套环境（选人 / 加载界面 / 外交）对照见 `civ6-asset-forge/reference/frontend-portrait.md` §〇。

## 文本：必须走 `UpdateText`

同文明：`.modinfo` 的 `<LocalizedText>` 只管 mod 列表界面，**游戏内文本必须经
`UpdateText` 加载 `Text/*.sql`**（详见 `gotchas.md`「本地化文本通道」）。

文本 tag 一律由完整领袖变量名 `LEADER_<ID>`（含项目级后缀）推导，派生 tag 必须继承完整变量名，不得截断为裸名。

**语音 7 条**（quote 经 `LeaderQuotes.QuoteAudio` 配语音；六条外交语音由 `Speech.bnk` 事件判定）：

```
LOC_PEDIA_LEADERS_PAGE_LEADER_<ID>_QUOTE          加载界面名言（配 LeaderQuotes.Quote）
LOC_DIPLO_FIRST_MEET_LEADER_<ID>_ANY               初次见面
LOC_DIPLO_DECLARE_WAR_FROM_HUMAN_LEADER_<ID>_ANY   人类玩家宣战
LOC_DIPLO_DECLARE_WAR_FROM_AI_LEADER_<ID>_ANY      AI 宣战
LOC_DIPLO_KUDO_EXIT_LEADER_<ID>_ANY                议程正面回应
LOC_DIPLO_WARNING_EXIT_LEADER_<ID>_ANY             警告后告别
LOC_DIPLO_DEFEAT_FROM_AI_LEADER_<ID>_ANY           战败台词
```

**必填文本**（`LOC_TRAIT_<ID>_*` 这类 tag 归 `Text_Config_*` 文件；`LOC_LOADING_INFO_LEADER_<ID>` 是开幕颂词，写 100 字上下的完整长句，禁止只写称号）：

```
LOC_LEADER_<ID>_NAME                      领袖名
LOC_LEADER_<ID>_DESCRIPTION               称号（写 Text_Config）
LOC_TRAIT_<ID>_NAME                       能力名
LOC_TRAIT_<ID>_DESCRIPTION                能力说明（写 Text_Config，配 Players.LeaderAbilityDescription）
LOC_LOADING_INFO_LEADER_<ID>              开幕颂词
LOC_AGENDA_<ID>_NAME / DESCRIPTION        议程名与可见描述
```

★ **两端独立**：FrontEnd 与 InGame 是两套独立的 LocalizedText 环境，`<UpdateText>` 只对它注册的那一端生效。`Text_Config_*` 的 tag 被哪一端引用，就在哪一端注册；两端都引用时必须两端各注册一次。引用闭合按端分别核对，InGame 侧跑 `rgn_validate`，FrontEnd 侧对照 `DebugConfiguration.sqlite` 检查 `Players`/`PlayerItems`，不能让某一端的结果覆盖另一端。

**无语音外交文本**（可选补齐，按黑海岸标准；tag 后缀统一为 `_LEADER_<ID>_ANY`）：

```
LOC_DIPLO_FIRST_MEET_VISIT_RECIPIENT_LEADER_<ID>_ANY
LOC_DIPLO_FIRST_MEET_NO_MANS_INFO_EXCHANGE_LEADER_<ID>_ANY
LOC_DIPLO_FIRST_MEET_NEAR_INITIATOR_POSITIVE_LEADER_<ID>_ANY
LOC_DIPLO_GREETING_LEADER_<ID>_ANY
LOC_DIPLO_DECLARE_FRIEND_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_ACCEPT_DECLARE_FRIEND_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_REJECT_DECLARE_FRIEND_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_ACCEPT_DECLARE_FRIEND_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_REJECT_DECLARE_FRIEND_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_DELEGATION_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_ACCEPT_DELEGATION_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_REJECT_DELEGATION_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_OPEN_BORDERS_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_ACCEPT_OPEN_BORDERS_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_REJECT_OPEN_BORDERS_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_MAKE_ALLIANCE_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_ACCEPT_MAKE_ALLIANCE_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_MAKE_PEACE_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_MAKE_PEACE_AI_ACCEPT_DEAL_LEADER_<ID>_ANY
LOC_DIPLO_MAKE_PEACE_AI_REFUSE_DEAL_LEADER_<ID>_ANY
LOC_DIPLO_ACCEPT_MAKE_DEAL_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_REJECT_MAKE_DEAL_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_DENOUNCE_FROM_HUMAN_LEADER_<ID>_ANY
LOC_DIPLO_DENOUNCE_FROM_AI_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_TOO_MANY_TROOPS_NEAR_ME_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_TOO_MANY_TROOPS_NEAR_ME_AI_RESPONSE_POSITIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_TOO_MANY_TROOPS_NEAR_ME_AI_RESPONSE_NEGATIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_SPYING_ON_ME_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_SPYING_ON_ME_AI_RESPONSE_POSITIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_SPYING_ON_ME_AI_RESPONSE_NEGATIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_DIGGING_UP_ARTIFACTS_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_DIGGING_UP_ARTIFACTS_AI_RESPONSE_POSITIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_DIGGING_UP_ARTIFACTS_AI_RESPONSE_NEGATIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_CONVERTING_MY_CITIES_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_CONVERTING_MY_CITIES_AI_RESPONSE_POSITIVE_LEADER_<ID>_ANY
LOC_DIPLO_WARNING_STOP_CONVERTING_MY_CITIES_AI_RESPONSE_NEGATIVE_LEADER_<ID>_ANY
```

不补上表之外的 no-voice 外交 tag，尤其不生成 `LOC_DIPLO_DEFEAT_FROM_HUMAN_*`（六个外交槽位无此语音）。

**禁止生成的 tag**：

```
LOC_DIPLO_QUOTE_*                        原版 0 条，quote 只走 LOC_PEDIA_LEADERS_PAGE_LEADER_<ID>_QUOTE
LOC_DIPLO_ATTACKED_*                     原版 0 条
LOC_DIPLO_DEFEAT_FROM_HUMAN_*           无语音槽位
LOC_TRAIT_AGENDA_<ID>_*                  衍生 trait 不生成 NAME/DESCRIPTION（Traits 两列 NULL）
LOC_AGENDA_<ID>_DESCRIPTION_HIDDEN       原版 0 条
```

`LocalizedText` 实列：`Language, Tag, Text, Gender, Plurality`。

所有衍生 trait（特色物品专用、议程）的 `Traits.Name / Description` 都必须是 `NULL`，
也只有主 trait 才生成 `LOC_TRAIT_*_NAME` / `LOC_TRAIT_*_DESCRIPTION`。

## 代码/配置怎么写

用 `tools/civ_leader_data.py` 从规格 JSON 机械推导（**不要手写这些行**）：

```bash
python tools/civ_leader_data.py reference/civ-leader-spec.example.json \
       --project <工程根> --write
```

产出 `Data/CivLeader_<Slug>.sql` + `Data/Config_<Slug>.sql` + `Text/Text_<Slug>.sql`，
并自检 LOC tag 闭包、8 语言齐缺、`Portrait` 未登记 XLP 告警。

三个 `.sql` 目标文件不存在时脚本新建直写；任一已存在且内容有变化时，改写结果落到
`<解决方案根>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时
打印待写入清单。

`leaders[]` 里支持 `civilization` 字段指定挂靠文明；与本规格的 `civilization.type`
不一致时会告警提示"确认这是 leader-only"。

## 与其它 skill 的分工（**不在本文重复**）

| 内容 | 去哪 |
|---|---|
| 领袖图标（32/45/48/50/55/64/80/256）、2D 立绘与选人界面背景 | **`civ6-asset-forge`** skill |
| 3D 场景 / 引用原版领袖模型 / `Leaders.artdef`·XLP 链 | **`civ6-art-reference`** skill |
| 领袖语音、BGM | **`civ6-audio-pipeline`** skill |
| 议程（`Agendas` / 领袖 AI 偏好） | `agenda-authoring.md` |
| 领袖能力（Trait/Modifier）实现 | `modifiers-cheatsheet.md` / `gameplay-lua.md` |
| 发布上工坊 | `release.md` |

## 验证顺序

```bash
python tools/modinfo_build.py <X.civ6proj> --deploy   # 派生 modinfo + 引用闭合自检
node scripts/rgn_validate_runner.mjs <Data 目录>      # SQL 引用完整性
python scripts/check_proj_content.py                  # Content 清单双向闭合
```

进游戏复核（静态校验答不了"选人界面到底显不显示"）：
`civ6-tuner` skill 可在运行中的对局里直接读 `Players` 行与控件状态。

## 未核实项（用前请自行确认）

- `Leaders.InheritFrom` 的官方取值域、`SceneLayers` 的写法：本文只给出列名，
  **未核实**取值含义与合法范围。
- `SameSexPercentage` 的取值范围：**未核实**。
