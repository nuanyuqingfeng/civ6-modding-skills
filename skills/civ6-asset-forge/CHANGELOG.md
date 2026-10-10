# CHANGELOG — civ6-asset-forge

## 2026-10-10 · 新增类别⑩ 资源图标：加成黄盘 / 奢侈紫盘底盘 + 图案黑边 + 纯图案合成

**来源**：Ragunna_Pack 资源图标重制——重建图集时把源图案直接导入，丢失了资源底盘
（加成黄盘 / 奢侈紫盘 + 黑圆环），游戏内表现为图案浮在空底上，与其它资源不成套；
同一轮补齐了原版图案自带的黑边（描边）。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/resource-icon.md` | 类别⑩ 分册：入口判定 / 底盘几何与配色 / 类别判定 / 构图铁律 / 双引擎脚本 / 模板 PSD 结构 / 验证与交付 |
| `assets/TEMPLATE_resource_plate_bonus.png` | 加成底盘（盘面 alpha 153 RGB (189,141,11)，圆环 alpha 255 RGB (33,33,33)） |
| `assets/TEMPLATE_resource_plate_luxury.png` | 奢侈底盘（盘面 alpha 153 RGB (96,56,123)，圆环同色） |
| `assets/TEMPLATE_resource_plate_bonus_fow.png` | 加成迷雾底盘（盘面 alpha 202 RGB (170,124,34)，圆环 RGB (26,23,18)、6991 px） |
| `assets/TEMPLATE_resource_plate_luxury_fow.png` | 奢侈迷雾底盘（盘面 alpha 202 RGB (108,73,95)，圆环 7597 px） |
| `scripts/build_resource_icon.py` | 无 PS 引擎：**图案黑边**（主体掩码 alpha ≥ 64 且不补洞，沿全部边缘向外 5px 纯黑 + σ0.6 羽化，缩放落位之后，各格等宽）/ 内容包围盒裁剪 / 等比缩放 / 居中 / 预乘 alpha LANCZOS / source-over 叠底盘；`--no-stroke` 跳过黑边，`--pattern-only` 只出图案层，`--plates` 打印底盘规格 |
| `scripts/ps_place_resource.py` + `ps_place_resource.jsx` | PS 自动化引擎（首选）：`place_pattern` 预构图（含黑边）→ COM 打开内置模板 → 图案贴入 `Pattern` 组、按类别单独显示底盘 → 导出（exit 4 分两种成因分别提示：缺 pywin32 附 `pip install pywin32` 命令 / `Photoshop.Application` 连不上） |
| `templates/resource_icon/Resource_Icon_Photoshop_CC.psd` | 模板 PSD：`Choose Plate` 组四张底盘（`bonus` / `luxury` / `bonus FOW` / `luxury FOW`）+ `Pattern` 占位组 |

### 底盘真值（四张共用几何）

画布 256×256、非零 33033 px、alpha 包围盒 `186x190@35,33`、几何中心 (128.0, 128.0)；
径向剖面 r 0~92 alpha 153（母版）/ 202（FOW）、r 95~110 alpha 255、r 111~114 收边。

**FOW 是独立的一套合成**：盘面 alpha 与圆环配色都不同（母版中性灰圆环、FOW 偏暖褐），
生成路线是「图案层做迷雾变换 → 叠到 FOW 底盘」，直接对母版整幅做迷雾变换会同时污染底盘配色。

### SKILL.md 接线

description 增 ⑩ 枚举与触发词；§一 类别表 / §二 路由表 / §二 路由判定 / §三 素材表 /
§6.1 声明层 / §七 校验表 / §八 目录树与脚本表全部补 ⑩。工具名录已刷新（24 个脚本）。

### 已验证

- **图案黑边**：主体掩码取 alpha ≥ 64 且不补内部空洞（浅阴影与软边不参与成环），
  在**缩放落位之后**按成品像素沿全部边缘——外轮廓、枝节边缘、内部空隙——向外铺 5px 纯黑、环带 alpha 做 σ0.6 高斯羽化；
  39 格实测宽度逐格为 5px，环带与主体零交集。
  描边必须在输出空间：源空间描边会随源图尺寸与缩放系数变化，本工程 39 张源图（160²~2048²）的等效宽度曾相差 12 倍（0.46~5.51px）；
  掩码曾用 alpha ≥ 8 补洞：软阴影被并入轮廓（黑边描到投影上，主体边缘反被划为内部），枝节与镂空又被当成实心而漏描；改主体阈值且不补洞后两处一并消除；
  边缘暗化剖面（同一批像素位置、按本格内部亮度归一）原版第 1/2/3px 为 54.2/40.1/11.6%，本规格为 63.1/59.9/53.8%（按肉眼可辨取 5px）；
- **底盘保真判据**：图案透明处输出逐像素等于底盘，39 格合计 0 处不等；
- 端到端重建 Ragunna_Pack 全档图集（256/64/50/38/32 + FOW），
  `verify_icon_atlas.py --edge-qa` 报 32/38/50/64 四档全部 ok（比值参考值逐档一致）；
- `check_pantry.py` 0 error，cook 后 `Platforms/Windows/BLPs/UI/Icons.blp` 重建；
- PS 引擎实测跑通：当前解释器装上 pywin32 后 `Photoshop.Application` 连接成功，39 格母版 + 39 格 FOW 两引擎对差——alpha 逐像素完全相同、可见区 RGB 均差 0.0165（最大 1），78 组零失败。

### 世界地图档 mip（`m_CookParams` 的 `IsScalable`）

原版 `Resources*.tex` 的 `m_CookParams` 带 `IsScalable` / `TexturePadding=2` / 目标尺寸，本工程六张资源 `.tex` 原为空块。
逐档复刻官方同名文件的参数后实测：`IsScalable=true` 的三档（256 / 64 / FOW）cook 时被打成
**未压缩基数层 + 完整 mip 金字塔**，`Icons.blp` 由 33618944 B 增至 58166272 B（md5 `1e6992f6` → `2e8d01f1`），
与官方 `Resources256.dds`（2048²、mips=12、未压缩 fourcc）形态一致；
`IsScalable=false` 的两档（50 / 38）即使源 `.dds` 自带 mip 链也不打包。

单档控制实测（50 档）：源 `.dds` 带 mips=9 + 官方 `m_NumMipMaps=8` + `IsScalable=false` → 增量 +0；
同一 `.dds` 把 `IsScalable` 改 true → +372224 B；改回单 mip 与空参数块 → 精确回到基线。

大地图档位由 `WorldViewIconsManager.lua:94` 的 `FindIconAtlas(iconName, 256)` 取 256 档，
`WorldViewIconsManager.xml:6` 的 `WorldAnchor UnitsPerPixel="0.06"` 让该图持续缩小采样，mip 链即缩小锯齿的修法。
六个 `.dds` 保持单 mip，`verify_icon_atlas.py` 的 mips=1 闸门不受影响。**未经实机验证。**

## 2026-10-01 · 新增类别⑨ 领袖头像：ICON_LEADER_* 素材整备管线

**来源**：作者需求「优化领袖头像的导入流程」。

### 内容

- 新增 `reference/leader-avatar.md`（类别⑨ 全部规则：三分判定 / 锚点采集 / 定标 / 圆缘贴合 /
  出圈三规则 / 验证与边界）与 `scripts/prepare_leader_avatar.py`
  （判定 + 定标合成 + 底图换色；锚点 JSON 由 AI 视觉定位提供；exit 2 = 满幅/缺锚点）。
- 底图真源 `assets/TEMPLATE_leader_avatar_base.png`（256 画布 ⌀234.6 暗青蓝渐变盘，作者提供；
  径向拟合 R=117.3）。
- SKILL.md：description 增 ⑧⑨ 枚举与触发词；§一/§二/§三/§七/§八 接线类别⑨；
  §1.0 增「底图换色」显式豁免（仅底图层：色相→主色相、S 钳制 0.05~0.28、明度逐像素保留）。
- 定标要点：脸中心 = 双眼中点与唇中点的中点（x 居中）；底边 = 下巴-肩线中点（落圆底）；
  顶隙 g = (肩线−下巴)/4（头冠点到圆缘上沿，头冠 = 脸部中心竖直线上的视觉定位点）；
  s = 盘径 ÷ (底边 − 头冠 + g)；圆缘贴合（艺术层 ∩ 底图 alpha）；
  出圈三规则（上半区连通域、深度上限 1.18R、画布圆软边界 ⌀−4px，AA 收尾）。
- 工具名录已刷新（22 脚本）。

### 已知物理边界

高耸头饰（高于头冠）受画布上缘物理限制，超出部分沿画布缘软裁；需完整保留时由作者在
「减小顶隙 g」与「缩小脸占比」间定夺，脚本不做主（Dengdeng 鼠耳即此类）。

## 2026-09-28 · 类别④ 灯光链必须随工程自带（**实机实测**）

**来源**：停云纸片人在外交场景渲染成零星色块；补齐本地灯光链并重新 cook 后正常显示。

### 问题

artdef 的 Lightrig 槽是一个真实被解析的引用：写成 `ART_DEFAULT_LIGHT` 后，该条目要到官方
`Leader_LightRigs.xlp`（包名 `leaders/light_rigs`）里解析；工程内没有本地同名包时，
`.dep` 里 `LeaderLighting` 库的 `PackageDependencies` 为空，领袖场景取不到灯光。

### 改动

| 文件 | 改动 |
|---|---|
| `SKILL.md` §五bis | 「不生成任何灯光资产」改为「灯光链随工程自带，三处齐备」；写明实测症状与成因 |
| `SKILL.md` 类别表 / §6.1 / §6.2 第 1 条 / §七 校验表 | 类别④ 的产出与校验项补灯光链；`LightRigs/`、`EnvironmentLights/` 回到「构建时自动扫描」清单 |
| `SKILL.md` §八 与脚本表 | `templates/` 清单与 `gen_leader_2d.py` 说明去掉「不含灯光链」 |
| `reference/leader-2d.md` §一 / §三 / §3.6(1) / §四 命名表 / §五 清单 / §四 接线步骤 | Lightrig 槽改为 `{LEADER}_LightRig`；补三件套的命名、规格、`.Art.xml` 与 `.civ6proj` 两处接线；删去「不生成灯光资产」与迁移到 `ART_DEFAULT_LIGHT` 的步骤 |
| `templates/Leaders.artdef` | Lightrig 槽 `ART_DEFAULT_LIGHT` 改为 `{LEADER}_LightRig` |
| `templates/LEAD_ABBR_Name_LightRig.lrg`（新增） | 灯光绑定模板，`m_ClassName=LeaderEnvironment` |
| `templates/LEAD_ABBR_Name_Environment.env`（新增） | 环境光模板，三盏方向灯，强度 1.55 / 1.5 / 0.446472 |
| `templates/Leader_Environment.dds`（新增） | Hojo 通用环境光贴图，128×128 RGBA8 单 mip，393,344 字节，MD5 `100A9AF5C487BDF8D1BD84AFF854F1A6` |
| `templates/Leader_LightRigs.xlp`（新增） | `m_ClassName=LeaderLighting`，包名 `leaders/light_rigs`，按领袖块复制 |
| `scripts/gen_leader_2d.py` | 模板表补 `.lrg` / `.env` / `.dds` / `Leader_LightRigs.xlp`；新增通用贴图复制循环；文件头结论改写；收尾提示补两处工程接线 |

### 验证

生成器在空工程里实跑，12 个产物全部产出：artdef 的 Lightrig 槽为
`LEADER_XIANZHOU_TINGYUN_LightRig`，`Leader_LightRigs.xlp` 条目正确，
环境光 dds 的 MD5 与模板、Ragunna、本工程源工程四处一致。

## 2026-09-28 · 全类别补执行顺序与收敛判据（**流程优先，调研默认禁止**）

**来源**：用户指出本 skill 在实作中被当成背景材料来阅读理解，导致每个任务都先展开大量调研；并要求「按照流程走完为优先，除非遇到素材无法认定或者缺失才询问用户，在用户明确要求之前，一定不可以做任何调研」。

### 改动

| 文件 | 改动 |
|---|---|
| `SKILL.md` §〇（新增） | 四步执行顺序（路由 → 执行 → 校验 → 交付）；**收敛条件 = 校验器退出码**；顺序内的读取白名单，白名单之外的读取须先说明用途并取得许可 |
| `SKILL.md` §三 | 由「开始任何任务前必须先询问」改为「**询问的唯一条件**」：素材无法认定（候选多于一份 / 来源路径不明），或素材缺失、规格不满足。素材认定以工程 `AGENTS.md`「美术与音频资产」表的「来源」列为准；反推源文件、比对候选、按像素差寻找匹配一律不出现 |
| `SKILL.md` §五ter（新增） | **改动面由动词决定**：「重新生成图片」只重出图片与 `.tex`/`.dds`；「重新导入并 cook」再加构建；「显示异常」按排查条目逐条走；上次未结案的问题不随新任务展开；执行受阻就地停下报错误原文 |
| `SKILL.md` §七 | 新增第 0 步「先跑本类只读校验器拿基线」；明确 `[warn]`/`[info]` 不构成失败项、不需要处理、不写进交付说明 |
| `reference/leader-2d.md` §一 / §2.5 | 删去「层级 1／2／3」三段式（自行读图分析、检查本机工具、调用子代理）；入口收敛为 `process_leader_png.py` 一条命令；只保留三类停下询问的情形；补记 texconv 子进程管道被环境拒绝时就地停下 |
| `reference/governor-art.md` | 「强制约定」补素材认定与询问条件，指向 `SKILL.md` §〇 / §三 / §七 |
| `reference/frontend-portrait.md` §3b.6 | 标题与首句改指向 `SKILL.md` §三，明确素材路径已知且存在时不提问 |

### 未改动

类别②⑤⑥ 的 reference 与全部 `scripts/` 一字未动。它们的入口、规格与校验脚本维持原样；本次只统一执行顺序、询问条件与收敛判据。

## 2026-09-28 · 类别⑦ 补 1:2.85 竖条分支（**仅 FrontEnd**）

**来源**：用户指出「图片素材为 1:2.85 的竖直长条时，应该作为背景，并把前景置空为 `''`」，
而 skill 里当时没有这条分支；并明确「LoadingInfo 不受这个 FrontEnd 的效果管辖」。

### 问题

`classify()` 只看 alpha 透明率，不看尺寸：

| 素材 | 长宽比 | 透明% | 不透明% | 旧行为 |
|---|---|---|---|---|
| 竖版背景（实心） | 1:2.849 | 0.1 | 99.9 | ② 满幅图（碰巧对） |
| 竖版背景（柔和边缘） | 1:2.849 | 0.7 | 29.6 | **⛔ 中间地带，白问用户一轮** |

`LeaderBG` 控件是 328×935（1:2.8506）且 `StretchMode="None"`，
长宽比落在这个比例上的素材按尺寸就该进 placard 背景位；只看透明率会把它漏进中间地带。

### ★ 作用范围：只在 FrontEnd（环境 A）

1:2.85 竖条这条规则管的是**选人 placard**（`Players.Portrait` / `Players.PortraitBackground`，Config 库）。
**加载界面（环境 B）不受它管辖**：`LoadingInfo.ForegroundImage` 是另一条独立通道
（Gameplay 库、`LoadScreen.lua` 消费），照旧取 `LEADER_<KEY>_NEUTRAL`。
竖条本身是背景，顶替不了加载界面的前景——那份前景仍需单独一张立绘抠图。

### 改动（`scripts/prepare_frontend_portrait.py`）

| 改动 | 说明 |
|---|---|
| 新增 `is_placard_shape()` + `PLACARD_RATIO` / `PLACARD_RATIO_TOL` | 长宽比 1:2.85 ±3% 即判为 placard 形，**只看尺寸、不看 alpha** |
| `classify()` 增第 2 条判据 | 判据次序：透明 ≥40% → **placard 形** → 透明 ≤5% 且不透明 ≥90% → 中间地带。**透明率优先**，高瘦人物抠图（同为 1:2.85、透明 81.6%）仍按抠图处理 |
| `acquire_bgs()` 增 `strip_src` 参数 | 素材本身即 1:2.85 竖条时，直接 cover 到 328×935 采用，产出 `LEADER_<KEY>_PLACARD_BACKGROUND`；不再因"placard 缺竖版源"报 exit 3。**只影响 placard 背景这一项** |
| placard 形分支只置 `Players.Portrait` | ``''`` 只写给 FrontEnd 那列；`loading_fg` 保持 `LEADER_<KEY>_NEUTRAL`，且**不拿竖条去顶替**加载界面前景 |
| `PLACARD_BG_PATTERNS` 增 `LEADER_%s_PLACARD_BACKGROUND` | 二次执行走"① 工程既有"分支，幂等 |
| 计划输出标注判定依据与作用范围 | 仅当**尺寸**这条规则真正决定了结果时才标"1:2.85 竖条 = placard 形"；并显式打印"该规则只在 FrontEnd 触发，加载界面不受管辖" |

### 验证（隔离工程，真实竖版背景素材）

| 用例 | 结果 |
|---|---|
| 竖版背景实心（透明 0.1%） | ② 满幅图 → `Players.Portrait = ''` + placard 背景 cover 328×935 |
| 竖版背景柔边（透明 0.7%） | **由中间地带改为** placard 形，不再 exit 3 |
| 高瘦人物抠图 1:2.85（透明 81.6%） | ① 人物抠图（透明率优先，未被尺寸抢走） |
| 方形人物抠图（透明 47.6%） | ① 人物抠图（回归无变化） |
| 横版载入背景（透明 0%） | ② 满幅图（回归无变化） |
| placard 形分支的 `LoadingInfo.ForegroundImage` | 保持 `LEADER_<KEY>_NEUTRAL`，未被置空 |
| `--write --confirmed` 落盘 | 产出 `LEADER_PROBE_PLACARD_BACKGROUND` 328×935，DDS 实测尺寸一致 |
| 二次执行 | 走"① 工程既有竖版"，幂等 |

### 文档同步

`reference/frontend-portrait.md`：§3b.1 分类表改为"先透明率、后尺寸"四行 + 实测对照表，
并加 ★ 段写明**只在 FrontEnd 触发、加载界面不受管辖**；§3b.2 空串写法补适用范围；
§3b.3 placard 降级顺序补"素材本身即 1:2.85 竖条"一档并注明只作用于 placard；
§3b.4 命名备注；§3b.6 会停下询问的情形与 §四 判定树同步。

## 2026-09-19(4) · 换行归一化（skill 仓库全 LF）+ 根因修复

**来源**：用户裁决 —— 编码/换行归一化属安全改动，倾向"彻底做一次"，
把 skill 里的遗留与现有部分一次修好。

### 问题

`git ls-files --eol` 显示两仓库存在 `i/lf w/crlf`（索引为 LF、**工作区漂移为 CRLF**）：

| 仓库 | 归一化前 w/crlf |
|---|---|
| `civ6-modding` | 77 |
| `civ6-asset-forge` | 4 |
| `civ6-audio-pipeline` | 3 |

**根因**：`scripts/normalize_eol.py` 只认「原版换行分层铁律」的扩展名
（`.artdef/.xlp/.tex/.lua/.sql/.xml`…），**`.md/.py/.ps1/.json/.txt/.csv` 不在任何表里**，
落入"非目标扩展名跳过"。2026-09-18 那次归一化修的是 **mod 工程**口径，覆盖不到 **skill 自身**。

### 根因修复（`civ6-modding/scripts/normalize_eol.py`）

| 改动 | 说明 |
|---|---|
| 新增 `--repo-skill` 模式 | skill 仓库**一律 LF**（含分层表未定义的 `.md/.py/.ps1/.json/.txt/.csv` 等），与两仓库 `.gitattributes` 的 `* text=auto eol=lf` 一致 |
| 新增 `SKILL_EXT` 扩展名集 | `.md/.py/.ps1/.json/.txt/.csv/.jsonc/.yml/.yaml/.toml/.cfg/.ini/.sh/.mjs/.cjs/.ts` |
| **NONE 保护** | 无换行的文件（如单行 JSON）原先被判"需归一化"（转换实为 no-op、却会无意义写盘）；现直接计为符合 |

### 执行结果

| 仓库 | 已归一化 | 归一化后 w/crlf |
|---|---|---|
| `civ6-modding` | 77 | **0** |
| `civ6-asset-forge` | 4 | **0** |
| `civ6-audio-pipeline` | 3 | **0** |
| `civ6-art-reference` / `civ6-tuner` | 0（本就干净） | **0** |

**安全性验证**（归一化前先取基线，事后逐项复核）：

| 检查 | 结果 |
|---|---|
| 内容不变 | 420 个文件按「LF 化后 MD5」比对，**0 变化**（只改行尾） |
| BOM 保留 | 20 个带 BOM 的文件（`.ps1`/中文名 `.csv`）BOM 原样保留 |
| 二进制 | NUL 检测 0 命中 |
| 语法 | 93 个 `.py` 全部编译通过；全部 `.json` 解析通过 |
| 工具可用 | `prepare_frontend_portrait` / `verify_frontend_portrait` 实跑正常 |

> 排查中一度出现"status 报 96 个 M、但 `git diff --numstat` 为 0"的现象 ——
> 经 `git cat-file blob` 与工作区**逐字节比对确认完全一致**，属 `core.autocrlf=true`
> 下的 stat 缓存陈旧，已用 `git add` 刷新（blob 相同故不产生任何内容变更），
> 现已 `git reset` 回到未暂存状态。

## 2026-09-19(3) · 定位收敛为「整理与导入」+ 总规则 + 全库冗余叙述清理

**来源**：用户裁决 —— 把「**不对图片进行除裁剪、通道透明度、描边等既有工具能胜任的简单工作**」
确立为**整个美术素材处理部分的总规则**；本 skill 的定位是**对已预处理、基本符合要求的素材
做进一步整理和导入**，**不是全流程图片处理工作流**。要求同步删除被该规则覆盖的冗余描述
（踩坑记录、用户要求之类），不留痕迹。

### 新增：总规则（`SKILL.md` §1.0，占先并覆盖全 skill）

| 允许 | 禁止 |
|---|---|
| **裁剪**（定内容框 / 居中 / 等比缩放）、**通道透明度**（alpha 阈值、遮罩）、**描边**、复制/改名/格式转换 | 重绘、修补、重着色、调色（levels / gamma / 亮度 / 对比度 / 饱和度 / 色相）、去背景重构、超分/降噪/锐化、生成式补图、迭代式调参 |

**遇到不满足上表的素材 → 停下询问用户**，不自行尝试。

### 脚本改动：`prepare_frontend_portrait.py` 改为**两段式**并补齐"停下询问"

| 改动 | 说明 |
|---|---|
| **计划 → 确认 → 执行** | 默认只出计划（不写盘）；`--write` **必须**同时给 `--confirmed`，否则直接拒绝（exit 3） |
| **移除边缘克隆补边** | 原 `make_loading_bg` 在源图不够宽时用最近邻克隆边缘像素补满 —— 属**合成新内容**，违反总规则；现改为抛 `NeedsDecision` 交用户 |
| **placard 缺竖版源 → 停下询问** | 原为"拿横版别名去凑 + 警告"，现改为 `NeedsDecision`（不自行决定降级方案） |
| **不覆盖已有贴图** | `emit()` 发现同名 `.dds` 已存在即 `NeedsDecision`（除非用户明确授权） |
| **两条背景轨道分离** | placard（竖版 328×935）与 loading（宽幅 ≥960）尺寸要求不同，原先共用一个 `--bg-dir` 源会互相冲突；现按尺寸各自归位 |

汇总的 **exit 3（需用户裁决）** 情形：分类中间地带 / 色系回退 Δh>60° / placard 缺竖版源 /
源图高 <960 / 缩放后宽不足 / 目标贴图已存在 / `--write` 未带 `--confirmed`。

### 冗余叙述清理（被总规则覆盖的部分）

| 文件 | 删除内容 |
|---|---|
| `SKILL.md` | 合并来历与逐字搬运说明、类别③ 作废经过（"失败尝试的遗留"）、`Voice.bnk` 实测经过、铁律三的括号说明、`.tex` 类别"最大的静默坑"、命名铁律的踩坑叙述、XLP 接入点的实测举例 |
| `reference/leader-2d.md` | 文首合并来历块 + 原 frontmatter yaml 块 + 搬运注记 |
| `reference/governor-art.md` | 同上（来历块 + frontmatter） |
| `reference/loyalty-icon.md` | 同上；另清 §六 标题的"实测/踩坑记录"及各条括注（"实测踩坑"、"工程 A 游戏实测"、"绕过此坑"） |
| `reference/ui-leader-portrait.md` | "为什么曾经踩坑"整段（保留结论：为何必须独立命名空间） |
| `reference/promotion-icon-sizes.md` | 文首作废与删除清单说明（保留：类别③ 只有尺寸规格） |
| `civ6-modding/art-pipeline.md` | 「色相铁律（2026-09 实战教训）」→「只做几何变换」；两条 role 表的"改色即返工" |
| `civ6-modding/art/normalize_icon.py` | docstring 的"着色铁律（实战教训）"与返工叙述 |

**保留的原则**：技术事实（尺寸、类别、命名约束、引擎行为、悬空引用会静默失败等）
以及**注册链相关的静默失败机制**（那是导入正确性问题，不是"图片处理踩坑"）。

### 验证

| 用例 | 结果 |
|---|---|
| 计划态 | `MODE: PLAN (no write)`，**零写盘** |
| `--write` 无 `--confirmed` | **exit 3** 拒绝 |
| 无竖版源 | exit 3，报"placard 竖版背景缺失，请提供 328×935" |
| 竖版+宽幅两个源 | 正确分流：`LEADER_*_BACKGROUND` 1920×1080（crop）/ `LEADER_*_PLACARD_BACKGROUND` 328×935（cover） |
| 重跑（目标已存在） | exit 3，报"不覆盖已有素材" |

## 2026-09-19(2) · 类别⑦ 增「自动处理流程」+ 加载界面背景尺寸口径修正 + 校验器三态修复

**来源**：用户裁决四点 ——
① 加载界面背景**以官方 960 为基准、允许超过**（本项目 1920×1080 实机效果良好），只有**低于 960 才有两侧裁剪风险**；
② 自动分类的**中间地带仍走用户询问流程**，由用户裁决；
③ 新增素材**命名以官方为准**，本项目既有 `PORTRAIT_*` / `IMG_LOADING_*` **不做重构**；
④ 执行方案。

### 新增

| 文件 | 说明 |
|---|---|
| `scripts/prepare_frontend_portrait.py` | **一站式自动处理**：① 像素构成分类（人物抠图 / 满幅图 / 中间地带）→ ② 两分支处理（定内容框/底对齐/内容定宽 **或** 空白前景+铺满背景）→ ③ 背景降级获取（工程既有 → `--bg-dir` → 色系回退 Δh≤60° → 报缺失）→ ④ XLP 别名登记 + 接线 SQL 打印。复用 `gen_suk_portrait` 的 bbox/定宽工艺与 `pick_vanilla_background` 的调色板/挑选/别名机制，**不重复实现** |

### 修正（错误口径与缺陷）

| 位置 | 问题 | 修正 |
|---|---|---|
| `verify_frontend_portrait.py` `check()` | **重大误报**：把 `''` 与 `NULL` 都当"留空" → 把本项目**正确的**"空白前景+铺满背景"设计报成 5 个 error | 改为**三态判定**：贴图名 / `''`（Lua truthy → 真空白且**短路回退**，INFO）/ `NULL`（falsy → 触发回退，回退名不可解析才 ERROR）。依据 `PlayerSetupLogic.lua:807-829`。修复后本项目实跑 **0 error / 0 warn** |
| `verify_frontend_portrait.py` B 环境尺寸 | `≠1920×960 → INFO` 口径过窄 | 改为 **`h < 960` → WARN（两侧裁剪风险）；`≥960` → 合规**；官方 1920×960 静默通过 |
| `pick_vanilla_background.py` `insert_alias()` | 插入的别名块**多一级缩进**（锚点已含前导 tab，又拼了一个） | 锚点改为 `\n\t</m_Entries>`，缩进与其余条目对齐 |
| `frontend-portrait.md` §2.3 | 把 1920×960 写成**硬规格** | 改为**官方基线 + 960 为基准可超过**，新增 §2.4 专节（含 <960 裁剪的表与机制假说，明确标注"未经实机对照"） |
| `art-pipeline.md` role 表 | 同上 | `background` 行与三环境对照表同步 960 基准口径 |

### 新增/更新的文档章节

| 文件 | 改动 |
|---|---|
| `reference/frontend-portrait.md` | 新增 **§三bis 自动处理流程**（分类表 + 实测透明率参考 + 分支②的空串 vs NULL 对照 + 背景降级顺序 + 官方命名表 + 用法与"会/不会做什么"）；判定树补入分类器路径；验证清单补第 0 步（先跑 prepare）与 960 口径；实测依据表补 3 行 |
| `SKILL.md` | 脚本表 + 路由表 + 触发词 加入 `prepare_frontend_portrait.py` |
| `TOOLS.md` | 由 `skill_manifest.py` 重跑刷新（17 个脚本） |

### 验证（实跑）

| 用例 | 结果 |
|---|---|
| 分支①（`SUK_UI_PORTRAIT_CARTETHYIA`，透明 66.4%） | 判为人物抠图 → 产出 `LEADER_*_NEUTRAL` 1020×1024、裁切 0；背景走"① 工程既有" |
| 分支②（`IMG_LOADING_BACKGROUND_ROCCIA`，透明 0%） | 判为满幅图 → 前景 `''` + placard/加载两版背景；**产出与本项目当前做法一致** |
| 中间地带（构造透明 16.0%） | **exit 3**，正确要求 `--force-subject` / `--force-bleed` |
| 色系回退（隔离工程，无背景素材） | Δh=7.3° → 自动选用 `LEADER_PEDRO_BACKGROUND`，写出 `Shell_Loading.xlp` + `UILeaders.xlp` 两条**官方命名**别名 |
| 幂等性 | 二次运行两条别名均报 `已存在`，EntryID 计数不变（各 1） |
| 本项目回归 | `verify_frontend_portrait.py` → **0 error / 0 warn / 14 info**；工程 XLP 与 `Textures` 未被测试污染（`DEMO/TEST` 命中 0） |

## 2026-09-19 · 新增类别⑦「原版 FrontEnd 立绘/背景」+ 修正 Suk 类别⑤ 的定位与一处口径错误

**来源**：一次真实误判 —— 把 Suk 适配（**可选分支**）当成了 FrontEnd 立绘的全部。
用户指出：**同一对「前景/背景」在三个互不相同的环境里各有一套通道**，
其中**原版环境下的 FrontEnd 前景/背景才是必需的**，Suk 只是可选分支。
据此重新调研引擎源码与官方数据库快照，并全面补齐。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/frontend-portrait.md` | **类别⑦ 分册**：三环境对照表（A 选人 placard / B 加载界面 / C 外交）；`328×935` 的**完整推导**（`AdvancedSetup.xml:148,600` + `AdvancedSetup.lua:19,1671-1675`）；A/B 两环境的**回退链源码**；自建 vs 别名复用两条路；**色调近似选型的量化口径**；判定树与验证清单 |
| `reference/vanilla-leader-backgrounds.json` | 官方 41 张 `LEADER_*_BACKGROUND` 的调色板缓存（加权圆平均色相 / 平均与中位 RGB / 所属 pack） |
| `scripts/verify_frontend_portrait.py` | 类别⑦ 只读校验器：**留空 → 回退不可解析 = 空白风险**（前端不报错）、悬空引用、`Players`/`LoadingInfo` 的 Action 段归属、竖版背景尺寸、类别、行尾 |
| `scripts/pick_vanilla_background.py` | 按色调近似挑官方背景 + 产 XLP **别名**条目与数据行接线（`--list` / `--reference` / `--check` / `--write`），幂等 |

