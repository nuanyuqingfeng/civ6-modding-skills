#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预分类审核清单：把「不符 316 + 无法验证 155」逐条归入可决策的桶，
并叠加 Civ6LuaHelper.exe 内置数据的 humanChecked（人工验证）裁定。

产出（写入桌面交付目录）：
  审核清单_预分类.csv      全部 471 条，含桶/证据/建议动作/是否已人工裁定
  审核清单.md              分桶逐条列举（人工裁定单列一节）
  审核清单.xlsx            每桶一个 sheet，便于筛选审核
  helper_humanChecked.json 助手内 18 条人工验证条目原文摘录
"""
from __future__ import annotations

import collections
import csv
import io
import json
import re
import sys
from pathlib import Path

WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")
OUT = WORK / "out"
DEST = Path(r"<本目录（随 skill 分发）>")
HELPER_JSON = Path(r"%USERPROFILE%\AppData\Local\Temp"
                   r"\onefile_33376_938175_aW1luoQf41E\data\api_enhanced.json")
HELPER_EXE = Path(r"<第三方工具 Civ6LuaHelper.exe>")

EXIST = {"function", "table", "userdata", "number", "string", "boolean", "thread"}


def clean_surf(x):
    x = x.replace("__SC.", "")
    return x[2:] if x.startswith("C_") else x


def build_name_index():
    """name -> {(ctx, surface)}：把扫描期所有「确实存在」的成员名按面归档。"""
    d = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    idx = collections.defaultdict(set)
    ns = collections.defaultdict(set)

    def add(ctx, surf, name):
        if name and not name.startswith("__") and re.match(r"^[A-Za-z_]\w*$", name):
            idx[name].add((ctx, surf))

    for ctx in ("gp", "ui"):
        for e, st in d[ctx]["probe"].items():
            if st in EXIST and "." in e:
                surf, _, name = e.rpartition(".")
                add(ctx, clean_surf(surf), name)
        for g, info in d[ctx]["enum_globals"].items():
            if info.get("type") in ("table", "userdata"):
                ns[g].add(ctx)
            for k in info.get("keys", []):
                if ":" in k:
                    add(ctx, g, k.split(":")[0])
        for key, ks in d[ctx]["enum_methods"].items():
            for k in ks:
                if ":" in k:
                    add(ctx, clean_surf(key), k.split(":")[0])
    for ctx, f in (("gp", "l3_gp.txt"), ("ui", "l3_ui.txt")):
        p = OUT / f
        if p.exists():
            for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if ln.startswith("L3K|"):
                    q = ln.split("|", 3)
                    if not q[3].startswith("<"):
                        for k in q[3].split(","):
                            if ":" in k:
                                add(ctx, q[1][2:] + "→L3", k.split(":")[0])
    for ctx in ("gp", "ui"):
        for key in ("codebuddyfuncs", "raw_normalized"):
            for e in d["codebuddy"][ctx][key]:
                surf, _, name = e.rpartition(".")
                add(ctx, clean_surf(surf), name)
    return idx, ns


def load_helper_verified():
    """助手内置数据里 humanChecked=true 的条目（以 id 为键）。"""
    if not HELPER_JSON.exists():
        return {}, "未找到助手解包数据"
    d = json.loads(HELPER_JSON.read_text(encoding="utf-8-sig"))
    out = {}
    for oname, o in d.get("objects", {}).items():
        if not isinstance(o, dict):
            continue
        for fname, f in o.items():
            if isinstance(f, dict) and f.get("humanChecked"):
                out[f.get("id", fname)] = {
                    "id": f.get("id"), "displayName": f.get("displayName"),
                    "availability": f.get("availability"), "invoke": f.get("invoke"),
                    "table": f.get("table"),
                    "path": [f.get("functionA"), f.get("functionB"), f.get("functionC")],
                    "notes": f.get("notes") or [],
                    "enrichUnused": f.get("enrichUnused"),
                    "usageSummary": f.get("usageSummary"),
                }
    return out, f"来源：{HELPER_EXE.name} 运行时解包目录 data/api_enhanced.json（Nuitka onefile，PID 33376）"


def _tokens(name):
    parts = re.split(r"[_\s]+", name)
    out = []
    for pt in parts:
        out += re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", pt)
    return {t for t in out if len(t) >= 6}


def _plausible(member, surface):
    """名字巧合过滤：成员名与命中面需共享一个 >=6 字符的驼峰词元。"""
    a, b = _tokens(member), _tokens(surface.replace("_P_", "_"))
    return bool(a & b)


def _scope_bucket(r, v, tbl, gp, ui, gpe, uie):
    """availability 标错（A）与运行时确无（C）的判定，命名空间行与成员行共用。"""
    if v == "文档偏宽：GP 未见":
        inc = tbl in ("TunerUtilities", "ToolTipHelper", "g_ToolTipGenerators", "InstanceManager",
                      "PopupDialog", "SupportFunctions")
        return ("A availability 标错",
                "UI 专属模块被标 Both（需 include）" if inc else "UI 专属被标 Both（原生）",
                f"GP={gp}（该上下文不存在此面）　UI={ui}", "availability 改为 UI")
    if v == "文档偏宽：UI 未见":
        return "A availability 标错", "GP 专属被标 Both", f"UI={ui}　GP={gp}", "availability 改为 GamePlay"
    if v == "文档偏窄：GP 亦可见":
        return "A availability 标错", "标 UI 但 GP 亦可调", f"GP={gp}　UI={ui}", "availability 放宽为 Both"
    if v == "文档偏窄：UI 亦可见":
        return "A availability 标错", "标 GamePlay 但 UI 亦可调", f"GP={gp}　UI={ui}", "availability 放宽为 Both"
    if v in ("文档偏宽：双端均未见", "文档存疑：UI 未见", "文档存疑：GP 未见"):
        return "C 运行时确无此名", v, f"GP={gp}/{gpe}　UI={ui}/{uie}", "裁决：删除条目 / 标注版本或 DLC 条件"
    return "E 其它", v, f"GP={gp}/{gpe}　UI={ui}/{uie}", "人工判断"


def _gameinfo_bucket(r, tbl):
    HERO = {"HeroAbilities", "HeroActions", "HeroDefinitions", "Hero_AccumulatedXp",
            "Hero_Attributes", "Hero_XpNeeded", "DualHeroes"}
    LOC = {"Icons", "Colors", "IconDefinitions", "Icons_FontIcons"}
    if tbl in HERO:
        why = "英雄与传说(Heroes & Legends)模式表：本局未启用该模式/DLC，GameInfo 无此表"
    elif tbl in LOC:
        why = "属本地化/图标库（Localization DB 或未随本局加载），GP/UI 的 GameInfo 不暴露"
    else:
        why = "Gameplay/Localization/Configuration 三库转储均无此表：疑为旧版本或其它模式/DLC 专属"
    return ("C 运行时确无此名", "GameInfo 子表在本局不可达",
            f"GameInfo.{tbl} 双端均为 nil；{why}", "标注启用条件（模式/DLC/库归属），勿当通用表使用")


def classify(r, idx, ns, l3sets=None):
    """返回 (桶, 子类, 证据, 建议动作)。l3sets: {ctx: {容器键: {方法名}}}"""
    v = r["一致性判定"]
    tbl, fn, sub = r["命名空间/类"], r["方法"], r["子方法"]
    name = sub or fn or tbl
    gp, ui = r["GP状态"], r["UI状态"]
    gpe, uie = r["GP存在"], r["UI存在"]
    l3sets = l3sets or {}

    # D 暂不可测
    if v.startswith("无法验证") or v.startswith("动态"):
        reason = v.split("：", 1)[-1] if "：" in v else v
        return "D 暂不可测", reason, f"GP={gp}/{gpe}　UI={ui}/{uie}", "按补测条件复跑一轮"
    if v == "文档存疑：UI 未见" and tbl == "Player" and fn == "GetGovernors":
        return ("D 暂不可测", "需已任命总督（Governor 三层实例）", f"GP={gp}/{gpe}　UI={ui}/{uie}",
                "任命任一总督后复跑三层恢复")

    # C 特例：GameInfo 子表不可达（可能是 namespace 行，也可能是 gameinfo 行）
    if r["路径类别"] == "gameinfo" or "GameInfo 子表不存在" in (r["GP备注"] + r["UI备注"]):
        return _gameinfo_bucket(r, tbl)

    # 命名空间自身行：直接进 A/C
    if not (fn or sub):
        return _scope_bucket(r, v, tbl, gp, ui, gpe, uie)

    # 缺失上下文（文档声称该有、但实测没有的那一端）
    miss = []
    if r["文档可用性"] in ("Both", "GamePlay") and gpe == "否":
        miss.append("gp")
    if r["文档可用性"] in ("Both", "UI") and uie == "否":
        miss.append("ui")

    # B1 已确认真名
    if r["GP真名"] or r["UI真名"]:
        return ("B 文档名可修", "已确认真名（三层压平/拼接）",
                f"真名 GP={r['GP真名'] or '—'} / UI={r['UI真名'] or '—'}", "按真名改文档")
    # B2 id 残留
    if "-" in name or re.search(r"[A-Z]-", name):
        return "B 文档名可修", "名称含 id 残留（损坏）", f"名={name}", "人工订正名称后重测"
    # B3 复数容器 -> 元素类（三层压平的另一形态）
    m = re.match(r"^Get(.+?)s$", fn or "")
    if m and sub:
        cls = m.group(1)
        for ctx in miss:
            ms = l3sets.get(ctx, {})
            for key, names in ms.items():
                if key == "C_" + cls or ("_P_Get" + cls + "s") in key:
                    if sub in names:
                        return ("B 文档名可修", "三层压平：真名在元素对象上",
                                f"{ctx.upper()} 侧 `{cls}` 对象有 `{sub}`（经 {tbl}:{fn}() 的元素取得）",
                                f"文档路径改为 {tbl}:{fn}():<元素>:{sub}()")
    # B4/B5 名字在别的面 / 近似名（只看缺失的那一端，且需词干可信）
    hits = sorted(idx.get(name, []))
    own = {tbl, tbl.replace(".", "_")}
    other = [(c, s) for c, s in hits
             if c in miss and s.split("_P_")[0] not in own and s != tbl and _plausible(name, s)]
    stripped = re.sub(r"^(Get|Set|Can|Is|Has)", "", name)
    ns_hit = sorted(x for x in ns.get(stripped, []) if x in miss) if stripped else []
    if ns_hit:
        return ("B 文档名可修", "挂错父级：真身是同名命名空间",
                f"运行时存在命名空间 `{stripped}`（{'/'.join(ns_hit)}）", f"改为直接访问 `{stripped}.*`")
    if other:
        s = "、".join(f"{c.upper()}:{sur}" for c, sur in other[:3])
        return "B 文档名可修", "挂错父级：名字在别的面存在", f"命中面 {s}", "核对文档层级后改路径"
    # 父对象已实测枚举、去前缀候选也不存在 -> 文档多写
    if "亦不存在" in (r["GP备注"] + r["UI备注"]):
        return ("C 运行时确无此名", "文档多写的子方法（父对象已实测枚举）",
                (r["UI备注"] or r["GP备注"])[:120], "删除条目（父对象方法面已完整枚举）")
    if r["GP近似名"] or r["UI近似名"]:
        near = (r["GP近似名"] or r["UI近似名"]).split()[:3]
        return "B 文档名可修", "近似名可对齐", f"运行时近似名：{'、'.join(near)}", "确认是否改名/版本号差异"

    return _scope_bucket(r, v, tbl, gp, ui, gpe, uie)


def main():
    full = list(csv.DictReader(io.open(DEST / "api_scope_full.csv", encoding="utf-8-sig")))
    idx, ns = build_name_index()
    (OUT / "name_index.json").write_text(
        json.dumps({"names": {k: sorted([list(x) for x in v]) for k, v in idx.items()},
                    "ns": {k: sorted(v) for k, v in ns.items()}}, ensure_ascii=False), encoding="utf-8")
    verified, vsrc = load_helper_verified()

    problems = [r for r in full if r["一致性判定"].startswith(("文档偏宽", "文档偏窄", "文档存疑",
                                                             "无法验证", "部分不可验证", "动态"))]
    rows = []
    for r in problems:
        bucket, sub, ev, act = classify(r, idx, ns)
        hv = verified.get(r["id"])
        api = r["命名空间/类"] + ("." + r["方法"] if r["方法"] else "") + ("." + r["子方法"] if r["子方法"] else "")
        rows.append({
            "id": r["id"], "API": api, "命名空间/类": r["命名空间/类"], "方法": r["方法"], "子方法": r["子方法"],
            "调用形态": r["调用形态"], "文档可用性": r["文档可用性"],
            "GP实测": f'{r["GP状态"]}/{r["GP存在"]}', "UI实测": f'{r["UI状态"]}/{r["UI存在"]}',
            "原判定": r["一致性判定"], "桶": bucket, "子类": sub, "证据": ev,
            "运行时真名": r["GP真名"] or r["UI真名"] or "",
            "运行时近似名": r["GP近似名"] or r["UI近似名"] or "",
            "其它UI状态": r["其它UI状态"],
            "助手人工验证": "是" if hv else "",
            "助手结论availability": hv["availability"] if hv else "",
            "助手displayName": hv["displayName"] if hv else "",
            "助手备注首条": (hv["notes"][0] if hv and hv["notes"] else "") if hv else "",
            "是否需审核": "否（以助手人工验证结论为准）" if hv else "是",
            "建议动作": act,
            "参数": r["参数"], "返回": r["返回"],
        })

    # 助手人工验证条目（含未落在问题集里的）
    vrows = []
    byid = {r["id"]: r for r in full}
    for vid, hv in verified.items():
        sr = byid.get(vid)
        vrows.append({
            "id": vid, "助手displayName": hv["displayName"], "助手availability": hv["availability"],
            "助手路径": " → ".join([x for x in hv["path"] if x]),
            "助手备注首条": hv["notes"][0] if hv["notes"] else "",
            "本次GP实测": (sr["GP状态"] + "/" + sr["GP存在"]) if sr else "（本次清单无此行）",
            "本次UI实测": (sr["UI状态"] + "/" + sr["UI存在"]) if sr else "",
            "本次判定": sr["一致性判定"] if sr else "",
            "是否在问题集": "是" if sr and sr["一致性判定"].startswith(("文档偏宽", "文档偏窄", "文档存疑", "无法验证", "动态")) else "否",
        })

    cols = list(rows[0].keys())
    with open(DEST / "审核清单_预分类.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for x in sorted(rows, key=lambda z: (z["桶"], z["子类"], z["命名空间/类"], z["API"])):
            w.writerow(x)
    vcols = list(vrows[0].keys())
    with open(DEST / "助手人工验证条目.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=vcols, extrasaction="ignore")
        w.writeheader()
        for x in vrows:
            w.writerow(x)
    (DEST / "helper_humanChecked.json").write_text(json.dumps(
        {"source": vsrc, "count": len(verified), "entries": verified}, ensure_ascii=False, indent=1), encoding="utf-8")

    # xlsx：每桶一个 sheet
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = Workbook()
        wb.remove(wb.active)
        buckets = sorted({x["桶"] for x in rows})
        head_fill = PatternFill("solid", fgColor="1F4E79")
        head_font = Font(color="FFFFFF", bold=True)
        for b in buckets + ["全部"]:
            data = [x for x in rows if x["桶"] == b] if b != "全部" else rows
            ws = wb.create_sheet(b.replace("/", "-")[:28])
            ws.append(cols)
            for c in ws[1]:
                c.fill, c.font = head_fill, head_font
                c.alignment = Alignment(vertical="center")
            for x in sorted(data, key=lambda z: (z["子类"], z["命名空间/类"], z["API"])):
                ws.append([x[c] for c in cols])
            widths = {"id": 34, "API": 46, "证据": 44, "建议动作": 30, "子类": 30, "桶": 18,
                      "原判定": 26, "助手displayName": 40, "助手备注首条": 46, "是否需审核": 22}
            for i, c in enumerate(cols, 1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = widths.get(c, 14)
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
        ws = wb.create_sheet("助手人工验证18条")
        ws.append(vcols)
        for c in ws[1]:
            c.fill, c.font = head_fill, head_font
        for x in vrows:
            ws.append([x[c] for c in vcols])
        ws.freeze_panes = "A2"
        wb.save(DEST / "审核清单.xlsx")
        xlsx_ok = True
    except Exception as e:
        xlsx_ok = f"失败：{e}"

    stat = {
        "问题总数": len(rows),
        "已人工验证裁定": sum(1 for x in rows if x["助手人工验证"] == "是"),
        "仍需审核": sum(1 for x in rows if x["是否需审核"] == "是"),
        "桶分布": dict(collections.Counter(x["桶"] for x in rows).most_common()),
        "桶分布_剔除人工验证后": dict(collections.Counter(x["桶"] for x in rows if x["是否需审核"] == "是").most_common()),
        "子类分布_剔除人工验证后": {f"{b} | {c}": n for (b, c), n in collections.Counter(
            (x["桶"], x["子类"]) for x in rows if x["是否需审核"] == "是").most_common()},
        "助手条目总数": len(verified),
        "助手条目落在问题集": sum(1 for x in vrows if x["是否在问题集"] == "是"),
        "xlsx": str(xlsx_ok),
        "verified_source": vsrc,
    }
    (DEST / "审核清单_统计.json").write_text(json.dumps(stat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stat, ensure_ascii=False, indent=1))
    return rows, vrows, stat, verified, vsrc


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
