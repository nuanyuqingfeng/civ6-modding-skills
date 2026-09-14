# -*- coding: utf-8 -*-
"""
new_bank_project.py -- 克隆模板工程 -> 独立 bank 工程 (素材导入 + work unit 注入 + 可选生成)
适用: sfx 普通音频全自动; voice/bgm 传 --template 指向用户已复制好的教程模板副本。
用法:
  python new_bank_project.py --proj <新工程目录> --bank <Bank名> --media <素材目录|文件...>
        [--template <模板工程>] [--prefix Play_] [--streaming|--nostream] [--generate] [--dry-run]
- 声音名 = 文件名主干; 事件 = <prefix><名> / Stop_<名> 成对
- 默认自动流式: 时长>=30s 开 Stream (可用 --streaming/--nostream 覆盖)
- 模板: FelineJasperKitty (Wwise 2015.1); 关键 GUID 谱系随模板继承
"""
import os, sys, json, glob, uuid, random, shutil, subprocess, argparse
import paths

DEF_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'assets', 'template_slim', 'FelineJasperKitty')
DEF_WWCLI = paths.get('wwcli') or '<未配置 wwcli>'
CONV_OBJ = '{6D1B890C-9826-4384-BF07-C15223E9FB56}'
CONV_WU = '{1517B564-DC3C-401F-A5D3-E764772893A6}'
BUS_OBJ = '{1514A4D8-1DA6-412A-A17E-75CA0C2149F3}'
BUS_WU = '{9E91763E-B8C9-4FEC-A959-7E4171FD2AC9}'
GUID_RE = r'\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}'

def G(): return '{%s}' % str(uuid.uuid4()).upper()
_used = set()
def S():
    while True:
        v = random.randint(100000000, 4290000000)
        if v not in _used:
            _used.add(v); return v

