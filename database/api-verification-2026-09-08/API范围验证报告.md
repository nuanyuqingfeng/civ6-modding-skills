# 文明6 全量 API × UI/GP 范围存在性验证报告

> 生成时间：2026-09-08 16:19:49　|　验证通道：FireTuner 调试接口 (TCP 127.0.0.1:4318)
> 游戏实例：`Civ6 / Sid Meier's Civilization 6 / F:\Steam\steamapps\common\Sid Meier's Civilization VI\Base\Binaries\Debug`
> 上下文：GP = `GameCore_Tuner`(状态 19)　UI = `InGame`(状态 174)　+ 复查用其它 UI 状态 12 个
> 文档基线：civ6-modding `api.sqlite`（4857 行 API）

---

## 0. 结论速览

1. **共验证 4857 条 API**（文档全量），其中 **3667 条为真实运行时命名空间/类**，**1190 条（24.5%）属文档转储清单**（`CodeBuddyFuncs` / `CodeBuddyFuncsRaw`，运行时并无该全局）。
2. **文档 availability 与运行时一致率 87.2%**（3196/3667，不含转储清单）；**不符 316 条（8.6%）**，**无法验证 155 条（4.2%）**。
3. **运行时实际范围**：双端可见 1024 条、仅 UI 1848 条、仅 GP 511 条、双端未见 284 条。UI 面显著宽于 GP 面（1848 vs 511）。
4. **最典型偏差：文档把 UI 专属模块标成 `Both`**——「文档偏宽：GP 未见」126 条中，TunerUtilities(57)、ToolTipHelper(15)、g_ToolTipGenerators(13) 等均为 UI 脚本模块。
5. **同名对象在两端是不同类**：`City` 在 GP 是服务端 City（29 法），在 UI 是 CacheCity（42 法，仅 18 法共有）；`Player` GP 49 / UI 46（共有 29）；`Plot` 几乎对称（GP 91 / UI 89，共有 89）。
6. **GameInfo 数据库面比文档宽得多**：运行时 426/427 张库表可经 `GameInfo.<表>` 双端取到，文档只登记了 161 张；唯一不可达：NavigationProperties。
7. **事件面是动态代理**：GP 的 `GameEvents` / `LuaEvents`、UI 的 `LuaEvents` 对任意名都返回 table（自动注册），因此「存在性」对事件无意义；UI 的 `Events` 与 GP 的 `Events` 不自动生成，可正常判定。
8. **文档名本身有缺陷 59 条**：三层路径被压平（`City:GetDistricts():GetDistrict(i):X` 写成 `GetDistrictX`）、id 残留（`Q-MapGetCityPlots…`）、`Get` 前缀冗余（`UI.GetGameParameters` 的 15 个子名，实际对象只有 5 个方法）。

---

## 1. 验证目标与方法

**目标**：对文档收录的全部文明6 API，逐条判定其在 **GP（GamePlay 脚本层）** 与 **UI（前端脚本层）** 两个上下文中**是否存在**（只做存在性，不验证签名、不验证返回值、不验证行为）。

### 1.1 通道与前置

| 项 | 值 |
|---|---|
| 通道 | FireTuner 调试协议（帧 `[4B 长度][4B tag][NUL 结尾 payload]`，tag=4 握手 / tag=3 执行） |
| 游戏构建 | Debug（`Base\Binaries\Debug`），Tuner 已开启，FireTuner GUI 关闭（单连接限制） |
| 对局状态 | 进行中（GP 状态索引 19，UI 状态索引 174；本机共 178 个 Lua 状态） |
| 执行次数 | 主扫描 219 次 + 补测 84 次 + 定点核验约 15 次 |
| 单次载荷 | 每批 600 条表达式（约 26 KB），实测 1 秒内返回 |

### 1.2 判定手法（严格只读）

```lua
-- 每条 API 都还原成一次「索引」，用 loadstring + pcall 取类型，不调用任何方法
local f = loadstring("return (" .. expr .. ")")
local ok, v = pcall(f)
-- ok 且 v ~= nil  -> 存在（记录 type）
-- ok 且 v == nil  -> 容器可达但无此成员
-- not ok          -> ERR：命名空间不存在 / 无实例 / 父对象未解析
```

三类访问路径的还原方式：

