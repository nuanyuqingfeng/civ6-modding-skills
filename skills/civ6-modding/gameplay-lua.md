# GamePlay Lua Scripting

GamePlay Lua scripts are **standalone `.lua` files** — no XML needed. They run on the game core side and interact with game rules, data, and logic.

## File Location

Register in `.modinfo`:
```xml
<AddGameplayScripts id="MyScripts" criteria="MyCriteria">
    <File>Scripts/MyGameplayScript.lua</File>
</AddGameplayScripts>
```

## Template

```lua
-- ===========================================================================
--  Member variables
-- ===========================================================================
local m_bInitialized :boolean = false;

-- ===========================================================================
--  Game event hooks
-- ===========================================================================
function OnPlayerTurnStarted(playerID:number)
    local pPlayer = Players[playerID];
    if pPlayer == nil or not pPlayer:IsAlive() then return; end
end

function Initialize()
    if m_bInitialized then return; end
    GameEvents.PlayerTurnStarted.Add(OnPlayerTurnStarted);
    m_bInitialized = true;
end

Initialize();
```

## Persisted State

Game scripts can store data that survives save/load:

```lua
-- Store
Game:SetProperty("KeyName", value);

-- Retrieve
local value = Game:GetProperty("KeyName") or defaultValue;

-- Check initialization status
local bInit = Game:GetProperty("Mod_Initialized") or false;
```

## Key GamePlay API

> **API 查找优先用 `api-cheatsheet.md`（速查），不在表中则查 api.sqlite。** 以下仅列出最核心的函数快速参考。

### Game State
```lua
Game.GetLocalPlayer()                        -- Local player ID (may be < 0 for observers)
Game.GetCurrentGameTurn()                    -- Current turn
Game.GetRandNum(maxValue, "LogString")       -- Seeded random number
Game:GetProperty(key)                        -- Persisted property
Game:SetProperty(key, value)
Game.IsVictoryEnabled("VICTORY_DOMINATION")
Game.GetReligion():GetReligions()            -- World religions
```

### Player Manager
```lua
PlayerManager.GetAliveIDs()                  -- Array of alive player IDs
PlayerManager.GetAlive()                     -- All alive player objects
PlayerManager.GetAliveMajors()
PlayerManager.GetAliveMinors()
```

### Player Access
```lua
local pPlayer = Players[iPlayerID];
pPlayer:GetCities() / pPlayer:GetUnits()
pPlayer:GetTechs() / pPlayer:GetCulture()
pPlayer:GetTreasury() / pPlayer:GetReligion()
pPlayer:GetResources() / pPlayer:GetTrade()
pPlayer:GetInfluence() / pPlayer:GetDiplomacy()
pPlayer:GetWMDs() / pPlayer:GetStats()
pPlayer:IsAlive() / IsHuman() / IsMajor()
pPlayer:IsTurnActive()
pPlayer:GetEra()                           -- 0-based

-- Player Config (static data)
local cfg = PlayerConfigurations[iPlayerID];
cfg:GetCivilizationTypeName()
cfg:GetLeaderTypeName()
cfg:GetPlayerName()
cfg:GetCivilizationShortDescription()
```

### Cities
```lua
local cities = pPlayer:GetCities();
local pCity = cities:GetFirstRangedAttackCity();
pCity:GetBuildings()
pCity:ChangePopulation(amount)
pCity:GetName()
```

### Units
```lua
local pUnit = ...;
pUnit:GetUnitType() / pUnit:GetOwner() / pUnit:GetComponentID()
pUnit:GetMovesRemaining() / pUnit:GetAttacksRemaining()
pUnit:GetCombat() / pUnit:GetRangedCombat() / pUnit:GetBombardCombat()
pUnit:GetX() / pUnit:GetY()
pUnit:GetGreatPerson():GetIndividual()
pUnit:GetMilitaryFormation()
pUnit:GetFortifyTurns()
pUnit:HasMovedIntoZOC()
pUnit:GetMovementMovesRemaining()

-- Unit Manager
UnitManager.CanStartOperation(kUnit, operationType, nil, tParameters)
UnitManager.RequestOperation(kUnit, operationType, tParameters)
UnitManager.GetReachableTargets(kUnit)
UnitManager.GetReachableMovement(kUnit)
UnitManager.GetReachableZonesOfControl(kUnit, bool)
UnitManager.CanFormMilitaryFormation(...)
```

