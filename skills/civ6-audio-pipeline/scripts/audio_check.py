# -*- coding: utf-8 -*-
"""
audio_check.py -- Civ6 音频素材核验
体检项: PCM 编码 / 48000Hz / 声道(语音=单声道, BGM=立体声) / 时长 / LUFS 响度
        / LRA 响度范围 / 短时响度分位数 / 同池听感离散度
用法:
  python audio_check.py <文件或目录...> [--category voice|bgm|sfx] [--era ancient|later] [--fix]
                        [--filelist F] [--jobs N] [--json PATH] [--lra-cap F] [--pool-spread F]
  --filelist 每行一个路径的清单(规避 shell 引号问题); --jobs 并行度; --json 结果落盘(程序化验收)
  --fix  自动纠正容器问题(重采样48k/声道/pcm_s16le), 就地写+备份 .bak_check
  --lra-cap   归一化动态范围上限(默认 11, 与 audio_normalize.py --lra 同源)
  --pool-spread 同池短时响度极差告警阈值(默认 2.0 dB)
目标响度(教程11章): 语音-21 / BGM远古-28 / BGM后世-25; sfx 仅报告不评判

为什么还要看 LRA 与短时响度(实证结论, 见 references/mechanism.md):
  * 只查积分 LUFS 是查不出泵浦的 —— 泵浦文件的积分响度完全达标。
  * 积分响度相等 != 听感相等: 实测同一批 BGM 积分极差仅 3.1 dB 时,
    中位短时响度(S_p50)极差可达 7.6 dB, corr(LRA, S_p50-I) = -0.555。
  * 源 LRA > --lra 的文件若再跑一次默认归一, ffmpeg 会把 linear 静默降级为
    时变增益(泵浦) —— 这类文件必须先被点出来。
"""
import os, sys, re, json, glob, subprocess, shutil, argparse, statistics

# 非交互重定向场景(管道/DSH 采集)统一 UTF-8 输出; 原生控制台保持当前代码页
for _s in (sys.stdout, sys.stderr):
    try:
        if not _s.isatty():
            _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = json.load(open(os.path.join(HERE, '..', 'references', 'calibration.json'), encoding='utf-8'))
TARGET_LUFS = {'voice': CAL['defaults']['voice'],
               'quote': CAL['defaults']['quote'],
               'bgm_ancient': CAL['defaults']['bgm_ancient'],
               'bgm_later': CAL['defaults']['bgm_later']}
SUSPECT_BGM_SEC = 60.0  # 未分类且 ≥60s → 疑似 BGM, 按 skill 规则需询问用户

_RE_S = re.compile(r'\bS:\s*(-?\d+(?:\.\d+)?)')
# 摘要行以空白开头; 逐帧行走 "[Parsed_ebur128_0 @ ...] t: ..." 不会命中
_RE_SUM_I = re.compile(r'^\s*I:\s*(-?\d+(?:\.\d+)?)\s*LUFS', re.M)
_RE_SUM_LRA = re.compile(r'^\s*LRA:\s*(-?\d+(?:\.\d+)?)\s*LU', re.M)

def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(glob.glob(os.path.join(p, '*.wav')))
        elif os.path.isfile(p):
            out.append(p)
    return out

def probe(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json',
                        '-show_streams', '-show_format', f],
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    try:
        d = json.loads(r.stdout or '{}')
    except Exception:
        return None
    st = next((s for s in d.get('streams', []) if s.get('codec_type') == 'audio'), None)
    if not st:
        return None
    dur = st.get('duration') or d.get('format', {}).get('duration') or 0
    return dict(codec=st.get('codec_name'), rate=int(st.get('sample_rate') or 0),
                ch=int(st.get('channels') or 0), dur=float(dur))

