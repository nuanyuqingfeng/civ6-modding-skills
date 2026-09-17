-- ===========================================================================
-- prop_ab.lua —— PROPERTY 开关 A/B：验证「某属性是否立即生效」
--   用法：按 CONFIG 改目标实体与属性键，然后两端各跑一次（一般 gamecore 即可）
--     python tuner_exec.py exec --context gamecore --file snippets/prop_ab.lua
--
--   实测背书：地块属性置位后 **同帧** 即影响产出（示例工程 实测 FAITH 0→6，
--   与 Modifier Amount=6 精确吻合），复位精确回基线 → 不需要过回合。
--
--   ⚠ 前提陷阱：修饰器若挂在【建筑/单位】上，依赖实体不存在时属性置位毫无效果，
--     会得到"假阴性"。动手前先确认依赖实体存在（如首都是否已拥有该虚拟建筑）。
--   ⚠ 顺序陷阱：紧凑循环里反复「置位→读→复位」，复位未必在同帧被重算，
--     会让下一条的基线带上前一条残留。批量测试务必分段 + 复位确认。
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    PLAYER_ID   = 0,
    -- 属性挂在哪个实体：'plot'（首都地块）| 'player' | 'game'
    TARGET      = "plot",
    PROPERTY    = "PROPERTY_CTTH_SWORD_DIVINITY_FAITH_HARVEST",
    -- 观测哪些产出（Yields 索引：0食 1锤 2金 3科 4文 5信）
    YIELDS      = { 0, 1, 2, 3, 4, 5 },
    YNAME       = { "FOOD", "PRODUCTION", "GOLD", "SCIENCE", "CULTURE", "FAITH" },
}

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function target()
    local pl = Players[CONFIG.PLAYER_ID]
    if CONFIG.TARGET == "plot" then
        local cap = pl:GetCities():GetCapitalCity()
        if not cap then return nil end
        return Map.GetPlot(cap:GetX(), cap:GetY()), cap
    elseif CONFIG.TARGET == "player" then
        return pl, nil
    else
        return Game, nil
    end
end

local function cities()
    local t = {}
    -- ⚠ Members() 是 (key, value) 双返回迭代器；写成 for c in ... 会拿到数字 key
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

local function show(tag, s)
    for id, row in pairs(s) do
        local parts = {}
        for _, i in ipairs(CONFIG.YIELDS) do
            parts[#parts + 1] = string.format("%s=%s", CONFIG.YNAME[i + 1] or ("y" .. i), S(row[i]))
        end
        print(string.format("  [%-10s] 城%-8s %s", tag, tostring(id), table.concat(parts, "  ")))
    end
end

local function main()
    local ent, cap = target()
    print(string.format("目标实体 = %s（PLAYER=%d %s）", S(ent), CONFIG.PLAYER_ID,
        cap and ("首都(" .. cap:GetX() .. "," .. cap:GetY() .. ")") or ""))
    if not ent then print("无目标实体，退出"); return end

    print("属性 = " .. CONFIG.PROPERTY)
    print("置位前 = " .. S(ent:GetProperty(CONFIG.PROPERTY)))

    local a = snap()
    ent:SetProperty(CONFIG.PROPERTY, 1)
    local b = snap()
    ent:SetProperty(CONFIG.PROPERTY, nil)
    local c = snap()

    print("")
    show("基线", a)
    show("置位", b)
    show("复位", c)

    print("")
    print("===== 差量 =====")
    local anyOn, anyBack = false, false
    for id, row in pairs(b) do
        local one, back = {}, {}
        for _, i in ipairs(CONFIG.YIELDS) do
            local d1 = (row[i] or 0) - ((a[id] or {})[i] or 0)
            local d2 = ((c[id] or {})[i] or 0) - ((a[id] or {})[i] or 0)
            if math.abs(d1) > 1e-9 then anyOn = true; one[#one + 1] = string.format("%s%+g", CONFIG.YNAME[i + 1], d1) end
            if math.abs(d2) > 1e-9 then anyBack = true; back[#back + 1] = string.format("%s%+g", CONFIG.YNAME[i + 1], d2) end
        end
        print(string.format("  城%-8s 置位-基线: %-40s 复位-基线: %s", tostring(id),
            #one > 0 and table.concat(one, " ") or "（无变化）",
            #back > 0 and table.concat(back, " ") or "（无变化）"))
    end
    print("")
    if anyOn and not anyBack then
        print(">>> 【立即生效且可逆】置位即变化、复位即回基线 ✔")
    elseif not anyOn then
        print(">>> 【零变化】可能是：属性键写错 / 依赖实体不存在（假阴性）/ 修饰器类型不在产出上")
    else
        print(">>> 【有变化但复位未回基线】注意残留或重算延迟")
    end
end

local ok, err = pcall(main)
if not ok then print("pcall err=" .. tostring(err)) end
