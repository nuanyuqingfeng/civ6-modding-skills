# Decision Trees & Task Workflows

## 文件使用指南

在使用本文件的工作流时，请配合以下参考文件：

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| `ui-controls.md` | ForgeUI 控件详细参考 | **查找控件属性、Lua 方法时必读** |
| `ui-lua.md` | UI 生命周期、事件处理 | 了解 Context 生命周期、输入处理等 |
| `xml-templates.md` | XML 布局模板 | 复制粘贴模板时 |
| `conventions.md` | 命名约定和代码规范 | 文件命名、代码风格 |
| `project-setup.md` | .civ6proj / .modinfo 注册 | 注册 UI/脚本时 |
| `validation.md` | 验证清单 | 完成开发后验证 |

**重要提示：**
- 需要查找控件的 XML 属性或 Lua 方法时，优先查看 `ui-controls.md`
- 需要了解 Context 生命周期或事件处理时，查看 `ui-lua.md`
- 需要复制粘贴 XML 模板时，查看 `xml-templates.md`

---

## Decision Tree 1: What UI Mode Do I Need?

```
What do you want to do?
│
├─ ADD new UI to an existing game screen (e.g., add a button to LaunchBar)
│   └─ Use: AddUserInterfaces + BuildInstanceForControl or ChangeParent
│       → See "Workflow A: Add Button to Existing UI"
│
├─ REPLACE an existing UI panel's behavior (e.g., modify UnitPanel)
│   └─ Use: ReplaceUIScript + include() chain
│       → See "Workflow B: Replace Existing UI Script"
│
├─ CREATE a brand new standalone panel (e.g., custom info screen)
│   └─ Use: AddUserInterfaces (fullscreen overlay pattern)
│       → See "Workflow C: Create New Standalone Panel"
│
└─ ADD data that existing UI should display (e.g., new yield type)
    └─ Use: UpdateDatabase + maybe ReplaceUIScript for display logic
        → See "Workflow D: Add New Data to Existing UI"
```

## Decision Tree 2: How to Communicate Between Contexts?

```
What needs to talk to what?
│
├─ UI Context A ↔ UI Context B
│   └─ Use: LuaEvents (sender fires, receiver subscribes)
│       → Both are UI-side, safe to pass simple types
│
├─ UI → Gameplay (read game state)
│   └─ Use: PROPERTY 直接读 / Core 共享读取函数（跨端）；ExposedMembers 仅限 GP 同端跨文件，禁止跨端暴露
│       → See ui-lua.md "UI <—> Gameplay Communication"
│
├─ UI → Gameplay (modify game state)
│   └─ Use: PlayerOperations + UI.RequestPlayerOperation()
│       → Only works during that player's turn
│
└─ Gameplay → UI (notify UI of changes)
    └─ Use: GameEvents (Gameplay fires, UI subscribes)
        → UI must be actively listening
```

## Decision Tree 3: ChangeParent vs BuildInstance?

```
How to add controls to another context's UI?
│
├─ I have a single, pre-defined control (e.g., one button)
│   └─ Use: ChangeParent
│       → Define control in your XML, move it to target in AttachControls()
│       → Simpler, but control must already exist in your XML
│
└─ I need multiple dynamic items (e.g., list entries, button stack)
    └─ Use: BuildInstanceForControl
        → Define <Instance> template in XML, build instances in Lua
        → More flexible, supports dynamic counts
        → Required for LaunchBar buttons (official pattern)
```

---

## Workflow A: Add Button to Existing UI (e.g., LaunchBar)

**Goal:** Add a clickable button to an existing game UI element.

### Step 1 — Define Instance Template in XML

