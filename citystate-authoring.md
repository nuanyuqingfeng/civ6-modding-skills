# 城邦编写（City-State Authoring）

> 来源：`工程 E`（27 个自定义城邦）工程审查 + skill 自带数据库实查（标 ★）。
> 所有表名/列名/取值均已用 `DebugGameplay.sqlite` / `DebugConfiguration.sqlite` 复核。

---

## 一、★ 城邦横跨两个数据库 —— 这是本主题最容易踩错的一点

同一套"文明/领袖"概念被拆到两个库，**写错库 = 静默无效**：

| 库 | 文件 | 含有的表 |
|---|---|---|
| **Gameplay 库** | `database/DebugGameplay.sqlite`（427 表） | `Civilizations` ✓ / `Leaders` ✓ / `Colors` ✓ / `PlayerColors` ✓ / `DuplicateLeaders` ✓；**`CityStates` ✗ `Parameters` ✗ `ParameterDependencies` ✗ `Players` ✗ `PlayerItems` ✗** |
| **Configuration 库** | `database/DebugConfiguration.sqlite`（78 表） | `CityStates` ✓ / `Parameters` ✓ / `ParameterDependencies` ✓ / `Players` ✓ / `PlayerItems` ✓ / `DuplicateLeaders` ✓；**`Civilizations` ✗ `Leaders` ✗ `Colors` ✗ `PlayerColors` ✗** |

推论（硬性）：

- **选单条目**（`CityStates` / `Parameters` / `ParameterDependencies`）只能写进 **`FrontEndActions`** 的 `UpdateDatabase`；
- **游戏内文明本体**（`Civilizations` / `Leaders` / `Traits` / `Colors` / `PlayerColors`）走 **`InGameActions`**；
- `Players` / `PlayerItems` 属**前端**（这解释了为什么文明/领袖的 `Config_*.xml` 总挂在 FrontEndActions）；
- `DuplicateLeaders` **两个库都有** → 需要同时声明（同 `Leaders` 多文明的处境，见 §五）。

> 实测照抄第三方 mod 会引入"解析不到的配置依赖"：某工程的 27 行 `Parameters` / `ParameterDependencies` 依赖 `ConfigurationId='SelectCityStates'`，而该值在**原版全库 grep 零命中**，只出现在工坊 CSE（City-States Expanded）与 YnAMP 里 → 这 27 行大概率是死配置。**城邦能否进选单，只由 `CityStates.Domain` 决定。**

---

## 二、`CityStates` 表（Configuration 库）

★ 实查列定义与取值：

| 列 | 说明 | 实测取值 |
|---|---|---|
| `Domain` | **决定进哪个规则集的选单** | `StandardCityStates`(42) / `Expansion1CityStates`(42) / `Expansion2CityStates`(48) |
| `CivilizationType` | 指向 Gameplay 库的 `CIVILIZATION_*` | — |
| `Name` | LOC tag | 原版用独立的 `LOC_..._FRONTEND_NAME`（可选） |
| `Icon` | 选单图标名 | `ICON_CIVILIZATION_<X>` |
| `CityStateCategory` | 类别（六大类） | ★ `TRADE` / `SCIENTIFIC` / `RELIGIOUS` / `MILITARISTIC` / `INDUSTRIAL` / `CULTURAL`，各 22 条 |
| `Bonus` / `Bonus_XP1` / `Bonus_XP2` | 三档规则集下的能力描述 LOC | 各写各的 |
| `SortIndex` | 选单排序 | — |

```sql
-- FrontEndActions → UpdateDatabase
INSERT OR REPLACE INTO CityStates
  (Domain, CivilizationType, CityStateCategory, Name, Icon, Bonus, SortIndex) VALUES
('Expansion2CityStates', 'CIVILIZATION_MYCS', 'SCIENTIFIC',
 'LOC_CIVILIZATION_MYCS_NAME', 'ICON_CIVILIZATION_MYCS',
 'LOC_TRAIT_MYCS_DESCRIPTION', 200);
```

> **原版新增 DLC 城邦（Babylon 加 6 个）并没有新增任何 `Parameters` 行** —— 只写 `CityStates` 就够了。
> 要覆盖多个规则集就在这张表里**按 Domain 各写一行**。

---

## 三、城邦完整注册链

### Gameplay 库（`InGameActions`）

