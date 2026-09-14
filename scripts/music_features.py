# -*- coding: utf-8 -*-
"""
music_features.py -- BGM 音乐特征分析: BPM/响度/动态/亮度/打击密度 + 唤醒度评分
用途: 时代分区参考(引擎仅支持 Ancient/Medieval/Industrial/Atomic 四时代)、主题曲挑选、素材池概览。
唤醒度 = 0.40*z(BPM) + 0.30*z(RMS) + 0.15*z(打击密度) + 0.15*z(高频亮度)
        BPM 截断到 [50,170]; 自相关置信度低(<0.15, 多为氛围曲)者用批内中位数替代。
输出: 控制台按唤醒度升序清单 + --out CSV (含 quartile 四分位建议 1=远古..4=原子)。
用法:
  python music_features.py <文件或目录...> [--out features.csv] [--jobs 4] [--cache DIR]
特征均为客观信号量, 时代归属是参考建议而非裁定; 文件夹间人工微调不影响格式合规。
"""
import os, sys, csv, json, argparse, subprocess, shutil
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
AUDIO_EXT = (".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".opus")
BAND_EDGES = np.geomspace(40.0, min(11000.0, SR / 2 - 100), 25)
FREQS = np.fft.rfftfreq(NFFT, 1.0 / SR)


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(AUDIO_EXT))
        elif os.path.isfile(p):
            out.append(p)
    return out


def decode_mono(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, timeout=600)
    if r.returncode != 0 or not r.stdout:
        raise RuntimeError("decode fail: " + r.stderr.decode("utf-8", "replace")[:200])
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def features(x):
    n = len(x)
    nfr = max(1, (n - NFFT) // HOP)
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(nfr)[:, None]
    frames = x[idx] * np.hanning(NFFT).astype(np.float32)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    band = np.empty((nfr, len(BAND_EDGES) - 1), np.float32)
    for b in range(len(BAND_EDGES) - 1):
        sel = np.where((FREQS >= BAND_EDGES[b]) & (FREQS < BAND_EDGES[b + 1]))[0]
        band[:, b] = mag[:, sel].mean(axis=1)
    logb = np.log10(band + 1e-6)
    dlog = np.diff(logb, axis=0)
    flux = np.maximum(dlog, 0).sum(axis=1)  # 谱流 onset 包络
    flux -= flux.mean()
    autoc = np.correlate(flux, flux, "full")[len(flux) - 1:]
    autoc /= (autoc[0] + 1e-9)
    lag_lo, lag_hi = int(60.0 / 190 * SR / HOP), int(60.0 / 55 * SR / HOP)  # 55~190 BPM
    seg = autoc[lag_lo:lag_hi]
    bpm, conf = 0.0, 0.0
    if len(seg) > 2 and np.isfinite(seg).all():
        pk = int(np.argmax(seg))
        bpm = 60.0 * SR / HOP / (lag_lo + pk)
        conf = float(seg[pk])
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    frame_db = 20 * np.log10(rms + 1e-9)
    cent = (FREQS[None, :] * mag).sum(axis=1) / (mag.sum(axis=1) + 1e-9)
    return dict(
        bpm=round(float(bpm), 1), bpm_conf=round(conf, 3),
        rms_db=round(float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)), 2),
        dyn_db=round(float(np.percentile(frame_db, 90) - np.percentile(frame_db, 10)), 2),
        centroid_hz=round(float(np.exp(np.mean(np.log(cent + 1.0)))), 1),
        brightness=round(float(np.mean(mag[:, FREQS > 4000]) / (np.mean(mag[:, FREQS <= 4000]) + 1e-9)), 4),
        onset_density=round(float((flux > flux.std()).mean() * SR / HOP), 3),
        dur_sec=round(n / SR, 2),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default=None, help="CSV 输出路径")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--cache", default=None)
    a = ap.parse_args()
    if not shutil.which('ffmpeg'):
        raise SystemExit('[FAIL] 未找到 ffmpeg，请先安装 FFmpeg 并加入 PATH 后重试。')
    files = collect(a.paths)
    if not files:
        raise SystemExit("没有找到音频文件")
    print("[FEAT] %d 个文件" % len(files))
    cache = {}
    if a.cache:
        os.makedirs(a.cache, exist_ok=True)

    def _one(path):
        key = "%s_%d_%d.json" % (os.path.basename(path)[:80].replace("#", "_"),
                                 int(os.path.getmtime(path)), os.path.getsize(path))
        cpath = os.path.join(a.cache, key) if a.cache else None
        if cpath and os.path.exists(cpath):
            return path, json.load(open(cpath, encoding="utf-8"))
        ft = features(decode_mono(path))
        if cpath:
            json.dump(ft, open(cpath, "w", encoding="utf-8"))
        return path, ft

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        results = list(ex.map(_one, files))

    bpm = np.array([min(170.0, max(50.0, ft["bpm"])) for _, ft in results])
    conf = np.array([ft["bpm_conf"] for _, ft in results])
    med = float(np.median(bpm[conf >= 0.15])) if (conf >= 0.15).any() else float(np.median(bpm))
    bpm = np.where(conf < 0.15, med, bpm)
    rms = np.array([ft["rms_db"] for _, ft in results])
    onset = np.array([ft["onset_density"] for _, ft in results])
    bright = np.log10(np.array([ft["brightness"] + 1e-4 for _, ft in results]))

    def z(v):
        return (v - v.mean()) / (v.std() + 1e-9)

    arousal = 0.40 * z(bpm) + 0.30 * z(rms) + 0.15 * z(onset) + 0.15 * z(bright)
    order = np.argsort(arousal)
    quartile = np.empty(len(results), int)
    base, extra = divmod(len(results), 4)
    pos = 0
    for q in range(4):
        sz = base + (1 if q < extra else 0)
        quartile[order[pos:pos + sz]] = q + 1
        pos += sz

    labels = {1: "远古候选(舒缓)", 2: "中古候选(轻快)", 3: "工业候选(激昂)", 4: "原子候选(最激昂)"}
    rows = []
    for i, (path, ft) in enumerate(results):
        row = dict(name=os.path.basename(path), path=path, quartile=int(quartile[i]),
                   bpm_used=round(float(bpm[i]), 1), arousal=round(float(arousal[i]), 3), **ft)
        rows.append(row)
        print("  Q%d %5.1fbpm %6.1fdB %s | %s" % (quartile[i], bpm[i], ft["rms_db"],
                                                  labels[quartile[i]], os.path.basename(path)))
    print("[FEAT] 完成 | BPM中位数(低置信替代)=%.1f | 低置信 %d 个" % (med, int((conf < 0.15).sum())))
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("[FEAT] CSV -> %s" % a.out)


if __name__ == "__main__":
    main()
