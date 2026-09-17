---
name: civ6-modding
description: "文明6 mod 玩法侧总入口：Lua（UI + GamePlay）、ForgeUI XML 布局、.civ6proj / .modinfo 注册、数据库 XML/SQL、事件系统与全量 API 参考。内含决策树、任务工作流、XML 模板、验证清单，以及离线数据库目录（934 ModifierTypes / 761 EffectTypes / 327 RequirementTypes；1051 条 Requirements / 982 条 RequirementSets）+ SQLite 查询工具。专项章节：总督编写、城邦编写、平衡补丁（差分覆盖）、议程与领袖 AI、素材转换管线。发布：Steam 创意工坊上传/更新（release.md）。工具：7 个零依赖校验器（SQL 可执行性 / 引用完整性 / Types.Kind / SQL 语义反模式 / 内容清单闭合 / .lua 加载路径 / pantry 卫生）+ 双目录一致性比对。触发词：文明6、Civ6、modding、Lua、ForgeUI、UI 面板、按钮、弹窗、modinfo、civ6proj、数据库、Modifier、Requirement、PROPERTY、事件、GameEvents、LuaEvents、总督、governor、城邦、city-state、平衡补丁、balance patch、议程、agenda、创意工坊、workshop、上传、发布、校验、rgn_validate。"
version: "2.0"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - civilization
  - lua
  - forgeui
  - modding
  - ui
  - gameplay
  - database
models:
  recommended:
    - claude-sonnet-4
    - claude-opus-4
  compatible:
    - claude-3-5-sonnet
    - gpt-4
    - gpt-4o
languages:
  - en
  - zh
---

> 🧰 **工具先查名录（硬性）**：要写脚本做某件事之前，先看本 skill 的 [`TOOLS.md`](TOOLS.md)
> —— 本 skill 全部脚本的用途 / 用法 / 路径清单，外加本机**路径收纳**表。
> **有能用的就改它，不要重建。** 新增或改名脚本后，跑一次
> `python "<skills>/civ6-modding/tools/skill_manifest.py" civ6-modding` 刷新名录（`--check` 可做漂移检测）。
> 跨 skill 找工具先看 [`reference/FAMILY_INDEX.md`](reference/FAMILY_INDEX.md)（家族路由）；
> `tools/` 的用法细节、推荐顺序与踩坑记录见 [`tools/README.md`](tools/README.md)。

## 环境路径总表（必读 · 分享自举）

> **使用顺序：`<skill目录>\local_paths.json`（若存在）＞ 下表硬编码值。**
> 任一路径 `Test-Path` 失败 → 按"自动纠正"列依次探测；全部失败 → **询问用户一次**，
> 把结果写入 `<skill目录>\local_paths.json`（个人环境文件，分享时不携带、不覆盖他人）后继续。

| # | 用途 | 本机硬编码 | 自动纠正链 |
|---|---|---|---|
| P1 | ModBuddy 源工程目录 | `D:\documents\Firaxis ModBuddy\Civilization VI` | ① `%USERPROFILE%\Documents\Firaxis ModBuddy\Civilization VI` → ② 询问用户 |
| P2 | Mods 加载目录 | `D:\documents\My Games\Sid Meier's Civilization VI\Mods` | ① 注册表 `UserPath`＋`\Mods` → ② `%USERPROFILE%\Documents\My Games\Sid Meier's Civilization VI\Mods` → ③ 询问用户 |
| P3 | 游戏本体（UI/Lua/XML/Text 官方原文） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI` | ① 注册表 `ToolsPath` 去尾部 ` SDK` → ② Steam `libraryfolders.vdf` 找 appid 289070 → ③ 询问用户 |
| P4 | SDK Assets（artdef/解包素材） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` | ① 注册表 `AssetsPath` → ② P3＋` SDK Assets` → ③ 询问用户 |
| P5 | SDK 工具（ModBuddy/MSBuild） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK` | ① 注册表 `ToolsPath` → ② P3＋` SDK` → ③ 询问用户 |
| P6 | 创意工坊参考件 | `F:\Steam\steamapps\workshop\content\289070` | ① libraryfolders.vdf → ② 询问用户 |

注册表键（P2/P4/P5 同源，一条读三值）：
`HKCU\SOFTWARE\Firaxis\Civilization6_ModBuddy\2013\DialogPage\Firaxis.VisualStudio.Projects.Civ6.OptionsPages.OptionsDialogPage`
→ `UserPath / AssetsPath / ToolsPath`

## 查询三级阶梯（无结果时的强制流程，禁止跳步）

```
L1  skill 自带参考库（最先，零许可）
    database\DebugGameplay.sqlite(427表) / database\api.sqlite(4857函数) /
    database\DebugLocalization.sqlite / database\DebugConfiguration.sqlite /
    reference\*.json / 各 *.md
    ⚙ 先路径自检：引用的库文件必须存在且非 0 字节，异常先修复再查
    │  无结果
    ▼
    ⛔ 强制停下，询问用户（模板）：
       「我用〈方法〉查〈关键词〉于〈库〉无结果——是否查询方式有误？
         是否允许改查官方本机文件（拟查：〈L2路径〉×〈关键词〉）？」
    │  获批
    ▼
L2  官方本机文件（P3/P4/P6）
    Base\Assets\UI（控件 XML 与 lua 原文）· Base\Assets\Database ·
    Base\Assets\Text · DLC\ · SDK Assets\Civ6\ · 工坊参考件
    │  仍无结果
    ▼
    ⛔ 第二次停下：「L1/L2 均无结果（已查：〈完整清单〉）——是否允许联网？」
