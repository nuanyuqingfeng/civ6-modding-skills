-- tech-complete.lua —— 完成一项科技（gamecore 上下文）
-- 用法：python tuner_exec.py act tech-complete --tech TECH_BRONZE_WORKING
--
-- 参数
--   TECH  科技类型名（GameInfo.Technologies 的 TechnologyType）
--   PID   玩家编号，-1 表示本地玩家
--
-- 前置断言
--   Players[pid] 存在；TECH 在 GameInfo.Technologies 内；GetTechs() 的
--   SetResearchProgress / HasTech 为 function
--
-- 执行步骤
--   1. 读 HasTech 当前值
--   2. 已有时直接给出 ALREADY=true，不重复写入
--   3. 未有时 SetResearchProgress(科技索引, 科学成本) 一次做满
--   4. 回读 HasTech 与 GetResearchProgress
--
-- 成功判据
--   VERIFY_HAS_TECH=true；FINAL=OK
--
-- 失败码
--   1 参数错误 2 Lua 报错 3 超时 4 连接断开
--
-- 已知限制
--   1. 尤里卡（Boost）不随之记为已触发，且本动作不改 Boost 状态
--   2. 走 SetResearchProgress 会连带把该科技设为已完成，研究队列里的原目标被顶掉
--   3. 只有 gamecore 侧可写，UI 侧只有 HasTech 查询

-- ===== CONFIG =====
local CONFIG = {
    TECH = "",
    PID = -1,
}
-- ===================

local function S(v) if v == nil then return "nil" end return tostring(v) end

local function main()
    print("=== TECH-COMPLETE START ===")

    if CONFIG.TECH == "" then
        print("ASSERTION_FAIL|tech_empty")
        error("必须给出 --tech")
    end
    if CONFIG.PID < 0 then CONFIG.PID = Game.GetLocalPlayer() end
    local pPlayer = Players[CONFIG.PID]
    if pPlayer == nil then
        print("ASSERTION_FAIL|player_missing|pid=" .. S(CONFIG.PID))
        error("玩家不存在：" .. S(CONFIG.PID))
    end

    local index = nil
    for row in GameInfo.Technologies() do
        if row.TechnologyType == CONFIG.TECH then
            index = row.Index
            break
        end
    end
    if index == nil then
        print("ASSERTION_FAIL|tech_not_in_db|" .. CONFIG.TECH)
        error("库里没有该科技：" .. CONFIG.TECH)
    end
    print("ASSERTION_OK|tech_in_db|" .. CONFIG.TECH .. "|index=" .. S(index))

    local pTechs = pPlayer:GetTechs()
    if type(pTechs.SetResearchProgress) ~= "function" then
        print("ASSERTION_FAIL|techs_unwritable=" .. S(type(pTechs.SetResearchProgress)))
        error("科技写入接口不可用：本态不是 gamecore")
    end

    local already = pTechs:HasTech(index)
    print("BEFORE_HAS_TECH=" .. S(already))
    if already then
        print("EXECUTE|skipped|already_completed")
        print("VERIFY_HAS_TECH=true")
        print("FINAL=OK")
        print("=== TECH-COMPLETE COMPLETE ===")
        return
    end

    local cost = pTechs:GetResearchCost(index)
    print("COST=" .. S(cost))
    pTechs:SetResearchProgress(index, cost)
    print("EXECUTE|SetResearchProgress|" .. S(cost))

    local after = pTechs:HasTech(index)
    local progress = pTechs:GetResearchProgress(index)
    print("VERIFY_HAS_TECH=" .. S(after))
    print("VERIFY_PROGRESS=" .. S(progress))

    if not after then
        print("FINAL=FAIL|has_tech_false")
        error("科技未标记为已完成：" .. CONFIG.TECH)
    end
    print("FINAL=OK")
    print("=== TECH-COMPLETE COMPLETE ===")
end

main()
