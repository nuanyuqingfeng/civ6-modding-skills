---
name: civ6-asset-forge
description: "Civ6 美术素材合成 + 注册链一体化 skill（美术素材合成类 4 类合一）：① 总督素材（governor icon / 就职图标与晋升徽章 24px / 32、64px 头像 / 206x208、326x339 立绘 / 边缘透明渐变、立绘抠边）；② 忠诚度与宗教压力图标（文明 Loyalty Overlay/Pressure + 战略视图 sprite，含新增自定义宗教分支）；③ 单位晋升图标（promotion icon：白金/黄金/白银/青铜四类金属五边形盾形底徽章 + 白色剪影合成）；④ 2D 领袖立绘纸片人（完整美术注册链 + 1024×1024 TEXTURE/OPACITY）。四类共用同一注册链机制（.dds/.tex → xlp/artdef/mtl/ast → Art.xml → .civ6proj 幂等补注册）与同一套校验顺序；处理用户素材前必须先询问，默认只生成注册文件。边界：总督八边形徽章与单位晋升五边形盾形**不得混用**；3D 模型、UI 布局改动、2D UI 宗教图标（IconTextureAtlases 270px 图集）、config（领袖互斥/同名）不在本 skill 范围；png→dds/.tex 转换走 `civ6-modding` 的 art-pipeline。触发词：总督素材、governor icon、就职图标、总督徽章、总督立绘、边缘透明渐变、立绘抠边、忠诚度图标、宗教压力图标、自定义宗教注册、晋升图标、promotion icon、单位晋升、白色图标合成、盾形徽章、2D 领袖、立绘纸片人、领袖美术注册链。"
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
> `civ6-governor-art` / `civ6-leader-2d`），来源与各自最后 commit 见 `CHANGELOG.md`。
> 骨架共用：给定 PNG → 确定性合成器（Python/Pillow）→ 原版风格素材 → 注册链 → 校验器；
> 注册链逻辑只在本文件维护一份，类别专属实测规格（尺寸/坐标/配色/像素参数）逐字保留在 `reference/*.md`。

## 一、本 skill 覆盖的四类素材（边界先读）

| 类别 | 解决的"做什么素材" | 主要产出 | **不做什么** |
|------|------------------|---------|-------------|
| 总督素材<br>`reference/governor-art.md` | 总督头像/徽章/立绘（含立绘边缘透明渐变、抠边） | 24px 就职/晋升徽章、32/64px 头像图标、206×208 常态立绘、326×339 选中立绘、软边 1024² TEXTURE/OPACITY | 不做 3D 总督模型；不做城市横幅滴的 UI 布局改动（只出贴图）；不改 `GovernorPanel.lua` 图标查找逻辑 |
| 忠诚度 / 宗教压力图标<br>`reference/loyalty-icon.md` | 文明忠诚度图标、宗教压力图标、新增自定义宗教 | 每文明 4 张 PNG（3D 覆盖/压力 + 战略视图覆盖/压力）、每宗教 3 张 PNG + 完整 UILens 注册链 | 不处理 2D UI 宗教图标（`IconTextureAtlases` 270px 图集，数据路径）；不处理立绘 |
| 单位晋升图标<br>`reference/promotion-icon.md` | 单位晋升图标（四类金属底 + 白色剪影）+ 生图模板再造 | 1024 交付 PNG + 32px 游戏内图集位、`IconTextureAtlases` / `Icons_Promotions.xml` 注册 | 不处理总督晋升（XP1/XP2 `GovernorPromotions24` 体系）与 3D 单位模型；不修改游戏文件 |
| 2D 领袖<br>`reference/leader-2d.md` | 2D 领袖立绘纸片人（全套注册链）、1024×1024 TEXTURE/OPACITY | XLP 包 / `Leaders.artdef` / 几何 / 材质 / 灯光 / 环境光 / `.tex` / 行为资产 ast | 不生成素材（用户未提供时只出注册文件）；不做 config（领袖互斥/同名，见项目 `DuplicateLeaders`） |

**两条最容易踩的混用**：

1. 总督 24px 徽章是**八边形**（上下切角），单位晋升是**五边形盾形**——两者规格、配色、图集完全是两套，**禁止互相套用**（详见 `reference/governor-art.md` 的「与单位晋升的区别」与 `reference/promotion-icon.md` 的盾形轮廓表）。
2. 「晋升」一词要分清：**单位晋升**（本 skill 类别③）与**总督晋升徽章**（类别①）不是同一件事。

