---
name: civ6-modding
description: "Civilization VI modding: Lua scripting (UI + GamePlay), ForgeUI XML layouts, .modinfo configuration, database XML. Covers UI Add/Replace, gameplay scripts, events, and full API reference. Includes decision trees, task workflows, XML templates, validation checklists, and deep database catalogs (907 ModifierTypes, 1987 Effects, 545 Requirements) with offline SQLite query tools for reliable code generation."
version: "2.0"
author: civ6-modding
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
    database\DebugGameplay.sqlite(427表) / database\api.sqlite(5075函数) /
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

> L2 的许可是**一次性按关键词批**，不是无限授权——换新查询目标仍回 L1 重走阶梯。

## Task Routing — Read This First

**Full workflow:** `workflows.md` · **Gotchas (必读):** `gotchas.md`  
**若项目根目录存在 AGENTS.md，也需提前阅读。**

### 1. Task Type → Go To

| Type | Go To |
|------|-------|
| **UI panel** (XML + Lua) | → UI Routing ↓ |
| **Art asset conversion / Icon 尺寸规格问答**（用户素材 PNG→DDS/.tex、多图 atlas 图集/序列图拼版、XLP 实存过滤、"xxx 图标需要什么尺寸"类提问） | → `art-pipeline.md`（先读其"素材询问铁律"，≥2 张图必问拼版意图）尺寸表直接查其第三节 |
| **Gameplay logic** (Lua only) | → Gameplay Routing ↓ |
| **Game data** (units, buildings, modifiers) | → Data Routing ↓ |
| **Mixed** | → Read all relevant |
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
ADD civ/leader                          → database.md + `query_api.py`
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
ADD localization text   → database.md + DebugLocalization.sqlite (Colors/Icons) + 本地化桥接
```

### 4.1 本地化桥接（翻译/多语言任务）

`（外部翻译 skill，已不作为依赖）` 是跨项目翻译总 skill；civ6-modding 保持自足，仅在用户发起翻译/本地化任务时借调其工具，并仍以本 skill 的 Civ6 风格规则做最终校验。

- 词库查证（SQLite 优先）：`python %USERPROFILE%/.config/opencode/skills/（外部翻译 skill，已不作为依赖）/references/（已移除）/scripts/search_（已移除）.py "守岸人" --source-type term,item --field-type name --limit 10`
- 全工程审计（只读）：`python %USERPROFILE%/.config/opencode/skills/（外部翻译 skill，已不作为依赖）/scripts/civ6_text_audit.py audit --root <工程目录> --out report.txt`
- 主工程 vs 平衡补丁：`python %USERPROFILE%/.config/opencode/skills/（外部翻译 skill，已不作为依赖）/scripts/civ6_text_audit.py diff-tags --base <主工程> --balance <补丁> --out diff.txt`
- 写入（自动备份 + 元组级替换 + 写后 verify）：`python %USERPROFILE%/.config/opencode/skills/（外部翻译 skill，已不作为依赖）/scripts/civ6_locale_tool.py merge --sql Text_X.sql --changes changes.json`；`apply-edits --sql Text_X.sql --edits edits.json`
- 单命令闭环：`python %USERPROFILE%/.config/opencode/skills/（外部翻译 skill，已不作为依赖）/scripts/civ6_pipeline.py run --root <工程目录> --names names.json --workdir out --db %USERPROFILE%/.config/opencode/skills/（外部翻译 skill，已不作为依赖）/references/（已移除）/（语料库已移除）`；默认只补缺失语言，`--overwrite` 才覆盖已有译文，`--strict` 卡后置审计，`--dry-run` 只出计划。
- import 复用：`civ6_locale_tool.py` 已通过 `sys.path` 复用 `civ6_text_audit.py` 的 `parse_sql_rows` / `extract_file_rows`；主模型或子代理也可直接 import `audit_files` / `marker_drift` / `diff_tags`。
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
没查 → SELECT * FROM api_functions WHERE func_name LIKE '%Key%' OR sub_func_name LIKE '%Key%' (database\api.sqlite)
       需要参数签名 → SELECT a.* FROM api_args a JOIN api_functions f ON a.func_id=f.id
                       WHERE f.func_name='X' OR f.sub_func_name='X'
       需要示例/注释 → grep "FuncName" reference/api_enhanced.json
```

**铁律：严禁凭经验猜测 API 名称或参数** — `database\api.sqlite` 有 5075 个函数，猜错即返工。

> **小技巧：尝试复数形式** — `GetAbility` 的子方法可能在 `sub_func_name` 列为 `GetAbilities`，`UnitModifier` 可能是 `UnitModifiers`。以 `s` 结尾的 `func_name` 往往是遍历器，其实方法在 `sub_func_name` 中。

### 三问：是否通过案例验证查询到的接口用法？

查到了 API 不等于会用。写代码前确认实际的调用方式和参数：

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

