---
name: civ6-asset-forge
description: "Civ6 美术素材合成 + 注册链一体化 skill（美术素材合成类 5 类合一）：① 总督素材（governor icon / 就职图标与晋升徽章 24px / 32、64px 头像 / 206x208、326x339 立绘 / 边缘透明渐变、立绘抠边）；② 忠诚度与宗教压力图标（文明 Loyalty Overlay/Pressure + 战略视图 sprite，含新增自定义宗教分支）；③ 单位晋升图标（promotion icon）**生成管线已作废**（失败尝试的遗留），只保留尺寸/格式规格 `reference/promotion-icon-sizes.md`；④ 2D 领袖立绘纸片人（完整美术注册链 + 1024×1024 TEXTURE/OPACITY）；⑤ UI 领袖立绘与选人界面背景（Sukritact's Civ Selection Screen 适配：Players.Portrait/PortraitBackground 的 2D 立绘 + 1440×1080 背景）；⑥ 历史时刻插画（MomentIllustrations：456×332 卡片，含 18 张官方形状模板套版）。五类共用同一注册链机制（.dds/.tex → xlp/artdef/mtl/ast → Art.xml → .civ6proj 幂等补注册）与同一套校验顺序；处理用户素材前必须先询问，默认只生成注册文件。边界：总督八边形徽章与单位晋升五边形盾形**不得混用**；3D 模型、UI 布局改动、2D UI 宗教图标（IconTextureAtlases 270px 图集）、config（领袖互斥/同名）不在本 skill 范围；png→dds/.tex 转换走 `civ6-modding` 的 art-pipeline。触发词：总督素材、governor icon、就职图标、总督徽章、总督立绘、边缘透明渐变、立绘抠边、忠诚度图标、宗教压力图标、自定义宗教注册、晋升图标、promotion icon、单位晋升、白色图标合成、盾形徽章、2D 领袖、立绘纸片人、领袖美术注册链、suk selection、Sukritact、Civ Selection Screen、选人界面、领袖选择界面、PortraitBackground、UILeaders.xlp、UI 领袖立绘、领袖选择背景、历史时刻、历史时刻插画、时代得分图、historic moment、MomentIllustrations、Moment_、PrideMoments。"
version: "1.0"
author: 千与千寻瀑
license: MIT
category: game-modding
tags:
  - civ6
  - art-pipeline
  - icon
  - artdef
  - xlp
  - mtl
  - ast
  - texture
  - imagegen
  - modding
models:
  recommended:
    - claude-sonnet-4
  compatible:
    - gpt-4o
    - deepseek-v3
languages:
  - zh
  - en
---

> 🧰 **工具先查名录（硬性）**：要写脚本做某件事之前，先看本 skill 的 [`TOOLS.md`](TOOLS.md)
> —— 本 skill 全部脚本的用途 / 用法 / 路径清单，外加本机**路径收纳**表。
> **有能用的就改它，不要重建。** 新增或改名脚本后，跑一次
> `python "<skills>/civ6-modding/tools/skill_manifest.py" civ6-asset-forge` 刷新名录（`--check` 可做漂移检测）。

> **本 skill 由 4 个美术素材合成类 skill 合并而来**（`civ6-loyalty-icon` / `civ6-promotion-icon` /
> `civ6-governor-art` / `civ6-leader-2d`），来源与各自最后 commit 见 `CHANGELOG.md`；
> 2026-09-17 新增第 ⑤ 类（UI 领袖立绘 / Suk 选人界面背景，`reference/ui-leader-portrait.md`）
> 与第 ⑥ 类（历史时刻插画，`reference/moment-illustration.md`）；
> **2026-09-17/18 类别③ 单位晋升图标的生成管线按用户裁决作废**（失败尝试的遗留，已删除），
> 只保留尺寸/格式规格 `reference/promotion-icon-sizes.md`（清单见 `CHANGELOG.md`）。
> 骨架共用：给定 PNG → 确定性合成器（Python/Pillow）→ 原版风格素材 → 注册链 → 校验器；
> 注册链逻辑只在本文件维护一份，类别专属实测规格（尺寸/坐标/配色/像素参数）逐字保留在 `reference/*.md`。

## 一、本 skill 覆盖的五类素材（边界先读）