| 文档形态 | 运行时表达式 | 说明 |
|---|---|---|
| `Dot (Global)` | `<命名空间>[.<方法>][.<子方法>]` | 直接索引全局表 |
| `Colon (Instance)` | `__SC.C_<类>[.<方法>]` | `__SC` 为扫描期登记的实例表（见 1.3） |
| 带子方法（嵌套） | `__SC.C_<类>_P_<父方法>.<子方法>` | 先取父对象再查子方法 |
| GameInfo 库表 | `GameInfo.<表名>` | 文档中 161 条 `Q-GameInfo*` |

### 1.3 实例提供者（Colon 类的取实例途径）

| 类 | 取法 | GP | UI |
|---|---|---|---|
| Player | `Players[Game.GetLocalPlayer()]` | ✅ | ✅ |
| City | `player:GetCities():Members()` 首个 | ✅（服务端 City） | ✅（CacheCity） |
| Unit | `player:GetUnits():Members()` 首个 | ✅ | ✅ |
| Plot | `Map.GetPlotByIndex(0)` | ✅ | ✅ |
| Game | `Game` 全局本身 | ✅ | ✅ |
| Control | `Controls` 中首个 `CTypeName==ControlBase` | —（GP 无 UI） | ✅ |
| ContextPtr / UIManager / TouchManager … | 同名全局（模块/代理表） | 部分 | ✅ |
| Notification / DiplomacyDeal / InputStruct … | 需特定运行条件 | ❌ | ❌ |

### 1.4 三轮扫描

1. **主扫描**：登记 `__SC` → 解析 74 个嵌套父对象 → 分批探测 5189 条表达式 + 427 张 GameInfo 库表 → 枚举 266 个命名空间的键与实例方法表。
2. **补测**：修正首轮 48 条「dot 型带子方法」的表达式（原式是索引函数，必然 ERR）；对 85 个可疑子名生成候选真名重测；把「文档声称可用却未见」的条目拿到 12 个其它 UI 状态复查（WorldInput, StrategicView, TopPanel_TT, ARXManager, CityBannerManager, PlotToolTip 等）。
3. **三层恢复**：文档把 `City:GetDistricts():GetDistrict(i):GetAirSlots()` 压平成 `GetDistrictGetAirSlots`，故再下钻一层取 District 实例（GP 20 法 / UI 27 法）核对真名；Governor 层因本局无已任命总督而未能取到。

### 1.5 副作用与复原（重要）

- 全程**只做索引**；唯一的调用是文档标注的**零参 `Get*` 父方法**（用于取子对象方法表），外加两个只读查询 `Territories:GetTerritoryAt(0)`、`MapRoutes.GetIndexedPortal(0)`。未结束回合、未改任何游戏状态。
- UI 侧为取到模块类做过 `include`，**白名单仅限已逐文件核实「加载期无顶层副作用」的模块**：`InstanceManager`、`PopupDialog`、`ToolTipHelper`（及其传递依赖 `SupportFunctions`、`TechAndCivicUnlockables`）。
- **主动排除 `TunerUtilities`**：其文件末尾执行 `UIManager:SetGlobalInputHandler(TunerUtilities.OnInputHandler)`，会顶掉 InGame 的全局输入处理器（该处理器拦截 CapsLock 切换取色/拾取）。
- 收尾已复原：清除扫描期新增的全局（`__SC` / `__SCINFO` / `__SCAN_ADDED` 及 include 进来的模块全局）、把全局输入处理器复位为 `function() return false end`，并逐项复核为 `nil`；游戏原生全局（`PopupDialogInGame` / `GenerationalInstanceManager` / `PullDownInstanceManager`）未动。扫描后 `check` 仍显示对局正常。

### 1.6 状态语义

| 状态 | 含义 |
|---|---|
| `function` / `table` / `userdata` / `string` / `number` | 存在（记录到的运行时类型） |
| `nil` | 容器可达，但没有这个成员 → **该上下文不提供** |
| `ERR` | 索引失败：命名空间不存在 / 类无实例 / 父对象未解析 |
| `CF` | 表达式无法编译（文档给的是 C++ 签名串，不是 Lua 名） |
| `不可判` | 无实例通道或动态代理，存在性无法判定（≠ 不存在） |

---

## 2. 总体判定

