# 平衡补丁 / 差分覆盖（Balance Patch）

> 来源：`工程 A 的平衡补丁` + `工程 C 的平衡补丁` 两个纯差分工程横向审查（标 ★ 者为逐条对撞核实）。
> 适用：**不新增内容，只改主工程数值 / 解挂载 / 覆盖文本**的"补丁 mod"。

---

## 一、定位与总原则

平衡补丁是**差分覆盖层**，不是独立的 mod。四条总原则：

1. **只改值，不重定义** —— 保住主工程的定义，卸载后能完整恢复；
2. **只断关系，不删定义** —— `DELETE` 只删绑定表；
3. **软依赖** —— 不声明主工程 `<Reference>`，用 `Criteria/ModInUse` 判"主工程在场才跑"；
4. **必须晚于主工程的一切覆盖层** —— 见 §三（这是最容易翻车的一条）。

---

## 二、工程骨架

```
Balance_Patch.civ6proj
├─ ActionCriteriaData
│    <Criteria id="MainMod"><ModInUse>主工程GUID</ModInUse></Criteria>
│    <Criteria id="OtherMod_Disabled"><ModInUse inverse="1">对方GUID</ModInUse></Criteria>
├─ AssociationData          ← 只写 DLC 依赖（如 Gathering Storm），**不写主工程**
├─ FrontEndActionData       ← 前端文本覆盖（LoadOrder 高于主工程前端层）
└─ InGameActionData
     <UpdateDatabase id="Patch_Data"> <Criteria>MainMod</Criteria> <Properties><LoadOrder>…</LoadOrder></Properties> …
     <UpdateText     id="Patch_Text"> 同上
     <AddGameplayScripts id="Patch_Lua"> <File>…_Patch.lua</File>   ← 只做标志广播
```

> ⚠ **不要用 `<Dependencies><Mod id=…>` 做与主工程的绑定** —— 那是硬依赖，会在缺主工程时报缺失。
> 用 `Criteria/ModInUse` 则是"主工程不在场就静默跳过整块动作"，补丁可安全常驻订阅列表。
> 完整 `ModInUse` 三态（正向 / `inverse="1"` / `any="1"`）见 `project-setup.md`。

---

## 三、★ LoadOrder：补丁必须压过主工程的**最终覆盖层**（实测踩过）

**症状**：补丁数值"改了但游戏里没变"，且**完全无报错**。

**根因**：主工程内部往往还有自己的"最终覆盖层"（HD 适配 / 兼容补丁 / 立绘覆盖），它的 `LoadOrder` 比普通内容层高得多。补丁若取一个"看起来很大"的值，仍可能**低于**那一层 → 补丁先执行、主工程覆盖层后执行 → **补丁被静默回滚**。

**实测对撞**（工程 C 的平衡补丁 `888888` vs 主工程 HD 层 `999999`，逐条核实 25+ 处被回滚）：

| ModifierId | 补丁值 | 主工程 HD 层值 | 实际生效 |
|---|---|---|---|
| `GOV_PROMO_…_GOVERN_VIRTUE_1` | `10` | `20` | **HD 胜** |
| `…_LOGICAL_HARMONIOUS_GREATPERSON_POINT` | `10` | `40` | **HD 胜** |
| `…_TODO_LIST_PRODUCTION_BONUS` | `0` | `15` | **HD 胜** |
| `TRAIT_INDUSTRIAL_TRADE_YIELD_BONUS_…` | `3` | `10` | **HD 胜** |

> 附带后果：HD 层还把描述改指向 `*_HD_DESCRIPTION`，而补丁改的是**原 tag** → 补丁文案成死文本。

**硬性规则**

1. **先摸清主工程各层的 LoadOrder 分布**（`.civ6proj` 全量提取），再给补丁取一个**严格大于最高内容覆盖层**的值；
2. **数据层与文本层分别取值**（实测主工程数据层与文本层的顶值常常不同：数据 `999999` / 文本 `777777`）；
3. **前端（FrontEnd）与游戏内（InGame）是两条独立序列**，各自都要压过；
4. ⚠ **跨 mod 同 LoadOrder 的执行次序无保证**。多个工程都爱用 `999999`，一旦与别人的同值动作写同一张表同一行，就是不确定行为 → **新增同名 tag / 同 ModifierId 时务必自查是否撞车**。

**自检**：把补丁的每个 `LoadOrder` 与主工程 `.civ6proj` 的**全部** `LoadOrder` 值列表比对，确保同轴同层内补丁最大。

---

## 四、差分手法表

