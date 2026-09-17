# Event System

Civ6 has **three separate event systems**. Using the wrong one is a common error.

## 1. C++ Engine Events (`Events.*`) — Single-target hooks

These are emitted by the C++ game engine. Register with `.Add()`, unregister with `.Remove()`.

```lua
-- Subscribe in Initialize()
Events.LocalPlayerTurnBegin.Add( OnTurnBegin );
Events.UnitOperationSegmentComplete.Add( OnUnitOpComplete );
Events.NotificationAdded.Add( OnNotificationAdded );

-- MUST unsubscribe in OnShutdown() to prevent leaks across context reloads
Events.LocalPlayerTurnBegin.Remove( OnTurnBegin );

-- Raise an engine event (usually called by C++ side, but can be raised in Lua):
Events.SomeEvent();
Events.ExitToMainMenu();
```

**`Events.*` 运行时实测 463 个**（UI 与 GP 两张表内容完全一致）。The most important ~100 are listed below by category. Use `python database/scripts/query_events.py --search 关键词` to look up any event's parameters and signature.

> **可用性实测（2026-09 FireTuner）**：引擎共注册 325 个 `GameCoreEvent`，其中 **277 个暴露到 `Events.*`**，另 **48 个完全不经 Lua**（仅引擎内部使用）。
> 这 48 个在 `events_enhanced.json` 中标注为 `availability: "None"` + `luaSubscribable: false`。
> ⚠ **UI 侧对不存在的事件写 `.Add()` 会抛 `attempt to index a nil value`，并中断所在函数后续的全部初始化**（不是静默失败）——示例工程 曾因此整个面板打不开。
> 判定某事件是否存在的**唯一权威探针**是 `type(Events.名称) == "table"`。

### Type Legend

| Type | Behavior |
|------|----------|
| `GameCoreEvent` | Core game state change. Available in both UI and GamePlay Lua. |
| `UIEvent` | UI-specific engine event. UI contexts only. |
| `SerialEvent` | UI serialization/state event. UI contexts only. |
| `LocalMachineEvent` | Local machine only (not networked). UI contexts. |
| `SequenceEvent` | UI flow/sequence state event. |

### Important Events by Category

#### Turn / Phase

| Event | Parameters | Type |
|-------|-----------|------|
| TurnBegin |  | GameCoreEvent |
| TurnEnd |  | GameCoreEvent |
| PreTurnBegin |  | GameCoreEvent |
| PhaseBegin |  | GameCoreEvent |
| PhaseEnd |  | GameCoreEvent |
| LocalPlayerTurnBegin |  | GameCoreEvent |
| LocalPlayerTurnEnd |  | GameCoreEvent |
| LocalPlayerTurnUnready |  | GameCoreEvent |
| PlayerTurnActivated | playerID:number, isFirstTurn:boolean | GameCoreEvent |
| PlayerTurnDeactivated | playerID:number | GameCoreEvent |
| PlayerTurnCompleteIgnored |  | GameCoreEvent |
| RemotePlayerTurnBegin |  | GameCoreEvent |
| RemotePlayerTurnEnd |  | GameCoreEvent |
| EndTurnBlockingChanged | EndTurnBlockingTypes prev, EndTurnBlockingTypes new | GameCoreEvent |
| EndTurnDirty |  | GameCoreEvent |
| GameEraChanged | previousEraIndex:number, newEraIndex:number | GameCoreEvent |
| AfterPlayerTurnActivated |  | UIEvent |

#### City

| Event | Parameters | Type |
|-------|-----------|------|
| CityAddedToMap | playerID:number, cityID:number, x:number, y:number | GameCoreEvent |
| CityRemovedFromMap | playerID:number, cityID:number | GameCoreEvent |
| CityChanged |  | GameCoreEvent |
| CityInitialized | playerID:number, cityID:number, x:number, y:number | GameCoreEvent |
| CityProductionChanged | playerID:number, cityID:number, productionID:number, objectID:number, wasCancelled:boolean | GameCoreEvent |
| CityProductionCompleted | playerID:number, cityID:number, constructionType:number, unitID:number, wasCancelled:boolean | GameCoreEvent |
| CityProductionUpdated | playerID:number, cityID:number, objectID:number, productionID:number | GameCoreEvent |
| CityProductionQueueChanged |  | GameCoreEvent |
| CityProjectCompleted | playerID:number, cityID:number, projectID:number, buildingIndex:number, x:number, y:number, isCancelled | GameCoreEvent |
| CityPopulationChanged | playerID:number, cityID:number, cityPopulation:number | GameCoreEvent |
| CityFocusChanged | playerID:number, cityID:number | GameCoreEvent |
| CityMadePurchase | playerID:number, cityID:number, x:number, y:number, EventSubTypes, purchasableItemIndex:number | GameCoreEvent |
| CityLoyaltyChanged | playerID:number, cityID:number | GameCoreEvent |
| CityPowerChanged |  | GameCoreEvent |
| CitySiegeStatusChanged | playerID:number, cityID:number, isBesieged:boolean | GameCoreEvent |
| CityLiberated | playerID:number, cityID:number | GameCoreEvent |
| CityOccupationChanged | playerID:number, cityID:number | GameCoreEvent |
| CityTransfered | newOwnerID:number, cityID:number, oldOwnerID:number, CityTransferTypes | GameCoreEvent |
| CapitalCityChanged | playerID:number, cityID:number | GameCoreEvent |
| CityTileOwnershipChanged | playerID:number, cityID:number, x:number, y:number | GameCoreEvent |
| CityUnitsChanged | playerID:number, cityID:number | GameCoreEvent |
| CityVisibilityChanged | playerID:number, cityID:number, eVisibility:number | GameCoreEvent |
| CityReligionChanged | playerID:number, cityID:number, eVisibility:number, otherCityID:number | GameCoreEvent |
| CityReligionFollowersChanged | playerID:number, cityID:number, eVisibility:number, influencingCItyID:number | GameCoreEvent |
| CityWorkerChanged | ownerPlayerID:number, cityID:number, x:number, y:number | GameCoreEvent |

