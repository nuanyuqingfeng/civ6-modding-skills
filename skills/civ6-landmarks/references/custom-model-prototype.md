# 自建静态模型：先验证一个样板

本页补充官方拼接之外的试验路线。适用于用户选择自行建模时的单个静态地标样板；转换后的 GEO/FGX/MTL/TEX/DDS 可通过 `landmark compose` 的 `local_pantry` 与 `local_files` 纳管；该命令不负责 Blender/CN6 转换，也不支持任意动画或粒子资源。样板源、转换助手和源 pantry 留在 Mod 的工作目录。

## 先解决造型

用户提供的游戏截图优先于离线渲染的美术判断。2026-09-25 的 19.47 反馈证明：能编译、能在地图显示不等于好看；官方部件的时代、材质和尺度混杂，会让新地标仍像原版奇观或零散公园。先确定主体轮廓、占地、色板与用途，再增加细节。

区域必须同时设计空区域与建满后的轮廓；空区域也要有可识别的固定入口或低矮主体。后续建筑应成为同一建筑群的翼楼、院落或塔楼。用户认可的已有模型应保留。

先做一个样板并给用户看实际几何预览。精修阶段前完成 FGX 转换与 Cooker 小闭环，以免只有漂亮的 Blender 文件。预览标明离线渲染，不能冒充游戏图。

## 本机已验证的窄路径

1. Blender 4.5.2 后台 `--factory-startup --disable-autoexec` 生成原创静态几何；应用位置/旋转/缩放与需要的修改器，三角化。
2. 一个网格、一套 atlas 材质、一个静态根骨骼，全部顶点权重归根；每个面有有效 UV、法线和切线。使用用户本机已有的 CN6 导出插件，不要求安装旧 Blender。
3. 调用已安装 CivNexus6 1.3.3 的解析与包装库做 CN6 → FGX；使用它自带的 3UV 模板并生成 GEO/GeometrySet。专用助手只覆盖上述单网格静态样板，不能推广为单位/动画导入器；不改安装目录、不分发 Firaxis DLL。
4. **重置模板的 InitialPlacement**。本次模板原来有 `[-144,96,0]` 偏移；仅改顶点而不清除模型放置矩阵会整体错位。写出后重新加载 FGX，核对原点、包围盒、三角数、UV 范围和材质组。
5. 用独立 pantry 准备 Assets、Geometries、Materials、Textures、XLPs 与 ArtDefs。AST 与 GEO 使用真实输出的 mesh/group/bone 名，XLP 仍要登记 AST；这些源目录不作为 civ6proj Content/Folder/None 发布。
6. 官方 Cooker 编译本次资源，检查退出码、日志和新 BLP；从 FGX 回读网格，使用实际 DDS 再渲染一次，排除只在源场景里正确的情况。

本次读取旧 Firaxis 变换代理的 ScaleShear 得到异常布局，核对变换时改用 CivNexus 的变换包装器/实际逆矩阵，不仅凭代理返回数组判断。二进制转换依赖具体版本，应把版本、输入输出散列与转换后检查一并记录。

## 容易漏掉的问题

- **活动 UV 层**：Blender 基本体可能已经有 UVMap，再新建同名层会成为 UVMap.001，着色器可能仍读取旧层。本次出现台阶跨色板取色。明确移除不用的 UV 层或设置正确的活动渲染层；导出前逐材质区检查。
- **硬边法线**：本机 CN6 导出器会对共享顶点的法线求平均；只在 Blender 里把面设成 flat 仍可能在 FGX 回读后变圆。本次台阶、台座出现这一问题。导出前按锐角拆分顶点，并以回读 FGX 的法线渲染复核；保持平滑曲面与硬边的区别。
- **单通道 DDS 兼容性**：本机 texconv 生成的 R8 DDS 使用 `DDPF_LUMINANCE` 标志；给 AO/Metalness 使用它时 Cooker 以 0xC0000005 退出，日志没有 ERROR。基础色、法线或仅 Gloss 的对照组合没有复现相同失败。改用 RGBA DDS 输入、保留正确的 Generic_AO/Generic_Metalness 等 TEX 类后完整编译通过。这是当前组合的实测规避法，不代表所有 R8 DDS 都不可用；官方 R8 源文件的头部标志与本次 texconv 产物不同。

排错做单变量交叉：自建几何＋官方材质、官方几何＋自建材质、逐贴图替换。切勿把崩溃返回码当作“日志没错所以成功”，也不要用旧 BLP 代替本次结果。

## 转正前还要完成

- 目标地图缩放下的轮廓、颜色和占地评审；LOD/三角数、材质和贴图预算。
- 状态范围先服从用户需求。用户接受单套外观时，建设、正常、劫掠可共用几何，未建设隐藏；不强制制作独立破损、FOW 或雪贴图。保留状态键和引用链，说明外观复用。
- 区域建筑增减、直接授予高阶建筑、空建筑集合。
- 通过 local_pantry/local_files 接入工程落地流程的可重复安装：新增 GEO/FGX/MTL/TEX/DDS 都必须列出并校验散列；二进制不经文本转换。不得仅在 ModBuddy 输出目录复制。
- 用户游戏内验收。本次月影之茧自建样板只完成离线构图、几何往返与官方编译，未验证游戏显示。

## 参考

- [CivNexus6 作者源码](https://github.com/deliverator23/CivNexus6)：CN6FileOps、GrannyMeshWrapper、GrannyTransformWrapper、MetadataWriter；本地已安装版本是实际转换库。
- [CN6 Blender 插件说明](https://github.com/Sukritact/Nexus-Buddy-2-Blender-Scripts)：本机已有插件用于样板，不随工具仓库复制。
