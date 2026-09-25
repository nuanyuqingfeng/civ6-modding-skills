# UI Lua + XML (ForgeUI)

## Step-by-Step: Creating a New In-Game UI Panel

### Step 1 — Create XML Layout

Define a standalone `<Context>` with your controls:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Context Name="MyPanel">
    <Container ID="MainContainer" Size="parent,parent" Anchor="C,C" Hidden="1" ConsumeMouseButton="1">
        <Image ID="Background" Size="parent,parent" Color="0,0,0,180" ConsumeMouseButton="1"/>
        <GridButton ID="CloseButton" Anchor="R,T" Offset="-40,40" Size="40,40"
                    Texture="Controls_Close" SliceCorner="14,14" SliceTextureSize="28,28"/>
        <Label ID="TitleLabel" Anchor="C,T" Offset="0,60"
               String="LOC_MY_PANEL_TITLE" Font="Font_22"/>
        <ScrollPanel ID="ContentScroll" Anchor="C,C" Size="800,550" ScrollBarAutoHide="1">
            <Stack ID="ItemStack" Anchor="T,L" StackGrowth="Vertical"/>
        </ScrollPanel>
    </Container>
</Context>
```

Key points:
- `<Context Name="...">` becomes the path segment for `LookUpControl`
- Fullscreen overlay: `Size="parent,parent" Anchor="C,C"` + semitransparent `Image` background
- Start the overlay container with `Hidden="1"` (shown later via Lua)

### Step 2 — Create Lua Script

```lua
-- Normal flow:     OnInit(isReload=false) => register callbacks(**Note: all registered callbacks should be unregistered in OnShutdown**) => Initialize().

-- Callback flow : Players click a button => OnShow() => click close button => Close() => hide container.
-- Hot-reload flow has three paths: 
-- first path(RECOMMENDED): OnShutdown() save state via LuaEvents.GameDebug_AddValue() => OnInit(isReload=true) LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID); => Trigger GameDebug_Return event to execute OnGameDebugReturn() to restore state and refresh the context.
-- second path: OnShutdown() but no cache => OnInit(isReload=true) Refresh() =>Refresh and reconstruct the context.
-- third path: OnShutdown() but no cache => OnInit(isReload=true) ContextPtr:RequestRefresh() Trigger registered refresh handler(this path is used to refresh the context in other files).

-- Init vs Hot Reload pattern:

REGISTERS = {}
REGISTERS_CACHE = {} -- restore external UI state on hot-reload
RELOAD_CACHE_ID = "MyPanel";

CALLBACKS = {
    CloseButton_Click:function()
        ContextPtr:SetHide(true);
    end,
    CallbakeKey2:function(arg1,arg2,...)
        -- do something
    end,
}

function OnInit(isReload:boolean)
    if isReload then
        --Three paths to reload
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID); -- first path
        Refresh(); -- second path
        ContextPtr:RequestRefresh(); -- third path
    end
end

function ShowPanel()
    ContextPtr:SetHide(false);  -- mod contexts start hidden, must show
end

function OnShow()
    -- Called every time the context transitions to visible
    -- Use for refresh-on-become-visible, NOT one-time init
end

function Close()
    ContextPtr:SetHide(true);
end

function OnInputHandler(pInputStruct:table)
    local uiMsg = pInputStruct:GetMessageType();
    if uiMsg == KeyEvents.KeyUp and pInputStruct:GetKey() == Keys.VK_ESCAPE then
        Close();
        return true;
    end
    return false;
end

function OnShutdown()
    -- Unregister callbacks
    UnregisterCallbacks()
    -- Unsubscribe events
    UnsubscribeEvents()
    -- Save state for hot-reload
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, "REGISTERS_CACHE", REGISTERS_CACHE);
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, "SomeKey", someValue);
end

function OnGameDebugReturn(context:string, contextTable:table)
    if context == RELOAD_CACHE_ID then 
        someValue = contextTable["someKey"];
        if contextTable["isHidden"] ~= nil and (not contextTable["isHidden"]) then
            ShowPanel();
        end
        if contextTable["REGISTERS_CACHE"] ~= nil then
            for i, registerpack in pairs(contextTable["REGISTERS_CACHE"]) do
                RegisterCallback(registerpack[1],registerpack[2],registerpack[3],true)
            end
        end
    end
end



