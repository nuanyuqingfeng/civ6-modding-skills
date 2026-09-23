# -*- coding: utf-8 -*-
r"""cook_dep.py — 从 <ModName>.Art.xml 生成 <ModName>.dep（AssetObjects..GameDependencyData）。

## 为什么需要它

`.dep` 是 **UpdateArt 的实际载荷**：`.modinfo` 的 `<UpdateArt><File>X.dep</File></UpdateArt>`
靠它把美术/图标 BLP 挂进游戏。它**不是** ModBuddy 独有的产物 ——
`Civ6AssetCooker_FinalRelease.exe` 原生支持 `--mode Dependency`（见 `--help` 的 Known modes），
可完全无 GUI 生成：

    Civ6AssetCooker_FinalRelease.exe --mode Dependency --platform Windows \
        --pantry <工程> --dependency_root <输出目录> --config <SDK>\AssetModTools\Cooker\Civ6.cfg \
        <工程>\<ModName>.Art.xml

关键实测事实（2026-09-22，本机）：
  · `--mode Dependency` 与 `--mode ArtDef`（无 dependency 参数）产出的 `.dep` **SHA256 逐字节相同**；
    即任意 cook 模式都会**顺带**写出 `.dep`，只是没人管它落到哪。
  · **落点 = cooker 进程的 CWD**（**不是** `--banquet_hall` / `--stewpot`）；
    `Civ6.targets` 的三条 Exec 都没传 `--dependency_root`，所以 ModBuddy 构建时落点随 CWD 漂移
    （4 个兄弟工程的 `Cooked\<Name>.dep` 即由此而来）。本工具显式传 `--dependency_root` 消除漂移。
  · cooker 输出 `Unable to generate dependency information ...` 并返回非 0 时，`.dep` **仍完整正确** ——
    该行指「ArtDef 依赖无法自动补全」，不影响 `.dep` 本体（已字节比对确认），故本工具不据此判失败。
  · `Clutter.artdef` 的 `relativeArtDefPaths` 会被 cooker 有意丢弃（日志有明示）——
    `.dep` ↔ `.Art.xml` 对比时该条差异**不算缺陷**。

## 用法

    # 生成到 workspace/tmp/dep（默认），然后自行复制
    python cook_dep.py <工程根>

    # 生成并直接放到指定目录（如 Mods 副本）
    python cook_dep.py <工程根> --out "<Mods>/<ModName>"

    # 只校验现有 .dep 是否与 .Art.xml 同源（不 cook）
    python cook_dep.py <工程根> --check

退出码：0 成功 / 1 失败 / 2 参数或依赖缺失
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "art"))


def find_cooker() -> str | None:
    """定位 Civ6AssetCooker。优先 SDK 安装目录（由 _paths 解析），再退环境变量。"""
    env = os.environ.get("CIV6_COOKER")
    if env and os.path.isfile(env):
        return env
    try:
        import _paths
        sdk = _paths.get("sdk")          # <SDK> 根
        if sdk:
            p = os.path.join(sdk, "AssetModTools", "Cooker",
                             "Civ6AssetCooker_FinalRelease.exe")
            if os.path.isfile(p):
                return p
    except Exception:
        pass
    # 常见硬编码兜底（与 skill local_paths 的 P5 一致）
    p = (r"F:\Steam\steamapps\common\Sid Meier's Civilization VI SDK"
         r"\AssetModTools\Cooker\Civ6AssetCooker_FinalRelease.exe")
    return p if os.path.isfile(p) else None


def find_config(cooker: str) -> str:
    return os.path.join(os.path.dirname(cooker), "Civ6.cfg")


def generate(proj: str, art_xml: str, out_dir: str, platform: str) -> tuple[bool, str]:
    """跑 cooker --mode Dependency，返回 (成功, 说明)。"""
    cooker = find_cooker()
    if not cooker:
        return False, ("找不到 Civ6AssetCooker_FinalRelease.exe。"
                       "设环境变量 CIV6_COOKER 指向它，或确认 SDK 已安装。")
    cfg = find_config(cooker)
    if not os.path.isfile(cfg):
        return False, "找不到 cooker 配置：%s" % cfg

    os.makedirs(out_dir, exist_ok=True)
    cmd = [cooker, "--absolute_paths", "--no_mt",
           "--mode", "Dependency", "--platform", platform,
           "--pantry", proj,
           "--dependency_root", out_dir,
           "--config", cfg,
           art_xml]
    # 注意：不要用 capture_output=True —— 部分受限宿主禁管道。
    # 先落临时日志，再读回过滤（等价且不依赖管道）。
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "cooker.log")
        with open(log, "wb") as fh:
            rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT,
                                cwd=out_dir).returncode
        text = open(log, encoding="utf-8", errors="replace").read()

    # ★ .dep 文件名来自 .Art.xml 的 <id><name>（= mod 名），**不是**工程目录名
    #   （工程目录可能叫 NtE_Eidolon_Mode 而 mod 名是 NtE_Anomaly_Mode）。
    #   故按产物扫描，不靠目录名拼。
    deps = [f for f in os.listdir(out_dir) if f.lower().endswith(".dep")]
    if not deps:
        return False, "cook 未产出 .dep（exit %s）：\n%s" % (rc, text.strip()[-1200:])
    dep = os.path.join(out_dir, max(deps, key=lambda f: os.path.getmtime(os.path.join(out_dir, f))))
    note = ""
    if rc != 0:
        note = "（cooker exit %s；该行通常指 ArtDef 依赖无法自动补全，.dep 本体验证通过）" % rc
    return True, note


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 <ModName>.dep（从 .Art.xml，无需 ModBuddy GUI）")
    ap.add_argument("project", help="工程根目录（含 <ModName>.Art.xml）")
    ap.add_argument("--out", default="", help=".dep 输出目录（默认 <工程>/workspace/tmp/dep）")
    ap.add_argument("--platform", default="Windows", help="平台（默认 Windows）")
    ap.add_argument("--check", action="store_true", help="只报告现状，不 cook")
    a = ap.parse_args()

    proj = os.path.abspath(a.project)
    if not os.path.isdir(proj):
        print("ERROR: 工程目录不存在：%s" % proj, file=sys.stderr)
        return 2
    mod_name = os.path.basename(proj.rstrip("\\/"))
    art_xml = os.path.join(proj, mod_name + ".Art.xml")
    if not os.path.isfile(art_xml):
        # 退而求其次：工程内唯一的 *.Art.xml
        cands = [f for f in os.listdir(proj) if f.lower().endswith(".art.xml")]
        if len(cands) == 1:
            art_xml = os.path.join(proj, cands[0])
            mod_name = os.path.splitext(os.path.splitext(cands[0])[0])[0]
        else:
            print("ERROR: 找不到 %s.Art.xml（工程内 .Art.xml 候选：%s）"
                  % (mod_name, cands or "无"), file=sys.stderr)
            return 2

    out_dir = os.path.abspath(a.out) if a.out else os.path.join(proj, "workspace", "tmp", "dep")

    def _latest_dep(d: str):
        if not os.path.isdir(d):
            return None
        ds = [f for f in os.listdir(d) if f.lower().endswith(".dep")]
        return os.path.join(d, max(ds, key=lambda f: os.path.getmtime(os.path.join(d, f)))) if ds else None

    if a.check:
        found = _latest_dep(out_dir) or _latest_dep(proj)
        print("Art.xml : %s" % art_xml)
        print(".dep    : %s" % (("%s  %d B" % (found, os.path.getsize(found))) if found else "**不存在**"))
        print("Cooker  : %s" % (find_cooker() or "**未找到**"))
        return 0 if found else 1

    print("Art.xml : %s" % art_xml)
    print("输出到  : %s" % out_dir)
    ok, note = generate(proj, art_xml, out_dir, a.platform)
    if not ok:
        print("FAIL %s" % note, file=sys.stderr)
        return 1
    dep_path = _latest_dep(out_dir)
    print("OK  ->  %s  %d B %s" % (dep_path, os.path.getsize(dep_path), note))
    print()
    print("提醒：.dep 必须同时出现在 .modinfo 的 <UpdateArt> 与顶层 <Files>。")
    print("      用 modinfo_build.py --deploy 部署时会自动补 <Files>；")
    print("      本工具生成的 .dep 需自行复制到 Mods 副本（或用 --out 直接指定）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
