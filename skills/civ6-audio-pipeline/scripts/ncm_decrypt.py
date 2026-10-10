# -*- coding: utf-8 -*-
"""
ncm_decrypt.py -- 网易云 .ncm 解密为裸流 (flac/mp3/wav/ogg)
依据: anonymous5l/ncmdump 参考实现(taurusxin 复刻版) -- AES-128-ECB(core key) 解 RC4 密钥,
      KSA 置换后按静态公式生成密钥流表, 以 j=(i+1)&0xFF 取用异或音频。
      注意: 密钥流不是预生成 stream 表, 也不是 KSA box 直接取用(两种民间变体均错)。
用法:
  python ncm_decrypt.py <ncm文件或目录...> [--out DIR] [--delete-source] [--selftest]
  --out DIR        输出目录, 默认 <各源文件所在目录>/converted
  --delete-source  仅在 ffprobe 复核通过后删除对应 .ncm (默认不删, 防止解密失败丢源)
  --selftest       构造合成 ncm 做往返自检(不依赖真实素材), 期望 PASS
依赖: pycryptodome (pip install pycryptodome), ffmpeg/ffprobe
实证: 2026-09 本地 54/54 (53x 96kHz/24bit FLAC + 1x MP3), 含 klen=128 布局变体与 music: 元数据前缀
"""
import os, sys, json, struct, base64, argparse, subprocess, shutil

try:
    from Crypto.Cipher import AES
except ImportError:
    raise SystemExit(
        '[FAIL] 缺少 pycryptodome。请先执行: pip install pycryptodome'
    )

CORE_KEY = b"hzHRAmso5kInbaxW"
META_KEY = b"#14ljk_!\\]&0U<'("
NETEASE_PREFIX = b"neteasecloudmusic"
META_B64_PREFIX = b"163 key(Don't modify):"


def unpad(data: bytes) -> bytes:
    if not data:
        return data
    pad = data[-1]
    if 0 < pad <= 16 and data[-pad:] == bytes([pad]) * pad:
        return data[:-pad]
    return data


def build_key_box(key: bytes) -> bytes:
    """KSA 置换 (参考实现仅此一轮, 无第二段 stream 生成)"""
    box = list(range(256))
    last, off = 0, 0
    for i in range(256):
        swap = box[i]
        idx = (swap + last + key[off]) & 0xFF
        off = 0 if off + 1 >= len(key) else off + 1
        box[i] = box[idx]
        box[idx] = swap
        last = idx
    return bytes(box)


def keystream_table(box: bytes) -> bytes:
    """Dump 循环的静态密钥流表: k[j] = box[(box[j]+box[(box[j]+j)&0xFF])&0xFF]"""
    return bytes(box[(box[j] + box[(box[j] + j) & 0xFF]) & 0xFF] for j in range(256))


