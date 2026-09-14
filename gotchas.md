# 🔴 易错点汇总 (Mandatory Pre-Coding Read)

**本文件是 Civ6 模组开发中 AI Agent 最常犯的低级错误汇总。**
每次写代码前，先扫一遍确认不会重蹈覆辙。

> 性质：防错清单，不是教程。只记录"以为对、实际错"的知识点。

## Fatal Errors

1. **UI Lua MUST call `Initialize()` at the bottom of the file.** The context system looks for this function. GamePlay Lua also typically calls it.

2. **`AddUserInterfaces` 里只列 `.xml`；配套 `.lua` 是否需要另登记，看它的角色**（2026-09 修订）
   - **UI 上下文脚本**（有同名 `<Context>` `.xml` 被列进 `AddUserInterfaces`）→ 引擎**自动加载同名 `.lua`**，**只需在打包清单 `<Content Include>` 里**，不必再单列 Action（官方+工坊 170 个 modinfo 中 203 例如此，且 5 个 mod 整包零 Action 级 lua 仍正常工作）；
   - **include 扩展件 / 官方脚本替代件**（`<官方名>_<后缀>.lua`，靠官方 `include("<官方名>_", true)` 通配拉入，或替换官方文件）→ **必须进 `ImportFiles`**（Firaxis 的 `UI/Additions/*.lua`、`UI/Replacements/*.lua` 全在 `ImportFiles`）；
   - **反过来一定错的是**：只列 `.lua` 而不列 `.xml` → **上下文根本不会建立**。
   - 完整判定表与证据见本文件 §3 的「两轴」小节。

