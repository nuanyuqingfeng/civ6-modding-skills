# 工程文件写入守卫：代码文件一律拒写，只有美术与音频产物允许脚本落盘
#
# 铁律真源：焚诀「禁止用程序化的方式编写或修改任何代码文件（最严厉铁律）」，
# 与 civ6-modding/SKILL.md「工程文件写入铁律」。
#
# 脚本对代码文件（.sql/.lua/.xml/.ini/.gitignore/.gitattributes）的任何写入都抛
# CodeWriteForbidden，不设暂存分支 —— 暂存同样是生成器产出代码文件。脚本只能把结果
# 写成 workspace/gen/reports/ 下的数据清单，由人逐行写入工程。
#
# 三个工程文件允许官方工具从零产生：.civ6sln 与 .civ6proj 由 ModBuddy，.modinfo 由
# .civ6proj 派生。脚本只在目标不存在时直写；目标已存在即抛 CodeWriteForbidden。
#
# 美术与音频产物由脚本直接覆盖（文件编辑工具无法忠实写出这些字节）：
#   .artdef/.xlp/.ast/.mtl/.dep、*.Art.xml、.dds/.tex、.bnk/.wem/.wav/.wwu/.wproj，
#   以及 Platforms/Windows/Audio/ 下 WwiseCLI 产出的 <Bank>.xml 与 <Bank>.txt。
#
# 六份副本必须逐字节相同，一致性由 civ6-modding/scripts/check_script_write_targets.py 体检：
#   civ6-modding/art/_projwrite.py、civ6-modding/tools/_projwrite.py、
#   civ6-modding/scripts/_projwrite.py、civ6-asset-forge/scripts/_projwrite.py、
#   civ6-art-reference/scripts/_projwrite.py、civ6-audio-pipeline/scripts/_projwrite.py
import argparse
import glob
import json
import os

_SNAPSHOTS = {}
_ROOTS = set()
_REPORTS = []

CODE_EXTS = (".sql", ".lua", ".xml", ".ini", ".gitignore", ".gitattributes")
PROJECT_EXTS = (".civ6sln", ".civ6proj", ".modinfo")
ART_EXTS = (".artdef", ".xlp", ".ast", ".mtl", ".dep", ".dds", ".tex",
            ".png", ".tga", ".jpg", ".jpeg")
AUDIO_EXTS = (".bnk", ".wem", ".wav", ".wwu", ".wproj")
# 兼容既有调用方（align_tex_format.py / prepare_frontend_portrait.py）
TEXT_EXTS = CODE_EXTS + PROJECT_EXTS

# prune_applied 的排除项：暂存部署副本、报告目录、build.py modinfo 的产物
PRUNE_SKIP_DIRS = ("Mods", "reports")
PRUNE_SKIP_SUFFIXES = (".modinfo",)


class CodeWriteForbidden(Exception):
    """脚本试图编写或改写代码文件。按铁律这是硬错误，不提供回退。"""


def classify(rel_path):
    """按工程内相对路径判定写入类别：code / project / art / audio。

    未知扩展名按 code 处理（失败关闭）：宁可拒绝，也不给绕过留口子。
    """
    name = os.path.basename(rel_path)
    ext = os.path.splitext(name)[1].lower()
    posix = rel_path.replace("\\", "/")
    if name.lower().endswith(".art.xml"):
        return "art"
    if posix.startswith("Platforms/Windows/Audio/"):
        # 只有 WwiseCLI 直接产出的三类算音频产物；<Bank>_Banks.ini 是手写注册文件，
        # 必须落到下面按扩展名判定的 code 分支。
        if ext in (".bnk", ".wem", ".xml", ".txt"):
            return "audio"
    if ext in CODE_EXTS:
        return "code"
    if ext in PROJECT_EXTS:
        return "project"
    if ext in ART_EXTS:
        return "art"
    if ext in AUDIO_EXTS:
        return "audio"
    return "code"


