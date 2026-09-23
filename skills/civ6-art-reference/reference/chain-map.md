# 文明6 美术素材引用与配置规律汇总

> 基于 F 盘 Civ6 安装（Base + 全部 DLC，584 个 artdef）与 SDK Assets（262 个 xlp、131 个 artdef）
> 全量解析得出（索引器 0 解析错误）。本文是"规律"层，操作步骤见 `workflow.md`。

## 一、核心机制：四层引用链

```
游戏数据库（Resources/Districts/Buildings/... 表，Type 名）
    │  同名匹配
    ▼
ArtDef 条目（ArtDefs/*.artdef，"装配图"：决定用什么、怎么摆）
    │  ArtDefReferenceValue（跨 artdef 文件引用）+ XrefName 字符串
    ▼
ArtDef 条目（如 Clutter.artdef 的 CLUTTER_X / Landmarks.artdef 的 LM_X）
    │  BLPEntryValue（终端引用，按名指向已打包资产）
    ▼
XLP 条目（*.xlp 是"资产清单"）→ 打包 .blp（模型/贴图/材质本体，game data pack）
```

关键结论：

1. **ArtDef 是装配图，XLP 是资产清单，模型本体在打包 .blp 里**。mod 引用原版素材
   **不需要、也不应该解包任何 .blp**——所有引用都是"按名引用"：
   artdef 条目名、XrefName 字符串、BLPEntryValue 四元组（entry + xlppath + package + class）。
2. **跨文件按名解析**：`ArtDefReferenceValue` 的 `m_ArtDefPath` 指向目标模板文件；
   `m_ElementName` 为空时用成对的 `XrefName` 字符串值作为目标条目名。
   解析时引擎在 **base + 全部 DLC + 全部 mod 的同名模板合并集** 中查找条目——
   因此 mod 条目可以直接引用原版/DLC 的条目而不携带其文件
   （本工程实证：`ArtDefs/Districts.artdef` 的 `DISTRICT_SANCTUARY_RGN` 引用原版
   `StrategicView.artdef::HolySite`；`BUILDING_HUANGLAN_QYQXP` 引用原版 `Library`）。
3. **合并规则（三层级，务必分清）**：
   - 模板级：同名模板（如 `Landmarks.artdef`）合并成一张表。
   - **条目级：同名条目合并到同一容器，不是整体覆盖** —— 最容易踩错的一层。
   - **子条目级：同一子集合内同名子条目被替换，不同名追加，原版未提及的子条目完整保留**。
   实证：原版 `DLC/Ethiopia/ArtDefs/Landmarks.artdef` 的 `DISTRICT_CITY_CENTER` 条目
   `BaseVariants` 为 **0 条**、`BuildingSets` 只加 4 条新标签；若是整体覆盖，原版那 80 条
   BaseVariants 会全部消失，非埃塞俄比亚文明的市中心将集体失去模型。
   推论：给原版对象加东西只能「新增不同名子条目」；改名覆盖会让原版对象在别的场景下失去外观。
4. **消费者（Consumer）注册**：每个 artdef 文件必须挂在 mod `.Art.xml` 的某个
   `artConsumers` 条目下；ModBuddy 构建时把 `.Art.xml` 编译成 `.modinfo` 引用的
   `.dep`，并**自动展开依赖闭包**（如 Improvements consumer 自动补 Landmarks/
   Cultures/Buildings/StrategicView）。运行时引擎按消费者合并加载。
   消费者 ↔ 模板的对应关系以 vanilla 为准（`Resources` 消费者挂 `Resources.artdef`，
   `Landmarks` 消费者挂 `Landmarks/Improvements/Resources/...artdef`）。
5. **civ6proj 清单**：本工程 `ArtDefs/`、`XLPs/` 下的 artdef/xlp 均**未**写入
   `.civ6proj` 的 `<Content>` 清单（ModBuddy 自动打包），生效完全靠 `.Art.xml`
   → `.dep` 链路。新增 artdef/xlp **不需要**改 proj，只需改 `.Art.xml`。
