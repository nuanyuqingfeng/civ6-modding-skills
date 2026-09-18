# database/ 目录说明（离线参考库）

> 本目录是 skill 的**查询三级阶梯 L1**：写任何 SQL / Lua 之前先在这里查，零联网、零游戏依赖。
> **2026-09-18 二次修订**：`DebugLocalization.sqlite` 改为**本机重建、不入库**（见 §零），
> 其余参考库仍随仓库分发。

## 零、两个本地化文本库 —— 本机重建，不入库 ⚠️

本目录下有**两个**本地化文本库，都**不进 git**、都在本机落地使用（直接可用，无需联网）：

| 库 | 内容 | 期望规模 | 体积 |
|---|---|---|---|
| `DebugLocalization.sqlite` | **主文本库**：Base + EXP1 + EXP2 + 全部领袖/文明 DLC（`EXP2>EXP1>base`，**排除情景与 Mode**）+ `SkillAnnotation_*` 人工标注侧表 | 336,125 行 / 28,060 tag / 12 语言 | 约 116 MB |
| `Localization_Mode.sqlite` | **模式文本库**：8 个 GAMEMODE（英雄 / 秘密结社 / 塔防 / 行业与公司 / 风云变幻 / 蛮族氏族 / 天启 / 树随机）独立成库 | 15,417 行 / 1,360 tag / 12 语言 | 5.2 MB |

**为什么都不入库**：两者都是**分层重建的派生库**，可从本机游戏安装数十秒重建。
主库尤其如此（62 MB → 116 MB），放进 git 会让仓库体积翻倍、且每次游戏版本/DLC 变动
都要重传一个百兆二进制。不可再生的人工成果（`SkillAnnotation_Colors` / `SkillAnnotation_Icons`）
已由重建流程原样保留。

> 两库**互不覆盖**：主库不含模式文本，模式库只装模式文本。二者有 239 个交集键，
> 其中 238 个是模式对主库值的改写（如「消灭蛮族哨站」→「驱散蛮族哨站」）；
> **运行时若同时启用模式，应按「模式库胜出」合并使用**。

### 一键重建（推荐）

```bash
# 0) 前置：本机已装游戏，且 tools/_paths.py 能解析到 game 键
python skills/civ6-modding/tools/_paths.py          # 自检，game 键应为 [OK]

# 1) 只读预览（分段 + 分层 + 与现有库的差异统计，不写盘）
python skills/civ6-modding/database/scripts/build_localization.py --report

# 2) 一键按规范重建两个库（--rebuild = 就地补全主库 + 重建模式库）
python skills/civ6-modding/database/scripts/build_localization.py --rebuild --dry-run
python skills/civ6-modding/database/scripts/build_localization.py --rebuild

# 3) 验收（期望三项依次为 336125 / 241 / 51）
python skills/civ6-modding/database/scripts/audit_schema_drift.py
python -c "import sqlite3;c=sqlite3.connect(r'skills/civ6-modding/database/DebugLocalization.sqlite');print(c.execute('SELECT COUNT(*) FROM LocalizedText').fetchone()[0], c.execute('SELECT COUNT(*) FROM SkillAnnotation_Icons').fetchone()[0], c.execute('SELECT COUNT(*) FROM SkillAnnotation_Colors').fetchone()[0])"
```

**也可分步执行**（等价于 `--rebuild`）：

```bash
# 主库：就地补全（保留侧表；--apply-rewrites 才会用 EXP2 覆盖既有 base 值）
python skills/civ6-modding/database/scripts/build_localization.py --augment-main --apply-rewrites
# 模式库：独立新建（只加不覆盖）
python skills/civ6-modding/database/scripts/build_localization.py --build-mode skills/civ6-modding/database/Localization_Mode.sqlite
```

> **幂等**：重复跑 `--rebuild` 安全。主库第二次跑会显示「待新增 0 行 / 待改写 0 行」
> 且**文件字节不变**；模式库会整库重写（内容一致，仅 SQLite 页布局可能不同）。

### 重建时靠什么保住"不可再生"的内容

