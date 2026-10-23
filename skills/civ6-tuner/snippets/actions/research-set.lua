-- research-set.lua —— 设定当前研究的科技（ingame 上下文）
-- 用法：python tuner_exec.py act research-set --tech TECH_POTTERY
--
-- 参数
--   TECH  科技类型名（GameInfo.Technologies 的 TechnologyType）
--   PID   玩家编号，-1 表示本地玩家
--
-- 前置断言
--   ingame 态可达；PlayerOperations.RESEARCH 与 PARAM_TECH_TYPE 可索引；
--   TECH 在 GameInfo.Technologies 内
--
-- 执行步骤
--   1. 按类型名查科技行取 Hash
--   2. 按官方 ResearchChooser 的写法发 RESEARCH 操作
--      （PARAM_TECH_TYPE + PARAM_INSERT_MODE=VALUE_EXCLUSIVE）
--   3. 回读 ResearchingTech 的索引与类型名
--
-- 成功判据
--   VERIFY_RESEARCHING 等于请求的科技类型名；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 操作异步结算，回读在同一 chunk 内完成，个别情况下需要再查询一次才稳定
--   2. 已完成或前置不满足的科技由引擎拒绝，本动作按回读不一致报失败
--   3. 只有 UI 侧能发玩家操作，gamecore 侧 PlayerOperations 是 table 但操作不会生效

-- ===== CONFIG =====
local CONFIG = {
    TECH = "",
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== RESEARCH-SET START ===")

if CONFIG.TECH == "" then
    print("ASSERTION_FAIL|tech_empty")
    error("必须给出 --tech")
end
if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end

if type(PlayerOperations) ~= "table" then
    print("ASSERTION_FAIL|playeroperations=" .. S(type(PlayerOperations)))
    error("PlayerOperations 不可用：本态不能发玩家操作")
end
if type(PlayerOperations.RESEARCH) ~= "number" then
    print("ASSERTION_FAIL|research_op=" .. S(type(PlayerOperations.RESEARCH)))
    error("PlayerOperations.RESEARCH 不是数字")
end
print("ASSERTION_OK|player_operations")

local techRow = nil
for row in GameInfo.Technologies() do
    if row.TechnologyType == CONFIG.TECH then
        techRow = row
        break
    end
end
if techRow == nil then
    print("ASSERTION_FAIL|tech_not_in_db|" .. CONFIG.TECH)
    error("库里没有该科技：" .. CONFIG.TECH)
end
print("ASSERTION_OK|tech_in_db|" .. CONFIG.TECH ..
    "|index=" .. S(techRow.Index) .. "|hash=" .. S(techRow.Hash))

local pPlayer = Players[CONFIG.PID]
local pTechs = pPlayer:GetTechs()
local before = pTechs:GetResearchingTech()
if before ~= nil and before >= 0 then
    print("BEFORE_RESEARCHING=" .. S(GameInfo.Technologies[before].TechnologyType))
else
    print("BEFORE_RESEARCHING=none")
end

local params = {}
params[PlayerOperations.PARAM_TECH_TYPE] = techRow.Hash
params[PlayerOperations.PARAM_INSERT_MODE] = PlayerOperations.VALUE_EXCLUSIVE
UI.RequestPlayerOperation(CONFIG.PID, PlayerOperations.RESEARCH, params)
print("EXECUTE|RESEARCH|" .. CONFIG.TECH)

local after = pTechs:GetResearchingTech()
local actual = "none"
if after ~= nil and after >= 0 then
    actual = GameInfo.Technologies[after].TechnologyType
end
print("VERIFY_RESEARCHING=" .. actual)

if actual ~= CONFIG.TECH then
    print("FINAL=FAIL|researching_mismatch")
    error("当前研究回读不一致：" .. actual .. " ~= " .. CONFIG.TECH)
end
print("FINAL=OK")
print("=== RESEARCH-SET COMPLETE ===")
