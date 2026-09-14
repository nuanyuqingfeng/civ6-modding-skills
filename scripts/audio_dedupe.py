# -*- coding: utf-8 -*-
"""
audio_dedupe.py -- 跨目录音频指纹查重: 同曲判定 -> 组内质量排序 -> 淘汰件备份隔离(默认只报告)
指纹: 24 对数频带 × 64 时间片能量谱(fp) + 响度包络相关(env) + 时长比。
判同(自动): fp>=0.975 且 env>=0.985 且 时长比>=0.99 (本地 129 文件/32 对判同实证;
            校验基准: 同母带跨封装 fp>=0.977, 同曲不同混音/昼夜变体 fp<=0.99 且 env<=0.97)。
守卫: 名称一边含 伴奏/instrumental/inst 而另一边不含 -> 即使高相似也只进疑似清单(人声/伴奏是不同曲)。
质量排序(高者留): 无损>有损 -> 采样率 -> 位深 -> 时长 -> --prefer 子串匹配方(如可辨认的网易云曲名)。
用法:
  python audio_dedupe.py <文件或目录...> [--auto 0.975 --env 0.985 --dur 0.99]
      [--prefer 子串] [--quarantine DIR] [--cache DIR] [--jobs 4] [--report PATH]
  默认只报告不移动; --quarantine DIR 才把淘汰件移入(备份隔离, 禁止直接删除)。
  --cache DIR 逐文件指纹缓存(mtime+size 键), 重跑免解码。
"""
import os, sys, json, csv, argparse, subprocess, shutil
from concurrent.futures import ThreadPoolExecutor

try:
    import numpy as np
except ImportError:
    raise SystemExit(
        '[FAIL] 缺少 numpy。请先执行: pip install numpy'
    )

SR = 22050
NFFT = 2048
HOP = 512
BANDS = 24
SLICES = 64
AUDIO_EXT = (".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".opus")
INSTR_TOKENS = ("伴奏", "instrumental", "inst")

BAND_EDGES = np.geomspace(40.0, min(11000.0, SR / 2 - 100), BANDS + 1)
FREQS = np.fft.rfftfreq(NFFT, 1.0 / SR)
BAND_IDX = [np.where((FREQS >= BAND_EDGES[b]) & (FREQS < BAND_EDGES[b + 1]))[0] for b in range(BANDS)]


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(AUDIO_EXT))
        elif os.path.isfile(p):
            out.append(p)
    return out


def ffprobe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    d = json.loads(r.stdout or "{}")
    st = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not st:
        return None
    dur = float(st.get("duration") or d.get("format", {}).get("duration") or 0)
    return dict(codec=st.get("codec_name"), sr=int(st.get("sample_rate") or 0),
                ch=int(st.get("channels") or 0), dur=dur,
                bits=int(st.get("bits_per_raw_sample") or st.get("bits_per_sample") or 0))