L3  联网（未获批准前禁止任何 websearch/webfetch 动作）
```

> L2 的许可一次性按关键词批：换新目标回 L1 重走阶梯。

## Task Routing — Read This First

> 🧭 **第一次接触这个 skill 家族？先读 `reference/FAMILY_INDEX.md`**（5 个 skill 的职责/边界/路由表 + 共用约定 + 分享状态）。

**Full workflow:** `workflows.md` · **Gotchas (必读):** `gotchas.md`  
**若项目根目录存在 AGENTS.md，也需提前阅读。**

### 1. Task Type → Go To

| Type | Go To |
|------|-------|
| **UI panel** (XML + Lua) | → UI Routing ↓ |
| **Art asset conversion / Icon 尺寸规格问答**（用户素材 PNG→DDS/.tex、多图 atlas 图集/序列图拼版、XLP 实存过滤、"xxx 图标需要什么尺寸"类提问） | → `art-pipeline.md`（先读其"素材询问铁律"，≥2 张图必问拼版意图）尺寸表直接查其第三节，图标规范化/占幅/边距规范查其第四节 |
| **图标实机锯齿 / 边缘发硬 / 毛刺**（"游戏里图标不清晰"、"小尺寸档有锯齿"、接手他人图集想验中间档） | → `art-pipeline.md` **第 8.1 节「边缘质量门」**：`verify_icon_atlas.py --edge-qa` 体检 + `regen_atlas_tiers.py` 从母版重出。**注意结构校验查不出这类问题** |
| **原版美术素材引用 / ArtDef·XLP 链**（给新对象配原版模型、查引用链、排查美术悬空、ArtDef cook 报错或"不同步"、单位渲染残缺） | → **`civ6-art-reference` skill**（引用链与 cook 层逻辑全在该 skill 内，此处不重复） |
| **Gameplay logic** (Lua only) | → Gameplay Routing ↓ |
| **Game data** (units, buildings, modifiers) | → Data Routing ↓ |
| **总督（Governor）**（新增总督 / 晋升树 / 就职回合 / 立绘注册 / 名额扩容） | → `governor-authoring.md`（美术规格另见 `civ6-asset-forge` skill 的 `reference/governor-art.md`） |
| **城邦（City-State）**（自定义城邦 / 选单不出现 / 宗主国加成 / 使者层级） | → `citystate-authoring.md` |
| **文明周边数据收尾**（百科资料卡 `CivilizationInfo` / 城市名 `CityNames` / 市民名 `CivilizationCitizenNames` / 出生关联 `StartBias*` / BGM 开关 `CivilizationAudioTags` / 知名地名 `NamedMountains·NamedRivers` 等） | → **`reference/civ-metadata.md`**（各表 schema、取值域、写作要点、数量建议、最小检查清单） |
| **Asset Editor 字段名 / 调试查日志 / 枚举取值**（"AE 里那个框叫什么"、"Database.log 怎么看"、"Culture 有哪些值"、"忠诚度材质的字段名"） | → **`reference/editor-and-enums.md`**（AE 字段速查 / 调试三板斧 / `Cultures.artdef` 取值表 / 忠诚度 3D 链字段） |
| **平衡补丁 / 差分覆盖**（改主工程数值、解挂载、覆盖文本的补丁 mod） | → `balance-patch.md` |
| **Mixed** | → Read all relevant |
| **Steam 创意工坊上传/更新** | → `release.md` |
| **Debug** | → `debug-tools.md` + `gotchas.md` |

### 2. UI Routing

```
ADD to existing UI
├─ Button on LaunchBar/PartialScreen → workflows.md "A" + xml-templates.md "LaunchBar"
├─ Info onto CityPanel/UnitPanel     → workflows.md "B" (ReplaceUIScript)
└─ Popup/overlay from existing UI    → workflows.md "C" + "E"

REPLACE existing UI behavior → workflows.md "B" + ui-lua.md "UI Replacement"
CREATE new standalone panel  → workflows.md "C" + xml-templates.md "Fullscreen Overlay"
MODIFY data display          → workflows.md "D" + database.md
```

**必读:** `ui-controls.md`（控件属性/Lua 方法/XML 示例）· `ui-lua.md`（生命周期/事件/热重载）· `xml-templates.md`（模板）

### 3. Gameplay Routing

```
ADD game mechanic
├─ React to events (turn, move, build)  → gameplay-lua.md + events.md
├─ Store custom data                    → gameplay-lua.md "SetProperty/GetProperty"
└─ Expose data to UI                    → gameplay-lua.md "UI ↔ GP Communication"

MODIFY rules
├─ Via SQL modifiers (preferred)        → database.md + `query_api.py`
├─ Via Lua hooks (GameEvents)           → gameplay-lua.md + events.md
└─ Via Lua override                     → gameplay-lua.md + `query_api.py`

ADD content (unit/building/district)    → database.md + project-setup.md（优先查 .civ6proj）
ADD civ/leader / agenda / AI 偏好                          → database.md + agenda-authoring.md + `query_api.py`
```

**查询:** 事件签名 → `python database/scripts/query_events.py --search 关键词` · API → `api-cheatsheet.md` + `database\api.sqlite`

### 4. Data Routing

```
ADD new unit/building/district
├─ 列定义 → PRAGMA table_info(TableName) (DebugGameplay.sqlite)
├─ 写法   → database.md
├─ ModifierType 查询 → SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'
├─ ModifierArguments → SELECT Name,Value FROM ModifierArguments WHERE ModifierId='X'
├─ RequirementType   → SELECT * FROM Requirements WHERE RequirementType LIKE '%Key%'
└─ 类型名中英对照    → SELECT UnitType FROM Units WHERE UnitType LIKE '%Key%'