6. **SDK pantry 的角色**：`... SDK Assets/Civ6/pantry/` 是官方源素材库（几何/材质/
   贴图/xlp/artdef 源文件），仅供查询"XLP 里有什么条目、叫什么名"。游戏运行加载的
   是 `Base/ArtDefs` + `DLC/*/ArtDefs` 的 artdef 与打包 blp。
7. **cook 层（本文件之上的一层）另见 `reference/cook-layer.md`** —— 四层引用链只保证
   「引用写对了」；ModBuddy 把源文件 cook 成加载产物时还会：① 因 `.Art.xml` 的
   `<requiredGameArtIDs>` 缺包而**找不到 pantry 源文件**；② 把解析不到的引用
   **静默替换成默认值**（`has had its value replaced with its default value`）；
   ③ 对产物做**归一化**使源文件与加载副本必然逐字节不同。三条都会让人误判。

## 二、Xref 解析细则（实测归纳）

| ArtDefReferenceValue 形态 | 解析目标 |
|---|---|
| `m_ArtDefPath="Clutter.artdef"` + 空元素名 + 成对 `XrefName=CLUTTER_X` | Clutter.artdef 的 `CLUTTER_X` |
| `m_ArtDefPath="Landmarks.artdef"` + `m_RootCollectionName="Districts"` + `m_ElementName="DISTRICT_X"` | 直接指定条目 |
| 空路径 + 空元素名 + `m_ParamName="Xref3D"` + 成对 `Xref3DName=...` | 3D 音频/特殊解析（资源条目中多为音频） |
| 空路径 + 空元素名 + 成对 `XrefName=RES_LM_X`（Landmark 子集合内） | 按参数名解析到 Landmarks.artdef |
| `m_ElementName="Completed"` + `m_ArtDefPath="Improvements.artdef"` + `m_RootCollectionName="BuildStates"` | 同模板文件内的集合条目 |

- `XrefName`/`Xref` 成对出现是最常见模式：**字符串参数决定目标名，引用参数决定目标文件**。
- 资源条目的 `XrefStop`/`Xref3DName` 是**音频**参数（如 `RESOURCE_FISH2D_STOP`），不是模型。

## 三、分对象类别的美术链路（全部实测验证）

### 1. 资源（本 skill 最高频场景）

```
Resources 表（Frequency/SeaFrequency>0 才会出现在地图上，才有可见模型）
→ Resources.artdef :: Resource/RESOURCE_X
   ├─ Clutter 子集合: XrefName=CLUTTER_Y + Xref→Clutter.artdef   ← 常规地表/海面挂载
   ├─ Landmark 子集合: XrefName=RES_LM_Z（Xref 路径空）           ← 特殊挂载（海龟群等）
   ├─ Audio 子集合（可空）
   └─ ClutterVariants: 按 Feature/Terrain 引用换 clutter（如 AMBER 的森林/雪原变体）
→ Clutter.artdef :: CLUTTER_Y
   └─ Plants/Props 子集合 → BLPEntryValue → environment/clutter 包（clutter.xlp）
      例：CLUTTER_OLIVES → RES_Olives_Tree_01..03 + Boulder_* @ environment/clutter
   或 Landmarks.artdef :: RES_LM_Z → BLP @ landmarks/tilebases（RES_Turtles）
```

- 原 44 个 base 资源 + DLC 追加（Expansion1: AMBER/OLIVES/TURTLES；GranColombia: MAIZE/HONEY）。
- 全部可用 CLUTTER 条目（114 base + DLC）见 `art_lookup.py --list Clutter`。
- 2D 图标**不走 artdef**：`IconTextureAtlases`（SQL）+ `Icons.xlp`（UI/Icons 包）。

### 2. 区域