def decode_mono(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, timeout=600)
    if r.returncode != 0 or not r.stdout:
        raise RuntimeError("decode fail: " + r.stderr.decode("utf-8", "replace")[:200])
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def fingerprint(x):
    """返回 (fp 指纹向量, env 响度包络, dur)"""
    n = len(x)
    nfr = max(1, (n - NFFT) // HOP)
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(nfr)[:, None]
    frames = x[idx] * np.hanning(NFFT).astype(np.float32)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    band = np.empty((nfr, BANDS), np.float32)
    for b in range(BANDS):
        band[:, b] = mag[:, BAND_IDX[b]].mean(axis=1)
    logb = np.log10(band + 1e-6)
    prof = np.zeros((SLICES, BANDS), np.float32)
    for i, s in enumerate(np.array_split(np.arange(nfr), min(SLICES, nfr))):
        if len(s):
            p = logb[s].mean(axis=0)
            prof[i] = p - np.median(p)
    fp = prof.flatten()
    fp /= (np.linalg.norm(fp) + 1e-9)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    env = np.interp(np.linspace(0, nfr - 1, 128), np.arange(nfr), np.log10(rms + 1e-9))
    env -= env.mean()
    env /= (np.linalg.norm(env) + 1e-9)
    return fp, env, n / SR


def lossless(meta):
    return 1 if (meta["codec"] or "") == "flac" or (meta["codec"] or "").startswith("pcm") else 0


def rank_key(meta, prefer):
    return (lossless(meta), meta["sr"], meta["bits"] or 0, round(meta["dur"], 1),
            1 if prefer and prefer in os.path.basename(meta["path"]) else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--auto", type=float, default=0.975)
    ap.add_argument("--env", type=float, default=0.985)
    ap.add_argument("--dur", type=float, default=0.99)
    ap.add_argument("--suspect", type=float, default=0.90, help="疑似关联对报告阈值(fp)")
    ap.add_argument("--prefer", default=None, help="质量平局时优先保留文件名含此子串的一方")
    ap.add_argument("--quarantine", default=None, help="淘汰件移入此目录(备份隔离); 缺省只报告")
    ap.add_argument("--cache", default=None)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    if not (shutil.which('ffprobe') and shutil.which('ffmpeg')):
        raise SystemExit('[FAIL] 未找到 ffprobe/ffmpeg，请先安装 FFmpeg 并加入 PATH 后重试。')

    files = collect(a.paths)
    if not files:
        raise SystemExit("没有找到音频文件")
    print("[DEDUPE] %d 个文件 | 阈值 fp>=%.3f env>=%.3f dur>=%.2f" % (len(files), a.auto, a.env, a.dur))

    metas, fps, envs = [], [], []
    cache = {}
    if a.cache:
        os.makedirs(a.cache, exist_ok=True)

    def _one(path):
        key = "%s_%d_%d.json" % (os.path.basename(path)[:80].replace("#", "_"),
                                 int(os.path.getmtime(path)), os.path.getsize(path))
        cpath = os.path.join(a.cache, key) if a.cache else None
        if cpath and os.path.exists(cpath):
            c = json.load(open(cpath, encoding="utf-8"))
            meta, fp, env = c["meta"], np.array(c["fp"], np.float32), np.array(c["env"], np.float32)
        else:
            meta = ffprobe(path)
            if not meta:
                return None
            fp, env, dur = fingerprint(decode_mono(path))
            meta["dur"] = dur
            if cpath:
                json.dump(dict(meta=meta, fp=fp.tolist(), env=env.tolist()), open(cpath, "w", encoding="utf-8"))
        return path, meta, fp, env

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        for r in ex.map(_one, files):
            if r is None:
                print("  [FAIL] 无法解析(跳过)")
                continue
            path, meta, fp, env = r
            meta["path"] = path
            metas.append(meta)
            fps.append(fp)
            envs.append(env)

    n = len(metas)
    if n < 2:
        raise SystemExit("有效文件不足 2 个")
    F, E = np.vstack(fps), np.vstack(envs)
    S_fp, S_env = F @ F.T, E @ E.T
    durs = np.array([m["dur"] for m in metas])

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    auto_pairs, suspect = [], []
    for i in range(n):
        for j in range(i + 1, n):
            fp_s, env_s = float(S_fp[i, j]), float(S_env[i, j])
            if fp_s < 0.75 and env_s < max(a.env, 0.95):
                continue
            ratio = min(durs[i], durs[j]) / max(durs[i], durs[j])
            ni, nj = os.path.basename(metas[i]["path"]), os.path.basename(metas[j]["path"])
            inst_i = any(t in ni.lower() for t in INSTR_TOKENS)
            inst_j = any(t in nj.lower() for t in INSTR_TOKENS)
            if inst_i != inst_j:
                if fp_s >= a.suspect:
                    suspect.append((fp_s, env_s, ratio, ni, nj, "人声/伴奏差异"))
                continue
            if fp_s >= a.auto and env_s >= a.env and ratio >= a.dur:
                parent[find(i)] = find(j)
                auto_pairs.append((fp_s, env_s, ratio, ni, nj))
            elif fp_s >= a.suspect:
                suspect.append((fp_s, env_s, ratio, ni, nj, "同曲不同混音/分轨?"))

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    moves = []
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda i: rank_key(metas[i], a.prefer), reverse=True)
        for lo in members[1:]:
            moves.append((os.path.basename(metas[lo]["path"]), os.path.basename(metas[members[0]]["path"]),
                          metas[lo]["path"]))

    for s, e, r, x, y in sorted(auto_pairs, key=lambda p: -p[0]):
        print("  [同曲] fp=%.3f env=%.3f dur=%.2f | %s == %s" % (s, e, r, x, y))
    for s, e, r, x, y, why in sorted(suspect, key=lambda p: -p[0]):
        print("  [疑似] fp=%.3f env=%.3f dur=%.2f | %s || %s (%s)" % (s, e, r, x, y, why))
    for lo, keep, _ in moves:
        print("  [淘汰] %s  ->  保留 %s" % (lo, keep))
    print("[DEDUPE] 判同 %d 对, 淘汰 %d 个, 疑似 %d 对%s" % (
        len(auto_pairs), len(moves), len(suspect),
        (" -> " + a.quarantine if moves and a.quarantine else "")))

    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write("[audio_dedupe] %d 文件 | 阈值 fp>=%.3f env>=%.3f dur>=%.2f | prefer=%s\n\n"
                    % (n, a.auto, a.env, a.dur, a.prefer))
            for lo, keep, _ in moves:
                f.write("[淘汰] %s -> 保留 %s\n" % (lo, keep))
            for s, e, r, x, y, why in suspect:
                f.write("[疑似] fp=%.3f env=%.3f dur=%.2f | %s || %s (%s)\n" % (s, e, r, x, y, why))
        print("[DEDUPE] 报告 -> %s" % a.report)

    if moves and a.quarantine:
        os.makedirs(a.quarantine, exist_ok=True)
        moved = 0
        for _, _, p in moves:
            dst = os.path.join(a.quarantine, os.path.basename(p))
            if os.path.exists(p) and not os.path.exists(dst):
                shutil.move(p, dst)
                moved += 1
        print("[DEDUPE] 已隔离 %d 个 -> %s (未删除)" % (moved, a.quarantine))


if __name__ == "__main__":
    main()
