# 资料依据（SOURCES）

> 本 skill 各 reference 文档的引用锚点汇合页。类型、字段与用例的**权威数据源**以 `database/` 自带库为准；
> 吸收自外部知识库的文档（如 `reference/modifiers-catalog/`、`reference/ui-panels/`）逐篇篇头标注来源，
> 家族级吸收边界见 `reference/FAMILY_INDEX.md` §八。

## 类型与枚举

- **主库**：`database/DebugGameplay.sqlite`（427 表官方 schema 快照）——
  `Improvements.ImprovementType`、`Terrains.TerrainType`、`Features.FeatureType`、`Districts.DistrictType`
  等表与列的真实集合以此为准；查询工具 `database/scripts/query_civ6_db.py`。
- **行级来源**：`database/source_index.sqlite`——官方行的来源索引 + 人工 DLC 依赖标注；
  判断「原版类型还是其他 Mod 的自定义类型」以它为准（运行时缓存会混入已装 Mod 的类型，不作数）。
- **FrontEnd 配置快照**：`database/DebugConfiguration.sqlite`（Maps、GameModeItems 等）。
- **schema 漂移体检**：`python database/scripts/audit_schema_drift.py`（改库后必跑，有漂移 exit 1）。

## 文本与 LOC

- `database/DebugLocalization.sqlite`：本机重建的 12 语言文本主库（本机重建、不入 git；
  重建入口 `database/scripts/build_localization.py`）。游戏运行时的 DebugLocalization 缓存
  首次生成后不再更新，禁止用它补全本库。
- 人工标注侧表（`SkillAnnotation_*`）随包 JSON：`database/scripts/export_side_tables.py`。

## 查询与反查工具（详见 TOOLS.md）

- `database/scripts/search_impl.py` —— 反查「某个效果/对象原版怎么实现」（整句自然语言走 BM25 兜底）；
- `database/scripts/query_effect_args.py` —— 查 EffectType/ModifierType 的参数签名；
- `database/scripts/query_api.py` —— Lua API 检索（api.sqlite，含 FireTuner 实测核验列）。

## 外部来源登记

- 第三方许可与采用范围：`THIRD_PARTY_NOTICES.md`（本仓库）与家族各仓库同名文件。
