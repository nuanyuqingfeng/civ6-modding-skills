← 返回 `SKILL.md` 路由

> 本文件内 `scripts/…`、`templates/…`、`assets/…`、`reference/…` 的根目录 = `civ6-asset-forge/`。

## 一、铁律：素材处理前必须询问

**开始任何忠诚度图标任务前，必须先询问用户是否提供文明图标素材**。询问模板：

> 本次任务是否已提供文明图标素材？
>
> **素材要求：**
> - 格式：PNG 或 DDS，**透明背景**，尺寸 **≥256×256**（512 更佳）
> - 尺寸判定基准 = 图标 **alpha 质量集中区（主体）**，外围稀疏装饰（射线、飘带等）不参与定标；主体须贴合官方光晕轮廓（细则见第六节第 1 条）
>
> 请选择：
> - **已有素材**：提供图标路径
> - **暂无素材**：我将自动从工程 `Textures/` 里找**尺寸最大**的 `ICON_CIVILIZATION_*` 作为图标源
>
> 产出 4 张 PNG（默认输出到 `D:\desktop\loyalty_out`），由你审核后再做 DDS/.tex。

- 光晕模板（黑色径向光晕 512×512）**skill 内置**：`templates/Loyalty_Overlay_Template.png`，无需用户提供
- 用户坚持用自己模板时用 `--glow` 指定（尺寸必须 512×512）
- **宗教分支**：图标 = 宗教标志（非文明徽记），未提供时自动找工程 Textures 最大的 `ICON_RELIGION_*`

## 二、任务路由

| 任务 | 处理 |
|------|------|
| 为新文明生成忠诚度图标 PNG（4 张） | → 第四节：运行 `process_loyalty_icon.py`（默认 `--kind loyalty`） |
| 生成并注册忠诚度注册链（XLP/ArtDef/mtl/ast/Art.xml/civ6proj） | → 第四节：运行 `gen_loyalty_art.py` |
| **为新增自定义宗教生成宗教压力图标 PNG（3 张）** | → 第八节：`process_loyalty_icon.py --kind religion` |
| **为新宗教生成并注册注册链** | → 第八节：`gen_religion_art.py` |
| 覆盖官方预留宗教（RELIGION_CUSTOM_1~12）的图标 | **不走注册链**：直接覆盖同名贴图（`TEXTURE_Religion_Pressure_Custom1` 等），见第八节末 |
| 2D UI 宗教图标（Civilopedia/信仰面板的 270px、IconTextureAtlases 图集） | **不在本 skill 范围**（IconTextureAtlases 数据路径，与战略视图/3D 镜头无关） |
| 审核通过后做 DDS/.tex | → `civ6-modding` skill 的 `art-pipeline.md`（role：`loyalty_3d` / `loyalty_sv`） |
| 2D 领袖立绘相关 | → 本 skill `reference/leader-2d.md`（本类不处理立绘） |

> **触发判定**：仅当任务涉及**宗教图标**（宗教压力、宗教镜头覆盖、自定义宗教注册）时走宗教分支；涉及文明忠诚度时走忠诚度分支。两者可共存于同一工程（注册链文件相同，条目按命名区分）。

## 三、产出物一览（每文明 4 张图 + 8 个注册文件）

### 图像素材（process_loyalty_icon.py 生成）

| 文件 | 尺寸 | 内容 | 用途 |
|------|------|------|------|
| `Loyalty_Overlay_{S}.png` | 512×512 | 黑色光晕 + 图标原色居中叠放 | 3D 覆盖材质贴图（UILensOverlayTexture） |
| `Loyalty_Pressure_{S}.png` | 128×128 | 白色小剪影（透明背景） | 3D 压力材质贴图 |
| `StrategicView_Loyalty_Overlay_{S}.png` | 256×256 | 512 版 LANCZOS 缩小 | 战略视图覆盖 sprite |
| `StrategicView_Loyalty_Pressure_{S}.png` | 128×128 | 与 3D 压力版相同 | 战略视图压力 sprite |

占位符 `{S}` 定义见第七节。

### 注册链（gen_loyalty_art.py 生成）