3. **`<Files>` must list every XML/SQL/Lua file.** Missing any of these will cause packaging/distribution failure or the mod silently not loading. 注意范围：ImportFiles 引用的图片/视频、`Platforms/` 下的音频 bank 等媒体资产走专门的导入流程或用户手动导入；其余文件 ModBuddy 引擎默认自动打包，无需写进清单（见 project-setup.md「文件清单同步」）。

   > **⚠ 两轴必须分清：`<Content Include>` 管「打包」，Action 管「加载」**（2026-09 修订）
   >
   > | 轴 | 来源 | 作用 |
   > |---|---|---|
   > | **打包** | `.civ6proj` 的 `<Content Include="…">` → 构建时展平成 `.modinfo` 顶层 `<Files>` | 决定文件**是否被复制进 Mods 目录**（编译期） |
   > | **加载** | `.civ6proj` 的 Action 段 | 决定文件**在游戏里以什么身份被装载** |
   >
   > **怎么判断某个 `.lua` 会不会被加载 —— 按它的「角色」分三类，不要一刀切：**
   >
   > | `.lua` 的角色 | 判定依据 | 需要在哪里登记 |
   > |---|---|---|
   > | **① UI 上下文脚本** | 有一个**同名 `.xml`**（`<Context>`）被列进 `AddUserInterfaces` | ★ **只需在打包清单里**。引擎建上下文时会**自动加载同名 `.lua`**，**不必**再单列 Action |
   > | **② include 扩展件 / 官方脚本替代件** | 文件名形如 `<官方名>_<后缀>.lua`，靠官方 `include("<官方名>_", true)` 通配拉入；或整体替换官方文件 | ★ **必须进 `ImportFiles`** —— 否则不在 UI 上下文的 `include()` 搜索路径里 |
   > | **③ GamePlay 脚本** | 在 GP 侧运行 | **必须进 `AddGameplayScripts`** |
   >
   > **证据（官方 + 工坊 170 个 modinfo 全量统计）**：
   > - `AddUserInterfaces` 区块内**只列 `.xml`** 的有 **128/130** 例 —— 这是标准写法；
   > - 其同名 `.lua` **只出现在 `<Files>` 打包清单、不在任何 Action** 的有 **203 例**（其中 5 个 mod 整包**零个** Action 级 `.lua` 却正常工作，如 Sukritact's Relations Overview、Maple_Leaves_Music）→ **证明①的自动加载确实存在**；
   > - 而 Firaxis 官方 DLC 的 `UI/Additions/*.lua`、`UI/Replacements/*.lua`（Expansion2 有 138 个）**全部登记在 `ImportFiles`**；`Ethiopia.modinfo` 的 `UI/Loaders/TechAndCivicUnlockables_Ethiopia.lua` 也在 `ImportFiles` → **证明②确实需要 ImportFiles**。
   >
   > **⚠ 曾经写反过**：早期版本把「`AddUserInterfaces` 只列 xml + `.lua` 不在任何 Action」直接判为"打包了却从不执行"——
   > 那是**错的**，对①类文件引擎会自动加载。**只有②类文件漏登记才真的不生效。**
   >
   > **自检**：把 Action 段引用的文件与 `<Content Include>` 做归一化（`\`→`/`）差集，
   > 逐个判断上表角色 —— ③类在差集里 = 真漏；①类在差集里 = 正常。参考实现：示例工程 `workspace/_tools/check_proj_content.py`。

<!-- 4. **Mod ID must be a valid GUID.** Don't reuse GUIDs across mods. -->

## Event Pitfalls

5. **C++ events (`Events.*`) must be `.Remove()`'d in `OnShutdown()`.** Failing to do so causes memory leaks and phantom callbacks across context reloads (hot reload).

6. **LuaEvents automatically clean up** — no need to `.Remove()`.

7. **GamePlay 脚本 `Events.*` 和 `GameEvents.*` 均可用，不可用 `LuaEvents.*`。** `LuaEvents.*` 是 UI 上下文的广播系统，GP 侧不可用。UI 侧不可用 `GameEvents.*`。

> **⚠ 三条总线互不镜像 —— 用错总线是「静默无效」，必须按事件查表，不要凭印象**（2026-09 修订）
>
> 同一个逻辑事件**通常只在其中一张表上有效**。用错总线的后果是**不报错、也永远不回调**（静默无效登记）。
>
> **权威判据 = `reference/events_enhanced.json` 的 `eventSystem` 字段**（1081 条全覆盖）：
>
> | `eventSystem` | 条数 | 注册方式 |
> |---|---|---|
> | `LuaEvents` | 481 | `LuaEvents.X.Add()`（UI 上下文互播；GP 侧不可用） |
> | `Events` | 470 | `Events.X.Add()` |
> | `GameEvents` | 130 | `GameEvents.X.Add()` |
>
> 也可以用 `python database/scripts/query_events.py --show <事件名>` 直接看 `System` 列。
>
> **⚠ 旧版本写「`GameEvents.*` 只承载 Lua 级事件、不承载任何引擎事件」——那是错的。**
> 准确说法：`GameEvents.*` 上**存在一批非自定义事件，且它们在 `Events.*` 上没有对应条目**，例如 `OnDistrictConstructed` / `CityConquered` / `PolicyChanged` / `PlayerTurnStarted` / `OnUnitMoved` / `OnCombatOccurred` / `UnitCreated` / `PlotPropertyChanged`（130 条中 82 条 `availability=GamePlay`，`events_enhanced.json` 自带的 `exampleCode` 就写 `GameEvents.X.Add(...)`）。
> 实测反证：一个已发布 mod 全工程 127 个事件注册点与 `eventSystem` 比对 **63/63 命中、0 处不一致**，其中 `GameEvents.PolicyChanged` / `GameEvents.CityConquered` / `GameEvents.OnDistrictConstructed` 都在正常工作；另一个工程 18 个事件同样零例外。
> 同理 `UnitMoveComplete` 只在 `Events.*` 上有回调 —— **两边各自拥有一批对方没有的事件，谁也不能替代谁**。
> 心智模型：三条总线是**按事件划分**的三张表，不是按「引擎 vs Lua」划分的 —— 所以永远查 `eventSystem`，不要按来源猜。
>
> **⚠ `GameEvents.X` 不是存在性探针**——它对**任意**名字都返回 table（自动建表）。只能用 `type(Events.X) == "table"` 判断事件是否存在；对不存在的事件写 `Events.X.Add()`，**UI 侧会直接抛 `attempt to index a nil value` 并中断该函数后续所有初始化**。引擎未暴露到 `Events.*` 的 48 个事件在 `events_enhanced.json` 中标 `availability: "None"`（这 48 条的 `eventSystem` 同为 `GameEvents`，即「按名字该走 GameEvents，但实际哪一层都订阅不到」）。

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

---

## LoadOrder 与跨 mod 门控（2026-09 · 11 个工程实测）

44. **官方文档之外的 LoadOrder 阶梯：`-1` 是事实约定，`600000` 段是社区约定**
    本文档上文只给了 vanilla 的 `-100 … 100` 阶梯；11 个真实工程实测分布的**观测值**如下（**按观测呈现，不臆造依据**）：

    | 用途（按观测归纳） | 观测值 | 出现工程 |
    |---|---|---|
    | 内容/类型**定义**前置 | `-2` / `-1` | 工程 F、工程 G、工程 H、工程 B、工程 C、工程 I、示例工程、工程 A |
    | 常规内容 | `10` – `200`（`200` 最常见，多用于 Types） | 多数 |
    | 跨 mod 适配层 | `1000` / `10000` / `20000` / `30000` | BlackShores_Patch、工程 F/SK、工程 D |
    | 大包主体（需晚于他人读取） | `600000` – `610003` | 工程 A `600003`、工程 C `600000/600001`、示例工程 `600000/600005`、UI 层 `610002/610003` |
    | 最终覆盖层（立绘/适配/补丁） | `777777` – `9999999`（`999999` 见于 7 个工程） | 多个 |

    - ★ **`-1` 出现在 8/11 个工程**，且 4 个独立总督工程都把它用于 `Governors` 数据 → **强约定**：*被其他内容引用的定义类数据要早加载*。
    - **UI 层的 LoadOrder 要晚于 `ImportFiles`**（实测 `ImportFiles` 600000 → `AddUserInterfaces`+`Context=InGame` 610002）。
    - ⚠ **跨 mod 同 LoadOrder 的执行次序无保证**。`999999` 被 6 个工程同时占用；**新增同名 tag / 同 ModifierId 前必须自查是否与他人撞值**。
    - 写平衡补丁时必须压过主工程**最终覆盖层**，详见 `balance-patch.md` §三。

45. **`<Criteria>` 除了单个 `ModInUse`，还支持 `any="1"` 与 `inverse="1"` 组合**
    ```xml
    <!-- 任一命中即成立（多候选 mod GUID） -->
    <Criteria id="Rover_Any" any="1">
      <ModInUse>073b6367-…</ModInUse>
      <ModInUse>21183d1e-…</ModInUse>
      <ModInUse>66685738-…</ModInUse>
    </Criteria>
    <!-- 反选：对方【不】在场才成立 -->
    <Criteria id="X_Disabled"><ModInUse inverse="1">对方GUID</ModInUse></Criteria>
    ```
    vanillar/CDATA 特性：`inverse` 是 `.civ6proj` CDATA 才支持的写法，手写 `.modinfo` 需预定义独立的 `X_Disabled` 判据。
    **三态生态用法**（11 工程实测，skill 此前只文档了语法未文档用法）：
    | 用法 | 语义 |
    |---|---|
    | `<ModInUse>GUID</ModInUse>` | 对方在场 → **加载我的适配内容** |
    | `<ModInUse inverse="1">GUID</ModInUse>` | 对方在场 → **关闭我的重复内容**（避免同一内容被两个 mod 各定义一份） |
    | 补丁门控 | 父 mod 在场才加载补丁（见 `balance-patch.md`） |
    实测被多个工程共同适配的生态 GUID：`HD`、`Suk_Portrait`、`工程 I`、`DLL`、`BuilderCharges`。

46. **Lua 拿不到 `<Criteria>` —— 用 `GlobalParameters` 做桥**
    `<Criteria>` 只在**加载期**决定"这块内容跑不跑"，Lua 运行时读不到它。
    需要让 Lua 按"某 mod 是否在场"分支时：主数据文件先声明 `(Name, 0)`，由被 Criteria 守护的兼容文件把它 `UPDATE` 成 `1`，Lua 启动读值分支。
    ```sql
    -- 主数据文件
    INSERT OR REPLACE INTO GlobalParameters (Name, Value) VALUES ('MYMOD_ADAPT_FIX_X', 0);
    -- 被 <Criteria> 守护的兼容文件（对方在场时才执行）
    UPDATE GlobalParameters SET Value = 1 WHERE Name = 'MYMOD_ADAPT_FIX_X';
    ```
    ```lua
    local ADAPT = math.floor(GlobalParameters.MYMOD_ADAPT_FIX_X) or 0;
    ```
    另一条路：补丁侧 `Game.SetProperty("X_BALANCED", 1)`，主 mod 读 `Game.GetProperty` —— 见 `balance-patch.md` §五。
    第三条路（**不需要对方配合**）：遍历 `GameInfo.Leaders()` 等表探测对方领袖/条目是否存在；SQL 侧等价物是 `WHERE EXISTS (SELECT 1 FROM …)`。

---

## 引擎数据细节（skill 库实查 · 反直觉）

47. **`Modifiers.OwnerRequirementSetId = 'ON_TURN_STARTED'` 是伪条件集（每回合重评估）**
    该列**不是只能填 RequirementSetId** —— `ON_TURN_STARTED` 是引擎识别的伪值。
    ★ vanilla 实测 66 行，**全部**是 `MODIFIER_PLAYER_DIPLOMACY_AGENDA_*`（议程需要周期性重估）。
    查库确认：除该伪值外，`OwnerRequirementSetId` 的取值与 `RequirementSets` 差集为空。
    ```sql
    SELECT OwnerRequirementSetId, COUNT(*) FROM Modifiers GROUP BY 1 ORDER BY 2 DESC;
    ```
    用法：把修饰符挂上它即可获得"每回合重算"的触发时机（实测被用于"每回合授予经验"等场景）。

48. **`ModifierArguments.Value` 支持逗号列表，按位置与另一参数配对**
    ```sql
    -- 一条修饰符改三种产出
    ('PETRA_YIELD_MODIFIER', 'YieldType', 'YIELD_FOOD,YIELD_GOLD,YIELD_PRODUCTION'),
    ('PETRA_YIELD_MODIFIER', 'Amount',    '2,2,1')
    ```
    ★ vanilla 实测 45 行含逗号（`YieldType` 16 / `Amount` 15 / `UnitType` 7 / `DistrictType` 4）。
    **反直觉点**：`Amount` 列被当字符串存，**不做数值校验** —— 两边长度写不等会**静默错配**，不报错。
    紧凑写法（`2,2,1`）与带空格写法（`1, 1, 1`）原版都在用。

49. **`Modifiers.SubjectStackLimit` / `OwnerStackLimit` 限叠加（词条型效果重复挂会出 bug）**
    ★ 实测列存在、vanilla 57 行非 0。同一 `ModifierId` 被多个来源（多建筑 / 多次 ATTACH / 多晋升）挂到同一主体时**默认叠加**；
    视野、攻击次数、移动力、进入深海这类词条型效果重复叠加会出显示或逻辑 bug。
    `SubjectStackLimit = 1` = 同一主体只生效一份。（注意：这与 `gotchas.md` §30「同名 ABILITY 只叠加 1 层」是**两个不同层面**的机制。）

50. **`EFFECT_CHANGE_UNIT_OPERATION_AVAILABILITY` 的参数只认 `UNITOPERATION_*`，填 `UNITCOMMAND_*` 是空转**
    ★ `UnitOperations`（键列 `OperationType`）与 `UnitCommands`（键列 `CommandType`）是**两张不同的表**。
    vanilla 用法：`MODIFIER_ALL_UNITS_DISABLE_OPERATION` 的参数为 `Available` + `OperationType='UNITOPERATION_SOOTHSAYER_SACRIFICE'`。
    实测踩坑：把 `UNITCOMMAND_MOVE_JUMP` 填进 `OperationType`（`Available=0`）**毫无作用、也不报错**，原版行为照旧。
    **规范**：写任何枚举型参数前，先 `SELECT DISTINCT <列> FROM <表>` 确认合法取值域。

51. **`Improvements.Coast = 1` 指「沿海陆地」，水域改良必须 `Domain='DOMAIN_SEA'` + `Coast=0`**
    ★ vanilla 实查：`Domain='DOMAIN_SEA'` 的 8 条改良（FISHING_BOATS / OFFSHORE_OIL_RIG / KAMPUNG / POLDER / FISHERY / OFFSHORE_WIND_FARM / SEASTEAD / FEITORIA）**全部 `Coast=0`**；
    唯一 `Coast=1` 的是 `IMPROVEMENT_BEACH_RESORT`，其 `Domain='DOMAIN_LAND'`。
    ```sql
    SELECT Domain, Coast, COUNT(*) FROM Improvements GROUP BY 1,2;
    -- DOMAIN_LAND/0 = 57 ; DOMAIN_LAND/1 = 1 ; DOMAIN_SEA/0 = 8
    ```
    **禁止 `Domain='DOMAIN_SEA'` + `Coast=1`。**

52. **SQL `LIKE ('%A%' OR '%B%')` 是陷阱：括号表达式先求值为整数 `0`**
    症状：多关键词搜索**一条都搜不到**，且**不报错**。
    ```
    WHERE col LIKE ('%大剑%' OR '%knight%')     -- ✗ 括号先算 (字符串 OR 字符串) → 整数 0 → 等价 LIKE 0
    WHERE col LIKE '%大剑%' OR col LIKE '%knight%'   -- ✓
    ```
    更隐蔽的是：`LIKE 0` **不是永不命中**，而是**只命中字面量为 `'0'` 的行**（内存 SQLite 实跑复现：只返回值为 `'0'` 的那行）。
    **写多关键词检索一律把 `LIKE` 重复写在每个条件上。**

53. **`LIKE` 里的 `_` 是单字符通配符，匹配字面下划线必须 `ESCAPE '\'`**
    ```sql
    WHERE Type LIKE 'CIVILIZATION\_（已移除）\_WAVES\_%' ESCAPE '\'
    ```
    漏写 `ESCAPE` 会静默多匹配（`\_` 被当"任意单字符"），在批量 `DELETE`/`UPDATE` 里后果放大。

