---
name: civ6-asset-forge
description: "Civ6 美术素材**整理与导入** + 注册链一体化 skill（只做裁剪/通道透明度/描边等简单操作，不做图片处理工作流）：① 总督素材（governor icon / 就职图标 / 晋升徽章 / 头像 / 立绘 / 抠边）；② 忠诚度与宗教压力图标（Loyalty Overlay/Pressure + 战略视图 sprite）；③ 单位晋升图标（仅尺寸规格）；④ 2D 领袖立绘纸片人（完整美术注册链 + 1024 TEXTURE/OPACITY）；⑤ UI 领袖立绘与选人界面背景（Sukritact's Civ Selection Screen）；⑥ 历史时刻插画（MomentIllustrations 卡片）；⑦ 原版 FrontEnd 立绘·背景；⑧ 区域图标（官方模板底图 + 图案合成）；⑨ 领袖头像（ICON_LEADER_* 圆形头像：三分判定/占比定标/底图换色/出圈）；⑩ 资源图标（加成黄盘/奢侈紫盘底盘 + 纯图案合成，PS 自动化首选）。共用同一注册链机制（.dds/.tex → xlp/artdef/mtl/ast → Art.xml → .civ6proj 幂等补注册）与校验顺序；处理用户素材前必须先询问，默认只生成注册文件。边界：不含 3D 模型、UI 布局、2D UI 宗教图标、config；png→dds 转换走 civ6-modding 的 art-pipeline；总督八边形徽章与晋升五边形盾形不得混用。触发词：总督素材、governor icon、就职图标、总督徽章、总督立绘、边缘透明渐变、立绘抠边、忠诚度图标、宗教压力图标、自定义宗教注册、晋升图标、promotion icon、单位晋升、白色图标合成、盾形徽章、区域图标、district icon、District_Icon、区域图案、区域底图、2D 领袖、立绘纸片人、领袖美术注册链、suk selection、Sukritact、Civ Selection Screen、选人界面、领袖选择界面、PortraitBackground、UILeaders.xlp、UI 领袖立绘、领袖选择背景、原版选人界面、FrontEnd 立绘、FrontEnd 背景、加载界面背景、LoadingInfo、ForegroundImage、Shell_Loading.xlp、LEADER_NEUTRAL、领袖前景、借用原版背景、自动处理立绘、素材分类、人物抠图、满幅图、历史时刻、历史时刻插画、时代得分图、historic moment、MomentIllustrations、Moment_、PrideMoments、领袖发灰、领袖发糊、纸片滤镜、材质类、Leader_Matte、migrate_leader_matte、领袖头像、leader avatar、ICON_LEADER、头像底图、头像换色、资源图标、resource icon、ICON_RESOURCE、加成图标、奢侈图标、资源底盘、黄盘、紫盘。"
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

> 类别：① 总督 / ② 忠诚度·宗教 / ③ 单位晋升（**仅尺寸规格，无管线**）/ ④ 2D 领袖纸片人 /
> ⑤ Suk UI 立绘 / ⑥ 历史时刻插画 / ⑦ 原版 FrontEnd 立绘·背景 / ⑧ 区域图标 / ⑨ 领袖头像 /
> ⑩ 资源图标。
> 骨架共用：**给定成品 PNG** → 简单整理（总规则见 §1.0）→ 注册链 → 校验器；
> 注册链逻辑只在本文件维护一份，类别专属规格（尺寸/坐标/配色/参数）逐字保留在 `reference/*.md`。

## 〇、执行顺序（先读这一节，覆盖本文件其余全部内容）

每个任务按下面四步走，步与步之间不插入其它动作：

1. **路由**：按第二节的类别路由表定出本次任务所属类别，取出该类别的入口脚本。
2. **执行**：按路由表与对应 reference 给出的参数调用入口脚本。
3. **校验**：跑第七节校验表里本类别的校验脚本，再跑工程自己的校验入口（如 `python workspace/_tools/build.py check`）；入口脚本改了既有工程文件时，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径，脚本会在退出码 2 时打印待写入清单。
4. **交付**：按第九节报产物清单与校验退出码，并报 `<工程>/workspace/gen/` 待写入清单的处置结果。

**收敛条件是校验器的退出码。** 退出码为 0 即交付；非 0 就只改它列出的失败项，然后原样重跑，直到为 0。理解程度、与参照工程的相似程度、对照数据的整齐程度，都不作为收敛条件。

**顺序内的读取白名单**：本次要写入或改写的文件；入口脚本与校验脚本的参数所指向的文件；校验器报错时点名的那一个文件；用户在当前指令里点名的文件。白名单之外的读取（机理章节、勘误章节、兄弟工程对照、历史会话记录、游戏运行日志）**先说明要读哪个文件、用途是什么，得到用户许可再读**。

**询问的唯一条件见第三节**：素材无法认定，或素材缺失、规格不满足。除这两类情形外不向用户提问，也不以调研替代执行。

## 一、本 skill 覆盖的素材类别（边界先读）

### 1.0 总规则（占先，覆盖本 skill 全部内容）

> **本 skill 只做「整理与导入」，不是图片处理工作流。**
>
> 素材必须是**已经过预处理、基本符合要求**的成品。本 skill 对其只允许做
> **既有工具就能胜任的简单操作**：
>
> | 允许 | 例子 |
> |---|---|
> | **裁剪** | 定内容框、居中裁、按比例裁、缩放 |
> | **通道透明度** | alpha 阈值/二值化、读 alpha 边界、透明度遮罩 |
> | **描边** | 现成描边工具的输出 |
> | 上述的组合与非破坏性搬运 | 复制、改名、格式转换（PNG/DDS/`.tex`） |
>
> **禁止**：任何需要"把图改好"的复杂处理——重绘、修补、重着色、调色（levels / gamma /
> 亮度 / 对比度 / 饱和度 / 色相曲线）、去背景重构、超分/降噪/锐化、
> 生成式补图，以及"多试几组参数慢慢调"的迭代式修图。
>
> **遇到不满足上表的素材 → 停下询问用户**（不要自行尝试、不要"先试试看"），
> 由用户重新提供合规素材，或明确授权某一步。
>
> 需要真正的图片处理能力时，本 skill **不承接**：交回用户/外部工具，处理完再回来导入。
>
> **例外（类别⑨ 领袖头像）**：底图换色按 `reference/leader-avatar.md` 的规则执行
> （仅底图层：色相 → 角色主色相、饱和度钳制 0.05~0.28、明度逐像素保留），不视为重绘；
> 主体像素仍然一概不动。

