local function S(x) if x == nil then return "nil" end return tostring(x) end
local p = Players[1]
print("player alive=" .. S(p:IsAlive()))
local jiyanKey = p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")
print("JIYAN_KEY=" .. S(jiyanKey))
local jueKey = p:GetProperty("GREATPERSON_JUE_GRANTED_1")
print("JUE_KEY=" .. S(jueKey))
local scaleID = GameInfo.Resources["RESOURCE_LOONG_SCALE_QYQXP"].Index
print("LOONG_SCALE=" .. S(p:GetResources():GetResourceAmount(scaleID)))
local cap = p:GetCities():GetCapitalCity()
print("capital=" .. S(cap and cap:GetName() or "NIL"))