### 修正（错误口径）

| 位置 | 原文 | 修正 |
|---|---|---|
| `scripts/gen_suk_portrait.py:12` | 「原版 mod 的 `PortraitBackground` 是 328×935 竖版」 | **官方数据不符**：官方填值的行指向 `LEADER_*_BACKGROUND`，实测 41/41 全为 **1920×960**。`328×935` 是 **`LeaderBG` 控件尺寸**，本工程的竖版背景是**工程侧选择**。已改写并加注 |
| `reference/ui-leader-portrait.md` §二 | 「`加载界面` → **不关联**（另一条链）」 | 判定本身没错，但**没有文档承接** → 改为指向**类别⑦** |
| `SKILL.md` §2.1 | 同上 | 同上，并新增「**原版 FrontEnd 必需、Suk 可选**」的前置说明 |
| `SKILL.md` §一 第 3 条 | 「领袖立绘分两种」 | 扩为**四种**（④ 3D 纸片人 / ⑤ Suk / ⑦ 前景 / ⑦ 背景），并加第 4 条「Suk 可选、原版必需」 |

### 与其它 skill 的联动

| skill / 文件 | 改动 |
|---|---|
| `civ6-modding/leader-authoring.md` | `Portrait`/`PortraitBackground` 一节重写：原文「默认由游戏按 3D 场景显示，通常可留空」是**范畴错误**（A 环境是纯 2D placard）→ 补回退链、Action 段归属、两个校验器 |
| `civ6-modding/art-pipeline.md` | role 表 `portrait`/`background` 行补「双消费方」说明；§三.1 后新增**环境对照表**与类别⑦ 交叉引用 |
| `civ6-modding/tools/civ_leader_data.py` | 原先**只在有值时**提醒登记 XLP；现补**留空时**的回退风险告警（`Portrait`/`PortraitBackground` 各自） |
| `civ6-modding/SKILL.md` | Task Routing 新增一行「领袖前景/背景」→ 类别⑦ |
| `civ6-modding/reference/FAMILY_INDEX.md` | 路由表新增一行；skill 总览与分册清单同步 |