Modifier/PROPERTY 设计
├─ 作用域决策 → 见下文"写前三问"
├─ ATTACH 模式 → reference/WORKSHOP_PATTERNS.md
└─ 参数分类   → reference/MODIFIER_ARGUMENTS.md

ADD tech/civic/policy   → database.md
ADD resource/feature    → database.md
REMOVE/MODIFY data      → database.md "Removing Data" + project-setup.md "LoadOrder"（优先查 .civ6proj）
ADD localization text   → database.md + DebugLocalization.sqlite (SkillAnnotation_Colors/Icons) + 本地化桥接
```

### 4.1 本地化桥接（翻译/多语言任务）—— **可选：依赖本机外部 skill**

> ⚠ **本节是"作者本机附加能力"，不是本 skill 的组成部分。** 下表命令指向另一个 skill
> （`（外部翻译 skill，已不作为依赖）`，位于作者机器的 `~/.config/opencode/skills/`）与一份**不随本 skill 分发**的
> 语料库 `（语料库已移除）`。**全新环境里这些路径不存在**，命令会直接失败——这**不影响** Civ6 侧的其它任何功能。
>
> 你要做翻译/本地化时，二选一：
> ① 自行准备等价工具（本 skill 侧只需守住下面的"风格底线"）；
> ② 拿到 `（外部翻译 skill，已不作为依赖）` 与 `（语料库已移除）` 后，把命令里的路径替换成你自己的实际路径再跑。
>
> `（外部翻译 skill，已不作为依赖）` 是跨项目翻译总 skill；仅在翻译/本地化任务时借调其工具，最终校验仍用本 skill 的 Civ6 风格规则。

- 词库查证（SQLite 优先）：`python <（外部翻译 skill，已不作为依赖）>/references/（已移除）/scripts/search_（已移除）.py "守岸人" --source-type term,item --field-type name --limit 10`
- 全工程审计（只读）：`python <（外部翻译 skill，已不作为依赖）>/scripts/civ6_text_audit.py audit --root <工程目录> --out report.txt`
- 主工程 vs 平衡补丁：`python <（外部翻译 skill，已不作为依赖）>/scripts/civ6_text_audit.py diff-tags --base <主工程> --balance <补丁> --out diff.txt`
- 写入（自动备份 + 元组级替换 + 写后 verify）：`python <（外部翻译 skill，已不作为依赖）>/scripts/civ6_locale_tool.py merge --sql Text_X.sql --changes changes.json`；`apply-edits --sql Text_X.sql --edits edits.json`
- 单命令闭环：`python <（外部翻译 skill，已不作为依赖）>/scripts/civ6_pipeline.py run --root <工程目录> --names names.json --workdir out --db <你的 （语料库已移除）>`；默认只补缺失语言，`--overwrite` 才覆盖已有译文，`--strict` 卡后置审计，`--dry-run` 只出计划。
- 可直接 import（主模型或子代理）：`audit_files` / `marker_drift` / `diff_tags`；另可复用 `parse_sql_rows` / `extract_file_rows`。
- 风格底线：语言代码 `en_US` / `zh_Hans_CN` / `zh_Hant_HK` / `ja_JP` / `ko_KR` / `de_DE` / `es_ES` / `fr_FR`；`[ICON_X]`、`[COLOR:...]`、`[ENDCOLOR]`、`[NEWLINE]`、`{LOC_TAG}` 必须保留；默认多语言合并进原 SQL，不新增分语言文件；UTF-8/CRLF/注释/尾逗号保持原样；Config 覆盖属预期加载语义。

### 5. 中文文件处理（必读）

处理含中文的 SQL/Lua/XML 时，严格执行以下规则（完整版见项目 AGENTS.md「UTF-8 与中文文件处理」）：

- 所有文件读写默认 UTF-8，不得改变原有编码、换行风格和无关内容。
- PowerShell 中读写含中文文件前先 `chcp 65001`，并设置 `[Console]::OutputEncoding` / `$OutputEncoding` 为 UTF-8。
- 查看含中文文件优先用 Read 工具，避免 PowerShell 打印中文（控制台乱码多为显示问题，不代表文件损坏）。
- 禁止 PowerShell here-string 管道/重定向/`Set-Content`/`Out-File` 写入含中文内容；不要用 `sed`/`awk` 处理含中文文件，改用 Python 或 Node.js 并显式 UTF-8 读写。
- 不要为了修编码而整文件重写、全文件格式化或全文件字符串替换。

---

## 写前三问（Core Rules 浓缩版）

写任何代码前，依次回答三个问题：

### 一问：SQL 能搞定吗？

```
能 → 查表确认，写 SQL，不用 Lua
不能 → 进二问
```

**确认清单：**
- 列是否在表中？ → `PRAGMA table_info(TableName)`（DebugGameplay.sqlite）
- NotNull 列是否都填了？ → 检查上一步输出中 `notnull=1` 且 `dflt_value=NULL` 的列
- ModifierType 存在吗？ → `SELECT * FROM Modifiers WHERE ModifierType LIKE '%X%'`
- 参数签名对吗？ → `SELECT Name,Value FROM ModifierArguments WHERE ModifierId='X'`
- `.civ6proj` / `.modinfo` 注册了吗？ → 优先查 .civ6proj 项目文件清单，否则 UpdateDatabase 或 AddGameplayScripts
- **新出现的 XxxType 已在 Types 表注册？** → `SELECT * FROM Types WHERE Type = '新TYPE值'`，无结果则先 `INSERT INTO Types (Type, Kind) VALUES ('X', 'KIND_...')`。**注意：一切新主体 Type 都须注册**——不止 ModifierType/RequirementType，还包括 Unit、Building、District、Promotion（`KIND_PROMOTION`）、PromotionClass（`KIND_PROMOTION_CLASS`）等（完整 Kind 值见 `schema-annotated.md` Types 表）。遗漏注册会在游戏加载时报 `FOREIGN KEY constraint failed` / `Invalid Reference on X does not exist in Types`

**Modifier 作用域速查：**

| 绑定表 | ModifierType 前缀 | 效果范围 |
|--------|------------------|---------|
| BuildingModifiers / DistrictModifiers / UnitAbilityModifiers | `SINGLE_CITY_*` / `SINGLE_UNIT_*` | 单城/单单位 |
| TraitModifiers / PolicyModifiers | `PLAYER_CITIES_*` / `PLAYER_UNITS_*` | 玩家所有城市/单位 |
| GameModifiers | `GAME_*` | 全局 |

绑定表与 ModifierType 前缀可自由组合（如 BuildingModifiers 绑 `PLAYER_CITIES_ADJUST_BUILDING_YIELD_CHANGE` 有效）。

需要 ATTACH 条件分发？→ `reference/WORKSHOP_PATTERNS.md`
需要 ABILITY 不叠加分发？→ `gotchas.md` §26-27

### 二问：写 Lua 前查 API 了吗？

```
查了 → 写
没查 → python database/scripts/query_api.py --search <Key>     # 已同时搜 table/func/sub_func/true_name/id
       （等价的裸 SQL：WHERE func_name LIKE '%Key%' OR sub_func_name LIKE '%Key%'）
       查详情 → --show Table.Func[.Sub]   # 父项会附带列出其全部子项
       列整表 → --object Table            # 或 --object Table.Func 看某方法的所有子项
       需要示例/注释 → --show 会自动合并 reference/api_enhanced.json 的 exampleCode/notes
       需要「运行时是否真有 / UI 还是 GP」→ 看 verify_status + verify_scope + runtime_gp/runtime_ui（见「API 核验字段」）
