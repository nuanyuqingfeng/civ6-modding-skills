local mods={"PopupDialog","PopupDialogInGame","InstanceManager","GenerationalInstanceManager","PullDownInstanceManager","MapPinConfiguration","ToolTipHelper","UITree","json","Tools","g_ToolTipGenerators","InputStruct","PlayerVisibility","DirtyComponents","FreeCities","DiplomacyDeal","DiplomacyDealItem","Notification","TunerUtilities","CodeBuddyFuncs","AssetPreview","IconManager","EffectsManager","TTManager","TouchManager","UITutorialManager","Fractal","FeatureGenerator","NaturalWonderGenerator","WorldBuilderResourceGenerator","Territories","Areas","Units","Cities","Calendar","GameSummary"}
for i=1,#mods do
  local n=mods[i]
  local f=loadstring("return "..n)
  local before = (f and select(2,pcall(f)) or nil)
  local bt=type(before)
  local inc="n/a"
  if bt=="nil" and type(include)=="function" then
    local ok,err=pcall(function() include(n) end)
    inc=tostring(ok)
    if ok then
      local f2=loadstring("return "..n)
      local after=(f2 and select(2,pcall(f2)) or nil)
      bt=bt.."=>inc:"..type(after)
    else
      bt=bt.."=>incERR:"..tostring(err):sub(1,60)
    end
  end
  print("MOD|"..n.."|"..bt.."|"..inc)
end
print("---END---")
