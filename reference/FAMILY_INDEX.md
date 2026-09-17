# Civ6 skill 家族索引（Family Index）

> 一页式导航：**什么任务 → 加载哪个 skill**，以及各 skill 的边界、共用约定与分享状态。
> 生成于 2026-09-14 的 12 工程横向审查；2026-09 家族整合后由 9 个 skill 收缩为 **5 个**。
> 各 skill 的详细内容以各自 `SKILL.md` 为准。

---

## 一、家族总览（5 个 skill）

| Skill | 版本 | 管什么（一句话） | 体量 |
|---|---|---|---|
| **`civ6-modding`** | 2.0 | **玩法侧总入口 + 发布**：Lua（UI + GP）、ForgeUI XML、`.civ6proj`/`.modinfo`、数据库 XML/SQL、事件系统、API 参考，以及 **Steam 创意工坊发布（`release.md`）**；含 934 ModifierTypes / 761 EffectTypes / 327 RequirementTypes（1051 条 Requirements / 982 条 RequirementSets）离线库与查询工具 | 173.3 MiB（含 4 个 SQLite 快照） |
| `civ6-art-reference` | 1.3 | **引用原版美术素材**：ArtDef/XLP 四层引用链 + **cook 层**（pantry 解析→产物归一化→警告即静默降级→源/产物差异分级） | 1.40 MiB |
| `civ6-audio-pipeline` | 1.3 | **音频全流程**：素材整备→核验→按类别响度均衡→Wwise 工程直改→自动注册（语音 / BGM / 普通 sfx 三类路由） | 4.93 MiB |
| `civ6-tuner` | — | **FireTuner 运行时验证**（TCP 4318）：在运行中的对局里执行 Lua，回答"这个 API 实际行为是什么" | 0.11 MiB |
| **`civ6-asset-forge`** | 1.0 | **2D 美术素材总入口**：由原 `civ6-loyalty-icon` + `civ6-promotion-icon` + `civ6-governor-art` + `civ6-leader-2d` **四个 skill 合并而成**——忠诚度/宗教压力图标、总督素材、2D 领袖立绘注册（各成一册 `reference/*.md`）；2026-09-17 增第 ⑤ 类 **UI 领袖立绘 / 选人界面背景（Suk 适配）** 与第 ⑥ 类 **历史时刻插画（MomentIllustrations）**。⚠ **单位晋升图标（原第 ③ 类）生成管线已于 2026-09-18 作废**，只保留规格 `reference/promotion-icon-sizes.md` | 14.6 MiB |

> **体量口径**（2026-09-18 实测）：**不含 `.git/` 与 `__pycache__/`**，1 MiB = 1,048,576 字节
> （`Get-ChildItem -Recurse -File | Measure-Object Length -Sum` 同口径）；asset-forge 的 14.6 MiB
> 含 18 张官方历史时刻 PSD 模板。

> **两条整合线**（2026-09）：
> - `civ6-workshop-uploader` → 并入 **`civ6-modding/release.md`**（发布同属工程管理；脚本落在 `civ6-modding/release/scripts/`、模板 `release/templates/`、清单 `release/docs/`）。
> - `civ6-loyalty-icon` + `civ6-promotion-icon` + `civ6-governor-art` + `civ6-leader-2d` → 合并为 **`civ6-asset-forge`**。

> **家族外的依赖**：本家族 5 个 skill 自洽，**不依赖任何家族外 skill**；多语言文本按 `SKILL.md` §4.1 的
> Civ6 侧规则自行处理（工具自备）。

> 🧰 **每个 skill 都有 `TOOLS.md`（可复用工具名录）** —— 要写脚本做某件事之前先查它：
> 本 skill 全部脚本的用途 / 用法 / 路径 + 本机**路径收纳**表。**有能用的就改它，不要重建。**
> 新增/改名脚本后跑 `python "<skills>/civ6-modding/tools/skill_manifest.py" <skill>` 刷新名录。
>
> 跨 skill 的通用工具（构建 `.modinfo`、交付包体检、工坊元数据、封面合成、本地生图）
> 集中在 **`civ6-modding/tools/`**，用法与踩坑见 `civ6-modding/tools/README.md`；
> 本机路径单一真源是 `civ6-modding/tools/_paths.py`（`python _paths.py` 自检）。

---

## 二、路由表：任务 → skill

