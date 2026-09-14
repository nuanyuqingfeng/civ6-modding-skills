# -*- coding: utf-8 -*-
"""
music_wire.py -- 交互音乐工程接线 (BGM 半自动流程的自动化部分)
子命令:
  fade <wav>                          检测末尾淡出点: 淡出起点后 0.5s 为停止点(不足则取末帧)
  exitcustom <工程目录> [--wwu <音乐wwu>] [--media-dir <目录>] [--dry]
                                      对音乐 work unit 内每个 MusicTrack: 依据其 AudioFile 的
                                      实测时长/淡出点, 写入/更新 ExitCustom (CueType=2, TimeMs=毫秒)
  weights <工程目录> --civ-prefix X [--wwu <音乐wwu>] [--dry]
                                      按权威规则设置时代权重:
                                      Ancient=全50等权 | Medieval=主题50其余各10 |
                                      Industrial/Atomic=主题60其余各10 | Leader=主题100
模式依据: 模板 FelineBackgroundMusic.wwu 实测 schema (MusicCue CueType=2; Weight=Real64)
"""
import os, re, sys, glob, wave, struct, argparse, shutil, uuid

def rd(p):
    return open(p, encoding='utf-8').read()

def new_guid():
    return '{%s}' % str(uuid.uuid4()).upper()

def dur(f):
    try:
        w = wave.open(f, 'rb')
        d = w.getnframes() / float(w.getframerate())
        w.close()
        return d
    except Exception:
        return 0.0

def fade_point(f, win=0.05, floor_ratio=0.12, scan=15.0):
    """返回 (淡出起点秒, 停止点秒)。停止点 = 淡出起点+0.5s, 不足则取末帧前 0.05s。"""
    w = wave.open(f, 'rb')
    n, rate, ch, sw = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
    total = n / float(rate)
    w.setpos(max(0, n - int(scan * rate)))
    raw = w.readframes(n - w.tell())
    w.close()
    step = int(win * rate) * ch
    rms = []
    for i in range(0, len(raw) - step + 1, step):
        seg = raw[i:i + step]
        cnt = len(seg) // (sw * ch)
        vals = struct.unpack('<%dh' % (cnt * ch), seg[:cnt * sw * ch])
        rms.append((sum(v * v for v in vals) / max(1, len(vals))) ** 0.5)
    if not rms:
        return max(0.0, total - 0.05), max(0.0, total - 0.05)
    peak = max(rms) or 1.0
    floor = peak * floor_ratio
    fade_i = len(rms) - 1
    hold = max(1, int(0.3 / win))
    for i in range(len(rms) - hold):
        if all(x < floor for x in rms[i:i + hold]):
            fade_i = i
            break
    fade_t = (total - scan) + fade_i * win
    stop = min(fade_t + 0.5, total - 0.05)
    return max(0.0, fade_t), max(0.0, stop)

def cmd_fade(a):
    f_t, s_t = fade_point(a.wav)
    print('%.3f\t%.3f\t%s  (淡出起点/停止点/文件)' % (f_t, s_t, a.wav))

def find_wwu(proj, hint):
    hits = sorted(glob.glob(os.path.join(proj, 'Interactive Music Hierarchy', '*.wwu')))
    for p in hits:
        if hint and hint in os.path.basename(p):
            return p
    if hits:
        return hits[0]
    raise SystemExit('未找到音乐 wwu')

def cmd_exitcustom(a):
    ww = a.wwu or find_wwu(a.proj, 'BackgroundMusic')
    media = a.media_dir or os.path.join(a.proj, 'Originals', 'SFX')
    txt = rd(ww)
    changed = 0
    out, pos = [], 0
    for m in re.finditer(r'<MusicTrack\b.*?</MusicTrack>', txt, re.S):
        blk = m.group(0)
        out.append(txt[pos:m.start()])
        af = re.search(r'<AudioFile>([^<]+)</AudioFile>', blk)
        if af:
            wav = os.path.join(media, af.group(1))
            if os.path.exists(wav):
                f_t, s_t = fade_point(wav)
                ms = '%.6f' % (s_t * 1000.0)
                cue = ('<MusicCue Name="ExitCustom" ID="%s">\n'
                       '\t\t\t\t\t\t\t\t\t\t<PropertyList>\n'
                       '\t\t\t\t\t\t\t\t\t\t\t<Property Name="CueType" Type="int16" Value="2"/>\n'
                       '\t\t\t\t\t\t\t\t\t\t\t<Property Name="TimeMs" Type="Real64" Value="%s"/>\n'
                       '\t\t\t\t\t\t\t\t\t\t</PropertyList>\n'
                       '\t\t\t\t\t\t\t\t\t</MusicCue>') % (new_guid(), ms)
                if 'ExitCustom' in blk:
                    blk = re.sub(r'<MusicCue Name="ExitCustom">\s*<PropertyList>.*?</PropertyList>\s*</MusicCue>',
                                 cue.replace('\n', '\n'), blk, flags=re.S)
                else:
                    blk = blk.replace('</CueList>', cue + '\n\t\t\t\t\t\t\t\t</CueList>')
                changed += 1
                print('  [CUE] %-28s 停止点 %.2fs' % (af.group(1), s_t))
        out.append(blk)
        pos = m.end()
    out.append(txt[pos:])
    if changed and not a.dry:
        shutil.copy2(ww, ww + '.bak_wire')
        open(ww, 'wb').write(''.join(out).encode('utf-8'))
    print('[EXITCUSTOM] 更新 %d 条%s' % (changed, ' (dry-run)' if a.dry else ''))

