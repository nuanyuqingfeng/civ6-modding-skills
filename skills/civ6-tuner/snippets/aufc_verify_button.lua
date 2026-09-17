-- ===========================================================================
-- aufc_verify_button.lua —— 建城按钮显隐端到端验证（跑在 mod 自己的 UI 上下文）
--
--   用法：python tuner_exec.py exec --state AllUnitsFoundCity --file snippets/aufc_verify_button.lua
--   ⚠ mod UI 上下文里才有 AUFCIsButtonHidden / Controls.AUFCGrid；
--     普通 ingame(InGame) 态里这些全是 nil。
--
--   打印：当前选中单位位置 / 到最近城市的距离 / 引擎裁定 / 刷新前后的 Grid.IsHidden。
--   配合 GP 侧 UnitManager.PlaceUnit(Unit, x, y) 搬单位，即可逐距离段验证。
--   只调 AUFCRefreshButton()（mod 自己的刷新入口），不写任何游戏状态。
-- ===========================================================================

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function main()
    print("---- aufc_verify_button ----")
    if type(AUFCIsButtonHidden) ~= "function" or Controls == nil or Controls.AUFCGrid == nil then
        print("[verify] 不在 mod UI 上下文（AUFCIsButtonHidden / AUFCGrid 缺失）")
        return
    end
    local u = UI.GetHeadSelectedUnit()
    if u == nil then
        print("[verify] 当前无选中单位 —— 请在游戏里选中一个单位后重跑")
        return
    end
    local x, y = u:GetX(), u:GetY()
    local pPlot = Map.GetPlot(x, y)
    local unitRow = GameInfo.Units[u:GetType()]

    local dmin = nil
    for _, pid in ipairs(PlayerManager.GetAliveIDs() or {}) do
        local p = Players[pid]
        local c = p and p:GetCities()
        if c ~= nil then
            for _, city in c:Members() do
                local d = Map.GetPlotDistance(x, y, city:GetX(), city:GetY())
                if dmin == nil or d < dmin then dmin = d end
            end
        end
    end

    local okv, v = pcall(function() return pPlot:IsValidFoundLocation() end)
    print(string.format("[verify] 单位=%s id=%s pos=(%d,%d) moves=%s 最近城距=%s",
        S(unitRow and unitRow.UnitType), S(u:GetID()), x, y, S(u:GetMovementMovesRemaining()), S(dmin)))
    print(string.format("[verify] 引擎 Plot:IsValidFoundLocation=%s   mod AUFCIsButtonHidden=%s",
        okv and S(v) or ("ERR:" .. tostring(v)), S(AUFCIsButtonHidden(u))))
    print("[verify] 刷新前 Grid.IsHidden=" .. S(Controls.AUFCGrid:IsHidden()))
    AUFCRefreshButton()
    print("[verify] 刷新后 Grid.IsHidden=" .. S(Controls.AUFCGrid:IsHidden())
        .. "   （false = 按钮可见 / true = 按钮隐藏）")
    print("---- end ----")
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
