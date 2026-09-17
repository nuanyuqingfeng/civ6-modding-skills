# -*- coding: utf-8 -*-
"""
wwise_shortid.py - WWise ShortID 核心规律 + 纯 Python bank 打包核心库。

本模块由早期独立音频打包工具内化而来，核心内容保留：
  * Event ShortID = FNV-1(32) 对小写 UTF-8 事件名哈希
  * Sound/Action/Media/Container 等非事件对象 ID 必须全域唯一
  * 锚点容器 id88602518 / id854467727 / id424381547 禁止改号
  * 用 IdAllocator + 注册表在新增音频时自动避让已用 ID
  * 从模板 Speech.bnk 提取字节模板，再用纯 Python 重建语音/普通音频 bank

本机实证：8/8 事件 ShortID 与成品 mod 完全一致；bank 分块布局与模板一致。
"""
import struct, json, os, re, random, subprocess, tempfile

M32 = 0xFFFFFFFF
FNV_PRIME = 16777619
FNV_OFFSET = 2166136261

ANCHOR_1 = 88602518
ANCHOR_2 = 854467727
ANCHOR_3 = 424381547


# ---------------------------------------------------------------------------
# ShortID 算法
# ---------------------------------------------------------------------------
def wwise_event_shortid(name: str) -> int:
    """WWise Event ShortID = FNV-1(32) on lowercase UTF-8 name."""
    h = FNV_OFFSET
    for b in name.lower().encode('utf-8'):
        h = (h * FNV_PRIME) & M32
        h ^= b
    return h & M32


