---
name: civ6-modding
description: "文明6 mod 玩法侧总入口：Lua（UI + GamePlay）、ForgeUI XML 布局、.civ6proj / .modinfo 注册、数据库 XML/SQL、事件系统与全量 API 参考。内含决策树、任务工作流、XML 模板、验证清单，以及离线数据库目录（934 ModifierTypes / 761 EffectTypes / 327 RequirementTypes；1051 条 Requirements / 982 条 RequirementSets）+ SQLite 查询工具。专项章节：总督编写、城邦编写、平衡补丁（差分覆盖）、议程与领袖 AI、素材转换管线。发布：Steam 创意工坊上传/更新（release.md）。工具：7 个零依赖校验器（SQL 可执行性 / 引用完整性 / Types.Kind / SQL 语义反模式 / 内容清单闭合 / .lua 加载路径 / pantry 卫生）+ 双目录一致性比对。触发词：文明6、Civ6、modding、Lua、ForgeUI、UI 面板、按钮、弹窗、modinfo、civ6proj、数据库、Modifier、Requirement、PROPERTY、事件、GameEvents、LuaEvents、总督、governor、城邦、city-state、平衡补丁、balance patch、议程、agenda、创意工坊、workshop、上传、发布、校验、rgn_validate、外交背景、外交背景黑色遮罩、原版外交背景遮挡。"
version: "2.0"
author: 千与千寻瀑
license: PolyForm-Noncommercial-1.0.0 (repository root LICENSE)
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

## 0. 这份 skill 是什么

**定位**：文明6 玩法侧的总入口。从「一句话需求」到「可加载的 mod」之间的工作都从这里起步——Lua（UI 与 GamePlay）、ForgeUI XML 布局、`.civ6proj` / `.modinfo` 注册、数据库 SQL/XML、事件与 API 查询，以及交付前的校验。

**本文件覆盖**：任务路由、硬性规则、工作流程、速查表、验证脚本、参考库入口。

**外派边界**（这些任务进对应的 skill，本文件只保留路由行）：

| 任务 | 去处 |
|---|---|
| 原版美术素材引用、ArtDef / XLP / cook 层 | `civ6-art-reference` |
| 素材整理与导入（图标、立绘、素材注册链） | `civ6-asset-forge` |
| 音频整备、Wwise、bank、语音、BGM | `civ6-audio-pipeline` |
| 面向玩家的文本描述、翻译、LOC 规范 | `civ6-text-authoring` |
| HTML 原型转 ForgeUI 原生界面与纹理 | `civ6-html-ui` |
| 地标模型与 TileBase AST | `civ6-landmarks` |
| 运行时实测（FireTuner 执行 Lua） | `civ6-tuner` |
| 受限素材通道（默认禁用，需会话内授权） | `civ6-art-unpack` |

**首次阅读顺序**：

1. 家族职责与分工 → [`reference/FAMILY_INDEX.md`](reference/FAMILY_INDEX.md)
2. 本次任务属于哪一类 → 本文件 §2 任务路由
3. 工程根存在 `AGENTS.md` 时先读它，项目私有约定优先于本 skill

**本文件地图**：

| 节 | 管什么 | 什么时候读 |
|---|---|---|
| §1 硬性规则 | 工程文件写入、目录卫生、中文文件处理 | 每次动手前 |
| §2 任务路由 | 一类任务去哪个文件或哪个 skill | 接到需求的第一步 |
| §3 工作流程 | 查询阶梯、写前检索、判级、代码生成五步 | 写代码的全程 |
| §4 速查 | 事件总线、跨上下文通信（→ `reference/context-matrix.md`）、PROPERTY | 写 UI 或 GP 通信时 |
| §5 验证 | 校验脚本清单与执行器用法 | 写完代码之后 |
| §6 参考资料 | 路径总表、数据查询、文件清单、图标尺寸、数据库与 API 核验字段 | 需要查具体值时 |
| §7 附录 | 致谢、workspace 落点、Agent 约束模板 | 建立新工程或需要出处时 |

§2 回答「去哪个文件」，§6.4 回答「那个文件是什么」，两张表分工固定，不互相替代。

## 1. 硬性规则（先读）

以下三条在每一次改动里都成立，与焚诀同源，违反即任务不合格。

> 🧰 **工具先查名录（硬性）**：要写脚本做某件事之前，先看本 skill 的 [`TOOLS.md`](TOOLS.md)
> —— 本 skill 全部脚本的用途 / 用法 / 路径清单，外加本机**路径收纳**表。
> **有能用的就改它，不要重建。** 新增或改名脚本后，跑一次
> `python "<skills>/civ6-modding/tools/skill_manifest.py" civ6-modding` 刷新名录（`--check` 可做漂移检测）。
> 跨 skill 找工具先看 [`reference/FAMILY_INDEX.md`](reference/FAMILY_INDEX.md)（家族路由）；
> `tools/` 的用法细节、推荐顺序与踩坑记录见 [`tools/README.md`](tools/README.md)。

### 1.1 工程文件写入铁律（适用本家族全部 skill）

> **代码文件只能逐行编辑。脚本与工具不得编写、不得改写任何代码文件，新建的空文件同样必须从零逐行编辑。**
>
> 这一条与焚诀「禁止用程序化的方式编写或修改任何代码文件（最严厉铁律）」同源，违反即整个任务不合格。
>
> 允许由官方工具从零产生的只有三个工程文件：`.civ6sln` 与 `.civ6proj` 由 ModBuddy 产生，`.modinfo` 由 `.civ6proj` 派生。这三个文件需要在既有内容上改动某几行时，同样只能逐行编辑。
>
> 美术与音频产物由官方工具直接落盘：`.artdef`、`.xlp`、`.ast`、`.mtl`、`.dep`、`*.Art.xml`、`.dds`、`.tex`、`.png`、`.tga`、`.jpg`、`.jpeg`、`.bnk`、`.wem`、`.wav`、`.wwu`、`.wproj`，以及 `Platforms/Windows/Audio/` 下 WwiseCLI 产出的 `<Bank>.xml` 与 `<Bank>.txt`。

「工程文件」指工程核心文件夹之下的一切文件：`.civ6proj`、`.modinfo`、`*.Art.xml`，以及 `Data/`、`Text/`、`Scripts/`、`UI/`、`Mod_Adaptation/`、`ImportFiles/`、`Assets/`、`Textures/`、`XLPs/`、`ArtDefs/`、`Materials/`、`Geometries/`、`LightRigs/`、`EnvironmentLights/`、`Platforms/` 下的全部文件；`.civ6sln` 按两层目录布局位于解决方案根（工程核心文件夹的上一层，见 `project-setup.md`），同样受本铁律约束。

1. **分类判定只看目标路径的类别**：`classify(rel)` 返回 `code` / `project` / `art` / `audio` 四档，未登记的扩展名一律按 `code` 处理（失败关闭）。
   - `code`：一律抛 `CodeWriteForbidden`，不提供暂存分支。脚本只能把结果写成 `<解决方案根>/workspace/gen/reports/` 下的 JSON / TSV / Markdown 数据清单，由人逐行写入工程。
   - `project`：目标不存在时允许从零直写；目标已存在即抛 `CodeWriteForbidden` 并提示逐行编辑。
   - `art` / `audio`：允许脚本直接覆盖。
2. **`workspace/gen` 不再是代码文件的出口**：该目录只承载数据清单（`reports/` 子目录）与暂存部署副本（`Mods/`）。旧机制把改写结果转存 `gen` 再由人写回，现已取消。
3. **实现的唯一通道是 `_projwrite.py`**：`write_project_file(target, data, project_root)` 返回 `NEW`（官方工具从零新建）或 `SAME`（与既有一致，未动盘），美术与音频产物另返回 `OVERWRITE`；代码文件与已存在的工程文件一律抛 `CodeWriteForbidden`。`emit_report(name, payload, project_root)` 把结果写成 `workspace/gen/reports/` 下的数据清单并返回落盘路径，`finish()` 打印本轮写出的报告清单。该模块在本家族有六份逐字节相同的副本（`civ6-modding/art/`、`civ6-modding/tools/`、`civ6-modding/scripts/`、`civ6-asset-forge/scripts/`、`civ6-art-reference/scripts/`、`civ6-audio-pipeline/scripts/`），不得各写一份，一致性由 `scripts/check_script_write_targets.py` 体检。
4. **不受本条约束的动作**：`tools/modinfo_build.py`、`tools/cook_assets.py`、`tools/cook_dep.py`、`landmark_tool.py cook` 写的是 Mods 加载副本与构建输出目录；`tools/new_project.py` 只创建目录，并把骨架全文写进 `workspace/gen/reports/project_scaffold/`；`scripts/` 的校验器与 `database/scripts/` 的查询器只读。
5. **AI 拿到 `workspace/gen/reports/` 的数据清单之后**：读一遍内容，与工程既有文件逐段比对，再用文件编辑工具逐行写入工程对应路径。`.tex` 按工程既定的 ANSI 代码页写出（口径见 `art-pipeline.md`）。
6. 用户要求「直接用脚本改工程」时，说明本条铁律，改用第 1 条与第 5 条的做法。
7. **禁止用「先删除既有工程文件、再新建同名文件」绕过第 1 条**：`_projwrite.py` 在首次写入该工程时记下文件清单，目标已不在盘上、却出现在清单里即抛 `CodeWriteForbidden`（删除是持久意图，脚本不得重建）；`check_script_write_targets.py` 对同时 import 守卫与调用删除／改名原语的脚本判违规（删除豁免须在脚本内显式声明）。

