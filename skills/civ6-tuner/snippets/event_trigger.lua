-- event_trigger.lua —— 在 UI VM 手动触发 LuaEvents，验证 GP→UI 通知链路
-- 上下文：ingame（UI 层；LuaEvents 触发/监听都在这个 VM）
-- 用法：python tuner_exec.py exec --context ingame --file snippets\event_trigger.lua
-- 注意：触发后观察游戏画面是否出现预期反应（弹窗/面板刷新），
--       再用 `exec ... logs` 尾随 Lua.log 确认接收端无脚本报错。

-- ==== CONFIG ====
local EVENT_NAME = "RGNPlayMovies"   -- 要触发的 LuaEvents 名（改这里）
local ARG1 = 1                       -- 第一个参数（按接收端签名调整）
-- ================

-- 动态索引 LuaEvents 表并调用
local handler = LuaEvents[EVENT_NAME]
if handler == nil then
    print("NOT_FOUND: LuaEvents['" .. EVENT_NAME .. "'] 不存在")
else
    -- 监听者数量接口待实测（Count 非文档化 API）：成功则报告，失败则跳过
    local ok, count = pcall(function() return handler:Count() end)
    if ok and type(count) == "number" then
        print("Listeners=" .. tostring(count))
        if count == 0 then
            print("无人监听该事件：检查对应 UI 文件的 include 与 RGNCheckTraitInGame 门控")
        end
    end
    handler(ARG1)
    print("FIRED " .. EVENT_NAME .. "(" .. tostring(ARG1) .. ") —— 请看画面反应")
end