```xml
<?xml version="1.0" encoding="utf-8"?>
<Context Name="MyMod_LaunchButton">
    <!-- Instance template for the button -->
    <Instance Name="MyButton_Item">
        <Button ID="MyButton" Anchor="L,C" Size="49,49"
                Texture="LaunchBar_Hook_GovernmentButton" Style="ButtonNormalText"
                StateOffsetIncrement="0,49" ToolTip="LOC_MY_BUTTON_TOOLTIP">
            <Image ID="ButtonIcon" Size="35,35" Anchor="C,C" Offset="0,0"
                   Texture="ICON_MY_CUSTOM_ICON"/>
        </Button>
    </Instance>
    <!-- Optional: pin instance (the dot on the right side) -->
    <Instance Name="MyButton_PinInstance">
        <Image ID="Pin" Anchor="L,C" Offset="0,-2" Size="7,7"
               Texture="LaunchBar_TrackPip" Color="255,255,255,200"/>
    </Instance>
</Context>
```

### Step 2 — Create Lua Script

```lua
include("InstanceManager");

local RELOAD_CACHE_ID:string = "MyMod_LaunchButton";
local m_buttonInstance:table = {};

function OnButtonClick()
    -- Open your panel, fire LuaEvents, etc.
    LuaEvents.MyPanel_Toggle();
end

function AttachControls()
    local buttonStack = ContextPtr:LookUpControl("/InGame/LaunchBar/ButtonStack");
    if not buttonStack then
        print("ERROR: Could not find LaunchBar ButtonStack");
        return;
    end

    -- Build button instance
    ContextPtr:BuildInstanceForControl("MyButton_Item", m_buttonInstance, buttonStack);
    m_buttonInstance.MyButton:RegisterCallback(Mouse.eLClick, OnButtonClick);

    -- Build pin instance
    ContextPtr:BuildInstanceForControl("MyButton_PinInstance", {}, buttonStack);

    -- Resize LaunchBar backing to fit new button
    buttonStack:CalculateSize();
    local backing = ContextPtr:LookUpControl("/InGame/LaunchBar/LaunchBacking");
    if backing then
        backing:SetSizeX(buttonStack:GetSizeX() + 116);
    end
    local backingTile = ContextPtr:LookUpControl("/InGame/LaunchBar/LaunchBackingTile");
    if backingTile then
        backingTile:SetSizeX(buttonStack:GetSizeX() - 20);
    end
    LuaEvents.LaunchBar_Resize(buttonStack:GetSizeX());
end

function OnInit(isReload:boolean)
    if isReload then
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID);
    end
end

function OnShutdown()
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, "isHidden", ContextPtr:IsHidden());
end

function OnGameDebugReturn(context:string, contextTable:table)
    if context == RELOAD_CACHE_ID then
        if contextTable["isHidden"] ~= nil and (not contextTable["isHidden"]) then
            -- Re-attach if needed
        end
    end
end

function Initialize()
    ContextPtr:SetInitHandler(OnInit);
    ContextPtr:SetShutdown(OnShutdown);

    LuaEvents.GameDebug_Return.Add(OnGameDebugReturn);
    Events.LoadGameViewStateDone.Add(AttachControls);
end
Initialize();
```

### Step 3 — Register in .modinfo

```xml
<AddUserInterfaces id="MyModLaunchButton" criteria="MyCriteria">
    <Properties><Context>InGame</Context></Properties>
    <File>UI/Additions/MyMod_LaunchButton.xml</File>
</AddUserInterfaces>
<ImportFiles id="MyModLaunchButtonFiles" criteria="MyCriteria">
    <File>UI/Additions/MyMod_LaunchButton.lua</File>
</ImportFiles>
```

### Step 4 — Verify

- [ ] Button appears in LaunchBar after game loads
- [ ] Button click triggers expected action
- [ ] LaunchBar resizes correctly
- [ ] Hot reload works (F10 in tuner)

---

## Workflow B: Replace Existing UI Script

**Goal:** Modify behavior of an existing game UI without copying the entire file.

### Step 1 — Find the LuaContext ID

