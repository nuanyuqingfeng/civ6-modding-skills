#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clash Verge proxy node tester/selector for Civ6 Steam Workshop uploads.

Uses the same named-pipe API as Clash Verge's UI.
Selects the lowest-latency responsive node to steamcommunity.com.
"""
import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

HELPER = Path(__file__).with_name("clash_api.ps1")
RAW = Path(tempfile.gettempdir()) / "civ6_skill_clash_raw_response.txt"


def clash(method: str, path: str, body: str = None):
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(HELPER), "-Method", method, "-Path", path, "-OutFile", str(RAW),
    ]
    if body is not None:
        cmd += ["-Body", body]
    subprocess.run(cmd, check=True, capture_output=True)
    raw = RAW.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
    if "\n\n" in raw:
        head, body_text = raw.split("\n\n", 1)
    else:
        head, body_text = raw, ""
    if "transfer-encoding: chunked" in head.lower():
        decoded = b""
        data = body_text.encode("utf-8")
        pos = 0
        while pos < len(data):
            line_end = data.find(b"\n", pos)
            if line_end == -1:
                break
            size_str = data[pos:line_end].strip().split(b";")[0]
            try:
                size = int(size_str, 16)
            except ValueError:
                break
            pos = line_end + 1
            if size == 0:
                break
            decoded += data[pos:pos + size]
            pos += size
            if data[pos:pos + 2] == b"\r\n":
                pos += 2
            elif data[pos:pos + 1] == b"\n":
                pos += 1
        body_text = decoded.decode("utf-8", errors="replace")
    return head, body_text


def get_proxies():
    head, body = clash("GET", "/proxies")
    if "200 OK" not in head:
        raise RuntimeError(f"Clash API error: {head.splitlines()[0] if head else 'empty'}")
    return json.loads(body)["proxies"]


def test_delay(name: str, url: str, timeout_ms: int = 3000):
    path = (
        "/proxies/" + urllib.parse.quote(name, safe="")
        + "/delay?url=" + urllib.parse.quote(url, safe="")
        + f"&timeout={timeout_ms}"
    )
    head, body = clash("GET", path)
    if "200 OK" in head:
        try:
            return name, json.loads(body).get("delay")
        except Exception:
            return name, None
    return name, None


def select_node(name: str):
    body = json.dumps({"name": name}, ensure_ascii=True)
    head, resp = clash("PUT", "/proxies/GLOBAL", body=body)
    if "204" not in head:
        raise RuntimeError(f"Failed to select node {name!r}: {head} {resp}")
    _, gbody = clash("GET", "/proxies/GLOBAL")
    return json.loads(gbody).get("now")


def main():
    parser = argparse.ArgumentParser(description="Test Clash nodes and select best for Steam upload")
    parser.add_argument("--url", default="https://steamcommunity.com/sharedfiles/filedetails/?id=<你的工坊条目 ID>",
                        help="Steam URL to test latency against")
    parser.add_argument("--timeout", type=int, default=3000, help="per-node delay timeout ms")
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--select", action="store_true", default=True,
                        help="select the best node in GLOBAL selector")
    args = parser.parse_args()

    proxies = get_proxies()
    skip_types = {"Selector", "URLTest", "Fallback", "Direct", "Compatible", "Pass", "Reject", "RejectDrop"}
    nodes = {n: i for n, i in proxies.items() if i.get("type") not in skip_types}
    # skip subscription info pseudo-nodes
    nodes = {n: i for n, i in nodes.items() if "剩余流量" not in n and "套餐到期" not in n}

    print(f"Testing {len(nodes)} nodes against {args.url}")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = {ex.submit(test_delay, name, args.url, args.timeout): name for name in nodes}
        for fut in concurrent.futures.as_completed(futures):
            name, delay = fut.result()
            results[name] = delay

    ok = {k: v for k, v in results.items() if v is not None}
    print(f"Responsive: {len(ok)}/{len(nodes)}")
    if not ok:
        print("No responsive node found.")
        sys.exit(2)

    best = min(ok, key=ok.get)
    print("Best node:", json.dumps(best, ensure_ascii=True), "delay:", ok[best])

    if args.select:
        now = select_node(best)
        print("GLOBAL now:", json.dumps(now, ensure_ascii=True))

    # save results for inspection
    out = Path(tempfile.gettempdir()) / "civ6_skill_clash_delay_results.json"
    out.write_text(json.dumps(results, ensure_ascii=True, indent=2), encoding="utf-8")
    print("Results saved to", out)


if __name__ == "__main__":
    main()
