# -*- coding: utf-8 -*-
"""
register_to_mod.py -- bank 产物注册到 mod (P1 源工程 .civ6proj / P2 运行目录 .modinfo 双注册)
拷贝: bank 三件套(bnk/xml/txt) + bank xml 内引用的全部流式 wem -> Platforms/Windows/Audio
写盘: <名>_Banks.ini (无BOM/CRLF) + modinfo(UpdateAudio+Files) + civ6proj(CDATA UpdateAudio + Content 条目)
用法:
  python register_to_mod.py --bank-dir <工程>\\GeneratedSoundBanks\\Windows --bank <Bank名> \
      (--find <mod名> | --mod <mod目录>) [--section ingame|global|menu] [--civ6proj <路径>] [--dry-run]
先例: 本地某 .civ6proj mod / 本地某 .modinfo mod 双实证
"""
import os, sys, re, glob, shutil, argparse
import xml.etree.ElementTree as ET
import paths

P1 = paths.get('p1') or '<未配置 p1>'
P2 = paths.get('p2') or '<未配置 p2>'
INI_HEADER = ''';\r
; Sections are defined like so:\r
; Global = banks always resident\r
; Menu = banks loaded only during main menu\r
; InGame = banks loaded during gameplay, either 2D or 3D mode\r
; 2D = banks loaded only during 2D mode gameplay\r
; 3D = banks loaded only during 3D mode gameplay\r
; FMV = banks loaded only during the intro (and outro?) FMV\r
;\r
\r
[Global]\r
\r
[Menu]\r
\r
[InGame]\r
\r
[2D]\r
\r
[3D]\r
\r
[FMV]\r
'''

def backup(p, tag='.bak_reg'):
    b = p + tag
    if not os.path.exists(b):
        shutil.copy2(p, b)

def bank_media(bank_dir, bank):
    """返回 (三件套列表, wem列表)"""
    base = []
    for ext in ('.bnk', '.xml', '.txt'):
        f = os.path.join(bank_dir, bank + ext)
        if os.path.exists(f):
            base.append(f)
    if not base:
        raise SystemExit('bank 产物不存在: ' + os.path.join(bank_dir, bank + '.bnk'))
    wems = []
    xml = os.path.join(bank_dir, bank + '.xml')
    ids = re.findall(r'<File Id="(\d+)" Language="SFX">', open(xml, encoding='utf-8').read())
    for i in sorted(set(ids)):
        w = os.path.join(bank_dir, i + '.wem')
        if os.path.exists(w):
            wems.append(w)
        else:
            print('  [WARN] xml 引用的流式文件缺失:', i + '.wem')
    return base, wems

def find_mod(name):
    """返回 dict(modinfo=路径 or None, civ6proj=路径 or None, srcdir=源工程目录 or None, rtdir=运行目录 or None)"""
    out = dict(modinfo=None, civ6proj=None, srcdir=None, rtdir=None)
    rt = os.path.join(P2, name)
    if os.path.isdir(rt):
        m = glob.glob(os.path.join(rt, '*.modinfo'))
        if m:
            out['modinfo'], out['rtdir'] = m[0], rt
    src = os.path.join(P1, name)
    if os.path.isdir(src):
        for cand in (os.path.join(src, name, name + '.civ6proj'),
                     os.path.join(src, name + '.civ6proj')):
            if os.path.exists(cand):
                out['civ6proj'] = cand
                out['srcdir'] = os.path.dirname(cand)
                break
        if not out['civ6proj']:
            hits = glob.glob(os.path.join(src, '*', '*.civ6proj'))
            if hits:
                out['civ6proj'] = hits[0]
                out['srcdir'] = os.path.dirname(hits[0])
    return out

