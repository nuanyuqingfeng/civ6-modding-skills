-- sql_like_trap.lua —— 实机复核 SQL `LIKE ('%A%' OR '%B%')` 陷阱
-- 上下文：gamecore（只读）
-- 假设：括号内 (`'%a%' OR '%b%'`) 先按字符串→整数强制转换求值为整数 0，
--       于是 `X LIKE (…)` 等价 `X LIKE 0`，**只命中字面量为 '0' 的行**（不是"永不命中"）。

local function dump(label, sql)
    print("--- " .. label)
    local ok, rows = pcall(DB.Query, sql)
    if not ok then
        print("   [DB.Query 报错] " .. tostring(rows))
        return
    end
    if rows == nil then print("   (返回 nil)") return end
    local n = 0
    for _, r in pairs(rows) do
        n = n + 1
        local parts = {}
        for k, v in pairs(r) do parts[#parts + 1] = tostring(k) .. "=" .. tostring(v) end
        table.sort(parts)
        print("   " .. table.concat(parts, "  "))
    end
    if n == 0 then print("   (0 行)") end
end

local function main()
    print("DB.Query = " .. tostring(DB.Query))
    print("")

    print("========== A. 纯字面量语义 ==========")
    dump("A1 括号表达式求值 / 类型",
        "SELECT ('%a%' OR '%b%') AS expr, typeof('%a%' OR '%b%') AS typ")
    dump("A2 错误写法: 'abc' LIKE ('%a%' OR '%b%')",
        "SELECT 'abc' AS s WHERE 'abc' LIKE ('%a%' OR '%b%')")
    dump("A3 错误写法: '0' LIKE ('%a%' OR '%b%')   ← 预测会命中",
        "SELECT '0' AS s WHERE '0' LIKE ('%a%' OR '%b%')")
    dump("A4 正确写法: 'abc' LIKE '%a%' OR 'abc' LIKE '%b%'",
        "SELECT 'abc' AS s WHERE 'abc' LIKE '%a%' OR 'abc' LIKE '%b%'")
    print("")

    print("========== B. 真实运行时库（Types 表） ==========")
    dump("B1 正确写法 计数",
        "SELECT COUNT(*) AS n FROM Types WHERE Type LIKE '%TRAIT%' OR Type LIKE '%POLICY%'")
    dump("B2 错误写法 计数   ← 预测为 0 或极小",
        "SELECT COUNT(*) AS n FROM Types WHERE Type LIKE ('%TRAIT%' OR '%POLICY%')")
    dump("B3 错误写法 命中样本",
        "SELECT Type FROM Types WHERE Type LIKE ('%TRAIT%' OR '%POLICY%') LIMIT 5")
    dump("B4 错误写法是否只命中字面量 '0'",
        "SELECT COUNT(*) AS n FROM Types WHERE Type LIKE ('%TRAIT%' OR '%POLICY%') AND Type = '0'")
    print("")

    print("========== C. 三个关键词一起 OR（工坊常见写法） ==========")
    dump("C1 正确写法",
        "SELECT COUNT(*) AS n FROM Types WHERE Type LIKE '%UNIT%' OR Type LIKE '%BUILDING%' OR Type LIKE '%DISTRICT%'")
    dump("C2 错误写法",
        "SELECT COUNT(*) AS n FROM Types WHERE Type LIKE ('%UNIT%' OR '%BUILDING%' OR '%DISTRICT%')")
end

local ok, err = pcall(main)
print("")
print("pcall ok=" .. tostring(ok) .. "  err=" .. tostring(err))
