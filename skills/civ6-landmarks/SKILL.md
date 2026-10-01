---
name: civ6-landmarks
description: 使用已安装的文明6 SDK 官方几何体组合改良和区域的静态 TileBase AST，建立 Landmarks.artdef、tilebases.xlp、建筑差分和 Art.xml 引用链，落地到 ModBuddy 工程并运行官方 Cooker。适用于地标模型制作、AST 附件排布和美术资源缺失排查；支持本地自建静态模型资源包；不用于单位动画或 HTML UI。与 .civ6proj 手工维护流程兼容（工程登记只出清单，D6 决议）。
---

# 文明6地标与 AST 组合

目标是可再生成、可验证的地标资源包。AST 是几何实例、材质分组、状态和附件的组合描述，不是模型文件本身。优先复用已安装 SDK 的 `Geometries/*.geo` 与配套 FGX；保留官方材质引用，不把无骨骼的场景网格当作单位模型。

工具为 `civ6-modding/tools/landmark_tool.py`（算法层 `landmark_lib/`，移植自 ModTools 5.4 MIT），与 .CIV 工程通道完全解耦；官方编译需要用户本地 SDK 与 SDK Assets（路径经 `civ6-modding/tools/_paths.py` 解析）。美术源目录（Assets/Geometries/Materials/Textures）不进 .civ6proj Content，由 Cooker pantry 读取——与 `civ6-art-reference` 的 pantry 约定一致。

## 开始工作

1. 家族内先按 `civ6-modding` 的 L0 检索阶梯查正文；本技能命令契约见 `references/workflow.md`。
2. 确定目标 ModBuddy 工程根、SDK Assets 根（P4）和官方 SDK 根（P5）。先 commit 工程，保留游戏逻辑、UI、图标。
3. 从工程数据列出改良、区域和真正可见的建筑，核对目标玩法的前置、互斥和实际授予/移除逻辑，先列可达阶段。隐藏效果建筑不配模型。区分时代差分与建设/破损状态：取消时代差分不等于删除状态。
4. 设计每种模型的主建筑、地面、装饰、空地和建筑槽位。先贯通一个改良，再做区域。只有确有必要才进行 FGX/FBX 转换、安装其他 Blender 或修改官方工具。

## 按阶段读取

- **找模型、组成 AST**：读 [组合结构与边界](references/composition.md)。用 `landmark_tool.py catalog` 查看 TileBase 候选，同时查看 `.geo` 的网格、材质组和骨骼。不能只根据文件名判定模型内容。只有 WonderMovie 主体时，按该文的"奇观完成态作为静态地标的有限适配"核对几何类别与绑定姿态，不直接改类名绕过检查。
- **制作区域建筑差分**：读 [Landmarks 与建筑状态](references/landmarks.md)。先按该文"先推导可达阶段，再排模型"确定 building_sets，再核对 BaseVariants、BuildingVariants 和建筑美术登记。
- **用户选择自行建模**：读 [自建静态样板](references/custom-model-prototype.md)。先贯通单个样板；通过 local_pantry/local_files 纳管已经转换好的静态资源。模型转换仍由 Blender/CivNexus 等外部工具完成。
- **落地、编译及验收**：读 [工具与验证](references/workflow.md)。从 [最小配方](assets/minimal-recipe.json) 开始；里面的游戏实体名须换成已有工程条目的 Type。

## 必须遵守

