-- fog-reveal.lua —— 揭示指定地块周围视野（gamecore 上下文）
-- 用法：python tuner_exec.py act fog-reveal --x 10 --y 12 --radius 3
--
-- 参数
--   PID     玩家编号，-1 表示本地玩家
--   X / Y   中心地块坐标
--   RADIUS  揭示半径（方形范围）
--
-- 前置断言
--   全局表 PlayersVisibility[pid] 存在；IsRevealed / ChangeVisibilityCount 为 function；
--   中心地块存在；地块索引经 plot:GetIndex() 取得且为 number
--
-- 执行步骤
--   1. 统计范围内总地块数与已揭示地块数，输出 BEFORE_REVEALED
--   2. 对未揭示地块逐格 ChangeVisibilityCount(idx, 1) 再 (idx, -1)，净额归零但永久揭示生效
--   3. 重新统计已揭示地块数，输出 AFTER_REVEALED
--
-- 成功判据
--   AFTER_REVEALED 等于范围内总地块数；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 半径按方形范围计算，六边形距离未实现
--   2. player:GetVisibility() 与 Plot:IsRevealed 双端均为 nil，唯一入口是全局表 PlayersVisibility
--   3. 只影响视野揭示状态，不改变地块归属与已探索标记之外的任何游戏状态

-- ===== CONFIG =====
local CONFIG = {
    PID = -1,
    X = 0,
    Y = 0,
    RADIUS = 3,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== FOG-REVEAL START ===")

if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pVis = PlayersVisibility[CONFIG.PID]
if pVis == nil then
    print("ASSERTION_FAIL|visibility_missing|pid=" .. S(CONFIG.PID))
    error("视野管理器不存在：" .. S(CONFIG.PID))
end
if type(pVis.ChangeVisibilityCount) ~= "function" then
    print("ASSERTION_FAIL|visibility_unwritable=" .. S(type(pVis.ChangeVisibilityCount)))
    error("视野写入接口不可用")
end
print("ASSERTION_OK|visibility_manager|pid=" .. S(CONFIG.PID))

local center = Map.GetPlot(CONFIG.X, CONFIG.Y)
if center == nil then
    print("ASSERTION_FAIL|plot_missing|" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))
    error("中心地块不存在：" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))
end
print("ASSERTION_OK|plot_exist|" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))

local targets = {}
for dx = -CONFIG.RADIUS, CONFIG.RADIUS do
    for dy = -CONFIG.RADIUS, CONFIG.RADIUS do
        local p = Map.GetPlot(CONFIG.X + dx, CONFIG.Y + dy)
        if p ~= nil then
            local idx = p:GetIndex()
            if type(idx) ~= "number" then
                print("ASSERTION_FAIL|plot_index_not_number|" ..
                    S(CONFIG.X + dx) .. "," .. S(CONFIG.Y + dy) .. "|type=" .. S(type(idx)))
                error("地块索引不是数字：" .. S(CONFIG.X + dx) .. "," .. S(CONFIG.Y + dy))
            end
            table.insert(targets, idx)
        end
    end
end
print("TARGET_PLOTS=" .. S(#targets))

local function countRevealed()
    local n = 0
    for _, idx in ipairs(targets) do
        if pVis:IsRevealed(idx) then
            n = n + 1
        end
    end
    return n
end

local before = countRevealed()
print("BEFORE_REVEALED=" .. S(before))

local revealed = 0
for _, idx in ipairs(targets) do
    if not pVis:IsRevealed(idx) then
        pVis:ChangeVisibilityCount(idx, 1)
        pVis:ChangeVisibilityCount(idx, -1)
        revealed = revealed + 1
    end
end
print("EXECUTE|revealed_new_plots=" .. S(revealed))

local after = countRevealed()
print("AFTER_REVEALED=" .. S(after))

if after ~= #targets then
    print("FINAL=FAIL|incomplete|revealed=" .. S(after) .. "/" .. S(#targets))
    error("揭示不完整：" .. S(after) .. " / " .. S(#targets))
end
print("FINAL=OK")
print("=== FOG-REVEAL COMPLETE ===")
