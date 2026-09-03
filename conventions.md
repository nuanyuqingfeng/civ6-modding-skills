# Conventions & Templates

Civ6 uses **Havok Script** (Lua with optional type annotations). Tabs = 4 spaces.

## Naming Conventions

### Variable Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `m_` | File-scoped member | `m_isDirty`, `m_currentID` |
| `g_` | Global (cross-file accessible) | `g_TrackedItems`, `g_kMessageInfo` |
| `k` | Table parameter / table member | `kUnit`, `kInfo`, `m_kFilters` |
| `p` | C++ object pointer | `pPlayer`, `pCity`, `pUnit` |
| `e` | Enum / numeric value | `ePlayer`, `eTech`, `eOldMode` |
| `s` | String value | `sTooltip`, `sName` |
| `ui` | UI control reference | `uiLeader`, `uiEntry` |
| `b` / `is` | Boolean | `bIsConcrete`, `isTruncated` |
| `i` | Index / counter | `iPlayer`, `iIndex` |

### Function Naming

| Convention | Scope | Example |
|-----------|-------|---------|
| `PascalCase` | Public / event handlers | `RefreshYields()`, `OnTurnBegin()` |
| `camelCase` | Local / private | `resetOverflowArrow()` |
| `On` prefix | Event / callback | `OnCityInitialized`, `OnResearchChanged` |
| `Update` prefix | Content update | `UpdateResearchPanel` |
| `Refresh` prefix | Full re-render | `RefreshAll`, `RefreshYields` |
| `Realize` prefix | UI layout | `RealizeStack`, `RealizeEmptyMessage` |
| `Get` prefix | Data retrieval | `GetYieldTextIcon`, `GetData` |

### Type Annotations

```lua
local value : number  = 0;
local name  : string  = "";
local flag  : boolean = false;
local tbl   : table   = {};
local obj   : object  = nil;          -- C++ game object
function GetValue( pUnit:table ) : number
    return pUnit:GetX();
end
```

### Constant Prefixes

| Prefix | Use | Example |
|--------|-----|---------|
| `COLOR_` | ABGR color numbers | `COLOR_WHITE` |
| `PIC_` | Texture names (DDS or BLP) | `PIC_DEFAULT_LEADER` |
| `SIZE_` | Pixel dimensions | `SIZE_ICON_SMALL` |
| `TXT_` | Pre-localized string | `TXT_END_TURN` |

## UI Lua File Template

Every UI context Lua file follows this structure:

```lua
-- ===========================================================================
--  FILE NAME - Brief description
-- ===========================================================================

include("InstanceManager");
include("SupportFunctions");
include("Civ6Common");
-- ... more includes as needed ...

-- ===========================================================================
--  CONSTANTS
-- ===========================================================================
local MAX_BEFORE_TRUNC :number = 180;
local RELOAD_CACHE_ID  :string = "MyContextName";

-- ===========================================================================
--  MEMBERS (m_ prefix)
-- ===========================================================================
local m_kInstanceIM :table   = InstanceManager:new("InstanceType", "RootControl", Controls.MyStack); -- 三参数：模板名, 根控件ID, 父容器（仅当父控件非Context直接子控件时需要）
local m_isDirty     :boolean = false;

-- ===========================================================================
function OnShow()
    Refresh();
end

function OnInputHandler( pInputStruct:table )
    local uiMsg = pInputStruct:GetMessageType();
    if uiMsg == KeyEvents.KeyUp then
        if pInputStruct:GetKey() == Keys.VK_ESCAPE then
            Close();
            return true;    -- handled
        end
    end
    return false;           -- not handled
end

-- ===========================================================================
function Refresh()
    ContextPtr:ClearRequestRefresh();
    -- Build / update UI ...
end

-- ===========================================================================
function OnContextInitialize( isReload:boolean )
    if isReload then
        LuaEvents.GameDebug_GetValues(RELOAD_CACHE_ID);
    end
    Refresh();
end

function OnShutdown()
    -- Remove C++ event listeners
    Events.LocalPlayerTurnBegin.Remove( OnTurnBegin );
    -- Save state for hot reload
    LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, "m_state", m_state);
end

-- ===========================================================================
function Initialize()
    ContextPtr:SetInitHandler( OnContextInitialize );
    ContextPtr:SetShowHandler( OnShow );
    ContextPtr:SetInputHandler( OnInputHandler, true );  -- true = extended
    ContextPtr:SetShutdown( OnShutdown );

    -- C++ engine events
    Events.LocalPlayerTurnBegin.Add( OnTurnBegin );

    -- Lua broadcast events
    LuaEvents.MyEventName.Add( OnMyEventHandler );

    -- Control callbacks
    Controls.MyButton:RegisterCallback( Mouse.eLClick, OnButtonClicked );
end
Initialize();  -- CRITICAL: must be called at end of file
```

## GamePlay Lua File Template

