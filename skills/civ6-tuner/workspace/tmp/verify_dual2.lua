local function S(x) if x == nil then return "nil" end return tostring(x) end
local ok, err = pcall(function()
    local pid = -1
    for _, p in ipairs(PlayerManager.GetAliveMajorIDs()) do
        if PlayerConfigurations[p]:GetLeaderTypeName() == "LEADER_CHANGLI_QYQXP" then pid = p end
    end
    print("changli_pid=" .. tostring(pid))
    -- 双开时长离侧政府广场赠送仍工作（并集闸门命中 HasTraitChangli）
    ChangliAddGovernmentGreatPersonOnDistrictConstructed(pid, GameInfo.Districts["DISTRICT_GOVERNMENT"].Index, 19, 31)
    local key = Players[pid]:GetProperty("GREATPERSON_CHANGLI_GRANTED_" .. pid)
    print("gov_grant_in_dual=" .. S(key))
end)
if not ok then print("ERR_OUT:" .. tostring(err)) end