| 文件 | 说明 |
|------|------|
| `XLPs/UILensModels.xlp` | UILensAsset 条目包：2 个 Box 素材条目/文明 |
| `XLPs/StrategicView_UILenses.xlp` | StrategicView_Sprite 条目包：追加 2 条 sprite/文明 |
| `ArtDefs/Overlay.artdef` | `LoyaltyLensArrows`（civ→Pressure_Box）+ `LoyaltyWarning_{CIV}`（→Overlay_Box） |
| `ArtDefs/StrategicView.artdef` | `UILenses`（2 元素/文明）+ `UILensEntries`（2 条目/文明） |
| `Materials/Loyalty_{Overlay,Pressure}_{S}_material.mtl` | UILensMaterial，引用贴图 ObjectName |
| `Assets/Loyalty_{Overlay,Pressure}_{S}_Box.ast` | UILensAsset 素材：几何 + 材质绑定 |
| `<工程>.Art.xml` | 幂等补 consumer/library 接线 |
| `<工程>.civ6proj` | 幂等补 4 条 Content 注册 |

## 四、标准工作流

### 1. 收集信息

- 确认文明精确 `CivilizationType`（从项目 Data SQL 查，如 `CIVILIZATION_RAGUNNA_QYQXP`）
- 按第一节铁律确认图标来源

### 2. 生成 4 张 PNG

```bash
# 用户提供了图标
python <skill>\scripts\process_loyalty_icon.py --icon "<图标路径>" --suffix RAGUNNA_QYQXP --out-dir "<输出目录>"

# 未提供：自动从工程 Textures 找最大的 ICON_CIVILIZATION_*
python <skill>\scripts\process_loyalty_icon.py --project "<工程路径>" --suffix RAGUNNA_QYQXP --out-dir "<输出目录>"
```

- 尺寸判定默认 `--fit-mode core`（定标细则见第六节第 1 条）：主体仍偏小/偏大时调
  `--keep`（默认 0.90，**调小→核心区更小→图标更大**，如 0.85；调大→更保守）
- `--fit-mode extent` 恢复"最外圈像素"定标（官方 Feline 样例对齐用）
- 源图标为**彩色**时加 `--whiten-overlay`（官方样例图标本身是白色，故默认保持原色）
- 输出 PNG 交用户审核；不通过时调 `--glow`/`--keep` 或更换源图标（过审门槛见第九节）

### 3. 生成注册链

```bash
python <skill>\scripts\gen_loyalty_art.py --project "<工程路径>" --civ-types CIVILIZATION_RAGUNNA_QYQXP
```

多文明聚合：`--civ-types CIVILIZATION_A,CIVILIZATION_B`（XLP/ArtDef 条目幂等追加）。

脚本行为：
- XLP 已存在 → 追加缺失条目（兼容 `<m_Entries/>` 空自闭合形式）；全存在 → 未变
- **两个 ArtDef 只在不存在时整体生成**；已存在则跳过并提示手动合并（防止覆盖其他功能条目）
- Art.xml 接线（幂等）：consumer `Overlay`/`RangeArrows`/`UILensAsset` ← `Overlay.artdef`；consumer `StrategicView_Properties`/`StrategicView_Sprite` ← `StrategicView.artdef`；library `UILensAsset` ← 包 `UILensAssets`
- civ6proj 幂等补 4 条 Content：`XLPs\UILensModels.xlp`、`XLPs\StrategicView_UILenses.xlp`、`ArtDefs\Overlay.artdef`、`ArtDefs\StrategicView.artdef`

### 4. 审核 + DDS/.tex（滞后步骤）

用户审核 PNG 通过后，直接对审核用的 PNG（**留在原处即可**，桌面审核文件夹、任意路径均可）走 `civ6-modding` art-pipeline：

1. manifest role 用 `loyalty_3d`（512/128 两张，单尺寸）与 `loyalty_sv`（256/128 两张，单尺寸），source 填绝对路径
2. `convert_art.ps1` 出 DDS + `gen_tex.py` 出 `.tex`，产出落在工程 `Textures/`（按第五节命名）。
   **`gen_tex.py` 默认把 `m_ClassName` 写成 `UserInterface`，出 `.tex` 后必须手工改类别**（见第六节第 10 条），
   直接对照 `templates/loyalty_chain/Textures/` 里的 4 个模板改 `m_ClassName` 与 `m_Tags`
3. ModBuddy 重新构建，进游戏开一局验证：城市受忠诚度负向压力时 3D 六边形显示图标、战略视图显示 sprite