#### Unit

| Event | Parameters | Type |
|-------|-----------|------|
| UnitAddedToMap | playerID:number, unitID:number | GameCoreEvent |
| UnitRemovedFromMap | playerID:number, unitID:number | GameCoreEvent |
| UnitMoved | playerID:number, unitID:number, x:number, y:number, locallyVisible, stateChange | GameCoreEvent |
| UnitMoveComplete | playerID:number, unitID:number, x:number, y:number | GameCoreEvent |
| UnitDamageChanged | playerID:number, unitID:number, newDamage:number, prevDamage:number | GameCoreEvent |
| UnitKilledInCombat | killedPlayerID:number, killedUnitID:number, playerID:number, unitID:number | GameCoreEvent |
| UnitPromoted | playerID:number, unitID:number | GameCoreEvent |
| UnitPromotionAvailable | playerID:number, unitID:number, promotionID:number | GameCoreEvent |
| UnitOperationStarted | ownerID:number, unitID:number, operationID:number | GameCoreEvent |
| UnitOperationDeactivated | playerID:number, unitID:number, UnitOperationTypes, data1:number | GameCoreEvent |
| UnitOperationSegmentComplete | playerID:number, unitID:number, UnitCommandTypes, data1:number | GameCoreEvent |
| UnitOperationsCleared | playerID:number, unitID:number, UnitCommandTypes, data1:number | GameCoreEvent |
| UnitAbilityGained | playerID:number, unitID:number, unitAbilityIndex:number | GameCoreEvent |
| UnitAbilityLost | playerID:number, unitID:number, unitAbilityIndex:number | GameCoreEvent |
| UnitTeleported | playerID:number, unitID:number, x:number, y:number | GameCoreEvent |
| UnitUpgraded | playerID:number, unitID:number | GameCoreEvent |
| UnitEmbarkedStateChanged | playerID:number, unitID:number, isEmbarked:boolean | GameCoreEvent |
| UnitCaptured | currentUnitPlayerID:number, unitID:number, owningPlayerID:number, capturingPlayerID:number | GameCoreEvent |
| UnitCommandStarted | playerID:number, unitID:number, UnitCommandTypes, data1:number | GameCoreEvent |
| UnitFormArmy | playerID:number, unitID:number | GameCoreEvent |
| UnitFormCorps | playerID:number, unitID:number | GameCoreEvent |
| UnitEnterFormation | firstUnitPlayerID:number, firstUnitID:number, secondUnitPlayerID:number, secondUnitID:number | GameCoreEvent |
| UnitExitFormation | firstUnitPlayerID:number, firstUnitID:number, secondUnitPlayerID:number, secondUnitID:number | GameCoreEvent |
| UnitGreatPersonCreated | playerID:number, unitID:number, greatPersonClassID:number, greatPersonIndividualID:number | GameCoreEvent |
| UnitGreatPersonActivated | unitPlayerID:number, unitOwner:number, unitID:number, greatPersonClassID:number, greatPersonIndividualID:number | GameCoreEvent |
| UnitTradeChanged | playerID:number, unitID:number | GameCoreEvent |
| UnitVisibilityChanged | playerID:number, unitID:number | GameCoreEvent |
| UnitMovementPointsChanged | playerID:number, unitID:number, movementPoints:number | GameCoreEvent |
| UnitActivityChanged | playerID:number, unitID:number, ActivityTypes | GameCoreEvent |

#### Combat

| Event | Parameters | Type |
|-------|-----------|------|
| Combat | combatResult:table | GameCoreEvent |
| CombatVisBegin |  | SerialEvent |
| CombatVisEnd |  | SerialEvent |
| DistrictCombatChanged | EventSubTypes, playerID:number, districtID:number | GameCoreEvent |
| DistrictDamageChanged | playerID:number, districtID:number, DefenseTypes, newDamage:number, oldDamage:number | GameCoreEvent |

#### Player

| Event | Parameters | Type |
|-------|-----------|------|
| PlayerDefeat | playerID:number, defeatIndex:number, eventID:number | GameCoreEvent |
| PlayerVictory |  |  |
| PlayerDestroyed |  | GameCoreEvent |
| PlayerRestored |  | GameCoreEvent |
| PlayerRevived |  | GameCoreEvent |
| PlayerEraChanged | playerID:number, eraIndex:number | GameCoreEvent |
| PlayerEraScoreChanged | playerID:number, amountAwarded:number | GameCoreEvent |
| PlayerBordersChanged |  | GameCoreEvent |
| PlayerResourceChanged | ownerPlayerID:number, resourceTypeID:number | PlayerGameCoreEvent |
| LocalPlayerChanged | localPlayerID:number, prevLocalPlayerID:number | GameCoreEvent |
| PlayerAgeChanged | playerID:number | GameCoreEvent |
| PlayerDarkAgeChanged | playerID:number | GameCoreEvent |
| PlayerEraTransitionBegins | playerID:number | GameCoreEvent |