8. **`workspace/gen` 的回收**：`prune_applied(project_root)` 拿工程侧同相对路径逐字节比对，相同即删暂存副本、并自下而上删空目录，返回 `(removed, pending, orphans)`。判据三档：工程侧存在且相同 → 回收；存在但不同 → 待写回；工程侧不存在 → 孤立（源文件已改名或删除，只报告不动）。该机制只处理历史遗留，新流程不再产生暂存副本。`gen/Mods` 与 `gen/reports` 不参与判定。
9. **`*.Art.xml` 禁止写入 `workspace/` 任何位置**（含 `gen/`、`tmp/`、`src/`）：它是 cook 的唯一输入，也是 mod 名与产物目录名的真源（`project_mod_name` 优先取它的 `<id><name>`）。`workspace/gen/` 里的副本不被任何体检覆盖 —— `find_art_xml` 只扫工程根、`check_project_hygiene.py` 只扫解决方案根顶层 —— 陈旧副本一旦被搬回工程，`<requiredGameArtIDs>` 会静默回退到旧状态，症状是全部美术与图标空白。`*.Art.xml` 的改写一律在工程根原地完成，不转存；`workspace/` 下已存在的副本按疑似遗留上报，不得搬回工程。

### 1.2 工程核心文件夹卫生（适用本家族全部 skill）

> **工程核心文件夹（`<解决方案根>/<ModName>/`）只允许出现工程文件与处理后的成品素材；中间产物、日志、脚本、备份、素材库副本一律落在 `<解决方案根>/workspace/`。**

允许出现在工程核心文件夹的内容：

- 工程描述与版本控制文件：`.civ6proj`、`*.Art.xml`、`.gitignore`、`.gitattributes`；
- mod 成品：`Data/`、`Text/`、`Scripts/`、`UI/`、`ImportFiles/` 下的源文件；
- 处理后可直接进 cook 的素材：`Textures/`、`XLPs/`、`ArtDefs/`、`Assets/`、`Materials/`、`Geometries/`、`Animations/` 下的成品文件。

不允许出现：

- `workspace/`、`gen/`、`tmp/` 与任何备份目录（`*.bak_*`、`_offproj_*`、时间戳目录、`copy_*`）；
- `Build/`、`Cooked/`、`.modinfo` 等构建产物；
- 日志（`*.log`）、调试脚本、临时图片、素材库副本；唯一例外是工程核心根顶层的 `cooker.log`（ModBuddy 与本家族 cook 工具共用的唯一一份构建日志，全解决方案不允许第二份，判据见 `civ6-art-reference/SKILL.md` 铁律五）。

中间产物落点 = `<解决方案根>/workspace/`（`gen/`、`tmp/`、`src/`、`_tools/`）。工具若在工程核心文件夹内新建了 `workspace/`，必须把产物归位到解决方案根 `workspace/` 的同一相对路径，并删除工程核心文件夹内的该目录。

**workspace 自身不留冗余（硬性）**：`workspace/` 是中间产物的落点，不是第二份工程的存放处。

- `gen/` 顶层只允许 `Mods/`（暂存部署副本）、`reports/`（待逐行写入工程的数据清单）与 `build.py modinfo` 派生的 `<ModName>.modinfo`。`reports/` 里的清单写入工程后即删除；
- 暂存部署副本按「干净重建」维护：`modinfo_build.py --deploy` 收尾用 `prune_stale()` 删掉本次没有产出的旧文件，副本恒等于本次部署结果；
- 暂存区（`workspace/gen/Mods`）内的 `<Content Include>` 文件走硬链接，与工程共用同一份字节（`modinfo_build.py` 按 `--mods-root` 是否落在暂存区自动判定，也可用 `--hardlink` / `--no-hardlink` 覆盖）。游戏 Mods 目录不用硬链接：那里在测试迭代中会被直接改动，硬链接会把改动回写进工程；
- cook 的平台轮次按全部 XLP 的 `m_AllowedPlatforms` 并集与 `Civ6.targets` 两档求交集，某档无任何声明时不跑该轮；跨平台逐字节相同的 BLP 由 `dedupe_identical_blps()` 换成指向 Windows 档的硬链接。

**删除纪律（硬性）**：代理只把「工程所需文件」新建进核心文件夹；核心文件夹内**既有**的文件，只有**本次任务自己造成错位**的才允许由代理处置，其余一律只报告、不迁移、不删除（对照 AGENTS.md「文件落盘边界与 Workspace 规范」第 2、3 条）。允许表只收录引擎通用目录与工程描述／版本控制文件，工程自建的专属目录一律走「未登记 → 由人裁决」，不靠登记放行。

**解决方案根顶层同样只允许**「工程主体目录 + `workspace/` + 解决方案文件（`.civ6sln`／`.civ6suo`／`.code-workspace`）与版本控制、Agent 规范文件」；`Cooked/`、`Docs/`、日志、调试脚本、素材库副本一律收进 `<解决方案根>/workspace/`。

体检：`python scripts/check_project_hygiene.py <解决方案根> --solution`（工程核心文件夹与解决方案根顶层一并体检，退出码 0 = 干净）；只查核心文件夹时去掉 `--solution`。

### 1.3 中文文件处理（必读）

处理含中文的 SQL/Lua/XML 时，严格执行以下规则（完整版见项目 AGENTS.md「UTF-8 与中文文件处理」）：

- 所有文件读写默认 UTF-8，不得改变原有编码、换行风格和无关内容。
- PowerShell 中读写含中文文件前先 `chcp 65001`，并设置 `[Console]::OutputEncoding` / `$OutputEncoding` 为 UTF-8。
- 查看含中文文件优先用 Read 工具，避免 PowerShell 打印中文（控制台乱码多为显示问题，不代表文件损坏）。
- 禁止 PowerShell here-string 管道/重定向/`Set-Content`/`Out-File` 写入含中文内容；不要用 `sed`/`awk` 处理含中文文件，改用 Python 或 Node.js 并显式 UTF-8 读写。
- 不要为了修编码而整文件重写、全文件格式化或全文件字符串替换。

## 2. 任务路由（Task Routing — Read This First）

先在这里定位任务，再进入对应小节或对应 skill。

> 🧭 **第一次接触这个 skill 家族？先读 `reference/FAMILY_INDEX.md`**（7 个 skill 的职责/边界/路由表 + 共用约定 + 分享状态）。

**Full workflow:** `workflows.md` · **Gotchas (必读):** `gotchas.md`  
**若项目根目录存在 AGENTS.md，也需提前阅读。**

### 2.1 Task Type → Go To

