# -*- coding: utf-8 -*-
"""Skill 路径配置中心（本机私有，不随 skill 分发）。

读取 skill 根目录 `local_paths.json`；也支持同名 `CIV6_*` 环境变量覆盖，
方便在没有配置文件的 CI/新机器上临时指定：

    CIV6_WWCLI        WwiseCLI.exe 绝对路径
    CIV6_TEMPLATE_FULL 完整模板工程目录
    CIV6_P1           ModBuddy 源工程根目录
    CIV6_P2           Civ6 运行 Mods 目录

`local_paths.json` 示例：
    {
        "wwcli": "D:/Wwise_v2015.1.9/.../WwiseCLI.exe",
        "template_full": "D:/.../WWiseProject/FelineJasperKitty",
        "p1": "D:/documents/Firaxis ModBuddy/Civilization VI",
        "p2": "D:/documents/My Games/Sid Meier's Civilization VI/Mods"
    }
"""
import os
import json
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
LP = os.path.join(SKILL, 'local_paths.json')
_ENV_PREFIX = 'CIV6_'


def _load():
    data = {}
    try:
        if os.path.exists(LP):
            with open(LP, encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
    except Exception:
        data = {}
    return data


def get(key, default=None):
    """返回 local_paths.json 中 key 的值；未设置时回退环境变量，再回退 default。"""
    data = _load()
    val = data.get(key)
    if val:
        return val
    env = os.environ.get(_ENV_PREFIX + key.upper())
    if env:
        return env
    return default


# ---------------------------------------------------------------- 自查辅助（不改动 get() 语义）

KNOWN_KEYS = ('wwcli', 'template_full', 'p1', 'p2')

_KEY_HINTS = {
    'wwcli': 'WwiseCLI.exe 绝对路径（Wwise 2015.1）',
    'template_full': '完整模板工程目录（WWiseProject/FelineJasperKitty）',
    'p1': 'ModBuddy 源工程根目录',
    'p2': 'Civ6 运行 Mods 目录',
}


def summary(keys=None):
    """各键「已配置 / 缺失」一览（与 civ6-modding/tools/_paths.py 的 summary() 对齐）。"""
    rows = []
    for k in (keys or KNOWN_KEYS):
        v = get(k)
        if not v:
            mark, shown = '[缺失]  ', '(未配置)'
        elif os.path.exists(v):
            mark, shown = '[已配置]', v
        else:
            mark, shown = '[已配置·路径不存在]', v
        rows.append('  %-14s %s %s' % (k, mark, shown))
    return '\n'.join(rows)


def describe_missing(keys=None):
    """只列缺失的键，并逐条给出「写哪、写什么、对应哪个环境变量」。"""
    miss = [k for k in (keys or KNOWN_KEYS) if not get(k)]
    if not miss:
        return '全部键均已配置。'
    rows = ['缺失 %d 个键（写入 %s，或用环境变量临时指定）：' % (len(miss), LP)]
    for k in miss:
        rows.append('  %-14s %s' % (k, _KEY_HINTS.get(k, '')))
        rows.append('  %-14s → local_paths.json: {"%s": "<你的绝对路径>"}   或   环境变量 %s%s'
                    % ('', k, _ENV_PREFIX, k.upper()))
    return '\n'.join(rows)


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    print('civ6-audio-pipeline 本机路径配置：')
    print(summary())
    print()
    print(describe_missing())
    print()
    print('提示：%s%s' % (LP, '（不存在，可自行新建）' if not os.path.exists(LP) else ''))
