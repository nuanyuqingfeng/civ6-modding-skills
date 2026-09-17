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
  if type(ix)~="table" then print("M|"..label.."|ix="..type(ix).."|pairs="..count(inst)) return end
  local names={}
  for k,v in pairs(ix) do names[#names+1]=tostring(k)..":"..type(v) end
  table.sort(names)
  print("M|"..label.."|"..#names.."|"..table.concat(names,","))
end
local function firstcity()
  local gc=Game.GetCities()
  if type(gc)~="table" then return nil end
  local out=nil
  pcall(function() for i,c in gc:Members() do if out==nil then out=c end end end)
  return out
end
local function firstunit()
  local gu=Game.GetUnits()
  if type(gu)~="table" then return nil end
  local out=nil
  pcall(function() for i,u in gu:Members() do if out==nil then out=u end end end)
  return out
end
print("T|Game.GetCities|"..type(Game.GetCities))
print("T|Game.GetUnits|"..type(Game.GetUnits))
local c=firstcity(); print("T|city|"..type(c))
local u=firstunit(); print("T|unit|"..type(u))
dumpix("City", c)
dumpix("Unit", u)
dumpix("Player", Players[0])
local pl=Map.GetPlotByIndex(0)
dumpix("Plot", pl)
if c then
  local b=c:GetBuildings(); dumpix("CityBuildings", b)
  local cq=c:GetQueue(); dumpix("CityQueue", cq)
end
if u then
  local ab=u:GetAbility(); dumpix("UnitAbility", ab)
end
local ok1,v1=pcall(function() return GameInfo.ThisTableDoesNotExist_zz end)
print("T|GameInfo.bad|"..tostring(ok1).."|"..type(v1))
print("T|GameInfo.Units|"..type(GameInfo.Units).."|count="..count(GameInfo.Units))
local ok3,v3=pcall(function() return Locale.ThisDoesNotExist_zz end)
print("T|Locale.bad|"..tostring(ok3).."|"..type(v3))
local ok4,v4=pcall(function() return Events.ThisEventDoesNotExist_zz end)
print("T|Events.bad|"..tostring(ok4).."|"..type(v4))
local ok5,v5=pcall(function() return GameEvents.ThisEventDoesNotExist_zz end)
print("T|GameEvents.bad|"..tostring(ok5).."|"..type(v5))
print("T|Game.count|"..count(Game))
local gk={} for k,v in pairs(Game) do gk[#gk+1]=tostring(k)..":"..type(v) end table.sort(gk)
print("K|Game|"..table.concat(gk,","))
print("---END---")