#### Diplomacy

| Event | Parameters | Type |
|-------|-----------|------|
| DiplomacyMeet | player1ID:number, player2ID:number | GameCoreEvent |
| DiplomacyDeclareWar | firstPlayerID:number, secondPlayerID:number | GameCoreEvent |
| DiplomacyMakePeace | firstPlayerID:number, secondPlayerID:number | GameCoreEvent |
| DiplomacyDealEnacted |  | GameCoreEvent |
| DiplomacyDealExpired |  | GameCoreEvent |
| DiplomacyIncomingDeal | fromPlayerID:number, toPlayerID:number, DiplomacyActionTypes | GameCoreEvent |
| DiplomacySessionClosed | sessionID:number | GameCoreEvent |
| DiplomacyStatement | actingPlayerID:number, reactingPlayerID:number, values:table | GameCoreEvent |
| AllianceAvailable | playerID:number, otherplayerID:number, allianceIndex:number | GameCoreEvent |
| AllianceEnded | playerID:number, otherplayerID:number, allianceIndex:number | GameCoreEvent |

#### Research / Culture / Policies

| Event | Parameters | Type |
|-------|-----------|------|
| ResearchChanged | playerID:number, technologyIndex:number | GameCoreEvent |
| ResearchCompleted | playerID:number, technologyIndex:number | GameCoreEvent |
| TechBoostTriggered | playerID:number, techBoosted:number, unknownA:number, unknownB:number | GameCoreEvent |
| CivicChanged | playerID:number, civicIndex:number | GameCoreEvent |
| CivicCompleted | playerID:number, civicIndex:number, isCancelled:number | GameCoreEvent |
| CivicBoostTriggered | playerID:number, civicIndex:number, unknownA:number, unknownB:number | GameCoreEvent |
| GovernmentChanged | playerID:number, governmentID:number | GameCoreEvent |
| GovernmentPolicyChanged | playerID:number, policyID:number | GameCoreEvent |
| GovernmentPolicyObsoleted | playerID:number | GameCoreEvent |
| CultureChanged |  | GameCoreEvent |
| CultureYieldChanged | playerID:number | GameCoreEvent |
| ResearchYieldChanged | playerID:number | GameCoreEvent |

#### Religion

| Event | Parameters | Type |
|-------|-----------|------|
| ReligionFounded | playerID:number, religionID:number | GameCoreEvent |
| PantheonFounded | playerID:number | GameCoreEvent |
| BeliefAdded | playerID:number, beliefID:number | GameCoreEvent |
| FaithChanged | playerID:number, yield:number, balance:number | GameCoreEvent |

#### Map / Plot / Buildings

| Event | Parameters | Type |
|-------|-----------|------|
| BuildingAddedToMap | x:number, y:number, buildingIndex:number, playerID:number, cityID:number, percentComplete:number, isPillaged:boolean | GameCoreEvent |
| BuildingChanged | x:number, y:number, buildingID:number, playerID:number, percentComplete:number, unknown:number | GameCoreEvent |
| BuildingRemovedFromMap | x:number, y:number | GameCoreEvent |
| DistrictAddedToMap | playerID:number, districtID:number, cityID:number, x:number, y:number, districtIndex:number, percentComplete:number | GameCoreEvent |
| DistrictRemovedFromMap | playerID:number, districtID:number, cityID:number, x:number, y:number, districtIndex:number | GameCoreEvent |
| DistrictPillaged | ownerID:number, districtID:number, cityID:number, x:number, y:number, districtIndex:number, percentComplete:number, isPillaged:boolean | GameCoreEvent |
| ImprovementAddedToMap | x:number, y:number, improvementIndex:number, playerID:number | GameCoreEvent |
| ImprovementChanged | x:number, y:number, improvementIndex:number, playerID, resourceIndex, isPillaged, isWorked | GameCoreEvent |
| ImprovementRemovedFromMap | x:number, y:number, owningPlayerID:number | GameCoreEvent |
| FeatureAddedToMap | x:number, y:number | GameCoreEvent |
| FeatureRemovedFromMap | x:number, y:number | GameCoreEvent |
| PlotVisibilityChanged | x:number, y:number, visibilityType:number | GameCoreEvent |
| PlotYieldChanged | x:number, y:number | GameCoreEvent |
| MapYieldsChanged |  | GameCoreEvent |
| ResourceAddedToMap | x:number, y:number, resourceIndex:number | GameCoreEvent |
| ResourceRemovedFromMap | iX:number, iY:number, resourceIndex:number | GameCoreEvent |
| TerrainTypeChanged |  | GameCoreEvent |
| WonderCompleted | x:number, y:number, buildingIndex:number, playerIndex:number, cityID:number, percentComplete:number, unknown:number | GameCoreEvent |

#### Trade / Economy

| Event | Parameters | Type |
|-------|-----------|------|
| TreasuryChanged | playerID:number, yield:number, balance | GameCoreEvent |
| FavorChanged |  | GameCoreEvent |
| TradeRouteAddedToMap | playerID:number, x:number, y:number | GameCoreEvent |
| TradeRouteRemovedFromMap | playerID:number, x:number, y:number | GameCoreEvent |
| TradeRouteActivityChanged | playerID, originPlayerID, originCityID, targetPlayerID, targetCityID | GameCoreEvent |
| TradeRouteCapacityChanged | playerID:number | GameCoreEvent |