> **不要为导入而把源 PNG 复制进工程**（如 `.assets` / `Textures`）：`.tex` 的 `SourceFilePath`
> 只在 AssetEditor 重新导入时才用到，**构建/游戏只读同名 DDS，导入后删除源 PNG 不影响任何东西**。
> manifest/asset_map.json 等临时工作文件用完即删。

## 五、命名规范

| 对象 | 格式 | 示例 |
|------|------|------|
| 3D 贴图/纹理名 | `Loyalty_Overlay_{S}` / `Loyalty_Pressure_{S}` | `Loyalty_Overlay_RAGUNNA_QYQXP` |
| 战略视图 sprite | `StrategicView_Loyalty_Overlay_{S}` / `StrategicView_Loyalty_Pressure_{S}` | `StrategicView_Loyalty_Pressure_RAGUNNA_QYQXP` |
| 材质 | `Loyalty_{Kind}_{S}_material` | `Loyalty_Overlay_RAGUNNA_QYQXP_material` |
| Box 素材 | `Loyalty_{Kind}_{S}_Box` | `Loyalty_Pressure_RAGUNNA_QYQXP_Box` |
| UILensEntries 条目 | `LoyaltyOverlayIcon_{S}` / `LoyaltyPressureIcon_{S}` | `LoyaltyOverlayIcon_RAGUNNA_QYQXP` |
| artdef 元素名 | `LoyaltyWarning_{CIV}`、`{CIV}`（引擎按完整文明类型查找） | `LoyaltyWarning_CIVILIZATION_RAGUNNA_QYQXP` |

## 六、关键架构事实

1. **尺寸判定基准（core 模式，默认）**：以图标 alpha 质量（不透明像素）的**集中区**定标——
   横/竖两个方向的 alpha 边际分布各裁掉 `(1-keep)/2` 尾部质量（`--keep` 默认 0.90），
   核心区适配官方盒；全图同比例缩放、核心中心对齐画布中心。RGN 徽记类外围带射线/飘带的
   图标主体可放大 ~1.5 倍，装饰稀疏时 core≈extent。
   **官方 PSD 摆放盒**：Overlay 512 中核心区 fit 进 **227×269 居中 (256,256)**，叠在
   光晕上层保持原色不透明；Pressure 128 中白色剪影 fit 进 **40×48 居中 (64,64)**。
   SV 覆盖版 = 512 版 LANCZOS 缩到 256；SV 压力版与 3D 压力版同图。
2. **光晕模板**：黑色径向光晕（中心平台 alpha≈168，向边缘衰减），只含 alpha 形状信息；官方样例的最终 alpha = 光晕 alpha（图标画在光晕之上）。
3. **Box ast 复用官方几何**：Overlay 用 `HexModelGeo`（mesh `Official_Hex 034`，AnimType `FADE_LOOP`，AutoPlay true）；Pressure 用 `PipModelGeo`/`PipModel`（AnimType `NONE`，AutoPlay false）。**不自建几何**，唯一变量是材质引用。
4. **材质最小单元是贴图但入口在材质**：AssetEditor 无法直接导入 3D 镜头贴图，必须经 mtl 的 `UILensOverlayTexture` 参数挂贴图（脚本直接写 mtl）。
5. **XLP / ArtDef 的构建接入点：`.civ6proj` 的 `<Content>` 不是必需项**——`.xlp` 是 cook 输入，既不进 Content 也不进产物；`.artdef` 由构建产物 `.modinfo` 自动收进。**真正的必需项是 `.Art.xml`**（经 `<UpdateArt>` 的 `(Mod Art Dependency File)` 挂载）中的 consumer / `requiredGameArtIDs` 声明。`gen_loyalty_art.py` / `gen_religion_art.py` 会**幂等补写** Content 条目（可选冗余，写了不报错）；Materials/Assets/Textures 目录构建时自动扫描，无需注册。
6. **包合并**：`strategicview/strategicview_uilenses`、`UILensAssets` 包与基础库同名合并，故 artdef 引用基础/自有条目均可。
7. **引擎查找约定**：Overlay.artdef 的 `LoyaltyLensArrows` 下子集合名 = 完整 `CIVILIZATION_X` 类型名；StrategicView.artdef 的 UILenses 元素名 = `LoyaltyWarning_{CIV}` 与 `{CIV}`——名字打错游戏不报错但图标不显示。
8. **压力箭头**：SV 压力条目里的 `ReligionPressureArrow_ReligionPressureArrow` 是官方共享箭头条目，直接引用不要改名。
9. Pressure 仅 48px 高，细节多的图标缩成一团属正常（源图尺寸要求见第一节）。
10. **`.tex` 类别硬约束（cooker 报错 `has class: 'UserInterface', but is bound to parameter:
   'UILensOverlayTexture' which does not accept this class` 的根因）**：3D 镜头贴图
   （`Loyalty_Overlay_*` / `Loyalty_Pressure_*`）`m_ClassName` 必须是 **`Generic_BaseColor`**
   （此类贴图 `m_Tags` 留空）；战略视图 sprite（`StrategicView_Loyalty_*`）必须是
   **`StrategicView_Sprite`**（`m_Tags` 三连 `StrategicView_Sprite` / `StrategicView` / `Sprite`）。
   错误会沿"材质 → Box 资产 → XLP 条目"逐级传播，XLP cook 仍显示 "completed with success"
   但条目已被替换成 error asset，不能当成功处理。模板见 `templates/loyalty_chain/Textures/`。
