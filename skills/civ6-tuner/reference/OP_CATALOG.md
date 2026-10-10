# OP_CATALOG.md —— FireTuner 操作类 API 目录（操作库总源）

> 生成于 2026-10-02。数据来源：
> ① `civ6-modding/database/api.sqlite` 的 `runtime_gp` / `runtime_ui` 实测标注（2026-09-08 测）；`GP` = gamecore 侧，`UI` = ingame/UI 侧；`function`=存在，`nil`=不存在，`ERR`=未测或报错。
> ② 官方源码（相对游戏安装根）：`Base/Assets` 与 `DLC/Expansion1..3/Assets` 的 .lua，标注为 `文件:行号`。
> ③ 2026-10-02 实机验证：SetGoldBalance / SetFaithBalance / SetResearchProgress / InitUnit / RequestCommand(DELETE) / AutoplayManager 全套 / Network.SaveGame / Network.LoadGame / Network.RestartGame / Events.ExitToMainMenu / MainMenu 无头建局八步 / Modding.EnableMod 全部通过（详见 SKILL.md 边界节）。
> `Players[pid]` 索引与 `Game.GetLocalPlayer()` 双端可用（GP+UI=function）。

## 1. 玩家经济与资源

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `Players[pid]:GetTreasury():SetGoldBalance(n)` | gamecore | GP=function + 已知可用 | 直接设定金币余额 |
| `GetTreasury():ChangeGoldBalance(n)` | gamecore | GP=function | 增减金币 |
| `GetTreasury():ChangeGoldBalanceByPercentage(n)` | gamecore | GP=function | 按百分比增减金币 |
| `GetTreasury():GetGoldBalance()` | gamecore/ingame | GP+UI=function | 读金币 |
| `Players[pid]:GrantYield(yieldIndex, amount)` | gamecore | GP=function | 任意产出直接注入（金/科研/文化/信仰等，按 YieldTypes 序号） |
| `Players[pid]:GetReligion():SetFaithBalance(n)` | gamecore | GP=function | 设定信仰值 |
| `GetReligion():ChangeFaithBalance(n)` | gamecore | GP=function | 增减信仰 |
| `GetReligion():GetFaithBalance()` | gamecore/ingame | GP+UI=function | 读信仰 |
| `Players[pid]:GetGreatPeoplePoints():ChangePointsTotal(classIndex, n)` | gamecore | GP=function | 按伟人类别增减伟人点 |
| `GetGreatPeoplePoints():SetPointsTotal(...)` | gamecore | GP=function | 直接设定伟人点 |
| `GetGreatPeoplePoints():GetPointsTotal(classIndex)` | gamecore/ingame | GP+UI=function | 读伟人点 |
| `Players[pid]:GetInfluence():ChangeTokensToGive(...)` | gamecore | GP=function | 改使者（影响力）持有数 |
| `GetInfluence():GiveFreeTokenToPlayer(...)` | gamecore | GP=function | 白送一个使者 |
| `GetInfluence():GetTokensToGive()` | gamecore/ingame | GP+UI=function | 读使者数 |
| `Players[pid]:GetDiplomacy():ChangeFavor(n)` | gamecore | GP=function | 增减外交支持点（Favor） |
| `GetDiplomacy():GetFavor()` / `GetFavorPerTurn()` | gamecore | GP=function | 读外交支持点及每回合 |
| `Players[pid]:GetResources():ChangeResourceAmount(resIndex, n)` | gamecore | GP=function | 增减战略资源库存 |
| `GetResources():GetResourceAmount(...)` | gamecore/ingame | GP+UI=function | 读资源库存 |
| `Players[pid]:GetWMDs():ChangeWeaponCount(n)` | gamecore | GP=function | 增减核弹（WMD）数量 |
| `Players[pid]:GetStats():ChangeScienceVictoryPoints` | gamecore | GP=function | 写科技胜利点数 |
| `GetStats():GetTourism()` | ingame | UI=function | 读旅游业绩（引擎无直接写接口） |
| `GetStats():GetDiplomaticVictoryPoints()` | ingame | UI=function | 读外交胜利点 |
| `Game.GetEras():ChangePlayerEraScore(pid, n)` | gamecore | GP=function | 增减时代分（黄金/黑暗判定） |
| `Players[pid]:GetScore()` | gamecore/ingame | GP+UI=function | 读总分（无 SetScore 写接口） |