- 资源包（bundle）是美术唯一真源：改配方后重新 compose 和 install，不靠手改工程里的 AST 维持结果（散列校验会阻断）。
- 官方拼接通道使用本地已安装 SDK 作为几何和材质源；用户选择自建模型时按静态样板流程独立验证。本技能不附官方 FGX、DDS 或材质，也不将可读取的文件宣称为开源授权。
- 原始几何引用、网格名、材质组、骨骼名必须存在；附件所指 AST 必须登记在同一 TileBase XLP。发现缺失不能改用一个看似相近的名字糊弄校验。
- Assets、Geometries、Materials 等美术源目录不注册为 civ6proj Content；ArtDefs/XLPs 编译项按本家族惯例进 Content（与 ModTools 原约定相反，以本家族 check_proj_content 闭合体检为准）。
- 官方组合保留源 AST 的分组状态，不同时显示互斥几何。自建静态模型可按用户要求共用完整外观于建设、正常和劫掠状态；未建设隐藏。独立破损、FOW、雪等不是用户已接受单套外观时的强制交付门槛，应说明实际验证范围。
- 区域阶段只覆盖玩法可达的建筑组合；互斥建筑可共享槽位和资产，不为假设的异常授予枚举全部子集。区域各阶段的底板应与当前建筑组合匹配；可用 base_variants 替换临时庭院、铺装和绿化，为新增建筑让位。建筑差分由游戏建筑 Type 触发；只有 BaseVariants 的完整大楼会在空区域提前出现。
- 优先使用官方已有骨骼锚点，保持附件偏移为零。需要自定义偏移时同时核对父模型、骨骼变换、缩放和坐标单位；不能直接把 Blender 中的原始 FGX 数值当成游戏坐标结论。
- 单 Mod 的探索脚本、截图、日志留在工程工作区；通用工具、原创测试和技能才属于 skill 仓库。
- **工程文件写入铁律**：脚本可以**新建**工程文件，绝不允许**改写**工程文件。`landmark_tool.py install` 遇到工程里已有的 `ArtDefs/*.artdef` 与 `XLPs/*.xlp` 时不做合并覆盖，改写结果落到 `workspace/gen/` 由 AI 用文件编辑工具写入；`compose` 写的是独立 `--out` 目录，`cook` 写的是临时目录与输出目录。真源见 `civ6-modding/SKILL.md` 的「工程文件写入铁律」。

## 最小闭环

```powershell
python "<skills>/civ6-modding/tools/landmark_tool.py" catalog --query Sphinx
python "<skills>/civ6-modding/tools/landmark_tool.py" compose --recipe "recipe.json" --out "MyMod.landmarks"
python "<skills>/civ6-modding/tools/landmark_tool.py" install --bundle "MyMod.landmarks/manifest.json" --project "<ModBuddy 工程根>" --dry-run
python "<skills>/civ6-modding/tools/landmark_tool.py" install --bundle "MyMod.landmarks/manifest.json" --project "<ModBuddy 工程根>"
python "<skills>/civ6-modding/scripts/check_proj_content.py" "<ModBuddy 工程根>"
python "<skills>/civ6-modding/tools/landmark_tool.py" verify --bundle "MyMod.landmarks/manifest.json" --project "<ModBuddy 工程根>"
python "<skills>/civ6-modding/tools/landmark_tool.py" cook --bundle "MyMod.landmarks/manifest.json" --out "<输出目录>" --project "<ModBuddy 工程根>"
```

`install` 落地文件并输出 .civ6proj 登记清单（ArtDefs/XLPs 编译项手工进 Content）与 Art.xml 三项核对点；
工程里已有且内容有变化的 artdef / xlp，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，
由 AI 用文件编辑工具写入工程对应路径，脚本会在退出码 2 时打印待写入清单。
`check_proj_content` 核对清单闭合；`cook` 只编译本资源链并保留日志，不部署 Mod，
其 `--out` 落在工程之内时同样按本条处理：工程里尚不存在的产物直写，既有产物有变化则结果入位 `workspace/gen/`。
已有授权足够时继续完成，不在每一步重复索取批准。

## 验收分层

1. **配方与静态引用**：唯一名称、无附件环、存在的骨骼/网格/材质、完整 XLP 和引用链。
2. **工程往返**：重跑 `install` 幂等（已一致文件如实报告）；.civ6proj Content 登记闭合（check_proj_content 0 error）；补充 Buildings.artdef 合并不覆盖既有建筑。
3. **官方编译**：本次独立暂存目录产生非空 BLP 和 ArtDef；同时检查返回码、日志和文件。旧文件、MSBuild 成功标记或截图都不能替代它。
4. **外观检查**：正常、未工作、建设、破损、空区域和每种已确认可达的建筑组合；至少两个方向看穿插、漂浮、比例、遮挡与六边形边界。
5. **游戏验收**：AE 的 TileBase 预览与实际地图地形、缩放、建造/劫掠/修复、建筑增减分别核实。Blender 离线图只用于构图，不验证引擎状态机、FOW、雪、道路和贴地。

交付附配方、资源包、工程位置、编译日志及待验收项，明确哪些阶段完成。AE 或游戏暂时不可用时如实记录，不将离线渲染描述为游戏截图。
