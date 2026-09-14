# -*- coding: utf-8 -*-
"""
wwise_wire.py -- Wwise 工程直改工具 (Wwise 2015.x, Yuni 谱系工程实测)
用途: 用户在 Wwise GUI 导入素材并保存后, 由本工具接管"改名/建事件/挂bank"的机械步骤。

用法:
  扫描   python wwise_wire.py <工程目录> --scan
  接线   python wwise_wire.py <工程目录> --wire <BANK名> [--events-wu <名称>]
                [--play-prefix Play_] [--stop-prefix Stop_]
                [--only <名称子串>] [--max N] [--dry-run]
  改名   python wwise_wire.py <工程目录> --rename-event <旧事件名> <新事件名>
  生成   python wwise_wire.py <工程目录> --generate [BANK名...]

铁律:
  1) 运行前 Wwise 必须关闭(或已保存且不再保存), 否则 GUI 内存态会覆盖直改结果;
  2) 只做增量插入与按 GUID 的 Name 更新, 绝不重排/重写原有对象;
  3) 事件引用一律走 GUID, 改名不换 ID, 引擎侧零风险。
"""
import os, re, sys, glob, uuid, random, shutil, subprocess
import paths

WWCLI = paths.get('wwcli') or '<未配置 wwcli>'
GUID_RE = r'\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}'

def G(): return '{%s}' % str(uuid.uuid4()).upper()
_used_short = set()
def S():
    while True:
        v = random.randint(100000000, 4290000000)
        if v not in _used_short:
            _used_short.add(v); return v

def rd(p):
    for enc in ('utf-8', 'utf-8-sig'):
        try: return open(p, encoding=enc).read()
        except UnicodeError: continue
    return open(p, encoding='utf-8', errors='replace').read()

def backup(p):
    bp = p + '.bak_wire'
    if not os.path.exists(bp): shutil.copy2(p, bp)

def list_wwu(proj, sub):
    return sorted(glob.glob(os.path.join(proj, sub, '*.wwu')))

# ---------------- 解析 ----------------
def parse_sounds(proj):
    out = []  # (name, guid, wu_path)
    for p in list_wwu(proj, 'Actor-Mixer Hierarchy'):
        txt = rd(p)
        for m in re.finditer(r'<Sound\s+Name="([^"]+)"\s+ID="(%s)"' % GUID_RE, txt):
            out.append((m.group(1), m.group(2), p))
    return out

def parse_events(proj):
    out = []  # (name, guid, targets(list), wu_path)
    for p in list_wwu(proj, 'Events'):
        txt = rd(p)
        for m in re.finditer(r'<Event\s+Name="([^"]+)"\s+ID="(%s)">(.*?)</Event>' % GUID_RE, txt, re.S):
            targets = re.findall(r'<ObjectRef\s+Name="[^"]*"\s+ID="(%s)"' % GUID_RE, m.group(3))
            out.append((m.group(1), m.group(2), targets, p))
    return out

def parse_banks(proj):
    out = []  # (name, guid, [event names], wu_path)
    for p in list_wwu(proj, 'SoundBanks'):
        txt = rd(p)
        for m in re.finditer(r'<SoundBank\s+Name="([^"]+)"\s+ID="(%s)">(.*?)</SoundBank>' % GUID_RE, txt, re.S):
            refs = re.findall(r'<ObjectRef\s+Name="([^"]*)"[^>]*Filter="7"', m.group(3))
            out.append((m.group(1), m.group(2), refs, p))
    return out

# ---------------- scan ----------------
def do_scan(proj):
    sounds = parse_sounds(proj); events = parse_events(proj); banks = parse_banks(proj)
    wired = set()
    for name, guid, targets, _ in events:
        for t in targets: wired.add(t)
    unwired = [(n, g, w) for (n, g, w) in sounds if g not in wired]
    print('[SCAN] 工程:', proj)
    print('  Sound 对象: %d 个 | 事件: %d 个 | bank: %d 个' % (len(sounds), len(events), len(banks)))
    for bn, _, refs, _ in banks:
        print('  bank [%s]: %d 个事件引用' % (bn, len(refs)))
    print('  未接线索材 (无可播放事件): %d 个' % len(unwired))
    for n, g, w in unwired:
        print('     -', n, '  (', os.path.basename(w), ')')
    dangling = [(n, t) for (n, _, ts, _) in events for t in ts
                if t not in {g for (_, g, _) in sounds}]
    if dangling:
        print('  指向非 Sound 目标的事件动作 (容器/结构, 工具不处理): %d 个' % len(dangling))
    return unwired

