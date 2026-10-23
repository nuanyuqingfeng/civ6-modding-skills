# reference/ — 简体中文语料（风云变幻为准）

本目录是 **civ6-text-authoring 的数据底座**：从 F 盘原版游戏文件按引擎真实加载顺序
（`EXP2 > EXP1 > base`）重导的简体中文有效文本。口径详见 `../SKILL.md` §0。

## 文件

| 文件 | 内容 | 说明 |
|---|---|---|
| `zh_corpus.sqlite` | **常规主库**：27,998 tag（可查询） | 表 `LocalizedText(Tag,Category,Text,Gender,Plurality,Tier,Source,IsAdjacency,HasIcon,TranslationMissing)` + 6 个视图 |
| `zh_mode_corpus.sqlite` | **模式语料**（仅 §1.1 模式模块）：1,282 tag | 同表结构 + 视图 `zh_mode`；⚠ 官方简体中文仅 197 可用、1,085 为 `TRANSLATION MISSING` |
| `catalog/mode.tsv` | 模式清单 1,282 条 | `Tag<TAB>Text`，可 grep |
| `catalog/leader_trait.tsv` | 类1 清单 1,946 条 | `Tag<TAB>Text`，可直接 grep |
| `catalog/item.tsv` | 类2 清单 4,682 条 | 同上 |
| `catalog/opening_ode.tsv` | 类3 开幕颂词 179 条（70 领袖加载介绍词 + 109 时代旁白） | 同上 |
| `catalog/diplomacy.tsv` | 类4 外交 3,748 条 | 同上 |
| `catalog/other.tsv` | 其余 17,443 条（百科/城市/界面） | 同上 |
| `zh_corpus_stats.txt` | 分类统计 | — |
| `zh_diff_report.txt` | 与旧库 `DebugLocalization.sqlite` 的差异（14 条实质不同 / 18 条集合差） | 验收依据 |
| `zh_tombstones.txt` | 风云变幻环境下**已删除**的 tag（11 条） | — |
| `civ6-icon-tags.sql` | 权威图标名表（5,056 个 `[ICON_*]`） | 类6 用 |
| `civ6-civilopedia-constants.sql` | 百科常量 | — |

## 查询

```sql
-- 主库
-- 某 tag 官方中文
SELECT Text FROM LocalizedText WHERE Tag='LOC_TRAIT_CIVILIZATION_AMAZON_DESCRIPTION';
-- 分类浏览（视图）
SELECT * FROM zh_leader_trait  LIMIT 20;
SELECT * FROM zh_opening_ode;                  -- 70 条领袖加载介绍词 + 109 条时代旁白
SELECT * FROM zh_diplomacy WHERE Tag LIKE 'LOC_DIPLO_KUDO%';
-- 跨类标记
SELECT Tag,Text FROM zh_adjacency;            -- 440 条相邻写法
SELECT Tag,Text FROM zh_icon;                 -- 2,579 条含 [ICON_]
-- 按来源分层
SELECT Tier,COUNT(*) FROM LocalizedText GROUP BY Tier;   -- base/exp1/exp2/dlc
```

## 重建（确定性）

```bash
# 常规类
python ../scripts/export_zh_text.py       # 从游戏文件重导 → zh_effective.json + 差异报告 + tombstone
python ../scripts/build_zh_corpus.py      # -> zh_corpus.sqlite + catalog/*.tsv
# 模式类（仅供「模式模块」用；见 ../mode-text.md）
python ../scripts/export_zh_text.py --class mode
python ../scripts/build_zh_corpus.py --class mode
```

依赖同级 `civ6-modding/database/scripts/build_localization.py`（分段权威实现）；脚本自动定位，
不改动既有工具与库。`zh_effective.json` 为中间产物（与 sqlite 冗余），已随仓库保存以便审计。
