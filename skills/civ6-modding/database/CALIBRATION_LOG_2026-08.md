# Civ6 Modding Skill 全量校准 — 验证日志 (2026-08-06)

## 一、执行概况

| 阶段 | 内容 | 产出 |
|------|------|------|
| P1 | Lua/XML 提取脚本 | work_xml_rows.sqlite (303,725 行, 1135 XML 文件, 0 解析错误, 5 行无行号) / work_lua_calls.sqlite (646 Lua, 3016 事件注册, 53,796 API 调用, 9,245 函数定义) |
| P2 | SQL 内容补全 | DebugGameplay.sqlite +8,178 行 / DebugConfiguration.sqlite +152 行（共 +8,330） |
| P2 | 来源标注 | source_index.sqlite: row_source 64,293 行级标注 / 469 表 |
| P3 | API/事件校准 | api.sqlite 4,665→4,857（+192）；api_enhanced.json +165；events_enhanced.json +5；events.md +26 事件 |
| P4 | modinfo 分析 | 42 官方 modinfo 解析 → project-setup.md 新增官方实证章节 |
| P5 | 文档同步 | database.md +source_index 使用说明 |
| P6 | 独立复核 | review 子代理（edit: deny）7 项全 PASS，P2 遗留已修复 |
| P7 | LuaEvents DLC 标注 | events_enhanced.json LuaEvents 480→481（+1 新增），446 条补 `dlcSources`/`panels`/`registerVerified` 字段；排除 8 个仅情景/模式事件 + 4 个 Platforms 平台事件 |
| P7 | 残留清理 | 删除零字节历史残留：skill 根 api.sqlite、database/civ6.db、database/DebugGameplay_Base.sqlite |
| P8 | 非领袖 DLC 内容清理 | 补全后删除 4,459 行情景/模式来源的内容表行 + Types 内容 Kind 行；保留系统词典表全量（1,231 情景机制行）+ 领袖 DLC + 资料片 |

### P8 清理详情（用户决策：内容表+Types 清理，系统表保留）

- 背景：补全后情景/模式专属内容（UNIT_EXPLORER、BUILDING_PLAGUE_HOSPITAL、LEADER_DARIUS_III 等）会污染查询——常规对局不存在，modder 误用即报错
- 删除：内容表非领袖来源行 + Types 内容类 Kind（KIND_UNIT/BUILDING/LEADER 等）情景行 = **4,459 行**（cleanup_log 表记录）
- 保留：
  - 系统词典表全量：Requirements 1,051 / RequirementSets 982 / Modifiers 4,185 / ModifierArguments 7,595 / DynamicModifiers 995（含情景新机制定义 1,231 行）
  - Types 系统类 Kind 1,331 行（KIND_MODIFIER/KIND_REQUIREMENT）
  - 领袖 DLC 15,066 行 + Expansion1/2（GovernorPromotions 70、UNIT_ROCK_BAND、UNIT_GIANT_DEATH_ROBOT 等）
- 验证：情景内容 5 项抽样 = 0 ✓；领袖 DLC 抽样 > 0 ✓；PRAGMA integrity_check = ok ✓
- 备份：清理前完整备份在 %TEMP%\opencode\（DebugGameplay_backup.sqlite = 原始旧库；清理后现库 = 补全+清理态）

### LuaEvents 收录规则（用户指示）

