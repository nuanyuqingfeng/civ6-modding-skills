-- 发起近战攻击（ingame 侧）：战士131073 攻击相邻蛮族 50,34
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local u = Players[0]:GetUnits():FindID(131073)
    if not u then print("ERR:no warrior") return end
    local t = {}
    t[UnitOperationTypes.PARAM_X] = 50
    t[UnitOperationTypes.PARAM_Y] = 34
    t[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
    local ok, err = pcall(function()
        UnitManager.RequestOperation(u, UnitOperationTypes.MOVE_TO, t)
    end)
    print("ATTACK_REQUESTED ret=" .. S(ok) .. " err=" .. S(err))
end)
