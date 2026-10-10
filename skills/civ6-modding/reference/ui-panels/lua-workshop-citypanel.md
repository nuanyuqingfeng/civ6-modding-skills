# CityPanel — 城市详情面板

> **来源**：`Panels/CityPanel.xml`(190行) + `.lua`(1336行) + `CityPanelOverview.xml`(511行) + `.lua`(1131行)
> **地位**：选中城市后右下角弹出的城市信息面板——产出/人口/建筑/生产/MOD按钮注入。

---

## XML 结构（主面板 CityPanel.xml）

```
AlphaAnim(CityPanelAlpha) ← 打开动画 (R,B, Speed=4)
  SlideAnim(CityPanelSlide) ← Start="0,0" End="-73,0" 向左滑入
    GridButton(MainPanelBacking) ← 木纹背景 (500×162)
      
      ← 左侧头像区：
      Image(PortraitFrame) ← 城市肖像框
      Container(LabelButtonRows) ← 建筑/宗教/设施/住房统计
        Grid×4 + Label×4 (Num + 英文标签)
      TextureBar(GrowthTurnsBar) ← 增长进度条
      Meter(CityHealthMeter) ← 城防血条 (95×95, Percent=".6")
      Meter(WallHealthMeter) ← 城墙血条 (110×110)
      Image(CivIcon) ← 文明图标 (Circle80 三层叠加)
      
      ← 右侧生产区：
      ScrollPanel(ProductionDataScroll) ← 生产信息滚动区
      TextureBar(ProductionTurnsBar) ← 生产进度条
      
      ← 顶部产量区：
      Stack(YieldStack) ← 6个产量格子
        CheckBox×6 + Button×6 ← Culture/Food/Production/Science/Faith/Gold
      
      ← 操作栏（MOD注入点★）：
      Stack(ActionStack) ← StackGrowth=Right
        CheckBox×6 ← PurchaseTile/ManageCitizens/ProduceWithGold/Faith/ChangeProduction/ToggleOverview
```

## ActionStack — MOD 按钮注入点

```xml
<Stack ID="ActionStack" StackGrowth="Right" Padding="3">
    <CheckBox ID="PurchaseTileCheck" ... />
    <CheckBox ID="ManageCitizensCheck" ... />
    <!-- MOD 在此添加自定义 CheckBox -->
</Stack>
```

MOD 通过 `Controls.ActionStack` 注入按钮：
```lua
-- 在 LateInitialize 中
local cb = Controls.ActionStack:CreateCheckBox("MyAction", "MyTexture", "MyTooltip")
cb:RegisterCheckHandler(function() ... end)
```

## CityPanelOverview — 全屏城市详情

通过 `LuaEvents.CityPanel_LiveCityDataChanged` 接收 CityPanel 的数据表，避免重复计算。

**标签系统**（TabSupport）：
```lua
AddTab(healthButton, OnSelectHealthTab)    ← 市民/增长
AddTab(buildingsButton, OnSelectBuildingsTab) ← 建筑/区域
AddTab(religionButton, OnSelectReligionTab)   ← 宗教
```

MOD 可调用 `AddTab(uiButton, callback)` 和 `GetTabButtonInstance()` 扩展标签。

**InstanceManager**（8个）：`AmenityInstance`, `HousingInstance`, `BuildingInstance`, `DistrictInstance`, `WonderInstance`, `TradingPostInstance`, `ReligionBeliefsInstance`, `ProductionInstance`

## 数据流

```
CityPanel.GetCityData(city) → m_kData
  ↓ ViewMain(m_kData) ← 填充主面板
  ↓ LuaEvents.CityPanel_LiveCityDataChanged(m_kData)
  ↓ CityPanelOverview.OnLiveCityDataChanged → Refresh()
```

## 事件注册

**游戏事件**（17个）：`CitySelectionChanged`, `CityProductionChanged/Completed/Updated`, `CityFocusChanged`, `CityWorkerChanged`, `DistrictDamageChanged`, `GreatWorkCreated/Moved`, `PlayerResourceChanged`, `UnitSelectionChanged` 等

**LuaEvents**：`CityPanelOverview_CloseButton`, `ProductionPanel_Open/Close`, `Tutorial_CityPanelOpen`, `Tutorial_ContextDisableItems`
