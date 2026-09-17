__SC = {}
local function rslv(e)
  local f=loadstring("return ("..e..")")
  if not f then return nil end
  local ok,r=pcall(f)
  if not ok then return nil end
  return r
end
local function reg(k,v) if v~=nil then __SC["C_"..k]=v end end
local function firstPlayer()
  local lp=rslv("Game.GetLocalPlayer and Game.GetLocalPlayer()")
  if type(lp)=="number" and rslv("Players["..lp.."]")~=nil then return rslv("Players["..lp.."]") end
  for i=0,63 do local p=rslv("Players["..i.."]") if type(p)=="table" then return p end end
end
local function firstMember(obj,getter)
  local out=nil
  if obj==nil then return nil end
  pcall(function()
    local m=obj[getter]
    if type(m)~="function" then return end
    local c=m(obj)
    if type(c)~="table" then return end
    for i,v in c:Members() do if out==nil then out=v end end
  end)
  return out
end
local pl=firstPlayer()
reg("Player",pl)
local city=firstMember(pl,"GetCities")
reg("City",city)
reg("Unit",firstMember(pl,"GetUnits"))
reg("Plot",rslv("Map.GetPlotByIndex(0)"))
reg("Game",rslv("Game"))
local function sub(inst,parent,key)
  if type(inst)~="table" then return nil end
  local v=nil
  pcall(function() v=inst[parent] end)
  if type(v)=="function" then
    local ok,r=pcall(v,inst)
    if ok and type(r)=="table" then __SC[key]=r return r end
    local ok2,r2=pcall(v)
    if ok2 and type(r2)=="table" then __SC[key]=r2 return r2 end
  elseif type(v)=="table" then __SC[key]=v return v end
  return nil
end
sub(city,"GetDistricts","C_City_P_GetDistricts")
sub(city,"GetBuildings","C_City_P_GetBuildings")
sub(pl,"GetGovernors","C_Player_P_GetGovernors")
sub(pl,"GetCities","C_Player_P_GetCities")
local g=rslv("Game")
sub(g,"GetGreatPeople","C_Game_P_GetGreatPeople")
local u=__SC["C_Unit"]
sub(u,"GetAbility","C_Unit_P_GetAbility")
local n=0 for _ in pairs(__SC) do n=n+1 end
print("P3SETUP|"..n)
print("---END---")