**范围外的相邻任务**：png→dds/.tex 转换与素材导入 → `civ6-modding` 的 `art-pipeline.md`；
原版素材引用链查询/克隆（ArtDef/XLP 四层引用、cook 层排查）→ `civ6-art-reference`。

## 二、任务 → 类别路由

| 用户说要做什么 | 类别 | 去哪 |
|---------------|------|------|
| 「总督素材」「governor icon」「就职图标」「晋升徽章」「总督立绘」「立绘抠边/边缘透明渐变」 | ① 总督 | `reference/governor-art.md`；脚本 `scripts/build_icon_set.py`、`scripts/edge_gradient.py`、`scripts/verify_badge.py` |
| 「忠诚度图标」「忠诚度覆盖/压力」「战略视图忠诚度」「新增自定义宗教」「宗教压力图标」「宗教镜头覆盖」 | ② 忠诚度/宗教 | `reference/loyalty-icon.md`；脚本 `scripts/process_loyalty_icon.py`（`--kind loyalty` / `--kind religion`）、`scripts/gen_loyalty_art.py`、`scripts/gen_religion_art.py` |
| 「晋升图标」「promotion icon」「单位晋升」「白色图标合成」「盾形徽章」「五边形徽章」 | ③ 单位晋升 | `reference/promotion-icon.md`；脚本 `scripts/compose.py`、`scripts/recolor_template.py`、`scripts/verify.py`、`scripts/vcheck_multi.py`、`scripts/slice_atlas.py` |
| 「2D 领袖」「立绘纸片人」「领袖注册链」「领袖 XLP/artdef/几何/材质/灯光」「1024 TEXTURE/OPACITY」 | ④ 2D 领袖 | `reference/leader-2d.md`；脚本 `scripts/gen_leader_2d.py`、`scripts/process_leader_png.py` |
| 「png → dds / .tex」转换、素材导入工程 | — | 不在本 skill：走 `civ6-modding` 的 `art-pipeline.md`（role 由类别决定，见第六节） |

**路由判定三条**：

1. 先判**对象**：总督 / 文明忠诚度 / 宗教 / 单位晋升 / 领袖——五类对象里"宗教"并入类别②（与忠诚度同一套引擎机制，仅命名映射与 artdef 目标集合不同）。
2. 再判**产出层级**：只要 PNG 素材（合成层）还是连注册链（注册层）一起做。**注册层逻辑四类共用**（第六节），差别只在声明层文件名与目标集合。
3. 素材与注册链**都要**时：先出 PNG 交用户审核，审核通过后才做 DDS/.tex 与注册链（第七节）。

## 三、铁律一：处理用户素材前必须先询问（四类共用）

**开始任何一类素材任务前，必须先询问用户是否提供素材**，得到答复后再动手。**默认只生成注册文件/注册链，不主动生成、不擅自处理素材**。

- 询问必须包含：**格式要求、尺寸要求、自动兜底方案、输出目录**四项，并给出「已有素材 / 暂无素材」两个选项。
- 每类的询问模板与素材要求（逐字原文）在对应 reference 文件里，**照用不要自己改写尺寸**：

| 类别 | 询问模板与素材要求位置 | 素材要求摘要 | 未提供时的默认行为 |
|------|----------------------|-------------|------------------|
| ① 总督 | `reference/governor-art.md`「目的 / 强制约定」 | 至少一张头像（另可给两张立绘做边缘渐变） | 不代生成素材，交付贴图规格与注册文件 |
| ② 忠诚度/宗教 | `reference/loyalty-icon.md` 第一节 | PNG/DDS、透明背景、≥256×256（512 更佳），定标基准 = alpha 质量集中区 | 自动从工程 `Textures/` 找**尺寸最大**的 `ICON_CIVILIZATION_*`（宗教分支找 `ICON_RELIGION_*`） |
| ③ 单位晋升 | `reference/promotion-icon.md` 工作流① | 纯白 `#FFFFFF` 剪影、透明背景、正方形 256~1024px、图形占画布 60%~75% | 不代生成素材 |
| ④ 2D 领袖 | `reference/leader-2d.md` 第一节 | PNG、建议透明背景、尺寸近似 1:1 | **只生成注册文件**；`.tex` 的 `SourceFilePath` 指向占位路径，素材由用户后续导入 |

