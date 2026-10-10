-- 丹瑾实测探针2（gamecore）：龙须酥授予链诊断
pcall(function()
    local function S(x) if x == nil then return "nil" end return tostring(x) end
    local res = GameInfo.Resources["RESOURCE_LONGXUSU_QYQXP"]
    print("RES=" .. S(res and res.ResourceType or nil) .. " idx=" .. S(res and res.Index or nil)
        .. " class=" .. S(res and res.ResourceClassType or nil) .. " freq=" .. S(res and res.Frequency or nil))

    -- 回读我方授予链参数
    for row in GameInfo.ModifierArguments() do
        if row.ModifierId == "DJ_LONGXUSU_GRANT" then
            print("MYARG|" .. S(row.Name) .. "=" .. S(row.Value))
        end
    end

    -- 回读我方 modifier 行与绑定
    local m = GameInfo.Modifiers["DJ_LONGXUSU_GRANT"]
    if m then
        print("MYMOD|" .. S(m.ModifierType) .. "|sub=" .. S(m.SubjectRequirementSetId) .. "|own=" .. S(m.OwnerRequirementSetId))
    end

    -- 桑给巴尔原版对照
    for row in GameInfo.ModifierArguments() do
        if row.ModifierId == "MINOR_CIV_ZANZIBAR_CINNAMON_RESOURCE_BONUS" then
            print("ZANZIBAR_ARG|" .. S(row.Name) .. "=" .. S(row.Value))
        end
    end

    -- 资源对象成员枚举
    local pRes = Players[0]:GetResources()
    local keys = {}
    for k in pairs(pRes) do keys[#keys + 1] = tostring(k) end
    table.sort(keys)
    print("RES_MEMBERS=" .. table.concat(keys, ","))
end)
