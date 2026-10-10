# CHANGELOG — civ6-art-reference

## 1.3 — 2026-09-14

来源：把 1.2 的「源 ↔ Mods 副本不一致」结论拿去**横向验证 12 个工程**，发现 1.2 写的
「源与产物永远不同、无意义」**太粗**——它对一半以上文件是必然的，等于把真实缺陷也一起
忽略了。本版把一维判据升级为**分级判据**，并新增只读体检工具。

### 🔴 更正 1.2 的过度结论：「源 ↔ Mods 不一致」不是一个信号，要分级

1.2 写「源 `ArtDefs/X.artdef` vs Mods 副本 —— 永远不同，无意义」。
**实测不成立**：12 个工程里有 **5 个工程的源 artdef 与产物逐字节相同**（L0）。
正确表述是**分级**：

| 级别 | 归一化 | 性质 |
|---|---|---|
| L0 | 无 | 完全一致 |
| L1 | 统一行尾 | 纯 CRLF/LF |
| L2 | + 自闭合收紧 `\s+/>`→`/>` | `<x />` vs `<x/>` |
| L3 | + 抹缩进 | 缩进 |
| L4 | + 删空行 | 空行 |
| L5 | + 剥 XML 注释 | 注释被 cook 剥离 |
| — | L5 仍不同 | **语义层**：`cook 补结构`（无害但永久）/ `引用被清空`（★ 真缺陷） |

**L1–L5 命中即可忽略**；只有 L5 仍不同才需要人工看。

### 🔴 更正：编码层的消除办法是**把源统一成 cook 规范写法**

**cook 的规范形式就是 LF**。源若为 `LF + <x/> 紧凑 + 无注释`，cook 不再改变它，
源可与产物逐字节相同。两条实证：

1. 5 个「源即产物」的工程（`工程 E` / `工程 F` / `工程 G` /
   `工程 H` / `工程 I`）源 artdef **全部是 LF（CRLF=0）**，L0 全同。
2. **`工程 C` 是天然对照实验**：12 个文件里唯一是 CRLF 的
   `FallbackLeaders.artdef`，恰好是唯一 L0 不同的文件。

`示例工程` 之所以「几乎全部不同步」，就是源 artdef 混了大量 CRLF
（9 个文件含 CRLF，`Resources.artdef` 多达 2161 处）：13 个文件里
**6 个纯 L1 行尾、3 个 L4、1 个 L5、3 个语义层**。

### 🆕 新增：语义层差异的两个具体默认值

1.2 说「引用被替换成默认值」，但没写默认值是什么。实测：

- artdef 条目引用不到 → 产物写成 **`_MissingArt`**
- 条目名 / XLP 引用不到 → 产物写成 **`text=""`**

因此 `Districts.artdef` / `Landmarks.artdef` 这类文件**永远不可能靠统一编码与产物一致**
—— 只有修掉解析不到的引用才会一致。

### 🆕 新工具：`scripts/artdef_sync_check.py`（只读）

```bash
python artdef_sync_check.py <工程名>      # 单工程
python artdef_sync_check.py --all         # 扫工程根下全部工程
python artdef_sync_check.py <工程名> --detail 3 --report r.txt --json r.json
```

逐文件给出 L0–L5 级别或语义层定性（`cook 补结构` / `引用被清空→_MissingArt` /
`引用被清空→空值`），并单独报告「仅源有」「仅 Mods 有」的文件级增删。
退出码 0 = 只有编码层差异；1 = 存在语义层差异或文件增删（便于接 CI/钩子）。
默认路径自动探测，可用 `--src-root` / `--mods-root` 或环境变量
`CIV6_PROJ_ROOT` / `CIV6_MODS_ROOT` 覆盖。

### ⚠️ 方法本身的实证更正（第二次，同类）

1.2 已记录过「bin 全集口径写窄 → 假阳性爆炸」。这次同类错误又出现在**自闭合收紧**上：
v1 用「标签名后紧跟空白」的正则 `<([A-Za-z_][^\s>/]*)\s+/>` —— 它**跨越不了属性里的
空格**，只能匹配无属性空元素（`<Element />`），于是把大量带属性的自闭合
（`<m_ParamName text="X" />`）误判成「内容真不同」，让 `示例工程` 的
「纯编码层」文件数从 9 被低估成 6。

**教训（已写入 `cook-layer.md` §2.2）**：归一化正则必须用 `\s+/>` → `/>` 这种
**不依赖标签名结构**的写法；且任何分级判据上线前都要先用已知样本反向校验。

