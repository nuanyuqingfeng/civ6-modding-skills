local ok, err = pcall(function()
    print("modding_type=" .. type(Modding))
    local jinhsiHandle = Modding.GetModHandle("21a799be-b75a-4d46-9952-577bb570ff44")
    print("jinhsi_handle=" .. tostring(jinhsiHandle))
    if jinhsiHandle then
        Modding.EnableMod(jinhsiHandle, true)
        print("enable_requested=true")
        local mods = Modding.GetEnabledMods()
        for _, m in ipairs(mods) do
            print("enabled: " .. tostring(m.ModHandle))
        end
    end
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
