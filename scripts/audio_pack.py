# -*- coding: utf-8 -*-
"""
audio_pack.py - ShortID 注册表 + 纯 Python bank 结构实验（历史独立打包器内化）

⚠️ EXPERIMENTAL / 已降级：
  正式音频交付请走 Wwise Vorbis 流式（new_bank_project.py / wwise_wire.py → WwiseCLI）。
  早期实机验证已判定：用 ffmpeg 标准 MS ADPCM 内嵌进 WWise 语音模板后，
  游戏按 WWise 私有 ADPCM 解码，产生噪音+闪退，因此 speechbank/plainbank 的产物
  **不得用于正式交付**。本脚本仅保留用于：
  * scan          - 扫描既有成品 bank / 模板工程 WWU，重建 id_registry.json（防冲突基础，仍有效）
  * speechbank    - 实验：纯 Python 重建 Speech.bnk（只做结构/ShortID 研究）
  * plainbank     - 实验：纯 Python 重建普通 bank（只做结构/ShortID 研究）

仍有效的共同规律：
  * Event ShortID = FNV-1(小写事件名) -> 区分靠唯一事件名前缀。
  * 媒体/声音/动作/容器/银行 ID 从注册表避让分配 -> 不同内容全域唯一防覆盖。
  * 锚点 id88602518 / id854467727 / id424381547 由 IdAllocator 自动加入已用集合，一律不发放。

用法：
  python audio_pack.py scan
  [实验] python audio_pack.py speechbank <wav目录> --out <Audio目录> [--bank 名] [--template 模板bnk]
  [实验] python audio_pack.py plainbank <wav目录> --bank <名> --out <Audio目录> [--prefix Play_] [--ini-prefix X]
"""
import os, sys, json, re, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import wwise_shortid as ca
import paths

# skill 本地状态目录（注册表放这里）
STATE_DIR = os.path.join(SKILL, 'state')
REGISTRY = os.path.join(STATE_DIR, 'id_registry.json')

# 模板 Speech.bnk：默认从瘦身模板工程生成一次得到；不存在时提示用 --template 指定
SLIM_TEMPLATE_DIR = os.path.join(SKILL, 'assets', 'template_slim', 'FelineJasperKitty')
DEFAULT_TEMPLATE_BNK = os.path.join(os.path.dirname(SLIM_TEMPLATE_DIR), 'template_speech.bnk')


def _default_finished_mod_dirs():
    """本机先例成品 mod 的 Audio 目录（scan 时扫描，可被 --mods 覆盖）。

    默认路径按本机环境自动探测；示例目录名以实际安装的 mod 为准。
    """
    base = paths.get('p2') or ''
    if not os.path.isdir(base):
        return []
    # 泛化：扫描运行目录下所有含 Audio 产物的 mod，不写死任何项目名
    out = []
    for name in sorted(os.listdir(base)):
        audio = os.path.join(base, name, 'Platforms', 'Windows', 'Audio')
        if os.path.isdir(audio):
            out.append(audio)
    return out


def _default_wwu_dirs():
    """模板工程 WWU 目录（泛化：从 local_paths.json 或本机常见位置探测，可被 --wwu 覆盖）。"""
    v = paths.get('template_full')
    if v and os.path.isdir(v):
        return [v]
    slim = os.path.join(SKILL, 'assets', 'template_slim', 'FelineJasperKitty')
    return [slim] if os.path.isdir(slim) else []


def cmd_scan(args):
    os.makedirs(STATE_DIR, exist_ok=True)
    mods = args.mods if args.mods else _default_finished_mod_dirs()
    wwus = args.wwu if args.wwu else _default_wwu_dirs()
    used = ca.scan_id_registry(mods, wwus)
    reg = ca.IdAllocator(REGISTRY)
    reg.add(used)
    reg.save()
    print(f"[OK] id_registry 已更新: {REGISTRY}")
    print(f"     已用 ShortID {len(reg.used)} 个（含锚点 {len(ca.IdAllocator.ANCHORS)}）")
    return 0