## 2. 科技与市政

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `Players[pid]:GetTechs():SetResearchProgress(idx, 1000000)` | gamecore | GP=function + 已知可用 | 立即完成指定科技（2026-10-02 实机验证） |
| `GetTechs():SetTech(...)` | gamecore | GP=function | 直接标记科技已研发 |
| `GetTechs():TriggerBoost(...)` | gamecore | GP=function | 手动触发尤里卡（官方用法见 AustraliaScenario.lua:784） |
| `GetTechs():ReverseBoost(...)` | gamecore | GP=function | 撤销尤里卡 |
| `GetTechs():SetResearchingTech(...)` | gamecore | GP=function | 设定当前研发目标 |
| `GetTechs():ChangeCurrentResearchProgress(...)` | gamecore | GP=function | 增减当前科研进度 |
| `GetTechs():CanTriggerBoost` / `HasBoostBeenTriggered` | gamecore/ingame | GP+UI=function | 尤里卡状态查询 |
| `GetTechs():HasTech` / `GetResearchProgress` / `GetResearchCost` | gamecore/ingame | GP+UI=function | 科技状态查询 |
| `Players[pid]:GetCulture():SetCivic(...)` | gamecore | GP=function | 直接标记市政完成（同构 SetTech） |
| `GetCulture():SetProgressingCivic(...)` | gamecore | GP=function | 设定当前推进的市政 |
| `GetCulture():SetCulturalProgress(...)` | gamecore | GP=function | 写文化进度值 |
| `GetCulture():TriggerBoost(...)` | gamecore | GP=function | 触发市政鼓舞 |
| `GetCulture():UnlockPolicy` / `UnlockGovernment` | gamecore | GP=function | 解锁政策卡/政体 |
| `GetCulture():RequestChangeGovernment(govHash)` | ingame | 源码 Base\Assets\UI\Screens\GovernmentScreen.lua:912 | 发起换政体 |
| `GetCulture():RequestPolicyChanges(clearList, addList)` | ingame | 源码 GovernmentScreen.lua:1570 | 批量卸下/装上政策卡 |
| `GetCulture():SetCurrentGovernment(...)` | gamecore | GP=function | 直接改当前政体 |
| `GetCulture():RequestEnactPolicy` / `RequestClearSlot` | gamecore | 库标注 ACTION | 单卡装卸的引擎入口 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.RESEARCH, {[PlayerOperations.PARAM_TECH_TYPE]=hash, [PlayerOperations.PARAM_INSERT_MODE]=PlayerOperations.VALUE_EXCLUSIVE})` | ingame | 源码 Base\Assets\UI\Choosers\ResearchChooser.lua:255-261 | 选科技入研队列 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.PROGRESS_CIVIC, {[PlayerOperations.PARAM_CIVIC_TYPE]=hash, ...})` | ingame | 源码 Base\Assets\UI\Choosers\CivicsChooser.lua:245-250 | 选市政入研队列 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.UNLOCK_POLICIES, {})` | ingame | 源码 GovernmentScreen.lua:1592 | 付金解锁换卡/换政体能力 |

## 3. 单位操作

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `UnitManager.InitUnit(pid, "UNIT_BUILDER", x, y)` | gamecore | GP=function + 已知可用 | 刷兵（2026-10-02 实机验证） |
| `UnitManager.InitUnitValidAdjacentHex(pid, type, x, y, n)` | gamecore | GP=function | 在相邻可放格刷兵 |
| `UnitManager.Kill(unit)` | gamecore | GP=function | gamecore 侧删兵 |
| `UnitManager.MoveUnit(unit, x, y)` | gamecore | GP=function | 瞬移（免移动消耗） |
| `UnitManager.PlaceUnit(unit, x, y)` | gamecore | GP=function | 放置到指定格 |
| `UnitManager.RestoreMovement(unit)` | gamecore | GP=function | 恢复移动力 |
| `UnitManager.RestoreMovementToFormation(unit)` | gamecore | GP=function | 恢复整编队移动力 |
| `UnitManager.RestoreUnitAttacks(unit)` | gamecore | GP=function | 恢复攻击次数 |
| `UnitManager.FinishMoves(unit)` | gamecore | GP=function | 清空移动力 |
| `UnitManager.ChangeMovesRemaining(unit, n)` | gamecore | GP=function | 增减移动力 |
| `UnitManager.WakeUnit(unit)` | gamecore | GP=function | 唤醒休眠单位 |
| `UnitManager.CanFormMilitaryFormation(pid, domain, type, unit)` | gamecore | GP=function | 编队可行性查询 |
| `UnitManager.GetUnit(pid, unitID)` | gamecore/ingame | GP+UI=function | 取单位对象 |
| `Unit:SetDamage(n)` | gamecore | GP=function | 回血（设 0 即满血） |
| `Unit:ChangeDamage(n)` | gamecore | GP=function | 增减伤害 |
| `Unit:ChangeExtraMoves(n)` | gamecore | GP=function | 追加本回合额外移动力 |
| `Unit:SetActionCharges(n)` / `ChangeActionCharges(n)` | gamecore | GP=function | 建设者/传教等次数 |
| `Unit:SetFortifyTurns(n)` | gamecore | GP=function | 设 fortify 回合数 |
| `Unit:SetMilitaryFormation(MilitaryFormationTypes.X)` | gamecore | GP=function | 设军团/军队形态 |
| `Unit:GetExperience():ChangeExperience(n)` | gamecore | GP=function | 加经验（满经验用大数值） |
| `Unit:GetExperience():SetPromotion(promotionID, true)` | gamecore | GP=function | 直接授予晋升 |
| `Unit:GetExperience():ChangeStoredPromotions` | gamecore | GP=function | 改可用晋升次数 |
| `Unit:GetExperience():SetExperienceLocked` | gamecore | GP=function | 锁定经验获取 |
| `UnitManager.RequestCommand(unit, UnitCommandTypes.DELETE, {})` | ingame | UI=function + 源码 Base\Assets\UI\Panels\UnitPanel.lua:2757 | 删兵（2026-10-02 实机验证，目标用 `Players[pid]:GetUnits():FindID(unitID)` 定位） |
| `RequestCommand(unit, UnitCommandTypes.PROMOTE, {[UnitCommandTypes.PARAM_PROMOTION_TYPE]=hash})` | ingame | 源码 UnitPanel.lua:2714、Base\Assets\UI\Popups\UnitPromotionPopup.lua:72 | 晋级 |
| `RequestCommand(unit, UnitCommandTypes.UPGRADE)` | ingame | 源码 UnitPanel.lua:475 | 升级单位 |
| `RequestCommand(unit, UnitCommandTypes.RESTORE_UNIT_MOVES, {[PARAM_X]=x, [PARAM_Y]=y})` | ingame | 源码 Base\Assets\UI\WorldInput.lua:3272 | 恢复移动力命令 |
| `RequestCommand(unit, UnitCommandTypes.TRANSFORM_UNIT, {[PARAM_X]=x, [PARAM_Y]=y})` | ingame | 源码 WorldInput.lua:3213 | 变换形态 |
| `RequestCommand(unit, UnitCommandTypes.KILL_WEAKER_UNIT, {[PARAM_X], [PARAM_Y]})` | ingame | 源码 WorldInput.lua:3153 | 清扫残兵 |
| `RequestCommand(unit, UnitCommandTypes.AIRLIFT, {[PARAM_X], [PARAM_Y]})` | ingame | 源码 WorldInput.lua:3046 | 空运 |
| `RequestCommand(unit, UnitCommandTypes.PARADROP, {[PARAM_X], [PARAM_Y]})` | ingame | 源码 WorldInput.lua | 空降 |
| `RequestCommand(unit, UnitCommandTypes.FORM_CORPS, tParameters)` | ingame | 源码 WorldInput.lua:2882 | 合编军团 |
| `RequestCommand(unit, UnitCommandTypes.FORM_ARMY, tParameters)` | ingame | 源码 WorldInput.lua:2952 | 合编军队 |
| `RequestCommand(unit, UnitCommandTypes.ENTER_FORMATION, tParameters)` | ingame | 源码 UnitPanel.lua:2604 | 编入编队 |
| `RequestCommand(unit, UnitCommandTypes.CANCEL)` | ingame | 源码 WorldInput.lua:831 | 取消当前动作/状态 |
| `RequestCommand(unit, UnitCommandTypes.WAKE)` | ingame | 源码 WorldInput.lua:955 | 唤醒 |
| `RequestCommand(unit, UnitCommandTypes.MOVE_JUMP, {[PARAM_X], [PARAM_Y]})` | ingame | 源码 WorldInput.lua:412 | 跳移到格 |
| `RequestCommand(unit, UnitCommandTypes.NAME_UNIT, tParameters)` | ingame | 源码 UnitPanel.lua:2813 | 命名单位 |
| `RequestCommand(unit, UnitCommandTypes.NAVAL_GOLD_RAID, {[PARAM_X], [PARAM_Y]})` | ingame | 源码 WorldInput.lua:3333 | 海岸劫掠（金） |
| `RequestCommand(unit, UnitCommandTypes.PLUNDER_TRADE_ROUTE)` | ingame | 源码 WorldInput.lua | 劫掠商路 |
| `RequestCommand(unit, UnitCommandTypes.CONDEMN_HERETIC)` | ingame | 源码 WorldInput.lua | 谴责异端 |
| `RequestCommand(unit, UnitCommandTypes.PRIORITY_TARGET, tParameters)` | ingame | 源码 WorldInput.lua | 设优先目标 |
| `RequestCommand(unit, UnitCommandTypes.EXECUTE_SCRIPT, tParameters)` | ingame | 源码 WorldInput.lua（15 处引用） | 执行单位脚本动作 |
| `UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, {[UnitOperationTypes.PARAM_X]=x, [PARAM_Y]=y})` | ingame | UI=function + 源码 Base\Assets\UI\UnitFlagManager.lua:297-298 | 寻路移动 |
| `UnitManager.CanStartCommand(unit, cmdType, params, true)` / `CanStartOperation(...)` | ingame | UI=function | 命令/操作预检 |
| `UnitOperationTypes.FOUND_CITY`（RequestOperation） | ingame | 源码 Base\Assets\Scenarios\Tutorial\TutorialScenarioBase.lua:4781 | 建城操作 |
| `UnitOperationTypes.BUILD_IMPROVEMENT {PARAM_IMPROVEMENT_TYPE}` / `BUILD_IMPROVEMENT_ADJACENT` | ingame | 源码 WorldInput.lua | 修改良 |
| `UnitOperationTypes.RANGE_ATTACK` / `AIR_ATTACK` / `REBASE` / `DEPLOY` / `COASTAL_RAID` / `FORTIFY` / `SWAP_UNITS` / `MAKE_TRADE_ROUTE` | ingame | 源码 WorldInput.lua | 战斗与移动类操作 |
| `UnitOperationTypes.WMD_STRIKE {PARAM_WMD_TYPE}` | ingame | 源码 WorldInput.lua | 核打击 |

## 4. 城市操作

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `city:GetBuildQueue():FinishProgress()` | gamecore | GP=function | 立即完成当前生产项 |
| `GetBuildQueue():AddProgress(n)` | gamecore | GP=function | 加生产力进度 |
| `GetBuildQueue():CreateBuilding(city, buildingIndex, progress, plotID)` | gamecore | GP=function | 直接造好建筑 |
| `GetBuildQueue():CreateDistrict(city, districtID, progress, plot)` | gamecore | GP=function | 直接造好区域 |
| `GetBuildQueue():CreateIncompleteBuilding` / `CreateIncompleteDistrict` | gamecore | GP=function | 放置未完成建筑/区域 |
| `GetBuildQueue():RemoveBuilding` / `RemoveDistrict` | gamecore | GP=function | 从队列移除 |
| `city:GetBuildings():RemoveBuilding(idx)` | gamecore | GP=function | 拆除已有建筑 |
| `GetBuildings():SetBuildingLocation(x, y)` | gamecore | GP=function | 挪建筑位置 |
| `GetBuildings():SetPillaged(idx, bool)` | gamecore | GP=function | 设建筑劫掠状态 |
| `city:ChangePopulation(n)` | gamecore | GP=function | 增减人口 |
| `city:ChangeLoyalty(n)` | gamecore | GP=function | 增减忠诚度 |
| `city:SetName(name)` | gamecore | GP=function | 改城名 |
| `city:GetCitizens():SetFavoredYield(YieldTypes.X, bool)` | gamecore | GP=function | 设市民产出偏好 |
| `city:GetReligion():SetAllCityToReligion(religionIndex)` | gamecore | GP=function | 全城改宗 |
| `GetReligion():AddOneFollower` / `AddReligiousPressure` / `RemoveOtherReligions` / `RemovePressureOneReligion` | gamecore | GP=function | 信徒与压力操作 |
| `CityManager.SetAsCapital(city)` | gamecore | GP=function | 设为首都 |
| `CityManager.SetAsOriginalCapital(city)` | gamecore | GP=function | 设历史原都 |
| `CityManager.TransferCity(city, pid, CityTransferTypes.X)` | gamecore | GP=function | 城市转让（征服/归还原主等） |
| `CityManager.TransferCityToFreeCities(city)` | gamecore | GP=function | 转为自由城 |
| `CityManager.DestroyCity(pid, districtID)` | gamecore | GP=function | 夷城（gamecore） |
| `Cities.DestroyCity(player, city)` | gamecore | GP=function | 夷城（全局表入口） |
| `CityManager.DestroyDistrict` | gamecore | GP=function | 拆区域 |
| `CityManager.GetCityAt(x, y)` / `GetCity(player, cityID)` | gamecore/ingame | GP+UI=function | 取城对象 |
| `CityManager.RequestOperation(city, CityOperationTypes.BUILD, {[PARAM_UNIT_TYPE]=hash, PARAM_INSERT_MODE})` | ingame | 源码 Base\Assets\UI\Panels\ProductionPanel.lua:298-301 | 入队生产单位（建筑/区域用 PARAM_BUILDING_TYPE / PARAM_DISTRICT_TYPE） |
| `CityManager.RequestCommand(city, CityCommandTypes.PURCHASE, {[PARAM_UNIT_TYPE]=hash, [PARAM_YIELD_TYPE]=yieldIdx, [PARAM_MILITARY_FORMATION_TYPE]=form})` | ingame | 源码 ProductionPanel.lua:425-434 | 金/信购买单位 |
| `RequestCommand(city, CityCommandTypes.PURCHASE, {[PARAM_BUILDING_TYPE]=hash, [PARAM_YIELD_TYPE]=...})` | ingame | 源码 ProductionPanel.lua:455-465 | 买建筑 |
| `RequestCommand(city, CityCommandTypes.PURCHASE, {[PARAM_PLOT_PURCHASE]=..., [PARAM_X]=x, [PARAM_Y]=y})` | ingame | 源码 Base\Assets\UI\WorldView\PlotInfo.lua:88-97 | 买地 |
| `CityManager.RequestCommand(city, CityCommandTypes.DESTROY, tParameters)` | ingame | 源码 Base\Assets\UI\Popups\RazeCity.lua:20-52 | 夷城（UI 途径） |
| `RequestCommand(city, CityCommandTypes.SET_FOCUS, {[PARAM_DATA0]=0或1})` | ingame | 源码 Base\Assets\UI\Panels\CityPanel.lua:450-458 | 市民侧重/忽略某产出 |
| `RequestCommand(city, CityCommandTypes.MANAGE, tParameters)` / `SWAP_TILE_OWNER {[PARAM_SWAP_TILE_OWNER]}` | ingame | 源码 PlotInfo.lua:65/78 | 市民管理/互换地块归属 |
| `RequestCommand(city, CityCommandTypes.RANGE_ATTACK, {[PARAM_X], [PARAM_Y]})` | ingame | 源码 WorldInput.lua:2556 | 城市远程攻击 |
| `RequestCommand(city, CityCommandTypes.WMD_STRIKE, tParameters)` | ingame | 源码 WorldInput.lua:2272 | 城市核打击 |
| `RequestCommand(city, CityCommandTypes.NAME_CITY, {[PARAM_NAME]=...})` | ingame | 源码 Base\Assets\UI\Panels\CityPanelOverview.lua:765 | 改城名 |
| `CityManager.CanStartCommand(city, cmdType, params)` / `CanStartOperation(city, opType, params)` | ingame | UI=function | 城市命令预检 |

## 5. 外交与战争

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `Players[pid]:GetDiplomacy():DeclareWarOn(...)` | gamecore | GP=function | gamecore 侧宣战 |
| `GetDiplomacy():MakePeaceWith(pid)` | gamecore | GP=function | 直接媾和 |
| `GetDiplomacy():NeverMakePeaceWith(...)` | gamecore | GP=function | 设永不媾和标记 |
| `GetDiplomacy():SetHasMet(pid)` | gamecore | GP=function | 直接相遇 |
| `GetDiplomacy():SetHasEmbassyAt` / `SetHasDelegationAt` | gamecore | GP=function | 设使馆/代表团 |
| `GetDiplomacy():SetHasDeclaredFriendship` / `SetHasAllied` / `SetPermanentAlliance` | gamecore | GP=function | 设友谊/同盟/永久同盟 |
| `GetDiplomacy():SendKudoTo` / `SendWarningTo` | gamecore | GP=function | 表扬/警告 |
| `GetDiplomacy():IsAtWarWith` / `CanDeclareWarOn` / `CanMakePeaceWith` | gamecore/ingame | GP+UI=function（部分单端） | 战和状态查询 |
| `Players[pid]:GetAi_Diplomacy():AdjustBaseDiplomacy(...)` | gamecore | GP=function、UI=ERR | 改 AI 基础关系值 |
| `GetAi_Diplomacy():GetDiplomaticScore` / `GetDiplomaticState` / `GetDiplomaticModifiers` | gamecore | GP=function、UI=ERR | AI 关系值与状态查询 |
| `GetAi_Diplomacy():SetTradeWithHuman(...)` | gamecore | GP=function | 开关 AI 与人交易意愿 |
| `Game.GetGameDiplomacy():SetAlliesShareVisFlag(bool)` | gamecore | GP=function | 盟友共享视野开关 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.DIPLOMACY_DECLARE_WAR, {[PARAM_PLAYER_ONE]=a, [PARAM_PLAYER_TWO]=b})` | ingame | 源码 Base\Assets\UI\Popups\DeclareWarPopup.lua:77-81 | UI 途径宣战 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.DIPLOMACY_MAKE_PEACE, {[PARAM_PLAYER_ONE], [PARAM_PLAYER_TWO]})` | ingame | 源码 Base\Assets\UI\PartialScreens\CityStates.lua:814-819 | UI 途径媾和 |
| `DiplomacyManager.RequestSession(from, to, "DECLARE_SURPRISE_WAR" / "DECLARE_TERRITORIAL_WAR" / "DECLARE_GOLDEN_WAR" / "DECLARE_WAR_OF_RETRIBUTION" / "DECLARE_IDEOLOGICAL_WAR")` | ingame | UI=function（api.sqlite）+ 源码 DLC\Expansion1\UI\Replacements\DiplomacyActionView_Expansion1.lua:132-138 | 按 Casus Belli 开战谈判会话 |
| `DiplomacyManager.RequestSession(from, to, "MAKE_DEAL")` | ingame | 源码 DiplomacyActionView_Expansion1.lua:155 | 打开交易会话 |
| `DealManager.GetWorkingDeal(dir, from, to)` / `SendWorkingDeal(DealProposalAction.X, from, to)` | gamecore/ingame | GP+UI=function + 源码 DLC\Expansion2\UI\Replacements\DiplomacyDealView.lua:151-581 | 组装并发送交易（ACCEPTED/PROPOSED/DEMANDED 等） |
| `DealManager.ClearWorkingDeal(dir, from, to)` | gamecore/ingame | GP+UI=function | 清空工作交易 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.GIVE_INFLUENCE_TOKEN, {[PARAM_PLAYER_ONE]=城邦id})` | ingame | 源码 CityStates.lua:757-760 | 给城邦使者 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.LEVY_MILITARY, parameters)` | ingame | 源码 CityStates.lua:838 | 征用城邦军队 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.ACCEPT_EMERGENCY, kParameters)` | ingame | 源码 DLC\Expansion1\UI\Additions\WorldCrisisPopup.lua:194 | 加入紧急情况 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.REJECT_EMERGENCY, kParameters)` | ingame | 源码 WorldCrisisPopup.lua | 拒绝紧急情况 |
| `Game.GetEmergencyManager():GetEmergencyInfoTable(pid)` | ingame | UI=function、GP=ERR | 读紧急情况表 |
| `Game.GetWorldCongress():GetResolutions/GetVotesandFavorCost/...` | ingame | UI=function、GP=ERR | 世界议会只读查询 |
| `Players[pid]:GetAgendasAndVisibilities()` / `GetAgendaTypes()` | ingame | UI=function | 议程读取（无运行时写接口） |

## 6. 宗教

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `Game.GetReligion():FoundPantheon(pid, beliefID)` | gamecore | GP=function | 直接创万神殿 |
| `Game.GetReligion():FoundReligion()` | gamecore | GP=function（参数待实测） | 直接创教 |
| `Game.GetReligion():AddBelief()` / `AddBeliefHash()` | gamecore | GP=function（参数待实测） | 添加信条 |
| `Game.GetReligion():AddBuilding(...)` | gamecore | GP=function | 挂宗教建筑 |
| `Players[pid]:GetReligion():SetFaithBalance(n)` / `ChangeFaithBalance(n)` | gamecore | GP=function | 信仰余额读写（见第 1 类） |
| `City:GetReligion():SetAllCityToReligion(idx)` | gamecore | GP=function | 城市改宗 |
| `City:GetReligion():RemoveOtherReligions()` | gamecore | GP=function | 清除异教压力 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.FOUND_PANTHEON, {[PARAM_BELIEF_TYPE]=hash, [PARAM_INSERT_MODE]=VALUE_EXCLUSIVE})` | ingame | 源码 Base\Assets\UI\Choosers\PantheonChooser.lua:128-133 | UI 途径创万神殿 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.FOUND_RELIGION, {[PARAM_RELIGION_TYPE]=hash, [PARAM_RELIGION_CUSTOM_NAME]=..., PARAM_INSERT_MODE})` | ingame | 源码 Base\Assets\UI\ReligionScreen.lua:900-913 | UI 途径创教 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.ADD_BELIEF, {[PARAM_BELIEF_TYPE]=hash, PARAM_INSERT_MODE})` | ingame | 源码 ReligionScreen.lua:914-919 | UI 途径加信条 |

