---
name: civ6-tuner
version: "1.0"
author: 千与千寻瀑
license: MIT
category: game-modding
description: 通过文明6 FireTuner 调试接口(TCP:4318)在运行中的对局里执行任意 Lua，用于接口行为/参数/PROPERTY/modifier 的运行时验证、游戏内快速测试、复现脚本报错。探针一律 Write 落盘 --file 投递（零 shell 转义），日志按统一前缀打点 + logs --prefix 提取；内置 GP/UI 端口可用性实测矩阵、API 子集对照与生命周期控制（存读档/无头建局/强推回合）。当静态校验(rgn_validate)无法回答"这个 API 实际行为是什么"、需要查询运行时状态或验证 GP/UI 通信时使用。
---

> ☁ **云端总仓库（合一 monorepo，单 main 分支）**：`https://github.com/nuanyuqingfeng/civ6-modding-skills`
> —— 全部 skill 以 `skills/<skill名>/` 子目录共存于总仓库 **main**；本地镜像工作区 `~/.agents/skills-monorepo/`。
> **上传流程**：① `cd ~/.agents/skills-monorepo && git pull`；② 逐个导出有改动的 skill：`git -C ~/.agents/skills/<skill名> archive HEAD | tar -x -C ~/.agents/skills-monorepo/skills/<skill名>`；③ `git add -A && git commit -m "sync: <说明>" && git push`。网络间歇失败时多重试，或给 git 挂本地代理（Clash 混合端口 `git -c http.proxy=http://127.0.0.1:7897 ...`）。
> **上传判据**：用户明示「上传 / 推送云端」时，无视改动归属统一处理全部有改动的 skill；推送前先 `git ls-remote origin` 检测云端可达且与上述地址匹配，不匹配即停下报告，不得换址推送。

> 🧰 **工具先查名录（硬性）**：要写脚本做某件事之前，先看本 skill 的 [`TOOLS.md`](TOOLS.md)
> —— 本 skill 全部脚本的用途 / 用法 / 路径清单，外加本机**路径收纳**表。
> **有能用的就改它，不要重建。** 新增或改名脚本后，跑一次
> `python "<skills>/civ6-modding/tools/skill_manifest.py" civ6-tuner` 刷新名录（`--check` 可做漂移检测）。

> ⚠ **工程文件写入铁律**：脚本可以新建工程文件，绝不允许改写工程文件。本 skill 的 `tuner_exec.py` 只连 FireTuner 执行 Lua，不写工程文件。真源见 `civ6-modding/SKILL.md` 的「工程文件写入铁律」。

# civ6-tuner：游戏内 Lua 快速测试

## 前置条件

1. 游戏启动且 Options 已勾选 **Tuner**（禁成就；或 `AppOptions.txt` 设 `EnableTuner 1`）
2. **FireTuner GUI 已关闭**——游戏只允许一个 tuner 连接，GUI 占着脚本就连不上
3. **测试需要处于进行中的对局**——主菜单没有 GameCore_Tuner/InGame 状态；
   冷启动或退到主菜单后，用 `gamectl.py load <档名>` 直接进对局（`Network.LoadGame` 在主菜单同样可用）
4. 直启命令（`<Civ6 安装根>` 的本机取值由 `civ6-modding/tools/_paths.py` 解析）：
   `python <skill>/scripts/gamectl.py launch`（自动定位安装路径，不经 PowerShell，
   路径含空格与撇号均安全）
5. 生命周期控制（存/读/重开/杀进程/拉起/无头建局）用 `scripts/gamectl.py`，
   "点击进入"确认界面的按键投递用 `scripts/game_input.py`（PostMessage，不抢焦点）。
6. Python 解释器不在 PATH 时改用 `scripts/tuner_node.js`（Node 内置模块，同一线协议，
   同样的哨兵补齐与迟帧对齐），执行能力与 `tuner_exec.py` 一致。

## ★ 破坏性操作边界（2026-10-03 起，全部实测）

**允许对当前对局执行一切破坏性操作**——灭亡玩家、夷城、删单位、改地形资源、注入/清除
modifier、强制胜负、篡改经济科技——不考虑恢复、不考虑存档完整性，测试效率为唯一优先。
需要干净状态时走重载而不是规避；存档损坏即重开，不抢救。保留的底线只有两条：
不写工程文件（既有铁律）；FireTuner 单连接限制与坏握手防护照旧。

生命周期原语（端别为 tuner 状态名；全部 2026-10-02/03 实机验证）：

