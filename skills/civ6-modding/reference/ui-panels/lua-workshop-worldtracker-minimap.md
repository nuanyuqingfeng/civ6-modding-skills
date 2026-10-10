# WorldTracker + MinimapPanel + Notifications — HUD 信息面板

> **来源**：`WorldTracker.xml`(82行) + `.lua`(1187行) + `MinimapPanel.xml`(93行) + `.lua`(1153行) + `NotificationPanel.xml`(83行) + `.lua`(1898行) + `StatusMessagePanel.xml`(43行) + `.lua`(404行)
> **地位**：左上角科技/市政/单位追踪器，左下角小地图+镜头系统，右侧通知面板，状态消息。

---

## WorldTracker — 左上角追踪器

### XML 结构
```
AlphaAnim(WorldTrackerAlpha) + SlideAnim(WorldTrackerSlide)
  Stack(PanelStack) ← StackGrowth=Down
    
    WorldTrackerHeader ← Box (40,35,25,230)
      Label(WorldTracker) ← FontFlair16
      ToggleDropdownButton ← 下拉按钮
    
    VerticalContainer(WorldTrackerVerticalContainer) ← 296×300
      ← BuildInstanceForControl:
      ResearchInstance / CivicInstance / UnitListInstance ← 动态构建
    
    ChatPanelContainer ← 聊天 (LuaContext)
    TutorialGoals ← 教程目标 (LuaContext)
  
  ScrollPanel(DropdownScroll) ← 下拉选项
    ResearchCheck / CivicsCheck / ChatCheck / UnitCheck
```

### 半动态实例（BuildInstanceForControl）
```lua
ContextPtr:BuildInstanceForControl("ResearchInstance", m_researchInstance, Controls.WorldTrackerVerticalContainer)
ContextPtr:BuildInstanceForControl("CivicInstance", m_civicsInstance, Controls.WorldTrackerVerticalContainer)
ContextPtr:BuildInstanceForControl("UnitListInstance", m_unitListInstance, Controls.WorldTrackerVerticalContainer)
```
每个实例的结构来自独立的 `.xml` 包含文件（`WorldTrackerCivic.xml`, `WorldTrackerResearch.xml`, `WorldTrackerUnits.xml`）。

### InstanceManager
```lua
m_unitEntryIM = InstanceManager:new("UnitListEntry", "Button", m_unitListInstance.UnitStack)
```

### 面板显示/隐藏切换
```lua
-- 4个复选框控制各面板可见性
Controls.ResearchCheck:RegisterCheckHandler(...)
Controls.CivicsCheck:RegisterCheckHandler(...)
Controls.ChatCheck:RegisterCheckHandler(...)
Controls.UnitCheck:RegisterCheckHandler(...)
```

### 事件驱动刷新（21个游戏事件）
`CityInitialized`, `BuildingChanged`, `CivicChanged/Completed`, `ResearchChanged/Completed`, `UnitAddedToMap/RemovedFromMap`, `UnitMovementPointsChanged`, `LoadGameViewStateDone` 等。

---

## MinimapPanel — 小地图+镜头

### XML 结构
```
SlideAnim(Pause) ← 暂停动画
Grid(LensPanel) ← 镜头面板 (190×326, Hidden=1)

Grid(MapOptionsPanel) ← 地图选项 (220×119, Hidden=1)
  ScrollPanel → Stack ← CheckBox: Grid/Yields/Resources 切换

Container(MiniMap)
  SlideAnim(CollapseAnim) + SlideAnim(ExpandAnim) ← 折叠/展开
    Grid(MinimapBacking) ← 木框背景
    Image(MinimapContainer) ← 小地图纹理
    Image(MinimapImage) ← 小地图画面
    Button(CollapseButton/ExpandButton) ← 折叠/展开按钮
    Stack(OptionsStack) ← 功能按钮行
      CheckBox(LensButton) ← 镜头列表
      CheckBox(MapOptionsButton) ← 地图选项
      CheckBox(MapPinListButton) ← 图钉列表
      CheckBox(MapSearchButton) ← 地图搜索
      Button(StrategicSwitcherButton) ← 战略视图
      Button(FullscreenMapButton) ← 全屏地图
    Meter(CompassArm) ← 指南针 (320×320)
```

### 镜头系统（RadioButton组）
```lua
CreateLensToggleButton("Religion", "宗教镜头", ToggleReligionLens)
-- 共8个镜头: Religion, Continent, Appeal, Water, Government, Owner, Tourism, Empire
-- 全部 RadioGroup="ActiveLens", AllowClickOff=1
```

