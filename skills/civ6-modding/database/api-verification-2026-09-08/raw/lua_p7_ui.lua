local function dumpbase(label, inst)
  local mt=getmetatable(inst)
  if type(mt)~="table" then print("B|"..label.."|nomt") return end
  local bt=mt.BaseType
  print("B|"..label.."|CTypeName="..tostring(mt.CTypeName).."|BaseType="..type(bt))
  if type(bt)=="table" then
    local names={}
    for k,v in pairs(bt) do names[#names+1]=tostring(k)..":"..type(v) end
    table.sort(names)
    print("Y|"..label.."|"..#names.."|"..table.concat(names,","))
    local mt2=getmetatable(bt)
    if type(mt2)=="table" then
      print("B2|"..label.."|BaseType.mt keys:")
      local n2={} for k,v in pairs(mt2) do n2[#n2+1]=tostring(k)..":"..type(v) end
      table.sort(n2) print("Y2|"..label.."|"..table.concat(n2,","))
      if type(mt2.BaseType)=="table" then
        local n3={} for k,v in pairs(mt2.BaseType) do n3[#n3+1]=tostring(k)..":"..type(v) end
        table.sort(n3) print("Y3|"..label.."|"..#n3.."|"..table.concat(n3,","))
      end
    end
  end
end
local ctrl=nil for k,v in pairs(Controls) do if ctrl==nil and type(v)=="table" then ctrl=v end end
dumpbase("Control", ctrl)
dumpbase("ContextPtr", ContextPtr)
print("---END---")