def choose_ini(audio_dir, bank):
    """选择 bank 注册用的 ini：优先已有同名 <bank>s.ini，其次复用已有 *_Banks.ini（集中式），否则默认 <bank>s.ini。"""
    legacy = os.path.join(audio_dir, bank + 's.ini') if not bank.endswith('s') else os.path.join(audio_dir, bank + '.ini')
    if os.path.exists(legacy):
        return legacy
    banks = sorted(glob.glob(os.path.join(audio_dir, '*_Banks.ini')))
    if banks:
        return banks[0]
    return legacy

def is_backup_or_meta(name):
    """验证时忽略备份/系统元数据文件，避免 .bak_reg 等干扰 磁盘↔清单 一致性。"""
    return name.endswith(('.bak', '.bak_reg')) or '.bak_' in name or name.startswith('.') or name == 'desktop.ini'

def write_ini(audio_dir, bank, section):
    ini = choose_ini(audio_dir, bank)
    txt = INI_HEADER
    if not os.path.exists(ini):
        open(ini, 'wb').write(txt.encode('ascii'))
    b = open(ini, 'rb').read().decode('ascii')
    sec = {'ingame': '[InGame]', 'global': '[Global]', 'menu': '[Menu]'}[section]
    m = re.search(re.escape(sec) + r'\r\n((?:[^\[]|\r\n)*)', b)
    assert m, 'ini 缺少节 ' + sec
    if (bank + '.bnk') in m.group(1):
        print('  [INI] 已存在条目, 跳过:', ini)
        return ini
    b = b[:m.end(1)] + bank + '.bnk\r\n' + b[m.end(1):]
    backup(ini)
    open(ini, 'wb').write(b.encode('ascii'))
    return ini

def rel_audio(fn):
    return 'Platforms/Windows/Audio/' + fn

def verify_modinfo(modinfo, audio_id=None, audio_dir=None):
    """语义校验:
       ① UpdateAudio 的 File 必须指向 .ini(禁止 .wem/.bnk), 且目标 id 恰好 1 个;
       ② 规则: 所有物理文件都必须出现在 Files 节; ini 额外在 UpdateAudio 注册。
       audio_dir 提供时额外校验: 磁盘文件 ↔ Files 清单完全一致(防漏)。
    """
    raw = open(modinfo, 'rb').read()
    txt = raw.decode('utf-8-sig')
    try:
        ET.fromstring(txt)
    except ET.ParseError as e:
        return False, ['XML 解析失败: %s' % e]
    problems = []
    # ① UpdateAudio 语义
    ua = []
    for m in re.finditer(r'<UpdateAudio[^>]*id="([^"]+)"[^>]*>(.*?)</UpdateAudio>', txt, re.S):
        files = re.findall(r'<File>([^<]+)</File>', m.group(2))
        ua.append((m.group(1), files))
        for f in files:
            if not f.endswith('.ini'):
                problems.append('UpdateAudio[%s] 指向非 ini: %s' % (m.group(1), f))
    if audio_id:
        ids = [x[0] for x in ua]
        if ids.count(audio_id) != 1:
            problems.append('UpdateAudio id=%s 应恰好1个, 实得 %d' % (audio_id, ids.count(audio_id)))
    # ② Files 节内条目
    fs = txt[txt.find('<Files>'):txt.find('</Files>')]
    fs_entries = set(re.findall(r'<File>([^<]+)</File>', fs))
    ini_in_files = any(e.endswith('.ini') for e in fs_entries)
    if audio_id:
        # ini 必须同时在 Files 与 UpdateAudio 出现
        ini_refs = [f for _, fs_ in ua for f in fs_ if f.endswith('.ini')]
        if ini_refs and not ini_in_files:
            problems.append('ini 出现在 UpdateAudio 但缺失于 Files 节: %s' % ini_refs)
    # ③ 磁盘 ↔ Files 一致(防漏文件)
    if audio_dir and os.path.isdir(audio_dir):
        disk = set(os.listdir(audio_dir))
        missing = []
        for d in disk:
            if is_backup_or_meta(d):
                continue
            rel = 'Platforms/Windows/Audio/%s' % d
            if rel not in fs_entries:
                missing.append(d)
        if missing:
            problems.append('磁盘有但 Files 缺失 %d 个: %s' % (len(missing), sorted(missing)[:8]))
    return (not problems), problems

