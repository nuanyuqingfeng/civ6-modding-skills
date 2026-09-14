-- ===========================================================================
-- bridge_probe_1_register.lua —— UI→GP 派发可达性验证 · 第 1 步（GP 侧注册接收器）
--
--   用法：python tuner_exec.py exec --context gamecore --file snippets/bridge_probe_1_register.lua
--         → 再跑 bridge_probe_2_dispatch.lua（ingame）→ 最后 bridge_probe_3_read.lua（gamecore）
--
--   目的：确认 UI 侧 UI.RequestPlayerOperation(EXECUTE_SCRIPT) 的 OnStart 名，
--         到底有没有到达「你注册处理器的那个 GP 态」。
--   机制：引擎按 GameEvents.<OnStart名> 派发（见 civ6-modding/gameplay-lua.md）。
--
--   ★ 更稳的变体：直接借项目里【已有的生产接收器】做探针（无需新增任何代码），
--     一次调用即同时证明「引擎派发正常」+「该注册点的态能收到」——
--     只需把 CONFIG.EVENT_NAME 换成它的 OnStart 名、并把落盘层级照它的实现对齐。
--   ⚠ tuner 的 gamecore/ingame 是独立沙箱态，**看不到任何 mod 全局**，
--     所以不能用 type(mod函数名) 判断注册是否生效。
-- ===========================================================================

-- ===== CONFIG =====
local CONFIG = {
    -- OnStart 名 = GP 侧 GameEvents 事件名
    EVENT_NAME  = "PROBE_BridgeDispatch",
    -- 落盘用属性 key
    PROBE_KEY   = "PROPERTY_TUNER_PROBE_BRIDGE",
    -- 落盘层级："Player"（Players[pid]）| "Game"（Game，全 GP 态共享）
    --   ⚠ 与第 3 步读取层级必须一致；Game 与 Player 是两个不同属性空间
    PROBE_LEVEL = "Player",
}

local function writeProbe(playerID, v)
    if CONFIG.PROBE_LEVEL == "Game" then
        Game.SetProperty(CONFIG.PROBE_KEY, v)              -- 点号写法；冒号会多传 self
    else
        local p = Players[playerID or Game.GetLocalPlayer()]
        if p then p:SetProperty(CONFIG.PROBE_KEY, v) end
    end
end

local ok, err = pcall(function()
    if type(GameEvents) ~= "table" then
        print("[STEP1] GameEvents 在本端为 " .. type(GameEvents) .. "（GP 侧应为 table）")
        return
    end
    GameEvents[CONFIG.EVENT_NAME].Add(function(playerID, params)
        writeProbe(playerID, {
            Hit = 1,
            Pid = playerID,
            V = (params and params.V) or -1,
        })
    end)
    -- 先清标记，避免上次残留被误读成本次成功
    writeProbe(Game.GetLocalPlayer(), { Hit = 0 })

    print("[STEP1] 已注册 GameEvents." .. CONFIG.EVENT_NAME .. " 接收器")
    print("[STEP1] 落盘层级=" .. CONFIG.PROBE_LEVEL .. " key=" .. CONFIG.PROBE_KEY)
    print("[STEP1] 下一步: exec --context ingame --file snippets/bridge_probe_2_dispatch.lua")
end)
if not ok then print("[STEP1] ERR " .. tostring(err)) end