```

**铁律：严禁凭经验猜测 API 名称或参数** — `database\api.sqlite` 有 4857 行 API，猜错即返工。

> **⚠ 子项务必用 `sub_func_name` 一起搜**：`api_functions` 里父项与子项是**两列**
> （`func_name` = 父方法/遍历器，`sub_func_name` = 真正要调的方法）。
> 只搜 `func_name` 会漏掉全部 1044 条子项，且 `--search` 命中时若只显示父项名会
> 被误读成"父项才是该方法"。典型：`GetHolyCityID` 是 `Player:GetReligion()` 的子项、
> `CurrentlyBuilding` 是 `City:GetBuildQueue()` 的子项、`IsValidFoundLocation` 同名的两条
> （`Plot` 版 Both / `Player:GetCities()` 版仅 GP）可用 `--sub-only` 区分。

> **核验优先**：`verify_status` 三档语义与计数见下文「API 核验字段」（2026-09-08 FireTuner 全量实测）；
> `='存疑'` 必按 `verify_note` / `true_name` / `true_path` 改用真身，勿照抄。

> **小技巧：尝试复数形式** — `GetAbility` 的子方法可能在 `sub_func_name` 列为 `GetAbilities`，`UnitModifier` 可能是 `UnitModifiers`。以 `s` 结尾的 `func_name` 往往是遍历器，其实方法在 `sub_func_name` 中。

### 三问：接口用法查证了吗？（示例 / 签名 / 同类模式 / 陷阱）

写代码前确认实际调用方式与参数：

- API 调用示例 → `grep "FuncName" reference/api_enhanced.json`
- 事件回调签名 → `python database/scripts/query_events.py --show EventName`
- 同类 Modifier 模式 → `reference/WORKSHOP_PATTERNS.md`
- 常见陷阱 → `gotchas.md`

---

## Event System Quick Decision

| 所在位置 | 用 | 必须移除？ |
|---------|----|-----------|
| UI Lua context | `Events.*` | YES — `.Remove()` in `OnShutdown()` |
| UI Lua context | `LuaEvents.*` | No — auto-cleanup |
| GamePlay Lua script | `GameEvents.*` | No — loaded once per game |
| GamePlay Lua script | `Events.*` | 引擎事件在 GP 侧同样可用；`.Remove()` 非必需（脚本每局加载一次） |

> ⚠ **`Events.*` / `GameEvents.*` / `LuaEvents.*` 是三条互不镜像的总线**（2026-09 修订）：同一个逻辑事件**通常只在其中一张上有效**，用错总线**静默无效**（不报错、不回调）。
> **禁止凭印象选总线 —— 查 `reference/events_enhanced.json` 的 `eventSystem` 字段**（1081 条全覆盖：`LuaEvents` 481 / `Events` 470 / `GameEvents` 130），或 `python database/scripts/query_events.py --show <事件名>` 看 `System` 列。
> 注意 `GameEvents.*` 上**存在一批非自定义事件、且它们在 `Events.*` 上无对应条目**（`OnDistrictConstructed`/`CityConquered`/`PolicyChanged`/`PlayerTurnStarted` 等，130 条中 82 条 `availability=GamePlay`）三条总线**按事件划分**，不按「引擎 vs Lua」划分 —— 永远查表、不要按来源猜。
> 另：`GameEvents.X` 对任意名字都自动建 table，**不能**用 `type()` 判断事件是否存在——只有 `type(Events.X)` 是权威探针。
> `availability: "None"` 的 48 条**哪一层都订阅不到**（UI 侧 `.Add()` 会 nil 崩溃）。
> 详见 `gotchas.md` §7 与 `events.md` Gotcha 8。

## 数据传递速查

### 跨脚本通信

| 方向 | 方式 | 场景 |
|------|------|------|
| UI ↔ UI | LuaEvents（仅基础类型） | 面板间广播 |
| UI → Gameplay | EXECUTE_SCRIPT | 按钮触发 GP 动作 |
| Gameplay → UI | ReportingEvents.SendLuaEvent | 数据变更推送 |
| GP ↔ UI 被动读 | PROPERTY 直接读（跨端）；ExposedMembers 仅限 GP 同端跨文件 | 查询，非按钮回调；禁止跨端暴露 |

### PROPERTY 系统速查

| 读渠道 | 适用范围 | 方式 |
|--------|---------|------|
| `REQUIREMENT_PLOT_PROPERTY_MATCHES` | 仅地块 — 条件检测 | 引擎内置 |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH Key=` | 仅单位战斗力 | 引擎内置 |
| 全部其他 | 玩家/城市/单位/地块任意 | 仅 Lua: `entity:GetProperty(key)` |