| 类别 | 解决的"做什么素材" | 主要产出 | **不做什么** |
|------|------------------|---------|-------------|
| 总督素材<br>`reference/governor-art.md` | 总督头像/徽章/立绘（含立绘边缘透明渐变、抠边） | 24px 就职/晋升徽章、32/64px 头像图标、206×208 常态立绘、326×339 选中立绘、软边 1024² TEXTURE/OPACITY | 不做 3D 总督模型；不做城市横幅滴的 UI 布局改动（只出贴图）；不改 `GovernorPanel.lua` 图标查找逻辑 |
| 忠诚度 / 宗教压力图标<br>`reference/loyalty-icon.md` | 文明忠诚度图标、宗教压力图标、新增自定义宗教 | 每文明 4 张 PNG（3D 覆盖/压力 + 战略视图覆盖/压力）、每宗教 3 张 PNG + 完整 UILens 注册链 | 不处理 2D UI 宗教图标（`IconTextureAtlases` 270px 图集，数据路径）→ **真实落点在 `civ6-modding/art-pipeline.md` 的图标规范化一节**（注意"同名重复注册会静默劫持图标"）；不处理立绘 |
| 2D 领袖<br>`reference/leader-2d.md` | **可选扩展**：2D 领袖立绘纸片人（全套注册链）、1024×1024 TEXTURE/OPACITY；**必须步骤**：外交回退立绘 `FALLBACK_NEUTRAL_*`（见 `reference/leader-diplo-fallback.md`） | XLP 包 / `Leaders.artdef` / 几何 / 材质 / `.tex` / 行为资产 ast / **灯光链（LightRigs + EnvironmentLights + Leader_LightRigs.xlp）** | 不生成素材（用户未提供时只出注册文件）；不做 config（领袖互斥/同名，见项目 `DuplicateLeaders`）。**材质类必须是 `Leader_Matte`（平面类），误用 `Leader`（PBR 人物类）会导致纸片发灰+发糊，见 §3.5 与 `migrate_leader_matte.py`**；**灯光链必须随工程自带、artdef 的 Lightrig 槽指本工程灯光，缺本地 `leaders/light_rigs` 包会渲染成零星色块，见 §3.6**；**两个 `.tex` 必须最高品质（色度降采样会致发糊+色差），见 §3.6** |
| **UI 领袖立绘 / 选人界面背景**<br>`reference/ui-leader-portrait.md` | **Sukritact's Civ Selection Screen** 选人界面的 2D 立绘（`Players.Portrait`）与背景（`Players.PortraitBackground`） | 每领袖 2 张 `_Suk` 贴图（立绘 = 峰值列对齐 `--peak-frac`（默认 0.70）、外交立绘保持原尺寸；背景 = 外交背景中心裁 1440×1080）+ `UPDATE Players` + XLP + `Criteria` 接线 | 不做 3D 纸片人注册链（→ 类别④）；不负责 Suk mod 本体分发；不处理加载界面（`IMG_LOADING_*` / `LoadingInfo`，另一条链） |
| **历史时刻插画**<br>`reference/moment-illustration.md` | **`MomentIllustrations`** 的插画卡片（特色单位/区域/建筑/改良/总督的时刻图） | 每张 **456×332** 贴图（套 **18 张官方形状模板**之一）+ `UI_PrideMoments.xlp` 登记 + `MomentIllustrations` 行 | 不新增 `MomentIllustrationType`（属玩法侧表级改动）；不做 `Moments` 表（时刻本体）；不处理非历史时刻的其它 UI 图 |
| **原版 FrontEnd 立绘 / 背景**<br>`reference/frontend-portrait.md` | **原版环境**下领袖的**前景（立绘）与背景**：FrontEnd 选人 placard（`Players`）+ 加载界面（`LoadingInfo`） | 前景（**1080×1080**，主体高 882、顶部留空 198，`LEADER_<X>_NEUTRAL` 约定）+ 背景（竖版 **328×935** 自建，或别名复用原版 `LEADER_<X>_BACKGROUND`）+ XLP 登记 + `Players`/`LoadingInfo` 行 | 不做外交场景（→ `civ6-modding/art-pipeline.md` §三.1）；不做 3D 纸片人（→ 类别④）；Suk 分支另见类别⑤ |
| **区域图标**<br>`reference/district-icon.md` | 区域（District）图标母版：官方 PSD 模板底图 + 白色图案素材 → 256×256 六边形图标；**构图唯一来源**是 `build_district_icon.fit_pattern`，两引擎共用 | 每区域 1 张 256×256 PNG（区域主题色渐变图案 + 边框） | 不做 PNG→DDS 与 `IconTextureAtlases` 注册（审核通过后 → `civ6-modding/art-pipeline.md`）；不做城市横幅内的小尺寸切图 |
| **资源图标**<br>`reference/resource-icon.md` | 资源（Resource）图标单元格：**已内置**的加成黄盘/奢侈紫盘底盘 + 纯图案素材 → 256×256 RGBA 单元格；**构图唯一来源**是 `build_resource_icon.place_pattern`（裁剪 → 等比缩放 → 居中 → 预乘重采样 → 输出空间等宽黑边），两引擎共用 | 每个资源 1 张 256×256 PNG（图案 + 黑边 + 类别底盘） | 不做 PNG→DDS 与 `IconTextureAtlases` 注册（审核通过后 → `civ6-modding/art-pipeline.md`）；不做无底盘的裸图案单元格；不重复加黑边（素材自带时用 `--no-stroke`） |
| **领袖头像**<br>`reference/leader-avatar.md` | 领袖圆形头像 `ICON_LEADER_*` 素材整备：三分判定（合规直通/仅缩放/Icon 制作）+ 占比定标 + 底图换色 + 出圈 | 每素材 256 规范成品 + 300 等比版 + 换色底图 + 锚点证据图 + metrics（注册走 `leader_icon` 8 尺寸） | 不做注册链与 DDS（→ art-pipeline）；满幅复杂背景不承接抠图；不做 3D 纸片人与 FrontEnd 立绘；高耸头饰超画布物理空间时如实报告不自动缩小 |

> ⚠ **类别③ 单位晋升图标：本 skill 只有尺寸与格式规格**（`reference/promotion-icon-sizes.md`），
> 无生成管线、无模板、无脚本。确需做图 → 走 `civ6-modding` 的 `art-pipeline.md` 通用图标管线。

**四条最容易踩的混用**：

1. 总督 24px 徽章是**八边形**（上下切角），单位晋升是**五边形盾形**——两者规格、配色、图集完全是两套，**禁止互相套用**（详见 `reference/governor-art/specs.md` §2.3「与单位晋升的区别」、`reference/governor-art.md`「边界」节，与 `reference/promotion-icon-sizes.md` 的盾形轮廓表）。
2. 「晋升」一词要分清：**单位晋升**（类别③，仅存尺寸规格）与**总督晋升徽章**（类别①）不是同一件事。
3. 「领袖立绘」要分清**四种**东西（这四种都叫"领袖立绘"但互不相同）：
   - **类别④**：给 3D 引擎当纸片人的 `_TEXTURE`/`_OPACITY`（走 `Leaders.artdef`）；
   - **类别⑤（Suk，可选分支）**：给 Suk 这类第三方 2D 选人界面用的 `SUK_UI_*`（走 `UITexture` XLP，`Criteria` 门控）；
   - **类别⑦ 前景（原版，必需）**：`Players.Portrait`（空则回退 `<LeaderType>_NEUTRAL`），走 `UILeaders.xlp`；
   - **类别⑦ 背景（原版，必需）**：`Players.PortraitBackground`（竖版 **328×935**）+ 加载界面的
     `LoadingInfo.BackgroundImage`（**1920×960**，走 `Shell_Loading.xlp`）。
   `FALLBACK_NEUTRAL_*` 属**类别④ 的 3D 回退**（`Leader_Fallback` 类），与类别⑦的 `LEADER_*_NEUTRAL` **不是同一批**。
   命名陷阱详见 `reference/ui-leader-portrait.md` §4.4；三环境对照见 `reference/frontend-portrait.md` §〇。

