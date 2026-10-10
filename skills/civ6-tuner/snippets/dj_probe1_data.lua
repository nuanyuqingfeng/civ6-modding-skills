-- 丹瑾实测探针1（gamecore）：库内数据 + 领袖 + 特性标记 + 龙须酥库存
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local pcfg = PlayerConfigurations[0]
    print("LEADER=" .. S(pcfg:GetLeaderTypeName()))
    print("CIV=" .. S(pcfg:GetCivilizationTypeName()))

    print("TYPE_BLOODPRICE=" .. S(GameInfo.Types["ABILITY_DJ_BLOODPRICE"] and GameInfo.Types["ABILITY_DJ_BLOODPRICE"].Index or nil))
    print("UNITABILITY_BLOODPRICE=" .. S(GameInfo.UnitAbilities["ABILITY_DJ_BLOODPRICE"] and 1 or nil))
    for i = 1, 4 do
        print("UNITABILITY_MOVE" .. i .. "=" .. S(GameInfo.UnitAbilities["ABILITY_DJ_BLOOD_MOVE_" .. i] and 1 or nil))
    end
    local res = GameInfo.Resources["RESOURCE_LONGXUSU_QYQXP"]
    print("RESOURCE_IDX=" .. S(res and res.Index or nil))
    print("MOD_LONGXUSU_GRANT=" .. S(GameInfo.Modifiers["DJ_LONGXUSU_GRANT"] and 1 or nil))
    print("ARG_AMOUNT=" .. S(GameInfo.ModifierArguments and "skip" or nil))
    print("MOD_MIANLONG_PROD=" .. S(GameInfo.Modifiers["MIANLONG_ADJACENCY_PRODUCTION_QYQXP"] and 1 or nil))
    print("TRAITMOD_ML=" .. S(GameInfo.TraitModifiers and 1 or nil))

    print("TRAIT_PROP_DJSJ=" .. S(Players[0]:GetProperty("PROPERTY_DJSJ_TRAIT")))

    local pRes = Players[0]:GetResources()
    if res then
        local ok, amount = pcall(function() return pRes:GetResourceAmount(res.Index) end)
        if ok then
            print("LONGXUSU_COUNT=" .. S(amount))
        else
            print("LONGXUSU_COUNT_ERR=" .. S(amount))
            local ok2, amount2 = pcall(function() return pRes:GetResourceAmount(res.ResourceType) end)
            print("LONGXUSU_COUNT_STR=" .. S(ok2 and amount2 or ("ERR:" .. tostring(amount2))))
        end
    end
    print("TURN=" .. S(Game.GetCurrentGameTurn()))
end)
