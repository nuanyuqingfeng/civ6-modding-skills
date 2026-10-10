# -*- coding: utf-8 -*-
"""
audio_normalize.py -- Civ6 audio loudness normalization (ffmpeg loudnorm 2-pass, linear)
Base: references/calibration.json (voice -21 / quote -23.5 / bgm ancient -28 / later -25)
Modes:
  absolute (default) target = calibrated base (or --i override)  —— 对齐"整轨积分响度"
  relative           target_i = anchor + retain*(L_i - anchor)
                     anchor = batch median by default; retain default 0.10
  shortterm          target = base 作用于"短时响度中位数 S_p50", 用恒定增益 volume= 实现
                     —— 轮播池(BGM 轮播组)用这个: 积分响度相等 != 听感相等,
                     实测同池积分只差 3.1 dB 时 S_p50 可差 7.6 dB (corr(LRA, S_p50-I)=-0.555)
Output: 48000Hz pcm_s16le; voice->mono, bgm->stereo.
  --out DIR 模式下输出统一 .wav 后缀(非 wav 输入的容器转换一并完成);
  就地模式会把结果写回原文件名(含原扩展名), 非 wav 输入建议用 --out。

三道安全闸(均为实证结论, 见 references/mechanism.md):
  1) 幂等闸 --idem 0.3 : 已落在目标 +-0.3 dB 内的文件直接跳过, 不重复处理。
     重复处理是纯风险: 源池已达标时增益=0, 唯一产物是下方第 2 条的降级损伤。
  2) 线性闸 --allow-dynamic : ffmpeg loudnorm 的 linear=true 是"允许"不是"保证"。
     af_loudnorm.c init() 仅在 (offset_tp <= target_tp) 且 (measured_lra <= target_lra)
     同时成立时才走 LINEAR_MODE, 否则静默切到 FIRST/INNER/FINAL_FRAME 时变增益(=泵浦)。
     本脚本预检该条件, 不满足即拒写该文件并计入 blocked(退出码 2); 处理后再读
     ffmpeg 自报的 normalization_type 复核, 报 dynamic 一律判失败。
  3) 短时闸 : BGM 轮播池改用 --mode shortterm, 恒定增益不可能产生泵浦。
最终响度验收以 audio_check.py 为准(它已加 LRA 与同池听感离散度检查)。
"""
import os, sys, re, json, glob, subprocess, shutil, argparse, statistics, tempfile

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

_RE_S = re.compile(r'\bS:\s*(-?\d+(?:\.\d+)?)')