54. **SQL 保留字列名要加反引号：`` `Range` ``**
    `Units` 表的 `Range` 列是 SQL 关键字，`INSERT` 时须写 `` `Range` ``。写枚举列/保留字列前先看同文件既有写法。

55. **引擎自带的拼写错误只能"照抄"，但必须先在原版数据里实证**
    判定标准：该字符串能在**原版数据快照 / 游戏本体文件**里查到，且**同族字符串拼写正确** → 认定为引擎官方笔误，逐字照抄。
    **工程或第三方 mod 里的拼写错误不要跟着抄**（那是缺陷，不是约定）。
    ★ 已实证例（互为镜像的一对）：
    | 错误串 | 位置 | 同族正确写法（对照证据） |
    |---|---|---|
    | `MODIFIER_GOVERNOR_ADJUST_PREVENET_STRUCTURAL_DAMAGE` | `Modifiers` 的 ModifierType | 对应 `EffectType` = `EFFECT_ADJUST_PREVENT_STRUCTURAL_DAMAGE` |
    | `EFFECT_GOVERNOR_ADJUST_IDENITITY_PER_TITLE` | `DynamicModifiers` 的 EffectType | 对应 `ModifierType` = `MODIFIER_PLAYER_GOVERNORS_ADJUST_IDENTITY_PER_TITLE` |
    复核命令：`SELECT ModifierType, CollectionType, EffectType FROM DynamicModifiers WHERE ModifierType LIKE '%PREVENET%' OR EffectType LIKE '%IDENITITY%';`
    （更多总督相关内容见 `governor-authoring.md` §五。）

