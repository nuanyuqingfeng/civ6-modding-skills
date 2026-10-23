-- select-unit.lua —— 按条件筛选并选中一个单位（ingame 上下文）
-- 用法：python tuner_exec.py act select-unit --type UNIT_WARRIOR
--       python tuner_exec.py act select-unit --x 10 --y 12
--       python tuner_exec.py act select-unit --radius 3 --hp-threshold 100
--
-- 参数
--   TYPE          单位类型名，空表示不按类型筛选
--   X / Y         地块坐标，-1 表示不按坐标筛选（两者需同时给出）
--   RADIUS        以本地玩家首都为中心的方形半径，-1 表示不按半径筛选
--   HP_THRESHOLD  血量百分比上限（只接受不高于该值的单位），-1 表示不筛选
--   PROMOTION     要求已获得该晋升类型名，空表示不筛选
--
-- 前置断言
--   ingame 态可达；UI.SelectUnit / UI.GetHeadSelectedUnit 为 function；
--   Players[pid]:GetUnits() 可枚举
--
-- 执行步骤
--   1. 按 TYPE / 坐标 / 半径 / 血量 / 晋升逐项筛选，取第一个命中的单位
--   2. UI.SelectUnit(unit) 选中
--   3. 回读 UI.GetHeadSelectedUnit() 的 GetID 与 GetType
--
-- 成功判据
--   FOUND_MATCH 与 VERIFY_SELECTED 的 ID 一致；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 六边形距离未实现，RADIUS 按方形范围计算
--   2. 单位清单取 UI 侧集合，刚被删除的单位会作为幽灵行出现（只影响候选数量）
--   3. 晋升筛选依赖 Unit:GetExperience() 子对象，未获取晋升时该子对象可能为空
--   4. 主体必须包在 main() 里：顶层 chunk 里的 return 会结束整个 chunk，
--      连带吞掉 execute() 补的哨兵，表现为「收集到若干行后超时」

-- ===== CONFIG =====
local CONFIG = {
    TYPE = "",
    X = -1,
    Y = -1,
    RADIUS = -1,
    HP_THRESHOLD = -1,
    PROMOTION = "",
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function main()
    print("=== SELECT-UNIT START ===")

    if type(UI.SelectUnit) ~= "function" then
        print("ASSERTION_FAIL|ui_selectunit=" .. S(type(UI.SelectUnit)))
        error("选中接口不可用：本态不是 ingame")
    end
    print("ASSERTION_OK|ui_select_api")

    local pid = Game.GetLocalPlayer()
    local pPlayer = Players[pid]
    if pPlayer == nil then
        print("ASSERTION_FAIL|player_missing|pid=" .. S(pid))
        error("本地玩家不存在：" .. S(pid))
    end
    print("ASSERTION_OK|player_exist|pid=" .. S(pid))

    local center = nil
    if CONFIG.RADIUS >= 0 then
        local cap = pPlayer:GetCities():GetCapitalCity()
        if cap == nil then
            print("ASSERTION_FAIL|no_capital")
            error("按半径筛选需要首都，当前没有首都（先建城）")
        end
        center = { x = cap:GetX(), y = cap:GetY() }
        print("CENTER|capital|" .. S(center.x) .. "," .. S(center.y))
    end

    local total = 0
    local match = nil
    for _, u in pPlayer:GetUnits():Members() do
        total = total + 1
        local ok = true

        if CONFIG.TYPE ~= "" then
            local uType = GameInfo.Units[u:GetType()].UnitType
            if uType ~= CONFIG.TYPE then ok = false end
        end

        if ok and CONFIG.X >= 0 and CONFIG.Y >= 0 then
            if u:GetX() ~= CONFIG.X or u:GetY() ~= CONFIG.Y then ok = false end
        end

        if ok and center ~= nil then
            local dx = math.abs(u:GetX() - center.x)
            local dy = math.abs(u:GetY() - center.y)
            if dx > CONFIG.RADIUS or dy > CONFIG.RADIUS then ok = false end
        end

        if ok and CONFIG.HP_THRESHOLD >= 0 then
            local maxHp = u:GetMaxDamage()
            local dmg = u:GetDamage()
            local pct = (maxHp - dmg) * 100 / maxHp
            if pct > CONFIG.HP_THRESHOLD then ok = false end
        end

        if ok and CONFIG.PROMOTION ~= "" then
            local has = false
            local exp = u:GetExperience()
            for _, promo in ipairs(exp:GetPromotions()) do
                if GameInfo.UnitPromotions[promo].UnitPromotionType == CONFIG.PROMOTION then
                    has = true
                    break
                end
            end
            if not has then ok = false end
        end

        if ok and match == nil then
            match = u
        end
    end

    print("CANDIDATE_COUNT=" .. S(total))

    if match == nil then
        print("FOUND_MATCH=none")
        print("FAIL_REASON=no_unit_matching_filters")
        print("FINAL=FAIL|no_match")
        print("=== SELECT-UNIT COMPLETE ===")
        return
    end

    local mid = match:GetID()
    local mtype = GameInfo.Units[match:GetType()].UnitType
    print("FOUND_MATCH|Unit ID=" .. S(mid) .. " Type=" .. mtype ..
        " Pos=" .. S(match:GetX()) .. "," .. S(match:GetY()))

    UI.SelectUnit(match)
    local selected = UI.GetHeadSelectedUnit()
    if selected == nil then
        print("VERIFY_SELECTED=nil")
        print("FINAL=FAIL|selection_empty")
        error("选中后回读为空")
    end

    local sid = selected:GetID()
    local stype = GameInfo.Units[selected:GetType()].UnitType
    print("VERIFY_SELECTED: Expected=" .. S(mid) .. " Actual=" .. S(sid))

    if sid ~= mid then
        print("FINAL=FAIL|selection_mismatch")
        error("选中结果不一致：" .. S(sid) .. " ~= " .. S(mid))
    end

    print("SELECTED_TYPE=" .. stype)
    print("FINAL=OK")
    print("=== SELECT-UNIT COMPLETE ===")
end

main()
