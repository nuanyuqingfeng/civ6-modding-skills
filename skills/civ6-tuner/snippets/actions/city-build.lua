-- city-build.lua —— 把建筑、单位或区域加入城市生产队列（ingame 上下文）
-- 用法：python tuner_exec.py act city-build --building BUILDING_MONUMENT
--       python tuner_exec.py act city-build --unit UNIT_WARRIOR --append
--       python tuner_exec.py act city-build --district DISTRICT_CAMPUS
--
-- 参数
--   CITY       capital 或城市 ID
--   BUILDING   建筑类型名，空表示不排建筑
--   UNIT       单位类型名，空表示不排单位
--   DISTRICT   区域类型名，空表示不排区域（必须同时给 X / Y）
--   X / Y      区域放置地块坐标；--district 时必填
--   APPEND     true 时追加到队尾，false 时替换当前位置
--
-- 前置断言
--   ingame 态可达；CityManager.RequestOperation 与 CityOperationTypes.BUILD 可用；
--   三个类型名中恰好给一个；城市存在；类型名在库内
--
-- 执行步骤
--   1. 定位城市（capital 取 GetCapitalCity，否则按 GetID 匹配）
--   2. 按给谁排谁取该行的 Hash
--   3. 按 ProductionPanel.lua:296-402 的写法发 CityOperationTypes.BUILD 操作
--   4. 回读生产队列当前项（gamecore 侧 CurrentlyBuilding）
--
-- 成功判据
--   VERIFY_QUEUE 等于本次排入的类型名；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 生产进度与队列长度在 tuner 侧不可读，回读只覆盖「当前生产项」一项
--   2. 排队为异步结算，回读在 RETRY 次内轮询
--   3. 前置科技、市政、区域由引擎判定，本动作不做补齐（补齐用 build 或 tech-complete / civic-complete）

-- ===== CONFIG =====
local CONFIG = {
    CITY = "capital",
    BUILDING = "",
    UNIT = "",
    DISTRICT = "",
    X = -1,
    Y = -1,
    APPEND = false,
    RETRY = 20,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== CITY-BUILD START ===")

local given = 0
if CONFIG.BUILDING ~= "" then given = given + 1 end
if CONFIG.UNIT ~= "" then given = given + 1 end
if CONFIG.DISTRICT ~= "" then given = given + 1 end
if given ~= 1 then
    print("ASSERTION_FAIL|need_exactly_one|given=" .. S(given))
    error("--building / --unit / --district 必须且只能给一个")
end

if type(CityManager.RequestOperation) ~= "function" then
    print("ASSERTION_FAIL|requestoperation=" .. S(type(CityManager.RequestOperation)))
    error("城市操作接口不可用：本态不是 ingame")
end
if type(CityOperationTypes) ~= "table" or CityOperationTypes.BUILD == nil then
    print("ASSERTION_FAIL|operation_build=" .. S(type(CityOperationTypes.BUILD)))
    error("CityOperationTypes.BUILD 不可用")
end
print("ASSERTION_OK|city_operation_api")

local pid = Game.GetLocalPlayer()
local pPlayer = Players[pid]
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
print("ASSERTION_OK|city_exist|id=" .. S(city:GetID()))

local hash = nil
local expectName = nil
local paramKey = nil
if CONFIG.BUILDING ~= "" then
    for row in GameInfo.Buildings() do
        if row.BuildingType == CONFIG.BUILDING then
            hash = row.Hash
            break
        end
    end
    expectName, paramKey = CONFIG.BUILDING, CityOperationTypes.PARAM_BUILDING_TYPE
elseif CONFIG.UNIT ~= "" then
    for row in GameInfo.Units() do
        if row.UnitType == CONFIG.UNIT then
            hash = row.Hash
            break
        end
    end
    expectName, paramKey = CONFIG.UNIT, CityOperationTypes.PARAM_UNIT_TYPE
else
    for row in GameInfo.Districts() do
        if row.DistrictType == CONFIG.DISTRICT then
            hash = row.Hash
            break
        end
    end
    expectName, paramKey = CONFIG.DISTRICT, CityOperationTypes.PARAM_DISTRICT_TYPE
end
if hash == nil then
    print("ASSERTION_FAIL|type_not_in_db|" .. expectName)
    error("库里没有该类型：" .. expectName)
end
print("ASSERTION_OK|type_in_db|" .. expectName .. "|hash=" .. S(hash))

local t = {}
t[paramKey] = hash
-- 区域必须带放置坐标：官方 ConfirmPlaceDistrict 一并传 PARAM_X / PARAM_Y
if CONFIG.DISTRICT ~= "" then
    if CONFIG.X < 0 or CONFIG.Y < 0 then
        print("ASSERTION_FAIL|district_needs_plot|--x/--y 未给出")
        error("排区域必须同时给出 --x 与 --y，用于确定放置地块")
    end
    t[CityOperationTypes.PARAM_X] = CONFIG.X
    t[CityOperationTypes.PARAM_Y] = CONFIG.Y
    print("PLOT|" .. CONFIG.X .. "," .. CONFIG.Y)
end
if CONFIG.APPEND then
    t[CityOperationTypes.PARAM_INSERT_MODE] = CityOperationTypes.VALUE_APPEND
else
    -- REPLACE_AT 必须同时给出目标位置，否则引擎不把该项排入队列
    t[CityOperationTypes.PARAM_INSERT_MODE] = CityOperationTypes.VALUE_REPLACE_AT
    t[CityOperationTypes.PARAM_QUEUE_DESTINATION_LOCATION] = 0
end
CityManager.RequestOperation(city, CityOperationTypes.BUILD, t)
print("ENQUEUE_CONSTRUCTION|" .. expectName ..
    "|mode=" .. (CONFIG.APPEND and "APPEND" or "REPLACE_AT"))

-- 回读由 Python 侧另发 gamecore 查询：生产进度方法只在 gamecore 侧存在
local kind = "unit"
if CONFIG.BUILDING ~= "" then kind = "building" end
if CONFIG.DISTRICT ~= "" then kind = "district" end
print("EXPECT_KIND=" .. kind)
print("EXPECT_INDEX=" .. S(hash))
print("EXPECT_QUEUE=" .. expectName)
print("FINAL=OK")
print("=== CITY-BUILD COMPLETE ===")