56. **`TypeProperties` 是"不打 Lua 就给 Type 挂引擎开关"的声明式表 —— 与 Lua `SetProperty` 是两套**
    ```sql
    INSERT OR REPLACE INTO TypeProperties (Type, Name, Value) VALUES
      ('UNIT_X', 'CAN_TELEPORT_TO_CITY', '1'),
      ('UNIT_X', 'IGNORE_PLAYER_STAT_MAX_STRENGTH', '1');
    ```
    ★ vanilla 实测 395 行 / 42 个不同 `Name`（`CityStateCategory` / `LIFESPAN` / `CAN_MOVE_AFTER_PURCHASE` / `CAN_EVER_TRAIN_CITY_STATE` / `HERO_LOYALTY_CHANGE_PER_TURN` …）。
    注意原版行**还带第 4 列 `PropertyType`**（如 `PROPERTYTYPE_IDENTITY`）；省略是否降级未实测。

---

## UI / GP 双端 API 面差异（工程实测；标注为项目断言者未独立复核）

> **通用写法：探测方法存在性，而不是靠上下文标志分支。** 同一份 Core 文件要被 GP 和 UI 同时 `include()`，
> 就写成「探测方法存在 → 用；不存在 → 换等价方法；都没有 → 走保守默认值」：
> ```lua
> local f = pUnit.GetUnitType or pUnit.GetType;
> ```

