local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    local p = Players[1]
    local scaleID = GameInfo.Resources["RESOURCE_LOONG_SCALE_QYQXP"].Index
    -- ① 军营：通用赠送（戟言）
    ChangliAddGreatPersonOnDistrictConstructed(1, 3, 19, 31)
    print("after ENCAMPMENT: JIYAN_KEY=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    -- ② 眠龙庭：通用赠送（岁先知 + 龙鳞+1）
    ChangliAddGreatPersonOnDistrictConstructed(1, 21, 19, 31)
    print("after MIANLONG: JUE_KEY=" .. S(p:GetProperty("GREATPERSON_JUE_GRANTED_1")) .. " LOONG_SCALE=" .. S(p:GetResources():GetResourceAmount(scaleID)))
    -- ③ 重复军营：键拦截
    ChangliAddGreatPersonOnDistrictConstructed(1, 3, 19, 31)
    print("after ENCAMPMENT again: JIYAN_KEY=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    -- ④ 政府广场：长离专属赠送（长离科学家，并集闸门命中 HasTraitChangli）
    ChangliAddGovernmentGreatPersonOnDistrictConstructed(1, 8, 19, 31)
    print("after GOVERNMENT: CHANGLI_KEY=" .. S(p:GetProperty("GREATPERSON_CHANGLI_GRANTED_1")))
    -- ⑤ 银行完成：通用赠送（马赫）—— purchaseType/iConstructionType=1
    ChangliAddMahe(1, 0, 1, GameInfo.Buildings["BUILDING_BANK"].Index, false)
    print("after BANK: MAHE_KEY=" .. S(p:GetProperty("GREATPERSON_MAHE_GRANTED_1")))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
