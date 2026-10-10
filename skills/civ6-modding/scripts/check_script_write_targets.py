# -*- coding: utf-8 -*-
"""工程文件写入体检：脚本只能新建工程文件，改写一律走 _projwrite 入位 workspace/gen。

铁律真源：civ6-modding/SKILL.md「工程文件写入铁律」。

三条规则：
  规则一  六份 _projwrite.py 副本必须逐字节相同（唯一实现，禁止各写一份）。
  规则二  凡同时出现「工程标记」与「写盘调用」的脚本，必须 import _projwrite：
          允许脚本新建工程文件与直写可再生资产，改写的唯一通道是守卫模块。
  规则三  其余写盘调用只报告，不判违规（写临时目录、skill 自身目录、素材目录）。

豁免用显式表格声明（相对路径 → 理由），命中即跳过并在末尾列出，不静默跳过。

用法：
    python check_script_write_targets.py [--skills <skills 根目录>]

退出码：0 = 未发现问题；1 = 违规；2 = 参数或文件错误。
"""
import argparse
import ast
import hashlib
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

GUARD = "_projwrite.py"
GUARD_COPIES = (
    "civ6-modding/art/" + GUARD,
    "civ6-modding/tools/" + GUARD,
    "civ6-modding/scripts/" + GUARD,
    "civ6-asset-forge/scripts/" + GUARD,
    "civ6-art-reference/scripts/" + GUARD,
    "civ6-audio-pipeline/scripts/" + GUARD,
)

# 出现这些字符串说明脚本认识「工程」，此时写盘必须走守卫
PROJECT_MARKERS = ("civ6proj", ".modinfo", "--project", "project_root", "projectRoot")

WRITE_MODULES = {
    ("shutil", "copy"), ("shutil", "copy2"), ("shutil", "copyfile"), ("shutil", "copytree"),
    ("shutil", "move"), ("shutil", "rmtree"), ("os", "replace"), ("os", "remove"),
    ("os", "unlink"), ("os", "rename"), ("os", "rmdir"), ("os", "makedirs"),
    ("json", "dump"),
}
WRITE_METHODS = ("write_text", "write_bytes", "write")

# 含写盘调用但按设计不写工程的脚本（相对路径子串 → 理由）
EXEMPT_FILES = {
    "tools/modinfo_build.py": "构建与部署：只写 Mods 副本与 --out 指定的输出位置",
    "tools/cook_assets.py": "构建：只写 Mods 副本与构建输出目录",
    "tools/cook_dep.py": "构建：只写 --dependency_root 指定的输出位置",
    "tools/workshop_meta.py": "工坊元数据：写 --out / --record 指定的位置",
    "tools/workshop_cover.py": "封面排版：写 --out / --master / --preview 指定的位置",
    "tools/local_flux.py": "本地生图：写 --out 指定的位置",
    "tools/skill_manifest.py": "名录生成器：只写 skill 自身的 TOOLS.md",
    "tools/templates/workspace_build.py": "工程内构建入口模板，由 new_project.py 复制",
    "scripts/normalize_eol.py": "换行归一化：mod 工程只报告，--repo-skill 只写 skill 自身仓库",
    "scripts/clear_ae_cache.py": "删除 %APPDATA% 下的 AssetEditor 依赖缓存",
    "scripts/check_sql_exec.py": "校验器：只在 %TEMP% 建临时库",
    "database/scripts/build_localization.py": "写 skill 自身的 DebugLocalization.sqlite",
    "database/scripts/export_side_tables.py": "写 skill 自身的 annotations/ 侧表",
    "database/scripts/query_effect_args.py": "写 --dump-json 指定的位置",
    "database/api-verification-2026-09-08/": "一次性核验脚本，产物留在 skill 自身目录",
    "civ6-html-ui/scripts/": "HTML UI：写 --out 指定的纹理目录，不写 mod 工程",
    "civ6-art-reference/scripts/artdef_indexer.py": "重建索引：写 skill 自身的 assets/",
    "civ6-art-reference/scripts/artdef_sync_check.py": "体检报告：写 --report / --json 指定的位置",
    "civ6-audio-pipeline/scripts/audio_": "音频素材整备：写 --out 指定的位置",
    "civ6-audio-pipeline/scripts/ncm_decrypt.py": "解密产物写 --out 指定的位置",
    "civ6-audio-pipeline/scripts/music_features.py": "特征缓存写 --cache / --out 指定的位置",
    "civ6-audio-pipeline/scripts/ensure_template.py": "Wwise 模板工程落在用户主目录与 skill 配置",
    "civ6-audio-pipeline/scripts/new_bank_project.py": "建独立 Wwise 工程，不写 mod 工程",
    "civ6-audio-pipeline/scripts/wwise_": "改写 Wwise 工程工作单元，不写 mod 工程",
    "civ6-audio-pipeline/scripts/music_wire.py": "改写 Wwise 工程工作单元，不写 mod 工程",
    "civ6-audio-pipeline/scripts/build_combination_bank.py": "改写 Wwise 工程工作单元，不写 mod 工程",
    "civ6-audio-pipeline/scripts/wwise_shortid.py": "ShortID 分配表落在 skill 自身 state/",
    "civ6-modding/release/scripts/clash_proxy.py": "代理测速状态落在 %TEMP%",
    "civ6-modding/tools/_projwrite.py": "守卫模块自身",
    "civ6-modding/art/_projwrite.py": "守卫模块自身",
    "civ6-modding/scripts/_projwrite.py": "守卫模块自身",
    "civ6-asset-forge/scripts/_projwrite.py": "守卫模块自身",
    "civ6-art-reference/scripts/_projwrite.py": "守卫模块自身",
    "civ6-audio-pipeline/scripts/_projwrite.py": "守卫模块自身",
}


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def write_calls(tree):
    """返回该文件的写盘调用点列表 [(行号, 名称)]。"""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            name = func.attr
            base = func.value
            if name in WRITE_METHODS:
                found.append((node.lineno, name))
            elif isinstance(base, ast.Name) and (base.id, name) in WRITE_MODULES:
                found.append((node.lineno, base.id + "." + name))
        elif isinstance(func, ast.Name) and func.id in ("open", "compile"):
            if not node.args:
                continue
            mode = node.args[1] if len(node.args) > 1 else None
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode = keyword.value
            text = ast.dump(mode) if mode is not None else ""
            if any(flag in text for flag in ("'w'", "'a'", "'x'", "'wb'", "'ab'", "'xb'")):
                found.append((node.lineno, "open"))
    return sorted(set(found))