4. **Suk 是可选分支、原版 FrontEnd 是必需**：Suk 只在启用时改写 `Players` 两列；
   未启用 Suk 时走的是**类别⑦**那一套。**只做 Suk 会导致原版界面空白**（`Portrait` 留空 →
   回退到不存在的 `<LeaderType>_NEUTRAL`，前端不报错）。两套都要能跑。

**范围外的相邻任务**：png→dds/.tex 转换与素材导入 → `civ6-modding` 的 `art-pipeline.md`；
原版素材引用链查询/克隆（ArtDef/XLP 四层引用、cook 层排查）→ `civ6-art-reference`。

## 二、任务 → 类别路由

| 用户说要做什么 | 类别 | 去哪 |
|---------------|------|------|
| 「总督素材」「governor icon」「就职图标」「晋升徽章」「总督立绘」「立绘抠边/边缘透明渐变」 | ① 总督 | `reference/governor-art.md`；脚本 `scripts/build_icon_set.py`、`scripts/edge_gradient.py`、`scripts/verify_badge.py` |
| 「忠诚度图标」「忠诚度覆盖/压力」「战略视图忠诚度」「新增自定义宗教」「宗教压力图标」「宗教镜头覆盖」 | ② 忠诚度/宗教 | `reference/loyalty-icon.md`；脚本 `scripts/process_loyalty_icon.py`（`--kind loyalty` / `--kind religion`）、`scripts/gen_loyalty_art.py`、`scripts/gen_religion_art.py` |
| 「晋升图标」「promotion icon」「单位晋升」「白色图标合成」「盾形徽章」「五边形徽章」 | ③ 单位晋升<br>**（管线已废）** | 只查尺寸：`reference/promotion-icon-sizes.md`（**仅尺寸/格式规格，生成管线已废弃**）。**不要再照旧文档做图**；确需重做 → 走 `civ6-modding` 的 `art-pipeline.md` 通用图标管线 |
| 「2D 领袖」「立绘纸片人」「领袖注册链」「领袖 XLP/artdef/几何/材质/灯光」「1024 TEXTURE/OPACITY」「领袖发灰/发糊/像蒙了滤镜」「纸片模糊/不够清晰」「领袖材质类」「纸片色差/边缘洇色」「LightRig/环境光要不要做」 | ④ 2D 领袖 | `reference/leader-2d.md`（**材质类铁律 §3.5 / 灯光与贴图品质铁律 §3.6**）；脚本 `scripts/gen_leader_2d.py`、`scripts/process_leader_png.py`、`scripts/migrate_leader_matte.py`（存量工程 `Leader`→`Leader_Matte` 体检/迁移） |
| 「suk selection」「Sukritact」「Civ Selection Screen」「选人界面」「领袖选择界面」「PortraitBackground」「UILeaders.xlp」「UI 领袖立绘」「领袖选择背景」 | ⑤ UI 立绘/Suk | `reference/ui-leader-portrait.md`；脚本 `scripts/gen_suk_portrait.py`、`scripts/verify_suk_portrait.py` |
| 「历史时刻」「历史时刻插画」「时代得分图」「historic moment」「MomentIllustrations」「Moment_」「PrideMoments」 | ⑥ 历史时刻 | `reference/moment-illustration.md`；脚本 `scripts/apply_moment_template.py`、`scripts/verify_moment.py` |
| 「原版选人界面」「FrontEnd 立绘/背景」「加载界面背景」「LoadingInfo」「ForegroundImage」「Shell_Loading.xlp」「领袖前景」「借用原版背景」「给我一张图自动做领袖立绘/背景」 | ⑦ 原版 FrontEnd | `reference/frontend-portrait.md`；脚本 `scripts/prepare_frontend_portrait.py`（自动分类+处理）、`scripts/verify_frontend_portrait.py`（校验）、`scripts/pick_vanilla_background.py`（挑官方背景） |
| 「区域图标」「district icon」「District_Icon」「区域图案」「区域底图」 | ⑧ 区域图标 | **先做入口判定**（快速检查素材：已含六边形边框等官方区域图标显著特征的成品图**不进入**本流程——本流程只接受纯图案素材，六边形底图与边框由官方模板提供）；判定通过 → **默认跑 `scripts/ps_place_district.py`（PS 自动化，效果最好；导入前先用 `build_district_icon.pattern_canvas` 按落位框完成构图）**，exit 4（本机无 Photoshop）时询问用户改走模拟引擎 `scripts/build_district_icon.py` 还是安装 PS，不静默降级；规格见 `reference/district-icon.md` |
| 「领袖头像」「leader avatar」「ICON_LEADER」「头像底图」「头像换色」 | ⑨ 领袖头像 | `reference/leader-avatar.md`；脚本 `scripts/prepare_leader_avatar.py`（判定+占比定标合成+底图换色；锚点 JSON 由 AI 视觉定位提供；`--passthrough` 直通） |
| 「资源图标」「resource icon」「ICON_RESOURCE」「加成图标」「奢侈图标」「资源底盘」「黄盘」「紫盘」 | ⑩ 资源图标 | **先做入口判定**（快速检查素材：已含黄盘/紫盘/圆环等底盘特征的成品图**不进入**本流程——本流程只接受纯图案素材，底盘由本 skill 内置）；判定通过 → **默认跑 `scripts/ps_place_resource.py`（PS 自动化，效果最好；导入前先用 `build_resource_icon.place_pattern` 按落位框完成构图）**，exit 4（PS 自动化通道不可用：缺 pywin32 模块，或 `Photoshop.Application` 连不上）时询问用户改走无 PS 引擎 `scripts/build_resource_icon.py` 还是补齐缺口后重跑，不静默降级；规格见 `reference/resource-icon.md` |
| 「png → dds / .tex」转换、素材导入工程 | — | 不在本 skill：走 `civ6-modding` 的 `art-pipeline.md`（role 由类别决定，见第六节） |

**路由判定三条**：

1. 先判**对象**：总督 / 文明忠诚度 / 宗教 / 单位晋升 / 领袖（3D 纸片人）/ 领袖（原版 FrontEnd 立绘·背景）/ 领袖（Suk UI 立绘）/ 历史时刻 / 区域图标 / 领袖（圆形头像）/ 资源——"宗教"并入类别②（与忠诚度同一套引擎机制，仅命名映射与 artdef 目标集合不同）；"历史时刻"独立成类（走 `MomentIllustrations` 数据表 + `UI/PrideMoments` 贴图包，机制与其它四类都不同）。
2. 再判**产出层级**：只要 PNG 素材（合成层）还是连注册链（注册层）一起做。**注册层逻辑各类共用**（第六节），差别只在声明层文件名与目标集合。
3. 素材与注册链**都要**时：先出 PNG 交用户审核，审核通过后才做 DDS/.tex 与注册链（第七节）。

### 2.1 类别⑤ 的触发判定（先说清再动手）

用户提到 Suk / 选人界面相关词时，**先判定关联性再决定走哪条**：

| 关键词 | 判定 |
|---|---|
| `suk selection` / `Sukritact` / `Civ Selection Screen` / `选人界面` / `领袖选择界面` | **强关联** → 类别⑤ |
| `PortraitBackground` / `Players` 表的 `Portrait` 列 / `SUK_UI_*`（旧名 `FALLBACK_NEUTRAL_*_Suk`） | **强关联** → 类别⑤ |
| `领袖立绘` / `领袖选择背景`（**未**指明 Suk） | **弱关联** → 先问清是**原版界面**还是 **Suk 界面**：原版 3D 走类别④；原版 2D placard 走**类别⑦**；Suk 2D 走类别⑤。★ **原版 FrontEnd 是必需、Suk 是可选分支**，不要只做 Suk |
| `加载界面`（`IMG_LOADING_*` / `LoadingInfo` / `ForegroundImage`） | **关联** → **类别⑦** `reference/frontend-portrait.md` §二（此前被误判为"不关联"，导致该链无人承接） |