def _forbidden(target, rel, kind):
    if kind == "project":
        return ("%s 已存在，工程文件只能逐行编辑（焚诀·最严厉铁律）。"
                % rel)
    return ("%s 是代码文件，脚本不得编写或改写（焚诀·最严厉铁律）。"
            "结果请用 emit_report() 写到 workspace/gen/reports/，由人逐行写入工程。"
            % rel)


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def solution_root(project_root):
    """解决方案根：`.civ6sln` 所在的那一层。

    ModBuddy 的两层布局里工程根是 `<解决方案根>/<ModName>/`，`.civ6sln` 在其上一层；
    单层布局（`.civ6sln` 与 `.civ6proj` 同层）时就是工程根自身。
    """
    root = os.path.abspath(project_root)
    if glob.glob(os.path.join(root, "*.civ6sln")):
        return root
    return os.path.dirname(root)


def workspace_gen(project_root):
    """改写结果的落点：<解决方案根>/workspace/gen（工程核心文件夹之外，不入工程）。"""
    return os.path.join(solution_root(project_root), "workspace", "gen")


def is_direct(rel_path):
    """该相对路径是否属于允许脚本直接写盘的美术或音频产物。"""
    return classify(rel_path) in ("art", "audio")


def _snapshot(root):
    """进程首次写入某工程时记录其文件清单，用于识别「先删除、再新建」的绕过手法。"""
    if root not in _SNAPSHOTS:
        paths = set()
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
            for name in filenames:
                paths.add(_norm(os.path.join(dirpath, name)))
        _SNAPSHOTS[root] = paths
    return _SNAPSHOTS[root]


def _same_bytes(left, right):
    with open(left, "rb") as fa, open(right, "rb") as fb:
        return fa.read() == fb.read()


def _prune_empty_dirs(top):
    """自下而上删掉空目录（顶层本身与非空目录不动）。"""
    top_abs = os.path.abspath(top)
    for dirpath, _dirnames, _filenames in os.walk(top, topdown=False):
        if os.path.abspath(dirpath) == top_abs:
            continue
        if not os.listdir(dirpath):
            os.rmdir(dirpath)


def prune_applied(project_root):
    """回收历史遗留的暂存副本（旧机制把改写结果转存 gen），返回 (removed, pending, orphans)。

    新版不再产生暂存副本：代码文件一律拒写，结果只以数据清单的形式写进 gen/reports/。
    本函数只用于清理旧机制留下的残件——gen 与工程侧同相对路径逐字节相同即删，目录空即删。

    判据只看工程侧同相对路径的文件：
      · 存在且逐字节相同 → 删掉暂存副本（已写回，removed）；
      · 存在但内容不同   → 保留（尚未写回，pending）；
      · 工程侧不存在     → 保留（源文件已改名或删除，orphans，交人裁决）。
    整棵 gen/Mods（暂存部署副本）、gen/reports（数据清单）与 gen 顶层的 *.modinfo
    （build.py modinfo 的产物）不参与判定 —— 它们是派生产物，本来就没有工程侧对应文件。
    """
    root = os.path.abspath(project_root)
    gen = workspace_gen(root)
    removed, pending, orphans = [], [], []
    if not os.path.isdir(gen):
        return removed, pending, orphans
    for dirpath, dirnames, filenames in os.walk(gen):
        if os.path.abspath(dirpath) == os.path.abspath(gen):
            dirnames[:] = [d for d in dirnames if d not in PRUNE_SKIP_DIRS]
        for name in sorted(filenames):
            if os.path.abspath(dirpath) == os.path.abspath(gen) and name.lower().endswith(PRUNE_SKIP_SUFFIXES):
                continue
            staged = os.path.join(dirpath, name)
            rel = os.path.relpath(staged, gen)
            target = os.path.join(root, rel)
            if not os.path.isfile(target):
                orphans.append(rel)
                continue
            if not _same_bytes(target, staged):
                pending.append(rel)
                continue
            os.remove(staged)
            removed.append(rel)
    _prune_empty_dirs(gen)
    return removed, pending, orphans