def _write_bank_outputs(out, bank_name, bank_id, voices, ini_prefix='', leader_bank=''):
    evs = sorted((v['event_name'], v['event_id']) for v in voices)
    ev_sorted = sorted((v['event_id'], v['event_name']) for v in voices)
    media = [(v['media_id'], v['event_name'] + '.wav', v['event_name'] + '.wem',
              len(v['wem_bytes'])) for v in voices]

    xml = ca.render_soundbank_xml(bank_name, bank_id, '<audio_project_root>', media, ev_sorted)
    open(os.path.join(out, bank_name + '.xml'), 'w', encoding='utf-8').write(xml)

    txt = ca.render_soundbank_txt(evs, media, leader_bank=leader_bank or bank_name)
    open(os.path.join(out, bank_name + '.txt'), 'w', encoding='utf-8').write(txt)

    ini_name = (ini_prefix or os.path.splitext(bank_name)[0].replace('_Speech', '')) + '_Banks.ini'
    ini_text = (
        ';\n; Sections are defined like so:\n'
        '; Global = banks always resident\n'
        '; Menu = banks loaded only during main menu\n'
        '; InGame = banks loaded during gameplay, either 2D or 3D mode\n'
        '; 2D = banks loaded only during 2D mode gameplay\n'
        '; 3D = banks loaded only during 3D mode gameplay\n'
        '; FMV = banks loaded only during the intro (and outro?) FMV\n;\n\n'
        '[Global]\n\n[Menu]\n\n[InGame]\n' + bank_name + '.bnk\n\n[2D]\n\n[3D]\n\n[FMV]\n'
    )
    open(os.path.join(out, ini_name), 'w', encoding='utf-8').write(ini_text)
    print(f"[OK] 已写出 {bank_name}.xml / {bank_name}.txt / {ini_name}")


_EXP_WARN = (
    "[WARN] 实验性路径！内嵌 MS ADPCM 在游戏内会按 WWise 私有格式解码导致噪音+闪退"
    "（早期实机验证实证）。正式交付请走 Wwise Vorbis 流式（new_bank_project.py）。"
)


def cmd_speechbank(args):
    print(_EXP_WARN)
    wav_dir = os.path.abspath(args.wavdir)
    if not os.path.isdir(wav_dir):
        print(f"[错误] 语音目录不存在: {wav_dir}")
        return 2
    template = args.template or _speechbank_template()
    if not os.path.exists(template):
        print(f"[错误] 找不到模板 Speech.bnk: {template}")
        print("  解决：a) 先在本机用 Wwise/先例生成一份模板 bnk；")
        print("        b) 或 --template 指向任意已知可用的 Speech.bnk（如本机先例 mod 的同名文件）；")
        print("        c) 普通音频请改用 new_bank_project.py（Wwise 工程直改）。")
        return 2

    wavs = sorted(fn for fn in os.listdir(wav_dir) if fn.lower().endswith('.wav'))
    if not wavs:
        print("[错误] 目录下没有 wav 文件")
        return 2

    os.makedirs(STATE_DIR, exist_ok=True)
    reg = ca.IdAllocator(REGISTRY)
    tpl = ca.SpeechTemplates.from_bank(open(template, 'rb').read())
    bank_id = reg.fresh()
    leaf_id = reg.fresh()
    voices = []
    for fn in wavs:
        event_name = os.path.splitext(fn)[0].upper()
        if not event_name or event_name.startswith('_'):
            print(f"[跳过] 忽略文件名: {fn}")
            continue
        wem = ca.wav_to_speech_wem(os.path.join(wav_dir, fn), args.ffmpeg)
        voices.append({
            'event_name': event_name,
            'media_id': reg.fresh(),
            'sound_id': reg.fresh(),
            'action_id': reg.fresh(),
            'event_id': ca.wwise_event_shortid(event_name),
            'wem_bytes': wem,
        })
    if not voices:
        print("[错误] 没有可用的语音")
        return 2
    reg.save()

    bank_name = args.bank or os.path.splitext(os.path.basename(template))[0]
    bank_bytes = ca.build_speech_bank(tpl, bank_id, leaf_id, voices)
    chunks, didx, hirc, _ = ca.parse_bank(bank_bytes)
    assert sum(s for _, _, s in didx) == len(chunks[b'DATA']), 'DIDX != DATA'
    os.makedirs(args.out, exist_ok=True)
    open(os.path.join(args.out, bank_name + '.bnk'), 'wb').write(bank_bytes)
    print(f"[OK] {bank_name}.bnk  {len(bank_bytes)} 字节, 语音 {len(voices)} 条, "
          f"银行ID {bank_id}, 叶容器 {leaf_id}")
    print(f"     事件 ID 示例: {voices[0]['event_name']} -> {voices[0]['event_id']}")
    _write_bank_outputs(args.out, bank_name, bank_id, voices,
                        leader_bank=os.path.splitext(bank_name)[0])
    return 0


