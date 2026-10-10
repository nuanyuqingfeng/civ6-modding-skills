-- 读档后验证：龙须酥不重发 + 首都宜居度
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local cap = Players[0]:GetCities():GetCapitalCity()
    print("CAPITAL=" .. S(cap and (cap:GetX() .. "," .. cap:GetY()) or "nil"))
    print("TURN=" .. S(Game.GetCurrentGameTurn()))
    print("LONGXUSU=" .. S(Players[0]:GetResources():GetResourceAmount(GameInfo.Resources["RESOURCE_LONGXUSU_QYQXP"].Index)))
    if cap then
        local ok, am = pcall(function() return cap:GetAmenities() end)
        print("AMENITIES=" .. S(ok and am or ("ERR:" .. tostring(am))))
        local ok2, amn = pcall(function() return cap:GetAmenitiesNeeded() end)
        print("AMENITIES_NEEDED=" .. S(ok2 and amn or "GP_NIL"))
    end
end)