| 步骤 | 表 | 关键点 |
|---|---|---|
| ① | `Types` | `KIND_CIVILIZATION` + `KIND_LEADER` + `KIND_TRAIT` |
| ② | `Civilizations` | ★ **`StartingCivilizationLevelType = 'CIVILIZATION_LEVEL_CITY_STATE'`**（合法值：`FULL_CIV` / `CITY_STATE` / `TRIBE` / `FREE_CITIES`） |
| ③ | `CivilizationLeaders` | `(CivilizationType, LeaderType, CapitalName)` |
| ④ | `CityNames` | 城邦名称池 |
| ⑤ | `Leaders` | ★ **`InheritFrom = 'LEADER_MINOR_CIV_<类别>'`** —— 见 §四 |
| ⑥ | `LeaderTraits` | 领袖 → 城邦 Trait |
| ⑦ | `Traits` | Trait 本体 + LOC |
| ⑧ | `TypeProperties` | ★ `(Type='CIVILIZATION_X', Name='CityStateCategory', Value='SCIENTIFIC')` —— 游戏内判定用；原版还带第 4 列 **`PropertyType='PROPERTYTYPE_IDENTITY'`** |
| ⑨ | `PlayerColors` | `Usage='Minor'` + 类别配色 |
| ⑩ | `TraitModifiers` → `Modifiers` → `ModifierArguments` | 宗主国加成，见 §四 |

> ⚠ **类别要写两处**：Configuration 库的 `CityStates.CityStateCategory`（选单徽章/筛选）与 Gameplay 库的 `TypeProperties(Name='CityStateCategory')`（游戏内判定）。两处不一致会出现"选单显示科学、游戏内当商业"。

### Configuration 库（`FrontEndActions`）

`CityStates`（§二）+ 前端 `Players` / `PlayerItems`（若该城邦要出现在前端列表）+ `Colors` 不需要（在 Gameplay 库）。

---

## 四、★ 两条最该抄的实证规律

### 4.1 宗主国加成：唯一标准写法（vanilla 与 mod 逐字同形）

```
TraitModifiers(TRAIT_<城邦>)
  → ModifierId: <城邦>_ATTACH_<效果>
     ModifierType = MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER
     SubjectRequirementSetId = 'PLAYER_IS_SUZERAIN'      ← 门槛只有这一条
       → ModifierArguments: Name='ModifierId', Value=<内层效果 ModifierId>
          → 内层效果 modifier 自带城市/地块条件
             （如 REQSET_CITY_HAS_CAMPUS / REQSET_PLOT_COAST_IMPROVEMENT）
```

**关键理解**：`PLAYER_IS_SUZERAIN` **不区分是哪个城邦** —— 它只判"我是某个城邦的宗主国"。
"是**这个**城邦的宗主国"靠 **Trait 归属**区分（`TraitModifiers` 挂在 `TRAIT_<该城邦>` 上，只有该城邦的 Trait 才会把效果发给玩家）。

vanilla 佐证：`MINOR_CIV_GENEVA_TRAIT` → `MINOR_CIV_GENEVA_UNIQUE_INFLUENCE_BONUS`（= `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER` + `PLAYER_IS_SUZERAIN`）→ 内层 `MINOR_CIV_GENEVA_SCIENCE_AT_PEACE_BONUS`。
`PLAYER_IS_SUZERAIN` 自身 = `TEST_ALL(REQUIRES_PLAYER_AT_PEACE, REQUIRES_PLAYER_IS_SUZERAIN, REQUIRES_PLAYER_IS_SUZERAIN_BONUS_ENABLED)`。

### 4.2 使者层级加成（1 / 3 / 6 使者）**不用自己写**

只要 `Leaders.InheritFrom` 指向正确的类别领袖，**使者层级加成自动继承**：

```sql
INSERT OR REPLACE INTO Leaders (LeaderType, Name, InheritFrom) VALUES
('LEADER_MYCS', 'LOC_LEADER_MYCS_NAME', 'LEADER_MINOR_CIV_SCIENTIFIC');
```

六选一：`LEADER_MINOR_CIV_SCIENTIFIC` / `_CULTURAL` / `_RELIGIOUS` / `_TRADE` / `_INDUSTRIAL` / `_MILITARISTIC`。

vanilla 机制：`LeaderTraits('LEADER_MINOR_CIV_SCIENTIFIC' → 'MINOR_CIV_SCIENTIFIC_TRAIT')`，该 trait 的 envoy 加成用 `SubjectRequirementSetId` = `PLAYER_HAS_SMALL_INFLUENCE` / `_MEDIUM_` / `_LARGE_`，其成员是 `REQUIREMENT_PLAYER_HAS_GIVEN_INFLUENCE_TOKENS` + `REQUIRES_PLAYER_AT_PEACE`。

