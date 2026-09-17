# API 范围核验原始记录（2026-09-08）

> 本目录是 `database/api.sqlite` 与 `reference/api_enhanced.json` 里**核验列/标记的原始凭证**：
> 4857 条 Lua API 的 "UI / GamePlay 双端是否存在、实际是什么类型" 是**在运行中的游戏里实跑出来**的，
> 不是文档转储。随仓库分发，便于他人复核、复现与增量补测。

## 一、这些记录回答什么问题

| 问题 | 用哪个文件 |
|---|---|
| 某个 API 到底在 UI 端 / GP 端存在吗？运行时类型是什么？ | `api_scope_full.csv`（全量表）、`raw/results.json` |
| 哪些条目与官方/第三方文档**说法不一致**？ | `api_scope_文档与运行时不符.csv`、`api_scope_文档名异常.csv` |
| 哪些文档条目**根本不存在**（第三方转储混入）？ | `api_scope_CodeBuddy转储.csv` |
| 哪些**本次没能实测**（缺实例通道/动态代理）？ | `api_scope_无法验证.csv` |
| 命名空间可见性汇总 | `命名空间汇总.csv`、`命名空间可见性.csv`、`GameInfo库表可达性.csv` |
| UI 端 / GP 端方法面差异 | `GP_UI方法面差异.csv` |
| 人工复核进度与结论 | `审核清单.md` / `审核清单.xlsx` / `审核清单_预分类.csv`、`helper_humanChecked.json`、`实装记录.md` |
| 完整叙述版报告 | `API范围验证报告.md` |

## 二、与数据库列的对应关系

`api.sqlite` 的 `api_functions` 表新增列即由本目录的原始记录产出：

| 列 | 含义 | 取值来源 |
|---|---|---|
| `verify_status` | `已核验` / `存疑` / `''`（本次无法实测） | 实测结果与文档对照 |
| `verify_scope` | 双端 / 仅GP / 仅UI / 双端未见 / 含不可判 | `raw/*_probe.txt` + `results.json` |
| `runtime_gp` / `runtime_ui` | 运行时实际类型（function/table/userdata/string/nil/ERR/CF） | 同上 |
| `true_name` / `true_path` | 文档名有误时的真名 / 真身路径 | `api_scope_文档名异常.csv` |
| `corrected_from` | 被实装修正的 availability 原值（53 条） | `实装记录.md` |
| `suspect_type` / `audit_priority` | 存疑类型 / 审核优先级（P1 已实装、P2 需裁决、P4 未收录…） | `审核清单_预分类.csv` |

`reference/api_enhanced.json` 的 `humanChecked` / `suspect` / `pendingTest` 标记同源。

## 三、目录内容

| 文件 | 说明 |
|---|---|
| `API范围验证报告.md` | 结论性报告（**先读这份**） |
| `api_scope_full.csv` | 全量 4857 条 × 文档可用性 / 运行时实测 / 判定 |
| `raw/results.json`、`raw/supplement.json` | 原始探测结果（机读） |
| `raw/raw_gp_probe.txt`、`raw/raw_ui_probe.txt` | FireTuner 实跑输出原文 |
| `raw/name_index.json` | 名称索引（含真名修正映射） |
| `raw/audit_run_log.txt` | 审核脚本的一次运行日志（原为 `.log`，改名以便随仓库分发——`.gitignore` 忽略 `*.log`） |
| `审核清单*` / `helper_humanChecked.json` | 人工复核清单与勾选状态 |
| `实装记录.md` | 已回灌进 `api.sqlite` 的修正记录 |
| `统计.json` | 汇总统计 |

## 四、复现与增量补测

1. 用 `civ6-tuner` skill 连上运行中的对局（FireTuner，TCP 4318）；
2. 按 `raw/raw_gp_probe.txt` / `raw/raw_ui_probe.txt` 里的探测口径重跑（同一条 API 在两端的
   `type()` 探针）；
3. 新结果按上表列名回灌 `api.sqlite`，并在 `实装记录.md` 追加一条。

> ⚠ 记录里的路径、命名空间与 API 名均按**当时游戏版本**采集；游戏更新后需增量补测，
> 不要直接把这批结论当永久真值（这与 `api.sqlite` 的 `verify_at` 字段口径一致）。