判定为类别⑤ 后，按第三节的询问条件处理素材来源（素材路径已知就用它；未知或缺失才问）。本类**默认复用工程既有素材**（既有立绘 + 外交背景），无需询问。
完整规格、类别陷阱与验证顺序见 `reference/ui-leader-portrait.md`。

### 2.2 类别⑥ 的触发判定与素材来源

| 关键词 | 判定 |
|---|---|
| `历史时刻` / `历史时刻插画` / `时代得分图` / `historic moment` | **强关联** → 类别⑥ |
| `MomentIllustrations` / `Moment_*` / `PrideMoments` / `UI_PrideMoments.xlp` | **强关联** → 类别⑥ |
| `加载界面插画`（`IMG_LOADING_*`） | **不关联**（另一条链） |

判定为类别⑥ 后，模板已随包内置、无需询问；**只在源图路径未知或缺失时按第三节询问源图**：

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

## 三、铁律一：询问的唯一条件（各类共用）

**只有下列两类情形才向用户提问，提问只覆盖这两点：**

1. **素材无法认定**：候选多于一份，或者来源路径不明。
2. **素材缺失**，或者规格不满足本 skill 写明的输入要求（尺寸、透明通道、长宽比例）。

**素材的认定以工程 `AGENTS.md`「美术与音频资产」表的「来源」列为准**：该列写明源文件时直接使用，不提问；该列未写明、或与磁盘实存文件不符时才提问。

提问一次问清，拿到答复后直接执行。**反推源文件、比对候选、按像素差寻找匹配、逐工程对照，这些动作不出现**——它们既不是流程步骤，也不产生任何交付物。

- 除上面两类情形外，**不向用户提问，也不以调研替代执行**；流程能跑完就先跑完。
- 已知素材齐备的任务（例如用户说"重新生成已有的贴图"）直接进入执行步骤，不做素材询问。
- 每类的素材要求与默认行为（逐字原文）在对应 reference 文件里，**照用不要自己改写尺寸**：

| 类别 | 素材要求位置 | 素材要求摘要 | 素材缺失时的默认行为 |
|------|------------|-------------|------------------|
| ① 总督 | `reference/governor-art.md`「目的 / 强制约定」 | 至少一张头像（另可给两张立绘做边缘渐变） | 不代生成素材，交付贴图规格与注册文件 |
| ② 忠诚度/宗教 | `reference/loyalty-icon.md` 第一节 | PNG/DDS、透明背景、≥256×256（512 更佳），定标基准 = alpha 质量集中区 | 自动从工程 `Textures/` 找**尺寸最大**的 `ICON_CIVILIZATION_*`（宗教分支找 `ICON_RELIGION_*`） |
| ④ 2D 领袖 | `reference/leader-2d.md` 第一节 | PNG、建议透明背景、尺寸近似 1:1 | **只生成注册文件**；`.tex` 的 `SourceFilePath` 指向占位路径，素材由用户后续导入 |
| ⑤ UI 立绘/Suk | `reference/ui-leader-portrait.md` 第三节 | 立绘：PNG 建议透明背景、近似 1:1；背景：建议 16:9（如 1920×1080） | **推荐复用工程既有素材**（`FALLBACK_NEUTRAL_*` 立绘 + `IMG_LEADER_*_DIPLOMACY_BACKGROUND` 外交背景），自动裁切缩放 |
| ⑥ 历史时刻 | `reference/moment-illustration.md` 第三节（官方形状模板）与第四节（制作流程 4.1/4.2） | 源图：每张插画的 PNG（任意尺寸）；**模板**：官方形状 PSD（`1..18.psd`） | 模板与源图都需用户提供；脚本负责套版、缩放、报告覆盖率 |
| ⑧ 区域图标 | `reference/district-icon.md` 第一、二节 | 模板：**已内置** `templates/district_icon/`；图案：白色/浅色 PNG（带透明通道或近纯色背景，纯黑白素材走亮度映射路径） | 只需用户提供图案素材路径；脚本负责删背景、主体裁剪、单步重采样、质心对齐与逐区域合成（细节原样进入成品，不做锐化/降噪/形态学加工） |
| ⑩ 资源图标 | `reference/resource-icon.md` 第一、二、三节 | 图案：纯图案 PNG（自带透明通道；**不要自带黑边**，黑边由脚本按原版规格加）；底盘：**已内置** `assets/TEMPLATE_resource_plate_*.png`；类别以 `Data/Resources_RGN.sql` 的 `ResourceClassType` 为准 | 只需用户提供图案素材路径；脚本负责图案黑边、内容包围盒裁剪、等比缩放、居中、预乘 alpha 重采样与底盘合成 |
| ⑨ 领袖头像 | `reference/leader-avatar.md`「锚点采集」 | 透明抠图或圆形成品 PNG；锚点 JSON（L/R/lip/chin/crown/shoulder）由 AI 视觉定位 + 肤色核验提供 | 满幅复杂背景 exit 2 停下询问；圆形成品走 `--passthrough` 直通 |

- 用户坚持用自己提供的模板/素材时，一律按其提供的路径走参数（如 `--glow`、`--icon`、`--avatar`、`--input`），不要替换成内置模板。
- 交付物中必须写明**实际用了哪个素材文件**（含自动回退时选中的源文件路径）。

## 四、铁律二：不静默备份

**不静默备份。有 git 走 git；仅在用户明确要求时才另存副本。**

- 不做 `*.bak_*`、不做时间戳目录、不做"先拷一份再改"。
- 破坏性改动（覆盖/重写 `Art.xml`、`*.civ6proj`、artdef、xlp）前，先确认工程工作区已 commit，把历史交给 git。
- 可再生中间产物（合成图、临时 manifest/asset_map.json）用完即删，不留存。

## 五、铁律三：原版素材来源（只读 pantry）

- **美术素材只允许在** `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` 内查找（各类 pantry 子路径见对应 reference）。
- 需要原版图就用 pantry 散装 DDS，用 **`civ6-modding` 的 texconv** 做纯格式转换
  （随包内置 `civ6-modding/art/bin/texconv.exe`，定位真源 `art/_texconv.py`：`TEXCONV` → 内置 → `PATH`
  → WinGet Links；探测链说明见 `civ6-modding/art/bin/README.md`）。
- 游戏安装目录只读 XML/Lua 数据定义，**不作素材来源**。
- 交付产物一律写到用户指定目录；**不修改游戏文件**。

## 五bis、铁律四：2D 纸片人（类别④）是可选扩展；外交回退立绘（fallback）才是必须步骤

**外交回退立绘（`FALLBACK_NEUTRAL_*`，`Leader_Fallback` 类）是每位领袖必须制作的根本步骤**，
无论领袖有没有外交语音、是否进入纸片模型分支，都必须制作——外交场景里纸片模型缺失或未加载时，
引擎回退显示的就是它。注册链见 `reference/leader-diplo-fallback.md`。