57. **同一语义在两端的可用性可能不同，且"存在但语义错"比"不存在"更难查**

    | API | 实测差异 | 处置 |
    |---|---|---|
    | `Unit:GetMovesRemaining()` | UI 返回 4.5 / **GP 返回 4（整数截断）** | 统一改用分数接口 `GetMovementMovesRemaining()` |
    | `Plot:IsValidFoundLocation()` | UI 可用；**GP 恒 `false`** | 用 `GetCities():IsValidFoundLocation(x,y)`（仅 GP） |
    | `GetPastTimeline` | **仅 UI** | UI 采集后经 `EXECUTE_SCRIPT` 回灌 GP |
    | `Game.SetProperty` | **仅 GP** | —— |
    | `GetNumBeliefsEarned` | **仅 UI** | GP 侧用 `GetStats:GetNumBeliefsInReligion` |
    | `Unit:GetUnitType` | **仅 UI**（GP 只有 `GetType` 返回索引） | 上面的探测式写法 |

    ⚠ `Plot:IsValidFoundLocation()` 在 `database/api.sqlite` 里标 `availability=Both` —— 即「**存在但语义错**」，查库查不出来，只有实测能发现。**这类差异是"查 API 库"覆盖不到的地带。**

58. **`ContextPtr:AddUpdate` / `RemoveUpdate` 在 Civ6 不存在** —— 逐帧回调用 `ContextPtr:SetUpdate(fn)` / `SetUpdate(nil)`。
    ⚠ `SetUpdate` **只在 context 可见时被调度**。

