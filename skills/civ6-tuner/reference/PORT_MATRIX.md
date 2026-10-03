# GP / UI 端口可用性对照表（实测）

> 数据来源：2026-09-13 FireTuner 双上下文实测（`gamecore` = GP，`ingame` = UI）。
> 方法：同一份探针脚本两端各跑一次，只做「索引不调用」。
> **本表优先于 `civ6-modding/database/api.sqlite` 的 `availability` 列** —— 已发现文档错漏的条目在下方单列。
> 本表回答「某个名字在这一端是不是 table / function」；**通道口径**（能不能跨上下文调用函数、有哪些固定通道）见 端内跨上下文只有 `LuaEvents`；跨端只有 `EXECUTE_SCRIPT`（UI→GP）、`ReportingEvents.SendLuaEvent`（GP→UI 推送）、PROPERTY 读取（双向）三个固定通道，其余任何跨上下文调用函数都不可达。真源 `civ6-modding/reference/context-matrix.md`。

## 一、总线与命名空间

| 名称 | GP | UI | 说明 |
|---|---|---|---|
| `Events` | table | table | 引擎 GameCoreEvent 总线，两端都有 |
| **`GameEvents`** | table | **nil** | **UI 侧整条总线不存在** → UI 可达代码里任何 `GameEvents.*` 必崩 |
| `LuaEvents` | table | table | **端内跨上下文唯一通道**：UI 上下文互播 / GP 文件互播（表格按引用传递）；不跨端，禁止用它调用其它上下文的函数 → `civ6-modding/reference/context-matrix.md` |
| `ReportingEvents` | table | table | 元素 `SendLuaEvent` 两端都在（GP→UI 推送用） |
| `ExposedMembers` | table | table | GP 同端跨文件（本项目已改用 LuaEvents）；**不该跨端用**。技术可行但不属于固定通道：端内跨上下文只有 `LuaEvents`，其余不可达 → `civ6-modding/reference/context-matrix.md` |
| `NotificationManager` | table | table | — |
| `Locale` | **nil** | table | `Locale.Lookup` 只能在 UI 侧调用 |
| `UI` / `Controls` / `ContextPtr` | **ERR** | table | UI 专有命名空间，GP 侧不存在 |
| `AssetPreview` | **ERR** | table | UI 专有 |
| `ImprovementBuilder` / `TerrainBuilder` / `ResourceBuilder` / `RouteBuilder` | function 级可用 | **ERR** | 命名空间在 UI 侧不存在 |
| `PlayerOperations` | nil | table | UI 下指令用 |

## 二、API 逐项（GP / UI）

| API | GP | UI | 判定 |
|---|---|---|---|
| `Game.SetProperty` | function | **nil** | GP-only |
| `Game.GetProperty` | function | function | Both（UI 可读 Game 属性） |
| `Game.GetRandNum` | function | **nil** | GP-only |
| `Game.GetEras` | function | function | Both |
| `Game.ChangePlayerEraScore` | **nil** | **nil** | **双端都无**；正确用法是 `Game.GetEras():ChangePlayerEraScore(pid, n)` |
| `Game.GetGreatPeople` | function | function | Both（但**成员分端口**，见下） |
| `Player:SetProperty` | function | **nil** | GP-only（UI 写属性必须走 `EXECUTE_SCRIPT`） |
| `Player:GetProperty` | function | function | Both |
| `Player:GetEras` | function | **nil** | GP-only |
| `City:SetProperty` / `City:GetPlot` | function | **nil** | GP-only |
| `CityBuildQueue:CreateBuilding` / `AddProgress` | function | **nil** | GP-only |
| `CityBuildings:RemoveBuilding` | function | **nil** | GP-only |
| **`CityGrowth:GetAmenitiesNeeded` / `GetFood` / `GetGrowthThreshold`** | **nil** | function | **UI-only**（注意它是 `City:GetGrowth()` 的子对象，不是 City 本身） |
| `Plot:SetProperty` | function | **nil** | GP-only |
| `Plot:GetProperty` / `Plot:GetYield` | function | function | Both |
| `Unit:SetProperty` / `SetDamage` / `SetMilitaryFormation` | function | **nil** | GP-only |
| `Unit:GetAbilityCount` / `ChangeAbilityCount` | **nil** | **nil** | **不在 Unit 上**！真身在 `Unit:GetAbility()` 返回的对象（两端都 function） |
| `UnitManager:InitUnit` / `RestoreMovement` / `Kill` / `InitUnitValidAdjacentHex` | function | **nil** | GP-only |
| `CityManager:DestroyDistrict` | function | **nil** | GP-only |
| `GameRandomEvents:ApplyEvent` | function | **nil** | GP-only |
| `Diplomacy:MakePeaceWith` | function | **nil** | GP-only |
| `Religion:ChangeFaithBalance` | function | **nil** | GP-only |
| `PlayerStats:GetNumBeliefsInReligion` | function | **nil** | GP-only |
| `GreatPeoplePoints:GetPointsTotal` | function | function | Both（`Player:GetGreatPeoplePoints()` 的子对象） |
| `UI.PlaySound` / `UI.GridToWorld` / `UI.AddTemporaryPlotVisibility` | **ERR** | function | UI-only |
| `AssetPreview:*` | **ERR** | function | UI-only |
| `GameEffects:GetModifierActive` | function | function | Both |