```
Districts 表 → Districts.artdef :: DISTRICT_X
   ├─ 3×BuildStates（Completed/Pillaged/UnderConstruction）+ 3×StrategicView Xref
   └─ Audio
→ Landmarks.artdef :: Districts/DISTRICT_X
   ├─ BaseVariants → BLP DIS_XXX_Ancient/..._Base @ landmarks/tilebases（时代底座）
   ├─ BuildingVariants → BLP DIS_XXX_Library 等 @ landmarks/hero_buildings（hero 建筑本体）
   ├─ BuildingSets 子条目（hero 建筑**组合**，纯索引不含模型 —— 详见 §三.3）
   └─ 引用 CityGenerators::Gen_GenericDistrict / Eras / Cultures / Appeal
→ StrategicView.artdef :: Districts/<名称>（2D 战略视图精灵）
   ★ mod 区域可直接复用原版条目（本工程 DISTRICT_SANCTUARY_RGN 用原版 HolySite）
```

### 3. 建筑（★ 本 skill 最容易踩错的一节）

**核心事实：建筑自身条目不含 3D 模型。** `Buildings.artdef :: BUILDING_X` 只有：

```
Buildings 表 → Buildings.artdef :: BUILDING_X
   ├─ Audio
   └─ StrategicView ×3（Amphitheater / _Pillaged / _UnderConstruction 战略视图精灵）
      ★ 战略视图与 3D 模型是两套东西，可分别指向不同原版对象
```

真正的模型在**该建筑所在区域**的 `Landmarks.artdef` 条目里，由**三个子集合协作**给出：

```
Landmarks.artdef :: Districts/DISTRICT_X          （区域条目）
   ├─ BuildingSets      按「区域内有哪些 hero 建筑」做内容匹配 → 得出一行「标签」
   │    每个子条目 = 一个 CollectionValue，内含若干 ArtDefReferenceValue
   │    param 名 Set / Set001 / Set002…（vanilla 用 Set，ModBuddy 导出为 SetNNN）
   │    指向 Buildings.artdef :: Building/BUILDING_Y
   ├─ BaseVariants      按「标签 + 时代 + 文化 + 吸引力」→ 区域底座模型
   │    param：Set_HeroBuildings(标签) / Tag_Era / Tag_Culture / Tag_Appeal / Asset(BLP)
   │    资产落在 landmarks/tilebases
   └─ BuildingVariants  按「Tag_HeroBuilding = 建筑 art 条目名」→ 建筑本体模型
        param：Tag_HeroBuilding / Tag_Era / Tag_Culture / Tag_Appeal / Asset(BLP)
        资产落在 landmarks/hero_buildings
```

三条硬规律：

1. **标签是任意内部键，不与 DB Type 挂钩。** 原版用过 `MUSEUM_NAT`、`BROADCAST CENTER`
   （后者还带空格），而这两个串在整个游戏 `Data/` 里**根本不存在** —— 它们只是
   `BuildingSets.m_Name` 与 `BaseVariants.Set_HeroBuildings` 之间的连接键。
   引擎先按**内容**（引用了哪些 Building 条目）匹配到 `BuildingSets` 子条目，
   再读它的 `m_Name` 去 `BaseVariants` 里找同名标签。
2. **是否参与这套组合由建筑的 `AffectsDistrictBuildingSet` 字段决定**（在 `Buildings.artdef`）。
   想知道某建筑算不算 hero building，直接看这个字段（`--building` 会打印）。
3. **奇观不走这条路**：`Landmarks.artdef` 独立条目 + `WonderMovie.artdef`（建成动画）。

查询工具：

```
python art_lookup.py --building BUILDING_AMPHITHEATER        # 反查它在哪些区域/哪些组合里，模型落在哪个包
python art_lookup.py --district-buildings DISTRICT_THEATER   # 列出某区域的 hero 组合表（标签 -> 建筑 -> 资产）
```

#### 3.1 替换型建筑（unique / replacement building）怎么上模型

场景：新建筑 `BUILDING_NEW` 取代 `BUILDING_BASE`（如结社建筑取代古罗马剧场）。
原版 Ethiopia 的结社建筑就是这么做的（`BUILDING_OLD_GOD_OBELISK` 取代纪念碑），照抄即可：

