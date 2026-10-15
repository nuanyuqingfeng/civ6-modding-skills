local ok, err = pcall(function()
    local sk = GameInfo.GreatWorks["GREATWORK_WE_ARE_ONE_SK"]
    local cml = GameInfo.GreatWorks["GREATWORK_BRACELET_CML"]
    print("SK audio=" .. tostring(sk and sk.Audio))
    print("CML audio=" .. tostring(cml and cml.Audio))
    print("BS_include=" .. tostring(include("GreatWorkShowcase_BS.lua")))
    print("Changli_include=" .. tostring(include("GreatWorkShowcase_Changli.lua")))
    print("ShowScreen=" .. type(ShowScreen) .. " HideScreen=" .. type(HideScreen))
    UI.PlaySound("Stop_GREATWORK_WE_ARE_ONE_SK_QUOTE")
    UI.PlaySound("Stop_GREATWORK_BRACELET_CML_QUOTE")
    print("both Stop events dispatched OK")
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
