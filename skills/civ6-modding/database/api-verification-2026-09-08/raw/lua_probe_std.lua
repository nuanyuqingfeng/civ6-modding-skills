local fns={"pairs","ipairs","type","tostring","tonumber","pcall","xpcall","getmetatable","setmetatable","rawget","rawset","rawequal","select","next","unpack","error","assert","string","table","math","os","io","debug","coroutine","loadstring","load","dofile","require"}
for _,n in ipairs(fns) do print("S|"..n.."|"..type(_G[n])) end
print("VER|"..tostring(_VERSION))
local ok,c=pcall(function() local k=0 for _ in pairs(_G) do k=k+1 end return k end)
print("GLOBALS_COUNT|"..tostring(ok and c or "ERR:"..tostring(c)))
print("---END---")
