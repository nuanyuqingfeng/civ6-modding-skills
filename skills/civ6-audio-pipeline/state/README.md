# state（本机状态，不随 skill 分发）

此目录存放本机运行产生的 `id_registry.json`（已用 ShortID 注册表）。

- 由 `scripts/audio_pack.py scan` 生成/刷新（在 Wwise 打包前维护注册表防冲突）。
- 分享 skill 时请排除本目录下的 `id_registry.json`，避免把作者机器特有的成品 ID 表带给他人。
- 另外 skill 根目录的 `local_paths.json`（WwiseCLI / 模板 / ModBuddy 路径）同样是本机私有配置，分享前也应删除。
- 注意：正式音频交付走 Wwise Vorbis；`audio_pack.py` 的 speechbank/plainbank 仅为实验研究。
