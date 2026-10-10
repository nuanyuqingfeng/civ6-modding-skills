-- ===========================================================================
-- member_enum.lua —— 摸清一个对象的真实成员（对抗"测错对象"与文档不可信）
--   用法：改 CONFIG.PATH 后跑；两端各跑一次可看出成员是否分端口
--     python tuner_exec.py exec --both --file snippets/member_enum.lua
--
--   为什么需要它：
--     · 多数对象是 userdata 支撑，`pairs()` 只能看到 `__instance`，
--       必须**按候选名逐个 type() 探测**（或先查 api.sqlite 拿候选名列表）。
--     · 同一方法常不在你以为的对象上。实测反例：
--         `Unit:GetAbilityCount`        → nil
--         `Unit:GetAbility():GetAbilityCount` → function   ← 真身在子对象上
--         `Player:GetGreatPeoplePoints():GetPastTimeline` → nil
--         `Game:GetGreatPeople():GetPastTimeline`         → UI 端 function / GP 端 nil
--       结论：**测 API 前先确认「对象对不对」+「端对不对」。**
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    PLAYER_ID = 0,
    -- 要枚举的对象：从下面几种里挑一种
    PATH = "greatpeople",   -- player | cities | capital | citygrowth | buildqueue | buildings
                            -- | unit | unitability | plot | game | greatpeople | diplomacy
                            -- | religion | stats | gppoints
    -- 已知候选名（来自 api.sqlite 或文档）；留空则只做 pairs() 扫描
    CANDIDATES = {
        "GetTimeline", "GetPastTimeline", "RecruitPerson", "GrantPerson", "CreatePerson",
        "CanRecruitPerson", "CanPatronizePerson", "GetPatronizeCost", "IsClassAvailable",
        "CountPeopleReceivedByPlayer", "GetEarnConditionsText",
    },
}

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function pick()
    local pl = Players[CONFIG.PLAYER_ID]
    local cap = pl and pl:GetCities():GetCapitalCity()
    local p = CONFIG.PATH
    if p == "player" then return pl
    elseif p == "cities" then return pl and pl:GetCities()
    elseif p == "capital" then return cap
    elseif p == "citygrowth" then return cap and cap:GetGrowth()
    elseif p == "buildqueue" then return cap and cap:GetBuildQueue()
    elseif p == "buildings" then return cap and cap:GetBuildings()
    elseif p == "plot" then return cap and Map.GetPlot(cap:GetX(), cap:GetY())
    elseif p == "game" then return Game
    elseif p == "greatpeople" then
        local ok, v = pcall(function() return Game.GetGreatPeople() end); return ok and v or nil
    elseif p == "gppoints" then return pl and pl:GetGreatPeoplePoints()
    elseif p == "diplomacy" then
        local ok, v = pcall(function() return pl:GetDiplomacy() end); return ok and v or nil
    elseif p == "religion" then
        local ok, v = pcall(function() return pl:GetReligion() end); return ok and v or nil
    elseif p == "stats" then
        local ok, v = pcall(function() return pl:GetStats() end); return ok and v or nil
    elseif p == "unit" then
        for _, u in pl:GetUnits():Members() do return u end
        return nil
    elseif p == "unitability" then
        for _, u in pl:GetUnits():Members() do
            local ok, ab = pcall(function() return u:GetAbility() end)
            if ok and ab then return ab end
        end
        return nil
    end
    return nil
end

local function main()
    print("=== member_enum: PATH=" .. CONFIG.PATH .. " ===")
    local obj = pick()
    print("对象 = " .. S(obj) .. " (" .. type(obj) .. ")")
    if obj == nil then
        print("对象为 nil —— 可能该端不存在 / 该实体本刻不存在（注意区分！）")
        return
    end

    print("")
    print("--- pairs() 扫描（多数对象只有 __instance） ---")
    local n = 0
    for k, v in pairs(obj) do
        n = n + 1
        if n <= 40 then print(string.format("   %-36s %s", S(k), type(v))) end
    end
    print("   成员数 = " .. n)

    if #CONFIG.CANDIDATES > 0 then
        print("")
        print("--- 候选名逐个索引（只探测不调用） ---")
        for _, m in ipairs(CONFIG.CANDIDATES) do
            local ok, v = pcall(function() return obj[m] end)
            print(string.format("   %-36s %s", m, ok and type(v) or ("ERR:" .. tostring(v):sub(1, 40))))
        end
    end

    print("")
    print("提示：本端 nil ≠ 不存在 —— 可能只是「另一端专有」。请用 --both 对跑再下结论。")
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