| 判定 | 条数 | 占全量 |
|---|---:|---:|
| 一致 | 3095 | 63.7% |
| 文档转储（非运行时命名空间） | 1190 | 24.5% |
| 文档偏宽：GP 未见 | 126 | 2.6% |
| 一致（GP 侧不可验证） | 101 | 2.1% |
| 文档偏宽：双端均未见 | 81 | 1.7% |
| 无法验证：需进行中的外交交易会话（Deal 内条目） | 38 | 0.8% |
| 文档存疑：UI 未见 | 38 | 0.8% |
| 文档偏窄：GP 亦可见 | 33 | 0.7% |
| 无法验证：需玩家当前有未读通知（本局本地玩家通知列表为空） | 30 | 0.6% |
| 文档偏宽：UI 未见 | 28 | 0.6% |
| 无法验证：需进行中的外交交易会话（DealManager 取出 Deal 实例） | 24 | 0.5% |
| 无法验证：需世界生成器会话（WorldBuilder.ResourceGenerator） | 23 | 0.5% |
| 无法验证：需输入事件回调实参（UI 输入处理器触发时才有） | 16 | 0.3% |
| 无法验证：需地图钉编辑 UI 上下文（MapPinManager 内） | 13 | 0.3% |
| 文档存疑：GP 未见 | 10 | 0.2% |
| 无法验证：需存在自由城市实例（CityManager.GetFreeCityAt） | 7 | 0.1% |
| 无法验证：需 Fractal.Create(...) 参数化构造（世界生成期） | 3 | 0.1% |
| 动态事件代理（不可判） | 1 | 0.0% |
| **合计** | **4857** | 100% |

去掉 1190 条文档转储后，真实 API 3667 条：**一致 3196（87.2%）**、**不符 316（8.6%）**、**无法验证 155（4.2%）**。

### 运行时实际范围（不含转储清单）

| 实际范围 | 条数 | 占比 |
|---|---:|---:|
| 双端 | 1024 | 27.9% |
| 仅UI | 1848 | 50.4% |
| 仅GP | 511 | 13.9% |
| 双端未见 | 284 | 7.7% |

> 「双端未见」= 文档声称可用，但两端都没检出；其中大部分是文档名缺陷或版本差异（见 §6、§8），少数确需特定运行条件（见 §7）。

---

## 3. 命名空间层面的 UI/GP 分界

文档共涉及 267 个命名空间/类名。运行时可见性：

| 可见性 | 数量 |
|---|---:|
| 双端可见 | 39 |
| 仅 GP 可见 | 13 |
| 仅 UI 可见 | 39 |
| 双端不可见 | 176 |

**仅 GP（13）**：`AreaBuilder`、`Areas`、`City`、`Fractal`、`GameEvents`、`ImprovementBuilder`、`Player`、`PlayerVisibility`、`ResourceBuilder`、`RouteBuilder`、`StartPositioner`、`TerrainBuilder`、`Unit`

> 世界生成/地形改写类（`TerrainBuilder`、`ResourceBuilder`、`RouteBuilder`、`ImprovementBuilder`、`AreaBuilder`、`Areas`、`StartPositioner`、`Fractal`）与 `GameEvents` 是 GP 专属；`PlayerVisibility` 在 GP 是命名空间、在 UI 需实例。

**仅 UI（39）**：`AssetPreview`、`AutoProfiler`、`Benchmark`、`Calendar`、`ContextPtr`、`Definitions`、`DiplomacyManager`、`DirtyComponentsManager`、`EffectsManager`、`FeatureGenerator`、`FiraxisLive`、`GenerationalInstanceManager`、`HallofFame`、`IconManager`、`Input`、`InstanceManager`、`Matchmaking`、`Modding`、`NaturalWonderGenerator`、`Network`、`Options`、`PopupDialog`、`PopupDialogInGame`、`PullDownInstanceManager`、`Search`、`SimUnitSystem`、`Steam`、`TTManager`、`ToolTipHelper`、`TouchManager`、`TunerUtilities`、`UI`、`UILens`、`UIManager`、`UITree`、`UITutorialManager`、`UserConfiguration`、`WorldView`、`g_ToolTipGenerators`

> 全部 UI 专属面：`UI`/`UILens`/`UIManager`/`Input`/`Network`/`Modding`/`Options`/`Steam`/`Matchmaking`/`UserConfiguration`/`AssetPreview`/`ToolTipHelper`/`InstanceManager`/`PopupDialog`/`TunerUtilities` 等。

