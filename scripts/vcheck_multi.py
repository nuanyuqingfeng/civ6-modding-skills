"""vcheck_multi.py — 多图视觉复核：把若干 PNG 一起丢给 Gemini 问一个问题

用法:
  python vcheck_multi.py "<问题>" <图片1.png> [图片2.png ...]
                         [--api-key KEY] [--proxy URL] [--model M] [--endpoint URL]

凭据与网络（按序解析，别人机器无需作者的私有文件）:
  key    --api-key  →  $GOOGLE_API_KEY  →  $GEMINI_API_KEY  →  ~/.local/share/opencode/auth.json 的 google.key
  proxy  --proxy    →  $HTTPS_PROXY（或 https_proxy / $HTTP_PROXY）→  作者示例默认值 http://127.0.0.1:7897
         --proxy none（或空串）表示直连、不走代理
"""
import json, os, sys, base64, urllib.request, urllib.error

DEFAULT_PROXY = "http://127.0.0.1:7897"   # 作者本机示例值；用 --proxy 或 HTTPS_PROXY 覆盖
DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
AUTH_JSON = os.path.expanduser("~/.local/share/opencode/auth.json")

_USAGE = __doc__


def _die(msg, code=2):
    sys.stderr.write("[错误] " + msg + "\n")
    raise SystemExit(code)


def parse_args(argv):
    """位置参数语义不变：第一个是问题，其余是图片；--xxx 为新增覆盖项。"""
    opts = {"api_key": None, "proxy": None, "model": None, "endpoint": None}
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(_USAGE)
            raise SystemExit(0)
        if a.startswith("--"):
            name, eq, inline = a[2:].partition("=")
            key = {"api-key": "api_key", "key": "api_key",
                   "proxy": "proxy", "model": "model", "endpoint": "endpoint"}.get(name)
            if key is None:
                _die("未知参数 %s（-h 看用法）" % a)
            if eq:
                opts[key] = inline
            else:
                i += 1
                if i >= len(argv):
                    _die("参数 %s 缺少取值" % a)
                opts[key] = argv[i]
        else:
            positional.append(a)
        i += 1
    return opts, positional


def resolve_key(cli_key):
    """CLI → 环境变量 → 原 auth.json；三处都没有则明确报错。"""
    if cli_key:
        return cli_key
    for env in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        v = os.environ.get(env)
        if v:
            return v
    try:
        with open(AUTH_JSON, encoding="utf-8") as f:
            k = (json.load(f).get("google") or {}).get("key")
        if k:
            return k
    except Exception:
        pass
    _die("拿不到 Google Gemini API key。三种提供方式任选其一：\n"
         "    1) 命令行：   --api-key <KEY>\n"
         "    2) 环境变量： GOOGLE_API_KEY=<KEY>（或 GEMINI_API_KEY=<KEY>）\n"
         "    3) 配置文件： %s 内写 {\"google\": {\"key\": \"<KEY>\"}}\n"
         "  （该文件是作者私有凭据，不随 skill 分发，别人机器上通常不存在）" % AUTH_JSON)


def resolve_proxy(cli_proxy):
    """CLI → HTTPS_PROXY/HTTP_PROXY → 作者示例默认值；none/空串 = 直连。"""
    if cli_proxy is not None:
        p = cli_proxy.strip()
        return None if p.lower() in ("", "none", "off", "-") else p
    for env in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        v = os.environ.get(env)
        if v:
            return v
    return DEFAULT_PROXY


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    opts, positional = parse_args(sys.argv[1:])
    if not positional:
        _die("缺少问题文本（第一个位置参数）。-h 看用法")
    q = positional[0]
    images = positional[1:]

    key = resolve_key(opts["api_key"])
    proxy = resolve_proxy(opts["proxy"])
    model = opts["model"] or DEFAULT_MODEL
    endpoint = opts["endpoint"] or DEFAULT_ENDPOINT.format(model=model)

    parts = [{"text": q}]
    for p in images:
        b64 = base64.b64encode(open(p, 'rb').read()).decode()
        parts.append({"text": f"[图片{sys.argv.index(p)}: {p}]"})
        parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})
    body = json.dumps({"contents": [{"parts": parts}],
                       "generationConfig": {"temperature": 0.2}}).encode()
    if proxy:
        handler = urllib.request.ProxyHandler({"https": proxy, "http": proxy})
    else:
        handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(handler)
    req = urllib.request.Request(
        f"{endpoint}?key={key}",
        data=body, headers={"Content-Type": "application/json"})
    try:
        r = json.load(opener.open(req, timeout=120))
    except urllib.error.HTTPError as e:
        _die("Gemini 接口返回 HTTP %s：%s"
             % (e.code, e.read()[:500].decode("utf-8", "replace")), code=1)
    except Exception as e:
        _die("请求 Gemini 失败：%s\n  当前代理=%s（作者示例默认值；可用 --proxy <URL> 覆盖，"
             "--proxy none 直连）" % (e, proxy or "直连"), code=1)
    print(r["candidates"][0]["content"]["parts"][0]["text"])


if __name__ == "__main__":
    main()