function RegisterCallback(control:table,operation:number, callback:string,withCache:boolean)
    -- withCache is used to save external UI callback info for hot-reload
    control:RegisterCallback(operation, CALLBACKS[callback])
    local registerpack = {control, operation,callback};
    table.insert(REGISTERS,registerpack)
    if withCache then
        table.insert(REGISTERS_CACHE,registerpack)
    end
end

function UnregisterCallbacks()
    for i, registerpack in ipairs(REGISTERS) do
        registerpack[1]:ClearCallback(registerpack[2])
    end
end



function AttachControls()
    -- lookup target UI and attach controls or build instances
end

function LocalControlsRegister() -- Register common controls that can access via Controls table,not instances.
    local controls ={
        {Controls.CloseButton,Mouse.eLClick,"CloseButton_Click"}, --operation is Mouse.eLClick or others
        {Controls.B,operation,callbackKey2},
        {Controls.C,operation,callbackKey3},
    }
    for i, control in ipairs(controls) do
        RegisterCallback(control[1],control[2], control[3],false)
    end
end

function OnLoadGameViewStateDone()
    LocalControlsRegister()
    AttachControls()
end

function SubscribeEvents()
    Events.LoadGameViewStateDone.Add(OnLoadGameViewStateDone)
    Events.SomeOtherEvent.Add(OnSomeOtherEvent)

    LuaEvents.GameDebug_Return.Add( OnGameDebugReturn );
end

function UnsubscribeEvents()
    Events.LoadGameViewStateDone.Remove(OnLoadGameViewStateDone)
    Events.SomeOtherEvent.Remove(OnSomeOtherEvent)

    LuaEvents.GameDebug_Return.Remove( OnGameDebugReturn );
end

function Initialize()
    SubscribeEvents();

    -- Some common handlers,but they are not necessary in any case.
    ContextPtr:SetInitHandler(OnInit); --Set a callback function when the first context has just finished initializing. The callback function will also be called when a hotload occurs.
    ContextPtr:SetRefreshHandler(OnRefresh); --Sets a callback function which will occur explicitly, once on C++ Update(). Used when a lot of values are changing but rather than realize real-time, a delay is fine; usually to prevent recomputing sub-pieces of a complex screen.
    ContextPtr:SetShowHandler(OnShow);
    ContextPtr:SetInputHandler(OnInputHandler, true);
    ContextPtr:SetShutdown(OnShutdown);
end
Initialize();
```

### Step 3 — Register in .modinfo

```xml
<AddUserInterfaces id="MyPanelUI" criteria="MyCriteria">
    <Properties><Context>InGame</Context></Properties>
    <File>UI/Additions/MyPanel.xml</File>
</AddUserInterfaces>
<ImportFiles id="MyPanelFiles" criteria="MyCriteria">
    <File>UI/Additions/MyPanel.lua</File>
</ImportFiles>
```

### Step 4 — Understand How Mod Contexts Load

InGame.lua loads mod UIs like this:

```lua
-- InGame.lua:348
for i, addin in ipairs(Modding.GetUserInterfaces("InGame")) do
		print("Loading InGame UI - " .. addin.ContextPath);
		local id		:string = addin.ContextPath:sub( -(string.find( string.reverse(addin.ContextPath), '/') - 1) );		-- grab id from end of path
		local isHidden	:boolean = true;
		local newContext:table = ContextPtr:LoadNewContext(addin.ContextPath, Controls.AdditionalUserInterfaces, id, isHidden);	-- Content, ID, hidden