**类别④（2D 领袖立绘纸片人）是可选扩展，唯一判定依据 = 该领袖有没有「外交语音」。**

**纸片人判定门（三步，任一不通过即不生成纸片模型，但 fallback 仍必须制作）**：

1. **工程 `Platforms/` 下没有音频目录/文件 → 直接跳过**（无音频 = 无外交语音）。
2. 素材里**没有明确的外交语音** → 不触发。
3. 查 **Speech bank**（如 `Platforms/Windows/Audio/*_Speech.txt`）的事件名，
   命中任一**外交槽位**关键字才算「有外交语音」：
   `FIRST_MEET` / `DECLARE_WAR_FROM_HUMAN` / `DECLARE_WAR_FROM_AI` /
   `KUDO_EXIT` / `WARNING_EXIT` / `DEFEAT_FROM_AI`

> ⚠ **`QUOTE` 不算外交语音。** `QuoteAudio` / `LeaderQuotes` 有值也**不**触发纸片人——
> quote 只用于加载界面与百科，不进外交场景。

**命中 → 生成纸片模型**：`Leaders.artdef` + Geometries / Materials / `Assets/*.ast` /
leader XLP 全套；**未命中 → 纸片模型不生成**，但外交回退立绘
（`FALLBACK_NEUTRAL_*`，走 `reference/leader-diplo-fallback.md`）与 2D 立绘
（`IMG_LOADING_FOREGROUND_*` 等）仍必须制作。

> ⚠ **灯光链随工程自带，三处齐备**：`LightRigs/{Name}_LightRig.lrg`、
> `EnvironmentLights/{Name}_Environment.env` + `.dds`、`XLPs/Leader_LightRigs.xlp`；
> `Leaders.artdef` 的 Lightrig 槽写本工程的 `LEADER_<KEY>_LightRig`，且 `.Art.xml` 的
> `LeaderLighting` 库 `relativePackagePaths` 写 `leaders/light_rigs`。
> Lightrig 槽指 `ART_DEFAULT_LIGHT` 而工程内没有本地 `leaders/light_rigs` 包时，
> 纸片人在外交场景渲染成零星色块。
> 规格、命名与接线见 `reference/leader-2d.md` §3.6。

**`.ast` 与 `Leaders.artdef` 必须同进同退**：ast 只有 6 个外交槽位
（`01_FIRST_MEET` … `06_DEFEAT` + `NEUTRAL_POSITIVE_A`），没有外交语音时 ast 的 `m_FXName`
全是空引用 —— 整条纸片人链失去唯一用途。

> ⚠ **判定必须看 `Speech.bnk`，不是 `Voice.bnk`。** `Voice.bnk` 装的是游戏内 SFX
> （如 `Play_RGN_CTTH_SLASH_A`，挂 `Voice_Mixer`），**不构成外交语音**；外交语音在
> `Speech.bnk`（挂 `LeaderSpeech_*`）。

**音频导入流程的钩子**：`civ6-audio-pipeline` 处理到领袖外交语音时，应检查该领袖是否已有
3D 纸片人；若没有，询问用户是否补上，并完善 `.ast` 的音频引用（`m_FXName`）。

## 五ter、改动面由动词决定（防止把任务做宽）

用户指令的动词决定改动面，**越界的部分一律不做**：

| 指令形态 | 改动面 | 明确不动的 |
|---|---|---|
| 「重新生成……图片」 | 重跑该类别的素材脚本，产出图片与对应的 `.tex`、`.dds` | 注册链、cook 参数、材质类、几何定义 |
| 「重新导入并 cook」 | 重跑素材脚本，再跑工程的构建入口（如 `build.py stage`） | 注册链文件 |
| 「显示异常」「显示缺失」 | 按本类 reference 的排查条目逐条走 | 条目之外的链路 |
| 「新增……素材」 | 该类别的完整流程（素材 → 注册链 → 校验） | — |

**上一次会话没有结案的问题，不随新任务自动展开。** 只有当用户在当前指令里点名该问题时，才进入对应流程；读到历史记录、旧日志、旧诊断脚本时按第七节白名单处理（先问再读）。

**执行受阻时就地停下，把错误原文与可用于续跑的命令报给用户**，不绕道、不换工具试第二次、不为了绕开某个环境限制而改写做法。

## 五quater、工程文件写入铁律

脚本可以**新建**工程文件，绝不允许**改写**工程文件；既有工程文件的每一次改动由 AI 用文件编辑工具完成。
判据、`workspace/gen/` 落点、可再生二进制资产的例外、六份 `_projwrite.py` 副本，全部以 [`civ6-modding/SKILL.md`](../civ6-modding/SKILL.md) 的「工程文件写入铁律」为唯一真源。

本 skill 的落点：`gen_leader_2d.py`、`gen_loyalty_art.py`、`gen_religion_art.py`、`gen_suk_portrait.py`、`prepare_frontend_portrait.py`、`pick_vanilla_background.py`、`process_leader_png.py`、`migrate_suk_namespace.py` 的工程写入全部经过 `scripts/_projwrite.py`；`.civ6proj`、`*.Art.xml`、`.xlp`、`.artdef`、`.sql`、`.lua` 已有内容有变化时一律入位 `workspace/gen/`，脚本不覆盖。

## 六、注册链总览（各类共用链条）

```
用户/合成器产出 PNG（512/256/128/1024/24/32/64/206×208/326×339/峰值列对齐 70%×原尺寸等）
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
   打包清单：*.civ6proj 补 Content Include 条目（补好的 .civ6proj 落 workspace/gen/，由 AI 写入工程；类别⑤ 另需 FrontEndAction + Criteria）
        │
        ▼
   ModBuddy 构建 → 进游戏开一局验证
```

### 6.1 各类的声明层落点

| 类别 | XLP | artdef | 材质/资产 | 其它 |
|------|-----|--------|----------|------|
| ① 总督 | `XLPs/Icons.xlp`（贴图加进去）+ `IconTextureAtlases` 图集 + `IconDefinitions` | — | — | `Governors` 表列（`Image` / `PortraitImage` / `PortraitImageSelected`） |
| ② 忠诚度/宗教 | `XLPs/UILensModels.xlp`、`XLPs/StrategicView_UILenses.xlp` | `ArtDefs/Overlay.artdef`、`ArtDefs/StrategicView.artdef` | `Materials/*_material.mtl`、`Assets/*_Box.ast` | 复用官方几何（Overlay `HexModelGeo` / Pressure `PipModelGeo`），不自建几何 |
| ④ 2D 领袖 | `XLPs/leader_{PACK}.xlp` + `XLPs/Leader_LightRigs.xlp` | `ArtDefs/Leaders.artdef`（Lightrig 槽 = `LEADER_<KEY>_LightRig`） | `Geometries/*.geo`、`Materials/*.mtl`、`Textures/*.tex`、`Assets/*.ast`、`LightRigs/*.lrg`、`EnvironmentLights/*.env` + `*.dds` | 每个领袖 6 类；聚合模板按领袖数复制块；灯光文件与几何/材质一样由构建自动扫描进 BLP |
| ⑤ UI 立绘/Suk | `XLPs/*.xlp`（**`m_ClassName=UITexture`** 的那一个，如 `UILeaders.xlp`） | — | `Textures/SUK_UI_*.{dds,tex}`（`UserInterface`） | `Players` 表 `Portrait`/`PortraitBackground` 列 + **`FrontEndAction` 挂 `Criteria`**（未启用 Suk 时不加载） |
| ⑥ 历史时刻 | `UI_PrideMoments.xlp`（`m_ClassName=UITexture`，`PackageName=UI/PrideMoments`） | — | `Textures/Moment_*.{dds,tex}`（`UserInterface`，456×332） | `MomentIllustrations` 表（四列，`Texture` **带 `.dds` 后缀**） |
| ⑦ 原版 FrontEnd | `UILeaders.xlp`（前景 + 竖版背景）、`Shell_Loading.xlp`（加载界面背景）——**两者均 `UITexture`** | — | `Textures/*.{dds,tex}`（`UserInterface`） | `Players.Portrait/PortraitBackground`（**Config 库 → FrontEndActions**）+ `LoadingInfo.ForegroundImage/BackgroundImage`（**Gameplay 库 → InGameActions**）；可走 XLP **别名**复用官方贴图 |
| ⑩ 资源图标 | `XLPs/Icons.xlp`（`m_ClassName=UITexture`） | — | `Textures/RGN_Icon_Resources*.{dds,tex}`（`UserInterface`，未压缩 `R8G8B8A8_UNORM`、`mips=1`） | `IconTextureAtlases` 一档一行（32/38/50/64/256 + FOW 256）+ `IconDefinitions` 一格一行 |

