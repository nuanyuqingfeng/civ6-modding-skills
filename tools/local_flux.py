# -*- coding: utf-8 -*-
"""本地 FLUX.2-klein-4B 文生图封装（免费、离线、约 8–30s/张）。

用途：工坊封面底图与徽记、一般风格插图。**不适合图标** —— 图标走
`make-icon.ps1`（白色扁平剪影 + 阈值后处理）。

已知边界（实测）：
  · **中文/日文字形不可用** —— 扩散模型渲染出的是形近伪字（"人类玩家" → "义凵薊…"）。
    需要中文文字的成品（如工坊封面）必须走「模型出底图 + PIL 确定性排版」两步，
    见 `workshop_cover.py`。
  · 拉丁文可以出，但长句会掉字母（`CIVILIZATION` → `CIVILLZATION`），仍需人工核对。

用法：
    python local_flux.py --prompt "..." --out x.png [--seed 42] [--size 1024]
    python local_flux.py --prompt-file p.txt --out x.png --seeds 42,7,123   # 多 seed 取样挑图

退出码：0 成功 / 1 失败
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MODEL_DIR_NAME = "flux2-klein4b"
MODEL_FILES = ("flux-2-klein-4b-Q4_0.gguf", "vae_small_decoder.safetensors", "qwen3-4b-Q4_K_M.gguf")


def gen(prompt: str, out: str, seed: int, size: int, steps: int = 4) -> bool:
    sd = _paths.require_tool("sd_cpp")
    models = os.path.join(sd, "models", MODEL_DIR_NAME)
    missing = [f for f in MODEL_FILES if not os.path.isfile(os.path.join(models, f))]
    if missing:
        print("FAIL 模型文件缺失（%s）：%s" % (models, missing))
        return False
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [
        os.path.join(sd, "sd-cli.exe"),
        "--diffusion-model", os.path.join(models, MODEL_FILES[0]),
        "--vae", os.path.join(models, MODEL_FILES[1]),
        "--llm", os.path.join(models, MODEL_FILES[2]),
        "-p", prompt,
        "--cfg-scale", "1.0", "--steps", str(steps),
        "-H", str(size), "-W", str(size),
        "--diffusion-fa", "--offload-to-cpu",
        "--seed", str(seed),
        "-o", out,
    ]
    r = subprocess.run(cmd, capture_output=True, cwd=sd)
    if not os.path.isfile(out):
        tail = r.stdout.decode("utf-8", "replace").strip().splitlines()[-6:]
        print("FAIL seed=%d 生成失败\n%s\n%s" % (seed, "\n".join(tail),
                                                 r.stderr.decode("utf-8", "replace")[-800:]))
        return False
    print("OK   %s  %d B  (seed=%d)" % (out, os.path.getsize(out), seed))
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="本地 FLUX 文生图封装")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--prompt-file", default=None, help="从 UTF-8 文件读提示词")
    ap.add_argument("--out", required=True, help="输出 PNG；多 seed 时自动插入 _<seed> 后缀")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--seeds", default=None, help="逗号分隔的多个 seed（取样挑图）")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--steps", type=int, default=4)
    args = ap.parse_args()

    prompt = open(args.prompt_file, encoding="utf-8").read().strip() if args.prompt_file else args.prompt
    if not prompt:
        raise SystemExit("必须给 --prompt 或 --prompt-file")

    if args.seeds:
        ok = True
        stem, ext = os.path.splitext(args.out)
        for s in [int(x) for x in args.seeds.split(",") if x.strip()]:
            ok = gen(prompt, "%s_%d%s" % (stem, s, ext), s, args.size, args.steps) and ok
        return 0 if ok else 1
    return 0 if gen(prompt, args.out, args.seed, args.size, args.steps) else 1


if __name__ == "__main__":
    sys.exit(main())
