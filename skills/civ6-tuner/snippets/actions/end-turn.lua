-- end-turn.lua —— 结束回合并报告回合推进起点（ingame 上下文）
-- 用法：python tuner_exec.py act end-turn
--       python tuner_exec.py act end-turn --force --timeout 180
--
-- 参数
--   FORCE       改发 REASON="UserForced"（Shift+Enter 等价，可推过被阻塞的回合）
--   BLOCKCHECK  执行前先读回合阻塞项清单
--   TIMEOUT     由 Python 侧消费：等待回合推进的秒数
--
-- 前置断言
--   ingame 态可达；UI.RequestAction / UI.RequestPlayerOperation 为 function；
--   Game.GetCurrentGameTurn 可读
--
-- 执行步骤
--   1. 读当前回合，输出 TURN_BEFORE
--   2. BLOCKCHECK 为真时读 NotificationManager.GetAllEndTurnBlocking() 的条目数量
--   3. 投递结束回合请求
--   4. 由 Python 侧轮询 gamecore 的 GetCurrentGameTurn 直到推进
--
-- 成功判据
--   Python 侧输出 [OK] 回合推进：X -> Y，退出码 0
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 回合未推进/超时 4 连接断开
--
-- 已知限制
--   1. GetAllEndTurnBlocking() 返回数字 id 数组，反查名称无路，本动作只报数量
--   2. AI 回合处理期间 InGame 查询会强制上下文切换，轮询一律走 gamecore

-- ===== CONFIG =====
local CONFIG = {
    FORCE = false,
    BLOCKCHECK = true,
    TIMEOUT = 120,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== END-TURN START ===")

if type(UI.RequestAction) ~= "function" then
    print("ASSERTION_FAIL|ui_requestaction=" .. S(type(UI.RequestAction)))
    error("结束回合接口不可用：本态不是 ingame")
end
print("ASSERTION_OK|ingame_action_api")

local turn = Game.GetCurrentGameTurn()
print("TURN_BEFORE=" .. S(turn))

if CONFIG.BLOCKCHECK then
    local items = NotificationManager.GetAllEndTurnBlocking()
    local n = 0
    if type(items) == "table" then
        n = #items
    end
    print("BLOCKING_ITEMS_COUNT=" .. S(n))
    for i, item in ipairs(items) do
        print("BLOCKING_ITEM|" .. i .. "|id=" .. S(item) .. "|type=" .. S(type(item)))
    end
end

if CONFIG.FORCE then
    UI.RequestAction(ActionTypes.ACTION_ENDTURN, { REASON = "UserForced" })
    print("EXECUTE|ACTION_ENDTURN|UserForced")
else
    UI.RequestPlayerOperation(Game.GetLocalPlayer(), PlayerOperations.END_TURN, {})
    print("EXECUTE|PlayerOperations.END_TURN")
end

print("FINAL=OK")
print("=== END-TURN COMPLETE ===")
