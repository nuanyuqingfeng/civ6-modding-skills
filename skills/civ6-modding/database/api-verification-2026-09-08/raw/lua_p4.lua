local function count(v)
  if type(v)~="table" then return -1 end
  local ok,c=pcall(function() local k=0 for _ in pairs(v) do k=k+1 if k>20000 then break end end return k end)
  return ok and c or -2
end
local function keys(v)
  local out={}
  local ok=pcall(function() for k,val in pairs(v) do out[#out+1]=tostring(k)..":"..type(val) end end)
  table.sort(out)
  return (ok and "" or "ERR:")..table.concat(out,",")
end
local function step(label, fn)
  local ok,r=pcall(fn)
  if ok then print("S|"..label.."|"..tostring(r)) else print("S|"..label.."|PCALLERR|"..tostring(r)) end
end
step("Game.keys", function() return keys(Game) end)
step("Cities.keys", function() return keys(Cities) end)
step("Player0.GetCities.type", function() return type(Players[0]:GetCities()) end)
step("Player0.GetCities.keys", function() return keys(Players[0]:GetCities()) end)
step("CityManager.keys", function() return keys(CityManager) end)
step("UnitManager.keys", function() return keys(UnitManager) end)
step("cityCount", function() local n=0 for i,c in Players[0]:GetCities():Members() do n=n+1 end return n end)
step("allCityCount", function() local n=0 for i,p in ipairs(Players) do if p and p:IsAlive() then pcall(function() for j,c in p:GetCities():Members() do n=n+1 end end) end end return n end)
step("firstCityAnyPlayer", function()
  for i,p in ipairs(Players) do
    if type(p)=="table" then
      local ok,cm=pcall(function() return p:GetCities() end)
      if ok and type(cm)=="table" then
        local out=nil
        pcall(function() for j,c in cm:Members() do if out==nil then out=c end end end)
        if out then return "player"..i end
      end
    end
  end
  return "none"
end)
step("Players.keys", function() return keys(Players) end)
step("Players.count", function() return count(Players) end)
print("---END---")