| Type | Go To |
|------|-------|
| **从零新建工程**（"建一个新 mod / 新工程骨架"、要一个可构建的 `.civ6proj`） | → `python tools/new_project.py <源工程根>\<ModName> --name <ModName>`（生成 **两层布局**：工作区根放 `.civ6sln`、同名子目录放 `.civ6proj` + **按需创建的目录** + `.gitignore`/`.gitattributes` + **`workspace/_tools/build.py` 构建入口**；`--deploy` 建完直接部署到 Mods）；格式细节见 `project-setup.md`「两层目录布局」，**GUID 必须新生成**（工具内置全网查重）。★ **目标目录不得位于 Mods 加载目录内** —— 游戏递归扫描 Mods 全树，工程里的构建产物会被当成第二个 mod（同一 GUID 两条记录），命中即退出码 2 |
| **"直接生成在 Mods 目录"**（用户只要一份游戏能加载的成品，不要工程） | → 两种情况：**工程已存在** → `python tools/modinfo_build.py <X.civ6proj> --deploy`（cook 美术 + 拷 Content + 写 modinfo + ArtDefs 同步，一条命令出成品）；**工程不存在** → `python tools/new_project.py <源工程根>\<ModName> --name <ModName> --deploy`。**不要**把工程目录取在 Mods 里 |
| **新文明 / 新领袖的数据与文本** | → `civilization-authoring.md` / `leader-authoring.md`（表清单、LOC 推导、注册位置）；**LOC 文本命名与写法 → `civ6-text-authoring`**（trait/能力文案见其 `leader-trait-text.md`）；美术→`civ6-asset-forge`、3D 引用→`civ6-art-reference`、BGM/语音→`civ6-audio-pipeline`（Wwise 侧）；文明音乐的引擎侧接线判定（`CivilizationAudioTags` + `Civilizations.artdef`）→ `reference/civ-metadata.md` §六 |
| **Config 文件改动**（增删改 `Players` / `PlayerItems` 行、选人界面物品清单与条目） | → `leader-authoring.md`「**`PlayerItems` 准入规则**」（哪些对象有资格进物品清单：限有实质 TRAIT 链的区域/建筑/单位/改良设施，资源不入列）+ `project-setup.md`「文件类型 → 注册位置对照表」（Config 文件挂 FrontEnd 仅） |
| **领袖前景（立绘）/ 背景**（选人界面立绘、加载界面背景、`Players.Portrait/PortraitBackground`、`LoadingInfo`、借用原版背景） | → `civ6-asset-forge` skill 的 **`reference/frontend-portrait.md`**（三环境对照：选人 placard / 加载界面 / 外交；含 328×935 推导与色调近似选型）；Suk 分支另见其 `reference/ui-leader-portrait.md` |
| **文明图标配套**（已做/正在做 `ICON_CIVILIZATION_*`，补忠诚度/压力镜头图标） | → `civ6-asset-forge` skill 的 **`reference/loyalty-icon.md`**（4 张 PNG + UILens 注册链；纯 2D 图集档位另走 `art-pipeline.md`） |
| **UI panel** (XML + Lua) | → UI Routing ↓ |
| **Art asset conversion / Icon 尺寸规格问答**（用户素材 PNG→DDS/.tex、多图 atlas 图集/序列图拼版、XLP 实存过滤、"xxx 图标需要什么尺寸"类提问） | → `art-pipeline.md`（先读其"素材询问铁律"，≥2 张图必问拼版意图）尺寸表直接查其第三节，图标规范化/占幅/边距规范查其第四节。★ 该管线把 `.xlp`/`.artdef`/`*.Art.xml`/`.dds`/`.tex` 直接写盘；Icons XML 属代码文件，待插入的行写进 `<解决方案根>/workspace/gen/reports/` 的数据清单，由人逐行写入工程 |
| **图标实机锯齿 / 边缘发硬 / 毛刺**（"游戏里图标不清晰"、"小尺寸档有锯齿"、接手他人图集想验中间档） | → `art-pipeline.md` **第 8.1 节「边缘质量门」**：`verify_icon_atlas.py --edge-qa` 体检 + `regen_atlas_tiers.py` 从母版重出（产物是 `.dds`，脚本直接覆盖，不必 AI 回写）。**注意结构校验查不出这类问题** |
| **原版美术素材引用 / ArtDef·XLP 链**（给新对象配原版模型、查引用链、排查美术悬空、ArtDef cook 报错或"不同步"、单位渲染残缺） | → **`civ6-art-reference` skill**（引用链与 cook 层逻辑全在该 skill 内，此处不重复） |
| **Gameplay logic** (Lua only) | → Gameplay Routing ↓ |
| **Game data** (units, buildings, modifiers) | → Data Routing ↓ |
| **总督（Governor）**（新增总督 / 晋升树 / 就职回合 / 立绘注册 / 名额扩容） | → `governor-authoring.md`（美术规格另见 `civ6-asset-forge` skill 的 `reference/governor-art.md`） |
| **城邦（City-State）**（自定义城邦 / 选单不出现 / 宗主国加成 / 使者层级） | → `citystate-authoring.md` |
| **文明周边数据收尾**（百科资料卡 `CivilizationInfo` / 城市名 `CityNames` / 市民名 `CivilizationCitizenNames` / 出生关联 `StartBias*` / 文明音乐（`CivilizationAudioTags` + `ArtDefs/Civilizations.artdef`）/ 知名地名 `NamedMountains·NamedRivers` 等） | → **`reference/civ-metadata.md`**（各表 schema、取值域、写作要点、数量建议、最小检查清单） |
| **Asset Editor 字段名 / 调试查日志 / 枚举取值**（"AE 里那个框叫什么"、"Database.log 怎么看"、"Culture 有哪些值"、"忠诚度材质的字段名"） | → **`reference/editor-and-enums.md`**（AE 字段速查 / 调试三板斧 / `Cultures.artdef` 取值表 / 忠诚度 3D 链字段） |
| **平衡补丁 / 差分覆盖**（改主工程数值、解挂载、覆盖文本的补丁 mod） | → `balance-patch.md` |
| **换行 / EOL 归一化**（"CRLF 还是 LF"、行尾混了、`.gitattributes` 怎么写、接手他人工程先体检） | → `gotchas.md` **§68「换行分层铁律」**（唯一真源）+ `scripts/normalize_eol.py`（默认只报告；`--fix` 只写美术与音频产物，代码文件的换行偏离清单落 `<解决方案根>/workspace/gen/reports/`；`--repo-skill` 清理 skill 自身仓库仍直写） |
| **工坊封面 / 预览图**（做封面、"封面上的中文别画错"、"封面太模糊"） | → 排版走 `tools/workshop_cover.py`（确定性 CJK 排版）；**预览图缩放执行端在 `art/make_workshop_preview.py`**（Lanczos 阶梯 + unsharp、默认 512、已达标直通不二次缩放；见 `art-pipeline.md` 第九·补节）；发布流程见 `release.md` §3.2 |
| **音频**（导入 / 素材整备 / 响度均衡 / Wwise / bank / 语音 / BGM） | → **`civ6-audio-pipeline` skill**（音频全流程在该 skill 内，此处不重复） |
| **运行时验证**（"这个 API 实际行为是什么"、复现脚本报错、PROPERTY/modifier 实测） | → **`civ6-tuner` skill**（FireTuner TCP 4318，在运行中的对局里执行 Lua；静态校验回答不了的问题走这里） |
| **面向玩家的文本描述**（新建 / 改 / 译 / 润色 / 校验文案、LOC tag 命名与后缀变体、`[ICON_x]`/`[COLOR]`/`[NEWLINE]` 标记、相邻加成写法、**开幕颂词（领袖加载介绍词 `LOC_LOADING_INFO_LEADER_*`）**、外交文本、领袖能力描述） | → **`civ6-text-authoring` skill**（文本权威规范唯一真源；含风云变幻口径 zh 语料 `zh_corpus.sqlite` + 六大类规范文档 + `SKILL.md` 入口） |
| **翻译 / 多语言文本**（补缺失语言、审计语言齐缺失、主工程 vs 补丁文本 diff） | → **`civ6-text-authoring`**（语言代码 / 标记必须保留 / 合并进原 SQL / 写后复核，口径在该 skill；本 skill §2.5 仅保留本地化参考库构建工具） |
| **Mixed** | → Read all relevant |
| **Steam 创意工坊上传/更新** | → `release.md` |
| **工坊介绍 / 条目依赖 / 更新说明**（首传写介绍、更新写 changeNote、声明官方 DLC 与工坊作品依赖） | → `workshop-intro.md`（`release.md` 的姊妹分册：它管上传什么文字，`release.md` 管怎么传） |
| **"能不能从这个文件调用那个文件的函数"** / **"跨文件、跨上下文、跨端怎么通信"** / **"UI 怎么调 GP 的函数"** | → **`reference/context-matrix.md`**（唯一真源：术语 / 通道矩阵 / 症状表 / 检索词） |
| **"UI 收不到 GP 的消息"** / **`attempt to call a nil value`** / **`attempt to index a nil value`** / **`function expected instead of nil`** | → **`reference/context-matrix.md`** 症状表，再进 `gotchas.md` §36–§38 |
| **Debug** | → `debug-tools.md` + `gotchas.md` |

### 2.2 UI Routing

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

### 2.3 Gameplay Routing

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

### 2.4 Data Routing

```
ADD new unit/building/district
├─ 列定义 → PRAGMA table_info(TableName) (DebugGameplay.sqlite)
├─ 写法   → database.md
├─ 有取代关系（*Replaces 表）时先取子表清单 → `python scripts/replacement_subtables.py <工程根> --diff`（见 gotchas.md G15b）
├─ ModifierType 查询 → SELECT * FROM Modifiers WHERE ModifierType LIKE '%Key%'
├─ ModifierArguments → SELECT Name,Value FROM ModifierArguments WHERE ModifierId='X'
├─ RequirementType   → SELECT * FROM Requirements WHERE RequirementType LIKE '%Key%'
└─ 类型名中英对照    → SELECT UnitType FROM Units WHERE UnitType LIKE '%Key%'

Modifier/PROPERTY 设计
├─ 作用域决策 → 见下文"写前三问"的「三问的执行材料」（先按该节第一步判级）
├─ ATTACH 模式 → reference/WORKSHOP_PATTERNS.md
├─ 参数分类   → reference/MODIFIER_ARGUMENTS.md
├─ **参数取值域（该 Effect 的参数能填什么）** → `python database/scripts/query_effect_args.py --effect <EFFECT_X>`
│    （或 `--modifier <MODIFIER_X>` 自动解析到 Effect；`--arg <参数名>` 反查）
└─ **某效果原版怎么实现的（照抄现成链）** → 查 `DynamicModifiers ⋈ Modifiers ⋈ ModifierArguments`
     + `TraitModifiers`/`CivilizationTraits` 等绑定表（见下"写前先搜现成实现"）

ADD tech/civic/policy   → database.md
ADD resource/feature    → database.md
REMOVE/MODIFY data      → database.md "Removing Data" + project-setup.md "LoadOrder"（优先查 .civ6proj）
ADD localization text   → database.md + DebugLocalization.sqlite (SkillAnnotation_Colors/Icons) + 本地化桥接
                         生成文本时按内置映射直接补 `[ICON_x]`（不需要等用户说明）→ `python art/iconify_text.py <工程根> --audit` / `--check` / `--write`
                         （`--write` 把待改内容写进 `<解决方案根>/workspace/gen/reports/`，由人逐行写入工程）
                         双向引用体检（图标正向 + `{LOC_x}` 反向 + 配置孤儿 tag）→ `python scripts/check_text_refs.py <工程根>`
                         DLC 文本查不到 → `python database/scripts/build_localization.py --report`
```