> 类别③ 的声明层事实值（`IconTextureAtlases` `IconSize="32"` +
> `Icons_Promotions.xml` 的 `ICON_<UnitPromotionType>` 行）见 `reference/promotion-icon-sizes.md` §六。

> 类别②「宗教分支」与忠诚度**同一套引擎机制**（同两个 XLP 包 + 同两个 artdef + 同一套官方几何/贴图类别约束），差别仅在命名映射与 artdef 目标集合（`ReligionLensIcons` / `ReligionLensArrows` 同名元素合并追加）。细节见 `reference/loyalty-icon.md` 第八节。

### 6.2 工程接线的五条共用规则

1. **`Materials/`、`Assets/`、`Textures/`、`Geometries/`、`LightRigs/`、`EnvironmentLights/` 构建时自动扫描**编译进 `Platforms\Windows\BLPs\*.blp`，**不需要**写进 `*.civ6proj` 清单。
2. **XLP / ArtDef 的构建接入点**：`.civ6proj` 的 `<Content>` 条目**不是**必需
   （`.xlp` 属 cook 输入，`.artdef` 由构建产物 `.modinfo` 自动收进）；**真正必须的是第 3 条的 `.Art.xml`**。
   脚本会幂等补 Content 条目，属可选冗余；civ6proj 可能有多个 `ItemGroup`，统一插到最后一个 `</Content>` 之后。
   `.civ6proj` 属永不放行的工程文件：条目的新增结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程。
