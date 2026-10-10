-- 状态核查：玩家0城市与单位全列表
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    print("TURN=" .. S(Game.GetCurrentGameTurn()))
    print("LEADER=" .. S(PlayerConfigurations[0]:GetLeaderTypeName()))
    for _, c in Players[0]:GetCities():Members() do
        print("CITY|" .. S(c:GetName()) .. "|at=" .. S(c:GetX()) .. "," .. S(c:GetY()) .. "|pop=" .. S(c:GetPopulation()))
    end
    for _, u in Players[0]:GetUnits():Members() do
        print("UNIT|" .. S(GameInfo.Units[u:GetType()].UnitType) .. "|id=" .. S(u:GetID()) .. "|at=" .. S(u:GetX()) .. "," .. S(u:GetY()) .. "|dmg=" .. S(u:GetDamage()))
    end
    print("LONGXUSU=" .. S(Players[0]:GetResources():GetResourceAmount(GameInfo.Resources["RESOURCE_LONGXUSU_QYQXP"].Index)))
    print("FLAG=" .. S(Players[0]:GetProperty("PROPERTY_DJ_LONGXUSU_GRANTED")))
end)