## 7. 总督与伟人

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `UI.RequestPlayerOperation(pid, PlayerOperations.APPOINT_GOVERNOR, {[PlayerOperations.PARAM_GOVERNOR_TYPE]=id})` | ingame | 源码 DLC\Expansion2\UI\Additions\GovernorPanel.lua:548-553 | 任命总督 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.ASSIGN_GOVERNOR, {[PARAM_GOVERNOR_TYPE]=id, [PlayerOperations.PARAM_CITY_DEST]=cityID})` | ingame | 源码 GovernorPanel.lua:560-566 | 派驻城市 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.PROMOTE_GOVERNOR, {[PARAM_GOVERNOR_TYPE]=id, [PlayerOperations.PARAM_GOVERNOR_PROMOTION_TYPE]=id})` | ingame | 源码 GovernorPanel.lua:570-577 | 总督晋升 |
| `Players[pid]:GetGovernors():ChangeGovernorPoints` | gamecore | GP=function | 增减总督点 |
| `GetGovernors():GetGovernorList()` / `GetGovernor(hash)` | ingame | UI=function | 读总督列表/对象 |
| `Game.GetGreatPeople():RecruitPerson(pid, "GREAT_PERSON_xxx")` | gamecore | GP=function | 直接招募伟人 |
| `Game.GetGreatPeople():CreatePerson(pid, type, x, y)` | gamecore | GP=function | 在指定格生成伟人 |
| `Game.GetGreatPeople():GrantPerson(hash, classHash, eraHash, cost, pid, bool)` | gamecore | GP=function | 低层直接授予 |
| `GetGreatPeople():CanRecruitPerson / GetRecruitCost / CanPatronizePerson` | gamecore/ingame | GP+UI=function | 伟人资格与价格查询 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.RECRUIT_GREAT_PERSON, {[PlayerOperations.PARAM_GREAT_PERSON_INDIVIDUAL_TYPE]=id})` | ingame | 源码 Base\Assets\UI\Popups\GreatPeoplePopup.lua:886-892 | UI 途径招募 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.PATRONIZE_GREAT_PERSON, kParameters)` | ingame | 源码 GreatPeoplePopup.lua:905-927 | 金/信赞助 |
| `UI.RequestPlayerOperation(pid, PlayerOperations.REJECT_GREAT_PERSON, kParameters)` | ingame | 源码 GreatPeoplePopup.lua:896-903 | 拒绝伟人 |
| `Game.GetHeroesManager():PlayerDiscoverNextHero(pid)` / `SetHeroDiscovered(...)` | gamecore | GP=function | 英雄模式发现/解锁英雄 |

