local ok, err = pcall(function()
    local h = Modding.GetModHandle("21183d1e-24b3-4323-a0b4-53d676c0b0ac")
    print("bs_handle=" .. tostring(h))
    if h then Modding.EnableMod(h, true) print("bs_enabled=true") end
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