**写入：** SQL `MODIFIER_PLAYER_ADJUST_PROPERTY` / `SINGLE_CITY_*` / `UNIT_*` · Lua `entity:SetProperty(name, val)`

不存在 `CITY_PROPERTY_MATCHES` 或 `UNIT_PROPERTY_MATCHES` — 城市/玩家 PROPERTY 做条件必须走 Lua。

## Code Generation Workflow

所有代码生成任务遵循此流程。

### ① Understand — 理解需求

写任何代码前，先澄清：
- 任务类型：UI（XML+Lua）/ Gameplay（Lua）/ Data（SQL/XML）/ 混合
- 范围：新增 / 修改 / 修复
- 通信需求：需要 UI↔GP 吗？需要跨脚本传数据吗？
- 持久化：需要跨存档保存状态吗？（→ PROPERTY）

### ② Route — 确定走向

按 §1 Task Routing 表选定模式，进入对应 Routing 小节。

### ③ Plan — 规划实现

确定文件清单、模式、API：

| 维度 | 参考文件 |
|------|---------|
| 文件清单 | `project-setup.md`「文件清单同步」+ 本次 diff 涉及的文件 |
| 模式选择 | `workflows.md`（A-J） |
| API 查询 | `api-cheatsheet.md` / `database\api.sqlite` |
| 事件选择 | `events.md` |
| 命名规范 | `conventions.md` |
| 多列表格填表 | **预先** `database/schema-annotated.md`（列定义/必填/示例值） |

### ④ Write — 编写代码

遵循参考文件写代码，完成后注册到 `.civ6proj` / `.modinfo`（仅 XML/SQL/Lua 必须写文件清单；ImportFiles 图片/视频、Platform 音频 bank 等媒体资产走专门导入或用户手动导入，其余文件 ModBuddy 引擎自动打包无需写入 —— 见 project-setup.md「文件清单同步」）。

### ⑤ Validate — 验证

对照 `validation.md` 清单逐项确认。

---

### Anti-Patterns 反模式

1. **不要混用 UI/GP API** — 查可用性
2. **不要忘记热重载** — 始终处理 `OnInit(isReload)` 和 `OnShutdown()`
3. **不要通过 LuaEvents 传 C++ 对象** — 仅传基础类型

---

## DSH 工具集成（dsh-rgn-tools）

**调用优先级（硬性）**：

1. **原生插件工具（首选）**：会话工具列表存在 `dsh_validate` / `dsh_validate`（opencode 全局适配插件，注册于 `~/.config/opencode/dsh-plugins/dsh-rgn-tools.mjs`）→ 直接调用；
2. **离线执行器（无原生工具时）**：node 直调下述 runner，参数语义与工具一致；
3. **最终退化**：执行器也不可用才允许手动查 skill 自带 sqlite / 人工核对，交付注明"未经 rgn_validate 校验"。

| 场景 | 原生工具 | 离线执行器 |
|------|--------|-----------|
| 查（已移除）官方译名/名词/剧情台词（`（语料库已移除）`，12 万行语料，多语言+说话人） | `dsh_validate` | `（语料执行器已移除）` |
| 校验项目 `*_RGN.sql` 引用完整性（悬空 ModifierId/Type/RequirementSetId 等，可对照基础库） | `dsh_validate` | `scripts/rgn_validate_runner.mjs` |

### 自带校验/运维脚本（`scripts/`，全部零依赖 + 带退出码）

**完整清单与标准验证顺序见 `scripts/README.md`。** 改完代码/数据后按序跑：

