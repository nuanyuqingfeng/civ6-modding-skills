#!/usr/bin/env python3
"""Civ6 API Query Tool — 直接查 api_enhanced.json，按函数名/对象/类型搜索。"""

import argparse, json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
JSON_PATH = os.path.join(SKILL_ROOT, "reference", "api_enhanced.json")


def _load():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)["objects"]


def verify_tag(m):
    """核验标记：已核验(humanChecked) / 存疑(suspect) / 待补测(pendingTest) / 空。"""
    if m.get("humanChecked"):
        return "已核验"
    if m.get("suspect"):
        return "存疑"
    if m.get("pendingTest"):
        return "待补测"
    return ""


def match_verify(m, verify):
    if not verify:
        return True
    return verify_tag(m) == {"verified": "已核验", "suspect": "存疑", "pending": "待补测"}[verify]


def search(objs, keyword, type_filter=None, verify=None):
    kw = keyword.lower()
    results = []
    for obj_name, methods in objs.items():
        for mid, m in methods.items():
            if not isinstance(m, dict):
                continue
            if type_filter and m.get("type") != type_filter:
                continue
            if not match_verify(m, verify):
                continue
            name = m.get("functionA", "")
            if kw in name.lower() or kw in mid.lower():
                results.append((obj_name, mid, m))
    return results


def get_detail(objs, obj_name, func_name):
    obj = objs.get(obj_name)
    if not obj:
        return None
    # search by functionA or by method id
    for mid, m in obj.items():
        if not isinstance(m, dict):
            continue
        if m.get("functionA") == func_name or mid.endswith(func_name):
            return m
    return None


def list_object(objs, obj_name):
    obj = objs.get(obj_name)
    if not obj:
        return []
    return [(mid, m) for mid, m in obj.items() if isinstance(m, dict)]


def print_list(results):
    if not results:
        print("No results.")
        return
    print(f"{'Object':22s} {'Function':30s} {'Type':10s} {'Availability':15s} {'核验':8s}")
    print("-" * 90)
    for obj_name, mid, m in results:
        func = m.get("functionA", "")
        typ = m.get("type", "")
        avail = m.get("availability", "")
        if m.get("availabilityCorrectedFrom"):
            avail += f"(原{m['availabilityCorrectedFrom']})"
        print(f"{obj_name:22s} {func:30s} {typ:10s} {avail:15s} {verify_tag(m):8s}")
    print(f"\n{len(results)} result(s). Use --show <Object>.<Func> for detail.")


def print_detail(obj_name, func_name, m):
    print(f"\n{'='*60}")
    print(f"  {obj_name}.{func_name}")
    print(f"{'='*60}")
    print(f"  Table:       {m.get('table', '')}")
    print(f"  Type:        {m.get('type', '')}")
    print(f"  Availability: {m.get('availability', '')}")
    print()

    sig = m.get("signature")
    if sig:
        print(f"  Signature:   {sig}\n")

    invoke = m.get("invoke")
    if invoke:
        print(f"  Invoke:      {invoke}")
        inv_note = m.get("invokeNote")
        if inv_note:
            print(f"  Invoke Note: {inv_note}")
        print()

    args = m.get("argsA")
    if args:
        print(f"  Args:        {args}\n")

    returns = m.get("returns")
    if returns:
        print(f"  Returns:     {returns}\n")

    example = m.get("exampleCode")
    if example:
        print("  Example:")
        for line in example.split("\n"):
            print(f"    {line}")
        print()

    # ---- 运行时核验（2026-09-08 FireTuner 全量实测）----
    tag = verify_tag(m)
    if tag or m.get("runtimeGP") or m.get("runtimeUI"):
        print("  Verification:")
        print(f"    状态:      {tag or '（未标记）'}")
        if m.get("verifiedAt"):
            print(f"    核验日期:  {m['verifiedAt']}   范围: {m.get('verifiedScope', '')}")
        print(f"    实测类型:  GP={m.get('runtimeGP', '-')}  UI={m.get('runtimeUI', '-')}")
        if m.get("availabilityCorrectedFrom"):
            print(f"    已修正:    availability {m['availabilityCorrectedFrom']} -> {m.get('availability')}")
        if m.get("trueName"):
            print(f"    运行时真名: {m['trueName']}")
        if m.get("truePath"):
            print(f"    运行时真身: {m['truePath']}")
        if m.get("suspectType"):
            print(f"    存疑类型:  {m['suspectType']}（优先级 {m.get('suspectPriority', '')}）")
        if m.get("pendingReason"):
            print(f"    待补测:    {m['pendingReason']}")
        if m.get("helperHumanChecked"):
            print(f"    助手人工验证: 是（Civ6LuaHelper availability={m.get('helperAvailability', '')}）")
        print()

    notes = m.get("notes")
    if notes:
        for line in notes:
            print(f"  Note:        {line}")
        print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Civ6 API Query Tool")
    parser.add_argument("--search", "-s", help="Search functions by keyword")
    parser.add_argument("--show", "-S", help="Show detail: Object.FuncName")
    parser.add_argument("--object", "-o", help="List all functions of an object")
    parser.add_argument("--type", "-t", choices=["ACTION", "QUERY", "CONTEXT", "OBJECT"],
                        help="Filter by type (with --search)")
    parser.add_argument("--limit", "-l", type=int, default=30)
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--verified", action="store_const", const="verified", dest="verify_filter",
                   help="只看已核验（humanChecked，实测过关/已修正）")
    g.add_argument("--suspect", action="store_const", const="suspect", dest="verify_filter",
                   help="只看存疑（文档自身有误：availability/名称/路径/确无此名/文档转储）")
    g.add_argument("--pending", action="store_const", const="pending", dest="verify_filter",
                   help="只看待补测（本次无法实测，标记留空）")
    args = parser.parse_args()

    if not any([args.search, args.show, args.object]):
        parser.print_help()
        return

    objs = _load()

    if args.search:
        results = search(objs, args.search, args.type, args.verify_filter)
        results.sort(key=lambda x: x[2].get("functionA", ""))
        print_list(results[:args.limit])

    if args.show:
        parts = args.show.split(".", 1)
        if len(parts) != 2:
            print("Use format: Object.FuncName  e.g. Game.GetLocalPlayer")
            return
        obj_name, func_name = parts
        m = get_detail(objs, obj_name, func_name)
        if not m:
            print(f"Not found: {args.show}. Use --search to find matching functions.")
            return
        print_detail(obj_name, func_name, m)

    if args.object:
        methods = list_object(objs, args.object)
        if not methods:
            print(f"Object '{args.object}' not found. Available objects:")
            for k in sorted(objs.keys()):
                print(f"  {k}")
            return
        print(f"\n=== {args.object} ({len(methods)} functions) ===")
        print(f"{'Function':35s} {'Type':10s} {'Availability':15s} {'核验':8s}")
        print("-" * 75)
        for mid, m in methods:
            if not match_verify(m, args.verify_filter):
                continue
            func = m.get("functionA", mid)
            typ = m.get("type", "")
            avail = m.get("availability", "")
            print(f"{func:35s} {typ:10s} {avail:15s} {verify_tag(m):8s}")


if __name__ == "__main__":
    main()
