-- 档位/property 全扫描（原生战士 131073）+ 城市列表核对
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    for _, c in Players[0]:GetCities():Members() do
        print("CITY|" .. S(c:GetName()) .. "|at=" .. S(c:GetX()) .. "," .. S(c:GetY()))
    end
    local su = Players[0]:GetUnits():FindID(131073)
    if not su then print("ERR:no warrior") return end
    local function report(tag)
        local ab = su:GetAbility()
        local tiers = {}
        for i = 1, 4 do
            tiers[i] = tostring(ab:GetAbilityCount("ABILITY_DJ_BLOOD_MOVE_" .. i))
        end
        print(tag .. "|dmg=" .. S(su:GetDamage()) .. "|tiers=" .. table.concat(tiers, "/")
            .. "|prop=" .. S(su:GetProperty("PROPERTY_DJ_BLOOD_PRICE")))
    end
    report("STEP0")
    su:ChangeDamage(19)  -- -> 30
    report("STEP1")
    su:ChangeDamage(20)  -- -> 50
    report("STEP2")
    su:ChangeDamage(25)  -- -> 75
    report("STEP3")
    su:ChangeDamage(-70) -- -> 5
    report("STEP4")
end)
