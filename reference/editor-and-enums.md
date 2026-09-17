← 返回 `SKILL.md` 路由

> **来源**：2026-09-17 由《Civ6 Modding Textbook》12 章 + 190 张配图（全部本地 OCR）
> 逆向整理，凡涉字段名/枚举/路径者均**对照本机真实文件或游戏数据复核**。
> 用途：本 skill 的**速查附件**——`art-pipeline.md` 讲"怎么做"，本文件讲"界面上那些
> 字段叫什么、取值有哪些、日志怎么写"。

# 速查：Asset Editor 字段 / 调试 / 枚举

## 一、Asset Editor 字段名速查

AE（`Launch Asset Editor...`）的字段名与官方文档一样零散，教程正文只讲流程，
**字段名只在截图里**。下表由 190 张截图 OCR 提取，并标注可信度。

### 1.1 XLP 编辑器（新建/打开 `.xlp`）

| 界面标签 | 说明 |
|---|---|
| `Module Name` | XLP 类（如 `UITexture`）——**等同 XML 里的 `<m_ClassName>`** |
| `Package Name` | 包名（如 `UI/Icons`、`UILeaders`、`LeaderFallbacks`） |
| `XLP Class` | 有的版本写作 `XLP Class`（与 `Module Name` 同一处，OCR 两版都有） |
| `Entries` | 条目列表区 |
| `Search` | 条目搜索框 |
| `Entry ID` | 条目名列 |
| `Hotload Targets` | 底部状态页签（热重载目标） |

> 顶部路径栏会显示 `... .xlp(Feline_JasperKitty)`；打开官方包时显示
> `...\Civ6\pantry\XLPs\Icons.xlp(Civ6)(Read Only)` —— **只读**标记很关键：
> 官方 pantry 只能看不能改。

### 1.2 `Mini Importer`（导入素材对话框）

| 界面标签 | 说明 |
|---|---|
| `Mini Importer` | 对话框标题 |
| `Entity Type:` | 实体类型（导入贴图时 = `Texture`） |
| `Entity Name:` | **实体名 = 未来的 `.tex` 名 / XLP 条目名**（技术名） |
| `Entity Class` | 导出类（对应 `.tex` 的 `m_ClassName`） |
| `Sort` | 按名排序 |
| `Select/Deselect` | 全选/反选 |
| `Overwrite ...` | 覆盖已有（OCR 残缺，教程截图里有 `Overwrite All` 之类） |

> **实测印证**：导入后条目列表里出现的是 `Feline128` / `Feline22` / `Feline256` /
> `Feline30` / `Feline32` / `Feline36` / `Feline44` / `Feline45` / `Feline48` … ——
> 即**每个尺寸档一个独立贴图条目**，与 `art-pipeline.md` 第三节的尺寸表一致。

### 1.3 Art.xml 编辑器（`Open an existing art specification document`）

| 界面标签 | 说明 |
|---|---|
| `Consumers` | 素材用户（art consumer）列表 |
| `Libraries` | 素材库列表 |
| `Dependencies` | 依赖列表 |
| `ArtDefs` + `Add...` | 给当前 consumer 添加 artdef（按钮因 bug 文字看不清，实为 `Add...`） |
| `Template:` | 新建 artdef 时的模板下拉 |

> 改动 Art.xml 后会弹：**`Please restart the AssetEditor for your Art.xml changes to
> take effect`**（必须重启 AE，改的才生效）。

### 1.4 ArtDef 模板下拉（可见模板名）

新建 ArtDef 时的模板列表（OCR 可见部分，非全集）：
`Civilizations` / `Cultures` / `Buildings` / `Landmarks` / `Units` / `Leaders` /
`LeaderFallback` / `Overlay` / `StrategicView` / `Improvements` / `Resources` /
`Districts` / `Clutter` / `Unit_Bins` / `Routes` / `Features` / `GameLighting` /
`FOWConfig` / `Eras` / `Appeal` / `DynamicGeometry` / `GamePropertyRanges` /
`GoodyHuts` / `GraphicsTweaks` / `LodSettings` / `Minimap` / `ScriptedSelector` /
`CityGenerators` / `CityBuildings` / `SplineBorder` / `UnitMovementTypes` /
`UnitFormationTypes`

### 1.5 Material / Asset 编辑器

| 界面标签 | 说明 |
|---|---|
| `Class Name` | 材质类（如 `UILensMaterial`）/ 资产类（如 `UILensAsset`） |
| `GeometrySet` / `Primitive` / `Mesh` | 几何（`HexModelGeo` 用于 Overlay、`PipModelGeo` 用于 Pressure） |
| `Add New...` / `Add Existing...` | 新增/引用已有（**做过一次就用 Add Existing**） |
| `Reimport` / `Open` / `Remove` | 贴图槽右侧操作按钮 |

---

