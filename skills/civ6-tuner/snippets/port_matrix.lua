-- ===========================================================================
-- port_matrix.lua —— GP / UI 端口存在性矩阵（同一份脚本两端对跑）
--   用法： python tuner_exec.py ports
--      或： python tuner_exec.py exec --both --file snippets/port_matrix.lua
--
--   设计要点：
--     · 只做「索引不调用」（type(obj.member)），不触发任何副作用
--     · 实例方法通过真实实例索引，避免"测错对象"导致的假结论
--     · 结论口径：function=可用 / nil=该端没有此成员 / ERR=命名空间或实例在该端不存在
--
--   ⚠ 铁律：判定端口合法性，必须在【调用方所在的那一端】实测。
--     在 GP 测出 nil 不代表"API 不存在"——可能只是 UI-only（反之亦然）。
-- ===========================================================================

-- ===== CONFIG：需要额外探测的「全局命名空间 → 成员」清单（按需追加） =====
local CONFIG = {
    -- 形如 { "命名空间", {"成员1","成员2"} }
    { "Game",                 { "SetProperty", "GetProperty", "GetRandNum", "GetEras",
                                "GetGreatPeople", "ChangePlayerEraScore", "GetCurrentGameTurn" } },
    { "UnitManager",          { "InitUnit", "RestoreMovement", "Kill", "InitUnitValidAdjacentHex",
                                "CanFormMilitaryFormation" } },
    { "CityManager",          { "DestroyDistrict", "GetCity" } },
    { "PlayerManager",        { "GetAliveMajorIDs", "GetAliveBarbarianIDs" } },
    { "NotificationManager",  { "SendNotification" } },
    { "GameEffects",          { "GetModifierActive", "GetModifierArgumentString" } },
    { "GameRandomEvents",     { "ApplyEvent" } },
    { "ImprovementBuilder",   { "SetImprovementPillaged", "SetImprovementType" } },
    { "TerrainBuilder",       { "SetFeatureType" } },
    { "ResourceBuilder",      { "SetResourceType" } },
    { "RouteBuilder",         { "SetRouteType" } },
    { "UI",                   { "PlaySound", "GridToWorld", "AddTemporaryPlotVisibility",
                                "RequestPlayerOperation", "LookAt" } },
    { "AssetPreview",         { "Create", "SetInstanceCulling", "SetInstanceAnimation",
                                "SetInstanceAutoDestroy" } },
    { "Locale",               { "Lookup" } },
    { "ReportingEvents",      { "SendLuaEvent" } },
}

local function S(v) if v == nil then return "nil" end return tostring(v) end

-- 安全索引：obj[member]，obj 本身不存在时返回 ERR
local function idx(obj, member)
    if obj == nil then return "ERR" end
    local ok, v = pcall(function() return obj[member] end)
    if not ok then return "ERR" end
    return type(v)
end

local function line(label, t)
    print(string.format("  %-48s %s", label, t))
end

-- ---------- 0. 总线 / 命名空间自身 ----------
local function buses()
    print("===== BUS: 总线与命名空间 =====")
    for _, n in ipairs({ "Events", "GameEvents", "LuaEvents", "ReportingEvents",
                         "ExposedMembers", "Players", "GameInfo", "Game", "Map",
                         "UI", "Controls", "ContextPtr", "Locale" }) do
        local v
        if n == "Events" then v = Events
        elseif n == "GameEvents" then v = GameEvents
        elseif n == "LuaEvents" then v = LuaEvents
        elseif n == "ReportingEvents" then v = ReportingEvents
        elseif n == "ExposedMembers" then v = ExposedMembers
        elseif n == "Players" then v = Players
        elseif n == "GameInfo" then v = GameInfo
        elseif n == "Game" then v = Game
        elseif n == "Map" then v = Map
        elseif n == "UI" then v = UI
        elseif n == "Controls" then v = Controls
        elseif n == "ContextPtr" then v = ContextPtr
        elseif n == "Locale" then v = Locale
        end
        line(n, type(v))
    end
end

-- ---------- 1. 配置清单 ----------
local function namespaces()
    print("")
    print("===== NS: 全局命名空间成员 =====")
    for _, entry in ipairs(CONFIG) do
        local nsName, members = entry[1], entry[2]
        local ns
        if nsName == "Game" then ns = Game
        elseif nsName == "UnitManager" then ns = UnitManager
        elseif nsName == "CityManager" then ns = CityManager
        elseif nsName == "PlayerManager" then ns = PlayerManager
        elseif nsName == "NotificationManager" then ns = NotificationManager
        elseif nsName == "GameEffects" then ns = GameEffects
        elseif nsName == "GameRandomEvents" then ns = GameRandomEvents
        elseif nsName == "ImprovementBuilder" then ns = ImprovementBuilder
        elseif nsName == "TerrainBuilder" then ns = TerrainBuilder
        elseif nsName == "ResourceBuilder" then ns = ResourceBuilder
        elseif nsName == "RouteBuilder" then ns = RouteBuilder
        elseif nsName == "UI" then ns = UI
        elseif nsName == "AssetPreview" then ns = AssetPreview
        elseif nsName == "Locale" then ns = Locale
        elseif nsName == "ReportingEvents" then ns = ReportingEvents
        end
        for _, m in ipairs(members) do
            line(nsName .. "." .. m, idx(ns, m))
        end
    end