def xor_keystream(data: bytes, ktab: bytes) -> bytes:
    """data[i] ^= ktab[(i+1)&0xFF]; 大文件用大整数异或(stdlib, 每秒数百 MB)"""
    unit = ktab[1:] + ktab[:1]  # 循环相位 +1 后的重复单元
    rep = (unit * (len(data) // 256 + 2))[:len(data)]
    return (int.from_bytes(data, "little") ^ int.from_bytes(rep, "little")).to_bytes(len(data), "little")


def sniff(data: bytes):
    if data[:4] == b"fLaC":
        return "flac"
    if data[:3] == b"ID3" or (len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data[:4] == b"RIFF":
        return "wav"
    if data[:4] == b"OggS":
        return "ogg"
    if len(data) > 8 and data[4:8] == b"ftyp":
        return "m4a"
    return None


def decrypt_ncm(path):
    """返回 (audio_bytes, ext, meta_dict 或 None)"""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:8] != b"CTENFDAM":
        raise ValueError("magic 不符: %r" % raw[:8])
    pos = 10  # magic 8 + gap 2
    (klen,) = struct.unpack_from("<I", raw, pos); pos += 4
    kd = bytes(b ^ 0x64 for b in raw[pos:pos + klen]); pos += klen
    kd = unpad(AES.new(CORE_KEY, AES.MODE_ECB).decrypt(kd))
    if kd[:len(NETEASE_PREFIX)] == NETEASE_PREFIX:
        kd = kd[len(NETEASE_PREFIX):]

    meta = None
    (mlen,) = struct.unpack_from("<I", raw, pos); pos += 4
    md = bytes(b ^ 0x63 for b in raw[pos:pos + mlen]); pos += mlen
    try:
        if md[:22] == META_B64_PREFIX:
            m2 = unpad(AES.new(META_KEY, AES.MODE_ECB).decrypt(base64.b64decode(md[22:])))
            meta = json.loads(m2[m2.index(b"{"):].decode("utf-8", "replace"))  # 可能带 music: 前缀
    except Exception:
        meta = None

    pos += 4   # crc32
    pos += 5   # gap
    (ilen,) = struct.unpack_from("<I", raw, pos); pos += 4
    pos += ilen  # 封面图
    ktab = keystream_table(build_key_box(kd))
    dec = xor_keystream(raw[pos:], ktab)
    ext = sniff(dec)
    if ext is None:
        raise ValueError("无法识别音频头, 前16字节=%s" % dec[:16].hex())
    return dec, ext, meta


def ffprobe_ok(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        d = json.loads(r.stdout or "{}")
        st = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
        if not st:
            return False, "无音频流"
        dur = float(st.get("duration") or d.get("format", {}).get("duration") or 0)
        if dur < 1:
            return False, "时长异常 %.1fs" % dur
        return True, "%.1fs %s %sHz %sch" % (dur, st.get("codec_name"), st.get("sample_rate"), st.get("channels"))
    except Exception as e:
        return False, "ffprobe异常: %s" % e


def selftest():
    """合成 ncm 往返自检: 生成正弦 wav -> 加密封装 -> 解密 -> 字节比对"""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ncm_selftest_")
    wav = os.path.join(tmp, "t.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=2", "-ar", "48000", "-ac", "2", wav],
                   check=True, capture_output=True)
    audio = open(wav, "rb").read()
    key = bytes((i * 7 + 3) & 0xFF for i in range(128))
    ktab = keystream_table(build_key_box(key))
    enc_audio = xor_keystream(audio, ktab)
    enc_key = bytes(b ^ 0x64 for b in AES.new(CORE_KEY, AES.MODE_ECB).encrypt(_pad(NETEASE_PREFIX + key)))
    meta_json = b'music:{"musicId":"1","musicName":"selftest","format":"wav"}'
    enc_meta_b64 = base64.b64encode(AES.new(META_KEY, AES.MODE_ECB).encrypt(_pad(meta_json)))
    enc_meta = bytes(b ^ 0x63 for b in META_B64_PREFIX + enc_meta_b64)
    ncm = (b"CTENFDAM" + b"\x00\x00"
           + struct.pack("<I", len(enc_key)) + enc_key
           + struct.pack("<I", len(enc_meta)) + enc_meta
           + struct.pack("<I", 0) + b"\x00" * 5
           + struct.pack("<I", 0))
    src = os.path.join(tmp, "t.ncm")
    open(src, "wb").write(ncm + enc_audio)
    dec, ext, meta = decrypt_ncm(src)
    ok = dec == audio and ext == "wav" and meta and meta.get("musicName") == "selftest"
    print("[SELFTEST] %s (ext=%s, meta=%s, bytes=%d)" % ("PASS" if ok else "FAIL", ext,
                                                         meta.get("musicName") if meta else None, len(dec)))
    return ok


def _pad(data: bytes) -> bytes:
    n = 16 - len(data) % 16
    return data + bytes([n]) * n


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith(".ncm"))
        elif os.path.isfile(p):
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="ncm 文件或目录")
    ap.add_argument("--out", default=None)
    ap.add_argument("--delete-source", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not (shutil.which('ffprobe') and shutil.which('ffmpeg')):
        raise SystemExit('[FAIL] 未找到 ffprobe/ffmpeg，请先安装 FFmpeg 并加入 PATH 后重试。')
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    files = collect(a.paths)
    if not files:
        raise SystemExit("没有找到 ncm 文件 (自检请用 --selftest)")
    files = [f for f in files if f.lower().endswith(".ncm")]
    print("[NCM] 共 %d 个" % len(files))
    n_ok = n_del = 0
    for i, src in enumerate(files, 1):
        out_dir = a.out or os.path.join(os.path.dirname(src), "converted")
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(src))[0]
        try:
            dec, ext, meta = decrypt_ncm(src)
            dst = os.path.join(out_dir, base + "." + ext)
            open(dst, "wb").write(dec)
            ok, info = ffprobe_ok(dst)
            if not ok:
                os.remove(dst)
                print("  [FAIL] %s : %s" % (os.path.basename(src), info))
                continue
            if a.delete_source:
                os.remove(src)
                n_del += 1
            n_ok += 1
            print("  [OK] %s -> %s (%s%s)" % (os.path.basename(src), os.path.basename(dst), info,
                                              ", meta:" + str(meta.get("musicName")) if meta else ""))
        except Exception as e:
            print("  [FAIL] %s : %s" % (os.path.basename(src), e))
    print("[NCM] 成功 %d/%d, 已删源 %d%s" % (n_ok, len(files), n_del,
                                            " (--delete-source)" if a.delete_source else ""))
    sys.exit(0 if n_ok == len(files) else 1)


if __name__ == "__main__":
    main()