| 原语 | 写法 | 备注 |
|---|---|---|
| 存档 | `Network.SaveGame({Name=.., Location=SaveLocations.LOCAL_STORAGE, Type=SaveTypes.SINGLE_PLAYER, FileType=SaveFileTypes.GAME_STATE})` | 返回 true；文件落 `Saves/Single/<Name>.Civ6Save`；传字符串返回 false |
| 读档 | 对局中：`Network.LeaveGame(); Network.LoadGame(同形表, ServerType.SERVER_TYPE_NONE)`；主菜单：直接 `Network.LoadGame`（**主菜单可用**，冷启动即可一条命令进对局） | true=受理；异步重载，完成后停在"点击进入"界面 → **溯源路线优先**：LoadScreen 态可达时直接调官方处理体 `OnActivateButtonClicked()`（LoadScreen.lua:42，核心命令 `Events.LoadScreenClose()`），不可达再 `game_input.py esc` 兜底；完成判定=GameCore_Tuner/InGame 状态重现 |
| 同配置重开 | `Network.RestartGame()` | 重载后 turn=1 |
| 退主菜单 | `Events.ExitToMainMenu()` | 切换期 4318 短暂拒绝连接，轮询重试 |
| 彻底退出 | `gamectl.py kill`（按实际 PID 逐个 `/T /F`，覆盖 DX12 与启动器子进程） | `UI.ExitGame` 在沙箱双态均 nil；按钮真实链路=`Events.UserConfirmedClose()`（一发即退，无弹窗） |
| 拉起 | `gamectl.py launch`（`subprocess.Popen` 直启，自动解析安装路径） | 游戏已在运行时直接拒绝，不再重复拉起；冷启动到菜单约 42 秒 |
| 无头建局 | MainMenu 态八步：`SetToDefaults`→`SetValue("RULESET",nil)`→`BuildHeadlessGameSetup`→`RebuildPlayerParameters(true)`→`GameSetup_RefreshParameters`→`ReleasePlayerParameters`→`HideGameSetup`→`Network.HostGame(SERVER_TYPE_NONE)` | 出处 MainMenu.lua:160-175 |
| 指定领袖 | `PlayerConfigurations[0]:SetLeaderTypeName(lid)`（**复数表**）在八步的 rebuild 之后、host 之前 | 出处 AdvancedSetup.lua:1154 |
| 建城 | snippets/found_city.lua（ingame 侧 `UnitManager.RequestOperation(settler, UnitOperationTypes.FOUND_CITY)`；gamecore 侧发起会抛错） | host-game/无头建局产出标准开局：有开拓者、**无首都**；城市/宫殿/资源/宜居度类探针前先建城（2026-10-05 实测） |
| 启停 mod | `Modding.EnableMod(Modding.GetModHandle(guid), true)` | 出处 Mods.lua:391 |
| 强制过回合 | `UI.RequestAction(ActionTypes.ACTION_ENDTURN, {REASON="UserForced"})` | Shift+Enter 等价（ActionPanel.lua:1098），实测推过被阻塞回合 |
| 结束回合 | `gamectl.py end-turn [--force] [--timeout N]` | 投递 END_TURN + 轮询回合数推进；`--force` 等价上行的 UserForced（2026-10-03 新增） |
| 保存档 | `gamectl.py save <name>` / `load <name>` / `host-game --leader X` | 组合了确认链与轮询 |

## ★ 七条铁律（全部为实测结论）

### 1. `gamecore` / `ingame` 是**独立沙箱 Lua 态**，不是 mod 的 `_ENV`

```
type(Players/Game/Map/GameInfo/Events)           = table   ← 引擎命名空间都在
type(GameEvents)                                 = table   ← 仅 gamecore 可见；UI(ingame) 侧为 nil，见铁律2
type(RGNHasTrait) / type(BUFF_POOL) / type(CTTH_*)  = nil   ← mod 定义的全是 nil
GameEvents.某个mod注册过的事件:Count()               = 0     ← 不同总线实例
```
- ❌ **不能用 tuner 调用 mod 的函数**；`GameEvents.X:Call(...)` 也到不了 mod。
- ✅ tuner 只能：读引擎态（`GameInfo`、PROPERTY、单位/城市字段）、写引擎态、读日志。
- ✅ 要观察 mod 内部行为 → **改 Mods 副本加 `print()` 打点**，再 `logs --grep` 提取。
- ✅✅ **例外（2026-09-16 实测）：mod 自有的 UI 上下文里，mod 的全局函数是可调的。**
  `LSQ:` 列表里那些带 Context 名的条目（如 `AllUnitsFoundCity`）就是 mod 自己那份 UI Lua 的 VM；
  用 `exec --state <Context 名>` 直接投递，`type(ModGlobalFunction)` = **function**、`Controls` 是 mod 的控件表。
  GP 文件同样是独立 context（`Lua_*_RGN` 等：各自 VM、全局互不可见，`include` 的 Core 函数可见）：
  `--state <GP 文件>` 可读该文件全局、调用其注册的函数，并跨文件验证 `LuaEvents` 派发（表格按引用传递，双向活表）。
  ```bash
  # 在 mod 的 UI 上下文里直接调用它自己的检定函数 + 读它的控件状态
  # （--code 单引号包裹；本例代码内无引号字符，符合 --code 安全边界，见「命令速查」）
  T=~/.agents/skills/civ6-tuner/scripts/tuner_exec.py
  python "$T" exec --state AllUnitsFoundCity --code 'print(tostring(AUFCIsButtonHidden(UI.GetHeadSelectedUnit())))'
  ```
  铁律"call 不到 mod"只适用于 `gamecore` / `ingame` 两个沙箱态；能省掉"改 Mods 加 print + 等热重载"的整轮往返。
  ⚠ 反例：GP 态探针里 `UI = nil`（`UI.GetHeadSelectedUnit()` 直接报 `attempt to index a nil value`）→
  跨端通用的探针必须 `UI and UI.GetHeadSelectedUnit()` 这样判空；跨端只有 `EXECUTE_SCRIPT` / `ReportingEvents` / PROPERTY 读取三个通道 → `civ6-modding/reference/context-matrix.md`。