11. **ArtDefReferenceValue 引用名必须与 UILensEntries 定义名逐字符一致**：`UILensEntries` 条目名用
   短后缀 `{S}`（`LoyaltyOverlayIcon_{S}` / `LoyaltyPressureIcon_{S}`），`UILenses` 集合里的引用
   也必须用短后缀——不要用完整 `CIVILIZATION_X`。悬空引用游戏/cooker 都不报错，但战略视图图标静默不显示。
12. **Pressure ast 的 `m_GroupName` 固定为 `"09 - Default"`**（PipModelGeo 官方网格组名），不能写成 `"PipModel"`——组名对不上压力小图标不渲染。
13. **宗教分支（第八节）**：引擎查找键是 artdef 元素名 `RELIGION_{R}`
   （= DB `Religions.Type`，错字静默不显示，同第 7/11 条）；SV sprite 与 UILensEntries 条目
   **同名** `ReligionPressureIcon_{R}`（忠诚度是条目名≠sprite名）；`ReligionLensIcons`/
   `ReligionLensArrows` 走同名元素合并追加（见第八节第 3 条）。
   官方宗教压力贴图 128×128、均为白色单色模板。
14. **素材透明化原则（处理源图时的铁律）**：黑底白图转透明只做"亮度→alpha 直映射、颜色置纯白"，
   **只保留白色**；图形内部的黑色切线、镂空一律保持透明（游戏内透出底色/光晕），**禁止洞填充、
   禁止把内部镂空做实**。

## 七、参考工程与内置模板

### 内置模板：`templates/loyalty_chain/`

完整忠诚度注册链通用模板（**出处 工程 A，游戏构建验证通过**）。占位符：

- **`{S}`** = 文明内部名去掉 `CIVILIZATION_` 前缀（如 `RAGUNNA_QYQXP`），出现在文件名与条目名中
- **`{CIV}`** = 完整文明类型名（如 `CIVILIZATION_RAGUNNA_QYQXP`），仅出现在 artdef 元素名中

| 子目录 | 文件 | 说明 |
|--------|------|------|
| `ArtDefs/` | `Overlay.artdef`、`StrategicView.artdef` | 3D 镜头 + 战略视图接线；根集合只保留空骨架，内容仅 `LoyaltyLensArrows`、`LoyaltyWarning_{CIV}`（Overlay）与 `UILenses`、`UILensEntries`（StrategicView） |
| `XLPs/` | `UILensModels.xlp`、`StrategicView_UILenses.xlp` | 两个条目包，各含 2 条忠诚度条目 |
| `Materials/` | `Loyalty_{Overlay,Pressure}_{S}_material.mtl` | UILensMaterial，`UILensOverlayTexture` 挂贴图 |
| `Assets/` | `Loyalty_{Overlay,Pressure}_{S}_Box.ast` | UILensAsset（官方几何复用 + 材质绑定） |
| `Textures/` | 4 个 `.tex` | **类别正确的贴图声明**：3D 版 `Generic_BaseColor` / SV 版 `StrategicView_Sprite`，修 tex 类别错误时以此为准 |

> 两个 artdef 模板是"忠诚度专用最小集"：工程已有同名 artdef 时走幂等合并，不要整体覆盖。

### 内置模板：`templates/religion_chain/`

新宗教注册链通用模板（**出处为官方 Base 游戏 `Base/ArtDefs` 明文 artdef + `UILensAssets.blp` 实测结构**）。占位符：