end
--Log
InGame: Loading InGame UI - ../../../DLC/Expansion2/UI/Additions/GovernorPanel
InGame: Loading InGame UI - ../../../DLC/Expansion2/UI/Additions/HistoricMoments
InGame: Loading InGame UI - ../../../DLC/Expansion2/UI/Additions/WorldCrisisPopup
InGame: Loading InGame UI - ../Mods/<YourMod>/UI/Additions/YourPanel
InGame: Loading InGame UI - ../Mods/<YourMod>/UI/Additions/AnotherPanel
InGame: Loading InGame UI - ../Mods/<YourMod>/UI/Additions/ThirdPanel
```

**Consequences:**
- Mod contexts are placed under `/InGame/AdditionalUserInterfaces/<Name>`
- They start **hidden** — you must call `ContextPtr:SetHide(false)` to show them
- `OnShow` fires when the context transitions hidden→visible (not at load time)
- While hidden, controls still exist and can receive `ChangeParent` / `RegisterCallback`

### Step 5 — Fullscreen Panel Pattern (Show/Hide/ESC)

The standard fullscreen panel lifecycle:

| Action | Code |
|--------|------|
| Open | `ContextPtr:SetHide(false)` → `OnShow` fires |
| Close | `ContextPtr:SetHide(true)` |
| ESC close | `OnInputHandler` returns `true` for `Keys.VK_ESCAPE` |
| Toggle | Track `ContextPtr:IsHidden()` state |
| Close other panels | Fire `LuaEvents.LaunchBar_Close*` events before showing |

### Step 6 — Add new UI to Existing UI (ChangeParent)
Beacuse this is a modding skill,the UI of mods are placed in the AdditionalUserInterfaces folder.So,we should add custom ui to the existing UI.We can use `ChangeParent` function to move the UI to the target UI or use target UI to build instances.
**We should use LookupControl to get the target UI,but the target UI can not be get in the init function,so we should attach or build instances in the Events.LoadGameViewStateDone**
If using build instances ,change parent is may not necessary.
Define the button in your XML, then move it to the target via `ChangeParent`(ChangeParent usually executes once per game,so it should be placed in init function):

```xml
<!-- In your panel XML -->
<Button ID="LaunchButton" Anchor="L,C" Size="49,49" Hidden="1"
        Texture="LaunchBar_Hook_GovernmentButton" Style="ButtonNormalText"
        StateOffsetIncrement="0,49" ToolTip="LOC_MY_TOOLTIP">
    <Image ID="LaunchIcon" Size="35,35" Anchor="C,C" Offset="0,0"/>
</Button>
```

```lua

function AttachControls()
    local target = ContextPtr:LookUpControl("/InGame/LaunchBar/ButtonStack");
    if target then
        Controls.LaunchButton:ChangeParent(target);
        --or build instances
        local m_Instance = {}
        ContextPtr:BuildInstanceForControl(instanceName, m_Instance, target);
        m_Instance.SubControlName:Operation(); --We can access the instance's sub-controls via m_Instance.
    end
end
```

### Step 7 — Cross-Context Communication (LuaEvents)

Two different UI contexts communicate via LuaEvents:

**Sender context (e.g., LaunchBar replacement):**
```lua
LuaEvents.MyPanel_Open(data);
```

**Receiver context (your panel):**
```lua
function OnOpenRequest(data)
    ContextPtr:SetHide(false);
end
LuaEvents.MyPanel_Open.Add(OnOpenRequest);
```

---

## Context Lifecycle

```lua
ContextPtr:SetInitHandler( OnInit );  -- First load or reload
ContextPtr:SetShowHandler( OnShow );              -- Context becomes visible
ContextPtr:SetRefreshHandler( OnRefresh );         -- Called on RequestRefresh()
ContextPtr:SetInputHandler( OnInputHandler, true ); -- Input (true=extended)
ContextPtr:SetShutdown( OnShutdown );              -- Before unload
```

> **Shutdown 触发：`OnShutdown` 与普通函数一样，必须用 `ContextPtr:SetShutdown(OnShutdown)` 注册后才会在上下文销毁时被调用。定义 OnShutdown 时这一行不能省。**

| Handler | Fires When | Use For |
|---------|-----------|---------|
| `SetInitHandler` | Context created or hot-reloaded | Register events, create instances |
| `SetShowHandler` | Hidden → Visible transition | Refresh displayed data |
| `SetRefreshHandler` | `ContextPtr:RequestRefresh()` called | On-demand content refresh |
| `SetInputHandler` | Input received (if `true` = extended) | Hotkeys, ESC handling |
| `SetShutdown` | Context about to destroy | Remove event listeners |

**CRITICAL: `OnShow` is NOT a one-time init.** It fires every time hidden→visible. Do not use it for initial setup (use `OnInit`). Never call `SetHide(true)` inside `OnShow` — it hides the context and kills all further input/refresh.

### LoadGameViewStateDone — Wait for Game to Finish Loading

In `OnInit`, distinguish first load from hot reload:

```lua
function OnInit(isReload:boolean)
    if isReload then
        -- GameDebug function is same as Reload()
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID);
        Reload(); --Reload or trigger ContextPtr:RequestRefresh()
    end
end
```

---

## UI Replacement: include + Redefine (Compatibility Chain)

Instead of copying the entire base Lua file, re-use the original by `include()` and redefining only changed functions:

```lua
-- Save the original function reference
local BASE_MyFunction = MyFunction;