#### Governor / Spy / Great Person

| Event | Parameters | Type |
|-------|-----------|------|
| GovernorAppointed | playerID:number, governorID:number | GameCoreEvent |
| GovernorAssigned | cityPlayerID:number, cityID:number, governorPlayerID:number, governorID:number | GameCoreEvent |
| GovernorPromoted | playerID:number, governorIndex:number, promotionIndex:number | GameCoreEvent |
| GovernorChanged | playerID:number, governorID:number | GameCoreEvent |
| GovernorPointsChanged | playerID:number, delta:number | GameCoreEvent |
| SpyAdded | spyPlayerID:number, spyUnitID:number | GameCoreEvent |
| SpyMissionCompleted | playerID:number, missionID:number | GameCoreEvent |
| SpyRemoved | spyPlayerID:number, counterSpyPlayerID:number | GameCoreEvent |
| GreatPeoplePointsChanged | playerID:number | GameCoreEvent |
| GreatPeopleTimelineChanged |  | GameCoreEvent |
| GreatWorkCreated | playerID:number, unitID:number, cityPlotX:number, cityPlotY:number, buildingID:number, greatWorkID:number | GameCoreEvent |
| GreatWorkMoved | fromCityPlayerID, fromCityID, toCityPlayerID, toCityID, buildingID, greatWorkTypeIndex | GameCoreEvent |

#### WMD / Climate

| Event | Parameters | Type |
|-------|-----------|------|
| WMDCountChanged | playerID:number, WMDIndex:number | GameCoreEvent |
| WMDDetonated | x:number, y:number, playerID:number, WMDIndex:number | GameCoreEvent |
| ClimateChangeEvent |  | GameCoreEvent |
| NaturalWonderRevealed | x:number, y:number, featureIndex:number, wasFirstToFind:boolean | GameCoreEvent |
| StormAddedToMap |  | GameCoreEvent |
| StormRemovedFromMap |  | GameCoreEvent |
| DroughtAddedToMap |  | GameCoreEvent |
| DroughtRemovedFromMap |  | GameCoreEvent |

#### World Congress / Emergencies

| Event | Parameters | Type |
|-------|-----------|------|
| WorldCongressStage1 |  | GameCoreEvent |
| WorldCongressStage2 |  | GameCoreEvent |
| WorldCongressStage3 |  | GameCoreEvent |
| WorldCongressFinished |  | GameCoreEvent |
| EmergencyAvailable | targetPlayerID:number, emergencyIndex:number | GameCoreEvent |
| EmergencyStarted | playerID:number, targetPlayerID:number, turn:number | GameCoreEvent |
| EmergencyCompleted | playerID:number, targetPlayerID:number, turn:number | GameCoreEvent |

#### Notifications

| Event | Parameters | Type |
|-------|-----------|------|
| NotificationAdded | playerID:number, notificationID:number | GameCoreEvent |
| NotificationActivated | playerID:number, notificationID:number, wasActivatedByUser:boolean | GameCoreEvent |
| NotificationDismissed | playerID:number, notificationID:number | GameCoreEvent |
| NotificationRefreshRequested |  | GameCoreEvent |
| EventPopupRequest | popupData:table | GameCoreEvent |
| EventSoundRequest | sound:string, playerID:number | GameCoreEvent |

#### UI / Camera

| Event | Parameters | Type |
|-------|-----------|------|
| InterfaceModeChanged | InterfaceModeTypes prev, InterfaceModeTypes new | SerialEvent |
| InputActionTriggered | actionID:number | LocalMachineEvent |
| LensLayerOn |  | SerialEvent |
| LensLayerOff |  | SerialEvent |
| DragCamera |  | UIEvent |
| SystemUpdateUI | type, tag, data1:number, data2:number, data3:string | UIEvent |
| CursorHexPositionChanged |  | SerialEvent |
| ContextVisibilityChanged |  | UIEvent |

#### Load / Save / Game Init

| Event | Parameters | Type |
|-------|-----------|------|
| LoadComplete |  | SerialEvent |
| LoadScreenClose |  | SequenceEvent |
| AppInitComplete |  | SequenceEvent |
| GameViewStateDone |  | SequenceEvent |
| MainMenuStateDone |  | SequenceEvent |
| BeforeGameplayContentChange |  | SerialEvent |
| AfterGameplayContentChange |  | SerialEvent |

#### Event-Based Initialization

Use `LoadGameViewStateDone` for all event subscriptions to prevent `AddedToMap` series bugs:

```lua
function Initialize()
    Events.UnitMoved.Add(OnUnitMoved);
    Events.ImprovementAddedToMap.Add(OnImprovementAdded);
end

Events.LoadGameViewStateDone.Add(Initialize);
```

On hot reload, `OnContextInitialize(isReload:boolean)` receives `isReload=true` — call init work directly since the game is already loaded.

#### Options / Config

| Event | Parameters | Type |
|-------|-----------|------|
| OptionChanged |  | LocalMachineEvent |
| OptionsSaved |  | LocalMachineEvent |
| UserOptionChanged |  | SerialEvent |
| GameConfigChanged |  | LocalMachineEvent |

