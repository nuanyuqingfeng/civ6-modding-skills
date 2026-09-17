# database/ 目录说明（离线参考库）

> 本目录是 skill 的**查询三级阶梯 L1**：写任何 SQL / Lua 之前先在这里查，零联网、零游戏依赖。
> 本文件说明**哪些库随仓库分发、哪些不随、缺了会怎样、怎么补齐**。

## 一、随仓库分发（clone 即有）

| 文件 | 体积 | 内容 | 可再生？ |
|---|---|---|---|
| `api.sqlite` | 2.5 MB | 4857 条 Lua API（含 2026-09-08 FireTuner 实测核验列：`verify_status` / `verify_scope` / `runtime_gp` / `runtime_ui` / `true_name` / `corrected_from` 等） | ❌ **不可再生**：1854 条修正与标记是纯人工成果 |
| `DebugLocalization.sqlite` | 62.1 MB | 官方 `LocalizedText` 全量（中英等）+ skill 自建侧表 `SkillAnnotation_Colors` / `SkillAnnotation_Icons`（手工配色与图标名） | ❌ 侧表不可再生（官方文本部分可再生） |
| `annotations/dynamic_modifiers_dlc.json` | 7 KB | 人工整理的 DLC 依赖标注（`source_index.dlc_dependency` 的镜像，12 行 Mode/Scenario） | ❌ 人工成果 |
| `scripts/`、`*.md` | — | 查询脚本与注解文档 | ✅ |

## 二、**不**随仓库分发（`.gitignore` 排除）

| 文件 | 体积（作者本机） | 为什么排除 | 缺了会怎样 |
|---|---|---|---|
| `DebugGameplay.sqlite` | 61,014,016 B（58.2 MiB） | 官方 gameplay 库快照，体积大且**原则上可重建** | ★ 见下节——**这是全新环境最需要补的一件** |
| `DebugConfiguration.sqlite` | 1.1 MB | 官方 FrontEnd 配置快照，可重建 | `SELECT * FROM Maps` 之类 FrontEnd 查询报错 |
| `source_index.sqlite` | 29.1 MB | 官方行级来源索引（`row_source`）+ 人工 `dlc_dependency` | `audit_schema_drift.py` 的标注镜像检查告警（人工标注部分已在 `annotations/*.json` 留档） |

## 三、缺少 `DebugGameplay.sqlite` 时的真实影响（**已被实测确认的坑**）

`rgn_validate`（改完 `*_RGN.sql` 的强制关卡）默认以本库为基础库：

```bash
node "<skills>/civ6-modding/scripts/rgn_validate_runner.mjs" <工程目录> '*.sql'
```

- 库存在 → 真实执行项目 SQL 后与**整库**比对，能查出对原版 ID 的悬空引用；
- 库缺失 → 校验器**无法**对照官方定义。2026-09-17 之前它会在这种情况下回落到内存空库、
  仍打印 `✅ 未发现悬空引用`，把"只做了项目内自洽检查"误读成"引用全部闭合"。
  **现已修正为显式告警**（报告开头 `⚠⚠ 基础库缺失` + 结论行降级为"未经基础库对照"）。
- 同缺库时 `scripts/check_sql_exec.py`、`scripts/check_types_kinds.py`、`database/scripts/query_civ6_db.py`
  都会直接报错退出——它们与 `rgn_validate` 是**互补**关系，别把其中一个的"绿"当成全部通过。

## 四、怎么补齐 `DebugGameplay.sqlite`

按可行性排序，任选其一（放好后**务必**先跑一次结构自检）：

```bash
python database/scripts/audit_schema_drift.py      # 有漂移 exit 1；0 = 与官方 schema 1:1
```

1. **从可信来源取得一份官方 gameplay 库快照**，直接放到 `database/DebugGameplay.sqlite`。
   校验器内置了高流量表的列断言（`DynamicModifiers` / `Modifiers` / `ModifierArguments` / `Types`），
   库被手工加过列会当场告警，所以"来路不明的库"也能被机械筛一遍。
2. **手上有官方 gameplay SQL dump**（形如 `DebugGameplay_ALL_MODES.sql`）时，直接导入：
   ```bash
   python -c "import sqlite3;c=sqlite3.connect('database/DebugGameplay.sqlite');c.executescript(open('DebugGameplay_ALL_MODES.sql',encoding='utf-8').read());c.close()"
   ```
   （作者本机就是这样起步的：官方全量导入 + 8,178 行补全，见 `CALIBRATION_LOG_2026-08.md`。）
3. **只做项目内自洽检查**：不补库，改用 `--static` 或接受上面那条告警——
   但**不要**把它当作发布前结论。

> ⚠ **已知缺口（待补）**：从零重建该库（官方 XML/SQL → sqlite）的**标准流程尚未脚本化**，
> 目前依赖手工导入。若你希望它变成一条命令，见本次 skill 审查报告的"待决事项"一节。

## 五、库的权威性口径（改库前必读）

- `DebugGameplay.sqlite` 必须与官方 schema **1:1**（回到 100% 官方镜像，不保留 skill 专属侧表/视图）；
  DLC 依赖这类元数据一律放 `source_index.sqlite` 或 `annotations/*.json`，**不许加列**。
  `gotchas.md` / `schema-annotated.md` 里的「官方仅 3 列」铁律即由此而来。
- 改库后按 `CALIBRATION_LOG_2026-08.md` 的流程复验：`PRAGMA integrity_check` + `audit_schema_drift.py`。
