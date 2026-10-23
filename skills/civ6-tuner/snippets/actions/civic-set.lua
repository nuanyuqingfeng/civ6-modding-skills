-- civic-set.lua —— 把某项市政设为当前推进目标（ingame 上下文）
-- 用法：python tuner_exec.py act civic-set --civic CIVIC_FOREIGN_TRADE
--
-- 参数
--   CIVIC  市政类型名（GameInfo.Civics 的 CivicType）
--   PID    玩家编号，-1 表示本地玩家
--
-- 前置断言
--   ingame 态可达；UI.RequestPlayerOperation 与 PlayerOperations.PROGRESS_CIVIC 存在；
--   CIVIC 在库内；该市政未完成
--
-- 执行步骤
--   1. 读当前推进目标 BEFORE_CIVIC
--   2. 按 CivicsChooser.lua:245-250 的写法发起 PROGRESS_CIVIC 操作（VALUE_EXCLUSIVE）
--   3. 轮询回读 GetProgressingCivic 直到等于目标市政或超时
--
-- 成功判据
--   VERIFY_CIVIC 等于请求的市政；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 只设当前推进目标，不改文化进度；进度类需求用 civic-complete
--   2. 已完成市政由引擎拒绝，本动作在操作前先断言未完成
--   3. 推进为异步派发，回读在上限 RETRY 次内轮询

-- ===== CONFIG =====
local CONFIG = {
    CIVIC = "",
    PID = -1,
    RETRY = 20,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== CIVIC-SET START ===")

if CONFIG.CIVIC == "" then
    print("ASSERTION_FAIL|civic_empty")
    error("必须给出 --civic")
end
if type(UI.RequestPlayerOperation) ~= "function" then
    print("ASSERTION_FAIL|requestplayeroperation=" .. S(type(UI.RequestPlayerOperation)))
    error("玩家操作接口不可用：本态不是 ingame")
end
if type(PlayerOperations) ~= "table" or PlayerOperations.PROGRESS_CIVIC == nil then
    print("ASSERTION_FAIL|playeroperations_progress_civic")
    error("PlayerOperations.PROGRESS_CIVIC 不可用")
end
print("ASSERTION_OK|player_operation_api")

if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pPlayer = Players[CONFIG.PID]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
    error("玩家不存在：" .. S(CONFIG.PID))
end

local index = nil
local hash = nil
for row in GameInfo.Civics() do
    if row.CivicType == CONFIG.CIVIC then
        index = row.Index
        hash = row.Hash
        break
    end
end
if index == nil then
    print("ASSERTION_FAIL|civic_not_in_db|" .. CONFIG.CIVIC)
    error("库里没有该市政：" .. CONFIG.CIVIC)
end
print("ASSERTION_OK|civic_in_db|" .. CONFIG.CIVIC .. "|index=" .. S(index) .. "|hash=" .. S(hash))

local pCulture = pPlayer:GetCulture()
if pCulture:HasCivic(index) then
    print("ASSERTION_FAIL|civic_already_completed|" .. CONFIG.CIVIC)
    error("该市政已完成，不能设为推进目标：" .. CONFIG.CIVIC)
end

local before = pCulture:GetProgressingCivic()
if before ~= nil and before >= 0 then
    print("BEFORE_CIVIC=" .. GameInfo.Civics[before].CivicType)
else
    print("BEFORE_CIVIC=none")
end

local t = {}
t[PlayerOperations.PARAM_CIVIC_TYPE] = hash
t[PlayerOperations.PARAM_INSERT_MODE] = PlayerOperations.VALUE_EXCLUSIVE
UI.RequestPlayerOperation(CONFIG.PID, PlayerOperations.PROGRESS_CIVIC, t)
print("EXECUTE|PROGRESS_CIVIC|" .. CONFIG.CIVIC)

local actual = nil
for _ = 1, CONFIG.RETRY do
    actual = pCulture:GetProgressingCivic()
    if actual == index then
        break
    end
end

if actual ~= nil and actual >= 0 then
    print("VERIFY_CIVIC=" .. GameInfo.Civics[actual].CivicType)
else
    print("VERIFY_CIVIC=none")
end

if actual ~= index then
    print("FINAL=FAIL|civic_mismatch")
    error("推进目标回读不一致，请求 " .. CONFIG.CIVIC)
end
print("FINAL=OK")
print("=== CIVIC-SET COMPLETE ===")