### 关键实测（为什么可信）

- `Players` 在 **Config 库**（78 表）、`LoadingInfo` 在 **Gameplay 库**（427 表）——node:sqlite 实测两库表清单；
- 官方 `LEADER_*_BACKGROUND` **41/41 = 1920×960**；`LEADER_*_NEUTRAL` 高 1024/1080、宽 389~803；
- 官方**无任何跨领袖背景借用**（`Players`×3 Domain + `LoadingInfo` 41 行全表扫描；跨引用仅同领袖变体）；
- XLP **别名机制真实存在**：`Shell_Loading.xlp` 2 条、`UI_Leaders.xlp` 2 条、`UI_LeaderScenes.xlp` **23 条** `EntryID≠ObjectName`。

### 验证

- `verify_frontend_portrait.py` 在 `Ragunna_Pack` 实跑：**5 error**（5 位领袖 `Portrait` 留空 +
  `LEADER_*_NEUTRAL` 不可解析 = 真实空白风险）+ 6 info + 0 warn，**证明了该类静默失败可被机械拦下**；
- `pick_vanilla_background.py` 在 `Ragunna_Pack` 实跑：`--list` 40 张、
  `--reference SUK_UI_PORTRAIT_CARTETHYIA_QYQXP.dds` → top1 `LEADER_PEDRO_BACKGROUND`（Δh=7.3）、
  `--check` 正确产出别名接线且**未写盘**（exit 0）。

