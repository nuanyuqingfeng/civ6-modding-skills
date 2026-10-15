# Civilization Authoring — 新文明编写指南

> 本文只讲**文明**这一内容类型。领袖见 `leader-authoring.md`；
> 玩法逻辑（Lua/Modifier/UI）见 `gameplay-lua.md` / `workflows.md`；
> 工程骨架与 `.civ6proj` / `.modinfo` 结构见 `project-setup.md`。

## 你要写哪几张表

一个可玩的文明最少涉及 **4 张 gameplay 表 + 2 张 Config 表**。
下表列名**全部取自 `database/DebugGameplay.sqlite` / `database/DebugConfiguration.sqlite` 实测**，
不是记忆：

| 表 | 库 | 全列 | 必需 |
|---|---|---|---|
| `Civilizations` | gameplay | `CivilizationType`, `Name`, `Description`, `Adjective`, `RandomCityNameDepth`, `StartingCivilizationLevelType`, `Ethnicity` | `CivilizationType` / `Name` / `Description` / `Adjective` |
| `CivilizationTraits` | gameplay | `CivilizationType`, `TraitType` | 至少 1 行（文明能力） |
| `CivilizationLeaders` | gameplay | `LeaderType`, `CivilizationType`, `CapitalName` | ★ **必需**——漏了领袖与文明不关联，选人界面看不到 |
| `CityNames` | gameplay | `ID`, `CivilizationType`, `LeaderType`, `ContinentType`, `CityName`, `SortIndex` | 至少几座城 |
| `CivilizationCitizenNames` | gameplay | `CivilizationType`, `CitizenName`, `Female`, `Modern` | 可选 |
| `CivilizationInfo` | gameplay | `CivilizationType`, `Header`, `Caption`, `SortIndex` | 百科资料卡，可选 |
| `CivilizationAudioTags` | gameplay | `CivilizationType`, `MusicOverride` | 可选；★ **`MusicOverride` 是 0/1 布尔，不是音乐 tag**；与 `ArtDefs/Civilizations.artdef` 配对，判定与写法见 `reference/civ-metadata.md` §六 |
| `StartBiasTerrains` | gameplay | `CivilizationType`, `TerrainType`, `Tier` | 出生偏好，可选 |
| `Players` | **Config** | 18 列，见 `leader-authoring.md` | ★ 选人界面/设置界面靠它 |
| `PlayerItems` | **Config** | `Domain`, `CivilizationType`, `LeaderType`, `Type`, `Name`, `Description`, `Icon`, `SortIndex` | 特色项列表（★ 准入规则见 `leader-authoring.md`「`PlayerItems` 准入规则」：只收有实质 TRAIT 链的区域/建筑/单位/改良设施，资源不入列） |

> **库的分工**：`Players` / `PlayerItems` 属 **Config**（`DebugConfiguration.sqlite`），
> 不在 gameplay 库。所以文明/领袖的 SQL 通常拆成 **gameplay 一份 + Config 一份**——
> 分别挂 `InGameActions` 与 `FrontEndActions`（见 `project-setup.md`）。

### 知名地名与其它关联表

gameplay 库里另有按地形分的「知名地名」表，均为 **`CivilizationType` + `Named<Kind>Type`**
两列（★ **不是 `Name`**，实测）：

| 表 | 第二列 |
|---|---|
| `NamedMountainCivilizations` | `NamedMountainType` |
| `NamedRiverCivilizations` | `NamedRiverType` |
| `NamedVolcanoCivilizations` | `NamedVolcanoType` |
| `NamedDesertCivilizations` | `NamedDesertType` |
| `NamedLakeCivilizations` | `NamedLakeType` |
| `NamedOceanCivilizations` | `NamedOceanType` |
| `NamedSeaCivilizations` | `NamedSeaType` |

`civ_leader_data.py` 的 `named_places` 会按 `Named<Kind>Type` 自动推导列名
（`table` 以 `Civilizations` 结尾时去掉该后缀再拼 `Type`），可用 `column` 显式覆盖。

### 出生偏好

`StartBiasTerrains`（`Tier` 越小优先级越高）。同族还有按 Feature / River 等的变体，
用 `PRAGMA table_info` 查实际存在的表，不要凭表名猜列。

## Trait 写法总则

