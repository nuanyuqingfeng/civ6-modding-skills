local function ixkeys(o)
  if type(o)~="table" then return nil end
  local mt=getmetatable(o)
  if type(mt)~="table" or type(mt.__index)~="table" then return nil end
  local out={}
  for k,v in pairs(mt.__index) do out[#out+1]=tostring(k)..":"..type(v) end
  table.sort(out)
  return out
end
local found=nil; local how="none"
-- 路径1：任意玩家 GetGovernors():GetGovernor(i)
for i=0,63 do
  local p=Players[i]
  if type(p)=="table" and found==nil then
    local ok,gov=pcall(function() return p:GetGovernors() end)
    if ok and type(gov)=="table" then
      for j=0,12 do
        local ok2,g=pcall(function() return gov:GetGovernor(j) end)
        if ok2 and type(g)=="table" then found=g; how="player"..i..":GetGovernors():GetGovernor("..j..")" break end
      end
      if found==nil then
        local ok3,lst=pcall(function() return gov:GetGovernorList() end)
        if ok3 and type(lst)=="table" then
          pcall(function() for k,v in pairs(lst) do if found==nil and type(v)=="table" then found=v how="GetGovernorList[]" end end end)
        end
      end
    end
  end
end
-- 路径2：城市 GetAssignedGovernor / GetAllAssignedGovernors
if found==nil then
  for i=0,63 do
    local p=Players[i]
    if type(p)=="table" then
      local okc,cm=pcall(function() return p:GetCities() end)
      if okc and type(cm)=="table" then
        pcall(function()
          for cid,c in cm:Members() do
            if found==nil then
              local okg,g=pcall(function() return c:GetAssignedGovernor() end)
              if okg and type(g)=="table" then found=g how="city:GetAssignedGovernor()" end
            end
          end
        end)
      end
    end
    if found~=nil then break end
  end
end
print("GOV|"..how.."|"..type(found))
if found~=nil then
  local ks=ixkeys(found)
  if ks then print("L3K|C_Player_P_GetGovernors|"..#ks.."|"..table.concat(ks,","))
  else print("L3K|C_Player_P_GetGovernors|0|<non-enumerable>") end
end
print("---END---")