| 类别 | 解决的"做什么素材" | 主要产出 | **不做什么** |
|------|------------------|---------|-------------|
| 总督素材<br>`reference/governor-art.md` | 总督头像/徽章/立绘（含立绘边缘透明渐变、抠边） | 24px 就职/晋升徽章、32/64px 头像图标、206×208 常态立绘、326×339 选中立绘、软边 1024² TEXTURE/OPACITY | 不做 3D 总督模型；不做城市横幅滴的 UI 布局改动（只出贴图）；不改 `GovernorPanel.lua` 图标查找逻辑 |
| 忠诚度 / 宗教压力图标<br>`reference/loyalty-icon.md` | 文明忠诚度图标、宗教压力图标、新增自定义宗教 | 每文明 4 张 PNG（3D 覆盖/压力 + 战略视图覆盖/压力）、每宗教 3 张 PNG + 完整 UILens 注册链 | 不处理 2D UI 宗教图标（`IconTextureAtlases` 270px 图集，数据路径）→ **真实落点在 `civ6-modding/art-pipeline.md` 的图标规范化一节**（含"同名重复注册静默劫持图标"的实战坑）；不处理立绘 |
| 2D 领袖<br>`reference/leader-2d.md` | 2D 领袖立绘纸片人（全套注册链）、1024×1024 TEXTURE/OPACITY | XLP 包 / `Leaders.artdef` / 几何 / 材质 / 灯光 / 环境光 / `.tex` / 行为资产 ast | 不生成素材（用户未提供时只出注册文件）；不做 config（领袖互斥/同名，见项目 `DuplicateLeaders`） |
| **UI 领袖立绘 / 选人界面背景**<br>`reference/ui-leader-portrait.md` | **Sukritact's Civ Selection Screen** 选人界面的 2D 立绘（`Players.Portrait`）与背景（`Players.PortraitBackground`） | 每领袖 2 张 `_Suk` 贴图（立绘 = 内容定宽 ×1024 高；背景 = 外交背景中心裁 1440×1080）+ `UPDATE Players` + XLP + `Criteria` 接线 | 不做 3D 纸片人注册链（→ 类别④）；不负责 Suk mod 本体分发；不处理加载界面（`IMG_LOADING_*` / `LoadingInfo`，另一条链） |
| **历史时刻插画**<br>`reference/moment-illustration.md` | **`MomentIllustrations`** 的插画卡片（特色单位/区域/建筑/改良/总督的时刻图） | 每张 **456×332** 贴图（套 **18 张官方形状模板**之一）+ `UI_PrideMoments.xlp` 登记 + `MomentIllustrations` 行 | 不新增 `MomentIllustrationType`（属玩法侧表级改动）；不做 `Moments` 表（时刻本体）；不处理非历史时刻的其它 UI 图 |

> ⚠ **已作废：原类别③ 单位晋升图标（promotion icon）。** 其**生成管线**（盾形模板 + 白剪影合成器 /
> 四色重着色 / 图集切格 / IoU 校验 / 生图模板与提示词手册）是**失败尝试的遗留**，已按用户裁决作废并删除；
> 本 skill 只保留**尺寸与格式事实**：`reference/promotion-icon-sizes.md`。**不要再照旧文档做图。**

**三条最容易踩的混用**：

1. 总督 24px 徽章是**八边形**（上下切角），单位晋升是**五边形盾形**——两者规格、配色、图集完全是两套，**禁止互相套用**（详见 `reference/governor-art/specs.md` §2.3「与单位晋升的区别」、`reference/governor-art.md`「边界」节，与 `reference/promotion-icon-sizes.md` 的盾形轮廓表）。
2. 「晋升」一词要分清：**单位晋升**（原类别③，生成管线已作废、仅存尺寸规格）与**总督晋升徽章**（类别①，现行管线）不是同一件事。
3. 「领袖立绘」要分清：**类别④**是给 3D 引擎当纸片人的 `_TEXTURE`/`_OPACITY`（走 `Leaders.artdef`）；**类别⑤**是给 Suk 这类 2D 选人界面用的 `_Suk` UI 贴图（走 `UITexture` XLP）。两者同名前缀 `FALLBACK_NEUTRAL_*` 但**类别不同**，详见 `reference/ui-leader-portrait.md` §4.4。

**范围外的相邻任务**：png→dds/.tex 转换与素材导入 → `civ6-modding` 的 `art-pipeline.md`；
原版素材引用链查询/克隆（ArtDef/XLP 四层引用、cook 层排查）→ `civ6-art-reference`。

