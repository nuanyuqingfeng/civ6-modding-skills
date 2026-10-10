local names={"TunerUtilities","ToolTipHelper","PopupDialog","InstanceManager","SupportFunctions","TechAndCivicUnlockables","TechAndCivicUnlockables_","PopupDialogInGame","GenerationalInstanceManager","PullDownInstanceManager"}
local done={}
for i=1,#names do
  local n=names[i]
  local f=loadstring("return "..n)
  local before=(f and select(2,pcall(f)) or nil)
  -- 仅清理确属辅助模块的（PopupDialogInGame/GenerationalInstanceManager/PullDownInstanceManager 为游戏原生，不动）
  if before~=nil and (n=="TunerUtilities" or n=="ToolTipHelper" or n=="PopupDialog" or n=="InstanceManager" or n=="SupportFunctions" or n=="TechAndCivicUnlockables" or n=="TechAndCivicUnlockables_") then
    local g=loadstring(n.." = nil")
    if g then pcall(g) done[#done+1]=n end
  end
end
-- 复原全局输入处理器为空实现（TunerUtilities 载入时会安装 CapsLock 拾取处理器）
local ih="n/a"
pcall(function() UIManager:SetGlobalInputHandler(function() return false end) ih="reset-noop" end)
print("CLEAN|"..table.concat(done,",").."|inputHandler="..ih)
-- 复核
for i=1,#names do
  local f=loadstring("return "..names[i])
  local v=(f and select(2,pcall(f)) or nil)
  print("POST|"..names[i].."|"..type(v))
end
print("POST|__SC|"..type(__SC))
print("POST|__SCINFO|"..type(__SCINFO))
print("POST|__SCAN_ADDED|"..type(__SCAN_ADDED))
print("---END---")
