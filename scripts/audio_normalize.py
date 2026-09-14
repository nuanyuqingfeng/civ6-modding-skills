# -*- coding: utf-8 -*-
"""
audio_normalize.py -- Civ6 audio loudness normalization (ffmpeg loudnorm 2-pass, linear)
Base: references/calibration.json (voice -21 / quote -23.5 / bgm ancient -28 / later -25)
Modes:
  absolute (default) target = calibrated base (or --i override)
  relative           target_i = anchor + retain*(L_i - anchor)
                     anchor = batch median by default; retain default 0.10
Output: 48000Hz pcm_s16le; voice->mono, bgm->stereo.
  --out DIR 模式下输出统一 .wav 后缀(非 wav 输入的容器转换一并完成);
  就地模式会把结果写回原文件名(含原扩展名), 非 wav 输入建议用 --out。
  源 LRA > 目标 LRA 时 loudnorm linear 可能回退动态归一(泵浦风险), 会打印 [WARN];
  最终响度验收以 audio_check.py 为准。
"""
import os, sys, json, glob, subprocess, shutil, argparse, statistics, tempfile

# 非交互重定向场景(管道/DSH 采集)统一 UTF-8 输出; 原生控制台保持当前代码页
for _s in (sys.stdout, sys.stderr):
    try:
        if not _s.isatty():
            _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = json.load(open(os.path.join(HERE, '..', 'references', 'calibration.json'), encoding='utf-8'))
DEFAULTS = CAL['defaults']
RETAIN_DEFAULT = CAL.get('relative', {}).get('retain', 0.10)

def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(glob.glob(os.path.join(p, '*.wav')))
        elif os.path.isfile(p):
            out.append(p)
    return out

def probe_ch(f):
    # 探测音频声道数(仅统计, 不感知容器命名)
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json',
                        '-show_streams', f],
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    try:
        d = json.loads(r.stdout or '{}')
    except Exception:
        return None
    st = next((s for s in d.get('streams', []) if s.get('codec_type') == 'audio'), None)
    if not st:
        return None
    return int(st.get('channels') or 0)

def measure(f, I, TP, LRA):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f,
                        '-af', 'loudnorm=I=%g:TP=%g:LRA=%g:print_format=json' % (I, TP, LRA),
                        '-f', 'null', '-'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    t = r.stderr or ''
    i, j = t.rfind('{'), t.rfind('}')
    if i < 0 or j < i:
        raise SystemExit('loudnorm measure failed: ' + f)
    return json.loads(t[i:j + 1])

def stage_channels(f, ac, tmpdir):
    """若源声道数 != 目标声道数, 生成 PCM 中间件(声道转换), 使响度测量与最终输出为同一信号;
    否则返回原路径. 防止先测立体声再落盘降混造成固定 3dB 偏差."""
    if not ac:
        return f
    ch = probe_ch(f)
    if ch is None or ch == ac:
        return f
    fd, dst = tempfile.mkstemp(suffix='.wav', prefix='civ6_stage_%dch_' % ac, dir=tmpdir)
    os.close(fd)
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', f,
           '-ac', str(ac), '-ar', '48000', '-c:a', 'pcm_s16le', dst]
    subprocess.run(cmd, check=True)
    return dst