## 二、任务 → 类别路由

| 用户说要做什么 | 类别 | 去哪 |
|---------------|------|------|
| 「总督素材」「governor icon」「就职图标」「晋升徽章」「总督立绘」「立绘抠边/边缘透明渐变」 | ① 总督 | `reference/governor-art.md`；脚本 `scripts/build_icon_set.py`、`scripts/edge_gradient.py`、`scripts/verify_badge.py` |
| 「忠诚度图标」「忠诚度覆盖/压力」「战略视图忠诚度」「新增自定义宗教」「宗教压力图标」「宗教镜头覆盖」 | ② 忠诚度/宗教 | `reference/loyalty-icon.md`；脚本 `scripts/process_loyalty_icon.py`（`--kind loyalty` / `--kind religion`）、`scripts/gen_loyalty_art.py`、`scripts/gen_religion_art.py` |
| 「晋升图标」「promotion icon」「单位晋升」「白色图标合成」「盾形徽章」「五边形徽章」 | ③ 单位晋升<br>**（管线已废）** | 只查尺寸：`reference/promotion-icon-sizes.md`（**仅尺寸/格式规格，生成管线已废弃**）。**不要再照旧文档做图**；确需重做 → 走 `civ6-modding` 的 `art-pipeline.md` 通用图标管线 |
| 「2D 领袖」「立绘纸片人」「领袖注册链」「领袖 XLP/artdef/几何/材质/灯光」「1024 TEXTURE/OPACITY」 | ④ 2D 领袖 | `reference/leader-2d.md`；脚本 `scripts/gen_leader_2d.py`、`scripts/process_leader_png.py` |
| 「suk selection」「Sukritact」「Civ Selection Screen」「选人界面」「领袖选择界面」「PortraitBackground」「UILeaders.xlp」「UI 领袖立绘」「领袖选择背景」 | ⑤ UI 立绘/Suk | `reference/ui-leader-portrait.md`；脚本 `scripts/gen_suk_portrait.py`、`scripts/verify_suk_portrait.py` |
| 「历史时刻」「历史时刻插画」「时代得分图」「historic moment」「MomentIllustrations」「Moment_」「PrideMoments」 | ⑥ 历史时刻 | `reference/moment-illustration.md`；脚本 `scripts/apply_moment_template.py`、`scripts/verify_moment.py` |
| 「png → dds / .tex」转换、素材导入工程 | — | 不在本 skill：走 `civ6-modding` 的 `art-pipeline.md`（role 由类别决定，见第六节） |

**路由判定三条**：

1. 先判**对象**：总督 / 文明忠诚度 / 宗教 / 单位晋升 / 领袖（3D 纸片人）/ 领袖（UI 立绘）/ 历史时刻——"宗教"并入类别②（与忠诚度同一套引擎机制，仅命名映射与 artdef 目标集合不同）；"历史时刻"独立成类（走 `MomentIllustrations` 数据表 + `UI/PrideMoments` 贴图包，机制与其它四类都不同）。
2. 再判**产出层级**：只要 PNG 素材（合成层）还是连注册链（注册层）一起做。**注册层逻辑五类共用**（第六节），差别只在声明层文件名与目标集合。
3. 素材与注册链**都要**时：先出 PNG 交用户审核，审核通过后才做 DDS/.tex 与注册链（第七节）。

### 2.1 类别⑤ 的触发判定（先说清再动手）

用户提到 Suk / 选人界面相关词时，**先判定关联性再决定走哪条**：

| 关键词 | 判定 |
|---|---|
| `suk selection` / `Sukritact` / `Civ Selection Screen` / `选人界面` / `领袖选择界面` | **强关联** → 类别⑤ |
| `PortraitBackground` / `Players` 表的 `Portrait` 列 / `FALLBACK_NEUTRAL_*_Suk` | **强关联** → 类别⑤ |
| `领袖立绘` / `领袖选择背景`（**未**指明 Suk） | **弱关联** → 先问清是**原版界面**还是 **Suk 界面**：原版 3D 走类别④；Suk 2D 走类别⑤ |
| `加载界面`（`IMG_LOADING_*`） | **不关联**（`LoadingInfo` 表，另一条链） |

判定为类别⑤ 后，**先按第三节询问素材来源**（复用工程既有立绘+外交背景 / 用户提供），再动手。
完整规格、类别陷阱与验证顺序见 `reference/ui-leader-portrait.md`。

