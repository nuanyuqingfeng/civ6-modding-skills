-- found_city —— 建城原语：用开拓者发起 FOUND_CITY
-- host-game / 无头建局产出标准开局（有开拓者、无首都），城市相关探针前先跑本片段
-- 用法：python tuner_exec.py exec --context ingame --file snippets/found_city.lua
-- 建城请求为异步结算，随后用 Players[PID]:GetCities():GetCapitalCity() 复核

-- ==== CONFIG ====
local PID = -1  -- -1 = 本地玩家；或指定玩家 ID
-- ================

pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    if PID < 0 then PID = Game.GetLocalPlayer() end

    local settler = nil
    for _, u in Players[PID]:GetUnits():Members() do
        if GameInfo.Units[u:GetType()].UnitType == "UNIT_SETTLER" then
            settler = u
            break
        end
    end
    if settler == nil then
        print("ERR:no settler（可能已建城，先用 GetCapitalCity 复核）")
        return
    end

    local t = {}
    t[UnitOperationTypes.PARAM_X] = settler:GetX()
    t[UnitOperationTypes.PARAM_Y] = settler:GetY()
    UnitManager.RequestOperation(settler, UnitOperationTypes.FOUND_CITY, t)
    print("FOUND_CITY_REQUESTED|at=" .. S(settler:GetX()) .. "," .. S(settler:GetY()))
end)
