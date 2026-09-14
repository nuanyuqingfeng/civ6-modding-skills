-- cheat_setup.lua —— 造测试条件：金币/信仰/刷单位/完成科技
-- 上下文：ingame（写操作）
-- 用法：python tuner_exec.py exec --context ingame --file snippets\cheat_setup.lua

-- ==== CONFIG（按需打开开关）====
local PID = Game.GetLocalPlayer()
local SET_GOLD = nil          -- 设为具体数字如 10000 即生效；nil 跳过
local ADD_FAITH = nil         -- 增量信仰，如 5000；nil 跳过
local SPAWN_UNIT = nil        -- 单位类型串，如 "UNIT_BUILDER"；nil 跳过
local COMPLETE_TECH = nil     -- 科技类型串，如 "TECH_BRONZE_WORKING"（待实测）
-- ==============================

local pPlayer = Players[PID]

if SET_GOLD then
    pPlayer:GetTreasury():SetBalance(SET_GOLD)
    print("Gold -> " .. tostring(math.floor(pPlayer:GetTreasury():GetBalance())))
end

if ADD_FAITH then
    pPlayer:GetReligion():SetFaithBalance(
        pPlayer:GetReligion():GetFaithBalance() + ADD_FAITH)
    print("Faith -> " .. tostring(math.floor(pPlayer:GetReligion():GetFaithBalance())))
end

if SPAWN_UNIT then
    -- 首都旁找空地格刷单位
    local pCity = pPlayer:GetCities():GetCapitalCity()
    if pCity == nil then
        print("ERR:无首都，无法定位刷兵点")
    else
        local loc = pCity:GetLocationLowerLeft() or pCity:GetLocation()
        local unit = UnitManager.InitUnit(PID, SPAWN_UNIT, loc.x + 1, loc.y)
        if unit then
            print("SPAWNED " .. SPAWN_UNIT .. " @ (" .. (loc.x + 1) .. "," .. loc.y .. ")")
        else
            print("ERR:InitUnit 失败（检查类型名/坐标占用）")
        end
    end
end

if COMPLETE_TECH then
    -- 【待实测】SetResearchProgress 满 progress 完成科技的写法未在真机验证，
    -- 失败请改用 World Builder 或注释掉本段
    local techs = pPlayer:GetTechs()
    local tech = GameInfo.Technologies[COMPLETE_TECH]
    if tech then
        techs:SetResearchProgress(tech.Index, tech.Cost, PID)
        print("SET_PROGRESS " .. COMPLETE_TECH .. " (待确认是否已完成)")
    else
        print("NOT_FOUND: Technologies['" .. COMPLETE_TECH .. "']")
    end
end
