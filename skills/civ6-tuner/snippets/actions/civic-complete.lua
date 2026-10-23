-- civic-complete.lua —— 完成一项市政（gamecore 上下文）
-- 用法：python tuner_exec.py act civic-complete --civic CIVIC_CODE_OF_LAWS
--
-- 参数
--   CIVIC  市政类型名（GameInfo.Civics 的 CivicType）
--   PID    玩家编号，-1 表示本地玩家
--
-- 前置断言
--   Players[pid] 存在；CIVIC 在 GameInfo.Civics 内；GetCulture() 的
--   SetCulturalProgress / HasCivic 为 function
--
-- 执行步骤
--   1. 读 HasCivic 当前值
--   2. 已有时直接给出 ALREADY=true，不重复写入
--   3. 未有时 SetCulturalProgress(市政索引, 文化成本) 一次做满
--   4. 回读 HasCivic 与 GetCulturalProgress
--
-- 成功判据
--   VERIFY_HAS_CIVIC=true；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 鼓舞（Inspiration）不随之记为已触发，且本动作不改 Boosts 状态
--   2. 政策卡与政体解锁由引擎按市政完成事件下发，本动作不额外解锁
--   3. 只有 gamecore 侧可写，UI 侧只有 HasCivic 查询

-- ===== CONFIG =====
local CONFIG = {
    CIVIC = "",
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function main()
print("=== CIVIC-COMPLETE START ===")

if CONFIG.CIVIC == "" then
    print("ASSERTION_FAIL|civic_empty")
    error("必须给出 --civic")
end
if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pPlayer = Players[CONFIG.PID]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
    error("玩家不存在：" .. S(CONFIG.PID))
end

local index = nil
for row in GameInfo.Civics() do
    if row.CivicType == CONFIG.CIVIC then
        index = row.Index
        break
    end
end
if index == nil then
    print("ASSERTION_FAIL|civic_not_in_db|" .. CONFIG.CIVIC)
    error("库里没有该市政：" .. CONFIG.CIVIC)
end
print("ASSERTION_OK|civic_in_db|" .. CONFIG.CIVIC .. "|index=" .. S(index))

local pCulture = pPlayer:GetCulture()
if type(pCulture.SetCulturalProgress) ~= "function" then
    print("ASSERTION_FAIL|culture_unwritable=" .. S(type(pCulture.SetCulturalProgress)))
    error("市政写入接口不可用：本态不是 gamecore")
end

local already = pCulture:HasCivic(index)
print("BEFORE_HAS_CIVIC=" .. S(already))
if already then
    print("EXECUTE|skipped|already_completed")
    print("VERIFY_HAS_CIVIC=true")
    print("FINAL=OK")
    print("=== CIVIC-COMPLETE COMPLETE ===")
    return
end

local cost = pCulture:GetCultureCost(index)
print("COST=" .. S(cost))
pCulture:SetCulturalProgress(index, cost)
print("EXECUTE|SetCulturalProgress|" .. S(cost))

local after = pCulture:HasCivic(index)
print("VERIFY_HAS_CIVIC=" .. S(after))
print("VERIFY_COST=" .. S(cost))

if not after then
    print("FINAL=FAIL|has_civic_false")
    error("市政未标记为已完成：" .. CONFIG.CIVIC)
end
print("FINAL=OK")
print("=== CIVIC-COMPLETE COMPLETE ===")
end

main()
