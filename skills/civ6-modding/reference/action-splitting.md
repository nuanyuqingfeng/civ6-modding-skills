# 加载动作的划分与排序（LoadOrder / Priority）

> 本文是「一个文件该挂哪个动作」「什么时候要拆动作」「什么时候写 Priority」的**唯一权威依据**。
> 与 `project-setup.md` / `gotchas.md` 冲突时以本文为准，并回来修订那两处。

## 0. 一句话

**默认合并同类文件、默认不写 `Priority`。** 只有「强制拆分」4 类必须拆、「可选拆分」2 类才考虑拆。

---

## 1. 先分清两级排序（别混用）

| 层级 | 手段 | 作用范围 | 语义 |
|---|---|---|---|
| **动作级** | `<Properties><LoadOrder>N</LoadOrder></Properties>` | 整个动作**之间** | **数值小的先执行** |
| **文件级** | `<File Priority="N">` | **同一个动作内部**各 `<File>` | **数值大的先执行**（反直觉） |

两条必须记住的硬语义：

1. **`Priority` 数值越大越先执行。** 证据：官方 `Expansion2Core` 自注 `<!-- Schema comes first -->` 给 `Schema.sql` 用 `Priority="2"`、`<!-- Remove data second -->` 给 `RemoveData.xml` 用 `Priority="1"`，`Modding.log` 实测 Schema 先跑。
2. **同 `Priority`（含都省略）的 `<File>` 按路径字母序执行，不按声明序。** 证据：`Expansion2MajorContent` 声明 `…Units → UnitAbilities → UnitPromotions`，实测 `…UnitAbilities → UnitPromotions → Units`（严格字典序）。
   ⚠️ **声明顺序看起来正确却无效** —— 这是最容易踩的一条。依赖方若字母序在前，就会 `no such table`。

---

## 2. 强制拆分（无选择余地）

### 2.1 库归属决定容器：FrontEnd vs InGame

Civ6 有**两个独立数据库**：Config（FrontEnd 用）与 Gameplay（InGame 用）。同一张表可能只存在于一侧，也可能两侧都有 —— 后者**必须两端各注册一个动作**。

| 库 / 表 | FrontEnd | InGame | 漏注册的症状 |
|---|---|---|---|
| `Players` / `PlayerItems`（**Config 专属**） | ✅ 必须 | ❌ 不能有 | 放进 InGame → `no such table: Players` |
| `Civilizations` / `Leaders` / `Units` / `Buildings` 等（**Gameplay 专属**） | ❌ 不需要 | ✅ 必须 | 前端不需要 |
| `Colors` / `PlayerColors` | ✅ | ✅ | 选人界面有配色，**进游戏变默认色** |
| `IconTextureAtlases` | ✅ | ✅ | 选人界面有图标，**游戏内空白** |
| `LocalizedText` | ✅（Config 用的 LOC） | ✅（游戏内文本） | 前端缺 → mod 列表显示裸 key |
| 美术 `.dep`（`UpdateArt`） | ✅ | ✅ | 选人界面有立绘，游戏内不显示 |

**口诀**：*凡是「选人界面看得见、游戏里也看得见」的东西，两端都要注册* —— 即 **Colors / Icons / Text / Art**。
**实测反例**：`FHB_Shuai` 漏了 InGame `UpdateColors` → 进游戏后玩家颜色不对（静默失效，不报错）。

> **注意「双端」有两种形态，别搞混**：
> - **同一文件列两次**：Icons / Colors / Text / Art 这类**内容相同、两端都要**的 → 同一个文件被两个动作各列一次（分属 `<FrontEndActions>` 与 `<InGameActions>`）。
>   本项目实测即此形态：`Icons_Anomaly_Mode.xml` 同时出现在 FrontEnd `Icons` 与 InGame `Icons` 动作里。
> - **两个不同文件**：SQL 类往往内容不同（Config 侧写 `Players/PlayerItems`，Gameplay 侧写 `Civilizations/Leaders`）→ **各写一个文件、各挂一个动作**。
> 两种形态的共同点是：**动作必须有两个，且分属两个容器**。

### 2.2 `criteria` 不一致

`criteria` 是**动作元素上的属性**（`.modinfo`）或**子元素**（`.civ6proj`），**一个动作只能绑一个 criteria** → 加载条件不同的内容**结构上无法共处一个动作**，必须拆。

官方实证：`criteria` 属性在 42 个 modinfo 中出现 **501 处**、去重 **145 个**不同值；`Australia.modinfo` 的 `AustraliaGameplay`(criteria=`Australia`) / `_XP1`(`Australia_Expansion1`) / `_XP2`(`Australia_Expansion2`) 必须三分。

---