## 8. 地图与地块

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `PlayerVisibilityManager.GetPlayerVisibility(pid)` | gamecore/ingame | GP+UI=function | 取玩家视野对象 |
| `pVis:RevealAllPlots(...)` | gamecore | GP=function、UI=ERR | 揭示全图 |
| `pVis:ChangeVisibilityCount(plotIndex, n)` | gamecore | GP=function + 源码 DLC\AlexanderScenario\Scripts\AlexanderScenario.lua:59 | 逐格调视野等级（侦察值） |
| `pVis:GetNumRevealedHexes` / `IsRevealed` / `GetState` | gamecore | GP=function、UI=ERR | 视野状态查询 |
| `WorldBuilder.MapManager:SetAllRevealed(...)` | gamecore | GP=function、UI=ERR | WB 全图揭示 |
| `WorldBuilder.MapManager:SetRevealed(...)` | gamecore | GP=function、UI=ERR | WB 单格揭示 |
| `TerrainBuilder.SetTerrainType(plot, terrainIndex)` | gamecore | GP=function、UI=ERR | 改地形 |
| `TerrainBuilder.SetFeatureType(plot, featureID)` | gamecore | GP=function、UI=ERR | 改地貌（清除取值约定待实测） |
| `TerrainBuilder.SetResourceType(plot, resIdx, amount)` | gamecore | GP=function、UI=ERR | 放/改资源 |
| `TerrainBuilder.SetContinentType(...)` / `StampContinents()` | gamecore | GP=function、UI=ERR | 改大陆归属 |
| `TerrainBuilder.SetWOfRiver / SetNWOfRiver / SetNEOfRiver` + `Set*OfCliff` | gamecore | GP=function、UI=ERR | 写河流与断崖（引擎唯一河流写入口） |
| `TerrainBuilder.AddIce` / `AddCoastalLowland` / `GenerateFloodplains` | gamecore | GP=function、UI=ERR | 冰/低地/洪泛区 |
| `TerrainManager:FloodCoast` / `SubmergeCoast` / `ClearCoastalFlooding` | gamecore | GP=function | 海岸淹没/沉降（XP2 气候） |
| `plot:SetOwner(pid)` | gamecore | GP=function + 源码 DLC\AustraliaScenario\Scripts\AustraliaScenario.lua:1348 | 改地块归属（-1 为无主） |
| `plot:SetProperty(key, value)` / `GetProperty` | gamecore | GP=function（读双端） | 地块属性注入 |
| `Map.GetPlot(x, y)` / `Map.GetPlotByIndex(idx)` / `GetPlotIndex(plot)` | gamecore/ingame | GP+UI=function | 取/换地块对象 |
| `WorldBuilder.CityManager:Create(pid, plot)` / `RemoveAt(plot)` / `SetPlotOwner(plot[, pid])` | gamecore | GP=function、UI=ERR | WB 建城/移除/改归属 |
| `WorldBuilder.UnitManager:Create(unitIdx, pid, plot)` / `Remove(unit)` / `RemoveAll(pid)` | gamecore | GP=function、UI=ERR | WB 刷/清单位 |
| `WorldBuilder.MapManager:SetImprovementType / SetRouteType / SetCoastalLowland / EditRiver / EditCliff` | gamecore | GP=function、UI=ERR | WB 改良/道路/河流/断崖 |
| `WorldBuilder.PlayerManager:SetPlayerGold / SetPlayerFaith / SetPlayerEra / SetPlayerLeader / InitializePlayer` | gamecore | GP=function、UI=ERR | WB 层玩家初始化与数值 |
| `WorldBuilder:StartUndoBlock()` / `EndUndoBlock()` / `Undo()` / `Redo()` | gamecore | GP=function | WB 改动批量撤销 |
| `RiverManager:GetRiverForFloodplain(x, y)` 等 | gamecore/ingame | GP+UI=function | 河流全只读（写入口只有 TerrainBuilder） |

