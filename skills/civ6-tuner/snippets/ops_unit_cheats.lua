-- ops_unit_cheats.lua —— 单位操作实测合集（2026-10-02 逐条验证的方法名与写法）
-- 上下文分两段：PART="gp" 用 --context gamecore 投递；PART="ui" 用 --context ingame 投递
-- 用法：python tuner_exec.py exec --context gamecore --file snippets\ops_unit_cheats.lua
--       python tuner_exec.py exec --context ingame  --file snippets\ops_unit_cheats.lua

-- ==== CONFIG（按需改）====
local PART = "gp"             -- "gp"=gamecore 段 / "ui"=ingame 段
local PID = -1                -- -1=本地玩家
local SPAWN_TYPE = "UNIT_BUILDER"
local SPAWN_NEAR_CITY = true  -- 首都旁找一块合法陆地刷（自动校验地形，避开海岸）
local TELEPORT_ID = 0         -- 非 0：把该单位传送到 TELEPORT_X/Y
local TELEPORT_X, TELEPORT_Y = 0, 0
local DELETE_ID = 0           -- 非 0（UI 段）：删除该单位
local ATTACK_ID = 0           -- 非 0（UI 段）：近战攻击 ATTACK_X/Y 处的相邻敌单位
local ATTACK_X, ATTACK_Y = 0, 0
-- ========================

if PART == "gp" then
    -- gamecore 段：InitUnit / Kill / MoveUnit（传送）
    if PID < 0 then PID = Game.GetLocalPlayer() end

    if SPAWN_TYPE ~= "" and SPAWN_NEAR_CITY then
        local cap = Players[PID]:GetCities():GetCapitalCity()
        if cap == nil then
            print("ERR:无首都，无法定位刷兵点")
        else
            -- 先查地形再刷：陆军刷到 TERRAIN_COAST 会被引擎清除并留下 -9999 僵尸句柄
            local placed = false
            local base = cap:GetLocation()
            for r = 1, 3 do
                for dx = -r, r do
                    for dy = -r, r do
                        local x, y = base.x + dx, base.y + dy
                        local p = Map.GetPlot(x, y)
                        if p ~= nil and p:IsWater() == false and p:IsImpassable() == false then
                            local u = UnitManager.InitUnit(PID, SPAWN_TYPE, x, y)
                            print("SPAWN|" .. SPAWN_TYPE .. "|id=" ..
                                tostring(u and u:GetID() or "FAIL") .. "|at=" .. x .. "," .. y)
                            placed = true
                            break
                        end
                    end
                    if placed then break end
                end
                if placed then break end
            end
            if not placed then print("ERR:首都 3 格内无合法陆地") end
        end
    end

    if TELEPORT_ID ~= 0 then
        local u = Players[PID]:GetUnits():FindID(TELEPORT_ID)
        if u then
            UnitManager.MoveUnit(u, TELEPORT_X, TELEPORT_Y)
            print("TELEPORT|" .. TELEPORT_ID .. "->" .. TELEPORT_X .. "," .. TELEPORT_Y)
        else
            print("ERR:单位不存在 " .. TELEPORT_ID)
        end
    end
end

if PART == "ui" then
    -- ingame 段：删兵（RequestCommand DELETE）/ 近战攻击（MOVE_TO + ATTACK 修饰符，需与目标相邻）
    if PID < 0 then PID = Game.GetLocalPlayer() end

    if DELETE_ID ~= 0 then
        local u = Players[PID]:GetUnits():FindID(DELETE_ID)
        if u then
            UnitManager.RequestCommand(u, UnitCommandTypes.DELETE, {})
            print("DELETE_REQUESTED|" .. DELETE_ID)
        else
            print("ERR:单位不存在 " .. DELETE_ID)
        end
    end

    if ATTACK_ID ~= 0 then
        local u = Players[PID]:GetUnits():FindID(ATTACK_ID)
        if u then
            local t = {}
            t[UnitOperationTypes.PARAM_X] = ATTACK_X
            t[UnitOperationTypes.PARAM_Y] = ATTACK_Y
            t[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
            UnitManager.RequestOperation(u, UnitOperationTypes.MOVE_TO, t)
            print("ATTACK_REQUESTED|" .. ATTACK_ID .. "->" .. ATTACK_X .. "," .. ATTACK_Y)
        else
            print("ERR:单位不存在 " .. ATTACK_ID)
        end
    end
end
