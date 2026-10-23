-- snapshot.lua —— 玩家全量状态快照（gamecore 上下文）
-- 用法：python tuner_exec.py act snapshot
--
-- 参数
--   PID  玩家编号，-1 表示本地玩家
--
-- 前置断言
--   Players[pid] 存在；GetTreasury / GetReligion / GetTechs / GetCulture 为 function
--
-- 执行步骤
--   1. 读回合数、金币、信仰
--   2. 读当前研究科技与推进中的市政（含进度与成本）
--   3. 枚举城市（编号、人口、坐标）
--   4. 枚举单位（编号、类型、坐标、伤害值）
--
-- 成功判据
--   输出 SNAP|unit_count=N 且 FINAL=OK；本动作只读，不做写入校验
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 宜居度三件套（CityGrowth:GetAmenities 等）只在 UI 侧可用，本动作跑在 gamecore，不输出宜居度
--   2. 单位清单以 gamecore 为准，刚被删除的单位不会作为幽灵行出现
--   3. 城市列表不保证顺序稳定（引擎内部遍历顺序）

-- ===== CONFIG =====
local CONFIG = {
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== SNAPSHOT START ===")

if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
local pPlayer = Players[CONFIG.PID]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
    error("玩家不存在：" .. S(CONFIG.PID))
end
print("ASSERTION_OK|player_exist|pid=" .. S(CONFIG.PID))

print("SNAP|turn=" .. S(Game.GetCurrentGameTurn()) .. "|player=" .. S(CONFIG.PID))
print("SNAP|gold=" .. S(pPlayer:GetTreasury():GetGoldBalance()))
print("SNAP|faith=" .. S(pPlayer:GetReligion():GetFaithBalance()))

local pTechs = pPlayer:GetTechs()
local researching = pTechs:GetResearchingTech()
if researching ~= nil and researching >= 0 then
    print("SNAP|researching=" .. GameInfo.Technologies[researching].TechnologyType ..
        "|prog=" .. S(pTechs:GetResearchProgress(researching)) ..
        "/" .. S(pTechs:GetResearchCost(researching)))
else
    print("SNAP|researching=none")
end

local pCulture = pPlayer:GetCulture()
local progressing = pCulture:GetProgressingCivic()
if progressing ~= nil and progressing >= 0 then
    print("SNAP|civic=" .. GameInfo.Civics[progressing].CivicType ..
        "|cost=" .. S(pCulture:GetCultureCost(progressing)) ..
        "|turns_left=" .. S(pCulture:GetTurnsLeftOnCurrentCivic()))
else
    print("SNAP|civic=none")
end

local cityCount = 0
for _, c in pPlayer:GetCities():Members() do
    cityCount = cityCount + 1
    print("SNAP|city|id=" .. S(c:GetID()) .. "|pop=" .. S(c:GetPopulation()) ..
        "|at=" .. S(c:GetX()) .. "," .. S(c:GetY()))
end
print("SNAP|city_count=" .. S(cityCount))

local unitCount = 0
for _, u in pPlayer:GetUnits():Members() do
    unitCount = unitCount + 1
    print("SNAP|unit|id=" .. S(u:GetID()) .. "|" .. GameInfo.Units[u:GetType()].UnitType ..
        "|at=" .. S(u:GetX()) .. "," .. S(u:GetY()) .. "|dmg=" .. S(u:GetDamage()))
end
print("SNAP|unit_count=" .. S(unitCount))

print("FINAL=OK")
print("=== SNAPSHOT COMPLETE ===")
