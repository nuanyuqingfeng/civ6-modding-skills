# 工具契约与验证

## 配方

根：`format="MODTOOLS54_LANDMARK_RECIPE"`、`assets`、`bindings`。可选 `local_pantry` 和 `local_files` 用于已经转换好的自建静态资源。

`assets[]`：

| 字段 | 含义 |
|---|---|
| name | 本包唯一 ASCII 资源名，以字母开始，仅字母数字下划线 |
| source | 本地已声明或官方 TileBase AST 逻辑名，或对应根内的精确相对路径 |
| description | 可选说明 |
| attachments | 可选本包附件；asset、instance、bone 必填；position/rotation 缺省 [0,0,0]，scale 缺省 1 |
| hide_states | 可选；只能填五种合法状态；仅关闭对应几何组的可见性 |
| hide_geometry | 可选；隐藏源几何材质组，保留骨骼载体 |
| drop_stale_groups | 可选且默认 false；确认官方 AST 存在残留分组后才开启 |

`bindings[]`：`kind` 是 improvement 或 district；`entity` 是现有 CIV Type；`source` 是可复用的官方实体 ArtDef 名；`landmark` 是新 Landmark 名；`base_asset` 指向本包 AST。区域还可提供 `buildings=[{"type":"BUILDING_...","asset":"AST_..."}]`。

区域可选 `building_sets=[[],["BUILDING_A"],["BUILDING_A","BUILDING_B"]]`，显式列出经玩法前置/互斥关系确认的可达完整集合。仅生成列出的 BuildingSets 和对应 BaseVariants；顺序无关，输出按 buildings 声明顺序稳定命名。必须含空区域 `[]`，每个已声明建筑至少出现一次；拒绝重复集合、集合内重复/未知建筑、错误形状和非区域使用。省略或 null 保持旧配方全子集兼容（最多六个建筑）；新区域应明确列阶段，工具不自动推断数据库前置。

区域可选 `base_variants=[{"buildings":[],"asset":"EMPTY_BASE"},{"buildings":["BUILDING_A"],"asset":"A_BASE"}]`。按完整建筑集合精确匹配，数组顺序无关；未声明的集合回退 `base_asset`。每项只接受 buildings/asset，建筑必须属于本 binding，集合与集合内建筑不能重复，资产必须在同包声明；显式 building_sets 排除的集合不能写进 base_variants。该字段不修改玩法前置；只有 A 的布局不会自动用于 A+B，需单列或使用回退。

JSON 不写空字符串。模型实例内偏移编辑、动画、外包附件和任意 XML 注入不在 schema 内；已完成的自定义静态材质可走本地源清单；资产和附件的未知字段会报错，避免拼错 position 后静默落到原点。

## 自建静态资源清单

