# InGame 控件树 — 游戏 UI 框架全景

> **来源**：`InGame.xml`(139行) + `InGame.lua`(386行)
> **地位**：所有游戏内 UI 的根容器，定义 11 层渲染层级和 LuaContext 加载机制。

---

## 渲染层级（自底向上）

所有游戏内 UI 面板按以下顺序堆叠（越靠后越在上层）：

| 层 | 容器 ID | 包含的面板 | 是否受 BulkHide |
|----|---------|-----------|----------------|
| 1 | `Core` | WorldInput, StrategicView, ARXManager | 否 |
| 2 | `WorldViewControls` | CityBannerManager, UnitFlagManager, MapPinManager, PlotInfo, SelectedUnit, TourismBanner, 等 | ✅ |
| 3 | `HUD` | ActionPanel, CityPanel, UnitPanel, MinimapPanel, WorldTracker, NotificationPanel, StatusMessagePanel, PlotToolTip | ✅ |
| — | `EdgeScroll`（独立） | 屏幕边缘滚动 | 否 |
| 4 | `PartialScreens` | TopPanel, DiplomacyRibbon, CityStates, EspionageOverview, WorldRankings, TradeOverview, ReportsList, ProductionPanel, PartialScreenHooks | ✅ |
| 5 | `Screens` | TechTree, CivicsTree, GovernmentScreen, ReligionScreen, GreatWorksOverview, GreatWorkShowcase, ReportScreen, FullscreenMapPopup 等 | ✅ |
| 6 | `TopLevelHUD` | LaunchBar, 各类 Chooser, CityPanelOverview, ModalLensPanel | ✅ |
| 7 | `WorldPopups` | EraComplete, NaturalWonder, WonderBuilt, EventPopup, UnitPromotion, EspionagePopup 等（整层默认隐藏） | 否 |
| 8 | `FakePopups` | ChooseArtifact, EspionageEscape, UnitCaptured, InGamePopup | 否 |
| 9 | `Diplomacy` | LeaderScene, DiplomacyActionView, DiplomacyDealView, DeclareWarPopup | 否 |
| 10 | `EndGame` | EndGameMenu | 否 |
| 11 | `Network` | PlayerChange, NewTurnPanel | 否 |
| — | `Civilopedia`（独立） | 百科 | 否 |
| — | `PausePanel`（独立） | 暂停面板 | 否 |
| — | `AdditionalUserInterfaces` | **Mod 注入到此容器** | 否 |

---

## LuaContext 加载机制

每个面板通过 `<LuaContext>` 标签绑定：

```xml
<LuaContext ID="TechTree" FileName="TechTree" Hidden="1" />
```

**自动加载规则**：
1. 引擎加载 `FileName.lua`
2. 引擎自动加载同目录下的 `FileName.xml`
3. Lua 中 `ContextPtr` 指向该上下文根
4. `Hidden="1"` → 初始不显示，Lua 通过 `ContextPtr:SetHide(false)` 显示

**路径规则**：`FileName="WorldView/CameraManager"` → 加载 `WorldView/CameraManager.lua` + `CameraManager.xml`

---

## Mod 注入点

### AdditionalUserInterfaces（首选）

```xml
<!-- InGame.xml 第132-133行 -->
<Container ID="AdditionalUserInterfaces"/>
```

**modinfo 注册**：
```xml
<InGameActions>
    <AddUserInterfaces>
        <Item ContextPath="InGame/MyCustomPanel" />
    </AddUserInterfaces>
</InGameActions>
```

**运行时加载**（InGame.lua 第344行）：
```lua
for i, addin in ipairs(Modding.GetUserInterfaces("InGame")) do
    local id = addin.ContextPath:sub(ContextPath:find("/[^/]*$") + 1)
    local ctx = ContextPtr:LoadNewContext(addin.ContextPath, 
        Controls.AdditionalUserInterfaces, id, true)
    table.insert(g_uiAddins, ctx)
end
```

关键：Mod UI 始终 `isHidden=true` 加载，Mod 自身 Lua 调用 `ContextPtr:SetHide(false)` 显示。**不在 BulkHide 管理范围内**——外交屏/全屏地图切换不会影响 Mod UI。

### PartialScreenHooks

```xml
<LuaContext ID="PartialScreenHooks" FileName="PartialScreenHooks" />
```
用于劫持/替换 PartialScreens 层内的面板。见 `lua-workshop-partial-screen-hooks.md`。

### ActionStack（城市/单位面板按钮注入）

CityPanel 的 `<Stack ID="ActionStack">` 和 UnitPanel 的 `<Stack ID="StandardActionsStack">` 是操作按钮注入点。见 `lua-ui-button.md`。

---

## BulkHide 系统

当全屏面板（外交、全屏地图、末日菜单）打开时，需要隐藏 5 个 HUD 层：

```lua
-- InGame.lua 第161行
local kGroups = {"WorldViewControls", "HUD", "PartialScreens", "Screens", "TopLevelHUD"}
```

**不受 BulkHide 影响的层**（Mod UI 安全区）：
`Core`, `WorldPopups`, `FakePopups`, `Diplomacy`, `EndGame`, `Network`, `AdditionalUserInterfaces`, `Civilopedia`, `PausePanel`, `TopOptionsMenu`

### BulkHide 配对事件

| LuaEvent | 动作 |
|----------|------|
| `DiplomacyActionView_HideIngameUI` + `_ShowIngameUI` | 外交屏 |
| `EndGameMenu_Shown` + `_Closed` | 游戏结束 |
| `FullscreenMap_Shown` + `_Closed` | 全屏地图 |
| `NaturalWonderPopup_Shown/Closed` | 自然奇观弹窗 |
| `WonderBuiltPopup_Shown/Closed` | 奇观建成弹窗 |
| `ProjectBuiltPopup_Shown/Closed` | 项目建成弹窗 |

---

## Initialize 启动流程（InGame.lua 第339-386行）

```lua
Initialize():
  1. 获取本地玩家：m_activeLocalPlayer = Game.GetLocalPlayer()
  2. 加载所有 Mod UI：Modding.GetUserInterfaces("InGame") → LoadNewContext
  3. 注册 ContextPtr 处理器：SetInputHandler, SetShowHandler, SetRefreshHandler, SetShutdown
  4. 注册 UIManager 弹窗变化处理器
  5. 注册 GameCore 事件：LoadGameViewStateDone, LocalPlayerTurnBegin/End, SystemUpdateUI 等
  6. 注册 LuaEvents：所有 BulkHide 配对事件
```

---

## 键盘快捷键

| 按键 | 行为 |
|------|------|
| ESC | 打开 TopOptionsMenu（Shell 菜单） |
| Shift+Alt+B | 强制取消 BulkHide |
| Shift+Alt+J | 切换 BulkHide 状态 |
