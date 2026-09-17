# -*- coding: utf-8 -*-
r"""
unregister_audio.py -- 从 mod 注册点移除音频注册 (与 register_to_mod.py 互逆)
用法:
  python unregister_audio.py --audio-id <id> [--find <mod名> | --mod <目录> | --civ6proj <路径>]
      [--purge-source]   # 同时删除源工程 Platforms/Windows/Audio 下该 bank 的产物
移除内容:
  .modinfo   : <UpdateAudio id=...> 块 + <Files> 内 Platforms/Windows/Audio 条目
  .civ6proj  : CDATA 内 <UpdateAudio ...> 单行 + <Content Include="Platforms\Windows\Audio\..."> 条目
"""
import os, re, sys, glob, shutil, argparse
import xml.etree.ElementTree as ET
import paths

P1 = paths.get('p1') or '<未配置 p1>'
P2 = paths.get('p2') or '<未配置 p2>'

def backup(p):
    b = p + '.bak_unreg'
    if not os.path.exists(b):
        shutil.copy2(p, b)

def clean_modinfo(p, audio_id):
    raw = open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    txt = raw.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in txt else '\n'
    m = re.search(r'[ \t]*<UpdateAudio id="%s">.*?</UpdateAudio>%s?' % (re.escape(audio_id), re.escape(nl)), txt, re.S)
    if m:
        txt = txt[:m.start()] + txt[m.end():]
        print('  [MODINFO] 已移除 UpdateAudio:', audio_id)
    else:
        print('  [MODINFO] 无 UpdateAudio (%s)' % audio_id)
    txt2, n = re.subn(r'[ \t]*<File>Platforms/Windows/Audio/[^<]+</File>%s?' % re.escape(nl), '', txt)
    if n:
        print('  [MODINFO] 已移除 Files 音频条目: %d' % n)
    if txt2 != txt:
        backup(p)
        open(p, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + txt2.encode('utf-8'))
        ET.fromstring(txt2)
        print('  [MODINFO] 写回 + 回验通过')

def clean_civ6proj(p, purge):
    raw = open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    txt = raw.decode('utf-8-sig')
    txt2, n1 = re.subn(r'\s*<UpdateAudio id="[^"]+"><File>Platforms/Windows/Audio/[^<]*</File></UpdateAudio>', '', txt)
    txt2, n2 = re.subn(r'\s*<Content Include="Platforms\\Windows\\Audio\\[^"]+">\s*<SubType>Content</SubType>\s*</Content>', '', txt2)
    print('  [CIV6PROJ] 移除 UpdateAudio x%d, Content x%d' % (n1, n2))
    if txt2 != txt:
        backup(p)
        open(p, 'wb').write((b'\xef\xbb\xbf' if bom else b'') + txt2.encode('utf-8'))
    if purge:
        d = os.path.join(os.path.dirname(p), 'Platforms', 'Windows', 'Audio')
        if os.path.isdir(d):
            shutil.rmtree(d)
            print('  [CIV6PROJ] 已删除源工程音频目录:', d)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audio-id', default=None)
    ap.add_argument('--find', default=None)
    ap.add_argument('--mod', default=None)
    ap.add_argument('--civ6proj', default=None)
    ap.add_argument('--purge-source', action='store_true')
    a = ap.parse_args()
    targets = []
    if a.civ6proj:
        targets.append(('civ6proj', a.civ6proj))
    if a.mod:
        for m in glob.glob(os.path.join(a.mod, '*.modinfo')):
            targets.append(('modinfo', m))
    elif a.find:
        rt = os.path.join(P2, a.find)
        for m in glob.glob(os.path.join(rt, '*.modinfo')):
            targets.append(('modinfo', m))
        hits = glob.glob(os.path.join(P1, a.find, '*', '*.civ6proj')) or glob.glob(os.path.join(P1, a.find, '*.civ6proj'))
        if hits:
            targets.append(('civ6proj', hits[0]))
    if not targets:
        raise SystemExit('未定位到注册点')
    for kind, p in targets:
        print('[UNREG] %s: %s' % (kind, p))
        if kind == 'modinfo':
            if not a.audio_id:
                print('  [SKIP] 需要 --audio-id'); continue
            clean_modinfo(p, a.audio_id)
        else:
            clean_civ6proj(p, a.purge_source)

if __name__ == '__main__':
    main()
