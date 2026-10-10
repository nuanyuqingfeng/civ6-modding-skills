# 总督编写（Governor Authoring）

> 来源：3 个独立总督工程（工程 F / 工程 G / 工程 H）+ 2 个含总督的文明包（示例工程 / 工程 A）横向审查，
> 所有 schema 结论均已用 skill 自带 `database/DebugGameplay.sqlite` 复核（标 ★）。
> 美术侧规格见 **`civ6-asset-forge`** skill 的 `reference/governor-art.md`；本文只管**玩法注册链**。

---

## 一、引擎侧共 10 张总督表（★ PRAGMA 实查）

| 表 | 作用 | vanilla 用量 |
|---|---|---|
| `Governors` | 主体定义 | 12 行 |
| `Governors_XP2` | `AssignToMajor` | **仅 1 行**（`GOVERNOR_IBRAHIM`） |
| `GovernorPromotions` | 晋升定义（网格坐标） | — |
| `GovernorPromotionSets` | 总督 → 晋升 的归属 | — |
| `GovernorPromotionPrereqs` | 晋升前置图（多行 = AND） | — |
| `GovernorPromotionModifiers` | 晋升 → Modifier | **主力表** |
| `GovernorModifiers` | 总督 → Modifier（"基础能力位"） | ★ **0 行** |
| `GovernorPromotionConditions` | `EarliestGameEra` / `HiddenWithoutPrereqs` | 仅秘密结社总督 |
| `GovernorReplaces` | 总督取代关系 | 0 行 |
| `GovernorsCannotAssign` | 禁止派驻 | ★ **4 行**（4 个秘密结社总督，`CannotAssign=1`） |

> ⚠ **`GovernorModifiers` 在 vanilla 里一行都没有** —— 说明"用 `GovernorModifiers` 挂总督基础能力"这条路**没有被官方数据验证过**。
> 基础能力请走 `GovernorPromotions` 里 `BaseAbility=1` 的那一格 → `GovernorPromotionModifiers`（vanilla 12 个总督全部如此）。

---

## 二、从 0 到可玩：完整步骤

### ① `Types` —— 注册主体

```sql
INSERT OR REPLACE INTO Types (Type, Kind) VALUES
('GOVERNOR_MYMOD',              'KIND_GOVERNOR'),
('GOV_PROMO_MYMOD_1',           'KIND_GOVERNOR_PROMOTION'),
('GOV_PROMO_MYMOD_2',           'KIND_GOVERNOR_PROMOTION'),
-- …每个晋升一行
;
```
> 漏注册 → 加载时报 `Invalid Reference on Governors.GovernorType` / FOREIGN KEY 失败。

### ② `Governors` —— 12 列，**11 个 NOT NULL、唯一可空列是 `TraitType`**（★）

| 列 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `GovernorType` | TEXT | ✅ PK | 主体 Type |
| `Name` / `Title` / `ShortTitle` / `Description` | LOCALIZEDTEXT | ✅ | 4 个 LOC tag |
| `IdentityPressure` | INTEGER | ✅ default 0 | vanilla 全 8（结社总督 10） |
| `TransitionStrength` | INTEGER | ✅ default 0 | **就职回合**，见下 |
| `AssignCityState` | BOOLEAN | ✅ default 0 | |
| `Image` | TEXT | ✅ default `NO_IMAGE` | **纹理名**（非 atlas 名），引擎找 `ICON_<Image>` |
| `PortraitImage` / `PortraitImageSelected` | TEXT | ✅ | **裸纹理名**（走 UITexture XLP，不走 artdef / 不走 IconTextureAtlases） |
| **`TraitType`** | TEXT | ❌ **可空** | **通用 / 专属开关** —— 见 §三 |

```sql
INSERT OR REPLACE INTO Governors (
  GovernorType, Image, Name, IdentityPressure, Title, ShortTitle, Description,
  TransitionStrength, PortraitImage, PortraitImageSelected, TraitType
) VALUES (
  'GOVERNOR_MYMOD', 'GOVERNOR_MYMOD',
  'LOC_GOVERNOR_MYMOD_NAME', 8,
  'LOC_GOVERNOR_MYMOD_TITLE', 'LOC_GOVERNOR_MYMOD_SHORT_TITLE',
  'LOC_GOVERNOR_MYMOD_DESCRIPTION', 150,
  'PORTRAIT_IMAGE_GOVERNOR_MYMOD', 'GovernorSelected_IMAGE_MYMOD',
  NULL   -- NULL = 所有文明可用；填 TraitType = 仅该特性拥有者可用
);
```