def dur(f):
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json',
                            '-show_streams', f], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        st = json.loads(r.stdout or '{}').get('streams', [{}])[0]
        return float(st.get('duration') or 0)
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
    ap.add_argument('--media', nargs='+', required=True)
    ap.add_argument('--template', default=DEF_TEMPLATE)
    ap.add_argument('--prefix', default='Play_')
    ap.add_argument('--events-wu', default=None, help='默认 <bank>_Events')
    ap.add_argument('--streaming', dest='stream', action='store_true', default=None)
    ap.add_argument('--nostream', dest='stream', action='store_false')
    ap.add_argument('--generate', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    events_wu = a.events_wu or (a.bank + '_Events')

    media = []
    for p in a.media:
        if os.path.isdir(p):
            media += sorted(glob.glob(os.path.join(p, '*.wav')))
        elif os.path.isfile(p):
            media.append(p)
    if not media:
        raise SystemExit('没有找到 wav 素材')
    print('[PROJ] bank=%s | 素材 %d 个 | 模板=%s' % (a.bank, len(media), a.template))
    if not os.path.isdir(a.template):
        raise SystemExit(
            '[FAIL] 模板工程不存在: %s\n'
            '  内置瘦身模板位于 <skill>/assets/template_slim/FelineJasperKitty；\n'
            '  voice/bgm 所需完整模板可运行 scripts/ensure_template.py 获取，或用 --template 指定。' % a.template)

    if a.dry_run:
        for w in media:
            d = dur(w)
            print('   -', os.path.basename(w), '%.1fs' % d, '流式' if (a.stream if a.stream is not None else d >= 30) else '内存')
        print('[PROJ] dry-run 结束'); return

    # 1. 克隆
    DST = a.proj
    if os.path.exists(DST):
        raise SystemExit('目标工程目录已存在: ' + DST)
    def ig(dir, names):
        base = os.path.basename(dir)
        if base == os.path.basename(a.template):
            return {'GeneratedSoundBanks', '.cache'}
        if base == 'SFX':
            return list(names)
        if base == 'Originals':
            return [n for n in names if n == 'WavAnalysis.cache']
        return set()
    shutil.copytree(a.template, DST, ignore=ig)
    # 清理 Wwise/ModBuddy 在模板根目录留下的本机缓存/校验文件；文件名可能含本机用户名，不能写死
    for p in [os.path.join(DST, 'IncrementalSoundBankData.xml')] + glob.glob(os.path.join(DST, '*.validationcache')):
        if os.path.exists(p): os.remove(p)
    os.makedirs(os.path.join(DST, 'GeneratedSoundBanks'), exist_ok=True)

    # 2. 素材
    for w in media:
        shutil.copy2(w, os.path.join(DST, 'Originals', 'SFX', os.path.basename(w)))

    # 3. work units
    wu_mixer, folder_id = G(), G()
    wu_events, wu_bank, bank_id = G(), G(), G()
    meta = []
    for w in media:
        name = os.path.splitext(os.path.basename(w))[0]
        d = dur(w)
        stream = a.stream if a.stream is not None else (d >= 30)
        meta.append(dict(name=name, stream=stream, sound=G(), afs=G(), sshort=S(),
                         ev_play=G(), act_play=G(), el_play=G(),
                         ev_stop=G(), act_stop=G(), el_stop=G()))
    # mixer
    ch = [('\t'*4) + '<Folder Name="%s_SFX" ID="%s">' % (a.bank, folder_id),
          ('\t'*5) + '<ChildrenList>']
    for m in meta:
        ch += ['\r\n'.join([
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
            ('\t'*6) + '</ActiveSourceList>', ('\t'*5) + '</Sound>'])]
    ch += [('\t'*5) + '</ChildrenList>', ('\t'*4) + '</Folder>']
    open(os.path.join(DST, 'Actor-Mixer Hierarchy', '%s_Mixer.wwu' % a.bank), 'wb').write(
        wwu('AudioObjects', a.bank + '_Mixer', wu_mixer, '\r\n'.join(ch)))
    # events
    ev = []
    for m in meta:
        ev.append('\r\n'.join([
            ('\t'*4) + '<Event Name="{p}{n}" ID="{eid}">'.format(p=a.prefix, n=m['name'], eid=m['ev_play']),
            ('\t'*5) + '<ChildrenList>',
            ('\t'*6) + '<Action Name="Play" ID="{aid}" Type="Play" Scope="One" Global="false">'.format(aid=m['act_play']),
            ('\t'*7) + '<ElementList>', ('\t'*8) + '<Element ID="{el}" Global="false">'.format(el=m['el_play']),
            ('\t'*9) + '<ObjectRef Name="{n}" ID="{sid}" WorkUnitID="{wuid}"/>'.format(n=m['name'], sid=m['sound'], wuid=wu_mixer),
            ('\t'*8) + '</Element>', ('\t'*7) + '</ElementList>', ('\t'*6) + '</Action>',
            ('\t'*5) + '</ChildrenList>', ('\t'*4) + '</Event>',
            ('\t'*4) + '<Event Name="Stop_{n}" ID="{eid}">'.format(n=m['name'], eid=m['ev_stop']),
            ('\t'*5) + '<ChildrenList>',
            ('\t'*6) + '<Action Name="Stop" ID="{aid}" Type="Stop" Scope="One" Global="false">'.format(aid=m['act_stop']),
            ('\t'*7) + '<PropertyList>', ('\t'*8) + '<Property Name="FadeTime" Type="Real64" Value="1"/>', ('\t'*7) + '</PropertyList>',
            ('\t'*7) + '<ElementList>', ('\t'*8) + '<Element ID="{el}" Global="false">'.format(el=m['el_stop']),
            ('\t'*9) + '<ObjectRef Name="{n}" ID="{sid}" WorkUnitID="{wuid}"/>'.format(n=m['name'], sid=m['sound'], wuid=wu_mixer),
            ('\t'*8) + '</Element>', ('\t'*7) + '</ElementList>', ('\t'*6) + '</Action>',
            ('\t'*5) + '</ChildrenList>', ('\t'*4) + '</Event>']))
    open(os.path.join(DST, 'Events', '%s.wwu' % events_wu), 'wb').write(
        wwu('Events', events_wu, wu_events, '\r\n'.join(ev)))
    # bank
    refs = []
    for m in meta:
        for k, pre in (('ev_play', a.prefix), ('ev_stop', 'Stop_')):
            refs.append(('\t'*5) + '<ObjectRef Name="{p}{n}" ID="{eid}" WorkUnitID="{wuid}" Filter="7" Origin="Manual"/>'.format(
                p=pre, n=m['name'], eid=m[k], wuid=wu_events))
    bk = ['\r\n'.join([('\t'*4) + '<SoundBank Name="%s" ID="%s">' % (a.bank, bank_id),
                       ('\t'*5) + '<ObjectInclusionList>'])]
    bk += refs
    bk.append('\r\n'.join([('\t'*5) + '</ObjectInclusionList>', ('\t'*5) + '<ObjectExclusionList/>',
                           ('\t'*5) + '<GameSyncExclusionList/>', ('\t'*4) + '</SoundBank>']))
    open(os.path.join(DST, 'SoundBanks', '%s_Banks.wwu' % a.bank), 'wb').write(
        wwu('SoundBanks', a.bank + '_Banks', wu_bank, '\r\n'.join(bk)))
    print('[PROJ] 完成: 3 个 work unit 已注入 (%d 声音 / %d 事件 / 1 bank)' % (len(meta), len(meta)*2))

    # 4. 生成
    if a.generate:
        if not os.path.isfile(DEF_WWCLI):
            raise SystemExit(
                '[FAIL] 未找到 WwiseCLI.exe: %s\n'
                '  请安装 Wwise 2015.1.9，或在 skill 根目录 local_paths.json 中配置 "wwcli" 后重试。' % DEF_WWCLI)
        cmd = [DEF_WWCLI, os.path.join(DST, 'Yuni.wproj'), '-GenerateSoundBanks',
               '-Platform', 'Windows', '-Bank', a.bank, '-Verbose']
        print('[GEN]', ' '.join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                           encoding='utf-8', errors='replace')
        for line in ((r.stdout or '') + (r.stderr or '')).splitlines():
            if 'Status' in line or 'rror' in line:
                print('   ', line)
        print('[GEN] 退出码:', r.returncode)
        od = os.path.join(DST, 'GeneratedSoundBanks', 'Windows')
        if os.path.isdir(od):
            for f in sorted(os.listdir(od)):
                print('   ', f, os.path.getsize(os.path.join(od, f)))
        sys.exit(r.returncode or 0)

if __name__ == '__main__':
    main()
