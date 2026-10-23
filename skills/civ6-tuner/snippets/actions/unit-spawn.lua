-- unit-spawn.lua —— 在地块刷单位（gamecore 上下文）
-- 用法：python tuner_exec.py act unit-spawn --type UNIT_WARRIOR --x 10 --y 12 --count 2
--
-- 参数
--   TYPE   单位类型名（GameInfo.Units 的 UnitType）
--   X / Y  地块坐标
--   COUNT  生成数量
--   PID    玩家编号，-1 表示本地玩家
--
-- 前置断言
--   Players[pid] 存在；TYPE 在 GameInfo.Units 内；Map.GetPlot(X, Y) 非空；
--   该地块不是水域、不可通行或有主他人
--
-- 执行步骤
--   1. 校验地块：存在、非水域、非不可通行
--   2. 按 COUNT 逐个调用 UnitManager.InitUnit
--   3. 回读每个新单位的地块坐标，确认落点正确
--
-- 成功判据
--   SPAWN_SUCCESS 行数等于 COUNT，且每个回读坐标等于请求坐标；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. InitUnit 不校验地形，陆军刷到水域会被引擎清除并留下 -9999 坐标的僵尸句柄，
--      因此刷兵前必须先查地形（本动作已内置该检查）
--   2. 同格堆叠超过引擎上限时多余单位会被挤到相邻格，回读坐标随之不同，按失败处理
--   3. 只有 gamecore 侧可写，UI 侧 UnitManager.InitUnit 为 nil

-- ===== CONFIG =====
local CONFIG = {
    TYPE = "",
    X = 0,
    Y = 0,
    COUNT = 1,
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== UNIT-SPAWN START ===")

if CONFIG.TYPE == "" then
    print("ASSERTION_FAIL|type_empty")
    error("必须给出 --type")
end
if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pPlayer = Players[CONFIG.PID]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
    error("玩家不存在：" .. S(CONFIG.PID))
end

local unitRow = nil
for row in GameInfo.Units() do
    if row.UnitType == CONFIG.TYPE then
        unitRow = row
        break
    end
end
if unitRow == nil then
    print("ASSERTION_FAIL|unit_not_in_db|" .. CONFIG.TYPE)
    error("库里没有该单位类型：" .. CONFIG.TYPE)
end
print("ASSERTION_OK|unit_in_db|" .. CONFIG.TYPE)

if type(UnitManager.InitUnit) ~= "function" then
    print("ASSERTION_FAIL|initunit=" .. S(type(UnitManager.InitUnit)))
    error("刷兵接口不可用：本态不是 gamecore")
end

local plot = Map.GetPlot(CONFIG.X, CONFIG.Y)
if plot == nil then
    print("ASSERTION_FAIL|plot_missing|" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))
    error("地块不存在：" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))
end
local domain = unitRow.Domain
if plot:IsWater() and domain ~= "DOMAIN_SEA" then
    print("ASSERTION_FAIL|land_unit_on_water|domain=" .. S(domain))
    error("陆地单位不能刷在水域地块")
end
if plot:IsImpassable() then
    print("ASSERTION_FAIL|plot_impassable")
    error("地块不可通行")
end
print("ASSERTION_OK|plot_valid|" .. S(CONFIG.X) .. "," .. S(CONFIG.Y) ..
    "|water=" .. S(plot:IsWater()))

local spawned = 0
for i = 1, CONFIG.COUNT do
    local u = UnitManager.InitUnit(CONFIG.PID, CONFIG.TYPE, CONFIG.X, CONFIG.Y)
    if u == nil then
        print("SPAWN_FAIL|index=" .. i)
        print("FINAL=FAIL|initunit_nil")
        error("InitUnit 返回空单位：第 " .. i .. " 个")
    end
    local ux, uy = u:GetX(), u:GetY()
    print("SPAWN_SUCCESS|id=" .. S(u:GetID()) .. "|type=" .. CONFIG.TYPE ..
        "|at=" .. S(ux) .. "," .. S(uy))
    if ux ~= CONFIG.X or uy ~= CONFIG.Y then
        print("SPAWN_MOVED|expected=" .. S(CONFIG.X) .. "," .. S(CONFIG.Y) ..
            "|actual=" .. S(ux) .. "," .. S(uy))
        print("FINAL=FAIL|spawn_position_mismatch")
        error("单位落点与请求坐标不一致：引擎把单位挤到了相邻格")
    end
    spawned = spawned + 1
end

print("VERIFY_SPAWNED_COUNT=" .. S(spawned))
if spawned ~= CONFIG.COUNT then
    print("FINAL=FAIL|count_mismatch")
    error("生成数量不一致：" .. S(spawned) .. " ~= " .. S(CONFIG.COUNT))
end
print("FINAL=OK")
print("=== UNIT-SPAWN COMPLETE ===")