def percentile(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    k = (len(v) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)

def lufs_json(f):
    """回落测量: loudnorm 的 JSON 是稳定接口, 只给 I/LRA/TP, 没有短时分布。"""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f,
                        '-af', 'loudnorm=I=-24:TP=-1.5:LRA=11:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    txt = r.stderr or ''
    i, j = txt.rfind('{'), txt.rfind('}')
    if i < 0 or j < i:
        return None
    try:
        return json.loads(txt[i:j + 1])
    except Exception:
        return None

def measure(f):
    """一次 ebur128 逐帧遍历同时取: 积分响度 I / 响度范围 LRA / 短时分位数。
    逐帧日志必须配 -v verbose 才会输出。解析不到时回落 loudnorm JSON(仅 I/LRA)。"""
    r = subprocess.run(['ffmpeg', '-v', 'verbose', '-hide_banner', '-nostats', '-i', f,
                        '-af', 'ebur128=framelog=verbose', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    t = r.stderr or ''
    out = dict(I=None, LRA=None, S_p10=None, S_p50=None, S_p90=None, S_n=0)
    mi, ml = _RE_SUM_I.search(t), _RE_SUM_LRA.search(t)
    if mi:
        out['I'] = float(mi.group(1))
    if ml:
        out['LRA'] = float(ml.group(1))
    vals = []
    for m in _RE_S.finditer(t):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if v > -70:      # 排除静音帧
            vals.append(v)
    if vals:
        out['S_p10'] = percentile(vals, 0.10)
        out['S_p50'] = percentile(vals, 0.50)
        out['S_p90'] = percentile(vals, 0.90)
        out['S_n'] = len(vals)
    if out['I'] is None:          # 回落
        d = lufs_json(f) or {}
        if d.get('input_i') is not None:
            out['I'] = float(d['input_i'])
        if d.get('input_lra') is not None:
            out['LRA'] = float(d['input_lra'])
    return out

def fix(f, cat):
    tmp = f + '.tmp_check.wav'
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', f]
    if cat == 'voice':
        cmd += ['-ac', '1']
    cmd += ['-ar', '48000', '-c:a', 'pcm_s16le', tmp]
    subprocess.run(cmd, check=True)
    bak = f + '.bak_check'
    if not os.path.exists(bak):
        shutil.copy2(f, bak)
    shutil.move(tmp, f)

def pool_report(rows, target, spread_thresh):
    """同池离散度: 积分响度齐不齐、听感齐不齐、有没有多基准混排。"""
    print('[POOL] 同池离散度 (n=%d)' % len(rows))

    def disp(key, label, unit):
        v = [r[key] for r in rows if r.get(key) is not None]
        if len(v) < 2:
            return
        print('  %-16s min %7.2f | p25 %7.2f | med %7.2f | p75 %7.2f | max %7.2f | 极差 %5.2f %s'
              % (label, min(v), percentile(v, .25), percentile(v, .5),
                 percentile(v, .75), max(v), max(v) - min(v), unit))
        return v

    vi = disp('lufs', '积分响度 I', 'dB')
    vl = disp('lra', '响度范围 LRA', 'LU')
    vs = disp('s_p50', '中位短时 S_p50', 'dB')

    if vi and max(vi) - min(vi) > 0.5:
        print('  [WARN] 积分响度不齐(极差 %.2f dB) —— 同池不应出现多个基准' % (max(vi) - min(vi)))
        # 找最大间隔: 识别"两簇"式混排(例如 -28/-25 双轨制)
        sv = sorted(vi)
        gap, at = 0.0, None
        for k in range(1, len(sv)):
            if sv[k] - sv[k - 1] > gap:
                gap, at = sv[k] - sv[k - 1], k
        if at and gap >= 2.0 and at >= 2 and (len(sv) - at) >= 2:
            lo, hi = sv[:at], sv[at:]
            print('  [FAIL] 疑似双基准混排: 低簇 n=%d 中心 %.2f dB ／ 高簇 n=%d 中心 %.2f dB ／ 间隔 %.2f dB'
                  % (len(lo), statistics.mean(lo), len(hi), statistics.mean(hi), gap))
            print('         同一播放容器(同一时代列表)混排两档会逐曲跳台阶, 必须统一为一个基准')
    if vs and max(vs) - min(vs) > spread_thresh:
        print('  [WARN] 听感不均: 中位短时响度极差 %.2f dB > %.2f dB'
              % (max(vs) - min(vs), spread_thresh))
        print('         积分响度相同也可能听感差这么多; 轮播池建议改用 '
              'audio_normalize.py --mode shortterm 对齐 S_p50')
    if vl and max(vl) - min(vl) > 6.0:
        print('  [WARN] 动态范围离散: LRA 极差 %.2f LU —— 密实母带与宽动态曲目混播会明显不齐' % (max(vl) - min(vl)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--category', choices=['voice', 'quote', 'bgm', 'sfx'], default='sfx')
    ap.add_argument('--era', choices=['ancient', 'later'], default='ancient')
    ap.add_argument('--fix', action='store_true')
    ap.add_argument('--filelist', default=None, help='每行一个路径的清单文件')
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--json', dest='json_path', default=None, help='结果写为 JSON(程序化验收)')
    ap.add_argument('--lra-cap', type=float, default=11.0,
                    help='归一化动态范围上限(与 audio_normalize.py --lra 同源); 超过即点名')
    ap.add_argument('--pool-spread', type=float, default=2.0,
                    help='同池短时响度极差告警阈值(dB)')
    a = ap.parse_args()
    if not (shutil.which('ffprobe') and shutil.which('ffmpeg')):
        raise SystemExit('[FAIL] 未找到 ffprobe/ffmpeg，请先安装 FFmpeg 并加入 PATH 后重试。')
    if a.filelist:
        with open(a.filelist, encoding='utf-8') as fh:
            a.paths += [ln.strip() for ln in fh if ln.strip()]
    key = a.category if a.category != 'bgm' else 'bgm_' + a.era
    target = TARGET_LUFS.get(key)
    files = collect(a.paths)
    if not files:
        raise SystemExit('没有找到 wav 文件 (自检路径: 传文件/目录或 --filelist)')
    print('[CHECK] %d 个文件 | 类别=%s | LUFS 目标=%s | LRA 上限=%g'
          % (len(files), key, target, a.lra_cap))

    def _one(f):
        lines, pend = [], 0
        row = dict(file=f, ok=False, codec=None, rate=None, ch=None, dur=None,
                   lufs=None, lra=None, s_p50=None, s_p90=None, notes=[], issues=[])
        p = probe(f)
        if not p:
            lines.append('  [FAIL] %s : 无法解析音频流' % os.path.basename(f))
            row['issues'].append('无法解析音频流')
            return lines, row, 1
        issues, notes = [], []
        if not (p['codec'] or '').startswith('pcm'):
            issues.append('编码=%s(需PCM)' % p['codec'])
        if p['rate'] != 48000:
            issues.append('采样率=%d(需48000)' % p['rate'])
        if a.category == 'voice' and p['ch'] != 1:
            issues.append('声道=%d(语音需单声道)' % p['ch'])
        if a.category == 'bgm' and p['ch'] != 2:
            issues.append('声道=%d(BGM需立体声)' % p['ch'])
        M = measure(f)
        L, LRA, S50 = M['I'], M['LRA'], M['S_p50']
        lt = ('%.1f LUFS' % L) if L is not None else 'LUFS N/A'
        if LRA is not None:
            lt += ' LRA %.1f' % LRA
        if S50 is not None:
            lt += ' S_p50 %.1f' % S50
        hint = ''
        if L is not None and target is not None and abs(L - target) > 1.5:
            hint = ' | 偏离目标 %+.1f → 跑 audio_normalize.py' % (L - target)
        lines.append('  [%s] %s | %s %dkHz %dch %.1fs | %s%s'
                     % ('OK  ' if not issues else 'WARN', os.path.basename(f),
                        p['codec'], p['rate'], p['ch'], p['dur'], lt, hint))
        # 泵浦风险点名: 这类文件再跑一次默认 --lra 归一就会被降级为时变增益
        if LRA is not None and LRA > a.lra_cap:
            notes.append('LRA %.1f > 上限 %g: 再用默认 --lra 归一会被 ffmpeg 静默降级为'
                         '时变增益(泵浦); 如需重做请放宽 --lra' % (LRA, a.lra_cap))
        if a.category == 'sfx' and p['dur'] >= SUSPECT_BGM_SEC:
            lines.append('         - [需询问] >=60s 未分类, 疑似 BGM (skill 路由规则)')
        if issues:
            lines.append('         - ' + '; '.join(issues))
            if a.fix:
                fix(f, a.category)
                lines.append('         -> 已 --fix 纠正 (备份 .bak_check)')
            else:
                pend = 1
        for n in notes:
            lines.append('         - [注意] ' + n)
        row.update(ok=not issues, codec=p['codec'], rate=p['rate'], ch=p['ch'],
                   dur=p['dur'], lufs=L, lra=LRA, s_p50=S50, s_p90=M['S_p90'],
                   issues=issues, notes=notes)
        return lines, row, pend

    rows, pending = [], 0
    if a.jobs > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=a.jobs) as ex:
            results = list(ex.map(_one, files))
    else:
        results = [_one(f) for f in files]
    for lines, row, pend in results:
        for ln in lines:
            print(ln)
        rows.append(row)
        pending += pend
    if len(rows) > 1:
        pool_report(rows, target, a.pool_spread)
    n_lra = sum(1 for r in rows if r.get('lra') is not None and r['lra'] > a.lra_cap)
    print('[CHECK] 完成; 待处理 %d 个%s | 泵浦风险文件 %d 个'
          % (pending, ' (加 --fix 自动纠正)' if pending else '', n_lra))
    if a.json_path:
        with open(a.json_path, 'w', encoding='utf-8') as fh:
            json.dump(dict(category=key, target=target, files=len(files), pending=pending,
                           lra_cap=a.lra_cap, pool_spread=a.pool_spread,
                           lra_risk=n_lra, rows=rows),
                      fh, ensure_ascii=False, indent=1)
        print('[CHECK] JSON -> %s' % a.json_path)

if __name__ == '__main__':
    main()