两个库都不入库，但有三种内容**无法从游戏文件重新生成**，已导出为随包 JSON，
`--rebuild` 会自动灌回（首次/换机器时这几步是必需的）：

| 随包 JSON | 内容 | 行数 | 作用 |
|---|---|---|---|
| `annotations/localization_side_tables.json` | `SkillAnnotation_Icons` / `SkillAnnotation_Colors` | 241 / 51 | 图标名·颜色名 → 中文备注（人工标注） |
| ↑ 同上（`extraRows` 段） | 库中「游戏安装里没有」的行 | 64 | 本项目自造 tag（`_QYQXP_` 百科文本），不重建就丢 |
| `annotations/localization_aux_tables.json` | 7 张语言注册表 + 3 个视图的 DDL 与数据 | 95 | 换机器重建后仍是 **10 表 + 3 视图**，而不是只剩 `LocalizedText` |

手动导出（侧表有改动时跑）：

```bash
python skills/civ6-modding/database/scripts/export_side_tables.py          # 导出侧表 + extraRows
python skills/civ6-modding/database/scripts/export_side_tables.py --check  # 与库比对，有漂移 exit 1
```

> ⚠️ 若跳过这两份 JSON，重建会得到「只有 `LocalizedText` 一张表、缺 7 张注册表与 3 视图、
> 且没有项目自造 tag」的残缺库——**不报错**，只是后续按 `Languages` / `FontStyleSheets` 查询
> 或查 `_QYQXP_` 文本时才失败。重建后请按上面的验收命令确认 `336125 / 241 / 51`。

### 空白口径（实测，勿"顺手优化"）

引擎落盘时**会 strip 首尾空白**（游戏源文件常带尾随空格，如 `de_DE` 的
`LOC_ABILITY_CAPTIVE_WORKERS_DESCRIPTION` 源文件结尾是 `. `，运行时缓存里没有）。
因此重建写入时统一 `strip()`，否则新写的行会与库内既有行口径不一致
（实测会造出 2,868 行"仅首尾空白"的内部矛盾）。

**重建规则（已实测固定，勿随意改）**

| 项 | 值 |
|---|---|
| 主库范围 | Base + EXP1 + EXP2 + 全部领袖/文明 DLC（**排除情景 Scenario 与 Mode 文本**） |
| 优先级 | `EXP2 > EXP1 > base`；其它领袖包只补缺不覆盖 |
| 分段判据 | `.modinfo` 权威判据——新式看 `<ActionCriteria>` 的 `ConfigurationId=GAMEMODE_*`；旧式（仅 `VikingsScenario`）看 `<Properties><RuleSet>` 的 `RULESET_SCENARIO_*` |
| 模式清单权威表 | `DebugConfiguration.sqlite → GameModeItems`（8 行），**不在** Gameplay 库 |
| 删行 | **不应用任何 `<Delete Tag>`**（删除是加载域作用域，静态合成会误删其它环境仍有用的文本） |
| 侧表 | `SkillAnnotation_*` 与既有行**一行不丢**（`--augment-main` 用 `INSERT OR IGNORE` + 仅更新 `LocalizedText`） |
| 分段闭合 | 磁盘 368 个 `.xml` = main 267 + mode 46 + scenario 55 |

> ⚠️ **不要用游戏运行时缓存补全**：`%LOCALAPPDATA%\...\Cache\DebugLocalization.sqlite`
> 实测恒为 base 15,229 tag，**连当前加载的本 mod 文本都没有**（同目录 `DebugGameplay.sqlite`
> 却含本局全部内容），与本局模式和 mods 无关——它不反映"加载了什么"。

## 一、随仓库分发（clone 即有）

