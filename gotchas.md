# 🔴 易错点汇总 (Mandatory Pre-Coding Read)

**本文件是 Civ6 模组开发中 AI Agent 最常犯的低级错误汇总。**
每次写代码前，先扫一遍确认不会重蹈覆辙。

> 性质：防错清单，不是教程。只记录"以为对、实际错"的知识点。
>
> **编号即全家族引用键**（其它文档写作 `gotchas.md` §N）。历史上 **13 / 14 / 19 各重号一次**
> （分属不同小节，重号会让人按号引用时指错条目）——重号项已加**稳定锚点 `[G13a]` / `[G13b]`** 之类，
> 新写引用请优先用锚点（既有 `§3` / `§7` / `§26-27` / `§30` / `§31` / `§44` / `§52` / `§68` 均唯一，未变）。

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
   > | **① UI 上下文脚本** | 有一个**同名 `.xml`** 被列进 `AddUserInterfaces` | ★ **只需在打包清单里**。引擎建上下文时会**自动加载同名 `.lua`**，**不必**再单列 Action |
   > | **② include 扩展件 / 官方脚本替代件** | 文件名形如 `<官方名>_<后缀>.lua`，靠官方 `include("<官方名>_", true)` 通配拉入；或整体替换官方文件 | ★ **必须进 `ImportFiles`** —— 否则不在 UI 上下文的 `include()` 搜索路径里 |
   > | **③ GamePlay 脚本** | 在 GP 侧运行 | **必须进 `AddGameplayScripts`** |
   >
   > **★ ①的两个关键放宽（容易误判，务必记住）**：
   > 1. **`.xml` 允许空着** —— 哪怕内容只是一个空的 `<GameData></GameData>` 占位（甚至没有真正的 `<Context>`），
   >    引擎**依然会自动加载同名 `.lua`**。所以"xml 里没有东西"不等于"lua 不会跑"。实测例：某工程 `UI/Disaster_Plots/DisasterPlot_BS.xml` 全文就是空的 `<GameData></GameData>`，同名的 `DisasterPlot_BS.lua`（511 B）照样被加载。
   > 2. **`.xml` 必须在 `AddUserInterfaces` 里** —— 这是①成立的前提；**只列 `.lua` 不列 `.xml` 才是真错**（上下文根本不会建立）。
   >
   > 因此判定①类文件的唯一问题是：**它有没有同名 `.xml`？那个 `.xml` 在不在 `AddUserInterfaces` 里？** 两条都满足 → 不需任何额外登记。
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