```lua
function ToggleReligionLens()
    UILens.SetActive("Religion")  -- 引擎级镜头切换
end
```

### InstanceManager（3个）
```lua
m_LensButtonIM  = InstanceManager:new("LensButtonInstance", "LensButton", Controls.LensToggleStack)
m_MapOptionIM   = InstanceManager:new("MapOptionInstance", "ToggleButton", Controls.MapOptionsStack)
-- 通过 LuaContext 注入的子面板: MapPinListPanel, MapSearchPanel
```

---

## NotificationPanel — 通知面板

### XML 结构
```
SlideAnim(RailOffsetAnim) ← 右侧滑轨
  SlideAnim(RailAnim) ← 通知轨道
    Image(RailImage) ← 轨道纹理 (平铺)
  
  Container(Items) ← 通知项
  Container(Groups) ← 分组通知
  
  ScrollPanel(ScrollPanel) → Stack(ScrollStack) ← 可滚动通知
    ScrollBar
```

### ItemInstance（通知模板）
```xml
<Instance Name="ItemInstance">
  <Container ID="Top" Size="62,72">
    <ScrollPanel ID="Clip" Size="2048,66"> ← 超宽裁剪区
      <SlideAnim ID="NotificationSlide" Start="-250,0" Size="255,60">
        <Grid ID="ExpandedArea" Size="250,70"> ← 展开区域
          <Button ID="LeftArrow/RightArrow"/> ← 翻页
          <Stack ID="TitleStack"> ← 标题行
            <Label ID="TitleCount"/> ← 计数
            <Label ID="TitleInfo"/> ← 标题
          </Stack>
          <Label ID="Summary"/> ← 摘要
          <Stack ID="PagePipStack"/> ← 分页指示器
        </Grid>
      </SlideAnim>
    </ScrollPanel>
    <Image ID="Icon" Size="40,40"/> ← 通知图标
    <Label ID="Count"/> ← 角标数字
  </Container>
</Instance>
```
`ScrollPanel(Clip)` 的妙用——超宽裁剪区(2048px)允许SlideAnim滑入展开的内容而不增加布局尺寸。

### 点击/悬停交互
```lua
-- 悬停展示摘要
kInst.MouseInArea:RegisterCallback(Mouse.eMouseEnter, ...)
kInst.MouseOutArea:RegisterCallback(Mouse.eMouseExit, ...)
-- 点击激活
OnDefaultActivateNotification() → LookAtNotification() → UI.LookAtPlot/SelectUnit/SelectCity
```

### 通知处理器系统
```lua
g_notificationHandlers[NOTIFICATION_TYPE] = {
    Add, Dismiss, TryDismiss, TryActivate, Activate,
    OnPhaseBegin, OnNextSelect, OnPreviousSelect, AddSound
}
-- 每种通知类型有独立的处理逻辑
```

### InstanceManager（1个）
```lua
m_genericItemIM = InstanceManager:new("ItemInstance", "Top", Controls.ScrollStack)
```

---

## StatusMessagePanel — 状态消息

### 两种消息实例

**StatusMessageInstance**（普通状态）：
```xml
<Container ID="Root" Size="220,auto">
  <AlphaAnim ID="Anim" AlphaBegin="0" AlphaEnd="1" Speed="3" Cycle="OneBounce" EndPause="10">
    <GridButton ID="Button" Size="parent+10,auto" Style="EnhancedToolTip">
      <Label ID="Message" Style="BodyText12"/> ← 状态文本
    </GridButton>
  </AlphaAnim>
</Container>
```

**GossipMessageInstance**（流言消息）：
```xml
<Container ID="Root" Size="auto,auto">
  <AlphaAnim ID="Anim" EndPause="1"> ← 快速消失
    <Container ID="Content" Size="400,52" Texture="Controls_GossipContainer">
      <Image ID="Icon" Size="32,32"/> ← 类型图标
      <Label ID="Message" MinSize="305,14" WrapWidth="305"/>
      <Button ID="ExpandButton"/> ← 展开/折叠
    </Container>
  </AlphaAnim>
</Container>
```

### InstanceManager（2个）
```lua
m_gossipIM = InstanceManager:new("GossipMessageInstance", "Root", Controls.GossipStack)
m_statusIM = InstanceManager:new("StatusMessageInstance", "Root", Controls.DefaultStack)
```

### 消息生命周期
```
1. Events.StatusMessage → OnStatusMessage
2. AddGossip() 或 AddDefault() → 创建实例
3. AlphaAnim EndCallback → 自动移除实例
```
