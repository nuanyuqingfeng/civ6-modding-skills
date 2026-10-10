# 工程文件写入守卫：新建直写，改写一律入位 workspace/gen
#
# 铁律真源：civ6-modding/SKILL.md「工程文件写入铁律」。
# 脚本可以新建工程文件；改写既有工程文件由 AI 用文件编辑工具完成。
# 唯一例外：二进制与编码敏感的可再生资产（Textures/ 之下的贴图、Platforms/ 之下的
# 音频产物，以及扩展名 .dds/.tex/.bnk/.wem/.wav 的文件）由脚本直接覆盖 ——
# 文件编辑工具无法忠实写出这些字节。文本类注册文件（_Banks.ini 等）不走此例外。
#
# 六份副本必须逐字节相同，一致性由 civ6-modding/scripts/check_script_write_targets.py 体检：
#   civ6-modding/art/_projwrite.py、civ6-modding/tools/_projwrite.py、
#   civ6-modding/scripts/_projwrite.py、civ6-asset-forge/scripts/_projwrite.py、
#   civ6-art-reference/scripts/_projwrite.py、civ6-audio-pipeline/scripts/_projwrite.py
import os

STAGED = []

DIRECT_EXTS = (".dds", ".tex", ".bnk", ".wem", ".wav")
DIRECT_DIRS = ("Textures", "Platforms")
# 这些扩展名即使落在 DIRECT_DIRS 之下也是文本，必须走 workspace/gen 交 AI 写入
TEXT_EXTS = (".ini", ".xml", ".txt", ".sql", ".lua", ".json", ".xlp", ".artdef", ".ast", ".modinfo", ".civ6proj")


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def workspace_gen(project_root):
    """改写结果的落点：<工程>/workspace/gen（已被 .gitignore 忽略）。"""
    return os.path.join(os.path.abspath(project_root), "workspace", "gen")


def is_direct(rel_path):
    """该相对路径是否属于允许脚本直接覆盖的可再生资产。"""
    ext = os.path.splitext(rel_path)[1].lower()
    if ext in DIRECT_EXTS:
        return True
    head = rel_path.replace("\\", "/").split("/")[0]
    return head in DIRECT_DIRS and ext not in TEXT_EXTS


def write_project_file(target, data, project_root):
    """写入工程文件。

    返回 NEW（新建，已直写）、SAME（与既有一致，未动盘）、
    OVERWRITE（可再生资产，已直写覆盖）、STAGED（改写结果落在 workspace/gen）。
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    root = os.path.abspath(project_root)
    target = os.path.abspath(target)
    if not _norm(target).startswith(_norm(root) + os.sep):
        raise SystemExit("目标不在工程之内，拒绝写入：%s（工程：%s）" % (target, root))
    rel = os.path.relpath(target, root)
    if not os.path.isfile(target):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "xb") as handle:
            handle.write(data)
        return "NEW"
    with open(target, "rb") as handle:
        if handle.read() == data:
            return "SAME"
    if is_direct(rel):
        with open(target, "wb") as handle:
            handle.write(data)
        return "OVERWRITE"
    out = os.path.join(workspace_gen(root), rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as handle:
        handle.write(data)
    STAGED.append((target, out))
    return "STAGED"


def finish():
    """打印改写清单并给出退出码：无改写 0，有改写 2（等待用文件编辑工具写入工程）。"""
    if not STAGED:
        return 0
    print("")
    print("以下工程文件已存在且内容有变化，改写结果已写到 workspace/gen/ 的同一相对路径下：")
    for target, _ in STAGED:
        print("  %s" % target)
    print("请用文件编辑工具把改写结果写入上述工程文件。")
    return 2
