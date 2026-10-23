# 模式模块 —— Mode 文本（**仅路由**）

> **本模块是独立的「仅路由」模块**：常规六分类（类1–类6）**不含任何模式文本**；
> 仅当工作内容出现**模式关键词**时才路由进本模块，并允许取用本模块下的模式语料与编辑方法辅助完成任务。
> 语料：`reference/zh_mode_corpus.sqlite`（1,282 tag）｜ 清单：`reference/catalog/mode.tsv`

## 1. 路由触发关键词（命中任一即进入本模块）

| 类型 | 关键词 |
|---|---|
| tag / 文件名 | `*_mode`、`*_MODE`（如 `LOC_BARBARIAN_CLANS_MODE_*`）、`GAMEMODE_*`、`*_Translations_Text_MODE.xml`、`_MODE` 后缀 |
| 模式中文名 | **蛮族氏族**、**英雄**、**秘密结社**、**行业与公司**（垄断）、**天启**、**塔防**、**戏剧时代/黑暗时代**、**树随机** |
| 模式英文名 | Barbarian Clans / Heroes / Secret Societies / Monopolies and Corporations / Apocalypse / Tower Defense / Dramatic Ages / Tree Randomizer |

> 命中以上任一 → **只加载本模块**，不要回常规六分类找模式文本（那里没有）。

## 2. 模式清单（8 个）与文本来源

| 模式（GAMEMODE / 目录） | 中文名 | 权威数据 |
|---|---|---|
| `GAMEMODE_BARBARIAN_CLANS`（`BarbarianClansMode`） | 蛮族氏族模式 | 分段实测（不在 GameModeItems） |
| `GAMEMODE_HEROES` | 英雄模式 | `GameModeItems` |
| `GAMEMODE_SECRETSOCIETIES` | 秘密结社模式 | `GameModeItems` |
| `GAMEMODE_MONOPOLIES` | 行业与公司模式 | `GameModeItems` |
| `GAMEMODE_APOCALYPSE` | 天启模式 | `GameModeItems` |
| `GAMEMODE_DRAMATICAGES` | 戏剧时代模式 | `GameModeItems` |
| `GAMEMODE_TOWERDEFENSE` | 塔防模式 | `GameModeItems` |
| `TreeRandomizer` | 科技树随机 | 分段实测 |

- 权威模式清单表：`civ6-modding/database/DebugConfiguration.sqlite → GameModeItems`（6 行）+ 分段实测 2 个。
- 模式文本**不一定在专属目录**：实测分布在这些包的 `*_Text_MODE.xml` 里——
  `BarbarianClansMode` / `Babylon` / `TreeRandomizer` / `Byzantium_Gaul` / `KublaiKhan_Vietnam` /
  `Ethiopia` / `Portugal` / `GranColombia_Maya`（New Frontier 领袖包附带模式内容）。

## 3. ⚠ 官方简体中文覆盖率（最重要的警示）

模式类 zh 共 **1,282 tag**：**可用仅 197**，**1,085 条的值为 `[COLOR_RED]TRANSLATION MISSING[ENDCOLOR]`**（官方未译）。

| 缺失来源包 | 缺失条数 |
|---|---|
| KublaiKhan_Vietnam | 320 |
| Babylon | 317 |
| Ethiopia | 235 |
| Byzantium_Gaul | 102 |
| GranColombia_Maya | 60 |
| Portugal | 48 |
| TreeRandomizer | 3 |

**含义**：游戏里这些模式文本会显示英文或"翻译缺失"占位。写/改模式文本时：
- 若命中 `TRANSLATION MISSING` → **必须自行从英文翻译**（英文原文可查游戏 `en_US` 文件，
  或 `civ6-modding/database/Localization_Mode.sqlite` 的 `en_US` 行）；
- 可用文本（197 条，多为**蛮族氏族** `LOC_BARBARIAN_*` / `LOC_TRIBE_*` 与 `LOC_GAMEMODE_*` 名）
  → 直接复用官方译法，保持逐字一致；
- 本模块语料以 `TranslationMissing=1` 标出未译行，便于甄别（见 §5）。

## 4. 模式文本的编辑方法

1. **注册判据**（权威分段）：`.modinfo` 的
   `<InGameActions><UpdateText criteria="X">` → `<ActionCriteria><Criteria id="X">` 的
   `<ConfigurationValueMatches><ConfigurationId>GAMEMODE_*</ConfigurationId>`。
2. **文件命名惯例**：`<包>_Translations_Text_MODE.xml`，属性定语言（`<Replace Tag Language="zh_Hans_CN">`）；
   亦有 `Text/<lang>/` 目录形态，两种都要认（否则漏一半）。
3. **模式库语义 = 只加不覆盖**：模式文本独立分层，**不参与**常规的 `EXP2>EXP1>base` 覆盖
   （`build_localization.py` 的 `load_layered(seg,'mode')` 即此口径）。
4. **模式专属 tag 前缀**（便于识别，勿与常规混用）：
   `LOC_GAMEMODE_*`（模式名/说明）、`LOC_BARBARIAN_*`/`LOC_TRIBE_*`/`LOC_TREAT_*`（蛮族氏族）、
   `LOC_HERO_*`（英雄）、`LOC_SECRETSOCIETY_*`（秘密结社）、`LOC_INDUSTRY_*`/`LOC_CORPORATION_*`（行业与公司）、
   `LOC_TREE_*`（科技树随机）、`LOC_QUEST_*`。
5. **情景仍排除**：`RULESET_SCENARIO_*` 类情景文本**不属本模块**（也不属常规）。

## 5. 语料与查询

```sql
-- 模式类全部（1,282）
SELECT Tag,Text FROM zh_mode WHERE TranslationMissing=0;          -- 可用 197
SELECT Tag,Text FROM zh_mode WHERE TranslationMissing=1 LIMIT 20; -- 官方未译 1,085
SELECT Tag,Source,COUNT(*) FROM "zh_mode" GROUP BY Source ORDER BY 3 DESC;  -- 逐包分布
```
- 主库：`reference/zh_mode_corpus.sqlite`（视图 `zh_mode`，列含 `TranslationMissing`）
- 清单：`reference/catalog/mode.tsv`（`Tag<TAB>Text`，可 grep）
- 重建：`python scripts/build_zh_corpus.py --class mode`（先 `python scripts/export_zh_text.py --class mode`）
- 交叉核对基准：`civ6-modding/database/Localization_Mode.sqlite`（本导出与其 zh 行**逐条一致，0 差异**）

## 6. 与常规模块的边界

| | 常规模块（类1–类6） | 模式模块（本模块） |
|---|---|---|
| 语料 | `zh_corpus.sqlite`（27,998） | `zh_mode_corpus.sqlite`（1,282） |
| 内容 | 本体+EXP1+EXP2+全部领袖/文明 DLC | 8 个 GameMode 文本 |
| 分层 | `EXP2>EXP1>base` + DLC 补缺 | **只加不覆盖** |
| 路由 | 命中文本关键词即用 | **仅**命中模式关键词才进入 |

> 一句话：**常规不含模式，模式只在被点名时进入。**
