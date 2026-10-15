local hasJinhsi = GameInfo.Leaders["LEADER_JINHSI_QYQXP"] ~= nil
local hasChangli = GameInfo.Leaders["LEADER_CHANGLI_QYQXP"] ~= nil
print("JINHSI_MOD_IN_DB=" .. tostring(hasJinhsi))
print("CHANGLI_MOD_IN_DB=" .. tostring(hasChangli))
for _, pid in ipairs(PlayerManager.GetAliveMajorIDs()) do
    local p = Players[pid]
    local prop = p:GetProperty("PROPERTY_TRAIT_CIVILIZATION_JINZHOU_QYQXP") or 0
    local cprop = p:GetProperty("PROPERTY_TRAIT_CHANGLI_QYQXP") or 0
    local ccprop = p:GetProperty("PROPERTY_TRAIT_CHANGLI_CHINA_QYQXP") or 0
    local cfg = PlayerConfigurations[pid]
    print("player " .. pid .. " leader=" .. cfg:GetLeaderTypeName() .. " jinzhou=" .. prop .. " changli=" .. cprop .. " changlichina=" .. ccprop)
end
