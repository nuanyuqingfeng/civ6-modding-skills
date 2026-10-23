-- faith-inject.lua —— 设定或增减信仰值（gamecore 上下文）
-- 用法：python tuner_exec.py act faith-inject --amount 500
--       python tuner_exec.py act faith-inject --amount 100 --delta
--
-- 参数
--   AMOUNT  目标余额；DELTA 为真时按增量解释
--   DELTA   增量语义
--   PID     玩家编号，-1 表示本地玩家
--
-- 前置断言
--   Players[pid] 存在；GetReligion() 返回对象的 SetFaithBalance / ChangeFaithBalance 为 function
--
-- 执行步骤
--   1. 读当前信仰 BEFORE
--   2. DELTA 时 ChangeFaithBalance，否则 SetFaithBalance
--   3. 回读信仰 AFTER
--
-- 成功判据
--   AFTER 与预期一致；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 不校验万神殿/宗教是否已创立
--   2. 写入只有 gamecore 侧可用，UI 侧只有 GetFaithBalance

-- ===== CONFIG =====
local CONFIG = {
    AMOUNT = 0,
    DELTA = false,
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== FAITH-INJECT START ===")

if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pPlayer = Players[CONFIG.PID]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
    error("玩家不存在：" .. S(CONFIG.PID))
end

local pReligion = pPlayer:GetReligion()
if type(pReligion.SetFaithBalance) ~= "function" then
    print("ASSERTION_FAIL|religion_unwritable=" .. S(type(pReligion.SetFaithBalance)))
    error("信仰写入接口不可用：本态不是 gamecore")
end
print("ASSERTION_OK|religion_exist|pid=" .. S(CONFIG.PID))

local before = pReligion:GetFaithBalance()
print("BEFORE=" .. S(before))

if CONFIG.DELTA then
    pReligion:ChangeFaithBalance(CONFIG.AMOUNT)
    print("EXECUTE|ChangeFaithBalance|" .. S(CONFIG.AMOUNT))
else
    pReligion:SetFaithBalance(CONFIG.AMOUNT)
    print("EXECUTE|SetFaithBalance|" .. S(CONFIG.AMOUNT))
end

local after = pReligion:GetFaithBalance()
local expect = CONFIG.DELTA and (before + CONFIG.AMOUNT) or CONFIG.AMOUNT
print("AFTER=" .. S(after))
print("EXPECT=" .. S(expect))

if math.abs(after - expect) > 0.5 then
    print("FINAL=FAIL|mismatch")
    error("信仰回读不一致：" .. S(after) .. " ~= " .. S(expect))
end
print("FINAL=OK")
print("=== FAITH-INJECT COMPLETE ===")
