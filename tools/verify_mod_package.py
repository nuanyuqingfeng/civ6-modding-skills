# -*- coding: utf-8 -*-
"""交付包体检：源工程 ↔ Mods 副本 ↔ 上传工作区 三处一致性 + .modinfo 结构与引用闭合。

覆盖三类只有"打包之后"才暴露的问题：
  ① 三处不同步 —— Mods 副本（游戏真正加载的）落后于源工程，或上传工作区落后于 Mods；
  ② 悬空引用 —— modinfo 里声明的文件实际不存在（ModBuddy 只拷 `<Content>` 条目，
     只写在 InGameActions 而未进 Content 的文件会漏部署，本项目踩过）；
  ③ 漏登记 —— Mods 目录里躺着 modinfo 未声明的实体文件（会把不该传的东西带上工坊）。

★ **cook 产物感知**：`Platforms/Windows/BLPs/**`（AssetEditor/cooker 产出）与任意 `*.dep`
  在源工程里**本就不存在** —— 它们只活在 Mods 副本、且每次 `Rebuild All` 重新生成。
  这类文件也不计入问题（`--strict` 下仍会报），避免长期假红灯淹没真问题。

★ **美术管线感知**：美术引用链路上的文件（见 `ART_PIPELINE_EXTS`）按项目规范
  **不写进 `.civ6proj` 的 `<Content>`**，也**不写进 `.modinfo` 的 `<Files>`** ——
  它们由 cook 链路承载（pantry → cooker → `BLPs` / `.dep`）。故「Mods 里有而 modinfo 未声明」
  属预期，一律放行。

★ **`ImportFiles/` 不适用上面的豁免**：那是显式导入通道，其下素材与其它 ImportFiles 文件
  同等对待，须三处齐全，漏登记照报。

用法：
    python verify_mod_package.py --src <源工程目录> --mods <Mods/<ModName>>
                                 [--ws <上传工作区 content 目录>] [--files a/b.lua,c.lua]
                                 [--strict]

退出码：0 全部通过 / 1 有问题 / 2 参数或读取错误
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def find_modinfo(mods_dir: str) -> str:
    hits = [f for f in os.listdir(mods_dir) if f.lower().endswith(".modinfo")]
    if not hits:
        raise SystemExit("Mods 目录里没有 .modinfo：%s" % mods_dir)
    if len(hits) > 1:
        print("WARN 发现多个 modinfo，取第一个：%s" % hits)
    return os.path.join(mods_dir, hits[0])


# cook 产物：只存在于 Mods 副本，每次 Rebuild All 重新生成；源工程本就没有。
#   `.dep` 由 `Civ6AssetCooker` 生成（`--mode Dependency` 专用，或任意 cook 模式的副产物），
#   文件名 = <ModName>.dep，落点是 cooker 的 CWD（可用 `--dependency_root` 指定）。
#   ★ 它虽属「源工程没有」的产物，但**不是可忽略项**：ModBuddy 会把它写进 .modinfo 的
#     <UpdateArt> 与顶层 <Files>；缺失/未替换时游戏只写一行 ERROR、美术全空（静默失效）。
#     故在下面的 check_art_dep() 里单独硬检查，不参与「漏登记」软放行。
COOK_ARTIFACT_PREFIXES = ("platforms/windows/blps/", "platforms/macos/blps/")
COOK_ARTIFACT_SUFFIXES = (".dep",)

# 美术引用管线：由 cook 链路承载（pantry → cooker → Platforms/*/BLPs/ 与 .dep），
#   按项目规范不写进 .civ6proj 的 <Content>、也不写进 .modinfo 的 <Files>。
# 与 COOK_ARTIFACT_* 的分工：那边管「源工程本就没有的 cooker 产物」，
#   这边管「源工程有、但按规范不进清单」的美术管线文件。
ART_PIPELINE_EXTS = (
    ".artdef",                                # artdef 定义
    ".xlp",                                   # cook 输入，既不进 Content 也不进产物
    ".tex", ".dds",                           # pantry 源 / 图集素材
    ".mtl", ".geo", ".ast", ".lrg", ".env",   # 材质 / 几何 / 资产 / 光照
    ".fgx", ".wig", ".anm", ".s3d", ".blb",   # 其它美术中间格式
)

# 显式导入通道，不属于上面的豁免：经 ImportFiles 导入的素材（含直导的 .dds）
#   与其它 ImportFiles 文件同等对待，须 .civ6proj <Content> + <ImportFiles> 动作
#   + .modinfo 顶层 <Files> 三处齐全，故其下一切不豁免。
EXPLICIT_IMPORT_PREFIX = "importfiles/"

# ModBuddy 占位符：只允许出现在 .civ6proj 里；派生出的 .modinfo 必须已替换为 <ModName>.dep
ART_DEP_PLACEHOLDER = "(Mod Art Dependency File)"


def is_cook_artifact(rel: str) -> bool:
    r = rel.replace("\\", "/").lower()
    return r.startswith(COOK_ARTIFACT_PREFIXES) or r.endswith(COOK_ARTIFACT_SUFFIXES)


def is_art_pipeline(rel: str) -> bool:
    """美术引用管线文件：按规范不进 proj 的 <Content>、也不进 modinfo 的 <Files>。

    ImportFiles/ 之下不豁免 —— 那是显式导入通道，须三处齐全。
    """
    r = rel.replace("\\", "/").lower()
    if r.startswith(EXPLICIT_IMPORT_PREFIX):
        return False
    return os.path.splitext(r)[1] in ART_PIPELINE_EXTS


def main() -> int:
    ap = argparse.ArgumentParser(description="交付包三处一致性 + modinfo 结构体检")
    ap.add_argument("--src", required=True, help="ModBuddy 源工程目录（含 .civ6proj）")
    ap.add_argument("--mods", required=True, help="游戏 Mods 副本目录（含 .modinfo）")
    ap.add_argument("--ws", default=None, help="可选：上传工作区 content 目录")
    ap.add_argument("--files", default=None, help="可选：逗号分隔的待比对文件（默认取 modinfo 的 <Files>）")
    ap.add_argument("--strict", action="store_true",
                    help="关掉全部感知放行（cook 产物 / 美术管线），要求逐字节一致且零未登记")
    args = ap.parse_args()

    mods_dir = os.path.abspath(args.mods)
    if not os.path.isdir(mods_dir):
        raise SystemExit("Mods 副本目录不存在：%s" % mods_dir)
    modinfo = find_modinfo(mods_dir)
    raw = open(modinfo, encoding="utf-8").read()
    root = ET.fromstring(raw)

    declared = [f.text for f in root.findall("Files/File") if f.text]
    files = [x.strip() for x in args.files.split(",")] if args.files else declared

    print("modinfo      : %s" % modinfo)
    print("GUID         : %s" % root.get("id"))
    print("version      : %s" % root.get("version"))
    print("Authors      : %s" % (root.findtext("Properties/Authors") or "(未写)"))
    print("LoadOrders   : %s" % (re.findall(r"<LoadOrder>(\d+)</LoadOrder>", raw) or "无"))
    print()

    problems = 0
    cook_skipped = 0
    art_skipped = 0
    print("%-44s %s" % ("文件", "src / mods / ws"))
    for rel in files:
        rows, ok = [], True
        paths = {}
        for base in (args.src, mods_dir, args.ws):
            if base is None:
                continue
            p = os.path.join(base, rel.replace("/", os.sep))
            paths[base] = p
            if os.path.isfile(p):
                rows.append(sha256(p)[:12])
            else:
                rows.append("缺失")
                ok = False
        if len(set(rows)) != 1:
            ok = False
            # cook 产物感知：源工程本就没有（AssetEditor/cooker 生成，只在 Mods 副本）
            if not args.strict and is_cook_artifact(rel):
                ok = True
                cook_skipped += 1
        problems += 0 if ok else 1
        print("%-44s %s  %s" % (rel, " / ".join(rows),
                                "OK" if ok else "<== 不一致"))

    # ── <UpdateArt> / .dep 硬检查（静默失效类，必须拦） ──────────────
    try:
        modinfo_text = open(modinfo, encoding="utf-8-sig").read()
    except Exception:
        modinfo_text = ""
    if ART_DEP_PLACEHOLDER in modinfo_text:
        problems += 1
        print("\n占位符残留：.modinfo 里仍含 %r —— 应替换为 <ModName>.dep。"
              "\n  游戏症状：ERROR: Invalid file reference in action ... in <Files>?，且美术/图标全空。"
              % ART_DEP_PLACEHOLDER)
    m_art = re.search(r"<UpdateArt[^>]*>\s*<File>([^<]+)</File>", modinfo_text)
    if m_art:
        dep_rel = m_art.group(1).strip()
        dep_abs = os.path.join(mods_dir, dep_rel.replace("/", os.sep))
        if not os.path.isfile(dep_abs):
            problems += 1
            print("\n<UpdateArt> 指向 %s，但 Mods 副本里不存在该 .dep（美术将静默失效）。" % dep_rel)
            print("  生成：Civ6AssetCooker_FinalRelease.exe --mode Dependency --platform Windows \\")
            print("        --pantry <源工程> --dependency_root <源工程> --config <SDK>\\AssetModTools\\Cooker\\Civ6.cfg \\")
            print("        <源工程>\\<ModName>.Art.xml")
        elif dep_rel not in declared:
            problems += 1
            print("\n.dep 未登记进 modinfo 顶层 <Files>：%s（游戏会报 'did you forgot to add it in <Files>?'）" % dep_rel)

    dangling = [f for f in declared if not os.path.isfile(os.path.join(mods_dir, f.replace("/", os.sep)))]
    if dangling:
        problems += 1
        print("\n悬空引用（modinfo 声明但 Mods 副本没有）：%s" % dangling)

    unregistered = []
    for dirpath, _, names in os.walk(mods_dir):
        for n in names:
            rel = os.path.relpath(os.path.join(dirpath, n), mods_dir).replace(os.sep, "/")
            if not rel.lower().endswith(".modinfo") and rel not in declared:
                unregistered.append(rel)
    if unregistered:
        # 分级：art  = 美术引用管线（见 ART_PIPELINE_EXTS，ImportFiles/ 除外）
        #       cook = cooker 产物（BLPs/.dep）
        #       hard = 真正需要人看一眼的漏登记
        art, cook, hard = [], [], []
        for r in unregistered:
            if not args.strict and is_art_pipeline(r):
                art.append(r)
            elif not args.strict and is_cook_artifact(r):
                cook.append(r)
            else:
                hard.append(r)
        art_skipped = len(art)
        if hard:
            problems += 1
            print("漏登记（在 Mods 副本里但 modinfo 未声明）：%s" % hard)
        if art:
            print("（另有 %d 个美术管线文件未登记进 modinfo，属规范行为、不计入问题：%s）"
                  % (len(art), ", ".join(sorted({os.path.dirname(r) or "." for r in art}))))
        if cook:
            print("（另有 %d 个 cook 产物未登记，属预期、不计入问题）" % len(cook))

    langs = sorted({e.tag for e in root.findall("LocalizedText/Text/*")})
    print("\n本地化语言   : %s（%d 条 Text）" % (", ".join(langs) if langs else "无", len(root.findall("LocalizedText/Text"))))
    if cook_skipped:
        print("cook 产物    : %d 个 BLPs/.dep 只存在于 Mods 副本（源工程本就没有），按预期放行" % cook_skipped)
    if art_skipped:
        print("美术管线     : %d 个 artdef/dds 等未写进 modinfo <Files>（规范如此，走 cook 链路），按预期放行"
              % art_skipped)
    if cook_skipped or art_skipped:
        print("               （以上两类加 --strict 可强制逐字节核对）")
    print("\n结论: %s" % ("全部一致且引用闭合" if problems == 0 else "发现 %d 类问题，见上" % problems))
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
