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
| `PlayerItems` | **Config** | `Domain`, `CivilizationType`, `LeaderType`, `Type`, `Name`, `Description`, `Icon`, `SortIndex` | 特色项列表 |

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

## 「挂新文明」vs「leader-only 挂已有文明」

两者**差别只在 `CivilizationLeaders.CivilizationType` 指向谁**：

| 情形 | `CivilizationType` 指向 | 还要额外做什么 |
|---|---|---|
| 领袖 + 新文明（同一 mod） | 本 mod 新建的 `CIVILIZATION_*` | 另写文明那套表（见 `civilization-authoring.md`） |
| **leader-only**（挂到游戏已有文明，如中国） | 官方既有 `CIVILIZATION_CHINA` | **不要**写 `Civilizations` 行；只写 `Leaders` + `LeaderTraits` + `CivilizationLeaders` + `Players` |

leader-only 时 `Leaders.InheritFrom` 常指向该文明的原版领袖（或 `LEADER_DEFAULT`），
用于继承默认行为；具体取哪个以原版同文明领袖为准，**不要凭猜**。

## `Portrait` / `PortraitBackground`（★ 本类最容易误伤的两列）

这两列是**自由字符串**，指向 XLP 条目名（贴图名）：

- 默认（原版界面）：由游戏按领袖 3D 场景显示，通常可留空或指向标准立绘。
- **第三方 2D 选人界面适配**（如 Sukritact's Civ Selection Screen）：界面直接读这两列
  交给 Image 控件显示。适配 mod 的做法就是 `UPDATE Players SET Portrait=…, PortraitBackground=…`。

★ **命名铁律**：第三方界面适配素材**不得借用官方模板前缀**
（`FALLBACK_` = 官方 3D 回退 = `Leader_Fallback` 类）。走独立命名空间
`<适配对象短名>_UI_<KIND>_<KEY>`，例如 `SUK_UI_PORTRAIT_<KEY>` / `SUK_UI_BACKGROUND_<KEY>`。
理由、改名的实测前提与迁移工具见 `civ6-asset-forge/reference/ui-leader-portrait.md` §4.4。

★ 改这两列后**贴图必须在 `UITexture` 类 XLP 里登记**，否则不进 BLP → 界面空白
（cook 不报错）。校验：`civ6-asset-forge/scripts/verify_suk_portrait.py --project <工程根>`。

## 文本：必须走 `UpdateText`

同文明：`.modinfo` 的 `<LocalizedText>` 只管 mod 列表界面，**游戏内文本必须经
`UpdateText` 加载 `Text/*.sql`**（详见 `gotchas.md`「本地化文本通道」）。

常见 tag（`LOC_LEADER_<ID>_NAME` 等由你和生成器按同一规则推导，保持一致即可）：

```
LOC_LEADER_<ID>_NAME            领袖名
LOC_LEADER_<ID>_QUOTE           首次见面名言（配 LeaderQuotes.Quote）
LOC_LOADING_INFO_<ID>           载入界面信息
LOC_TRAIT_<ID>_ABILITY_NAME     能力名（配 Players.LeaderAbilityName）
LOC_TRAIT_<ID>_ABILITY_DESCRIPTION
```

`LocalizedText` 实列：`Language, Tag, Text, Gender, Plurality`。

## 代码/配置怎么写

用 `tools/civ_leader_data.py` 从规格 JSON 机械推导（**不要手写这些行**）：

```bash
python tools/civ_leader_data.py reference/civ-leader-spec.example.json \
       --project <工程根> --write
```

产出 `Data/CivLeader_<Slug>.sql` + `Data/Config_<Slug>.sql` + `Text/Text_<Slug>.sql`，
并自检 LOC tag 闭包、8 语言齐缺、`Portrait` 未登记 XLP 告警。

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
- 载入语 tag 的精确拼法（`LOC_LOADING_INFO_<ID>`）：**未核实**，建议照原版同文明领袖抄。
