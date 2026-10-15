local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    local p = Players[1]
    local scaleID = GameInfo.Resources["RESOURCE_LOONG_SCALE_QYQXP"].Index
    -- ① 军营建成：应赠送戟言
    GameEvents.OnDistrictConstructed:Fire(1, 3, 19, 31)
    print("after ENCAMPMENT: JIYAN_KEY=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    -- ② 眠龙庭建成：应赠送岁先知 + 龙鳞+1
    GameEvents.OnDistrictConstructed:Fire(1, 21, 19, 31)
    print("after MIANLONG: JUE_KEY=" .. S(p:GetProperty("GREATPERSON_JUE_GRANTED_1")) .. " LOONG_SCALE=" .. S(p:GetResources():GetResourceAmount(scaleID)))
    -- ③ 重复军营：键拦截，不应重复
    GameEvents.OnDistrictConstructed:Fire(1, 3, 19, 31)
    local gp = Game.GetGreatPeople()
    print("third-fire done, JIYAN_KEY still=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
