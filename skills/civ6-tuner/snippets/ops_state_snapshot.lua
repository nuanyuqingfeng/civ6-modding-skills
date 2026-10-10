-- ops_state_snapshot.lua —— 玩家全状态快照（2026-10-02/03 实测核对的方法名）
-- 上下文：ingame（CityGrowth 的宜居度方法只在 UI 侧，见铁律 5）
-- 用法：python tuner_exec.py exec --context ingame --file snippets\ops_state_snapshot.lua
-- ⚠ 单位清单跑在 UI 侧，会带出刚被 Kill 的「幽灵单位」并回报旧数值（2026-10-03 实测，
--   见 reference/PORT_MATRIX.md 九）——重要读数以 gamecore 复核或 exec --both 对跑

-- ==== CONFIG ====
local MAX_UNITS = 30          -- 单位清单上限
-- ================

local PID = Game.GetLocalPlayer()
print("SNAP|turn=" .. Game.GetCurrentGameTurn() .. "|player=" .. tostring(PID))

local pP = Players[PID]
local tr = pP:GetTreasury()
print("SNAP|gold=" .. tostring(math.floor(tr:GetGoldBalance())))

local rel = pP:GetReligion()
print("SNAP|faith=" .. tostring(math.floor(rel:GetFaithBalance())))

local ts = pP:GetTechs()
local rt = ts:GetResearchingTech()
if rt ~= nil and rt >= 0 then
    print("SNAP|researching=" .. GameInfo.Technologies[rt].TechnologyType ..
        "|prog=" .. tostring(ts:GetResearchProgress(rt)) .. "/" .. tostring(ts:GetResearchCost(rt)))
else
    print("SNAP|researching=none")
end

local cu = pP:GetCulture()
local cc = cu:GetProgressingCivic()
if cc ~= nil and cc >= 0 then
    print("SNAP|civic=" .. GameInfo.Civics[cc].CivicType ..
        "|prog=" .. tostring(cu:GetCulturalProgress(cc)) .. "/" .. tostring(cu:GetCultureCost(cc)))
else
    print("SNAP|civic=none")
end

for _, c in pP:GetCities():Members() do
    local line = "SNAP|city|id=" .. c:GetID() ..
        "|pop=" .. c:GetPopulation() ..
        "|at=" .. c:GetX() .. "," .. c:GetY()
    -- 宜居度三件套（UI 侧方法）：现状/需求/余量
    pcall(function()
        local g = c:GetGrowth()
        line = line .. "|amenity=" .. tostring(g:GetAmenities()) ..
            "|need=" .. tostring(g:GetAmenitiesNeeded())
    end)
    print(line)
end

local n = 0
for _, u in pP:GetUnits():Members() do
    n = n + 1
    if n <= MAX_UNITS then
        local nm = "?"
        pcall(function() nm = GameInfo.Units[u:GetType()].UnitType end)
        local dmg = 0
        pcall(function() dmg = u:GetDamage() end)
        print("SNAP|unit|id=" .. u:GetID() .. "|" .. nm ..
            "|at=" .. u:GetX() .. "," .. u:GetY() .. "|dmg=" .. tostring(dmg))
    end
end
print("SNAP|unit_count=" .. n)