# ---------------------------------------------------------------------------
# .bnk 解析（模板提取 / 自检）
# ---------------------------------------------------------------------------
def parse_bank(data: bytes):
    """返回 (chunks, didx, hirc, data_body_start)。hirc = list[(type, body)]"""
    pos = 0
    chunks = {}
    didx = []
    hirc = []
    data_body_start = None
    while pos + 8 <= len(data):
        tag = data[pos:pos+4]
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        body = data[pos+8:pos+8+size]
        chunks[tag] = body
        if tag == b'DIDX':
            for k in range(size // 12):
                fid, off, sz = struct.unpack('<III', body[k*12:k*12+12])
                didx.append((fid, off, sz))
        elif tag == b'DATA':
            data_body_start = pos + 8
        elif tag == b'HIRC':
            n = struct.unpack('<I', body[:4])[0]
            p = 4
            for _ in range(n):
                otype = body[p]
                osz = struct.unpack('<I', body[p+1:p+5])[0]
                od = body[p+5:p+5+osz]
                hirc.append((otype, od))
                p += 5 + osz
        pos += 8 + size
    return chunks, didx, hirc, data_body_start


# ---------------------------------------------------------------------------
# 模板提取：从“已知可工作的语音银行”提取字节模板
# ---------------------------------------------------------------------------
class SpeechTemplates:
    """从模板 Speech.bnk 提取 Sound/Action/Event/Anchor/Leaf 的字节模板。"""

    def __init__(self):
        self.sound_tpl = None
        self.action_tpl = None
        self.event_tpl = None
        self.leaf_header = None
        self.anchor_3_tpl = None
        self.anchor_2_tpl = None
        self.anchor_1_tpl = None

    @staticmethod
    def from_bank(data: bytes) -> 'SpeechTemplates':
        _, _, hirc, _ = parse_bank(data)
        t = SpeechTemplates()
        sounds = [od for typ, od in hirc if typ == 2]
        actions = [od for typ, od in hirc if typ == 3]
        events = [od for typ, od in hirc if typ == 4]
        mixers = [od for typ, od in hirc if typ == 7]
        if not sounds or not actions or not events:
            raise ValueError('模板银行缺少语音对象 (type 2/3/4)')
        if not all(len(x) == len(sounds[0]) for x in sounds):
            raise ValueError('声音对象长度不一致')
        t.sound_tpl = bytearray(sounds[0])
        t.action_tpl = bytearray(actions[0])
        t.event_tpl = bytearray(events[0])
        d = {struct.unpack('<I', m[:4])[0]: m for m in mixers}
        if ANCHOR_3 not in d or ANCHOR_2 not in d or ANCHOR_1 not in d:
            raise ValueError('模板银行缺少锚点混音器')
        leaf = [m for k, m in d.items() if k not in (ANCHOR_1, ANCHOR_2, ANCHOR_3)]
        if not leaf:
            raise ValueError('模板银行缺少叶子混音器')
        t.leaf_header = bytearray(leaf[0][:67])
        t.anchor_3_tpl = bytearray(d[ANCHOR_3])
        t.anchor_2_tpl = bytearray(d[ANCHOR_2])
        t.anchor_1_tpl = bytearray(d[ANCHOR_1])
        return t

    def build_sound(self, sound_id, media_id, media_size, leaf_id) -> bytes:
        b = bytearray(self.sound_tpl)
        b[0:4] = struct.pack('<I', sound_id)
        b[9:13] = struct.pack('<I', media_id)
        b[13:17] = struct.pack('<I', media_size)
        b[25:29] = struct.pack('<I', leaf_id)
        return bytes(b)

    def build_action(self, action_id, target_sound_id) -> bytes:
        b = bytearray(self.action_tpl)
        b[0:4] = struct.pack('<I', action_id)
        b[6:10] = struct.pack('<I', target_sound_id)
        return bytes(b)

    def build_event(self, event_id, action_id) -> bytes:
        b = bytearray(self.event_tpl)
        b[0:4] = struct.pack('<I', event_id)
        b[8:12] = struct.pack('<I', action_id)
        return bytes(b)

    def build_leaf_mixer(self, leaf_id, child_sound_ids) -> bytes:
        h = bytearray(self.leaf_header)
        h[0:4] = struct.pack('<I', leaf_id)
        ids = list(child_sound_ids)
        h[63:64] = struct.pack('B', len(ids))
        tail = b''.join(struct.pack('<I', i) for i in ids)
        return bytes(h) + tail

    def build_anchor_3(self, leaf_id) -> bytes:
        b = bytearray(self.anchor_3_tpl)
        b[36:40] = struct.pack('<I', leaf_id)
        return bytes(b)

    def build_anchor_2(self) -> bytes:
        return bytes(self.anchor_2_tpl)

    def build_anchor_1(self) -> bytes:
        return bytes(self.anchor_1_tpl)


# ---------------------------------------------------------------------------
# 语音/普通银行组装
# ---------------------------------------------------------------------------
def build_speech_bank(templates, bank_id, leaf_id, voices, language_id=0):
    """
    voices: list of dicts:
        event_name(str), media_id(int), sound_id(int), action_id(int),
        event_id(int), wem_bytes(bytes)
    """
    bkhd_body = struct.pack('<III', 113, bank_id, language_id) + b'\x00' * 8
    bkhd = b'BKHD' + struct.pack('<I', len(bkhd_body)) + bkhd_body

    data_body = b''.join(v['wem_bytes'] for v in voices)
    didx_body = b''
    off = 0
    for v in voices:
        didx_body += struct.pack('<III', v['media_id'], off, len(v['wem_bytes']))
        off += len(v['wem_bytes'])
    didx = b'DIDX' + struct.pack('<I', len(didx_body)) + didx_body
    data = b'DATA' + struct.pack('<I', len(data_body)) + data_body

    hirc_objs = []
    for v in voices:
        hirc_objs.append((2, templates.build_sound(
            v['sound_id'], v['media_id'], len(v['wem_bytes']), leaf_id)))
    child_ids = [v['sound_id'] for v in voices]
    hirc_objs.append((7, templates.build_leaf_mixer(leaf_id, child_ids)))
    hirc_objs.append((7, templates.build_anchor_3(leaf_id)))
    hirc_objs.append((7, templates.build_anchor_2()))
    hirc_objs.append((7, templates.build_anchor_1()))
    for v in voices:
        hirc_objs.append((3, templates.build_action(v['action_id'], v['sound_id'])))
        hirc_objs.append((4, templates.build_event(v['event_id'], v['action_id'])))

    hirc_body = struct.pack('<I', len(hirc_objs))
    for typ, body in hirc_objs:
        hirc_body += bytes([typ]) + struct.pack('<I', len(body)) + body
    hirc = b'HIRC' + struct.pack('<I', len(hirc_body)) + hirc_body

    return bkhd + didx + data + hirc


# ---------------------------------------------------------------------------
# WAV -> 内嵌 WEM（RIFF/WAVE 字节）
# ---------------------------------------------------------------------------
def wav_to_wem(wav_path: str, codec='adpcm', channels=0, rate=0,
               ffmpeg: str = 'ffmpeg') -> bytes:
    """
    把任意 wav 编码成 WWise 银行可内嵌的 RIFF/WAVE 字节。
      codec   : 'adpcm' -> MS ADPCM (4bit) | 'pcm' -> pcm_s16le
      channels: >0 强制声道数（语音用 1；普通/立体声素材用 2 或保留原样）
      rate    : >0 强制采样率（默认 48000）
    """
    fd, tmp = tempfile.mkstemp(suffix='.wav')
    os.close(fd)
    try:
        cmd = [ffmpeg, '-y', '-v', 'error', '-i', wav_path]
        if channels and channels > 0:
            cmd += ['-ac', str(channels)]
        if rate and rate > 0:
            cmd += ['-ar', str(rate)]
        if codec == 'pcm':
            cmd += ['-c:a', 'pcm_s16le']
        else:
            cmd += ['-c:a', 'adpcm_ms']
        cmd += ['-f', 'wav', tmp]
        subprocess.run(cmd, check=True, capture_output=True)
        return open(tmp, 'rb').read()
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def wav_to_speech_wem(wav_path: str, ffmpeg: str = 'ffmpeg') -> bytes:
    return wav_to_wem(wav_path, codec='adpcm', channels=1, rate=48000, ffmpeg=ffmpeg)


# ---------------------------------------------------------------------------
# ID 注册表：保证新分配的 ShortID 不与已存在内容冲突
# ---------------------------------------------------------------------------
class IdAllocator:
    ANCHORS = {ANCHOR_1, ANCHOR_2, ANCHOR_3}

    def __init__(self, registry_path):
        self.registry_path = registry_path
        self.used = set()
        self.load()

    def load(self):
        if os.path.exists(self.registry_path):
            try:
                data = json.load(open(self.registry_path, encoding='utf-8'))
                self.used = set(int(x) for x in data.get('used_ids', []))
            except Exception:
                self.used = set()
        else:
            self.used = set()
        self.used |= self.ANCHORS

    def save(self):
        tmp = self.registry_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump({'used_ids': sorted(self.used)}, f, indent=1)
        os.replace(tmp, self.registry_path)

    def add(self, values):
        for v in values:
            self.used.add(int(v))

    def fresh(self):
        for _ in range(1000000):
            x = random.randrange(1, 0xFFFFFFFF)
            if x not in self.used:
                self.used.add(x)
                return x
        raise RuntimeError('无法分配空闲 32 位 ID')


def scan_id_registry(finished_mod_dirs=(), wwu_dirs=(), stats=None):
    """扫描成品银行/模板工程 WWU，收集全部已用 ShortID。

    目录不存在时跳过并计数：跳过数会打印出来，并回填到可选的 stats
    （{'skipped_dirs': N, 'skipped_list': [...]}），供 audio_pack.py 的告警引用。
    """
    used = set(IdAllocator.ANCHORS)
    skipped = []
    pat_txt = re.compile(r'\b(\d{1,10})\b')
    pat_short = re.compile(r'ShortID="(\d+)"')
    for d in finished_mod_dirs:
        if not os.path.isdir(d):
            skipped.append(d)
            continue
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            if fn.endswith(('.wem', '.xml', '.txt')):
                try:
                    s = open(p, encoding='utf-8', errors='replace').read()
                except Exception:
                    continue
                used |= set(int(m) for m in pat_txt.findall(s))
    for d in wwu_dirs:
        if not os.path.isdir(d):
            skipped.append(d)
            continue
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith('.wwu'):
                    continue
                try:
                    s = open(os.path.join(root, fn), encoding='utf-8', errors='replace').read()
                except Exception:
                    continue
                used |= set(int(m) for m in pat_short.findall(s))
                used |= set(int(m) for m in re.findall(r'Name="id(\d+)"', s))
    if skipped:
        print('[WARN] scan_id_registry: 跳过 %d 个不存在的目录: %s'
              % (len(skipped), '; '.join(str(x) for x in skipped)))
    if stats is not None:
        stats['skipped_dirs'] = len(skipped)
        stats['skipped_list'] = list(skipped)
    return used


# ---------------------------------------------------------------------------
# 生成配套的 SoundBankInfo .txt / .xml
# ---------------------------------------------------------------------------
def render_soundbank_xml(bank_name, bank_id, project_root, media, events):
    """
    media: list of (file_id, shortname_wav, path_wem, data_size)
    events: list of (event_id, event_name)
    """
    lines = []
    lines.append('<?xml version="1.0" encoding="utf-8"?>')
    lines.append('<SoundBanksInfo Platform="Windows" BasePlatform="Windows" '
                 'SchemaVersion="10" SoundbankVersion="113">')
    lines.append('\t<RootPaths>')
    lines.append(f'\t\t<ProjectRoot>{project_root}</ProjectRoot>')
    lines.append(f'\t\t<SourceFilesRoot>{project_root}.cache\\Windows\\</SourceFilesRoot>')
    lines.append(f'\t\t<SoundBanksRoot>{project_root}GeneratedSoundBanks\\Windows\\</SoundBanksRoot>')
    lines.append('\t\t<ExternalSourcesInputFile></ExternalSourcesInputFile>')
    lines.append(f'\t\t<ExternalSourcesOutputRoot>{project_root}GeneratedSoundBanks\\Windows\\</ExternalSourcesOutputRoot>')
    lines.append('\t</RootPaths>')
    lines.append('\t<SoundBanks>')
    lines.append(f'\t\t<SoundBank Id="{bank_id}" Language="SFX">')
    lines.append(f'\t\t\t<ShortName>{bank_name}</ShortName>')
    lines.append(f'\t\t\t<Path>{bank_name}.bnk</Path>')
    lines.append('\t\t\t<IncludedEvents>')
    for eid, ename in sorted(events, key=lambda x: x[0]):
        lines.append(f'\t\t\t\t<Event Id="{eid}" Name="{ename}"/>')
    lines.append('\t\t\t</IncludedEvents>')
    lines.append('\t\t\t<IncludedMemoryFiles>')
    for fid, shortname, path, dsz in media:
        lines.append(f'\t\t\t\t<File Id="{fid}" Language="SFX">')
        lines.append(f'\t\t\t\t\t<ShortName>{shortname}</ShortName>')
        lines.append(f'\t\t\t\t\t<Path>SFX\\{path}</Path>')
        lines.append('\t\t\t\t</File>')
    lines.append('\t\t\t</IncludedMemoryFiles>')
    lines.append('\t\t</SoundBank>')
    lines.append('\t</SoundBanks>')
    lines.append('</SoundBanksInfo>')
    return '\n'.join(lines) + '\n'


def render_soundbank_txt(events, media, leader_bank=''):
    """按 WWise 导出的 txt 格式渲染。events/media 为列表。"""
    lines = ['Event\tID\tName\t\t\tWwise Object Path\tNotes']
    for ename, eid in sorted(events, key=lambda x: x[1]):
        lines.append(f'\t{eid}\t{ename}\t\t\t\\Default Work Unit\\{ename}\t')
    lines.append('')
    lines.append('In Memory Audio\tID\tName\tAudio source file\t\tWwise Object Path\tNotes\tData Size')
    prefix = leader_bank.upper() if leader_bank else 'BANK'
    for fid, short, path, dsz in media:
        lines.append(f'\t{fid}\t{short}\t\\\\{prefix}\\\\{path}\t\t'
                     f'\\Actor-Mixer Hierarchy\\{prefix}\\{short}\t{dsz}')
    return '\n'.join(lines) + '\n'