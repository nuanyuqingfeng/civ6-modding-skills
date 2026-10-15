local ok, err = pcall(function()
    local row = GameInfo.GreatWorks["GREATWORK_WULUJI_QYQXP"]
    print("wuluji_audio=" .. tostring(row and row.Audio))
    print("ShowScreen=" .. type(ShowScreen) .. " HideScreen=" .. type(HideScreen))
    HideScreen()
    print("HideScreen called OK")
    UI.PlaySound("Stop_GREAT_WORK_OBJECT_WULUJI_QUOTE")
    print("Stop event dispatched OK")
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