| 文件 | 体积 | 内容 | 需要解压？ |
|---|---|---|---|
| `api.sqlite` | 2.5 MB | 4857 条 Lua API（含 2026-09-08 FireTuner 实测核验列：`verify_status` / `verify_scope` / `runtime_gp` / `runtime_ui` / `true_name` / `corrected_from` 等） | 否 |
| `api-verification-2026-09-08/` | 6.2 MB | ★ **核验列的原始凭证**：FireTuner 实跑输出（`raw/*.txt`）、全量探测结果（`api_scope_full.csv` 等）、人工复核清单与报告 | 否 |
| `DebugGameplay.sqlite` | 58.2 MB | 官方 gameplay 库快照（427 表）—— **`rgn_validate` 的基础库**、所有 SQL 查询的主库 | 否 |
| `DebugConfiguration.sqlite` | 1.1 MB | 官方 FrontEnd 配置快照（`Maps`、`GameModeItems`/`Rulesets` 等表） | 否 |
| `source_index.sqlite` | 29.1 MB | 官方行级来源索引（`row_source`）+ 人工 `dlc_dependency` 标注（12 行 Mode/Scenario） | 否 |
| `annotations/dynamic_modifiers_dlc.json` | 7 KB | 人工整理的 DLC 依赖标注（`source_index.dlc_dependency` 的镜像） | 否 |
| `scripts/`、`*.md` | — | 查询脚本与注解文档 | 否 |
| ~~`DebugLocalization.sqlite`~~ | ~~62 MB~~ | **不入库**，本机重建（见 §零） | — |

> **可再生性**：`DebugGameplay` / `DebugConfiguration` / `source_index` 严格说可从游戏 + SDK 重建，
> 但按"参考库随包"的裁决一并入库，省掉每人重建一遍；`api.sqlite` 的核验列、
> `source_index.dlc_dependency`、`api-verification-*` 是**不可再生的人工成果**。
> `DebugLocalization` 的 `SkillAnnotation_*` 同样是人工成果，但它随重建流程保留在原库中。

## 二、不入库的文件

| 文件 | 为什么 |
|---|---|
| `DebugLocalization.sqlite` | **分层重建的主文本库**（约 116 MB），数十秒可重建；侧表在重建中保留（见 §零） |
| `Localization_Mode.sqlite` | **分层重建的模式文本库**（5.2 MB），同样可从游戏文件重建（见 §零） |
| `local_paths.json` | **个人环境配置**（本机路径），不是参考库；写入它之后所有脚本按本机路径解析 |
| `__pycache__/`、`*.log` | 运行缓存与日志，可再生 |

## 三、缺库时的真实影响（**已被实测确认的坑**）

`rgn_validate`（改完 `*_RGN.sql` 的强制关卡）默认以 `DebugGameplay.sqlite` 为基础库：

```bash
node "<skills>/civ6-modding/scripts/rgn_validate_runner.mjs" <工程目录> '*.sql'
```

- 库存在 → 真实执行项目 SQL 后与**整库**比对，能查出对原版 ID 的悬空引用；
- 库缺失（例如你手动删了、或用了 `--base` 指到不存在的路径）→ 校验器**无法**对照官方定义。
  2026-09-17 之前它会在这种情况下回落到内存空库、仍打印 `✅ 未发现悬空引用`，把"只做了项目内自洽检查"
  误读成"引用全部闭合"；**现已修正为显式告警**（报告开头 `⚠⚠ 基础库缺失` + 结论行降级）。
- 同缺库时 `scripts/check_sql_exec.py`、`scripts/check_types_kinds.py`、`database/scripts/query_civ6_db.py`
  都会直接报错退出——它们与 `rgn_validate` 是**互补**关系，别把其中一个的"绿"当成全部通过。

## 四、库的权威性口径（改库前必读）

- `DebugGameplay.sqlite` 必须与官方 schema **1:1**（回到 100% 官方镜像，不保留 skill 专属侧表/视图）；
  DLC 依赖这类元数据一律放 `source_index.sqlite` 或 `annotations/*.json`，**不许加列**。
  `gotchas.md` / `schema-annotated.md` 里的「官方仅 3 列」铁律即由此而来。
- 改库后按 `CALIBRATION_LOG_2026-08.md` 的流程复验：`PRAGMA integrity_check` + `audit_schema_drift.py`。
- 若你要**自行重建**官方快照（例如游戏大版本更新后）：用官方 XML/SQL 全量导入，
  再跑 `python database/scripts/audit_schema_drift.py` 对齐 schema（有漂移 exit 1）。
