# Civ6 Lua API 速查表

> **规则: 写 Lua 代码前先检查此表。不在表中的 API → `SELECT * FROM api_functions WHERE func_name LIKE '%Key%' OR sub_func_name LIKE '%Key%'` (api.sqlite)（搜不到？试试复数形式，如 GetAbility → GetAbilities）**
> 覆盖日常模组开发 90% 场景。~150 个函数，~6KB。

## Unit

| 方法 | 签名 |
|------|------|
| `GetCombat` | `() -> combat: number` |
| `GetRangedCombat` | `() -> rangedCombatStrength: number` |
| `GetBombardCombat` | `() -> amount: number` |
| `GetMaxDamage` | `() -> maxDamage: number` |
| `GetDamage` | `() -> damage: number` |
| `SetDamage` | `(damage: number)` |
| `GetX` | `() -> x: number` |
| `GetY` | `() -> y: number` |
| `GetUnitType` | `() -> unitType: number` |
| `GetType` | `() -> typeName: string` |
| `GetOwner` | `() -> playerID: number` |
| `GetMovesRemaining` | `() -> movesRemaining: number` |
| `GetMaxMoves` | `() -> maxMoves: number` |
| `SetMovesRemaining` | `(moves: number)` |
| `SetBaseMoves` | `(moves: number)` |
| `SetBaseSightRange` | `(sight: number)` |
| `IsFortified` | `() -> bool` |
| `GetBuildCharges` | `() -> charges: number` |
| `ChangeBuildCharges` | `(delta: number)` |
| `HasAbility` | `(abilityIndex: number) -> bool` |
| `AttachAbilityToUnit` | `(abilityIndex: number)` |
| `RemoveAbilityFromUnit` | `(abilityIndex: number)` |
| `GetProperty` | `(key: string) -> value` |
| `SetProperty` | `(key: string, value)` |

## Plot

| 方法 | 签名 |
|------|------|
| `GetX` | `() -> x: number` |
| `GetY` | `() -> y: number` |
| `GetTerrainType` | `() -> terrainType: number` |
| `GetFeatureType` | `() -> featureType: number` |
| `GetResourceType` | `() -> resourceType: number` |
| `GetDistrictType` | `() -> districtType: number` |
| `GetImprovementType` | `() -> improvementType: number` |
| `GetOwner` | `() -> playerID: number` |
| `SetOwner` | `(playerID: number)` |
| `GetUnitCount` | `() -> count: number` |
| `GetContinentType` | `() -> continentType: number` |
| `IsWater` | `() -> bool` |
| `IsCity` | `() -> bool` |
| `IsRevealed` | `(playerID: number) -> bool` |
| `GetProperty` | `(key: string) -> value` |
| `SetProperty` | `(key: string, value)` |
| `GetNearestLandPlot` | `() -> Plot` |

## City

| 方法 | 签名 |
|------|------|
| `GetX` | `() -> x: number` |
| `GetY` | `() -> y: number` |
| `GetOwner` | `() -> playerID: number` |
| `GetBuildQueue` | `() -> BuildQueue` |
| `GetBuildings` | `() -> Buildings` |
| `GetGrowth` | `() -> CityGrowth` |
| `GetCulture` | `() -> CityCulture` |
| `GetYield` | `(yieldIndex: number) -> amount`（仅 City / Plot；Player 无此方法）|
| `AttachModifierByID` | `(modifierId: string)` |
| `RemoveAttachedModifierByID` | `(modifierId: string)` |
| `GetProperty` | `(key: string) -> value` |
| `SetProperty` | `(key: string, value)` |

## Player

| 方法 | 签名 |
|------|------|
| `GetCities` | `() -> Cities` |
| `GetUnits` | `() -> Units` |
| `GetTreasury` | `() -> Treasury` |
| `GetCulture` | `() -> Culture` |
| `GetTechs` | `() -> Techs` |
| `GetReligion` | `() -> PlayerReligion`（别名 GetFaithYield；信仰存量用 `:GetFaithBalance()`） |
| `GetDiplomacy` | `() -> Diplomacy` |
| `GetEras` | `() -> Eras` |
| `IsBarbarian` | `() -> bool` |
| `IsHuman` | `() -> bool` |
| `GetProperty` | `(key: string) -> value` |
| `SetProperty` | `(key: string, value)` |