12. **`Requirements.Inverse` (BOOLEAN NOT NULL) is universally supported on ALL RequirementType.** While only 92 of 1051 `Requirements` rows use Inverse=1 in official data (实测 `SELECT COUNT(*) FROM Requirements WHERE Inverse=1`), the engine respects the column on every type. Use `Inverse=1` on the Requirements row to negate ANY requirement — confirmed safe for `REQUIREMENT_UNIT_TYPE_MATCHES`, `REQUIREMENT_UNIT_TAG_MATCHES`, and all others. Do NOT use `Inverse` as a RequirementArgument (it's a column on the Requirements table, not an argument in RequirementArguments).

13. [G13a] **文本里绝对不可以出现单个 `'`、也不可以用 `\'` 或 `\` —— 唯一的隔离方式是连续两个 `''`**
    SQL 的字符串转义是**两个连续单引号 `''`**，用来与文本两端的定界 `'` 区分开。
    反斜杠**不是**转义符：`\'` 会让字符串在那里提前闭合，`\` 本身也是非法字符。

    | 写法 | 结果 |
    |---|---|
    | `'Penitent''s End'` | ✅ 正确（`''` = 一个字面单引号） |
    | `'Penitent\'s End'` | ❌ 反斜杠非转义符 → 字符串在 `\` 前闭合 → 语法错误 |
    | `'Prophet's Teachings'` | ❌ 单个 `'` → 字符串在 `s` 前闭合 → 语法错误 |
    | 文本里任何裸 `\` | ❌ 非法字符，不要把 Windows 路径、正则、LaTeX 之类原样塞进文本 |

    **为什么必须当成硬性铁律**：
    - 报错的是**整条 `INSERT` 语句**，不是那一行 —— 该语句的**所有行**一起丢失；
    - 引擎/`executescript` **遇错即停**，**同文件后续语句块也全部不执行**；
    - 数据没进库 → 游戏按 `LanguagePriorities` 回退 en_US → **中文环境显示英文**，或直接显示裸 `LOC_` tag。

    实测规模（2026-09-14 修复）：某工程 2 个文件 **14 处**词内撇号
    （en_US 5 处 `Prophet's Teachings` ×3 / `Merchant's Fortune` ×2；fr_FR 9 处 `d'Écrivain` / `d'Amiral`），
    导致 en_US **463 行全丢**（块1 即失败，后续 6 块也不执行）、fr_FR **335 行丢失**，全程无任何构建期报错。
    修复后两文件各入库 463 行，全工程 152/152 SQL 通过。

    **自查**：`python scripts/check_sql_exec.py --root <工程>` —— 它会整文件 `executescript` 并单独列出「未转义的词内撇号」及其**真实行号**。
    另一条纪律：写含文本的 INSERT 时**不要用 PowerShell here-string / 重定向生成**（会引入转义层），用 Python/Node 显式 UTF-8 写入。


13. [G13b] **查询游戏数据 API 首选 SQLite。** `database/api.sqlite` (Lua API) 和 `database/DebugGameplay.sqlite` (游戏数据) 覆盖全部查询需求。详见 SKILL.md Rule 0.4。

14. [G14a] **`MODIFIER_*_ADJUST_PROPERTY` 的 ModifierArgument 用 `Key` + `Amount`；`REQUIREMENT_PLOT_PROPERTY_MATCHES` 的 RequirementArgument 用 `PropertyName` + `PropertyMinimum`。** — ModifierArgument 中无论玩家级还是单位级，设置 PROPERTY 值的参数名都是 `Key`。但 RequirementArgument 中检测 PROPERTY 用的是 `PropertyName`（以及 `PropertyMinimum` 阈值）。二者参数名不同，混用不会报错但永远不生效。`REQUIREMENT_PLAYER_PROPERTY_MATCHES` 等其他 PROPERTY 检测 RequirementType 也沿用 `PropertyName`。

## UI Pitfalls

14. [G14b] **When replacing a UI script**, you must know the exact `LuaContext` ID from the base game's XML. Find these in `Base/Assets/UI/*.xml` — search for `<LuaContext ID="..."`.

15. **PowerShell 5.1 `Set-Content -Encoding UTF8` 会自动写入 BOM。** — SQLite 和 Lua 5.4 不允许 BOM，会导致 `syntax error` 或静默跳过整个文件。替代方案：用 PowerShell 7 (`pwsh`) 的 `Set-Content -Encoding UTF8NoBOM`；或 5.1 下用 `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))`。

16. **`LookUpControl` wildcards** (`*`) cannot be used for the control name itself (the last path segment). Valid: `"*/FrontEndPopup/CloseButton"`. Invalid: `"../FrontEndPopup/*"`.

17. **`SetInputHandler`** with `true` (extended handler) gives you an `inputStruct` table. Without `true` (simple handler), you get raw `(uiMsg, wParam, lParam)`.

18. **Include files copy all content** into the including context's scope. Minimize local variables in them to avoid size bloat and name collisions.

19. [G19a] **UI 上下文禁止直接 `SetProperty`** — UI 侧 `Players[pid]:SetProperty(key, value)` 在多人游戏中不可靠，应统一走 `UI.RequestPlayerOperation(pid, PlayerOperations.EXECUTE_SCRIPT, { OnStart = handlerName, PropertyKey = key, Value = value })`。由 GP 侧 GameEvents handler 执行写入。同样适用于 Delta 增量：`{ PropertyKey = key, Delta = delta }`。handler 命名按项目规范定义。

39. **镜头名必须是引擎已注册镜头** — `UILens.CreateLensLayerHash("自定义名")` 静默不渲染，且无任何报错（症状："点击后无任何动作也没有报错"）。可用 vanilla 镜头：`"Hex_Coloring_Movement"`（绿色范围）、`"Hex_Coloring_Attack"`（红色目标指示）、`"Attack_Range"`（范围层）。目标指示器用三元组 `{"AttackRange_Target", sourcePlot, plotId}`（vanilla WMD 打击同款格式），sourcePlot 为发起地块对象。

40. **Civ 6 是偏移坐标系统（奇偶行错位），手工 `{dx,dy}` 方向偏移只有东西方向正确** — 斜向格按行奇偶错位，症状：1 环高亮"总有一个在 2 环"、同方向直线遍历整体歪斜。邻格遍历一律用引擎函数：`Map.GetAdjacentPlot(x, y, DirectionTypes)`（单格、有序）或 `Map.GetAdjacentPlots(x, y)`（返回 6 邻格，BFS 分层扩展用）。直线延伸：`Map.GetAdjacentPlot(curX, curY, direction)` 逐格迭代。

41. **`LuaEvents.WorldInput_WBSelectPlot` 回调签名固定为 `(plotId, plotEdge, boolDown, rButton)`** — 第 3 参是"按下/释放"（boolDown），不是左键标志；第 4 参才是右键。参数错位会静默失败：左键点击被误判为"释放+右键"直接 return、右键取消失效。悬停地块用 `LuaEvents.WorldInput_WBMouseOverPlot(plotID)`，配合 `Map.GetPlotByIndex`。

42. **WB_SELECT_PLOT 瞄准模式时序三条铁律** — ① `UI.SetInterfaceMode()` **同步**触发 `Events.InterfaceModeChanged`：先切模式再读全局状态会拿到已清空值（如 UnitID=-1 导致请求静默失效），必须先缓存所需值再切模式。② 高亮在 `InterfaceModeChanged(newMode == WB_SELECT_PLOT)` 回调中显示，不要在 SetInterfaceMode 前直接 UILens（避免时序冲突被引擎清除）。③ 瞄准期间 `Events.UnitSelectionChanged` 会被"点击地块上的单位"触发，需特判：发起单位仍存在则不取消瞄准（点击单位应等同点击其所在地块）。

## 本地化文本通道（.modinfo vs UpdateText）—— 放错就是"游戏里看不到字"

一条 LOC tag 在**选 mod 界面**能显示，**不代表**游戏内取得到：这是两条互不相通的通道。

| 用途 | 通道 | 生效范围 |
|---|---|---|
| **mod metadata** —— `Properties` 里的 `Name` / `Teaser` / `Description`（+ `Authors`） | `.civ6proj` 的 `<LocalizedTextData>` → `.modinfo` 的 `<LocalizedText>` | **仅"选择 mod / 额外内容"界面** |
| **游戏内文本** —— 任何被 Lua `Locale.Lookup` 取用、或被 data 列（`Name`/`Description`/…）引用的 LOC | `<UpdateText>` 动作 + `Text/*.sql`（或 XML） | 游戏内（InGame） |
| 配置界面文本 | FrontEnd 的 `<UpdateText>` | 仅 FrontEnd |

规定原文见 `project-setup.md`：`<LocalizedTextData>` 一栏注的是 "Mod metadata text (title/teaser/desc/authors)"；
"**游戏文本** (LocalizedText) → **InGame 仅** → `UpdateText`"。

- **症状**：把游戏内 tag 写进 modinfo → 游戏内显示原始 `LOC_XXX` 键名或空白，而 mod 列表里一切正常。**静默、极易漏测**（开发时只开 mod 列表看一眼是发现不了的）。
- **判定法**：写完自问"这条 tag 谁读？"—— Lua `Locale.Lookup` / data 列引用 → 必须 `UpdateText`；只有 `Properties` 的三个 metadata 字段才归 modinfo。
- **更省事的做法**：先查原版有没有现成 tag（`database/DebugLocalization.sqlite` 逐 tag 查 + 确认八语言齐全），能复用就连 `Text/` 动作都不用加 —— 原版文案还自带全语言、与官方按钮完全一致。
- 反面案例（2026-09-15，AllUnitsFoundCity v1–v3）：把自定义 tooltip / 失败提示两条游戏内 tag 写进了 modinfo 的 `<LocalizedText>`，
  游戏内取不到；最终改为**全部复用原版 tag**（`LOC_UNITOPERATION_FOUND_CITY_DESCRIPTION` 等），自定义游戏内文本清零。

## Type Annotation Pitfalls

19. [G19b] **Havok Script type annotations** (`:number`, `:string`, `:boolean`, `:table`) are optional but help catch errors.

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
    ★ vanilla 实测 66 行，**全部**是 `MODIFIER_PLAYER_DIPLOMACY_*` —— 其中 44 行为
    `..._AGENDA_*`（议程需要周期性重估），另 **22 行不含 `_AGENDA_`**（誓约 / 承诺 / 第三方评价等，
    共 13 个 ModifierType，最多的是 `..._THIRD_PARTY_EFFECTS` 8 行）。
    所以规律是"**外交类**修饰符普遍挂 `ON_TURN_STARTED`"，**不是**"只有议程才挂"。
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

    ★ **实机复核（2026-09-14 FireTuner · gamecore · `DB.Query`）—— 与内存 SQLite 结论完全一致**：

    | 探针 | 结果 |
    |---|---|
    | `SELECT ('%a%' OR '%b%'), typeof('%a%' OR '%b%')` | `0` / **`integer`** |
    | `SELECT 'abc' WHERE 'abc' LIKE ('%a%' OR '%b%')` | **0 行** |
    | `SELECT '0' WHERE '0' LIKE ('%a%' OR '%b%')` | **命中**（证实"只匹配字面量 0"） |
    | `SELECT 'abc' WHERE 'abc' LIKE '%a%' OR 'abc' LIKE '%b%'` | 命中 |

    真实运行时库（`Types` 表）全库检索对照：

    | 查询 | 命中 |
    |---|---|
    | `Type LIKE '%TRAIT%' OR Type LIKE '%POLICY%'` | **627** |
    | `Type LIKE ('%TRAIT%' OR '%POLICY%')` | **0** |
    | 三关键词版（UNIT / BUILDING / DISTRICT）正确 / 错误 | **1402 / 0** |

    > 引擎的 SQLite 与标准 SQLite 行为一致（字符串→数值强制转换为 0，`typeof` = `integer`）。
    > 危险点在于：在恰好有 `'0'` 值的列上，错误写法会给出**看似有结果、实则完全无关**的答案 —— 比"返回空"更难发现。
    > 复现探针存档：`civ6-tuner/snippets/sql_like_trap.lua`（`exec --context gamecore --file …`）。

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

## UI / GP 双端 API 面差异（工程实测）

> **证据口径**：本节条目来自**工程实测**（家族内工程的实机观测），均为**项目断言、未经独立复核**；
> 需要独立佐证时查 `database/api.sqlite` 的 `verify_status` / `runtime_gp` / `runtime_ui` 三列
> （2026-09-08 FireTuner 全量实测，见 SKILL.md「API 核验字段」）。

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

---

## UI 显隐检定（"该隐没隐"的两类静默故障 · 2026-09 复盘）

65. **检定内部抛错 = 显隐状态被冻在上一次结果上，极易误判成"判定规则写错"**
    UI 按钮的检定函数若直接 `for _, id in ipairs(PlayerManager.GetAliveIDs()) do … pOther:GetCities():Members() …`，
    只要某个玩家拿到 `nil` 的 `GetCities()`（或某接口在某个版本 / 上下文缺席），异常会顺着
    `检定 → 刷新函数 → 事件回调` 抛出去：**刷新中途中止，控件保持上一次的 `SetHide` 状态**。
    症状：按钮"偶尔/中后期一直亮着"，单位换位置也不更新（因为压根没重算完）。
    处方（两条一起上）：
    ```lua
    -- ① 对外入口 fail-safe：检定额外抛错一律按"隐藏"处理
    --    理由：按钮语义是"点了就能成"（GP 侧还会复核），宁可少显示，不给点了也不成的按钮
    function MyIsButtonHidden(pUnit)
        local ok, bHidden = pcall(MyEvaluateButtonHidden, pUnit);
        return (not ok) or (bHidden == true);
    end
    -- ② 集合遍历判空 + pairs（见 #63），异常不外溢
    for k, id in pairs(PlayerManager.GetAliveIDs() or {}) do
        if type(k) == "number" then
            local p = Players[id];
            if p and p:IsAlive() then
                local pCities = p:GetCities();
                if pCities then for _, c in pCities:Members() do … end end
            end
        end
    end
    ```
    排查手法：把检定拆成「内部实现 + 外层 `pcall` 包装」，就能一眼区分"判定确实返回了 true"与"检定额外抛错"。

66. **"N 格内有无城市"这类判定：地块层判据比玩家枚举更可靠；`GetNeighborPlots` 的环语义已实测定案**
    `Map.GetNeighborPlots(x, y, range)` 返回的是**含中心格的实心盘**（2026-09-16 FireTuner 实测：
    r=1/2/3/4 → n=7/19/37/61，`含中心格数=1`，覆盖距离 0..r 的全部地块），**不是"正好第 r 环"**
    （"正好第 r 环"是 GP 专有的 `Map.GetRingPlots`）。因此"半径内存在 X"直接按 `range` 取盘即可：
    ```lua
    local function HasCityWithin(x, y, ring)
        for r = 0, ring do                       -- r=0 即中心格，逐层叠加，语义无关
            for k, p in pairs(Map.GetNeighborPlots(x, y, r) or {}) do
                if type(k) == "number" and p and p:IsCity() then return true end
            end
        end
        return false
    end
    ```
    `Plot:IsCity()` 是**地块数据**（双端实测可用），与城市归属无关 —— 自己的 / 其他文明 / 城邦 / 自由城市的城心
    一律算数，不受 `Players` / `PlayerManager` 枚举是否完整影响；
    `Map.GetPlotDistance()` 逐城比对（`Player:GetCities():Members()`，各自判空）留作兜底，
    覆盖"地块标记与城市列表不同步"的边角。**两层同口径叠加，比单靠任一层都稳。**

67. **建城地块的权威判据是引擎自己的 `IsValidFoundLocation`；`CITY_MIN_RANGE` 是"含端点的禁止半径"**
    （2026-09-16 FireTuner 实测定案，别再用推断）

    | 接口 | 端 | 语义 |
    |---|---|---|
    | `Plot:IsValidFoundLocation()` | **UI + GP 均可** | 一次调用覆盖 间距 / 地形 / 地貌 / 水域 / 已有城市·区域 / 领土 |
    | `Player:GetCities():IsValidFoundLocation(x, y)` | 仅 GP | 同一口径；实测与上面**逐格结果完全一致** |

    实测样本：首都为中心逐环扫 1..5 环（90 个地块），两端作对照 ——
    **ring 1 / 2 / 3 全 false，ring 4 起才出现 true**（false 的那些是水域/山等本身不可建的地块）。

    结论：`GameInfo.GlobalParameters["CITY_MIN_RANGE"]`（原版 **3**）是**禁止半径且含端点**，
    即"距任意城市中心 **<= 3** 格不可建城"，**合法间距是 `距离 > CITY_MIN_RANGE`**（第 4 环才是第一个合法位）。
    → 手写间距检定必须写 `<=`，写成 `<` 会**恰好放宽一格**（距城 3 格多显示按钮，点下去才被 GP 驳回、按钮静默消失）。
    → 更稳的写法：把引擎裁定当主口径，手写规则只做它缺席时的兜底：
    ```lua
    local ok, bValid = pcall(function() return pPlot:IsValidFoundLocation() end);
    if ok and bValid == false then return false end   -- 引擎说不行就不行
    -- 引擎接口缺席 → 用本地自算（`<= CITY_MIN_RANGE`）兜底
    ```
    同类参数别按字面猜方向（"MIN_RANGE = 最小间距" 是错的读法）；**数值语义一律实机扫一遍边界再写死。**

68. **换行分层铁律：资产类文本一律 LF，代码/配置类一律 CRLF**（2026-09-16 原版随机抽样定案）

    原版实况（Base / DLC / SDK Assets 各随机 ≤40，非全量遍历）：

    | 目标 | 扩展名 | 抽样实况 |
    |---|---|---|
    | **LF** | `.artdef` | 38/40 LF |
    | **LF** | `.ast` `.mtl` `.geo` `.env` `.anm` `.xlp` `.lrg` `.tex` `.txt` | 25/25 文本，全 LF |
    | **CRLF** | `.lua` / `.xml` / `.modinfo` | 40/40 CRLF |
    | **CRLF** | `.sql` | 17/17 CRLF |

    **成因**：AssetEditor / cooker 输出的资产类文本**恒为 LF**；而 Lua/SQL/XML 这类代码与配置原版**恒为 CRLF**。

    **为什么必须钉死**（本机 `core.autocrlf=true`）：不在 `.gitattributes` 里钉死，
    checkout 会把 LF 资产写成 CRLF，于是「源 ↔ Mods 副本 ↔ cook 产物」出现**永久伪差异**，
    diff 噪声淹没真实改动（`.artdef` 早年正是因此被迫 `text eol=lf`，见 `civ6-art-reference/reference/cook-layer.md §2.3`）。

    ★ **`.txt` 按目录分**：`Platforms/Windows/Audio/` 下原版是 `.txt`=LF(51) 但 `.xml`=**CRLF(63)**、`.ini`=**CRLF(1)**
    —— 不能只看扩展名，音频目录要按「txt→LF、xml/ini→CRLF」分别对待。

    ★ **真二进制绝不能按文本处理**：`.fgx`(25/25) 与 `.wig`(25/25) 实测含 **NUL 字节**，
    所谓"换行"只是字节碰巧命中 `0x0A`，**语义上不存在换行**；`.dds` 同理。
    归一化脚本必须**按扩展名排除 + 逐文件 NUL 探测双重把关**。

    **施工与体检**：`python civ6-modding/scripts/normalize_eol.py <工程目录>`（默认只报告，`--fix` 才写盘）。
    工程侧在 `.gitattributes` 落实：

    ```gitattributes
    *.lua  text eol=crlf
    *.sql  text eol=crlf
    *.xml  text eol=crlf
    *.artdef text eol=lf
    *.xlp    text eol=lf
    *.txt    text eol=lf
    *.fgx  -text -diff -merge binary   # 真二进制
    ```

    **验收口径**：改完换行后 `git diff <文件>` 应当**为空**（`core.autocrlf` 下 CRLF/LF 归一为同一 blob）
    —— 若出现内容 diff，说明改动**不止换行**，必须回头查。
    另注意：工作区被重写后 `git status` 可能因 **stat 缓存过期**列出大量 `M`；
    用
    ```bash
    git add -A && git diff --cached --numstat   # 只有换行时这里应无输出
    git reset -q
    ```
    判定真实内容变更（实测：`status` 报 48 个 `M`，而 `--cached` 与逐文件 `git diff` 均为 0）。



69. **`luac -p` 对 Civ6 的 Lua 是「部分可信」：类型标注语法必报假错，必须差分判定**（2026-09-16 实测）

    Civ6 的 Lua 含 **Lua 5.1 不认识的类型标注**，例如：

    ```lua
    local kDiscoveredImages:table = {};      -- vanilla 全量替换文件里就有这句
    ```

    `luac -p` 会报 `unexpected symbol near ':'`。**这不是文件坏，是方言比 5.1 新。**

    ★ **要害：源文件与 Mods 副本同样报错**。所以任何"剥离/改写后跑 `luac -p` 自检"的流程，
    若只看**结果**不过就判失败，会对这类文件**每次都误报**——
    本项目实测：`strip_comments.py` 因 `ImportFiles/OfficialOverrides/SecretSocietyPopup.lua`
    恒定 `exit 1`，**真失败会被淹没在噪声里**（发布流程长期带着一个假红灯）。

    **正确做法 —— 差分判定**：先验原文、再验结果，只在「原文能过 → 结果不过」时报错：

    ```python
    ok_before = luac_check_text(raw)
    ok_after  = luac_check_text(stripped)
    if ok_before and not ok_after:      # 只有这个组合才是「我改坏了」
        fail()
    elif not ok_before:                 # 既存方言问题，跳过并计数提示
        preexisting += 1
    ```

    实测该项目：47 个 `.lua` 通过、1 个既存误报（`SecretSocietyPopup.lua`）、真失败 0
    —— 与源工程同口径（源也是 47 通过 / 1 误报），据此确认剥离无副作用。

    **同类判断**：本机唯一可用版本是 `E:\SoftWares\Lua\5.1\luac.exe`（`_paths.py` 的 `luac` 键）。
    任何"用 luac 当质量门"的脚本都要先确认它对目标文件**在改动前**是过的，
    否则把工具自身的方言局限当成了代码缺陷。



70. **图集「结构全对、实机却锯齿」= 中间档 alpha 被锐化/压对比；结构校验永远查不出**（2026-09 实测）

    症状：游戏内图标（尤其 frontend 小档，如领袖 45px）肉眼可见线条锯齿、硬边、毛刺。

    根因：图集**中间档**（32/45/50/80/128…）本应从最高分辨率母版逐格等比降采样，
    但实际常被**锐化或对比拉伸（levels）**处理过（或由已缩小过的图再缩）。
    这会把抗锯齿的过渡像素推向 alpha 两端，边缘退化成"二值硬边"。
    **母版（256）往往完全健康**，所以看母版永远看不出问题。

    ★ **要害：这类损伤结构上完全合法** —— 引用闭合、画布尺寸对、`.tex` 对齐、格子非空、
    mips=1，`verify_icon_atlas.py` 的**结构项全部 PASS**。本项目 2026-09 实测
    `DISTRICTS`(6) / `PRODUCT`(5) / `RESOURCES`(4) / `LEADERS`(7) 共 **22 个中间档**中招，
    结构校验一路绿灯，而实机图标全是锯齿。**只有 `--edge-qa` 能发现。**

    量化判据（边界像素口径；参考值 = 母版逐格 LANCZOS 重出）：

    | 指标 | 健康 | 受损（LEADERS 45px 实测） |
    |---|---|---|
    | 边界中间调 (20..235) 占比 | 43~48% | **20.4%**（原版 45.1%） |
    | 二值端 (≤8 或 ≥247) 占比 | ~50% | **74.7%** |
    | 过渡像素 ÷ 边界周长 | 1.8 | **0.59** |
    | 不透明区 Laplacian 方差 | ~7400 | **23026**（锐化残留） |

    **反直觉点**：受损档的**内部高频反而更高**（锐化放大噪点）。所以"清晰度"不能只看
    高频能量，要看边缘过渡是否**单调连续** —— 修复后过渡更宽（更软），观感却更清晰。

    修复：`python art/regen_atlas_tiers.py <projectRoot> --report --write-damaged`
    从 256 母版逐格 LANCZOS 重出，**尺寸不变，`.tex` / 网格 / 注册链都不用动**。

    ⚠ **配套陷阱**：素材目录里常有**每档一份的独立 PNG**（`ATLAS_X32.png`、`ATLAS_X45.png`…），
    这些小档 PNG **本身就是受损产物**。若把它们当"源素材"重跑 `make_atlas.py`，
    损伤会被**原样再产出一遍**（表现为"修了又变回锯齿"）。
    **图集重建一律只用最大档当母版**；本项目
    `D:\desktop\Material\Image-Rinascita\Atlas_Rgn\*_Atlas\` 下的小档 PNG 全属此类。

    完整机制、逐档实测与对照图见 `art-pipeline.md` 第 8.1 节。



71. **`.tex` 的"官方格式"不是一套常量：`bCompleteMipChain` 按类别不同，`UserInterface` 是 69/31 分裂**（2026-09 实测）

    想"把 `.tex` 对齐官方"时容易犯的错：拿某一个官方样本当模板全局套用。
    对全 SDK **12709 个 `.tex`** 做统计后，事实是：

    | 字段 | 官方真实情况 |
    |------|------------|
    | XML 声明 + 字节编码 | **100% UTF-8**（唯一真正全局一致的字段） |
    | 行尾 | **100% LF** |
    | `bCompleteMipChain` | **按 `m_ClassName` 分裂**：`Generic_*`/`StrategicView_*`/`Leader_*` 等几乎 100% `true`；`TerrainElementHeightmap`/`ColorKey` 等 100% `false`；**`UserInterface` 是 `true` 69% / `false` 31%** |
    | `m_Groups` | 多数自闭合 `<m_Groups/>`，但 `UserInterface` 有 25% 直接缺失 → **缺失也不算错** |
    | `m_CookParams` | `UserInterface` 有 **51%** 是空 `<m_Values/>` → **空 cook 完全合法**，别当缺失去补 |
    | `useMips` | **由 DDS 实际 mips 决定**（不是类别）：`StrategicView_Sprite` 100% `true`；`UserInterface` 100% `false`（其 DDS 多带 mip）；不变量是 `m_NumMipMaps = DDS mips - 1` |

    ★ **要害**：`bCompleteMipChain` 与 `m_Groups` 这类字段**不能一刀切**。正确做法是按
    `m_ClassName` 分组统计官方分布，**只对"同类别一致率 ≥80%"的类**套用，
    分裂的类（`UserInterface`）**保持原值不动**。工具 `art/align_tex_format.py`
    内置的 `COMPLETE_POLICY` 表就是这个策略。

    ⚠ **改编码前必须确认内容为纯 ASCII**：`gen_tex.py` 的警告（「.tex 写 UTF-8 会被
    AssetEditor 按 GBK 误读并崩溃」）**只在内容含非 ASCII 字节时成立**。
    ASCII 在 GBK/UTF-8 下字节完全相同 → 改声明+改编码零风险。若源路径含中文则**不可**改。
    参见 `art-pipeline.md` 第 8.2 节。

    ⚠ **`m_SourceFilePath` 是不可对齐项**：官方是 `//civ6/main/ArtDev/...` depot 路径，
    但本工程（及多数 mod 工程）的约定是 `D:/desktop/<stem>.png` **ASCII 虚拟路径** ——
    照抄官方会破坏 pom 约定甚至让 AssetEditor 崩溃。**格式对齐只针对格式类字段，值类字段一律不碰。**





