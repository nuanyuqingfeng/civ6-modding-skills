-- ===========================================================================
-- event_matrix.lua —— 事件存在性矩阵（同一份脚本两端对跑）
--   用法： ① 在下面 CONFIG.EVENTS 里填要查的事件名
--          ② python tuner_exec.py exec --both --file snippets/event_matrix.lua
--   判定：table = 该端有此事件（可 .Add/.Remove）；nil = 该端没有
--
--   ⚠ 两条铁律：
--     1) `GameEvents` 在 **UI 上下文整条总线不存在**（实测 type(GameEvents)==nil）。
--        被 UI 加载的文件里出现 GameEvents.* → 必然 "attempt to index a nil value"，
--        且会中断该 chunk 使其后语句全部不执行。
--     2) `Events.*` 与 `GameEvents.*` 是两条互不镜像的总线：
--        引擎 GameCoreEvent 只进 Events.*；GameEvents.* 只承载 Lua 级事件。
--        `GameEvents.X` 对任意名字都自动建 table —— **不能用 type() 判断"事件是否存在"**，
--        只有 `type(Events.X)` 是权威探针。
-- ===========================================================================

-- ===== CONFIG：要探测的事件名（两端都会查 Events.* 与 GameEvents.*） =====
local CONFIG = {
    EVENTS = {
        -- 引擎事件（预期两端都有）
        "PlayerTurnActivated", "PlayerTurnDeactivated", "CityAddedToMap", "CityOccupationChanged",
        "CapitalCityChanged", "CityLoyaltyChanged", "CityReligionChanged", "ReligionFounded",
        "BeliefAdded", "PlayerEraChanged", "ResearchCompleted", "CivicCompleted",
        "UnitAddedToMap", "UnitKilledInCombat", "UnitSelectionChanged", "UnitMoveComplete",
        "UnitGreatPersonCreated", "UnitGreatPersonActivated", "GovernmentPolicyChanged",
        "GamePropertyChanged", "LoadGameViewStateDone", "Combat", "PlayerOperationComplete",
        -- 下面这些若在 Events 里为 nil、只在 GameEvents 里有 → 属 Lua 级事件
        "PlayerTurnStarted", "CityConquered", "PolicyChanged",
    },
    -- 项目自定义事件（只可能在 GameEvents 上，且只在注册过的那一端非 nil）
    CUSTOM = {
        "RGNSetProperty", "PHBApplyGift", "RCCFinish", "HocusActivate",
        "CTTHSetSlotBuff", "CTRLAddDivinityBuffs",
    },
}

local function T(v) if v == nil then return "nil" end return type(v) end

local function main()
    print("===== 总线自身 =====")
    print(string.format("  %-24s %s", "Events", T(Events)))
    print(string.format("  %-24s %s", "GameEvents", T(GameEvents)))
    print(string.format("  %-24s %s", "LuaEvents", T(LuaEvents)))
    print(string.format("  %-24s %s", "ReportingEvents", T(ReportingEvents)))
    print("")
    print("===== Events.* vs GameEvents.* =====")
    print(string.format("  %-34s %-12s %-12s", "事件名", "Events", "GameEvents"))
    for _, n in ipairs(CONFIG.EVENTS) do
        local e = Events and Events[n]
        local g = GameEvents and GameEvents[n]
        print(string.format("  %-34s %-12s %-12s", n, T(e), T(g)))
    end
    print("")
    print("===== 项目自定义 GameEvents.* =====")
    for _, n in ipairs(CONFIG.CUSTOM) do
        print(string.format("  %-34s %s", n, T(GameEvents and GameEvents[n])))
    end
    print("")
    print("判读：")
    print("  · Events.X=table 且 GameEvents.X=table → 两条总线都有（少见）")
    print("  · Events.X=nil   且 GameEvents.X=table → Lua 级事件，仅 GP 侧可用")
    print("  · UI 端 GameEvents=nil → 该端任何 GameEvents 用法都会崩，必须改走 Events.* 或下沉到 GP 初始化入口")
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