> ⚠ 其中 4 个是 **`include` 之后才可见**（本次扫描按白名单 include 后检出，收尾已复原为 nil）：`InstanceManager`、`PopupDialog`、`ToolTipHelper`、`TunerUtilities`。其余 35 个为 InGame 根上下文**原生可见**（收尾复原后重新复核，原始回传见 `raw/native_ui_check.txt`）。也就是说：写 mod 时要用这些面，必须先 include 对应模块，否则运行时为 nil。

**双端不可见（176）**：其中 138 个是 GameInfo 库表名（`Buildings`、`Units`、`Modifiers`…，本来就不是全局，须经 `GameInfo.<表>` 访问，已单独验证见 §5）；其余是纯实例类（`Control`、`Notification`、`DiplomacyDeal(Item)`、`InputStruct`、`FreeCities`、`MapPinConfiguration`、`WorldBuilderResourceGenerator`）、文档转储（`CodeBuddyFuncs(Raw)`）与前端/工具模块（`json`、`Tools`、`Relationship`、`Tests.*`）。

**受保护元表（C 侧 `__index`，`pairs` 不可枚举，只能按名索引）**：GP 8 个、UI 22 个。典型：`UI`、`GameInfo`、`Locale`、`Network`、`Modding`、`Input`、`UILens`、`Options`、`Steam`、`Search`、`DB`、`Path`。这也是本次必须逐名探测（而非纯枚举）的原因。

---

## 4. 核心发现：同名对象在 GP/UI 是两个不同的类

| 对象 | GP 方法数 | UI 方法数 | 共有 | 仅 GP | 仅 UI |
|---|---:|---:|---:|---:|---:|
| Player（玩家） | 49 | 46 | 29 | 20 | 17 |
| City（城市 / UI 侧为 CacheCity） | 29 | 42 | 18 | 11 | 24 |
| Unit（单位） | 71 | 72 | 50 | 21 | 22 |
| Plot（地块） | 91 | 89 | 89 | 2 | 0 |
| City:GetBuildQueue() | 20 | 26 | 5 | 15 | 21 |
| City:GetBuildings() | 10 | 17 | 6 | 4 | 11 |
| City:GetGrowth() | 14 | 41 | 14 | 0 | 27 |
| City:GetDistricts() | 13 | 12 | 4 | 9 | 8 |
| Player:GetCulture() | 30 | 68 | 17 | 13 | 51 |
| Player:GetGovernors() | 4 | 22 | 3 | 1 | 19 |
| Unit:GetReligion() | 27 | 0 | 0 | 27 | 0 |

**要点**

- `City`：GP 侧独有写操作与底层数据（AttachModifierByID ChangeLoyalty ChangePopulation GetBuildingFaithPurchaseEnabled GetOwnedPlots GetPlot GetUnitFaithPurchaseEnabled SetBuildingFaithPu…）；UI 侧独有展示/缓存面（CanRaze GetAllAssignedGovernors GetAmenityAdvice GetAssignedGovernor GetBuildingPotentialYield GetBuildingYield GetCityAI GetComponentID GetCulturalIdentity GetCulture Ge…）。**在 GP 脚本里调 `city:GetGold()` / `city:GetCulture()` 会直接报 nil**——这是 mod 常见踩坑点。
- `Player`：GP 独有 `SetProperty`/`GrantYield`/`GrantWMDs`/`AttachModifierByID`/`GetAi_*`/`SetScoringScenario1..3`；UI 独有 `GetFavor*`/`GetAgendaTypes`/`GetImprovements`/`GetInfluenceMap`/`IsAI`/`GetCivilianLoyalty` 等读面。
- `Unit`：GP 独有 `Change*`/`Set*`（写），UI 独有 `Get*`（展示、间谍/摇滚乐队/考古等）。`Unit:GetReligion()` **仅 GP 有**（UI 侧返回 nil，UI 改用平铺的 `GetReligionType`/`GetReligiousStrength` 等）。
- `Plot`：两端几乎完全对称（共有 89），GP 只多 `SetOwner`/`SetProperty` 两个写方法——地块是最「同构」的对象。
- 子对象差异更大：`City:GetGrowth()` GP 14 法 vs UI 41 法；`Player:GetCulture()` GP 30 vs UI 68；`Player:GetGovernors()` GP 4 vs UI 22。
- 完整差集（含每个对象的「仅GP清单 / 仅UI清单」全文）见 `GP_UI方法面差异.csv`。

