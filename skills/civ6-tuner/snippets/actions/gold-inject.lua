-- gold-inject.lua —— 设定或增减金币（gamecore 上下文）
-- 用法：python tuner_exec.py act gold-inject --amount 10000
--       python tuner_exec.py act gold-inject --amount 500 --delta
--
-- 参数
--   AMOUNT  目标余额；DELTA 为真时按增量解释
--   DELTA   增量语义
--   PID     玩家编号，-1 表示本地玩家
--
-- 前置断言
--   Players[pid] 存在；GetTreasury() 返回对象的 SetGoldBalance / ChangeGoldBalance 为 function
--
-- 执行步骤
--   1. 读当前余额 BEFORE
--   2. DELTA 时 ChangeGoldBalance，否则 SetGoldBalance
--   3. 回读余额 AFTER
--
-- 成功判据
--   AFTER 与 BEGIN + AMOUNT（增量）或 AMOUNT（设定）一致；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 不校验负债与每回合收入，引擎对负余额的处置由引擎自行决定
--   2. 双端都有 GetGoldBalance，写入只有 gamecore 侧可用

-- ===== CONFIG =====
local CONFIG = {
    AMOUNT = 0,
    DELTA = false,
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== GOLD-INJECT START ===")

if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pPlayer = Players[CONFIG.PID]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
    error("玩家不存在：" .. S(CONFIG.PID))
end

local pTreasury = pPlayer:GetTreasury()
if type(pTreasury.SetGoldBalance) ~= "function" then
    print("ASSERTION_FAIL|treasury_unwritable=" .. S(type(pTreasury.SetGoldBalance)))
    error("国库写入接口不可用：本态不是 gamecore")
end
print("ASSERTION_OK|treasury_exist|pid=" .. S(CONFIG.PID))

local before = pTreasury:GetGoldBalance()
print("BEFORE=" .. S(before))

if CONFIG.DELTA then
    pTreasury:ChangeGoldBalance(CONFIG.AMOUNT)
    print("EXECUTE|ChangeGoldBalance|" .. S(CONFIG.AMOUNT))
else
    pTreasury:SetGoldBalance(CONFIG.AMOUNT)
    print("EXECUTE|SetGoldBalance|" .. S(CONFIG.AMOUNT))
end

local after = pTreasury:GetGoldBalance()
local expect = CONFIG.DELTA and (before + CONFIG.AMOUNT) or CONFIG.AMOUNT
print("AFTER=" .. S(after))
print("EXPECT=" .. S(expect))

if math.abs(after - expect) > 0.5 then
    print("FINAL=FAIL|mismatch")
    error("金币回读不一致：" .. S(after) .. " ~= " .. S(expect))
end
print("FINAL=OK")
print("=== GOLD-INJECT COMPLETE ===")