1. **`Buildings.artdef`**：克隆 `BUILDING_BASE` 条目 → `BUILDING_NEW`（含 StrategicView 三态）。
2. **`Landmarks.artdef`**：给**每个受影响的区域**增量补三组子条目：
   - `BuildingSets`：新标签组合（把标签里的原 token 换成新 token），引用改成 `BUILDING_NEW`
   - `BuildingVariants`：`Tag_HeroBuilding` 改成 `BUILDING_NEW`，Asset 沿用原建筑的
   - `BaseVariants`：标签换成新 token，Asset 沿用原建筑各时代底座

**两条铁律：**

- ❌ **绝不能改名覆盖原版子条目。** 必须**新增**新标签子条目；否则不玩该玩法、
  或其他文明建原建筑时会失去模型（合并是增量的，原标签子条目必须留着）。
- ⚠️ **必须反查 `DistrictReplaces`，不能只挂「原建筑所在的那个区域」。** 原建筑所在的
  `DISTRICT_BASE` 可能被某个文明特色区域取代（希腊卫城取代剧院广场、本工程
  `DISTRICT_ODYSSEY_RGN` 取代 `DISTRICT_THEATER`），那是**另一条独立的 artdef 链**，
  必须一起挂。`art_copy_building.py` 自动反查游戏侧全部相关区域；
  **mod 侧区域不在索引里，必须用 `--district` 显式补**。

一键生成：

```
python art_copy_building.py BUILDING_AMPHITHEATER BUILDING_GOLDEN_POETRY_SOCIETY_RGN     --buildings-out "<mod>/ArtDefs/Buildings.artdef"     --landmarks-out "<mod>/ArtDefs/Landmarks.artdef"     --district DISTRICT_ODYSSEY_RGN
```

工具行为：反查相关区域 → 逐区域从**该区域自己的子条目**推导形状（目标文件里已有该区域
就用它自己的，否则取游戏侧同名区域）→ 改标签 / `Tag_HeroBuilding` / `Set` 引用 →
**增量追加**（同名子条目自动跳过，幂等）→ 写完后自检「原有内容零丢失」。

取舍：`BuildingVariants` 一条 `Tag_Era=DEFAULT` 即可全时代通用；`BaseVariants` 建议按原建筑
逐条镜像，以保证区域底座随时代变化。

### 4. 改良

```
Improvements 表 → Improvements.artdef :: IMPROVEMENT_X
   ├─ Landmark Xref → Landmarks.artdef :: LM_X → BLP @ landmarks/tilebases 或 environment/clutter
   ├─ StrategicView×3（可复用原版，如本工程 BUBBLES 未自定义）
   └─ BuildStates×3
```

### 5. 单位

```
Units 表 → Units.artdef :: UNIT_X
   ├─ UnitMemberTypes 子条目（UnitMemberTypes/<名称>_Ancient01..）→ BLP @ units/units
   ├─ 引用 Cultures::UnitCulture / Eras::Era（文明/时代变体）
   └─ Formation/Audio/VFX
（领袖与文明另有专项 skill：civ6-asset-forge → reference/leader-2d.md / reference/loyalty-icon.md）
```

#### 5.1 单位美术的装配链（克隆前必须走通）

```
Units.artdef :: Units/<UNIT_X>            ← 条目名 == DB UnitType
   └─ Members/MembersN → Type → UnitMemberTypes/<成员类型名>     （成员类型）
        └─ Cultures/Any → Variations/A → Attachments/<部位>
             └─ Bins → <bin 路径>          （真正的模型部件）
```

**两个模板其实是一个**：`Unit_Bins.artdef` 的 `<m_TemplateName text="Units"/>`
与 `Units.artdef` 相同 —— 二者合并成同一张逻辑表。`Unit_Bins.artdef` 主体是
`Assets` 集合（bin 定义），`Units.artdef` 主体是 `Units`/`UnitMemberTypes`/`Bins` 引用。
**个别 DLC 的 `Units.artdef` 也自带 `Assets` 集合定义 bin**（实测
`DLC\CivRoyaleScenario\ArtDefs\Units.artdef`、`DLC\WarMachineScenario\ArtDefs\Units.artdef`）。