### 🔍 副产品：用新判据反查出两个兄弟工程的真实缺陷

判据跑 `--all` 后，`工程 A` 与 `工程 D` 各有 1 个文件报语义层差异：

- `StrategicView_Shared.artdef` 由 **`Civ6\DLC\Expansion2\pantry`** 提供
  （其中 L27 定义 `LoyaltyPressure`、L35 定义 `LoyaltyWarning`）；
- 这两个工程的 `.Art.xml` **只声明了 `Civ6`** → pantry 里没有 Expansion2
  → 源里的 `m_ElementName="LoyaltyWarning"` + `m_ArtDefPath="StrategicView_Shared.artdef"`
  在产物中被**双双清空**；
- **对照**：`工程 B` 声明了 `Expansion2`，产物保留该路径 → 因果吻合。

即这两个工程带着**与 示例工程 修复前完全相同的病**在构建。
另 `工程 B\ArtDefs\StrategicView.artdef` 引用了
`m_EntryName="StrategicView_DISTRICT_HIGHTECH_INDUSTRIAL_QYQXP"`（L1349/L1367，
指向 `StrategicView_UILenses.xlp`），但该 XLP 里**没有这个 EntryID** → 产物被清空
→ 实机该战略视图条目无美术。

> 按用户指示，**仅报告，未改动任何兄弟工程文件**。

### 证据来源

- 12 个工程 `ArtDefs/*.artdef` 源 vs `Mods/<名>/ArtDefs` 全量分级比对（本 CHANGELOG
  各表的数字均出自该次比对）
- `工程 C`：12 个文件中 11 个 L0 相同，唯一 CRLF 文件为唯一 L0 不同
- `示例工程` 语义层逐条定性：`Districts.artdef` 3 处 `Preserve*` → `_MissingArt`；
  `Landmarks.artdef` 5 处源值变空；`Overlay.artdef` 产物多 3 行 `<m_CollectionName>`；
  `StrategicView.artdef` 仅 3 行注释被剥
- SDK pantry：`Civ6\DLC\Expansion2\pantry\ArtDefs\StrategicView_Shared.artdef`
  定义 `LoyaltyPressure`(L27) / `LoyaltyWarning`(L35)
- 两个兄弟工程 `.Art.xml` 的 `<requiredGameArtIDs>` 段（均仅 `Civ6`）
- `工程 B\XLPs\StrategicView_UILenses.xlp` 的 `m_EntryID` 全集

---

## 1.2 — 2026-09-14

来源：为 示例工程 排「每次 build 后几乎全部 artdef 与 Mods 副本不同步」、
「XLP 登记报错」、「某单位实机只显示一个光头」三个问题，一路挖到**四层引用链之上
的 cook 层**。该层此前完全没有文档，现补 `reference/cook-layer.md` 并修正两处旧结论。

### 🆕 新增：cook 层（`reference/cook-layer.md`，全新一层）

四层引用链只解决「引用写对了没有」。**注册对了 ≠ cook 过了 ≠ 运行时对**，中间这层是：

| 主题 | 关键结论 |
|---|---|
| pantry 解析 | `.Art.xml` 的 `<requiredGameArtIDs>` 经 `Civ6.targets` 的 `GeneratePantryPaths` 展开成 cooker 的 `--pantry` 路径表（传递闭包自动展开）；漏声明 → `Cannot cook the ArtDef ... does not exist in the pantry!` / `Unable to find the XLP (...)` / `Unable to auto-generate ArtDef dependency information.` |
| 包依赖图 | `Civ6`(根，无 requiredGameArtIDs) ← `Shared` ← `Expansion1` / `Expansion2`；实测 GUID 已收录。**不是所有 DLC 都有 pantry**（`KublaiKhan_Vietnam` 没有） |
| 产物归一化 | cook 会 LF 化行尾、收紧空元素、剥注释、结构重排 → **源文件与加载副本必然逐字节不同** |
| 警告语义 | `references an ArtDef entry (X) that does not exist` + **`has had its value replaced with its default value`** = 引用被静默清成默认值（那个引用点实际没有美术了） |
| 判影响力 | **重新 cook → 产物与 Mods 副本逐字节比对**。日志级别会骗人 |
| XLP 可解析性 | `m_ObjectName` 解析失败（`<pantry>/Assets/<name>.ast` I/O 错误）→ 整条被移出 `.blp`，**产物字节不变 = 零运行时影响**；反之填一个真实资产名会真的打包并覆盖 DLC 几何体 = 实机被改坏 |