def cmd_plainbank(args):
    print(_EXP_WARN)
    wav_dir = os.path.abspath(args.wavdir)
    if not os.path.isdir(wav_dir):
        print(f"[错误] 目录不存在: {wav_dir}")
        return 2
    template = args.template or _speechbank_template()
    if not os.path.exists(template):
        print(f"[错误] 找不到模板 Speech.bnk: {template}（同上，需 --template 或先用 Wwise 生成）")
        return 2

    wavs = sorted(fn for fn in os.listdir(wav_dir) if fn.lower().endswith('.wav'))
    if not wavs:
        print("[错误] 目录下没有 wav")
        return 2

    os.makedirs(STATE_DIR, exist_ok=True)
    tpl = ca.SpeechTemplates.from_bank(open(template, 'rb').read())
    reg = ca.IdAllocator(REGISTRY)
    bank_name = args.bank or 'Plain_Bank'
    bank_id = reg.fresh()
    leaf_id = reg.fresh()
    voices = []
    for fn in wavs:
        stem = os.path.splitext(fn)[0]
        event_name = (args.prefix or 'Play_') + stem
        print(f"    event: {event_name}")
        wem = ca.wav_to_wem(os.path.join(wav_dir, fn),
                            codec=args.codec, channels=args.channels,
                            rate=args.rate, ffmpeg=args.ffmpeg)
        voices.append({
            'event_name': event_name,
            'media_id': reg.fresh(),
            'sound_id': reg.fresh(),
            'action_id': reg.fresh(),
            'event_id': ca.wwise_event_shortid(event_name),
            'wem_bytes': wem,
        })
    reg.save()

    bank_bytes = ca.build_speech_bank(tpl, bank_id, leaf_id, voices)
    chunks, didx, hirc, _ = ca.parse_bank(bank_bytes)
    assert sum(s for _, _, s in didx) == len(chunks[b'DATA'])
    os.makedirs(args.out, exist_ok=True)
    open(os.path.join(args.out, bank_name + '.bnk'), 'wb').write(bank_bytes)
    print(f"[OK] {bank_name}.bnk  {len(bank_bytes)} 字节, {len(voices)} 条音频, "
          f"HIRC {len(hirc)} 对象")
    _write_bank_outputs(args.out, bank_name, bank_id, voices,
                        ini_prefix=args.ini_prefix or os.path.splitext(bank_name)[0],
                        leader_bank='')
    return 0


def _speechbank_template():
    # 优先 skill 内置模板 bnk；不在则返回不存在路径让调用方提示
    if os.path.exists(DEFAULT_TEMPLATE_BNK):
        return DEFAULT_TEMPLATE_BNK
    return DEFAULT_TEMPLATE_BNK


def main():
    ap = argparse.ArgumentParser(description='Civ6 ShortID 注册表 + 实验性纯 Python bank（正式交付走 Wwise Vorbis）')
    sub = ap.add_subparsers(dest='cmd')

    p1 = sub.add_parser('scan', help='扫描并重建 id_registry.json')
    p1.add_argument('--mods', nargs='*', default=None, help='成品 mod Audio 目录（默认本机先例）')
    p1.add_argument('--wwu', nargs='*', default=None, help='模板工程 WWU 目录（默认本机）')
    p1.set_defaults(func=cmd_scan)

    p2 = sub.add_parser('speechbank', help='从 wav 目录生成领袖语音 Speech.bnk')
    p2.add_argument('wavdir')
    p2.add_argument('--bank', default='', help='输出银行名（默认取模板名）')
    p2.add_argument('--template', default='', help='模板 Speech.bnk 路径')
    p2.add_argument('--out', required=True, help='输出 Audio 目录')
    p2.add_argument('--ffmpeg', default='ffmpeg')
    p2.set_defaults(func=cmd_speechbank)

    p3 = sub.add_parser('plainbank', help='普通音频银行：每个 wav=一条 Play_XXX 事件')
    p3.add_argument('wavdir')
    p3.add_argument('--bank', default='Plain_Bank')
    p3.add_argument('--prefix', default='', help='事件名前缀；缺省自动用 Play_')
    p3.add_argument('--template', default='', help='模板语音银行 bnk 路径')
    p3.add_argument('--out', required=True)
    p3.add_argument('--codec', default='adpcm', choices=['adpcm', 'pcm'])
    p3.add_argument('--channels', type=int, default=2, help='声道数(0=保留)')
    p3.add_argument('--rate', type=int, default=48000, help='采样率(0=保留)')
    p3.add_argument('--ffmpeg', default='ffmpeg')
    p3.add_argument('--ini-prefix', default='')
    p3.set_defaults(func=cmd_plainbank)

    args = ap.parse_args()
    if not getattr(args, 'cmd', None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())