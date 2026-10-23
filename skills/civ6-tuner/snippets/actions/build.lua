-- build.lua —— 在指定城市建成一座建筑（gamecore 上下文）
-- 用法：python tuner_exec.py act build --building BUILDING_MONUMENT
--       python tuner_exec.py act build --city 65536 --building BUILDING_LIBRARY --force-precost
--
-- 参数
--   CITY           capital 或城市 ID
--   BUILDING       建筑类型名（GameInfo.Buildings 的 BuildingType）
--   FORCE_PRECOST  缺科技或市政前置时逐项补齐
--
-- 前置断言
--   Players[pid] 存在；城市存在或首都存在；BUILDING 在 GameInfo.Buildings 内；
--   GetBuildQueue():CreateBuilding 为 function
--
-- 执行步骤
--   1. 定位城市（capital 取 GetCapitalCity，否则按 GetID 匹配）
--   2. 读建筑行的前置科技与前置市政；FORCE_PRECOST 为真时逐项补齐
--   3. 直接调用 CreateBuilding 建成，进度传 100
--   4. 回读 HasBuilding
--
-- 成功判据
--   VERIFY_BUILDING=true；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 生产进度在 tuner 侧不可观测（GetTurnsLeft 抛 Not Implemented、GetGenericBuildingProgress 为 nil），
--      验证一律走完成式 HasBuilding
--   2. 区域前置（PrereqDistrict）不做补齐，缺区域时由引擎拒绝，本动作按失败报出
--   3. 人口与产能条件不校验

-- ===== CONFIG =====
local CONFIG = {
    CITY = "capital",
    BUILDING = "",
    FORCE_PRECOST = false,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== BUILD START ===")

if CONFIG.BUILDING == "" then
    print("ASSERTION_FAIL|building_empty")
    error("必须给出 --building")
end

local pid = Game.GetLocalPlayer()
local pPlayer = Players[pid]
if pPlayer == nil then
    print("ASSERTION_FAIL|player_missing|pid=" .. S(pid))
    error("本地玩家不存在：" .. S(pid))
end

local city = nil
if CONFIG.CITY == "capital" then
    city = pPlayer:GetCities():GetCapitalCity()
    if city == nil then
        print("ASSERTION_FAIL|no_capital")
        error("当前没有首都（先用 found_city 建城）")
    end
else
    for _, c in pPlayer:GetCities():Members() do
        if c:GetID() == tonumber(CONFIG.CITY) then
            city = c
            break
        end
    end
    if city == nil then
        print("ASSERTION_FAIL|city_not_found|" .. CONFIG.CITY)
        error("找不到城市：" .. CONFIG.CITY)
    end
end
print("ASSERTION_OK|city_exist|id=" .. S(city:GetID()) ..
    "|at=" .. S(city:GetX()) .. "," .. S(city:GetY()))

local buildingRow = nil
for row in GameInfo.Buildings() do
    if row.BuildingType == CONFIG.BUILDING then
        buildingRow = row
        break
    end
end
if buildingRow == nil then
    print("ASSERTION_FAIL|building_not_in_db|" .. CONFIG.BUILDING)
    error("库里没有该建筑：" .. CONFIG.BUILDING)
end
local bIndex = buildingRow.Index
print("ASSERTION_OK|building_in_db|" .. CONFIG.BUILDING .. "|index=" .. S(bIndex))

local pBuildQueue = city:GetBuildQueue()
if type(pBuildQueue.CreateBuilding) ~= "function" then
    print("ASSERTION_FAIL|createbuilding=" .. S(type(pBuildQueue.CreateBuilding)))
    error("建成建筑接口不可用：本态不是 gamecore")
end

local pTechs = pPlayer:GetTechs()
local pCulture = pPlayer:GetCulture()

-- 前置科技
local prereqTech = buildingRow.PrereqTech
if prereqTech ~= nil and prereqTech ~= "" then
    local techIndex = nil
    for row in GameInfo.Technologies() do
        if row.TechnologyType == prereqTech then
            techIndex = row.Index
            break
        end
    end
    if techIndex == nil then
        print("ASSERTION_FAIL|prereq_tech_not_in_db|" .. S(prereqTech))
        error("前置科技不在库里：" .. S(prereqTech))
    end
    local has = pTechs:HasTech(techIndex)
    print("HAS_TECH|" .. prereqTech .. "=" .. S(has))
    if not has then
        if CONFIG.FORCE_PRECOST then
            pTechs:SetResearchProgress(techIndex, pTechs:GetResearchCost(techIndex))
            local after = pTechs:HasTech(techIndex)
            print("FORCE_COMPLETE_TECH|" .. prereqTech .. "=" .. S(after))
            if not after then
                print("FINAL=FAIL|force_tech_failed")
                error("补齐前置科技失败：" .. prereqTech)
            end
        else
            print("FINAL=FAIL|missing_tech|" .. prereqTech)
            error("缺前置科技：" .. prereqTech .. "（可用 --force-precost 补齐）")
        end
    end
end

-- 前置市政
local prereqCivic = buildingRow.PrereqCivic
if prereqCivic ~= nil and prereqCivic ~= "" then
    local civicIndex = nil
    for row in GameInfo.Civics() do
        if row.CivicType == prereqCivic then
            civicIndex = row.Index
            break
        end
    end
    if civicIndex == nil then
        print("ASSERTION_FAIL|prereq_civic_not_in_db|" .. S(prereqCivic))
        error("前置市政不在库里：" .. S(prereqCivic))
    end
    local has = pCulture:HasCivic(civicIndex)
    print("HAS_CIVIC|" .. prereqCivic .. "=" .. S(has))
    if not has then
        if CONFIG.FORCE_PRECOST then
            pCulture:SetCulturalProgress(civicIndex, pCulture:GetCultureCost(civicIndex))
            local after = pCulture:HasCivic(civicIndex)
            print("FORCE_COMPLETE_CIVIC|" .. prereqCivic .. "=" .. S(after))
            if not after then
                print("FINAL=FAIL|force_civic_failed")
                error("补齐前置市政失败：" .. prereqCivic)
            end
        else
            print("FINAL=FAIL|missing_civic|" .. prereqCivic)
            error("缺前置市政：" .. prereqCivic .. "（可用 --force-precost 补齐）")
        end
    end
end

-- 前置区域：不做补齐，缺时直接报出
local prereqDistrict = buildingRow.PrereqDistrict
if prereqDistrict ~= nil and prereqDistrict ~= "" then
    print("PREREQ_DISTRICT|" .. prereqDistrict)
end

local already = city:GetBuildings():HasBuilding(bIndex)
print("BEFORE_HAS_BUILDING=" .. S(already))
if already then
    print("EXECUTE|skipped|already_present")
    print("VERIFY_BUILDING=true")
    print("FINAL=OK")
    print("=== BUILD COMPLETE ===")
else
    print("EXECUTE|CreateBuilding|" .. CONFIG.BUILDING)
    pBuildQueue:CreateBuilding(city, bIndex, 100, city:GetLocation())

    local verify = city:GetBuildings():HasBuilding(bIndex)
    print("VERIFY_BUILDING=" .. S(verify))
    if not verify then
        print("FINAL=FAIL|has_building_false")
        error("建筑未生效：" .. CONFIG.BUILDING)
    end
    print("FINAL=OK")
    print("=== BUILD COMPLETE ===")
end
