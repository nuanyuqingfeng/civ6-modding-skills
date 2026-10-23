import os
import shutil
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wwise_shortid as ws

# 从成品语音 bank 逆推 Wwise 工程：提取内嵌媒体 → 解码 → 按媒体名重命名 → 建工程。
# 适用于工程丢失、只剩 bank 与 .txt 侧车的 mod。
#
# 用法:
#   python speech_rebuild.py --bank <Bank.bnk> --proj <新工程目录> --name <Bank名>
#                            --work <中间目录> [--vgm <vgmstream-cli 路径>] [--generate]
# 解码器: vgmstream-cli（Wwise 私有 ADPCM，ffmpeg 解不了）
#   https://github.com/vgmstream/vgmstream/releases/latest/download/vgmstream-win64.zip

HERE = os.path.dirname(os.path.abspath(__file__))


def media_names(txt_path):
    table = {}
    started = False
    for line in open(txt_path, encoding="utf-8-sig", errors="replace"):
        if line.startswith("In Memory Audio"):
            started = True
            continue
        if not started:
            continue
        cells = line.rstrip("\n").split("\t")
        if len(cells) >= 3:
            ident, name = cells[1].strip(), cells[2].strip()
            if ident.isdigit() and name:
                table[int(ident)] = name
    return table


def extract(bank_path, wem_dir):
    with open(bank_path, "rb") as fh:
        data = fh.read()
    chunks, didx, _, _ = ws.parse_bank(data)
    body = chunks[b"DATA"]
    os.makedirs(wem_dir, exist_ok=True)
    for fid, off, size in didx:
        with open(os.path.join(wem_dir, "%d.wem" % fid), "wb") as out:
            out.write(body[off:off + size])
    return len(didx)


def decode(wem_dir, wav_dir, names, vgm):
    os.makedirs(wav_dir, exist_ok=True)
    count = 0
    for fn in sorted(os.listdir(wem_dir)):
        if not fn.endswith(".wem"):
            continue
        name = names.get(int(fn[:-4]))
        if not name:
            raise SystemExit("媒体 %s 在 .txt 里没有名字" % fn)
        r = subprocess.run([vgm, "-o", os.path.join(wav_dir, name + ".wav"), os.path.join(wem_dir, fn)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise SystemExit("解码失败 %s: %s" % (fn, (r.stderr or r.stdout).strip()))
        count += 1
    return count


def main():
    argv = sys.argv[1:]
    def val(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default

    bank = val("--bank")
    proj = val("--proj")
    name = val("--name")
    work = val("--work")
    if not (bank and proj and name and work):
        raise SystemExit("用法: speech_rebuild.py --bank <Bank.bnk> --proj <目录> --name <Bank名> --work <中间目录> [--vgm <路径>] [--generate]")

    txt = os.path.splitext(bank)[0] + ".txt"
    if not os.path.isfile(txt):
        raise SystemExit("缺少侧车: %s" % txt)
    vgm = val("--vgm") or shutil.which("vgmstream-cli")
    if not vgm:
        raise SystemExit("找不到 vgmstream-cli，用 --vgm 指定；下载地址 "
                         "https://github.com/vgmstream/vgmstream/releases/latest/download/vgmstream-win64.zip")

    names = media_names(txt)
    wem_dir = os.path.join(work, "wem")
    wav_dir = os.path.join(work, "wav")
    n_extract = extract(bank, wem_dir)
    n_decode = decode(wem_dir, wav_dir, names, vgm)
    print("[REBUILD] 提取 %d 个媒体，解码 %d 个 wav -> %s" % (n_extract, n_decode, wav_dir))

    cmd = [sys.executable, os.path.join(HERE, "new_bank_project.py"),
           "--proj", proj, "--bank", name, "--media", wav_dir, "--category", "voice"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or "").strip())
    if r.returncode != 0:
        raise SystemExit("建工程失败: %s" % (r.stderr or "").strip())

    if "--generate" in argv:
        r = subprocess.run([sys.executable, os.path.join(HERE, "wwise_wire.py"), proj, "--generate", name],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print((r.stdout or "").strip().splitlines()[-1] if r.stdout else "")
        if r.returncode != 0:
            raise SystemExit("生成失败，退出码 %d" % r.returncode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
