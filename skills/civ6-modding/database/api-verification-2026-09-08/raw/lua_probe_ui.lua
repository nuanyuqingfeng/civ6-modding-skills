local function gexpr(e)
  local f=loadstring("return "..e)
  if not f then return nil end
  local ok,r=pcall(f)
  if not ok then return nil end
  return r
end
local function count(v)
  if type(v)~="table" then return -1 end
  local ok,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>20000 then break end end return k end)
  return ok and c or -2
end
local names={"UI","Controls","ContextPtr","UIManager","UILens","Input","Network","Modding","Options","Steam","GameConfiguration","PlayerConfiguration","UserConfiguration","Notification","NotificationManager","TunerUtilities","CodeBuddyFuncs","InstanceManager","GenerationalInstanceManager","PullDownInstanceManager","IconManager","EffectsManager","PopupDialog","TouchManager","TTManager","ToolTipHelper","DiplomacyManager","DiplomacyDeal","DealManager","AssetPreview","AutoProfiler","FiraxisLive","HallofFame","Matchmaking","MapConfiguration","Search","GameSummary","Locale","Events","LuaEvents","ReportingEvents","UITree","g_ToolTipGenerators","json","serialize","Tools","Game","Players","Map","GameInfo","CityManager","UnitManager","PlayerOperations","UnitOperations","GameCapabilities","MapPinConfiguration","UITutorialManager","PlayerVisibility","PlayerVisibilityManager","CombatManager","WorldView","Territories","SimUnitSystem","Achievements","Benchmark","Path","DB","Calendar","Areas","Units","Cities","Plot","GameEffects","Automation"}
for _,n in ipairs(names) do
  local v=gexpr(n)
  local t=type(v)
  local extra=""
  if t=="table" then
    local mt=getmetatable(v)
    local ixd="n/a"
    if type(mt)=="table" then local ix=mt.__index ixd=type(ix) if type(ix)=="table" then ixd="table("..count(ix)..")" end end
    extra="|pairs="..count(v).."|mt="..type(mt).."|ix="..ixd
  end
  print("U|"..n.."|"..t..extra)
end
print("---END---")