### `Game:GetGreatPeople()` 的成员**分端口**（典型陷阱）

| 成员 | GP | UI | 语义 |
|---|---|---|---|
| `GetTimeline()` | function | function | **未来/待认领**时间线（实测 9 条，全部 `Claimant=-1`） |
| **`GetPastTimeline()`** | **nil** | function | **过去/已被认领**时间线（实测 1 条，`Claimant=0, Individual=213, TurnGranted=1`） |
| `RecruitPerson` / `GrantPerson` / `CreatePerson` / `IsClassAvailable` | function | **nil** | GP-only（实际授予动作必须在 GP） |
| `CanPatronizePerson` / `CanRecruitPerson` / `CanRejectPerson` / `GetRecruitCost` / `GetPatronizeCost` / `GetRejectCost` | function | function | Both |
| `CountPeopleReceivedByPlayer` / `GetEarnConditionsText` | **nil** | function | UI-only |

> **教训**：`GetPastTimeline` 在 GP 端 `type()` 为 `nil`，很容易误判成"这个 API 不存在"。
> 实际上它存在，只是 **UI-only**。判定端口合法性必须在**调用方所在的那一端**实测。

## 三、与 `api.sqlite` 冲突 / 需注意的条目

| 条目 | api.sqlite | 实测 | 处理 |
|---|---|---|---|
| `Game.GetEras:GetPlayerCurrentScore` | `Availability=UI`，`gp=nil` | 与文档一致 | 时代得分只能从 UI 读 |
| `Game.GetEras:ChangePlayerEraScore` | 文档另有 `Game.ChangePlayerEraScore` 一行 | `Game.ChangePlayerEraScore` 双端皆 nil | 用 `Game.GetEras():ChangePlayerEraScore` |
| `City:GetYield` | 文档签名串行（写成 `GetDistrict`） | 两端口都存在，签名是 `GetYield(yieldIndex)` | 以实测为准 |
| `Unit:SetMilitaryFormation` | 文档挂在 `Player:GetUnits():SetMilitaryFormation` | 真身在 `Unit` 实例 | 用 `api.sqlite.true_path` 校正 |
| `Game.GetGreatPeople:GetPastTimeline` | UI-only（正确） | UI 有 / GP nil | 与文档一致；GP 需要时须由 UI 中继 |

## 四、审查项目代码时的判定流程

```
① 判调用方上下文
   .civ6proj / .modinfo 动作分组：
     <AddGameplayScripts>                        → GP 入口
     <AddUserInterfaces Context=InGame>          → UI 入口
     <ImportFiles>                               → 可被 include 的库（上下文由 include 者决定）
   再沿 include 图传播 —— 注意 include 只让【目标文件的顶层】在该上下文执行，
   函数体要等被调用才算；被两端 include 的共享库需**两端各算一次**。

② 静态筛查（只作候选；假阳性率高）
   用 api.sqlite 的 runtime_gp/runtime_ui 建"方法名→端口"索引比对调用点。
   ⚠ 同名函数、跨文件按名解析会大量误报，**不要直接当结论**。

③ 对应端实测（决定性）
   exec --both / ports，看两端 type()。

④ 报告
   逐条给：文件:行 / 上下文 / API / 两端实测 / 判定。
   不确定就写"不确定"，禁止用假阳性凑数。
```

