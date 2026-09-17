local function count(v)
  if type(v)~="table" then return -1 end
  local ok,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>20000 then break end end return k end)
  return ok and c or -2
end
local function dumpctl(label, inst)
  if inst==nil then print("M|"..label.."|NOINST") return end
  local mt=getmetatable(inst)
  local ix=(type(mt)=="table") and mt.__index or nil
  print("M|"..label.."|type="..type(inst).."|mt="..type(mt).."|ix="..type(ix).."|pairs="..count(inst))
  if type(ix)=="table" then
    local names={}
    for k,v in pairs(ix) do names[#names+1]=tostring(k)..":"..type(v) end
    table.sort(names)
    print("X|"..label.."|"..#names.."|"..table.concat(names,","))
  elseif type(mt)=="table" then
    local names={}
    for k,v in pairs(mt) do names[#names+1]=tostring(k)..":"..type(v) end
    table.sort(names)
    print("T|"..label.."|"..#names.."|"..table.concat(names,","))
  end
end
local ctrlName, ctrl = nil, nil
for k,v in pairs(Controls) do
  if ctrl==nil and type(v)=="table" then ctrlName=k; ctrl=v end
end
print("C|firstControl|"..tostring(ctrlName).."|"..type(ctrl))
dumpctl("Control:"..tostring(ctrlName), ctrl)
dumpctl("ContextPtr", ContextPtr)
dumpctl("UIManager", UIManager)
print("D|include|"..type(include))
print("D|UI.IsUnitSelected|"..(function() local f=loadstring("return UI.IsUnitSelected") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("D|UI.NoSuch_zz|"..(function() local f=loadstring("return UI.NoSuch_zz") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("D|Events.NoSuch_zz|"..(function() local f=loadstring("return Events.NoSuch_zz") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("D|LuaEvents.NoSuch_zz|"..(function() local f=loadstring("return LuaEvents.NoSuch_zz") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("D|UILens.SetLens|"..(function() local f=loadstring("return UILens.SetLens") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("D|Network.HasTurnStarted|"..(function() local f=loadstring("return Network.HasTurnStarted") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("D|NotificationManager.Add|"..(function() local f=loadstring("return NotificationManager.Add") local ok,r=pcall(f) return tostring(ok).."|"..type(r) end)())
print("---END---")
