---
name: civ6-text-authoring
description: "文明6 文本处理的**权威规范**（skill 体系内唯一）：简体中文文本语料（风云变幻为准，27,998 tag）+ 六大类写法规范 —— 领袖与文明 trait 能力 / 区域建筑单位等可关联物品 / **开幕颂词（领袖加载介绍词 LOC_LOADING_INFO_LEADER_*）** / 外交文本 / 相邻加成写法 / Icon 引用规范；另设**模式模块（仅路由）**处理 GameMode 文本。含 zh 语料库（zh_corpus.sqlite / zh_mode_corpus.sqlite / catalog TSV）+ 从 F 盘原版游戏文件按引擎加载顺序（EXP2>EXP1>base）重导的确定性管线。触发词：文本、文案、文本描述、LOC_、LocalizedText、本地化、localization、翻译、多语言、zh_Hans_CN、trait 文本、能力描述、领袖文本、文明文本、区域文本、建筑文本、单位文本、开幕颂词、领袖介绍词、领袖开场白、加载信息、加载文本、加载界面、加载介绍词、loading info、loading_info、LOC_LOADING_INFO_LEADER、opening ode、时代旁白、era、外交文本、diplomacy、KUDO、WARNING、相邻加成、adjacency、图标引用、[ICON_、COLOR、NEWLINE、百科文本、文明百科、pedia、文案润色、措辞优化、游戏模式、模式文本、game mode、GAMEMODE、_mode、蛮族氏族、英雄模式、秘密结社、行业与公司、垄断、天启模式、塔防、戏剧时代、树随机、Barbarian Clans、Heroes、Secret Societies、Monopolies、Apocalypse、Tower Defense、Dramatic Ages、Tree Randomizer。"
version: "1.0"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - civilization
  - localization
  - text
  - loc
  - chinese
  - zh_Hans_CN
  - diplomacy
  - adjacency
  - icon
models:
  recommended:
    - claude-sonnet-4
    - claude-opus-4
  compatible:
    - claude-3-5-sonnet
    - gpt-4
    - gpt-4o
languages:
  - zh
  - en
---

# civ6-text-authoring — 文明6 文本权威规范

> ★ **本 skill 是 civ6-* 家族中「文本处理」的唯一权威规范。**
> 家族任何流程一旦涉及**面向玩家的文本描述**（新建 / 修改 / 翻译 / 润色 / 校验文案），
> **一律路由到本 skill 处理**；其它 skill 内与文本相关的规则段落只保留路由指针，不再各自维护口径。
>
> 唯一定义（LOC tag 命名、后缀变体、占位符、标记、图标引用、相邻加成句式、开幕颂词文风）
> 均以本 skill 为准；发生冲突时以 `reference/zh_corpus.sqlite`（风云变幻语料）为准绳。

## 0. 语料底座（风云变幻为准）

简体中文语料从 **F 盘原版游戏文件**按**引擎真实加载顺序**单遍重导，不采信任何二手快照：

| 项 | 值 |
|---|---|
| 提取范围 | **常规类**：本体 + Expansion1 + Expansion2 + 全部领袖/文明 DLC；**排除** Mode 与 Scenario（模式另设 §1.1 模式模块） |
| 分层裁决 | `EXP2 > EXP1 > base`；包内 `<RemoveText>`(Priority=2) 先于 `<Translations>`；各领袖包对 EXP2 只补缺不覆盖 |
| 删除语义 | `<Delete>` 无 `Language` 属性 = **全局删除**（对 zh 同样生效）→ 进 tombstone 并从有效文本剔除 |
| 规模 | **27,998 tag**（base 15,229 / EXP1 / EXP2 / DLC），tombstone 11 |
| 唯一真值 | `reference/zh_corpus.sqlite`（可查询）+ `reference/catalog/*.tsv`（可 grep）|

> 「风云变幻环境为唯一检验标准」的落地口径：**引擎载入顺序**决定最终生效文本。
> 示例 `LOC_MINOR_CIV_CULTURAL_TRAIT_LARGE_INFLUENCE_BONUS` 经 base→EXP1→EXP2→Ethiopia 四层改写，
> 最终生效值是 Ethiopia 包文案；`LOC_TECH_BANKING_DESCRIPTION` 被 EXP2 删除且未复现 → 该环境下**不存在**。
> 与「不应用删除、DLC 只补缺」的旧参考库 `DebugLocalization.sqlite` 存在 14 条取值差、18 条集合差，
> 差异明细见 `reference/zh_diff_report.txt` —— **本 skill 语料为权威**。

