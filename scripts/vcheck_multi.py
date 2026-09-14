import json, os, sys, base64, urllib.request
key = json.load(open(os.path.expanduser("~/.local/share/opencode/auth.json")))["google"]["key"]
q = sys.argv[1]
parts = [{"text": q}]
for p in sys.argv[2:]:
    b64 = base64.b64encode(open(p,'rb').read()).decode()
    parts.append({"text": f"[图片{sys.argv.index(p)}: {p}]"})
    parts.append({"inline_data":{"mime_type":"image/png","data":b64}})
body = json.dumps({"contents":[{"parts":parts}],"generationConfig":{"temperature":0.2}}).encode()
proxy = urllib.request.ProxyHandler({"https":"http://127.0.0.1:7897","http":"http://127.0.0.1:7897"})
opener = urllib.request.build_opener(proxy)
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={key}",
    data=body, headers={"Content-Type":"application/json"})
r = json.load(opener.open(req, timeout=120))
print(r["candidates"][0]["content"]["parts"][0]["text"])