## 2026-09-17/18 · 类别③「单位晋升图标」生成管线作废（仅保留尺寸说明）

**来源**：用户裁决 —— 类别③（promotion icon）的整条**生成管线**是**失败尝试的遗留**，不再需要；
**只保留一份"尺寸说明"**。本次只改本 skill，其它 4 个 skill 未动。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/promotion-icon-sizes.md` | **唯一保留**的类别③文档：只写尺寸/格式事实（`Promotions32.dds` 32px 图集 / `Promotion_Button*` 106×106×5 / 占幅 75%·12.5%·6% / glyph 参数 / 四类金属配色 / 40 格分类 / 注册目标 / `.tex` 约束），**不含**管线步骤、提示词与脚本用法 |

### 删除（逐文件已 grep 证明"引用它的地方只有类别③"）

| 文件 | 依据 |
|---|---|
| `scripts/compose.py` | `SKILL.md` / `TOOLS.md` / `TOOLS.overrides.json` / `reference/promotion-icon.md` / `prompts-metal-recolor.md` —— 全部类别③；**实测未被 `build_icon_set.py` import**（`TOOLS.md` 原注"也被 build_icon_set 调用"系误，一并随重跑消失） |
| `scripts/recolor_template.py` | 同上 5 处，全部类别③ |
| `scripts/slice_atlas.py` | `SKILL.md` / `TOOLS.md` / 自身 docstring，全部类别③ |
| `scripts/verify.py` | `SKILL.md` / `TOOLS.md` / `reference/promotion-icon.md` / `reference/promotion-icon/prompts.md` |
| `scripts/vcheck_multi.py` | `SKILL.md` / `TOOLS.md` / `TOOLS.overrides.json` / `reference/promotion-icon.md` |
| `scripts/__pycache__/vcheck_multi.cpython-314.pyc` | 已删模块的编译产物（`.gitignore` 已忽略，可再生） |
| `assets/TEMPLATE_{platinum,gold,silver,bronze}_{gt32,gt512,gt1024,1024}.png`（16 个） | 类别③ 生图模板与像素级 ground truth |
| `assets/white_glyph_samples/`（5 个：BATTLECRY / HOLD_THE_LINE / MARKSMAN / RANGER / VOLLEY） | 类别③ 白剪影样例（文件名全部属 `Promotions32` 的晋升） |
| `assets/vanilla_promotion_sheet.png` | 类别③ 原版盾形整表（840×150，五边形盾形金属底） |
| `reference/promotion-icon.md` | 类别③ 分册（原 `civ6-promotion-icon` 的 `SKILL.md`） |
| `reference/promotion-icon/specs.md`、`prompts.md`、`prompts-metal-recolor.md` | 类别③ 实测规格 / 提示词手册（`prompts-metal-recolor.md` 系 2026-09-17 当天新增，同属作废管线） |

删除后 `reference/promotion-icon/` 已空，目录一并移除。

### 保留（经证据核验**不属**类别③，未删）

| 文件 | 依据 |
|---|---|
| `scripts/verify_badge.py` | **类别① 总督**：八边形 24px 徽章验证器（`OFFICIAL_SPANS` y=3..20 共 18 行、最宽 18px），被 `SKILL.md` ① 行与 `reference/governor-art.md` 引用 |
| `assets/TEMPLATE_badge24_canonical.png` | **类别①**：24×24，逐行跨度与 `verify_badge.py` 的 `OFFICIAL_SPANS` **1:1 零差异**（八边形暖橄榄金） |
| `assets/TEMPLATE_badge24_canonical_x16.png` | **类别①**：上者的放大对照图（512×512，最近邻 **512/24 ≈ 21.3×** 铺满画布，内容 bbox 426×426）——**文件名里的 `x16` 与实测倍率无关**，勿按字面理解 |
| `assets/REF_official_promotions24_x6.png` | **类别①**：1152×144 = **8×1 @24px × 6 倍放大**。逐格按 6×6 块中心取样还原成 24px 后，**第 1~7 格与 `verify_badge.py` 的 `OFFICIAL_SPANS` 逐行完全一致**（第 0 格是 21 行的 generic 变体）；与 `governor-art/specs.md` §2.3「`XP1/XP2_GovernorPromotions24.dds` 24px **8×1**」、`governor-art.md` §一 第 3 行完全吻合 → 是官方**总督**晋升徽章图集（`GovernorPromotions24` 属类别①） |

> 上表 4 个文件均**无任何文本引用**（属素材级引用），归类依据是**内容 + 尺寸实测**，非文本引用。

### 改动

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 「六类」→「五类」（description / §一 标题 / §二 路由判定 / §三 标题 / §六 标题与 §6.1 标题 / §七 标题 / §八 目录树 / §九 标题）；**删除类别③ 行**（§一 分类表、§三 素材询问表、§6.1 声明层落点、§七 校验表）；§二 路由表 ③ 行改指 `reference/promotion-icon-sizes.md` 并注明"仅尺寸规格，管线已废"；§八 脚本表删 5 行（18 → 13）；§一 表下与 §6.1 表下补作废说明 |
| `TOOLS.overrides.json` | 删 `scripts/compose.py` / `scripts/recolor_template.py` / `scripts/vcheck_multi.py` 三条覆盖 |
| `reference/governor-art.md` | 「边界」节 ③ 指向改为 `reference/promotion-icon-sizes.md`（**CRLF 保持**） |
| `reference/governor-art/specs.md` | §2.3 结论行同样改指 `reference/promotion-icon-sizes.md`（**CRLF 保持**） |

### 待办（落在其它 skill / 生成器侧，本次未动）

- `civ6-modding/tools/skill_manifest.py` 的 `THIRD_PARTY["civ6-asset-forge"]` 仍列
  `compose.py` / `recolor_template.py` / `slice_atlas.py` / `verify.py` 四条 —— 该节由表**逐条原样输出**（不校验文件是否存在），
  **不清理则重跑生成器会把已删脚本写回 `TOOLS.md` 的「第三方依赖」节**。
- `civ6-modding/art/survey_icon_atlas.py`（"与 `slice_atlas.py` 的分工"节）与
  `civ6-modding/reference/FAMILY_INDEX.md`（第 55 / 61 行）仍指向已删的 `promotion-icon.md` / `slice_atlas.py`。
- 本 skill `TOOLS.md` 的工具表与依赖节按文件内"**勿手改表格**"约定**未手改**，待重跑 `skill_manifest.py` 刷新。

---

## 2026-09-17 · 新增类别⑥「历史时刻插画」（MomentIllustrations）

**来源**：用户提供官方历史时刻模板（`历史图片模板（新）/1..18.psd`）+ 用户既定 PS 工作流
（Ctrl+点击模板层载入选区 → 切目标图层 → Ctrl+J 复制 → 单独导出）+ 对原版 240 张时刻图的实测反推。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/moment-illustration.md` | 类别⑥ 完整分册：规格 / 18 张官方形状模板 / 手工与脚本流程 / 接线 / 验证 |
| `scripts/apply_moment_template.py` | 套官方形状模板（`--list`/`--template N`/`--auto`/`--dds`），并报告覆盖率对照原版区间 |
| `scripts/verify_moment.py` | 只读校验器：**alpha 覆盖率下界**、456×332、类别、XLP 登记、`MomentIllustrations` 配对 |

