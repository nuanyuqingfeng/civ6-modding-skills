local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    local p = Players[1]
    local cap = p:GetCities():GetCapitalCity()
    local jueKey = p:GetProperty("GREATPERSON_JUE_GRANTED_1")
    local jiyanKey = p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")
    print("JUE_KEY=" .. S(jueKey) .. " JIYAN_KEY=" .. S(jiyanKey))
    local bq = cap:GetBuildQueue()
    print("CreateBuilding=" .. type(bq.CreateBuilding) .. " CreateDistrict=" .. type(bq.CreateDistrict) .. " CreateIncompleteBuilding=" .. type(bq.CreateIncompleteBuilding))
    local distInfo = GameInfo.Districts["DISTRICT_ENCAMPMENT"]
    print("encampment index=" .. tostring(distInfo and distInfo.Index))
    local mianlong = GameInfo.Districts["DISTRICT_MIANLONG_QYQXP"]
    print("mianlong index=" .. tostring(mianlong and mianlong.Index))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