## 二、调试三板斧

### 2.1 `Database.log` —— 查数据库错误（最常用）

**路径**：
```
%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs\Database.log
```
（实测该目录存在，同目录还有 `Lua.log`、若干 `*.csv` 统计导出）

**典型错误行**（教程给的真实样例）：
```
[3887972.302] [Gameplay] ERROR: UNIQUE constraint failed: Requirements.RequirementId
```

**三类约束错误**：

| 错误 | 含义 | 常见成因 |
|---|---|---|
| `UNIQUE constraint failed: <表>.<列>` | 唯一键重复 | 同一条 id 写了两次（含跨文件） |
| `FOREIGN KEY constraint failed` | 引用了不存在的行 | 悬空引用（Type/ModifierId 没定义） |
| `NOT NULL constraint failed` | 必填列为空 | 漏写列 |

**两条硬性纪律**：

1. **从第一条错误开始看**。教程原文：
   > 「由于前述的读取机制，一个错误可能会导致出错文件的后续内容不再被读取，
   > 进而在其它文件中因为数据缺失而触发更多雪崩式的错误。
   > **如果盯着后面的错误不放，也许什么问题都没法解决！**」
   —— 同理，**语法错会让该文件从出错行到文件末尾整段被抛弃**
   （游戏照常进入、运行，只是那部分内容没生效 → 静默）。
2. **合格作品不应在数据库里制造任何错误**。教程原文：
   > 「一个合格的作品不应该在数据库中制造任何错误。」
   —— 多余错误还会在日志里留大量垃圾，影响他人排查。

**日志会清空**：教程明确「完全退出游戏（这样日志文件就会清空）」
→ 想干净复现，**先退游戏再构建再进游戏**；否则只能在长日志里找"本次追加的部分"。

### 2.2 FireTuner —— 查运行时状态