## 3. 可选拆分（仅 2 类，其余一律合并）

### 3.1 惯例：Types 定义 与 遍历/Modifier 逻辑 分开

| 类别 | 内容 | 归处 |
|---|---|---|
| **类型定义** | `Types` / `Buildings` / `Units` / `Civilizations` / `Districts` / `Leaders` / `Projects` / `Resources` / `Improvements` / `GreatPeople` / `GreatWorks` / `Beliefs` / `Governors` … | **一个动作（早加载）** |
| **遍历 / Modifier 逻辑** | `Modifiers` / `ModifierArguments` / `TraitModifiers` / `BuildingModifiers` / `DynamicModifiers` … | **另一个动作（晚加载）** |

用 `LoadOrder` 表达先后（如 `-1`/`200` → `600005`），或同动作内用 `Priority` 定序。

#### ★ 为什么要这样分（三条理由，缺一不可）

1. **Types 先加载，才能被其他逻辑遍历到。** 遍历/Modifier 逻辑通常要在 `Types`（及依赖它的表）里查找目标 —— 若 Types 后到，遍历时目标还不存在，只能得到空集。
2. **遍历逻辑延迟加载，才能遍历到其他 mod 可能有的部分。** 遍历是**全库扫描**语义：越晚执行，越能覆盖到其他 mod（尤其是不规范、加载较晚的 mod）已经写入的行。过早遍历 = 只看到自己与少数先到的内容。
3. **对环境影响小，不易被不规范的遍历污染。** 遍历会把**全库已有行**一起纳入处理；若自己的遍历跑得太早，可能把后续 mod 写入的、语义上不该被自己处理的行也卷进来（或反过来被对方的遍历波及）。把遍历层推后，等于把自己隔离在「上游已定型」之后，是**风险最小**的位置。

**实证**（本机 4 个成熟工程高度一致）：

| 工程 | Types 动作 | 遍历/Modifiers 动作 |
|---|---|---|
| `示例工程` | `RGN_Types` LO=200（**17 文件**） | `RGN_Modifiers` LO=600005（**8 文件**） |
| `工程 I` | `Data_Define` LO=-1 | `Data_Modifiers` LO=999999 |
| `工程 C` | `Jinhsi_Data` LO=-1（12 文件） | `Jinhsi_Modifiers` LO=600000 |
| `工程 A` | `BS_Data` LO=200（10 文件） | `BS_Modifier` LO=600003（4 文件） |

> **来源须注明**：官方 42 个 .modinfo **0 例**这样做，反而 **70 个动作把二者合在一起**（铁证：`Expansion2_Units_Major.xml` **同一文件内** `<Types>`:4-17 + `<Modifiers>`:143）。
> 即它是**成熟第三方工程惯例**，不是官方模式。**本项目采用它**（理由见上三条），但不要对外称「官方要求」。

### 3.2 可读性：文件极多时

**阈值建议 ≥50 个文件**才考虑拆分。

官方先例说明引擎与工具链**完全能承受大动作**，故阈值不该定低：

| 动作 | 文件数 |
|---|---|
| `Expansion2_Files`（ImportFiles） | **192** |
| `Expansion2CoreContent` | **87** |
| `Expansion1_CoreContent` | **44** |
| `VikingsScenario` `VIKING_COMPONENT` | 28 |

---

## 4. `Priority` 使用纪律

**默认不写。** 只在以下两种情况写：

| # | 条件 |
|---|---|
| ① | **明确需要先后加载**（已知依赖，且**不打算**为它拆动作） |
| ② | **SQL 报错指向加载顺序问题**（`no such table: X` / 外键失败） |

**官方实证支持「按需才用」**：官方 **32 个合并动作完全不用 `Priority`**（含 87 文件的 `Expansion2CoreContent`）；而 **35 个含 RemoveData 的合并动作 100% 都给它加了 `Priority`**（0 例外）—— 即它是**按「确知有依赖」才用**的精准手段，不是常规装饰。

> ⚠️ 反面教材：`VikingsScenario`/`VIKING_COMPONENT` 合并 28 文件，`RemoveData` 按字母序会掉到**第 21 位**（`R` 靠后），全靠 `Priority="1"` 提到最前 —— **不留心就会静默出错**。

---

## 5. 官方实际使用的划分轴（7 条，穷尽清单）

> 来源：42 个官方 .modinfo 全量解析（163 个 `UpdateDatabase` 动作）。**这 7 条就是「官方为什么拆」的完整答案**，超出这 7 条的原因官方一次也没用过。

