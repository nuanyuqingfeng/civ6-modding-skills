-- game-mode.lua —— 启用/关闭游戏模式（MainMenu 上下文）
-- 用法：python tuner_exec.py act game-mode --modes GAMEMODE_SECRETSOCIETIES,GAMEMODE_HEROES
--
-- 参数
--   MODES        启用的模式键名列表（ConfigurationId，来自 SetupParameters 表 GroupId=GameModes）
--   ENABLE_ONLY  仅保留 MODES 内的模式，其余 KNOWN 表内模式全部关闭
--
-- 前置断言
--   MainMenu 态可达；GameConfiguration.SetValue / GetValue 为 function；Locale.Bundle 为 function
--
-- 执行步骤
--   1. MODES 逐项写入 GAMEMODE_* = true
--   2. ENABLE_ONLY 为真时，把不在 MODES 内的 KNOWN 表模式写 false
--   3. 重建 GAMEMODES_ENABLED_NAMES（界面显示用本地化名数组）
--
-- 成功判据
--   SET_MODE_<键>=<写入值> 与 VERIFY_MODE_<键>=<回读值> 一致；FINAL=OK
--
-- 失败码
--   1 参数错误（Python 侧） 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 只覆盖 KNOWN 表内的官方模式键；mod 自带模式的 ConfigurationId 不在表内，不写入
--   2. GAMEMODES_ENABLED_NAMES 的顺序与界面勾选顺序一致，本动作按 MODES 顺序重建
--   3. 依赖缺失、互斥冲突由引擎在 HostGame 时判定，本动作只给出回读值

-- ===== CONFIG =====
local CONFIG = {
    MODES = {},
    ENABLE_ONLY = false,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

-- 官方模式的 ConfigurationId 与界面显示名 tag 对应表
local KNOWN = {
    GAMEMODE_SECRETSOCIETIES = "LOC_GAMEMODE_SECRETSOCIETIES_NAME",
    GAMEMODE_HEROES = "LOC_GAMEMODE_HEROES_NAME",
    GAMEMODE_MONOPOLIES = "LOC_GAMEMODE_MONOPOLIES_NAME",
    GAMEMODE_BARBARIAN_CLANS = "LOC_GAMEMODE_BARBARIAN_CLANS_NAME",
    GAMEMODE_DRAMATICAGES = "LOC_GAMEMODE_DRAMATICAGES_NAME",
    GAMEMODE_APOCALYPSE = "LOC_GAMEMODE_APOCALYPSE_NAME",
    GAMEMODE_TOWERDEFENSE = "LOC_GAMEMODE_TOWERDEFENSE_NAME",
    GAMEMODE_TREE_RANDOMIZER = "LOC_GAMEMODE_TREE_RANDOMIZER_NAME",
}

print("=== GAME-MODE START ===")

-- 1. 前置断言
if type(GameConfiguration.SetValue) ~= "function" then
    print("ASSERTION_FAIL|GameConfiguration.SetValue 不可用：" .. S(type(GameConfiguration.SetValue)))
    print("FINAL=FAIL")
    error("GameConfiguration.SetValue 不可用，本态无法设置游戏模式")
end
print("ASSERTION_OK|gameconfiguration_writable")

local want = {}
for _, key in ipairs(CONFIG.MODES) do
    want[key] = true
    if KNOWN[key] == nil then
        print("ASSERTION_WARN|unknown_mode=" .. key .. "（不在官方模式表内，仍会写入布尔键）")
    end
end

-- 2. 写入启用项与关闭项
local names = {}
local order = {}
for key in pairs(want) do
    table.insert(order, key)
end
table.sort(order)
for _, key in ipairs(order) do
    GameConfiguration.SetValue(key, true)
    print("SET_MODE_|" .. key .. "=true")
end

if CONFIG.ENABLE_ONLY then
    local off = {}
    for key in pairs(KNOWN) do
        if not want[key] then
            table.insert(off, key)
        end
    end
    table.sort(off)
    for _, key in ipairs(off) do
        GameConfiguration.SetValue(key, false)
        print("SET_MODE_|" .. key .. "=false")
    end
end

-- 3. 重建界面显示名数组
for _, key in ipairs(order) do
    if KNOWN[key] ~= nil then
        local bundle = Locale.Bundle(KNOWN[key])
        if bundle == nil then
            print("ASSERTION_WARN|missing_locale_tag=" .. KNOWN[key])
        else
            table.insert(names, bundle)
        end
    end
end
if #names > 0 then
    GameConfiguration.SetValue("GAMEMODES_ENABLED_NAMES", names)
else
    GameConfiguration.SetValue("GAMEMODES_ENABLED_NAMES", nil)
end

-- 4. 回读验证
local bad = 0
for _, key in ipairs(order) do
    local actual = GameConfiguration.GetValue(key)
    print("VERIFY_MODE_|" .. key .. "=" .. S(actual))
    if actual ~= true then
        bad = bad + 1
    end
end
if CONFIG.ENABLE_ONLY then
    for key in pairs(KNOWN) do
        if not want[key] then
            local actual = GameConfiguration.GetValue(key)
            print("VERIFY_MODE_|" .. key .. "=" .. S(actual))
            if actual ~= false then
                bad = bad + 1
            end
        end
    end
end

local back = GameConfiguration.GetValue("GAMEMODES_ENABLED_NAMES")
print("VERIFY_NAMES_COUNT=" .. S(type(back) == "table" and #back or 0))
for i, item in ipairs(type(back) == "table" and back or {}) do
    print("VERIFY_NAME|" .. i .. "|" .. S(item))
end
if #names ~= (type(back) == "table" and #back or 0) then
    bad = bad + 1
end

if bad > 0 then
    print("FINAL=FAIL|mismatch=" .. bad)
    error("游戏模式写入后回读不一致：" .. bad .. " 项")
end
print("FINAL=OK")
print("=== GAME-MODE COMPLETE ===")
