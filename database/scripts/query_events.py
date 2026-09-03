#!/usr/bin/env python3
"""Civ6 Event Query Tool — 直接查 events_enhanced.json，无需中间索引。"""

import argparse, json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
JSON_PATH = os.path.join(SKILL_ROOT, "reference", "events_enhanced.json")


def _load_events():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)["events"]


def search_events(events, keyword, system=None):
    kw = keyword.lower()
    results = []
    for ev in events:
        name = ev.get("eventName", "")
        if kw in name.lower():
            if system and ev.get("eventSystem") != system:
                continue
            results.append(ev)
    return results


def find_event(events, exact_name):
    for ev in events:
        if ev.get("eventName") == exact_name:
            return ev
    return None


def print_list(results):
    if not results:
        print("No events found.")
        return
    print(f"{'Event Name':45s} {'System':18s} {'Type':20s}")
    print("-" * 85)
    for ev in results:
        print(f"{ev.get('eventName',''):45s} {ev.get('eventSystem',''):18s} {ev.get('eventType','') or '':20s}")
    print(f"\n{len(results)} result(s). Use --show <ExactName> for full detail.")


def print_detail(ev):
    print(f"\n{'='*60}")
    print(f"  {ev.get('eventName', '?')}")
    print(f"{'='*60}")
    print(f"  System:       {ev.get('eventSystem', '?')}")
    print(f"  Type:         {ev.get('eventType', '?')}")
    print(f"  Category:     {ev.get('category', '?')}")
    print(f"  Availability: {ev.get('availability', '?')}")
    print()

    sig = ev.get("callbackSignature")
    if sig:
        print(f"  Signature:    {sig}\n")

    params = ev.get("callbackParams")
    if params:
        print("  Parameters:")
        for p in params:
            pname = p.get("name", "?")
            ptype = p.get("type", "?")
            pdesc = p.get("description", "")
            print(f"    {pname}: {ptype}  {pdesc}")
        print()

    example = ev.get("exampleCode")
    if example:
        print("  Example:")
        for line in example.split("\n"):
            print(f"    {line}")
        print()

    notes = ev.get("notes")
    if notes:
        print(f"  Notes: {notes}\n")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Civ6 Event Query Tool")
    parser.add_argument("--search", "-s", help="Search event by name keyword")
    parser.add_argument("--show", "-S", help="Show full detail of exact event name")
    parser.add_argument("--system", "-sys",
                        choices=["Events.", "GameEvents.", "LuaEvents."],
                        help="Filter by event system")
    args = parser.parse_args()

    if not args.search and not args.show:
        parser.print_help()
        return

    events = _load_events()

    if args.search:
        results = search_events(events, args.search, args.system)
        print_list(results)

    if args.show:
        ev = find_event(events, args.show)
        if ev:
            print_detail(ev)
        else:
            print(f"Event '{args.show}' not found. Use --search to find similar names.")


if __name__ == "__main__":
    main()