---

## 5. GameInfo 数据库面

- 以 `DebugGameplay.sqlite` 的 427 张库表为准逐名探测：**GP 426 张、UI 426 张可经 `GameInfo.<表>` 取到（返回 userdata）**。
- 不可达：NavigationProperties（该表存在于库转储但运行时未暴露）。
- 文档只登记了 161 张 GameInfo 子表，运行时可用面约为文档的 2.6 倍——**查库时不必受文档表清单限制**。
- 明细见 `GameInfo库表可达性.csv`。

---

## 6. 文档 availability 与运行时不符（316 条）

| 不符类型 | 条数 | 主要命名空间 |
|---|---:|---|
| 文档偏宽：GP 未见 | 126 | TunerUtilities(57)、ToolTipHelper(15)、g_ToolTipGenerators(13)、InstanceManager(10)、FeatureGenerator(10)、NaturalWonderGenerator(6) |
| 文档偏宽：双端均未见 | 81 | Player(15)、MapRoutes(5)、UI(5)、Unit(4)、Map(3)、Relationship(3) |
| 文档偏宽：UI 未见 | 28 | GameSummary(19)、PlayerVisibility(4)、RouteBuilder(4)、City(1) |
| 文档存疑：UI 未见 | 38 | Player(12)、UI(10)、IconManager(5)、Events(5)、Input(3)、PlayerVisibility(2) |
| 文档存疑：GP 未见 | 10 | UnitManager(7)、TerrainBuilder(2)、Map(1) |
| 文档偏窄：GP 亦可见 | 33 | Events(13)、Achievements(9)、GameSummary(9)、PlayerVisibilityManager(2) |

**逐类解读**

1. **文档偏宽：GP 未见（126 条）**——文档标 `Both`，实际只在 UI 存在。绝大多数是 UI 脚本模块被误标：`TunerUtilities.(命名空间)`、`TunerUtilities.Stringify`、`TunerUtilities.FromCSV`、`TunerUtilities.GetContextTree`、`TunerUtilities.GetControlChildren`。**结论：这些模块在 GP 脚本里根本不存在，`include` 也无效；而在 UI 侧也需先 `include` 才可见（见 §3 注）。**
2. **文档偏宽：双端均未见（81 条）**——两端都没有该名字，多为文档名与运行时不一致或版本差异：`Player.ChangeDiplomaticFavor`、`Player.GetAi_Diplomacy → GenerateToolTips`、`Player.GetAi_Diplomacy → GetNumToolTips`、`Player.GetAi_Diplomacy → GetToolTip`、`Player.GetDiplomacy → GetAllianceLevelWithPlayer`（运行时近似名：GetAllianceLevel…）、`Player.GetGovernors → GetIdentityPressure`。例如 `Player:SetScoringScenario` 运行时实为 `SetScoringScenario1/2/3`；`Player:GetDiplomacy():GetAllianceLevelWithPlayer` 运行时为 `GetAllianceLevel`。
3. **文档偏宽：UI 未见（28 条）**——GP 专属被标 `Both`：`GameSummary.GetDataPoints`、`GameSummary.GetOrCreateDataSet`、`GameSummary.FindDataSet`、`GameSummary.GetCityObject`、`GameSummary.GetDataSets`（`GameSummary`/`RouteBuilder`/`PlayerVisibility` 属世界生成与 GP 侧统计面）。
4. **文档存疑：UI 未见（38 条）**——文档标 `UI` 却在 InGame 上下文找不到：`Player.GetGovernors → GetGovernorGetComponentID`（运行时近似名：GetGovernor…）、`Player.GetGovernors → GetGovernorHasPromotion`（运行时近似名：GetGovernor…）、`Player.GetGovernors → GetGovernorGetOwner`（运行时近似名：GetGovernor…）、`Player.GetGovernors → GetGovernorCanAssignToMajorCiv`（运行时近似名：GetGovernor…）、`Player.GetGovernors → GetGovernorGetNeutralizedTurns`（运行时近似名：GetGovernor…）。细分为：Governor 三层对象本局取不到实例（12 条）、`IconManager` 需实例而非模块面（5 条）、FrontEnd 事件在 InGame 不可见（`Events.BeginFullGamePurchase`/`MultiplayerConnectionFailed` 等 5 条）、`InputStruct` 的方法被挂到了 `Input` 名下（3 条）。
5. **文档存疑：GP 未见（10 条）**——标 `GamePlay` 但 GP 侧没有：`UnitManager.SetLifespan`、`UnitManager.GetUnitType`、`UnitManager.ChangeLifespan`、`UnitManager.ResetLifespan`、`UnitManager.SetMaxHitPoints`（`UnitManager` 的 Lifespan/MaxHitPoints 系与 `TerrainBuilder.SetResourceType` 疑为旧版或 WorldBuilder 专属）。
6. **文档偏窄：GP 亦可见（33 条）**——标 `UI` 但 GP 也有，属**可利用的好消息**：`Events.Begin2KLoginProcess`、`Events.DisableColorKey`、`Events.EnableColorKey`、`Events.HideLeaderScreen`、`Events.RestartWonderMovie`（`Achievements`、`GameSummary`、`PlayerVisibilityManager`、部分 `Events` 在 GP 同样可调用）。