## 9. 回合与时间

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `UI.RequestAction(ActionTypes.ACTION_ENDTURN)` | ingame | UI=function + 源码 Base\Assets\UI\ActionPanel.lua:512 | 结束回合（官方按钮路径） |
| `UI.RequestAction(ActionTypes.ACTION_ENDTURN, { REASON = "UserForced" })` | ingame | 源码 ActionPanel.lua:1099 | 强制结束回合（带 UserForced 标记） |
| `UI.RequestPlayerOperation(pid, PlayerOperations.END_TURN, {})` | ingame | 已知可用 | 结束回合（操作途径，2026-10-02 实机验证） |
| `UI.RequestAction(ActionTypes.ACTION_UNREADYTURN)` | ingame | 源码 ActionPanel.lua:537 | 取消回合就绪 |
| `AutoplayManager.SetActive(true)` | gamecore/ingame | GP+UI=function | 开关托管（Autoplay，2026-10-02 实机验证调用通路） |
| `AutoplayManager.SetTurns(n)` | gamecore/ingame | GP+UI=function | 设托管持续回合数（初始值 -1） |
| `AutoplayManager.GetTurns()` / `IsActive()` | gamecore/ingame | GP+UI=function | 托管状态查询 |
| `AutoplayManager.SetObserveAsPlayer` / `SetReturnAsPlayer(pid)` | gamecore/ingame | GP+UI=function | 观察者接管/交还玩家 |
| `AutoplayManager.SetDisableAssertsForAutoplay(n)` | gamecore/ingame | GP+UI=function | 托管期屏蔽断言 |
| `Game.SetCurrentGameTurn(turn)` | gamecore | GP=function | 直接跳到指定回合 |
| `GameConfiguration.SetMaxTurns(n)` / `SetStartTurn` / `SetStartYear` | 前端（UI 侧） | UI=function | 回合上限/起始回合设定（建局前） |
| `Game.GetMaxGameTurns()` | ingame | UI=function | 读回合上限 |
| `Game.SetRandomSeed(seed)` | gamecore | GP=function | 固定随机种子 |
| `Players[pid]:GetEras():SetEra(...)` | gamecore | GP=function、UI=ERR | 强制设定玩家时代 |
| `Game.GetEras():GetCurrentEra()` | gamecore/ingame | GP+UI=function | 读当前世界时代 |