### 2.2 类别⑥ 的触发判定与素材询问

| 关键词 | 判定 |
|---|---|
| `历史时刻` / `历史时刻插画` / `时代得分图` / `historic moment` | **强关联** → 类别⑥ |
| `MomentIllustrations` / `Moment_*` / `PrideMoments` / `UI_PrideMoments.xlp` | **强关联** → 类别⑥ |
| `加载界面插画`（`IMG_LOADING_*`） | **不关联**（另一条链） |

判定为类别⑥ 后，**询问模板与源图**：

> 历史时刻插画需要**官方形状模板**套版（否则 UI 里卡片形状不对）。
>
> - **模板**：**已随 skill 内置** `templates/moment_illustration/1..18.psd`
>   （18 张官方形状；`4.psd` 是空的工作稿会自动跳过）——脚本默认就取这一份，无需再传路径。
>   要换成自己的模板时给 `--template-dir`（或写 `local_paths.json` 的 `moment_template_dir`）。
> - **源图**：每张成品插画的原图（PNG/PSD 导出均可，任意尺寸，脚本会缩放到 456×332）。
>   请给出目录或文件列表。
> - **模板选择**：指定编号（`--template N`）或让脚本按源图长宽比自动挑（`--auto`）。

> ⚠ **模板目录探测链**：内置 `templates/moment_illustration/` → `local_paths.json: moment_template_dir`
> → 作者机历史默认值 → 当前工作目录的 `模板/历史图片模板（新）/`；全都没有才报错。
> 若用户想自造蒙版，**不要凭猜**——先看清内置模板的图层语义
> （`python scripts/psd_inspect.py templates/moment_illustration --pick 1,4,18`：哪个是形状遮罩、哪个是描边），
> 再决定套哪一号模板。

## 三、铁律一：处理用户素材前必须先询问（五类共用）

**开始任何一类素材任务前，必须先询问用户是否提供素材**，得到答复后再动手。**默认只生成注册文件/注册链，不主动生成、不擅自处理素材**。

- 询问必须包含：**格式要求、尺寸要求、自动兜底方案、输出目录**四项，并给出「已有素材 / 暂无素材」两个选项。
- 每类的询问模板与素材要求（逐字原文）在对应 reference 文件里，**照用不要自己改写尺寸**：

| 类别 | 询问模板与素材要求位置 | 素材要求摘要 | 未提供时的默认行为 |
|------|----------------------|-------------|------------------|
| ① 总督 | `reference/governor-art.md`「目的 / 强制约定」 | 至少一张头像（另可给两张立绘做边缘渐变） | 不代生成素材，交付贴图规格与注册文件 |
| ② 忠诚度/宗教 | `reference/loyalty-icon.md` 第一节 | PNG/DDS、透明背景、≥256×256（512 更佳），定标基准 = alpha 质量集中区 | 自动从工程 `Textures/` 找**尺寸最大**的 `ICON_CIVILIZATION_*`（宗教分支找 `ICON_RELIGION_*`） |
| ④ 2D 领袖 | `reference/leader-2d.md` 第一节 | PNG、建议透明背景、尺寸近似 1:1 | **只生成注册文件**；`.tex` 的 `SourceFilePath` 指向占位路径，素材由用户后续导入 |
| ⑤ UI 立绘/Suk | `reference/ui-leader-portrait.md` 第三节 | 立绘：PNG 建议透明背景、近似 1:1；背景：建议 16:9（如 1920×1080） | **推荐复用工程既有素材**（`FALLBACK_NEUTRAL_*` 立绘 + `IMG_LEADER_*_DIPLOMACY_BACKGROUND` 外交背景），自动裁切缩放 |
| ⑥ 历史时刻 | `reference/moment-illustration.md` 第三节（官方形状模板）与第四节（制作流程 4.1/4.2） | 源图：每张插画的 PNG（任意尺寸）；**模板**：官方形状 PSD（`1..18.psd`） | 模板与源图都需用户提供；脚本负责套版、缩放、报告覆盖率 |

- 用户坚持用自己提供的模板/素材时，一律按其提供的路径走参数（如 `--glow`、`--icon`、`--avatar`、`--input`），不要替换成内置模板。
- 交付物中必须写明**实际用了哪个素材文件**（含自动兜底时选中的源文件路径）。

