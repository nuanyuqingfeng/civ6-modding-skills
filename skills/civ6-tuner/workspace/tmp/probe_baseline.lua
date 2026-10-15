local ok, err = pcall(function()
    local p = Players[1]
    local cap = p:GetCities():GetCapitalCity()
    if cap == nil then print("NO_CAPITAL") return end
    print("capital=" .. cap:GetName() .. " at " .. cap:GetX() .. "," .. cap:GetY())
    local scaleID = GameInfo.Resources["RESOURCE_LOONG_SCALE_QYQXP"].Index
    local amount = p:GetResources():GetResourceAmount(scaleID)
    print("LOONG_SCALE=" .. tostring(amount))
    print("JUE_KEY=" .. tostring(p:GetProperty("GREATPERSON_JUE_GRANTED_1")))
    print("JIYAN_KEY=" .. tostring(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    local bq = cap:GetBuildQueue()
    print("BuildQueue methods: CreateBuilding=" .. type(bq.CreateBuilding) .. " CreateDistrict=" .. type(bq.CreateDistrict) .. " CreateIncompleteBuilding=" .. type(bq.CreateIncompleteBuilding))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