### 语料查询（写文本前先查现成范式）

```bash
# 某 tag 的官方中文（先查有没有现成 tag，能复用就复用）
python -c "import sqlite3;print(sqlite3.connect('reference/zh_corpus.sqlite').execute(\"SELECT Text FROM LocalizedText WHERE Tag='LOC_TRAIT_CIVILIZATION_AMAZON_DESCRIPTION'\").fetchone())"

# 按分类浏览（catalog/*.tsv 可直接 grep）：leader_trait / item / opening_ode / diplomacy / other
# 相邻加成全部写法：catalog 里 grep「相邻」；或 SQL：WHERE IsAdjacency=1
# 含图标标记的文本：WHERE HasIcon=1
```

## 1. 六大分类 → 文档路由

| # | 分类 | 覆盖对象（LOC 命名空间） | 规范文档 | 语料规模 |
|---|---|---|---|---|
| 1 | 领袖与文明等 trait 能力 | `LOC_LEADER_*` `LOC_CIVILIZATION_*` `LOC_TRAIT_*` `LOC_ABILITY_*` `LOC_AGENDA_*` `LOC_GOVERNOR_*` `LOC_CIVINFO_*` `LOC_UNIQUE_*` | [leader-trait-text.md](leader-trait-text.md) | 1,946 |
| 2 | 区域/建筑/单位等（可被 trait 关联的物品） | `LOC_DISTRICT_*` `LOC_BUILDING_*` `LOC_UNIT_*` `LOC_UNITNAME_*` `LOC_IMPROVEMENT_*` `LOC_PROJECT_*` `LOC_PROMOTION_*` `LOC_RESOURCE_*` `LOC_FEATURE_*` `LOC_POLICY_*` `LOC_BELIEF_*` `LOC_GREAT*` `LOC_GOVT_*` `LOC_CIVIC_*` `LOC_TECH_*` `LOC_BOOST_*` | [item-text.md](item-text.md) | 4,682 |
| 3 | **开幕颂词**（**领袖加载介绍词**为主 + 时代旁白为辅） | `LOC_LOADING_INFO_LEADER_*`（70 条，含 `_DEFAULT` 兜底）；辅 `LOC_ERA_*`（109 条） | [opening-ode.md](opening-ode.md) | 179 |
| 4 | 外交文本 | `LOC_DIPLO_*` `LOC_DIPLOMACY_*` `LOC_DIPLOACTION_*` `LOC_GOSSIP_*` `LOC_EMERGENCY_*` | [diplomacy-text.md](diplomacy-text.md) | 3,748 |
| 5 | 相邻加成写法 | 跨类：`IsAdjacency=1`（含「相邻」或 `+N：每个…` 句式） | [adjacency-text.md](adjacency-text.md) | 440 |
| 6 | Icon 引用规范 | 跨类：`HasIcon=1`（`[ICON_x]` / `[COLOR]` / `[NEWLINE]` 标记） | [icon-reference.md](icon-reference.md) | 2,579 |

> 其余（百科 `LOC_PEDIA_*` 4,725、城市/市民/地名、界面/通知/选项等 17,443 条）归入 `other` 桶，
> 见 `reference/catalog/other.tsv`；其写法仍受 §2 通用规则约束。

### 1.1 模式模块（GameMode 文本，**仅路由**）

> **常规六分类不含任何模式文本。** 仅当工作内容出现**模式关键词**时，路由到 [mode-text.md](mode-text.md)：
> · tag/文件名 `*_mode` / `*_MODE` / `GAMEMODE_*` / `*_Translations_Text_MODE.xml`
> · 模式中文名：蛮族氏族、英雄、秘密结社、行业与公司（垄断）、天启、塔防、戏剧时代、树随机
>
> 该模块自带模式语料 `reference/zh_mode_corpus.sqlite`（**1,282 tag**）与模式文本编辑方法（注册判据 / 文件命名 /
> 「只加不覆盖」语义 / 模式专属 tag 前缀）。⚠ **官方简体中文覆盖率极低**：仅 **197 条可用**，
> **1,085 条为 `TRANSLATION MISSING`**（英雄/秘密结社/行业与公司/天启/塔防及多个领袖包附带的模式内容未译）
> —— 命中未译行须自行从英文翻译。详见 [mode-text.md](mode-text.md)。

## 2. 通用规则（跨六类强制）