### 2.5 多语言文本 / 本地化 → **全部路由到 `civ6-text-authoring`**

> ★ **文本处理的权威规范已独立为 `civ6-text-authoring` skill**
> （本机：`C:\Users\Administrator\.agents\skills\civ6-text-authoring`）。
> 凡涉及**面向玩家的文本描述**——新建 / 修改 / 翻译 / 润色 / 校验文案、LOC tag 命名与后缀变体、
> `[ICON_x]` / `[COLOR]` / `[NEWLINE]` 标记、相邻加成写法、**开幕颂词（领袖加载介绍词 `LOC_LOADING_INFO_LEADER_*`）**、外交文本——
> **一律路由到该 skill 处理**；本处不再重复口径。
>
> 该 skill 自带**风云变幻口径的简体中文语料**（27,998 tag，`reference/zh_corpus.sqlite`，六大类规范文档），
> 比本 skill 的 `DebugLocalization.sqlite` 更贴合「以风云变幻为准」——后者不应用 `<Delete>`、
> 对 DLC 只补缺不覆盖，存在 14 条取值差 / 18 条集合差（差异明细见该 skill 的 `reference/zh_diff_report.txt`）。
> 入口与六大类路由见 `civ6-text-authoring/SKILL.md`。

**本 skill 只保留**本地化参考库的**构建工具与查询口径**（`database/scripts/build_localization.py`）：

> 主库 `database/DebugLocalization.sqlite`（Base + EXP1 + EXP2 + 全部领袖/文明 DLC，
> 规则 `EXP2 > EXP1 > base`、其它领袖包只补缺不覆盖，**排除情景与 Mode**；336,125 行）与
> 模式库 `database/Localization_Mode.sqlite`（8 个 GAMEMODE，独立成库只加不覆盖；15,417 行）。
> 两库在 `database/` 下**只在本机保存、不入 git**（可从游戏文件数十秒重建）。
>
> ```bash
> python database/scripts/build_localization.py --report            # 只读：分段 + 分层 + 差异统计
> python database/scripts/build_localization.py --rebuild --dry-run # 一键重建两库（预演）
> python database/scripts/build_localization.py --rebuild           # 实际重建
> ```
>
> ⚠️ **不要试图用游戏运行时缓存补全**：`%LOCALAPPDATA%\...\Cache\DebugLocalization.sqlite`
> 实测恒为 base 15,229 tag，**连当前加载的 mod 文本都没有**——它不反映"加载了什么"。
> 权威分段判据在 `.modinfo`：新式看 `<ActionCriteria>` 里 `ConfigurationId=GAMEMODE_*`，
> 旧式（仅 `VikingsScenario`）看 `<Properties><RuleSet>` 的 `RULESET_SCENARIO_*`；
> 模式清单的权威表是 `DebugConfiguration.sqlite → GameModeItems`（8 行），**不在 Gameplay 库**。

> 文本与图标/颜色的对照数据在本 skill 内：`database/DebugLocalization.sqlite`（官方文本 + 手工标注侧表
> `SkillAnnotation_Colors` / `SkillAnnotation_Icons`）与 `reference/sources/` 的两份社区常量表。
> **文本类规范的唯一真源是 `civ6-text-authoring`。**

---

## 3. 工作流程

需求落到代码的全程：先按 §3.1 决定能查什么，再按 §3.3 判定要查多少，按 §3.5 的五步推进。

### 3.1 查询阶梯（无结果时的强制流程，禁止跳步）

```
L0  skill 家族正文检索（最先，零许可）
    在 <skills>\civ6-modding、civ6-tuner、civ6-asset-forge、civ6-art-reference、
    civ6-audio-pipeline、civ6-html-ui、civ6-landmarks、civ6-text-authoring 的 *.md 里按「检索词表」逐个搜；
    命中即用，不再往下走
    （受限通道 civ6-art-unpack 不在检索范围；新增成员在此与下方 Select-String 同步登记）
    ⚙ 结论型知识（能不能调用、走哪个通道、有没有这种用法）**只在 md 正文里**，
      sqlite 库存的是表结构与函数签名，L1 对这类问题无解 —— 先在 L0 搜正文
    │  无结果
    ▼
L1  skill 自带参考库（零许可）
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

**L0 的一条命令**（把「检索词表」整表喂给 ripgrep；词表真源见 `reference/context-matrix.md` 第六节）：

```powershell
Select-String -Path "<skills>\civ6-modding\*.md","<skills>\civ6-tuner\*.md","<skills>\civ6-asset-forge\*.md","<skills>\civ6-art-reference\*.md","<skills>\civ6-audio-pipeline\*.md","<skills>\civ6-html-ui\*.md","<skills>\civ6-landmarks\*.md","<skills>\civ6-text-authoring\*.md" -Pattern "跨上下文|跨端|跨脚本|跨文件|调用函数|全局函数|互不可见|独立沙箱|LuaEvents|ExposedMembers|EXECUTE_SCRIPT|ReportingEvents|SendLuaEvent|RequestPlayerOperation|GetProperty|SetProperty|attempt to call a nil value|attempt to index a nil value"
```

> ⚠ 检索范围是**显式枚举**：受限通道 `civ6-art-unpack` 永远不在 L0 检索范围（无授权禁止读取）；
> 家族新增成员时在此处与上方 L0 清单同步登记，门禁 skill 除外。

### 3.2 写前先搜现成实现（硬性 · 先查再写）

写任何 Modifier / Requirement **之前**，先在官方库里搜「这个效果原版是怎么实现的」——
**别凭记忆拼 ModifierType + 参数**。原版几乎总有同类效果可以照抄，照抄的链路一定是对的。

```bash
# ★ 首选：一条命令直接列出「某对象/某效果的完整 Modifier 链」（含参数与条件集）
python database/scripts/search_impl.py --object 农场              # 按对象（中文名或 Type）
python database/scripts/search_impl.py --object TRAIT_CIVILIZATION_KHMER_BARAYS
python database/scripts/search_impl.py --modifier ADJUST_PLOT_YIELD   # 按关键词反查谁在用它
python database/scripts/search_impl.py --effect EFFECT_ADJUST_PLOT_YIELD
python database/scripts/search_impl.py --list-objects             # 看支持哪些对象类别
```

它会输出 `ModifierId [EffectType] 参数: …` + `作用域` + 条件集（含 `REQUIREMENTSET_TEST_ANY`
这类**或**逻辑），并自动展开两条嵌套链：**ATTACH_MODIFIER**（递归取 `ModifierId`）与
**GRANT_ABILITY**（取 `AbilityType` → 展开该能力下属全部 Modifier）。递归自带**防环 + 限深**
（官方数据里 ATTACH 链存在成环写法）。

需要手写 SQL 时，等价写法：

```sql
-- 1) 找效果：反查「哪些 Modifier 用了这个 Effect」
SELECT d.ModifierType, d.CollectionType, m.ModifierId
FROM DynamicModifiers d JOIN Modifiers m ON m.ModifierType = d.ModifierType
WHERE d.EffectType LIKE '%YIELD%';

-- 2) 看参数：这个 Modifier 到底填了什么
SELECT Name, Type, Value FROM ModifierArguments WHERE ModifierId = '<上一步的 ID>';

