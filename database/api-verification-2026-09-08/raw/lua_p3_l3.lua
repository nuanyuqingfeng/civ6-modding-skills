__SC = __SC or {}
local function rslv(e)
  local f=loadstring("return ("..e..")")
  if not f then return nil end
  local ok,r=pcall(f)
  if not ok then return nil end
  return r
end
local function cnt(v)
  if type(v)~="table" then return -1 end
  local ok,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>4000 then break end end return k end)
  return ok and c or -2
end
local function ixkeys(o)
  if type(o)~="table" then return nil end
  local mt=getmetatable(o)
  if type(mt)~="table" or type(mt.__index)~="table" then return nil end
  local out={}
  for k,v in pairs(mt.__index) do out[#out+1]=tostring(k)..":"..type(v) end
  table.sort(out)
  return out
end
local function l3(o, getters)
  if type(o)~="table" then return nil,"noobj" end
  local out=nil
  pcall(function()
    if type(o.Members)=="function" then
      for i,v in o:Members() do if out==nil and type(v)=="table" then out=v end end
    end
  end)
  if out then return out,"Members" end
  for gi=1,#getters do
    local g=getters[gi]
    if type(o[g])=="function" then
      local argsets={{},{0},{1},{0,0}}
      for ai=1,#argsets do
        local a=argsets[ai]
        local ok,r=pcall(function()
          if #a==0 then return o[g](o)
          elseif #a==1 then return o[g](o,a[1])
          else return o[g](o,a[1],a[2]) end
        end)
        if ok and type(r)=="table" then return r,"call:"..g.."("..#a..")" end
      end
    end
  end
  return nil,"unresolved"
end
local targets={
  {"C_City_P_GetDistricts",{"GetDistrict","GetDistrictByIndex","GetDistrictByID"}},
  {"C_Player_P_GetGovernors",{"GetGovernor","GetAssignedGovernor","GetGovernorByIndex"}},
  {"C_Player_P_GetCities",{"GetCity","GetCities"}},
  {"C_Game_P_GetGreatPeople",{"GetGreatPerson"}},
  {"C_Unit_P_GetAbility",{"GetAbilities"}},
}
for i=1,#targets do
  local key,getters=targets[i][1],targets[i][2]
  local o=__SC[key]
  local obj,how=l3(o,getters)
  print("L3|"..key.."|"..tostring(o~=nil).."|"..how.."|"..type(obj))
  if obj~=nil then
    __SC[key.."_L3"]=obj
    local ks=ixkeys(obj)
    if ks then print("L3K|"..key.."|"..#ks.."|"..table.concat(ks,","))
    else print("L3K|"..key.."|0|<non-enumerable pairs="..cnt(obj)..">") end
    local mt=getmetatable(obj)
    if type(mt)=="table" then print("L3T|"..key.."|CTypeName="..tostring(mt.CTypeName)) end
  end
end
print("---END---")