### Map
```lua
Map.GetPlotByIndex(index)
Map.GetPlot(x, y)
Map.GetPlotXY(plotX, plotY, dx, dy)              -- offset from (plotX, plotY)
Map.GetPlotCount()
Map.GetPlotDistance(plotA, plotB)
Map.GetResourceCount(resourceHash)
```

### Diplomacy
```lua
local pDiplomacy = pPlayer:GetDiplomacy();
pDiplomacy:HasMet(otherPlayerID)
-- Declare war, make peace, etc.
```

### Players Visibility
```lua
PlayersVisibility[iPlayerID]:ChangeVisibilityCount(iObserverID, delta)
PlayersVisibility[iPlayerID]:RevealAllPlots(observerID, bReveal)
```

### Database Access
```lua
-- Direct access
GameInfo.Resources["RESOURCE_IRON"].Hash
GameInfo.Units["UNIT_WARRIOR"].Cost
GameInfo.Improvements["IMPROVEMENT_FARM"].Name

-- Iteration
for row in GameInfo.Units() do ... end
for row in GameInfo.Resources() do
    if row.ResourceClassType == "RESOURCECLASS_LUXURY" then ... end
end
for row in GameInfo.Improvement_ValidResources() do ... end
for row in GameInfo.Adjacency_YieldChanges() do ... end
```

### DB.Query — Direct SQL

大表筛选、聚合、JOIN 时用 SQLite 侧过滤代替 Lua 侧全遍历：

```lua
local results = DB.Query(
    "SELECT Name, Value FROM ModifierArguments WHERE ModifierId = 'MODIFIER_XY'")
for _, row in ipairs(results) do
    print(row.Name, row.Value)
end
```

### Improvement / Terrain Modifications
```lua
ImprovementBuilder.SetImprovementType(plot, improvementType, playerID)
TerrainBuilder.SetTerrainType(plot, terrainIndex)
```

## GameEvents.* (C++ Hooks)

```lua
GameEvents.CanUseResolutions.Add(function(resolutions) ... end);
GameEvents.WC_Validate_LuxuryBan.Add(function(resType, playerId, options) ... end);
GameEvents.WC_Validate_PowerResourceBan.Add(function(resType, playerId, options) ... end);
GameEvents.WC_Validate_YieldBan.Add(function(resType, playerId, options) ... end);
GameEvents.WC_Validate_PowerBuilding.Add(function(resType, playerId, options) ... end);
```

## Key Differences from UI Lua

| UI Lua | GamePlay Lua |
|--------|-------------|
| Needs matching `.xml` file | **No XML needed** |
| Uses `ContextPtr` / `Controls` | No UI access |
| Uses `Events.*` / `LuaEvents.*`（UI 上下文互播） | Uses `GameEvents.*` / `Events.*`；跨文件通信用 `LuaEvents.*` |
| Runs on UI thread | Runs on game core side |
| Loaded per-screen / per-context | Loaded once per game |
| Can read database via `GameInfo` | Can read AND modify game state |

## Advanced GamePlay Patterns

### SetProperty / GetProperty — Save Data

Works on: `Player`, `Game`, `Unit`, `City`, `Plot`. Survives save/load.

```lua
pPlayer:SetProperty("MY_FLAG_KEY", true);
local val = pPlayer:GetProperty("MY_FLAG_KEY");
if val == nil then return; end  -- not set
```

UI can only GetProperty. Gameplay can both Get and Set.

### UI <—> Gameplay Communication

#### 1. GP→UI 推送: `ReportingEvents.SendLuaEvent`（首推）

GP 数据变更后主动推送，UI 不轮询。

```lua
-- === GP 端 ===
ReportingEvents.SendLuaEvent('MyEvent', {
    playerID = playerID,
    data = someValue,
})

-- === UI 端 ===
LuaEvents.MyEvent.Add(function(params)
    UpdateDisplay(params.data)
end)
```

#### 2. UI→GP 动作: `PlayerOperations.EXECUTE_SCRIPT`（按钮触发的唯一方式）

按钮回调中触发的一切 UI→GP 调用必须走 EXECUTE_SCRIPT，禁止通过 ExposedMembers 直接调用 GP 函数。

```lua
-- UI calls:
local params = {};
params.OnStart = "MyOperationName";
params.SomeData = 42;
UI.RequestPlayerOperation(iPlayer, PlayerOperations.EXECUTE_SCRIPT, params);

-- GP receives:
function MyOperationName(playerID:number, params:table)
    -- do work
end
GameEvents.MyOperationName.Add(MyOperationName);
```

