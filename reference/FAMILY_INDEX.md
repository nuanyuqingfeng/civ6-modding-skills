# Civ6 skill 家族索引（Family Index）

> 一页式导航：**什么任务 → 加载哪个 skill**，以及各 skill 的边界、共用约定与分享状态。
> 生成于 2026-09-14 的 12 工程横向审查；2026-09 家族整合后由 9 个 skill 收缩为 **5 个**。
> 各 skill 的详细内容以各自 `SKILL.md` 为准。

---

## 一、家族总览（5 个 skill）

| Skill | 版本 | 管什么（一句话） | 体量 |
|---|---|---|---|
| **`civ6-modding`** | 2.0 | **玩法侧总入口 + 发布**：Lua（UI + GP）、ForgeUI XML、`.civ6proj`/`.modinfo`、数据库 XML/SQL、事件系统、API 参考，以及 **Steam 创意工坊发布（`release.md`）**；含 907 ModifierTypes / 1987 Effects / 545 Requirements 离线库与查询工具 | 218 MB（含 4 个 SQLite 快照） |
| `civ6-art-reference` | 1.3 | **引用原版美术素材**：ArtDef/XLP 四层引用链 + **cook 层**（pantry 解析→产物归一化→警告即静默降级→源/产物差异分级） | 1.45 MB |
| `civ6-audio-pipeline` | 1.3 | **音频全流程**：素材整备→核验→按类别响度均衡→Wwise 工程直改→自动注册（语音 / BGM / 普通 sfx 三类路由） | 5.12 MB |
| `civ6-tuner` | — | **FireTuner 运行时验证**（TCP 4318）：在运行中的对局里执行 Lua，回答"这个 API 实际行为是什么" | 0.10 MB |
| **`civ6-asset-forge`** | — | **2D 美术素材总入口**：由原 `civ6-loyalty-icon` + `civ6-promotion-icon` + `civ6-governor-art` + `civ6-leader-2d` **四个 skill 合并而成**——忠诚度/宗教压力图标、单位晋升图标、总督素材、2D 领袖立绘注册（各成一册 `reference/*.md`） | 3.45 MB |

> **两条整合线**（2026-09）：
> - `civ6-workshop-uploader` → 并入 **`civ6-modding/release.md`**（发布同属工程管理；脚本落在 `civ6-modding/release/scripts/`、模板 `release/templates/`、清单 `release/docs/`）。
> - `civ6-loyalty-icon` + `civ6-promotion-icon` + `civ6-governor-art` + `civ6-leader-2d` → 合并为 **`civ6-asset-forge`**。

> **家族外的依赖**：`（外部翻译 skill，已不作为依赖）`（翻译总 skill）位于 `~/.config/opencode/skills/`，**不在 DSH 的 `.agents/skills` 目录** —— DSH 会话无法用 `skill` 工具加载它，只能按绝对路径调用其脚本。见 §四。

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
| **做忠诚度 / 宗教压力图标** | `civ6-asset-forge` → `reference/loyalty-icon.md` |
| **做单位晋升图标** | `civ6-asset-forge` → `reference/promotion-icon.md` |
| **做总督素材（徽章 / 头像小图标 / 立绘 / 边缘透明渐变）** | `civ6-asset-forge` → `reference/governor-art.md` |
| **运行时验证 API 行为 / 复现脚本报错** | `civ6-tuner` |
| **上传 / 更新 Steam 工坊** | `civ6-modding` → **`release.md`**（脚本 `release/scripts/`） |
| 多语言翻译与本地化审计 | 借调 `（外部翻译 skill，已不作为依赖）`（见 §四） |

> `civ6-asset-forge` 的四类素材在 skill 内以 `reference/*.md` 分册组织（`leader-2d.md` / `loyalty-icon.md` / `promotion-icon.md` / `governor-art.md`，子资料在其同名子目录）；总入口与该 skill 自己的路由表见其 `SKILL.md`。
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
| `civ6-asset-forge` | **素材处理前必须先询问用户是否提供素材**（默认只生成注册文件）；只管美术规格与素材合成，**玩法注册链**仍在 `civ6-modding`（如总督玩法见 `governor-authoring.md`）；2D UI 宗教图标（`IconTextureAtlases` 270px 图集）不在范围 |

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

- **full**：含数据库快照（`DebugGameplay.sqlite` 61 MB / `DebugLocalization.sqlite` 65 MB / `api.sqlite` / `source_index.sqlite` …）—— 接收方开箱即用；
- **clean**：只出文档 + 脚本，接收方自行放数据库。

> ⚠ 分享前注意：数据库是**官方 schema 快照**，改动过要跑 `database/scripts/audit_schema_drift.py` 防污染（有漂移 exit 1）。

---

## 六、本次横向审查的产出（2026-09-14）

审查范围：`示例工程` + 12 个兄弟工程；7 路并行只读审查 + 主模型对高风险结论独立复核。

| 产出 | 位置 |
|---|---|
| 完整审查报告（含用户裁决更正、证据链） | 示例工程 `workspace/specs/2026-09-14-civ6-skill-family-audit.md` |
| **P0 纠错**：`Events.*` / `GameEvents.*` 总线路由错误结论 | `SKILL.md` / `gotchas.md` §7 / `events.md` |
| **P1 新章节** | `governor-authoring.md` / `citystate-authoring.md` / `balance-patch.md` |
| **P2 扩充** | `gotchas.md` §44–64（LoadOrder 阶梯 / Criteria 三态 / 引擎数据细节 / 双端 API 差异）；`project-setup.md`（LoadOrder 分层、两轴、工程骨架） |
| **P3 工具** | `scripts/` 六个新校验器 + `scripts/README.md` |
| art 侧 | `civ6-art-reference`：pantry 注意事项 + `cook-layer.md §2.3.1` 的 `.gitattributes` 执法手段 |

---

## 七、家族整合记录（2026-09）

| 动作 | 结果 |
|---|---|
| `civ6-workshop-uploader` 并入 `civ6-modding` | 内容成为 `release.md`；脚本/模板/清单移入 `civ6-modding/release/`；Task Routing 新增一行「Steam 创意工坊上传/更新 → `release.md`」 |
| 4 个美术素材类 skill 合并 | `civ6-loyalty-icon` + `civ6-promotion-icon` + `civ6-governor-art` + `civ6-leader-2d` → `civ6-asset-forge` |
| 家族规模 | **9 → 5** |
