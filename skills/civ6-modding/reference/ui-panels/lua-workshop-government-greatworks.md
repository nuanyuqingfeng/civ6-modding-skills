# GovernmentScreen + GreatWorks — 政体选择 + 巨作管理

> **来源**：`Screens/GovernmentScreen.xml`(458行) + `.lua`(2834行) + `GreatWorksOverview.xml`(80行) + `.lua`(1136行) + `GreatWorkShowcase.*`
> **地位**：全屏政体/政策卡界面（含拖拽系统）和巨作管理/展示界面。

---

## GovernmentScreen — 政体与政策卡

### 三标签结构
```
TabContainer
  ButtonMyGovernment → SelectMyGovernment(AlphaAnim)
  ButtonPolicies → SelectPolicies(AlphaAnim)
  ButtonGovernments → SelectGovernments(AlphaAnim)
  SlideAnim(TabAnim) + Image(TabArrow) ← 标签选择动画

ScrollPanel(水平, 768px)
  Image(Wood_Pattern, Tile) ← 背景
```

### MyGovernment 页面
```
Stack(MyGovernment) ← 垂直布局
  Grid(GovernmentTop) ← 当前政体
    Label(GovernmentName) + Label(GovernmentStats)
    Image(GovernmentImage) ← 政体图片
    Stack(BonusStack) ← 效果详细
  ← 4行政策卡槽
  Container(RowMilitary) ← Military/ Economic/ Diplomatic/ Wildcard
    AlphaAnim(MilitaryIconRingAnim) ← 环形图标闪烁
    政策卡实例
```

### 政策卡系统（PolicyCard Instance）
```xml
<Instance Name="PolicyCard">
  <Container ID="Content" Size="140,150">
    <Button ID="Button"/> ← 点击目标
    <Drag ID="Draggable" SnapBackSpeed="4" DragThreshold="8"/> ← 拖拽
    <Grid ID="Shadow" Size="200,238"/> ← 拖拽时的投影
    <Image ID="Background"/> ← 卡面纹理 (Military/Economic/Diplomatic/Wildcard)
    <Image ID="DropTargetGlow"/> ← 放置位高亮
    <Label ID="Title" TruncateWidth="120"/>
    <Label ID="Description" WrapWidth="119"/>
  </Container>
</Instance>
```

### 拖拽系统回调
```lua
-- 目录卡拖出
OnStartDragFromCatalog(dragStruct, cardInstance)
OnDragFromCatalog(dragStruct, cardInstance)
OnDropFromCatalog(dragStruct, cardInstance) → SetActivePolicyAtSlotIndex()

-- 行内卡拖出
OnStartDragFromRow(dragStruct, cardInstance)
OnDropFromRow(dragStruct, cardInstance)
```

### 其他 Instance

| 实例 | 用途 |
|------|------|
| `PolicyListItem` | 筛选器中的政策列表项 |
| `GovernmentItemInstance` | 政体选择项 (352×238) |
| `GovernmentEraLabelInstance` | 政体树中的时代标签 |
| `EmptyCard` | 空卡槽占位符 |
| `HeritageBonusInstance` | 传承加成项 |

### InstanceManager（4个）
```lua
m_policyCardIM            = InstanceManager:new("PolicyCard", "Content", Controls.PolicyCatalog)
m_kGovernmentLabelIM      = InstanceManager:new("GovernmentEraLabelInstance", "Top", ...)
m_kGovernmentItemIM       = InstanceManager:new("GovernmentItemInstance", "Top", ...)
m_kPolicyTabButtonIM      = InstanceManager:new("PolicyTabButtonInstance", "Button", ...)
```

---

## GreatWorksOverview — 巨作管理

### XML 结构
```
Image(ModalBG) ← Religion_BG 平铺全屏
Grid(WindowFrame)
  Label(ModalScreenTitle) ← FontFlair28
  Button(ModalScreenClose)
  
  ← 放置中的巨作
  Grid + Stack(PlacingIcon/PlacingName) ← 拖拽放置时的预览
  
  ← 按城市-建筑组织的巨作槽位
  ScrollPanel(GreatWorksScrollPanel) ← 水平滚动
    Stack(GreatWorksStack) ← StackGrowth="Down" WrapWidth=620
```

### 两个核心 Instance

**GreatWorkSlot**（建筑槽位）：
```xml
<Instance Name="GreatWorkSlot">
  <Container ID="TopControl" Size="248,150">
    <Button ID="DefaultBG"/> ← 无高亮背景
    <Button ID="HighlightedBG"/> ← 高亮背景 (Hidden=1)
    <Label ID="BuildingName"/>
    <Label ID="CityName"/>
    <Stack ID="GreatWorks"/> ← 槽位内巨作
    <Label ID="ThemingLabel"/>
    <Stack ID="ThemeBonuses"/>
  </Container>
</Instance>
```

**GreatWork**（单个巨作）：
```xml
<Instance Name="GreatWork">
  <Container ID="TopControl" Size="38,64">
    <Button ID="EmptySlot"/> ← 空槽位
    <Button ID="EmptySlotHighlight"/> ← 高亮 (Hidden=1)
    <Image ID="SlotTypeIcon"/>
    <Drag ID="GreatWorkDraggable" SnapBackSpeed="0" DragThreshold="8"/>
    <Image ID="GreatWorkIcon" Size="64,64"/>
  </Container>
</Instance>
```

### 拖拽系统
```lua
-- 注册3个Drag回调
OnClickGreatWork(Drag.eDown) ← 填充 m_kViableDropTargets
OnGreatWorkDrag(Drag.eDrag) ← GetBestOverlappingControl
OnGreatWorkDrop(Drag.eDrop) ← MoveGreatWork(src, dst)

-- 移动验证
CanMoveGreatWork(srcBldgs, srcSlot, dstBldgs, dstSlot) ← 检查子类型兼容性
```

### 嵌套 InstanceManager（每个建筑槽位动态创建）
```lua
-- 建筑槽位IM
m_GreatWorkSlotsIM = InstanceManager:new("GreatWorkSlot", "TopControl", Controls.GreatWorksStack)
-- 每个槽位内的巨作IM（动态创建）
greatWorkIM = InstanceManager:new("GreatWork", "TopControl", instance.GreatWorks)
```

---

## GreatWorkShowcase — 巨作展示

单页展示巨作全屏视图，无InstanceManager。
- `Image(GreatWorkImage)` ← 巨作大图 (AutoStretchMode)
- `Label(GreatWorkName)` ← FontFlair28
- `Label(CreatedBy/CreatedDate/CreatedPlace)` ← 元数据
- MusicDetails/WritingDetails ← 按类型分条件显示
- 导航：`NextGreatWork/PreviousGreatWork` + `ViewGreatWorks` 按钮