end

-- ---------- 2. 实例方法（关键：避免测错对象） ----------
local function instances()
    print("")
    print("===== INST: 实例方法（玩家 0 起） =====")
    local pid = 0
    local pl = Players[pid]
    if not pl then line("Players[0]", "nil"); return end
    for _, m in ipairs({ "SetProperty", "GetProperty", "GetEras", "GetCulture", "GetReligion",
                         "GetTreasury", "GetDiplomacy", "GetStats", "GetGreatPeoplePoints",
                         "GetTechs", "GetInfluence" }) do
        line("Player." .. m, idx(pl, m))
    end

    local cap = pl:GetCities():GetCapitalCity()
    if cap then
        for _, m in ipairs({ "SetProperty", "GetProperty", "GetPlot", "GetBuildQueue",
                             "GetBuildings", "GetGrowth", "GetDistricts", "GetPopulation" }) do
            line("City." .. m, idx(cap, m))
        end
        local bq = cap:GetBuildQueue()
        for _, m in ipairs({ "CreateBuilding", "AddProgress", "CreateUnit" }) do
            line("CityBuildQueue." .. m, idx(bq, m))
        end
        local bld = cap:GetBuildings()
        for _, m in ipairs({ "RemoveBuilding", "HasBuilding" }) do
            line("CityBuildings." .. m, idx(bld, m))
        end
        -- ⚠ 典型陷阱：CityGrowth 的成员是 UI-only，但它是【City 的子对象】而非 City 本身
        local gr = cap:GetGrowth()
        for _, m in ipairs({ "GetAmenities", "GetAmenitiesNeeded", "GetFood", "GetGrowthThreshold" }) do
            line("CityGrowth." .. m, idx(gr, m))
        end
    else
        line("City.*", "无首都，跳过")
    end

    local plot = cap and Map.GetPlot(cap:GetX(), cap:GetY())
    if plot then
        for _, m in ipairs({ "SetProperty", "GetProperty", "GetYield", "GetOwner",
                             "GetTerrainType", "IsCity" }) do
            line("Plot." .. m, idx(plot, m))
        end
    end

    local unit = nil
    for _, u in pl:GetUnits():Members() do unit = u; break end   -- ⚠ 必须 (_, u) 双返回
    if unit then
        for _, m in ipairs({ "SetProperty", "GetProperty", "SetDamage", "GetDamage",
                             "SetMilitaryFormation", "GetMilitaryFormation", "GetMovesRemaining" }) do
            line("Unit." .. m, idx(unit, m))
        end
        -- ⚠ 典型陷阱：GetAbilityCount 不在 Unit 上，而在 Unit:GetAbility() 返回的对象上
        local ok, ab = pcall(function() return unit:GetAbility() end)
        if ok and ab then
            for _, m in ipairs({ "GetAbilityCount", "ChangeAbilityCount", "AddAbilityCount",
                                 "CanHaveAbility" }) do
                line("Unit:GetAbility()." .. m, idx(ab, m))
            end
        end
    else
        line("Unit.*", "本刻无单位，无法判定实例方法（换个有单位的时机重跑）")
    end

    -- ⚠ 典型陷阱：Game.GetGreatPeople 的成员分端口（GetPastTimeline 仅 UI）
    local gp = Game.GetGreatPeople and Game.GetGreatPeople()
    for _, m in ipairs({ "GetTimeline", "GetPastTimeline", "RecruitPerson", "GrantPerson",
                         "CreatePerson", "CanRecruitPerson", "IsClassAvailable",
                         "CountPeopleReceivedByPlayer" }) do
        line("GreatPeople." .. m, idx(gp, m))
    end
end

-- ---------- 3. 事件总线名（可选：由 event_matrix.lua 专管） ----------
local function main()
    print("=== 端口矩阵（本端） ===")
    buses()
    namespaces()
    instances()
    print("")
    print("提示：本脚本请用 `tuner_exec.py ports` 或 `exec --both` 两端对跑；")
    print("      单端结果不足以判定可用性（nil 可能只是另一端专有）。")
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
