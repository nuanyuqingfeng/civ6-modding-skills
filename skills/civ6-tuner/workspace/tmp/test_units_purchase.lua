local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    -- 伟人单位到位检查
    local wanted = { UNIT_GENERAL_JIYAN_QYQXP=false, UNIT_PROPHET_JUE_QYQXP=false, UNIT_SCIENTIST_CHANGLI_QYQXP=false, UNIT_MERCHANT_MAHE_QYQXP=false }
    for _, unit in Players[1]:GetUnits():Members() do
        local info = GameInfo.Units[unit:GetType()]
        if info and wanted[info.UnitType] ~= nil then
            wanted[info.UnitType] = true
        end
    end
    for k, v in pairs(wanted) do print("unit " .. k .. " present=" .. S(v)) end
    -- 购买路径：清键后走 ChangliPurchaseCheck（purchaseType=135083828, 军营）
    local p = Players[1]
    p:SetProperty("GREATPERSON_JIYAN_GRANTED_1", false)
    ChangliPurchaseCheck(1, 0, 19, 31, 135083828, 3, false)
    print("purchase path: JIYAN_KEY=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    -- purchaseType 不符应早退（键先清）
    p:SetProperty("GREATPERSON_JIYAN_GRANTED_1", false)
    ChangliPurchaseCheck(1, 0, 19, 31, 999, 3, false)
    print("wrong purchaseType: JIYAN_KEY=" .. S(p:GetProperty("GREATPERSON_JIYAN_GRANTED_1")))
    -- 恢复键状态
    p:SetProperty("GREATPERSON_JIYAN_GRANTED_1", true)
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
