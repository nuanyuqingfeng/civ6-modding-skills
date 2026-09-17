# database/ 目录说明（离线参考库）

> 本目录是 skill 的**查询三级阶梯 L1**：写任何 SQL / Lua 之前先在这里查，零联网、零游戏依赖。
> **2026-09-18 起：所有参考库都随 skill 一起开源**（含官方快照；体积大的以压缩包形式分发，
> 解压步骤见对应目录的 `README.md`）。本文件说明每个库是什么、体积多大、要不要解压、缺了会怎样。

## 一、随仓库分发（clone 即有）

| 文件 | 体积 | 内容 | 需要解压？ |
|---|---|---|---|
| `api.sqlite` | 2.5 MB | 4857 条 Lua API（含 2026-09-08 FireTuner 实测核验列：`verify_status` / `verify_scope` / `runtime_gp` / `runtime_ui` / `true_name` / `corrected_from` 等） | 否 |
| `api-verification-2026-09-08/` | 6.2 MB | ★ **核验列的原始凭证**：FireTuner 实跑输出（`raw/*.txt`）、全量探测结果（`api_scope_full.csv` 等）、人工复核清单与报告 | 否 |
| `DebugGameplay.sqlite` | 58.2 MB | 官方 gameplay 库快照（427 表）—— **`rgn_validate` 的基础库**、所有 SQL 查询的主库 | 否 |
| `DebugLocalization.sqlite` | 62.1 MB | 官方 `LocalizedText` 全量（8 语言）+ skill 自建侧表 `SkillAnnotation_Colors` / `SkillAnnotation_Icons`（手工配色与图标名） | 否 |
| `DebugConfiguration.sqlite` | 1.1 MB | 官方 FrontEnd 配置快照（`Maps` 等表） | 否 |
| `source_index.sqlite` | 29.1 MB | 官方行级来源索引（`row_source`）+ 人工 `dlc_dependency` 标注（12 行 Mode/Scenario） | 否 |
| `（已移除）/（语料库已移除）` | 27.7 MB | 多语言语料库（约 13 万业务行 × 8 语言），**可选**：仅翻译/本地化时的词库查证用 | ★ **是**：`python -c "import zipfile;zipfile.ZipFile('（语料库已移除）').extractall('database/（已移除）')"` → 见 `（已移除）/README.md` |
| `annotations/dynamic_modifiers_dlc.json` | 7 KB | 人工整理的 DLC 依赖标注（`source_index.dlc_dependency` 的镜像） | 否 |
| `scripts/`、`*.md` | — | 查询脚本与注解文档 | 否 |

> **可再生性**：`DebugGameplay` / `DebugConfiguration` / `source_index` 严格说可从游戏 + SDK 重建，
> 但按"参考库随包"的裁决一并入库，省掉每人重建一遍；`api.sqlite` 的核验列、`DebugLocalization` 的
> `SkillAnnotation_*`、`source_index.dlc_dependency`、`api-verification-*` 则是**不可再生的人工成果**。

## 二、只有本机个人文件不入库

| 文件 | 为什么 |
|---|---|
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