从上方 Task Routing 表确定工作流模式：
- UI → UI Routing
- Gameplay → Gameplay Routing
- Data → Data Routing

### ③ Plan — 规划实现

确定文件清单、模式、API：

| 维度 | 参考文件 |
|------|---------|
| 文件清单 | 需要创建/修改哪些文件？ |
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

1. **不要跳过 Route 直接写代码** — 先确定模式
2. **不要跳过 Plan 步骤** — 先规划再写
3. **不要猜 API 签名** — 查 `database\api.sqlite`
4. **不要跳过 Validate** — 写完必须对照清单
5. **不要混用 UI/GP API** — 查可用性
6. **不要忘记热重载** — 始终处理 `OnInit(isReload)` 和 `OnShutdown()`
7. **不要通过 LuaEvents 传 C++ 对象** — 仅传基础类型

---

### Example: Full Workflow Walkthrough

**需求：** 在 LaunchBar 添加按钮，打开自定义面板显示玩家统计。

| 步骤 | 行动 | 输出 |
|------|------|------|
| ① Understand | UI 任务（按钮+面板），新功能，需跨上下文通信 | 任务定性 |
| ② Route | UI Routing → Workflow A（按钮）+ C（面板）+ E（通信）| 模式确定 |
| ③ Plan | 文件：Button.xml/.lua + Panel.xml/.lua + .modinfo；模式：BuildInstanceForControl + Fullscreen overlay + LuaEvents；API：`GetLocalPlayer()`、`Players[id]:GetProperty()` | 规划清单 |
| ④ Write | 按模板创建文件并注册到 .civ6proj | 代码完成 |
| ⑤ Validate | 对照 validation.md 检查 UI/Lua/modinfo 三项 | 验证通过 |

---

## DSH 工具集成（dsh-rgn-tools）

本技能与 DSH 工具包 `dsh-rgn-tools` 配合。**调用优先级（硬性）**：

1. **原生插件工具（首选）**：会话工具列表存在 `dsh_validate` / `dsh_validate`（opencode 全局适配插件，注册于 `~/.config/opencode/dsh-plugins/dsh-rgn-tools.mjs`）→ 直接调用；
2. **离线执行器（无原生工具时）**：node 直调下述 runner，参数语义与工具一致；
3. **最终退化**：执行器也不可用才允许手动查 skill 自带 sqlite / 人工核对，交付注明"未经 rgn_validate 校验"。

| 场景 | 原生工具 | 离线执行器 |
|------|--------|-----------|
| 查（已移除）官方译名/名词/剧情台词（`（语料库已移除）`，12 万行语料，多语言+说话人） | `dsh_validate` | `（语料执行器已移除）` |
| 校验项目 `*_RGN.sql` 引用完整性（悬空 ModifierId/Type/RequirementSetId 等，可对照基础库） | `dsh_validate` | `scripts/rgn_validate_runner.mjs` |

### rgn_validate 离线执行器

`scripts/rgn_validate_runner.mjs`：逻辑提取自 dsh-rgn-tools 插件源码，仅依赖 Node ≥22 内置 `node:sqlite`，任意终端可直接运行。默认**实跑模式**：把基础库快照到临时文件 → 真实执行项目 SQL（两遍：先跨文件 DDL 再其余语句，逐语句容错）→ 直接查库比对定义/引用全集，可识别 `INSERT INTO ... SELECT '字面量' || 列 ...` 动态拼接，并附带语法校验能力。

```bash
node "<本skill目录>/scripts/rgn_validate_runner.mjs" [目录=cwd] [文件模式=*.sql] [checkNaming=true] [--base <基础库路径>] [--static]
```

- 基础库默认 `<本skill目录>/database/DebugGameplay.sqlite`（相对脚本定位），`--base` 可覆盖；临时副本用后即删，原库只读不动
- `--static` 回退纯文本解析模式（仅认 VALUES 字面量行，SELECT 拼接会误报悬空）
- 执行错误多为基础库缺引擎专属表（如 Players 前端表、PlayerColors 新版列）或 node:sqlite 禁用双引号字符串字面量（Colors_RGN 的 `"COLOR_X"` 写法），属环境性容错项而非项目错误

### （已移除）_query 离线执行器

`（语料执行器已移除）`：移植自 dsh-rgn-tools 源码 `（已移除）Query()`，CLI 化。数据源 `D:\documents\Firaxis ModBuddy\Civilization VI\示例工程\（已移除的语料库键）\（语料库已移除）`。

```bash
node "<本skill目录>/（语料执行器已移除）" --q <关键词> [--table terms|story] [--lang zh|en|ja] [--speaker <人名>] [--exact] [--limit N]
```

- `terms` → `translations` 术语词典表；`story` → `story_dialogues` 剧情台词表（`speaker_{lang}` 模糊匹配说话人）
- 与原版差异：`--lang` 真实生效——原版固定匹配 `zh_hans` 列，本版按 lang 选择匹配列

## File Reference

