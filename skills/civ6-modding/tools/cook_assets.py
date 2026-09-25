# -*- coding: utf-8 -*-
r"""cook_assets.py — 无 GUI 重放 ModBuddy 的 ArtDef / XLP cook（Civ6.targets 的三组分区）。

为什么需要它
    `modinfo_build.py --deploy` 只把 `.civ6proj` 派生成 `.modinfo` 并拷贝 Content，
    `cook_dep.py` 只产 `.dep`；BLP 与 ArtDef 的 cook 一直只能在 ModBuddy GUI 里点 Build。
    无 GUI 会话改完贴图 / artdef / xlp 后产物进不了 Mods 副本，游戏读到的仍是旧包。

分区唯一真源
    `<SDK>\ModBuddy\Civ6.targets` 的三条 Exec（本机 119–121 行），逐文件 spawn：

      ① --mode ArtDef --platform Windows --banquet_hall <BuildDir>\ArtDefs
      ② --mode XLP    --platform Windows --stewpot     <BuildDir>\Platforms\Windows\BLPs
      ③ --mode XLP    --platform MacOS   --stewpot     <BuildDir>\Platforms\MacOS\BLPs

    `<BuildDir>` = `<Mods>\<ModName>`。.dep 由 ArtDef 轮顺带写出，落点是 `--banquet_hall`
    的父目录（实测：banquet 指 `<out>\ArtDefs` 时 .dep 落在 `<out>\`），因此把
    `--banquet_hall` 指向 `<BuildDir>\ArtDefs` 就等价于把 .dep 放进 Mods 副本根，
    不需要另传 `--dependency_root`（ArtDef 模式下该参数不起作用，实测指定到别处
    仍写进 banquet 的父目录）。XLP 轮不写 .dep。固定段照抄 targets：
    `--absolute_paths --no_mt --shaders <CookerDir> --pantry <工程> <包的 pantry…>
      --config <CookerDir>\Civ6.cfg`。
    `--shaders` 已被 cooker 废弃（每次打印一行 deprecated 提示），照抄 target 保持日志可比。

pantry 列表
    由 `.Art.xml` 的 `<requiredGameArtIDs>` 递归展开（本工程 `Civ6` + `Expansion2`
    → `[Civ6, Expansion2, Shared, Civ6]`；`Civ6\pantry` 出现两次属闭包正常结果）。
    实测顺序与重复都不影响产物，按 targets 的形状展开是为了与构建日志对照。

与 targets 刻意不同的三点
    · `IgnoreExitCode="true"` 不再沿用 —— 退出码被检查，并按日志模式分类报告；
    · CWD 固定到 `<工程>\workspace\tmp\cook_cwd`，`cooker.log` 不脏工程根（.dep 由 banquet 兜住）；
    · cook 之后把源工程 `ArtDefs/*.artdef` 覆盖进输出副本（见 sync_artdefs 的说明）。

报什么错、不报什么错
    `references an ArtDef entry … does not exist` / `has had its value replaced with its
    default value` / `HAS MISSING ENTRIES` / `Removing package asset entry` /
    `will not be cooked because it is not set to cook for platform` 全部只报告不判失败：

    · 前两类是本工程替换型区域引用越南 DLC 素材导致的既有降级（`KublaiKhan_Vietnam`
      在 SDK 里没有 pantry），cook 产物里的引用会被清成空值；Mods 副本侧由上面的
      「源覆盖产物」还原成源工程里完好的引用链；
    · `HAS MISSING ENTRIES`（tilebases 的 4 条 `DIS_Preserve_*`）是既定手段而非缺陷：
      那 4 条要指的名字属于越南 DLC，RGN 这边的 `tilebases.xlp` 只负责把名字登记出来，
      让 `Landmarks.artdef` 的 8 处引用在产物里保留（不登记则被清空，产物从 787,060 B
      掉到 786,964 B）；登记了但没有 `Assets/<名>.ast`，整条被移除，产物与空 BLP 逐字节相同
      （实测 34,816 B / `cc549f071b50`，与 `JuliusCaesar` / `BarbarianClansMode`
      的空 BLP 完全一致）→ 运行时零影响，代价只是日志变吵与 cooker 退出码 2。
    · MacOS 轮对本工程必然整轮空转（28 个 `.xlp` 全部 `AllowedPlatforms = WINDOWS`），
      仍要跑，否则日志与实际动作就和 ModBuddy 不一致。

    不要试图消灭 `HAS MISSING ENTRIES`：给它补一个真实存在的 `.ast` 会让词条成功打包
    （实测 BLP 从 34,816 B 涨到 85,504 B，产物里出现 `DIS_Preserve_Base_01` 字符串），
    本 mod 后挂载、包名与越南 DLC 同为 `landmarks/tilebases` → 同名条目覆盖 DLC 几何体，
    实机表现被改坏（cook-layer §4.3 的反例）。

    判失败的只有两类：产物缺失（该有的 `.blp` / `.artdef` / `.dep` 没产出），
    以及退出码非零且日志里没有任何可解释模式（既没有移除条目，也不是平台跳过）。

用法：
    python cook_assets.py <工程根>                    # 全量 cook 到 Mods 副本
    python cook_assets.py <工程根> --check            # 只列 pantry 展开、调用清单与对账结果
    python cook_assets.py <工程根> --only ArtDef      # 只跑 ArtDef 轮（同理 --only XLP）
    python cook_assets.py <工程根> --out <目录>       # 输出根改到指定目录（默认 <Mods>/<ModName>）
    python cook_assets.py <工程根> --quiet            # 只打印汇总，不逐行列调用

退出码：0 通过 / 1 产物或对账失败 / 2 参数、路径或 cooker 缺失
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _paths  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PLATFORMS = ("Windows", "MacOS")

# 日志模式 → 归类。顺序有意义：先匹配的先生效。
LOG_PATTERNS = (
    ("SKIP-PLATFORM", re.compile(r"will not be cooked because it is not set to cook for platform: '(\w+)'")),
    ("REF-MISSING", re.compile(r">> (\S+) >> .+? references an ArtDef entry \((.*?)\) that does not exist in the ArtDef Collection \((.*?)\) of ArtDef \((.*?)\)")),
    ("REF-DEFAULTED", re.compile(r"^>> (.*?) has had its value replaced with its default value")),
    ("ENTRY-REMOVED", re.compile(r"Removing package asset entry: \((.*?)\) due to errors in")),
    ("MISSING-ENTRIES", re.compile(r"HAS MISSING ENTRIES")),
    ("IO-ERROR", re.compile(r"I/O error reading XML: (.*)$")),
    ("ERROR-ASSET", re.compile(r"Loading error asset: \((.*?)\)")),
)

# 可解释 cooker 非零退出的模式
EXPLAINED_BY = {"ENTRY-REMOVED", "SKIP-PLATFORM"}


@dataclass
class CookCall:
    """一次 cooker 调用（= targets 里一条 Exec 展开出的一个输入文件）。"""

    mode: str
    platform: str
    flag: str
    outdir: str
    src: str

    @property
    def order(self) -> str:
        return "ArtDef" if self.mode == "ArtDef" else "XLP/%s" % self.platform

    @property
    def stem(self) -> str:
        return os.path.splitext(os.path.basename(self.src))[0]

    def cmd(self, cooker: str, config: str, pantry: list) -> list:
        return ([cooker, "--absolute_paths", "--no_mt", "--mode", self.mode,
                 "--platform", self.platform, "--shaders", os.path.dirname(cooker),
                 "--pantry"] + pantry +
                [self.flag, self.outdir, "--config", config, self.src])


@dataclass
class Report:
    calls: list = field(default_factory=list)
    rc_nonzero: list = field(default_factory=list)
    events: dict = field(default_factory=dict)
    synced_artdefs: list = field(default_factory=list)
    failures: list = field(default_factory=list)


def glob_ci(directory: str, pattern: str) -> list:
    """大小写不敏感地枚举文件。

    Windows 上 glob 本身就不区分大小写，同时跑 `*.Art.xml` 与 `*.art.xml`
    会命中同一批文件；用 os.path.normcase 去重，语义等价于 targets 的
    `<ProjectArtXmls Include="*.Art.xml"/>`。
    """
    out: dict = {}
    for p in glob.glob(os.path.join(directory, pattern)):
        out.setdefault(os.path.normcase(p), p)
    return [out[k] for k in sorted(out)]


def find_art_xml(root: str) -> tuple:
    """定位工程里唯一的 *.Art.xml，返回 (路径, 错误说明)。

    多于一份时按 targets 的 `<Error Text="There are too many art xml files…"/>` 同样拒绝。
    """
    seen = glob_ci(root, "*.Art.xml")
    if not seen:
        return None, "找不到 *.Art.xml：%s（cook 无从展开 pantry）" % root
    if len(seen) > 1:
        return None, "工程里有 %d 份 *.Art.xml，targets 规定只能有 1 份：%s" % (len(seen), seen)
    return seen[0], ""


def art_xml_identity(art_xml: str):
    el = load_art_spec(art_xml).find("./id/name")
    return el.get("text") if el is not None else None


def load_art_spec(xml_path: str):
    """解析一份 ArtSpecification。

    SDK 里 `Civ6/DLC/Shared/pantry/Shared.Art.xml` 有两处不合规：根标签写成
    `<AssetObjects::GameArtSpecification>`（双冒号不是合法的 XML 名称），
    文件末尾还多一个 NUL 字节。标准解析器两处都会拒绝。这里只做这两处
    归一化（双冒号改成 `..`、去掉尾部 NUL），再交给 ElementTree ——
    仍由 XML 解析器完成解析，不做任何手工切分。
    """
    text = open(xml_path, encoding="utf-8-sig", errors="replace").read()
    text = text.replace("AssetObjects::", "AssetObjects..").replace("\x00", "")
    return ET.fromstring(text)


def required_art_ids(xml_path: str) -> list:
    """读某个 AssetObjects..GameArtSpecification 的 <requiredGameArtIDs> 包名（保序）。"""
    node = load_art_spec(xml_path).find("requiredGameArtIDs")
    if node is None:
        return []
    out = []
    for el in node.findall("Element"):
        nm = el.find("name")
        if nm is not None and nm.get("text"):
            out.append(nm.get("text"))
    return out


def pantry_index(sdk_assets: str) -> dict:
    """{包名: pantry 目录}：根包 + 全部 DLC 包。"""
    out = {}
    base = os.path.join(sdk_assets, "Civ6", "pantry")
    if os.path.isdir(base):
        out["Civ6"] = base
    dlc = os.path.join(sdk_assets, "Civ6", "DLC")
    if os.path.isdir(dlc):
        for name in sorted(os.listdir(dlc)):
            p = os.path.join(dlc, name, "pantry")
            if os.path.isdir(p):
                out[name] = p
    return out


def package_deps(pantry_dir: str) -> list:
    """读 pantry 目录下 *.Art.xml 的 <requiredGameArtIDs>；读不到返回空表。"""
    cands = glob_ci(pantry_dir, "*.Art.xml")
    if not cands:
        return []
    return required_art_ids(cands[0])


def expand_pantry(declared: list, index: dict) -> tuple:
    """按声明顺序深度优先展开（自 → 依赖），不去重 —— 与 targets 的 PantryPath 形状一致。"""
    order: list = []
    warns: list = []

    def visit(name: str, chain: tuple) -> None:
        order.append(name)
        if name in chain:
            warns.append("包 %s 的依赖成环：%s" % (name, " -> ".join(chain + (name,))))
            return
        d = index.get(name)
        if d is None:
            warns.append("包 %s 在 SDK Assets 里没有 pantry 目录（引用它的 artdef 条目无法解析）" % name)
            return
        deps = package_deps(d)
        if not deps and name != "Civ6":
            warns.append("包 %s 的 pantry 里读不到 <requiredGameArtIDs>（依赖闭包需人工确认）" % name)
        for dep in deps:
            visit(dep, chain + (name,))

    for n in declared:
        visit(n, ())
    return order, warns


def enumerate_inputs(root: str) -> dict:
    """ArtDefs/*.artdef 与 XLPs/*.XLP（后缀匹配不区分大小写，与 targets 的 ItemGroup 等价）。"""
    out = {"ArtDef": [], "XLP": []}
    for sub, suffix, key in (("ArtDefs", ".artdef", "ArtDef"), ("XLPs", ".xlp", "XLP")):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        out[key] = sorted(os.path.join(d, f) for f in os.listdir(d)
                          if f.lower().endswith(suffix) and os.path.isfile(os.path.join(d, f)))
    return out


def build_calls(inputs: dict, out_root: str, only) -> list:
    calls: list = []
    if only in (None, "ArtDef"):
        for src in inputs["ArtDef"]:
            calls.append(CookCall("ArtDef", "Windows", "--banquet_hall",
                                  os.path.join(out_root, "ArtDefs"), src))
    if only in (None, "XLP"):
        for platform in PLATFORMS:
            for src in inputs["XLP"]:
                calls.append(CookCall("XLP", platform, "--stewpot",
                                      os.path.join(out_root, "Platforms", platform, "BLPs"), src))
    return calls


def xlp_package_name(path: str):
    el = load_art_spec(path).find("m_PackageName")
    return el.get("text") if el is not None else None


def xlp_allowed_platforms(path: str) -> set:
    node = load_art_spec(path).find("m_AllowedPlatforms")
    if node is None:
        return set()
    return {(e.text or "").strip().upper() for e in node.findall("Element")}


def run_call(cooker: str, config: str, pantry: list, call: CookCall,
             cwd: str, logdir: str) -> tuple:
    """spawn 一次 cooker；输出落日志文件再读回（受限宿主禁管道捕获）。"""
    os.makedirs(call.outdir, exist_ok=True)
    log = os.path.join(logdir, "%s_%s.log" % (call.order.replace("/", "_"), call.stem))
    with open(log, "wb") as fh:
        rc = subprocess.run(call.cmd(cooker, config, pantry), cwd=cwd,
                            stdout=fh, stderr=subprocess.STDOUT).returncode
    return rc, open(log, encoding="utf-8", errors="replace").read()


def classify(text: str) -> dict:
    """把一段 cooker 日志按 LOG_PATTERNS 归类；同一行只归一次。"""
    out: dict = {}
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        for key, rx in LOG_PATTERNS:
            m = rx.search(s)
            if not m:
                continue
            if key == "REF-MISSING":
                detail = "%s 引用 (%s) 于 %s，集合 %s" % (m.group(1), m.group(2), m.group(4), m.group(3))
            elif key in ("ENTRY-REMOVED", "IO-ERROR", "ERROR-ASSET", "SKIP-PLATFORM", "REF-DEFAULTED"):
                detail = m.group(1)
            else:
                detail = "(同批)"
            out.setdefault(key, []).append(detail)
            break
    return out


def merge_events(dst: dict, src: dict) -> None:
    for k, vs in src.items():
        dst.setdefault(k, []).extend(vs)


def expected_artifacts(calls: list, out_root: str, mod_name: str) -> list:
    """[(说明, 期望路径)]；平台未声明的 XLP 不进清单。"""
    exp: list = []
    seen: set = set()
    for c in calls:
        if c.mode == "ArtDef":
            p = os.path.join(out_root, "ArtDefs", os.path.basename(c.src))
        else:
            if c.platform.upper() not in xlp_allowed_platforms(c.src):
                continue
            pkg = xlp_package_name(c.src)
            if not pkg:
                continue
            # 包名可能带前导斜杠（/leaders/leader_ragunna_qyqxp），去掉再拼，
            # 否则 os.path.join 会把它当成绝对路径、丢掉 out_root。
            rel = pkg.replace("/", os.sep).lstrip(os.sep)
            p = os.path.join(out_root, "Platforms", c.platform, "BLPs", rel + ".blp")
        if p in seen:
            continue
        seen.add(p)
        exp.append(("%s/%s" % (c.order, os.path.basename(c.src)), p))
    # .dep 只在 ArtDef 轮产出（实测：XLP 轮不写依赖文件），--only XLP 下不纳入清单。
    if any(c.mode == "ArtDef" for c in calls):
        exp.append((".dep", os.path.join(out_root, mod_name + ".dep")))
    return exp


def sync_artdefs(root: str, out_root: str) -> tuple:
    """把源工程 ArtDefs/*.artdef 覆盖进输出副本，返回 (覆盖清单, 问题清单)。

    为什么必须做：cook 会把 pantry 解析不到的引用归一化成空值（本工程 5 个引用点，
    根因是 KublaiKhan_Vietnam 在 SDK 里没有 pantry）。ModBuddy 构建时 Mods 副本里
    留下的就是这种被降级的产物，而源工程保存的才是完好的引用链。以源覆盖产物不是
    「掩盖问题」——降级只发生在 cook 产物侧，运行期按名解析仍然成立，Mods 副本侧保留
    完好引用正是 ModBuddy 构不出来的那一份。
    artdef 属资产类文本（LF），copy2 原样搬运，不做任何换行或编码转换。
    """
    src_dir = os.path.join(root, "ArtDefs")
    dst_dir = os.path.join(out_root, "ArtDefs")
    synced: list = []
    problems: list = []
    if not os.path.isdir(src_dir):
        problems.append("源工程没有 ArtDefs 目录：%s" % src_dir)
        return synced, problems
    os.makedirs(dst_dir, exist_ok=True)
    for name in sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".artdef")):
        s, d = os.path.join(src_dir, name), os.path.join(dst_dir, name)
        if os.path.isfile(d):
            with open(s, "rb") as fa, open(d, "rb") as fb:
                if fa.read() == fb.read():
                    continue
        shutil.copy2(s, d)
        synced.append(name)
    return synced, problems


def artdefs_match_source(root: str, out_root: str) -> list:
    """同步后核对：副本里的 artdef 必须与源逐字节相同。"""
    bad: list = []
    src_dir = os.path.join(root, "ArtDefs")
    dst_dir = os.path.join(out_root, "ArtDefs")
    for name in sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".artdef")):
        s, d = os.path.join(src_dir, name), os.path.join(dst_dir, name)
        if not os.path.isfile(d):
            bad.append("%s（副本缺失）" % name)
            continue
        with open(s, "rb") as fa, open(d, "rb") as fb:
            if fa.read() != fb.read():
                bad.append("%s（与源不一致）" % name)
    return bad


def reconcile_art_xml(art_xml: str, inputs: dict) -> list:
    """与 .Art.xml 对账：实存的 artdef / XLP 包名是否都被声明。"""
    root = load_art_spec(art_xml)
    declared_artdef: set = set()
    declared_pkg: set = set()
    for node in root.iter("relativeArtDefPaths"):
        for el in node.findall("Element"):
            if el.get("text"):
                declared_artdef.add(el.get("text"))
    for node in root.iter("relativePackagePaths"):
        for el in node.findall("Element"):
            if el.get("text"):
                declared_pkg.add(el.get("text"))
    lines: list = []
    actual_artdef = {os.path.basename(p) for p in inputs["ArtDef"]}
    undeclared = sorted(actual_artdef - declared_artdef)
    dangling = sorted(declared_artdef - actual_artdef)
    lines.append("artdef：实存 %d / 声明 %d%s" % (
        len(actual_artdef), len(declared_artdef),
        "" if not undeclared and not dangling else
        "  未声明=%s 声明但不存在=%s" % (undeclared or "无", dangling or "无")))
    pkg_of = {os.path.basename(p): xlp_package_name(p) for p in inputs["XLP"]}
    undeclared_pkg = sorted(n for n in pkg_of.values() if n and n not in declared_pkg)
    lines.append("XLP ：实存 %d / 声明包 %d%s" % (
        len(pkg_of), len(declared_pkg),
        "" if not undeclared_pkg else "  未声明的包=%s" % undeclared_pkg))
    return lines


def print_plan(calls: list, quiet: bool) -> None:
    if quiet:
        return
    by_order: dict = {}
    for c in calls:
        by_order[c.order] = by_order.get(c.order, 0) + 1
    print("调用清单（共 %d 次）：%s" % (
        len(calls), "  ".join("%s×%d" % (k, v) for k, v in by_order.items())))
    for c in calls:
        print("   %-12s %-42s -> %s" % (c.order, os.path.basename(c.src), c.outdir))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="无 GUI 重放 ModBuddy 的 ArtDef / XLP cook（Civ6.targets 三分区）")
    ap.add_argument("project", help="工程根目录（含唯一的 *.Art.xml 与 ArtDefs/、XLPs/）")
    ap.add_argument("--check", action="store_true", help="只列 pantry 展开、调用清单与对账结果，不 cook")
    ap.add_argument("--only", choices=("ArtDef", "XLP"), default=None, help="只跑一档分区")
    ap.add_argument("--mods-root", default=None, help="Mods 根目录（默认由 _paths 解析）")
    ap.add_argument("--out", default=None, help="输出根目录（默认 <Mods>/<ModName>）")
    ap.add_argument("--quiet", action="store_true", help="不逐行列调用清单")
    args = ap.parse_args()

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print("ERROR 工程目录不存在：%s" % root, file=sys.stderr)
        return 2

    art_xml, art_err = find_art_xml(root)
    if art_err:
        print("ERROR %s" % art_err, file=sys.stderr)
        return 2
    mod_name = art_xml_identity(art_xml) or os.path.basename(root.rstrip("\\/"))

    sdk = _paths.get("sdk")
    sdk_assets = _paths.get("sdk_assets")
    if not sdk or not sdk_assets:
        print("ERROR 找不到 SDK / SDK Assets 路径。跑一次 python tools/_paths.py "
              "看缺哪个键，把实际路径写进 local_paths.json。", file=sys.stderr)
        return 2
    cooker = os.path.join(sdk, "AssetModTools", "Cooker", "Civ6AssetCooker_FinalRelease.exe")
    config = os.path.join(sdk, "AssetModTools", "Cooker", "Civ6.cfg")
    for p in (cooker, config):
        if not os.path.isfile(p):
            print("ERROR 缺少 cooker 组件：%s" % p, file=sys.stderr)
            return 2

    if args.out:
        out_root = os.path.abspath(args.out)
    else:
        mods_root = args.mods_root or _paths.get("mods")
        if not mods_root:
            print("ERROR 找不到 Mods 目录，请用 --mods-root 指定。", file=sys.stderr)
            return 2
        out_root = os.path.join(mods_root, mod_name)

    declared = required_art_ids(art_xml)
    index = pantry_index(sdk_assets)
    order, warns = expand_pantry(declared, index)
    pantry = [root] + [index[n] for n in order if n in index]
    inputs = enumerate_inputs(root)
    calls = build_calls(inputs, out_root, args.only)
    exp = expected_artifacts(calls, out_root, mod_name)

    print("工程      : %s" % root)
    print("Art.xml   : %s" % os.path.basename(art_xml))
    print("ModName   : %s" % mod_name)
    print("输出副本  : %s" % out_root)
    print("cooker    : %s" % cooker)
    print("声明包    : %s" % (declared or "（无 <requiredGameArtIDs>）"))
    print("pantry 展开：")
    for n in order:
        print("   %-22s %s" % (n, index.get(n, "**无 pantry 目录**")))
    for w in warns:
        print("   WARN %s" % w)
    print_plan(calls, args.quiet)

    rec = reconcile_art_xml(art_xml, inputs)
    print("对账：")
    for line in rec:
        print("   %s" % line)

    if args.check:
        print()
        print("预计产物 %d 个（%s）" % (
            len(exp),
            "含 .dep 1 个" if any(c.mode == "ArtDef" for c in calls) else "纯 XLP 轮，不产 .dep"))
        print("CHECK 模式：未执行任何 cook，未写入任何文件。")
        return 0

    cook_cwd = os.path.join(root, "workspace", "tmp", "cook_cwd")
    logdir = os.path.join(cook_cwd, "logs")
    os.makedirs(logdir, exist_ok=True)
    for c in calls:
        os.makedirs(c.outdir, exist_ok=True)

    rep = Report(calls=calls)
    print()
    print("开始 cook（%d 次调用，逐文件 spawn）…" % len(calls))
    t0 = time.time()
    for i, c in enumerate(calls, 1):
        rc, text = run_call(cooker, config, pantry, c, cook_cwd, logdir)
        ev = classify(text)
        merge_events(rep.events, ev)
        if rc != 0:
            rep.rc_nonzero.append((c, rc))
            if not (set(ev) & EXPLAINED_BY):
                rep.failures.append("cooker 退出码 %d 且日志无可解释模式：%s / %s"
                                    % (rc, c.order, os.path.basename(c.src)))
        if not args.quiet:
            tail = "  ".join("%s×%d" % (k, len(v)) for k, v in sorted(ev.items())) or "ok"
            print("   [%2d/%d] %-12s %-40s rc=%d  %s"
                  % (i, len(calls), c.order, os.path.basename(c.src), rc, tail))
    elapsed = time.time() - t0

    print()
    print("产物核对：")
    missing = [("%s -> %s" % (label, path)) for label, path in exp if not os.path.isfile(path)]
    if missing:
        for m in missing:
            print("   缺失 %s" % m)
        rep.failures.extend("产物缺失：%s" % m for m in missing)
    else:
        print("   全部存在（%d 个）" % len(exp))

    print()
    print("ArtDefs 同步（源 → 副本）：")
    synced, problems = sync_artdefs(root, out_root)
    rep.synced_artdefs = synced
    rep.failures.extend(problems)
    print("   覆盖 %d 个%s" % (len(synced), ("：" + ", ".join(synced)) if synced else "（已一致）"))
    bad = artdefs_match_source(root, out_root)
    if bad:
        rep.failures.extend("artdef 同步后仍不一致：%s" % b for b in bad)
        for b in bad:
            print("   不一致 %s" % b)
    else:
        print("   副本 artdef 与源逐字节一致")

    print()
    print("日志统计（%d 次调用，%.1f 秒，非零退出 %d 次）："
          % (len(calls), elapsed, len(rep.rc_nonzero)))
    if not rep.events:
        print("   无可报告项")
    for key, _ in LOG_PATTERNS:
        vals = rep.events.get(key)
        if not vals:
            continue
        uniq = sorted(set(vals))
        extra = "" if len(uniq) == len(vals) else "，去重 %d" % len(uniq)
        print("   %-16s %d 行%s" % (key, len(vals), extra))
        for v in uniq[:6]:
            print("        %s" % v)
        if len(uniq) > 6:
            print("        …余 %d 类" % (len(uniq) - 6))
    if rep.rc_nonzero:
        print("   非零退出的调用：")
        for c, rc in rep.rc_nonzero:
            print("        rc=%d  %-12s %s" % (rc, c.order, os.path.basename(c.src)))

    print()
    if rep.failures:
        print("FAIL %d 项：" % len(rep.failures))
        for f in rep.failures:
            print("   %s" % f)
        return 1
    print("OK  产物 %d 个齐全，artdef 已同步，对账通过。" % len(exp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