- **`{R}`** = 宗教类型去掉 `RELIGION_` 前缀（如 `CUSTOM_RGN`），出现在文件名与条目名中
- **`RELIGION_{R}`** = 完整宗教类型名，仅出现在 artdef 元素名中（引擎查找键）

| 子目录 | 文件 | 说明 |
|--------|------|------|
| `ArtDefs/` | `Overlay.artdef`、`StrategicView.artdef` | `Religion_Pressure_{R}` + `ReligionLensIcons` + `ReligionLensArrows`（Overlay）；`UILenses` + `UILensEntries`（StrategicView） |
| `XLPs/` | `UILensModels.xlp`、`StrategicView_UILenses.xlp` | 2 Box 条目 + 1 sprite 条目 |
| `Materials/` | `Religion_{Overlay,Pressure}_{R}_material.mtl` | UILensMaterial，`UILensOverlayTexture` 挂贴图 |
| `Assets/` | `Religion_{Overlay,Pressure}_{R}_Box.ast` | UILensAsset（官方几何复用 + 材质绑定，与忠诚度同构） |
| `Textures/` | 3 个 `.tex` | **类别正确的贴图声明**：3D 版（Overlay 512 / Pressure 128）`Generic_BaseColor` 无 tags；SV 版（`ReligionPressureIcon_{R}` 128）`StrategicView_Sprite` 三 tags |

> 两 artdef 同样是"宗教专用最小集"：工程已有同名 artdef 时走脚本的幂等合并，不要整体覆盖。

### 外部参考工程

| 工程 | 路径 | 备注 |
|------|------|------|
| 示例工程（本工程） | `D:\documents\Firaxis ModBuddy\Civilization VI\示例工程\示例工程` | |
| 工程 A | `D:\documents\Firaxis ModBuddy\Civilization VI\工程 A\工程 A` | 忠诚度注册链模板来源（已内置上表副本，磁盘工程不存在时以内置模板为准） |
| 工程 C / 工程 B | 同级目录 | 对照 `Overlay.artdef` 的 `LoyaltyWarning_{CIV}` 与 `StrategicView.artdef` 的 `UILensEntries` 条目结构 |
| 教程素材（官方 PSD/样例） | `<上游教程仓库本地副本>\Assets\` | `Loyalty_Overlay_Template.psd`、`Loyalty_Pressure_Template.psd` 及 Feline 四张样例 |

## 八、宗教分支（新增自定义宗教压力图标）

与忠诚度**同一套引擎机制**（UILensAsset + 同两个 XLP 包 + 同两个 ArtDef + 同一套官方几何/贴图类别约束），仅命名映射与 artdef 目标集合不同。官方参照（Base 游戏实测）：`Base/ArtDefs/Overlay.artdef`、`Base/ArtDefs/StrategicView.artdef`、`Base/Platforms/Windows/BLPs/UILensAssets.blp`、`strategicview/strategicview_uilenses.blp`。

### 1. 命名映射（{R} = 宗教类型去掉 `RELIGION_` 前缀，如 `CUSTOM_RGN`）

| 对象 | 命名 | 对应官方样例 |
|------|------|------------|
| 宗教类型（DB `Religions.Type`） | `RELIGION_{R}`（**引擎查找键，artdef 元素名必须逐字符一致**） | `RELIGION_BUDDHISM` |
| 3D Box 资产 | `Religion_Overlay_{R}_Box` / `Religion_Pressure_{R}_Box` | `Religion_Pressure_Buddhism_Box` |
| 材质 | `Religion_{Overlay,Pressure}_{R}_material` | 同构 |
| 战略视图 sprite = UILensEntries 条目名（**两者同名**，与忠诚度的"条目名≠sprite名"不同） | `ReligionPressureIcon_{R}` | `ReligionPressureIcon_Hinduism` |
| 3D 贴图 | `Religion_Overlay_{R}`(512) / `Religion_Pressure_{R}`(128) | 同构 |
| 共享箭头 | 直接引用基础库 `ReligionPressureArrow_ReligionPressureArrow` / `ReligionPressureArrow_Box` 等，**不重复声明** | 同忠诚度规则 |

类型名自拟（建议 `RELIGION_XXX_RGN`，走 AGENTS.md 主体后置缩写）；**禁止 `RELIGION_CUSTOM_*`**（官方 1~12 预留位已全链注册，脚本会拒绝）。

### 2. 工作流

```bash
# ① 3 张 PNG（默认输出 D:\desktop\religion_out，交用户审核）
python <skill>\scripts\process_loyalty_icon.py --kind religion --icon "<图标路径>" --suffix CUSTOM_RGN
#    未提供图标时：--project "<工程路径>" 自动找 Textures 最大的 ICON_RELIGION_*
#    尺寸参数 --fit-mode/--keep/--whiten-overlay 与忠诚度分支共用