## 10. 会话与生命周期

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `Network.SaveGame({Name=..., Location=SaveLocations.LOCAL_STORAGE, Type=SaveTypes.SINGLE_PLAYER, FileType=SaveFileTypes.GAME_STATE})` | ingame | UI=function + 源码 Base\Assets\UI\Menus\SaveGameMenu.lua:55-66 | 存档（2026-10-02 实机验证：返回 true，文件落 Saves/Single/<Name>.Civ6Save；传字符串返回 false） |
| `Network.LoadGame(同形表, ServerType.SERVER_TYPE_NONE)` | ingame | UI=function + 源码 Automation_Profile.lua:256、Automation_StandardTests.lua:298、MainMenu.lua:146 | 读档（2026-10-02 实机验证：返回 true=受理，异步重载，完成后停在"点击进入"界面，需 PostMessage ESC；完成判定 = GameCore_Tuner/InGame 状态重现） |
| `Network.LeaveGame()` | ingame/前端 | 源码 MainMenu.lua:72 | 离开当前网络会话（读档前官方先调它） |
| `Network.RestartGame()` | ingame | UI=function + 源码 InGameTopOptionsMenu.lua:80 | 同配置重开新局（2026-10-02 实机验证：返回 true，重载后 turn=1） |
| `Events.ExitToMainMenu()` | ingame | Events 双端 + 源码 ActionPanel.lua:928、EndGameMenu.lua:345 | 退出到主菜单（2026-10-02 实机验证；切换期间 4318 短暂拒绝连接） |
| `UI.ExitGame()` | ingame | 源码 InGameTopOptionsMenu.lua:462 存在；api.sqlite GP=ERR、UI=nil | 退出游戏到桌面（2026-10-02 实测：tuner 沙箱 InGame/MainMenu 态均为 nil，不可用；彻底退出走 `taskkill //IM CivilizationVI.exe //F`） |
| `GameConfiguration.SetValue(key, value)` | 前端 | UI=function + 源码 GameSetupLogic.lua:815 | 任意建局参数写入 |
| `GameConfiguration.GetValue(key)` | 前端/ingame | GP+UI=function | 读建局参数 |
| `GameConfiguration.SetGameSpeedType(hash)` / `SetHandicapType` / `SetStartEra` / `SetCalendarType` / `SetRuleSet` / `SetGameMode` / `SetTurnTimerType` | 前端 | UI=function | 建局标准项 setter |
| `GameConfiguration.SetToDefaults()` / `SetToPreGame()` / `RegenerateSeeds()` / `SetWorldBuilder()` | 前端 | UI=function | 重置/种子/世界构建器标记 |
| `MapConfiguration.SetMapSize(sizeName)` / `SetScript(file)` / `SetMaxMajorPlayers(n)` / `SetMaxMinorPlayers(n)` / `SetValue(k, v)` / `SetImportFilename(file)` | 前端 | UI=function | 地图配置 setter |
| `PlayerConfiguration[pid]:SetLeaderTypeName("LEADER_X")` | 前端 | UI=function + 源码 Base\Assets\UI\FrontEnd\TutorialSetup.lua:139、AdvancedSetup.lua:1154 | 设领袖 |
| `PlayerConfiguration[pid]:SetCivilizationTypeName("CIVILIZATION_X")` | 前端 | UI=function + 源码 LoadGameMenu.lua:523 | 设文明 |
| `PlayerConfiguration[pid]:SetSlotStatus(SlotStatus.SS_COMPUTER / SS_OPEN / SS_HUMAN)` | 前端 | UI=function + 源码 AdvancedSetup.lua:1384、Multiplayer\StagingRoom.lua:832/899 | 槽位状态（AI/开放/人类） |
| `PlayerConfiguration[pid]:SetReady(bool)` | 前端 | UI=function | 就绪标记 |
| `PlayerConfiguration[pid]:SetTeam(tid)` / `SetHandicapTypeID(hash)` / `SetLeaderRandomPoolID(...)` / `SetLocked(bool)` / `SetHidden(bool)` / `SetValue(k, v)` / `SetHotseatPassword(s)` | 前端 | UI=function | 其余槽位 setter |
| `PlayerConfiguration[pid]:GetLeaderTypeName()` / `GetCivilizationTypeName()` / `GetSlotStatus()` | 前端/ingame | GP+UI=function | 配置读取（读端双端可用） |
| `Network.BroadcastGameConfig()` / `Network.LaunchGame()` | ingame(UI) | UI=function、GP=ERR | 广播配置/启动对局（多人场景） |
| `Modding.GetModHandle(modId)` + `Modding.EnableMod(handle, true)` / `DisableMod(handle)` | 前端 | 源码 Mods.lua:391/666、MainMenu.lua:486 | 程序化启用/停用 mod（2026-10-02 实机验证通过） |
| 无头建局八步（MainMenu 态内）：`GameConfiguration.SetToDefaults()` → `SetValue("RULESET", nil)` → `BuildHeadlessGameSetup()` → `RebuildPlayerParameters(true)` → `GameSetup_RefreshParameters()` → `ReleasePlayerParameters()` → `HideGameSetup()` → `Network.HostGame(ServerType.SERVER_TYPE_NONE)` | MainMenu 上下文 | 源码 MainMenu.lua:160-175（PlayNow 原文流程） | 从主菜单直接开默认对局（2026-10-02 实机验证全序列 ok 并建成新局） |