3. **Art.xml 与 artdef/xlp 必须同步**：新增/修改 `XLPs\`、`ArtDefs\` 之后必须重新生成 `.Art.xml`——用
   `python <civ6-modding skill>\art\gen_modartxml.py <projectRoot> --check`，人工确认差异后加 `--write`（脚本按工程实存文件重算 artConsumers / gameLibraries / requiredGameArtIDs，优于手工补引用）。
   `--write` 在 `.Art.xml` 尚不存在时直写新建；已有且内容有变化时，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径，脚本会在退出码 2 时打印待写入清单。
4. **已存在的 artdef 不整体覆盖**：走脚本的幂等合并；脚本找不到锚点时必须报"请手动合并"，**不静默跳过**（防止覆盖工程里其他功能条目）。合并结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径，脚本会在退出码 2 时打印待写入清单。
5. **`.tex` 类别是硬约束**：类别与所绑 XLP 参数不匹配时，cooker 报
   `has class: 'X', but is bound to parameter: 'Y' which does not accept this class`，
   但 **XLP cook 仍显示 success**（条目被静默替换成 error asset）——**不能当成功处理**。各类正确类别：
   - 3D 镜头贴图（忠诚度/宗教 `*_Overlay_*` / `*_Pressure_*`）→ `Generic_BaseColor`（`m_Tags` 留空）
   - 战略视图 sprite → `StrategicView_Sprite`（`m_Tags` 三连 `StrategicView_Sprite` / `StrategicView` / `Sprite`）
   - 带 alpha 的贴图 → `PF_R8G8B8A8_UNORM` + `bUseMips=false`（texconv 必须带 `-m 1`）；OPACITY 用单通道 `PF_R8_UNORM`
   - `gen_tex.py` 默认把 `m_ClassName` 写成 `UserInterface`，**出 `.tex` 后必须手工改类别**，可直接照抄 `templates/` 下的对应模板字段顺序
   - **UI 立绘 / 选人界面贴图 → `UserInterface`**（`m_Tags` 单条 `UserInterface`）。
     ★ **命名空间铁律**：第三方界面适配素材**不得借用官方模板前缀**
     （`FALLBACK_` = 官方 3D 回退 = `Leader_Fallback`，`LEADER_`/`ICON_` 同理），
     一律走 `<适配对象短名>_UI_<KIND>_<KEY>`——Suk 适配＝`SUK_UI_PORTRAIT_{KEY}` / `SUK_UI_BACKGROUND_{KEY}`。
     详见 `reference/ui-leader-portrait.md` §4.4

### 6.3 素材搬运边界（避免污染工程 pantry）

- **不要为导入而把源 PNG 复制进工程**（`.assets` / `Textures`）：`.tex` 的 `SourceFilePath` 只在 AssetEditor 重新导入时用得到，**构建/游戏只读同名 DDS**，导入后删除源 PNG 不影响任何东西。
- manifest / `asset_map.json` 等临时工作文件用完即删。
- 素材（fgx/wig/环境光 dds/立绘 png）由用户提供时，复制后必须做**哈希校验**并在交付说明中列出结果。

## 七、通用验证顺序与校验脚本

各类共用同一顺序，**缺一不可**：

0. **先跑本类的只读校验器**（类别④/⑤/⑥/⑦ 各有一个，见下表）。这类校验器不依赖素材是否重出，随时可跑，退出码 0 = 现有接线完好。**改动前先跑一次拿基线，改动后再跑一次做对比**——两次都是 0 以外的失败项才需要处理。

1. **合成后立刻跑本类的本地校验脚本**（数值判据，不依赖模型）：

入口脚本改了既有工程文件时，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径，脚本会在退出码 2 时打印待写入清单；写入完成后按下表逐项校验。

| 类别 | 校验脚本 | 判据 |
|------|---------|------|
| ① 总督 | `python scripts/verify_badge.py <24px徽章.png> [官方对应格.png]`（官方对照格直接点名：`assets/TEMPLATE_badge24_canonical.png`，另有放大对照 `assets/TEMPLATE_badge24_canonical_x16.png` 与 8×1 总督晋升图集 `assets/REF_official_promotions24_x6.png`） | 有对照：轮廓 IoU ≥0.95（本管线实测 0.985）、逐行跨度一致性、逐行均色误差、P90 高光/P10 暗部对比，**跨度表零差异**；无对照：几何自洽（18 行、y=3..20、最宽 18px、左右居中） |
| ② 忠诚度/宗教 | 合成参数自检（`--fit-mode` / `--keep` / `--whiten-overlay`）+ 审核 PNG | 主体贴合官方光晕轮廓（定标细则见 `reference/loyalty-icon.md` 第六节第 1 条） |
| ④ 2D 领袖 | 生成文件清单自检（XML 可解析 / 无残留 `{占位符}` / 条目数 = 对象数 / 引用名与磁盘文件逐字符一致 / **贴图 1024² 且 mip 链完整** / **灯光三件套齐备**：`LightRigs/*.lrg`·`EnvironmentLights/*.env`+`*.dds`·`XLPs/Leader_LightRigs.xlp` / artdef Lightrig 槽 = `LEADER_<KEY>_LightRig` / `.Art.xml` 的 `LeaderLighting` 库 = `leaders/light_rigs` / 两个 `.tex` cook 参数为最高品质） | 完整 checklist 见 `reference/leader-2d.md` 第五节 |
| ⑤ UI 立绘/Suk | `python scripts/verify_suk_portrait.py --project <工程根>` | 类别必须是 `UserInterface`（**类别陷阱**）、`.tex` 宽高 == DDS 实际、贴图已被 `UITexture` XLP 登记、SQL 引用无悬空、行尾合规 |
| ⑦ 原版 FrontEnd | `python scripts/verify_frontend_portrait.py --project <工程根>` | 回退可用性（两列留空且 `<LeaderType>_NEUTRAL/_BACKGROUND` 不可解析 = 空白，**前端不报错**）、悬空引用、`Players`/`LoadingInfo` 的 Action 段归属（写错段 `no such table`）、竖版背景尺寸、类别、行尾 |
| ⑥ 历史时刻 | `python scripts/verify_moment.py --project <工程根>` | **alpha 覆盖率 ≥75%**（原版 240 张最低 83%；漏套模板实测量到 14~15%）、456×332、类别 `UserInterface`、XLP 登记、`MomentIllustrations` 配对与 Texture 存在性 |
| ⑧ 区域图标 | `build_district_icon.py` 内置自检（无独立校验器） | 每张 256×256、全图不透明占比 45~85%（六边形正常区间）、图案质心相对落位框中心偏移 < 1.5px、同素材同落位框下两引擎图案几何偏移 < 2px；图形对照 `Reference` 官方小图 |
| ⑩ 资源图标 | `build_resource_icon.py --plates` 自检 + `civ6-modding/art/verify_icon_atlas.py --edge-qa` | 每张 256×256、**底盘保真**（图案透明处逐像素等于底盘）、**图案黑边**（规格 5px，沿主体 alpha ≥ 64 的全部边缘等宽，环带与主体零交集；边缘带向内第 1/2/3px 暗化约 63% / 60% / 54%，原版约 54% / 40% / 12%）、各档边缘中间调% 与母版逐格 LANCZOS 重出的参考值一致；**大地图档 mip**（256 / 64 / FOW 三档 `.tex` 的 `m_CookParams` 与官方同名文件逐项一致，`IsScalable=true`）；图形对照游戏内其它资源图标 |
| ⑨ 领袖头像 | `prepare_leader_avatar.py` 退出码 + `*_metrics.json` 落位复测 | `crown_f − 圆顶 ≈ g×s`、`bound_f ≈ 圆底`（≤2px）；`edge_hard = 0`（四缘 α≥200 硬接触为零）；换色色相与角色主色一致 |

2. **人眼验收**：与原版对照检查轮廓、描边、高光、渐变、图形对比度；可输出棋盘底预览图（`--checker` / `_preview.png`）。
3. **不达标 → 停下询问用户**（§三 的两类条件；校验器判 FAIL 属「规格不满足」一类）：不自行调参迭代、不手工修图。
4. **审核通过后才做 DDS/.tex**（滞后步骤，走 `civ6-modding` art-pipeline；role 与 `.tex` 类别按第六节 6.2 第 5 条）。
   ⚠ **`.tex` 类别是本 skill 最大的静默坑**（类别与所绑 XLP 参数不匹配 → cooker 仍报 success，条目被换成 error asset）：
   交付前**必须**跑一遍 `civ6-modding` 的类别校验器
   `python <civ6-modding>/art/verify_tex_class.py --project <工程根>`（可加 `--full` 遍历全部 `UITexture` 包）——
   这是家族内**唯一**能机械拦住该类别的校验器；本 skill 的类别①~⑥ 校验表**都不覆盖** `.tex` 类别。
5. **工程构建 + 进游戏开一局验证**（3D 六边形/战略视图/图集实际显示）。
6. **上传/交付**：审核未通过前不得生成 DDS/.tex，不得提交 git。

> **收敛判据**：退出码为 0 即通过。`[warn]` 与 `[info]` 两类输出**不构成失败项，不需要处理，也不写进交付说明**——它们只在用户问起时才展开。

> 常见"静默失败"：名字打错、引用名与定义名不逐字符一致时，游戏与 cooker **都不报错**，只是图标不显示。凡是 artdef 元素名 / XLP 条目名 / `ArtDefReferenceValue` 引用名，都必须逐字符核对（各类坑位清单见对应 reference）。

## 八、目录结构与本 skill 内文件归属

```
civ6-asset-forge/
├─ SKILL.md              ← 本文件：路由 + 各类共用链条（只写一份）
├─ CHANGELOG.md          ← 合并来源、各原仓库最后 commit、引用修正清单
├─ reference/
│   ├─ loyalty-icon.md          ← 类别② 全部类别专属内容（逐字）
│   ├─ promotion-icon-sizes.md  ← 类别③：**仅尺寸/格式规格**
│   ├─ governor-art.md          ← 类别①
│   ├─ leader-2d.md             ← 类别④
│   ├─ ui-leader-portrait.md    ← 类别⑤（Suk 选人界面适配，**可选分支**）
│   ├─ frontend-portrait.md     ← 类别⑦（原版 FrontEnd 选人 + 加载界面，**必需**）
│   ├─ vanilla-leader-backgrounds.json  ← 类别⑦ 官方背景调色板（色相/亮度缓存，供 color 近似选型）
│   ├─ moment-illustration.md   ← 类别⑥（历史时刻插画）
│   ├─ district-icon.md         ← 类别⑧（区域图标：模板结构 / 素材清理铁律 / 合成规格）
│   ├─ leader-avatar.md         ← 类别⑨（领袖圆形头像：三分判定 / 占比定标 / 底图换色 / 出圈）
│   ├─ resource-icon.md         ← 类别⑩（资源图标：底盘几何与配色 / 类别判定 / 图案黑边与构图铁律 / FOW）
│   └─ governor-art/     ← 原 governor 的 specs.md / inventory.md / palette.json（实测规格、素材清单、配色）
├─ scripts/              ← 各类脚本合并（原 18 个，③ 的 5 个已随管线删除）
├─ templates/            ← 模板合集：loyalty_chain/、religion_chain/、**moment_illustration/（18 张官方形状 PSD + README）**、
│                            **district_icon/（区域图标官方模板 PSD，类别⑧）**、
│                            **resource_icon/（资源图标模板 PSD，类别⑩）**、
│                            领袖模板（geo/geo_Camera/mtl/tex×2/ast/xlp/artdef、灯光 lrg/env + 通用环境光 dds、Leader_LightRigs.xlp）
│                            + 光晕模板（⑤ 无需模板）
└─ assets/               ← 素材合并（总督官方对照图：`TEMPLATE_badge24_canonical.png` / `_x16.png`、
                            `REF_official_promotions24_x6.png`、**领袖头像底图 `TEMPLATE_leader_avatar_base.png`（类别⑨）**、
                            **资源底盘 `TEMPLATE_resource_plate_{bonus,luxury}[_fow].png`（类别⑩）**；
                            晋升模板/剪影样例已随管线删除；⑤⑥ 无需素材）
```

| 脚本 | 类别 | 说明 |
|------|------|------|
| `scripts/build_icon_set.py` | ① | 头像 → 24px 徽章 + 32/64px 图标 + 两种立绘尺寸 |
| `scripts/edge_gradient.py` | ① | 立绘边缘透明渐变（软 alpha + 去杂边 + OPACITY 遮罩） |
| `scripts/verify_badge.py` | ① | 24px 徽章几何/配色验证 |
| `scripts/process_loyalty_icon.py` | ② | 忠诚度 4 张 / 宗教 3 张 PNG 合成（`--kind`） |
| `scripts/gen_loyalty_art.py` | ② | 忠诚度注册链（XLP/ArtDef/mtl/ast + Art.xml + civ6proj 补注册；改写结果落 `workspace/gen/`） |
| `scripts/gen_religion_art.py` | ② | 宗教注册链（同上机制，宗教命名映射） |
| `scripts/gen_leader_2d.py` | ④ | 全套领袖美术注册文件生成（读 `templates/` 模板；含灯光链 `.lrg`/`.env`/环境光 dds/`Leader_LightRigs.xlp`，见 §五bis） |
| `scripts/process_leader_png.py` | ④ | 立绘 PNG → 1024² TEXTURE/OPACITY（读 `templates/` 的两个 `.tex` 模板） |
| `scripts/gen_suk_portrait.py` | ⑤ | Suk 适配素材 + `UPDATE Players` + XLP + civ6proj 接线（幂等，`--check`/`--write`；SQL/XLP/civ6proj 的改写结果落 `workspace/gen/`） |
| `scripts/verify_suk_portrait.py` | ⑤ | Suk 适配只读校验（类别陷阱 / 尺寸对齐 / XLP 登记 / 悬空引用 / 行尾） |
| `scripts/verify_frontend_portrait.py` | ⑦ | 原版 FrontEnd + 加载界面校验（A/B 两环境回退可用性 / 悬空 / Action 段归属 / 尺寸 / 类别 / 行尾） |
| `scripts/pick_vanilla_background.py` | ⑦ | 按色调近似从官方背景里挑可复用项 + 产 XLP 别名与数据行接线（`--list` / `--check` / `--write`；XLP 别名的改写结果落 `workspace/gen/`） |
| `scripts/prepare_frontend_portrait.py` | ⑦ | **两段式**：先出计划（分类 + 处置方案 + 背景来源，**不写盘**），用户确认后才 `--confirmed` 执行；判断类一律 exit 3 停下询问。执行时 `.dds`/`.tex` 直写工程 `Textures/`，XLP 别名的改写结果落 `workspace/gen/` |
| `scripts/apply_moment_template.py` | ⑥ | 历史时刻插画套官方形状模板（`--list` / `--template N` / `--auto` / `--dds`；报告覆盖率对照 83~99%） |
| `scripts/verify_moment.py` | ⑥ | 历史时刻只读校验（**覆盖率下界** / 456×332 / 类别 / XLP / `MomentIllustrations` 配对） |
| `scripts/ps_place_district.py` | ⑧ | 区域图标 **PS 自动化引擎（首选）**：`pattern_canvas` 先按落位框完成构图，再交本机 Photoshop 原位置入智能对象做效果光栅化并逐区域导出（exit 4 = 无 PS，触发用户询问；依赖 pywin32） |
| `scripts/build_district_icon.py` | ⑧ | 区域图标模拟引擎（回退）：**内置官方 PSD 底图** + 白色图案素材（删背景分路 / 可选 `--enhance` 低画质增强 / trim+单步 INTER_AREA 缩放+alpha 质心对齐 / 形状掩码 50% 阈值只界定作用范围 / 三效果按模板参数连续着色：外发光距离场读 `choke`+`quality_range`、渐变按完整色标、描边距离场 1px 软过渡） |
| `scripts/ps_place_resource.py` | ⑩ | 资源图标 **PS 自动化引擎（首选）**：`place_pattern` 按落位框完成构图并在输出空间描等宽黑边，再交本机 Photoshop 打开内置模板，把已构图图案贴入 `Pattern` 组、按类别选底盘导出（exit 4 = 无 PS 或缺 pywin32，两种成因分别提示，触发用户询问；依赖 pywin32） |
| `scripts/build_resource_icon.py` | ⑩ | 资源图标无 PS 引擎（回退）：**内置四张底盘** + 纯图案素材（**图案黑边**（落位后按成品像素 5px 等宽 + σ0.6 羽化，掩码取主体 alpha ≥ 64 且不补洞，外轮廓与枝节、镂空边缘一并成环）/ 内容包围盒裁剪 / 等比缩放 / 居中 / 预乘 alpha LANCZOS 重采样 / source-over 叠底盘；`--no-stroke` 跳过黑边，`--pattern-only` 供 PS 路径预构图，`--plates` 打印底盘规格） |
| `scripts/prepare_leader_avatar.py` | ⑨ | 领袖头像判定 + 占比定标合成 + 底图换色（`--material` + `--anchors` JSON，锚点由 AI 视觉定位提供；`--passthrough` 直通；exit 2 = 满幅/缺锚点） |

> `templates/` 与 `scripts/` **必须保持同级**：`process_loyalty_icon.py`（默认光晕模板 `templates/Loyalty_Overlay_Template.png`）、
> `gen_leader_2d.py`、`process_leader_png.py` 都按 `scripts/../templates` 定位模板。
> 类别⑤ 两个脚本按 `scripts/../../civ6-modding/art/dds_io.py` 复用 DDS 读写（单一真源）。

## 九、交付要求（各类共用）

- 交付说明必须包含：**生成文件清单（含尺寸/输出目录）**、**注册链文件清单**、`Art.xml` / `*.civ6proj` 改动说明、**"待用户审核 / 待 tex+dds / 待用户提供素材"清单**。
- 素材相关一律标注"待用户处理"，**除非用户明确要求代处理**。
- 素材未提供时，明确标注实际使用了哪个文件作为源（含自动回退选中的源文件路径）。
- 处理过立绘/头像时，列出生成的 PNG 尺寸、`.tex` 更新结果、DDS 生成结果（或明确提示未生成）。
- **不静默备份**（第四节）：交付物里不应出现任何 `*.bak_*` / 时间戳副本 / `copy_*`。
- **领袖前景/背景交付时**必须同时声明**三套环境各自的状态**（A 选人 / B 加载界面 / C 外交）
  以及 **Suk 开与关两种情形**——只报一套等于没报（见 `reference/frontend-portrait.md` §〇）。

---

## 作者与致谢

- 整理人：千与千寻瀑
- 随包素材/模板：18 张历史时刻形状 PSD（由原版时刻插画轮廓整理）、总督官方对照图 —— 社区与官方素材的整理成果；
  本 skill 的管线、工作流与实测规格为整理人所作
- texconv（PNG→DDS）来自 [microsoft/DirectXTex](https://github.com/microsoft/DirectXTex)（MIT，随包内置在 `civ6-modding/art/bin/`）
- 致谢：优妮