```lua
print("Initializing MyMod Lua");

-- ===========================================================================
--  Cached data
-- ===========================================================================
local cachedData = nil;

-- ===========================================================================
function Initialize()
    local bInitialized :boolean = Game:GetProperty("MyMod_Initialized") or false;
    if bInitialized == false then
        InitializeNewGame();
        Game:SetProperty("MyMod_Initialized", true);
    end
end

function InitializeNewGame()
    for row in GameInfo.Units() do
        -- Setup ...
    end
    for _, iPlayerID in ipairs(PlayerManager.GetAliveIDs()) do
        -- Per-player setup ...
    end
end

-- ===========================================================================
--  Game event hooks
-- ===========================================================================
GameEvents.OnSomething.Add(function(playerID, data)
    -- Handle ...
end);

Initialize();
```

## Include System

```lua
include("InstanceManager");       -- UI instance pooling
include("SupportFunctions");      -- String/table/math utilities
include("Civ6Common");           -- Common Civ6 helpers
include("ToolTipHelper");        -- Tooltip generation
include("GameCapabilities");     -- HasCapability(), expansion checks
include("Colors");               -- Color constants
include("PopupDialog");          -- Popup dialog system
include("ButtonUtilities");      -- Button helpers
include("PlayerSupport");        -- Player utilities
include("LeaderIcon");           -- Leader icon management

-- Glob include (loads all matching files):
include("WorldTrackerItem_", true);  -- true = glob mode
```

**Important**: Include files copy ALL content into the local context. Minimize local variables in include files to avoid size bloat and name conflicts.

## LOC Tag 推导表（事前预防层）

写任何文本行前按本表推导 tag——**推导有表、出错有检**（事后兜底 = `rgn_validate` / `civ6_text_audit`）。
规则：`{ID}` 一律原样大写；游戏按「当前语言 → en_US → 显示裸 tag」回退，缺词条即裸 tag。

| 你定义的主体 Type | 脚本/AI 必须推导出的 tag |
|---|---|
| `CIVILIZATION_X` | `LOC_CIVILIZATION_X_NAME` / `_DESCRIPTION` / `_ADJECTIVE`；图标 `ICON_CIVILIZATION_X` |
| `LEADER_X` | `LOC_LEADER_X_NAME` / `_QUOTE`；图标 `ICON_LEADER_X`；加载语 `LOC_LOADING_INFO_LEADER_X` |
| `TRAIT_X`（文明/领袖能力） | `LOC_TRAIT_X_NAME` / `_DESCRIPTION` |
| `BUILDING_X` / `DISTRICT_X` | `LOC_{Type}_NAME` / `_DESCRIPTION`；图标 `ICON_{Type}` |
| `UNIT_X` | `LOC_UNIT_X_NAME` / `_DESCRIPTION` / `_CIVILOPEDIA`；图标 `ICON_UNIT_X`（55/64/80/256） |
| `IMPROVEMENT_X` | `LOC_IMPROVEMENT_X_NAME` / `_DESCRIPTION`；图标 `ICON_IMPROVEMENT_X` |
| `RESOURCE_X` | `LOC_RESOURCE_X_NAME` / `_DESCRIPTION` / `_CIVILOPEDIA`；图标 `ICON_RESOURCE_X` |
| `POLICY_X` | `LOC_POLICY_X_NAME` / `_DESCRIPTION` |
| `PROJECT_X` | `LOC_PROJECT_X_NAME` / `_DESCRIPTION` / `_SHORT_DESCRIPTION` |
| 城市 `"Chang'an"`（英文名） | `LOC_CITY_NAME_CHANGAN`（撇号剔除、非字母数字→`_`、合并、大写） |
| 公民名（第 i 个） | `LOC_CITIZEN_{SHORT}_MALE_i` / `_FEMALE_i`（现代组加 `_MODERN` 段） |
| 文明信息四栏 | `LOC_CIVINFO_{SHORT}_LOCATION` / `_SIZE` / `_POPULATION` / `_CAPITAL` |
| 领袖百科段落 i | `LOC_PEDIA_LEADERS_PAGE_LEADER_X_CHAPTER_CAPSULE_BODY` / `_DETAILED_BODY` / `_HISTORY_PARA_i` |
| mod 自身（id=MyMod） | `LOC_MYMOD_MOD_TITLE` / `_MOD_TEASER` / `_MOD_DESCRIPTION`（id 转大写） |

**配套硬校验**（写完即跑，报错先改源头再交付）：
- id 冲突前置：`python database/scripts/query_civ6_db.py --check-id <新TYPE...>`（命中内置 Type 即冲突）
- 同 tag 多语言 `[NEWLINE]` 分段数必须一致（pedia 类长文本易漂移）
- 全树残留占位符扫描：`\{[A-Z][A-Z0-9_]+\}`（Text/Data/UI 目录；排除合法 PowerShell/Lua 片段）

本表只管 **tag 后半段的推导**（`_NAME/_DESCRIPTION/ICON_...`），两处规则正交叠加使用。