**`TransitionStrength` → 就职回合**（工程注释来源，vanilla 旁证）：

| 值 | 就职回合 | vanilla 旁证 |
|---|---|---|
| 100 | 5 | Amani / Cardinal / Builder / Educator / Merchant / Resource Manager |
| 150 | 3 | **Victor**（THE_DEFENDER）、Ibrahim |
| 200 | 2 | — |
| 400 | 1 | — |
| 600 | 0（即刻） | — |

> 数值表本身来自工程注释（`工程 G.xml`），**未独立实测**；100/150 两个档位有 vanilla 实值支撑。

### ③ `GovernorPromotionSets` —— 归属

```sql
INSERT OR REPLACE INTO GovernorPromotionSets (GovernorType, GovernorPromotion) VALUES
('GOVERNOR_MYMOD', 'GOV_PROMO_MYMOD_1'),
('GOVERNOR_MYMOD', 'GOV_PROMO_MYMOD_2');
```

### ④ `GovernorPromotions` —— 网格坐标（**6 列，没有 Icon 列**）

```sql
INSERT OR REPLACE INTO GovernorPromotions
  (GovernorPromotionType, Name, Description, Level, Column, BaseAbility) VALUES
('GOV_PROMO_MYMOD_1', 'LOC_GOV_PROMO_MYMOD_1_NAME', 'LOC_GOV_PROMO_MYMOD_1_DESC', 0, 1, 1), -- 基础能力
('GOV_PROMO_MYMOD_2', 'LOC_GOV_PROMO_MYMOD_2_NAME', 'LOC_GOV_PROMO_MYMOD_2_DESC', 1, 0, 0),
('GOV_PROMO_MYMOD_3', 'LOC_GOV_PROMO_MYMOD_3_NAME', 'LOC_GOV_PROMO_MYMOD_3_DESC', 1, 2, 0);
```

> ★ **`BaseAbility=1` 恒在 `Level=0, Column=1`** —— vanilla 12 个总督**全体一致**（已逐条查询确认）。
> 网格是 `Level`（行，0 起）× `Column`（列，0/1/2）的 3 列布局；官方晋升树都是"底部一格起手，向上一分为二、再合流"。

### ⑤ `GovernorPromotionPrereqs` —— 前置图

```sql
INSERT OR REPLACE INTO GovernorPromotionPrereqs (GovernorPromotionType, PrereqGovernorPromotion) VALUES
('GOV_PROMO_MYMOD_2', 'GOV_PROMO_MYMOD_1'),
('GOV_PROMO_MYMOD_3', 'GOV_PROMO_MYMOD_1'),
('GOV_PROMO_MYMOD_4', 'GOV_PROMO_MYMOD_2'),
('GOV_PROMO_MYMOD_4', 'GOV_PROMO_MYMOD_3');   -- 两条前置 = 同时满足（合流）
```

> **顶层晋升如果要"串行"、不要"分叉"**，检查 `Column` 是否真的对齐了 —— 列位与前置不匹配会导致晋升树在 UI 上连线错乱（工程里修过一次：`fix(Governor): 修正晋升树列位与顶层前置`）。

### ⑥ `GovernorPromotionModifiers` —— 挂效果

```sql
INSERT OR REPLACE INTO GovernorPromotionModifiers (GovernorPromotionType, ModifierId) VALUES
('GOV_PROMO_MYMOD_1', 'MYMOD_PROMO_1_EFFECT');

INSERT OR REPLACE INTO Modifiers (ModifierId, ModifierType, SubjectRequirementSetId) VALUES
('MYMOD_PROMO_1_EFFECT', 'MODIFIER_SINGLE_CITY_ADJUST_CITY_YIELD_CHANGE', NULL);

INSERT OR REPLACE INTO ModifierArguments (ModifierId, Name, Value) VALUES
('MYMOD_PROMO_1_EFFECT', 'YieldType', 'YIELD_SCIENCE'),
('MYMOD_PROMO_1_EFFECT', 'Amount', 5);
```

