# AST 组合结构与边界

## 依据与检索

优先检查用户安装的 SDK Assets：`Civ6/pantry`、`Civ6/DLC/Shared/pantry`、`Expansion1/pantry`、`Expansion2/pantry`。AST 位于 Assets，几何描述位于 Geometries，材质位于 Materials。查询：

```powershell
python "<skills>/civ6-modding/tools/landmark_tool.py" catalog --query Museum
```

catalog 返回来源相对路径、几何实例和附件数量。同名 AST 有多个候选时使用精确 SDK 相对路径，不按扫描顺序选第一个。GEO/MTL/TEX 的同名副本仅在 XML 字节及直接关联的 FGX/DDS 字节全部相同后允许合并，优先 Shared；任一差异或缺文件仍报歧义。SDK 根以外的路径和 `..` 被拒绝。

可以学习已有 Mod 的排布和 Landmarks 写法，但先追踪其几何、材质、动画与 XLP；不能将另一个 Mod 的自定义部件当成官方资源。已有示例也可能有 `Lankmarks.artdef` 等拼写错误。

## 几何与材质

`.geo` 中应检查：

- `m_Meshes/Element/m_Name`：真实网格名；每个网格下 `m_Groups` 是材质分组。
- `m_Bones`：附件可选的骨骼名。AST 的实例名、几何名和骨骼名不是同一个概念。
- `m_DataFiles`：配套 FGX 必须存在。只引用 `.geo` 名并不能补救缺失的二进制模型。
- `m_ClassName`：地标通常是 LandmarkModel；单位及其动画不在此工作流内。

AST 的 `m_GeometrySet/m_ModelInstances` 保留几何和每个材质组的状态表。`m_GroupStates` 下对应的参数包括 Material、FOWMaterial、BurnMaterial、SnowMaterial、Visible 等。不要把模型的唯一材质名套到全部网格上。

`landmark_tool.py compose` 以官方 TileBase AST 为静态源，保留实例、材质和组状态；去掉旧附件、DSG、动画/VFX 时间线，再按配方创建本地附件。此流程不适用于需要动画行为的喷泉水流、机械或单位；静态喷泉模型本身可以使用，但不能声称保留了水流特效。

## 附件

每个附件必须同时提供：

- 本包中的 `asset` 名；生成 BLPEntryValue，Class/Library=TileBase，XLP=`tilebases.xlp`，Package=`landmarks/tilebases`。
- 父 AST 的 `instance` 名及该实例几何中的 `bone` 名。
- `position` 三维偏移、`rotation` 三维旋转、正的 `scale`。配方旋转沿用 AST 的弧度数据；复制参考布局时不要把弧度当度数。

生成器使用 `ConnectionType=NONE`、`TerrainFollowMode=Pivot Height`、`Cull Mode=PERMANENT`，适用于固定装饰。道路接口、水岸装饰、资源条件化附件应另查官方写法，不强塞进当前有限 schema。

优先选官方锚点，让 `position=[0,0,0]`。旋转和缩放还会叠加骨骼本身的变换；同样的三维数值在不同锚点上未必得到相同世界位置。不要在 `m_ModelInstances` 中发明 XML 位置字段。

## 状态与遮挡轮廓

Worked、Unworked、Pillaged、Construction、Unbuilt 是状态，不是时代。原有废墟和建设网格的 Visible 表必须保留。某些奇观组件在五种状态都可见，可以通过 `hide_states` 只限制 Construction/Unbuilt，避免主体提前出现；该字段不会强制打开原本不可见的网格。

官方底板若给出 Obstruction Profile，应保留原有合法轮廓。骨骼型空底板可能没有三角网格，强制自动生成 OB 会得到空轮廓警告。添加超出原轮廓的大体积部件还需要在 AE/游戏中验证遮挡、单位穿插；Cooker 无报错不意味着碰撞轮廓合适。

`hide_geometry` 只隐藏源实例的材质组，常用于保留锚点的组合载体；它不自动隐藏附件，也不替代父子状态验收。

## 已遇到的 SDK 格式问题

