-- ===========================================================================
-- bridge_probe_2_dispatch.lua —— UI→GP 派发可达性验证 · 第 2 步（UI 侧发派发）
--
--   用法：python tuner_exec.py exec --context ingame --file snippets/bridge_probe_2_dispatch.lua
--
--   ⚠ 只发一次即可。派发是异步的（下一帧/下一个操作处理点生效），
--     第 3 步之前留一点时间；不要靠"立刻读不到"就判定失败。
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    -- 必须与第 1 步 EVENT_NAME 一致
    EVENT_NAME = "PROBE_BridgeDispatch",
    -- 期望在 GP 侧读回的标记值（须与第 3 步 EXPECT_V 一致）
    PROBE_V    = 42,
}

local function S(v) if v == nil then return "nil" end return tostring(v) end

local ok, err = pcall(function()
    print("[STEP2] UI.RequestPlayerOperation=" .. type(UI.RequestPlayerOperation))
    print("[STEP2] PlayerOperations.EXECUTE_SCRIPT="
        .. S(PlayerOperations and PlayerOperations.EXECUTE_SCRIPT))

    if type(UI.RequestPlayerOperation) ~= "function" then
        print("[STEP2] 本端无 UI.RequestPlayerOperation（应在 ingame 上下文运行）")
        return
    end

    UI.RequestPlayerOperation(Game.GetLocalPlayer(), PlayerOperations.EXECUTE_SCRIPT, {
        OnStart = CONFIG.EVENT_NAME,
        V = CONFIG.PROBE_V,
    })
    print("[STEP2] 已派发 " .. CONFIG.EVENT_NAME .. " (V=" .. S(CONFIG.PROBE_V) .. ")")
    print("[STEP2] 下一步: exec --context gamecore --file snippets/bridge_probe_3_read.lua")
end)
if not ok then print("[STEP2] ERR " .. tostring(err)) end