- 用户坚持用自己提供的模板/素材时，一律按其提供的路径走参数（如 `--glow`、`--icon`、`--avatar`、`--input`），不要替换成内置模板。
- 交付物中必须写明**实际用了哪个素材文件**（含自动兜底时选中的源文件路径）。

## 四、铁律二：不静默备份

**不静默备份。有 git 走 git；仅在用户明确要求时才另存副本。**

- 不做 `*.bak_*`、不做时间戳目录、不做"先拷一份再改"。
- 破坏性改动（覆盖/重写 `Art.xml`、`*.civ6proj`、artdef、xlp）前，先确认工程工作区已 commit，把历史交给 git。
- 可再生中间产物（合成图、临时 manifest/asset_map.json）用完即删，不留存。

## 五、铁律三：原版素材来源（只读 pantry，禁止解包）

*（类别① 总督 与 类别③ 单位晋升 共用的强制约定，两条原文逐字保留在各自 reference 内）*

- **美术素材只允许在** `F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK Assets` 内查找（各类 pantry 子路径见对应 reference）。
- **任何情况下不允许解包**（`.blp` 等打包文件不碰、不写解包器）；需要原版图就用 pantry 散装 DDS，用 `F:\CivNexus6\texconv.exe` 做纯格式转换。
- 游戏安装目录只读 XML/Lua 数据定义，**不作素材来源**。
- 交付产物一律写到用户指定目录；**不修改游戏文件**。

## 六、注册链总览（四类共用链条）

```
用户/合成器产出 PNG（512/256/128/1024/24/32/64/206×208/326×339 等）
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
   打包清单：*.civ6proj 幂等补注册（Content Include）
        │
        ▼
   ModBuddy 构建 → 进游戏开一局验证
```

### 6.1 四类的声明层落点

| 类别 | XLP | artdef | 材质/资产 | 其它 |
|------|-----|--------|----------|------|
| ① 总督 | `XLPs/Icons.xlp`（贴图加进去）+ `IconTextureAtlases` 图集 + `IconDefinitions` | — | — | `Governors` 表列（`Image` / `PortraitImage` / `PortraitImageSelected`） |
| ② 忠诚度/宗教 | `XLPs/UILensModels.xlp`、`XLPs/StrategicView_UILenses.xlp` | `ArtDefs/Overlay.artdef`、`ArtDefs/StrategicView.artdef` | `Materials/*_material.mtl`、`Assets/*_Box.ast` | 复用官方几何（Overlay `HexModelGeo` / Pressure `PipModelGeo`），不自建几何 |
| ③ 单位晋升 | 自建图集 + `Icons_Promotions.xml` 加 `ICON_<UnitPromotionType>` 行 | — | — | 走 2D `IconTextureAtlases`（`IconSize 32`）路径，**不走** `.dds/.tex` BLP 链 |
| ④ 2D 领袖 | `XLPs/leader_{PACK}.xlp`、`XLPs/Leader_LightRigs.xlp` | `ArtDefs/Leaders.artdef` | `Geometries/*.geo`、`Materials/*.mtl`、`LightRigs/*.lrg`、`EnvironmentLights/*.env`、`Textures/*.tex`、`Assets/*.ast` | 每个领袖一套 6 类；聚合模板按领袖数复制块 |

> 类别②「宗教分支」与忠诚度**同一套引擎机制**（同两个 XLP 包 + 同两个 artdef + 同一套官方几何/贴图类别约束），差别仅在命名映射与 artdef 目标集合（`ReligionLensIcons` / `ReligionLensArrows` 同名元素合并追加）。细节见 `reference/loyalty-icon.md` 第八节。

### 6.2 工程接线的五条共用规则

