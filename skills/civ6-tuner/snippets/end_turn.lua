-- end_turn.lua —— 请求结束当前回合，观察跨回合结算（PROPERTY 结算、modifier 触发等）
-- 上下文：ingame（UI 层操作）
-- 用法：python tuner_exec.py exec --context ingame --file snippets\end_turn.lua
-- 注意：若存在未处理的回合阻塞项（单位未下指令/弹窗），
--       游戏可能弹提示而不真正结束——属正常表现，处理后重发即可。

-- ==== CONFIG ====
local PID = Game.GetLocalPlayer()
-- ================

print("Turn(before)=" .. Game.GetCurrentGameTurn())
UI.RequestPlayerOperation(PID, PlayerOperations.END_TURN, {})
print("END_TURN 已请求 —— 等待 AI 回合后观察画面与日志")
