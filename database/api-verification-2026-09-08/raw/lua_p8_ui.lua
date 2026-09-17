local ct={}
for k,v in pairs(Controls) do
  local tn="?"
  if type(v)=="table" then
    local mt=getmetatable(v)
    if type(mt)=="table" then tn=tostring(mt.CTypeName) end
  else tn=type(v) end
  ct[#ct+1]=k.."="..tn
end
table.sort(ct)
print("CT|"..#ct.."|"..table.concat(ct,","))
print("---END---")