## 11. Modifier / Property 运行时注入

| API 调用式 | 所在端 | 依据 | 一句话说明 |
|---|---|---|---|
| `Game.SetProperty(key, value)`（点号调用） | gamecore | GP=function | 全局属性写入 |
| `Game.GetProperty(key)` | gamecore/ingame | GP+UI=function | 全局属性读取 |
| `Game.SetRandomSeed(seed)` | gamecore | GP=function | 固定随机种子 |
| `Players[pid]:SetProperty(key, value)` | gamecore | GP=function | 玩家属性写入 |
| `Players[pid]:GetProperty(key)` / `GetProperties()` | gamecore/ingame | GP+UI=function（GetProperties 仅 UI） | 玩家属性读取 |
| `Players[pid]:AttachModifierByID("MODIFIER_xxx")` | gamecore | GP=function | 运行时把库内 Modifier 挂到玩家 |
| `city:AttachModifierByID(...)` | gamecore | GP=function | 运行时挂 Modifier 到城市 |
| `city:SetProperty(key, value)` / `GetProperty` | gamecore | GP=function | 城市属性注入 |
| `unit:SetProperty(key, value)` / `GetProperty` | gamecore | GP=function（读双端） | 单位属性注入 |
| `plot:SetProperty(key, value)` | gamecore | GP=function | 地块属性注入 |
| `PlayerManager.SetProperty(...)` | gamecore | GP=function | 玩家管理器层属性 |
| `WorldBuilder.MapManager:SetPlotValue(plot, k, v)` / `CityManager:SetCityValue(city, k, v)` / `SetDistrictValue(...)` | gamecore | GP=function、UI=ERR | WB 数值注入通道 |
| `GameEffects.GetModifierActive(id)` / `GetModifierDefinition(id)` / `GetModifierSubjects(id)` | gamecore/ingame | GP+UI=function | Modifier/ReqSet 运行时只读检查（运行时挂载只走 AttachModifierByID） |

## 待实测（依据不完整或冲突）