- 游戏安装 `Debug\` 目录下有 35 个 `.ltp`（Lua Tuner Panel）面板；
  实测关键几个：**`City.ltp` / `Player.ltp` / `Players.ltp` / `Unit.ltp` / `Modifiers.ltp`**
- 注意 **`Player.ltp` 与 `Players.ltp` 是两个不同文件**（教程特别标注
  `Player.ltp` **没有 s**）——按面板功能找，别按名字猜。
- 典型用途：`City.ltp` 加人口、`Unit.ltp` 恢复全部移动力、加金币等。
- 本 skill 另有 `civ6-tuner` 做**脚本化**的 Tuner 调用（TCP 4318），比手点面板可复现。
- 详细面板格式见 `debug-tools.md`。

### 2.3 引擎本身的静默行为（不属于以上两者，但必须知道）

| 静默点 | 表现 | 防具 |
|---|---|---|
| 数据库语法错 | 该文件出错行→末尾整段丢弃；游戏照常跑 | `check_sql_exec.py`、**先看 Database.log 第一条** |
| `.tex` 类别写错 | cooker 只报一行 class 不匹配，**XLP cook 仍显示 success**，条目变 error asset | **`art/verify_tex_class.py`** |
| `Types` 的 Kind 非法 | 打包不报错，加载期整行丢弃 | `check_types_kinds.py` |
| 引用名打错 | 游戏与 cooker **都不报错**，只是不显示 | `rgn_validate_runner.mjs` |
| 控制组名打错（Condition/Requirement） | 同上 | 同上 |

---

## 三、`Cultures.artdef` 取值表（权威）

**这不是数据库表** —— `Cultures` / `CultureTypes` 在
`DebugGameplay.sqlite` / `DebugConfiguration.sqlite` / `api.sqlite` 里**都不存在**
（实测三库均无 `%Culture%` 表）。它是**纯 artdef 概念**，只有 `Culture` 与
`UnitCulture` 两个集合。

来源：官方自带 **33 份 `Cultures.artdef`**（`Base\ArtDefs\` + 各 DLC），
下表按资料片分组列出（实测递归解析所得）。

### 3.1 `Culture` 集合（建筑/城市外观风格）

| 来源 | 取值 |
|---|---|
| **Base（19）** | `DEFAULT` `America` `AncientBrick` `AncientEarth` `AncientWood` `Baltic` `Brazil` `Colonial` `EastAsian` `Indonesian` `Mediterranean` `ModernGlass` `Mughal` `NorthAfrican` `RowHouse` `Scottish` `SouthAfrican` `SouthAmerican` `SoutheastAsian` |
| **Expansion1（12）** | `AncientBrick` `AncientEarth` `AncientWood` `Baltic` `Colonial` `Mediterranean` `ModernGlass` `Mughal` `RowHouse` `Scottish` `SouthAfrican` `SoutheastAsian` |
| **Expansion2（16）** | `America` `AncientBrick` `AncientEarth` `AncientWood` `Baltic` `Colonial` `Indonesian` `Maori` `Mediterranean` `ModernGlass` `Mughal` `NorthAfrican` `RowHouse` `Scottish` `SouthAfrican` `SouthAmerican` |
| 全 DLC 合并后新增 | `NorthernEuropean` `Nubian` `Vikings` `CIVILIZATION_GAUL`（后者是 DLC 里少见的"用文明名当 culture"写法） |

> **通用建议**：**一律写 `DEFAULT`**，除非你确实要复刻某个文明的建筑外观。
> 绝大多数 mod 用 `DEFAULT` 即可，写错的值不会报错、只是显示为默认外观。

### 3.2 `UnitCulture` 集合（单位人种外观）

| 来源 | 取值 |
|---|---|
| **Base（11）** | `African` `Asian` `Barbarian` `European` `Indian` `Maori` `Mediterranean` `MiddleEastern` `NativeAmerican` `SouthAmerican` `SouthEastAsian` |
| 全 DLC 合并后新增 | `Aliens` `England` `Euro` `Mutant` `Pirates` `Scientist` `Spain` `Wastelander` `Zombies` |

> 注意 **`European` 与 `Euro` 是两个不同的值**，`England`/`Spain` 是"国别单位外观"
> （多用于场景）。新文明一般取 `European` / `Asian` / `African` 等大类。

---

## 四、忠诚度 / 宗教 3D 链字段名（实测自工程真实文件）

由 `civ6-asset-forge` 的 `reference/loyalty-icon.md` 讲完整流程，这里只固化
**字段名**（教程截图 OCR + 对照 `示例工程` 真实文件双向确认）。

### 4.1 材质（`.mtl`）

实测 `Materials/Loyalty_Overlay_RAGUNNA_QYQXP_material.mtl`：

| 字段 | 值 |
|---|---|
| `m_ClassName` | **`UILensMaterial`** |
| `m_Name` | `<...>_material` |
| `m_ObjectName` | 贴图名（如 `Loyalty_Overlay_RAGUNNA_QYQXP`） |
| `m_ParamName` | **`UILensOverlayTexture`** ← 贴图槽 |
| `m_ParamName` | `TransitionLensTexture`（转场用，可留空） |

### 4.2 资产（`.ast`）

实测 `Assets/Loyalty_Overlay_RAGUNNA_QYQXP_Box.ast`：

| 字段 | Overlay | Pressure |
|---|---|---|
| `m_ClassName` | **`UILensAsset`** | `UILensAsset` |
| 几何 `m_GeoName` | **`HexModelGeo`** | **`PipModelGeo`** |
| 材质 | `Loyalty_Overlay_..._material` | `Loyalty_Pressure_..._material` |
| `m_ParamName` | `LensMaterial` / `FOWMaterial` / `Offset` / `Color` / `Alpha` / `UVOffset` / `UVScale` / `RotateToAlign` / `IsBillboard` / `AnimType` / `AnimDuration` / `AutoPlay` | 同左 |

> **两个几何名不要弄反**：忠诚度覆盖（大范围染色）= `HexModelGeo`（六边形）；
> 压力（小图标）= `PipModelGeo`（点）。
> 几何列是 **`<m_GeoName text="HexModelGeo"/>`**（不是 `m_Name`——`.ast` 里
> `m_Name` 是资产自己的名字，别混）。

### 4.3 XLP

实测 `XLPs/UILensModels.xlp`：

| 字段 | 值 |
|---|---|
| `m_ClassName` | `UILensAsset` |
| `m_PackageName` | **`UILensAssets`**（注意不是 `UILensModels`——**包名与文件名不同**） |
| 条目 | `<...>_Box`（Overlay/Pressure/Religion 各一对） |

> 战略视图那一侧在 `XLPs/StrategicView_UILenses.xlp`，`m_ClassName` = `StrategicView_Sprite`，
> `m_PackageName` = `strategicview/strategicview_uilenses`。
> 五组字段名详见 `civ6-asset-forge/reference/loyalty-icon.md`。

---

## 五、可信度标注

| 内容 | 状态 |
|---|---|
| AE 字段名（§一） | **FROM-OCR**：来自教程截图 OCR，拼写已按常见形式修正（如 `ModuIe`→`Module`、`CIass`→`Class`）；个别按钮文字 OCR 残缺已标注 |
| 调试路径/错误样例/日志清空（§二） | **VERIFIED**：本机实测目录存在；错误样例与纪律引用教程原文；`.ltp` 文件清单实测 |
| `Cultures`/`UnitCulture` 取值（§三） | **VERIFIED**：递归解析 33 份官方 `Cultures.artdef` 所得；并实测确认三库均无 `%Culture%` 表 |
| 忠诚度字段（§四） | **VERIFIED**：对照 `示例工程` 真实 `.mtl`/`.ast`/`.xlp` 逐字段读出 |
