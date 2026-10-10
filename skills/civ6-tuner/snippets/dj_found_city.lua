-- 用开拓者建城（gamecore），然后回读首都与龙须酥数量
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local settler = nil
    for _, u in Players[0]:GetUnits():Members() do
        local t = GameInfo.Units[u:GetType()].UnitType
        if t == "UNIT_SETTLER" then settler = u end
        print("UNIT|" .. t .. "|id=" .. S(u:GetID()) .. "|at=" .. S(u:GetX()) .. "," .. S(u:GetY()))
    end
    if settler == nil then
        print("ERR:no settler")
        return
    end
    local opType = UnitOperationTypes.FOUND_CITY
    print("OP_FOUND_CITY=" .. S(opType))
    local ok, err = pcall(function()
        UnitManager.RequestOperation(settler, opType, {})
    end)
    print("REQUEST=" .. S(ok) .. " err=" .. S(err))
end)