## 四、铁律二：不静默备份

**不静默备份。有 git 走 git；仅在用户明确要求时才另存副本。**

- 不做 `*.bak_*`、不做时间戳目录、不做"先拷一份再改"。
- 破坏性改动（覆盖/重写 `Art.xml`、`*.civ6proj`、artdef、xlp）前，先确认工程工作区已 commit，把历史交给 git。
- 可再生中间产物（合成图、临时 manifest/asset_map.json）用完即删，不留存。

## 五、铁律三：原版素材来源（只读 pantry，禁止解包）

*（原为类别① 总督 与 类别③ 单位晋升 共用的强制约定；③ 的生成管线已作废、原文不再保留，现仅类别① 适用）*

- **美术素材只允许在** `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` 内查找（各类 pantry 子路径见对应 reference）。
- **任何情况下不允许解包**（`.blp` 等打包文件不碰、不写解包器）；需要原版图就用 pantry 散装 DDS，用 **`civ6-modding` 的 texconv** 做纯格式转换
  （随包内置 `civ6-modding/art/bin/texconv.exe`，定位真源 `art/_texconv.py`：`TEXCONV` → 内置 → `PATH`
  → WinGet Links；探测链说明见 `civ6-modding/art/bin/README.md`）。
- 游戏安装目录只读 XML/Lua 数据定义，**不作素材来源**。
- 交付产物一律写到用户指定目录；**不修改游戏文件**。

## 六、注册链总览（五类共用链条）

```
用户/合成器产出 PNG（512/256/128/1024/24/32/64/206×208/326×339/内容定宽×1024 等）
        │  ① 审核通过后才进入下一步
        ▼
   DDS + .tex（civ6-modding art-pipeline：convert_art.ps1 / gen_tex.py；role 按类别选）
        │
        ▼
   声明层：xlp（条目包） + artdef（集合/槽位） + mtl（材质→贴图） + ast（行为资产）
        │
        ▼
   工程接线：*.Art.xml（artConsumers / gameLibraries / requiredGameArtIDs）
        │
        ▼
   打包清单：*.civ6proj 幂等补注册（Content Include；类别⑤ 另需 FrontEndAction + Criteria）
        │
        ▼
   ModBuddy 构建 → 进游戏开一局验证
```

### 6.1 五类的声明层落点

| 类别 | XLP | artdef | 材质/资产 | 其它 |
|------|-----|--------|----------|------|
| ① 总督 | `XLPs/Icons.xlp`（贴图加进去）+ `IconTextureAtlases` 图集 + `IconDefinitions` | — | — | `Governors` 表列（`Image` / `PortraitImage` / `PortraitImageSelected`） |
| ② 忠诚度/宗教 | `XLPs/UILensModels.xlp`、`XLPs/StrategicView_UILenses.xlp` | `ArtDefs/Overlay.artdef`、`ArtDefs/StrategicView.artdef` | `Materials/*_material.mtl`、`Assets/*_Box.ast` | 复用官方几何（Overlay `HexModelGeo` / Pressure `PipModelGeo`），不自建几何 |
| ④ 2D 领袖 | `XLPs/leader_{PACK}.xlp`、`XLPs/Leader_LightRigs.xlp` | `ArtDefs/Leaders.artdef` | `Geometries/*.geo`、`Materials/*.mtl`、`LightRigs/*.lrg`、`EnvironmentLights/*.env`、`Textures/*.tex`、`Assets/*.ast` | 每个领袖一套 6 类；聚合模板按领袖数复制块 |
| ⑤ UI 立绘/Suk | `XLPs/*.xlp`（**`m_ClassName=UITexture`** 的那一个，如 `UILeaders.xlp`） | — | `Textures/*_Suk.{dds,tex}`（`UserInterface`） | `Players` 表 `Portrait`/`PortraitBackground` 列 + **`FrontEndAction` 挂 `Criteria`**（未启用 Suk 时不加载） |
| ⑥ 历史时刻 | `UI_PrideMoments.xlp`（`m_ClassName=UITexture`，`PackageName=UI/PrideMoments`） | — | `Textures/Moment_*.{dds,tex}`（`UserInterface`，456×332） | `MomentIllustrations` 表（四列，`Texture` **带 `.dds` 后缀**） |