`local_pantry` 是相对配方文件或绝对源目录；`local_files` 是明确的 POSIX 相对路径列表，仅支持 Assets/*.ast、Geometries/*.geo/*.fgx、Materials/*.mtl、Textures/*.tex/*.dds（可有子目录）。不扫描复制整个 pantry，不允许路径越界；文件不得只放磁盘而未声明。逻辑引用优先解析已声明本地文件，其余到 SDK；使用唯一前缀避免覆盖官方名字。

```json
{
  "local_pantry": "authored-pantry",
  "local_files": ["Assets/MY_HALL.ast", "Geometries/MY_HALL.geo", "Geometries/MY_HALL.fgx", "Materials/MY_STONE.mtl", "Textures/MY_STONE_B.tex", "Textures/MY_STONE_B.dds"]
}
```

这是根字段片段，完整配方仍需要 format/assets/bindings。AST 的 source 可写 MY_HALL，原有官方组合可混用。本地 GEO/TEX 的 m_DataFiles 必须在清单中，MTL→TEX、AST→GEO/MTL 用实际引用校验；FGX 的内部几何仍需外部回读与 Cooker 验证。资源包版本 2 保存这些源文件的散列，版本 1 仍可读取。生成器与 preview 按字节写出 FGX/DDS，工程总览只显示二进制大小。打包后的 recipe 保存本地源绝对路径，搬迁后更新 local_pantry 并重新 compose。

## 资源包与工程落地

`landmark_tool.py compose` 校验全部配方后写出 Assets、XLPs、ArtDefs、已声明本地资源、recipe.json 和 manifest.json。manifest 记录文件 SHA-256、绑定、SDK 来源与必需 Art ID。非空且不含 manifest 的输出目录被拒绝；不会递归清空用户目录。

`landmark_tool.py install --bundle <manifest> --project <工程根>` 先完整校验再落地：Assets/Geometries/Materials/Textures 源文件进工程同名目录（pantry 源，不进 Content）；Landmarks/Buildings artdef 无则写入、已有则按条目合并（合并结果不擦既有美术）；tilebases.xlp 已存在且不同时要求 `--force`（必须与 AST 全集一致）；实体条目的 Landmark Xref 自动回填，条目缺失时如实报告。工程里已有且内容有变化的 artdef / xlp，命令跑完后结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径；脚本会在退出码 2 时打印待写入清单。`--dry-run` 只出计划。ArtDefs/XLPs 不登记 .civ6proj（Civ6.targets 直接扫描磁盘；D6 决议：工程清单手工维护）；check_proj_content.py 照跑，核对工程既有清单闭合。

重跑 install 幂等：与 bundle 一致的文件如实报告不重写（改写既有 artdef 时，先由 AI 把 `workspace/gen/` 的结果写入工程，再重跑 install 即为这个状态）。直接修改资源包里的受管文件会改变散列，verify 会阻断并提示重新 compose；AE 中试出的有效布局应改回配方再生成；当前不支持将任意 AE 工程反向导入配方。

## 静态检查

`landmark_tool.py verify --bundle ...` 检查散列、AST 名称/类、附件引用/环、XLP 的一对一登记和 Landmarks 资产引用。

加 `--sdk-assets`：验证官方几何、FGX、材质、真实网格/材质组、锚点实例和骨骼。加 `--project`：核对落地文件与 bundle 一致、实体 Xref、Art.xml 的 TileBase/consumer/DLC 声明和补充建筑。

该检查不是通用引擎模拟器，不验证材质的实际视觉效果或建筑状态机。无 SDK 时无法判定外部官方贴图是否存在，完整引用验证需传 --sdk-assets。

## 官方 Cooker

`landmark_tool.py cook` 使用新建的英文临时目录，因为官方 Cooker 实测会损坏中文 pantry 路径。它复制当前资源包和可选项目 ArtDef/Art.xml，再调用安装的 `Civ6AssetCooker_FinalRelease.exe`；不修改 SDK、不启动 ModBuddy、不部署游戏。整机 cook（全部 ArtDef/XLP 重放 ModBuddy 构建）走 `civ6-modding/tools/cook_assets.py`。`--out` 落在工程之内时，工程里尚不存在的产物由脚本直写，既有产物有变化则结果落在 `<工程>/workspace/gen/` 的同一相对路径，由 AI 用文件编辑工具写入工程对应路径（退出码 2 时打印待写入清单）。

输出包含日志、`cook-report.json` 和本次生成的 BLP/ArtDefs。检查返回码、非空新文件以及错误日志，不沿用上次输出。官方 MSBuild 的部分 Exec 使用 IgnoreExitCode，不能仅凭 ModBuddy 的“成功”判定资源有效。

无 `--project` 时可做最小包试编译，但会缺少真实 Game Art 文件和实体上下文；完整验收应传实际工程。保留暂存路径便于调试；若要清理，只删除报告中明确属于本任务的目录。

## AE 与离线预览

1. 从绑定的 ModBuddy 工程打开 AE，确保项目与所需 SDK pantry 已加载。若中文路径导致解析问题，在英文路径建立独立测试工程并使用本次资源；Cooker 暂存 pantry 不包含完整 civ6proj，不能当成可直接打开的 AE 工程。
2. 在 AE 的 TileBase 资源中找到自定义 AST；查看 Worked/Unworked/Pillaged/Construction/Unbuilt。
3. 对区域逐个加载底板及建筑组合，检查空槽位、互斥博物馆、直接授予高阶建筑和两种保留地建筑。
4. 最后在游戏里核实贴地、树林/地貌相交、道路、冬雪/FOW、单位遮挡和建筑触发。没有对应界面截图或引擎反馈时不要标为完成。

Blender 可读离线提取的官方网格做构图；推荐后台 `--factory-startup`，避免用户已装的角色/MMD 插件影响渲染，不改变其个人启动文件。高版本 Blender 是否兼容旧导入插件，要按实际使用的交换格式验证；纯离线网格预览不需要先安装旧版。

## 本轮经验的验证范围

2026-09-25 的 19.47 实作：22 个 AST、2 个改良、3 个区域和 6 个可见建筑差分完成资源链、CIV 往返、静态检查、官方 Cooker 与 Blender 构图预览。AE 桌面控制入口受到本机工具启动错误影响，游戏内状态切换仍待验收。这个结果不能作为以后任何新组合免检的依据。
