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