| 脚本 | 查什么 | 与谁的职责互补 |
|------|--------|---------------|
| `scripts/check_sql_exec.py` | **可执行性** —— 非法转义（`'…\'s…'`）导致**整条 INSERT 报废**；遇错即停，同文件后续语句块也全不执行 | ★ `rgn_validate` 查不到：语句没跑起来 = 数据没进库 = 引用不悬空 |
| `scripts/rgn_validate_runner.mjs` | **引用完整性** —— 悬空 ID | 与上面互补 |
| `scripts/check_types_kinds.py` | `INSERT INTO Types` 的 `Kind` 是否引擎合法枚举 | 打包不报错、加载期才丢弃 |
| `scripts/check_sql_antipatterns.py` | **语义反模式** —— 语法合法但恒假：`LIKE ('%A%' OR '%B%')`、`WHERE … = NULL` | ★ 前三个都抓不到：它跑得起来、引用也闭合，只是**意思错了** |
| `scripts/check_proj_content.py` | `<Content Include>` ↔ 磁盘**双向闭合**（悬空清单项 / 漏登记） | 见 `gotchas.md` §3「打包 vs 加载」 |
| `scripts/check_pantry.py` | **pantry 卫生** —— `.tex` 位置 / 重名 / depot 路径 / 非 ASCII / `.tex`↔`.dds` 配对 | 开 AssetEditor 前必跑 |
| `art/verify_tex_class.py` | **`.tex` 类别 vs XLP 注册类**是否匹配（如 `UITexture` 包里的贴图必须 `UserInterface`） | ★ 唯一能防「类别写错 → cooker 静默替换成 error asset」的机械防线；`check_pantry`/`verify_icon_atlas`/`align_tex_format` 都不查它 |
| `scripts/clear_ae_cache.py` | 清 AssetEditor 依赖缓存（动过贴图后**必须**清，否则验证结论是缓存假象） | 同上 |
| `scripts/verify_trees.py` | 两棵目录逐字节相同（源 ↔ Mods 副本） | 双目录一致性 |


### rgn_validate 离线执行器

`scripts/rgn_validate_runner.mjs`：逻辑提取自 dsh-rgn-tools 插件源码，仅依赖 Node ≥22 内置 `node:sqlite`，任意终端可直接运行。默认**实跑模式**：把基础库快照到临时文件 → 真实执行项目 SQL（两遍：先跨文件 DDL 再其余语句，逐语句容错）→ 直接查库比对定义/引用全集，可识别 `INSERT INTO ... SELECT '字面量' || 列 ...` 动态拼接，并附带语法校验能力。

```bash
node "<本skill目录>/scripts/rgn_validate_runner.mjs" [目录=cwd] [文件模式=*.sql] [checkNaming=true] [--base <基础库路径>] [--static]
```

- 基础库默认 `<本skill目录>/database/DebugGameplay.sqlite`（相对脚本定位），`--base` 可覆盖；临时副本用后即删，原库只读不动
- `--static` 回退纯文本解析模式（仅认 VALUES 字面量行，SELECT 拼接会误报悬空）
- 执行错误多为基础库缺引擎专属/前端表（如 Players、PlayerItems）或校验器限制（Config 文件按 gameplay schema 校验，如 DuplicateLeaders.Domain；Types.Hash UNIQUE 未模拟引擎哈希；temp 表两遍执行顺序），属环境性容错项而非项目错误
- **基础库防污染**：参考库必须与官方 schema 1:1。改过 DB 后跑 `python database/scripts/audit_schema_drift.py`（有漂移 exit 1）；校验器也会对 DynamicModifiers/Modifiers/ModifierArguments/Types 做列断言并告警

### （已移除）_query 离线执行器

`（语料执行器已移除）`：移植自 dsh-rgn-tools 源码 `（已移除）Query()`，CLI 化。数据源 `D:\documents\Firaxis ModBuddy\Civilization VI\示例工程\（已移除的语料库键）\（语料库已移除）`。

```bash
node "<本skill目录>/（语料执行器已移除）" --q <关键词> [--table terms|story] [--lang zh|en|ja] [--speaker <人名>] [--exact] [--limit N]
```

- `terms` → `translations` 术语词典表；`story` → `story_dialogues` 剧情台词表（`speaker_{lang}` 模糊匹配说话人）
- `--lang` 按所选语言匹配文本列（默认 `zh`，可选 `en` / `ja`）

## File Reference

### 数据查询（写前必跑）

| 查什么 | 怎么查 |
|--------|-------|
| Modifier/Requirement/Unit 等游戏数据 | `SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'` (DebugGameplay.sqlite) |
| Lua API 函数签名 | `SELECT * FROM api_functions WHERE func_name LIKE '%Key%'` (database\api.sqlite) |
| API 参数详情 | `SELECT a.* FROM api_args a JOIN api_functions f ON ...` (database\api.sqlite) |
| API 运行时是否真有 / UI-GP 范围 | `SELECT id,availability,verify_status,verify_scope,runtime_gp,runtime_ui,true_path FROM api_functions WHERE func_name LIKE '%Key%'` |
| 只取已核验 API | `... WHERE verify_status='已核验' AND availability IN ('Both','UI')` |
| 查存疑项与真身 | `SELECT id,availability,suspect_type,true_name,true_path,verify_note FROM api_functions WHERE verify_status='存疑' AND table_name='X'` |
| 命令行查（含核验标记） | `python database/scripts/query_api.py --search Key [--verified\|--suspect\|--pending] [--sub-only]`<br>`--show Table.Func[.Sub]` 查详情（父项会附带列出全部子项）；`--object Table[.Func]` 列整表/某方法的子项 |
| 列定义 / NotNull / Default | `PRAGMA table_info(TableName)` (DebugGameplay.sqlite) |
| 中英文游戏文本 | `SELECT Text FROM LocalizedText WHERE Tag='LOC_X' AND Language='zh_Hans_CN'` (DebugLocalization.sqlite) |
| 颜色/图标名 | `SELECT * FROM SkillAnnotation_Colors` / `SELECT * FROM SkillAnnotation_Icons` (DebugLocalization.sqlite；skill 自带查询表，非游戏表) |
| FrontEnd 数据 (Map/Difficulty) | `SELECT * FROM Maps` (DebugConfiguration.sqlite) |
| 事件回调参数 | `python database/scripts/query_events.py --show ExactEventName` |

