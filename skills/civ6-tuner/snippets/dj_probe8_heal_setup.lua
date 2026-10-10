-- 战斗回血准备（gamecore）：把战士伤害调到55，找蛮族玩家并在战士旁刷一个蛮族战士
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local u = Players[0]:GetUnits():FindID(131073)
    if not u then print("ERR:no warrior") return end
    u:ChangeDamage(55 - (u:GetDamage() or 0))
    print("WARRIOR dmg=" .. S(u:GetDamage()) .. " at=" .. S(u:GetX()) .. "," .. S(u:GetY()))

    -- 找蛮族玩家
    local barbID = nil
    for i = 0, 64 do
        local p = Players[i]
        if p and type(p.IsBarbarian) == "function" and p:IsBarbarian() then barbID = i break end
    end
    print("BARB_ID=" .. S(barbID))
    if not barbID then return end

    -- 单位类型：蛮族战士（找不到就用普通战士兜底）
    local bt = "UNIT_BARBARIAN_WARRIOR"
    if not GameInfo.Units[bt] then bt = "UNIT_WARRIOR" end
    print("BARB_TYPE=" .. bt)

    -- 在战士相邻格找空地刷蛮族
    local wx, wy = u:GetX(), u:GetY()
    local spot = nil
    for dx = -1, 1 do
        for dy = -1, 1 do
            if dx ~= 0 or dy ~= 0 then
                local p = Map.GetPlot(wx + dx, wy + dy)
                if p and p:IsWater() == false and p:IsImpassable() == false and p:GetUnitCount() == 0 then
                    spot = { wx + dx, wy + dy }
                    break
                end
            end
        end
        if spot then break end
    end
    if not spot then print("ERR:no adjacent free plot") return end
    local bu = UnitManager.InitUnit(barbID, bt, spot[1], spot[2])
    print("BARB_SPAWN|id=" .. S(bu and bu:GetID() or "FAIL") .. "|at=" .. spot[1] .. "," .. spot[2])
end)
