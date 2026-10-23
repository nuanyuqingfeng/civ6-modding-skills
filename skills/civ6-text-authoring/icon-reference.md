# 类 6 —— Icon 引用规范

> 跨类集合（语料 2,579 条含标记，`HasIcon=1`）。
> 权威图标名表：`reference/civ6-icon-tags.sql`（5,056 个 `[ICON_*]`，社区整理，随 skill 分发）
> 校验器：`civ6-modding/art/iconify_text.py`（`--audit`/`--check`/`--write`）+ `scripts/check_text_refs.py`

## 1. 图标标记语法

```
[ICON_<Name>]        行内图标（如 [ICON_Science] 科技值）
[ICON_BULLET]        列表符号（bullet）
[ICON_<Name>_LARGE]  大图标变体（如 [ICON_BOMBARD_LARGE]）
```

**★ 静默失败铁律**：图标名写错**不报错、只是不显示**（游戏里留空）。
所以"批量加图标"必须配"名称校验"，否则等于批量制造静默失败。

### 大小写
官方文本里大小写**并存**（`[ICON_Production]` 292 次 vs `[ICON_PRODUCTION]` 75 次；
`[ICON_Bullet]` 100 次 vs `[ICON_BULLET]` 83 次）——两者都能渲染（查找**不区分大小写**）。
- 权威表 `civ6-icon-tags.sql` 用**全大写**登记；
- **写作建议**：与同类官方文本保持一致（产出类官方常用大写，如 `[ICON_CULTURE]`；但 `[ICON_Gold]`/`[ICON_Faith]` 官方驼峰也很常见）——**只要名字在权威表里能查到即可**，不必强求单一大小写。

## 2. 常用图标词表（按语料出现频次）

| 产出 | 标记 | 类别 | 标记 |
|---|---|---|---|
| 战斗力 | `[ICON_Strength]` | 首都 | `[ICON_Capital]` |
| 金币 | `[ICON_Gold]` | 贸易路线 | `[ICON_TradeRoute]` |
| 生产力 | `[ICON_Production]` | 移动力 | `[ICON_Movement]` |
| 信仰值 | `[ICON_Faith]` | 公民 | `[ICON_Citizen]` |
| 文化值 | `[ICON_Culture]` | 食物 | `[ICON_Food]` |
| 科技值 | `[ICON_Science]` | 旅游业绩 | `[ICON_Tourism]` |
| 伟人点数 | `[ICON_GreatPerson]` | 宜居度 | `[ICON_Amenities]` |
| 住房 | `[ICON_Housing]` | 使者 | `[ICON_Envoy]` |
| 列表符号 | `[ICON_Bullet]` | 外交支持 | `[ICON_Favor]` |

> 完整表：`reference/civ6-icon-tags.sql`；工程自定义图标另查项目 `Icons` XML。

## 3. 其它文本标记（与图标同属「不可破坏的原始标记」）

| 标记 | 含义 | 范式 |
|---|---|---|
| `[COLOR_<C>]…[ENDCOLOR]` | 着色区间（红/绿/浮金等） | `[COLOR_RED]-17 [ICON_Bombard][ENDCOLOR] 轰炸攻击力。` |
| `[COLOR_FLOAT_GOLD]…[ENDCOLOR]` | 浮金（数值动效色） | `[COLOR_FLOAT_GOLD]+{1_Num} [ICON_Gold][ENDCOLOR]` |
| `[NEWLINE]` | 强制换行 | 多段能力描述、议程解释 |
| `{LOC_x}` | 内嵌另一条本地化文本 | `{LOC_ERA_TT_HAVE_GOLDEN_AGE_EFFECT}` |
| `{1_Arg}` / `{1_num}` / `{Amount}` | 引擎/Modifier 传参占位 | 见类1/类5 |

**规则**：这些标记在翻译/改写时**必须原样保留**，位置、大小写（对大小写敏感者如 `ENDCOLOR`）都不得改动。

## 4. 常见错误

| 错误 | 后果 | 正确 |
|---|---|---|
| 图标名拼错（`[ICON_Scicence]`） | **静默**不显示 | 对照 `civ6-icon-tags.sql` 校验 |
| 漏写 `[ENDCOLOR]` | 其后整段被着色 | 成对书写 |
| 把 `[ICON_Culture]` 写成 `[Icon_Culture]` | 前缀错 → 不解析 | 前缀必须 `ICON_` |
| 中文与图标间缺空格 | 官方惯例留空格（`+1 [ICON_Faith] 信仰值`） | 数值/图标左右留空格 |
| 翻译时把 `{1_Arg}` 译掉 | 传参失效 | 占位符不译 |

## 5. 校验（必跑）

```bash
# 审计文本里所有 [ICON_x] 是否可解析（只读）
python <civ6-modding>\art\iconify_text.py <工程根> --audit
# 预演自动补图标（不写盘）
python <civ6-modding>\art\iconify_text.py <工程根> --check
# 双向引用体检：图标正向 + {LOC_x} 反向 + Config 孤儿 tag
python <civ6-modding>\scripts\check_text_refs.py <工程根>
```

## 6. 校验清单

- [ ] 每个 `[ICON_x]` 都能在 `civ6-icon-tags.sql` 或工程 Icons 里解析到
- [ ] `[COLOR_*]` 与 `[ENDCOLOR]` 成对
- [ ] `{LOC_x}` / `{1_Arg}` 占位符原样保留
- [ ] 图标与前后文留空格
- [ ] `iconify_text.py --audit` + `check_text_refs.py` 均 0 问题