-- 3) 看条件：它的 RequirementSet 由哪些 Requirement 组成
SELECT * FROM RequirementSetRequirements WHERE RequirementSetId = '<上一步的 ReqSet>';
SELECT * FROM RequirementArguments WHERE RequirementId = '<上一步的 ReqId>';
```

- **参数该填什么值** → `python database/scripts/query_effect_args.py --effect <EFFECT_X>`
  （给参数签名 + **`DatabaseKind`→`Types` 的权威取值全集** + 官方实际用过的值）；
- **Modifier 挂在哪张表** → `DynamicModifiers.CollectionType` 决定作用域，绑定表见
  `reference/WORKSHOP_PATTERNS.md`；不同对象挂载路径不同（Trait 走 `TraitModifiers`、
  文明走 `CivilizationTraits` 中转、总督晋升走 `GovernorPromotionSets` 中转）；
  完整绑定路径表见 `search_impl.py` 的 `OBJECT_TYPES`（6 种 kind）。

> 教训（来自 ModTools 5.4 的实践，2026-09 吸收）：它的校验器在报「未知 EffectType」时
> **会把操作指引一起打出来**——「用 `search <效果词>` 查现成实现，不要凭记忆断言」。
> 把方法论编进错误信息，比写在文档里更不容易被忽略；本 skill 的 `rgn_validate` 在检测到
> Modifier/Effect 类悬空引用时也会追加同样的下一步指引。
>
> ⚠️ 反向教训：ModTools 的注册表把总督晋升写成 `GovernorPromotions.GovernorType`，而本库
> schema 里**没有这一列**（真实结构是中间表 `GovernorPromotionSets`）——照抄外部工具的
> 表/列假设前，先 `PRAGMA table_info` 核对。

---

### 3.3 写前三问（按指令明确程度分级）

同一份 skill，对「已经指名文件与做法的指令」和「只有一句需求」该花的检索量差一个数量级。
动手前先按用户这一轮指令的文本判级，再按级别决定问几问、能读什么。

#### 第一步：判级

判据只看用户这一轮指令的文本，不看工程里有什么、不看 skill 里有什么。四样：

| 代号 | 判据 |
|---|---|
| 甲 | 指令写出工程内的目标文件路径 |
| 乙 | 指令写出要改的标识符（函数名、ModifierId、表名、Type 名等） |
| 丙 | 指令写出可照抄的参照，并且跟到具体文件（「参考兄弟项目 X」未跟到文件时不算） |
| 丁 | 指令写明改动边界（改哪些文件、哪些不动） |

| 级别 | 条件 |
|---|---|
| 一级 | 甲乙丙丁齐全 |
| 二级 | 有甲、有乙，缺丙或缺丁 |
| 三级 | 有甲、无乙 |
| 四级 | 无甲 |

判级出现歧义时取检索更少的一级。

#### 第二步：按级执行

| 级别 | 一问 SQL 能否解决 | 二问 API 是否查证 | 三问 接口用法是否查证 | 参考库之外允许的读取 | 改动范围 |
|---|---|---|---|---|---|
| 一级 | 跳过 | 跳过 | 跳过 | 甲指向的文件；丙指向的文件里丙指向的那个符号所在的段落；照做受阻时允许追加读取一个直接相关文件，读完即返回 | 甲文件里的乙符号 |
| 二级 | 跳过（丙已经决定用 SQL 还是 Lua） | 只确认乙用到的 API 存在，每个关键词一次查询命令 | 在本工程内搜同款写法，每个关键词一次搜索命令 | 甲文件；本工程 | 甲文件内 |
| 三级 | 必答 | 必答 | 查 skill 对应章节一节 | 甲文件；skill 对应章节 | 甲所在一类文件内 |
| 四级 | 必答 | 必答 | 必答，并且走「查询阶梯」L0→L1 | 按「查询阶梯」 | 指令涉及的文件 |

三级与四级禁止通读兄弟工程与原版实现；需要通读时先说明读哪个文件、用途是什么，得到许可再读。

三问的详细执行材料（一问确认清单、Modifier 作用域速查、`query_api.py` 命令与陷阱、三问的四类查证入口）在下方「三问的执行材料」一节，供三级与四级使用。

#### skill 参考库的使用口径（与级别无关）

**范围**。随 skill 分发的一切内容：`<skill>\*.md`、`<skill>\reference\**`、`<skill>\database\*.sqlite`、`<skill>\database\schema-annotated.md`、`<skill>\database\scripts\**` 里既定的查询命令、`<skill>\tools\**`。

**读取不设限**。四个级别都可以读，不占用「单次检索上限」，不需要事先说明用途，命中即照它给出的命令与参数执行。

**只取结论，不追来源**。查到一条结论就直接照它写代码。禁止为了确认这条结论去追它背后的机制与来源，具体包括：

- 不读 `database\api-verification-*\raw\` 一类的实测原始数据，那是结论的产生过程
- 不打开游戏本体的 `Base\Assets\**`、`DLC\**`、工坊参考件去核对结论，即「查询阶梯」的 L2 仍然按级别受控
- 不反查同一结论在别的 skill 里的第二条记录，一条结论在参考库里出现过一次即采信
- 不为了弄清「引擎为什么这样」去读核验说明、字段来源注释、反编译记录

例外：两条结论互相冲突、或结论与本工程现状冲突时，允许就冲突点追源核实一次，只读产生冲突的那一条的来源，核实完即回归本口径。

**禁止扩散**。参考库里搜不到某个标识符时，按当前级别的规则处理（升级或停下询问），不因为「参考库允许读」就把检索范围扩到参考库之外。

#### 第三步：各级共用的四条约束

**停止条件。** 手上材料足以把整段代码一次写完整时，检索立即停止。判断标准是能否一次写出完整可运行的代码。

**单次检索上限。** 每个未决问题在检索前先列出关键词清单（与该问题直接相关，通常 1~3 个），清单内每个关键词允许一次查询动作，计数范围是参考库之外的检索。清单在检索前一次列定，中途不得追加；同一概念的同义改写不算新关键词，禁止对同一关键词更换说法重试，禁止转而查看别的工程。某个关键词未命中时进入下一条阶梯；整份清单用尽仍无命中，视为该问题未决，停下询问或按「失败升级」处理。

**改动边界默认值。** 指令未列出的文件一律不改，文档同步也不做；唯一例外是校验器点名的必须修复项（如改名产生的悬空引用），其最小同步修改计入改动边界。

**失败升级。** 按当前级别写完并执行校验，校验未通过时允许升一级重试一次；仍未通过则升到四级。书写类失败（语法错误、拼写错误、格式错误、静默报错、单次输出被截断）就地修正，不计入升级次数。

#### 覆盖开关

用户在本轮任务里说过「不调研」「不额外调研」「不做验证」「直接做」中的任意一句，当次任务直接按一级执行，参考库之外的读取全部关闭，仅保留参考库读取。

反向同样成立：用户在本轮指令中明确授权完全读取 / 全面调研（如「随便读」「放开查」「彻底调研一下」）时，当次任务不受判级的读取范围、「单次检索上限」与通读禁令束缚，按用户授权的范围执行；「改动边界默认值」与「工程文件写入铁律」不受此开关影响，改动边界仍以指令为准。


### 3.4 三问的执行材料（三级 · 四级用）

#### 一问：SQL 能搞定吗？

```
能 → 查表确认，写 SQL，不用 Lua
不能 → 进二问
```

**确认清单：**
- 列是否在表中？ → `PRAGMA table_info(TableName)`（DebugGameplay.sqlite）
- NotNull 列是否都填了？ → 检查上一步输出中 `notnull=1` 且 `dflt_value=NULL` 的列
- 有默认值的列是否真的需要改？ → 不需要就省略，保持数据库默认值；注册物品只写实际需要的列，不要为了让完整列清单齐全而把默认值逐列显式补一遍（逐列默认值查阅 `database/schema-annotated.md`）
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

#### 二问：写 Lua 前查 API 了吗？

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

#### 三问：接口用法查证了吗？（示例 / 签名 / 同类模式 / 陷阱）

写代码前确认实际调用方式与参数：

- API 调用示例 → `grep "FuncName" reference/api_enhanced.json`
- 事件回调签名 → `python database/scripts/query_events.py --show EventName`
- 同类 Modifier 模式 → `reference/WORKSHOP_PATTERNS.md`
- 常见陷阱 → `gotchas.md`

---

### 3.5 Code Generation Workflow

所有代码生成任务遵循此流程。

#### ① Understand — 理解需求

写任何代码前，先澄清：
- 任务类型：UI（XML+Lua）/ Gameplay（Lua）/ Data（SQL/XML）/ 混合
- 范围：新增 / 修改 / 修复
- 通信需求：需要 UI↔GP 吗？需要跨脚本传数据吗？（→ `reference/context-matrix.md` 通道矩阵）
- 持久化：需要跨存档保存状态吗？（→ PROPERTY）

#### ② Route — 确定走向

按 §2.1 Task Routing 表选定模式，进入对应 Routing 小节。

#### ③ Plan — 规划实现

确定文件清单、模式、API：

先按 §3.3「写前三问」判级；一级与二级按判级结果直接写，下表只对三级与四级生效。

| 维度 | 参考文件 |
|------|---------|
| 检索量 | §3.3「写前三问」第一步判级 |
| 文件清单 | `project-setup.md`「文件清单同步」+ 本次 diff 涉及的文件 |
| 模式选择 | `workflows.md`（A-J） |
| API 查询 | `api-cheatsheet.md` / `database\api.sqlite` |
| 事件选择 | `events.md` |
| 命名规范 | `conventions.md` |
| 多列表格填表 | **预先** `database/schema-annotated.md`（列定义/必填/示例值） |

#### ④ Write — 编写代码

遵循参考文件写代码，完成后注册到 `.civ6proj` / `.modinfo`（仅 XML/SQL/Lua 必须写文件清单；ImportFiles 图片/视频、Platform 音频 bank 等媒体资产走专门导入或用户手动导入，其余文件 ModBuddy 引擎自动打包无需写入 —— 见 project-setup.md「文件清单同步」）。

**写取代映射之后必做一步**：本次写的 SQL 里出现 `BuildingReplaces` / `DistrictReplaces` / `UnitReplaces` 时，映射写完、子表开写之前跑一次 `python scripts/replacement_subtables.py <工程根> --diff`，按它列出的未覆盖表逐表复刻，口径见 `gotchas.md` G15b。被取代对象的子表行不会被引擎继承，缺一张表就是一类行为静默丢失、加载期零报错。用户点名「补全 xx 的全部表格」时，用 `--object xx --sql` 取原版全部行。

#### ⑤ Validate — 验证

按 `scripts/README.md` 的标准顺序跑完全部脚本（含改过 `.lua` 时必跑的 `check_lua_context.py`，必须 0 问题）；对照 `validation.md` 清单逐项确认。

---

#### 反模式（Anti-Patterns）

1. **不要混用 UI/GP API** — 查可用性
2. **不要忘记热重载** — 始终处理 `OnInit(isReload)` 和 `OnShutdown()`
3. **不要通过 LuaEvents 传 C++ 对象** — 表格按引用传递（端内跨文件实时同步），C++ 对象（userdata）禁止

---

## 4. 速查

写 UI 与 GP 通信时的对照表，口径真源是 `reference/context-matrix.md`。

### 4.1 事件总线（Event System Quick Decision）

| 所在位置 | 用 | 必须移除？ |
|---------|----|-----------|
| UI Lua context | `Events.*` | YES — `.Remove()` in `OnShutdown()` |
| UI Lua context | `LuaEvents.*` | No — auto-cleanup |
| GamePlay Lua script | `LuaEvents.*` | No — GP 文件间跨文件派发可达；表格按引用传递 |
| GamePlay Lua script | `GameEvents.*` | No — loaded once per game |
| GamePlay Lua script | `Events.*` | 引擎事件在 GP 侧同样可用；`.Remove()` 非必需（脚本每局加载一次） |

> ⚠ **`Events.*` / `GameEvents.*` / `LuaEvents.*` 是三条互不镜像的总线**（2026-09 修订）：同一个逻辑事件**通常只在其中一张上有效**，用错总线**静默无效**（不报错、不回调）。
> **禁止凭印象选总线 —— 查 `reference/events_enhanced.json` 的 `eventSystem` 字段**（1081 条全覆盖：`LuaEvents` 481 / `Events` 470 / `GameEvents` 130），或 `python database/scripts/query_events.py --show <事件名>` 看 `System` 列。
> 注意 `GameEvents.*` 上**存在一批非自定义事件、且它们在 `Events.*` 上无对应条目**（`OnDistrictConstructed`/`CityConquered`/`PolicyChanged`/`PlayerTurnStarted` 等，130 条中 82 条 `availability=GamePlay`）三条总线**按事件划分**，不按「引擎 vs Lua」划分 —— 永远查表、不要按来源猜。
> 另：`GameEvents.X` 对任意名字都自动建 table，**不能**用 `type()` 判断事件是否存在——只有 `type(Events.X)` 是权威探针。
> `availability: "None"` 的 48 条**哪一层都订阅不到**（UI 侧 `.Add()` 会 nil 崩溃）。
> 详见 `gotchas.md` §7 与 `events.md` Gotcha 8。

### 4.2 数据传递速查

#### 跨脚本通信

> **★ 前提：每个 `.lua` 文件都是一个独立上下文**（`AddGameplayScripts` 的 GP 文件、`<Context Name="X">` 的 UI 文件皆然），各自一份全局、互不可见——同端文件之间也不例外。下面列的都是运行期桥接手段，口径真源 `reference/context-matrix.md`。

> **跨端（UI↔GP）四个通道：`EXECUTE_SCRIPT`（UI→GP 动作）、`ReportingEvents.SendLuaEvent`（GP→UI 推送）、PROPERTY 读取（GP 写、UI 延后读的被动辅助）、暴露函数 `ExposedMembers`（双向；仅 UI 按钮回调禁用，需要同步返回值时优先）。端内跨上下文：`LuaEvents`（首选）或暴露函数。直接读写另一上下文全局仍不可达。真源 `reference/context-matrix.md`。**

完整口径（术语 / 通道矩阵 / 症状表 / 实测记录 / 检索词表）见 **`reference/context-matrix.md`**。

| 方向 | 方式 | 场景 |
|------|------|------|
| UI ↔ UI / GP ↔ GP | LuaEvents（表格按引用传递；禁传 C++ 对象） | 端内跨文件广播/通知（首选；也可用暴露函数） → `reference/context-matrix.md` |
| UI → Gameplay | EXECUTE_SCRIPT | 按钮触发 GP 动作 |
| Gameplay → UI | ReportingEvents.SendLuaEvent | 数据变更推送（接收方拿到的是副本） |
| GP ↔ UI 被动读 | PROPERTY 直接读（跨端） | 查询，非按钮回调；GP 写、UI 延后读，属被动辅助 |
| GP ↔ UI（需同步返回值） | 暴露函数 `ExposedMembers` | 双向、可直接调用；**仅 UI 按钮回调禁用** |
| 直接调用另一上下文全局 | 无 | **不可达**，须经上面的通道桥接，见 `reference/context-matrix.md` |

#### PROPERTY 系统速查

| 读渠道 | 适用范围 | 方式 |
|--------|---------|------|
| `REQUIREMENT_PLOT_PROPERTY_MATCHES` | 仅地块 — 条件检测 | 引擎内置 |
| `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH Key=` | 仅单位战斗力 | 引擎内置 |
| 全部其他 | 玩家/城市/单位/地块任意 | 仅 Lua: `entity:GetProperty(key)` |

**写入：** SQL `MODIFIER_PLAYER_ADJUST_PROPERTY` / `SINGLE_CITY_*` / `UNIT_*` · Lua `entity:SetProperty(name, val)`

不存在 `CITY_PROPERTY_MATCHES` 或 `UNIT_PROPERTY_MATCHES` — 城市/玩家 PROPERTY 做条件必须走 Lua。

---

## 5. 验证与工具

代码与数据写完之后的口径：先跑工具，再按清单确认。

### 5.1 DSH 工具集成（dsh-rgn-tools）

**调用优先级（硬性）**：

1. **原生插件工具（首选）**：会话工具列表存在 `dsh_validate`（opencode 全局适配插件，注册于 `~/.config/opencode/dsh-plugins/dsh-rgn-tools.mjs`）→ 直接调用；
2. **离线执行器（无原生工具时）**：node 直调下述 runner，参数语义与工具一致；
3. **最终退化**：执行器也不可用才允许手动查 skill 自带 sqlite / 人工核对，交付注明"未经 rgn_validate 校验"。

| 场景 | 原生工具 | 离线执行器 |
|------|--------|-----------|
| 校验项目 `*_RGN.sql` 引用完整性（悬空 ModifierId/Type/RequirementSetId 等，可对照基础库） | `dsh_validate` | `scripts/rgn_validate_runner.mjs` |

### 5.2 自带校验/运维脚本（`scripts/`，全部零依赖 + 带退出码）

**完整清单与标准验证顺序见 `scripts/README.md`。** 改完代码/数据后按序跑：

| 脚本 | 查什么 | 与谁的职责互补 |
|------|--------|---------------|
| `scripts/check_sql_exec.py` | **可执行性** —— 非法转义（`'…\'s…'`）导致**整条 INSERT 报废**；遇错即停，同文件后续语句块也全不执行 | ★ `rgn_validate` 查不到：语句没跑起来 = 数据没进库 = 引用不悬空 |
| `scripts/rgn_validate_runner.mjs` | **引用完整性 + 本次改动 Modifier 单复数/作用域（--scope-check）** —— 悬空 ID / 单复数误用 | 与上面互补 |
| `scripts/check_types_kinds.py` | `INSERT INTO Types` 的 `Kind` 是否引擎合法枚举 | 打包不报错、加载期才丢弃 |
| `scripts/check_sql_antipatterns.py` | **语义反模式** —— 语法合法但恒假/恒错：`LIKE ('%A%' OR '%B%')`、`WHERE … = NULL`、前置列填了特色对象（D 类，口径见 `gotchas.md` G15） | ★ 前三个都抓不到：它跑得起来、引用也闭合，只是**意思错了** |
| `scripts/check_proj_content.py` | `<Content Include>` ↔ 磁盘**双向闭合**（悬空清单项 / 漏登记） | 见 `gotchas.md` §3「打包 vs 加载」 |
| `scripts/check_pantry.py` | **pantry 卫生** —— `.tex` 位置 / 重名 / depot 路径 / 非 ASCII / `.tex`↔`.dds` 配对 | 开 AssetEditor 前必跑 |
| `art/verify_tex_class.py` | **`.tex` 类别 vs XLP 注册类**是否匹配（如 `UITexture` 包里的贴图必须 `UserInterface`） | ★ 唯一能防「类别写错 → cooker 静默替换成 error asset」的机械防线；`check_pantry`/`verify_icon_atlas`/`align_tex_format` 都不查它 |
| `scripts/clear_ae_cache.py` | 清 AssetEditor 依赖缓存（动过贴图后**必须**清，否则验证结论是缓存假象） | 同上 |
| `scripts/verify_trees.py` | 两棵目录逐字节相同（源 ↔ Mods 副本） | 双目录一致性 |
| `scripts/check_lua_registration.py` | **`.lua` 注册体检** —— 按角色（UI 上下文 / include 扩展件 / GP 脚本）判定哪些 `.lua` 实际不会被加载；角色判定在 `scripts/_lua_roles.py`（与下一个脚本共用） | 改过 `.lua` 后必跑（`scripts/README.md` 标准顺序第 ⑥ 步） |
| `scripts/check_lua_context.py` | **跨上下文体检** —— UI 侧 `GameEvents` / UI 侧 `SetProperty` / 跨端注册触发 `LuaEvents` / 调用不在 include 闭包内的全局函数 / `ExposedMembers` 使用点（仅报告，不阻断）；端内 `LuaEvents` 首选、跨端四通道，口径真源 `reference/context-matrix.md` | 新增或改过 `.lua` 后必跑（标准顺序第 ⑦ 步） |
| `scripts/check_doc_anchors.py` | **文档指针一致性** —— 跨上下文结论行是否都带 `context-matrix.md` 指针、指针行是否带排他结论 | 改过家族 md 或移动真源文件后 |
| `scripts/normalize_eol.py` | **换行归一化** —— 按 `gotchas.md` §68「资产类 LF / 代码·配置类 CRLF」体检（默认只报告；`--fix` 只写美术与音频产物，代码文件的清单落 `workspace/gen/reports/`） | 接手他人工程、批量改过行尾后 |


### 5.3 rgn_validate 离线执行器

`scripts/rgn_validate_runner.mjs`：逻辑提取自 dsh-rgn-tools 插件源码，仅依赖 Node ≥22 内置 `node:sqlite`，任意终端可直接运行。默认**实跑模式**：把基础库快照到临时文件 → 真实执行项目 SQL（两遍：先跨文件 DDL 再其余语句，逐语句容错）→ 直接查库比对定义/引用全集，可识别 `INSERT INTO ... SELECT '字面量' || 列 ...` 动态拼接，并附带语法校验能力。

```bash
node "<本skill目录>/scripts/rgn_validate_runner.mjs" [目录=cwd] [文件模式=*.sql] [checkNaming=true] [--base <基础库路径>] [--static] [--scope-check]
```

- 基础库默认 `<本skill目录>/database/DebugGameplay.sqlite`（相对脚本定位），`--base` 可覆盖；临时副本用后即删，原库只读不动
- `--static` 回退纯文本解析模式（仅认 VALUES 字面量行，SELECT 拼接会误报悬空）
- 执行错误多为基础库缺引擎专属/前端表（如 Players、PlayerItems）或校验器限制（Config 文件按 gameplay schema 校验，如 DuplicateLeaders.Domain；Types.Hash UNIQUE 未模拟引擎哈希；temp 表两遍执行顺序），属于环境性容错项，与项目错误无关
- **基础库防污染**：参考库必须与官方 schema 1:1。改过 DB 后跑 `python database/scripts/audit_schema_drift.py`（有漂移 exit 1）；校验器也会对 DynamicModifiers/Modifiers/ModifierArguments/Types 做列断言并告警
- `--lang` 按所选语言匹配文本列（默认 `zh`，可选 `en` / `ja`）

## 6. 参考资料（File Reference）

需要时查，不必通读。§6.2 是写数据前的查询入口，§6.4 是「哪个文件干什么」，其余按需取用。

### 6.1 环境路径总表（必读 · 分享自举）

> **使用顺序：`<skill目录>\local_paths.json`（若存在）＞ 下表硬编码值。**
> 任一路径 `Test-Path` 失败 → 按"自动纠正"列依次探测；全部失败 → **询问用户一次**，
> 把结果写入 `<skill目录>\local_paths.json`（个人环境文件，分享时不携带、不覆盖他人）后继续。
> 「本机硬编码」列是整理人机器的示例值，换机器一律走「自动纠正链」或 `local_paths.json`。

| # | 用途 | 本机硬编码 | 自动纠正链 |
|---|---|---|---|
| P1 | ModBuddy 源工程目录 | `D:\documents\Firaxis ModBuddy\Civilization VI` | ① `%USERPROFILE%\Documents\Firaxis ModBuddy\Civilization VI` → ② 询问用户 |
| P2 | Mods 加载目录 | `D:\documents\My Games\Sid Meier's Civilization VI\Mods` | ① 注册表 `UserPath`＋`\Mods` → ② `%USERPROFILE%\Documents\My Games\Sid Meier's Civilization VI\Mods` → ③ 询问用户 |
| P3 | 游戏本体（UI/Lua/XML/Text 官方原文） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI` | ① 注册表 `ToolsPath` 去尾部 ` SDK` → ② Steam `libraryfolders.vdf` 找 appid 289070 → ③ 询问用户 |
| P4 | SDK Assets（artdef/解包素材） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` | ① 注册表 `AssetsPath` → ② P3＋` SDK Assets` → ③ 询问用户 |
| P5 | SDK 工具（ModBuddy/MSBuild） | `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK` | ① 注册表 `ToolsPath` → ② P3＋` SDK` → ③ 询问用户 |
| P6 | 创意工坊参考件 | `F:\Steam\steamapps\workshop\content\289070` | ① libraryfolders.vdf → ② 询问用户 |

> ⚠ **P2 是游戏递归扫描的加载根**：任何位置的 `*.modinfo` 都会被收成一条 mod 记录。
> **源工程目录绝不允许放在 P2 之内**（否则工程里的构建产物会被当成第二个 mod，同一 GUID
> 两条记录）。判定由 `tools/_paths.py` 的 `assert_source_tree()` 提供，四个写入工具入口已接入；
> 依据见 `gotchas.md`「Mods 加载树里不能放工程」。

注册表键（P2/P4/P5 同源，一条读三值）：
`HKCU\SOFTWARE\Firaxis\Civilization6_ModBuddy\2013\DialogPage\Firaxis.VisualStudio.Projects.Civ6.OptionsPages.OptionsDialogPage`
→ `UserPath / AssetsPath / ToolsPath`

### 6.2 数据查询（写前必跑）

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

### 6.3 参考其他工坊作品（默认顺序）

路径见 §6.1「环境路径总表」：**P1 = ModBuddy 源工程目录（首选）、P6 = 创意工坊参考件（次选）**。
禁止使用 `.lnk` 快捷方式地址，直接使用总表解析出的文件夹路径。

### 6.4 核心文件

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
| `workshop-intro.md` | **工坊介绍与更新说明**：三栏口径（甲预置模板 / 乙用户提供 / 丙从 `Text/` 提取）/ 首传与更新的流程分流 / 依赖声明（工坊 ID 与官方 DLC 分置）/ changeNote 风格与排序 / 长度上限 | **首传写介绍、更新写说明、声明依赖时** |
| `conventions.md` | 命名规范/文件模板 | 写任何文件前 |
| `reference/context-matrix.md` | **Lua 上下文口径唯一真源**：术语 / 通信矩阵（端内 LuaEvents 首选、跨端四通道含暴露函数）/ 症状表 / 实测记录 / 检索词表 | **写任何跨文件、跨端、跨上下文的通信代码前** |
| `validation.md` | 验证清单 | 完成开发后 |
| `debug-tools.md` | 调试面板/热重载 | 调试时 |
| `gotchas.md` | **常见错误（必读）** | **写代码前扫一遍** |
| `art-pipeline.md` | 素材转换管线（单图 PNG→DDS/.tex、多图 atlas 图集/序列图拼版、Mod.Art.xml 生成、19 类图标尺寸全表）+ 素材询问铁律 + **图标规范化专属章节（第四节，每类 Icon 对应规范，Units 已验证）** | 涉及素材文件时 |

### 6.5 速查表（先扫一眼）

| 文件 | 内容 | 大小 |
|------|------|------|
| `api-cheatsheet.md` | Lua API 速查（150 函数） | 8KB |
| `modifiers-cheatsheet.md` | Modifier/Requirement 速查 | 7KB |

### 6.6 图标尺寸速查（Art asset 问答必查此表，禁止凭记忆报尺寸）

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

### 6.7 深度参考（需要时 grep）

| 文件 | 用途 |
|------|------|
| `reference/FAMILY_INDEX.md` | **家族索引**：6 个 civ6 skill 的职责/边界/路由表 + 共用约定 + 分享状态 |
| `reference/api_enhanced.json` | 增强 API + 中文注释（核验标记见「API 核验字段」） |
| `reference/events_enhanced.json` (1.2MB) | 增强事件（`query_events.py` 查询） |
| `database/schema-annotated.md` | 常用多列表注解（列定义/必填/示例值） |
| `reference/MODIFIER_ARGUMENTS.md` | Modifier 参数分类 |
| `database/scripts/query_effect_args.py` | **Effect/Modifier 参数取值域查询**（参数签名 + `DatabaseKind`→`Types` 权威全集 + 官方实际用值；支持 `--effect` / `--modifier` / `--arg` / `--search` / `--dump-json`） |
| `database/scripts/search_impl.py` | **「某对象/效果原版怎么实现」反查**（16 类对象 × 6 种绑定路径；递归展开 ATTACH / GRANT_ABILITY / 嵌套 REQSET，自带防环限深；支持 `--object` / `--modifier` / `--effect` / `--bm25` / `--json`；整句自然语言走 BM25 兜底，约 1-3 分钟建索引） |
| `database/scripts/build_localization.py` | **分层合成两个本地化文本库**（主库 / 模式库）：从游戏安装按 `.modinfo` 权威分段（main/mode/scenario），主库 `EXP2>EXP1>base` + 既有库补缺，Mode 独立成库只加不覆盖；`--rebuild` 一键重建两库 / `--report` 只读 / `--build-main` / `--build-mode` / `--augment-main`；不删行、不动 schema、不应用 `<Delete>`。两库均**不入 git**（可重建），见 `database/README.md` §零 |
| `reference/WORKSHOP_PATTERNS.md` | 高级 SQL 模式 |
| `reference/TYPE_NAME_MAPPING.md` | Type→名称 + Trait→Modifier 关联链 |
| `database/modifiers-guide.md` | Modifier 系统指南 |
| `database/scripts/sql_query_templates.sql` | SQL 查询模板 |
| `database/scripts/query_events.py` | 事件查询工具（查参数/签名/示例） |
| `database/scripts/query_api.py` | API 查询工具（主源 `api.sqlite`，**父项与子项一并查**；含 availability/核验字段，示例/注释来自 JSON 富化） |
| `database/scripts/requirement_reference.sql` | RequirementType 分类 |
| `database/scripts/query_civ6_db.py` | 通用 DB 查询 CLI（SQLite 封装；`--check-id <TYPE>` 可做新 Type 的 id 冲突前置检查） |
| `database/CALIBRATION_LOG_2026-08.md` | 2026-08 **全量校准验证日志**（库补全 / 来源标注 / API 核验的取证过程与结论） |
| `database/source_index.sqlite` | **官方行级来源索引**（`row_source` 457 表 / 5.8 万行）+ 人工 `dlc_dependency`（12 行 Mode/Scenario DLC 依赖；版本真值镜像见 `database/annotations/dynamic_modifiers_dlc.json`） |
| `reference/modifiers-catalog/` | **Modifier 分域参考**（16 篇 EffectType 分类 + patterns A-G + 实案库；来源 ModTools 5.4 MIT，吸收边界见 FAMILY_INDEX §八） |
| `reference/ui-panels/` | **官方 UI 面板 XML+Lua 双文件对照**（17 篇：InGame 结构 / PopupDialog / InstanceManager / Support 库 / HUD / 外交 / 全屏 / 样式；来源同上） |
| `release/docs/checklist.md` · `release/docs/troubleshooting.md` | 工坊发布**核对清单**与**异常诊断**（`release.md` 引用） |
| `tools/workshop_intro.py` | 工坊介绍**丙栏**提取（`scan` 列 tag / `build` 出 `[code]` 主体与规格 JSON）、**标题来源**（`titles`：取 `.civ6proj` 的 `..._MOD_TITLE` 并可回填规格 JSON）与**依赖清单**（`deps`：官方 DLC 与工坊 ID 分列） |
| `release/scripts/draft_note.py` | 更新记录草稿：按「上传基线 → HEAD」的 git 差异产出 `changeNote` 与台账行（`workshop-intro.md` §三 引用） |
| `release/templates/intro.spec.example.json` | 三栏口径的规格 JSON 样板 |
| `release/templates/intro-presets.md` | 甲栏预置模板（点赞横幅 8 语言 + QQ 群行），**本机自留、分享时不带**（`.gitignore` 排除） |
| `reference/sources/` | 外部参考件（Civ VI Modding Companion、原版议程表、原版图标标记全表、颜色/图标常量、StretchMode 统计）；出处与许可见该目录 README |
| `art/bin/texconv.exe` | 随包内置的 PNG→DDS 转换器（Microsoft DirectXTex，MIT，v2026.5.8.1）；探测顺序见 `art/bin/README.md` |
| `art/make-icon.ps1` | 白色扁平图标生成（本地扩散模型 + 阈值抠底），依赖需自备，参数见 `reference/imagegen-channels.md` |
| `reference/imagegen-channels.md` | 文生图渠道现状与"扩散模型不能出中文"等实测坑 |
| `reference/sources/` | 外部参考件（Civ VI Modding Companion、原版议程表），出处与许可见该目录 README |
| `database/api-verification-2026-09-08/` | **API 核验原始记录**（FireTuner 实跑输出、全量 CSV、人工复核清单）；核验列的真源，见该目录 README |

### 6.8 数据库文件（**2026-09-18 起全部随仓库分发**）

| 数据库 | 用途 |
|--------|------|
| `database/DebugGameplay.sqlite` | 游戏数据（427 表）；`rgn_validate` 的基础库、SQL 查询主库 |
| `database/api.sqlite` | Lua API（4857 行；含 2026-09-08 FireTuner 实测核验列，见下节；**原始记录随包**：`database/api-verification-2026-09-08/`） |
| `database/DebugLocalization.sqlite` | 官方本地化文本（**12 语言**）+ `SkillAnnotation_*` 手工标注侧表 |
| `database/DebugConfiguration.sqlite` | FrontEnd 配置数据（`Maps` 等） |
| `database/source_index.sqlite` | 官方行级来源索引 + 人工 `dlc_dependency` 标注 |
| `database/api-verification-2026-09-08/` | API 核验原始记录 |

> 逐库说明、可再生性、缺库影响与重建口径见 `database/README.md`。
> 文中各处行数、计数与大小为建库时点快照，现值以查询为准。

### 6.9 API 核验字段（2026-09-08 FireTuner 全量实测 · UI/GP 范围存在性）

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



### 6.10 Game Files

```
Game installation: 见 §6.1「环境路径总表」P3（游戏本体）/ P2（Mods 加载目录）
Reference: Civ6Docs.html (Civ6 root) + Civ VI Modding Companion 2.0.xlsx
```

---

## 7. 附录

### 7.1 Special Thanks

[Civ VI Modding Companion 2.0.xlsx] by ChimpanG, WildW
枫叶佬的 Lua 教程: https://github.com/FYMapleLeaves/ml-civ6-lua-tutorial/tree/main
原版图标标记全表 by 号码菌（`reference/sources/civ6-icon-tags.sql`）
texconv（PNG→DDS）来自 [microsoft/DirectXTex](https://github.com/microsoft/DirectXTex)（MIT，随包内置 `art/bin/`）
工坊上传器 [Jianbao233/Civ6WorkshopUploader](https://github.com/Jianbao233/Civ6WorkshopUploader)（MIT，**不随包**，用
`release/scripts/ensure_uploader.ps1` 从上游获取）
`civ6-html-ui` by 糸七（HTML→ForgeUI 原生界面）
`civ6-art-unpack` by 千川白浪（受限素材通道）

---

### 7.2 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮、Hemmelfort、枫叶、夏凉凉凉、AWAW、糸七、千川白浪 等
- 随包的素材/模板来自社区前人的整理与分享；本 skill 的管线、工作流与实测结论为整理人所作

### 7.3 workspace 落点

> 本文所有 `workspace/`、`<解决方案根>/workspace/` 均指 `.civ6sln` 所在解决方案根下的 `workspace/`。

---

### 7.4 Civ6 Agents.md 通用约束模板

#### 📍 模板路由（必读）

**本 skill 内维护 Civ6 专用 Agent 通用约束模板**，作为所有 Civ6 mod 项目的 **AGENTS.md「焚诀」部分**派生源头：

📄 **模板位置**: `{{SkillsRoot}}\civ6-modding\templates\agents-rules-canonical.md`

> ⚠️ **AI 自动同步授权**: 用户给予 AI 一次性永久授权，允许在执行任务期间检测并同步该模板到当前工程的 `AGENTS.md`（最多每天一次），保持 `焚诀` 部分与最新版模板一致。

#### 🔀 同步规则

```
技能更新 → AI 读取模板最新版本 → 对比本工程 AGENTS.md 焚诀部分 → 有差异则自动合并
```

**同步粒度：**
- ✅ **操作约束层**（Git 阈值、提交审计、语言规范等）→ 高频同步（最多每天一次）
- ❌ **项目级约定层**（领袖缩写、双目录配置等）→ 不自动同步，新工程创建时从 `reference/agents-best-practices.md` 派生示例

#### 📚 参考文档

- **最佳实践参考**: `reference/agents-best-practices.md` ← 本机已有项目的通用约定提炼
- **本地化示例**: 见本项目 `AGENTS.md` 的「焚诀」节，由 `<!-- FENJUE:BEGIN -->` 与 `<!-- FENJUE:END -->` 标记界定

> 💡 **使用建议**: 新工程首次创建时，AI 应从模板提取通用约束 + 从最佳实践参考提取项目约定，自动生成完整的 `AGENTS.md`