### 改动

| 文件 | 说明 |
|---|---|
| `SKILL.md` | description/触发词加历史时刻系列；「五类」→「六类」；路由 / 素材询问 / 声明层 / 校验表 / 目录结构均补类别⑥ |

### 关键实测结论（写进 reference）

- **画布 456×332、`m_ClassName=UserInterface`**：原版 240 张 `Moment_*.dds` 全部如此。
- **alpha 覆盖率 83.0%~98.5%**：原版 240 张实测区间（min 83.0 / 中位 88.0 / max 98.5），**无一张 <50%**。
  官方每张时刻图都用同一族**卡片形状蒙版**裁出，故覆盖率有下界。
- **18 张模板 = 官方形状族**：原版 240 张对 18 模板做二值 IoU，**全部 ≥0.80**（0.90–0.95 占 22.9%、
  0.80–0.90 占 75.8%），且 18 形状两两互不重复 → 证实其为官方完整形状族。
  其中 `4.psd` 的数字层为空（作者中间稿），脚本自动跳过。
- **漏套模板的实际后果**：某工程 `MOMENT_UNIT_GONDOLA_RGN` / `MOMENT_UNIT_PATRICIUS_RGN`
  覆盖率仅 **14.5% / 15.3%**（最佳模板 IoU 仅 0.30）→ 即未套任何模板，卡片形状不对。