> 全部不符条目（含运行时近似名建议列）见 `api_scope_文档与运行时不符.csv`。

---

## 7. 无法验证清单（155 条）与补救办法

| 阻塞原因 | 条数 | 复现所需条件 |
|---|---:|---|
| `DiplomacyDealItem` | 38 | 需进行中的外交交易会话（Deal 内条目） |
| `Notification` | 30 | 需玩家当前有未读通知（本局本地玩家通知列表为空） |
| `DiplomacyDeal` | 24 | 需进行中的外交交易会话（DealManager 取出 Deal 实例） |
| `WorldBuilderResourceGenerator` | 23 | 需世界生成器会话（WorldBuilder.ResourceGenerator） |
| `InputStruct` | 16 | 需输入事件回调实参（UI 输入处理器触发时才有） |
| `MapPinConfiguration` | 13 | 需地图钉编辑 UI 上下文（MapPinManager 内） |
| `FreeCities` | 7 | 需存在自由城市实例（CityManager.GetFreeCityAt） |
| `Fractal` | 3 | 需 Fractal.Create(...) 参数化构造（世界生成期） |
| `GameEvents` | 1 | 动态事件代理（不可判） |

**补救办法（需要时再跑一轮即可闭环）**

- `Notification`（30 条）：先用 GP 造一条通知（或读一个有未读通知的存档），再重跑 pass3 即可取到实例。
- `DiplomacyDeal` / `DiplomacyDealItem`（62 条）：进入一次外交交易界面（`DealManager` 取 working deal）后重扫 UI。
- `Player:GetGovernors():GetGovernor(i)` 三层（16 条）：本局无已任命总督；任命任一总督后重跑三层恢复即可。
- `WorldBuilderResourceGenerator`（23 条）/ `Fractal`（3 条）：需在世界生成器会话中扫描。
- `InputStruct`（16 条）：需真实输入事件回调时抓 `pInputStruct` 实例（可在 UI 输入处理器里挂一次性钩子）。
- `MapPinConfiguration`（13 条）：在地图钉编辑 UI 打开时扫描。
- `MapRoutes.GetIndexedPortal` 子方法（5 条）：需地图上存在传送门（portal）；`GetIndexedPortal(0)` 在本图返回空。

---

## 8. 文档数据缺陷（api.sqlite 侧）

### 8.1 转储清单冒充命名空间：1190 条（24.5%）

- `CodeBuddyFuncs`（595 条）与 `CodeBuddyFuncsRaw`（595 条）在 GP/UI **都没有这个全局**，它们是把各处 UI 辅助函数汇总成的文档清单。
- 把 `CodeBuddyFuncs` 的 594 个函数名拿到真实面上反查（UI 51 个面 / GP 43 个面）：**UI 侧命中 238 个名字、GP 侧命中 9 个、两端都找不到 354 个**。归属面 Top：

| 归属面 | 命中名数 |
|---|---:|
| `实例:ContextPtr` | 136 |
| `实例:Control` | 103 |
| `实例:UIManager` | 52 |
| `TouchManager` | 17 |
| `UITutorialManager` | 11 |
| `TTManager` | 9 |
| `TunerUtilities` | 7 |

- `CodeBuddyFuncsRaw` 的「名字」其实是 C++ 原始签名串（如 `ButtonControl* GetButton( void )`、`CFunction: AddVertex`），**无法作为 Lua 名索引**（首轮 582 条 `CF` 状态即由此产生）；从签名里归一化出 574 个候选标识符后，UI 侧命中 243 个。
- 明细见 `CodeBuddy归属面.csv` 与 `api_scope_CodeBuddy转储.csv`。

