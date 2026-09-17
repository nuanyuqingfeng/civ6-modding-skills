#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本次 FireTuner UI/GP 范围验证结果实装进 civ6-modding skill。

标记规则（按用户指定）
--------------------
verify_status = '已核验'  本次核查过关者（判定「一致」）+ P1（已实装修正/已确认真身）
verify_status = '存疑'    **仅**本次查出 API 文档自身不对者：
                          A availability 标错（非 P1）/ B 文档名或路径错（非 P1）/
                          C 运行时确无此名 / CodeBuddy 文档转储
verify_status = ''（留空）本次**无法实测**者（D 桶：缺实例通道/动态事件代理），
                          既不判过关也不挂嫌疑，只写 verify_note 说明补测条件
所有行一律**不删除**。P1 之外的嫌疑行只标记、保留原值。

写入目标
--------
1. database/api.sqlite         新增 11 列并回填；P1 的 availability 实装修正
2. reference/api_enhanced.json 已核验 -> humanChecked=true（助手「人工核查」字段）；
                               存疑 -> suspect=true；待补测 -> pendingTest=true（不挂任何核验/嫌疑标记）
3. 删除既有备份 database/api.sqlite.bak_pre_tuner_20260908_112150
"""
from __future__ import annotations

import csv
import io
import json
import re
import shutil
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

SKILL = Path(r"%USERPROFILE%\.agents\skills\civ6-modding")
DB = SKILL / "database" / "api.sqlite"
JSONF = SKILL / "reference" / "api_enhanced.json"
BACKUPS = [SKILL / "database" / "api.sqlite.bak_pre_tuner_20260908_112150"]
DEST = Path(r"<本目录（随 skill 分发）>")
WORK = Path(r"%USERPROFILE%\AppData\Local\Temp\civ6_api_scope")
SAFE = WORK / "out" / "pre_install"          # 变更前的安全副本（放在 skill 之外）
TODAY = "2026-09-08"

NEW_COLS = [
    ("verify_status", "TEXT DEFAULT ''"),
    ("verify_scope", "TEXT DEFAULT ''"),
    ("verify_note", "TEXT DEFAULT ''"),
    ("verify_at", "TEXT DEFAULT ''"),
    ("runtime_gp", "TEXT DEFAULT ''"),
    ("runtime_ui", "TEXT DEFAULT ''"),
    ("audit_priority", "TEXT DEFAULT ''"),
    ("suspect_type", "TEXT DEFAULT ''"),
    ("corrected_from", "TEXT DEFAULT ''"),
    ("true_name", "TEXT DEFAULT ''"),
    ("true_path", "TEXT DEFAULT ''"),
]


def rd(name):
    return list(csv.DictReader(io.open(DEST / name, encoding="utf-8-sig")))


def target_avail(action):
    m = re.search(r"availability (?:改为|放宽为) (\w+)", action or "")
    return m.group(1) if m else None


def true_path_from(sub, ev, name, near):
    """从 P1 的 B 桶证据里还原真身路径/真名。"""
    tp = tn = ""
    if sub == "三层压平：真名在元素对象上":
        m = re.search(r"`(\w+)` 对象有 `(\w+)`", ev or "")
        if m:
            tp, tn = f"{m.group(1)}:{m.group(2)}()", m.group(2)
    elif sub == "挂错父级：真身是同名命名空间":
        m = re.search(r"命名空间 `(\w+)`", ev or "")
        if m:
            tp = f"{m.group(1)}.*（全局命名空间）"
            tn = name
    elif sub == "挂错父级：名字在别的面存在":
        m = re.search(r"命中面 ([^；]+)", ev or "")
        if m:
            surfs = [x.split(":", 1)[-1] for x in m.group(1).split("、")[:2]]
            tp = " / ".join(f"{s}.{name}" for s in surfs)
            tn = name
    elif sub == "近似名可对齐":
        tn = (near or "").strip().replace(" ", " | ")
        tp = tn
    return tp, tn


def main(apply=True):
    full = {r["id"]: r for r in rd("api_scope_full.csv")}
    audit = {r["id"]: r for r in rd("审核清单_预分类.csv")}
    hj = json.loads((WORK / "helper_human_checked.json").read_text(encoding="utf-8"))

    SAFE.mkdir(parents=True, exist_ok=True)
    if apply:
        shutil.copy2(DB, SAFE / "api.sqlite.orig")
        shutil.copy2(JSONF, SAFE / "api_enhanced.json.orig")

    plan = {}     # id -> dict(字段)
    stats = Counter()
    for rid, r in full.items():
        a = audit.get(rid)
        v = r["一致性判定"]
        tbl = r["命名空间/类"]
        gp, ui = r["GP状态"], r["UI状态"]
        scope = r["实际范围"]
        doc = r["文档可用性"]
        tname = r["GP真名"] or r["UI真名"] or ""
        rec = {"runtime_gp": gp, "runtime_ui": ui, "verify_at": TODAY,
               "verify_status": "", "verify_scope": "", "verify_note": "",
               "audit_priority": "", "suspect_type": "", "corrected_from": "",
               "true_name": tname, "true_path": "", "new_availability": ""}
        base = f"{TODAY} FireTuner 实测：GP={gp}、UI={ui}"

        if tbl.startswith("CodeBuddy"):
            rec.update(verify_status="存疑", suspect_type="文档转储（非运行时命名空间）",
                       audit_priority="转储",
                       verify_note=(f"{base}；GP/UI 均无 `{tbl}` 全局——该清单是把各处 UI 辅助函数汇总的"
                                    f"文档转储（CodeBuddyFuncsRaw 更是 C++ 签名串，不可作 Lua 名索引）；"
                                    f"归属面详见桌面 CodeBuddy归属面.csv。未删除，保留备查"))
            stats["存疑·转储"] += 1
        elif v.startswith("一致"):
            rec["verify_status"] = "已核验"
            rec["verify_scope"] = scope
            note = f"{base}；范围={scope}；与文档 availability={doc} 一致"
            if "不可验证" in v:
                note += f"（{v}：该侧无实例通道/父对象缺失，子方法必然不存在）"
            if tname:
                note += f"；文档名缺陷已核出真名 `{tname}`（存在性以真名确认）"
            rec["verify_note"] = note
            stats["已核验·一致"] += 1
        elif a is None:
            rec.update(verify_status="", audit_priority="",
                       verify_note=f"{base}；未进入问题集（判定={v}）")
            stats["其它"] += 1
        else:
            bucket, sub, prio = a["桶"], a["子类"], a["优先级"]
            ev, act = a["证据"], a["建议动作"]
            near = a["运行时近似名"]
            name = r["子方法"] or r["方法"] or tbl
            if bucket.startswith("D"):
                # 无法实测 -> verify_status 留空
                rec["pending_reason"] = sub
                rec.update(verify_status="", audit_priority="待补测", suspect_type="",
                           verify_note=(f"{TODAY} 本次无法实测：{sub}；"
                                        f"非文档缺陷，具备条件后复测（GP={gp}、UI={ui} 仅为索引失败/无实例）"))
                stats["留空·无法实测"] += 1
            elif prio == "P1":
                rec["verify_status"] = "已核验"
                rec["verify_scope"] = scope
                rec["audit_priority"] = "P1"
                if bucket.startswith("A"):
                    nv = target_avail(act)
                    if nv and nv != doc:
                        rec["new_availability"] = nv
                        rec["corrected_from"] = doc
                        rec["verify_note"] = (f"{base}；原标 {doc} 与实测不符，实为 {nv}，"
                                              f"已实装修正 availability（{sub}）")
                        stats["已核验·P1改availability"] += 1
                    else:
                        rec["verify_note"] = f"{base}；{sub}；{ev}（未改动 availability）"
                        stats["已核验·P1其它"] += 1
                else:
                    tp, tn = true_path_from(sub, ev, name, near)
                    rec["true_path"], rec["true_name"] = tp, (tn or tname)
                    rec["verify_note"] = (f"{base}；文档名称/路径有误，运行时真身：{tp or tn or ev}；"
                                          f"已加注真身，未改文档键（{sub}）")
                    stats["已核验·P1注真身"] += 1
            else:
                rec.update(verify_status="存疑", suspect_type=f"{bucket} · {sub}",
                           audit_priority=prio,
                           verify_note=(f"{base}；{bucket} · {sub}；{ev}；建议：{act}"
                                        f"（仅标记存疑，未删除、未改原值）"))
                stats[f"存疑·{prio}"] += 1
        plan[rid] = rec

    # 助手人工验证的 1 条与实测冲突：记录人工结论，不改实测事实
    special = "Q-CityGetBuildQueueGetTurnsLeft"
    if special in plan:
        plan[special]["verify_note"] += ("；⚠ 助手(Civ6LuaHelper)人工验证结论 availability=UI，"
                                         "本次实测 GP/UI 两端均存在该函数——按实测保留 Both，人工结论已记录待你裁决")
        plan[special]["suspect_type"] = ""
    # 上一会话已按实测修正过的一行，补充留痕
    prev = "Q-PlayerVisibilityManagerGetPlayerVisibility"
    if prev in plan:
        plan[prev]["verify_note"] += "；（本行 availability 已于本次扫描前由 UI 修正为 Both，本次实测复核通过）"

    # ---------------- 写 sqlite ----------------
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    have = {r[1] for r in con.execute("PRAGMA table_info(api_functions)")}
    if apply:
        for c, t in NEW_COLS:
            if c not in have:
                con.execute(f"ALTER TABLE api_functions ADD COLUMN {c} {t}")
        cols = [c for c, _ in NEW_COLS]
        for rid, rec in plan.items():
            sets = {c: rec.get(c, "") for c in cols}
            if rec["new_availability"]:
                sets["availability"] = rec["new_availability"]
            sql = ("UPDATE api_functions SET " + ", ".join(f"{k}=:{k}" for k in sets) + " WHERE id=:__id")
            con.execute(sql, {**sets, "__id": rid})
        con.commit()
        con.execute("VACUUM")
    chk = dict(Counter(r[0] for r in con.execute("select verify_status from api_functions"))) if apply else {}
    navail = con.execute("select count(*) from api_functions where corrected_from<>''").fetchone()[0] if apply else 0
    con.close()

    # ---------------- 写 api_enhanced.json ----------------
    J = json.loads(JSONF.read_text(encoding="utf-8-sig"))
    jstats = Counter()
    touched = 0
    for oname, o in J["objects"].items():
        if not isinstance(o, dict):
            continue
        for fk, f in o.items():
            if not isinstance(f, dict):
                continue
            rid = f.get("id")
            rec = plan.get(rid)
            if not rec:
                jstats["无对应sqlite行"] += 1
                continue
            touched += 1
            f["runtimeGP"] = rec["runtime_gp"]
            f["runtimeUI"] = rec["runtime_ui"]
            if rec["verify_status"] == "已核验":
                f["humanChecked"] = True
                f["verifiedAt"] = TODAY
                f["verifiedScope"] = rec["verify_scope"]
                if rec["corrected_from"]:
                    f["availabilityCorrectedFrom"] = rec["corrected_from"]
                    if apply and rec["new_availability"]:
                        f["availability"] = rec["new_availability"]
                if rec["true_path"]:
                    f["truePath"] = rec["true_path"]
                if rec["true_name"]:
                    f["trueName"] = rec["true_name"]
                note = "[核验] " + rec["verify_note"]
                jstats["humanChecked=true"] += 1
            elif rec["verify_status"] == "存疑":
                f["suspect"] = True
                f["suspectType"] = rec["suspect_type"]
                f["suspectPriority"] = rec["audit_priority"]
                note = "[存疑] " + rec["verify_note"]
                jstats["suspect=true"] += 1
            else:
                f["pendingTest"] = True
                f["pendingReason"] = rec.get("pending_reason", "")
                note = ""      # 无法实测：不挂核验/存疑标记，也不加提示行
                jstats["pendingTest=true(标记留空)"] += 1
            if apply and note:
                notes = f.get("notes")
                if not isinstance(notes, list):
                    notes = [notes] if notes else []
                notes = [x for x in notes if not (isinstance(x, str) and x.startswith(("[核验]", "[存疑]")))]
                notes.append(note)
                f["notes"] = notes
            # 助手原有人工验证结论留痕
            if rid in hj:
                f["helperHumanChecked"] = True
                f["helperAvailability"] = hj[rid].get("availability", "")
                jstats["助手原人工验证"] += 1
    if apply:
        J.setdefault("metadata", {})["verification"] = {
            "method": "FireTuner 运行时存在性验证（GP=GameCore_Tuner / UI=InGame，只索引不调用）",
            "date": TODAY,
            "fields": {
                "humanChecked": "本次实测过关（含 P1 已修正）——助手「人工核查」标记",
                "suspect": "本次查出文档自身有误（availability 标错 / 名称路径错 / 运行时确无此名 / 文档转储），仅标记不删除",
                "pendingTest": "本次无法实测（缺实例通道或动态事件代理），核验与嫌疑标记均留空",
                "runtimeGP/runtimeUI": "实测取到的运行时类型（function/table/userdata/string/nil/ERR/CF）",
                "verifiedScope": "实测范围：双端 / 仅GP / 仅UI / 双端未见 / 含不可判",
                "availabilityCorrectedFrom": "P1 实装修正前的 availability 原值",
                "trueName/truePath": "文档名有误时的运行时真名/真身路径",
            },
            "counts": dict(jstats),
            "report": str(DEST / "API范围验证报告.md"),
        }
        JSONF.write_bytes(json.dumps(J, ensure_ascii=False, indent=2).encode("utf-8"))

    # ---------------- 删除既有备份 ----------------
    removed = []
    if apply:
        for b in BACKUPS:
            if b.exists():
                b.unlink()
                removed.append(b.name)

    out = {"计划标记统计": dict(stats), "sqlite回填后verify_status": chk,
           "sqlite实装修正availability行数": navail,
           "json触达条目": touched, "json标记统计": dict(jstats),
           "已删除备份": removed, "安全副本目录": str(SAFE), "apply": apply}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    (WORK / "out" / "install_plan.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return plan


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(apply="--apply" in sys.argv)