def write_project_file(target, data, project_root):
    """写入工程文件。

    返回 NEW（官方工具从零产生的工程文件，已直写）、SAME（与既有一致，未动盘）、
    OVERWRITE（美术或音频产物，已直写覆盖）。
    代码文件一律抛 CodeWriteForbidden；工程文件已存在时同样抛，因为改动只能逐行编辑。
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    root = os.path.abspath(project_root)
    target = os.path.abspath(target)
    if not _norm(target).startswith(_norm(root) + os.sep):
        raise SystemExit("目标不在工程之内，拒绝写入：%s（工程：%s）" % (target, root))
    _ROOTS.add(root)
    rel = os.path.relpath(target, root)
    kind = classify(rel)
    if kind == "code":
        raise CodeWriteForbidden(_forbidden(target, rel, kind))
    exists = os.path.isfile(target)
    if exists:
        with open(target, "rb") as handle:
            if handle.read() == data:
                return "SAME"
        if kind == "project":
            raise CodeWriteForbidden(_forbidden(target, rel, kind))
        with open(target, "wb") as handle:
            handle.write(data)
        return "OVERWRITE"
    if _norm(target) in _snapshot(root):
        # 该路径在首次写入时已记录、此刻却不在盘上：既有文件被删除。
        # 删除是持久意图，脚本不得重建；交人裁决。
        raise CodeWriteForbidden(
            "%s 曾被记录为既有文件、现在不在盘上，脚本不得重建（焚诀·最严厉铁律）。" % rel)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "xb") as handle:
        handle.write(data)
    return "NEW"


def emit_report(name, payload, project_root):
    """把生成器的结果写成 workspace/gen/reports/ 下的数据清单，返回落盘路径。

    payload 为 dict 或 list 时写 JSON，为 str 时按原样写文本。
    报告不是工程文件，可以由脚本直接写。
    """
    gen = workspace_gen(project_root)
    out = os.path.join(gen, "reports", name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if isinstance(payload, (dict, list)):
        body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
    else:
        body = payload
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
    _REPORTS.append(out)
    return out


def finish():
    """打印本轮写出的报告清单，回收已写回的暂存副本，给出退出码。

    退出码恒为 0：本模块不再产生待写回的暂存副本。
    """
    if _REPORTS:
        print("")
        print("以下数据清单已写入 workspace/gen/reports/，请逐行写入工程：")
        for path in _REPORTS:
            print("  %s" % path)
    removed, pending, orphans = [], [], []
    for root in sorted(_ROOTS):
        got_removed, got_pending, got_orphans = prune_applied(root)
        removed.extend(got_removed)
        pending.extend(got_pending)
        orphans.extend(got_orphans)
    if removed:
        print("")
        print("已回收 %d 份历史遗留的暂存副本（workspace/gen）：" % len(removed))
        for rel in removed:
            print("  回收 %s" % rel)
    if pending:
        print("")
        print("以下历史遗留的暂存副本与工程内容不同（已不再产生，供人工核对）：")
        for rel in pending:
            print("  %s" % rel)
    if orphans:
        print("")
        print("以下暂存副本在工程里已没有同相对路径的文件（源文件已改名或删除，未动）：")
        for rel in orphans:
            print("  孤立 %s" % rel)
    return 0


def main():
    ap = argparse.ArgumentParser(description="回收 workspace/gen 里已写回工程的暂存副本")
    ap.add_argument("project", help="工程根目录（含 .civ6proj 或 *.Art.xml 的那一层）")
    ap.add_argument("--quiet", action="store_true", help="只打印汇总")
    args = ap.parse_args()
    removed, pending, orphans = prune_applied(args.project)
    if not args.quiet:
        for rel in removed:
            print("  回收 %s" % rel)
        for rel in pending:
            print("  待写回 %s" % rel)
        for rel in orphans:
            print("  孤立 %s" % rel)
    print("workspace/gen：回收 %d 项 / 待写回 %d 项 / 孤立 %d 项"
          % (len(removed), len(pending), len(orphans)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