-- Override
function MyFunction(params)
    if someCondition then
        return customResult;
    end
    return BASE_MyFunction(params);  -- fall through to original
end
```

Compatibility chain for multiple mods:
```lua
include("UnitPanel.lua");
pcall(function() include("UnitPanel_Expansion1.lua"); end);
pcall(function() include("UnitPanel_Expansion2.lua"); end);
-- Include compatible mod files with lower LoadOrder
pcall(function() include("OtherMod_UnitPanel.lua"); end);

local BASE_SomeFunc = SomeFunc;
function SomeFunc(params)
    -- your override
    return BASE_SomeFunc(params);
end
```

---

## LookUpControl — Navigate the Context Tree

Navigates the context hierarchy, NOT the control hierarchy. Path segments are context/LuaContext names, with the final segment being a control ID.

```lua
-- Mod-added context under AdditionalUserInterfaces:
ContextPtr:LookUpControl("/InGame/AdditionalUserInterfaces/MyPanel/MainContainer");

-- Base game contexts directly under InGame:
ContextPtr:LookUpControl("/InGame/LaunchBar/ButtonStack");
ContextPtr:LookUpControl("/InGame/UnitPanel/StandardActionsStack");
ContextPtr:LookUpControl("/InGame/PartialScreenHooks/ButtonStack");

-- Step up one level (relative)
ContextPtr:LookUpControl("../SelectedUnitContainer");

-- Wildcard for child contexts (NOT control names)
ContextPtr:LookUpControl("/InGame/*/CloseButton");
```

Common cross-context lookup targets:

| Target | Path |
|--------|------|
| LaunchBar button area | `/InGame/LaunchBar/ButtonStack` |
| Unit panel action buttons | `/InGame/UnitPanel/StandardActionsStack` |
| Upper-right hook buttons | `/InGame/PartialScreenHooks/ButtonStack` |
| City panel | `/InGame/CityPanel` |
| Minimap | `/InGame/MinimapPanel/MinimapContainer` |
| Your mod panel | `/InGame/AdditionalUserInterfaces/YourContextName` |

---

> **控件详细参考**：控件类型、XML 属性、Lua 方法等详细内容请参见 [`ui-controls.md`](ui-controls.md)。

---

## Input Handling

There are two handler types:

### Extended Handler (recommended)

```lua
function OnInputHandler(pInputStruct:table)
    local uiMsg = pInputStruct:GetMessageType();

    if uiMsg == KeyEvents.KeyUp then
        local key = pInputStruct:GetKey();
        if key == Keys.VK_ESCAPE then
            Close();
            return true;    -- handled, stop propagation
        end
    end

    return false;   -- not handled, pass through
end
ContextPtr:SetInputHandler(OnInputHandler, true);  -- true = extended
```

### Simple Handler (legacy)

```lua
function InputHandler(uiMsg:number, wParam:number, lParam:number)
    if uiMsg == KeyEvents.KeyDown then
        if wParam == Keys.VK_ESCAPE then
            OnBack();
            return true;
        end
    end
    return false;
end
ContextPtr:SetInputHandler(InputHandler);  -- no second param
```

**Return value semantics:**
- Return `true` → input handled, stops propagation **within this root context**
- Return `false` → input not handled, other contexts in the same root get a chance
- Only one input handler per context

### InputStruct Methods (Extended Handler)

| Method | Returns | Description |
|--------|---------|-------------|
| `GetMessageType()` | number | `KeyEvents.KeyDown`, `KeyEvents.KeyUp`, `MouseEvents.LButtonDown`, etc. |
| `GetKey()` | number | `Keys.VK_ESCAPE`, `Keys.VK_RETURN`, etc. |
| `GetFlags()` | number | Low-level bit-flags |
| `GetX()` / `GetY()` | number | Mouse/touch position |
| `GetMouseDX()` / `GetMouseDY()` | number | Mouse delta since last frame |
| `GetWheel()` | number | Mouse wheel value |
| `GetTouchID()` | number | Touch identifier |
| `IsShiftDown()` | bool | |
| `IsControlDown()` | bool | |
| `IsLButtonDown()` / `IsRButtonDown()` / `IsMButtonDown()` | bool | |
| `IsAnyButtonDown()` | bool | |

---

## Instance Manager (Dynamic Control Creation)

```lua
local m_kInstanceIM = InstanceManager:new("MyInstanceType", "RootControl", Controls.MyStack);
-- 三参数：模板名, 根控件ID, 父容器（仅当父控件不是Context的直接子控件时需要传入）