### 🔴 更正：同步 Mods 副本的对象是 **cook 产物**，不是裸源（`workflow.md` §⑦⑧）

旧文写「`Copy-Item` 同步源文件 → Mods 副本」。对 artdef 而言这是**错的**：Mods 副本是
cook 产物，拷裸源会让副本与下一次构建结果漂移，并掩盖「有人手改过副本」的真实信号。

正确判据：

- ✗ 源 `ArtDefs/X.artdef` vs Mods 副本 —— 永远不同，无意义；
- ✓ **重新 cook 一次的产物** vs Mods 副本 —— 本工程实测 **13 / 13 逐字节相同**。

推论：artdef 源 ↔ Mods 副本不一致**不构成**「双目录不一致」告警。

### 🆕 新增：单位链路补充（`chain-map.md` §三.5.1–5.4）

1. **`Unit_Bins.artdef` 与 `Units.artdef` 是同一个模板**（`<m_TemplateName text="Units"/>`），
   合并成一张逻辑表；且**个别 DLC 的 `Units.artdef` 也自带 `Assets` 集合定义 bin**。
2. **克隆原版单位条目前必做 bin 可解析性体检** —— 原版自身就有引用了不存在 bin 的
   成员类型。合并集 302 个成员类型中 8 个有悬空 bin。
3. **伟人单位的 artdef 条目名是运行时拼的**：`GreatPersonClasses.UnitType`
   + `Gender` + `EraType` → `UNIT_GREAT_<CLASS>[_FEMALE|_MALE][_<ERA>]`。
   DB `Units` 表里**只有类级基名**，组合名一个都查不到 —— 所以**不能拿 DB 去校验
   这些条目名的存在性**，也**不能只看「artdef 里有没有被引用」判断它会不会渲染**。
4. **症状签名**：单位「只剩一个头（光头）」= `Armor`/`Bodies` 类 bin 解析失败
   （Head bin 独立，仍能加载）。

### 🆕 新增：`SKILL.md` 排错速查表

把本次三类现象直接映射到对应章节（artdef「不同步」/ pantry 报错 / 引用被降级 /
`error asset:` 误报 / 单位只剩头）。

### ⚠️ 方法本身的实证更正（重要，避免重踩）

给成员类型做 bin 体检时，我第一版按「**`Assets` 子集合**」抽取 bin 名 —— 结果被
嵌套集合截断，Base 只抽到 489 条（该文件实有 1364 处 `Assets`），于是
**301 / 302 个成员类型全被误判「悬空」**。换用「文件内全部 `<m_Name>`」的粗口径
（合并集 3485 条）后结果才收敛为 8 个。

**教训**：体检脚本的「全集口径」必须先用已知完好对象做反向校验（例如
`Great_Musician_Female_Industrial` 的 6 个 bin 必须全部解析成功），否则假阳性会淹没真问题。

### 证据来源

