local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    local gov = GameInfo.Districts["DISTRICT_GOVERNMENT"]
    print("DISTRICT_GOVERNMENT index=" .. S(gov and gov.Index))
    ChangliAddGovernmentGreatPersonOnDistrictConstructed(1, gov.Index, 19, 31)
    print("after GOVERNMENT: CHANGLI_KEY=" .. S(Players[1]:GetProperty("GREATPERSON_CHANGLI_GRANTED_1")))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