### 2. 两端**总线可见性不同**：`GameEvents` 在 UI 侧整条不存在

| 总线 | GP | UI |
|---|---|---|
| `Events` | table | table |
| **`GameEvents`** | table | **nil** |
| `LuaEvents` / `ReportingEvents` / `ExposedMembers` / `NotificationManager` | table | table |

> 两端的表都在，不等于可以互调：端内跨上下文只有 `LuaEvents`，其余不可达 → `civ6-modding/reference/context-matrix.md`

- 被 UI 加载的文件（含被 UI `include` 的共享库）里出现 `GameEvents.*` → **必然 `attempt to index a nil value`**，并中断该 chunk 使其后语句**全部不执行**。
- `Events.*` 两端都有（安全）；`Events.X=nil` 且 `GameEvents.X=table` 的才是 Lua 级 GP 事件。
- **修法**：把 GP 事件注册**下沉到 GP 初始化入口**（由 GP 脚本调用），UI 侧不注册。
- ⚠ `GameEvents.X` 对任意名字都自动建 table → **不能用 `type(GameEvents.X)` 判断事件是否存在**，只有 `type(Events.X)` 是权威探针。

### 3. `entity:GetProperty(k)` 未设置时返回 **0 个值**（不是 nil）

```lua
-- ❌ 会以 "bad argument #1 to 'tostring' (value expected)" 中断调用方函数
print(string.format("%s", tostring(pPlayer:GetProperty(key))))
-- ✅ 先落局部变量，或包一层（形参天然得到 nil）
local v = pPlayer:GetProperty(key)
local function S(x) if x == nil then return "nil" end return tostring(x) end
print(S(pPlayer:GetProperty(key)))
```

### 4. `Members()` 是 **(key, value) 双返回迭代器**

```lua
for c in Players[0]:GetCities():Members() do ... end       -- ❌ c 是数字 key
for _, c in Players[0]:GetCities():Members() do ... end    -- ✅ c 是城市对象
```
症状：`attempt to index a number value`。项目既有代码统一写 `for _, x in ...:Members()`。

### 5. 判定端口合法性，**必须在调用方所在的那一端实测**

同一方法在不同端可能一个有、一个没有（实测：`Game.GetGreatPeople():GetPastTimeline` = **UI 有 / GP nil**；`CityGrowth:GetAmenitiesNeeded` = **UI 有 / GP nil**；`Game.SetProperty` = **GP 有 / UI nil**；`Player:GetEras()` 子对象链 = **GP 有 / UI nil**，UI 端等价能力是 `Player:GetEra()` 直挂——2026-10-04 两端对照实测，与前三例方向相反）。
**在 GP 测出 nil 不等于"API 不存在"** —— 结论必须写明"在哪一端、测出什么"。用 `exec --both` 或 `ports` 对跑。
端口可用性只决定「这个方法在这一端有没有」，**跨上下文调用函数本身一律不可达**（见 `civ6-modding/reference/context-matrix.md`）。

### 6. 属性改动**立即生效**，但"依赖实体不存在"会给出假阴性

实测：修饰器所依附的实体（如虚拟建筑）存在时，属性置位**同帧**即影响产出（与 Modifier `Amount` 精确吻合），复位精确回基线，**不需要过回合**。
反之若实体不存在 → 属性置位毫无效果 → 会被误判为"功能失效"。**动手前先确认依赖实体存在。**

### 7. 验证「跨端写入」前，先确认**对象层级**（读错层级 = 假阴性）

> 跨端只有 `EXECUTE_SCRIPT`（UI→GP）、`ReportingEvents.SendLuaEvent`（GP→UI 推送）、PROPERTY 读取（双向）三个固定通道，其余任何跨上下文调用函数都不可达 → `civ6-modding/reference/context-matrix.md`。

同一个 `key` 字符串挂在 Game / Player / City / Plot / Unit 上是**不同的属性空间**：

```lua
Game.SetProperty(k, v)           -- Game 层：全 GP 态共享、跨玩家  ← 点号写法，不是 Game:SetProperty
Players[pid]:SetProperty(k, v)   -- Player 层：单玩家
Game.GetProperty(k)              -- 两端可读；但只能读到【Game 层】那个 key
Players[pid]:GetProperty(k)      -- 两端可读；只能读到【Player 层】那个 key
```

实测（2026-09-13）：`RGNSetProperty` 默认 `obj = "Player"`，写入的是 `Players[pid]` 层；
读 `Game.GetProperty(同名 key)` 得 `nil` **≠ 派发失败**。
→ **宣布"写不进去 / 派发没到 / 功能失效"之前，先核对属性挂在哪个层级。** 详见 `reference/PORT_MATRIX.md` 五。

### 附：其它高频坑