def percentile(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    k = (len(v) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)

def measure_shortterm(f):
    """EBU R128 短时(3s)响度分布, 供 --mode shortterm 与听感离散度评估使用。
    注意: framelog=verbose 的逐帧日志必须配 -v verbose 才会输出到 stderr。"""
    r = subprocess.run(['ffmpeg', '-v', 'verbose', '-hide_banner', '-nostats', '-i', f,
                        '-af', 'ebur128=framelog=verbose', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    vals = []
    for m in _RE_S.finditer(r.stderr or ''):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if v > -70:          # 排除静音帧(ebur128 用 -120.7 之类填零)
            vals.append(v)
    if not vals:
        return None
    return {'S_p10': percentile(vals, 0.10), 'S_p50': percentile(vals, 0.50),
            'S_p90': percentile(vals, 0.90), 'S_n': len(vals)}

def linear_ok(m, target_i, tp, lra):
    """复刻 af_loudnorm.c init() 的线性判定。不满足时 ffmpeg 不会报错, 而是静默改用
    FIRST/INNER/FINAL_FRAME 时变增益(听感=泵浦)。返回 (bool, 拒绝原因)。
    判定式(与源码逐字对应):
        offset    = target_i - measured_i
        offset_tp = measured_tp + offset
        linear  <=> (offset_tp <= target_tp) and (measured_lra <= target_lra)
                    且四个哨兵值均未被占用"""
    try:
        mi, mtp = float(m['input_i']), float(m['input_tp'])
        mlra, mth = float(m['input_lra']), float(m['input_thresh'])
    except Exception:
        return False, '测量值缺失'
    if mtp == 99 or mth == -70 or mlra == 0 or mi == 0:
        return False, '哨兵测量值(tp=99/thresh=-70/lra=0/I=0) → ffmpeg 拒绝线性'
    offset = target_i - mi
    offset_tp = mtp + offset
    if offset_tp > tp:
        return False, '线性增益后峰值 %.2f > 上限 %.2f dBTP' % (offset_tp, tp)
    if mlra > lra:
        return False, '源 LRA %.2f > --lra %g → 会切动态归一(泵浦)' % (mlra, lra)
    return True, ''

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
    """应用两遍 loudnorm, 并回收 ffmpeg 自报统计。
    关键: 加 print_format=json 后 uninit() 会输出 normalization_type=linear|dynamic,
    这是"到底有没有被降级"的权威判据(比事后反推增益轨迹更可靠)。
    注意日志级别要放到 info, 否则该 JSON 会被 -loglevel error 吞掉。"""
    af = ('loudnorm=I=%g:TP=%g:LRA=%g:measured_I=%s:measured_TP=%s:measured_LRA=%s:'
          'measured_thresh=%s:offset=%s:linear=true:print_format=json'
          % (I, TP, LRA, m['input_i'], m['input_tp'], m['input_lra'],
             m['input_thresh'], m.get('target_offset', 0)))
    cmd = ['ffmpeg', '-y', '-hide_banner', '-nostats', '-v', 'info', '-i', src,
           '-af', af, '-ar', '48000', '-c:a', 'pcm_s16le']
    if ac:
        cmd += ['-ac', str(ac)]
    cmd += [dst]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError('ffmpeg 应用失败: ' + (r.stderr or '')[-400:])
    t = r.stderr or ''
    i, j = t.rfind('{'), t.rfind('}')
    if i < 0 or j < i:
        return {}
    try:
        return json.loads(t[i:j + 1])
    except Exception:
        return {}

def apply_gain(src, gain_db, ac, dst):
    """恒定增益路径(供短时锚使用): 纯 volume 滤波器, 全程同一个增益,
    结构上不可能产生泵浦 —— 这是轮播池最安全的对齐手段。
    调用方须已把增益夹到不越过真峰上限。"""
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', src,
           '-af', 'volume=%.3fdB' % gain_db, '-ar', '48000', '-c:a', 'pcm_s16le']
    if ac:
        cmd += ['-ac', str(ac)]
    cmd += [dst]
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--category', choices=['voice', 'quote', 'bgm', 'sfx'], default='sfx')
    ap.add_argument('--era', choices=['ancient', 'later'], default='ancient')
    ap.add_argument('--mode', choices=['absolute', 'relative', 'shortterm'], default='absolute')
    ap.add_argument('--retain', type=float, default=RETAIN_DEFAULT)
    ap.add_argument('--anchor', type=float, default=None)
    ap.add_argument('--i', type=float, default=None)
    ap.add_argument('--tp', type=float, default=-1.5)
    ap.add_argument('--lra', type=float, default=11.0,
                    help='动态范围上限; 注意它同时是 ffmpeg 是否允许线性归一的判据之一, '
                         '源 LRA 超它就会被静默降级为时变增益(见 --allow-dynamic)')
    ap.add_argument('--idem', type=float, default=0.3,
                    help='幂等闸: 已落在目标 +-该值(dB)内的文件直接跳过, 默认 0.3')
    ap.add_argument('--force', action='store_true', help='关闭幂等闸, 强制处理所有文件')
    ap.add_argument('--allow-dynamic', action='store_true',
                    help='允许 loudnorm 从 linear 降级为 dynamic(时变增益/泵浦)。'
                         '默认拒写该类文件并以退出码 2 报出')
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
            st = None
            if a.mode == 'shortterm':
                try:
                    st = measure_shortterm(src)
                except Exception as e:
                    print('  [WARN] %s 短时响度测量失败 (%s)' % (os.path.basename(f), e))
            return f, src, m, st

        if a.jobs > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=a.jobs) as ex:
                results = list(ex.map(_meas, files))
        else:
            results = [_meas(f) for f in files]
        measured, lra_wide = [], []
        for f, src, m, st in results:
            measured.append(dict(f=f, src=src, m=m, I=float(m['input_i']), st=st))
            extra = ''
            if st:
                extra = ' | S_p50 %6.1f' % st['S_p50']
            print('  [MEAS] %-50s %6.1f LUFS%s' % (os.path.basename(f), measured[-1]['I'], extra))
            if float(m.get('input_lra') or 0) > a.lra:
                lra_wide.append(os.path.basename(f))
        if lra_wide and a.mode != 'shortterm':
            print('  [WARN] %d 个文件源 LRA > --lra %g: %s%s'
                  % (len(lra_wide), a.lra, ', '.join(lra_wide[:6]),
                     ' ...' if len(lra_wide) > 6 else ''))
            print('         这些文件若还需处理, ffmpeg 会把 linear 静默降级为时变增益(泵浦);'
                  ' 已在目标上的会被幂等闸跳过')

        targets = {}
        if a.mode == 'shortterm':
            if base is None:
                print('[NORM] shortterm 需要目标值: 用 --i 指定(或选一个自带基准的类别)'); return
            print('[NORM] shortterm | 目标 S_p50 %.1f LUFS | 恒定增益对齐"听感": 积分响度相等 != 听感相等'
                  % base)
            for it in measured:
                if it['st'] is None:
                    continue
                # 以"应施加的增益(dB)"承载目标: 短时锚走 volume 路径, 不经过 loudnorm
                targets[it['f']] = base - it['st']['S_p50']
            if not targets:
                print('[NORM] 全部文件都取不到短时响度, 无可用目标'); return
        elif a.mode == 'relative':
            anchor = (a.anchor if a.anchor is not None
                      else statistics.median(it['I'] for it in measured))
            print('[NORM] relative | anchor(median) %.1f | retain %.2f' % (anchor, a.retain))
            for it in measured:
                targets[it['f']] = anchor + a.retain * (it['I'] - anchor)
        else:
            if base is None:
                print('[NORM] sfx without --i: no absolute target, nothing to do'); return
            print('[NORM] absolute | base %.1f LUFS' % base)
            for it in measured:
                targets[it['f']] = base

        def _apply_one(it):
            f, src, m, v = it['f'], it['src'], it['m'], it['I']
            name = os.path.basename(f)
            t = round(base if a.mode == 'shortterm' else targets[f], 1)
            if a.out:
                # 输出到目录: 统一 .wav 后缀(修复非 wav 输入产出错误后缀的问题)
                dst = os.path.join(a.out, os.path.splitext(name)[0] + '.wav')
            else:
                dst = f + '.tmp_norm.wav'

            def _commit():
                if not a.out:
                    bak = f + '.bak_norm'
                    if not os.path.exists(bak):
                        shutil.copy2(f, bak)
                    shutil.move(dst, f)

            def _passthrough():
                # 跳过响度处理, 但仍要产出规格一致的输出(--out 模式), 否则输出集不完整
                if a.out:
                    apply_gain(src, 0.0, ac, dst)

            # ---- 闸 1: 幂等. 已在目标上的文件重复处理没有任何响度收益, 只可能被降级损伤 ----
            if a.mode == 'shortterm':
                if it['st'] is None:
                    return dict(name=name, status='BLOCKED', was=v, target=t,
                                why='取不到短时响度(无法判定目标)')
                gain = targets[f]
                if (not a.force) and abs(gain) <= a.idem:
                    _passthrough()
                    return dict(name=name, status='SKIP', was=v, target=t,
                                mode=None, gain=0.0, st=it['st'])
            else:
                if (not a.force) and abs(v - t) <= a.idem:
                    _passthrough()
                    return dict(name=name, status='SKIP', was=v, target=t, mode=None)
                # ---- 闸 2(预检): 复刻 ffmpeg 的线性判定, 不满足就别动手 ----
                ok, why = linear_ok(m, t, a.tp, a.lra)
                if not ok and not a.allow_dynamic:
                    return dict(name=name, status='BLOCKED', was=v, target=t, mode=None, why=why)

            if a.mode == 'shortterm':
                # 恒定增益 + 真峰夹紧: 结构上不可能泵浦
                g = targets[f]
                ceil = a.tp - float(m['input_tp'])
                if g > ceil:
                    g = ceil
                apply_gain(src, g, ac, dst)
                _commit()
                return dict(name=name, status='OK', was=v, target=t,
                            mode='constant-gain', gain=g, st=it['st'])

            info = apply(src, m, t, a.tp, a.lra, ac, dst)
            ntype = (info or {}).get('normalization_type')
            # ---- 闸 2(后验): ffmpeg 自报的处理类型是权威判据 ----
            if ntype == 'dynamic' and not a.allow_dynamic:
                try:
                    os.remove(dst)
                except OSError:
                    pass
                return dict(name=name, status='BLOCKED', was=v, target=t, mode='dynamic',
                            why='ffmpeg 自报 normalization_type=dynamic(产物已丢弃)')
            _commit()
            return dict(name=name, status='OK', was=v, target=t, mode=ntype or '?',
                        out_i=(info or {}).get('output_i'),
                        out_lra=(info or {}).get('output_lra'))

        if a.jobs > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=a.jobs) as ex:
                done = list(ex.map(_apply_one, measured))
        else:
            done = [_apply_one(it) for it in measured]

        n_ok = n_skip = 0
        blocked = []
        for d in done:
            if d['status'] == 'OK':
                n_ok += 1
                extra = ''
                if d.get('mode') == 'constant-gain':
                    extra = ' | 恒定增益 %+.2f dB | S_p50 %.1f' % (d['gain'], d['st']['S_p50'])
                elif d.get('out_i') is not None:
                    extra = ' | 实测输出 %s LUFS / LRA %s' % (d['out_i'], d.get('out_lra'))
                print('  [OK]   %-48s %6.1f -> %6.1f LUFS | %s%s'
                      % (d['name'], d['was'], d['target'], d['mode'], extra))
            elif d['status'] == 'SKIP':
                n_skip += 1
                print('  [SKIP] %-48s 已在目标 %.1f (实测 %.2f, 差 %+.2f dB) —— 幂等闸跳过'
                      % (d['name'], d['target'], d['was'], d['was'] - d['target']))
            else:
                blocked.append(d)
                print('  [BLOCK] %-47s 拒写: %s' % (d['name'], d.get('why', '')))

        print('[NORM] 完成: 处理 %d / 幂等跳过 %d / 拒写 %d | 模式 %s | 目标 %s%s'
              % (n_ok, n_skip, len(blocked), a.mode, base,
                 ' (backups: .bak_norm)' if not a.out else ''))
        if blocked:
            print('[NORM] !! %d 个文件被拒写(原文件未改动)。处置二选一:' % len(blocked))
            print('       a) 放宽 --lra(如 --lra 20) 让线性判定通过 —— 保留原动态, 推荐;')
            print('       b) 确认接受时变增益(泵浦)后加 --allow-dynamic。')
        print('[NORM] 终验: audio_check.py (含 LRA 与同池听感离散度)')
        return 2 if blocked else 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == '__main__':
    sys.exit(main())