| 你要做的事 | 加载 |
|---|---|
| 写 UI 面板 / 按钮 / 弹窗（XML + Lua） | `civ6-modding` → `ui-lua.md` / `ui-controls.md` / `xml-templates.md` |
| 写玩法逻辑（GP Lua）、事件、PROPERTY、UI↔GP 通信 | `civ6-modding` → `gameplay-lua.md` / `events.md` / `gotchas.md` |
| 增删改游戏数据（单位/建筑/区域/政策/资源/改良） | `civ6-modding` → `database.md` + `schema-annotated.md` |
| 写议程、外交好感、领袖 AI 偏好 | `civ6-modding` → `agenda-authoring.md` |
| **新增总督 / 改晋升树 / 就职回合 / 名额扩容** | `civ6-modding` → **`governor-authoring.md`**（美术另见 `civ6-asset-forge` 的总督素材分册） |
| **新增城邦 / 城邦不进选单 / 宗主国加成 / 使者层级** | `civ6-modding` → **`citystate-authoring.md`** |
| **写平衡补丁 / 差分覆盖 mod** | `civ6-modding` → **`balance-patch.md`** |
| 注册 `.civ6proj` / `.modinfo` / 文件清单 | `civ6-modding` → `project-setup.md` |
| 给新对象配**原版模型素材** | `civ6-art-reference` |
| 排查 ArtDef 双端不同步 / cook 报错 / 单位渲染残缺 | `civ6-art-reference` → `reference/cook-layer.md` |
| PNG → DDS/`.tex`、图标尺寸问答、图集拼版 | `civ6-modding` → `art-pipeline.md` |
| 导入语音 / BGM / 音效、bank、响度均衡 | `civ6-audio-pipeline` |
| **做 2D 领袖立绘（立绘纸片人注册链）** | `civ6-asset-forge` → `reference/leader-2d.md` |
| **适配 Sukritact 选人界面（suk selection / 领袖选择界面 2D 立绘+背景）** | `civ6-asset-forge` → `reference/ui-leader-portrait.md` |
| **做历史时刻插画（MomentIllustrations / 时代得分图 / Moment_*）** | `civ6-asset-forge` → `reference/moment-illustration.md` |
| **做忠诚度 / 宗教压力图标** | `civ6-asset-forge` → `reference/loyalty-icon.md` |
| **问单位晋升图标（promotion icon）尺寸 / 格式 / 注册** | `civ6-asset-forge` → `reference/promotion-icon-sizes.md`（**仅规格**；生成管线已作废） |
| **做总督素材（徽章 / 头像小图标 / 立绘 / 边缘透明渐变）** | `civ6-asset-forge` → `reference/governor-art.md` |
| **运行时验证 API 行为 / 复现脚本报错** | `civ6-tuner` |
| **上传 / 更新 Steam 工坊** | `civ6-modding` → **`release.md`**（脚本 `release/scripts/`） |
| 多语言翻译与本地化审计 | `civ6-modding` → `（本地化工具已移除）/`（已内化）；语料库查证为可选外部依赖 |

> `civ6-asset-forge` 的素材类分册在 skill 内以 `reference/*.md` 组织：`leader-2d.md` / `loyalty-icon.md` / `governor-art.md` / `ui-leader-portrait.md` / `moment-illustration.md` / `promotion-icon-sizes.md`（最后一册**只有尺寸规格**——类别③ 的生成管线已作废）；总入口与该 skill 自己的路由表见其 `SKILL.md`。
> 原 `civ6-leader-2d` / `civ6-loyalty-icon` / `civ6-promotion-icon` / `civ6-governor-art` 四个名字**已废止**，一律改走 `civ6-asset-forge`。

**混合任务**：先按本表定位主 skill，再按需读其它 skill 的对应章节；`civ6-modding/SKILL.md` 的 Task Routing 是完整决策树。

---

## 三、边界：各 skill **不**做什么

| Skill | 明确不做 |
|---|---|
| `civ6-modding` | 不承载美术引用链与 cook 层逻辑（→ `civ6-art-reference`）；不承载音频 bank 生成（→ `civ6-audio-pipeline`）；不承载 2D 素材合成与注册链（→ `civ6-asset-forge`）。**工坊发布在本 skill 内**（`release.md`），不外派 |
| `civ6-art-reference` | **不解包任何 `.blp`**（一律按名引用）；2D UI 图标默认不处理（仅悬空时补链）；领袖立绘 / 忠诚度图标 / 晋升图标 / 总督素材走 `civ6-asset-forge` |
| `civ6-audio-pipeline` | 不做 3D/2D 美术资产；音频以外的注册一律回 `civ6-modding/project-setup.md` |
| `civ6-tuner` | 只做**运行时**验证；静态校验走 `civ6-modding` 的 `rgn_validate` / `scripts/*.py`，不在本 skill 重复 |
| `civ6-asset-forge` | **素材处理前必须先询问用户是否提供素材**（默认只生成注册文件）；只管美术规格与素材合成，**玩法注册链**仍在 `civ6-modding`（如总督玩法见 `governor-authoring.md`）；2D UI 宗教图标（`IconTextureAtlases` 270px 图集）不在范围（→ `civ6-modding/art-pipeline.md` §图标规范化）。五类素材见其 `SKILL.md` §一（③ 晋升图标只剩尺寸规格） |