1. **标记必须原样保留**：`[ICON_X]`、`[COLOR_*]…[ENDCOLOR]`、`[NEWLINE]`、`{LOC_TAG}`、`{1_Arg}` 占位符。
   → 细则见 [icon-reference.md](icon-reference.md)。
2. **语言代码固定**：`zh_Hans_CN` / `zh_Hant_HK` / `en_US`（默认基线 L0 三语；项目 AGENTS.md 优先）。
3. **中文文件处理**：UTF-8 读写、不改编码/换行风格/无关内容；PowerShell 先 `chcp 65001`；
   禁用 here-string / `Set-Content` / `sed` 写中文；查看用 Read 工具。
4. **先查现成语料再写**：能复用官方 tag 就复用（文案与官方逐字一致）。
5. **写后必校验**：`[ICON_x]`/`{LOC_x}` 双向引用闭合 → §4 执行层。
6. **数值/产出一律带图标**：新建或改写的 **trait / 物品（区域·建筑·单位·改良）/ 议程描述**里，每个产出、战力、移动力、伟人点数等**数值前必须挂 `[ICON_x]`**；官方惯例是「数值 + 空格 + `[ICON_x]` + 空格 + 名词」（`+1 [ICON_Faith] 信仰值`），英文同样带图标（`+1 [ICON_Faith] Faith`）。生成后**必须**跑 `iconify_text.py --audit/--check/--write` 补齐，再跑 `check_text_refs.py` 确认闭合。
   ⚠ **外交台词不加图标**：`LOC_DIPLO_*_ANY` 一类的**对白句**（领袖说的话）不挂图标——官方 2,491 条对白里仅 2 条含 `[ICON_x]`，且都是旁注说明；图标只用于**规则说明类**文本（能力/物品描述、`LOC_DIPLOACTION_*_DESCRIPTION`）。

## 3. 环境路径

| 用途 | 路径 |
|---|---|
| P3 游戏本体 | `F:\Steam\steamapps\common\Sid Meier's Civilization VI` |
| 本 skill 语料 | `reference/zh_corpus.sqlite` |
| 家族参考库（旧，非权威） | `..\civ6-modding\database\DebugLocalization.sqlite` |

## 4. 执行层（校验脚本，位于 civ6-modding，本 skill 引用而非复制）

> 为避免跨仓库断裂，文本校验器**保持单源**在 `civ6-modding`，本 skill 以路径引用。

| 脚本 | 查什么 | 命令 |
|---|---|---|
| `check_text_refs.py` | `[ICON_x]` 正向 / `{LOC_x}` 反向 / Config 孤儿 tag | `python <civ6-modding>\scripts\check_text_refs.py <工程根>` |
| `check_adjacency_text.py` | 相邻加成描述与 `Adjacency_YieldChanges` 一致性 | `python <civ6-modding>\scripts\check_adjacency_text.py <工程根>` |
| `iconify_text.py` | 内置关键词→`[ICON_x]` 映射；`--audit`/`--check`/`--write` | `python <civ6-modding>\art\iconify_text.py <工程根> --audit` |

## 5. 语料重建管线（本 skill 自带）

```bash
# 常规类（默认）
python scripts/export_zh_text.py            # → reference/zh_effective.json + 差异报告 + tombstone
python scripts/build_zh_corpus.py           # → reference/zh_corpus.sqlite + reference/catalog/*.tsv
# 模式类（仅供 §1.1 模式模块）
python scripts/export_zh_text.py --class mode   # → reference/zh_mode_effective.json + 差异报告
python scripts/build_zh_corpus.py --class mode  # → reference/zh_mode_corpus.sqlite + reference/catalog/mode.tsv
```
依赖 `civ6-modding` 的 `build_localization.Segment`（分段/文件枚举权威实现），脚本自动定位家族目录。

## 6. 家族路由收口

- `civ6-modding` §4.1（多语言文本 / 本地化）→ 已改为指向本 skill 的**路由指针**。
- 家族索引 `civ6-modding/reference/FAMILY_INDEX.md` 已登记本 skill。
- `civ6-modding` SKILL.md 的 Task Routing 表新增「文本描述 → civ6-text-authoring」。

---

## 附：与旧口径的差异（验收依据）

`reference/zh_diff_report.txt` 记录本语料 vs 旧库 `DebugLocalization.sqlite`：
- **14 条实质不同** = 旧库停留在 base 旧值、本语料取到风云变幻生效值（正确）；
- **18 条旧库独有** = 10 条为本环境已删除（tombstone）+ 8 条为工程自造 tag（非游戏文本）。

作者：千与千寻瀑 · MIT
