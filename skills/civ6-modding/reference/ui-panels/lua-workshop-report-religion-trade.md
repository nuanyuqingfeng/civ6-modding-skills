# ReportScreen + ReligionScreen + TradeOverview — 报告/宗教/贸易

> **来源**：`Screens/ReportScreen.xml`(768行) + `.lua`(1858行) + `ReligionScreen.xml`(387行) + `.lua`(1580行) + `TradeOverview.xml`(195行) + `.lua`(830行) + `Choosers/TradeRouteChooser.*` + `TradeOriginChooser.*`
> **地位**：全屏报告/宗教/贸易面板——TabSupport 标签系统+可折叠组+路线选择器。

---

## ReportScreen — 多页报告

### TabSupport 标签
```lua
AddTabSection("YIELDS", ViewYieldsPage)
AddTabSection("RESOURCES", ViewResourcesPage)
AddTabSection("CITY_STATUS", ViewCityStatusPage)
AddTabSection("GOSSIP", ViewGossipPage)
```

### XML 结构
```
Box(Main)
  TabArea → TabContainer → TabAnim/TabArrow
  ScrollPanel(Scroll) → Stack(Stack)
  BottomYieldTotals ← 底部产出合计
    Label(GoldIncome/FaithIncome/ScienceIncome/CultureIncome/TourismIncome)
    Label(GoldExpense/GoldNet/FaithNet/...)
  BottomResourceTotals
    StrategicGrid → StrategicResources
    BonusGrid → BonusResources
    LuxuryGrid → LuxuryResources
```

### 可折叠组（GroupInstance）
```xml
<Instance Name="GroupInstance">
  <Container ID="Top">
    <GridButton ID="RowHeaderButton"/> ← 展开/折叠按钮
    <Image ID="RowExpandCheck"/> ← 展开箭头
    <ScrollPanel ID="CollapseScroll">
      <SlideAnim ID="CollapseAnim"> ← 折叠动画
        <Stack ID="ContentStack"/> ← 动态填充内容
      </SlideAnim>
    </ScrollPanel>
  </Container>
</Instance>
```

### 城市收入实例（CityIncomeInstance）
最复杂的实例——22×7 列布局：CityName + LineItemStack (Building/District/... × 6列产出值) + 进度条。每个城市行包含 `Food/Gold/Faith/Science/Culture/Tourism` 6列数值。

### InstanceManager（5个）

```lua
m_simpleIM        = InstanceManager:new("SimpleInstance", "Top", Controls.Stack)
m_tabIM           = InstanceManager:new("TabInstance", "Button", Controls.TabContainer)
m_groupIM         = InstanceManager:new("GroupInstance", "Top", Controls.Stack)
m_strategicResourcesIM = InstanceManager:new("ResourceAmountInstance", "Info", ...)
m_bonusResourcesIM     = InstanceManager:new("ResourceAmountInstance", "Info", ...)
m_luxuryResourcesIM    = InstanceManager:new("ResourceAmountInstance", "Info", ...)
```
城市收入行使用 `ContextPtr:BuildInstanceForControl("CityIncomeInstance", ...)`。

---

## ReligionScreen — 宗教管理

### 状态机流程
```
WorkingTowardsPantheon → WorkingTowardsReligion
  → SelectPantheonBeliefs → ChooseReligion
  → SelectReligionBeliefs → ViewReligion → ViewAllReligions
```

### 关键控件
```
PullDown(FilterType) ← 城市过滤
ScrollPanel(CitiesScrollbar) → Stack(Cities) ← 城市列表
ScrollPanel(ReligionsScrollbar) → Stack(Religions) ← 所有宗教

← 选择信仰
ScrollPanel(AvailableBeliefsScrollbar) → Stack(AvailableBeliefs) ← 可选信仰

← 查看宗教
Image(ViewReligionImage) + Stack(ViewReligionStack)
  Label(ViewReligionTitle/Founder/HolyCity/Dominance)
  ScrollPanel(ViewReligionScroll) → Stack(ViewReligionBeliefs)
```

### Instance（10个）