local kInst = m_kInstanceIM:GetInstance();
kInst.TopLabel:SetText("hello");
kInst.IconButton:RegisterCallback(Mouse.eLClick, OnClick);

m_kInstanceIM:ResetInstances();  -- Clear all
```

XML instance (define in your context XML):
```xml
<Instance Name="MyInstanceType">
    <Container ID="RootControl">
        <Label ID="TopLabel" />
        <Button ID="IconButton" />
    </Container>
</Instance>
```

---

## Text Formatting

```lua
"[NEWLINE]"                              -- Line break
"[COLOR:Red]text[ENDCOLOR]"              -- Colored segment (全色名: DebugLocalization.sqlite.SkillAnnotation_Colors)
"[ICON_Food]"                            -- Inline icon from Icon Atlas (全图标: DebugLocalization.sqlite.SkillAnnotation_Icons)
```

## Localization

```lua
Locale.Lookup("LOC_KEY")                 -- Simple lookup
Locale.Lookup("LOC_KEY", arg1, arg2)     -- With format args

Controls.Label:LocalizeAndSetText("LOC_KEY")
Controls.Label:LocalizeAndSetToolTip("LOC_KEY")
```

Attributes in XML: `String="LOC_KEY"`, `ToolTip="LOC_KEY"`, `Text="LOC_KEY"`

---

## Modal Popup Panel (QueuePopup + DequeuePopup)

完整模态弹窗模式，替代裸 `SetHide(false)`：

```lua
function Open()
    if not UIManager:IsInPopupQueue(ContextPtr) then
        UIManager:QueuePopup(ContextPtr, PopupPriority.Low, {
            RenderAtCurrentParent = true,
            InputAtCurrentParent = true,
            AlwaysVisibleInQueue = true
        })
    end
    ContextPtr:SetHide(false)
    Controls.ScreenAnimIn:SetToBeginning()
    Controls.ScreenAnimIn:Play()
end

function Close()
    UIManager:DequeuePopup(ContextPtr)
    ContextPtr:SetHide(true)
end
```

**自动获得的能力：**

| 特性 | 机制 |
|------|------|
| ESC 关闭 | `QueuePopup` 自动将 ESC 路由到最上层 popup |
| 背景输入阻断 | `InputAtCurrentParent` 防止点击穿透到下层 UI |
| z-order 正确 | popup 始终渲染在其他内容之上 |
| 热重载清理 | `DequeuePopup` 恢复弹窗堆叠 |
| 打开/关闭音效 | `UI.PlaySound("UI_Screen_Open/Close")` |

**XML 配合：** 最外层容器 `<Container Hidden="1" ConsumeMouseButton="1">` + 半透明背景 `<Image Color="0,0,0,140" ConsumeMouseButton="1"/>` 确保点击遮罩区域也能关闭（注册 `Mouse.eLClick → Close`）。

---

## PopupDialog (Confirmation Box)

```lua
include("InstanceManager");
include("PopupDialog");

local m_kPopupDialog = PopupDialog:new("MyDialog");

function ShowConfirm(text)
    m_kPopupDialog:Close();
    m_kPopupDialog:ShowOkDialog(Locale.Lookup(text), function()
        m_kPopupDialog:Close();
        UIManager:DequeuePopup(ContextPtr);
    end);
    UIManager:QueuePopup(ContextPtr, PopupPriority.Utmost);
end
```

---

## Notification System (Right Sidebar)

**Database:**
```xml
<Types><Row Type="NOTIFICATION_MY_TEST" Kind="KIND_NOTIFICATION"/></Types>
<Notifications>
    <Row NotificationType="NOTIFICATION_MY_TEST" SeverityType="MID"
         ExpiresEndOfTurn="True" AutoNotify="False" AutoActivate="False"
         Message="LOC_NOTIFICATION_MY_TEST_MESSAGE"
         Summary="LOC_NOTIFICATION_MY_TEST_SUMMARY"/>