- `Civ6.targets`（`<SDK>\ModBuddy\`）的 `GeneratePantryPaths` / `ArtDefCookerCmd` /
  `XLPCookerCmdWindows` / `<Exec ConsoleToMsBuild="true" IgnoreExitCode="true">`
- MSBuild 输出的 `Art Pantry Path -` 行（4 条路径，`Civ6\pantry` 重复）
- SDK pantry：`Civ6.Art.xml`（无 requiredGameArtIDs）、`Shared.Art.xml`(→Civ6)、
  `Expansion1.Art.xml`(→Shared)、`Expansion2.Art.xml`(→Shared)；`KublaiKhan_Vietnam`
  无 pantry Art.xml
- 手工重放 ArtDef cook：7 对 `references ...` + `... replaced with its default value`
  （全部指向 `DISTRICT_PROTOVENO_RGN`）
- 手工重放 XLP cook：4 × `Removing package asset entry` + `HAS MISSING ENTRIES!`
  + **退出码 2**；产物 `landmarks/tilebases.blp` = 34,816 B / SHA256 `CC549F071B50ADDF…`，
  与改动前及实机副本逐字节相同
- MOD 全量 13 个 artdef 新 cook 产物 vs 实机 Mods 副本：**13/13 逐字节相同**
- SDK pantry 全部 262 个 xlp、16,358 条条目：`EntryID == ObjectName` 占 93.4%
- 合并集审计（`Base/ArtDefs` + 全 `DLC/*/ArtDefs`，35 个 Units.artdef + 31 个
  Unit_Bins.artdef、302 个 UnitMemberTypes、bin 名全集 3485 条）：
  `Great_Musician_Female_Renaissance` 的 `GreatPeople/GreatMusician_Renaissance_Female`
  **在任何 Units 模板文件中都没有定义**（对照 `_Male` 有）
- DB（`DebugGameplay.sqlite`）：`GreatPersonClasses.UnitType` 只有类级基名；
  `UNIT_GREAT_MUSICIAN_FEMALE` / `_MALE` / `_FEMALE_INDUSTRIAL` 在 `Units` 表**均不存在**；
  原版女性音乐家 3 位全部是 `ERA_ATOMIC` / `ERA_INFORMATION`
- 全游戏 XML/SQL 搜索：`UNIT_GREAT_MUSICIAN_FEMALE` **0 命中**（对照男性 `UNIT_GREAT_MUSICIAN`
  15 命中），但它**存在**于 `Base\ArtDefs\Units.artdef:16067` 作为条目名

### 回归验证方式

```
# 1) cook 产物 vs Mods 副本（应 13/13 逐字节相同）
#    手工重放 cook 到临时 --banquet_hall，再逐个 SHA256 比对（命令模板见 cook-layer.md §五）
# 2) 单位 bin 体检（应只剩 8 个成员类型有悬空 bin，其中 Great_* 仅 1 个）
#    bin 名全集取「所有 Units 模板文件的全部 <m_Name>」，勿用 Assets 子集合口径
# 3) 伟人条目名不可用 DB 校验
#    SELECT COUNT(*) FROM Units WHERE UnitType='UNIT_GREAT_MUSICIAN_FEMALE'  → 0（正常）
```

---

## 1.1 — 2026-09-11

来源：为「黄金诗社」建筑（取代古罗马剧场）注册 3D 模型时，发现本 skill 的建筑链路描述
**有错且不完整**，遂整轮更正并把方法工具化。所有结论均有实证，见文末「证据来源」。

### 🔴 更正：建筑 3D 模型链路（`reference/chain-map.md` §三.3 整节重写）

| 旧文档 | 实况 |
|---|---|
| 建筑模型由所在区域 `BuildingSets` 提供 | `BuildingSets` 只是**组合索引**，不含模型；模型分在 `BaseVariants`（区域底座 @ `landmarks/tilebases`）与 `BuildingVariants`（建筑本体 @ `landmarks/hero_buildings`）|
| 包名 `landmarks/city_buildings` | `city_buildings` 只被 **CityGenerators** 引用（程序化城区房屋），与建筑链无关 |
| 未提连接键 | 连接键是 `Set_HeroBuildings`（标签）与 `Tag_HeroBuilding`（建筑 art 条目名）|
| 未提判定字段 | 建筑是否参与组合由 `Buildings.artdef` 的 `AffectsDistrictBuildingSet` 决定 |

三条新写入的硬规律：

1. **标签是任意内部键**，不与 DB Type 挂钩。原版用过 `MUSEUM_NAT`、`BROADCAST CENTER`
   （带空格），这两个串在整个游戏 `Data/` 里**根本不存在** —— 引擎是按「引用了哪些
   Building 条目」做内容匹配，再拿 `BuildingSets.m_Name` 去 `BaseVariants` 找同名标签。
2. 建筑条目只有 `Audio` + `StrategicView ×3`，**没有模型**。
3. 奇观不走这条路（`Landmarks.artdef` 独立条目 + `WonderMovie.artdef`）。

### 🔴 更正：artdef 合并语义（`reference/chain-map.md` §一.3 重写）

旧文档写「mod 条目名 = 已有名字 → **覆盖**（慎用）」，**这是误导性的**，照做会破坏原版外观。
实测为**三层级增量合并**：

- 模板级：同名模板合并成一张表
- **条目级：同名条目合并到同一容器，不是整体覆盖**
- **子条目级：同一子集合内同名子条目替换，不同名追加，原版未提及的子条目完整保留**

推论（已写入 §六 坑位）：**给原版对象加东西只能新增不同名子条目**；改名覆盖会让原版对象
在别的场景下失去外观。

### 新增：替换型建筑上 3D 模型流程（§三.3.1 + `workflow.md` §④′）

场景：新建筑取代原版建筑（结社建筑 / 特色建筑）。照原版 Ethiopia 结社建筑的做法，
给**每个受影响的区域**增量补 `BuildingSets` / `BuildingVariants` / `BaseVariants` 三组子条目。

**两条铁律：**

1. ❌ 绝不改名覆盖原版子条目 —— 只能**新增**新标签子条目
2. ⚠️ 必须反查 `DistrictReplaces` —— 原建筑所在区域可能被特色区域取代，
   那是**另一条独立的 artdef 链**。实证：本工程除 `DISTRICT_THEATER` 外，
   还必须挂 `DISTRICT_ODYSSEY_RGN`（mod 特色区域）与 **`DISTRICT_ACROPOLIS`**
   （原版希腊特色区域 —— 靠人肉想是想不到的，是工具自动反查揪出来的）

### 新增：§七 裸纹理名链（悬空排查例外章）

`Governors.PortraitImage` / `PortraitImageSelected`、`SecretSocieties.SmallIcon` 这类
**存纹理名、靠 UITexture XLP 按名查找**的列：不走 artdef，也不走 IconTextureAtlases，
查不到通常是静默空白。收录了实测规格（206×208 / 326×339 / 59×59，圆盘直径 55px）、
必须做的三件事，以及 `SecretSocietyPopup.lua` 里 `kDiscoveredImages` 写死映射表的坑。

### 工具

| 工具 | 变化 |
|---|---|
| `artdef_indexer.py` | schema 扩展：`entries[].childCollections`（子集合结构）、`entries[].fields`（`AffectsDistrictBuildingSet` 等）、`references[].param`、**新增 `childReferences[]`（子条目级引用）** |
| `art_lookup.py` | 新增 `--building B`（反查建筑 3D 模型链）、`--district-buildings D`（列区域 hero 组合表）；两者按 `parent` 限定作用域（同名子条目会跨区域重名） |
| `art_copy_building.py` | **新建**：反查相关区域 → 逐区域从该区域自己的子条目推导形状 → 改标签/`Tag_HeroBuilding`/`Set` → 增量追加（幂等）→ 自带「原有内容零丢失」自检 |

### ⚠️ 必须重建索引

`assets/art_index.json.gz` 已用新版 schema 重建（artdefs 715 / xlps 262 / 解析错误 0 /
1.29 MB）。**用旧索引跑新 `art_lookup` 的 `--building` / `--district-buildings` 会拿不到数据。**

```
python scripts/artdef_indexer.py
```

### 证据来源

- 原版 `DLC/Ethiopia/ArtDefs/Landmarks.artdef` 的 `DISTRICT_CITY_CENTER`：`BaseVariants`
  **0 条**、`BuildingSets` 只加 4 条新标签 → 证明是增量合并
- 同上 `DISTRICT_CAMPUS` / `DISTRICT_COMMERCIAL_HUB` / `DISTRICT_DIPLOMATIC_QUARTER`：
  同样只加新标签子条目
- 原版 `Ethiopia_SecretSocieties_MODE.xml` 定义的 `BUILDING_OLD_GOD_OBELISK` 是
  **玩法门控**的，而引用它的 Landmarks.artdef 无条件加载 → 证明「引用门控对象」是原版
  认可的做法，安全
- 全库搜索：`MUSEUM_NAT` / `BROADCAST CENTER` 在游戏 `Data/` 中不存在 → 证明标签非派生
- `landmarks/city_buildings` 的全部引用方 = CityGenerators（15 个 artdef）→ 证明旧文档包名写错
- 端到端回归：`art_lookup.py --building BUILDING_OLD_GOD_OBELISK` 能正确复现原版
  Ethiopia 的 4 条 `OBELISK` 组合与 `DIS_CTY_Obelisk` 资产

### 回归验证方式

原版 Ethiopia 的**旧神方尖碑**是「替换型建筑」的同款场景，作 ground truth：

```
python art_lookup.py --building BUILDING_OLD_GOD_OBELISK          # 应出 DISTRICT_CITY_CENTER 的 OBELISK* 组合
python art_lookup.py --district-buildings DISTRICT_THEATER        # 应出 8 组合 / 5 本体 / 16 底座
python art_copy_building.py <原版建筑> <新建筑> --dry-run          # 先看反查结果与目标区域
```

---

## 1.0 — 2026-09-05

初始版本：ArtDef/XLP 四层引用链（DB Type → artdef 条目 → Xref → BLPEntryValue → 打包资产）、
资源与区域链路、消费者注册、静态校验清单，工具 `artdef_indexer.py` / `art_lookup.py` / `art_copy.py`。