Search base game XML for the context ID:
```
Base/Assets/UI/<ScreenName>/<FileName>.xml
→ Look for: <LuaContext ID="ContextName">
```

Common context IDs:
| UI Element | LuaContext ID |
|-----------|---------------|
| Unit Panel | `UnitPanel` |
| City Panel | `CityPanel` |
| Top Panel | `TopPanel` |
| Launch Bar | `LaunchBar` |
| Notification Panel | `NotificationPanel` |

### Step 2 — Create Replacement Lua with Include Chain

```lua
-- Include original (copies all content into this context)
include("UnitPanel");

-- Include expansions in order
pcall(function() include("UnitPanel_Expansion1.lua"); end);
pcall(function() include("UnitPanel_Expansion2.lua"); end);

-- Include compatible mods (lower LoadOrder)
pcall(function() include("OtherMod_UnitPanel.lua"); end);

-- Save original function reference
local BASE_UpdateActionsPanel = UpdateActionsPanel;

-- Override with your logic
function UpdateActionsPanel(unitOwner:number, unitID:number)
    -- Your custom logic first
    if ShouldUseCustomPanel(unitOwner, unitID) then
        ShowCustomActions(unitOwner, unitID);
        return;
    end

    -- Fall through to original
    BASE_UpdateActionsPanel(unitOwner, unitID);
end
```

### Step 3 — Register in .modinfo

```xml
<ReplaceUIScript id="MyModUnitPanel" criteria="MyCriteria">
    <Properties>
        <LuaContext>UnitPanel</LuaContext>
        <LuaReplace>UI/Replacements/UnitPanel_MyMod.lua</LuaReplace>
    </Properties>
</ReplaceUIScript>
<ImportFiles id="MyModUnitPanelFiles" criteria="MyCriteria">
    <File>UI/Replacements/UnitPanel_MyMod.lua</File>
</ImportFiles>
```

### Step 4 — Verify

- [ ] Original UI functionality still works
- [ ] Your override triggers under correct conditions
- [ ] Fall-through to original works when conditions not met
- [ ] Expansion DLCs still work (include chain correct)

---

## Workflow C: Create New Standalone Panel

**Goal:** Create a completely new UI panel (fullscreen overlay or embedded).

### Step 1 — Create XML Layout

Use the appropriate template from `xml-templates.md`:
- Fullscreen overlay → Template "Fullscreen Overlay Panel"
- Embedded panel → Template "Embedded Panel"

### Step 2 — Create Lua Script

Use the template from `conventions.md` → "UI Lua File Template". Key structure:

```lua
include("InstanceManager");

local RELOAD_CACHE_ID:string = "MyPanel";

-- Instance Managers
local m_itemIM:table = InstanceManager:new("ItemInstance", "Root", Controls.ItemStack);

function Refresh()
    m_itemIM:ResetInstances();
    -- Populate data...
    Controls.ItemStack:CalculateSize();
    Controls.ItemStack:ReprocessAnchoring();
    Controls.ContentScroll:CalculateInternalSize();
end

function Open()
    Refresh();
    ContextPtr:SetHide(false);
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

function OnInit(isReload:boolean)
    if isReload then
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID);
    end
    Refresh();
end

function OnShutdown()
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, "isHidden", ContextPtr:IsHidden());
end

function OnGameDebugReturn(context:string, contextTable:table)
    if context == RELOAD_CACHE_ID then
        if contextTable["isHidden"] ~= nil and (not contextTable["isHidden"]) then
            Open();
        end
    end
end

function Initialize()
    ContextPtr:SetInitHandler(OnInit);
    ContextPtr:SetShutdown(OnShutdown);
    ContextPtr:SetShowHandler(function() Refresh(); end);
    ContextPtr:SetInputHandler(OnInputHandler, true);

    LuaEvents.GameDebug_Return.Add(OnGameDebugReturn);
    Controls.CloseButton:RegisterCallback(Mouse.eLClick, Close);

    -- Subscribe to game events
    Events.LocalPlayerTurnBegin.Add(function() if not ContextPtr:IsHidden() then Refresh(); end; end);
end
Initialize();
```

