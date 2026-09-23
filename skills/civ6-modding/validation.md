# Validation Checklist

Use this checklist after generating any Civ6 mod code to catch common errors.

---

## XML Validation (UI)

- [ ] **Context name matches file basename** — `<Context Name="MyPanel">` in `MyPanel.xml`
- [ ] **All IDs are unique within the context** — no duplicate `ID` attributes
- [ ] **Size uses valid syntax** — `parent`, `auto`, `N,N` (not raw CSS like `100%`)
- [ ] **Anchor uses valid combo** — `L/C/R` × `T/C/B` (not `left`, `top`, etc.)
- [ ] **Hidden="1" on overlay containers** — mod contexts start hidden
- [ ] **ConsumeMouseButton="1" on overlay backgrounds** — prevents click-through
- [ ] **Instance templates have Root control** — `<Instance Name="X"><Container ID="Root">...`
- [ ] **ScrollPanel contains a Stack or Container child** — not raw controls directly

## Lua Validation (UI)

- [ ] **`Initialize()` called at bottom of file** — `Initialize();` as last line
- [ ] **`include()` for required modules** — `InstanceManager`, `SupportFunctions`, etc.
- [ ] **`RELOAD_CACHE_ID` is unique** — not colliding with other mods
- [ ] **`OnInit` handles both first load and reload** — `if isReload then` branch exists
- [ ] **`OnShutdown` saves state** — `LuaEvents.GameDebug_AddValue(RELOAD_CACHE_ID, ...)`
- [ ] **`OnGameDebugReturn` restores state** — handles all saved keys
- [ ] **Input handler returns `true` for handled, `false` for not** — correct semantics
- [ ] **No C++ objects passed via LuaEvents** — only string/number/boolean/pure-Lua tables
- [ ] **C++ events `.Remove()`'d in OnShutdown** — prevents memory leaks
- [ ] **LuaEvents NOT `.Remove()`'d** — they auto-cleanup
- [ ] **Stack recalculated after content changes** — `CalculateSize()` + `ReprocessAnchoring()`
- [ ] **ScrollPanel recalculated after stack changes** — `CalculateInternalSize()`
- [ ] **Type annotations used** — `:number`, `:string`, `:boolean`, `:table` on locals
- [ ] **Naming conventions followed** — `m_` prefix, `PascalCase` functions, `On` prefix for handlers

## .modinfo Validation

- [ ] **`AddUserInterfaces` references `.xml` only** — not `.lua`
- [ ] **`ImportFiles` references `.lua`** — the Lua file goes here
- [ ] **`AddGameplayScripts` references `.lua`** — no XML needed for gameplay
- [ ] **`<Files>` lists ALL XML/SQL/Lua files** — 每个代码/数据文件都在清单；媒体资产（ImportFiles 图片/视频、Platform 音频 bank 等）走专门导入或用户手动导入，其余文件引擎自动打包、无需列出（见 project-setup.md「文件清单同步」）
- [ ] **Mod ID is a valid GUID** — unique per mod
- [ ] **`criteria` references defined criteria** — or omitted for unconditional
- [ ] **`Context` property set** — usually `InGame` for in-game UI

## ReplaceUIScript Validation

- [ ] **`include()` chain is correct** — base → expansion1 → expansion2 → other mods
- [ ] **Original function saved before override** — `local BASE_X = X;`
- [ ] **Override falls through to original** — `return BASE_X(params);`
- [ ] **`LuaContext` ID matches base game** — found via `<LuaContext ID="...">` in base XML

## BuildInstanceForControl Validation

- [ ] **Instance name matches XML** — `"MyInstance"` matches `<Instance Name="MyInstance">`
- [ ] **Target control found with nil check** — `if not target then return; end`
- [ ] **Called in `Events.LoadGameViewStateDone`** — not in `OnInit` (target may not exist yet)
- [ ] **LaunchBar resized after adding** — `buttonStack:CalculateSize()` + backing resize

## Hot Reload Validation (UI)

- [ ] **Tuner F10 works** — panel survives hot reload
- [ ] **State restored correctly** — `OnGameDebugReturn` restores all saved values
- [ ] **Panel visibility preserved** — hidden/shown state survives reload
- [ ] **Callbacks re-registered** — `REGISTERS_CACHE` pattern if using external callbacks

---

## GamePlay Lua Validation

- [ ] **Script file in `Scripts/` directory** — not `UI/`
- [ ] **Registered with `AddGameplayScripts`** — not `AddUserInterfaces`
- [ ] **`Initialize()` called at bottom** — `Initialize();` as last line
- [ ] **Uses `Events.*` / `GameEvents.*`** — 引擎事件按 `eventSystem` 选线；跨文件通信用 `LuaEvents.*`
- [ ] **No UI access** — no `ContextPtr`, `Controls`, `UIManager`, etc.
- [ ] **`LuaEvents.*` 仅用于同端跨文件** — UI 上下文互播 / GP 文件间跨文件；不跨端（GP→UI 用 ReportingEvents.SendLuaEvent）
- [ ] **Nil checks on game objects** — `if pPlayer ~= nil and pPlayer:IsAlive() then`
- [ ] **No `math.random()` in multiplayer** — use `Game.GetRandNum(n)`
- [ ] **No `Game.GetLocalPlayer()` in Gameplay** — it's a UI concept
- [ ] **Type annotations used** — `:number`, `:string`, `:boolean`, `:table`
- [ ] **Naming conventions followed** — `PascalCase` functions, `On` prefix for handlers

## Database XML Validation

- [ ] **Root element is `<GameInfo>` or `<GameData>`** — both work
- [ ] **`<Types>` row for new types** — `Type="UNIT_X" Kind="KIND_UNIT"`
- [ ] **SQL 版 Types 注册核对** — 所有新 `Type`（含 `KIND_PROMOTION` 等）在 `Types` 表注册，且 Kind 正确
- [ ] **灌库验证脚本须开启 FK** — `PRAGMA foreign_keys = ON`（SQLite 默认 OFF，不开则漏检外键错误）
- [ ] **Referenced types exist** — `PrereqTech`, `TraitType`, etc. must be valid
- [ ] **`LoadOrder` set correctly** — `-100` for schema/removal, `0` for standard, `100` for scenario
- [ ] **依赖顺序已显式安排** — 动作之间用 `LoadOrder`（移除/前置 `-100`）；**同一动作内部**用 `Priority`（**数值越大越先**）。注意**同 `Priority`（含都省略）按路径字母序执行**，声明序无效 —— 曾被此坑导致 `no such table`
      **什么算「明确需要先后加载」**（只有这两种才该写 `Priority`）：① 后者会**遍历/引用**前者写入的行（典型：Types → 遍历；建表 → `SELECT FROM` 该表）；② 运行时报错已**指向**加载顺序（`no such table: X` / 外键失败）。其余情况**不写** —— 动作划分总则见 `reference/action-splitting.md`
- [ ] **双端注册齐备** — `Colors`/`PlayerColors`/`IconTextureAtlases`/`LocalizedText`/美术 `.dep` 必须在 **FrontEnd 与 InGame 各注册一个动作**（漏一端**静默失效、不报错**）
- [ ] **动作划分复核** — 同类文件是否已**尽量合并**？只有 4 类「必须拆」与 2 类「可选拆」才该拆（详见 `reference/action-splitting.md` 决策树）
- [ ] **Localization uses `<BaseGameText>`** — with `Tag` and `Text` columns
- [ ] **Icon definitions use `<IconDefinitions>`** — with `Name`, `Atlas`, `Index`

## SetProperty Validation

- [ ] **Key is unique string** — use mod prefix: `"MyMod_KeyName"`
- [ ] **Value is safe to persist** — number, string, boolean, or pure-Lua tables (engine serializes automatically)
- [ ] **Nil check on read** — `local val = obj:GetProperty(key) or defaultValue`
- [ ] **Only set on valid objects** — check `pPlayer ~= nil` before `SetProperty`

## UI ↔ Gameplay Communication Validation

- [ ] **No C++ objects passed across boundary** — only primitives
- [ ] **GP 同端跨文件通信用 LuaEvents** — 接收端 `LuaEvents.X.Add(fn)`（文件加载期注册），触发端 `LuaEvents.X(params)`；表格按引用传递，handler 回写、调用方无需 return；不用 ExposedMembers 跨文件传函数
- [ ] **PlayerOperations only during player's turn** — UI side constraint
- [ ] **Function arguments are simple types** — number, string (not tables)

---

## Common Mistakes Quick Check

### UI Mistakes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Panel never shows | Missing `ContextPtr:SetHide(false)` | Call in `Open()` |
| Panel shows but can't click | Missing `ConsumeMouseButton="1"` | Add to overlay container |
| Panel doesn't close on ESC | Input handler missing or wrong return | Return `true` for ESC |
| Crash on hot reload | C++ event not `.Remove()`'d | Add to `OnShutdown()` |
| LaunchBar button missing | Target not found | Use `Events.LoadGameViewStateDone` |
| Instance not found | Name mismatch | Check `<Instance Name="X">` vs `BuildInstanceForControl("X", ...)` |
| Stack not resizing | Missing recalculate | Add `CalculateSize()` + `ReprocessAnchoring()` |
| UI freezes | LuaEvent passing C++ object | Pass simple types only |

### Gameplay Mistakes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Script not loading | Wrong registration | Use `AddGameplayScripts`, not `AddUserInterfaces` |
| Event not firing | Wrong event system | 按事件实际所在总线查 `reference/events_enhanced.json`（1081 条）的 `eventSystem` 字段：`Events` 与 `GameEvents` **按事件划分**，不可二选一；UI 侧 `GameEvents` 为 `nil` |
| Crash on nil | Missing nil check | Add `if pPlayer ~= nil then` |
| Data lost on save | Not using SetProperty | Use `Game:SetProperty()` for persistence |
| Multiplayer desync | `math.random()` | Use `Game.GetRandNum(n)` |
| UI can't read data | Not exposed | Use `PROPERTY` 直接读 / Core 共享读取函数（禁止跨端 `ExposedMembers`） |
| Wrong player data | Using `GetLocalPlayer()` in Gameplay | Use event parameters or `PlayerManager` |

### Database Mistakes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Data not loading | Missing `<Types>` row | Add `Type` + `Kind` registration |
| Type not found | Wrong `Kind` value | Check schema for correct `KIND_*` |
| Removal not working | Wrong Priority/LoadOrder | 用独立动作 + `LoadOrder="-100"`，或同动作内给移除文件**更大**的 `Priority`（注意数值越大越先，写 `1` 可能不够早） |
| `no such table: X`（同 mod 内自建表） | 同动作内文件按**路径字母序**执行，依赖件被排到后面 | 给被依赖文件更大的 `Priority`（同动作内定序），或拆成不同动作 + `LoadOrder` 定序 |
| Localization missing | Wrong tag format | Use `LOC_` prefix, match XML references |
| Icon not showing | Wrong Atlas/Index | Check base game icon atlases |
