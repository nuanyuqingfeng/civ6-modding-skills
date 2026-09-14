-- property_check.lua —— 查询玩家/地块 PROPERTY 与基础状态（金币/信仰/时代分）
-- 上下文：gamecore（只读）
-- 用法：python tuner_exec.py exec --context gamecore --file snippets\property_check.lua

-- ==== CONFIG ====
local PID = Game.GetLocalPlayer()          -- 默认本地玩家；查 AI 改成具体数字
local PROP_KEY = "PROPERTY_RGN_SWORD_TIER" -- 要查的 PROPERTY key，无则填 nil
local PLOT_X, PLOT_Y = nil, nil            -- 要查的地块坐标，无则保持 nil
-- ================

local pPlayer = Players[PID]
print("PlayerID=" .. PID .. " (" .. tostring(PlayerConfigurations[PID]:GetCivilizationTypeName()) .. ")")
print("Gold=" .. tostring(math.floor(pPlayer:GetTreasury():GetBalance())))
print("Faith=" .. tostring(math.floor(pPlayer:GetReligion():GetFaithBalance())))
print("EraScore=" .. tostring(pPlayer:GetEra():GetEraScore()))

if PROP_KEY then
    -- 玩家级 PROPERTY（引擎内置，GP/UI 双端可读）
    print("Player['" .. PROP_KEY .. "']=" .. tostring(pPlayer:GetProperty(PROP_KEY)))
end

if PLOT_X and PLOT_Y then
    local pPlot = Map.GetPlot(PLOT_X, PLOT_Y)
    if pPlot then
        print("Plot(" .. PLOT_X .. "," .. PLOT_Y .. ") Property['"
            .. tostring(PROP_KEY) .. "']=" .. tostring(pPlot:GetProperty(PROP_KEY)))
        print("  Owner=" .. tostring(pPlot:GetOwner()))
        print("  Improvement=" .. tostring(pPlot:GetImprovementType()
            and GameInfo.Improvements[pPlot:GetImprovementType()].ImprovementType or "<无>"))
    else
        print("Plot(" .. PLOT_X .. "," .. PLOT_Y .. ") 不存在")
    end
end