| 条目 | 现状 |
|---|---|
| `Game.ChangePlayerEraScore(pid, n)` | api.sqlite 双端 nil；替代项 `Game.GetEras():ChangePlayerEraScore` 已验证 GP=function |
| `Game.GetReligion():FoundReligion()` / `AddBelief()` 参数签名 | UI 途径参数已由 ReligionScreen.lua:911/918 补全，GP 直调参数进局验证 |
| `UnitManager.RequestCommandImmediate(...)` | api.sqlite UI=function，args 为空 |
| `CityCommandTypes.DESTROY` 的 tParameters 具体 key | RazeCity.lua:20-52 只确认调用式 |
| 旅游业绩/总分的直接写接口 | 引擎未见 `SetTourism` / `SetScore`，只能经 Modifier/属性间接 |
| 议程运行时写入 | `Player:GetAgendasAndVisibilities` 只读，无写接口 |
| `DealManager.EnactWorkingDeal()` 直接成交 | GP=function，需先自建工作交易 |
| `UnitManager.SetLifespan/ChangeLifespan/SetMaxHitPoints` 等 | api.sqlite 双端 nil（判定文档偏宽），`Unit:SetDamage`/`ChangeExtraMoves` 可覆盖主要需求 |
| `TerrainBuilder.SetFeatureType` 清除地貌的取值约定 | 传 -1 或特定占位值需进局验证 |
| `Tests.QuitGame/Tests.End/Tests.PauseGame/Tests.QuitApp` 全系列 | api.sqlite 双端 ERR，判定不存在 |

## 2026-10-02 第二轮实测补充（指定领袖入局 + 人类行为模拟专项）

| 结论 | 依据 |
|---|---|
| 玩家配置表是 **`PlayerConfigurations`（复数）**；单数 `PlayerConfiguration` 在 tuner 前端态为 nil | 实测 + 官方 `AdvancedSetup.lua:1154` |
| 指定领袖入局：`PlayerConfigurations[0]:SetLeaderTypeName(lid)` 必须在 `RebuildPlayerParameters(true)` 之后、`Network.HostGame` 之前设定；实测 LEADER_CARLOTTA_QYQXP 成功入局 | 实机验证 |
| 城市入队生产只传 `t[CityOperationTypes.PARAM_UNIT_TYPE]=hash` 即可生效；附带 `CityOperationTypes.PARAM_INSERT_MODE=VALUE_EXCLUSIVE` 反而不入队（两次对照实测） | 实机验证 |
| `UnitOperationTypes` 枚举在 tuner 沙箱缺 SLEEP/SKIP_TURN/AUTOMATE_EXPLORE 成员（nil），但数据库哈希可直接调用：SLEEP=-41338758、SKIP_TURN=745019656、AUTOMATE=`UnitCommandTypes.AUTOMATE`=893276661 | 实机验证（GameInfo.UnitCommands/UnitOperations 行） |
| 近战攻击可靠写法：单位与目标相邻时 `RequestOperation(u, MOVE_TO, {PARAM_X, PARAM_Y, [PARAM_MODIFIERS]=UnitOperationMoveModifiers.ATTACK})`；实测蛮族受伤 23 / 我方受伤 27、双方原格不动 | 实机验证 |
| `Unit` 对象在 tuner UI 态只有部分方法可用：GetID/GetX/GetY/GetType/GetDamage/GetUpgradeCost 正常；IsFortified/GetMovement 等抛 "Not a valid instance" | 实机验证 |
| **`InitUnit` 不校验地形**：陆军刷到 TERRAIN_COAST 会被引擎清除并留下位置 -9999,-9999 的僵尸句柄，后续对其调方法抛 "实例无效"。刷兵前先 `Map.GetPlot(x,y)` 查地形 | 实机验证（64,14/64,13 均为海岸） |
| 升级门槛未解：`GetUpgradeCost()` 返回正确费用（投石手 60）说明引擎认得升级链（UnitUpgrades 表 UNIT_WARRIOR→UNIT_SWORDSMAN 在），但 `CanStartCommand(u, UPGRADE, false, true)` 持续 false——金币/科技/资源/境内外/回合 2 全部排除，本机 40-mod 环境未复现成功。确定性替代：`UnitManager.Kill(u)` + `InitUnit(目标单位, 同格)`（实测投石手→弓手） | 实机验证 |
| AUTOMATE 指令被受理但单位跨回合未移动（效果未证实，待查） | 实机验证 |
| 结束回合阻塞：`NotificationManager.GetAllEndTurnBlocking()` 返回阻塞哈希表，用 `EndTurnBlockingTypes` 枚举反查名称（实测 ENDTURN_BLOCKING_UNITS）；给全部空闲单位发 SKIP_TURN 后清零；**强制过回合 = `UI.RequestAction(ACTION_ENDTURN, {REASON="UserForced"})`**——官方注释原文即 Shift+Enter 强制过回合（ActionPanel.lua:1098-1101），实测把被阻塞的回合推过去了 | 实机验证 + 源码 |
| 局内"退出游戏"按钮的真实链路：`Controls.ExitGameButton → OnExitGameAskAreYouSure → OnExitGame → Events.UserConfirmedClose()`（InGameTopOptionsMenu.lua:697/152-165/135-141）；`UI.ExitGame()` 属另一分支（ms_ExitToMain=false）且 tuner 沙箱双态均 nil | 源码 + 实测 |
| `ActionTypes` 仅 4 项：ACTION_ENDTURN / ACTION_RETIRE（投降）/ ACTION_UNREADYTURN / NO_ACTION；真实输入面在 `InputSettings.json` 的 117 个命名动作（EndTurn/Attack/AutoExplore/Fortify/FortifyUntilHeal/Sleep/SkipTurn/DeleteUnit/FoundCity/MoveTo/RangedAttack/QuickSave/QuickLoad/镜头/透镜等，另含本机 mod 注入项），程序化等价物即对应 Command/Operation 哈希 | 实测转储 + 本机 InputSettings.json |
| **读档后"点击进入"界面的按键溯源**：ESC 的 OnInput 处理体（LoadScreen.lua:78-88）在 m_isLoadComplete 时调 `OnActivateButtonClicked()`（:42-58）= 核心命令 `Events.LoadScreenClose()` + 音效 + `UIManager:DequeuePopup(ContextPtr)` + `Input.SetActiveContext(InputContext.World)`。LoadScreen 态在 LSQ 可达时直调整个处理函数（gamectl 确认链溯源路线），不可达才 `game_input.py esc` 兜底 | 源码 LoadScreen.lua:42-58/78-88 + 实测 |