一个文明主体只有一个主 trait：`Traits.Name / Description` 填 `LOC_*_NAME` 与
`LOC_*_DESCRIPTION`，经 `CivilizationTraits` 挂到文明，能力 Modifier 全部经 `TraitModifiers`
挂到主 trait。

每个特色物品（区域、建筑、单位、改良设施）对应一个衍生 trait，ID 沿主 trait 追加
`_DISTRICT` / `_BUILDING` / `_UNIT` / `_IMPROVEMENT`；`Traits.Name / Description` 一律写 `NULL`。
它必须同时完成两条绑定：`CivilizationTraits`（或 `LeaderTraits`）挂到归属主体，
物品主表（`Districts` / `Buildings` / `Units` / `Improvements`）的 `TraitType` 指向该衍生
trait。特色物品主表的 `TraitType` 禁止指向主 trait。

议程 trait 同属衍生 trait：`Traits.Name / Description` 写 `NULL`，可见文案只写在 `Agendas`。

```sql
INSERT OR REPLACE INTO Types (Type, Kind) VALUES ('TRAIT_CIVILIZATION_RGN_X', 'KIND_TRAIT');
INSERT OR REPLACE INTO Traits (TraitType, Name, Description) VALUES
('TRAIT_CIVILIZATION_RGN_X', 'LOC_TRAIT_CIVILIZATION_RGN_X_NAME', 'LOC_TRAIT_CIVILIZATION_RGN_X_DESCRIPTION');
INSERT OR REPLACE INTO CivilizationTraits (CivilizationType, TraitType) VALUES
('CIVILIZATION_RGN_X', 'TRAIT_CIVILIZATION_RGN_X');

INSERT OR REPLACE INTO Types (Type, Kind) VALUES ('TRAIT_CIVILIZATION_RGN_X_IMPROVEMENT', 'KIND_TRAIT');
INSERT OR REPLACE INTO Traits (TraitType, Name, Description) VALUES
('TRAIT_CIVILIZATION_RGN_X_IMPROVEMENT', NULL, NULL);
INSERT OR REPLACE INTO CivilizationTraits (CivilizationType, TraitType) VALUES
('CIVILIZATION_RGN_X', 'TRAIT_CIVILIZATION_RGN_X_IMPROVEMENT');
```

`tools/civ_leader_data.py` 的规格条目用 `"main": true` 标记主 trait，衍生 trait 不填 Name/Description。

## 命名规则：文明变量必须带项目级后缀

`CIVILIZATION_*` 的末尾段必须带项目级后缀（如 _SNZ），防止与其他 mod 的文明 Type 冲突：
文明 Type、文明 Trait、城市名 tag、百科 Caption tag 全部沿用同一后缀。

| 示例 | 说明 |
|---|---|
| `CIVILIZATION_RGN_X` | 文明 Type（末尾段 `RGN_X` 是项目级后缀） |
| `LOC_CIVILIZATION_RGN_X_NAME` | 文明名 tag，完整继承末尾段 |
| `LOC_CITY_NAME_RGN_X_1` | 城市名 tag，同样继承 |
| `LOC_CIVINFO_RGN_X_LOCATION` | 百科资料卡 Caption tag |

- 项目另有领袖/文明变量后缀约定的，以本项目 **AGENTS.md** 为准（AGENTS.md 是项目私有约定的唯一真源）。
- AI **不参与**文明 Type 本身的格式纠正（见 AGENTS.md「用户自拟命名空间」）；只保证定义-引用闭合、tag 继承完整。
- 该后缀**不**写进本 skill 的模板或生成器默认值；生成脚本 `tools/civ_leader_data.py` 只按规格 JSON 的 `type` 字段原样拼接。

## 代码/配置怎么写

**不要手写这些行** —— 用 `tools/civ_leader_data.py` 从规格 JSON 机械推导：

```bash
python tools/civ_leader_data.py reference/civ-leader-spec.example.json \
       --project <工程根> --write
```

它输出 `Data/CivLeader_<Slug>.sql`（gameplay）、`Data/Config_<Slug>.sql`（Config）、
`Text/Text_<Slug>.sql`（8 语言文本），并自检：