#### 5.2 ★ 克隆原版单位条目前必做：bin 可解析性体检

原版条目「存在」不代表「能正常渲染」——**原版自身就有引用了不存在 bin 的成员类型**。
克隆到这种条目上，实机表现是**单位渲染残缺**。

体检方法（合并集范围，Base + 全 DLC）：

1. 取所有 Units 模板文件（`Units.artdef` + `Unit_Bins.artdef`，含各 DLC）里出现过的
   **全部 `<m_Name>`** 作为 bin 名全集；
2. 对目标成员类型，取 `Bins` 集合里的每条 `m_Name`（bin 路径，按 `/` 分段）；
3. 每一段（跳过运行时占位符 `#`、`V:` 前缀）都必须落在 bin 名全集里。

**坑**：按「`Assets` 子集合」抽取 bin 名会被嵌套集合截断而漏名，导致假阳性爆炸
（实测某次误抽只得到 489 条，于是 301/302 个成员类型全被误判「悬空」）。
用「文件内全部 `m_Name`」这种粗口径反而可靠。

实测结论（合并集 302 个成员类型中）：**只有 8 个成员类型存在悬空 bin**，
其中 `Great_*` 系列**仅 1 个**（见 §5.3），其余 21 个 `Great_*` 全部完好。

#### 5.3 伟人（Great Person）单位：条目名是**运行时拼出来的**

```
GreatPersonClasses.UnitType          → 类级基名（DB 只有这个，如 UNIT_GREAT_MUSICIAN）
        + GreatPersonIndividuals.Gender   → _FEMALE / _MALE
        + GreatPersonIndividuals.EraType  → _INDUSTRIAL / _RENAISSANCE / ...
        ▼
引擎去 artdef 里找条目 UNIT_GREAT_<CLASS>[_FEMALE|_MALE][_<ERA>]
```

实测：DB `Units` 表里**只有** `UNIT_GREAT_MUSICIAN`，而
`UNIT_GREAT_MUSICIAN_FEMALE` / `_MALE` / `_FEMALE_INDUSTRIAL` / `_MALE_INDUSTRIAL`
**一律不存在** —— 这些名字只存在于 `Base\ArtDefs\Units.artdef` 的条目里。
30 个 `Great_*` 成员类型全部由这类「组合名 artdef 条目」引用
（`UNIT_GREAT_ARTIST_FEMALE` → `Great_Painter_Female_Renaissance` 等等）。

**推论（排查/克隆时最容易错的一点）**：判断某个成员类型「是否真的会被渲染」，
**不能只看它在 artdef 里有没有被引用** —— 组合名条目存在，但如果没有任何
`(UnitType, Gender, Era)` 三元组会拼出那个名字，它永远不会被选中。

实证缺陷：`UNIT_GREAT_MUSICIAN_FEMALE` 这个 artdef 条目存在，但它指向的
成员类型 `Great_Musician_Female_Renaissance` 的
`GreatPeople/GreatMusician_Renaissance_Female` bin **在任何 Units 模板文件里都没有定义**
（对照：`GreatMusician_Renaissance_Male` 有）。而**原版 3 位女性音乐家全部是
`ERA_ATOMIC` / `ERA_INFORMATION`** —— 于是 `_Renaissance` 档在原版从未被渲染过，
这个缺陷也就从未暴露。

**症状签名**（很有用）：

| 实机表现 | 缺的 bin |
|---|---|
| **只有头（光头），身体/服饰/道具全没** | `Armor` / `Bodies` 类 bin 解析失败（Head bin 独立，仍能加载） |
| 有身体但缺手/道具 | 对应 `Hands` / `Weapons` / `Accessories` bin 解析失败 |

修法：换一个 bin 全部可解析的成员类型（或自己声明补齐缺失 bin）。
实测 `Great_Musician_Female_Industrial` 的 6 个 bin 全部可解析，可作女性音乐家替代。

