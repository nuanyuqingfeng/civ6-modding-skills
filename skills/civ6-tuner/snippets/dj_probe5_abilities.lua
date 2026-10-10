-- 单位能力实测（gamecore）：ABILITY 授予、四档移动力、property 战斗力随伤害变化
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local cap = Players[0]:GetCities():GetCapitalCity()
    local cx, cy = cap:GetX(), cap:GetY()

    -- 在首都旁找一块无单位陆地，刷一个战士
    local spot, su = nil, nil
    for r = 1, 3 do
        for dx = -r, r do
            for dy = -r, r do
                local p = Map.GetPlot(cx + dx, cy + dy)
                if p and p:IsWater() == false and p:IsImpassable() == false and p:GetUnitCount() == 0 then
                    spot = { cx + dx, cy + dy }
                    break
                end
            end
            if spot then break end
        end
        if spot then break end
    end
    if not spot then print("ERR:no free land plot") return end
    su = UnitManager.InitUnit(0, "UNIT_WARRIOR", spot[1], spot[2])
    print("SPAWN|id=" .. S(su and su:GetID() or "FAIL") .. "|at=" .. spot[1] .. "," .. spot[2])
    if not su then return end

    -- 能力读取函数
    local function abilityReport(tag)
        local okA, ab = pcall(function() return su:GetAbility() end)
        if not okA then print(tag .. " GetAbility_ERR:" .. S(ab)) return end
        local has, hErr = pcall(function() return ab:HasAbility("ABILITY_DJ_BLOODPRICE") end)
        print(tag .. " BLOODPRICE_HAS=" .. S(has) .. S(hErr and (" ERR:" .. hErr) or ""))
        for i = 1, 4 do
            local c, cErr = pcall(function() return ab:GetAbilityCount("ABILITY_DJ_BLOOD_MOVE_" .. i) end)
            print(tag .. " MOVE" .. i .. "_COUNT=" .. S(c) .. S(cErr and (" ERR:" .. cErr) or ""))
        end
    end

    abilityReport("FULLHP")
    print("PROP_FULL=" .. S(su:GetProperty("PROPERTY_DJ_BLOOD_PRICE")))

    -- 加伤害到 30（二档区间 25-49），UnitDamageChanged 应触发 Lua 同步
    su:ChangeDamage(30)
    local d1 = su:GetDamage() or 0
    print("DMG1=" .. S(d1))
    abilityReport("DMG" .. d1)
    print("PROP_1=" .. S(su:GetProperty("PROPERTY_DJ_BLOOD_PRICE")))

    -- 加到 60（三档 50-74）
    su:ChangeDamage(30)
    local d2 = su:GetDamage() or 0
    print("DMG2=" .. S(d2))
    abilityReport("DMG" .. d2)
    print("PROP_2=" .. S(su:GetProperty("PROPERTY_DJ_BLOOD_PRICE")))

    -- 加到 80（四档 >=75）
    su:ChangeDamage(25)
    local d3 = su:GetDamage() or 0
    print("DMG3=" .. S(d3))
    abilityReport("DMG" .. d3)
    print("PROP_3=" .. S(su:GetProperty("PROPERTY_DJ_BLOOD_PRICE")))

    -- 治疗回到 10（一档）
    su:ChangeDamage(-70)
    local d4 = su:GetDamage() or 0
    print("DMG4=" .. S(d4))
    abilityReport("DMG" .. d4)
    print("PROP_4=" .. S(su:GetProperty("PROPERTY_DJ_BLOOD_PRICE")))

    print("TESTUNIT_ID=" .. S(su:GetID()))
end)