> **Player 的四种基础产出对象**（别名已通过 api.sqlite 验证）：`GetTreasury`(GetGoldYield 金币)、`GetCulture`(GetCultureYield 文化)、`GetReligion`(GetFaithYield 信仰)、`GetTechs`(GetScienceYield 科技)。已核实的存量读取：信仰存量 `GetReligion():GetFaithBalance()`（`GetFaithBalance` 为 PlayerReligion 子方法，UI/GP 均可用）。**Player 本身没有 `GetYield` / `GetYieldBalance`**（`GetYield` 只存在于 City / Plot），写错会直接 `function expected instead of nil`。

## Map

| 方法 | 签名 |
|------|------|
| `GetPlot` | `(x, y) -> Plot` |
| `GetPlotByIndex` | `(index: number) -> Plot` |
| `GetPlotCount` | `() -> count: number` |
| `GetAdjacentPlots` | `(x, y) -> Plot[]` |
| `GetNeighborPlots` | `(x, y, range: number) -> Plot[]` |

## UnitManager

| 方法 | 签名 |
|------|------|
| `GetUnit` | `(playerID, unitID) -> Unit` |
| `Kill` | `(unit: Unit, ...)` |
| `PlaceUnit` | `(unit: Unit, x, y)` |
| `RequestCommand` | `(unit: Unit, commandHash: number, ...)` |
| `RequestMission` | `(playerID, unitID, missionType, x, y, ...)` |
| `InitUnitValidAdjacentHex` | `(playerID, unitType, x, y, ...)` |

## CityManager

| 方法 | 签名 |
|------|------|
| `GetCity` | `(playerID, cityID) -> City` |
| `DestroyCity` | `(city: City)` |
| `DestroyDistrict` | `(playerID, cityID, districtType)` |

## PlayerManager

| 方法 | 签名 |
|------|------|
| `GetAliveMajorIDs` | `() -> playerID[]` |

## Game

| 方法 | 签名 |
|------|------|
| `GetLocalPlayer` | `() -> playerID: number` |
| `GetCurrentGameTurn` | `() -> turn: number` |
| `GetRandNum` | `(max: number, name?: string) -> int` |
| `GetProperty` | `(key: string) -> value` |
| `SetProperty` | `(key: string, value)` |

## GameInfo 查表

| 方法 | 说明 |
|------|------|
| `GameInfo.Types["TYPE_NAME"]` | 返回类型行 |
| `GameInfo.Units["UNIT_XXX"]` | 返回单位行（.Index .Cost .Combat .UnitType） |
| `GameInfo.Buildings["BUILDING_XXX"]` | 返回建筑行（.Index .IsWonder） |
| `GameInfo.Districts["DISTRICT_XXX"]` | 返回区域行 |
| `GameInfo.Improvements["IMPROVEMENT_XXX"]` | 返回改良设施行 |
| `GameInfo.Resources["RESOURCE_XXX"]` | 返回资源行（.SeaFrequency） |
| `GameInfo.Terrains["TERRAIN_XXX"]` | 返回地形行 |
| `GameInfo.Features["FEATURE_XXX"]` | 返回地貌行（.NaturalWonder） |
| `GameInfo.Yields["YIELD_XXX"]` | 返回产出行 |
| `GameInfo.Technologies["TECH_XXX"]` | 返回科技行 |
| `GameInfo.UnitAbilities["ABILITY_XXX"]` | 返回能力行 |
| `GameInfo.Projects["PROJECT_XXX"]` | 返回项目行 |
| `GameInfo.GreatPersonClasses["GREAT_PERSON_CLASS_XXX"]` | 返回伟人类型行 |
| `for row in GameInfo.Resources()` | 遍历表（GameInfo 所有子表都可用） |

## DB.Query — Direct SQL

| 方法 | 说明 |
|------|------|
| `DB.Query("SELECT Type, Kind FROM Types WHERE Kind = 'KIND_UNIT'")` | 直接 SQL（大表筛选 / 聚合 / JOIN，仅返回结果集） |

## Treasury / Techs / Culture / Faith / Diplomacy