def cmd_verify(modinfo, audio_id=None, audio_dir=None):
    ok, problems = verify_modinfo(modinfo, audio_id, audio_dir)
    print('[VERIFY] %s' % ('PASS' if ok else 'FAIL'))
    for p in problems:
        print('   -', p)
    return 0 if ok else 1

def patch_modinfo(modinfo, bank, audio_id, section, files, dry):
    rt_audio = os.path.join(os.path.dirname(modinfo), 'Platforms', 'Windows', 'Audio')
    if not dry:
        os.makedirs(rt_audio, exist_ok=True)
    ini_name = os.path.basename(write_ini(rt_audio, bank, section)) if not dry else os.path.basename(choose_ini(rt_audio, bank))
    # 约束: 所有物理文件(含 ini)都要进 Files; ini 额外在 UpdateAudio 注册
    all_files = list(files) + [os.path.join(rt_audio, ini_name)]
    raw = open(modinfo, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    txt = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in txt else '\n'
    if ('UpdateAudio id="%s"' % audio_id) in txt:
        print('  [MODINFO] UpdateAudio 已存在, 跳过注入')
    else:
        block = ('    <UpdateAudio id="%s">%s' % (audio_id, nl)
                 + '      <File>%s</File>%s' % (rel_audio(ini_name), nl)
                 + '    </UpdateAudio>')
        i = txt.find('<InGameActions>')
        assert i >= 0, 'modinfo 缺 <InGameActions>'
        j = i + len('<InGameActions>')
        txt = txt[:j] + nl + block + txt[j:]
    if '<Files>' in txt:
        fs_start = txt.find('<Files>'); fs_end = txt.find('</Files>')
        fs_region = txt[fs_start:fs_end]
        add = ''.join('    <File>%s</File>' % rel_audio(os.path.basename(f)) + nl
                      for f in all_files
                      if rel_audio(os.path.basename(f)) not in fs_region)
        if add:
            # 只在 <Files> 节内插入(锚定节内第一个 4空格 <File> 行前; 无则插在 </Files> 前)
            m2 = re.search(r'\n    <File>', fs_region)
            if m2:
                ins_at = fs_start + m2.start() + 1
                txt = txt[:ins_at] + add + txt[ins_at:]
            else:
                fi = txt.rfind('</Files>')
                ls = txt.rfind('\n', 0, fi) + 1
                txt = txt[:ls] + add + txt[ls:]
    else:
        print('  [MODINFO] 无 <Files> 节 (散装 mod 可省), 跳过 Files')
    if dry:
        print('  [DRY] modinfo 将写入(若与原文不同):', modinfo)
        return
    backup(modinfo)
    open(modinfo, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + txt.encode('utf-8'))
    ok, problems = verify_modinfo(modinfo, audio_id, rt_audio)
    if not ok:
        raise SystemExit('[FAIL] 注册后语义校验未通过——UpdateAudio 只指向 ini 且所有物理文件进 Files:\n  ' + '\n  '.join(problems))
    print('  [MODINFO] 注册完成 + 语义校验通过:', modinfo)

def verify_civ6proj(civ6proj, audio_id=None, audio_dir=None):
    """语义校验 .civ6proj:
       ① CDATA 内 UpdateAudio 只指向 .ini, 目标 id 恰好 1 个;
       ② 规则: 所有物理文件都必须在 Content Include 注册; ini 额外在 CDATA UpdateAudio 注册。
       audio_dir 提供时校验: 磁盘文件 ↔ Content 清单一致(防漏)。
    """
    raw = open(civ6proj, 'rb').read()
    txt = raw.decode('utf-8-sig')
    try:
        ET.fromstring(txt)
    except ET.ParseError as e:
        return False, ['XML 解析失败: %s' % e]
    problems = []
    # ① CDATA 内 UpdateAudio 语义
    cdata = txt[txt.find('<InGameActionData>'):]
    ua = []
    for m in re.finditer(r'<UpdateAudio[^>]*id="([^"]+)"[^>]*>(.*?)</UpdateAudio>', cdata, re.S):
        files = re.findall(r'<File>([^<]+)</File>', m.group(2))
        ua.append((m.group(1), files))
        for f in files:
            if not f.endswith('.ini'):
                problems.append('civ6proj UpdateAudio[%s] 指向非 ini: %s' % (m.group(1), f))
    if audio_id:
        ids = [x[0] for x in ua]
        if ids.count(audio_id) != 1:
            problems.append('civ6proj UpdateAudio id=%s 应恰好1个, 实得 %d' % (audio_id, ids.count(audio_id)))
    # ② Content Include 清单
    content = set(re.findall(r'<Content Include="(Platforms\\Windows\\Audio\\[^"]+)"', txt))
    content_rel = set(c.replace('\\', '/') for c in content)
    if audio_id:
        ini_refs = [f for _, fs in ua for f in fs if f.endswith('.ini')]
        if ini_refs:
            ini_rel = ini_refs[0].replace('\\', '/')
            if ini_rel not in content_rel:
                problems.append('civ6proj: ini 在 CDATA UpdateAudio 但缺失于 Content: %s' % ini_refs[0])
    # ③ 磁盘 ↔ Content 一致
    if audio_dir and os.path.isdir(audio_dir):
        disk = set(os.listdir(audio_dir))
        missing = []
        for d in disk:
            if is_backup_or_meta(d):
                continue
            rel = 'Platforms/Windows/Audio/%s' % d
            if rel not in content_rel:
                missing.append(d)
        if missing:
            problems.append('civ6proj: 磁盘有但 Content 缺失 %d 个: %s' % (len(missing), sorted(missing)[:8]))
    return (not problems), problems

def cmd_verify_civ6proj(civ6proj, audio_id=None, audio_dir=None):
    ok, problems = verify_civ6proj(civ6proj, audio_id, audio_dir)
    print('[VERIFY-civ6proj] %s' % ('PASS' if ok else 'FAIL'))
    for p in problems:
        print('   -', p)
    return 0 if ok else 1

def patch_civ6proj(civ6proj, srcdir, bank, audio_id, section, files, dry):
    audio_dir = os.path.join(srcdir, 'Platforms', 'Windows', 'Audio')
    ini_name = os.path.basename(choose_ini(audio_dir, bank))
    if not dry:
        os.makedirs(audio_dir, exist_ok=True)
        write_ini(audio_dir, bank, section)
    raw = open(civ6proj, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    txt = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in txt else '\n'
    if ('UpdateAudio id="%s"' % audio_id) not in txt:
        ins = '\n      <UpdateAudio id="%s"><File>%s</File></UpdateAudio>' % (audio_id, rel_audio(ini_name))
        i = txt.find('</InGameActions>')
        assert i >= 0, 'civ6proj 缺 InGameActions CDATA'
        txt = txt[:i] + ins + txt[i:]
    else:
        print('  [CIV6PROJ] UpdateAudio 已存在, 跳过注入')
    need = [os.path.basename(f) for f in files
            if ('Include="Platforms\\Windows\\Audio\\%s"' % os.path.basename(f)) not in txt]
    if need:
        items = []
        for fn in need:
            items += ['    <Content Include="Platforms\\Windows\\Audio\\%s">' % fn,
                      '      <SubType>Content</SubType>',
                      '    </Content>']
        add = '\r\n'.join(items) + '\r\n'
        lines = txt.split('\n')
        idx = next((k for k, l in enumerate(lines) if '<Content Include="Platforms' in l), None)
        if idx is None:
            idx = next(k for k, l in enumerate(lines) if '<Content Include="' in l)
        lines.insert(idx, add.rstrip('\r\n'))
        txt = '\n'.join(lines)
    if dry:
        print('  [DRY] civ6proj 将写入(若与原文不同):', civ6proj)
        return
    backup(civ6proj)
    open(civ6proj, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + txt.encode('utf-8'))
    try:
        ET.fromstring(txt)
        print('  [CIV6PROJ] 注册完成 + XML 回验通过:', civ6proj)
    except ET.ParseError as e:
        print('  [CIV6PROJ] 已写入, 但 XML 回验警告:', e)
    # 拷贝产物到源工程
    for f in files:
        shutil.copy2(f, os.path.join(audio_dir, os.path.basename(f)))
    print('  [CIV6PROJ] 产物已拷入源工程:', audio_dir)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bank-dir', default=None)
    ap.add_argument('--bank', default=None)
    ap.add_argument('--find', default=None, help='mod 名 (在 P1/P2 自动定位)')
    ap.add_argument('--mod', default=None, help='mod 目录 (含 .modinfo)')
    ap.add_argument('--section', choices=['ingame', 'global', 'menu'], default='ingame')
    ap.add_argument('--audio-id', default=None, help='UpdateAudio id, 默认 <Bank>_Audio')
    ap.add_argument('--civ6proj', default=None)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verify', action='store_true', help='仅语义校验既有 modinfo (UpdateAudio 只指向 ini)')
    a = ap.parse_args()
    if a.verify:
        targets = []
        if a.mod:
            targets += glob.glob(os.path.join(a.mod, '*.modinfo'))
        elif a.find:
            targets += glob.glob(os.path.join(P2, a.find, '*.modinfo'))
        if not targets:
            raise SystemExit('未定位到 modinfo (用 --mod 或 --find)')
        rc = 0
        for mi in targets:
            ad = os.path.join(os.path.dirname(mi), 'Platforms', 'Windows', 'Audio')
            rc |= cmd_verify(mi, a.audio_id, ad if os.path.isdir(ad) else None)
        sys.exit(rc)
    if not a.bank_dir or not a.bank:
        raise SystemExit('注册模式需要 --bank-dir 与 --bank (或使用 --verify)')
    audio_id = a.audio_id or (a.bank + '_Audio')
    base, wems = bank_media(a.bank_dir, a.bank)
    files = base + wems
    print('[REG] bank=%s | 产物 %d 个 (三件套 %d + 流式 wem %d)'
          % (a.bank, len(files), len(base), len(wems)))

    targets = []
    if a.mod:
        mi = glob.glob(os.path.join(a.mod, '*.modinfo'))
        targets.append(dict(modinfo=mi[0] if mi else None, rtdir=a.mod,
                            civ6proj=a.civ6proj, srcdir=None))
    else:
        t = find_mod(a.find)
        if a.civ6proj:
            t['civ6proj'] = a.civ6proj
            t['srcdir'] = os.path.dirname(a.civ6proj)
        targets.append(t)
    if not any(t['modinfo'] or t['civ6proj'] for t in targets):
        raise SystemExit('未定位到 mod (P1/P2 均未命中 %s), 可用 --mod 或 --civ6proj 指定' % a.find)

    for t in targets:
        # 拷贝到运行目录
        if t['rtdir'] and t['modinfo']:
            ad = os.path.join(t['rtdir'], 'Platforms', 'Windows', 'Audio')
            if not a.dry_run:
                os.makedirs(ad, exist_ok=True)
                for f in files:
                    shutil.copy2(f, os.path.join(ad, os.path.basename(f)))
            print('  [COPY] 运行目录 %s <- %d 个文件' % (ad, len(files)))
            patch_modinfo(t['modinfo'], a.bank, audio_id, a.section, files, a.dry_run)
        # 源工程
        if t['civ6proj']:
            patch_civ6proj(t['civ6proj'], t['srcdir'], a.bank, audio_id, a.section,
                           files, a.dry_run)
    print('[REG] 完成%s' % (' (dry-run 未写盘)' if a.dry_run else ''))

if __name__ == '__main__':
    main()