</Notifications>
```

**Lua:**
```lua
local notif = GameInfo.Notifications["NOTIFICATION_MY_TEST"];
local data = {};
data[ParameterTypes.MESSAGE] = Locale.Lookup(notif.Message);
data[ParameterTypes.SUMMARY] = Locale.Lookup(notif.Summary, playerID, val);
data[ParameterTypes.LOCATION] = { x = iX, y = iY };
NotificationManager.SendNotification(playerID, notif.Hash, data);
```

Variable placeholders in text: `{1_Playerid}`, passed via `Locale.Lookup(key, val1, val2)`

---

## PlayerConfigurations — Save Data in UI

```lua
-- Read
local data = PlayerConfigurations[0]:GetValue("MY_KEY");
-- Write
PlayerConfigurations[0]:SetValue("MY_KEY", serializedString);
```

For complex tables, serialize with `DataDumper.lua` (found in BetterTradeScreen).

---

## Official Best Practices (from Civ6Docs.html)

### Lua Conventions

**Use Havokscript type qualifiers** — 完整命名规范和代码风格见 [`conventions.md`](conventions.md)：

```lua
local numPlayers     :number = 0;
local isReady        :boolean = false;
local data           :table = {};
```

**Event Registering:**
Place broadcast callbacks at the bottom of the file in an "Events" section in Initialize().

```lua
function Initialize()
    -- Events
    ContextPtr:SetInitHandler( OnInit );
    ContextPtr:SetRefreshHandler( OnRefresh );
    Events.CitySelectionChanged.Add( OnCitySelectionChanged );
    Events.LocalPlayerTurnBegin.Add( OnLocalPlayerTurnBegin );
    Events.UnitOperationsCleared.Add( OnUnitOperationsCleared );
    LuaEvent.TestPanel_AllSectionsClosed.Add( OnAllSectionsClosed );
end
```

**LUAEvents:**
- Name based on the context from where it's raised
- Only pass simple types (strings, numbers, booleans, tables without C++ objects)

**Include Files:**
Any included files will have all contents copied into the local context. Minimize local variables and state in include files to prevent name conflicts.

---

## Complete Example: Official Panel Pattern

Based on official code (GreatWorksOverview.lua, GovernorPanel.lua):

```lua
include("InstanceManager");
include("PopupDialog");
include("GameCapabilities");

-- Constants
local RELOAD_CACHE_ID:string = "MyPanel";
local PANEL_MAX_WIDTH:number = 1890;

-- Instance Managers
local m_itemIM:table = InstanceManager:new("ItemInstance", "Root", Controls.ItemStack);

-- Player Variables
local m_LocalPlayer:table;
local m_LocalPlayerID:number;

-- ===========================================================================
function UpdatePlayerData()
    m_LocalPlayerID = Game.GetLocalPlayer();
    if m_LocalPlayerID ~= -1 then
        m_LocalPlayer = Players[m_LocalPlayerID];
    end
end

-- ===========================================================================
function Refresh()
    if (m_LocalPlayer == nil) then
        return;
    end
    
    m_itemIM:ResetInstances();
    
    -- Populate data
    -- ...
    
    -- Realize stack and scrollbar
    Controls.ItemStack:CalculateSize();
    Controls.ItemStack:ReprocessAnchoring();
    Controls.ItemScrollPanel:CalculateInternalSize();
    Controls.ItemScrollPanel:ReprocessAnchoring();
end

-- ===========================================================================
function OnInit(isReload:boolean)
    if isReload then
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID);
    end
    UpdatePlayerData();
    Refresh();
end

-- ===========================================================================
function OnShutdown()
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, "isHidden", ContextPtr:IsHidden());
end

-- ===========================================================================
function OnGameDebugReturn(context:string, contextTable:table)
    if context == RELOAD_CACHE_ID then
        if contextTable["isHidden"] ~= nil and (not contextTable["isHidden"]) then
            Open();
        end
    end
end

-- ===========================================================================
function Open()
    UpdatePlayerData();
    Refresh();
    ContextPtr:SetHide(false);
end

-- ===========================================================================
function Close()
    ContextPtr:SetHide(true);
end

-- ===========================================================================
function OnInputHandler(pInputStruct:table)
    local uiMsg = pInputStruct:GetMessageType();
    if uiMsg == KeyEvents.KeyUp then
        local key = pInputStruct:GetKey();
        if key == Keys.VK_ESCAPE then
            Close();
            return true;
        end
    end
    return false;
end