| 症状 | 原因与对策 |
|---|---|
| 属性读取批量返回 nil | 在同一 chunk 里对 `GetProperty` 返回的**表做了 `table.sort`**（原地改动污染）。→ 先复制再排序 |
| 同一表达式一次给 10、一次给 0 | 在调用参数里**现拼属性 key**。→ 先把 key 落到局部变量 |
| **"跨端写入没生效"（假阴性）** | **读错了对象层级**：写进 `Players[pid]` 却去读 `Game.GetProperty(同名 key)`。→ 先确认属性挂在 Game / Player / City / Plot / Unit 哪一层（详见 `reference/PORT_MATRIX.md` 五；跨端只有 `EXECUTE_SCRIPT` / `ReportingEvents` / PROPERTY 读取三个通道 → `civ6-modding/reference/context-matrix.md`） |
| **"派发/事件没到"** | ① 读错层级（同上）；② 派发是**异步**的，读太早；③ 注册所在的 GP 态不是派发目标态 → 最稳做法是**借项目已有的生产接收器复测**（见 `snippets/bridge_probe_*.lua`） |
| 探针"没跑"但无报错 | chunk 内抛错会**丢弃整段 stdout**。→ 顶层 `pcall` 包住并打印结果 |
| `--both` 里 UI 段读出空 | GP 段末尾把对照用的探针键**清理掉了**。→ 清理放最后单独跑，或用 `CLEANUP=false` |
| 破坏了游戏状态 | 改属性前**没重新读当前值**（据旧快照改） |
| 误报"发现缺陷" | 异常读数**没做自洽核实**（打印 `plot:GetX()/GetY()`、全量扫描定位真实落点） |
| 误判"事件不触发" | **事件派发有异步窗口**：UI 操作 → 回调之间有延迟。判断必须靠**打点证据**，不能靠"状态没变" |
| GP 探针里 `Locale.Lookup` 报错 | `Locale` 在 **GP 侧为 nil** |
| 同一地块属性出现两次 | `Map.GetPlot(x,y)` 遍历时**坐标横向环绕**（x 差 = 地图宽） |
| `Unit:GetAbilityCount` 测出 nil | 它不在 Unit 上，在 **`Unit:GetAbility()` 返回的对象**上 → 先确认对象对不对（见 `snippets/member_enum.lua`） |

## 命令速查

**Shell 口径与零转义规则（硬性）**：所有示例按 **Git Bash** 口径给出（agent 的 Bash 工具即 Git Bash；PowerShell 下变量语法不同，自行换算）。Lua 代码进入命令行的唯一安全形态是**不含引号字符的单行**（单引号包裹）；凡含引号字符（`"` `'`）或任何嵌套的 Lua 一律先经 Write 工具落盘（UTF-8，内容不经 shell 解析），再 `--file` 投递——探针放 `snippets/`（可复用）或 `workspace/tmp/`（一次性）。不做逐字符转义，不试错。

```bash
T=~/.agents/skills/civ6-tuner/scripts/tuner_exec.py

# ① 每次测试会话第一步：探测连接与对局状态
python "$T" check          # 等价简写: python "$T" --check

# ② 执行 Lua（gamecore = GP 层读写，ingame = UI 层读写）—— 探针一律 --file 投递
python "$T" exec --context gamecore --file <skill>/snippets/property_check.lua
python "$T" exec --context ingame  --file <skill>/snippets/end_turn.lua
python "$T" exec --context gamecore --code 'print(Game.GetCurrentGameTurn())'   # 无引号单行才可用 --code

# ②a' 投递到 mod 自有的 UI 上下文（名字或索引都行；那里 mod 全局可调，见铁律 1 的例外）
python "$T" exec --state AllUnitsFoundCity --file <skill>/snippets/aufc_verify_button.lua
python "$T" exec --state 169 --code 'print(type(AUFCIsButtonHidden))'

# ②b 两端对跑（同脚本各跑一次，输出带 GP/UI 标签，便于直接比对）
python "$T" exec --both --file <skill>/snippets/port_matrix.lua

# ②c 端口矩阵（内置片段，一键双端）
python "$T" ports

# ③ 尾随日志；或按标记精准提取（避开旧会话噪声）。
#   字面前缀过滤优先 --prefix（字面量、脚本内自动正则转义，零转义负担）；
#   确需正则才用 --grep，pattern 单引号包裹
python "$T" logs -n 80
python "$T" logs --since-mark "TUNER|op=xxx|begin" --prefix "TUNER|RGN" -n 0
python "$T" logs --log-file Database.log -n 50

# ④ 生命周期自助（见「破坏性操作边界」节；内部已组合确认链与端口轮询）
python <skill>/scripts/gamectl.py wait [--timeout 120]
python <skill>/scripts/gamectl.py save <档名> | load <档名> | restart | exit-menu
python <skill>/scripts/gamectl.py end-turn [--force] [--timeout 120]   # 结束回合+轮询推进
python <skill>/scripts/gamectl.py kill | launch | close [--save 档名]
python <skill>/scripts/gamectl.py host-game [--leader LEADER_X] [--civ CIVILIZATION_X]
python <skill>/scripts/game_input.py esc     # 向游戏窗口投递 ESC（读档/建局后的"点击进入"）
node <skill>/scripts/tuner_node.js check     # Python 不在 PATH 时的等价回退（Node 内置模块实现）
```

`gamectl.py wait --want inmenu` 以 `MainMenu` 态出现为准：冷启动过程中会短暂出现只有
`Main State` 的两三个状态，那不是可用上下文，等它长成完整菜单再用。

`scripts/tuner_node.js` 是 `tuner_exec.py` 的等价实现（同一线协议、同一持久帧缓冲、
同一超时重同步口径），仅在 Python 解释器不可用时改用；子命令为 `check` / `exec <状态名> <文件>`。


