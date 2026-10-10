local function ixkeys(o)
  if type(o)~="table" then return nil end
  local mt=getmetatable(o)
  if type(mt)~="table" or type(mt.__index)~="table" then return nil end
  local out={}
  for k,v in pairs(mt.__index) do out[#out+1]=tostring(k)..":"..type(v) end
  table.sort(out)
  return out
end
local function keys(o)
  local out={}
  pcall(function() for k,v in pairs(o) do out[#out+1]=tostring(k)..":"..type(v) end end)
  table.sort(out)
  return out
end
local gp=nil; local how="none"
if type(UI)=="table" and type(UI.GetGameParameters)=="function" then
  local ok,r=pcall(function() return UI.GetGameParameters() end)
  if ok and type(r)=="table" then gp=r how="UI.GetGameParameters()" end
end
print("GP_OBJ|"..how.."|"..type(gp))
if gp then
  local ks=ixkeys(gp) or keys(gp)
  print("GPK|"..#ks.."|"..table.concat(ks,","))
  -- 逐名探测文档所载（带 Get 前缀）与去前缀候选
  local docs={"GetSetValue","GetGetValueAt","GetGetCount","GetGet","GetRemoveAt","GetAppendValue","GetGetKeyAt","GetSetValueAt","GetGetAt","GetGetValue","GetGetValueIndex","GetContainsValue","GetInsertValueAt","GetRemove","GetAdd"}
  for i=1,#docs do
    local dn=docs[i]
    local stripped=dn:sub(4)
    local a=gp[dn]~=nil
    local b=gp[stripped]~=nil
    print("CMP|"..dn.."|orig="..tostring(a).."|stripped="..stripped.."|"..tostring(b).."|"..type(gp[stripped]))
  end
end
print("---END---")
