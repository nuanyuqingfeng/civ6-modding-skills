# -*- coding: utf-8 -*-
"""工坊条目线上状态核对（Steam Web API，无需登录）。

比 `release/scripts/verify.ps1` 多查：归属账号（creator）、标题、描述、标签、预览图。
上传后用来确认「真的成功了」，以及确认**标题/标签/可见性没被顺带改掉**。

用法：
    python workshop_item_check.py 3801714971 [3800974286 ...]
    python workshop_item_check.py 3801714971 --expect-title "All Units Can Found Cities" --expect-public

已知限制（2026-09 实测）：
  · 接口忽略 `language` 参数，**只返回默认（english）变体**；非英语变体只能靠
    上传器日志里的 `Language variant 'x' updated.` + Steam 日志交叉验证。
  · `result=9` 不代表条目不存在（可能只是私有 / 不可匿名查询）。
  · 工坊页面已客户端渲染，抓 HTML 拿不到标题描述。

退出码：0 有结果 / 1 全部查不到 / 3 --expect-* 断言不通过
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
# Steam API 在部分网络下直连会被 reset，退回本机 Clash Verge 混合端口（release.md 有记录）
FALLBACK_PROXIES = ["http://127.0.0.1:7897", "http://127.0.0.1:7890"]
KNOWN_CREATORS = {
    "76561199127383393": "千与千寻瀑",
    "76561199122676977": "暖雨晴风",
}


def _opener(proxy: str | None):
    handler = urllib.request.ProxyHandler({"https": proxy, "http": proxy}) if proxy \
        else urllib.request.ProxyHandler({})
    return urllib.request.build_opener(handler)


def _fetch_once(ids: list[str], opener) -> list[dict]:
    body = urllib.parse.urlencode(
        [("itemcount", len(ids))] + [("publishedfileids[%d]" % i, v) for i, v in enumerate(ids)]
    ).encode()
    req = urllib.request.Request(API, data=body)
    with opener.open(req, timeout=60) as r:
        return json.load(r)["response"]["publishedfiledetails"]


def fetch(ids: list[str], proxy: str | None = None) -> list[dict]:
    """先直连，失败后自动回落代理（--proxy 可强制指定）。"""
    attempts = [proxy] if proxy else [None] + FALLBACK_PROXIES
    last = None
    for p in attempts:
        try:
            return _fetch_once(ids, _opener(p))
        except Exception as e:
            last = e
            print("  （%s 连接失败：%s）" % (p or "直连", str(e)[:80]), file=sys.stderr)
    raise SystemExit("Steam API 不可达，最后一次错误：%s" % last)


def main() -> int:
    ap = argparse.ArgumentParser(description="工坊条目线上状态核对")
    ap.add_argument("ids", nargs="+", help="工坊条目 ID")
    ap.add_argument("--expect-title", default=None, help="断言标题包含该子串")
    ap.add_argument("--expect-public", action="store_true", help="断言 visibility=0")
    ap.add_argument("--proxy", default=None, help="强制走该代理（默认先直连，失败自动回落 127.0.0.1:7897）")
    args = ap.parse_args()

    details = fetch(args.ids, args.proxy)
    found, failed = 0, 0
    asserts_ok = True
    for it in details:
        pid = it.get("publishedfileid")
        if it.get("result") != 1:
            print("== %s  查询失败 result=%s（可能私有 / 不存在 / 不可匿名查询）" % (pid, it.get("result")))
            failed += 1
            continue
        found += 1
        creator = it.get("creator") or ""
        print("== %s" % pid)
        print("   标题      : %s" % it.get("title"))
        print("   归属账号  : %s (%s)%s" % (KNOWN_CREATORS.get(creator, "未知账号"), creator,
                                            "" if creator in KNOWN_CREATORS else "   <== 未登记账号，建议补进本脚本 KNOWN_CREATORS 与台账"))
        print("   可见性    : %s (visibility=%s)" % ({0: "public", 1: "friends_only", 2: "private", 3: "unlisted"}
                                                     .get(it.get("visibility"), "?"), it.get("visibility")))
        print("   标签      : %s" % [t.get("tag") for t in (it.get("tags") or [])])
        print("   内容清单  : hcontent_file=%s" % it.get("hcontent_file"))
        print("   时间      : created=%s updated=%s" % (it.get("time_created"), it.get("time_updated")))
        desc = it.get("description") or ""
        print("   描述      : %d B" % len(desc.encode("utf-8")))
        print("   %s" % desc.replace("\n", "\n   "))
        print("   预览图    : %s" % (it.get("preview_url") or "(无)"))
        if args.expect_title and args.expect_title not in (it.get("title") or ""):
            print("   !! 断言失败：标题不含 %r" % args.expect_title)
            asserts_ok = False
        if args.expect_public and it.get("visibility") != 0:
            print("   !! 断言失败：visibility != 0")
            asserts_ok = False

    if not found:
        return 1
    return 0 if asserts_ok else 3


if __name__ == "__main__":
    sys.exit(main())