#### Multiplayer / Network

| Event | Parameters | Type |
|-------|-----------|------|
| MultiplayerGameLaunched |  | SerialEvent |
| MultiplayerPlayerConnected |  | LocalMachineEvent |
| MultiplayerPrePlayerDisconnected |  | LocalMachineEvent |
| MultiplayerChat |  | LocalMachineEvent |
| MultiplayerHostMigrated |  | LocalMachineEvent |
| SteamServersConnected |  | LocalMachineEvent |
| SteamServersDisconnected |  | LocalMachineEvent |

#### ARX / VR / Visual

| Event | Parameters | Type |
|-------|-----------|------|
| BeginGameView |  | LocalMachineEvent |
| EndGameView |  | LocalMachineEvent |
| BeginWonderReveal |  | LocalMachineEvent |
| EndWonderReveal |  | LocalMachineEvent |
| ShowLeaderScreen |  | LocalMachineEvent |
| HideLeaderScreen |  | LocalMachineEvent |
| ExitToMainMenu |  | LocalMachineEvent |

---

## 2. Lua Broadcast Events (`LuaEvents.*`) — Broadcasting to all UI contexts

No need to unregister — auto-cleanup on context teardown.

```lua
-- Subscribe
LuaEvents.MyEventName.Add( OnMyEventHandler );

-- Raise (broadcasts to ALL contexts currently loaded)
LuaEvents.ActionPanel_OpenChooseResearch();
LuaEvents.DiplomacyActionView_HideIngameUI.Add( OnHide );
LuaEvents.EndGameMenu_Shown.Add( OnEndGameMenuShown );

-- Raise with args
LuaEvents.ActionPanel_ActivateNotification( pNotification );
```

**LuaEvents naming convention**: Prefix with the raising context name.
```
LuaEvents.ActionPanel_ActivateNotification(...)
LuaEvents.InGame_OpenInGameOptionsMenu()
LuaEvents.ReportScreen_Open()
```

**LuaEvents data rules**:
- Only pass **simple types**: string, number, boolean.
- Tables are OK if they contain **only pure Lua data** (no C++ objects, no UI controls).
- Never pass UI controls or game engine objects — the owning context may delete them before the receiver processes the event.

**LuaEvents 共享表传参** — 无需额外返回值事件：

```lua
-- handler 同步执行，被调用方改表后调用方可立即读到：
local ctx = { a = 1, b = 2 }
LuaEvents.Handler(ctx)
print(ctx.c)    -- 3   ← handler 已同步修改完成
```

```lua
function Handler(ctx)
    ctx.c = 3    -- 只改表，不 dispatch 任何返回事件
end
```

There are **480 LuaEvents** (use `python database/scripts/query_events.py --search 关键词` for the full list). Key ones:

| Event | Purpose |
|-------|---------|
| ActionPanel_OpenChooseResearch / _OpenChooseCivic | Open research/civic chooser |
| CityPanel_ChooseProduction / _ChoosePurchase | Begin city production/purchase |
| DiplomacyActionView_HideIngameUI / _ShowIngameUI | Toggle normal UI during diplomacy |
| DiploPopup_ShowMakeDeal / _ShowMakeDemand | Open deal/demand popup |
| EndGameMenu_Shown / _Closed | Game over screen |
| Government_OpenGovernment / _CloseGovernment | Government screen |
| LaunchBar_RaiseCivicsTree / _RaiseTechTree | Open tree chooser |
| NotificationPanel_* | Notification button actions |
| PartialScreenHooks_Open* / _Close* | Open/close partial screens (espionage, city-states, trade, rankings) |
| Tutorial* | Tutorial system (UI control restrictions, highlights) |
| TunerEnterDebugMode / _ExitDebugMode | Fire Tuner connection |
| WorldInput_* | World mouse interaction |
| WorldTracker_* | Top-panel interaction |
| WorldBuilder_* | World Builder editor events |

---

## 3. GP→UI: `ReportingEvents.SendLuaEvent` — Gameplay pushes to UI

GP→UI 的标准推送方式。GP 数据变更后主动通知 UI，UI 不轮询。

```lua
-- === GP 端（发信）===
ReportingEvents.SendLuaEvent('MyEvent', {
    playerID = playerID,
    data = someValue,
})
```

```lua
-- === UI 端（收信）===
LuaEvents.MyEvent.Add(function(params)
    print(params.data)
end)
```

**规则：**
- GP 数据变更时主动推送，UI 在 `LuaEvents` handler 中更新显示
- UI **被动读取** GP 数据（刷新查询）只能用 PROPERTY 直接读或 Core 共享读取函数；`ExposedMembers` 禁止跨端暴露给 UI
- UI **主动触发 GP 动作**（按钮回调中）必须走 `EXECUTE_SCRIPT`，禁止通过 `ExposedMembers` 直接调用
- UI 可直接读 PROPERTY：`Players[id]:GetProperty("KEY")` / `pPlot:GetProperty("KEY")` 在 UI 侧同样可用。共享读取函数定义在 Core 文件中，GP 和 UI 各自 `include()` 即可

---

## 4. GamePlay Events (`GameEvents.*`) — GamePlay scripts only

Used exclusively in GamePlay Lua scripts (under `DLC/<Mod>/Scripts/`). NOT available in UI contexts.