## 五、跨端写入验证：先确认「对象层级」（实测踩坑，最易误判；跨端只有 `EXECUTE_SCRIPT` / `ReportingEvents` / PROPERTY 读取三个通道 → `civ6-modding/reference/context-matrix.md`）

**同一个 `key` 字符串，挂在不同的对象层级 = 完全不同的两个属性空间。**
验证「UI→GP 写入是否生效」之前，必须先确认目标属性挂在哪一层：

| 层级 | 写入（GP-only） | 读取（两端可读） | 作用域 |
|---|---|---|---|
| Game | `Game.SetProperty(k, v)`（**点号**） | `Game.GetProperty(k)` | 全 GP 态共享、跨玩家 |
| Player | `Players[pid]:SetProperty(k, v)` | `Players[pid]:GetProperty(k)` | 单玩家 |
| City / Plot / Unit | `obj:SetProperty(k, v)` | `obj:GetProperty(k)` | 单实体 |

**实测踩坑（2026-09-13）**：项目里 `RGNSetProperty(playerID, params)` 默认 `params.Object = "Player"`，
真正执行的是 **`Players[playerID]:SetProperty`**。我做"派发可达性"验证时去读 `Game.GetProperty(同名 key)`，
得到 `nil`，一度判定 **"EXECUTE_SCRIPT 派发失败"**；改读 `Players[0]:GetProperty(key)` 立刻拿到 `42` → **PASS**。
→ **教训：读错对象层级 = 假阴性。宣布"写不进去/派发失败"之前，先核对属性挂在哪个层级。**

另注意 `Game.SetProperty` 是**点号**写法（属性表风格）；写成 `Game:SetProperty(k, v)` 会多传 `self`，不是正确形式。

## 六、`Game.SetProperty` 存表保真（2026-09-13 实测，GP 写 → 两端读回逐字段比对）

| 形态 | 结果 |
|---|---|
| 平行数组 `{Individuals={213,214,215}, Claimants={0,1,2}, Turns={1,2,-1}}` | **保真**（`#` 与逐元素值全对） |
| 负值哨兵 `Turns[3] = -1` | **原样保留**（不会变 nil / 0，可安全用作"缺失"标记） |
| 嵌套表 `{Nested = {{Individual=213, Claimant=0}}}` | **保真** |
| 空数组 `{Individuals={}, Claimants={}, Turns={}}` | **保真**（读回仍是空表，非 nil） |
| UI 端读 GP 写入的表 | **完整可读**（实测 `#=3`、值一致） |

> 顶层若是「字符串键 map」，`#t == 0` 属正常现象（不是丢数据）；判内容请看具体字段。
> 结论：**跨端传结构体无需退化到 JSON 字符串**，平行数组 / 嵌套表直接传即可。端内跨上下文只有 `LuaEvents`（表格按引用），跨端经 `ReportingEvents` 送的是副本 → `civ6-modding/reference/context-matrix.md`。

## 七、`EXECUTE_SCRIPT` 派发可达性验证配方（决定性）

目标：确认 UI 发的 `OnStart` 到底有没有到达**你注册处理器的那个 GP 态**。

```
① GP：注册接收器   GameEvents.<OnStart名>.Add(<Fn>)        ← 与项目 RGNCoreInit 同处
② UI：UI.RequestPlayerOperation(Game.GetLocalPlayer(), PlayerOperations.EXECUTE_SCRIPT,
          { OnStart = "<OnStart名>", PropertyKey = "PROPERTY_..._PROBE", Value = 42 })
③ GP：在【正确层级】读属性，== 42 即 PASS
```

- **最稳用法**：借项目里**已有的生产接收器**（如 `RGNSetProperty`）做探针，一次调用即同时证明
  「引擎派发正常」+「该注册点所在的态能收到」，**无需新增任何代码**。
- 机制与 `civ6-modding/gameplay-lua.md` 一致：GP 侧以 `GameEvents.<OnStart>.Add(<Fn>)` 接收，
  签名 `(playerID, params)`。
- ⚠ **不能用 `type(mod函数名)` 判断注册是否生效** —— tuner 的 `gamecore` / `ingame` 是独立沙箱态，
  看不到任何 mod 全局（实测连既有的 `RGNSetProperty` / `HOCUSPushRecordToGP` 都是 `nil`）。