| # | 划分轴 | 证据 |
|---|---|---|
| 1 | **Schema / RemoveData / 内容 三层** | `Expansion2Core`(LO=-100) 内 `Schema(P2)`→`RemoveData(P1)`；内容动作无 LoadOrder |
| 2 | **criteria 维度** | 属性 501 处、去重 145 个值 |
| 3 | **action 类型** | Database / Icons / Colors / Text / Art / Audio / ImportFiles / UI… |
| 4 | **InGame vs FrontEnd 容器** | `Babylon.modinfo` InGame :110-243 / FrontEnd :245-268 |
| 5 | **XP1 / XP2 来源** | `Expansion2CoreContent` 内 `:43 <!-- XP1 -->` / `:88 <!-- XP2 -->` |
| 6 | **`_Major` 替换型 vs 新增型** | `Expansion2MajorContent` 9 文件全 `_Major`，criteria=`Expansion2AndBeyond` |
| 7 | **可读性** | `Expansion2_Files` **192** 文件、`Expansion2CoreContent` **87** 文件 |

> **官方 `LoadOrder` 极其罕见**：全 42 文件**仅 17 处**，取值只有 `-100`（2 次，schema 优先）与 `100`（15 次，场景依赖外部 DLC 的 `<Include>`）。**679/696 个动作没有 LoadOrder。**
> 网上流传的 `-75` / `-50` / `50` 等「官方阶梯」**官方并不存在**，属社区/第三方约定（见 `gotchas.md` §44 的观测表）。

---

## 6. 决策树

```
一个（或一组）文件要注册
│
├─ 该表只存在于 Config 库？ ──────── 是 → FrontEndActions 动作
├─ 该表只存在于 Gameplay 库？ ────── 是 → InGameActions 动作
├─ 该表两侧都有（Colors/Icons/Text/Art）？
│        └─ 是 → ★ 两端各注册一个动作（漏一端 = 静默失效）
│
├─ 已有动作的 criteria 与本文件不同？ ─ 是 → ★ 必须新建动作（一个动作只能一个 criteria）
│
├─ 是「Types 定义」还是「遍历/Modifier 逻辑」？
│        ├─ Types ────→ 放进 Types 动作（LoadOrder 早，如 -1/200）
│        └─ 遍历 ─────→ 放进 Modifiers 动作（LoadOrder 晚，如 600005）
│
├─ 拟放入的动作已有 ≥50 个文件？ ─── 是 → 可考虑拆（官方有 192 先例，不急）
│
└─ 否则 ──────────────────────────── 合并进同类动作，**不写 Priority**

然后：只有当「明确有先后依赖」或「SQL 报错指向顺序」时，才回头给文件加 Priority。
```

---

## 7. 正反实证速查

**✅ 合并 + 不写 Priority（官方主流）**
- `Expansion2CoreContent`：87 文件一个动作，0 个 Priority
- `BabylonGameplay`：8 文件（含 `_Civilizations` / `_Leaders` / `_Modifiers` / `_Units` …）一个动作，0 个 Priority
- `Expansion1_CoreContent`：44 文件一个动作，0 个 Priority

**✅ 同动作 + Priority 定序（有明确依赖时）**
- 官方 `Byzantium_Gaul` `DramaticAges_Gameplay_XP1`：4 文件用 `Priority="3"/"2"/"1"/"0"` 排 `RemoveData → GameCapabilities → MODE → XP1_MODE`
- 官方 `Expansion2Core`：`Priority="2"` Schema → `Priority="1"` RemoveData
- 本项目 `Anomaly_Database`：3 个 SQL 用 `Priority="3"/"2"/"1"`

**✅ 因 criteria 拆动作**
- 官方 `AustraliaGameplay` / `_XP1` / `_XP2`（三个 criteria）
- 本项目：FrontEnd 侧 `Icons`/`Text`/`Art` **无 criteria**（选人界面无条件可用），InGame 侧同名动作 **带 `criteria=Amomaly_Mode`**（只在模式启用时加载）→ 同一份内容因 criteria 不同而**必须分属两个动作**，且正好也符合「双端注册」要求（见下）

**✅ 双端注册（Colors / Icons / Text / Art）**
- 本项目实测：`UpdateIcons` / `UpdateText` / `UpdateArt` 均 **FrontEnd 1 个 + InGame 1 个 = 双侧齐备**；
  且 FrontEnd 侧**不带 criteria**、InGame 侧**带 `Amomaly_Mode`** —— 这是正确形态：前端无条件、游戏内按模式门控。

**❌ 反例（不要这样做）**
- 依赖 `RemoveData` 先跑却不写 `Priority` → 字母序把 `R` 排到后面（`VIKING_COMPONENT` 若不加会掉到第 21/28 位）
- 只注册 InGame `UpdateColors`，漏 FrontEnd → 选人界面无配色（静默）
- 把 Config 专属表（`Players`）写进 InGameActions → `no such table: Players`
