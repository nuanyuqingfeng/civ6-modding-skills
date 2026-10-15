# -*- coding: utf-8 -*-
"""
new_bank_project.py -- 克隆模板工程 -> 独立 bank 工程 (素材导入 + work unit 注入 + 可选生成)
适用: sfx 普通音频全自动; voice 领袖语音走 --category voice 挂到模板手调语音链;
      bgm 文明音乐传 --template 指向用户已复制好的教程模板副本后按 §1.5 半自动。
用法:
  python new_bank_project.py --proj <新工程目录> --bank <Bank名> --media <素材目录|文件...>
        [--category sfx|voice] [--speech-name 名] [--template <模板工程>] [--prefix Play_]
        [--streaming|--nostream] [--generate] [--dry-run]
- 声音名 = 文件名主干
- sfx   : 事件 = <prefix><名> / Stop_<名> 成对, Sound 挂在自建 <bank>_SFX Folder 之下
- voice : 事件 = 裸名(与 .ast 的 m_FXName 一致), 不生成 Stop_ 事件, Sound 挂在
          模板手调链 id88602518 > id854467727 > id424381547 之下(与 JasperKittySpeech 同级),
          由官方全局 Stop_Leader_Speech 命中; 模板对象一个字节不碰
- 默认自动流式: 时长>=30s 开 Stream (可用 --streaming/--nostream 覆盖); voice 一律不流式
- 模板: FelineJasperKitty (Wwise 2015.1); 关键 GUID 谱系随模板继承
"""
import os, re, sys, json, glob, uuid, random, shutil, subprocess, argparse
import paths
from bank_output import normalize_generated_eol

DEF_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'assets', 'template_slim', 'FelineJasperKitty')
DEF_WWCLI = paths.get('wwcli') or '<未配置 wwcli>'
CONV_OBJ = '{6D1B890C-9826-4384-BF07-C15223E9FB56}'
CONV_WU = '{1517B564-DC3C-401F-A5D3-E764772893A6}'
BUS_OBJ = '{1514A4D8-1DA6-412A-A17E-75CA0C2149F3}'
BUS_WU = '{9E91763E-B8C9-4FEC-A959-7E4171FD2AC9}'
REVERB_OBJ = '{5E28702E-D128-4905-BDC0-FD571754AD45}'
GUID_RE = r'\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}'
# 模板手调语音链: 全局 Stop_Leader_Speech 按 ShortID 854467727 寻址, Sound 必须在其子树内
VOICE_PARENT = 'id424381547'
VOICE_CHAIN = 'id88602518 > id854467727 > id424381547'

def G(): return '{%s}' % str(uuid.uuid4()).upper()
_used = set()
def S():
    while True:
        v = random.randint(100000000, 4290000000)
        if v not in _used:
            _used.add(v); return v

def rd(p):
    return open(p, encoding='utf-8').read()

def dur(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json',
                        '-show_streams', f], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    st = json.loads(r.stdout or '{}').get('streams', [{}])[0]
    return float(st.get('duration') or 0)

def wwu(root_tag, wu_name, wu_id, inner):
    T = '\t'
    L = ['<?xml version="1.0" encoding="utf-8"?>',
         '<WwiseDocument Type="WorkUnit" ID="%s" SchemaVersion="70">' % wu_id,
         T + '<%s>' % root_tag,
         T*2 + '<WorkUnit Name="%s" ID="%s" PersistMode="Standalone">' % (wu_name, wu_id),
         T*3 + '<ChildrenList>', inner, T*3 + '</ChildrenList>',
         T*2 + '</WorkUnit>', T + '</%s>' % root_tag, '</WwiseDocument>']
    return ('\r\n'.join(L) + '\r\n').encode('utf-8')

def prop(ind, name, ptype, values):
    L = [ind + '<Property Name="%s" Type="%s">' % (name, ptype), ind + '\t<ValueList>']
    for v in values:
        L.append(ind + '\t\t<Value>%s</Value>' % v)
    L += [ind + '\t</ValueList>', ind + '</Property>']
    return L