### 数据查询（写前必跑）

| 查什么 | 怎么查 |
|--------|-------|
| Modifier/Requirement/Unit 等游戏数据 | `SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'` (DebugGameplay.sqlite) |
| Lua API 函数签名 | `SELECT * FROM api_functions WHERE func_name LIKE '%Key%'` (database\api.sqlite) |
| API 参数详情 | `SELECT a.* FROM api_args a JOIN api_functions f ON ...` (database\api.sqlite) |
| 列定义 / NotNull / Default | `PRAGMA table_info(TableName)` (DebugGameplay.sqlite) |
| 中英文游戏文本 | `SELECT Text FROM LocalizedText WHERE Tag='LOC_X' AND Language='zh_Hans_CN'` (DebugLocalization.sqlite) |
| 颜色/图标名 | `SELECT * FROM Colors` / `SELECT * FROM Icons` (DebugLocalization.sqlite) |
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
| `project-setup.md` | .civ6proj / .modinfo 项目结构与注册指南 | 注册文件时 |
| `conventions.md` | 命名规范/文件模板 | 写任何文件前 |
| `validation.md` | 验证清单 | 完成开发后 |
| `debug-tools.md` | 调试面板/热重载 | 调试时 |
| `gotchas.md` | **常见错误（必读）** | **写代码前扫一遍** |
| `art-pipeline.md` | 素材转换管线（单图 PNG→DDS/.tex、多图 atlas 图集/序列图拼版、Mod.Art.xml 生成、19 类图标尺寸全表）+ 素材询问铁律 | 涉及素材文件时 |

### 速查表（先扫一眼）

| 文件 | 内容 | 大小 |
|------|------|------|
| `api-cheatsheet.md` | Lua API 速查（150 函数） | 8KB |
| `query_api.py` | API 查询工具（查 api_enhanced.json，3270 函数全量） |
| `modifiers-cheatsheet.md` | Modifier/Requirement 速查 | 7KB |

### 图标尺寸速查（Art asset 问答必查此表，禁止凭记忆报尺寸）

来源：Civ6 Modding Assistant 反编译表（完整版+用法见 `art-pipeline.md` 第三节）。
问"xxx 要什么尺寸"→ 在此直接作答；做素材转换 → 在 manifest 里填对应 role，尺寸由脚本内置。

| 类别 | 尺寸 |
|------|------|
| Civilizations（civ_icon） | 22,30,32,36,44,45,48,50,64,80,128,200,256 |
| Leaders（leader_icon） | 32,45,48,50,55,64,80,256 |
| Buildings / Units / Districts | 22,32,38,50,80,128,256 |
| Resources / Wonders | 38,50,64,256 |
| Civics / Tech | 38,42,128,160 |
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

> 例外：忠诚度贴图 512/128 与 256/128（`civ6-loyalty-icon` skill）；项目可自定义增减
> （如本项目 Resources 另加 32、Product 含 45），以项目 Icons XML 现状为准。

### 深度参考（需要时 grep）

| 文件 | 用途 |
|------|------|
| `reference/api_enhanced.json` (4.2MB) | 增强 API + 中文注释 |
| `reference/events_enhanced.json` (1.2MB) | 增强事件（`query_events.py` 查询） |
| `database/schema-annotated.md` | 常用多列表注解（列定义/必填/示例值） |
| `reference/MODIFIER_ARGUMENTS.md` | Modifier 参数分类 |
| `reference/WORKSHOP_PATTERNS.md` | 高级 SQL 模式 |
| `reference/TYPE_NAME_MAPPING.md` | Type→名称 + Trait→Modifier 关联链 |
| `database/modifiers-guide.md` | Modifier 系统指南 |
| `database/scripts/sql_query_templates.sql` | SQL 查询模板 |
| `database/scripts/query_events.py` | 事件查询工具（查参数/签名/示例） |
| `database/scripts/query_api.py` | API 查询工具（查 signature/exampleCode/availability） |
| `database/scripts/requirement_reference.sql` | RequirementType 分类 |

### 数据库文件

| 数据库 | 大小 | 用途 |
|--------|------|------|
| `database/DebugGameplay.sqlite` | 10.9 MB | 游戏数据 (427 表) |
| `database/api.sqlite` | 1.5 MB | Lua API (5075 函数) |
| `database/DebugLocalization.sqlite` | 64.9 MB | 中英文文本 |
| `database/DebugConfiguration.sqlite` | — | FrontEnd 配置数据 |

### Game Files

```
Game installation: 见文首「环境路径总表」P3（游戏本体）/ P2（Mods 加载目录）
Reference: Civ6Docs.html (Civ6 root) + Civ VI Modding Companion 2.0.xlsx
```

---

## Special Thanks

[Civ VI Modding Companion 2.0.xlsx] by ChimpanG, WildW
枫叶佬的 Lua 教程: https://github.com/FYMapleLeaves/ml-civ6-lua-tutorial/tree/main