# ② 注册链（幂等追加，可与忠诚度条目共存）
python <skill>\scripts\gen_religion_art.py --project "<工程路径>" --religion-types RELIGION_CUSTOM_RGN
#    多宗教：--religion-types RELIGION_A,RELIGION_B

# ③ 审核通过后 DDS/.tex：同第四节第 4 步，role 相同（loyalty_3d / loyalty_sv），
#    .tex 类别硬约束相同（3D→Generic_BaseColor / SV→StrategicView_Sprite），
#    tex 模板见 templates/religion_chain/Textures/
```

每宗教 3 张 PNG（战略视图无覆盖层，比忠诚度少一张 256 SV overlay）：

| 文件 | 尺寸 | 用途 |
|------|------|------|
| `Religion_Overlay_{R}.png` | 512×512 | 3D 宗教镜头城市 hex 覆盖（光晕 + 图标） |
| `Religion_Pressure_{R}.png` | 128×128 | 3D 压力 pip 白色剪影 |
| `ReligionPressureIcon_{R}.png` | 128×128 | 战略视图压力 sprite（与 128 版同图） |

### 3. 注册链落点（与忠诚度的差异）

| 文件 | 宗教分支追加内容 |
|------|----------------|
| `ArtDefs/Overlay.artdef`（根集合 Overlays） | ① 元素 `Religion_Pressure_{R}`（Model 子集合，官方完整字段集：`HexModel`+`HexModelFOW` 双 Box 引用 + `MoveOffset` 等 13 参数）；② 元素 `ReligionLensIcons`（LensModel 子项 `RELIGION_{R}` → `Religion_Overlay_{R}_Box`）；③ 元素 `ReligionLensArrows`（LensModel 子项 `RELIGION_{R}` → `Religion_Pressure_{R}_Box`） |
| `ArtDefs/StrategicView.artdef` | `UILenses` 元素 `RELIGION_{R}`（PositionSet=`1_Center`、PlacementRule=`ReligiousPressure`，**两者 ArtDefPath 均为 StrategicView.artdef**，与忠诚度用 StrategicView_Shared.artdef 不同；Entries: Arrow=共享箭头 / Icon=`ReligionPressureIcon_{R}`）+ `UILensEntries` 条目 `ReligionPressureIcon_{R}` |
| `XLPs/UILensModels.xlp` | 2 Box 条目/宗教 |
| `XLPs/StrategicView_UILenses.xlp` | 1 sprite 条目/宗教（宗教只有 SV 压力图标，无 SV 覆盖） |
| `Materials/`、`Assets/` | 每宗教 2 mtl + 2 ast（几何与忠诚度完全相同：HexModelGeo/FADE_LOOP、PipModelGeo/NONE、组名 `09 - Default`） |

**同名元素合并语义**：`ReligionLensIcons`/`ReligionLensArrows` 是基础库已有元素，mod 侧以**同名元素**声明 + `m_ReplaceMergedCollectionElements=false`，游戏合并时即向 LensModel 子集合**追加**子项，无需覆盖官方 25 个宗教条目；`gen_religion_art.py` 找不到锚点时报"请手动合并"，不静默跳过。

### 4. 不覆盖 Custom 预留位

官方 `RELIGION_CUSTOM_1~12` 的 3D/战略视图链已全部注册（2D 图集另预留到 Custom36）。换用预留位只需**覆盖同名贴图**（`TEXTURE_Religion_Pressure_Custom1` 等），不需要本脚本的注册链。

## 九、交付要求

- 交付说明包含：4 张 PNG 清单（尺寸/输出目录）、注册链文件清单、Art.xml/civ6proj 改动说明、"待用户审核/待 tex+dds"清单
- 图标源未提供时，明确标注实际使用了工程内哪个文件作为图标源
- 审核未通过前不得生成 DDS/.tex，不得提交 git
- DDS/.tex 阶段**不得**把源 PNG 复制进工程（见第四节末尾说明），临时 manifest/asset_map 用完即删