def cmd_weights(a):
    ww = a.wwu or find_wwu(a.proj, 'BackgroundMusic')
    txt = rd(ww)
    pre = a.civ_prefix
    n = 0
    for era in ['Ancient', 'Medieval', 'Industrial', 'Atomic']:
        for kind in ('Civ', 'Leader'):
            cname = '%s%s_%s' % (pre, kind, era)
            m = re.search(r'<MusicPlaylistContainer Name="%s".*?</MusicPlaylistContainer>' % re.escape(cname), txt, re.S)
            if not m:
                print('  [SKIP] %s 不存在' % cname)
                continue
            blk = m.group(0)
            refs = re.findall(r'<SegmentRef Name="([^"]+)"', blk)
            if not refs:
                continue
            theme = [r for r in refs if 'theme' in r.lower() and era.lower() in r.lower()]
            others = [r for r in refs if r not in theme]
            plan = {}
            if era == 'Ancient':
                plan = {r: 50.0 for r in refs}
            elif kind == 'Leader':
                plan = {r: 0.0 for r in refs}
                if theme: plan[theme[0]] = 100.0
            else:
                plan = {r: 0.0 for r in refs}
                if theme: plan[theme[0]] = 50.0 if era == 'Medieval' else 60.0
                for r in others:
                    plan[r] = 10.0

            def patch_item(im):
                b = im.group(0)
                seg = re.search(r'<SegmentRef Name="([^"]+)"', b).group(1)
                w = plan.get(seg)
                if w is None:
                    return b
                if 'Name="Weight"' in b:
                    b = re.sub(r'\s*<Property Name="Weight".*?</Property>', '', b, flags=re.S)
                indent = '\t' * (b.count('\n\t') and 15 or 15)
                add = ('\n\t\t\t\t\t\t\t\t\t\t<Property Name="Weight" Type="Real64">'
                       '\n\t\t\t\t\t\t\t\t\t\t\t<ValueList>'
                       '\n\t\t\t\t\t\t\t\t\t\t\t\t<Value Platform="Windows">%g</Value>'
                       '\n\t\t\t\t\t\t\t\t\t\t\t</ValueList>'
                       '\n\t\t\t\t\t\t\t\t\t\t</Property>') % w
                b = b.replace('</PropertyList>', add + '\n\t\t\t\t\t\t\t\t\t</PropertyList>', 1)
                return b

            blk2 = re.sub(r'<MusicPlaylistItem\b(?:(?!<MusicPlaylistItem\b).)*?</MusicPlaylistItem>',
                          patch_item, blk, flags=re.S)
            txt = txt[:m.start()] + blk2 + txt[m.end():]
            n += 1
            print('  [W] %-32s %s' % (cname, {r: plan[r] for r in refs}))
    if n and not a.dry:
        shutil.copy2(ww, ww + '.bak_wire')
        open(ww, 'wb').write(txt.encode('utf-8'))
    print('[WEIGHTS] 更新 %d 个容器%s' % (n, ' (dry-run)' if a.dry else ''))

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('fade'); f.add_argument('wav')
    e = sub.add_parser('exitcustom'); e.add_argument('proj')
    e.add_argument('--wwu', default=None); e.add_argument('--media-dir', default=None)
    e.add_argument('--dry', action='store_true')
    w = sub.add_parser('weights'); w.add_argument('proj')
    w.add_argument('--wwu', default=None); w.add_argument('--civ-prefix', required=True)
    w.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'fade':
        cmd_fade(a)
    elif a.cmd == 'exitcustom':
        cmd_exitcustom(a)
    else:
        cmd_weights(a)

if __name__ == '__main__':
    main()
