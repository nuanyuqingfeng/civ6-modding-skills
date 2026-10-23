-- leader.lua —— 指定玩家槽位的领袖与文明（MainMenu 上下文，建局前）
-- 用法：python tuner_exec.py act leader --player-id 0 --leader LEADER_CARTETHYIA_QYQXP
--
-- 参数
--   PLAYER_ID  玩家槽位编号（PlayerConfigurations 的索引）
--   LEADER     领袖类型名（GameInfo.Leaders 的 LeaderType）
--   CIV        文明类型名（GameInfo.Civilizations 的 CivilizationType），留空表示不改
--   PREPARE    先跑官方建局准备链，再写领袖
--
-- 前置断言
--   MainMenu 态可达；PlayerConfigurations 为 table 且该槽位存在；
--   LEADER 在 GameInfo.Leaders 内；CIV 为空或在 GameInfo.Civilizations 内
--
-- 执行步骤
--   1. PREPARE 为真时按官方顺序跑七步建局准备（MainMenu.lua:160-175）
--   2. 写入 CIV（非空时）与 LEADER
--   3. 回读 GetLeaderTypeName / GetCivilizationTypeName
--
-- 成功判据
--   VERIFY_ACTUAL_LEADER 与写入值一致；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 必须在 RebuildPlayerParameters 之后写领袖，PREPARE=false 时由调用方自行保证顺序
--   2. 对局内 Players[i]:GetType() 的一致性需在建局后另行核对，本动作只覆盖建局前配置
--   3. DLC 缺失时引擎在 HostGame 阶段拒绝，本动作只校验类型名是否存在

-- ===== CONFIG =====
local CONFIG = {
    PLAYER_ID = 0,
    LEADER = "",
    CIV = "",
    PREPARE = true,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== LEADER START ===")

-- 1. 前置断言
if CONFIG.LEADER == "" then
    print("ASSERTION_FAIL|leader_empty")
    error("必须给出 --leader")
end
if type(PlayerConfigurations) ~= "table" then
    print("ASSERTION_FAIL|playerconfigurations=" .. S(type(PlayerConfigurations)))
    error("PlayerConfigurations 不可用：本态不是前端建局配置态")
end
local pc = PlayerConfigurations[CONFIG.PLAYER_ID]
if pc == nil then
    print("ASSERTION_FAIL|player_config_missing|pid=" .. S(CONFIG.PLAYER_ID))
    error("玩家槽位不存在：" .. S(CONFIG.PLAYER_ID))
end
print("ASSERTION_OK|player_config_exist|pid=" .. S(CONFIG.PLAYER_ID))

local leader_row = nil
for row in GameInfo.Leaders() do
    if row.LeaderType == CONFIG.LEADER then
        leader_row = row
        break
    end
end
if leader_row == nil then
    print("ASSERTION_FAIL|leader_not_in_db|" .. CONFIG.LEADER)
    error("库里没有该领袖类型：" .. CONFIG.LEADER)
end
print("ASSERTION_OK|leader_in_db|" .. CONFIG.LEADER)

-- CIV 留空时按领袖行的 CivilizationCollection 反查，避免只写领袖不写文明
if CONFIG.CIV == "" then
    local collection = leader_row.CivilizationCollection
    local first = nil
    for _, civ in pairs(collection) do
        first = civ.CivilizationType
        break
    end
    if first == nil then
        print("ASSERTION_FAIL|leader_has_no_civ|" .. CONFIG.LEADER)
        error("该领袖没有关联文明，必须显式给出 --civ：" .. CONFIG.LEADER)
    end
    CONFIG.CIV = first
    print("DERIVE_CIV|" .. CONFIG.CIV .. "|from=" .. CONFIG.LEADER)
end

local civ_row = nil
for row in GameInfo.Civilizations() do
    if row.CivilizationType == CONFIG.CIV then
        civ_row = row
        break
    end
end
if civ_row == nil then
    print("ASSERTION_FAIL|civ_not_in_db|" .. CONFIG.CIV)
    error("库里没有该文明类型：" .. CONFIG.CIV)
end
print("ASSERTION_OK|civ_in_db|" .. CONFIG.CIV)

-- 2. 前置建局准备链（官方 PlayNow 顺序，MainMenu.lua:160-175）
if CONFIG.PREPARE then
    GameConfiguration.SetToDefaults()
    print("PREPARE_STEP|defaults=ok")
    GameConfiguration.SetValue("RULESET", nil)
    print("PREPARE_STEP|ruleset_nil=ok")
    BuildHeadlessGameSetup()
    print("PREPARE_STEP|headless=ok")
    RebuildPlayerParameters(true)
    print("PREPARE_STEP|rebuild=ok")
    GameSetup_RefreshParameters()
    print("PREPARE_STEP|refresh=ok")
    ReleasePlayerParameters()
    print("PREPARE_STEP|release=ok")
    HideGameSetup()
    print("PREPARE_STEP|hide=ok")
    pc = PlayerConfigurations[CONFIG.PLAYER_ID]
    if pc == nil then
        print("ASSERTION_FAIL|player_config_missing_after_rebuild|pid=" .. S(CONFIG.PLAYER_ID))
        error("准备链执行后槽位消失：" .. S(CONFIG.PLAYER_ID))
    end
    print("ASSERTION_OK|player_config_after_rebuild|pid=" .. S(CONFIG.PLAYER_ID))
end

-- 3. 写入文明与领袖
if CONFIG.CIV ~= "" then
    pc:SetCivilizationTypeName(CONFIG.CIV)
    print("SET_CIV|" .. CONFIG.CIV)
end
pc:SetLeaderTypeName(CONFIG.LEADER)
print("SET_LEADER|" .. CONFIG.LEADER)

-- 4. 回读验证
local actual_leader = pc:GetLeaderTypeName()
local actual_civ = pc:GetCivilizationTypeName()
print("VERIFY_ACTUAL_LEADER=" .. S(actual_leader))
print("VERIFY_ACTUAL_CIV=" .. S(actual_civ))

if actual_leader ~= CONFIG.LEADER then
    print("FINAL=FAIL|leader_mismatch")
    error("领袖回读不一致：" .. S(actual_leader) .. " ~= " .. CONFIG.LEADER)
end
if CONFIG.CIV ~= "" and actual_civ ~= CONFIG.CIV then
    print("FINAL=FAIL|civ_mismatch")
    error("文明回读不一致：" .. S(actual_civ) .. " ~= " .. CONFIG.CIV)
end

print("FINAL=OK")
print("=== LEADER COMPLETE ===")