```lua
-- Add a handler (return a table or modify parameters in place)
GameEvents.CanUseResolutions.Add(function(resolutions)
    resolutions.Resolutions = allowed_resolutions;
end);

GameEvents.WC_Validate_LuxuryBan.Add(function(resolutionType, playerId, options)
    options.ResolutionOptions = cachedLuxuryResources;
end);

GameEvents.PlayerTurnStarted.Add(function(playerID)
    -- Handle game event
end);
```

**Key difference**: GamePlay scripts run on the game core side, not the UI side. They cannot access UI controls, `ContextPtr`, or `Controls`. Both `Events.*` and `GameEvents.*` are available in GP; `LuaEvents.*` is UI-only.

> **⚠ 两条总线互不镜像（2026-09 FireTuner 对照实验，同上下文同时注册两边处理器）**
> | 事件 | `Events` 命中 | `GameEvents` 命中 |
> |---|---|---|
> | `UnitMoveComplete` | 11 | **0** |
> | `PlayerTurnStarted` | **0** | 17 |
>
> **实测事实**：两边**各自只在一张表上有回调**，注册到另一张上就是**静默无效登记**——不报错、也永远不会回调。
>
> **⚠ 但由此推出「引擎事件一律走 `Events.*`、`GameEvents.*` 只装你自己写的 Lua 事件」是错的**（旧版本此处如此断言，2026-09 已更正）。
> `events_enhanced.json` 里 `eventSystem=GameEvents` 共 **130 条**，其中 **82 条 `availability=GamePlay`**，都是**不是你自定义的**事件，且**在 `Events.*` 上根本没有对应条目**：
> `OnDistrictConstructed` / `CityConquered` / `PolicyChanged` / `OnUnitMoved` / `OnCombatOccurred` / `UnitCreated` / `PlotPropertyChanged` / `OnWMDCountChanged` …（该库自带的 `exampleCode` 就写 `GameEvents.X.Add(...)`）。
> 实测反证：一个已发布 mod 全工程 127 个事件注册点与 `eventSystem` 比对 **63/63 命中、0 处不一致**，其中 `GameEvents.PolicyChanged` / `GameEvents.CityConquered` / `GameEvents.OnDistrictConstructed` 都在正常工作；另一工程 18 个事件同样零例外。
>
> **正确的心智模型**：三条总线是**三张按事件划分的表**，不是按「引擎 vs Lua」划分的。
> **选总线永远查 `eventSystem` / `query_events.py` 的 `System` 列**，不要按来源猜。
> **⚠ `GameEvents.X` 对任意名字都返回 table（自动建表）**：`type(GameEvents.X)` 说明不了任何事，别拿它当探针；只有 `type(Events.X)` 有效。

### Full GameEvents Reference (82 hooks)

> **注**：本表列的是**实际被使用过**的 GamePlay 钩子（语料扫描所得）。`events_enhanced.json` 里 `eventSystem=GameEvents` 的记录数要多于此（2026-09 起含 48 条引擎内部事件，标 `availability: "None"` + `luaSubscribable: false`，**任何一层都订阅不到**）——查库时以 `availability` 字段区分，别只看 eventSystem。

| Event | Parameters |
|-------|-----------|
| BuildingConstructed | playerID:number, cityID:number, buildingID:number, plotID:number, isOriginalConstruction:boolean |
| BuildingPillageStateChanged | playerID:number, cityID:number, buildingID:number, isPillaged:boolean |
| CanUseResolutions |  |
| CityBuilt | playerID:number, cityID:number, x:number, y:number |
| CityConquered | newPlayerID:number, oldPlayerID:number, newCityID:number, cityX:number, cityY:number |
| CivRoyale_GetSafeZone |  |
| CivRoyale_SmallSafeZone |  |
| DiploSurpriseDeclareWar | mainPlayer, opponentPlayer |
| EventPopupChoice | playerID:number, parameters:table |
| FoundNewWorld | playerID:number, threshold:number |
| HasFourCities | playerID:number, threshold |
| OnCityPopulationChanged | cityOwner:number, cityID:number, amountChanged:number |
| OnCivicCulturevated | playerID:number, civicIndex:number |
| OnCombatOccurred |  |
| OnDistrictConstructed | playerID:number, districtID:number, x:number, y:number |
| OnFaithEarned | playerID:number, amountEarned:number |
| OnGameTurnStarted | playerID:number |
| OnGreatPersonActivated |  |
| OnImprovementPillaged |  |
| OnNewMajorityReligion |  |
| OnNuclearWeaponDetonated |  |
| OnPillage | playerID:number, unitID:number, isPillaged:boolean, buildingIndex:number |
| OnPlayerCommandSetObjectState | playerID:number, parameters:table |
| OnPlayerGaveInfluenceToken | majorID:number, minorID:number, amount:number |
| OnPlayerTurnEnded |  |
| OnRandomEventOccurred | iType:number, severity:number, x:number, y:number, mitigationLevel:number |
| OnUnitMoved |  |
| OnUnitRetreated | unitOwner:number, unitID:number |
| OnWMDCountChanged |  |
| PiratesScenario_DeleteUnitsAtGoal |  |
| PlayerTurnStartComplete | playerID:number |
| PlayerTurnStarted | playerID:number |
| PlotOwnershipChanged |  |
| PlotPropertyChanged | x:number, y:number |
| PolicyChanged | playerID:number, policyID:number, wasEnacted:boolean |
| PostUnitPromotionEarned |  |
| TradeRoutePlundered |  |
| UnitCreated | playerID:number, unitID:number |
| UnitInitialized |  |
| UnitTriggerGoodyHut |  |
| WC_Validate_ArmsControlTreaty |  |
| WC_Validate_BorderControl |  |
| WC_Validate_DeforestationFeature |  |
| WC_Validate_DiploVictory |  |
| WC_Validate_ESPIONAGE_PACT |  |
| WC_Validate_GreatWorkObjects |  |
| WC_Validate_LuxuryBan |  |
| WC_Validate_MigrationTreaty |  |
| WC_Validate_MILITARY_ADVISORY |  |
| WC_Validate_Patronage |  |
| WC_Validate_PolicyTreaty |  |
| WC_Validate_PowerBuilding |  |
| WC_Validate_PowerResourceBan |  |
| WC_Validate_PublicWorks |  |
| WC_Validate_TradeTreaty |  |
| WC_Validate_UrbanDevelopment |  |
| WC_Validate_WorldIdeology |  |
| WC_Validate_YieldBan |  |
| WC_ValidateGovernanceDoctrine |  |