> **这解释了"为什么类别必须选对"** —— 类别不是标签，是**行为继承链**。

---

## 五、进阶：跨城邦能力 / 自定义分组标签

"统计我拥有的本 mod 城邦数量""给所有本 mod 城邦加 buff"这类需求，**原版没有现成标签可用**（★ 实查：原版城邦领袖**完全没有** `TypeTags`，`Tag LIKE '%MINOR_CIV%'` 零命中）。自建：

```sql
INSERT OR REPLACE INTO Vocabularies (Vocabulary) VALUES ('MINOR_CIV_MYMOD_CLASS');
INSERT OR REPLACE INTO Tags (Tag, Vocabulary) VALUES ('CLASS_MYMOD_LEADERS', 'MINOR_CIV_MYMOD_CLASS');
INSERT OR REPLACE INTO TypeTags (Type, Tag) VALUES ('LEADER_MYCS', 'CLASS_MYMOD_LEADERS');
```
消费端用 `REQUIREMENT_PLAYER_LEADER_TAG_MATCHES`（`Name='Tag'`, `Value='CLASS_MYMOD_LEADERS'`）。

> ⚠ 这是**自创机制**，不是原版城邦写法。原版 `Tags` 表只用了 6 个 Vocabulary（`TAG_REQUIREMENT` / `TAG_MODIFIER` / `RESOURCE_CLASS` / `ABILITY_CLASS` / `FEATURE_CLASS` / `POWER_CONVERSION_CLASS`）。
> ⚠ 用它做"宗主国"门槛时要小心逻辑：宗主国玩家的领袖**不是**城邦领袖，`LEADER_TAG_MATCHES` 判的是**玩家自己的领袖**，不是他当宗主的城邦 —— 容易写出永不生效的条件。

---

## 六、素材

| 项 | 规格 |
|---|---|
| 图标尺寸 | ★ `22, 30, 32, 36, 40, 44, 48, 64, 68, 80, 256`（14 档，见 `art-pipeline.md` 尺寸表 `citystate_icon`） |
| 命名 | `ICON_CIVILIZATION_<X>_<size>.dds` + `IconTextureAtlases` + `IconDefinitions` |
| 注册 | `Icons.xlp`（`m_PackageName=UI/Icons`）+ `<Mod>.Art.xml` 的 `UITexture` 库 |
| 3D | 城邦一般**不需要**自定义 3D 模型（纯 2D 图标即可） |

---

## 七、验证清单

- [ ] `CityStates` 写进了 **FrontEndActions**（不是 InGameActions）
- [ ] `Civilizations` / `Leaders` 写进了 **InGameActions**
- [ ] `Civilizations.StartingCivilizationLevelType = 'CIVILIZATION_LEVEL_CITY_STATE'`
- [ ] `Leaders.InheritFrom` 指向正确的 `LEADER_MINOR_CIV_<类别>`
- [ ] 类别在 `CityStates.CityStateCategory` 与 `TypeProperties(Name='CityStateCategory')` **两处一致**
- [ ] `PlayerColors` 用 `Usage='Minor'`
- [ ] 宗主国加成走 `MODIFIER_ALL_PLAYERS_ATTACH_MODIFIER` + `PLAYER_IS_SUZERAIN`
- [ ] 若覆盖多个规则集，`CityStates` 按 `Domain` 各写一行
- [ ] **不要**从第三方 mod 抄 `Parameters` / `ParameterDependencies`，除非确认其 `ConfigurationId` 在本机原版里真实存在
- [ ] `<Content Include>` **与** Action 段两处都登记（见 `gotchas.md` §3）
- [ ] 跑 `rgn_validate`

---

## 八、踩过的坑

| 坑 | 症状 |
|---|---|
| 把 `CityStates` 写进 InGameActions | 城邦能玩但**不进选单**，且无报错 |
| `InheritFrom` 填 `LEADER_MINOR_CIV_*` 之外的值 | 使者层级加成全部丢失 |
| 照抄 CSE/YnAMP 的 `Parameters` 行 | 依赖一个本机不存在的 `ConfigurationId` → 死配置 |
| `TypeProperties` 漏写 / 类别与 `CityStates` 不一致 | 游戏内类别判定与选单不符 |
| 用 `LEADER_TAG_MATCHES` 做"我的城邦被 X 宗主"判定 | 判的是玩家自己的领袖 → 条件永不成立 |
| 只写 `<Content Include>` 不写 Action | 打包了但从不加载（`gotchas.md` §3） |