| 目的 | 写法 | 关键点 |
|---|---|---|
| **改数值** | `UPDATE ModifierArguments SET Value = … WHERE ModifierId = …` | 最常用 |
| **相对缩放** | `SET Value = 0.5 * Value WHERE ModifierId LIKE '…'` | 主工程调基数时"减半"语义自动跟随 —— **优于写死绝对值** |
| **改内容本体** | `UPDATE Governors/Projects/Units/Resources/Improvements/… SET …` | 直接改主工程行 |
| **改结构 / 换门槛** | `UPDATE Modifiers SET ModifierType / SubjectRequirementSetId / OwnerRequirementSetId / SubjectStackLimit` | 免删旧建新，**不破坏其他表对同一 ModifierId 的引用** |
| **解挂载（停用）** | `DELETE FROM TraitModifiers / DistrictModifiers / UnitPromotionModifiers / GovernorPromotionModifiers / …` | 只断关系，**保留 `Modifiers` + `ModifierArguments`** → 卸载可恢复 |
| **彻底删除** | 绑定表 → `Modifiers` → `ModifierArguments` **三连** | 只删中间表会留悬空绑定与孤儿参数 |
| **清动态 ID 族** | `DELETE … WHERE ModifierId LIKE '族前缀%'` | 主工程若用 `WITH RECURSIVE` 批量生成，补丁**无法枚举**，只能按命名族清 |
| **追加参数** | `INSERT OR REPLACE INTO ModifierArguments … SELECT '目标ModifierId','新Name',值` | 主键 `(ModifierId, Name)` → 天然幂等 |
| **覆盖文本** | `REPLACE INTO LocalizedText (Tag, Language, Text) VALUES …` | 主键 `(Language, Tag)`，一条即精确覆盖整条词条，**无需 WHERE、无需 DELETE** |
| **重基到原版行** | `DELETE` 本 mod 行 → `INSERT INTO <表> SELECT 部分字面量, 其余列 FROM <表> WHERE <原版行>` | 让自定义行的数值跟随原版；**收尾必须补回被连带删掉的关联行** |
| **通知主工程** | `Game.SetProperty("X_BALANCED", 1)`，主工程 Lua 读值分流 | `Criteria` 是加载期判据，Lua 里读不到 → 只能用 PROPERTY 桥 |

> ⚠ **`LIKE` 里的 `_` 是通配符**：字面下划线必须 `ESCAPE '\'`，即 `LIKE '%\_GOLD\_QYQXP' ESCAPE '\'`。漏写 `ESCAPE` 会静默多匹配一堆不相干的行。
> ⚠ **`LIKE` 清族要靠命名约定**：主工程若用递归 CTE 批量生成 ID，**必须同步约定「可被 `LIKE` 命中的稳定命名族」**，否则下游无法差分 —— 这是"生成式命名"设计的隐性契约。

---

## 五、一份代码出两个版本：全局标志 + 公式化系数

比"补丁里复制一份完整逻辑"更省事的做法：**补丁只设一个全局标志，主工程把所有可调数值写成该标志的算术式。**

```lua
-- 补丁侧（6 行脚本，全部内容就这一句）
Game.SetProperty("MYMOD_BALANCED", 1)
```
```lua
-- 主工程侧：开局读一次
local B = (Game.GetProperty("MYMOD_BALANCED") == 1) and 1 or 0;
-- 之后所有可调数值写成 B 的表达式
local v1 = 3 / (1 + 2 * B);   -- B=0 → 3 ; B=1 → 1
local v2 = 10 * (1 + B);      -- B=0 → 10; B=1 → 20
local v3 = 5 - 2 * B;         -- B=0 → 5 ; B=1 → 3
local v4 = math.min(x, 5);
```

**收益**：两套平衡共享同一份逻辑与 UI（无双份维护）；无加载顺序风险（只是读一个属性）。
**代价**：读代码必须先知道 `B` 的取值 —— 建议把公式集中在文件头并注释。

> 同一模式可被**多个补丁**复用（实测 `Rover` 侧与主包侧各有一套独立的 `XXX_BALANCED` 标志）。

---

## 六、文本差分

- 用 `REPLACE INTO LocalizedText`，**只列被改动的 tag**（实测 40+ 条 vs 主包 1752 条）；
- **语言要跟主工程对齐**：实测有补丁只覆盖 5 语言、主工程 8 语言 → 缺的 3 语言仍是未削弱文案；
- 前端文本（选人界面能力描述）与游戏内文本是两套 tag，分别注册在 `FrontEndActions` / `InGameActions`；
- **旧文案留档**：若用了"公共头部 `_FORMER` + 尾部"的片段拼接手法，补丁改写 `_FORMER` 即可让前后端同时生效。

---

## 七、验证清单

- [ ] 补丁各 `LoadOrder` **严格大于主工程同轴的最高覆盖层**（数据 / 文本 / 前端分别核对）
- [ ] 与主工程**无 `Association` 硬依赖**，改用 `Criteria/ModInUse`
- [ ] 所有 `DELETE` 都只针对绑定表（"停用"）或完整三连（"删除"）
- [ ] 无裸 `INSERT INTO` 到绑定了主键的枚举表
- [ ] 文本用 `REPLACE`，覆盖语言集与主工程一致
- [ ] `LIKE` 里的字面下划线都带 `ESCAPE '\'`
- [ ] 补丁 `.lua` **两处登记**（`<Content Include>` + Action，见 `gotchas.md` §3）
- [ ] 卸载补丁后主工程行为完全恢复（定义未被动过）
- [ ] 跑 `rgn_validate`

---

## 八、踩过的坑

| 坑 | 症状 |
|---|---|
| LoadOrder 低于主工程最终覆盖层 | **数值改了但没生效，零报错**（§三） |
| 只删 `Modifiers` 不删绑定表/参数表 | 悬空绑定，加载报 `Invalid Reference` |
| 用 `<Dependencies><Mod>` 绑主工程 | 缺主工程时整包报缺失，而非静默跳过 |
| `LIKE '%\_X'` 漏 `ESCAPE` | 静默多匹配，误改一片 |
| 只覆盖部分语言 | 其余语言仍是旧文案 |
| 补丁改的 tag 被主工程 HD 层改指向 `_HD_` 变体 | 补丁文案成死文本 |
| 补丁脚本只写 `<Content Include>` | 标志永不设置，两套平衡都不对 |
| 多个 mod 都用 `999999` | 跨 mod 执行次序无保证 → 不确定行为 |