### Step 3 — Register in .modinfo

```xml
<AddUserInterfaces id="MyPanel" criteria="MyCriteria">
    <Properties><Context>InGame</Context></Properties>
    <File>UI/Additions/MyPanel.xml</File>
</AddUserInterfaces>
<ImportFiles id="MyPanelFiles" criteria="MyCriteria">
    <File>UI/Additions/MyPanel.lua</File>
</ImportFiles>
<!-- Add to Files section -->
<Files>
    <File>UI/Additions/MyPanel.xml</File>
    <File>UI/Additions/MyPanel.lua</File>
</Files>
```

### Step 4 — Verify

- [ ] Panel starts hidden (mod contexts auto-hidden)
- [ ] Panel shows when triggered
- [ ] ESC closes panel
- [ ] Hot reload restores panel state
- [ ] Stack/ScrollPanel recalculates after content changes

---

## Workflow D: Add New Data to Existing UI

**Goal:** Add new game data (yields, resources, etc.) that existing UI can display.

### Step 1 — Define Data in Database XML

```xml
<!-- Data/MyNewYield.xml -->
<Types>
    <Row Type="YIELD_MYMOD_ENERGY" Kind="KIND_YIELD"/>
</Types>
<Yields>
    <Row YieldType="YIELD_MYMOD_ENERGY" Name="LOC_YIELD_MYMOD_ENERGY_NAME"
         IconString="[ICON_MyMod_Energy]" Color="100,200,255,255"/>
</Yields>
```

### Step 2 — Add Display Logic via ReplaceUIScript

If the existing UI needs modification to show your new data, use Workflow B.
If the existing UI already handles dynamic yields (like TopPanel), you may only need to register your yield type.

### Step 3 — Localization

```xml
<!-- Text/en_US/MyText.xml -->
<LocalizedText>
    <Row Tag="LOC_YIELD_MYMOD_ENERGY_NAME" Language="en_US">
        <Text>Energy</Text>
    </Row>
</LocalizedText>
```

### Step 4 — Verify

- [ ] Data appears in database (check with SQL tuner)
- [ ] UI displays the new data correctly
- [ ] Localization works for all supported languages

---

## Workflow E: Cross-Context Panel (Button Opens Panel)

**Goal:** A button in one context opens a panel in another context.

### Step 1 — Define LuaEvents

In the button's context (e.g., LaunchBar addition):
```lua
function OnButtonClick()
    LuaEvents.MyPanel_Open(someData);
end
```

In the panel's context:
```lua
function OnOpenRequest(data)
    -- Store data if needed
    Open();
end
LuaEvents.MyPanel_Open.Add(OnOpenRequest);
```

### Step 2 — Ensure Both Contexts Load

Both must be registered in `.modinfo` with `AddUserInterfaces`.

### Step 3 — Verify

- [ ] Button click fires LuaEvent
- [ ] Panel receives event and opens
- [ ] Data passes correctly (simple types only, no C++ objects)
- [ ] Panel closes properly and can re-open

---

---

# Gameplay Decision Trees & Workflows

## Decision Tree 4: What Gameplay Pattern Do I Need?