> 给 mod 单位（含伟人）配美术时，最稳的做法是**让 artdef 条目名 == DB 的 UnitType**
> 并显式指向一个已验证的成员类型 —— 这样不依赖运行时拼名。

#### 5.4 单位条目命名观察

30 个 `Great_*` 成员类型对应的 artdef 条目名形如
`UNIT_GREAT_<CLASS>`（类级）、`UNIT_GREAT_<CLASS>_FEMALE|_MALE`（性别级）、
`UNIT_GREAT_<CLASS>_FEMALE|_MALE_<ERA>`（时代级）。**这些名字在 DB 里都查不到**，
不要拿 `Units` 表去校验它们的存在性。

### 6. 特征（Features.artdef）与 2D 图标

- 特征：Features 表 → Features.artdef（+ Clutter/Landmarks/StrategicView 联动）。
- 2D UI 图标（单位/建筑/资源头像）：`IconTextureAtlases` + `IconFontIcons`（SQL），
  素材在 `Icons.xlp`（UI/Icons 包）。**与本 skill 的 artdef 链无关**。

## 四、XLP 包 → 作用对照（引用时的"终点"速查）

| BLP package | 内容 | 常见来源 artdef |
|---|---|---|
| `environment/clutter` | 资源/地表杂物模型 | Clutter |
| `landmarks/tilebases` | 区域底座、改良地标、资源地标 | Landmarks/Improvements |
| `landmarks/city_buildings` | 程序化生成的城区普通房屋 | **CityGenerators**（不是建筑链！）|
| `landmarks/hero_buildings` | 区域内置建筑**本体**（Amphitheater/Museum/BroadcastCenter…）| Landmarks `BuildingVariants` |
| `units/units` | 全部单位模型 | Units |
| `strategicview/strategicview_*` | 战略视图 2D 精灵 | StrategicView |
| `UI/Icons` | 2D 图标图集 | Icons.xlp（SQL 侧引用） |
| `VFX` / `lighting/default_lighting` | 特效 / 灯光 | VFX / Leaders |

查询任意包的条目清单：`art_lookup.py --xlp environment/clutter`。

## 五、素材命名风格速查（便于"猜"原版资产名）

- 资源杂物：`RES_<名>_Tree_01` / `RES_Crabs` / `RES_Turtles`（XLP 条目）
- 区域：`DIS_<缩写>_<时代>_Base_0N`、`DIS_<缩写>_<建筑>`（tilebases / hero_buildings）
- 建筑：`BLD_*`（city_buildings）
- 地标改良：`LM_*`（Landmarks.artdef 条目）；单位：UnitMemberTypes 无前缀直接语义名
- Clutter：`CLUTTER_<资源名>[_FOREST|_JUNGLE|_TUNDRA|_SNOW]`（特征/地形变体后缀）
- 资源 Landmark：`RES_LM_<名>`

## 六、坑与注意

1. **只在地图上刷的资源才需要模型**（`Frequency>0` 或 `SeaFrequency>0`；其余引用会
   因永不出现在地块而不渲染，配了也无害）。
2. 引用 DLC 引入的条目（如 Expansion1 的 `CLUTTER_OLIVES`）要求玩家拥有该 DLC——
   在 mod 依赖（AssociationData）里声明对应依赖即可（本工程已依赖 GS）。
3. `m_ReplaceMergedCollectionElements` / `m_AppendMergedParameterCollections` 一般保持
   `false`（与 vanilla、本工程既有文件一致）。
4. 个别原版 SDK 文件有损坏（单冒号前缀 `AssetObjects:`、尾部 NUL 截断，集中在
   Expansion1 pantry 少量文件）——索引器已做容错；游戏安装目录的 artdef 全部完好。
5. artdef 不进 rgn_validate 校验范围（那是 SQL 引用完整性工具）；artdef 的"定义-引用
   闭合"检查靠本 skill 的 `art_lookup.py`（条目是否存在）+ 游戏内验证。