### ⑦ 可选：用时代门控晋升（`GovernorPromotionConditions`）

官方只用它做**秘密结社总督**的时代解锁，但机制对任何总督可用：

```sql
INSERT OR REPLACE INTO GovernorPromotionConditions
  (GovernorPromotionType, HiddenWithoutPrereqs, EarliestGameEra) VALUES
('GOV_PROMO_MYMOD_3', 1, 'ERA_MEDIEVAL'),   -- 前置未满时隐藏；中世纪起可用
('GOV_PROMO_MYMOD_5', 1, 'ERA_INDUSTRIAL');
```
> ★ 表结构 3 列；vanilla 16 行全部是 `OWLS_OF_MINERVA` / `HERMETIC_ORDER` / `VOIDSINGERS` / `SANGUINE_PACT` 四家结社总督，档位固定 `ERA_MEDIEVAL` / `ERA_INDUSTRIAL` / `ERA_ATOMIC`。

### ⑧ 可选：`Governors_XP2.AssignToMajor`

```sql
INSERT OR REPLACE INTO Governors_XP2 (GovernorType, AssignToMajor) VALUES ('GOVERNOR_MYMOD', 1);
```
> ★ vanilla 只有 `GOVERNOR_IBRAHIM` = 1。语义未充分实测，保守做法是**不写**（走默认）。

### ⑨ 文本

固定 4 个总督 tag + 每晋升 2 个：

```
LOC_GOVERNOR_<X>_NAME / _TITLE / _SHORT_TITLE / _DESCRIPTION
LOC_GOV_PROMO_<X>_NAME / _DESCRIPTION      ← 每晋升一组
```

**可选但极易漏**：百科章节（"注册链完整但百科空白"的典型漏项）
```
LOC_PEDIA_GOVERNORS_PAGE_<GovernorType|PromotionType>_CHAPTER_HISTORY_PARA_<n>
```

### ⑩ 图标与立绘

| 素材 | 注册位置 |
|---|---|
| `Image`（32 / 64 头像） | `IconTextureAtlases`（atlas 名 = `ICON_<Image>`）+ `IconDefinitions` |
| 晋升 24px 徽章 | atlas（官方 `XP1_GovernorPromotions24` / `XP2_GovernorPromotions24` 同构） |
| `PortraitImage` / `PortraitImageSelected` | **裸纹理名**：`XLPs/Icons.xlp`（`m_ClassName=UITexture` + `m_PackageName=UI/Icons`）→ `<Mod>.Art.xml` 的 `gameLibraries/UITexture/relativePackagePaths = UI/Icons` |
| 图集文件 | `Textures/<Filename>_{22,32,38,50,80,128,256}.dds/.tex` |

> ★ 实测 62 个总督相关 `.tex` **全为 `PF_R8G8B8A8_UNORM` + `bUseMips=false`**、`m_ClassName`/`m_Tags = UserInterface`。
> ⚠ 立绘**不是固定画布**：三工程实测 `PortraitImage` 有 200×208 / 208×208 / 206×208，`Selected` 有 325×339 / 339×331 / 325×339。
> `civ6-asset-forge` 的 `reference/governor-art.md` 里的 206×208 / 326×339 应视为**推荐值，不属于硬规格**。

### ⑪ `.civ6proj` 注册

`UpdateDatabase` 动作 + `<Content Include>` **两处都要写**（见 `gotchas.md` §3 的「打包 vs 加载」两轴）。
**推荐 `LoadOrder = -1`**：实测 4 个独立总督工程 + 示例工程 全部把总督数据放在 `-1`（或 `-2`）—— 总督数据被其他内容引用，需早于常规内容（`200`）加载。

### ⑫ 名额扩容（**必须做，且必须用增量**）

```sql
UPDATE GlobalParameters SET Value = Value + 3 WHERE Name = 'MAX_GOVERNOR_APPOINTMENTS';
```
> ⚠ **绝不要写 `SET Value = <绝对值>`** —— 会覆盖其他 mod 的调整。
> 实测：示例工程 `+10`、工程 A `+3`，两工程独立收敛到同一写法。