```
What gameplay task?
│
├─ REACT to game events (turn start, unit move, city built, etc.)
│   └─ Use: GameEvents.* hooks in a Gameplay Lua script
│       → See "Workflow F: React to Game Events"
│
├─ STORE custom data that survives save/load
│   └─ Use: Game:SetProperty / Player:SetProperty / Unit:SetProperty
│       → See "Workflow G: Store Custom Data"
│
├─ COMMUNICATE between UI and Gameplay
│   ├─ UI needs to READ game state
│   │   └─ Use: PROPERTY 直接读 / Core 共享读取函数（跨端）；ExposedMembers 仅限 GP 同端跨文件，禁止跨端暴露
│   ├─ UI needs to MODIFY game state
│   │   └─ Use: PlayerOperations + UI.RequestPlayerOperation()
│   └─ Gameplay needs to NOTIFY UI
│       └─ Use: GameEvents (Gameplay fires, UI subscribes)
│       → See "Workflow H: UI ↔ Gameplay Communication"
│
├─ ADD new game content (units, buildings, etc.)
│   └─ Use: Database XML + UpdateDatabase
│       → See "Workflow I: Add New Game Content"
│
└─ CREATE a custom game mechanic (new system)
    └─ Combine: GameEvents + SetProperty + Database modifiers
        → See "Workflow J: Custom Game Mechanic"
```

## Decision Tree 5: Which Event System?

```
Where is your code running?
│
├─ UI Lua context (has ContextPtr, Controls)
│   ├─ React to C++ engine events → Events.* (MUST .Remove() in OnShutdown)
│   ├─ React to other UI contexts → LuaEvents.* (auto-cleanup)
│   └─ React to Gameplay push → LuaEvents.*（GP 用 ReportingEvents.SendLuaEvent 推送；禁止跨端 ExposedMembers）
│
└─ GamePlay Lua script (no UI access)
    ├─ React to game state changes → GameEvents.*
    └─ Custom hooks for GP 同端跨文件 → GameEvents.* + ExposedMembers；GP→UI 推送用 ReportingEvents.SendLuaEvent
```

## Decision Tree 6: How to Persist Data?

```
What kind of data?
│
├─ Per-game data (one value for the whole game)
│   └─ Game:SetProperty("KEY", value) / Game:GetProperty("KEY")
│
├─ Per-player data (each player has their own)
│   └─ Player:SetProperty("KEY", value) / Player:GetProperty("KEY")
│
├─ Per-city data
│   └─ City:SetProperty("KEY", value) / City:GetProperty("KEY")
│
├─ Per-unit data
│   └─ Unit:SetProperty("KEY", value) / Unit:GetProperty("KEY")
│
├─ Per-plot data
│   └─ Plot:SetProperty("KEY", value) / Plot:GetProperty("KEY")
│
└─ Complex data (tables, nested structures)
    └─ Serialize with DataDumper or JSON, store as string
        → PlayerConfigurations[i]:SetValue("KEY", serializedString)
```

---

## Workflow F: React to Game Events

**Goal:** Execute custom logic when something happens in the game (turn start, unit moves, city built, etc.).

### Step 1 — Create GamePlay Lua Script

Place in `Mods/<ModName>/Scripts/MyScript.lua`（Mods 加载目录，见 SKILL.md 环境路径总表 P2）:

```lua
print("MyMod: Initializing gameplay script");

-- ===========================================================================
--  Member variables
-- ===========================================================================
local m_initialized:boolean = false;

-- ===========================================================================
--  Event handlers
-- ===========================================================================
function OnPlayerTurnStarted(playerID:number)
    local pPlayer = Players[playerID];
    if pPlayer == nil or not pPlayer:IsAlive() then return; end

    -- Your logic here
    print("MyMod: Turn started for player " .. tostring(playerID));
end

function OnUnitMoved(playerID:number, unitID:number, x:number, y:number)
    local pPlayer = Players[playerID];
    if pPlayer == nil then return; end
    local pUnit = pPlayer:GetUnits():FindID(unitID);
    if pUnit == nil then return; end

    -- Your logic here
end

function OnCityBuilt(playerID:number, cityID:number, x:number, y:number)
    -- Your logic here
end

-- ===========================================================================
--  Initialization
-- ===========================================================================
function Initialize()
    if m_initialized then return; end

    -- Subscribe to game events
    GameEvents.PlayerTurnStarted.Add(OnPlayerTurnStarted);
    GameEvents.OnUnitMoved.Add(OnUnitMoved);
    GameEvents.CityBuilt.Add(OnCityBuilt);

    m_initialized = true;
    print("MyMod: Gameplay script initialized");
end

Initialize();
```

