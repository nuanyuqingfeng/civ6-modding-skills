-- ===========================================================================
-- dump_props.lua —— 按 GameInfo 权威清单逐条 dump 实体属性（避免手写 key 漏项）
--   用法：改 CONFIG 后跑；两端各跑一次可看出「mod 写的」与「引擎写的」是否一致
--     python tuner_exec.py exec --both --file snippets/dump_props.lua
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    PLAYER_ID = 0,
    -- 清单来源：'sword'（Cartethyia_Sword_Buffs 表）| 'list'（手工列表）
    SOURCE    = "sword",
    LIST      = {},
    -- 属性名模板：清单项会拼到 %s 位置
    TEMPLATE  = "PROPERTY_CTTH_SWORD_%s",
    -- 目标实体：'plot'（首都地块）| 'player' | 'game'
    TARGET    = "plot",
    -- 另附：列出所有与某前缀匹配且已置位的属性（用于反查残留）
    DUMP_PREFIX = "PROPERTY_CTTH_",
}

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function entity()
    local pl = Players[CONFIG.PLAYER_ID]
    if CONFIG.TARGET == "plot" then
        local cap = pl:GetCities():GetCapitalCity()
        if not cap then return nil end
        local p = Map.GetPlot(cap:GetX(), cap:GetY())
        -- 自洽核实：确认取到的地块身份与首都一致
        if p and (p:GetX() ~= cap:GetX() or p:GetY() ~= cap:GetY()) then
            print(string.format("!! 地块身份不一致：cap=(%d,%d) plot=(%d,%d)",
                cap:GetX(), cap:GetY(), p:GetX(), p:GetY()))
        end
        return p, cap
    elseif CONFIG.TARGET == "player" then
        return pl, nil
    else
        return Game, nil
    end
end

local function keys()
    local out = {}
    if CONFIG.SOURCE == "sword" then
        for row in GameInfo.Cartethyia_Sword_Buffs() do
            out[#out + 1] = string.format(CONFIG.TEMPLATE, row.BuffId)
        end
    else
        for _, k in ipairs(CONFIG.LIST) do out[#out + 1] = k end
    end
    return out
end

local function main()
    local ent, cap = entity()
    print(string.format("=== dump_props: TARGET=%s PLAYER=%d %s ===", CONFIG.TARGET, CONFIG.PLAYER_ID,
        cap and ("首都(" .. cap:GetX() .. "," .. cap:GetY() .. ")") or ""))
    print("实体 = " .. S(ent) .. " (" .. type(ent) .. ")")
    if not ent then print("无实体，退出"); return end

    local n, set = 0, 0
    for _, k in ipairs(keys()) do
        n = n + 1
        -- ⚠ 先落局部变量：GetProperty 未设置时返回 0 个值，直接塞进 tostring 会报错
        local v = ent:GetProperty(k)
        if v and v ~= 0 then
            set = set + 1
            print(string.format("   %-58s = %s", k, S(v)))
        end
    end
    print(string.format("清单 %d 条，其中已置位 %d 条", n, set))
    if set == 0 then
        print("   ⚠ 全为 0/未设置 —— 先确认：属性键拼对了吗？mod 的写属性逻辑跑过吗？依赖实体（如虚拟建筑）存在吗？")
    end

    -- ⚠ Members() 双返回：用 for _, x 才拿到对象
    local cities = {}
    for _, c in Players[CONFIG.PLAYER_ID]:GetCities():Members() do cities[#cities + 1] = c end
    print("")
    print("=== 各城市该清单的置位数 ===")
    for _, c in ipairs(cities) do
        local plot = Map.GetPlot(c:GetX(), c:GetY())
        local cnt = 0
        for _, k in ipairs(keys()) do
            local v = plot:GetProperty(k)
            if v and v ~= 0 then cnt = cnt + 1 end
        end
        print(string.format("   城%-8s (%s,%s) 置位 %d", tostring(c:GetID()), tostring(c:GetX()), tostring(c:GetY()), cnt))
    end
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
