# civ6-modding-skills

文明 6（Civilization VI）mod 开发 AI skill 合集。8 个 skill 以子目录共存于本仓库 `main` 分支。

| 目录 | 管什么 |
|---|---|
| `skills/civ6-modding/` | 玩法侧总入口 + 发布：Lua（UI + GP）、ForgeUI XML、`.civ6proj` / `.modinfo`、数据库 XML/SQL、事件系统、API 参考、Steam 创意工坊发布 |
| `skills/civ6-art-reference/` | 引用原版美术素材：ArtDef/XLP 四层引用链 + cook 层（pantry 解析 / 产物归一化 / 警告即静默降级） |
| `skills/civ6-asset-forge/` | 2D 美术素材总入口：总督、忠诚度与宗教压力、单位晋升规格、2D 领袖纸片人、UI 立绘与选人背景、历史时刻插画、FrontEnd 立绘、区域图标、领袖头像、资源图标 |
| `skills/civ6-audio-pipeline/` | 音频全流程：素材整备 → 核验 → 按类别响度均衡 → Wwise 工程直改 → 自动注册 |
| `skills/civ6-tuner/` | FireTuner 运行时验证（TCP 4318）：在运行中的对局里执行 Lua |
| `skills/civ6-html-ui/` | HTML/CSS 设计 → UI 纹理 → 原生 XML/Lua |
| `skills/civ6-landmarks/` | 静态地标组合：SDK 官方几何 → Landmarks.artdef + tilebases.xlp + 建筑差分 → Cooker |
| `skills/civ6-art-unpack/` | 受限素材通道（默认禁用）：唯一入口是 `civ6-art-reference` SKILL.md 的路由句 |

各 skill 的详细内容以各自 `SKILL.md` 为准；家族路由、边界与共用约定见
`skills/civ6-modding/reference/FAMILY_INDEX.md`。

## 同步流程

本地各 skill 是独立 git 仓库，本仓库由 `civ6-modding/tools/sync_monorepo.py` 同步：
临时克隆本仓库到 `%TEMP%\civ6-mono`，逐个比对本地 skill 的 HEAD 树与云端 `skills/<名>/`
子树，只重新导出有差异的那些，提交、推送、核对云端 ref 后删除临时目录。

```bash
python ~/.agents/skills/civ6-modding/tools/sync_monorepo.py
```

参数（`--skills` / `--message` / `--dry-run` / `--keep` / `--proxy` / `--url`）见脚本 docstring。

本文件由该脚本从 `skills/civ6-modding/tools/monorepo_README.md` 复制，改动请改源文件。

## 许可

MIT，见 [LICENSE](LICENSE)。第三方吸收内容的许可与采用范围见各 skill 的
`THIRD_PARTY_NOTICES.md` 与 `SOURCES.md`。
