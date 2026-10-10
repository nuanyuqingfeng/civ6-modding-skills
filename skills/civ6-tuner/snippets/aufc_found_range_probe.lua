-- ===========================================================================
-- aufc_found_range_probe.lua —— 建城按钮「距城间距」检定现场探针（AllUnitsFoundCity）
--
--   用途：一次性回答三个问题
--     ① CITY_MIN_RANGE 参数实际读出来是多少（UI / GP 两端各读一次）；
--     ② Map.GetNeighborPlots(x,y,r) 的"环"语义（含不含中心格 / 是 ==r 还是 <=r）；
--     ③ 引擎权威口径 Plot:IsValidFoundLocation() 在距城 1/2/3 环各是什么，
--        以及 mod 自己的 AUFCIsButtonHidden() 对当前选中单位给的是隐藏还是显示。
--
--   用法：⚠ 必须跑在 mod 自己的 UI 上下文（状态名 AllUnitsFoundCity），
--         普通 ingame(InGame) 态里 mod 的全局函数是 nil。
--     python tuner_exec.py exec --state AllUnitsFoundCity --file snippets/aufc_found_range_probe.lua
--     python tuner_exec.py exec --state GameCore_Tuner     --file snippets/aufc_found_range_probe.lua
--
--   纯读操作：不改任何游戏状态（也不动按钮显隐）。
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    PLAYER_ID = nil,          -- nil = Game.GetLocalPlayer()
    MAX_RING = 4,             -- GetNeighborPlots 语义探测到第几环
    SCAN_CITY_RINGS = 5,      -- 对最近城市做 1..N 环的 IsValidFoundLocation 扫描（0 = 跳过）
}
-- ==================

local function S(v) if v == nil then return "nil" end return tostring(v) end

-- 引擎返回的"数组"可能是稀疏表 → 一律 pairs + 只认数字键（同 Mods 副本内的写法）
local function each(tList, fn)
    for k, v in pairs(tList or {}) do
        if type(k) == "number" and v ~= nil then fn(v) end
    end
end

local function ringStats(iX, iY, iRing)
    local t = Map.GetNeighborPlots(iX, iY, iRing)
    local n, dmin, dmax, dZero = 0, nil, nil, 0
    each(t, function(p)
        n = n + 1
        local d = Map.GetPlotDistance(iX, iY, p:GetX(), p:GetY())
        if d == 0 then dZero = dZero + 1 end
        if dmin == nil or d < dmin then dmin = d end
        if dmax == nil or d > dmax then dmax = d end
    end)
    return n, dmin, dmax, dZero
end

