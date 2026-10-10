# -*- coding: utf-8 -*-
"""
build_combination_bank.py -- 组合式 bank 构建器（乐队/分层音频专用）
N 个独立分轨 sound + 全部非空组合的事件：Play 事件含 N 个 Play 动作（引擎并轨合成），
Stop 事件含对应 N 个 Stop 动作。UI/Lua 端无需任何修改（事件名 = 前缀+组合码）。
用法:
  python build_combination_bank.py --proj <工程目录> --bank <Bank名> \
      --stems a.wav b.wav c.wav d.wav --codes C,D,H,L [--prefix Play_] [--dry]
前置: 分轨 wav 已放入工程 Originals/SFX；同名旧 work unit 会被替换（自动备份）。
"""
import os, re, sys, glob, uuid, random, shutil, argparse
from itertools import combinations

CONV_OBJ = '{6D1B890C-9826-4384-BF07-C15223E9FB56}'
CONV_WU = '{1517B564-DC3C-401F-A5D3-E764772893A6}'
BUS_OBJ = '{1514A4D8-1DA6-412A-A17E-75CA0C2149F3}'
BUS_WU = '{9E91763E-B8C9-4FEC-A959-7E4171FD2AC9}'

def G(): return '{%s}' % str(uuid.uuid4()).upper()
_used = set()
def S():
    while True:
        v = random.randint(100000000, 4290000000)
        if v not in _used:
            _used.add(v); return v

def dur(f):
    import wave
    try:
        w = wave.open(f, 'rb'); d = w.getnframes() / float(w.getframerate()); w.close(); return d
    except Exception:
        return 0.0