### Step 2 — Register in .modinfo

```xml
<AddGameplayScripts id="MyScripts" criteria="MyCriteria">
    <File>Scripts/MyScript.lua</File>
</AddGameplayScripts>
```

### Step 3 — Verify

- [ ] Script loads (check print output in logs)
- [ ] Event handlers fire at correct times
- [ ] No errors when players/units are nil
- [ ] Works in multiplayer (no `math.random()`, use `Game.GetRandNum()`)

---

## Workflow G: Store Custom Data

**Goal:** Store data that persists across save/load.

### Step 1 — Store Data

```lua
-- In your GamePlay Lua script:

-- Per-game data
Game:SetProperty("MyMod_TurnCount", (Game:GetProperty("MyMod_TurnCount") or 0) + 1);

-- Per-player data
local pPlayer = Players[playerID];
pPlayer:SetProperty("MyMod_CustomFlag", true);
pPlayer:SetProperty("MyMod_Score", 42);

-- Per-city data
pCity:SetProperty("MyMod_CityLevel", 3);

-- Per-unit data
pUnit:SetProperty("MyMod_ExperienceBonus", 10);

-- Per-plot data
local pPlot = Map.GetPlot(x, y);
pPlot:SetProperty("MyMod_PlotFlag", "special");
```

### Step 2 — Read Data

```lua
-- In GamePlay Lua or UI Lua (read-only for UI):

local value = Game:GetProperty("MyMod_TurnCount") or 0;
local flag = pPlayer:GetProperty("MyMod_CustomFlag") or false;
local level = pCity:GetProperty("MyMod_CityLevel") or 1;
```

### Step 3 — Verify

- [ ] Data persists after save/load
- [ ] Default values used when property not set (nil check)
- [ ] No C++ objects stored as properties (only primitives)

---

## Workflow H: UI ↔ Gameplay Communication

**Goal:** UI reads/modifies game state managed by Gameplay scripts.

### Method 1: PROPERTY / Core 共享读取函数（UI 跨端读取）；ExposedMembers 仅限 GP 同端跨文件

**GP 侧写数据**（`Scripts/MyData.lua`）：
```lua
Game:SetProperty("MyMod_CustomData", someValue);
```

**Core 共享读取函数**（GP/UI 均可 include）：
```lua
function GetMyModData()
    return Game:GetProperty("MyMod_CustomData") or {};
end
```

**UI 侧读取**（`UI/Additions/MyPanel.lua`）：
```lua
include("Core_MyMod");
local data = GetMyModData();
```

**GP 同端跨文件共享**（允许 ExposedMembers，但禁止跨端暴露给 UI）：
```lua
-- GP file A
ExposedMembers.MyMod = ExposedMembers.MyMod or {};
ExposedMembers.MyMod.GetValue = function(key)
    return Game:GetProperty(key);
end

-- GP file B（同一 GP 状态）
local value = ExposedMembers.MyMod.GetValue("MyMod_CustomData");
```

### Method 2: PlayerOperations (UI modifies Gameplay state)

**UI side:**
```lua
function RequestGameplayAction(actionName, data)
    local params = {};
    params.OnStart = actionName;
    for k, v in pairs(data) do params[k] = v; end
    UI.RequestPlayerOperation(Game.GetLocalPlayer(), PlayerOperations.EXECUTE_SCRIPT, params);
end

RequestGameplayAction("MyMod_SetFlag", { flag = true, targetID = 42 });
```

**GamePlay side:**
```lua
function OnSetFlag(playerID:number, params:table)
    local flag = params.flag;
    local targetID = params.targetID;
    -- Do something with the data
    Game:SetProperty("MyMod_Flag", flag);
end
GameEvents.MyMod_SetFlag.Add(OnSetFlag);
```