### 3.1 本家族**不负责**的方向（职责真空 —— 先看这里，别在 5 个 skill 之间空转）

下面三类**没有任何一个 civ6 skill 负责**。列在这里是为了让你在 30 秒内知道"这条路本家族走不通"，
而不是把 5 个 skill 逐个翻完才发现。确需自建时，只能走家族外的资料 / 工具链。

| 方向 | 你会卡在哪一步 | 建议去哪找 |
|---|---|---|
| **3D 模型与动画制作**（新建 mesh / 骨骼 / 动画；改单位 idle·攻击动画） | `civ6-art-reference` 只做「找到相近功能的原版对象、完整复制其美术引用链」——**它不造新模**；`civ6-asset-forge` 明确「不做 3D 模型」。一旦新单位要一把原版没有的武器、新资源要全新 3D 模型，本家族**没有入口** | 家族外工具链：AssetEditor 之外的建模 / 动画工具（Blender + Civ6 导入器一类）；`.fgx` / `.wig` 平面模型与 Animation / `.ast` 3D 动画本家族均无制作文档。可拆解工坊同类 mod、参考社区教程（Civ VI Modding Companion） |
| **UI 字体 / 字形**（游戏内中文显示成方块、想换 UI 字体、自定字号字形） | Task Routing 里「字体」**零落点**；`civ6-modding/art-pipeline.md` 的「字体图集（FontIcon）」是**文本内嵌图标**的注册，**不是**字体本体 / CJK 字形覆盖——照它做会发现完全不是同一件事 | 家族外：字体与字形覆盖属引擎资源，只能覆盖游戏字体包或做覆盖式 UI mod。先看原版 `Base\Assets\UI\Fonts`（路径见 `civ6-modding/SKILL.md` 环境路径总表 P3），再参考社区的字体覆盖 mod |
| **地图与场景制作**（自定义地图 / Scenario / 改地图生成脚本） | `civ6-modding` 里唯一的 Map 落点是**只读查询**（`SELECT * FROM Maps` @ `DebugConfiguration.sqlite`，见其「数据查询」表）——那是查原版地图列表，**不是**做地图 | 家族外：**WorldBuilder**（ModBuddy 之外的独立工具，随官方 SDK）+ `.Civ6Map` 与 Scenario 数据。本家族只在"把做好的地图注册进 `.civ6proj` / `.modinfo`"这一步可用（`civ6-modding/project-setup.md`） |

---

## 四、跨 skill 共用约定

### 4.1 环境路径总表（`civ6-modding/SKILL.md` 文首）

| # | 用途 | 本机 |
|---|---|---|
| P1 | ModBuddy 源工程目录 | `D:\documents\Firaxis ModBuddy\Civilization VI` |
| P2 | Mods 加载目录 | `D:\documents\My Games\Sid Meier's Civilization VI\Mods` |
| P3 | 游戏本体 | `F:\Steam\steamapps\common\Sid Meier's Civilization VI` |
| P4 | SDK Assets（artdef / 解包素材） | `…\Sid Meier's Civilization VI SDK Assets` |
| P5 | SDK 工具（ModBuddy/MSBuild） | `…\Sid Meier's Civilization VI SDK` |
| P6 | 创意工坊参考件 | `F:\Steam\steamapps\workshop\content\289070` |

**分享自举**：`<skill目录>/local_paths.json`（若存在）＞ 硬编码值 ＞ 自动探测链 ＞ 询问用户。
`local_paths.json` 是**个人环境文件**（已进 `.gitignore`），分享时**不携带、不覆盖他人**。

### 4.2 查询三级阶梯（`civ6-modding/SKILL.md`）

```
L1 skill 自带参考库（SQLite / JSON / md）—— 最先，零许可
   ↓ 无结果 → ⛔ 强制停下询问用户
L2 官方本机文件（P3/P4/P6）—— 需一次性按关键词获批
   ↓ 仍无结果 → ⛔ 第二次停下询问
L3 联网 —— 未获批准前禁止任何 websearch/webfetch
```

### 4.3 校验工具（`civ6-modding/scripts/`）

零依赖、参数化、带退出码。**三者互补，缺一不可**：

