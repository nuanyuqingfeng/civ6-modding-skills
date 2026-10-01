# Landmarks、实体绑定与建筑差分

## 完整引用链

```text
资源包（bundle，manifest 为散列真源）
  -> Assets/自定义.ast（引用官方或包内自建几何和材质）
  -> XLPs/tilebases.xlp：EntryID = ObjectName = AST 的 m_Name
  -> ArtDefs/Landmarks.artdef：TileBase BLPEntryValue
  -> Improvements.artdef / Districts.artdef：Landmark/Xref
  -> 项目 Art.xml：Landmarks consumer + TileBase library + SDK dependencies
  -> 官方 Cooker：landmarks/tilebases.blp + 编译后的 ArtDefs
```

AST、XLP 和 Landmarks 中的名字必须逐段一致。只创建 Landmarks、不改实体的 Landmark/Xref，游戏仍会显示旧模型。只建 AST、不登记 XLP，附件也不会自动加载。

Assets、Geometries、Materials、Textures、Animations、Behaviors、DSGs 等美术源目录，以及 XLPs、ArtDefs，均不注册为 `.civ6proj` 的 Content/Folder/None。源文件仍保存在工程的标准目录：官方 Civ6.targets 扫描 ArtDefs/*.artdef、XLPs/*.XLP，Cooker 通过 `--pantry <ProjectDir>` 读取 AST、几何和材质引用。Content 会被直接复制进发布目录，错误登记会把可编辑源文件一并发布。XLP 内的资产登记及 Art.xml 引用仍必须完整；磁盘源码、Cooker 输入和发布包文件是不同层次。编译后的 Platforms/.../BLPs 不属于这些源目录，不受过滤影响。

本规则已按本机官方 Civ6.targets 的 CheckCookAssets/CookAssets/Build 逻辑及用户确认修正（2026-09-25）；此前“AST 纳入 Content”的说明是错误的。

## 改良

Landmarks 根集合为 `Landmarks`，每项通常包含 FlattenTerrain、RotationType 和子集合 Eras。单套模型用 Tag_Era=DEFAULT、Tag_Culture=DEFAULT、Tag_Appeal=ANY；Asset 指向自定义 TileBase。

Improvements.artdef 的 Improvement 条目保留可用的官方战略视图/音效，通过 Landmark 子集合的 `Xref` 引用新 Landmark 名。当前工具要求所选官方模板含且仅含一个对应 Xref，否则拒绝错误绑定。

## 区域

Landmarks 的区域条目位于根集合 `Districts`，不是根 `Landmarks`。需要三个子集合：

| 子集合 | 功能 |
|---|---|
| BaseVariants | 根据 Set_HeroBuildings 和时代/文化/吸引力选择地面及固定部分 |
| BuildingVariants | Tag_HeroBuilding 对应某个游戏建筑 Type，选择其独立 AST |
| BuildingSets | 每个集合列出已建成建筑的 ArtDef 引用 |

默认空区域使用 EMPTY 集合。先查目标规则集与本 Mod 的玩法数据，再为可达阶段填写 `building_sets`；不要把 N 个建筑机械展开成 2^N 个模型组合。前置与互斥关系决定建筑槽位和基底布局，不只是生成代码的裁剪条件。工具不会自动从运行缓存推断玩法关系；缺省全子集只用于旧配方兼容，不是新设计的推荐流程。

### 先推导可达阶段，再排模型

1. 核对 `BuildingPrereqs`、`MutuallyExclusiveBuildings`、替代建筑以及本 Mod 的 SQL/Lua/Modifier 授予和移除逻辑。多个前置行可能是备选，不能直接按全部同时满足处理；将结果与官方同类 Landmarks 和项目实际行为交叉核对。
2. 按正常建造路径列出空区域及可达的完整建筑集合。只在项目确有越级授予或移除前置建筑的实现、或用户明确要求兼容时添加例外；不要为假设中的其他 Mod、作弊或异常存档穷举组合。劫掠不等于移除建筑，Worked/Pillaged 等状态与建筑集合是两层逻辑。
3. 用 `building_sets` 限定生成的 BuildingSets/BaseVariants；`base_variants` 只负责这些阶段选择哪块底板，不能代替阶段清单。被排除阶段的 base_variants 应报错。
4. 互斥建筑可以共用槽位与 AST；相同庭院布局复用同一基底资产。需要造型区别时替换同一个位置的附馆，不为绝不同时存在的建筑预留两个空位。

例如标准剧院链：古罗马剧场为两种博物馆的前置；艺术与考古博物馆互斥；广播中心以前述任一种博物馆为前置。正常阶段只有六种：

| 阶段 | 完整建筑集合 |
|---|---|
| 空区域 | 无 |
| 一级 | 古罗马剧场 |
| 艺术分支 | 古罗马剧场＋艺术博物馆 |
| 考古分支 | 古罗马剧场＋考古博物馆 |
| 艺术分支满级 | 古罗马剧场＋艺术博物馆＋广播中心 |
| 考古分支满级 | 古罗马剧场＋考古博物馆＋广播中心 |

同一等级两条分支可共用基底，因此六个选择阶段只需四种基底布局；不生成双博物馆、无剧场博物馆或孤立广播中心。此例以目标玩法未改写标准前置为前提，不应硬编码到所有区域。

一套时代模型仍要覆盖已确认可达的建筑出现/消失差分。底板可以按建筑组合改变，通过配方 base_variants 精确选择，不必让空区域为全部未来建筑永久留白；未列出的集合使用 base_asset。各个集合都必须有有效的 BaseVariant，建筑模型仍由 BuildingVariants 触发。含永久隐藏效果的内部建筑不进入 BuildingSets。

Buildings.artdef 中的 `AffectsDistrictBuildingSet=true` 是建筑参与集合切换的关键。SDK 未包含的新资料片建筑可能没有可编译的注册条目，应补充对应建筑 Type 的最小美术字段。工具生成的补充 Buildings.artdef 与当前 Mod 的建筑条目合并，不用整份文件覆盖。

## 时代、DLC 与消费者

- 单套模型不需要为每个时代复制相同条目，DEFAULT 是明确的回退选择。
- 来源模型的 SDK pantry 决定依赖。Expansion2.Art.xml 依赖 Shared，**并不等于声明 Expansion1**；使用 Expansion1 的模型需保留对应 ID。
- compose 的 manifest 从实际 SDK Art.xml 读取 ID；install 把 `required_game_art_ids` 写进报告，工程 Art.xml 需保留全部已有和新增依赖，不能固定输出一个资料片。
- TileBase library 的包名与 BLP 的目录一致；Landmarks consumer 要引用 Landmarks.artdef 并声明 TileBase。实体/Buildings 的相关消费者也沿用官方规则。
- 不凭素材路径推断所有拥有基础游戏的玩家都具备全部 DLC 资源。项目依赖和目标玩家环境应一致。