# ---------------- wire ----------------
def ev_xml(indent, name, guid, act, typ, target, wu_mixer, is_stop):
    L = []
    L.append(indent + '<Event Name="%s" ID="%s">' % (name, guid))
    L.append(indent + '\t<ChildrenList>')
    props = ''
    if is_stop:
        props = (indent + '\t\t<PropertyList>\r\n'
                 + indent + '\t\t\t<Property Name="FadeTime" Type="Real64" Value="1"/>\r\n'
                 + indent + '\t\t</PropertyList>\r\n')
    L.append(indent + '\t\t<Action Name="%s" ID="%s" Type="%s" Scope="One" Global="false">' % (act, G(), typ))
    if props: L.append(props.rstrip('\r\n'))
    L.append(indent + '\t\t\t<ElementList>')
    L.append(indent + '\t\t\t\t<Element ID="%s" Global="false">' % G())
    L.append(indent + '\t\t\t\t\t<ObjectRef Name="%s" ID="%s" WorkUnitID="%s"/>' % (target[0], target[1], wu_mixer))
    L.append(indent + '\t\t\t\t</Element>')
    L.append(indent + '\t\t\t</ElementList>')
    L.append(indent + '\t\t</Action>')
    L.append(indent + '\t</ChildrenList>')
    L.append(indent + '</Event>')
    return '\r\n'.join(L)

def do_wire(proj, bank, events_wu, play_prefix, stop_prefix, only, maxlen, dry):
    sounds = parse_sounds(proj); events = parse_events(proj); banks = parse_banks(proj)
    wired = {t for (_, _, ts, _) in events for t in ts}
    todo = [(n, g, w) for (n, g, w) in sounds
            if g not in wired and (only is None or only in n)][:maxlen]
    if not todo:
        print('[WIRE] 没有需要接线的素材'); return
    print('[WIRE] 待接线 %d 个:' % len(todo))
    for n, g, w in todo: print('     -', n)
    if dry:
        print('[WIRE] dry-run, 未写盘'); return
    # 目标 bank
    b = [x for x in banks if x[0] == bank]
    if not b:
        raise SystemExit('bank 不存在: %s (可先用 Wwise GUI 建一个再保存)' % bank)
    bpath = b[0][3]
    # 目标 events work unit
    efile = None
    for p in list_wwu(proj, 'Events'):
        if re.search(r'<WorkUnit\s+Name="%s"' % re.escape(events_wu), rd(p)):
            efile = p; break
    if efile is None:
        raise SystemExit('Events work unit 不存在: %s' % events_wu)
    etxt = rd(efile)
    ind = re.search(r'(\t+)<Event\s', etxt)
    indent = ind.group(1) if ind else '\t\t\t\t'
    wu_mixer = {w: re.search(r'<WorkUnit\s+Name="[^"]+"\s+ID="(%s)"' % GUID_RE, rd(w)).group(1)
                for (_, _, w) in todo}
    blocks = []
    for (n, g, w) in todo:
        blocks.append(ev_xml(indent, play_prefix + n, G(), 'Play', 'Play', (n, g), wu_mixer[w], False))
        blocks.append(ev_xml(indent, stop_prefix + n, G(), 'Stop', 'Stop', (n, g), wu_mixer[w], True))
    backup(efile)
    key = indent[:-1] + '</ChildrenList>'
    i = etxt.rfind(key)
    assert i > 0, 'Events work unit 结构异常'
    etxt = etxt[:i] + ('\r\n'.join(blocks) + '\r\n') + etxt[i:]
    open(efile, 'wb').write(etxt.encode('utf-8'))
    print('[WIRE] 事件已写入:', os.path.basename(efile), '(%d 个新事件)' % (len(blocks)))
    # bank 追加
    btxt = rd(bpath)
    m = re.search(r'(<SoundBank\s+Name="%s".*?)(\s*</ObjectInclusionList>)' % re.escape(bank), btxt, re.S)
    assert m, 'bank 块异常'
    refs = []
    for (n, g, w) in todo:
        refs.append('<ObjectRef Name="%s%s" ID="%s" WorkUnitID="%s" Filter="7" Origin="Manual"/>'
                    % (play_prefix, n, G(), '?EVENTWU?'))
        refs.append('<ObjectRef Name="%s%s" ID="%s" WorkUnitID="%s" Filter="7" Origin="Manual"/>'
                    % (stop_prefix, n, G(), '?EVENTWU?'))
    # 事件 GUID 在写入后才能确定: 重新解析
    new_events = parse_events(proj)
    name2guid = {}
    for (n, _, _, _) in new_events[-len(blocks):]:
        pass
    by_name = {n: g for (n, g, _, _) in new_events}
    ewu_guid = re.search(r'<WorkUnit\s+Name="[^"]+"\s+ID="(%s)"' % GUID_RE, etxt).group(1)
    ref_lines = []
    for (n, g, w) in todo:
        for pre in (play_prefix, stop_prefix):
            en = pre + n
            ref_lines.append('\t\t\t\t\t\t<ObjectRef Name="%s" ID="%s" WorkUnitID="%s" Filter="7" Origin="Manual"/>'
                             % (en, by_name[en], ewu_guid))
    # 用 bank 内既有缩进
    im = re.search(r'(\t+)<ObjectRef\s', m.group(1))
    if im:
        ref_lines = [re.sub(r'^\t+', im.group(1), r) for r in ref_lines]
    backup(bpath)
    btxt = btxt[:m.start(2)] + '\r\n' + '\r\n'.join(ref_lines) + btxt[m.start(2):]
    open(bpath, 'wb').write(btxt.encode('utf-8'))
    print('[WIRE] bank 已更新:', bank, '(+%d 引用)' % len(ref_lines))

