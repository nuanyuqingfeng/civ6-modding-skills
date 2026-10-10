-- 最小化逐项读取：对比原生单位与 InitUnit 单位的能力接口
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local native = Players[0]:GetUnits():FindID(131073)
    local spawned = Players[0]:GetUnits():FindID(327680)
    print("NATIVE=" .. S(native and native:GetID() or "nil"))
    print("SPAWNED=" .. S(spawned and spawned:GetID() or "nil"))
    if native then
        print("NATIVE_DMG=" .. S(native:GetDamage()))
        local ok, ab = pcall(function() return native:GetAbility() end)
        print("NATIVE_GETABILITY=" .. S(ok) .. "/" .. S(ab))
        if ok and ab then
            local ok2, h = pcall(function() return ab:HasAbility("ABILITY_DJ_BLOODPRICE") end)
            print("NATIVE_BLOODPRICE=" .. S(ok2) .. "/" .. S(h))
            for i = 1, 4 do
                local ok3, c = pcall(function() return ab:GetAbilityCount("ABILITY_DJ_BLOOD_MOVE_" .. i) end)
                print("NATIVE_MOVE" .. i .. "=" .. S(ok3) .. "/" .. S(c))
            end
        end
    end
    if spawned then
        print("SPAWNED_DMG=" .. S(spawned:GetDamage()))
        local ok, ab = pcall(function() return spawned:GetAbility() end)
        print("SPAWNED_GETABILITY=" .. S(ok) .. "/" .. S(ab))
        if ok and ab then
            local ok2, h = pcall(function() return ab:HasAbility("ABILITY_DJ_BLOODPRICE") end)
            print("SPAWNED_BLOODPRICE=" .. S(ok2) .. "/" .. S(h))
        end
    end
    print("DONE")
end)