退出码：`0` 成功 / `1` 连接失败或不在对局 / `2` Lua 报错(ERR:) / `3` 超时(未收到哨兵) / `4` 连接被对端关闭。

## 双上下文差异（选错的典型症状是 ERR 或空结果）

| | gamecore（≈ 项目 GP 层） | ingame（≈ 项目 UI 层） |
|---|---|---|
| 可用 | `Players[]`、`GameInfo.*`、`Game.*`、`Map.*` | 以上全部 + `UI.*`、`CityManager`、`UnitManager`、`PlayerOperations`、`LuaEvents` 触发 |
| 用途 | 查库表行、读 PROPERTY、查单位/城市状态、写引擎态 | 下指令（结束回合/购买）、触发 LuaEvents、UI 联动测试 |
| 写权限 | 有（破坏性操作放行，见边界节） | 有 |

## 输出约定

- Lua 内**必须用 `print()`** 输出（return 不回传）；`execute()` 统一补齐哨兵 `---END---`，
  调用方传不传都必然收到终止帧（游戏不会自动追加结束标记）
- 报错以 `ERR:` 回传；超时保留已收集输出
- 接收端按帧长度切分并持久保留残字节，任何一次读超时都不会让后续帧错位
- 片段文件顶部都有 `==== CONFIG ====` 区，执行前按目标修改

## 测试工作流（与 示例工程 双目录联动）

```
改源文件 → 同步 Mods 副本(复制+哈希校验，复制命令按当前 shell 自选 cp/Copy-Item) → gamectl.py 确保对局 → check 探测
→ exec 验证 → logs 查报错 → 结论写回源文件改动 → 循环或交付 → gamectl.py close 收尾
```

- 需要重进对局才能生效的改动（SQL/XML）：`gamectl.py load <档>` 或 `restart`，由本 skill 自助完成，不依赖用户
- 视觉/UI 表现（镜头、浮字、VFX、HUD 完整性、弹窗）可经 `snippets/screenshot.ps1` 截屏判读
  （2026-10-03 实测：表演移镜、传送光柱、ESC 菜单残留均成功判读）；色彩/布局细节仍需用户实机确认

### ★ 改动生效路径速查（2026-10-03 实测，每轮测试前先判据）

| 本轮改了什么 | 生效所需操作 | 说明 |
|---|---|---|
| modinfo **加载动作**（`<File>` 增删 / `LoadOrder` / `Priority` / `<Criteria>` / 动作增删）——**无论什么文件类型** | **`kill` + `launch` + `load`（进程级重启）** | `load` / `restart` 都不重新解析 modinfo；只读档 = 改动静默不生效 |
| 已注册文件的**内部内容**变更（UI / GP / ImportFiles / SQL / XML 均同） | `load` 读档即可 | context 重建时重读 Lua；`UpdateText` 重跑（实测 SQL 文案读档后 `Locale.Lookup` 即更新） |
| 新增物理文件但**未注册**进 modinfo | 永不生效 | `include("前缀_", true)` 不扫磁盘，匹配池只认 `<ImportFiles>` 动作注册的文件 |

**UI 实时热重载（2026-10-03 实测）**：tuner/调试连接下，`AddUserInterfaces` 注册的 UI 主 lua 变更后**数秒内引擎自动 Reload 该 context**（重读主文件并重跑其 include 链，LoadGameViewStateDone 不重放）——每个 context 只监听自己的主文件。GP 与 SQL **无**此机制，必须读档。

**include 通配分片两条路径（分析加载动作时先分清）**：分片放 `ImportFiles/` + 注册 `<ImportFiles>` 动作与 `<Files>` 清单 → 在调用 include 的宿主 context **同一 VM** 展开，函数/全局覆盖 GP 与 UI 都生效；放 `Scripts/` 走 `AddGameplayScripts` → 每个 File 成**独立 context（独立 _ENV）**，与宿主双向隔离，做补丁分片 = 静默失效。同前缀多分片展开顺序：`Priority` 数值大者先（**负数合法**，实测 -10 正常排序在后），无 Priority 按字母序，modinfo 条目排列顺序无影响。
完整机制与实验证据 → `civ6-modding/gotchas.md` §44。
- **收尾流程（硬性）**：测试交付之后一律退出游戏——`gamectl.py close [--save 档名]`
  （可选先存档再 `taskkill`）；唯一例外是用户明确说明保持游戏运行

## 片段库 `<skill>\snippets\`