Plus 24 `ScenarioCommand_*` events for Pirates scenario (`python database/scripts/query_events.py --search ScenarioCommand`).

#### Custom GameEvents

Define custom hooks for GP 同端跨文件共享（禁止跨端暴露给 UI）：

**Gameplay file A:**
```lua
ExposedMembers.GameEvents = GameEvents;

function ReadData(params)
    params.result = Game:GetProperty("MY_KEY");
end
GameEvents.ReadMyData.Add(ReadData);
```

**Gameplay file B（同一 GP 状态，同端跨文件）:**
```lua
GameEvents = ExposedMembers.GameEvents;
local params = {};
GameEvents.ReadMyData.Call(params);
local data = params.result;
```

**UI 侧禁止**通过 `ExposedMembers` 获取 `GameEvents` 跨端调用。UI→GP 动作只能走 `PlayerOperations` + `EXECUTE_SCRIPT`；UI 读取 GP 数据用 PROPERTY 或 Core 共享读取函数。

---

## Quick Decision Table

| You are in... | Use... | Notes |
|--------------|--------|-------|
| UI Lua context | `Events.*` | Must `.Remove()` in `OnShutdown()` |
| UI Lua context | `LuaEvents.*` | Auto-cleanup. Only pass simple types. |
| GamePlay Lua script | `Events.*` **或** `GameEvents.*` | 二选一，**按事件定**（见下） |
| Raising an event cross-context | `LuaEvents.*` | Name after the raising context. |
| Reacting to game state change | **查 `eventSystem` 后决定** | ⚠ 不可一律用 `Events.*`，见 Gotcha 8 |

> **选总线三步法（禁止凭印象）**
> 1. `python database/scripts/query_events.py --show <事件名>` 看 `System` 列（或查 `reference/events_enhanced.json` 的 `eventSystem`）；
> 2. `System=Events` → `Events.X.Add()`；`System=GameEvents` → `GameEvents.X.Add()`；`System=LuaEvents` → `LuaEvents.X.Add()`；
> 3. `availability=None`（48 条）→ **不要注册**，UI 侧会抛 nil 崩溃。

## Gotchas

1. **Events.* must be removed** — Forgetting `Events.X.Remove(handler)` in `OnShutdown()` causes stale callbacks across context reloads (hot reload).

2. **GameEvents.* not available in UI** — Don't use `GameEvents.*` in UI Lua contexts. It won't exist.

3. **LuaEvents.* not available in GamePlay** — GP scripts can't use `LuaEvents.*`. Use `GameEvents.*` or `Events.*` instead.

4. **Don't pass C++ objects through LuaEvents*** — Only pass strings, numbers, booleans, and pure Lua tables. C++ objects (Units, Cities, Controls) may be deleted after the event is raised but before the receiver processes it.

5. **Events.* uses colon notation** — Sometimes engine events have both a dot method and a colon method. Be consistent: `.Add()` and `.Remove()` for subscriptions.

6. **LuaEvents are broadcast to ALL contexts** — Every loaded UI context receives every `LuaEvents.*` message. Use unique names to avoid conflicts between mods.

7. **Context load order matters** — When a context loads, it subscribes to events. Already-fired events won't be replayed. Use `LoadScreenClose` or manual re-initialization for late-loading contexts.

