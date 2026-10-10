local function tname(v) local t=type(v); if t~="table" then return t end
  local mt=getmetatable(v); if mt==nil then return "table" end
  local ix=rawget(mt,"__index"); return "table(mt __index="..type(ix)..")"
end
local names={"Game","GameInfo","Map","Players","Cities","GameConfiguration","PlayerConfiguration","UserConfiguration","GameEffects","GameClimate","Locale","Modding","Network","UI","CityManager","UnitManager","WorldBuilder","TerrainBuilder","RiverManager","PlayerManager","Automation","Notification","Options","Steam","Input","UILens","UIManager","TunerUtilities","CodeBuddyFuncs","CodeBuddyFuncsRaw","math","Events","GameEvents","LuaEvents","ReportingEvents","ContextPtr","Controls","exposed"}
for _,n in ipairs(names) do
  local ok,v=pcall(function() return _G[n] end)
  if ok and v~=nil then
    local nkeys=-1
    local ok2,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 end return k end)
    if ok2 then nkeys=c end
    print(string.format("G|%s|%s|keys=%d",n,tname(v),nkeys))
  else
    print(string.format("G|%s|nil|keys=0",n))
  end
end
local p=Players[0]
print("P|Players[0]|"..tname(p))
if p then
  local mt=getmetatable(p)
  print("P|mt|"..type(mt))
  if type(mt)=="table" then for k,v in pairs(mt) do print("P|mtkey|"..tostring(k).."|"..type(v)) end end
end
print("---END---")