### 8.2 名称拼接/损坏：59 条

| 缺陷形态 | 例子 | 处理 |
|---|---|---|
| 三层路径压平 | `City.GetDistricts` → `GetDistrictGetAirSlots` | 下钻 `GetDistrict(i)` 取 District 实例后按真名 `GetAirSlots` 命中（UI 侧 12 条转为一致） |
| 三层路径压平 | `Player.GetGovernors` → `GetGovernorGetComponentID` | 同上，但本局无总督实例 → 仍记不可验证 |
| 文档 id 残留 | `Map.GetCityPlots` → `GetWorkingCityIDQ-MapGetCityPlots` | 真名 `GetWorkingCityID`（UI 命中） |
| 文档 id 残留 | `Map.GetContinentCoastalPlots` → `Q-MapGetCityPlotsGetPurchasedByCity` | 真身是 `Map.GetCityPlots():GetPurchasedByCity()`（UI 命中） |
| `Get` 前缀冗余 | `UI.GetGameParameters` → `GetSetValue` / `GetGetCount` … 15 条 | 实测该对象只有 `Add/Get/GetValue/Remove/SetValue` 5 法：5 条对得上、10 条属文档多写 |

> 明细见 `api_scope_文档名异常.csv`（含每条的 GP/UI 真名列）。

### 8.3 事件面是动态代理

| 面 | GP | UI | 说明 |
|---|---|---|---|
| `GameEvents` | 任意名 → table | 不存在 | GP 事件表按需自动生成，存在性检查无意义 |
| `LuaEvents` | 任意名 → table | 任意名 → table | 同上 |
| `Events` | 未知名 → nil | 未知名 → nil | **可以**做存在性判定（本轮据此判定 `Events.*` 25 条） |
| `ReportingEvents` | 未知名 → nil | 未知名 → nil | 同上 |

---

## 9. 交付物清单

目录：`<本目录（随 skill 分发）>`

| 文件 | 内容 |
|---|---|
| `API范围验证报告.md` | 本报告 |
| `api_scope_full.csv` | 全量 4857 条逐条结果（GP/UI 状态、存在性、真名、近似名、备注、判定） |
| `api_scope_文档与运行时不符.csv` | 316 条不符明细 |
| `api_scope_无法验证.csv` | 155 条不可判明细（含阻塞原因） |
| `api_scope_文档名异常.csv` | 59 条名称拼接/损坏（含真名） |
| `api_scope_CodeBuddy转储.csv` | 1190 条转储清单条目 |
| `命名空间汇总.csv` | 每个命名空间/类的条目数、GP/UI 存在数、判定分布 |
| `命名空间可见性.csv` | 267 个名字在 GP/UI 的类型、键数、是否受保护元表 |
| `GP_UI方法面差异.csv` | 实例与子对象的方法面差集（含仅GP/仅UI 全清单） |
| `GameInfo库表可达性.csv` | 427 张库表的运行时可达性 |
| `CodeBuddy归属面.csv` | 转储名字在真实面上的归属 |
| `统计.json` | 全部统计数字（机器可读） |
| `审核清单.md` / `审核清单.xlsx` / `审核清单_预分类.csv` | 471 条问题项的**预分类逐条清单**（P1 可直接改 / P2 需裁决 / P3 待补测 / P4 助手未收录），xlsx 每档一个 sheet 带筛选 |
| `助手人工验证条目.csv` / `helper_humanChecked.json` | Civ6LuaHelper 内 18 条 `humanChecked` 条目与本次实测对照 |
| `审核清单_统计.json` | 审核清单的机器可读统计 |
| `raw/` | 原始回传（探测/枚举/子对象/三层/补测）、扫描与分析脚本、Lua 片段，可复现 |

CSV 均为 UTF-8-BOM，Excel 直接双击可正确显示中文。

---

## 10. 复现方法