### Method 3: GameEvents (Gameplay notifies UI)

**GamePlay side:**
```lua
function OnSomethingHappened(playerID:number)
    -- Fire event that UI can listen to
    GameEvents.MyMod_SomethingHappened.Call(playerID, "some data");
end
```

**UI side:**
```lua
function OnSomethingHappened(playerID:number, data:string)
    -- Update UI
    Refresh();
end
GameEvents.MyMod_SomethingHappened.Add(OnSomethingHappened);
```

### Verify

- [ ] UI can read Gameplay data
- [ ] UI can trigger Gameplay actions
- [ ] Gameplay can notify UI of changes
- [ ] No C++ objects passed across boundary

---

## Workflow I: Add New Game Content (Database)

**Goal:** Add new units, buildings, districts, etc. via database XML.

### Step 1 — Create Data XML

```xml
<?xml version="1.0" encoding="utf-8"?>
<GameInfo>
    <!-- Register type -->
    <Types>
        <Row Type="UNIT_MYMOD_WARRIOR" Kind="KIND_UNIT"/>
    </Types>

    <!-- Define unit -->
    <Units>
        <Row UnitType="UNIT_MYMOD_WARRIOR"
             BaseMoves="2"
             Cost="80"
             Combat="36"
             BaseSightRange="2"
             ZoneOfControl="true"
             PromotionClass="PROMOTION_CLASS_MELEE"
             TraitType="TRAIT_CIVILIZATION_MYMOD"/>
    </Units>

    <!-- Upgrade path -->
    <UnitUpgrades>
        <Row Unit="UNIT_MYMOD_WARRIOR" UpgradeUnit="UNIT_SWORDSMAN"/>
    </UnitUpgrades>

    <!-- Replaces base unit -->
    <UnitReplaces>
        <Row CivUniqueUnitType="UNIT_MYMOD_WARRIOR" ReplacesUnitType="UNIT_WARRIOR"/>
    </UnitReplaces>

    <!-- Localization -->
    <BaseGameText>
        <Row Tag="LOC_UNIT_MYMOD_WARRIOR_NAME">
            <Text>Modded Warrior</Text>
        </Row>
        <Row Tag="LOC_UNIT_MYMOD_WARRIOR_DESCRIPTION">
            <Text>A stronger warrior unit.</Text>
        </Row>
    </BaseGameText>
</GameInfo>
```

### Step 2 — Register in .modinfo

```xml
<UpdateDatabase id="MyData" criteria="MyCriteria">
    <File>Data/MyUnits.xml</File>
</UpdateDatabase>
```

### Step 3 — Verify

- [ ] Unit appears in game (check with Tuner)
- [ ] Can be produced/purchased
- [ ] Upgrade path works
- [ ] Localization displays correctly

---

## Workflow J: Custom Game Mechanic

**Goal:** Create a completely new game system (e.g., custom resource, special ability, new mechanic).

### Step 1 — Design the System

Decide:
1. What data needs to be stored? → SetProperty
2. What events trigger the mechanic? → GameEvents
3. Does it need database entries? → Modifiers, Requirements
4. Does it need UI? → If yes, add UI workflows

### Step 2 — Database Layer (if needed)

```xml
<!-- Define custom modifier -->
<Modifiers>
    <Row ModifierId="MODIFIER_MYMOD_CUSTOM"
         ModifierType="MODIFIER_PLAYER_ADJUST_PROPERTY"
         RunOnce="false"
         Permanent="true">
        <Name>MyMod_CustomFlag</Name>
        <Value>1</Value>
    </Row>
</Modifiers>

<!-- Define requirement to check property -->
<Requirements>
    <Row RequirementId="REQ_MYMOD_HAS_FLAG"
         RequirementType="REQUIREMENT_PLAYER_PROPERTY_MATCHES">
        <Name>MyMod_CustomFlag</Name>
        <Value>1</Value>
    </Row>
</Requirements>
```