-- ===========================================================================
function Initialize()
    ContextPtr:SetInitHandler(OnInit);
    ContextPtr:SetShutdown(OnShutdown);
    ContextPtr:SetInputHandler(OnInputHandler, true);
    
    LuaEvents.GameDebug_Return.Add(OnGameDebugReturn);
    
    -- Register UI events
    Controls.CloseButton:RegisterCallback(Mouse.eLClick, Close);
    
    -- Register game events
    Events.LocalPlayerTurnBegin.Add(OnLocalPlayerTurnBegin);
    Events.LocalPlayerTurnEnd.Add(OnLocalPlayerTurnEnd);
end

if HasCapability("CAPABILITY_MY_PANEL") then
    Initialize();
end
```

---

## Common Patterns from Official Code

### Pattern 1: Capability Check
```lua
if HasCapability("CAPABILITY_MY_FEATURE") then
    Initialize();
end
```

### Pattern 2: Sound on Hover
```lua
Controls.Button:RegisterCallback(Mouse.eLClick, OnClick);
Controls.Button:RegisterCallback(Mouse.eMouseEnter, function() UI.PlaySound("Main_Menu_Mouse_Over"); end);
```

### Pattern 3: Yield Display
```lua
local YIELD_FONT_ICONS:table = {
    YIELD_FOOD          = "[ICON_FoodLarge]",
    YIELD_PRODUCTION    = "[ICON_ProductionLarge]",
    YIELD_GOLD          = "[ICON_GoldLarge]",
    YIELD_SCIENCE       = "[ICON_ScienceLarge]",
    YIELD_CULTURE       = "[ICON_CultureLarge]",
    YIELD_FAITH         = "[ICON_FaithLarge]",
};
```

### Pattern 4: Stack Management
```lua
Controls.Stack:CalculateSize();
Controls.Stack:ReprocessAnchoring();
Controls.ScrollPanel:CalculateInternalSize();
Controls.ScrollPanel:ReprocessAnchoring();
```

### Pattern 5: Instance Manager with Data Fields
```lua
local DATA_FIELD_IM:string = "InstanceManager";

local im:table = instance[DATA_FIELD_IM];
if(im == nil) then
    im = InstanceManager:new("SubInstance", "Root", instance.Stack);
    instance[DATA_FIELD_IM] = im;
else
    im:ResetInstances();
end
```

### Pattern 6: A new button in Launcher Bar(Other description: 上面的按钮栏)

```xml
Please ignore the specific name in this example,such as "ANW", it's just an example.
A button placed in the Launcher Bar needs a button instance and a pin instance in the right of the button.
    <Instance Name="ANW_Item">
		<Button ID="ANW_Button" Anchor="L,C" Size="49,49" Texture="LaunchBar_Hook_GreatPeopleButton" Style="ButtonNormalText" Color="200,0,0,220" TextureOffset = "0,0" ToolTip="LOC_CIVILIZATION_ANW_NAME">
			<Image ID="ANW_Icon" Size="35,35" Anchor="C,C" Offset="0,0"  Texture="ICON_CIVILIZATION_ANW_36"/>
			<Label ID="ANW_AlertIndicator" String="[ICON_New]" Anchor="R,T" AnchorSide="O,O" Offset="-18,-18" ToolTip="LOC_AlertIndicator_LAUNCH_NAME" Hidden="1"/>
		</Button>
	</Instance>
	<Instance Name="ANW_PinInstance">
		<Image ID="ANW_Pin" Anchor="L,C" Offset="0,-2" Size="7,7" Texture="LaunchBar_TrackPip" Color="255,255,255,200"/>
	</Instance>
```

```lua
We should use to build a instance for ButtonStack instead of attaching button to ButtonStack directly.
local ANWButtonInstance = {}
function AttachANWButton()
    local buttonStack = ContextPtr:LookUpControl("/InGame/LaunchBar/ButtonStack");

    ContextPtr:BuildInstanceForControl("ANW_Item", ANWButtonInstance, buttonStack);
    RegisterCallback(someargs);
    ContextPtr:BuildInstanceForControl("ANW_PinInstance", {}, buttonStack);

    -- Resize.
    buttonStack:CalculateSize();

    local backing = ContextPtr:LookUpControl("/InGame/LaunchBar/LaunchBacking");
    backing:SetSizeX(buttonStack:GetSizeX() + 116);

    local backingTile = ContextPtr:LookUpControl("/InGame/LaunchBar/LaunchBackingTile");
    backingTile:SetSizeX(buttonStack:GetSizeX() - 20);

    LuaEvents.LaunchBar_Resize(buttonStack:GetSizeX());
end
```