- **`Texture` 列带 `.dds` 后缀**（与 `Players.Portrait` 不带后缀的惯例相反，易写错）。

### 已验证

- `apply_moment_template.py` 端到端：把一张 94.1% 的「实心矩形（未套模板）」输入套模板后，
  覆盖率落入 **83.8%~89.5%**（官方区间内）；`--dds` 产出单 mip RGBA8。
- `verify_moment.py` 在 示例工程 上跑出 **2 个真缺陷**（上述 14.5%/15.3%）；
  一度误报 `MOMENT_DISTRICT_GONDOLA_RGN`（82.4%，仅低于原版下界 0.6pp 且软边正常 41.6%），
  已把默认下界从 83.0 调为 **75.0**（留 8pp 容差）并降级为 warn。

---

## 2026-09-17 · 新增类别⑤「UI 领袖立绘 / 选人界面背景」（Suk 适配）

**来源**：在 `示例工程` 上首次写入并实测通过的 Sukritact's Civ Selection Screen 适配流程，
用户确认「实测效果很好」后要求固化为备选管线。

### 新增

| 文件 | 说明 |
|---|---|
| `reference/ui-leader-portrait.md` | 类别⑤ 完整分册：触发判定 / 素材询问模板 / 实测规格 / **类别陷阱** / 接线 / 验证顺序 |
| `scripts/gen_suk_portrait.py` | 素材 + `UPDATE Players` + XLP + `civ6proj` 接线一体生成器（幂等，`--check`/`--write`） |
| `scripts/verify_suk_portrait.py` | 只读校验器（类别陷阱 / 尺寸对齐 / XLP 登记 / 悬空引用 / 行尾） |