def main():
    parser = argparse.ArgumentParser(description="工程文件写入体检")
    parser.add_argument("--skills", default=os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    args = parser.parse_args()
    root = os.path.abspath(args.skills)

    bad = 0

    digests = {}
    for rel in GUARD_COPIES:
        path = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            print("缺失    守卫副本 %s" % rel)
            bad += 1
            continue
        digests[rel] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if len(set(digests.values())) > 1:
        print("不一致  守卫副本内容不同：")
        for rel, digest in digests.items():
            print("    %s  %s" % (digest[:12], rel))
        bad += 1
    elif digests:
        print("一致    %d 份守卫副本  sha256=%s" % (len(digests), list(digests.values())[0][:12]))

    reported = []
    skipped = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            try:
                text = read_text(path)
                tree = ast.parse(text)
            except (OSError, SyntaxError) as error:
                print("解析失败  %s：%s" % (rel, error))
                bad += 1
                continue
            calls = write_calls(tree)
            if not calls:
                continue
            exempt = next((reason for key, reason in EXEMPT_FILES.items() if key in rel), None)
            if exempt:
                skipped.append((rel, exempt, len(calls)))
                continue
            markers = sorted({m for m in PROJECT_MARKERS if m in text})
            guarded = GUARD[:-3] in text
            reported.append((rel, len(calls), guarded, markers))
            if markers and not guarded:
                print("违规    %s：含工程标记 %s 与 %d 处写盘，但未 import %s"
                      % (rel, ",".join(markers), len(calls), GUARD[:-3]))
                for line, call in calls:
                    print("            第 %d 行  %s" % (line, call))
                bad += 1

    print("")
    if reported:
        print("走守卫或与工程无关的写盘脚本：")
        for rel, count, guarded, markers in reported:
            print("    %s  写盘 %d 处  守卫 %s  工程标记 %s"
                  % (rel, count, "有" if guarded else "无", ",".join(markers) or "-"))
    if skipped:
        print("")
        print("显式豁免（%d 个脚本）：" % len(skipped))
        for rel, reason, count in skipped:
            print("    %s  写盘 %d 处  %s" % (rel, count, reason))

    print("")
    if bad:
        print("%d 处需要处理。" % bad)
        return 1
    print("工程文件写入体检通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