| 实例 | 用途 |
|------|------|
| `ReligionTab` | 标签按钮（含Icon） |
| `BeliefSlot` | 可选信仰槽 |
| `ReligionBelief` | 已选信仰展示 |
| `ReligionOption` | 选择宗教按钮 |
| `ReligionIcon` | 宗教图标 |
| `City` | 城市行（CityName+Followers+Pantheon） |
| `Religion` | 宗教行（名称+创始人+城市+信仰列表） |
| `ReligionBeliefSmall` | 小号信仰条目 |
| `UnitIconInstance` | 宗教单位图标 |

### InstanceManager（13个）

绝大多数列表都有独立IM：`m_CitiesIM`, `m_ReligionsIM`, `m_ReligionTabsIM`, `m_ReligionIconsIM`, `m_AddAvailableBeliefsIM`, `m_SelectBeliefsIM`, `m_SelectedBeliefsIM`, `m_ReligionBeliefsIM`, `m_ReligionSelections`, `m_UnitIconIM`等。

---

## TradeOverview — 贸易总览

### 3标签结构
```
MyRoutesButton / RoutesToCitiesButton / AvailableRoutesButton
  (每个=GridButton + Selected变体 + TabLabel + Arrow)

HeaderFrame
  HeaderStack ← HeaderLabel + ActiveRoutesLabel

ScrollPanel(BodyScrollPanel) → Stack(BodyStack) ← 动态填充
```

### 布局分组
每类路线按目的地玩家分组：
```lua
CreatePlayerHeader(player) → HeaderInstance
  → 为每条路线 AddRouteFromRouteInfo() → RouteInstance
CreateCityStateHeader() → 城邦路线
CreateUnusedRoutesHeader() → 空闲商人
```

### RouteInstance
```xml
<Instance Name="RouteInstance">
  <Container ID="Top">
    <GridButton ID="GridButton"/>
    <Label ID="RouteStatusFontIcon"/> ← 状态图标
    <Label ID="RouteLabel"/> ← 路线名
    <Image ID="OriginCivIcon"/> → Image ID="DestinationCivIcon"/> ← 起止文明
    <Stack ID="ResourceStack"/> ← 收益资源列表
    <Label ID="RouteDistance"/> ← 距离
  </Container>
</Instance>
```

### InstanceManager（4个）
```lua
m_RouteInstanceIM       = InstanceManager:new("RouteInstance", "Top", Controls.BodyStack)
m_HeaderInstanceIM      = InstanceManager:new("HeaderInstance", "Top", Controls.BodyStack)
m_SimpleButtonInstanceIM = InstanceManager:new("SimpleButtonInstance", "Top", ...)
```

---

## TradeRouteChooser — 路线选择器

```
SlideAnim(RouteChooserSlideAnim) ← 从左侧滑入 (Begin="-350,0")
  
  TopGrid ← 当前选择预览
    Label(CityName) + Label(ChosenRouteTurns/DistenceToCity)
    出发/到达收益列（OriginResources / DestinationResources）
  
  BottomGrid ← 可选路线列表
    PullDown(DestinationFilterPulldown) ← 按文明/资源/城邦过滤
    ScrollPanel(RouteChoiceScrollPanel) → Stack(RouteChoiceStack)
  
  ConfirmGrid ← 确认/取消按钮
    GridButton(BeginRouteButton) + GridButton(CancelButton)
```

### 过滤系统
```lua
AddFilter("All", filterAllFn)
AddFilter("CityStates", FilterByCityStates)
AddFilter("CivName", FilterByCiv(civID))
AddFilter("ResourceName", FilterByResource(yieldIndex))
```

### 路径绘制（UILens）
```lua
AddTradeRoutePath(entry, color) → UILens.SetLayerHexesArea(lensHash, ...)
```

---

## TradeOriginChooser — 贸易起点选择器

最简洁的面板：
```xml
<SlideAnim>
  <Button(CloseButton) ← 样式 ArrowButtonLeft
  <ScrollPanel(CityScrollPanel) → Stack(CityStack) ← 城市按钮列表
</SlideAnim>
```

单实例 `CityInstance` ← GridButton `CityButton`。选择后通过 `TeleportToCity() → UnitOperationTypes.PARAM_OPERATION_TYPE` 传送镜头。