> 原类别③ 单位晋升图标的声明层落点已随管线作废**移出本节**；仅存的事实值
> （`IconTextureAtlases` `IconSize="32"` + `Icons_Promotions.xml` 的 `ICON_<UnitPromotionType>` 行）
> 见 `reference/promotion-icon-sizes.md` §六。

> 类别②「宗教分支」与忠诚度**同一套引擎机制**（同两个 XLP 包 + 同两个 artdef + 同一套官方几何/贴图类别约束），差别仅在命名映射与 artdef 目标集合（`ReligionLensIcons` / `ReligionLensArrows` 同名元素合并追加）。细节见 `reference/loyalty-icon.md` 第八节。

### 6.2 工程接线的五条共用规则

1. **`Materials/`、`Assets/`、`Textures/`、`Geometries/`、`LightRigs/`、`EnvironmentLights/` 构建时自动扫描**编译进 `Platforms\Windows\BLPs\*.blp`，**不需要**写进 `*.civ6proj` 清单。
2. **XLP / ArtDef 的构建接入点**：`.civ6proj` 的 `<Content>` 条目**不是**必需 —— 实测可运行工程（`示例工程`）的 `.civ6proj` 里 `.artdef` / `.xlp` 条目为 **0**，而其构建产物 `.modinfo` 自动收进全部 `.artdef`（`.xlp` 属 cook 输入，不进产物）。**真正必须的是第 3 条的 `.Art.xml`**。历史脚本（`gen_loyalty_art.py` / `gen_religion_art.py`）会**幂等补写** Content 条目，属可选冗余、写了不报错；civ6proj 可能有多个 `ItemGroup`，脚本统一插到最后一个 `</Content>` 之后，重复运行不产生重复条目。
3. **Art.xml 与 artdef/xlp 必须同步**：新增/修改 `XLPs\`、`ArtDefs\` 之后必须重新生成 `.Art.xml`——用
   `python <civ6-modding skill>\art\gen_modartxml.py <projectRoot> --check`，人工确认差异后加 `--write`（脚本按工程实存文件重算 artConsumers / gameLibraries / requiredGameArtIDs，优于手工补引用）。
4. **已存在的 artdef 不整体覆盖**：走脚本的幂等合并；脚本找不到锚点时必须报"请手动合并"，**不静默跳过**（防止覆盖工程里其他功能条目）。
5. **`.tex` 类别是硬约束**：类别写错时 cooker 报
   `has class: 'X', but is bound to parameter: 'Y' which does not accept this class`，且错误会沿"材质 → 资产 → XLP 条目"逐级传播、XLP cook 仍显示 "completed with success" 但条目已被替换成 error asset——**不能当成功处理**。各类正确类别见参考模板：
   - 3D 镜头贴图（忠诚度/宗教 `*_Overlay_*` / `*_Pressure_*`）→ `Generic_BaseColor`（`m_Tags` 留空）
   - 战略视图 sprite → `StrategicView_Sprite`（`m_Tags` 三连 `StrategicView_Sprite` / `StrategicView` / `Sprite`）
   - 带 alpha 的贴图 → `PF_R8G8B8A8_UNORM` + `bUseMips=false`（texconv 必须带 `-m 1`）；OPACITY 用单通道 `PF_R8_UNORM`
   - `gen_tex.py` 默认把 `m_ClassName` 写成 `UserInterface`，**出 `.tex` 后必须手工改类别**，可直接照抄 `templates/` 下的对应模板字段顺序
   - **UI 立绘 / 选人界面贴图 → `UserInterface`**（`m_Tags` 单条 `UserInterface`）。
     ⚠ `FALLBACK_NEUTRAL_{X}_Suk` 与 3D 回退贴图**同前缀但类别不同**：
     3D 回退是 `Leader_Fallback`（注册在 `LeaderFallbacks.xlp`），
     `_Suk` UI 立绘必须是 `UserInterface`（注册在 `UITexture` XLP）。
     `gen_tex.py` 的 `is_fallback()` 已显式排除 `_Suk`（`_UI_PORTRAIT_SUFFIXES`）；
     **新增同类 UI 后缀请往该常量里加**，不要再写前缀特例。详见 `reference/ui-leader-portrait.md` §4.4

### 6.3 素材搬运边界（避免污染工程 pantry）

- **不要为导入而把源 PNG 复制进工程**（`.assets` / `Textures`）：`.tex` 的 `SourceFilePath` 只在 AssetEditor 重新导入时用得到，**构建/游戏只读同名 DDS**，导入后删除源 PNG 不影响任何东西。
- manifest / `asset_map.json` 等临时工作文件用完即删。
- 素材（fgx/wig/环境光 dds/立绘 png）由用户提供时，复制后必须做**哈希校验**并在交付说明中列出结果。

## 七、通用验证顺序与校验脚本

五类共用同一顺序，**缺一不可**：

1. **合成后立刻跑本类的本地校验脚本**（数值判据，不依赖模型）：

| 类别 | 校验脚本 | 判据 |
|------|---------|------|
| ① 总督 | `python scripts/verify_badge.py <24px徽章.png> [官方对应格.png]`（官方对照格直接点名：`assets/TEMPLATE_badge24_canonical.png`，另有放大对照 `assets/TEMPLATE_badge24_canonical_x16.png` 与 8×1 总督晋升图集 `assets/REF_official_promotions24_x6.png`） | 有对照：轮廓 IoU ≥0.95（本管线实测 0.985）、逐行跨度一致性、逐行均色误差、P90 高光/P10 暗部对比，**跨度表零差异**；无对照：几何自洽（18 行、y=3..20、最宽 18px、左右居中） |
| ② 忠诚度/宗教 | 合成参数自检（`--fit-mode` / `--keep` / `--whiten-overlay`）+ 审核 PNG | 主体贴合官方光晕轮廓（定标细则见 `reference/loyalty-icon.md` 第六节第 1 条） |
| ④ 2D 领袖 | 生成文件清单自检（XML 可解析 / 无残留 `{占位符}` / 条目数 = 对象数 / 引用名与磁盘文件逐字符一致） | 完整 checklist 见 `reference/leader-2d.md` 第五节 |
| ⑤ UI 立绘/Suk | `python scripts/verify_suk_portrait.py --project <工程根>` | 类别必须是 `UserInterface`（**类别陷阱**）、`.tex` 宽高 == DDS 实际、贴图已被 `UITexture` XLP 登记、SQL 引用无悬空、行尾合规 |
| ⑥ 历史时刻 | `python scripts/verify_moment.py --project <工程根>` | **alpha 覆盖率 ≥75%**（原版 240 张最低 83%；漏套模板实测量到 14~15%）、456×332、类别 `UserInterface`、XLP 登记、`MomentIllustrations` 配对与 Texture 存在性 |

2. **视觉评审 / 人眼验收**：与原版对照检查轮廓、描边、高光、渐变、图形对比度。
   - 视觉评审不可用（模型侧 429 / 配额耗尽）时**不要反复重试**，改用本地像素度量 + 输出棋盘底预览图（`--checker` / `_preview.png`）给人眼验收。
3. **数值不达标时回退参数/模板**（改 `--keep`、`--feather` 等类别参数重生成），**不要手工修图**。
4. **审核通过后才做 DDS/.tex**（滞后步骤，走 `civ6-modding` art-pipeline；role 与 `.tex` 类别按第六节 6.2 第 5 条）。
   ⚠ **`.tex` 类别是本 skill 最大的静默坑**（类别与所绑 XLP 参数不匹配 → cooker 仍报 success，条目被换成 error asset）：
   交付前**必须**跑一遍 `civ6-modding` 的类别校验器
   `python <civ6-modding>/art/verify_tex_class.py --project <工程根>`（可加 `--full` 遍历全部 `UITexture` 包）——
   这是家族内**唯一**能机械拦住该类别的校验器；本 skill 的类别①~⑥ 校验表**都不覆盖** `.tex` 类别。
5. **工程构建 + 进游戏开一局验证**（3D 六边形/战略视图/图集实际显示）。
6. **上传/交付**：审核未通过前不得生成 DDS/.tex，不得提交 git。

> 常见"静默失败"：名字打错、引用名与定义名不逐字符一致时，游戏与 cooker **都不报错**，只是图标不显示。凡是 artdef 元素名 / XLP 条目名 / `ArtDefReferenceValue` 引用名，都必须逐字符核对（各类坑位清单见对应 reference）。

## 八、目录结构与本 skill 内文件归属

```
civ6-asset-forge/
├─ SKILL.md              ← 本文件：路由 + 五类共用链条（只写一份）
├─ CHANGELOG.md          ← 合并来源、各原仓库最后 commit、引用修正清单
├─ reference/
│   ├─ loyalty-icon.md          ← 类别② 全部类别专属内容（逐字）
│   ├─ promotion-icon-sizes.md  ← 原类别③：**仅尺寸/格式规格**（生成管线已作废）
│   ├─ governor-art.md          ← 类别①
│   ├─ leader-2d.md             ← 类别④
│   ├─ ui-leader-portrait.md    ← 类别⑤（Suk 选人界面适配）
│   ├─ moment-illustration.md   ← 类别⑥（历史时刻插画）
│   └─ governor-art/     ← 原 governor 的 specs.md / inventory.md / palette.json（实测规格、素材清单、配色）
├─ scripts/              ← 五类脚本合并（原 18 个，③ 的 5 个已随管线删除）
├─ templates/            ← 模板合集：loyalty_chain/、religion_chain/、**moment_illustration/（18 张官方形状 PSD + README）**、
│                            领袖模板 + 光晕模板（⑤ 无需模板）
└─ assets/               ← 素材合并（**仅总督官方对照图**：`TEMPLATE_badge24_canonical.png` / `_x16.png`、
                            `REF_official_promotions24_x6.png`；晋升模板/剪影样例已随管线删除；⑤⑥ 无需素材）