| 文件 | 用途 | 上下文 |
|------|------|--------|
| `port_matrix.lua` | **GP/UI 端口存在性矩阵**（总线+命名空间+实例方法，只索引不调用） | 双端（`exec --both` / `ports`） |
| `event_matrix.lua` | **事件存在性矩阵**（`Events.*` vs `GameEvents.*`） | 双端 |
| `member_enum.lua` | 摸清某对象的真实成员（对抗"测错对象"与文档不可信） | 双端 |
| `prop_ab.lua` | **PROPERTY 开关 A/B**：验证属性是否立即生效且可逆 | gamecore |
| `property_check.lua` | 玩家/地块 PROPERTY + 金币信仰时代分 | gamecore |
| `dump_props.lua` | **按 `GameInfo` 权威清单批量转储实体属性**（不手写 key，避免漏项）：清单来源可切 `sword`/`list`，目标实体可切 plot/player/game，并反查某前缀下已置位的残留 | 双端（`exec --both`，比对「mod 写的」与「引擎写的」是否一致） |
| `settle_read.lua` | **对抗「重算延迟」的稳定读数**：连读 N 次、两次一致才算稳定（复位未必同帧被下游重算，批量跑会带上一条残留） | gamecore |
| `modifier_probe.lua` | Modifier/RequirementSet 是否入库及挂载链 | gamecore |
| `event_trigger.lua` | 手动触发 LuaEvents 验证通知通路 | ingame |
| `context_channel_probe.lua` | **端内/跨端通道可达性验证**（register → fire → check → unregister 四步）：同端触发时接收器回写可见，跨端触发时回写为 `nil`，用来实证「端内跨上下文只有 `LuaEvents`，其余不可达」→ `civ6-modding/reference/context-matrix.md` | 任意两个 Lua 上下文各投递一次 |
| `bridge_probe_1_register.lua` → `_2_dispatch.lua` → `_3_read.lua` | **UI→GP 派发可达性三连测**（确认 `EXECUTE_SCRIPT` 的 `OnStart` 是否到达你注册的那个 GP 态） | gamecore → ingame → gamecore |
| `cheat_setup.lua` | 造测试条件（金币/信仰/刷兵/科技进度）。⚠ `SetBalance`/`GetBalance` 是错误方法名，正确为 `SetGoldBalance`/`GetGoldBalance`；刷兵块需 gamecore 投递（待重写） | ingame/gamecore |
| `ops_state_snapshot.lua` | **玩家全状态快照**：金/信仰/科技市政/城市(含宜居度 GetAmenities+GetAmenitiesNeeded)/单位清单/回合，一次打尽 | gamecore+ingame |
| `ops_unit_cheats.lua` | 单位操作实测合集：地形校验后刷兵/删兵/传送/回血/满经验/近战攻击模板 | gamecore+ingame |
| `found_city.lua` | **建城原语**：用开拓者发起 FOUND_CITY（host-game/无头建局后无首都，城市相关探针前先跑本片段） | ingame |
| `amenity_watch.lua` | **二进制宜居度监测**（拉古那洛可可机制）：城市宜居度三件套 + 城心地块 13 位 `PROPERTY_RGN_AMENITY_BIT_*` 逐位读取 + 欠账/回执/剧团地块计数 + resid 残差列 | ingame |
| `end_turn.lua` | 结束回合观察跨回合结算（要轮询推进请改用 `gamectl.py end-turn`，内置回合数轮询与 `--force`） | ingame |
| `screenshot.ps1` | **全屏截图**（PowerShell CopyFromScreen，不经 tuner 通道）：判读镜头/浮字/VFX/HUD/弹窗等视觉证据，补齐「视觉无法经 tuner 观察」的盲区 | 宿主机 |
| `sql_like_trap.lua` | **SQL `LIKE ('%A%' OR '%B%')` 陷阱实机复核** —— 等价 `LIKE 0` → 只命中字面量 `'0'` 的行（2026-09 实机复核 627 vs 0）。顺带示范 `DB.Query` 用法（逐条 `pcall` 包住）；⚠ `DB.Query` 在 tuner 沙箱与 mod GP 上下文实测均 nil（2026-10-03），该示范按历史记录保留，SQLite 查询改离线跑 api.sqlite | gamecore |
| `aufc_found_range_probe.lua` | **建城间距检定总探针**：读 `CITY_MIN_RANGE`、`GetNeighborPlots` 环语义（实心盘 n=7/19/37…）、以最近城为中心逐环扫 `IsValidFoundLocation`、逐单位 mod 裁定矩阵 | mod UI 上下文（`--state AllUnitsFoundCity`）；GP 态可跑（UI 段自动跳过） |
| `aufc_verify_button.lua` | **按钮显隐端到端验证**：打印选中单位位置 / 最近城距 / 引擎裁定 / 刷新前后 `Grid.IsHidden`；配 GP 侧 `UnitManager.PlaceUnit(Unit,x,y)` 搬单位即可逐距离段验证 | mod UI 上下文 |

> ⚠ `aufc_found_range_probe.lua` / `aufc_verify_button.lua` 绑定**第三方 mod `AllUnits Found City`**：
> `--state AllUnitsFoundCity` 是它自己的 UI 上下文名，`AUFCIsButtonHidden` / `Controls.AUFCGrid` 也由它提供。
> 没装该 mod 时这两个片段只会打印「不在 mod UI 上下文」而空过（`AllUnitsFoundCity` 不随本 skill 分发、无来源链接）；
> 其余片段与本 skill 全部功能不受影响。

片段中标注【待实测】的 API 未经验证，失败时换方案，勿当作已证实结论上报。
## 坑位清单

