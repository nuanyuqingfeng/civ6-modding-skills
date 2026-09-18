# database/ 目录说明（离线参考库）

> 本目录是 skill 的**查询三级阶梯 L1**：写任何 SQL / Lua 之前先在这里查，零联网、零游戏依赖。
> **2026-09-18 二次修订**：`DebugLocalization.sqlite` 改为**本机重建、不入库**（见 §零），
> 其余参考库仍随仓库分发。

## 零、`DebugLocalization.sqlite` —— 本机重建，不入库 ⚠️

**为什么不入库**：它是**分层重建的派生库**（62 MB → 约 116 MB）。放进 git 会让仓库体积翻倍，
且每次游戏版本/DLC 变动都要重传一个百兆二进制；而它在本机**数十秒即可重建**。
不可再生的人工成果（`SkillAnnotation_Colors` / `SkillAnnotation_Icons` 侧表）已由重建流程保留。

**重建流程**（换机器 / 游戏更新后 / 想补 DLC 文本时跑）：

```bash
# 0) 前置：本机已装游戏，且 tools/_paths.py 能解析到 game 键
python skills/civ6-modding/tools/_paths.py          # 自检，game 键应为 [OK]

# 1) 只读预览：分段（main/mode/scenario）+ 分层 + 与现有库的差异统计
python skills/civ6-modding/database/scripts/build_localization.py --report

# 2) 就地替换（关键：--augment-main 只加行 + 应用 EXP2 覆盖；侧表原样保留）
python skills/civ6-modding/database/scripts/build_localization.py --augment-main --apply-rewrites --dry-run
python skills/civ6-modding/database/scripts/build_localization.py --augment-main --apply-rewrites

# 3) 验收（三项都要过）
python skills/civ6-modding/database/scripts/audit_schema_drift.py
python -c "import sqlite3;c=sqlite3.connect(r'skills/civ6-modding/database/DebugLocalization.sqlite');print(c.execute('SELECT COUNT(*) FROM LocalizedText').fetchone()[0], c.execute('SELECT COUNT(*) FROM SkillAnnotation_Icons').fetchone()[0], c.execute('SELECT COUNT(*) FROM SkillAnnotation_Colors').fetchone()[0])"
#   期望：336125 行 / 241 / 51
```

**重建规则（已实测固定，勿随意改）**

| 项 | 值 |
|---|---|
| 主库范围 | Base + EXP1 + EXP2 + 全部领袖/文明 DLC（**排除情景 Scenario 与 Mode 文本**） |
| 优先级 | `EXP2 > EXP1 > base`；其它领袖包只补缺不覆盖 |
| 分段判据 | `.modinfo` 权威判据——新式看 `<ActionCriteria>` 的 `ConfigurationId=GAMEMODE_*`；旧式（仅 `VikingsScenario`）看 `<Properties><RuleSet>` 的 `RULESET_SCENARIO_*` |
| 模式清单权威表 | `DebugConfiguration.sqlite → GameModeItems`（8 行），**不在** Gameplay 库 |
| 删行 | **不应用任何 `<Delete Tag>`**（删除是加载域作用域，静态合成会误删其它环境仍有用的文本） |
| 侧表 | `SkillAnnotation_*` 与既有行**一行不丢**（`--augment-main` 用 `INSERT OR IGNORE` + 仅更新 `LocalizedText`） |
| 期望规模 | 336,125 行 / 28,060 tag / 12 语言 |

**模式文本另建一库**（只加不覆盖，独立可用）：

```bash
python skills/civ6-modding/database/scripts/build_localization.py --build-mode <输出目录>/Localization_Mode.sqlite
# 期望：15,417 行 / 1,360 tag；与主库有 239 个交集键，其中 238 个是模式改写（合并时模式应胜出）
```

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
| `DebugLocalization.sqlite` | **分层重建的派生库**（约 116 MB），数十秒可重建；侧表在重建中保留（见 §零） |
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