59. **`Religion:GetHolyCityID()` 返回的是 componentIDs 表 `{type, player, id}`，必须取 `.id`**
    曾把整表当数值转发导致下游静默失效。

60. **`bCancelled` 在日志里常见 `-1`，表示"未取消"** —— 只有 `true` / `1` 才算取消。
    把它当布尔用会把"正常事件"误判成"队列被取消"，导致逻辑中断。

61. **Modifier 授予/移除 PROPERTY 不会触发 `UnitPropertyChanged`**
    SQL modifier 直接写 PROPERTY 时，依赖 `Events.UnitPropertyChanged` 刷新 UI 的按钮/面板**静默不刷新**。
    兜底：`ContextPtr:SetUpdate` 累加计时 + 节流脏检查（实测 0.2s 一档可用）。

62. **需要"本局第一次通知"的 handler 必须写在文件加载期，不能放进初始化函数**
    `Events.NotificationAdded` 这类"开局前几回合就会来"的事件，若在 `LoadScreenClose` / `LoadGameViewStateDone` 里才 `.Add()`，
    初始化窗口内的事件**永久丢失且不报错**（实测漏掉通知 1、3，只剩 8）。
    **判据**：该事件是否可能在 `LoadGameViewStateDone` 之前触发？是 → 顶层注册。

63. **引擎返回的"数组"可能是稀疏 table —— 用 `pairs` 不要用 `ipairs`**
    `City:GetOwnedPlots()` 等 `Get*` 返回的列表底层可能有空洞，`ipairs` 会在第一个 `nil` 处停止，**静默丢掉后半段**
    （表现为"随机选地块总选不到某些格"）。
    ```lua
    for k, pPlot in pairs(plots or {}) do
      if type(k) == "number" and pPlot then … end
    end
    ```

64. **`INSERT OR REPLACE` / `INSERT OR IGNORE` / 裸 `INSERT INTO` 是三层语义，不要混用**
    | 写法 | 语义 | 场景 |
    |---|---|---|
    | `INSERT OR REPLACE` | **夺权**：覆盖已有定义 | 主流程（幂等可重跑） |
    | `INSERT OR IGNORE` | **只补缺，不夺权** | 与其他 mod 可能撞车的定义；属性标记 |
    | 裸 `INSERT INTO` | 写**没有 Types 注册**的纯数据表 | 该表不参与 Type 体系时 |
    裸 `INSERT` 出现得极少 —— 见到它通常是"该表不需要 Types"的信号。




