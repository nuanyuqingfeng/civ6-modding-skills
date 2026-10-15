local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    local p = Players[1]
    local cap = p:GetCities():GetCapitalCity()
    local bq = cap:GetBuildQueue()
    print("before: JIYAN_KEY=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    bq:CreateDistrict(3)  -- DISTRICT_ENCAMPMENT
    local jiyanKey = p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")
    print("after: JIYAN_KEY=" .. S(jiyanKey))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
