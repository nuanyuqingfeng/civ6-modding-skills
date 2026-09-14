# -*- coding: utf-8 -*-
"""
audio_check.py -- Civ6 音频素材核验
体检项: PCM 编码 / 48000Hz / 声道(语音=单声道, BGM=立体声) / 时长 / LUFS 响度
用法:
  python audio_check.py <文件或目录...> [--category voice|bgm|sfx] [--era ancient|later] [--fix]
                        [--filelist F] [--jobs N] [--json PATH]
  --filelist 每行一个路径的清单(规避 shell 引号问题); --jobs 并行度; --json 结果落盘(程序化验收)
  --fix  自动纠正容器问题(重采样48k/声道/pcm_s16le), 就地写+备份 .bak_check
目标响度(教程11章): 语音-21 / BGM远古-28 / BGM后世-25; sfx 仅报告不评判
"""
import os, sys, json, glob, subprocess, shutil, argparse

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

def lufs(f):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f,
                        '-af', 'loudnorm=I=-24:TP=-1.5:LRA=11:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    txt = r.stderr or ''
    i, j = txt.rfind('{'), txt.rfind('}')
    if i < 0 or j < i:
        return None
    try:
        return float(json.loads(txt[i:j + 1]).get('input_i'))
    except Exception:
        return None

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--category', choices=['voice', 'quote', 'bgm', 'sfx'], default='sfx')
    ap.add_argument('--era', choices=['ancient', 'later'], default='ancient')
    ap.add_argument('--fix', action='store_true')
    ap.add_argument('--filelist', default=None, help='每行一个路径的清单文件')
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--json', dest='json_path', default=None, help='结果写为 JSON(程序化验收)')
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
    print('[CHECK] %d 个文件 | 类别=%s | LUFS 目标=%s' % (len(files), key, target))

    def _one(f):
        lines, row, pend = [], dict(file=f, ok=False, codec=None, rate=None, ch=None,
                                    dur=None, lufs=None, issues=[]), 0
        p = probe(f)
        if not p:
            lines.append('  [FAIL] %s : 无法解析音频流' % os.path.basename(f))
            row['issues'].append('无法解析音频流')
            return lines, row, 1
        issues = []
        if not (p['codec'] or '').startswith('pcm'):
            issues.append('编码=%s(需PCM)' % p['codec'])
        if p['rate'] != 48000:
            issues.append('采样率=%d(需48000)' % p['rate'])
        if a.category == 'voice' and p['ch'] != 1:
            issues.append('声道=%d(语音需单声道)' % p['ch'])
        if a.category == 'bgm' and p['ch'] != 2:
            issues.append('声道=%d(BGM需立体声)' % p['ch'])
        L = lufs(f)
        lt = ('%.1f LUFS' % L) if L is not None else 'LUFS N/A'
        hint = ''
        if L is not None and target is not None and abs(L - target) > 1.5:
            hint = ' | 偏离目标 %+.1f → 跑 audio_normalize.py' % (L - target)
        lines.append('  [%s] %s | %s %dkHz %dch %.1fs | %s%s'
                     % ('OK  ' if not issues else 'WARN', os.path.basename(f),
                        p['codec'], p['rate'], p['ch'], p['dur'], lt, hint))
        if a.category == 'sfx' and p['dur'] >= SUSPECT_BGM_SEC:
            lines.append('         - [需询问] >=60s 未分类, 疑似 BGM (skill 路由规则)')
        if issues:
            lines.append('         - ' + '; '.join(issues))
            if a.fix:
                fix(f, a.category)
                lines.append('         -> 已 --fix 纠正 (备份 .bak_check)')
            else:
                pend = 1
        row.update(ok=not issues, codec=p['codec'], rate=p['rate'], ch=p['ch'],
                   dur=p['dur'], lufs=L, issues=issues)
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
    print('[CHECK] 完成; 待处理 %d 个%s' % (pending, ' (加 --fix 自动纠正)' if pending else ''))
    if a.json_path:
        with open(a.json_path, 'w', encoding='utf-8') as fh:
            json.dump(dict(category=key, target=target, files=len(files), pending=pending, rows=rows),
                      fh, ensure_ascii=False, indent=1)
        print('[CHECK] JSON -> %s' % a.json_path)

if __name__ == '__main__':
    main()
