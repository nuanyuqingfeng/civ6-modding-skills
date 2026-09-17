# reference/sources/ —— 外部参考件（随包分发）

本目录存放 skill 结论所**依赖的外部资料来源**，便于他人核对出处、复算数字、直接引用常量。

| 文件 | 原文件名 | 出处 / 许可 | 被谁引用 |
|---|---|---|---|
| `Civ-VI-Modding-Companion-2.0.xlsx` | Civ VI Modding Companion 2.0.xlsx | 社区作品，作者 **ChimpanG / WildW** | `reference/api_enhanced.json` 的 `source` 字段；`SKILL.md` 文末致谢 |
| `Agendas-reference.xlsx` | 议程表(绝大部分).xlsx | 社区整理的原版议程文本 | `agenda-authoring.md`（议程描述句式对齐原版） |
| `civ6-icon-tags.sql` | 图标大全-号码菌.sql | 社区整理（作者：号码菌） | **原版文本可用的 5056 个 `[ICON_*]` 标记全表**（`INSERT OR REPLACE INTO Icon_Collection`，SQLite 语法，可直接建库查询） |
| `civ6-civilopedia-constants.sql` | C6可用颜色与图标.sql | 社区整理 | 百科常量（`[COLOR_*]` / `[ICON_*]` / 介绍文本）的 MySQL dump；查颜色/图标常量名与备注用 |
| `stretchmode-vanilla-stats.md` | StretchMode方法汇总.md | 社区整理 | 原版 ForgeUI `StretchMode` 各取值的**出现次数统计**与效果说明；`ui-controls.md` 的 StretchMode 一节配套 |

说明：
- 这些文件是**第三方社区资源**，此处按"引用来源"随包分发；版权归原作者，若原作者要求移除请提 issue。
- 本 skill 自己的手工标注成果在别处：文本颜色/图标的**人工标注侧表**是
  `database/DebugLocalization.sqlite` 的 `SkillAnnotation_Colors` / `SkillAnnotation_Icons`；
  API 核验记录的真源是 `database/api-verification-2026-09-08/`。
- 本目录**不放**游戏原始素材；需要原版贴图请从自己的游戏安装目录（pantry）获取。

## 怎么用 `civ6-icon-tags.sql`

```bash
# 建一张可查的图标名表（SQLite）
python -c "import sqlite3;c=sqlite3.connect('icons.db');c.executescript(open('reference/sources/civ6-icon-tags.sql',encoding='utf-8').read());c.commit()"
# 之后：SELECT * FROM Icon_Collection WHERE IconString LIKE '%[ICON_GOLD%'
```

> ⚠ 标记必须在**游戏文本**里才生效（`UpdateText` 走 `Text/*.sql`）；图标名写错不会报错，只是不显示。
