# -*- coding: utf-8 -*-
"""
leader_timeline.py -- 领袖 2D 行为资产(.ast)的语音时间线自动配置
.ast 内 6 槽位: 01_FIRST_MEET / 02_DECLARE_WAR_FROM_HUMAN / 03_DECLARE_WAR_FROM_AI /
                04_KUDOS / 05_WARNING / 06_DEFEAT
每个槽位: m_FXName = 对应语音事件名(取自语音文件名主干), m_fDuration = 语音时长 + --pad
用法:
  patch <ast路径|目录> --media <语音wav目录|文件...> [--pad 0.5] [--map 槽位关键字=事件名 ...] [--dry]
  check <ast路径|目录>
路由(由 agent 按 SKILL.md 执行):
  ① 项目/工程内已有领袖 ast → 直接 patch
  ② 没有 → 跳过并在报告中说明
  ③ 任务本身要求新建 2D 领袖 → 引导 civ6-asset-forge（reference/leader-2d.md）生成后再 patch
"""
import os, re, sys, glob, json, argparse, subprocess

SLOTS = ['01_FIRST_MEET', '02_DECLARE_WAR_FROM_HUMAN', '03_DECLARE_WAR_FROM_AI',
         '04_KUDOS', '05_WARNING', '06_DEFEAT']

def find_ast(p):
    if os.path.isfile(p) and p.lower().endswith('.ast'):
        return [p]
    if os.path.isdir(p):
        hits = glob.glob(os.path.join(p, '**', '*.ast'), recursive=True)
        if hits: return hits
    return []

def dur(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', f],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        st = json.loads(r.stdout or '{}')['streams'][0]
        return float(st.get('duration') or 0)
    except Exception:
        return 0.0

def collect_media(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(glob.glob(os.path.join(p, '*.wav')))
        elif os.path.isfile(p):
            out.append(p)
    return out

def cmd_check(a):
    hits = find_ast(a.path)
    if not hits:
        print('[CASE2] 未找到领袖 .ast —— 跳过时间线配置, 请在报告中说明')
        return
    for p in hits:
        txt = open(p, encoding='utf-8-sig', errors='replace').read()
        print('AST:', p)
        for slot in SLOTS:
            m = re.search(r'<m_Name text="%s"/>.*?<m_FXName text="([^"]*)".*?<m_fDuration>([\d.]+)</m_fDuration>' % slot, txt, re.S)
            if m:
                print('  %-26s FX=%-40s Dur=%.2fs' % (slot, m.group(1), float(m.group(2))))

def cmd_patch(a):
    hits = find_ast(a.path)
    if not hits:
        print('[CASE2] 未找到领袖 .ast —— 跳过时间线配置, 请在报告中说明')
        sys.exit(0)
    media = collect_media(a.media)
    emap = dict(kv.split('=', 1) for kv in a.map) if a.map else {}
    for p in hits:
        txt = open(p, encoding='utf-8-sig', errors='replace').read()
        orig = txt
        print('AST:', p)
        for slot in SLOTS:
            ev = emap.get(slot)
            d = None
            if ev is None:
                kw = slot.split('_', 1)[1]  # FIRST_MEET / DECLARE_WAR_FROM_HUMAN / ...
                cand = [w for w in media if kw.lower() in os.path.basename(w).lower()]
                if cand:
                    w = cand[0]
                    ev = os.path.splitext(os.path.basename(w))[0]
                    d = dur(w)
            if ev is None:
                print('  [SKIP] %-26s 无对应语音素材' % slot)
                continue
            d = d if d is not None else 0.0
            new_dur = round(d + a.pad, 3)
            m = re.search(r'(<m_Name text="%s"/>(?:(?!</m_Timelines>).)*?)</Element>' % slot, txt, re.S)
            if not m:
                print('  [MISS] %s 未在 ast 中找到' % slot); continue
            blk = m.group(1)
            blk2 = re.sub(r'(<m_FXName text=")[^"]*(")', r'\g<1>%s\g<2>' % ev, blk)
            blk2 = re.sub(r'(<m_AnimationName text="[^"]*/>\s*<m_fDuration>)[\d.]+(</m_fDuration>)',
                          r'\g<1>%.6f\g<2>' % new_dur, blk2, count=1)
            txt = txt.replace(blk, blk2, 1)
            print('  [OK] %-26s FX=%-40s Dur=%.2fs (语音 %.2fs + pad %.1fs)' % (slot, ev, new_dur, d, a.pad))
        if txt != orig and not a.dry:
            import shutil
            shutil.copy2(p, p + '.bak_ast')
            open(p, 'wb').write(txt.encode('utf-8'))
            print('  [WRITE] 已写入 (备份 .bak_ast)')
        elif a.dry:
            print('  [DRY] 未写盘')

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('check'); c.add_argument('path')
    p = sub.add_parser('patch'); p.add_argument('path')
    p.add_argument('--media', nargs='+', required=True)
    p.add_argument('--pad', type=float, default=0.5)
    p.add_argument('--map', nargs='*', default=None, help='槽位=事件名 覆盖 (如 01_FIRST_MEET=X_FIRST_MEET_A)')
    p.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'check': cmd_check(a)
    else: cmd_patch(a)

if __name__ == '__main__':
    main()