---

## 三、`Governors.TraitType` —— 通用 / 专属开关（★ 已复核）

| 写法 | 语义 | 实例 |
|---|---|---|
| `TraitType = NULL` | **通用总督**，所有文明可用（独立总督包的标准做法） | vanilla 除 Ibrahim 外全部 |
| `TraitType = 'TRAIT_X'` | **专属总督**，仅拥有该特性的玩家可任用 | ★ vanilla `GOVERNOR_IBRAHIM` → `TRAIT_LEADER_SULEIMAN_GOVERNOR` |

- 独立总督 mod：该列**注释掉**或填 `NULL`；
- 文明包内嵌总督：填本文明的领袖/文明 Trait；
- 想让**另一个领袖**也能用这个总督：不要去改 `Governors`，而是补 `LeaderTraits`
  ```sql
  INSERT OR REPLACE INTO LeaderTraits (LeaderType, TraitType) VALUES ('LEADER_OTHER', 'TRAIT_X');
  ```

---

## 四、作用域与条件（★ 实查）

**集合**：`COLLECTION_PLAYER_GOVERNORS` 是**唯一**的总督作用域集合（`DynamicModifiers` 的 44 个 `COLLECTION_*` 中）。
自建总督级 ModifierType 时：

```sql
INSERT OR REPLACE INTO DynamicModifiers (ModifierType, CollectionType, EffectType) VALUES
('MODIFIER_MYMOD_PLAYER_GOVERNORS_ADJUST_X', 'COLLECTION_PLAYER_GOVERNORS', 'EFFECT_…');
```

**RequirementType**：全库只有 3 个总督相关条件 ★

| RequirementType | 参数 | 用途 |
|---|---|---|
| `REQUIREMENT_CITY_HAS_GOVERNOR` | `Established=1` | "有总督就任的城市"（**不是**"已指派"） |
| `REQUIREMENT_CITY_HAS_GOVERNOR_WITH_X_TITLES` | — | 按头衔数 |
| `REQUIREMENT_CITY_HAS_SPECIFIC_GOVERNOR_PROMOTION_TYPE` | — | 是否有某晋升 |

- "总督所在城市"另一写法：`REQSET_PLOT_ADJACENT_OWNER` + `MinimumCount = MaximumCount = 0`（周边无他人地块）。
- 相关 ModifierType 常用：`MODIFIER_PLAYER_ADJUST_GOVERNOR_POINTS` / `MODIFIER_ALL_PLAYERS_ADJUST_GOVERNOR_POINTS` / `MODIFIER_PLAYER_GOVERNORS_ADJUST_IDENTITY_PER_TITLE` / `MODIFIER_PLAYER_CITIES_ADJUST_CITY_YIELD_MODIFIER_PER_GOVERNOR_TITLE`。

**事件**（`eventSystem=Events`，★ 已与 `events_enhanced.json` 核对）：

| 事件 | 签名 |
|---|---|
| `GovernorEstablished` | `(cityOwner, cityID, governorOwner, governorType)` |
| `GovernorPromoted` | `(playerID, governor, promotion)` —— 注意给的是 **Index** |
| `GovernorAssigned` | `(playerID, governor, cityID)` |

> ⚠ **事件给 Index，取实例要 `GetGovernor(Hash)`** —— 两端口径不同，直接拿 Index 当 hash 用会取不到。

---

## 五、引擎拼写错误：**仅当在原版数据里实证是官方笔误时才照抄**

**判定标准（硬性）**：该字符串必须能在**原版数据**（`DebugGameplay.sqlite` 等官方快照，或游戏本体的 `Base/` `DLC/` 文件）里查到，且同族字符串拼写正确 → 才能认定为"引擎官方拼写错误"，必须**逐字照抄**。
**工程/第三方 mod 里的拼写错误不要跟着抄**，那是缺陷不是约定。

★ 已实证的两例（均出自官方数据快照，且互相印证同族写法正确）：