def voice_sound_block(m, n):
    """语音 Sound: 不流式 + 默认转换/主总线 + AudioFileSource。n 为 <Sound> 的缩进层数。"""
    T = '\t'
    i = lambda k: T * k
    L = [i(n) + '<Sound Name="%s" ID="%s" ShortID="%d" Type="SoundFX">' % (m['name'], m['sound'], m['sshort']),
         i(n+1) + '<PropertyList>']
    L += prop(i(n+2), 'IsStreamingEnabled', 'bool', ['False'])
    L += [i(n+1) + '</PropertyList>',
          i(n+1) + '<ReferenceList>',
          i(n+2) + '<Reference Name="Conversion"><ObjectRef Name="Default Conversion Settings" ID="%s" WorkUnitID="%s"/></Reference>' % (CONV_OBJ, CONV_WU),
          i(n+2) + '<Reference Name="OutputBus"><ObjectRef Name="Master Audio Bus" ID="%s" WorkUnitID="%s"/></Reference>' % (BUS_OBJ, BUS_WU),
          i(n+1) + '</ReferenceList>',
          i(n+1) + '<ChildrenList>',
          i(n+2) + '<AudioFileSource Name="%s" ID="%s" ShortID="%d">' % (m['name'], m['afs'], S()),
          i(n+3) + '<Language>SFX</Language>',
          i(n+3) + '<AudioFile>%s.wav</AudioFile>' % m['name'],
          i(n+2) + '</AudioFileSource>',
          i(n+1) + '</ChildrenList>',
          i(n+1) + '<ActiveSourceList>',
          i(n+2) + '<ActiveSource Name="%s" ID="%s" Platform="Linked"/>' % (m['name'], m['afs']),
          i(n+1) + '</ActiveSourceList>',
          i(n) + '</Sound>']
    return L

def voice_container_block(speech_name, speech_guid, meta):
    """语音容器: 与模板自带 JasperKittySpeech 同级(缩进 10), 属性照抄模板手调值。"""
    T = '\t'
    i = lambda k: T * k
    L = [i(10) + '<ActorMixer Name="%s" ID="%s" ShortID="%d">' % (speech_name, speech_guid, S()),
         i(11) + '<PropertyList>']
    L += prop(i(12), 'DivergenceCenter', 'int32', ['100'])
    L += prop(i(12), 'IsGlobalLimit', 'int16', ['1'])
    L += prop(i(12), 'MaxSoundPerInstance', 'int16', ['1'])
    L += prop(i(12), 'UseMaxSoundPerInstance', 'bool', ['True'])
    L += prop(i(12), 'UserAuxSendVolume0', 'Real64', ['-11'])
    L += [i(11) + '</PropertyList>',
          i(11) + '<ReferenceList>',
          i(12) + '<Reference Name="Conversion"><ObjectRef Name="Default Conversion Settings" ID="%s" WorkUnitID="%s"/></Reference>' % (CONV_OBJ, CONV_WU),
          i(12) + '<Reference Name="OutputBus"><ObjectRef Name="Master Audio Bus" ID="%s" WorkUnitID="%s"/></Reference>' % (BUS_OBJ, BUS_WU),
          i(12) + '<Reference Name="UserAuxSend0"><ObjectRef Name="Reverb_Leader_Scene" ID="%s" WorkUnitID="%s"/></Reference>' % (REVERB_OBJ, BUS_WU),
          i(11) + '</ReferenceList>',
          i(11) + '<ChildrenList>']
    for m in meta:
        L += voice_sound_block(m, 12)
    L += [i(11) + '</ChildrenList>', i(10) + '</ActorMixer>']
    return L

