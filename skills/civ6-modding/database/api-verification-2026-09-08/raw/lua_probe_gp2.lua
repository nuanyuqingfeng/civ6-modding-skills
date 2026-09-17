local function count(v)
  if type(v)~="table" then return -1 end
  local ok,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>20000 then break end end return k end)
  return ok and c or -2
end
local function dumpix(label, inst)
  if inst==nil then print("M|"..label.."|NOINST") return end
  local mt=getmetatable(inst)
  if type(mt)~="table" then print("M|"..label.."|nomt|"..type(inst).."|pairs="..count(inst)) return end
  local ix=mt.__index
  if type(ix)~="table" then print("M|"..label.."|ix="..type(ix)) return end
  local names={}
  for k,v in pairs(ix) do names[#names+1]=tostring(k)..":"..type(v) end
  table.sort(names)
  print("M|"..label.."|"..#names.."|"..table.concat(names,","))
end
-- city / unit instance acquisition
local p=Players[0]
print("T|p|"..type(p))
local ok,cities=pcall(function() return p:GetCities() end)
print("T|cities|"..tostring(ok).."|"..type(cities))
if ok and cities then
  local okm,m=pcall(function() return cities:Members() end)
  print("T|members|"..tostring(okm).."|"..type(m))
  if okm then
    local n=0
    for a,b in m do n=n+1 if n<=3 then print("T|member|"..tostring(a).."|"..type(b)) end end
    print("T|membercount|"..n)
  end
end
local okg,gc=pcall(function() return Game.GetCities() end)
print("T|Game.GetCities|"..tostring(okg).."|"..type(gc))
if okg and type(gc)=="table" then
  local n=0 local firstc=nil
  local okm2=pcall(function() for i,c in gc:Members() do n=n+1 if firstc==nil then firstc=c end end end)
  print("T|gcMembers|"..tostring(okm2).."|"..n.."|"..type(firstc))
  dumpix("City", firstc)
end
local oku,gu=pcall(function() return Game.GetUnits() end)
print("T|Game.GetUnits|"..tostring(oku).."|"..type(gu))
if oku and type(gu)=="table" then
  local fu=nil local n=0
  pcall(function() for i,u in gu:Members() do n=n+1 if fu==nil then fu=u end end end)
  print("T|uMembers|"..n.."|"..type(fu))
  dumpix("Unit", fu)
end
dumpix("Player", p)
local okp,pl=pcall(function() return Map.GetPlotByIndex(0) end)
dumpix("Plot", okp and pl or nil)
dumpix("Game", Game)
-- protected global member probing behaviour
local ok1,v1=pcall(function() return GameInfo.ThisTableDoesNotExist_zz end)
print("T|GameInfo.bad|"..tostring(ok1).."|"..type(v1))
local ok2,v2=pcall(function() return GameInfo.Units end)
print("T|GameInfo.Units|"..tostring(ok2).."|"..type(v2).."|count="..count(v2))
local ok3,v3=pcall(function() return Locale.ThisDoesNotExist_zz end)
print("T|Locale.bad|"..tostring(ok3).."|"..type(v3))
local ok4,v4=pcall(function() return Events.ThisEventDoesNotExist_zz end)
print("T|Events.bad|"..tostring(ok4).."|"..type(v4))
local ok5,v5=pcall(function() return GameEvents.ThisEventDoesNotExist_zz end)
print("T|GameEvents.bad|"..tostring(ok5).."|"..type(v5))
print("---END---")
