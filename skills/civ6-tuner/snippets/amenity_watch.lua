-- amenity_watch.lua —— 洛可可二进制宜居度逐回合监测（配合调试版 Core_RGN/Lua_Roccia_RGN）
-- 上下文：ingame（宜居度 UI 侧方法）
-- 用法：python tuner_exec.py exec --context ingame --file snippets\amenity_watch.lua

local BIT_BASE = "PROPERTY_RGN_AMENITY_BIT_";
local WEIGHTS = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 8192 };

local PID = Game.GetLocalPlayer();
local pP = Players[PID];

print("AW|turn=" .. Game.GetCurrentGameTurn());

-- 玩家级欠账（无城时的宜居度暂存）
local pend = nil;
pcall(function() pend = pP:GetProperty("PROPERTY_RGN_AMENITY_PENDING") end);
if type(pend) == "number" then
    print("AW|pending=" .. tostring(pend))
elseif pend == nil then
    print("AW|pending=nil")
else
    print("AW|pending_table_keys=" .. RCCCountTable and tostring(#pend) or "table")
end

-- 剧团地块表与已发放回执表规模
pcall(function()
    local tp = pP:GetProperty("PROPERTY_TROUPE_PLOT_TABLE");
    local n = 0;
    if type(tp) == "table" then for _ in pairs(tp) do n = n + 1 end end
    print("AW|troupe_plots=" .. n);
end);
pcall(function()
    local ach = pP:GetProperty("PROPERTY_RGN_ACHIEVED_TABLE");
    local n = 0;
    if type(ach) == "table" then for _ in pairs(ach) do n = n + 1 end end
    print("AW|achieved_tokens=" .. n);
end);

-- 每城：宜居度三件套 + 城市中心地块的二进制位逐位读取
for _, c in pP:GetCities():Members() do
    local cx, cy = c:GetX(), c:GetY();
    local plot = Map.GetPlot(cx, cy);
    local am, need = -999, -999;
    pcall(function()
        local g = c:GetGrowth();
        am = g:GetAmenities();
        need = g:GetAmenitiesNeeded();
    end);
    local line = "AW|city|id=" .. c:GetID() ..
        "|at=" .. cx .. "," .. cy ..
        "|amenity=" .. tostring(am) ..
        "|need=" .. tostring(need) ..
        "|surplus=" .. tostring(am - need);
    local decSum = 0;
    local setBits = {};
    if plot ~= nil then
        for _, w in ipairs(WEIGHTS) do
            local v = nil;
            pcall(function() v = plot:GetProperty(BIT_BASE .. w) end);
            if v == 1 then
                decSum = decSum + w;
                setBits[#setBits + 1] = tostring(w);
            end
        end
    end
    line = line .. "|bits_dec=" .. decSum .. "|bits=" ..
        (#setBits > 0 and table.concat(setBits, "+") or "-");
    -- 引擎宜居度与已写二进制位的差值：不为 0 即异常信号
    if am ~= -999 then
        line = line .. "|resid=" .. tostring(am - decSum);
    end
    print(line);
end
