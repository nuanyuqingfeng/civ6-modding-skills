-- modifier_probe.lua —— 验证 Modifier/RequirementSet 是否已进入运行时数据库并挂载
-- 上下文：gamecore（只读）
-- 用法：改 CONFIG 区三个 ID 后执行：
--   python tuner_exec.py exec --context gamecore --file snippets\modifier_probe.lua

-- ==== CONFIG ====
local MOD_ID = "TRAIT_RGN_WATER_FAITH"        -- 要验证的 ModifierId
local REQSET_ID = nil                         -- 关联 RequirementSetId，无则填 nil
local TRAIT_ID = "TRAIT_RGN_WATER_FAITH"      -- 所属 TraitType（用于查挂载目标），无则填 nil
-- ================

local row = GameInfo.Modifiers[MOD_ID]
if row == nil then
    print("NOT_FOUND: Modifiers['" .. MOD_ID .. "'] 未加载进运行时库")
else
    print("FOUND ModifierId=" .. row.ModifierId)
    print("  ModifierType=" .. tostring(row.ModifierType))
    print("  SubjectRequirementSetId=" .. tostring(row.SubjectRequirementSetId))
    local dyn = GameInfo.DynamicModifiers[row.ModifierType]
    print("  EffectType=" .. tostring(dyn and dyn.EffectType or "<未知ModifierType>"))
end

if REQSET_ID then
    local rs = GameInfo.RequirementSets[REQSET_ID]
    if rs == nil then
        print("NOT_FOUND: RequirementSets['" .. REQSET_ID .. "']")
    else
        print("FOUND RequirementSet=" .. rs.RequirementSetId)
        for _, req in ipairs(GameInfo.RequirementSetRequirements) do
            if req.RequirementSetId == REQSET_ID then
                print("  含条件: " .. tostring(req.RequirementId))
            end
        end
    end
end

if TRAIT_ID and GameInfo.Traits[TRAIT_ID] then
    -- 特性 → 类型挂载链（文明/领袖/城市等谁持有它）
    for _, tcm in ipairs(GameInfo.TraitModifiers) do
        if tcm.ModifierId == MOD_ID then
            local traitRow = GameInfo.Traits[tcm.TraitType]
            print("挂载点: TraitModifiers[" .. tostring(tcm.TraitType) .. "]"
                .. (traitRow and (" (" .. traitRow.TraitType .. ")") or ""))
        end
    end
end
