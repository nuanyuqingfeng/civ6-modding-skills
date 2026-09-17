-- ===========================================================================
-- settle_read.lua —— 对抗「重算延迟」的稳定读数
--   用途：紧凑循环里反复「置位 → 读 → 复位」时，复位未必在同帧被下游重算，
--         会让下一条的基线带上前一条残留（实测：批量跑信仰转化类得到 +0.898438
--         = 0.15×6，正好等于前三条残留之和；隔离复测为 0）。
--   做法：连续读 N 次，两次一致才认为"稳定"，否则报告不稳定并给出观测序列。
--   用法：改 CONFIG 后跑
--     python tuner_exec.py exec --context gamecore --file snippets/settle_read.lua
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    PLAYER_ID   = 0,
    MAX_TRIES   = 8,          -- 最多读几次
    YIELDS      = { 0, 1, 2, 3, 4, 5 },
    YNAME       = { "FOOD", "PRODUCTION", "GOLD", "SCIENCE", "CULTURE", "FAITH" },
    -- 可选：在这条读之前先做一次属性复位，检验"复位后是否真的回基线"
    RESET_PROPERTY = nil,     -- 例："PROPERTY_CTTH_SWORD_DIVINITY_FAITH_HARVEST"
}

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function cities()
    local t = {}
    -- ⚠ Members() 是 (key, value) 双返回迭代器
    for _, c in Players[CONFIG.PLAYER_ID]:GetCities():Members() do t[#t + 1] = c end
    return t
end

local function snap()
    local out = {}
    for _, c in ipairs(cities()) do
        local row = {}
        for _, i in ipairs(CONFIG.YIELDS) do
            local ok, v = pcall(function() return c:GetYield(i) end)
            row[i] = (ok and type(v) == "number") and v or nil
        end
        out[c:GetID()] = row
    end
    return out
end

local function same(a, b)
    for id, ra in pairs(a) do
        local rb = b[id]
        if not rb then return false end
        for _, i in ipairs(CONFIG.YIELDS) do
            if math.abs((ra[i] or 0) - (rb[i] or 0)) > 1e-9 then return false end
        end
    end
    return true
end

local function fmt(s)
    local parts = {}
    for id, row in pairs(s) do
        local one = {}
        for _, i in ipairs(CONFIG.YIELDS) do
            one[#one + 1] = string.format("%s=%s", CONFIG.YNAME[i + 1] or ("y" .. i), S(row[i]))
        end
        parts[#parts + 1] = "城" .. tostring(id) .. "[" .. table.concat(one, " ") .. "]"
    end
    table.sort(parts)
    return table.concat(parts, "  ")
end

local function main()
    if CONFIG.RESET_PROPERTY then
        local cap = Players[CONFIG.PLAYER_ID]:GetCities():GetCapitalCity()
        local plot = cap and Map.GetPlot(cap:GetX(), cap:GetY())
        if plot then
            plot:SetProperty(CONFIG.RESET_PROPERTY, nil)
            print("[RESET] 已清除 " .. CONFIG.RESET_PROPERTY)
        end
    end

    local prev, cur = nil, snap()
    local seq = { fmt(cur) }
    local stable = false
    for i = 2, CONFIG.MAX_TRIES do
        prev, cur = cur, snap()
        seq[#seq + 1] = fmt(cur)
        if same(prev, cur) then
            stable = true
            print(string.format(">>> 【已稳定】第 %d 次读数与前一次一致", i))
            break
        end
    end

    print("")
    print("读数序列：")
    for i, s in ipairs(seq) do print(string.format("  #%d %s", i, s)) end
    print("")
    if not stable then
        print(string.format(">>> 【未稳定】%d 次读数仍在变化 —— 说明重算确实有延迟/异步，", CONFIG.MAX_TRIES))
        print("    此时不要立刻下结论；改用「分段 + 过回合」或拉长间隔再读。")
    end
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