6. **同名 artdef 条目是增量合并，不是覆盖** —— 详见 §一.3。给原版对象加东西只能
   **新增不同名子条目**；改名覆盖会让原版对象在别的场景下失去外观。
7. **区域 hero 组合的标签名是任意内部键**，不要试图从 DB Type 推导（原版用过
   `MUSEUM_NAT` / `BROADCAST CENTER` 这种 Data 里根本不存在的串）。
8. **替换型建筑要反查 `DistrictReplaces`**，把原区域 + 所有取代它的特色区域都挂上，
   否则那条链没模型（本工程黄金诗社需同时挂 `DISTRICT_THEATER` +
   `DISTRICT_ODYSSEY_RGN` + `DISTRICT_ACROPOLIS`）。
9. **子集合是追加单位**：往已有条目追加子条目时，插到该集合的 `</Element>` 之前即可，
   不要重建整个条目。
10. **裸纹理名那一类**：`Governors.PortraitImage` / `PortraitImageSelected`、
    `SecretSocieties.SmallIcon` 存的是**纹理名**，靠 UITexture XLP 包按名查找
    （不走 IconTextureAtlases），排查见 §七。
11. **`.Art.xml` 的 `<requiredGameArtIDs>` 必须覆盖用到的每个 DLC 素材所属包** ——
    它经 `Civ6.targets` 的 `GeneratePantryPaths` 决定 cooker 的 `--pantry` 搜索路径。
    漏声明的症状是 `Cannot cook the ArtDef (..._Shared.artdef) since it does not exist
    in the pantry!` / `Unable to find the XLP (...)` / `Unable to auto-generate ArtDef
    dependency information.`。传递依赖会自动展开（声明 `Expansion2` 会带出 `Shared`）。
    详见 `reference/cook-layer.md` §一。
12. **源文件 ≠ 加载产物是固有的**（cook 会做行尾 LF 化、空元素收紧、剥注释、结构重排）。
    所以「`ArtDefs/` 与 Mods 副本逐字节不一致」**不是**异常信号；正确判据是
    **重新 cook 一次的产物** vs Mods 副本（实测 13/13 相同）。同步测试副本要拷
    **cook 产物**，不要拷裸源。
13. **构建日志里的 `error` 未必是错**：`EXEC(0,0): error asset: (Error/TileBase_Error_Asset)`
    是 MSBuild `ConsoleToMsBuild="true"` 对 cooker 输出行的重新分级；`IgnoreExitCode="true"`
    又让 cooker 的失败退出码被忽略。**判影响力要看产物字节，不要看日志级别**。

## 七、裸纹理名链（不走 artdef 的那类，悬空排查高发区）

有些 DB 列存的不是 icon 名，而是**纹理名本身**，引擎直接去 UITexture XLP 包里按名找。
这类引用没有 artdef 中转、也没有 IconTextureAtlases，**查不到通常是静默空白**（不报错，
只表现为「图没了」），是悬空排查最容易漏的一类。

| DB 列 | 用途 | 实测规格（原版 DDS） |
|---|---|---|
| `Governors.PortraitImage` | 总督面板结社栏 | **206×208** |
| `Governors.PortraitImageSelected` | 总督详情页；**也是结社「首次发现」弹窗主图** | **326×339** |
| `SecretSocieties.SmallIcon` | 结社小徽章（UI 里 `<Image Texture="...">`）| **59×59**（圆盘直径实测 55px）|

要点：

1. **必须做三件事**：① DDS 放 `Textures/`；② 在某个 UITexture XLP 里加
   `m_EntryID` + `m_ObjectName`；③ 该 XLP 的 `m_PackageName` 要挂在 `.Art.xml` 的
   `UITexture` consumer 的 `relativePackagePaths` 下。
