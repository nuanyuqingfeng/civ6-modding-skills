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
- [ ] **Uses `Events.*` / `GameEvents.*`** — NOT `LuaEvents.*`
- [ ] **No UI access** — no `ContextPtr`, `Controls`, `UIManager`, etc.
- [ ] **No `LuaEvents.*`** — LuaEvents 仅限 UI 上下文使用
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
- [ ] **`Priority` set for removal XML** — `Priority="1"` runs before default data
- [ ] **Localization uses `<BaseGameText>`** — with `Tag` and `Text` columns
- [ ] **Icon definitions use `<IconDefinitions>`** — with `Name`, `Atlas`, `Index`

## SetProperty Validation

- [ ] **Key is unique string** — use mod prefix: `"MyMod_KeyName"`
- [ ] **Value is safe to persist** — number, string, boolean, or pure-Lua tables (engine serializes automatically)
- [ ] **Nil check on read** — `local val = obj:GetProperty(key) or defaultValue`
- [ ] **Only set on valid objects** — check `pPlayer ~= nil` before `SetProperty`

## UI ↔ Gameplay Communication Validation

- [ ] **No C++ objects passed across boundary** — only primitives
- [ ] **ExposedMembers initialized（仅 GP 同端跨文件需要）** — `ExposedMembers.MyMod = ExposedMembers.MyMod or {}`；禁止跨端暴露给 UI
- [ ] **GameEvents exposed correctly（仅 GP 同端跨文件）** — `ExposedMembers.GameEvents = GameEvents`；禁止 UI 跨端获取
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
| Event not firing | Wrong event system | Use `GameEvents.*`, not `Events.*` |
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
| Removal not working | Wrong Priority/LoadOrder | Use `Priority="1"` and `LoadOrder="-100"` |
| Localization missing | Wrong tag format | Use `LOC_` prefix, match XML references |
| Icon not showing | Wrong Atlas/Index | Check base game icon atlases |