| 方法 | 签名 |
|------|------|
| `Treasury:ChangeGold` | `(amount: number)` |
| `Treasury:ChangeYield` | `(yieldIndex: number, amount)` |
| `Techs:SetTech` | `(techIndex: number, enabled: bool)` |
| `Techs:ChangeCurrentResearchProgress` | `(amount: number)` |
| `Culture:ChangeProgress` | `(amount: number)` |
| `Culture:ChangePoints` | `(amount, greatPersonClassIndex)` |
| `Culture:IsPolicyActive` | `(policyIndex: number) -> bool` |
| `Faith:AddFaith` | `(amount: number)` |
| `Diplomacy:IsAtWarWith` | `(otherPlayerID: number) -> bool` |

## BuildQueue / CityGrowth / CityCulture

| 方法 | 签名 |
|------|------|
| `BuildQueue:GetCurrentProductionTypeHash` | `() -> hash: number` |
| `BuildQueue:GetCurrentProductionProgress` | `() -> progress: number` |
| `BuildQueue:GetCurrentProductionCost` | `() -> cost: number` |
| `BuildQueue:AddProgress` | `(amount: number)` |
| `CityGrowth:GetAmenities` | `() -> amenities: number` |
| `CityGrowth:GetAmenitiesNeeded` | `() -> needed: number` |
| `CityCulture:ChangeGreatPersonProgress` | `(classIndex, amount)` |

## UI

| 方法 | 签名 |
|------|------|
| `UI.SelectUnit` | `(unit: Unit)` |
| `UI.SetInterfaceMode` | `(mode: number)` |
| `UI.RequestPlayerOperation` | `(playerID, operationType, params)` |
| `UI.PauseModCivMusic` | `()` |
| `UI.ResumeModCivMusic` | `()` |
| `UI.PlaySound` | `(soundName: string)` |

## DB / Locale / Misc

| 方法 | 签名 |
|------|------|
| `DB.MakeHash` | `(string) -> hash: number` |
| `Locale.Lookup` | `(key: string) -> localizedText` |
| `ExposedMembers.XXX` | GP 同端跨文件暴露成员；禁止跨端暴露给 UI |
| `include("file")` | 加载文件到当前作用域 |
| `include("file", true)` | 可选加载（文件不存在不报错） |

## Events (常用)

| Event | 参数 | 时机 |
|-------|------|------|
| `UnitActivate` | `owner, unitID, x, y, eReason, bVisibleToLocalPlayer` | 单位激活 |
| `UnitMoveComplete` | `playerID, unitID` | 单位移动完成 |
| `UnitAddedToMap` | `playerID, unitID` | 单位创建 |
| `CityMadePurchase` | `owner, cityID, plotX, plotY, purchaseType, objectType` | 单位/建筑购买 |
| `UnitCommandStarted` | `playerID, unitID, commandType, data1` | 单位命令 |
| `CityProductionCompleted` | `playerID, cityID, type, ...` | 城市生产完成 |
| `CityAddedToMap` | `playerID, cityID, x, y` | 城市创建 |
| `DistrictAddedToMap` | `playerID, districtID, cityID, x, y, type, percent` | 区域完成 |
| `ImprovementAddedToMap` | `x, y, improvementIndex, playerID` | 改良建成 |
| `PlayerTurnActivated` | `playerID, bIsFirstTime` | 回合开始 |
| `LoadGameViewStateDone` | `()` | 初始化入口 |
| `ReligionFounded` | `playerID, religionID` | 创立宗教 |
| `PlayerEraChanged` | `playerID, eraIndex` | 进入新时代 |
| `CapitalCityChanged` | `playerID, cityID` | 首都变更 |
| `WorldTextMessage` | `messageType, playerID, args` | 世界消息 |

## GameEvents (需在 GamePlay Script 中使用)

| Event | 参数 | 时机 |
|-------|------|------|
| `GameEvents.PolicyChanged` | `playerID, policyID, bEnacted` | 政策变更 |
| `GameEvents.MyMod_SetSomething` | `playerID, key, value` | 自定义事件（mod 自定义 hook） |
| `GameEvents.MyMod_BatchUpdate` | `playerID, params` | 自定义事件（mod 自定义 hook） |
