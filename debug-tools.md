# Debug & Tuner Tools

## Debug Directory

```
{SteamLibrary}\steamapps\common\Sid Meier's Civilization VI\Debug\
```

Contains **35 Lua Tuner Panel (`.ltp`) files** and `Civ6TunerPlugin.dll`. These are in-game debug/cheat panels.

Available panels:
- `Forge.ltp`, `Audio.ltp`, `City.ltp`, `Unit.ltp`, `Player.ltp`, `Players.ltp`
- `Map.ltp`, `AI.ltp`, `Network.ltp`, `Diplomacy.ltp`, `Modifiers.ltp`
- `Great People.ltp`, `Heroes.ltp`, `Random Events.ltp`, `Requirements.ltp`
- `AutoProfiler.ltp`, `Autoplay.ltp`, `Defeats.ltp`, `Storms.ltp`
- `DebugOptions.ltp` — Debug menu options
- `DefaultPanels.xml` — Lists which panels auto-load

## Lua Tuner Panel (.ltp) Format

XML-based with embedded Lua:

```xml
<PanelData>
    <Name>Forge</Name>
    <App>Civ6</App>
    <EnterAction>include("TunerUtilities")</EnterAction>
    <CompatibleStates>
        <string>FrontEnd</string>
        <string>InGame</string>
        <string>WorldBuilder</string>
    </CompatibleStates>

    <!-- Button actions -->
    <Actions>
        <ActionData>
            <Name>Play</Name>
            <Action>
                if TunerUtilities then
                    TunerUtilities:PlayAnimation()
                end
            </Action>
        </ActionData>
    </Actions>

    <!-- Read/write value controls -->
    <StringControls>
        <StringControlData>
            <Name>Path</Name>
            <GetFunction>
                function()
                    return currentPath
                end
            </GetFunction>
            <SetFunction>
                function(value)
                    currentPath = value
                end
            </SetFunction>
        </StringControlData>
    </StringControls>
</PanelData>
```

The Tuner is a separate application that connects to a running Civ6 process for live debugging. It reads `.ltp` files to build its UI.

## Hot Reload Support

UI Lua files can support hot reload (in Asset Editor) by saving state:

```lua
-- In OnShutdown(), save state:
function OnShutdown()
    local kData = {
        m_state = m_state,
        m_currentID = m_currentID,
    };
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, kData, ...);
end

-- In OnContextInitialize(), restore state:
function OnContextInitialize( isReload:boolean )
    if isReload then
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID);
    end
end

-- Handle restored data:
function OnGameDebugReturn( context, dataTable )
    if context == RELOAD_CACHE_ID then
        m_state = dataTable.m_state;
        m_currentID = dataTable.m_currentID;
    end
end
```

## Modding Workflow

1. Create mod folder under `DLC/<ModName>/`
2. Write `.modinfo`, Lua, XML, and data files
3. Launch Civ6 and enable the mod
4. Use the Tuner to debug/inspect game state
5. Hot reload changes via Asset Editor (save -> build -> Hot Load)

## Useful Debug Commands in Lua

```lua
print("Debug message: " .. tostring(value));
UI.DataError("Error: " .. tostring(value));    -- Log an error visible in UI
UI.AssertMsg(condition, "message");            -- Assertion check
UI.HighlightPlots(PlotHighlightTypes.PLACEMENT, true, plotTable);  -- Highlight plots
```