8. **不要凭印象选总线 —— 查 `eventSystem` 列**（2026-09 修订；旧结论有误）。
   同一个逻辑事件**通常只在 `Events.*` / `GameEvents.*` 其中一张上有效**，用错即**静默无效**（不报错、不回调）。
   权威判据是 `reference/events_enhanced.json` 的 **`eventSystem`** 字段（1081 条全覆盖）：`LuaEvents` 481 / `Events` 470 / `GameEvents` 130；
   等价命令：`python database/scripts/query_events.py --show <事件名>` 看 `System` 列。

   - 走 `Events.*` 的事件例：`UnitMoveComplete` / `CitySelectionChanged` / `UnitAddedToMap` / `PlayerTurnActivated`
   - **只在** `GameEvents.*` 上存在、`Events.*` 无对应条目的非自定义事件例：`OnDistrictConstructed` / `CityConquered` / `PolicyChanged` / `PlayerTurnStarted` / `OnUnitMoved` / `OnCombatOccurred`

   > ⚠ **旧版本本条写「`GameEvents.*` 只承载 Lua 级事件，不承载任何引擎 GameCoreEvent」——该结论是错的**。
   > 本条自身引用的实测数据（`PlayerTurnStarted`：GameEvents 端 17 次、Events 端 0 次）恰好证明它本就走 `GameEvents.*`。
   > 实测反证：一个已发布 mod 全工程 127 个事件注册点与 `eventSystem` 比对 **63/63 命中、0 处不一致**，其中 `GameEvents.PolicyChanged` / `GameEvents.CityConquered` / `GameEvents.OnDistrictConstructed` 都在正常工作；另一工程 18 个事件同样零例外。
   > 正确表述是「**三条总线是按事件划分的三张表**」，而不是「引擎事件一律走 `Events.*`」。

   `availability=None` 的 48 条**哪一层都订阅不到**，UI 侧 `.Add()` 还会直接抛 nil 崩溃（这 48 条的 `eventSystem` 同为 `GameEvents`，即「按名字该走 GameEvents，但实际不可用」）。
   ⚠ `GameEvents.X` 对**任意**名字都自动建 table，不能用作存在性探针——只有 `type(Events.X) == "table"` 是权威探针。

## P3 校准补充事件（2026-08，官方 Lua 验证）

> 以下事件在官方 Lua 文件中实际注册/调用，但此前事件库未收录。均已写入 `events_enhanced.json`（`query_events.py` 可查）。来源：官方 Lua 调用点扫描 + reasoner 判定。

### `Events.*`（21 个，官方调用验证）

| Event | Availability | 参数（官方调用推断） |
|-------|-------------|---------------------|
| Begin2KLoginProcess | UI | — |
| BeginFullGamePurchase | UI | — |
| DisableColorKey | UI | fadeTime:number |
| EnableColorKey | UI | colorkey:string, duration:number, fadeTime:number |
| ExitToMainMenu | Both | — |
| HideLeaderScreen | UI | — |
| LoadScreenClose | Both | — |
| PlayCameraAnimationAtHex | Both | animation:string, x:number, y:number, z:number, looping:boolean |
| PlayCameraAnimationAtPos | Both | animation:string, x:number, y:number, z:number, looping:boolean |
| RestartWonderMovie | UI | — |
| SetGameEntryMethod | UI | method:string |
| ShowLeaderScreen | UI | leaderName:string, isLocal:boolean |
| StopAllCameraAnimations | Both | — |
| SystemUpdateUI | UI | mode:SystemUpdateUI, context:string |
| UnitPlayCinematicAnimation | Both | animation:string, owner:number, unit:number, x:number, y:number |
| UnitStopCinematicAnimation | Both | animation:string, owner:number, unit:number, x:number, y:number |
| UserAcceptsEULA | UI | — |
| UserAcceptsOutdatedDriver | UI | — |
| UserAcceptsUnknownDevice | UI | — |
| UserConfirmedClose | UI | — |
| WorldBuilderSignal | UI | signal:WorldBuilderSignals（仅 WorldBuilder） |

### `Events.*` / `GameEvents.*`（5 个，官方注册验证）

| Event | System | Availability | 参数 |
|-------|--------|-------------|------|
| LeaderPopup | Events | UI | playerID:number, leaderType:string, isTutorial:boolean |
| MultiplayerConnectionFailed | Events | UI | — |
| MultiplayerNetRegistered | Events | UI | — |
| PlayerVersionMismatchEvent | Events | UI | — |
| AdvisorNegativeResourceRate | GameEvents | GamePlay | playerID:number |

### `LuaEvents.*` 官方自定义（不收入 API 库）

官方 UI 脚本大量使用 `LuaEvents.*` 做脚本间广播（如 `LuaEvents.ActionPanel_OpenChooseResearch()`）。这些是官方自定义事件，非引擎 API，**无需在 api.sqlite 注册**。若 mod 需要与官方 UI 联动，可在官方 Lua 中搜索同名事件的 `.Add(` 注册点确认参数。

#### LuaEvents DLC 来源标注（2026-08 校准）

`events_enhanced.json` 中 **481 个 LuaEvents** 已补充 `dlcSources`（所属 DLC）与 `panels`（调用面板文件）字段：

- **收录范围**：Base + 资料片（Expansion1/Expansion2）+ 领袖/文明包（Babylon、Ethiopia、Indonesia_Khmer、KublaiKhan_Vietnam 等）
- **不收录**：仅出现在纯情景（`*Scenario`）或纯模式（`BarbarianClansMode`、`TreeRandomizer`）DLC 的事件（如 `ActionPanel_EndObserverMode`、`OnViewPlagueLens` 等 8 个）；`Platforms\` 目录（Stadia 等平台专属）事件
- **查询方式**：`query_events.py --search 事件名` 可查 `dlcSources`/`panels`/`registerVerified`（是否官方注册验证）

```python
# 例：查某个 LuaEvents 的来源
python database/scripts/query_events.py --show LuaEvents.Babylon_xxx
# 结果含 dlcSources: "Babylon"、panels: "GreatPeoplePopup_Babylon_Heroes"
```

**判断事件是否可用**：事件出现在 Base/资料片/领袖 DLC 即表示对应环境下可用；仅情景独有的事件在常规对局中不触发。