2. **`IconTextureAtlases` 救不了它**：图集是「icon 名 → Atlas+Index」，
   裸纹理名查不到图集。反过来，图集自身 `Filename="X.dds"` 也需要 XLP 条目 ——
   只写 SQL/XML 不写 XLP 是常见漏项。

   > ⚠️ **重要更正（2026-09-19）**：**`.dds` 没有「裸名不进 XLP」这回事** —— 本项目实测
   > `Icons_RGN.xml` 的 107 个 `Filename`（69 个带 `.dds` + 38 个裸名）**全部**都在 `Icons.xlp` 里
   > （带后缀的以去后缀 stem 登记）。**图集贴图一律需要 XLP 条目。
   >
   > ✅ **真正的简化点在别处 —— 直接导入的图片（DDS）走 ImportFiles，写法与 bink 视频完全一致**：
   >
   > | 步骤 | 写法 |
   > |---|---|
   > | ① 磁盘位置 | `ImportFiles/<子目录>/<Name>.dds`（如 `ImportFiles/movies/` 放 bink 那样） |
   > | ② `.civ6proj` | `<Content Include="ImportFiles\<子目录>\<Name>.dds"><SubType>Content</SubType></Content>` |
   > | ③ 加载动作 | `<ImportFiles id="..."><Properties><LoadOrder>600000</LoadOrder></Properties><File>ImportFiles/<子目录>/<Name>.dds</File>...</ImportFiles>` |
   > | ④ 引用 | 在 `Icons` XML 或对应 SQL 表（如 `GreatWorks`、`MomentIllustrations`）直接填 `Filename` |
   >
   > 参照本项目 bink 视频的既有写法（`ImportFiles/movies/RGN_Bard_Movies_1.bik`，
   > `.civ6proj` `<Content>` + `ImportFiles` 动作 + modinfo `<Files>` 三处齐全）—— **图片照抄同款格式**。
   > **对照实例（直接照抄这两组，把 `.bik` 换成 `.dds`）**：
   >
   > ```xml
   > <!-- ① 视频（既有写法） -->
   > <Content Include="ImportFiles\movies\RGN_Bard_Movies_1.bik">
   >   <SubType>Content</SubType>
   > </Content>
   > <!-- ② 图片（照抄同款） -->
   > <Content Include="ImportFiles\icons\ICON_MY_THING_22.dds">
   >   <SubType>Content</SubType>
   > </Content>
   > ```
   >
   > ```xml
   > <ImportFiles id="MyMod_ImportFiles">
   >   <Properties><LoadOrder>600000</LoadOrder></Properties>
   >   <File>ImportFiles/movies/RGN_Bard_Movies_1.bik</File>
   >   <File>ImportFiles/icons/ICON_MY_THING_22.dds</File>
   > </ImportFiles>
   > ```
   >
   > ⚠️ **别把图片丢进 `Textures/`**：`Textures/` 是 pantry（AssetEditor 会递归扫描，
   > `.tex` 只许存在此处、且 `m_Name`/`m_RelativePath` 必须全工程唯一）。
   > 走 ImportFiles 的图片放 `ImportFiles/<子目录>/`，**不需要 `.tex`**、不进 pantry。
   >
   > **打包成品 mod 时的执行口径**：只要不涉及领袖外交相关图片导入，
   > **允许不询问用户**，直接按上表 ImportFiles 导入图片 + 填 `Filename` 引用。
   > **领袖外交相关图片**（立绘 / 外交背景 / 纸片人 TEXTURE·OPACITY）仍必须走 XLP + artdef 链。
3. **写死的映射表**：`SecretSocietyPopup.lua` 的 `kDiscoveredImages` 把 4 个原版结社
   硬编码映射到 `GovernorSelectedSTK_<Society>`；mod 结社取到 nil。需要**全量替换**该 Lua
   （先例：项目内 `RockBandMoviePopup.lua`，文件名与原版**完全一致**才能顶替，
   且要经 `ImportFiles` 注册、按玩法 Criteria 门控）。
4. **裸纹理名的 DDS 最好与项目既有素材逐字节同构**（头部签名 `FTXT`、RGBA8 掩码、
   无 mip 的未压缩 32bpp），比对基准：项目 `Textures/` 下任意既有 DDS。