def wwu(root_tag, wu_name, wu_id, inner):
    T = '\t'
    L = ['<?xml version="1.0" encoding="utf-8"?>',
         '<WwiseDocument Type="WorkUnit" ID="%s" SchemaVersion="70">' % wu_id,
         T + '<%s>' % root_tag,
         T*2 + '<WorkUnit Name="%s" ID="%s" PersistMode="Standalone">' % (wu_name, wu_id),
         T*3 + '<ChildrenList>', inner, T*3 + '</ChildrenList>',
         T*2 + '</WorkUnit>', T + '</%s>' % root_tag, '</WwiseDocument>']
    return ('\r\n'.join(L) + '\r\n').encode('utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--proj', required=True)
    ap.add_argument('--bank', required=True)
    ap.add_argument('--stems', nargs='+', required=True)
    ap.add_argument('--codes', required=True, help='逗号分隔, 与 --stems 一一对应, 如 C,D,H,L')
    ap.add_argument('--event-base', default='', help='事件名基段: 事件 = <prefix><base><组合码>, 如 MyBank_')
    ap.add_argument('--prefix', default='Play_')
    ap.add_argument('--streaming/--nostream', dest='stream', action='store_true', default=None)
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    codes = a.codes.split(',')
    assert len(codes) == len(a.stems), '分轨数与代码数不一致'
    names = [os.path.splitext(os.path.basename(w))[0] for w in a.stems]

    wu_mixer, wu_events, wu_bank = G(), G(), G()
    folder_id, bank_id = G(), G()
    meta = []
    for code, w in zip(codes, a.stems):
        name = os.path.splitext(os.path.basename(w))[0]
        stream = a.stream if a.stream is not None else (dur(os.path.join(a.proj, 'Originals', 'SFX', os.path.basename(w))) >= 30)
        meta.append(dict(code=code, name=name, stream=stream, sound=G(), afs=G(), sshort=S()))
    combos = []
    for size in range(1, len(codes) + 1):
        for cb in combinations(codes, size):
            combos.append(cb)

    # --- mixer ---
    ch = [('\t'*4) + '<Folder Name="%s_SFX" ID="%s">' % (a.bank, folder_id),
          ('\t'*5) + '<ChildrenList>']
    for m in meta:
        ch.append('\r\n'.join([
            ('\t'*5) + '<Sound Name="{n}" ID="{sid}" ShortID="{ss}" Type="SoundFX">'.format(n=m['name'], sid=m['sound'], ss=m['sshort']),
            ('\t'*6) + '<PropertyList>',
            ('\t'*7) + '<Property Name="IsStreamingEnabled" Type="bool">',
            ('\t'*8) + '<ValueList>', ('\t'*9) + '<Value>%s</Value>' % ('True' if m['stream'] else 'False'),
            ('\t'*8) + '</ValueList>', ('\t'*7) + '</Property>', ('\t'*6) + '</PropertyList>',
            ('\t'*6) + '<ReferenceList>',
            ('\t'*7) + '<Reference Name="Conversion"><ObjectRef Name="Default Conversion Settings" ID="%s" WorkUnitID="%s"/></Reference>' % (CONV_OBJ, CONV_WU),
            ('\t'*7) + '<Reference Name="OutputBus"><ObjectRef Name="Master Audio Bus" ID="%s" WorkUnitID="%s"/></Reference>' % (BUS_OBJ, BUS_WU),
            ('\t'*6) + '</ReferenceList>',
            ('\t'*6) + '<ChildrenList>',
            ('\t'*7) + '<AudioFileSource Name="{n}" ID="{aid}">'.format(n=m['name'], aid=m['afs']),
            ('\t'*8) + '<Language>SFX</Language>',
            ('\t'*8) + '<AudioFile>{n}.wav</AudioFile>'.format(n=m['name']),
            ('\t'*7) + '</AudioFileSource>', ('\t'*6) + '</ChildrenList>',
            ('\t'*6) + '<ActiveSourceList>',
            ('\t'*7) + '<ActiveSource Name="{n}" ID="{aid}" Platform="Linked"/>'.format(n=m['name'], aid=m['afs']),
            ('\t'*6) + '</ActiveSourceList>', ('\t'*5) + '</Sound>']))
    ch += [('\t'*5) + '</ChildrenList>', ('\t'*4) + '</Folder>']

    # --- events: 每个组合 = 1 Play 事件(多动作) + 1 Stop 事件(多动作) ---
    ev = []
    ev_guid = {}
    for cb in combos:
        code = ''.join(cb)
        stems = [m for m in meta if m['code'] in cb]
        for typ, pre in (('Play', a.prefix), ('Stop', 'Stop_')):
            eid = G(); ev_guid[pre + a.event_base + code] = eid
            acts = []
            for i, m in enumerate(stems):
                acts.append('\r\n'.join([
                    ('\t'*6) + '<Action Name="%s" ID="%s" Type="%s" Scope="One" Global="false">' % (typ, G(), typ),
                    (('\t'*7) + '<PropertyList>\r\n\t\t\t\t\t\t\t<Property Name="FadeTime" Type="Real64" Value="1"/>\r\n\t\t\t\t\t\t\t</PropertyList>') if typ == 'Stop' else '',
                    ('\t'*7) + '<ElementList>',
                    ('\t'*8) + '<Element ID="%s" Global="false">' % G(),
                    ('\t'*9) + '<ObjectRef Name="%s" ID="%s" WorkUnitID="%s"/>' % (m['name'], m['sound'], wu_mixer),
                    ('\t'*8) + '</Element>', ('\t'*7) + '</ElementList>', ('\t'*6) + '</Action>']))
            body = '\r\n'.join(x for x in acts if x)
            ev.append('\r\n'.join([
                ('\t'*4) + '<Event Name="%s%s%s" ID="%s">' % (pre, a.event_base, code, eid),
                ('\t'*5) + '<ChildrenList>', body,
                ('\t'*5) + '</ChildrenList>', ('\t'*4) + '</Event>']))
    # --- bank ---
    refs = ['\t\t\t\t\t\t<ObjectRef Name="%s" ID="%s" WorkUnitID="%s" Filter="7" Origin="Manual"/>'
            % (k, v, wu_events) for k, v in sorted(ev_guid.items())]
    bk = ['\r\n'.join([('\t'*4) + '<SoundBank Name="%s" ID="%s">' % (a.bank, bank_id),
                       ('\t'*5) + '<ObjectInclusionList>'])] + refs
    bk.append('\r\n'.join([('\t'*5) + '</ObjectInclusionList>', ('\t'*5) + '<ObjectExclusionList/>',
                           ('\t'*5) + '<GameSyncExclusionList/>', ('\t'*4) + '</SoundBank>']))

    if a.dry:
        print('[DRY] 分轨 %d | 组合事件 %d 对 | 声音: %s' % (len(meta), len(combos), [m['name'] for m in meta]))
        return
    def write(sub, fname, root_tag, wu_name, wu_id, inner):
        p = os.path.join(a.proj, sub, fname)
        if os.path.exists(p):
            shutil.copy2(p, p + '.bak_rebuild')
        open(p, 'wb').write(wwu(root_tag, wu_name, wu_id, inner))
        print('  [W] %s' % p)
    write('Actor-Mixer Hierarchy', '%s_Mixer.wwu' % a.bank, 'AudioObjects', a.bank + '_Mixer', wu_mixer, '\r\n'.join(ch))
    write('Events', '%s_Events.wwu' % a.bank, 'Events', a.bank + '_Events', wu_events, '\r\n'.join(ev))
    write('SoundBanks', '%s_Banks.wwu' % a.bank, 'SoundBanks', a.bank + '_Banks', wu_bank, '\r\n'.join(bk))
    print('[DONE] 分轨 %d, 组合 %d 对(Play/Stop), bank 引用 %d 事件' % (len(meta), len(combos), len(ev_guid)))

if __name__ == '__main__':
    main()