| 错误串 | 出现在 | 同族正确写法（对照证据） |
|---|---|---|
| `MODIFIER_GOVERNOR_ADJUST_PREVENET_STRUCTURAL_DAMAGE` | `Modifiers` 的 **ModifierType** | 其 `DynamicModifiers.EffectType` = `EFFECT_ADJUST_PREVENT_STRUCTURAL_DAMAGE`（拼写正确） |
| `EFFECT_GOVERNOR_ADJUST_IDENITITY_PER_TITLE` | `DynamicModifiers` 的 **EffectType** | 其 `ModifierType` = `MODIFIER_PLAYER_GOVERNORS_ADJUST_IDENTITY_PER_TITLE`（拼写正确） |

> 这两条正好是**镜像的一对**：一条错在 ModifierType、一条错在 EffectType。用 `SELECT * FROM DynamicModifiers WHERE EffectType LIKE '%IDENITIT%' OR ModifierType LIKE '%PREVENET%'` 可随时复核。
> 自查命令：`SELECT ModifierType, CollectionType, EffectType FROM DynamicModifiers WHERE ModifierType LIKE '%PREVENET%' OR EffectType LIKE '%IDENITITY%';`

---

## 六、跨 mod 兼容

- **软依赖探测**：`WHERE EXISTS (SELECT 1 FROM RequirementSets WHERE RequirementSetId='…')` 或 `WHERE EXISTS (SELECT 1 FROM Leaders WHERE LeaderType='…')` —— 比多开一个 `<Criteria>` 动作组更轻，适合几十行的小补丁。
- **Lua 侧判"某 mod 是否在场"**：遍历 `GameInfo.Leaders()`（`Criteria` 是加载期静态判据，Lua 里读不到）。
- 两个 mod 同时给同一文明加总督时，用 `<ModInUse inverse="1">` 互斥，见 `project-setup.md`「`ModInUse` 三态」。

---

## 七、验证清单

- [ ] `Types` 里 `KIND_GOVERNOR` + 每个 `KIND_GOVERNOR_PROMOTION` 都注册了
- [ ] `Governors` 11 个 NOT NULL 列全部有值（**只有 `TraitType` 可空**）
- [ ] `BaseAbility=1` 的行在 `Level=0, Column=1`，且**只有一个**
- [ ] 每个晋升都在 `GovernorPromotionSets` 里挂了归属
- [ ] 前置图无环、顶层合流处前置齐全
- [ ] `MAX_GOVERNOR_APPOINTMENTS` 用 **`Value = Value + N`** 增量
- [ ] 4 个总督 LOC + 每晋升 2 个 LOC 全部存在（漏了显示裸 tag）
- [ ] `Image` / `PortraitImage` / `PortraitImageSelected` 指向的纹理真的在 `Icons.xlp` 里
- [ ] 若装了百科：`LOC_PEDIA_GOVERNORS_PAGE_*` 章节齐全
- [ ] `.civ6proj` 的 `<Content Include>` **与** Action 段**两处都登记**了 SQL 文件
- [ ] 跑 `rgn_validate` 确认无悬空引用

---

## 八、踩过的坑

| 坑 | 症状 | 处置 |
|---|---|---|
| 立绘 `PortraitImage` 当 atlas 用 | 立绘空白、无报错 | 它是**裸纹理名**，必须进 `XLPs/Icons.xlp` + `Art.xml` 的 `UI/Icons` 包 |
| 图标引用错误 | **AssetEditor 闪退** | 见 `civ6-art-reference` 的 pantry 注意事项 |
| `TransitionStrength` 写 0 | 立刻就职（可能不是想要的） | 先按上表换算 |
| 用绝对值 `SET MAX_GOVERNOR_APPOINTMENTS` | 与其他 mod 互相覆盖 | 一律用增量 |
| 顶层晋升只写一条前置 | 晋升树连线错乱 / 无法解锁 | 合流格必须把两条前置都写进 `GovernorPromotionPrereqs` |
| 只写 `<Content Include>` 不写 Action | 文件打进了包但**从不执行**，无报错 | 见 `gotchas.md` §3 |
| `GovernorPromotions` 加 `Icon` 列 | 插入报错 | 该表**没有** Icon 列，图标靠命名约定 `ICON_<PromotionType>` |
| 手动附加能力（Lua） | 条件不生效 | `GRANT_ABILITY` 的 SubjectReqSet 是唯一门槛，Ability 内部 modifier 不要再设条件（`gotchas.md` §31） |
