# -*- coding: utf-8 -*-
"""export_side_tables.py — 把 `DebugLocalization.sqlite` 的**人工标注侧表**导出为随包 JSON。

## 为什么需要它

`database/DebugLocalization.sqlite` 已改为**本机重建、不入库**（见 database/README.md §零），
但它里面的两张侧表是**不可再生的人工成果**：

| 侧表 | 行数 | 内容 |
|---|---|---|
| `SkillAnnotation_Icons`  | 241 | 图标名 → 中文备注（`ICON_Bullet` → 项目符号图标） |
| `SkillAnnotation_Colors` |  51 | 颜色名 → 中文备注（`COLOR_Civ6DarkRed` → 文明6暗红色） |

若只把它们留在不入库的 sqlite 里，**换机器就永久丢失**。因此导出到
`database/annotations/localization_side_tables.json`（随包），重建时再由
`build_localization.py --rebuild` 自动灌回。

## 用法

    # 导出（侧表有改动时跑）
    python export_side_tables.py                 # 写入 annotations/ 下的规范位置
    python export_side_tables.py --out <路径>    # 指定输出
    python export_side_tables.py --check         # 只比对，不写（CI/体检用）

退出码：0 = 一致/已写；1 = --check 发现漂移；2 = 错误。
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(SKILL_DIR, "database", "DebugLocalization.sqlite")
OUT = os.path.join(SKILL_DIR, "database", "annotations", "localization_side_tables.json")

SIDE_TABLES = {
    "SkillAnnotation_Icons": "icons",
    "SkillAnnotation_Colors": "colors",
}

GAME_ROOT_HINT = r"F:\Steam\steamapps\common\Sid Meier's Civilization VI"


def read_extra_rows(db: str) -> list:
    """库中「游戏安装里没有」的行 —— 即非官方来源（本项目自造 tag 等）。

    这类行**不在任何游戏文件里**，重建时不会被重新生成 → 必须随包保存，
    否则换机器就丢。实测当前有 64 行（8 个 `_QYQXP_` 百科 tag × 8 语言）。
    """
    game = game_root()
    if not game or not os.path.isdir(game):
        return []
    tags = _game_tags(game)
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    try:
        rows = [(r[0], r[1], r[2] or "", r[3], r[4]) for r in
                con.execute("SELECT Language,Tag,Text,Gender,Plurality FROM LocalizedText")]
    finally:
        con.close()
    return [{"language": l, "tag": t, "text": x, "gender": g, "plurality": p}
            for (l, t, x, g, p) in rows if t not in tags]


def game_root() -> str | None:
    sys.path.insert(0, os.path.join(SKILL_DIR, "tools"))
    try:
        import _paths  # type: ignore
        return _paths.get("game")
    except Exception:
        return GAME_ROOT_HINT if os.path.isdir(GAME_ROOT_HINT) else None


def _game_tags(game: str) -> set:
    """游戏安装里出现过的全部 tag（Base + DLC）。"""
    import glob
    tags: set = set()
    for f in glob.glob(os.path.join(game, "Base", "Assets", "Text", "**", "*.xml"), recursive=True):
        try:
            s = open(f, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        tags |= set(_TAG_RE.findall(s))
    for f in glob.glob(os.path.join(game, "DLC", "**", "*.xml"), recursive=True):
        if os.sep + "Text" + os.sep not in f:
            continue
        try:
            s = open(f, encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        tags |= set(_TAG_RE.findall(s))
    return tags


_TAG_RE = __import__("re").compile(r'<(?:Row|Replace)\s+Tag="([^"]+)"')


def read_side_tables(db: str) -> dict:
    if not os.path.isfile(db):
        raise SystemExit("找不到库：%s（先按 database/README.md §零 重建）" % db)
    con = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    out: dict = {}
    try:
        tabs = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for t, key in SIDE_TABLES.items():
            if t not in tabs:
                out[key] = []
                continue
            cols = [r[1] for r in con.execute("PRAGMA table_info('%s')" % t)]
            # 统一成 {Name/Type, Remark} 两列语义
            keycol = "Name" if "Name" in cols else ("Type" if "Type" in cols else cols[0])
            out[key] = [
                {keycol.lower(): r[0], "remark": r[1] if len(r) > 1 else ""}
                for r in con.execute("SELECT %s, Remark FROM %s ORDER BY 1" % (keycol, t))
            ]
    finally:
        con.close()
    return out


def build_payload(data: dict, extra: list) -> dict:
    return {
        "schemaVersion": 1,
        "purpose": ("Skill-only annotations migrated out of DebugLocalization.sqlite. "
                    "That DB is rebuilt locally and not tracked in git, so these curated rows "
                    "live here to survive on fresh machines."),
        "warning": ("Neither the side tables nor `extraRows` are official game content — never "
                    "emit them into mod SQL. They exist so the skill can map icon/color names to "
                    "Chinese remarks, and so non-official localization rows are not lost."),
        "restore": ("`python database/scripts/build_localization.py --rebuild` restores both the "
                    "side tables and `extraRows` into the rebuilt DebugLocalization.sqlite."),
        "counts": dict(list({k: len(v) for k, v in data.items()}.items())
                       + [("extraRows", len(extra))]),
        "tables": data,
        "extraRows": extra,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="导出本地化库的人工标注侧表为随包 JSON")
    ap.add_argument("--db", default=DB)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true", help="只比对，不写盘")
    args = ap.parse_args()

    payload = build_payload(read_side_tables(args.db), read_extra_rows(args.db))
    text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False) + "\n"

    if args.check:
        if not os.path.isfile(args.out):
            print("DRIFT: 缺少随包 JSON %s（侧表只在未入库的 sqlite 里 → 换机器会丢）" % args.out)
            return 1
        cur = open(args.out, encoding="utf-8").read()
        if cur == text:
            print("OK  %s 与当前库的侧表一致（%s）"
                  % (os.path.basename(args.out),
                     ", ".join("%s=%d" % (k, v) for k, v in payload["counts"].items())))
            return 0
        print("DRIFT: %s 与当前库的侧表不一致（库里的更新）→ 跑一次导出" % args.out)
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("已导出 %s" % args.out)
    for k, v in payload["counts"].items():
        print("   %-8s %d 行" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