# ---------------- rename ----------------
def do_rename(proj, old, new):
    changed = 0
    for sub in ('Events', 'SoundBanks'):
        for p in list_wwu(proj, sub):
            txt = rd(p)
            t2 = txt.replace('Name="%s"' % old, 'Name="%s"' % new)
            if t2 != txt:
                backup(p); open(p, 'wb').write(t2.encode('utf-8'))
                n = txt.count('Name="%s"' % old)
                changed += n
                print('[RENAME] %s: %d 处  %s -> %s' % (os.path.basename(p), n, old, new))
    print('[RENAME] 完成, 共 %d 处 (GUID 不变)' % changed)

# ---------------- generate ----------------
def do_generate(proj, banks):
    if not os.path.isfile(WWCLI):
        raise SystemExit(
            '[FAIL] 未找到 WwiseCLI.exe: %s\n'
            '  请安装 Wwise 2015.1.9，或在 skill 根目录 local_paths.json 中配置 "wwcli" 后重试。' % WWCLI)
    cmd = [WWCLI, os.path.join(proj, 'Yuni.wproj'), '-GenerateSoundBanks',
           '-Platform', 'Windows', '-Verbose']
    for b in banks: cmd += ['-Bank', b]
    print('[GEN]', ' '.join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    for line in out.splitlines():
        if 'Status' in line or 'Error' in line or 'error' in line: print('   ', line)
    print('[GEN] 退出码:', r.returncode)
    od = os.path.join(proj, 'GeneratedSoundBanks', 'Windows')
    if os.path.isdir(od):
        for f in sorted(os.listdir(od)):
            print('   ', f, os.path.getsize(os.path.join(od, f)))
    return r.returncode

# ---------------- main ----------------
def main():
    a = sys.argv[1:]
    proj = a[0]; rest = a[1:]
    def val(flag, default=None):
        return rest[rest.index(flag)+1] if flag in rest else default
    if '--scan' in rest:
        do_scan(proj)
    elif '--wire' in rest:
        do_wire(proj, val('--wire'), val('--events-wu', 'Default Work Unit'),
                val('--play-prefix', 'Play_'), val('--stop-prefix', 'Stop_'),
                val('--only'), int(val('--max', '999')),
                dry=('--dry-run' in rest))
    elif '--rename-event' in rest:
        i = rest.index('--rename-event'); do_rename(proj, rest[i+1], rest[i+2])
    elif '--generate' in rest:
        i = rest.index('--generate')
        bk = rest[i+1:] or []
        sys.exit(do_generate(proj, bk) or 0)
    else:
        print(__doc__)

if __name__ == '__main__':
    main()
