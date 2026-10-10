# -*- coding: utf-8 -*-
r"""
unregister_audio.py -- 从 mod 注册点移除音频注册 (与 register_to_mod.py 互逆)
用法:
  python unregister_audio.py --audio-id <id> [--find <mod名> | --mod <目录> | --civ6proj <路径>]
      [--project-root <mod 工程根>]   # 运行目录的 modinfo 不在工程内时必填
移除内容:
  .modinfo   : <UpdateAudio id=...> 块 + <Files> 内 Platforms/Windows/Audio 条目
  .civ6proj  : CDATA 内 <UpdateAudio ...> 单行 + <Content Include="Platforms\Windows\Audio\..."> 条目
回写: 改写结果由 _projwrite 守卫写入 <工程>/workspace/gen/ 的同一相对路径, 由 AI 用文件编辑工具
      写入工程 (退出码 2 并打印清单)。
--purge-source: 另删源工程里该 bank 的产物 (三件套 + 它 xml 引用的 wem) 并清掉 ini 里该 bank 的行。
      .bnk/.wem 属可再生二进制资产 (重新编译 bank 即可重出), 删除不涉及工程代码内容;
      ini 属文本工程文件, 改行走守卫。未给 --bank 时只列出目录内容供确认, 不删任何文件。
"""
import os, re, sys, glob, argparse
import xml.etree.ElementTree as ET
import paths

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _projwrite import workspace_gen, write_project_file, finish
import register_to_mod

P1 = paths.get('p1') or '<未配置 p1>'
P2 = paths.get('p2') or '<未配置 p2>'

def project_root(p, explicit=None):
    """mod 工程根: 显式指定优先, 否则从目标文件向上找含 .civ6proj 的目录"""
    if explicit:
        return os.path.abspath(explicit)
    cur = os.path.dirname(os.path.abspath(p))
    while True:
        if glob.glob(os.path.join(cur, '*.civ6proj')):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit('未定位到工程根 (在运行目录改 modinfo 时请用 --project-root 指定): ' + p)
        cur = parent

def clean_modinfo(p, audio_id, root):
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
        result = write_project_file(p, (b'\xef\xbb\xbf' if bom else b'') + txt2.encode('utf-8'), root)
        ET.fromstring(txt2)
        print('  [MODINFO] 改写结果已入位 (%s) + 回验通过' % result)

def clean_civ6proj(p, purge, root, bank=None):
    raw = open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    txt = raw.decode('utf-8-sig')
    txt2, n1 = re.subn(r'\s*<UpdateAudio id="[^"]+"><File>Platforms/Windows/Audio/[^<]*</File></UpdateAudio>', '', txt)
    txt2, n2 = re.subn(r'\s*<Content Include="Platforms\\Windows\\Audio\\[^"]+">\s*<SubType>Content</SubType>\s*</Content>', '', txt2)
    print('  [CIV6PROJ] 移除 UpdateAudio x%d, Content x%d' % (n1, n2))
    if txt2 != txt:
        result = write_project_file(p, (b'\xef\xbb\xbf' if bom else b'') + txt2.encode('utf-8'), root)
        print('  [CIV6PROJ] 改写结果已入位 (%s): %s' % (result, os.path.join(workspace_gen(root), os.path.relpath(p, root))))
    if purge:
        purge_source(os.path.dirname(p), bank)

def purge_source(srcdir, bank=None):
    """删除源工程音频产物：只删该 bank 的三件套与它 xml 引用的 wem，并移除 ini 里该 bank 的行。

    产物是 .bnk/.wem 等可再生二进制资产（重新编译 bank 即可重出），删除不涉及工程代码内容；
    ini 属文本工程文件，改行走 _projwrite 守卫入位 workspace/gen。
    bank 未指定时列出目录内容供人工确认，不删任何文件。
    """
    audio_dir = os.path.join(srcdir, 'Platforms', 'Windows', 'Audio')
    if not os.path.isdir(audio_dir):
        print('  [PURGE] 源工程无音频目录:', audio_dir)
        return
    if not bank:
        todos = sorted(os.path.basename(f) for f in glob.glob(os.path.join(audio_dir, '*')))
        print('  [PURGE] 未指定 --bank，列出目录内容供确认（未删任何文件）：')
        for n in todos:
            print('      %s' % n)
        return
    names = register_to_mod.bank_media_names(audio_dir, bank)
    removed, missing = [], []
    for n in names:
        target = os.path.join(audio_dir, n)
        if os.path.isfile(target):
            os.remove(target)
            removed.append(n)
        else:
            missing.append(n)
    print('  [PURGE] 已删除 %d 个产物: %s' % (len(removed), ', '.join(removed) if removed else '无'))
    if missing:
        print('  [PURGE] 目录中本就不存在: %s' % ', '.join(missing))
    for ini in sorted(glob.glob(os.path.join(audio_dir, '*_Banks.ini'))):
        raw = open(ini, 'rb').read()
        txt = raw.decode('ascii')
        txt2, n = re.subn(r'%s\.bnk\r?\n' % re.escape(bank), '', txt)
        if n:
            result = write_project_file(ini, txt2.encode('ascii'), project_root(ini))
            print('  [PURGE] ini 移除 %s.bnk 行 (%s): %s' % (bank, result, os.path.basename(ini)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audio-id', default=None)
    ap.add_argument('--find', default=None)
    ap.add_argument('--mod', default=None)
    ap.add_argument('--civ6proj', default=None)
    ap.add_argument('--project-root', default=None, help='mod 工程根（运行目录的 modinfo 不在工程内时必填）')
    ap.add_argument('--purge-source', action='store_true',
                    help='同时删除源工程里该 bank 的产物（三件套 + 它引用的 wem，并清掉 ini 里该 bank 的行）')
    ap.add_argument('--bank', default=None, help='--purge-source 的 bank 名；不给则只列出目录内容供确认')
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
            clean_modinfo(p, a.audio_id, project_root(p, a.project_root))
        else:
            clean_civ6proj(p, a.purge_source, project_root(p, a.project_root), a.bank)
    return finish()

if __name__ == '__main__':
    sys.exit(main())