- ⚠ 派发是异步的（下一帧/下一个操作处理点生效）：先留时间再读，别用"立刻读不到"判失败。
- 现成片段：`snippets/bridge_probe_1_register.lua` → `_2_dispatch.lua` → `_3_read.lua`。

## 八、探针卫生（两条硬教训）

1. **不要把"清理探针键"放在 `exec --both` 的 GP 段末尾** —— `--both` 先跑 GP、后跑 UI，
   GP 段清理会把 UI 段要做的「跨端可见性」对照读毁掉，**制造假失败**（实测踩到；跨端只有 `EXECUTE_SCRIPT` / `ReportingEvents` / PROPERTY 读取三个通道 → `civ6-modding/reference/context-matrix.md`）。
   清理要么放在最后一步单独跑，要么用 `CLEANUP=false` 留到对照读之后。
2. **探针主体一律顶层 `pcall` 包住并打印结果** —— chunk 内抛错时已 `print` 的内容**整段不回传**，
   会让你误以为"脚本没跑"。典型触发：`tostring(x:GetProperty(k))` 在未设置时抛
   `bad argument #1 to 'tostring' (value expected)`。

## 九、tuner 沙箱对象子集与状态陷阱（2026-10-03 实测补充）

> 铁律 5 的延伸：除顶层命名空间外，**沙箱暴露的对象方法同样是不完整子集**，且 `type=function` 不保证可调用。
> 「gamecore 沙箱」指 `exec --context gamecore`；「mod GP 上下文」指 `exec --state <GP 文件>` 的完整 GP 环境。

| 名称 | gamecore 沙箱 | mod GP 上下文 | 备注 |
|---|---|---|---|
| `DB.Query` | **nil** | **nil** | `snippets/sql_like_trap.lua` 注释所称「gamecore 可用」未在沙箱复现；SQLite 查询改离线跑 `civ6-modding/database/*.sqlite` |
| `BuildQueue:GetTurnsLeft` | function，**调用抛 "Not Implemented."** | — | `type=function` 不等于可调用 |
| `BuildQueue:CurrentlyBuilding` / `CreateBuilding` | 未逐测 | function | 生产查询 / 排建筑走 mod GP 上下文 |
| `BuildQueue:CreateUnit` | — | **nil** | 排单位只能 `UnitManager.InitUnit`（GP-only） |
| `Game.GetActivePlayer` / `GameConfiguration.GetType` | **nil** | — | 调用即 `attempt to index/call nil` |
| `UI.IsGamePaused` / `UI.CanEndTurn` | — | CanEndTurn=function / IsGamePaused=**nil** | |
| `WarReasonTypes` | **nil** | **nil** | 双端缺失 → 宣战不可行 |
| `Diplomacy:DeclareWarOn` | 返回 true 但 **`IsAtWarWith` 恒 false** | 同 | 己方侧 reason=0 / 敌方侧 / `DB.MakeHash` 哈希三种形态一致假成功 |
| `ActionTypes.ACTION_QUICK_SAVE` | — | **nil** | 快速保存动作不可用 |
| `Network.SaveGame`（ingame） | — | function | **卡死会话（CINEMATIC 挂起等）下被拒**：true 不落盘 / false；重启游戏后恢复 |
| `NotificationManager.GetAllEndTurnBlocking()` | 返回**数字 id 数组** | 同 | 元素是 number，`EndTurnBlockingTypes[id]` 反查失败；无 `DB.Query`、候选名哈希匹配不上 → 解码无路（残留 id=23669119 未定名） |

**UI 幽灵单位**：`UnitManager.Kill` 之后（GP 侧 `GetUnits()` 已无此单位），ingame 侧
`GetUnits():Members()` 仍会列出该单位并回报旧值（实测 `GetBuildCharges` 回报早已清零前的 3）——
UI 集合是缓存视图。**单位读数以 gamecore 为准**，或 `exec --both` 两端对跑当场现形。

## 十、视野 / 时代 / 建造读回 API 补充（2026-10-04 菲比礼物 21 项实测）

> 实测载体：菲比的礼物全部效果 tuner 主动调用（mod GP 上下文 `--state <GP 文件>`），
> 18 项数值/状态精确验证；PRODUCTION 落点因下表读回缺失不可观测。
> 教训：**写探针前先查本表第二节**——`Player:GetEras` GP-only 早有记录，本轮仍因从 GP 文件
> 抄探针写法投到 UI 上下文而踩中（N 批两端对照复核确认）。