```
⚠ 单连接限制：跑脚本前必须关 FireTuner GUI，否则连接被拒
⚠ 坏握手挂死：连接异常后 tuner 可能不恢复——重启游戏是唯一解，及时叫用户
⚠ **`ContextPtr:Reload()`（mod UI 热重载）会把 tuner 连接一起打挂**（2026-09-16 实测：
   在 mod 上下文里投递 `ContextPtr:Reload()` 后，客户端收不到哨兵，
   随后 4318 监听端口**整个从 netstat 消失**，重连一律 `WinError 10061`，游戏本体仍存活。
   → **顺序很重要：先跑完所有 tuner 测试，最后才考虑热重载**；
     或干脆让用户重载对局 / 重启游戏来加载改动。别把热重载夹在两次探针之间。）
⚠ 必须在对局内：check 显示缺 GameCore_Tuner/InGame 即在主菜单
⚠ **改 modinfo 加载动作 = 必须 kill+launch 进程级重启**：`load`/`restart` 都不重新解析 modinfo，只读档 = 改动静默不生效；
   Lua 内容改动读档即可。逐类判据见「测试工作流」的「改动生效路径速查」表，完整机制 → civ6-modding/gotchas.md §44
⚠ 成就禁用：Tuner 开启期间该配置不拿成就，仅测试环境使用
⚠ 日志持久化：%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs
   保留上次游玩记录直到下次启动覆盖
   → 用 `logs --since-mark "<打点加载标志>" --prefix "<前缀>"` 精准取本次会话
   （连接挂了之后 `logs` 仍可用 —— 它是纯文件读取，最后一条证据从这里取）
⚠ 跑 Lua 报错会丢 stdout：chunk 内抛错时已 print 的内容不回传 →
   探针一律用顶层 pcall 包住主逻辑，并把 pcall 结果打出来
⚠ chunk 报错的定位行号 = 你提交的代码行号，但 --file 会带上 BOM/换行差异，
   对不上时先 read 文件核对那一行到底是什么
⚠ UI 侧热重载只重载文件、不重放 LoadGameViewStateDone →
   涉及「面板初始化 / 事件注册」的验证必须重载对局，不能靠热重载
⚠ **`logs --since-mark` 以"最后一次出现"为截取点**：逐行都带标记会退化成只取最后一行
   （2026-10-02 实测）→ 会话标记必须一次性输出，操作行用统一前缀 + grep
⚠ **全局键击误伤**：`keybd_event` 发键命中当前焦点窗口（会把调用方终端打岔）→
   向游戏窗口投递按键一律用 `game_input.py`（PostMessage 到 CivilizationVI.exe 窗口）
⚠ **按键是兜底层不是首选**：每个"用按键省事"的点位都要先溯源到它背后的命令——
   已溯源：读档后"点击进入"= LoadScreen 态 `OnActivateButtonClicked()`（LoadScreen.lua:42，
   ESC 的 OnInput 处理体 :78-88，核心命令 `Events.LoadScreenClose()`）→ gamectl 确认链
   溯源路线优先、按键兜底；Shift+Enter 强制过回合 = `REASON="UserForced"`（已直连）
⚠ **`InitUnit` 不校验地形**：陆军刷到 TERRAIN_COAST 会被引擎清除并留下位置 -9999,-9999
   的僵尸句柄（后续调方法抛 "Not a valid instance"）→ 刷兵前先 `Map.GetPlot` 查地形（2026-10-02）
⚠ **host-game/无头建局没有首都**：产出为标准开局（开拓者+起始单位，无城市）——城市/宫殿/资源/宜居度
   类探针第一步先断言 `GetCapitalCity()` 非空，不存在先用 snippets/found_city.lua 建城；
   FOUND_CITY 须从 ingame 侧发起，gamecore 侧 `RequestOperation` 会抛错（2026-10-05 实测）
⚠ **`PlayerConfigurations` 是复数表**；单数 `PlayerConfiguration` 在前端态为 nil →
   指定领袖用 `PlayerConfigurations[0]:SetLeaderTypeName(lid)`，
   且必须在 RebuildPlayerParameters 之后、HostGame 之前（2026-10-02）
⚠ **tuner 沙箱的枚举/对象是子集**：UnitOperationTypes 缺 SLEEP/SKIP_TURN（用 DB 哈希直调，
   见 OP_CATALOG.md）；Unit 对象的 IsFortified/GetMovement 等方法抛 "Not a valid instance"
   （GetID/GetX/GetDamage/GetUpgradeCost 正常）（2026-10-02）
⚠ **AI 回合处理期间只发 gamecore 查询**：发 InGame 查询（外交会话/UI.CanEndTurn/弹窗关闭）
   会强制上下文切换卡死 AI 外交子系统（civ6-mcp 跨五局实测结论）
⚠ 结束回合被阻塞：`NotificationManager.GetAllEndTurnBlocking()` 读阻塞表 +
   `EndTurnBlockingTypes` 反查名称；空闲单位发 SKIP_TURN（哈希 745019656）；
   推不动就用 REASON="UserForced"（2026-10-02）
⚠ **CINEMATIC 挂起会连锁废掉整套生命周期原语**（2026-10-03 实测）：mod 演出/影片把游戏留在
   CINEMATIC 界面模式且无人按键推进时 → HUD 全隐、`Network.SaveGame` 被拒（true 不落盘 /
   false）、END_TURN 含 UserForced 均失效；`UI.SetInterfaceMode(InterfaceModeTypes.SELECTION)`
   能改回模式值但 HUD 不恢复，画面上无弹窗可关（ESC 无落点）→ 唯一出路是重载对局 / 重启游戏。
   预防：触发可能播片的结算（秒完成 / 召募 / 巨作激活）后投一发 ESC 并核对 `UI.GetInterfaceMode()`
⚠ **沙箱无法建立战争状态**：`Diplomacy:DeclareWarOn` 三种写法（己方侧 reason=0 / 敌方侧 /
   `DB.MakeHash("WAR_REASON_SURPRISE_DECLARED")`）都返回 true 但 `IsAtWarWith` 恒 false，
   `WarReasonTypes` 双端 nil → 需要交战状态的测试只能预置存档，不能现场布阵（2026-10-03）
⚠ **回合阻塞项解码无路**：`GetAllEndTurnBlocking()` 返回**数字 id 数组**；
   `EndTurnBlockingTypes[id]` 反查失败、候选名 `DB.MakeHash` 匹配不上、`DB.Query` 沙箱不可用
   （2026-10-03 残留 id=23669119 未定名）→ 处理靠截图读屏上阻塞原因或 `end-turn --force`
⚠ **沙箱子集比铁律 5 更宽，BuildQueue 也命中**：`BuildQueue:GetTurnsLeft` 在 gamecore 是
   function 但调用抛 "Not Implemented."；`DB.Query` / `WarReasonTypes` / `Game.GetActivePlayer` /
   `UI.IsGamePaused` / `GameConfiguration.GetType` / `ActionTypes.ACTION_QUICK_SAVE` 缺失；
   `BuildQueue:CurrentlyBuilding`/`CreateBuilding` 在 mod GP 上下文可用、`CreateUnit` 不存在
   → 明细与判定法见 `reference/PORT_MATRIX.md` 九（2026-10-03）
⚠ **UI 侧单位集合含幽灵**：`UnitManager.Kill` 后（GP 侧 GetUnits 已无此单位），ingame 的
   `GetUnits():Members()` 仍列出该单位并报旧数值（实测 `GetBuildCharges` 回报 3）→
   单位读数以 gamecore 为准，或 `exec --both` 两端对跑；`ops_state_snapshot.lua` 跑在
   ingame，清单会带幽灵行（2026-10-03）
⚠ **视野查询正确入口 = 全局表 `PlayersVisibility[pid]`**：`player:GetVisibility()` 与
   `Plot:IsRevealed` 两端均 nil（2026-10-04）；`PlayersVisibility[pid]:IsRevealed(idx)` /
   `ChangeVisibilityCount(idx, ±1)` / `GetVisibilityCount(idx)` 可用——±1 净额归 0 但永久揭示
   生效（PHBRevealArea 惯用法，实测 IsRevealed false→true）
⚠ **建造/生产读回 API 子集缺失（GP 上下文 2026-10-04）**：`BuildQueue:GetTurnsLeft` 抛
   "Not Implemented."，`GetGenericBuildingProgress`/`GetQueueLength`/`GetCurrentBuildingType`/
   `CityBuildings:GetBuilding`/`GetNumBuildings`/`City:GetHousing`/`CityGrowth:GetFood` 均 nil；
   `CreateIncompleteBuilding` 对已完成建筑不拒绝、`HasBuilding` 对占位即 true →
   **生产类效果（AddProgress）的数值落点 tuner 侧不可观测**，数值验证改走完成式观测
   （`Techs:SetResearchingTech/GetResearchProgress` 可用；CULTURE/SCIENCE 用 hasCivic/hasTech 完成判定）
⚠ `Map.GetGridWidth/GetGridHeight` GP 端 nil → 用 `Map.GetPlotCount()` + `GetPlotByIndex` 定位远端地块（2026-10-04）
⚠ **"没报错"可作执行成功的证据**：`RGNPCall`（Core_RGN.lua:259）失败必打 `[ERROR][RGN_PCALL]`，从不静默
   → `logs --prefix` 提取无此标记 = 调用链零 Lua 错误；探针打点同步打印 pcall 返回值双确认
   （打点自身注意铁律 3：`tostring(GetProperty(...))` 先落局部变量）
```

