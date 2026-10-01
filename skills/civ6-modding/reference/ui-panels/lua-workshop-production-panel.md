# ProductionPanel + LaunchBar + TopPanel — 三大 HUD 条

> **来源**：`ProductionPanel.xml`(521行) + `ProductionManager.lua` + `ProductionHelper.lua` + `LaunchBar.xml/.lua` + `TopPanel.xml/.lua`
> **地位**：生产选择面板、科技/市政启动栏、顶部产出栏——构成游戏主要 HUD 的三块面板。

---

## ProductionPanel — 生产选择器

```
AlphaAnim(AlphaIn) + SlideAnim(SlideIn) ← 从右侧滑入 (Begin="330,0")
  Grid(Window) ← 窗口框架
    Tab系统(ProductionTab/PurchaseTab/PurchaseFaithTab/QueueTab/ManagerTab)
      + Mini变体 + TabAnim/TabArrow
    Container(CurrentProductionContainer) ← 当前生产中项目
      TextureBar(CurrentProductionProgress) ← 进度条
      FlipAnim(GearAnim) ← 齿轮动画
    ScrollPanel(ProductionListScroll) ← 主生产列表
      Stack(ProductionList) ← 动态填充列表项
    ScrollPanel(QueueListScroll) ← 生产队列
    ScrollPanel(PurchaseListScroll) ← 金币购买
    ScrollPanel(PurchaseFaithListScroll) ← 信仰购买
```

### 实例（5种列表项类型）

| 实例 | 用途 | 尺寸 |
|------|------|------|
| `NestedList` | 可展开分类标题 + 子列表 | 325×auto |
| `BuildingListInstance` | 建筑/奇观 | 320×48 |
| `DistrictListInstance` | 区域 | 320×48 |
| `CivilianListInstance` | 平民单位 | 320×56 |
| `UnitListInstance` | 军事单位 | 320×56 (含军团/军队扩展) |
| `ProjectListInstance` | 项目 | 320×48 |
| `ProductionQueueItem` | 队列槽位 | 42×48 |

### InstanceManager
```lua
m_CityInstanceIM = InstanceManager:new("CityInstance", "CityButton", Controls.CityStack)
-- 生产列表项是动态 BuildInstanceForControl
```

### LuaEvents
- `ProductionPanel_ToggleManager` / `_OpenManager` / `_CloseManager` (来自 CityPanel)
- `ProductionPanel_ProductionClicked` / `_CancelManagerSelection`

---

## LaunchBar — 科技/市政启动栏

```
Container(LaunchContainer) ← 左侧竖条
  Stack(ButtonStack) ← StackGrowth=Right, Padding=-2
    Button(ScienceButton) ← 51×51 科技按钮
      Image(ScienceHookWithMeter) ← 隐藏的带表盘背景
        Meter(ScienceMeter) ← 科技进度 (57×57, Follow=1)
    Button(CultureButton) ← 51×51 市政按钮
      Meter(CultureMeter) ← 市政进度 (57×57, Follow=1)
    Button(GovernmentButton) ← 49×49 政体
    Button(ReligionButton) ← 49×49 宗教
    Button(GreatPeopleButton) ← 49×49 伟人
    Button(GreatWorksButton) ← 49×49 巨作
    Image×6 ← Bolt pips 分隔符
```

### Meter 更新模式
```lua
function UpdateTechMeter(localPlayer)
    local progress = playerTechs:GetResearchProgress(TechType)
    local cost = playerTechs:GetResearchCost(TechType)
    Controls.ScienceMeter:SetPercent(progress / cost)
    -- 同时设置按钮图标为当前研究科技的图标
end
```

### 实例
| 实例 | 用途 |
|------|------|
| `LaunchBarItem` | MOD 可动态添加的启动栏按钮 (49×49) |
| `LaunchBarPinInstance` | 跟踪标记 (7×7) |

### 事件（19个游戏事件驱动刷新）
`ResearchChanged`, `CivicChanged`, `CivicCompleted`, `GovernmentChanged`, `GovernmentPolicyChanged`, `FaithChanged`, `GreatWorkCreated`, `TreasuryChanged`, `AnarchyBegins/Ends` 等

---

## TopPanel — 顶部产出栏

```
Grid(Backing) ← 顶部横条 (parent+100,29)
  Stack(RightContents) ← 右侧：菜单/百科/时间
  Stack(InfoStack) ← 左侧：产出
    Stack(YieldStack) ← 6个产出按钮位
    Stack(StaticInfoStack)
      Grid(TradeRoutes) ← 贸易路线数+容量
      Grid(Envoys) ← 使者进度
        Meter(EnvoysMeter) ← 24×24 使者圆点 (Follow=1)
      Grid(Resources) ← 战略资源
```

### 实例（产出按钮变体）

| 实例 | 用途 | 结构 |
|------|------|------|
| `YieldButton_SingleLabel` | 科技/文化/旅游 | YieldIconString + YieldPerTurn |
| `YieldButton_DoubleLabel` | 信仰/金币 | YieldIconString + YieldBalance + YieldPerTurn |
| `ResourceInstance` | 单个资源 | ResourceText + ResourceVelocity |
| `TopBarButtonInstance` | 自定义按钮 | 50×36 环形背景按钮 |

### 数据更新
`RefreshYields()` → 重建所有产出按钮 → 从玩家对象获取各产出值 → 格式化并设置文本/颜色。`RefreshInfluence()` → 计算 `influenceBalance/threshold` → `EnvoysMeter:SetPercent(ratio)`。

### 事件（27个游戏事件驱动刷新）
`CityFocusChanged`, `CityWorkerChanged`, `FaithChanged`, `GovernmentChanged`, `InfluenceChanged`, `TradeRouteActivityChanged`, `TreasuryChanged`, `PlayerResourceChanged`, `WMDCountChanged` 等