- **收录**：Base + 资料片（Expansion1/Expansion2）+ 领袖/文明包 DLC（Babylon、Ethiopia 等 23 个）
- **不收录**：仅出现在纯情景（`*Scenario`）/纯模式（`BarbarianClansMode`、`TreeRandomizer`）DLC 的事件（8 个：ActionPanel_EndObserverMode、ActionPanel_ObserverModeTurnBegin、CityBannerManager_OpenTreatWithTribePopup、NotificationPanel_UserNotificationActivate、OnPlagueLensOn、OnViewPlagueLens、RelicScreen_RelicScreenOpened、UnitPanel_CivRoyaleScenarioShowUnitFlagCombatPreview）
- **不收录**：`Platforms\` 目录（Stadia 等平台专属，4 个：ModsIAP、ModsIAPAutoUpdate、PlayTutorial、ResetMenus）
- 分类依据：work_lua_events_dlc.sqlite（446 条，含 dlc_sources/panels/reg_points/fire_points）

## 二、P2 SQL 补全详情

- 缺失基准：XML 有 DB 无 8,770 行（比对脚本, Base 优先规则）
- 补全结果：
  - inserted: 8,330（DebugGameplay 8,178 + DebugConfiguration 152）
  - conflict: 248（场景互斥唯一约束：Viking ERA_EARLY/MIDDLE/LATE 与 Base ChronologyIndex 冲突、Victories 缺 NOT NULL Blurb、CityStates/Players Domain 变体——情景与主游戏互斥，合理跳过）
  - skip: 192（引擎自动主键表如 BehaviorTreeNodes/PrimaryKey、ConfigurationUpdates 等）
  - Update/Delete 操作不纳入（用户指示）
- 验证：BELIEF_ORAL_TRADITION ✓、CIVILIZATION_AMSTERDAM ✓（补全前不存在）
- 备份：%TEMP%\opencode\DebugGameplay_backup.sqlite（60MB）

### 关键根因修复记录（比对误报排查）
1. XML 属性与 DB 列名大小写不敏感（ModifierID vs ModifierId）→ norm_pk 大小写不敏感匹配
2. XML 缺列取 DB 列默认值（AiFavoredItems.Favored 默认 1）→ 默认值填充
3. BOOLEAN/INTEGER 类型规范化（True→1）→ norm_val
4. Types.Hash UNIQUE 约束 → FNV-1a 兜底填充
5. 子元素形式行（`<Row><ModifierId>..</ModifierId></Row>`）→ 子元素提取
6. Update/Delete 的 Where/Set 子元素不产生行 → 排除

## 三、P3 API/事件校准详情

- **GameInfo 命名空间（重大发现）**：api_enhanced.json / api.sqlite 原完全缺失 Civ6 最核心的 GameInfo 数据表访问 API → 补 161 表条目（Q-GameInfoXXX, QUERY, Both, exampleCode: `for row in GameInfo.X() do end`）
- **Events.* 缺口 21**：官方调用验证（reasoner 判定 18 REAL + 3 UNCERTAIN→收录标注 UI）：Begin2KLoginProcess、ExitToMainMenu、LoadScreenClose、ShowLeaderScreen、SystemUpdateUI 等
- **Events/GameEvents 缺口 5**：LeaderPopup、MultiplayerConnectionFailed、MultiplayerNetRegistered、PlayerVersionMismatchEvent、AdvisorNegativeResourceRate（官方注册验证）
- **单函数缺口 4**：Game.GetLocalTeam、Game.IsTechRecommended、Locale.ConvertTextKey、MapConfiguration.SetImportFilename
- **LuaEvents 433 个**：官方自定义事件（非引擎 API），不收入 api 库，events.md 已说明
- **Platforms 目录**：Stadia 独有 LuaEvents（ModsIAP 等 5 个）排除

## 四、P4 modinfo 实证结论

- 42 个官方 modinfo 全量解析（0 错误）
- UpdateDatabase 118 次、ReplaceUIScript 117 次（官方最高频两种 action）
- File Priority 分布：1(前置/移除) 246+21 次、2(Schema 后主数据) 31+19 次、0/3 少量
- LoadOrder 官方实际值：-100(2 处) / 100(9 处)，多数不写
- ReplaceUIScript 的 LuaContext 官方值 Top12 已记录
- AddUserInterfaces Context 全部 = InGame
- criteria 命名模式：X_Expansion1 / X_Expansion2 / X_Mode / Scenario

## 五、P6 review 复核结论

| 项 | 结论 |
|----|------|
| DebugGameplay 补全真实性 | PASS（3 项抽样全过） |
| source_index 来源规则 | PASS |
| api.sqlite 新增 | PASS |
| api_enhanced.json 合法性 | PASS |
| events_enhanced.json | PASS |
| 文档 UTF-8（无 BOM 无乱码） | PASS |
| 遗留评估 | P2：GameInfo id 前缀 A-/Q- 不一致 → **已修复**（统一 Q-，sqlite+json 一致 161+1） |

## 六、剩余风险与未决项

1. **DebugGameplay.sqlite 与游戏实际加载顺序的差异**：补全基于"官方 XML 全量"，未模拟引擎加载顺序（Mod 冲突/覆盖语义）。情景/模式专属内容已清理，库内容与常规对局（Base+Expansion+领袖 DLC）一致；系统表（Modifiers/Requirements）保留情景机制定义（词典用途）。行级出处以 source_index.row_source 为准。
2. **Types.Hash 值**：补入行的 Hash 用 FNV-1a 兜底，与引擎计算值不同（仅参考库唯一约束用途，不影响查询）。
3. **Events 21 中 3 个 UNCERTAIN**（EnableColorKey/DisableColorKey/WorldBuilderSignal）：reasoner 判定不确定，已按 UI 收录并标注，待用户核对。
4. **引擎自动主键表**（BehaviorTreeNodes 等 16 表）行级来源无法标注，仅表级统计。
5. **LuaEvents 收录边界**：已按用户指示收录 Base/资料片/领袖 DLC 事件（481 个，446 条带 DLC 标注），排除情景/模式/Platforms 事件。

## 七、P9 收尾（2026-08-06 终审）

- **与用户打包备份比对**：`civ6-modding.zip`（7/30 状态，含旧版中间产物）→ 确认改动文件 10 个、新增 4 个、删除 3 个零字节+1 journal；JSON 无内容丢失（格式差异已修复：统一 `\n`+indent=2 无 CRLF）
- **误导点修复**：
  1. api_enhanced.json 格式还原（CRLF/缩进与原版一致）
  2. `source_index.row_source` 同步清理（删除 6,145 条非领袖内容行，58,148 条与 DB 一致；系统表情景机制行 1,874 条保留）
  3. `table_summary` 重算（457 表）
  4. 删除过程日志表：missing_rows、patch_log、cleanup_log、missing_resolved、engine_pk_tables
  5. database.md 章节更新（457 表/5.8 万行/无日志表引用）
- **中间产物清理**：删除 work_xml_rows.sqlite、work_lua_calls.sqlite、work_api_gap.sqlite、work_lua_events_dlc.sqlite、work_modinfo.sqlite（zip 备份与 Temp 备份保留可恢复）
- **清理后重新打包备份**：civ6-modding_2026-08-06_clean.zip（最终态）
- **引用完整性复核**：Modifiers→Types 0 断裂、RequirementSetRequirements→Requirements 0 断裂、TraitModifiers/UnitAbilityModifiers/ModifierArguments 0 断裂

## 八、最终变更文件清单

| 文件 | 变更 |
|------|------|
| database/DebugGameplay.sqlite | 补全+8,178 行 → 清理 4,459 行非领袖内容（最终 58MB） |
| database/DebugConfiguration.sqlite | +152 行 |
| database/source_index.sqlite | **新增**（row_source 58,148 行 / table_summary 457 / missing_tables 6） |
| database/api.sqlite | 4,665→4,857 函数 |
| reference/api_enhanced.json | +161 GameInfo + 4 函数（格式还原） |
| reference/events_enhanced.json | +5 事件 + 445 条 LuaEvents DLC 标注（1051 事件） |
| events.md | +26 事件章节 + LuaEvents DLC 标注说明 |
| database.md | +source_index 使用说明（更新为最终态） |
| project-setup.md | +官方 modinfo 实证章节 |
| database/CALIBRATION_LOG_2026-08.md | 校准全程记录 |


## 九、P10 幻列根因修复（2026-09-10）

### 根因
- `database/DebugGameplay.sqlite` 的 `DynamicModifiers` 被手工加了第 4 列 `IsDlcDependency`（12 行=1 / 983 行=0），`modifiers-cheatsheet.md` 又把它当官方列写进查询提示。
- 校验器 `rgn_validate_runner.mjs` 以该库为 ground truth → 执行期"侥幸成功" → 幻列 SQL 通过校验、游戏加载才报 `table DynamicModifiers has no column named IsDlcDependency`。

### 修复
| 对象 | 变更 |
|------|------|
| `DebugGameplay.sqlite` | `DynamicModifiers` 重建为官方 3 列；删除 skill 专属侧表/视图，恢复 100% 官方镜像 |
| `DebugGameplay.sqlite` | `PlayerColors` 补 `Alt1/2/3PrimaryColor`、`Alt1/2/3SecondaryColor` 6 列（`ColorManager.sql` + `Color_Tables.xml` 并集） |
| `source_index.sqlite` | 新增 `dlc_dependency`（12 行人工标注，Mode/Scenario DLC 依赖） |
| `annotations/dynamic_modifiers_dlc.json` | 新增：12 行标注的版本真值（DB 可再生，此文件是唯一真值） |
| `database/scripts/audit_schema_drift.py` | 新增：官方 schema 内存重建 → 逐表 `table_info` 比对，结构漂移 exit 1 |
| `scripts/rgn_validate_runner.mjs` | 新增 INSERT 显式列存在性预检 + 基础库关键表列断言；`enableDoubleQuotedStringLiterals` 对齐游戏双引号语义 |
| `DebugLocalization.sqlite` | skill 自带查询表 `Colors`/`Icons` 改名 `SkillAnnotation_Colors`/`SkillAnnotation_Icons`，避免与游戏表混淆 |
| `modifiers-cheatsheet.md` / `schema-annotated.md` / `modifiers-guide.md` / `database.md` / `SKILL.md` | 文档同步：官方 3 列铁律、DLC 标注查 `source_index.dlc_dependency`、PlayerColors 列全集 |

### 验证
- `audit_schema_drift.py`：修复库 0 漂移（exit 0）；修复前备份命中 `DynamicModifiers.IsDlcDependency` + `PlayerColors` 缺 6 列（exit 1）
- phantom 探针：修复前校验器放行；修复后命中 `INSERT INTO DynamicModifiers: unknown column(s) IsDlcDependency`
- 项目 `Mod_Adaptation/SecretSocieties`：71 条语句全部成功，0 悬空
- 项目 `Data`：双引号误报消除（成功 514→527、失败 23→10），剩余均为已知环境项（Players/PlayerItems 前端表、Config 的 DuplicateLeaders.Domain、Types.Hash UNIQUE、temp 表两遍顺序）
- `DebugConfiguration.sqlite`：78/78 表与官方 config schema 一致（0 漂移）
- `DebugGameplay.sqlite` / `DebugLocalization.sqlite`：`PRAGMA integrity_check = ok`

### 备份
- ⚠️ 历史打包 `civ6-modding*.zip`（3 个）内含修复前的 `DebugGameplay.sqlite`（含 `IsDlcDependency`，且 `PlayerColors` 缺 Alt 列），仅作历史归档；**不要直接覆盖现库**，如恢复必须先跑 `python database/scripts/audit_schema_drift.py`

---

## 追加修复：api.sqlite 两行 id 损坏（2026-09-17）

**背景**：`api_functions` 有 2 行 `id` 与 `sub_func_name` 混入了邻行 id 残留，此前仅以 `suspect_type` 标记存疑、未订正（原注释即写"人工订正名称后重测"）。

| 原值（损坏） | 修正后 | 依据 |
|---|---|---|
| `id=Q-MapGetCityPlotsGetWorkingCityIDQ-MapGetCityPlots`<br>`sub=GetWorkingCityIDQ-MapGetCityPlots` | `id=Q-MapGetCityPlotsGetWorkingCityID`<br>`sub=GetWorkingCityID`（= `true_name`） | 该行 `true_name` 已由 FireTuner 实测核出真名 `GetWorkingCityID`；`api_enhanced.json` 同 id 条目 `functionB=GetWorkingCityID` 佐证 |
| `id=Q-MapGetContinentCoastalPlotsQ-MapGetCityPlotsGetPurchasedByCity`<br>`sub=Q-MapGetCityPlotsGetPurchasedByCity` | `id=Q-MapGetContinentCoastalPlots`<br>`sub=NULL` | 该 API 是 `Map` 顶层函数（JSON 条目 `functionA=GetContinentCoastalPlots`、`functionB` 为空）；尾部是邻行 id 串入 |

- **影响面**：仅这 2 行。全表 161 条 `id` 与 `table+func+sub` 不自洽均为 GameInfo 命名约定（`Q-GameInfo<Table>`，`func_name` 本为空），属正常，未改动。
- **前置校验**：目标 id 均未被占用（0 冲突）；两行在 `api_args`/`api_returns` 均无关联行，故改 id 无外键孤儿。
- **处理方式**：改 `id` 与 `sub_func_name`，并在 `verify_note` 追加修复说明；`availability`/`verify_status`/`runtime_*` 等核验结论**原样保留**（`GetContinentCoastalPlots` 仍为"存疑"，因其 GP/UI 实测均为 ERR，属独立问题，不因改名而消失）。
- **验证**：两行 `id` 现已自洽；总行数保持 4857；子项数 1045→1044（第二行正确不再算子项）；`query_api.py --show Map.GetCityPlots.GetWorkingCityID` 与 `--show Map.GetContinentCoastalPlots` 均可直接命中。
- **连带**：`SKILL.md` 中过时的 `api.sqlite(5075函数)` 计数一并订正为 4857（现库实测值）。