local function main()
    local pid = CONFIG.PLAYER_ID or Game.GetLocalPlayer()
    print("===== AUFC 距城检定探针 =====")
    print("[ctx] AUFCIsButtonHidden=" .. type(AUFCIsButtonHidden)
        .. "  AUFCRefreshButton=" .. type(AUFCRefreshButton)
        .. "  Controls=" .. type(Controls))
    print("[ctx] PlayerManager.GetAliveIDs=" .. type(PlayerManager.GetAliveIDs)
        .. "  Map.GetNeighborPlots=" .. type(Map.GetNeighborPlots)
        .. "  Map.GetPlotDistance=" .. type(Map.GetPlotDistance))

    local gp = GameInfo.GlobalParameters["CITY_MIN_RANGE"]
    print("[param] GameInfo.GlobalParameters['CITY_MIN_RANGE'].Value=" .. S(gp and gp.Value))

    -- ① 列出所有存活玩家的城市（含城邦 / 自由城市）
    local tCities = {}
    each(PlayerManager.GetAliveIDs(), function(otherID)
        local pOther = Players[otherID]
        if pOther ~= nil and pOther:IsAlive() then
            local pCities = pOther:GetCities()
            if pCities ~= nil then
                for _, pCity in pCities:Members() do
                    if pCity ~= nil then
                        tCities[#tCities + 1] = pCity
                    end
                end
            end
        end
    end)
    print("[cities] 全图城市数=" .. #tCities)

    -- ② 当前选中单位
    local u = UI.GetHeadSelectedUnit()
    if u == nil then
        print("[unit] 当前无选中单位（请选中一个单位后重跑本探针）")
    else
        local ux, uy = u:GetX(), u:GetY()
        local unitRow = GameInfo.Units[u:GetType()]
        print(string.format("[unit] id=%s type=%s pos=(%d,%d) moves=%s owner=%s",
            S(u:GetID()), S(unitRow and unitRow.UnitType), ux, uy,
            S(u:GetMovementMovesRemaining()), S(u:GetOwner())))
        local up = Map.GetPlot(ux, uy)
        local ok, ival = pcall(function() return up:IsValidFoundLocation() end)
        print(string.format("[unit plot] IsCity=%s IsWater=%s owner=%s IsValidFoundLocation=%s",
            S(up:IsCity()), S(up:IsWater()), S(up:GetOwner()),
            ok and S(ival) or ("ERR:" .. tostring(ival))))
        if type(AUFCIsButtonHidden) == "function" then
            print("[mod] AUFCIsButtonHidden(选中单位)=" .. S(AUFCIsButtonHidden(u))
                .. "   Grid.IsHidden=" .. S(Controls.AUFCGrid and Controls.AUFCGrid:IsHidden()))
        end

        -- ③ GetNeighborPlots 环语义
        for r = 1, CONFIG.MAX_RING do
            local n, dmin, dmax, dZero = ringStats(ux, uy, r)
            print(string.format("[ring] GetNeighborPlots(r=%d) n=%d dmin=%s dmax=%s 含中心格数=%d",
                r, n, S(dmin), S(dmax), dZero))
        end

        -- ④ 逐城距离（按距离排序输出前 5 个）
        local tDist = {}
        for _, pCity in ipairs(tCities) do
            local d = Map.GetPlotDistance(ux, uy, pCity:GetX(), pCity:GetY())
            tDist[#tDist + 1] = { d = d, id = pCity:GetID(), x = pCity:GetX(), y = pCity:GetY(),
                owner = pCity:GetOwner(), name = S(pCity:GetName()) }
        end
        table.sort(tDist, function(a, b) return a.d < b.d end)
        for i = 1, math.min(5, #tDist) do
            local c = tDist[i]
            print(string.format("[dist] #%d city=%s(owner=%s) pos=(%d,%d) 距选中单位=%d",
                i, c.name, S(c.owner), c.x, c.y, c.d))
        end

        -- ⑤ 最近城市周边各环：引擎权威建城合法性与地块层命中
        local near = tDist[1]
        if near ~= nil and CONFIG.SCAN_CITY_RINGS > 0 then
            -- 引擎两套 API 现场对照：Plot:IsValidFoundLocation()（双端存在）
            --   vs Player:GetCities():IsValidFoundLocation()（GP 专有）
            local pSelf = Players[pid]
            local pSelfCities = pSelf and pSelf:GetCities()
            local bCitiesApi = pSelfCities ~= nil and pSelfCities.IsValidFoundLocation ~= nil
            print(string.format("[scan] 最近城市 %s pos=(%d,%d) 距=%d —— 逐环引擎口径（GetCities 接口可用=%s）：",
                near.name, near.x, near.y, near.d, tostring(bCitiesApi)))
            for r = 1, CONFIG.SCAN_CITY_RINGS do
                local rows = {}
                each(Map.GetNeighborPlots(near.x, near.y, r), function(p)
                    local px, py = p:GetX(), p:GetY()
                    if Map.GetPlotDistance(near.x, near.y, px, py) == r then
                        local okv, v = pcall(function() return p:IsValidFoundLocation() end)
                        local okc, c = false, nil
                        if bCitiesApi then
                            okc, c = pcall(function() return pSelfCities:IsValidFoundLocation(px, py) end)
                        end
                        rows[#rows + 1] = string.format("(%d,%d)PV=%s PC=%s",
                            px, py,
                            okv and S(v) or "ERR",
                            (not bCitiesApi) and "-" or (okc and S(c) or "ERR"))
                    end
                end)
                table.sort(rows)
                print(string.format("  ring %d (n=%d): %s", r, #rows, table.concat(rows, " | ")))
            end
        end
    end
    print("===== 探针结束 =====")
end

-- 附加诊断（只读）：引擎权威阈值 + mod 对每个单位位置的裁定矩阵
local function main2()
    local pid = Game.GetLocalPlayer()
    local gp = GameInfo.GlobalParameters["CITY_MIN_RANGE"]
    local range = tonumber(gp and gp.Value) or 3
    print("")
    print("===== 附加诊断：引擎阈值 / 单位裁定矩阵（range=" .. range .. "）=====")

    -- ① 引擎权威建城检定（GP 专有；UI 侧为 nil）
    local pPlayer = Players[pid]
    local pCities = pPlayer and pPlayer:GetCities()
    local bHaveEng = pCities ~= nil and pCities.IsValidFoundLocation ~= nil
    print("[engine] Player:GetCities():IsValidFoundLocation 可用=" .. tostring(bHaveEng))
    if bHaveEng then
        local cap = pCities:GetCount() > 0 and pCities:GetCapitalCity() or nil
        if cap ~= nil then
            print(string.format("[engine] 以首都 %s(%d,%d) 为中心逐环实测：",
                tostring(cap:GetName()), cap:GetX(), cap:GetY()))
            for r = 1, range + 1 do
                local rows = {}
                each(Map.GetNeighborPlots(cap:GetX(), cap:GetY(), r), function(p)
                    local px, py = p:GetX(), p:GetY()
                    local d = Map.GetPlotDistance(cap:GetX(), cap:GetY(), px, py)
                    if d == r then  -- 只看正好第 r 环（GetNeighborPlots 返回的是实心盘）
                        local okv, v = pcall(function() return pCities:IsValidFoundLocation(px, py) end)
                        rows[#rows + 1] = string.format("(%d,%d)=%s", px, py,
                            okv and tostring(v) or ("ERR:" .. tostring(v)))
                    end
                end)
                table.sort(rows)
                local nValid = 0
                for _, s in ipairs(rows) do if s:find("=true", 1, true) then nValid = nValid + 1 end end
                print(string.format("  ring %d: n=%d 其中 valid=true 数量=%d   %s",
                    r, #rows, nValid, table.concat(rows, " ")))
            end
        end
    end

    -- ② mod 对每个单位位置的裁定（UI 侧才有 AUFCIsButtonHidden）
    if type(AUFCIsButtonHidden) ~= "function" then
        print("[mod] 本态无 AUFCIsButtonHidden（GP 态正常如此）")
    else
        print("[mod] 单位裁定矩阵（只读调用，不改按钮状态）：")
        local pUnits = pPlayer:GetUnits()
        local n = 0
        if pUnits ~= nil then
            for _, u in pUnits:Members() do
                if u ~= nil then
                    n = n + 1
                    local ux, uy = u:GetX(), u:GetY()
                    local row = GameInfo.Units[u:GetType()]
                    -- mod 的两层检定在本态复刻一遍（只读）
                    local up = Map.GetPlot(ux, uy)
                    local diskHit = false
                    each(Map.GetNeighborPlots(ux, uy, range - 1), function(p)
                        if p ~= nil and p:IsCity() then diskHit = true end
                    end)
                    local listHit, dmin = false, nil
                    each(PlayerManager.GetAliveIDs(), function(oid)
                        local op = Players[oid]
                        if op ~= nil and op:IsAlive() then
                            local oc = op:GetCities()
                            if oc ~= nil then
                                for _, c in oc:Members() do
                                    local d = Map.GetPlotDistance(ux, uy, c:GetX(), c:GetY())
                                    if dmin == nil or d < dmin then dmin = d end
                                    if d < range then listHit = true end
                                end
                            end
                        end
                    end)
                    print(string.format(
                        "  #%d %s id=%s pos=(%d,%d) moves=%s city距=%s | 盘层命中=%s 城表层命中=%s | 应过近=%s | mod隐藏=%s",
                        n, S(row and row.UnitType), S(u:GetID()), ux, uy,
                        S(u:GetMovementMovesRemaining()), S(dmin),
                        tostring(diskHit), tostring(listHit),
                        tostring(diskHit or listHit), S(AUFCIsButtonHidden(u))))
                end
            end
        end
        print("[mod] 本方单位数=" .. n)
    end
    print("===== 附加诊断结束 =====")
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end

local ok2, err2 = pcall(main2)
if not ok2 then print("pcall(main2) err=" .. tostring(err2)) end
