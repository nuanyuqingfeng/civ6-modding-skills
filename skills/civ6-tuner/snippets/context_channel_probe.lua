-- 跨上下文实测探针（2026-09-26）：在 FireTuner 里对两个 Lua 上下文各投递一次，验证通道可达性。
-- 口径真源：civ6-modding/reference/context-matrix.md 第五节。
--
-- 用法（结果见真源第五节 F1–F12）：
--   1) 在接收方上下文跑 "--mode register"   → 注册 LuaEvents 接收器
--   2) 在触发方上下文跑 "--mode fire"       → 触发并按回写值判定是否同端
--   3) 在接收方上下文跑 "--mode check"      → 读计数器
--   4) 在接收方上下文跑 "--mode unregister" → 注销
-- 把 --mode 换成对应值即可；默认 register。

local mode = "register"

local function report(msg)
    print(msg)
    print("---END---")
end

if mode == "register" then
    __RGNCTX_SEEN = 0
    __RGNCTX_HANDLER = function(t)
        __RGNCTX_SEEN = __RGNCTX_SEEN + 1
        if type(t) == "table" then t.written_by_receiver = true end
    end
    LuaEvents.__RGNCTXPROBE.Add(__RGNCTX_HANDLER)
    report("registered LuaEvents.__RGNCTXPROBE in this context")
elseif mode == "fire" then
    local t = { from = "self" }
    LuaEvents.__RGNCTXPROBE(t)
    report("fired; t.written_by_receiver=" .. tostring(t.written_by_receiver)
           .. "（true = 接收器在同一端；nil = 跨端不达）")
elseif mode == "check" then
    report("seen=" .. tostring(__RGNCTX_SEEN))
elseif mode == "unregister" then
    if __RGNCTX_HANDLER then LuaEvents.__RGNCTXPROBE.Remove(__RGNCTX_HANDLER) end
    report("unregistered")
else
    report("未知 mode: " .. tostring(mode))
end