def mount_voice_container(dst, speech_name, speech_guid, meta):
    """把语音容器增量挂到模板手调链的 id424381547 之下, 返回该 work unit 的 ID。

    模板对象一字不改; 插入锚点按行首匹配, 避免命中更深层的同名收尾标记。
    """
    amh = os.path.join(dst, 'Actor-Mixer Hierarchy', 'LeaderSpeech_Feline.wwu')
    if not os.path.isfile(amh):
        raise SystemExit(
            '[FAIL] 模板缺 Actor-Mixer Hierarchy/LeaderSpeech_Feline.wwu: %s\n'
            '  voice 需要含手调语音链的教程模板; 请用 scripts/ensure_template.py 获取, '
            '或用 --template 指向完整模板工程。' % amh)
    txt = rd(amh)
    m = re.search(r'<WorkUnit\s+Name="[^"]+"\s+ID="(%s)"' % GUID_RE, txt)
    if not m:
        raise SystemExit('[FAIL] %s 缺 WorkUnit 声明' % amh)
    wu_id = m.group(1)
    anchor = re.search(r'<ActorMixer Name="%s"[^>]*>' % re.escape(VOICE_PARENT), txt)
    if not anchor:
        raise SystemExit('[FAIL] 模板缺锚点 ActorMixer %s (语音链 %s)' % (VOICE_PARENT, VOICE_CHAIN))
    close = '\n' + '\t' * 9 + '</ChildrenList>'
    i = txt.find(close, anchor.end())
    if i < 0:
        raise SystemExit('[FAIL] 模板缺 %s 的 ChildrenList 收尾标记' % VOICE_PARENT)
    block = '\n'.join(voice_container_block(speech_name, speech_guid, meta))
    txt = txt[:i + 1] + block + '\n' + txt[i + 1:]
    with open(amh, 'wb') as f:
        f.write(txt.encode('utf-8'))
    return wu_id

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--proj', required=True)
    ap.add_argument('--bank', required=True)
    ap.add_argument('--media', nargs='+', required=True)
    ap.add_argument('--category', choices=['sfx', 'voice'], default='sfx',
                    help='voice: 语音 Sound 挂到模板手调链 %s 之下, 事件用裸名, 不生成 Stop_' % VOICE_CHAIN)
    ap.add_argument('--speech-name', default=None, help='voice: 语音容器名, 默认 <bank>_Speech')
    ap.add_argument('--template', default=DEF_TEMPLATE)
    ap.add_argument('--prefix', default='Play_')
    ap.add_argument('--events-wu', default=None, help='默认 <bank>_Events')
    ap.add_argument('--streaming', dest='stream', action='store_true', default=None)
    ap.add_argument('--nostream', dest='stream', action='store_false')
    ap.add_argument('--generate', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    events_wu = a.events_wu or (a.bank + '_Events')
    speech_name = a.speech_name or (a.bank + '_Speech')
    is_voice = (a.category == 'voice')

    media = []
    for p in a.media:
        if os.path.isdir(p):
            media += sorted(glob.glob(os.path.join(p, '*.wav')))
        elif os.path.isfile(p):
            media.append(p)
    if not media:
        raise SystemExit('没有找到 wav 素材')
    print('[PROJ] bank=%s | 类别=%s | 素材 %d 个 | 模板=%s'
          % (a.bank, a.category, len(media), a.template))
    if not os.path.isdir(a.template):
        raise SystemExit(
            '[FAIL] 模板工程不存在: %s\n'
            '  瘦身模板位于 <skill>/assets/template_slim/FelineJasperKitty（第三方内容，公开仓库中为空属正常）；\n'
            '  voice/bgm 所需完整模板请运行 scripts/ensure_template.py 获取，或用 --template 指定。' % a.template)

    if a.dry_run:
        for w in media:
            d = dur(w)
            stream = False if is_voice else (a.stream if a.stream is not None else d >= 30)
            print('   -', os.path.basename(w), '%.1fs' % d, '流式' if stream else '内存')
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
        stream = False if is_voice else (a.stream if a.stream is not None else d >= 30)
        meta.append(dict(name=name, stream=stream, sound=G(), afs=G(), sshort=S(),
                         ev_play=G(), act_play=G(), el_play=G(),
                         ev_stop=G(), act_stop=G(), el_stop=G()))
    if is_voice:
        # 语音容器挂到模板手调链之下; 事件 WorkUnitID 用该 Actor-Mixer work unit
        speech_guid = G()
        wu_mixer = mount_voice_container(DST, speech_name, speech_guid, meta)
        print('[PROJ] 语音容器 %s 已挂入模板链 %s (work unit %s)'
              % (speech_name, VOICE_CHAIN, wu_mixer))
    else:
        # mixer: 自建扁平 SFX Folder (sfx 走 Master Audio Bus, 不经语音链)
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
    # events: voice 用裸名(与 .ast m_FXName 一致)且不生成 Stop_; sfx 用 <prefix>/Stop_ 成对
    ev = []
    for m in meta:
        if is_voice:
            ev.append('\r\n'.join([
                ('\t'*4) + '<Event Name="{n}" ID="{eid}">'.format(n=m['name'], eid=m['ev_play']),
                ('\t'*5) + '<ChildrenList>',
                ('\t'*6) + '<Action Name="Play" ID="{aid}" Type="Play" Scope="One" Global="false">'.format(aid=m['act_play']),
                ('\t'*7) + '<ElementList>', ('\t'*8) + '<Element ID="{el}" Global="false">'.format(el=m['el_play']),
                ('\t'*9) + '<ObjectRef Name="{n}" ID="{sid}" WorkUnitID="{wuid}"/>'.format(n=m['name'], sid=m['sound'], wuid=wu_mixer),
                ('\t'*8) + '</Element>', ('\t'*7) + '</ElementList>', ('\t'*6) + '</Action>',
                ('\t'*5) + '</ChildrenList>', ('\t'*4) + '</Event>']))
            continue
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
    if is_voice:
        # Filter=7: 连带父链一起入 bank —— 编译产物才会含 854467727 等锚点
        refs.append(('\t'*5) + '<ObjectRef Name="%s" ID="%s" WorkUnitID="%s" Filter="7" Origin="Manual"/>'
                    % (speech_name, speech_guid, wu_mixer))
        for m in meta:
            refs.append(('\t'*5) + '<ObjectRef Name="{n}" ID="{eid}" WorkUnitID="{wuid}" Filter="7" Origin="Manual"/>'.format(
                n=m['name'], eid=m['ev_play'], wuid=wu_events))
    else:
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
    print('[PROJ] 完成: work unit 已注入 (%d 声音 / %d 事件 / 1 bank)'
          % (len(meta), len(ev)))

    # 4. 生成
    if a.generate:
        if not os.path.isfile(DEF_WWCLI):
            raise SystemExit(
                '[FAIL] 未找到 WwiseCLI.exe: %s\n'
                '  该值取自本 skill 的 local_paths.json 的 "wwcli" 键；未配置时为占位符。\n'
                '  注意：local_paths.json 里原本写的是**作者机器**的路径（示例值），别人机器上勿照抄。\n'
                '  请二选一指向你自己的 WwiseCLI.exe：\n'
                '    1) 编辑 %s，写入：{"wwcli": "D:/Wwise_v2015.1.9/Authoring/x64/Release/bin/WwiseCLI.exe"}\n'
                '    2) 或设环境变量 CIV6_WWCLI=<你的 WwiseCLI.exe 绝对路径>\n'
                '  Wwise 2015.1 典型安装位置：<盘符>:/Wwise_v2015.1.9/Authoring/x64/Release/bin/WwiseCLI.exe\n'
                '  （装到默认位置时形如 C:/Program Files (x86)/Audiokinetic/Wwise_v2015.1.9/'
                'Authoring/x64/Release/bin/WwiseCLI.exe）'
                % (DEF_WWCLI, paths.LP))
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
            n_eol = normalize_generated_eol(od)
            if n_eol:
                print('   [EOL] 侧车换行归一 %d 个 (.txt->LF / .xml->CRLF)' % n_eol)
            for f in sorted(os.listdir(od)):
                print('   ', f, os.path.getsize(os.path.join(od, f)))
        sys.exit(r.returncode or 0)

if __name__ == '__main__':
    main()
