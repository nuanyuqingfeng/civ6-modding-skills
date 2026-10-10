-- 启用今州三件套 mod（丹瑾 + 今汐 + 长离），幂等
local guids = {
    "f845552e-0e31-4827-abeb-748b4b63ee95",
    "21a799be-b75a-4d46-9952-577bb570ff44",
    "66685738-4d78-4c73-874a-055e5d24d86a",
}
local names = { "DANJIN", "JINHSI", "CHANGLI" }
pcall(function()
    for i, g in ipairs(guids) do
        local h = Modding.GetModHandle(g)
        local ok = false
        if h then
            ok = Modding.EnableMod(h, true)
        end
        print("ENABLE " .. names[i] .. " handle=" .. tostring(h) .. " ret=" .. tostring(ok))
    end
    print("AFTER count=" .. tostring(Modding.GetEnabledModsCount and Modding.GetEnabledModsCount() or "n/a"))
end)
