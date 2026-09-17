local v={a=1}
local okc,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>5000 then break end end return k end)
print("L11OK",okc,c)
print("---END---")
