---
name: civ6-tuner
description: 通过文明6 FireTuner 调试接口(TCP:4318)在运行中的对局里执行任意 Lua，用于接口行为/参数/PROPERTY/modifier 的运行时验证、游戏内快速测试、复现脚本报错。当静态校验(rgn_validate)无法回答"这个 API 实际行为是什么"、需要查询运行时状态或验证 GP/UI 链路时使用。
---

# civ6-tuner：游戏内 Lua 快速测试

## 前置条件（不满足时明确告知用户需要做什么）

1. 游戏启动且 Options 已勾选 **Tuner**（禁成就；或 `AppOptions.txt` 设 `EnableTuner 1`）
2. **FireTuner GUI 已关闭**——游戏只允许一个 tuner 连接，GUI 占着脚本就连不上
3. **处于进行中的对局**——主菜单没有 GameCore_Tuner/InGame 状态
4. 直启命令（用户已验证可用）：
   `& "F:\Steam\steamapps\common\Sid Meier's Civilization VI\Base\Binaries\Win64Steam\CivilizationVI.exe"`

## ★ 七条铁律（不知道任意一条都会白费数轮；全部为实测结论）

### 1. `gamecore` / `ingame` 是**独立沙箱 Lua 态**，不是 mod 的 `_ENV`

```
type(Players/Game/Map/GameInfo/Events/GameEvents) = table   ← 引擎命名空间都在
type(RGNHasTrait) / type(BUFF_POOL) / type(CTTH_*)  = nil   ← mod 定义的全是 nil
GameEvents.某个mod注册过的事件:Count()               = 0     ← 不同总线实例
```
- ❌ **不能用 tuner 调用 mod 的函数**；`GameEvents.X:Call(...)` 也到不了 mod。
- ✅ tuner 只能：读引擎态（`GameInfo`、PROPERTY、单位/城市字段）、写引擎态、读日志。
- ✅ 要观察 mod 内部行为 → **改 Mods 副本加 `print()` 打点**，再 `logs --grep` 提取。

### 2. 两端**总线可见性不同**：`GameEvents` 在 UI 侧整条不存在

| 总线 | GP | UI |
|---|---|---|
| `Events` | table | table |
| **`GameEvents`** | table | **nil** |
| `LuaEvents` / `ReportingEvents` / `ExposedMembers` / `NotificationManager` | table | table |

- 被 UI 加载的文件（含被 UI `include` 的共享库）里出现 `GameEvents.*` → **必然 `attempt to index a nil value`**，并中断该 chunk 使其后语句**全部不执行**。
- `Events.*` 两端都有（安全）；`Events.X=nil` 且 `GameEvents.X=table` 的才是 Lua 级 GP 事件。
- **修法不是加守卫**：把 GP 事件注册**下沉到 GP 初始化入口**（由 GP 脚本调用），UI 侧不注册。
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

同一方法在不同端可能一个有、一个没有（实测：`Game.GetGreatPeople():GetPastTimeline` = **UI 有 / GP nil**；`CityGrowth:GetAmenitiesNeeded` = **UI 有 / GP nil**；`Game.SetProperty` = **GP 有 / UI nil**）。
**在 GP 测出 nil 不等于"API 不存在"** —— 结论必须写明"在哪一端、测出什么"。用 `exec --both` 或 `ports` 对跑。

### 6. 属性改动**立即生效**，但"依赖实体不存在"会给出假阴性

实测：修饰器所依附的实体（如虚拟建筑）存在时，属性置位**同帧**即影响产出（与 Modifier `Amount` 精确吻合），复位精确回基线，**不需要过回合**。
反之若实体不存在 → 属性置位毫无效果 → 会被误判为"功能失效"。**动手前先确认依赖实体存在。**

### 7. 验证「跨端写入」前，先确认**对象层级**（读错层级 = 假阴性）

同一个 `key` 字符串挂在 Game / Player / City / Plot / Unit 上是**不同的属性空间**：

```lua
Game.SetProperty(k, v)           -- Game 层：全 GP 态共享、跨玩家  ← 点号写法，不是 Game:SetProperty
Players[pid]:SetProperty(k, v)   -- Player 层：单玩家
Game.GetProperty(k)              -- 两端可读；但只能读到【Game 层】那个 key
Players[pid]:GetProperty(k)      -- 两端可读；只能读到【Player 层】那个 key
```

实测（2026-09-13）：项目 `RGNSetProperty` 默认 `obj = "Player"`，实际写的是 `Players[pid]:SetProperty`；
验证时我去读 `Game.GetProperty(同名 key)` 得到 `nil`，**一度判定"EXECUTE_SCRIPT 派发失败"**，
改读 `Players[0]:GetProperty(key)` 立刻拿到正确值 → PASS。
→ **宣布"写不进去 / 派发没到 / 功能失效"之前，先核对属性挂在哪个层级。** 详见 `reference/PORT_MATRIX.md` 五。

### 附：其它高频坑（一次踩到就浪费数轮）

| 症状 | 原因与对策 |
|---|---|
| 属性读取批量返回 nil | 在同一 chunk 里对 `GetProperty` 返回的**表做了 `table.sort`**（原地改动污染）。→ 先复制再排序 |
| 同一表达式一次给 10、一次给 0 | 在调用参数里**现拼属性 key**。→ 先把 key 落到局部变量 |
| **"跨端写入没生效"（假阴性）** | **读错了对象层级**：写进 `Players[pid]` 却去读 `Game.GetProperty(同名 key)`。→ 先确认属性挂在 Game / Player / City / Plot / Unit 哪一层（详见 `reference/PORT_MATRIX.md` 五） |
| **"派发/事件没到"（需先排除）** | ① 读错层级（同上）；② 派发是**异步**的，读太早；③ 注册所在的 GP 态不是派发目标态 → 最稳做法是**借项目已有的生产接收器复测**（见 `snippets/bridge_probe_*.lua`） |
| 探针"没跑"但无报错 | chunk 内抛错会**丢弃整段 stdout**。→ 顶层 `pcall` 包住并打印结果 |
| `--both` 里 UI 段读出空 | GP 段末尾把对照用的探针键**清理掉了**。→ 清理放最后单独跑，或用 `CLEANUP=false` |
| 破坏了游戏状态 | 改属性前**没重新读当前值**（据旧快照改） |
| 误报"发现缺陷" | 异常读数**没做自洽核实**（打印 `plot:GetX()/GetY()`、全量扫描定位真实落点） |
| 误判"事件不触发" | **事件派发有异步窗口**：UI 操作 → 回调之间有延迟。判断必须靠**打点证据**，不能靠"状态没变" |
| GP 探针里 `Locale.Lookup` 报错 | `Locale` 在 **GP 侧为 nil** |
| 同一地块属性出现两次 | `Map.GetPlot(x,y)` 遍历时**坐标横向环绕**（x 差 = 地图宽） |
| `Unit:GetAbilityCount` 测出 nil | 它不在 Unit 上，在 **`Unit:GetAbility()` 返回的对象**上 → 先确认对象对不对（见 `snippets/member_enum.lua`） |

## 命令速查

```powershell
$T = "%USERPROFILE%\.agents\skills\civ6-tuner\scripts\tuner_exec.py"

# ① 每次测试会话第一步：探测连接与对局状态
python $T check          # 等价简写: python $T --check

# ② 执行 Lua（gamecore = GP 层只读，ingame = UI 层读写）
python $T exec --context gamecore --code "print(Game.GetCurrentGameTurn())"
python $T exec --context ingame  --file <skill>/snippets/end_turn.lua

# ②b 两端对跑（同脚本各跑一次，输出带 GP/UI 标签，便于直接比对）
python $T exec --both --file <skill>/snippets/port_matrix.lua

# ②c 端口矩阵（内置片段，一键双端）
python $T ports

# ③ 尾随日志；或按标记+正则精准提取（避开旧会话噪声）
python $T logs -n 80
python $T logs --since-mark "打点版已加载" --grep "QJ|Runtime Error" -n 0
python $T logs --log-file Database.log -n 50
```

退出码：`0` 成功 / `1` 连接失败或不在对局 / `2` Lua 报错(ERR:) / `3` 超时。

## 双上下文差异（选错的典型症状是 ERR 或空结果）

| | gamecore（≈ 项目 GP 层） | ingame（≈ 项目 UI 层） |
|---|---|---|
| 可用 | `Players[]`、`GameInfo.*`、`Game.*`、`Map.*` | 以上全部 + `UI.*`、`CityManager`、`UnitManager`、`PlayerOperations`、`LuaEvents` 触发 |
| 用途 | 查库表行、读 PROPERTY、查单位/城市状态 | 下指令（结束回合/购买）、触发 LuaEvents、UI 联动测试 |
| 只读性 | 约定只读 | 有写权限 |

## 输出约定

- Lua 内**必须用 `print()`** 输出（return 不回传）；脚本自动追加哨兵 `---END---`
- 报错以 `ERR:` 回传并置退出码 2；超时置退出码 3 并保留已收集输出
- 片段文件顶部都有 `==== CONFIG ====` 区，执行前按目标修改

## 测试工作流（与 示例工程 双目录联动）

```
改源文件 → 同步 Mods 副本(Copy-Item+哈希校验) → 用户进对局 → check 探测
→ exec 验证 → logs 查报错 → 结论写回源文件改动 → 循环或交付
```

- 需要重进对局才能生效的改动（SQL/XML）：请用户重启游戏或读档，不要反复盲试
- 视觉/UI 表现无法经此通道观察，需用户看画面确认

## 片段库 `<skill>\snippets\`

| 文件 | 用途 | 上下文 |
|------|------|--------|
| `port_matrix.lua` | **GP/UI 端口存在性矩阵**（总线+命名空间+实例方法，只索引不调用） | 双端（`exec --both` / `ports`） |
| `event_matrix.lua` | **事件存在性矩阵**（`Events.*` vs `GameEvents.*`） | 双端 |
| `member_enum.lua` | 摸清某对象的真实成员（对抗"测错对象"与文档不可信） | 双端 |
| `prop_ab.lua` | **PROPERTY 开关 A/B**：验证属性是否立即生效且可逆 | gamecore |
| `property_check.lua` | 玩家/地块 PROPERTY + 金币信仰时代分 | gamecore |
| `modifier_probe.lua` | Modifier/RequirementSet 是否入库及挂载链 | gamecore |
| `event_trigger.lua` | 手动触发 LuaEvents 验证通知链路 | ingame |
| `bridge_probe_1_register.lua` → `_2_dispatch.lua` → `_3_read.lua` | **UI→GP 派发可达性三连测**（确认 `EXECUTE_SCRIPT` 的 `OnStart` 是否到达你注册的那个 GP 态） | gamecore → ingame → gamecore |
| `cheat_setup.lua` | 造测试条件（金币/信仰/刷兵/科技进度） | ingame |
| `end_turn.lua` | 结束回合观察跨回合结算 | ingame |
| `sql_like_trap.lua` | **SQL `LIKE ('%A%' OR '%B%')` 陷阱实机复核** —— 括号表达式求值为整数 `0`（`typeof`=`integer`），等价 `LIKE 0` → 只命中字面量 `'0'` 的行；真实库对照 627 vs 0。顺手示范 `DB.Query` 在 gamecore 的正确用法（逐条 `pcall` 包住，避免一处报错丢全部输出） | gamecore |

片段中标注【待实测】的 API 未经验证，失败时换方案，勿当作已证实结论上报。
端口可用性的**权威对照表**见 `reference/PORT_MATRIX.md`（本次实测，含与 api.sqlite 冲突的条目）。

## 坑位清单

```
⚠ 单连接限制：跑脚本前必须关 FireTuner GUI，否则连接被拒
⚠ 坏握手挂死：连接异常后 tuner 可能不恢复——重启游戏是唯一解，及时叫用户
⚠ 必须在对局内：check 显示缺 GameCore_Tuner/InGame 即在主菜单
⚠ 成就禁用：Tuner 开启期间该配置不拿成就，仅测试环境使用
⚠ 日志持久化：%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\Logs
   保留上次游玩记录直到下次启动覆盖——看报错注意时间戳区分新旧
   → 用 `logs --since-mark "<打点加载标志>" --grep "<前缀>"` 精准取本次会话
⚠ 跑 Lua 报错会丢 stdout：chunk 内抛错时已 print 的内容不回传 →
   探针一律用顶层 pcall 包住主逻辑，并把 pcall 结果打出来
⚠ chunk 报错的定位行号 = 你提交的代码行号，但 --file 会带上 BOM/换行差异，
   对不上时先 read 文件核对那一行到底是什么
⚠ UI 侧热重载只重载文件、不重放 LoadGameViewStateDone →
   涉及「面板初始化 / 事件注册」的验证必须重载对局，不能靠热重载
```

## 参考

- `reference/PORT_MATRIX.md` —— **GP/UI 端口可用性实测对照表**（含与 api.sqlite 冲突的条目、审查流程）
  - 五、跨端写入验证先确认**对象层级**（读错层级 = 假阴性）
  - 六、`Game.SetProperty` 存表保真（平行数组 / 嵌套表 / 空数组 / 负值哨兵）
  - 七、`EXECUTE_SCRIPT` **派发可达性验证配方**（含"借生产接收器做探针"的最稳变体）
  - 八、探针卫生（`--both` 清理时机、chunk 抛错丢 stdout）


## 协议备注

线格式与握手流程借鉴 [lmwilki/civ6-mcp](https://github.com/lmwilki/civ6-mcp)（MIT）逆向成果：
帧 `[4B LE 长度][4B LE tag][null 结尾 payload]`；tag=4 握手(`APP:`/`LSQ:`)，tag=3 执行
(`CMD:{索引}:{代码}`)；输出前缀 `O\x00<上下文>: `，错误前缀 `ERR:`，哨兵 `---END---`。