### 参考其他工坊作品（默认顺序）

路径见文首「环境路径总表」：**P1 = ModBuddy 源工程目录（首选）、P6 = 创意工坊参考件（次选）**。
禁止使用 `.lnk` 快捷方式地址，直接使用总表解析出的文件夹路径。

### 核心文件

| 文件 | 用途 | 何时读 |
|------|------|-------|
| `ui-controls.md` | ForgeUI 控件属性/Lua 方法/XML 示例 | **查控件时必读** |
| `ui-lua.md` | UI 生命周期、事件、热重载 | 写 UI 时读 |
| `xml-templates.md` | XML 布局模板 | 复制粘贴时 |
| `workflows.md` | 任务工作流决策树 | 路由指示时 |
| `gameplay-lua.md` | GP Lua 脚本基础 | 写 GP 逻辑时 |
| `database.md` | 数据增删改 + 查询指南 | 写数据时 |
| `agenda-authoring.md` | **议程与领袖 AI 行为编写**：议程好感链 / reqset 复用与自建规则 / 文案规范 / 28 个 AI System 偏好表 / 注册顺序与验证 | **写议程、外交好感、领袖 AI 偏好时** |
| `governor-authoring.md` | **总督编写**：10 张总督表 / 12 列必填（唯一可空列 `TraitType`）/ `BaseAbility` 网格位 / `TransitionStrength` 就职回合 / 名额扩容 / 作用域与条件 / 立绘注册 / 引擎笔误照抄判定 | **新增总督、改晋升树时** |
| `citystate-authoring.md` | **城邦编写**：★ 城邦横跨 Gameplay/Configuration 两个数据库 / `CityStates.Domain` / 宗主国加成标准模板 / 使者层级靠 `InheritFrom` 继承 / 自建分组标签 | **新增城邦、选单不出现时** |
| `balance-patch.md` | **平衡补丁 / 差分覆盖**：★ LoadOrder 必须压过主工程最终覆盖层 / 差分手法表（改值·解挂载·换门槛·清 ID 族·文本 REPLACE）/ 全局标志 + 公式化系数 / 验证清单 | **写补丁 mod 时** |
| `project-setup.md` | .civ6proj / .modinfo 项目结构与注册指南 | 注册文件时 |
| `release.md` | **Steam 创意工坊发布**：workspace 准备 / 非 Trimmed 上传工具构建 / validate→upload→Steam API 验证 / Clash Verge 代理诊断（附带脚本见 `release/scripts/`、模板 `release/templates/`、`release/docs/`） | **上传或更新工坊条目时** |
| `conventions.md` | 命名规范/文件模板 | 写任何文件前 |
| `validation.md` | 验证清单 | 完成开发后 |
| `debug-tools.md` | 调试面板/热重载 | 调试时 |
| `gotchas.md` | **常见错误（必读）** | **写代码前扫一遍** |
| `art-pipeline.md` | 素材转换管线（单图 PNG→DDS/.tex、多图 atlas 图集/序列图拼版、Mod.Art.xml 生成、19 类图标尺寸全表）+ 素材询问铁律 + **图标规范化专属章节（第四节，每类 Icon 对应规范，Units 已验证）** | 涉及素材文件时 |

### 速查表（先扫一眼）

| 文件 | 内容 | 大小 |
|------|------|------|
| `api-cheatsheet.md` | Lua API 速查（150 函数） | 8KB |
| `modifiers-cheatsheet.md` | Modifier/Requirement 速查 | 7KB |

### 图标尺寸速查（Art asset 问答必查此表，禁止凭记忆报尺寸）

来源：Civ6 Modding Assistant 反编译表（完整版+用法见 `art-pipeline.md` 第三节）。
问"xxx 要什么尺寸"→ 在此直接作答；做素材转换 → 在 manifest 里填对应 role，尺寸由脚本内置。

| 类别 | 尺寸 |
|------|------|
| Civilizations（civ_icon） | 22,30,32,36,44,45,48,50,64,80,128,200,256 |
| Leaders（leader_icon） | 32,45,48,50,55,64,80,256 |
| Buildings（building_icon） | 32,38,50,80,128,256 |
| Units（unit_icon） | 22,32,38,50,80,256 |
| Districts（district_icon） | 22,32,38,50,80,128,256 |
| Resources（resource_icon） | 38,50,64,256 |
| Wonders（wonder_icon） | 32,38,50,64,128,256 |
| Improvements（improvement_icon） | 38,50,80,256 |
| Civics（civic_icon） | 38,42,128,160 |
| Tech（tech_icon） | 30,38,42,128,160 |
| Policies | 32,38,50,256 |
| Projects | 30,32,38,50,70,80,256 |
| Greatworks | 45,64,256 |
| Features | 50,64,256 |
| Governments | 32,50 |
| Unit_Portraits | 38,50,70,95,200,256 |
| Unit_Actions | 38,50,80,256 |
| Victories | 64,80,130,220 |
| Citystates | 22,30,32,36,40,44,48,64,68,80,256 |
| Stats | 16,22,32,45,55 |

> 例外：忠诚度贴图 512/128 与 256/128（`civ6-asset-forge` skill 的 `reference/loyalty-icon.md`）；项目可自定义增减
> （如本项目 Resources 另加 32、Product 含 45），以项目 Icons XML 现状为准。
>
> **规范化占幅**：Units（unit_icon）主画布 256、内容占幅 ≈87.5%（224px）、四周 ≈16px 统一边距、白色剪影+Alpha；
> 狭长图标（长短边比 ≥1.3）可 `--slender-flush` 让长边平齐画布边缘（仅狭长图标适用）；
> 每类 Icon 对应规范见 art-pipeline 第四节（不同于尺寸表）；未验证类别：按 `art-pipeline.md` 第四节的「调研 / 原图入库 / 推断」流程处理后报数。