### 视野（揭示效果的正确读回路径）

| API | GP | UI | 备注 |
|---|---|---|---|
| 全局表 `PlayersVisibility` | table | — | **正确的视野入口**；`player:GetVisibility()` 与 `Plot:IsRevealed` / `IsVisible` 两端均 nil，勿用 |
| `PlayersVisibility[pid]:IsRevealed(idx)` | function | — | 远端地块 false → 调揭示后 true（直接读回验证，2026-10-04） |
| `PlayersVisibility[pid]:ChangeVisibilityCount(idx, ±1)` | function | — | +1 再 -1 净额归 0，永久揭示生效（惯用法，PHBRevealArea 同款） |
| `PlayersVisibility[pid]:GetVisibilityCount(idx)` | function | — | 净额读数 |

### Player 时代 API（两端挂法不同的复核与工程现状）

| API | GP | UI | 备注 |
|---|---|---|---|
| `Player:GetEras()`（子对象链） | function ✓ | **nil** | 第二节既有记录，N 批复核一致 |
| `Player:GetEra()`（直挂） | function ✓ | function ✓ | **双端等价能力，双端代码一律用这个** |

工程现状自洽核查（2026-10-04 grep）：双端/UI 路径（`Core_Phoebe_Gift` 146/1567/1575、
`Core_Ciaccona` 132）用直挂；GP 专用路径（`Lua_Phoebe_RGN:124`、`Lua_Hocus_RGN:681`、
`Core_SwordSystem:701` 自标 GP only）用链。共享库 `RGNGetEraMultiplier`（Core_RGN.lua:241）
用链且全工程**零调用者**——若将来从 UI 端调用会崩，调用前先核端。

### 建造/生产读回（tuner 侧不可观测清单，mod GP 上下文实测）

| API | 实测结果 |
|---|---|
| `CityBuildQueue:GetTurnsLeft` | function，调用抛 "Not Implemented."（与第九节一致） |
| `CityBuildQueue:GetGenericBuildingProgress` / `GetProgress` / `GetQueueLength` / `GetCurrentBuildingType` | nil |
| `CityBuildings:GetBuilding` / `GetNumBuildings` | nil |
| `City:GetHousing` | nil（`CityGrowth:GetFoodSurplus` 可用、`GetFood` nil；surplus 对照受临河约束干扰，勿作生产判据） |
| `CityBuildQueue:CreateIncompleteBuilding(bIdx, plotIdx)` | 可用；**对已完成建筑不拒绝** → 不能当完成判据 |
| `CityBuildings:HasBuilding` | 对 incomplete 占位即 true → 无法区分完成度 |
| `Techs:SetResearchingTech` / `GetResearchProgress` / `GetResearchCost` / `GetTurnsLeft` | 全部可用 ✓（SCIENCE 类验证替代通道：选中科技 → 差分/完成判定） |
| `PlayerStats:GetTurnYield` / `GetTotalYield` / `GetLifetimeYield`、`PlayerCulture:GetCivicProgress` | nil（CULTURE 改用 `hasCivic` 完成式观测） |
| `Map.GetGridWidth` / `GetGridHeight` | GP 端 nil；定位远端地块用 `Map.GetPlotCount()` + `GetPlotByIndex` |

→ **结论**：`AddProgress` 类生产效果的数值落点在 tuner 侧不可观测（写入无错误、读回全缺、
占位夹具无法当生产项）。数值验证改走完成式观测（科技/市政 hasTech/hasCivic、资源/国库差分）。

### 错误可见性（"没报错"的证据效力）

`RGNPCall`（Core_RGN.lua:259-265）失败时**必然**打印 `[ERROR][RGN_PCALL] <tag> <错误>`，从不静默。
探针打点同步打印 pcall 返回值（如 `applied ok=true`）→ 日志无 `[ERROR][RGN_PCALL]` 且 ok=true
双重成立时，「调用链零 Lua 错误」可直接作为结论依据。打点自身注意铁律 3：
`tostring(GetProperty(...))` 会因 0 返回值抛 "value expected"，先落局部变量（2026-10-04 实踩复现）。