```
check_sql_exec.py    「语句跑不跑得起来」← 一条语句报废 = 数据没进库 = 引用不悬空
rgn_validate         「引用闭不闭合」
check_types_kinds.py 「Kind 是不是合法枚举」← 打包不报错，加载期才丢弃
```
另有 `check_proj_content.py`（清单双向闭合）、`check_pantry.py`（pantry 卫生）、
`clear_ae_cache.py`（清 AE 缓存）、`verify_trees.py`（双目录逐字节比对）。
**完整清单与标准验证顺序见 `civ6-modding/scripts/README.md`。**

### 4.4 发布工具（`civ6-modding/release/`）

工坊上传/更新专用，随 `release.md` 一并并入 `civ6-modding`：

```
release/scripts/build.ps1       构建非 Trimmed Civ6WorkshopUploader（勿加 -p:PublishTrimmed=true）
release/scripts/validate.ps1    上传前 validate（exit 0 才允许 upload）
release/scripts/upload.ps1      上传/更新（默认 30 分钟超时 + 日志落盘）
release/scripts/verify.ps1      上传后 Steam API 验证（比对 time_updated / hcontent_file）
release/scripts/cleanup.ps1     真成功后删临时 workspace（仅允许删 $env:TEMP\civ6-ws\ 之下）
release/scripts/find_item_id.ps1  从 Steam 日志反查工坊条目 ID
release/scripts/clash_api.ps1    Clash Verge 命名管道 API 壳
release/scripts/clash_proxy.py   测节点延迟并自动选择最佳节点
release/templates/workshop.update.json  仅更新内容时的 workshop.json 最小模板
release/docs/checklist.md · release/docs/troubleshooting.md  核对清单与异常诊断
```

> 铁律：`0 of 0 bytes -- success` **不等于**成功——必须用 `verify.ps1` 确认 `hcontent_file` 变了才算真更新。

### 4.5 中文文件处理（所有 civ6 skill 通用）

UTF-8 读写；不改编码/换行；PowerShell 先 `chcp 65001`；**查看中文优先用 Read 工具**；
禁止用 PowerShell here-string / 重定向 / `Set-Content` 写含中文内容；不用 `sed`/`awk`。

---

## 五、版本控制与分享状态

| Skill | git | 说明 |
|---|---|---|
| `civ6-modding` | ✅ | 含 `.gitignore`（排除 SQLite 快照与 `local_paths.json`）与 `.gitattributes`（钉 LF） |
| 其余 4 个 | ✅ | 2026-09-14 纳入版本控制，各含 `.gitignore` / `.gitattributes` |

**分享包形态**（历史做法，见 `.agents/skills/civ6-modding_2026-08-06_*.zip`）：

- **full**：含数据库快照（`DebugGameplay.sqlite` 58.2 MiB / `DebugLocalization.sqlite` 62.1 MiB / `api.sqlite` / `source_index.sqlite` …）—— 接收方开箱即用；
- **clean**：只出文档 + 脚本，接收方自行放数据库。

> ⚠ 分享前注意：数据库是**官方 schema 快照**，改动过要跑 `database/scripts/audit_schema_drift.py` 防污染（有漂移 exit 1）。

---

## 六、本次横向审查的产出（2026-09-14）

审查范围：`示例工程` + 12 个兄弟工程；7 路并行只读审查 + 主模型对高风险结论独立复核。

| 产出 | 位置 |
|---|---|
| 完整审查报告（含用户裁决更正、证据链） | 作者本地工程记录（不随 skill 分发）；结论已全部回灌下列文件 |
| **P0 纠错**：`Events.*` / `GameEvents.*` 总线路由错误结论 | `SKILL.md` / `gotchas.md` §7 / `events.md` |
| **P1 新章节** | `governor-authoring.md` / `citystate-authoring.md` / `balance-patch.md` |
| **P2 扩充** | `gotchas.md` §44–64（LoadOrder 阶梯 / Criteria 三态 / 引擎数据细节 / 双端 API 差异）；`project-setup.md`（LoadOrder 分层、两轴、工程骨架） |
| **P3 工具** | `scripts/` 六个新校验器 + `scripts/README.md` |
| art 侧 | `civ6-art-reference`：pantry 注意事项 + `cook-layer.md §2.3` 的双端不一致分级判定（换行分层的执法口径已统一到 `gotchas.md` §68） |

---

## 七、家族整合记录（2026-09）

| 动作 | 结果 |
|---|---|
| `civ6-workshop-uploader` 并入 `civ6-modding` | 内容成为 `release.md`；脚本/模板/清单移入 `civ6-modding/release/`；Task Routing 新增一行「Steam 创意工坊上传/更新 → `release.md`」 |
| 4 个美术素材类 skill 合并 | `civ6-loyalty-icon` + `civ6-promotion-icon` + `civ6-governor-art` + `civ6-leader-2d` → `civ6-asset-forge` |
| 家族规模 | **9 → 5** |
