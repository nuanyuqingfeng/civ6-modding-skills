local function count(v)
  if type(v)~="table" then return -1 end
  local ok,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>20000 then break end end return k end)
  return ok and c or -2
end
local function t(e)
  local f=loadstring("return "..e)
  if not f then return "compilefail" end
  local ok,r=pcall(f)
  if not ok then return "ERR" end
  return type(r)
end
-- provider probes
print("PV|Players|"..t("Players"))
print("PV|Game.GetLocalPlayer|"..t("Game.GetLocalPlayer"))
local lp=nil
pcall(function() lp=Game.GetLocalPlayer() end)
print("PV|localPlayer|"..tostring(lp).."|"..t("Players["..tostring(lp).."]"))
-- first alive player
local found=nil
pcall(function()
  for i=0,63 do
    local p=Players[i]
    if type(p)=="table" then
      local ok,alive=pcall(function() return p:IsAlive() end)
      if ok and alive then found=i end
    end
  end
end)
print("PV|firstAlivePlayer|"..tostring(found))
print("PV|GetNotifications|"..t("Players["..tostring(found or 0).."]:GetNotifications()"))
local nn=0
pcall(function() for i,n in Players[found or 0]:GetNotifications():Members() do nn=nn+1 end end)
print("PV|notificationCount|"..nn)
-- units
local un=0 local up=nil
pcall(function() for i=0,63 do local p=Players[i] if type(p)=="table" then pcall(function() for j,u in p:GetUnits():Members() do un=un+1 if up==nil then up=i end end end) end end end)
print("PV|unitCount|"..un.."|firstUnitPlayer|"..tostring(up))
-- extra globals
for _,n in ipairs{"Units","Territories","Areas","FeatureGenerator","NaturalWonderGenerator","Fractal","WorldBuilderResourceGenerator","DirtyComponentsManager","GameRandomEvents","MapFeatureManager","StartPositioner","AutoplayManager","CombatManager","MapRoutes","GameSummary","Calendar","Path","Search","DB","Achievements","Benchmark","Definitions","Relationship","ResourceBuilder","RouteBuilder","ImprovementBuilder","AreaBuilder","TerrainBuilder","MapConfiguration","NotificationManager","DiplomacyManager","DealManager","Matchmaking","AssetPreview","UILens","Input","Network","Modding","Options","Steam","UserConfiguration","GameClimate","UnitOperations","PlayerOperations","GameCapabilities","ReportingEvents","LuaEvents","serialize","json","Tools","UITree","g_ToolTipGenerators","ContextPtr","Controls","UI","UIManager","InstanceManager","PopupDialog","ToolTipHelper","TunerUtilities","CodeBuddyFuncs","PlayerVisibility","PlayerVisibilityManager","SimUnitSystem","WorldView","TerrainManager","HallofFame","AutoProfiler","FiraxisLive","GameEffects","GlobalParameters","Locale","Map","GameInfo","Cities","CityManager","UnitManager","PlayerManager","Automation","GameConfiguration","PlayerConfiguration","WorldBuilder","RiverManager","include"} do
  local v=nil local f=loadstring("return "..n) if f then local ok,r=pcall(f) if ok then v=r end end
  local extra=""
  if type(v)=="table" then extra="|pairs="..count(v).."|mt="..type(getmetatable(v)) end
  print("GG|"..n.."|"..type(v)..extra)
end
print("---END---")
