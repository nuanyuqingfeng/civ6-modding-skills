-- ===========================================================================
-- bridge_probe_3_read.lua —— UI→GP 派发可达性验证 · 第 3 步（GP 侧读结果 + 清理）
--
--   用法：python tuner_exec.py exec --context gamecore --file snippets/bridge_probe_3_read.lua
--
--   ⚠ 必须在正确的【对象层级】读取，否则得到假阴性：
--     写进 Players[pid] 却去读 Game.GetProperty(同名 key) → nil → 误判"派发失败"。
--   ⚠ 若确认没到：先核对第 1 步注册所在的 GP 态是否为派发目标态；
--     最稳做法是借项目已有的生产接收器（如 RGNSetProperty）复测一次。
--   ⚠ CLEANUP 由本步负责：不要把清理放进第 1 步——`exec --both` 会先跑 GP 再跑 UI，
--     GP 段清理会把后续跨端对照读毁掉，制造假失败。
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    PROBE_KEY   = "PROPERTY_TUNER_PROBE_BRIDGE",
    -- 必须与第 1 步 PROBE_LEVEL 一致
    PROBE_LEVEL = "Player",
    -- 必须与第 2 步 PROBE_V 一致
    EXPECT_V    = 42,
    -- 验证完是否清标记（若后面还要做跨端对照读，先设 false）
    CLEANUP     = true,
}

local function readProbe(playerID)
    if CONFIG.PROBE_LEVEL == "Game" then
        return Game.GetProperty(CONFIG.PROBE_KEY)
    end
    local p = Players[playerID or Game.GetLocalPlayer()]
    if not p then return nil end
    return p:GetProperty(CONFIG.PROBE_KEY)   -- 未设置时返回 0 个值 → 先落局部变量再判类型
end

local function clearProbe(playerID)
    if CONFIG.PROBE_LEVEL == "Game" then
        Game.SetProperty(CONFIG.PROBE_KEY, nil)
    else
        local p = Players[playerID or Game.GetLocalPlayer()]
        if p then p:SetProperty(CONFIG.PROBE_KEY, nil) end
    end
end

local ok, err = pcall(function()
    local got = readProbe()
    print("[STEP3] 层级=" .. CONFIG.PROBE_LEVEL .. " 读回 type=" .. type(got))

    local pass = false
    if type(got) == "table" and got.Hit == 1 then
        print("[STEP3] Hit=1 Pid=" .. tostring(got.Pid) .. " V=" .. tostring(got.V))
        pass = (got.V == CONFIG.EXPECT_V)
    else
        print("[STEP3] 未见命中（Hit 非 1）→ 派发未到达本注册点，或读错了对象层级")
    end
    print("[STEP3] VERDICT(派发可达性) = " .. (pass and "PASS" or "FAIL"))

    if CONFIG.CLEANUP then
        clearProbe()
        print("[STEP3] 已清标记")
    end
end)
if not ok then print("[STEP3] ERR " .. tostring(err)) end