def apply(src, m, I, TP, LRA, ac, dst):
    af = ('loudnorm=I=%g:TP=%g:LRA=%g:measured_I=%s:measured_TP=%s:measured_LRA=%s:'
          'measured_thresh=%s:offset=%s:linear=true'
          % (I, TP, LRA, m['input_i'], m['input_tp'], m['input_lra'],
             m['input_thresh'], m.get('target_offset', 0)))
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', src,
           '-af', af, '-ar', '48000', '-c:a', 'pcm_s16le']
    if ac:
        cmd += ['-ac', str(ac)]
    cmd += [dst]
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--category', choices=['voice', 'quote', 'bgm', 'sfx'], default='sfx')
    ap.add_argument('--era', choices=['ancient', 'later'], default='ancient')
    ap.add_argument('--mode', choices=['absolute', 'relative'], default='absolute')
    ap.add_argument('--retain', type=float, default=RETAIN_DEFAULT)
    ap.add_argument('--anchor', type=float, default=None)
    ap.add_argument('--i', type=float, default=None)
    ap.add_argument('--tp', type=float, default=-1.5)
    ap.add_argument('--lra', type=float, default=11.0)
    ap.add_argument('--out', default=None)
    ap.add_argument('--filelist', default=None, help='每行一个路径的清单文件(规避 shell 引号问题)')
    ap.add_argument('--jobs', type=int, default=1, help='并行度(测量与写盘两阶段各自并行)')
    a = ap.parse_args()
    if not (shutil.which('ffprobe') and shutil.which('ffmpeg')):
        raise SystemExit('[FAIL] 未找到 ffprobe/ffmpeg，请先安装 FFmpeg 并加入 PATH 后重试。')
    if a.filelist:
        with open(a.filelist, encoding='utf-8') as fh:
            a.paths += [ln.strip() for ln in fh if ln.strip()]
    key = a.category if a.category != 'bgm' else 'bgm_' + a.era
    base = a.i if a.i is not None else DEFAULTS.get(key)
    ac = 1 if a.category == 'voice' else (2 if a.category == 'bgm' else None)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    files = collect(a.paths)
    if not files:
        raise SystemExit('no wav found')

    # 逐文件判定测量源: voice 输出单声道 / BGM 输出立体声 -> 若源声道数不符,
    # 先生成目标声道中间件, 保证 loudnorm 测量与最终输出是同一信号(避免固定 3dB 偏差).
    tmpdir = tempfile.mkdtemp(prefix='civ6_norm_stage_')
    try:
        def _meas(f):
            src = f
            if ac:
                try:
                    src = stage_channels(f, ac, tmpdir)
                except Exception as e:
                    print('  [WARN] %s 声道中间件生成失败 (%s), 回退直接测量源'
                          % (os.path.basename(f), e))
            m = measure(src, base if base is not None else -24, a.tp, a.lra)
            return f, src, m

        if a.jobs > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=a.jobs) as ex:
                results = list(ex.map(_meas, files))
        else:
            results = [_meas(f) for f in files]
        measured, lra_warn = [], 0
        for f, src, m in results:
            measured.append((f, src, m, float(m['input_i'])))
            print('  [MEAS] %-50s %6.1f LUFS' % (os.path.basename(f), measured[-1][3]))
            if float(m.get('input_lra') or 0) > a.lra:
                lra_warn += 1
                print('  [WARN] %-50s 源LRA %.1f > 目标 %g, linear 可能回退动态归一(泵浦风险), 建议听感复核'
                      % (os.path.basename(f), float(m['input_lra']), a.lra))

        targets = {}
        if a.mode == 'relative':
            anchor = a.anchor if a.anchor is not None else statistics.median(v for _, _, _, v in measured)
            print('[NORM] relative | anchor(median) %.1f | retain %.2f' % (anchor, a.retain))
            for f, src, m, v in measured:
                targets[f] = anchor + a.retain * (v - anchor)
        else:
            if base is None:
                print('[NORM] sfx without --i: no absolute target, nothing to do'); return
            print('[NORM] absolute | base %.1f LUFS' % base)
            for f, src, m, v in measured:
                targets[f] = base

        def _apply_one(item):
            f, src, m, v = item
            t = round(targets[f], 1)
            if a.out:
                # 输出到目录: 统一 .wav 后缀(修复非 wav 输入产出错误后缀的问题)
                dst = os.path.join(a.out, os.path.splitext(os.path.basename(f))[0] + '.wav')
            else:
                dst = f + '.tmp_norm.wav'
            apply(src, m, t, a.tp, a.lra, ac, dst)
            if not a.out:
                bak = f + '.bak_norm'
                if not os.path.exists(bak):
                    shutil.copy2(f, bak)
                shutil.move(dst, f)
            return f, v, t

        if a.jobs > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=a.jobs) as ex:
                done = list(ex.map(_apply_one, measured))
        else:
            done = [_apply_one(item) for item in measured]
        for f, v, t in done:
            print('  [OK] %-50s %6.1f -> %6.1f LUFS' % (os.path.basename(f), v, t))
        print('[NORM] 完成: %d 文件 | 目标 %.1f LUFS%s | LRA回退警告 %d (终验: audio_check.py)'
              % (len(done), base if base is not None else -24,
                 ' (backups: .bak_norm)' if not a.out else '', lra_warn))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == '__main__':
    main()
