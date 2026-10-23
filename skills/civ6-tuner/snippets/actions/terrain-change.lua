-- terrain-change.lua —— 改地块地形与地貌（gamecore 上下文）
-- 用法：python tuner_exec.py act terrain-change --x 10 --y 12 --terrain TERRAIN_GRASS
--       python tuner_exec.py act terrain-change --x 10 --y 12 --feature FEATURE_FLOODPLAINS
--
-- 参数
--   X / Y   地块坐标
--   TERRAIN 地形类型名（GameInfo.Terrains 的 TerrainType），留空表示不改
--   FEATURE 地貌类型名（GameInfo.Features 的 FeatureType），留空表示不改
--
-- 前置断言
--   Map.GetPlot(X, Y) 非空；TerrainBuilder.SetTerrainType / SetFeatureType 为 function；
--   非空的 TERRAIN / FEATURE 在库里存在
--
-- 执行步骤
--   1. 读地块当前地形与地貌，输出 BEFORE
--   2. TERRAIN 非空时 SetTerrainType，FEATURE 非空时 SetFeatureType
--   3. 回读地块地形与地貌
--
-- 成功判据
--   VERIFY_TERRAIN / VERIFY_FEATURE 与请求值一致；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 清除地貌的取值约定未实测，本动作只支持写入指定地貌
--   2. 改地形会改变地块的通行性与产出，不做任何合法性回退
--   3. 只有 gamecore 侧可写，UI 侧 TerrainBuilder 不存在

-- ===== CONFIG =====
local CONFIG = {
    X = 0,
    Y = 0,
    TERRAIN = "",
    FEATURE = "",
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

print("=== TERRAIN-CHANGE START ===")

if CONFIG.TERRAIN == "" and CONFIG.FEATURE == "" then
    print("ASSERTION_FAIL|nothing_to_change")
    error("--terrain 与 --feature 至少要给一个")
end

if type(TerrainBuilder.SetTerrainType) ~= "function" then
    print("ASSERTION_FAIL|terrainbuilder=" .. S(type(TerrainBuilder.SetTerrainType)))
    error("地形写入接口不可用：本态不是 gamecore")
end
print("ASSERTION_OK|terrain_builder_api")

local plot = Map.GetPlot(CONFIG.X, CONFIG.Y)
if plot == nil then
    print("ASSERTION_FAIL|plot_missing|" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))
    error("地块不存在：" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))
end
print("ASSERTION_OK|plot_exist|" .. S(CONFIG.X) .. "," .. S(CONFIG.Y))

local terrainIndex = nil
if CONFIG.TERRAIN ~= "" then
    for row in GameInfo.Terrains() do
        if row.TerrainType == CONFIG.TERRAIN then
            terrainIndex = row.Index
            break
        end
    end
    if terrainIndex == nil then
        print("ASSERTION_FAIL|terrain_not_in_db|" .. CONFIG.TERRAIN)
        error("库里没有该地形：" .. CONFIG.TERRAIN)
    end
end

local featureIndex = nil
if CONFIG.FEATURE ~= "" then
    for row in GameInfo.Features() do
        if row.FeatureType == CONFIG.FEATURE then
            featureIndex = row.Index
            break
        end
    end
    if featureIndex == nil then
        print("ASSERTION_FAIL|feature_not_in_db|" .. CONFIG.FEATURE)
        error("库里没有该地貌：" .. CONFIG.FEATURE)
    end
end

-- 地貌取值为 -1 表示无地貌，此时 GameInfo.Features[-1] 为 nil，不能直接取字段
local function featureName(idx)
    if idx < 0 then return "" end
    return GameInfo.Features[idx].FeatureType
end

print("BEFORE_TERRAIN=" .. S(GameInfo.Terrains[plot:GetTerrainType()].TerrainType))
print("BEFORE_FEATURE=" .. S(featureName(plot:GetFeatureType())))

if terrainIndex ~= nil then
    TerrainBuilder.SetTerrainType(plot, terrainIndex)
    print("EXECUTE|SetTerrainType|" .. CONFIG.TERRAIN)
end
if featureIndex ~= nil then
    TerrainBuilder.SetFeatureType(plot, featureIndex)
    print("EXECUTE|SetFeatureType|" .. CONFIG.FEATURE)
end

local actualTerrain = GameInfo.Terrains[plot:GetTerrainType()].TerrainType
local actualFeature = featureName(plot:GetFeatureType())
print("VERIFY_TERRAIN=" .. S(actualTerrain))
print("VERIFY_FEATURE=" .. S(actualFeature))

if terrainIndex ~= nil and actualTerrain ~= CONFIG.TERRAIN then
    print("FINAL=FAIL|terrain_mismatch")
    error("地形回读不一致：" .. S(actualTerrain) .. " ~= " .. CONFIG.TERRAIN)
end
if featureIndex ~= nil and actualFeature ~= CONFIG.FEATURE then
    print("FINAL=FAIL|feature_mismatch")
    error("地貌回读不一致：" .. S(actualFeature) .. " ~= " .. CONFIG.FEATURE)
end

print("FINAL=OK")
print("=== TERRAIN-CHANGE COMPLETE ===")