### 改动

| 文件 | 说明 |
|---|---|
| `SKILL.md` | frontmatter description 与触发词加 Suk 系列；「四类」→「五类」；路由表 / 素材询问表 / 声明层落点 / 校验表 / 目录结构均补类别⑤ |
| `civ6-modding/art/dds_io.py` | **新增**：Civ6 单 mip RGBA8 DDS 读写（纯 Python，带 `--selftest` 往返自检）。原 `regen_atlas_tiers.py` 内的头构造逻辑抽为共享模块 |
| `civ6-modding/art/gen_tex.py` | **修正 P0 类别陷阱**：`is_fallback()` 原为纯前缀判断，会把 `FALLBACK_NEUTRAL_*_Suk` 误判成 `Leader_Fallback`（它是 `UITexture` XLP 里的 UI 立绘，应为 `UserInterface`），导致 cooker「类别与参数不匹配」→ 静默变 error asset。现由 `_UI_PORTRAIT_SUFFIXES` 显式排除 |

### 已验证

- 生成器对 `示例工程` 既有 12 组交付物 **逐字节复现**（6 立绘 + 6 背景，含 DDS 头）；
- 校验器在真实工程 PASS，且在注入 10 类缺陷的最小工程上**全部命中**（非空跑）；
- `gen_tex.py` 修正后：`_Suk` → `UserInterface`，真 3D 回退 `FALLBACK_NEUTRAL_X` → 仍为 `Leader_Fallback`。

---

## 2026-09-14 · v1.0 · 由 4 个 skill 合并而来（初始版本）

本 skill 由 4 个「美术素材合成类」skill 合并而成。四者**同一骨架换参数**：
给定 PNG → 确定性合成器（Python/Pillow）→ 原版风格素材 → 注册链（`.dds`/`.tex` + xlp/artdef/mtl/ast
+ `Art.xml` + `.civ6proj`）→ 校验器。合并后注册链逻辑只在 `SKILL.md` 维护一份，
各类别专属实测规格（尺寸/坐标/配色/像素参数/完整哈希）**逐字保留**在 `reference/*.md`。

### 一、来源仓库与最后的 commit

| 原 skill | 最后 commit | 提交时间 | 末次提交标题 | 并入落点 |
|----------|-------------|---------|-------------|---------|
| `civ6-loyalty-icon` | `8f97cf686b65cdbd7eb618f579caa2c8b826f2da` | 2026-09-14 19:11:44 +0800 | docs: 剩余去冗余项 | `reference/loyalty-icon.md` + `scripts/` + `templates/` |
| `civ6-promotion-icon` | `b5b5a170b407ff760ae91516ba7eb620c6ac3536` | 2026-09-14 19:10:35 +0800 | docs: 剩余去冗余项 | `reference/promotion-icon.md` + `reference/promotion-icon/` + `scripts/` + `assets/` |
| `civ6-governor-art` | `ceb03d9f489c326d5f12246c84a8156b3d2ea012` | 2026-09-14 19:10:36 +0800 | docs: 剩余去冗余项 | `reference/governor-art.md` + `reference/governor-art/` + `scripts/` + `assets/` |
| `civ6-leader-2d` | `08767d49703d19d55d9edf2d5c69182185913e60` | 2026-09-14 19:10:35 +0800 | docs: 剩余去冗余项 | `reference/leader-2d.md` + `scripts/` + `templates/` |

