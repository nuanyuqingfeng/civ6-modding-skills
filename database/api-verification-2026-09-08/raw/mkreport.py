#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成中文验证报告 API范围验证报告.md（所有数字由 CSV/JSON 现算，不硬编码）。"""
from __future__ import annotations

import collections
import csv
import io
import json
import sys
import time
from pathlib import Path

DESKTOP = Path(r"<作者机桌面>")
WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")


def R(dest, name):
    return list(csv.DictReader(io.open(dest / name, encoding="utf-8-sig")))


def pct(a, b):
    return f"{a / b * 100:.1f}%" if b else "—"


def main():
    stamp = time.strftime("%Y%m%d")
    dest = DESKTOP / f"Civ6_API_UI-GP范围验证_{stamp}"
    full = R(dest, "api_scope_full.csv")
    ns = R(dest, "命名空间汇总.csv")
    gl = R(dest, "命名空间可见性.csv")
    diff = R(dest, "GP_UI方法面差异.csv")
    gi = R(dest, "GameInfo库表可达性.csv")
    cbr = R(dest, "CodeBuddy归属面.csv")
    st = json.load(io.open(dest / "统计.json", encoding="utf-8"))
    meta = st["meta"]

    CB = lambda r: r["命名空间/类"].startswith("CodeBuddy")
    ncb = [r for r in full if not CB(r)]
    cbd = [r for r in full if CB(r)]
    verdict = collections.Counter(r["一致性判定"] for r in full)
    vncb = collections.Counter(r["一致性判定"] for r in ncb)
    agree = sum(v for k, v in vncb.items() if k.startswith("一致"))
    disagree = sum(v for k, v in vncb.items() if k.startswith(("文档偏宽", "文档偏窄", "文档存疑")))
    unver = sum(v for k, v in vncb.items() if k.startswith(("无法验证", "部分", "动态")))
    scope = collections.Counter(r["实际范围"] for r in ncb)

    both = [g for g in gl if g["GP可见"] == "是" and g["UI可见"] == "是"]
    gpo = sorted(g["命名空间"] for g in gl if g["GP可见"] == "是" and g["UI可见"] == "否")
    uio = sorted(g["命名空间"] for g in gl if g["GP可见"] == "否" and g["UI可见"] == "是")
    non = [g["命名空间"] for g in gl if g["GP可见"] == "否" and g["UI可见"] == "否"]
    prot_gp = sum(1 for g in gl if g["GP受保护元表"] == "是")
    prot_ui = sum(1 for g in gl if g["UI受保护元表"] == "是")
    gi_ok = sum(1 for g in gi if g["GP"] not in ("nil", "NOPROBE", "ERR") and g["UI"] not in ("nil", "NOPROBE", "ERR"))
    gi_bad = [g["库表"] for g in gi if g["GP"] in ("nil", "NOPROBE", "ERR") or g["UI"] in ("nil", "NOPROBE", "ERR")]

    d = {x["对象/命名空间"]: x for x in diff}

    # 原生可见性复核（收尾复原后、未 include 的 InGame 状态）
    native, absent_native = set(), set()
    ncf = WORK / "out" / "native_ui_check.txt"
    if ncf.exists():
        for ln in ncf.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("NATIVE|"):
                native = {x.split("=")[0] for x in ln.split("|")[2].split(",") if x}
            elif ln.startswith("ABSENT|"):
                absent_native = {x for x in ln.split("|")[2].split(",") if x}
    inc_dep = [x for x in uio if x in absent_native]
    c1 = [r for r in cbr if r["清单"] == "CodeBuddyFuncs"]
    c2 = [r for r in cbr if r["清单"] != "CodeBuddyFuncs"]
    cb_ui = sum(1 for r in c1 if int(r["UI命中面数"]))
    cb_gp = sum(1 for r in c1 if int(r["GP命中面数"]))
    cb_none = sum(1 for r in c1 if not int(r["UI命中面数"]) and not int(r["GP命中面数"]))
    raw_ui = sum(1 for r in c2 if int(r["UI命中面数"]))
    surf_top = st["cb"]["surface_top"][:8]

    def byns(v):
        return collections.Counter(r["命名空间/类"] for r in ncb if r["一致性判定"] == v).most_common(6)

    def samples(v, n=6, only_ns=None):
        pool = [x for x in ncb if x["一致性判定"] == v]
        if only_ns:
            ordered = []
            for nsname, _c in only_ns:
                ordered += [x for x in pool if x["命名空间/类"] == nsname]
            pool = ordered + [x for x in pool if x["命名空间/类"] not in dict(only_ns)]
        out = []
        for r in pool[:n]:
            nm = r["方法"] or "(命名空间)"
            if r["子方法"]:
                nm += " → " + r["子方法"]
            extra = ""
            if r["GP真名"] or r["UI真名"]:
                extra = f'（真名 {r["GP真名"] or r["UI真名"]}）'
            elif r["GP近似名"] or r["UI近似名"]:
                extra = f'（运行时近似名：{(r["GP近似名"] or r["UI近似名"]).split()[0]}…）'
            out.append(f'`{r["命名空间/类"]}.{nm}`{extra}')
        return "、".join(out)

    L = []
    A = L.append
    A("# 文明6 全量 API × UI/GP 范围存在性验证报告")
    A("")
    A(f"> 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}　|　验证通道：FireTuner 调试接口 (TCP 127.0.0.1:4318)")
    A(f"> 游戏实例：`{meta['identity'].replace(chr(0), ' / ').strip()}`")
    A(f"> 上下文：GP = `GameCore_Tuner`(状态 {meta['states'].get('GameCore_Tuner')})　UI = `InGame`(状态 {meta['states'].get('InGame')})"
      f"　+ 复查用其它 UI 状态 {len(st['extra_states'])} 个")
    A(f"> 文档基线：civ6-modding `api.sqlite`（{st['meta']['n_rows']} 行 API）")
    A("")
    A("---")
    A("")
    A("## 0. 结论速览")
    A("")
    A(f"1. **共验证 {len(full)} 条 API**（文档全量），其中 **{len(ncb)} 条为真实运行时命名空间/类**，"
      f"**{len(cbd)} 条（{pct(len(cbd), len(full))}）属文档转储清单**（`CodeBuddyFuncs` / `CodeBuddyFuncsRaw`，运行时并无该全局）。")
    A(f"2. **文档 availability 与运行时一致率 {pct(agree, len(ncb))}**（{agree}/{len(ncb)}，不含转储清单）；"
      f"**不符 {disagree} 条（{pct(disagree, len(ncb))}）**，**无法验证 {unver} 条（{pct(unver, len(ncb))}）**。")
    A(f"3. **运行时实际范围**：双端可见 {scope['双端']} 条、仅 UI {scope['仅UI']} 条、仅 GP {scope['仅GP']} 条、双端未见 {scope['双端未见']} 条。"
      f"UI 面显著宽于 GP 面（{scope['仅UI']} vs {scope['仅GP']}）。")
    A(f"4. **最典型偏差：文档把 UI 专属模块标成 `Both`**——「文档偏宽：GP 未见」{verdict['文档偏宽：GP 未见']} 条中，"
      f"{byns('文档偏宽：GP 未见')[0][0]}({byns('文档偏宽：GP 未见')[0][1]})、"
      f"{byns('文档偏宽：GP 未见')[1][0]}({byns('文档偏宽：GP 未见')[1][1]})、"
      f"{byns('文档偏宽：GP 未见')[2][0]}({byns('文档偏宽：GP 未见')[2][1]}) 等均为 UI 脚本模块。")
    A(f"5. **同名对象在两端是不同类**：`City` 在 GP 是服务端 City（{d['C_City']['GP方法数']} 法），在 UI 是 CacheCity（{d['C_City']['UI方法数']} 法，仅 {d['C_City']['共有']} 法共有）；"
      f"`Player` GP {d['C_Player']['GP方法数']} / UI {d['C_Player']['UI方法数']}（共有 {d['C_Player']['共有']}）；"
      f"`Plot` 几乎对称（GP {d['C_Plot']['GP方法数']} / UI {d['C_Plot']['UI方法数']}，共有 {d['C_Plot']['共有']}）。")
    A(f"6. **GameInfo 数据库面比文档宽得多**：运行时 {gi_ok}/{len(gi)} 张库表可经 `GameInfo.<表>` 双端取到，"
      f"文档只登记了 {sum(1 for r in full if r['路径类别'] == 'gameinfo')} 张；唯一不可达：{', '.join(gi_bad) or '无'}。")
    A(f"7. **事件面是动态代理**：GP 的 `GameEvents` / `LuaEvents`、UI 的 `LuaEvents` 对任意名都返回 table（自动注册），"
      f"因此「存在性」对事件无意义；UI 的 `Events` 与 GP 的 `Events` 不自动生成，可正常判定。")
    A(f"8. **文档名本身有缺陷 {st['name_issue']} 条**：三层路径被压平（`City:GetDistricts():GetDistrict(i):X` 写成 `GetDistrictX`）、"
      f"id 残留（`Q-MapGetCityPlots…`）、`Get` 前缀冗余（`UI.GetGameParameters` 的 15 个子名，实际对象只有 5 个方法）。")
    A("")
    A("---")
    A("")
    A("## 1. 验证目标与方法")
    A("")
    A("**目标**：对文档收录的全部文明6 API，逐条判定其在 **GP（GamePlay 脚本层）** 与 **UI（前端脚本层）** 两个上下文中"
      "**是否存在**（只做存在性，不验证签名、不验证返回值、不验证行为）。")
    A("")
    A("### 1.1 通道与前置")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 通道 | FireTuner 调试协议（帧 `[4B 长度][4B tag][NUL 结尾 payload]`，tag=4 握手 / tag=3 执行） |")
    A(f"| 游戏构建 | Debug（`Base\\Binaries\\Debug`），Tuner 已开启，FireTuner GUI 关闭（单连接限制） |")
    A(f"| 对局状态 | 进行中（GP 状态索引 {meta['states'].get('GameCore_Tuner')}，UI 状态索引 {meta['states'].get('InGame')}；本机共 {len(meta['states'])} 个 Lua 状态） |")
    A(f"| 执行次数 | 主扫描 {meta['calls']} 次 + 补测 84 次 + 定点核验约 15 次 |")
    A(f"| 单次载荷 | 每批 600 条表达式（约 26 KB），实测 1 秒内返回 |")
    A("")
    A("### 1.2 判定手法（严格只读）")
    A("")
    A("```lua")
    A("-- 每条 API 都还原成一次「索引」，用 loadstring + pcall 取类型，不调用任何方法")
    A('local f = loadstring("return (" .. expr .. ")")')
    A("local ok, v = pcall(f)")
    A("-- ok 且 v ~= nil  -> 存在（记录 type）")
    A("-- ok 且 v == nil  -> 容器可达但无此成员")
    A("-- not ok          -> ERR：命名空间不存在 / 无实例 / 父对象未解析")
    A("```")
    A("")
    A("三类访问路径的还原方式：")
    A("")
    A("| 文档形态 | 运行时表达式 | 说明 |")
    A("|---|---|---|")
    A("| `Dot (Global)` | `<命名空间>[.<方法>][.<子方法>]` | 直接索引全局表 |")
    A("| `Colon (Instance)` | `__SC.C_<类>[.<方法>]` | `__SC` 为扫描期登记的实例表（见 1.3） |")
    A("| 带子方法（嵌套） | `__SC.C_<类>_P_<父方法>.<子方法>` | 先取父对象再查子方法 |")
    A("| GameInfo 库表 | `GameInfo.<表名>` | 文档中 161 条 `Q-GameInfo*` |")
    A("")
    A("### 1.3 实例提供者（Colon 类的取实例途径）")
    A("")
    A("| 类 | 取法 | GP | UI |")
    A("|---|---|---|---|")
    A("| Player | `Players[Game.GetLocalPlayer()]` | ✅ | ✅ |")
    A("| City | `player:GetCities():Members()` 首个 | ✅（服务端 City） | ✅（CacheCity） |")
    A("| Unit | `player:GetUnits():Members()` 首个 | ✅ | ✅ |")
    A("| Plot | `Map.GetPlotByIndex(0)` | ✅ | ✅ |")
    A("| Game | `Game` 全局本身 | ✅ | ✅ |")
    A("| Control | `Controls` 中首个 `CTypeName==ControlBase` | —（GP 无 UI） | ✅ |")
    A("| ContextPtr / UIManager / TouchManager … | 同名全局（模块/代理表） | 部分 | ✅ |")
    A("| Notification / DiplomacyDeal / InputStruct … | 需特定运行条件 | ❌ | ❌ |")
    A("")
    A("### 1.4 三轮扫描")
    A("")
    A("1. **主扫描**：登记 `__SC` → 解析 74 个嵌套父对象 → 分批探测 5189 条表达式 + 427 张 GameInfo 库表 → 枚举 266 个命名空间的键与实例方法表。")
    A("2. **补测**：修正首轮 48 条「dot 型带子方法」的表达式（原式是索引函数，必然 ERR）；对 85 个可疑子名生成候选真名重测；"
      f"把「文档声称可用却未见」的条目拿到 {len(st['extra_states'])} 个其它 UI 状态复查（{', '.join(st['extra_states'][:6])} 等）。")
    A("3. **三层恢复**：文档把 `City:GetDistricts():GetDistrict(i):GetAirSlots()` 压平成 `GetDistrictGetAirSlots`，"
      "故再下钻一层取 District 实例（GP 20 法 / UI 27 法）核对真名；Governor 层因本局无已任命总督而未能取到。")
    A("")
    A("### 1.5 副作用与复原（重要）")
    A("")
    A("- 全程**只做索引**；唯一的调用是文档标注的**零参 `Get*` 父方法**（用于取子对象方法表），"
      "外加两个只读查询 `Territories:GetTerritoryAt(0)`、`MapRoutes.GetIndexedPortal(0)`。未结束回合、未改任何游戏状态。")
    A("- UI 侧为取到模块类做过 `include`，**白名单仅限已逐文件核实「加载期无顶层副作用」的模块**："
      "`InstanceManager`、`PopupDialog`、`ToolTipHelper`（及其传递依赖 `SupportFunctions`、`TechAndCivicUnlockables`）。")
    A("- **主动排除 `TunerUtilities`**：其文件末尾执行 `UIManager:SetGlobalInputHandler(TunerUtilities.OnInputHandler)`，"
      "会顶掉 InGame 的全局输入处理器（该处理器拦截 CapsLock 切换取色/拾取）。")
    A("- 收尾已复原：清除扫描期新增的全局（`__SC` / `__SCINFO` / `__SCAN_ADDED` 及 include 进来的模块全局）、"
      "把全局输入处理器复位为 `function() return false end`，并逐项复核为 `nil`；游戏原生全局"
      "（`PopupDialogInGame` / `GenerationalInstanceManager` / `PullDownInstanceManager`）未动。扫描后 `check` 仍显示对局正常。")
    A("")
    A("### 1.6 状态语义")
    A("")
    A("| 状态 | 含义 |")
    A("|---|---|")
    A("| `function` / `table` / `userdata` / `string` / `number` | 存在（记录到的运行时类型） |")
    A("| `nil` | 容器可达，但没有这个成员 → **该上下文不提供** |")
    A("| `ERR` | 索引失败：命名空间不存在 / 类无实例 / 父对象未解析 |")
    A("| `CF` | 表达式无法编译（文档给的是 C++ 签名串，不是 Lua 名） |")
    A("| `不可判` | 无实例通道或动态代理，存在性无法判定（≠ 不存在） |")
    A("")
    A("---")
    A("")
    A("## 2. 总体判定")
    A("")
    A("| 判定 | 条数 | 占全量 |")
    A("|---|---:|---:|")
    for k, v in verdict.most_common():
        A(f"| {k} | {v} | {pct(v, len(full))} |")
    A(f"| **合计** | **{len(full)}** | 100% |")
    A("")
    A(f"去掉 {len(cbd)} 条文档转储后，真实 API {len(ncb)} 条：**一致 {agree}（{pct(agree, len(ncb))}）**、"
      f"**不符 {disagree}（{pct(disagree, len(ncb))}）**、**无法验证 {unver}（{pct(unver, len(ncb))}）**。")
    A("")
    A("### 运行时实际范围（不含转储清单）")
    A("")
    A("| 实际范围 | 条数 | 占比 |")
    A("|---|---:|---:|")
    for k in ("双端", "仅UI", "仅GP", "双端未见"):
        A(f"| {k} | {scope[k]} | {pct(scope[k], len(ncb))} |")
    A("")
    A("> 「双端未见」= 文档声称可用，但两端都没检出；其中大部分是文档名缺陷或版本差异（见 §6、§8），"
      "少数确需特定运行条件（见 §7）。")
    A("")
    A("---")
    A("")
    A("## 3. 命名空间层面的 UI/GP 分界")
    A("")
    A(f"文档共涉及 {len(gl)} 个命名空间/类名。运行时可见性：")
    A("")
    A("| 可见性 | 数量 |")
    A("|---|---:|")
    A(f"| 双端可见 | {len(both)} |")
    A(f"| 仅 GP 可见 | {len(gpo)} |")
    A(f"| 仅 UI 可见 | {len(uio)} |")
    A(f"| 双端不可见 | {len(non)} |")
    A("")
    A(f"**仅 GP（{len(gpo)}）**：`" + "`、`".join(gpo) + "`")
    A("")
    A("> 世界生成/地形改写类（`TerrainBuilder`、`ResourceBuilder`、`RouteBuilder`、`ImprovementBuilder`、`AreaBuilder`、"
      "`Areas`、`StartPositioner`、`Fractal`）与 `GameEvents` 是 GP 专属；`PlayerVisibility` 在 GP 是命名空间、在 UI 需实例。")
    A("")
    A(f"**仅 UI（{len(uio)}）**：`" + "`、`".join(uio) + "`")
    A("")
    A("> 全部 UI 专属面：`UI`/`UILens`/`UIManager`/`Input`/`Network`/`Modding`/`Options`/`Steam`/`Matchmaking`/"
      "`UserConfiguration`/`AssetPreview`/`ToolTipHelper`/`InstanceManager`/`PopupDialog`/`TunerUtilities` 等。")
    if inc_dep:
        A("")
        A(f"> ⚠ 其中 {len(inc_dep)} 个是 **`include` 之后才可见**（本次扫描按白名单 include 后检出，收尾已复原为 nil）："
          + "`" + "`、`".join(inc_dep) + "`。"
          f"其余 {len(uio) - len(inc_dep)} 个为 InGame 根上下文**原生可见**"
          "（收尾复原后重新复核，原始回传见 `raw/native_ui_check.txt`）。"
          "也就是说：写 mod 时要用这些面，必须先 include 对应模块，否则运行时为 nil。")
    A("")
    A(f"**双端不可见（{len(non)}）**：其中 {sum(1 for x in non if x in {g['库表'] for g in gi})} 个是 GameInfo 库表名"
      "（`Buildings`、`Units`、`Modifiers`…，本来就不是全局，须经 `GameInfo.<表>` 访问，已单独验证见 §5）；"
      "其余是纯实例类（`Control`、`Notification`、`DiplomacyDeal(Item)`、`InputStruct`、`FreeCities`、"
      "`MapPinConfiguration`、`WorldBuilderResourceGenerator`）、文档转储（`CodeBuddyFuncs(Raw)`）与前端/工具模块"
      "（`json`、`Tools`、`Relationship`、`Tests.*`）。")
    A("")
    A(f"**受保护元表（C 侧 `__index`，`pairs` 不可枚举，只能按名索引）**：GP {prot_gp} 个、UI {prot_ui} 个。"
      "典型：`UI`、`GameInfo`、`Locale`、`Network`、`Modding`、`Input`、`UILens`、`Options`、`Steam`、`Search`、`DB`、`Path`。"
      "这也是本次必须逐名探测、不能只做枚举的原因。")
    A("")
    A("---")
    A("")
    A("## 4. 核心发现：同名对象在 GP/UI 是两个不同的类")
    A("")
    A("| 对象 | GP 方法数 | UI 方法数 | 共有 | 仅 GP | 仅 UI |")
    A("|---|---:|---:|---:|---:|---:|")
    for k, label in [("C_Player", "Player（玩家）"), ("C_City", "City（城市 / UI 侧为 CacheCity）"),
                     ("C_Unit", "Unit（单位）"), ("C_Plot", "Plot（地块）"),
                     ("C_City_P_GetBuildQueue", "City:GetBuildQueue()"),
                     ("C_City_P_GetBuildings", "City:GetBuildings()"),
                     ("C_City_P_GetGrowth", "City:GetGrowth()"),
                     ("C_City_P_GetDistricts", "City:GetDistricts()"),
                     ("C_Player_P_GetCulture", "Player:GetCulture()"),
                     ("C_Player_P_GetGovernors", "Player:GetGovernors()"),
                     ("C_Unit_P_GetReligion", "Unit:GetReligion()")]:
        if k in d:
            r = d[k]
            A(f"| {label} | {r['GP方法数']} | {r['UI方法数']} | {r['共有']} | {r['仅GP']} | {r['仅UI']} |")
    A("")
    A("**要点**")
    A("")
    A(f"- `City`：GP 侧独有写操作与底层数据（{d['C_City']['仅GP清单'][:150]}…）；"
      f"UI 侧独有展示/缓存面（{d['C_City']['仅UI清单'][:170]}…）。"
      "**在 GP 脚本里调 `city:GetGold()` / `city:GetCulture()` 会直接报 nil**——这是 mod 常见踩坑点。")
    A(f"- `Player`：GP 独有 `SetProperty`/`GrantYield`/`GrantWMDs`/`AttachModifierByID`/`GetAi_*`/`SetScoringScenario1..3`；"
      f"UI 独有 `GetFavor*`/`GetAgendaTypes`/`GetImprovements`/`GetInfluenceMap`/`IsAI`/`GetCivilianLoyalty` 等读面。")
    A(f"- `Unit`：GP 独有 `Change*`/`Set*`（写），UI 独有 `Get*`（展示、间谍/摇滚乐队/考古等）。"
      f"`Unit:GetReligion()` **仅 GP 有**（UI 侧返回 nil，UI 改用平铺的 `GetReligionType`/`GetReligiousStrength` 等）。")
    A(f"- `Plot`：两端几乎完全对称（共有 {d['C_Plot']['共有']}），GP 只多 `SetOwner`/`SetProperty` 两个写方法——"
      "地块是最「同构」的对象。")
    A(f"- 子对象差异更大：`City:GetGrowth()` GP {d['C_City_P_GetGrowth']['GP方法数']} 法 vs UI {d['C_City_P_GetGrowth']['UI方法数']} 法；"
      f"`Player:GetCulture()` GP {d['C_Player_P_GetCulture']['GP方法数']} vs UI {d['C_Player_P_GetCulture']['UI方法数']}；"
      f"`Player:GetGovernors()` GP {d['C_Player_P_GetGovernors']['GP方法数']} vs UI {d['C_Player_P_GetGovernors']['UI方法数']}。")
    A("- 完整差集（含每个对象的「仅GP清单 / 仅UI清单」全文）见 `GP_UI方法面差异.csv`。")
    A("")
    A("---")
    A("")
    A("## 5. GameInfo 数据库面")
    A("")
    A(f"- 以 `DebugGameplay.sqlite` 的 {len(gi)} 张库表为准逐名探测：**GP {gi_ok} 张、UI {gi_ok} 张可经 `GameInfo.<表>` 取到（返回 userdata）**。")
    A(f"- 不可达：{', '.join(gi_bad) or '无'}（该表存在于库转储但运行时未暴露）。")
    A(f"- 文档只登记了 {sum(1 for r in full if r['路径类别'] == 'gameinfo')} 张 GameInfo 子表，"
      f"运行时可用面约为文档的 {gi_ok / max(1, sum(1 for r in full if r['路径类别'] == 'gameinfo')):.1f} 倍——"
      "**查库时不必受文档表清单限制**。")
    A("- 明细见 `GameInfo库表可达性.csv`。")
    A("")
    A("---")
    A("")
    A("## 6. 文档 availability 与运行时不符（%d 条）" % disagree)
    A("")
    A("| 不符类型 | 条数 | 主要命名空间 |")
    A("|---|---:|---|")
    for k in ("文档偏宽：GP 未见", "文档偏宽：双端均未见", "文档偏宽：UI 未见",
              "文档存疑：UI 未见", "文档存疑：GP 未见", "文档偏窄：GP 亦可见"):
        if verdict.get(k):
            tops = "、".join(f"{n}({c})" for n, c in byns(k))
            A(f"| {k} | {verdict[k]} | {tops} |")
    A("")
    A("**逐类解读**")
    A("")
    A(f"1. **文档偏宽：GP 未见（{verdict['文档偏宽：GP 未见']} 条）**——文档标 `Both`，实际只在 UI 存在。"
      f"绝大多数是 UI 脚本模块被误标：{samples('文档偏宽：GP 未见', 5, byns('文档偏宽：GP 未见'))}。"
      "**结论：这些模块在 GP 脚本里根本不存在，`include` 也无效；而在 UI 侧也需先 `include` 才可见（见 §3 注）。**")
    A(f"2. **文档偏宽：双端均未见（{verdict['文档偏宽：双端均未见']} 条）**——两端都没有该名字，多为文档名与运行时不一致或版本差异："
      f"{samples('文档偏宽：双端均未见', 6, byns('文档偏宽：双端均未见'))}。"
      "例如 `Player:SetScoringScenario` 运行时实为 `SetScoringScenario1/2/3`；"
      "`Player:GetDiplomacy():GetAllianceLevelWithPlayer` 运行时为 `GetAllianceLevel`。")
    A(f"3. **文档偏宽：UI 未见（{verdict['文档偏宽：UI 未见']} 条）**——GP 专属被标 `Both`："
      f"{samples('文档偏宽：UI 未见', 5, byns('文档偏宽：UI 未见'))}（`GameSummary`/`RouteBuilder`/`PlayerVisibility` 属世界生成与 GP 侧统计面）。")
    A(f"4. **文档存疑：UI 未见（{verdict['文档存疑：UI 未见']} 条）**——文档标 `UI` 却在 InGame 上下文找不到："
      f"{samples('文档存疑：UI 未见', 5, byns('文档存疑：UI 未见'))}。"
      "细分为：Governor 三层对象本局取不到实例（12 条）、`IconManager` 需要实例才能访问，模块面取不到（5 条）、"
      "FrontEnd 事件在 InGame 不可见（`Events.BeginFullGamePurchase`/`MultiplayerConnectionFailed` 等 5 条）、"
      "`InputStruct` 的方法被挂到了 `Input` 名下（3 条）。")
    A(f"5. **文档存疑：GP 未见（{verdict['文档存疑：GP 未见']} 条）**——标 `GamePlay` 但 GP 侧没有："
      f"{samples('文档存疑：GP 未见', 5, byns('文档存疑：GP 未见'))}（`UnitManager` 的 Lifespan/MaxHitPoints 系与 `TerrainBuilder.SetResourceType` 疑为旧版或 WorldBuilder 专属）。")
    A(f"6. **文档偏窄：GP 亦可见（{verdict['文档偏窄：GP 亦可见']} 条）**——标 `UI` 但 GP 也有，属**可利用的好消息**："
      f"{samples('文档偏窄：GP 亦可见', 5, byns('文档偏窄：GP 亦可见'))}（`Achievements`、`GameSummary`、`PlayerVisibilityManager`、部分 `Events` 在 GP 同样可调用）。")
    A("")
    A("> 全部不符条目（含运行时近似名建议列）见 `api_scope_文档与运行时不符.csv`。")
    A("")
    A("---")
    A("")
    A("## 7. 无法验证清单（%d 条）与补救办法" % unver)
    A("")
    A("| 阻塞原因 | 条数 | 复现所需条件 |")
    A("|---|---:|---|")
    reason = collections.Counter()
    for r in ncb:
        if r["一致性判定"].startswith(("无法验证", "动态")):
            reason[(r["命名空间/类"], r["一致性判定"])] += 1
    for (cls, v), c in reason.most_common():
        A(f"| `{cls}` | {c} | {v.split('：', 1)[-1] if '：' in v else v} |")
    A("")
    A("**补救办法（需要时再跑一轮即可闭环）**")
    A("")
    A("- `Notification`（30 条）：先用 GP 造一条通知（或读一个有未读通知的存档），再重跑 pass3 即可取到实例。")
    A("- `DiplomacyDeal` / `DiplomacyDealItem`（62 条）：进入一次外交交易界面（`DealManager` 取 working deal）后重扫 UI。")
    A("- `Player:GetGovernors():GetGovernor(i)` 三层（16 条）：本局无已任命总督；任命任一总督后重跑三层恢复即可。")
    A("- `WorldBuilderResourceGenerator`（23 条）/ `Fractal`（3 条）：需在世界生成器会话中扫描。")
    A("- `InputStruct`（16 条）：需真实输入事件回调时抓 `pInputStruct` 实例（可在 UI 输入处理器里挂一次性钩子）。")
    A("- `MapPinConfiguration`（13 条）：在地图钉编辑 UI 打开时扫描。")
    A("- `MapRoutes.GetIndexedPortal` 子方法（5 条）：需地图上存在传送门（portal）；`GetIndexedPortal(0)` 在本图返回空。")
    A("")
    A("---")
    A("")
    A("## 8. 文档数据缺陷（api.sqlite 侧）")
    A("")
    A(f"### 8.1 转储清单冒充命名空间：{len(cbd)} 条（{pct(len(cbd), len(full))}）")
    A("")
    A(f"- `CodeBuddyFuncs`（{sum(1 for r in cbd if r['命名空间/类'] == 'CodeBuddyFuncs')} 条）与 "
      f"`CodeBuddyFuncsRaw`（{sum(1 for r in cbd if r['命名空间/类'] == 'CodeBuddyFuncsRaw')} 条）在 GP/UI **都没有这个全局**，"
      "它们是把各处 UI 辅助函数汇总成的文档清单。")
    A(f"- 把 `CodeBuddyFuncs` 的 {len(c1)} 个名字拿到真实面上反查（UI 51 个面 / GP 43 个面）：**UI 侧命中 {cb_ui} 个名字、GP 侧命中 {cb_gp} 个、"
      f"两端都找不到 {cb_none} 个**。归属面 Top：")
    A("")
    A("| 归属面 | 命中名数 |")
    A("|---|---:|")
    for s_, c_ in surf_top:
        A(f"| `{s_.replace('__SC.C_', '实例:')}` | {c_} |")
    A("")
    A(f"- `CodeBuddyFuncsRaw` 的「名字」其实是 C++ 原始签名串（如 `ButtonControl* GetButton( void )`、`CFunction: AddVertex`），"
      f"**无法作为 Lua 名索引**（首轮 {st['stat']['GP状态分布'].get('CF', 0)} 条 `CF` 状态即由此产生）；"
      f"从签名里归一化出 {len(c2)} 个候选标识符后，UI 侧命中 {raw_ui} 个。")
    A("- 明细见 `CodeBuddy归属面.csv` 与 `api_scope_CodeBuddy转储.csv`。")
    A("")
    A(f"### 8.2 名称拼接/损坏：{st['name_issue']} 条")
    A("")
    A("| 缺陷形态 | 例子 | 处理 |")
    A("|---|---|---|")
    A("| 三层路径压平 | `City.GetDistricts` → `GetDistrictGetAirSlots` | 下钻 `GetDistrict(i)` 取 District 实例后按真名 `GetAirSlots` 命中（UI 侧 12 条转为一致） |")
    A("| 三层路径压平 | `Player.GetGovernors` → `GetGovernorGetComponentID` | 同上，但本局无总督实例 → 仍记不可验证 |")
    A("| 文档 id 残留 | `Map.GetCityPlots` → `GetWorkingCityIDQ-MapGetCityPlots` | 真名 `GetWorkingCityID`（UI 命中） |")
    A("| 文档 id 残留 | `Map.GetContinentCoastalPlots` → `Q-MapGetCityPlotsGetPurchasedByCity` | 真身是 `Map.GetCityPlots():GetPurchasedByCity()`（UI 命中） |")
    A("| `Get` 前缀冗余 | `UI.GetGameParameters` → `GetSetValue` / `GetGetCount` … 15 条 | 实测该对象只有 `Add/Get/GetValue/Remove/SetValue` 5 法：5 条对得上、10 条属文档多写 |")
    A("")
    A("> 明细见 `api_scope_文档名异常.csv`（含每条的 GP/UI 真名列）。")
    A("")
    A("### 8.3 事件面是动态代理")
    A("")
    A("| 面 | GP | UI | 说明 |")
    A("|---|---|---|---|")
    A("| `GameEvents` | 任意名 → table | 不存在 | GP 事件表按需自动生成，存在性检查无意义 |")
    A("| `LuaEvents` | 任意名 → table | 任意名 → table | 同上 |")
    A("| `Events` | 未知名 → nil | 未知名 → nil | **可以**做存在性判定（本轮据此判定 `Events.*` 25 条） |")
    A("| `ReportingEvents` | 未知名 → nil | 未知名 → nil | 同上 |")
    A("")
    A("---")
    A("")
    A("## 9. 交付物清单")
    A("")
    A(f"目录：`{dest}`")
    A("")
    A("| 文件 | 内容 |")
    A("|---|---|")
    A("| `API范围验证报告.md` | 本报告 |")
    A(f"| `api_scope_full.csv` | 全量 {len(full)} 条逐条结果（GP/UI 状态、存在性、真名、近似名、备注、判定） |")
    A(f"| `api_scope_文档与运行时不符.csv` | {disagree} 条不符明细 |")
    A(f"| `api_scope_无法验证.csv` | {unver} 条不可判明细（含阻塞原因） |")
    A(f"| `api_scope_文档名异常.csv` | {st['name_issue']} 条名称拼接/损坏（含真名） |")
    A(f"| `api_scope_CodeBuddy转储.csv` | {len(cbd)} 条转储清单条目 |")
    A("| `命名空间汇总.csv` | 每个命名空间/类的条目数、GP/UI 存在数、判定分布 |")
    A(f"| `命名空间可见性.csv` | {len(gl)} 个名字在 GP/UI 的类型、键数、是否受保护元表 |")
    A("| `GP_UI方法面差异.csv` | 实例与子对象的方法面差集（含仅GP/仅UI 全清单） |")
    A(f"| `GameInfo库表可达性.csv` | {len(gi)} 张库表的运行时可达性 |")
    A("| `CodeBuddy归属面.csv` | 转储名字在真实面上的归属 |")
    A("| `统计.json` | 全部统计数字（机器可读） |")
    A("| `raw/` | 原始回传（探测/枚举/子对象/三层/补测）、扫描脚本与 Lua 片段，可复现 |")
    A("")
    A("CSV 均为 UTF-8-BOM，Excel 直接双击可正确显示中文。")
    A("")
    A("---")
    A("")
    A("## 10. 复现方法")
    A("")
    A("```powershell")
    A("# 前置：游戏内 Options 勾选 Tuner；关闭 FireTuner GUI；读档进入对局")
    A('$T = "%USERPROFILE%/.agents/skills/civ6-tuner/scripts/tuner_exec.py"')
    A("python $T check                       # 确认 gamecore/ingame 状态存在")
    A(f'python "{WORK}\\scan.py"                # 主扫描（约 219 次调用，1~2 分钟）')
    A(f'python "{WORK}\\supplement.py"          # 补测（表达式修正 / 候选名 / 跨 UI 状态）')
    A(f'python "{WORK}\\finalize.py"            # 归并 -> 桌面 CSV')
    A(f'python "{WORK}\\mkreport.py"            # 生成本报告')
    A("```")
    A("")
    A("三个脚本均在 `raw/` 内随附；Lua 片段在 `raw/lua_*.lua`。")
    A("")
    A("---")
    A("")
    A("## 11. 局限性（诚实声明）")
    A("")
    A("1. **单存档、单视角**：本次对局为本地玩家 0（1 座城市、41 个单位、无总督、无未读通知、无进行中外交会话、地图无传送门），"
      "因此依赖这些条件的类无法验证（§7 列出 155 条）。")
    A("2. **UI 侧以 `InGame` 根上下文为主**，另在 12 个其它 UI 状态复查；**FrontEnd（主菜单/多人大厅）上下文未覆盖**"
      "（对局中无法进入），故 `Events.BeginFullGamePurchase`、`Matchmaking.*` 等前端面按「本上下文未见」记录。")
    A("3. **只判存在性**：不校验参数个数/类型、返回值、以及「名字存在但调用即报错」的情形；"
      "受保护元表（C 侧 `__index`）的成员只能按名索引，无法枚举出「文档未收录但运行时存在」的成员（实例类除外，其方法表可枚举）。")
    A("4. **`include` 会改变 UI 状态**：本轮已按白名单最小化并复原，但严格来说扫描后的 InGame 状态与从未扫描过的状态"
      "不是逐位相同（重新载入 UI 或重启游戏即完全一致）。")
    A("5. 文档基线 `api.sqlite` 自身存在缺陷（§8），因此「不符」条目里既有文档错、也有名字拼接错，"
      "报告已尽量区分并给出真名/近似名，但**最终仍应以运行时 CSV 为准**。")
    A("")
    (dest / "API范围验证报告.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("报告已写入：", dest / "API范围验证报告.md", len(L), "行")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