#### 3. GP↔UI 被动读取: PROPERTY 直接读（跨端）；GP 同端跨文件通知用 LuaEvents

UI 刷新查询时被动读取 GP 数据。优先用 PROPERTY 直接读（零跨状态调用），共享读取函数定义在 Core 文件中，GP 和 UI 各自 `include()` 即可。

```lua
-- Core 文件中定义（GP/UI 均可 include）：
function GetMyData(playerID)
    return Players[playerID]:GetProperty("MY_KEY") or 0
end
```

UI 可直接读 PROPERTY：`Players[id]:GetProperty("KEY")` / `pPlot:GetProperty("KEY")` 在 UI 侧同样可用。
`LuaEvents` 用于 GP 同端跨文件通信（多个 GP 文件互相通知）：接收端 `LuaEvents.X.Add(fn)`（文件加载期注册），触发端 `LuaEvents.X(params)`；表格按引用传递，handler 回写结果、调用方无需 return 即可读。**禁止跨端**：GP↔UI 不互通，GP→UI 用 `ReportingEvents.SendLuaEvent`，UI→GP 用 `EXECUTE_SCRIPT`。UI 需要读取 GP 数据时使用 PROPERTY 直接读或 Core 共享读取函数。

### AttachModifierByID — Dynamic Modifier

Define the modifier in database first, then attach at runtime:

```lua
pPlayer:AttachModifierByID("MODIFIER_MY_DYNAMIC");
pCity:AttachModifierByID("MODIFIER_MY_CITY_DYNAMIC");
```

The modifier stays permanently on the object. Use only on `pPlayer` and `pCity`.

### PlotProperty + REQUIREMENT_PLOT_PROPERTY_MATCHES

Set a property on a city's plot via Lua, then use database Requirement to activate a Modifier:

**Lua:**
```lua
local pPlot = Map.GetPlot(cityX, cityY);
pPlot:SetProperty("MY_PLOT_FLAG", someValue);
```

**Database:**
```xml
<Requirement>
    <Row RequirementId="REQ_MY_PLOT_PROP" RequirementType="REQUIREMENT_PLOT_PROPERTY_MATCHES">
        <PropertyName>MY_PLOT_FLAG</PropertyName>
        <PropertyMinimum>1</PropertyMinimum>
    </Row>
</Requirement>
```

This lets Lua dynamically toggle database-defined Modifiers.

### Property-Based Player/City/Unit Binding

Use special Modifiers to stamp a property, then detect it in Lua:

| ModifierType | Targets |
|---|---|
| `MODIFIER_PLAYER_ADJUST_PROPERTY` | Player |
| `MODIFIER_SINGLE_CITY_ADJUST_PROPERTY` | Single City |
| `MODIFIER_UNIT_ADJUST_PROPERTY` | Unit (via UnitAbility) |

```lua
local prop = pPlayer:GetProperty("My_Property_Key");
if prop then
    -- This player has our trait/ability
end
```

### Virtual Buildings

Buildings with no model, no icon, for functional purposes:
- `PrereqDistrict` — leave empty
- `MustPurchase=1` — prevents appearing in production/purchase UI
- `CivilopediaPageExcludes` — hide from Civilopedia

Common uses: building prerequisites, LA switching, new system abilities.

```lua
-- Grant
pCity:GetBuildQueue():CreateBuilding(GameInfo.Buildings["BUILDING_XXX"].Index);
-- Remove
pCity:GetBuildings():RemoveBuilding(GameInfo.Buildings["BUILDING_XXX"].Index);
```

### Variable Unit Combat Strength

Two-step approach: adjust a property, then read that property as combat strength:

1. Database: `MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH` with `<Name>Key</Name> <Value>MY_COMBAT_PROP</Value>`
2. Lua: set the property on units dynamically, the modifier reads it automatically.

```lua
unit:SetProperty("MY_COMBAT_PROP", newValue);
```

### Selective Event Add (Performance)

Only subscribe to events when the relevant player/civ/leader is present:

```lua
function Initialize()
    --We can use type-checking function to ensure we only subscribe to events for the relevant player
    Events.SampleEvent.Add(OnSampleEvent);
            
       
    
end
Events.LoadGameViewStateDone.Add(Initialize);
```