## 参考

- `reference/PORT_MATRIX.md` —— **GP/UI 端口可用性实测对照表**（含与 api.sqlite 冲突的条目、审查流程）
  - 五、跨端写入验证先确认**对象层级**（读错层级 = 假阴性；跨端只有 `EXECUTE_SCRIPT` / `ReportingEvents` / PROPERTY 读取三个通道 → `civ6-modding/reference/context-matrix.md`）
  - 六、`Game.SetProperty` 存表保真（平行数组 / 嵌套表 / 空数组 / 负值哨兵）
  - 七、`EXECUTE_SCRIPT` **派发可达性验证配方**（含"借生产接收器做探针"的最稳变体）
  - 八、探针卫生（`--both` 清理时机、chunk 抛错丢 stdout）
  - 九、tuner 沙箱对象子集与状态陷阱
  - 十、视野 / 时代 / 建造读回 API 补充（`PlayersVisibility` 入口、`GetEras` 链 GP 专属、生产落点不可观测清单、`[ERROR][RGN_PCALL]` 错误可见性）


## 协议备注

线格式与握手流程借鉴 [lmwilki/civ6-mcp](https://github.com/lmwilki/civ6-mcp)（MIT）逆向成果：
帧 `[4B LE 长度][4B LE tag][null 结尾 payload]`；tag=4 握手(`APP:`/`LSQ:`)，tag=3 执行
(`CMD:{索引}:{代码}`)；输出前缀 `O\x00<上下文>: `，错误前缀 `ERR:`，哨兵 `---END---`。

---

## 作者与致谢

- 整理人：千与千寻瀑
- 致谢：优妮