### 深度参考（需要时 grep）

| 文件 | 用途 |
|------|------|
| `reference/FAMILY_INDEX.md` | **家族索引**：5 个 civ6 skill 的职责/边界/路由表 + 共用约定 + 分享状态 |
| `reference/api_enhanced.json` | 增强 API + 中文注释（核验标记见「API 核验字段」） |
| `reference/events_enhanced.json` (1.2MB) | 增强事件（`query_events.py` 查询） |
| `database/schema-annotated.md` | 常用多列表注解（列定义/必填/示例值） |
| `reference/MODIFIER_ARGUMENTS.md` | Modifier 参数分类 |
| `reference/WORKSHOP_PATTERNS.md` | 高级 SQL 模式 |
| `reference/TYPE_NAME_MAPPING.md` | Type→名称 + Trait→Modifier 关联链 |
| `database/modifiers-guide.md` | Modifier 系统指南 |
| `database/scripts/sql_query_templates.sql` | SQL 查询模板 |
| `database/scripts/query_events.py` | 事件查询工具（查参数/签名/示例） |
| `database/scripts/query_api.py` | API 查询工具（主源 `api.sqlite`，**父项与子项一并查**；含 availability/核验字段，示例/注释来自 JSON 富化） |
| `database/scripts/requirement_reference.sql` | RequirementType 分类 |

### 数据库文件

| 数据库 | 大小 | 用途 |
|--------|------|------|
| `database/DebugGameplay.sqlite` | **61,014,016 字节（58.2 MiB）** | 游戏数据 (427 表)；**该库未入库（可再生产物）**，首次使用需自备，见 `database/README.md` |
| `database/api.sqlite` | 2.5 MB | Lua API（4857 行；含 2026-09-08 FireTuner 实测核验列，见下节） |
| `database/DebugLocalization.sqlite` | 64.9 MB | 中英文文本 |
| `database/DebugConfiguration.sqlite` | — | FrontEnd 配置数据 |

### API 核验字段（2026-09-08 FireTuner 全量实测 · UI/GP 范围存在性）

| `verify_status` | 含义 | 行数 | 怎么用 |
|---|---|---|---|
| `已核验` | 实测过关（与文档 availability 一致），或 P1 已实装修正 / 已核出真身 | 3256 | 可直接引用 |
| `存疑` | **文档自身不对**：availability 标错、名称/路径错、运行时确无此名、CodeBuddy 文档转储 | 1434 | 按 `verify_note` + `true_name`/`true_path` 改用真身；未删除任何条目 |
| `''` 留空 | **本次无法实测**（缺实例通道或事件动态代理），既不判过关也不挂嫌疑 | 167 | 待具备条件复测 |

新增列（`api_functions`）：`verify_status` `verify_scope` `verify_note` `verify_at` `runtime_gp` `runtime_ui`
`audit_priority` `suspect_type` `corrected_from` `true_name` `true_path`

- `verify_scope`：实测范围 = 双端 / 仅GP / 仅UI / 双端未见 / 含不可判
- `runtime_gp`、`runtime_ui`：实测类型（`function`/`table`/`userdata`/`string`/`nil`/`ERR`/`CF`）；
  `ERR` = 命名空间或实例在该上下文根本不存在，`nil` = 容器可达但无此成员
- `audit_priority`：`P1`（已实装）/ `P2`（需裁决）/ `P4`（Civ6LuaHelper 未收录）/ `转储` / `待补测`
- `corrected_from`：**已实装修正的 53 条 availability 原值**（Both→GamePlay 28、UI→Both 20、Both→UI 5）
- `true_name`（44 条）/ `true_path`（7 条）：文档名有误时的运行时真名与真身路径
  （例：`Player:GetUnits():SetMilitaryFormation` 真身 `Unit:SetMilitaryFormation()`；
  `Map.GetImprovementBuilder` 真身全局 `ImprovementBuilder`；`Player:SetScoringScenario` 实为 `SetScoringScenario1/2/3`）

`reference/api_enhanced.json`（5.1 MB，条目口径；与上表 `api.sqlite` 行数不同）同步标记：已核验 → `humanChecked:true` + `verifiedAt`/`verifiedScope`/
`runtimeGP`/`runtimeUI` + `[核验]` 备注行（3214 条）；存疑 → `suspect:true` + `suspectType`/`suspectPriority`
+ `[存疑]` 备注行（76 条）；无法实测 → 仅 `pendingTest:true` + `pendingReason`，**不挂核验/存疑标记、不加备注行**（143 条）。

> ⚠ `City:GetBuildQueue():GetTurnsLeft()` 保留为 `Both`；如需改回 UI 以人工结论为准（详情见该行 `verify_note`）。


### Game Files

```
Game installation: 见文首「环境路径总表」P3（游戏本体）/ P2（Mods 加载目录）
Reference: Civ6Docs.html (Civ6 root) + Civ VI Modding Companion 2.0.xlsx
```

---

## Special Thanks

[Civ VI Modding Companion 2.0.xlsx] by ChimpanG, WildW
枫叶佬的 Lua 教程: https://github.com/FYMapleLeaves/ml-civ6-lua-tutorial/tree/main

---

## 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮、Hemmelfort、枫叶、夏凉凉凉、AWAW 等