```powershell
# 前置：游戏内 Options 勾选 Tuner；关闭 FireTuner GUI；读档进入对局
$T = "%USERPROFILE%/.agents/skills/civ6-tuner/scripts/tuner_exec.py"
python $T check                       # 确认 gamecore/ingame 状态存在
python "%USERPROFILE%\AppData\Local\Temp\civ6_api_scope\scan.py"                # 主扫描（约 219 次调用，1~2 分钟）
python "%USERPROFILE%\AppData\Local\Temp\civ6_api_scope\supplement.py"          # 补测（表达式修正 / 候选名 / 跨 UI 状态）
python "%USERPROFILE%\AppData\Local\Temp\civ6_api_scope\finalize.py"            # 归并 -> 桌面 CSV
python "%USERPROFILE%\AppData\Local\Temp\civ6_api_scope\mkreport.py"            # 生成本报告
```

三个脚本均在 `raw/` 内随附；Lua 片段在 `raw/lua_*.lua`。

---

## 11. 独立复核（QA）

为排除「扫描器自身系统性错误」，另写了一份**不复用扫描器实例表**的复核脚本（`raw/lua_qa.lua`：实例就地推导、命名空间用 `X and X.Y` 短路取值），跨判定类别抽 20 个 API 在两端重测，与 `api_scope_full.csv` 逐条比对：

| API | CSV 判定 GP | 复核 GP | CSV 判定 UI | 复核 UI | 结论 |
|---|---|---|---|---|---|
| `Plot.IsWater` | function | function | function | function | 一致 |
| `GameEffects.GetModifierArgumentString` | function | function | function | function | 一致 |
| `Unit.GetFormationUnitIDs` | function | function | nil | nil | 一致 |
| `UI.GetCursorNearestPlotEdge` | ERR | nil | function | function | 一致 |
| `DiplomacyManager.CloseSession` | ERR | nil | function | function | 一致 |
| `Game.SetWinningTeam` | function | function | nil | nil | 一致 |
| `FeatureGenerator.AddJunglesAtPlot` | ERR | nil | function | function | 一致 |
| `TunerUtilities.GetParentID` | ERR | nil | function | nil | 预期差异（收尾已复原 include 模块） |
| `InstanceManager.DestroyInstances` | ERR | nil | function | nil | 预期差异（收尾已复原 include 模块） |
| `GameSummary.HasDataSetValues` | function | function | function | function | 一致 |
| `Events.Begin2KLoginProcess` | table | table | table | table | 一致 |
| `TerrainBuilder.SetResourceType` | nil | nil | ERR | nil | 一致 |
| `UnitManager.GetUnitType` | nil | nil | nil | nil | 一致 |
| `PlayerVisibility.IsVisible` | function | function | ERR | nil | 一致 |
| `PlayerVisibility.IsRevealed` | function | function | ERR | nil | 一致 |
| `UI.ZoomMap` | ERR | nil | nil | nil | 一致 |
| `Map.GetImprovementBuilder` | nil | nil | nil | nil | 一致 |
| `Cities.DestroyCity` | function | function | nil | nil | 一致 |
| `Locale.Lookup` | function | function | function | function | 一致 |

**复核结论：17 条一致、2 条预期差异、0 条未预期差异。**（`ERR` 与 `nil` 在语义上都表示「不存在」，差异只来自取值方式不同：扫描器直接索引、复核脚本短路取值。）

---

## 12. 局限性（诚实声明）

1. **单存档、单视角**：本次对局为本地玩家 0（1 座城市、41 个单位、无总督、无未读通知、无进行中外交会话、地图无传送门），因此依赖这些条件的类无法验证（§7 列出 155 条）。
2. **UI 侧以 `InGame` 根上下文为主**，另在 12 个其它 UI 状态复查；**FrontEnd（主菜单/多人大厅）上下文未覆盖**（对局中无法进入），故 `Events.BeginFullGamePurchase`、`Matchmaking.*` 等前端面按「本上下文未见」记录。
3. **只判存在性**：不校验参数个数/类型、返回值、以及「名字存在但调用即报错」的情形；受保护元表（C 侧 `__index`）的成员只能按名索引，无法枚举出「文档未收录但运行时存在」的成员（实例类除外，其方法表可枚举）。
4. **`include` 会改变 UI 状态**：本轮已按白名单最小化并复原，但严格来说扫描后的 InGame 状态与从未扫描过的状态不是逐位相同（重新载入 UI 或重启游戏即完全一致）。
5. 文档基线 `api.sqlite` 自身存在缺陷（§8），因此「不符」条目里既有文档错、也有名字拼接错，报告已尽量区分并给出真名/近似名，但**最终仍应以运行时 CSV 为准**。

