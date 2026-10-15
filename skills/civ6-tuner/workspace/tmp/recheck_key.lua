local function S(x) if x == nil then return "nil" end return tostring(x) end
local p = Players[1]
local jiyanKey = p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")
print("JIYAN_KEY=" .. S(jiyanKey))
local cap = p:GetCities():GetCapitalCity()
print("city districts=" .. tostring(cap:GetDistricts():GetNumDistricts()))