- **LOC tag 闭包**：被表引用但没有文本块的 tag → **报错**（漏了游戏里就显示原始 `LOC_XXX`）
- **语言齐缺**：8 语言里缺哪些逐一列出
- **`MusicOverride` 类型**：写字符串会被库的 `CHECK` 直接拒绝（实测）

三个 `.sql` 目标文件不存在时脚本新建直写；任一已存在且内容有变化时，改写结果落到
`<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时
打印待写入清单。

## 文本：必须走 `UpdateText`

★ `.modinfo` / `.civ6proj` 的 `<LocalizedText>` **只管「选择 mod / 额外内容」界面**的
Name / Teaser / Description。**游戏内文本必须另经 `UpdateText` 动作加载** `Text/*.sql`，
否则游戏里只显示原始 tag 键名——而 mod 列表看起来完全正常，属**静默失败**
（详见 `gotchas.md`「本地化文本通道」）。

语言代码（8 语言，与工程 `Text/` 目录一致）：
`en_US` / `zh_Hans_CN` / `zh_Hant_HK` / `ja_JP` / `ko_KR` / `de_DE` / `es_ES` / `fr_FR`

写入形式：

```sql
INSERT OR REPLACE INTO LocalizedText (Language, Tag, Text) VALUES
  ('en_US', 'LOC_CIVILIZATION_RGN_X_NAME', 'Ragunna'),
  ('zh_Hans_CN', 'LOC_CIVILIZATION_RGN_X_NAME', '拉古那');
```

`LocalizedText` 实列为 `Language, Tag, Text, Gender, Plurality`（后两列可省）。

## 注册位置

按 `project-setup.md` 的「**文件类型 → 注册位置对照表**」。文明相关文件通常是：

| 文件 | 注册到 |
|---|---|
| `Data/CivLeader_*.sql` | `InGameActions` → `UpdateDatabase` |
| `Data/Config_*.sql` | `FrontEndActions` → `UpdateDatabase` |
| `Text/Text_*.sql` | `InGameActions` **和** `FrontEndActions` → `UpdateText` |
| `Data/Icons_*.xml` | → `UpdateIcons` |
| `Data/Colors_*.sql` | → `UpdateColors` |

★ **同时补 `<Content Include>`**：ModBuddy 只拷贝 `<Content>` 条目——只写在
`InGameActions` 里而漏进 `<Content>` 的文件**不会被部署**（踩过的坑，
见 `AGENTS.md` 的「Project 文件同步规范」与 `project-setup.md`「文件清单同步」）。

## 与其他 skill 的分工（**不在本文重复**）

| 内容 | 去哪 |
|---|---|
| 文明图标（22/30/32/36/44/45/48/50/64/80/128/200/256）、领袖图标 | **`civ6-asset-forge`** skill |
| 3D 模型 / 引用原版美术素材 / ArtDef·XLP 链 | **`civ6-art-reference`** skill |
| BGM、领袖语音（含 Wwise bank 与 `Audio` 库） | **`civ6-audio-pipeline`** skill（Wwise 侧） |
| 文明音乐的引擎侧接线（`CivilizationAudioTags` + `ArtDefs/Civilizations.artdef`） | `reference/civ-metadata.md` §六 |
| 文明能力（Trait/Modifier）、UI、事件 | 本 skill：`modifiers-cheatsheet.md` / `gameplay-lua.md` / `ui-lua.md` |
| 领袖（`Leaders` 表、议程、AI） | `leader-authoring.md` / `agenda-authoring.md` |
| 发布上工坊 | `release.md` |

## 验证顺序

```bash
python tools/modinfo_build.py <X.civ6proj> --deploy   # 派生 modinfo + 引用闭合自检
node scripts/rgn_validate_runner.mjs <Data 目录>      # SQL 引用完整性（悬空必须清零）
python scripts/check_proj_content.py                  # Content 清单双向闭合
python scripts/check_sql_exec.py                      # SQL 可执行性
python scripts/check_types_kinds.py                   # Types.Kind 合法性
```

## 未核实项（用前请自行确认）

- `RandomCityNameDepth` / `Ethnicity` 的合法取值范围：本次只核了列存在，**未查官方取值域**。
- 除上表列出的表外，是否还有其它需要随文明一起写的关联表（如 `DuplicateCivilizations`、
  `CivilizationLevels` 的官方用法）：**未核实**。