1. **`Materials/`、`Assets/`、`Textures/`、`Geometries/`、`LightRigs/`、`EnvironmentLights/` 构建时自动扫描**编译进 `Platforms\Windows\BLPs\*.blp`，**不需要**写进 `*.civ6proj` 清单。
2. **XLP 与 ArtDef 必须注册到 `*.civ6proj` 的 Content 才会编译**；civ6proj 可能有多个 `ItemGroup`，脚本按幂等语义追加（插到最后一个 `</Content>` 之后），重复运行**不产生重复条目**。
3. **Art.xml 与 artdef/xlp 必须同步**：新增/修改 `XLPs\`、`ArtDefs\` 之后必须重新生成 `.Art.xml`——用
   `python <civ6-modding skill>\art\gen_modartxml.py <projectRoot> --check`，人工确认差异后加 `--write`（脚本按工程实存文件重算 artConsumers / gameLibraries / requiredGameArtIDs，优于手工补引用）。
4. **已存在的 artdef 不整体覆盖**：走脚本的幂等合并；脚本找不到锚点时必须报"请手动合并"，**不静默跳过**（防止覆盖工程里其他功能条目）。
5. **`.tex` 类别是硬约束**：类别写错时 cooker 报
   `has class: 'X', but is bound to parameter: 'Y' which does not accept this class`，且错误会沿"材质 → 资产 → XLP 条目"逐级传播、XLP cook 仍显示 "completed with success" 但条目已被替换成 error asset——**不能当成功处理**。各类正确类别见参考模板：
   - 3D 镜头贴图（忠诚度/宗教 `*_Overlay_*` / `*_Pressure_*`）→ `Generic_BaseColor`（`m_Tags` 留空）
   - 战略视图 sprite → `StrategicView_Sprite`（`m_Tags` 三连 `StrategicView_Sprite` / `StrategicView` / `Sprite`）
   - 带 alpha 的贴图 → `PF_R8G8B8A8_UNORM` + `bUseMips=false`（texconv 必须带 `-m 1`）；OPACITY 用单通道 `PF_R8_UNORM`
   - `gen_tex.py` 默认把 `m_ClassName` 写成 `UserInterface`，**出 `.tex` 后必须手工改类别**，可直接照抄 `templates/` 下的对应模板字段顺序

### 6.3 素材搬运边界（避免污染工程 pantry）

- **不要为导入而把源 PNG 复制进工程**（`.assets` / `Textures`）：`.tex` 的 `SourceFilePath` 只在 AssetEditor 重新导入时用得到，**构建/游戏只读同名 DDS**，导入后删除源 PNG 不影响任何东西。
- manifest / `asset_map.json` 等临时工作文件用完即删。
- 素材（fgx/wig/环境光 dds/立绘 png）由用户提供时，复制后必须做**哈希校验**并在交付说明中列出结果。

## 七、通用验证顺序与校验脚本

四类共用同一顺序，**缺一不可**：

1. **合成后立刻跑本类的本地校验脚本**（数值判据，不依赖模型）：

| 类别 | 校验脚本 | 判据 |
|------|---------|------|
| ① 总督 | `python scripts/verify_badge.py <24px徽章.png> [官方对应格.png]` | 有对照：轮廓 IoU ≥0.95（本管线实测 0.985）、逐行跨度一致性、逐行均色误差、P90 高光/P10 暗部对比，**跨度表零差异**；无对照：几何自洽（18 行、y=3..20、最宽 18px、左右居中） |
| ② 忠诚度/宗教 | 合成参数自检（`--fit-mode` / `--keep` / `--whiten-overlay`）+ 审核 PNG | 主体贴合官方光晕轮廓（定标细则见 `reference/loyalty-icon.md` 第六节第 1 条） |
| ③ 单位晋升 | `python scripts/verify.py <成品.png> <对应gt1024.png>` | 轮廓 IoU、配色采样、图形对比度；模板再造须 IoU ≥0.94 且配色贴近实测规格 |
| ④ 2D 领袖 | 生成文件清单自检（XML 可解析 / 无残留 `{占位符}` / 条目数 = 对象数 / 引用名与磁盘文件逐字符一致） | 完整 checklist 见 `reference/leader-2d.md` 第五节 |

2. **视觉评审 / 人眼验收**：与原版对照检查轮廓、描边、高光、渐变、图形对比度。
   - 类别③用 `scripts/vcheck_multi.py`（gemini-3-flash-preview，密钥与代理见 `reference/promotion-icon.md`）。
   - 视觉评审不可用（模型侧 429 / 配额耗尽）时**不要反复重试**，改用本地像素度量 + 输出棋盘底预览图（`--checker` / `_preview.png`）给人眼验收。
3. **数值不达标时回退参数/模板**（改 `scale`、`--keep`、`--feather`、换模板种子重生成），**不要手工修图**。
4. **审核通过后才做 DDS/.tex**（滞后步骤，走 `civ6-modding` art-pipeline；role 与 `.tex` 类别按第六节 6.2 第 5 条）。
5. **工程构建 + 进游戏开一局验证**（3D 六边形/战略视图/图集实际显示）。
6. **上传/交付**：审核未通过前不得生成 DDS/.tex，不得提交 git。

> 常见"静默失败"：名字打错、引用名与定义名不逐字符一致时，游戏与 cooker **都不报错**，只是图标不显示。凡是 artdef 元素名 / XLP 条目名 / `ArtDefReferenceValue` 引用名，都必须逐字符核对（各类坑位清单见对应 reference）。

## 八、目录结构与本 skill 内文件归属

```
civ6-asset-forge/
├─ SKILL.md              ← 本文件：路由 + 四类共用链条（只写一份）
├─ CHANGELOG.md          ← 合并来源、各原仓库最后 commit、引用修正清单
├─ reference/
│   ├─ loyalty-icon.md   ← 类别② 全部类别专属内容（逐字）
│   ├─ promotion-icon.md ← 类别③
│   ├─ governor-art.md   ← 类别①
│   ├─ leader-2d.md      ← 类别④
│   ├─ promotion-icon/   ← 原 promotion 的 specs.md / prompts.md（实测规格、提示词手册）
│   └─ governor-art/     ← 原 governor 的 specs.md / inventory.md / palette.json（实测规格、素材清单、配色）
├─ scripts/              ← 四类脚本合并（basename 无冲突，未改名）
├─ templates/            ← 四类模板合并（loyalty_chain/、religion_chain/、领袖模板 + 光晕模板）
└─ assets/               ← 四类素材合并（晋升 gt 模板 + 白色剪影样例、总督官方对照图）
```

| 脚本 | 类别 | 说明 |
|------|------|------|
| `scripts/build_icon_set.py` | ① | 头像 → 24px 徽章 + 32/64px 图标 + 两种立绘尺寸 |
| `scripts/edge_gradient.py` | ① | 立绘边缘透明渐变（软 alpha + 去杂边 + OPACITY 遮罩） |
| `scripts/verify_badge.py` | ① | 24px 徽章几何/配色验证 |
| `scripts/process_loyalty_icon.py` | ② | 忠诚度 4 张 / 宗教 3 张 PNG 合成（`--kind`） |
| `scripts/gen_loyalty_art.py` | ② | 忠诚度注册链（XLP/ArtDef/mtl/ast + Art.xml + civ6proj 幂等补注册） |
| `scripts/gen_religion_art.py` | ② | 宗教注册链（同上机制，宗教命名映射） |
| `scripts/compose.py` | ③ | 模板 + 白剪影 → 成品（1024 + 32px） |
| `scripts/recolor_template.py` | ③ | 带内容旧模板保浮雕重着色 |
| `scripts/verify.py` | ③ | 轮廓 IoU / 配色采样 / 图形对比度 |
| `scripts/vcheck_multi.py` | ③ | 视觉评审（多图对照） |
| `scripts/slice_atlas.py` | ③ | 原版 32px 图集切格（做 ground truth 用） |
| `scripts/gen_leader_2d.py` | ④ | 全套领袖美术注册文件生成（读 `templates/` 模板） |
| `scripts/process_leader_png.py` | ④ | 立绘 PNG → 1024² TEXTURE/OPACITY（读 `templates/` 的两个 `.tex` 模板） |

> `templates/` 与 `scripts/` **必须保持同级**：`process_loyalty_icon.py`（默认光晕模板 `templates/Loyalty_Overlay_Template.png`）、
> `gen_leader_2d.py`、`process_leader_png.py` 都按 `scripts/../templates` 定位模板。

## 九、交付要求（四类共用）

- 交付说明必须包含：**生成文件清单（含尺寸/输出目录）**、**注册链文件清单**、`Art.xml` / `*.civ6proj` 改动说明、**"待用户审核 / 待 tex+dds / 待用户提供素材"清单**。
- 素材相关一律标注"待用户处理"，**除非用户明确要求代处理**。
- 素材未提供时，明确标注实际使用了哪个文件作为源（含自动兜底选中的源文件路径）。
- 处理过立绘/头像时，列出生成的 PNG 尺寸、`.tex` 更新结果、DDS 生成结果（或明确提示未生成）。
- **不静默备份**（第四节）：交付物里不应出现任何 `*.bak_*` / 时间戳副本 / `copy_*`。

---

## 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮
