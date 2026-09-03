# 🔴 易错点汇总 (Mandatory Pre-Coding Read)

**本文件是 Civ6 模组开发中 AI Agent 最常犯的低级错误汇总。**
每次写代码前，先扫一遍确认不会重蹈覆辙。

> 性质：防错清单，不是教程。只记录"以为对、实际错"的知识点。

## Fatal Errors

1. **UI Lua MUST call `Initialize()` at the bottom of the file.** The context system looks for this function. GamePlay Lua also typically calls it.

2. **`AddUserInterfaces` references only the `.xml`.** The matching `.lua` must go in a separate `ImportFiles` entry. If you only list the `.lua`, the context won't load.

3. **`<Files>` must list every XML/SQL/Lua file.** Missing any of these will cause packaging/distribution failure or the mod silently not loading. 注意范围：ImportFiles 引用的图片/视频、`Platforms/` 下的音频 bank 等媒体资产走专门的导入流程或用户手动导入；其余文件 ModBuddy 引擎默认自动打包，无需写进清单（见 project-setup.md「文件清单同步」）。

<!-- 4. **Mod ID must be a valid GUID.** Don't reuse GUIDs across mods. -->

## Event Pitfalls

5. **C++ events (`Events.*`) must be `.Remove()`'d in `OnShutdown()`.** Failing to do so causes memory leaks and phantom callbacks across context reloads (hot reload).

6. **LuaEvents automatically clean up** — no need to `.Remove()`.

7. **GamePlay 脚本 `Events.*` 和 `GameEvents.*` 均可用，不可用 `LuaEvents.*`。** `LuaEvents.*` 是 UI 上下文的广播系统，GP 侧不可用。UI 侧不可用 `GameEvents.*`。

8. **Never pass C++ objects or UI controls across `LuaEvents`.** The owning context may delete them before the receiver processes the event, causing crashes. Pass only string/number/boolean or pure-Lua tables.

## Database Pitfalls

9. **Load order matters.** Use `LoadOrder="-100"` for schema changes/data removal. Use `LoadOrder="0"` (default) for standard content. Use `LoadOrder="100"` for scenario content.

10. **Higher `Priority` values load later.** Removal XML typically gets `Priority="1"` to run first. Standard data gets no Priority attribute (runs later, after removals).

11. **To remove data, use `<Delete>` tags** in XML with higher priority (lower Priority number).

12. **`Requirements.Inverse` (BOOLEAN NOT NULL) is universally supported on ALL RequirementType.** While only 53 of 545+ RequirementType instances use Inverse=1 in official data, the engine respects the column on every type. Use `Inverse=1` on the Requirements row to negate ANY requirement — confirmed safe for `REQUIREMENT_UNIT_TYPE_MATCHES`, `REQUIREMENT_UNIT_TAG_MATCHES`, and all others. Do NOT use `Inverse` as a RequirementArgument (it's a column on the Requirements table, not an argument in RequirementArguments).

13. **SQL 文件中文本内的单引号 `'` 必须转义为 `''`** — SQL 标准转义方式是用两个连续单引号，反斜杠 `\'` 无效，会直接报错或插入错误数据。例如：`'Penitent''s End'` ✓，`'Penitent\'s End'` ✗。这在 `LocalizedText`、`ModifierStrings` 等含英文文本的 INSERT 中极易遗忘。

13. **查询游戏数据 API 首选 SQLite。** `database/api.sqlite` (Lua API) 和 `database/DebugGameplay.sqlite` (游戏数据) 覆盖全部查询需求。详见 SKILL.md Rule 0.4。

14. **`MODIFIER_*_ADJUST_PROPERTY` 的 ModifierArgument 用 `Key` + `Amount`；`REQUIREMENT_PLOT_PROPERTY_MATCHES` 的 RequirementArgument 用 `PropertyName` + `PropertyMinimum`。** — ModifierArgument 中无论玩家级还是单位级，设置 PROPERTY 值的参数名都是 `Key`。但 RequirementArgument 中检测 PROPERTY 用的是 `PropertyName`（以及 `PropertyMinimum` 阈值）。二者参数名不同，混用不会报错但永远不生效。`REQUIREMENT_PLAYER_PROPERTY_MATCHES` 等其他 PROPERTY 检测 RequirementType 也沿用 `PropertyName`。

## UI Pitfalls

14. **When replacing a UI script**, you must know the exact `LuaContext` ID from the base game's XML. Find these in `Base/Assets/UI/*.xml` — search for `<LuaContext ID="..."`.

15. **PowerShell 5.1 `Set-Content -Encoding UTF8` 会自动写入 BOM。** — SQLite 和 Lua 5.4 不允许 BOM，会导致 `syntax error` 或静默跳过整个文件。替代方案：用 PowerShell 7 (`pwsh`) 的 `Set-Content -Encoding UTF8NoBOM`；或 5.1 下用 `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))`。

16. **`LookUpControl` wildcards** (`*`) cannot be used for the control name itself (the last path segment). Valid: `"*/FrontEndPopup/CloseButton"`. Invalid: `"../FrontEndPopup/*"`.

17. **`SetInputHandler`** with `true` (extended handler) gives you an `inputStruct` table. Without `true` (simple handler), you get raw `(uiMsg, wParam, lParam)`.

18. **Include files copy all content** into the including context's scope. Minimize local variables in them to avoid size bloat and name collisions.

19. **UI 上下文禁止直接 `SetProperty`** — UI 侧 `Players[pid]:SetProperty(key, value)` 在多人游戏中不可靠，应统一走 `UI.RequestPlayerOperation(pid, PlayerOperations.EXECUTE_SCRIPT, { OnStart = handlerName, PropertyKey = key, Value = value })`。由 GP 侧 GameEvents handler 执行写入。同样适用于 Delta 增量：`{ PropertyKey = key, Delta = delta }`。handler 命名按项目规范定义。

39. **镜头名必须是引擎已注册镜头** — `UILens.CreateLensLayerHash("自定义名")` 静默不渲染，且无任何报错（症状："点击后无任何动作也没有报错"）。可用 vanilla 镜头：`"Hex_Coloring_Movement"`（绿色范围）、`"Hex_Coloring_Attack"`（红色目标指示）、`"Attack_Range"`（范围层）。目标指示器用三元组 `{"AttackRange_Target", sourcePlot, plotId}`（vanilla WMD 打击同款格式），sourcePlot 为发起地块对象。

40. **Civ 6 是偏移坐标系统（奇偶行错位），手工 `{dx,dy}` 方向偏移只有东西方向正确** — 斜向格按行奇偶错位，症状：1 环高亮"总有一个在 2 环"、同方向直线遍历整体歪斜。邻格遍历一律用引擎函数：`Map.GetAdjacentPlot(x, y, DirectionTypes)`（单格、有序）或 `Map.GetAdjacentPlots(x, y)`（返回 6 邻格，BFS 分层扩展用）。直线延伸：`Map.GetAdjacentPlot(curX, curY, direction)` 逐格迭代。

41. **`LuaEvents.WorldInput_WBSelectPlot` 回调签名固定为 `(plotId, plotEdge, boolDown, rButton)`** — 第 3 参是"按下/释放"（boolDown），不是左键标志；第 4 参才是右键。参数错位会静默失败：左键点击被误判为"释放+右键"直接 return、右键取消失效。悬停地块用 `LuaEvents.WorldInput_WBMouseOverPlot(plotID)`，配合 `Map.GetPlotByIndex`。

42. **WB_SELECT_PLOT 瞄准模式时序三条铁律** — ① `UI.SetInterfaceMode()` **同步**触发 `Events.InterfaceModeChanged`：先切模式再读全局状态会拿到已清空值（如 UnitID=-1 导致请求静默失效），必须先缓存所需值再切模式。② 高亮在 `InterfaceModeChanged(newMode == WB_SELECT_PLOT)` 回调中显示，不要在 SetInterfaceMode 前直接 UILens（避免时序冲突被引擎清除）。③ 瞄准期间 `Events.UnitSelectionChanged` 会被"点击地块上的单位"触发，需特判：发起单位仍存在则不取消瞄准（点击单位应等同点击其所在地块）。

## Type Annotation Pitfalls

19. **Havok Script type annotations** (`:number`, `:string`, `:boolean`, `:table`) are optional but help catch errors.

20. **Don't use `== nil` for boolean checks** on game object methods — use the return value directly. Some functions return 0 instead of false.

## Hot Reload

21. **State is lost on hot reload** unless you use `LuaEvents.GameDebug_AddValue(key, value)` in `OnShutdown()` and `LuaEvents.GameDebug_GetValues(key)` in `OnInit( isReload:true )`. Use `RELOAD_CACHE_ID` as a unique context identifier.

## C++ Object Lifetimes

22. **Game objects (players, units, cities) can be destroyed at any time.** Always nil-check: `if pPlayer ~= nil and pPlayer:IsAlive() then ... end`

23. **A player being observed (dead, spectating) may have `GetLocalPlayer() < 0`** — guard against this.

## Multiplayer Gotchas

24. **Avoid `math.random()` in multiplayer** — use `Game.GetRandNum(n)` which produces [0, n-1] and is seeded for network sync.

25. **Avoid `Game.GetLocalPlayer()` in Gameplay scripts** — it's a UI concept. Use `PlayerManager.GetAliveIDs()` or event parameters instead.

## UnitAbility: Permanent vs Inactive

26. **`Permanent=1` 表示单位固有能力**，定义即自动赋予，无需 `MODIFIER_PLAYER_UNITS_GRANT_ABILITY`。单位天生就有，不可移除。
    - 示例：声骸类型标记、固有被动能力

27. **`Inactive=1` 表示 Lua 动态赋予/移除的标记**，修饰器随 Attach/Remove 即时生效。用于选择性赋予的能力。
    - 示例：Feather 增益/减益、毒伤标记

28. **两者互斥，不应同时为真。** Permanent 是"天生"的属性，Inactive 是"后天"的开关。

29. **ABILITY 由 TypeTags 限定作用范围** — 在 `TypeTags` 表中将 ABILITY 绑定到 `CLASS_*` 标签，单位通过 `TypeTags` 匹配该 CLASS 标签后，ABILITY 才对该单位生效。无需在 GRANT_ABILITY 的 modifier 上额外加 RequirementSet。

30. **同名 ABILITY 只会叠加 1 层** — 即使多个建筑或多次调用 `MODIFIER_PLAYER_UNITS_GRANT_ABILITY` 分发同一个 AbilityType，单位最终也只拥有该 ABILITY 的一个实例。因此多个建筑重复分发是安全的，无需 Lua 去重。

## SubjectReqSet 放置规则

31. **GRANT_ABILITY 的 SubjectReqSet 是唯一赠送门槛** — Ability 内部 modifier 不应重复设 SubjectReqSet。引擎自动 toggle 整组 Ability：条件满足时授予，不满足时收回。内部 modifier 一旦拥有即无条件生效。

32. **例外：Lua AttachAbilityToUnit** — 手动附加时无 GRANT toggle，需 modifier 自行控制条件。

## PROPERTY 存储

33. **`SetProperty(key, value)` 可以存任意 Lua 值** — 不仅仅是字符串和数字。可以直接存 table：`pUnit:SetProperty("state", {lastTurn=5, level=2})`。`GetProperty(key)` 原样取回。

34. **PROPERTY 中存的 table 跨存档持久化** — 游戏引擎自动序列化。无需手动字符串拼接/解析。

35. **`SetProperty` 前必须先读旧值，只写入有变化的位** — 批量设 Property 时不做对比直接写入，过回合会从数秒退化到数分钟。马良的模块化相邻加成就是因此从几秒优化到秒过回合。见 WORKSHOP_PATTERNS.md Binary Bitfield Pattern 的 Lua 示例。

## GP → UI 通信

36. **GP→UI 推送用 `ReportingEvents.SendLuaEvent`，不用 `LuaEvents.*` 直接触发** — 这是 GP→UI 的标准推送方式：
     ```lua
     ReportingEvents.SendLuaEvent('Name', { key = value })
     ```
     UI 侧 `LuaEvents.Name.Add(handler)` 接收。GP 中直接调用 `LuaEvents.Name(...)` 也能工作，但 `SendLuaEvent` 是官方跨 Lua 状态的 API。

37. **按钮触发的 UI→GP 动作必须走 `EXECUTE_SCRIPT`，禁止跨端通过 `ExposedMembers` 调用** — 按钮回调中触发的一切 GP 函数调用（升级、增益切换、购买等）统一使用 `UI.RequestPlayerOperation(EXECUTE_SCRIPT)`。`ExposedMembers` 仅限 GP 同端跨文件共享，禁止跨端暴露给 UI；UI 被动读取用 PROPERTY / Core 共享读取函数。

38. **UI 可直接读取 PROPERTY，共享读取函数放 Core 文件** — `Players[id]:GetProperty("KEY")` / `pPlot:GetProperty("KEY")` 在 UI 侧同样可用。将读取函数定义在 Core 文件中，GP 和 UI 各自 `include()` 即可；跨端不需要也不允许用 `ExposedMembers` 包装。

43. **ForgeUI `Offset` 正值恒指向容器内部，按锚点镜像翻转** — `Anchor` 是 `L/C/R × T/C/B` 九宫格，Offset 的正值方向不是全局坐标系而是相对锚点：`L`→右、`R`→**左**、`T`→下、`B`→**上**、`C`→全局正向（右/下）。症状：同一面板中一个按钮正常、另一个"贴屏幕边缘/面板外"，通常就是 `R,B`/`B` 系锚点写了负值（或镜像错值）。例：`R,B` + `Offset="-80,33"` = 向右 80 推出右缘；正确应为 `"80,33"`（向左）。vanilla 佐证 `WorldBuilderMenu.xml:14-15`（`R,B`/`L,B` 均正值正常）、`BoostUnlockedPopup.xml:38`（`C,B` + `0,15` 向上）。规避：角落锚点先按上表反推符号；或统一用 `C,*` 锚点 + 正值，无镜像歧义。详见 `xml-templates.md` "Anchor Syntax Reference"。