四个原仓库合并前工作区均干净（`git status --porcelain` 空）；合并完成后原目录已删除。

### 二、文件级合并结果（零丢失）

原 4 个 skill 共 **90 个 git 跟踪文件**（另有 8 个 `.gitignore` 排除的 `__pycache__/*.pyc`），
全部并入，逐文件 SHA256 核对通过：

| 原 skill | 跟踪文件数 | 并入 | 说明 |
|----------|-----------|------|------|
| `civ6-loyalty-icon` | 30 | 30 | `SKILL.md` → `reference/loyalty-icon.md`；3 脚本；1 光晕模板 + `loyalty_chain/`(12) + `religion_chain/`(11) |
| `civ6-promotion-icon` | 32 | 32 | `SKILL.md` → `reference/promotion-icon.md`；2 附属文档 → `reference/promotion-icon/`；5 脚本；22 素材 |
| `civ6-governor-art` | 12 | 12 | `SKILL.md` → `reference/governor-art.md`；3 附属文档 → `reference/governor-art/`；3 脚本；3 素材 |
| `civ6-leader-2d` | 16 | 16 | `SKILL.md` → `reference/leader-2d.md`；2 脚本；11 模板 |
| 4 × `.gitattributes` / `.gitignore` | 8 | 2 | 四份内容**逐字节相同**（SHA256 `7847EB84…` / `CA4140C9…`），各留一份 |

- **脚本未改名**：13 个脚本 basename 互不冲突（`verify.py` 与 `verify_badge.py` 是不同文件），
  因此无需加类别前缀，`SKILL.md` / `reference` 中的脚本名引用保持有效。
- **素材/模板未改名**：`assets/`（25）与 `templates/`（35）合并后无同名冲突。
- 未并入：`scripts/__pycache__/*.pyc`（loyalty 2 / governor 2 / leader-2d 2，共 6 个；promotion 无）
  —— `.gitignore` 排除的可再生运行缓存，原仓库亦未跟踪，脚本运行即自动重建。

### 三、引用修正（仅限"移动导致的失效引用"，逐条）

| 文件 | 原引用 | 改为 |
|------|--------|------|
| `reference/loyalty-icon.md` | `civ6-leader-2d` skill（2D 领袖相关） | 本 skill `reference/leader-2d.md` |
| `reference/leader-2d.md` | `civ6-loyalty-icon` skill（忠诚度图标链路） | 本 skill `reference/loyalty-icon.md` |
| `reference/leader-2d.md` | `C:\...\skills\civ6-leader-2d\scripts\gen_leader_2d.py`、`...\process_leader_png.py` | `C:\...\skills\civ6-asset-forge\scripts\...`（2 处） |
| `reference/leader-2d.md` | 第四节「备份：不静默备份…」 | 上移至 `SKILL.md` 第四节（四类共用，原文逐字保留），此处改为指向 |
| `reference/governor-art.md` | `reference/specs.md`、`reference/palette.json`、`reference/inventory.md` | `reference/governor-art/specs.md`、`…/palette.json`、`…/inventory.md` |
| `reference/governor-art.md` | `civ6-leader-2d` 管线 / `civ6-leader-2d/scripts/process_leader_png.py` | `reference/leader-2d.md` / `scripts/process_leader_png.py`（见 `reference/leader-2d.md`） |
| `reference/governor-art.md` | 单位晋升走 `civ6-promotion-icon` skill | 单位晋升走 `reference/promotion-icon.md` |
| `reference/promotion-icon.md` | `reference/prompts.md`、`reference/specs.md`、裸 `specs.md`（共 6 处） | `reference/promotion-icon/prompts.md`、`reference/promotion-icon/specs.md` |
| `reference/governor-art/specs.md` | `reference/inventory.md`、`reference/palette.json`、裸 `palette.json`、`civ6-promotion-icon` skill | `reference/governor-art/…`、`reference/promotion-icon.md`（3 处） |
| `reference/promotion-icon/prompts.md` | 裸 `specs.md` | `reference/promotion-icon/specs.md`（1 处） |
| `scripts/verify_badge.py`（注释） | `来自 reference/specs.md 实测` | `来自 reference/governor-art/specs.md 实测` |
| `scripts/build_icon_set.py`（注释） | `全部来自 reference/specs.md 的 1:1 实测` | `全部来自 reference/governor-art/specs.md 的 1:1 实测` |
| `scripts/gen_leader_2d.py`（注释） | `根据 civ6-leader-2d skill 的 templates/ 模板` | `根据 civ6-asset-forge skill 的 templates/ 模板` |

保留不动的引用：`civ6-modding`（art-pipeline / `gen_modartxml.py`）与 `civ6-art-reference` 均为独立 skill，仍然有效。

### 四、换行风格（逐文件按原值保留，未统一）

- **LF**：loyalty 的 `SKILL.md`、3 个脚本、`templates/loyalty_chain/**`（12 个，含 `.artdef`/`.ast`/`.mtl`/`.tex`/`.xlp`）；
  promotion 的全部文本文件（`SKILL.md`、2 附属文档、5 脚本）；governor 的 `reference/inventory.md`、`scripts/edge_gradient.py`、
  `scripts/verify_badge.py`；leader-2d 的全部文本文件（`SKILL.md`、2 脚本、11 模板）；本仓库新写的 `SKILL.md`、`CHANGELOG.md`。
- **CRLF**：governor 的 `SKILL.md`（→ `reference/governor-art.md`）、`reference/specs.md`（→ `reference/governor-art/specs.md`）、
  `reference/palette.json`（→ `reference/governor-art/palette.json`）、`scripts/build_icon_set.py`；
  loyalty 的 `templates/religion_chain/**`（11 个）。
- 说明：任务书假设"loyalty/promotion/leader-2d 全 LF、governor 全 CRLF"，**逐字节实测不符**——
  真实分布见上（loyalty 的 `religion_chain/` 是 CRLF，governor 有 3 份文本是 LF）。本仓库按**每个文件的实际值**保留。
- `.gitattributes` 沿用原约定 `* text=auto eol=lf`；索引内统一 LF，工作区保留各自原换行（与原仓库行为一致）。

### 五、结构变化（合并后新增/重组）

- 新增 `SKILL.md`（路由 + 四类共用链条/铁律/验证顺序，共用内容只写一份）与 `CHANGELOG.md`（本文件）。
- 原 4 份 `SKILL.md` → `reference/{loyalty-icon,promotion-icon,governor-art,leader-2d}.md`：
  正文逐字搬运，仅去掉 frontmatter（在文件头部以 yaml 块**逐字保留**）与文末「作者与致谢」（上移 `SKILL.md` 一份）。
- 原 `reference/specs.md` 同名冲突（promotion 与 governor 各一份）→ 按类别归入 `reference/<类别>/` 子目录。