```

| 脚本 | 类别 | 说明 |
|------|------|------|
| `scripts/build_icon_set.py` | ① | 头像 → 24px 徽章 + 32/64px 图标 + 两种立绘尺寸 |
| `scripts/edge_gradient.py` | ① | 立绘边缘透明渐变（软 alpha + 去杂边 + OPACITY 遮罩） |
| `scripts/verify_badge.py` | ① | 24px 徽章几何/配色验证 |
| `scripts/process_loyalty_icon.py` | ② | 忠诚度 4 张 / 宗教 3 张 PNG 合成（`--kind`） |
| `scripts/gen_loyalty_art.py` | ② | 忠诚度注册链（XLP/ArtDef/mtl/ast + Art.xml + civ6proj 幂等补注册） |
| `scripts/gen_religion_art.py` | ② | 宗教注册链（同上机制，宗教命名映射） |
| `scripts/gen_leader_2d.py` | ④ | 全套领袖美术注册文件生成（读 `templates/` 模板） |
| `scripts/process_leader_png.py` | ④ | 立绘 PNG → 1024² TEXTURE/OPACITY（读 `templates/` 的两个 `.tex` 模板） |
| `scripts/gen_suk_portrait.py` | ⑤ | Suk 适配素材 + `UPDATE Players` + XLP + civ6proj 接线（幂等，`--check`/`--write`） |
| `scripts/verify_suk_portrait.py` | ⑤ | Suk 适配只读校验（类别陷阱 / 尺寸对齐 / XLP 登记 / 悬空引用 / 行尾） |
| `scripts/apply_moment_template.py` | ⑥ | 历史时刻插画套官方形状模板（`--list` / `--template N` / `--auto` / `--dds`；报告覆盖率对照 83~99%） |
| `scripts/verify_moment.py` | ⑥ | 历史时刻只读校验（**覆盖率下界** / 456×332 / 类别 / XLP / `MomentIllustrations` 配对） |

> `templates/` 与 `scripts/` **必须保持同级**：`process_loyalty_icon.py`（默认光晕模板 `templates/Loyalty_Overlay_Template.png`）、
> `gen_leader_2d.py`、`process_leader_png.py` 都按 `scripts/../templates` 定位模板。
> 类别⑤ 两个脚本按 `scripts/../../civ6-modding/art/dds_io.py` 复用 DDS 读写（单一真源）。

## 九、交付要求（五类共用）

- 交付说明必须包含：**生成文件清单（含尺寸/输出目录）**、**注册链文件清单**、`Art.xml` / `*.civ6proj` 改动说明、**"待用户审核 / 待 tex+dds / 待用户提供素材"清单**。
- 素材相关一律标注"待用户处理"，**除非用户明确要求代处理**。
- 素材未提供时，明确标注实际使用了哪个文件作为源（含自动兜底选中的源文件路径）。
- 处理过立绘/头像时，列出生成的 PNG 尺寸、`.tex` 更新结果、DDS 生成结果（或明确提示未生成）。
- **不静默备份**（第四节）：交付物里不应出现任何 `*.bak_*` / 时间戳副本 / `copy_*`。

---

## 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮
