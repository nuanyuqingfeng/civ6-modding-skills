# Lua 上下文与通信矩阵（唯一真源）

> 本文件是「Lua 上下文」「跨上下文」「跨端」三个词的**唯一真源**。
> 家族其余文件只保留一句结论 + 指向本文件的短指针，不重复维护矩阵。
> 结论全部来自 FireTuner 实测（`civ6-tuner`，TCP 4318，进行中的对局）与官方原文，逐条附实测编号，见第五节。

---

## 一、术语（先看这一节）

| 词 | 含义 |
|---|---|
| **Lua 上下文** | 一段 Lua 代码运行时所在的独立状态。每个 UI 上下文（`<Context Name="X">` 对应的同名 `.lua`）是一个 Lua 上下文；每个 GP 脚本（`AddGameplayScripts` 列表里的 `.lua`）也是一个 Lua 上下文 |
| **端内跨上下文** | 同一端内两个 Lua 上下文之间：UI 上下文 ↔ UI 上下文、GP 脚本 ↔ GP 脚本 |
| **跨端** | UI 侧与 GP 侧之间 |
| **include 闭包** | 文件 A `include("B")` 后，B 的顶层在 A 所在的 Lua 上下文里执行，B 定义的函数成为 A 的全局。闭包按加载顺序传递，运行期无法再增加 |
| 对话上下文 | LLM 会话窗口，与本文件无关 |
| tuner 投递目标 | FireTuner 的 `--state <名字>` 指向某一个 Lua 上下文，用于把探针送进那个上下文内部执行 |

本文件里出现的「上下文」只指 Lua 上下文。

---

## 二、可见性三条规则

1. **全局互不可见。** A 上下文里定义的函数、变量、表格，B 上下文读到的是 `nil`。跨端如此，同端跨上下文同样如此。
2. **加载期唯一共享手段是 `include()`。** 被包含文件的顶层在包含者的上下文里执行一次，**每个包含者各持一份副本**；在某个上下文里改写被包含进来的函数，不影响别的上下文。
3. **运行期通信只能走下表的固定通道。** 除此以外任何「在 A 里调用 B 的函数」的写法都不可达。

---

## 三、通信矩阵（权威表）

端内跨上下文只有 `LuaEvents`；跨端只有 `EXECUTE_SCRIPT`（UI→GP）、`ReportingEvents.SendLuaEvent`（GP→UI 推送）、PROPERTY 读取（双向）三个固定通道；其余任何跨上下文调用函数都不可达。真源 `reference/context-matrix.md`。

| # | 调用方 | 目标 | 直接调用函数 | 允许的通道 | 传参与返回 |
|---|---|---|---|---|---|
| 1 | UI 上下文 | 同端另一 UI 上下文 | ❌ 不可达 | `LuaEvents.X.Add(fn)` 注册，`LuaEvents.X(参数)` 触发 | 表格**按引用**，handler 回写调用方立即可读；同步 |
| 2 | GP 脚本 | 同端另一 GP 脚本 | ❌ 不可达 | 同第 1 行 | 同第 1 行 |
| 3 | UI 上下文 | GP 脚本（动作） | ❌ 不可达 | `UI.RequestPlayerOperation(pid, PlayerOperations.EXECUTE_SCRIPT, { OnStart = "名字", ... })`；GP 侧 `GameEvents.名字.Add(fn)` | 无同步返回值 |
| 4 | GP 脚本 | UI 上下文（推送） | ❌ 不可达 | `ReportingEvents.SendLuaEvent("名字", 参数)`；UI 侧 `LuaEvents.名字.Add(fn)` | 表格**按值**（接收方拿到副本）；单向 |
| 5 | 任意上下文 | 另一端（推送） | ❌ 不可达 | 同第 4 行 | 同第 4 行。`ReportingEvents` 的两端表是同一个实例，广播域是「全部 UI 上下文」，GP 侧不参与 |
| 6 | 任意上下文 | PROPERTY（读取） | — | `Players[id]:GetProperty("KEY")` / `pPlot:GetProperty("KEY")`；共享读取函数放 Core 文件，两端各自 `include` | 同步读取 |
| 7 | GP 脚本 | PROPERTY（写入） | — | `Game:SetProperty(key, v)` / `pPlayer:SetProperty(key, v)` | 同帧生效 |
| 8 | UI 上下文 | PROPERTY（写入） | ❌ `SetProperty` 在 UI 侧为 `nil` | 只能经第 3 行的 `EXECUTE_SCRIPT` 交给 GP 侧写入 | — |
| 9 | UI 上下文 | GP 全局函数（需要同步返回值） | ❌ 不可达 | 暴露函数 `ExposedMembers`（**技术可行**，实测双向可读可调；使用策略见下） | 同步 |
| 10 | 其它任意组合 | — | ❌ 不可达 | 无 | 报错原文见第四节 |

**`LuaEvents` 与 `ReportingEvents` 是两套东西，接收端写法相同、触发端不同**：接收端都写 `LuaEvents.名字.Add(fn)`，只看 `.Add` 判断不出来源，必须看触发端那一行。

**第 9 行的策略口径**（工程私有约定，优先于技术矩阵）：按钮触发的 UI→GP 调用**只允许**走 `EXECUTE_SCRIPT`；非按钮的被动触发、且需要跨端拿到同步返回值时，才允许使用暴露函数，且**使用前须经用户首肯**（每会话授权一次），此外尽量少开。

---

## 四、症状对照表（按报错原文检索也能落到这里）

| 现象 / 报错原文 | 病因 | 处置 |
|---|---|---|
| `attempt to call a nil value`（点调用）或 `function expected instead of nil`（冒号调用） | 在另一个 Lua 上下文里调用了该函数，它在当前上下文是 `nil` | 改用第三节对应行的通道；共享代码放进 Core 文件由两端各自 `include` |
| `attempt to index a nil value (global 'GameEvents')` | UI 侧用了 `GameEvents.*`，整条为 `nil`，并中断该 chunk 使其后语句全部不执行 | 把 GP 事件注册下沉到 GP 脚本 |
| UI 收不到 GP 的通知 | GP 侧写了 `LuaEvents.X(参数)` | 改用 `ReportingEvents.SendLuaEvent`（第 4 行） |
| GP 收不到 UI 的动作 | UI 侧直接调用了 GP 函数 | 改用 `EXECUTE_SCRIPT`（第 3 行） |
| UI 侧 `SetProperty` 报 `function expected instead of nil` | UI 侧没有 `SetProperty` 端口 | 经 `EXECUTE_SCRIPT` 交给 GP 侧写入（第 8 行） |
| handler 回写的值调用方读不到 | 该表格是经 `ReportingEvents` 跨端送来的副本 | 跨端不依赖回写；需要回写就用端内 `LuaEvents`（第 1、2 行） |
| 改了 Core 文件里的函数，只有一部分地方行为变了 | include 的每个包含者各持一份副本 | 改被包含的源文件本身，运行期改写不会传播 |

---

## 五、实测记录（2026-09-26）

工具：`python <skills>/civ6-tuner/scripts/tuner_exec.py exec --state <上下文名> --file <探针>`。
上下文取值：GP = `Lua_Cartethyia_RGN` / `Lua_CuddleJump_RGN`；UI = `Cartethyia_Sword_MainPanel` / `CuddleJump`。

| 编号 | 验证内容 | 观察值 | 结论 |
|---|---|---|---|
| F1 | 在 GP 接收方注册 `LuaEvents.__RGNCTXPROBE.Add`，由**另一 GP 文件**触发 | 触发返回后 `t.written_by_receiver=true`；接收方 `seen=1` | 第 2 行成立，表格按引用 |
| F2 | 由 **UI** 触发同名 `LuaEvents.__RGNCTXPROBE` | `t.written_by_receiver=nil`；接收方 `seen` 仍为 1 | 跨端不达 |
| F3 | 在 UI 接收方注册，由**另一 UI 上下文**触发 | `t.written_by_receiver=true`；接收方 `seen=1` | 第 1 行成立 |
| F4 | 接收方 `.Remove(handler)` 后再触发 | 计数不变 | `.Remove` 生效 |
| F5 | 在 UI 上下文查询 GP 文件定义的全局函数 | `type(__RGNCTX_GPFN)=nil` | 规则 1 |
| F6 | 在 UI 上下文调用 GP 定义的全局函数 | `function expected instead of nil` | 症状表第 1 行 |
| F7 | GP 侧 `ReportingEvents.SendLuaEvent` → UI 侧 `LuaEvents` 接收 | 触发方 `t.seen_by_receiver=nil`；接收方 `rseen=1` | 第 4 行成立；跨端为副本、无回写 |
| F8 | `ExposedMembers` 双向：GP 写表与函数 → UI 读并调用；UI 写表与函数 → GP 读并调用 | 两侧均 `table` / `function`，调用返回 `99` / `77` | 第 9 行技术可行 |
| F9 | GP 侧 `Players[0]:SetProperty("__RGNCTXPROP", 123)` → UI 侧 `GetProperty` | UI 读到 `123` | 第 6 行成立 |
| F10 | UI 侧 `Players[0]:SetProperty(...)` | 报 `function expected instead of nil`；端口表：UI 侧 `SetProperty=nil` / `GetProperty=function`，GP 侧两者都是 `function` | 第 8 行成立 |
| F11 | UI 侧 `ReportingEvents.SendLuaEvent` → UI 侧接收；以及 GP 侧注册同一事件名后由 GP 发送 | UI 端内送达（`u2u seen=1`）；GP 侧注册者 `rseen=0` | 第 5 行成立 |
| F12 | 在 GP 上下文替换 `include` 进来的 `RGNCheckTraitInGame`，再在 UI 上下文读同一函数 | GP 侧读到替换后的值；UI 侧仍读原值 | 规则 2：每个包含者各持一份副本 |

> F11 的口径提醒：`ReportingEvents.SendLuaEvent` 在 GP 侧调用能到达 UI，在 UI 侧调用只能到达 UI；
> **GP 文件之间不要用它**，端内广播用 `LuaEvents`。GP 文件之间用 `LuaEvents` 时的派发验证见 `civ6-tuner/SKILL.md` 铁律 1。

---

## 六、检索词表

在 skill 家族正文里找跨上下文结论时，按下列词整表检索（L0 阶梯，见 `SKILL.md`）：

`跨上下文`、`跨端`、`跨脚本`、`跨文件`、`调用函数`、`全局函数`、`全局变量`、`互不可见`、`独立沙箱`、`context`、`LuaEvents`、`ExposedMembers`、`EXECUTE_SCRIPT`、`ReportingEvents`、`SendLuaEvent`、`RequestPlayerOperation`、`GetProperty`、`SetProperty`、`include`、`attempt to call a nil value`、`attempt to index a nil value`、`function expected instead of nil`

---

## 七、机械防线

| 工具 | 管什么 |
|---|---|
| `scripts/check_lua_context.py` | 按 Lua 上下文角色判定跨上下文写法是否可达（`GameEvents` 出现在 UI 侧、UI 侧 `SetProperty`、跨端 `LuaEvents`、不可达的全局函数调用、`ExposedMembers` 出现点） |
| `scripts/check_lua_registration.py` | `.lua` 有没有有效加载路径（角色判定交给 `_lua_roles.py`） |
| `scripts/check_doc_anchors.py` | 本文件的指针是否在家族各处逐字一致 |