- 部分 Expansion1 XML 用 `AssetObjects::` 名称并带文件末尾 NUL。读取器只将此已知名称转为 `AssetObjects..` 并去掉末尾 NUL；不修改 SDK 原文件。
- 某些官方 AST 残留已经从 `.geo` 删除的材质组。默认报错；确认来源后，配方可显式 `drop_stale_groups=true`，按实际网格/组删除残留绑定。不得关闭整个验证器来绕过问题。
- `Materials/FOW/DefaultMaterial.mtl` 是子目录资源，不能把斜杠一概理解为 SDK 根相对路径。精确带后缀的相对路径和库内逻辑名有不同用途。
- FGX 的原始单位、根变换和模型锚点都需要核对；离线导出的网格位置不自动等于 AST 的游戏空间。比较库中的完整组合，再做小范围调整。

实际核实样本包括官方 IMP_Sphinx、IMP_Open_Air_Museum、DIS_THR 系列及静态奇观组件。适用范围是静态 TileBase 组合，不能推广为所有官方 AST 的通用转换器。

## 差分尺寸与地面高度

A/B/C 等后缀可能表示几何、材质或状态差异，不保证只是大小不同。逐项检查正常可见网格、XY 占地、Z 范围、原点、父级骨骼变换及 Obstruction Profile；不能只看包含破损/建设网格的总包围盒。同一几何、相同正常外观的两份 AST，也可能在劫掠状态有不同可见表。

优先用同一官方系列的基底与原锚点建立样板。几何最低点经常是故意埋入地面的柱脚或树根，不应统一抬到 Z=0；正高度的铺装 Decal 也不等于实体台座。自定义布局使用实际网格中心补偿偏心原点，并检查大树树冠、亭子、路径与台阶是否相交。新增附件超出原有遮挡轮廓时，应重新制作并实机核对轮廓；不能用可见包围盒冒充引擎碰撞体。

离线预览应使用真实 FGX、UV 与原材质贴图，明确尚未模拟地形贴合、Decal 着色和游戏照明。基底高度最终以同类型官方模型为对照进行实机校准；只有离线图或编译结果时，报告仍注明贴地待验收。


## 奇观完成态作为静态地标的有限适配

优先复用已有 TileBase 子件。只有目标主体仍是 WonderMovie、且实际 FGX 的绑定姿态已经是完整建筑时，才考虑另建静态资源包装；单改 AST 的 ClassName 不够。读取目标 SDK 的 `AssetModTools/Cooker/Civ6.cfg`：TileBase 接受 LandmarkModel 与 DecalGeometry，WonderMovieModel 不是同一几何类别。

已验证的局部案例是 Expansion1 的 WON_TajMahal：主几何 WON_Taj_Maha 的最终绑定姿态可静态显示，另有独立 DecalGeometry。采用以下方式通过了资源引用检查和官方 Cooker；这不是任意奇观动画转换器，也不代表游戏贴地已经通过。

- 从有效 TileBase AST 建立新名称，使用目标的模型实例及真实材质组；清除原奇观附件占位符、时间线、动画和 DSG。保留原模型、网格、组和骨骼内部名称。
- 为不兼容的主几何建立独立 GEO 包装，ClassName 与标签为 LandmarkModel；DataFiles 指向独立名称的 FGX 副本，并校验副本与 SDK 源散列相同。不要修改 SDK 源文件。原本兼容的 DecalGeometry 仍直接引用。
- 用户接受单套外观时，可把经过检查的 Worked 分组状态复制到 Unworked、Construction、Pillaged，Unbuilt 设为隐藏。不要复制 WonderMovie 的状态机或仅根据名称猜测完成态；绑定姿态不完整、依赖动画位移或相机的模型需另做转换。
- 清除不匹配的 AO/LightMap/EmissionMap、旧遮挡引用，按新实体几何生成或制作遮挡轮廓；不要沿用无关模板建筑的轮廓。局部附件仍要核对自己的比例和轮廓。
- 通过 local_pantry/local_files 纳管新包装和载荷，再 compose；先跑小资源包 Cooker，再用正式项目 Art.xml 环境检查依赖。最终检查双向外观、状态、附属地面、建筑组合与实机地形。孤立 ArtDef 缺 Game Art File 的提示不能当作完整项目验证。

离线预览只应测量当前状态实际引用的三角面；隐藏组残留顶点会放大包围盒。显示平坦地面时可在预览着色器中裁掉地面下的片元以免薄六边形底板露出埋地基础，但不可据此删去 FGX 基础或修改游戏 Z 偏移。地形 Decal、打包 AO 通道和原生雪/FOW 着色不能用普通 Blender 材质直接等同。
