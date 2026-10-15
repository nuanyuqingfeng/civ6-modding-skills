# -*- coding: utf-8 -*-
"""bank_output.py -- Wwise 生成产物 (GeneratedSoundBanks/Windows) 的落盘后处理

WwiseCLI 产出的侧车换行与工程口径相反:
  .txt (人读事件表) 为 CRLF, 工程口径要求 LF
  .xml (SoundBanksInfo) 为 LF, 工程口径要求 CRLF
生成后调用 normalize_generated_eol() 就地归一, 免得每个工程再手工跑一次
civ6-modding 的 normalize_eol.py。

用法:
  python bank_output.py --normalize-eol <GeneratedSoundBanks/Windows 目录>
"""
import argparse
import os
import sys

# (扩展名, 目标换行)。归一化幂等: 先把 CRLF 压成 LF, 再按目标展开。
TARGETS = (('.txt', b'\n'), ('.xml', b'\r\n'))


def normalize_generated_eol(directory):
    """把目录下的 .txt 归一为 LF、.xml 归一为 CRLF; 返回实际改动的文件数。"""
    if not os.path.isdir(directory):
        return 0
    changed = 0
    for fn in sorted(os.listdir(directory)):
        path = os.path.join(directory, fn)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(fn)[1].lower()
        want = dict(TARGETS).get(ext)
        if want is None:
            continue
        raw = open(path, 'rb').read()
        new = raw.replace(b'\r\n', b'\n')
        if want == b'\r\n':
            new = new.replace(b'\n', b'\r\n')
        if new != raw:
            open(path, 'wb').write(new)
            changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser(description='Wwise 生成产物换行后处理')
    ap.add_argument('--normalize-eol', required=True, metavar='DIR',
                    help='GeneratedSoundBanks/Windows 目录')
    a = ap.parse_args()
    n = normalize_generated_eol(a.normalize_eol)
    print('[EOL] %s: 归一 %d 个文件 (.txt->LF / .xml->CRLF)' % (a.normalize_eol, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