### Step 3 — Gameplay Layer

```lua
print("MyMod: Custom mechanic initializing");

local MECHANIC_KEY = "MyMod_MechanicState";

function OnPlayerTurnStarted(playerID:number)
    local pPlayer = Players[playerID];
    if pPlayer == nil or not pPlayer:IsAlive() then return; end

    -- Check state
    local state = pPlayer:GetProperty(MECHANIC_KEY) or 0;

    -- Apply mechanic logic
    if state > 0 then
        -- Do something
        pPlayer:SetProperty(MECHANIC_KEY, state - 1);
    end
end

function OnCustomAction(playerID:number, params:table)
    -- Called via PlayerOperations from UI
    pPlayer:SetProperty(MECHANIC_KEY, params.value);
end

function Initialize()
    GameEvents.PlayerTurnStarted.Add(OnPlayerTurnStarted);
    GameEvents.MyMod_CustomAction.Add(OnCustomAction);
end

Initialize();
```

### Step 4 — UI Layer (if needed)

Follow Workflow C for the panel, Workflow H for communication.

### Step 5 — Register Everything

```xml
<UpdateDatabase id="MyMechanicData" criteria="MyCriteria">
    <File>Data/MyMechanic.xml</File>
</UpdateDatabase>
<AddGameplayScripts id="MyMechanicScripts" criteria="MyCriteria">
    <File>Scripts/MyMechanic.lua</File>
</AddGameplayScripts>
<AddUserInterfaces id="MyMechanicUI" criteria="MyCriteria">
    <Properties><Context>InGame</Context></Properties>
    <File>UI/Additions/MyMechanic.xml</File>
</AddUserInterfaces>
<ImportFiles id="MyMechanicUIFiles" criteria="MyCriteria">
    <File>UI/Additions/MyMechanic.lua</File>
</ImportFiles>
```

### Step 6 — Verify

- [ ] Database entries load correctly
- [ ] Gameplay logic works
- [ ] UI displays and updates
- [ ] Data persists across save/load
- [ ] Works in multiplayer

---

## Quick Reference: Common Patterns

### UI Patterns

| Task | Pattern | Key Function |
|------|---------|-------------|
| Add button to LaunchBar | BuildInstanceForControl | `ContextPtr:BuildInstanceForControl()` |
| Add button to PartialScreen | BuildInstanceForControl | Same as above, different target path |
| Open panel from button | LuaEvents | `LuaEvents.MyPanel_Open()` |
| Modify existing UI | ReplaceUIScript | `include()` + function override |
| Dynamic list | InstanceManager | `im:GetInstance()` / `im:ResetInstances()` |
| Hot reload state | GameDebug | `GameDebug_AddValue` / `GameDebug_GetValues` |

### Gameplay Patterns

| Task | Pattern | Key Function |
|------|---------|-------------|
| React to game event | GameEvents | `GameEvents.X.Add(handler)` |
| Store per-player data | SetProperty | `pPlayer:SetProperty(key, val)` |
| Store per-game data | SetProperty | `Game:SetProperty(key, val)` |
| UI reads Gameplay | PROPERTY / Core 共享读取函数 | `Players[id]:GetProperty()` / `include("Core_Mod")` |
| GP 同端跨文件共享 | ExposedMembers | `ExposedMembers.Mod.Func()`（禁止跨端暴露给 UI） |
| UI modifies Gameplay | PlayerOperations | `UI.RequestPlayerOperation()` |
| Gameplay notifies UI | GameEvents | `GameEvents.X.Call(data)` |
| Add new content | Database XML | `<Types>` + `<Row>` |
| Dynamic modifier | AttachModifierByID | `pPlayer:AttachModifierByID()` |
| Plot-based modifier | SetProperty + Requirement | `pPlot:SetProperty()` + DB Requirement |
