# scripts/ —— 离线工具集

所有工具：**零第三方依赖**（只用 Python 标准库 / Node 内置）、支持参数化根目录、**带退出码**（可直接接 CI / 提交前钩子）。
基础库默认指向 `<本skill>/database/DebugGameplay.sqlite`，**原库只读**（需要写入时先复制到临时文件）。

## 1. 校验器（改完必跑）

| 脚本 | 查什么 | 用法 | 退出码 |
|---|---|---|---|
| `rgn_validate_runner.mjs` | **引用完整性**：悬空 ModifierId / Type / RequirementSetId …（实跑模式会真实执行项目 SQL 再查库比对） | `node rgn_validate_runner.mjs <目录> [模式=*.sql] [checkNaming=true] [--base <库>] [--static]` | 0 无悬空 / 1 有 |
| `check_sql_exec.py` | **可执行性**：非法转义、字符错位导致「整条 INSERT 报废」 | `python check_sql_exec.py [--root <工程>] [--base <库>]` | 0 / 1 |
| `check_types_kinds.py` | `INSERT INTO Types` 的 `Kind` 是否是引擎合法枚举（复现 `Invalid Reference on Types.Kind`） | `python check_types_kinds.py [--root <工程>] [--db <库>] [--dirs Data,Mod_Adaptation]` | 0 / 1 |
| `check_proj_content.py` | `.civ6proj` 的 `<Content Include>` 与磁盘是否**双向闭合**（悬空清单项 / 漏登记） | `python check_proj_content.py <工程根目录>` | 0 / 1 |
| `check_lua_registration.py` | **`.lua` 有没有有效加载路径**（按「UI 上下文 / include 扩展件 / GP 脚本」三角色判定） | `python check_lua_registration.py <工程根目录>` | 0 / 1 |
| `check_pantry.py` | **pantry 卫生**：`.tex` 是否只在 `Textures/`、`m_Name`/`m_RelativePath` 是否全工程唯一、有无 depot 库路径、非 ASCII 文件名、`.tex`↔`.dds` 配对 | `python check_pantry.py [--root <pantry>] [--quiet]` | 0 通过 / 1 有 error |
| `verify_trees.py` | 两棵目录树是否**逐字节相同**（递归 SHA256）—— 源 ↔ Mods 副本一致性 | `python verify_trees.py <dirA> <dirB>` | 0 相同 / 1 不同 |

### 三者互补，缺一不可

```
check_sql_exec.py   管「语句跑不跑得起来」   ← 一条语句报废时，数据根本没进库
rgn_validate        管「引用闭不闭合」       ← 语句都跑通了，但引用了不存在的东西
check_types_kinds   管「Kind 是不是合法枚举」← 打包不报错，加载期才丢弃
```

> **★ 为什么需要 `check_sql_exec.py`**：一条 `INSERT` 因 `'knight\'s story!'`（应为 `''`）整条报废时，
> 那批数据压根没进库，**引用自然也不会悬空** —— `rgn_validate` 看不到这类问题。
> 真实症状：中英文共用同一条 INSERT 时英文行报错 → **中文行一起丢失** → 游戏按 `LanguagePriorities` 回退 en_US → **中文环境显示英文**。
> 且 `executescript` / `sqlite3_exec` 遇错即停，**同一文件后续语句块也全部不执行**。

## 2. 运维脚本

| 脚本 | 作用 | 用法 |
|---|---|---|
| `clear_ae_cache.py` | 删 `%APPDATA%\AssetCloud\mod-<Mod>-asset-deps.json`（可再生，AssetEditor 会重建）。**开 AE 前若动过贴图，必须先清**，否则"移走问题文件仍不闪退"是缓存假象 | `python clear_ae_cache.py [--mod <名>] [--dry-run]` |

## 3. 语料工具

| 脚本 | 作用 | 用法 |
|---|---|---|
| `（语料执行器已移除）` | 查跨项目语料库（术语 / 剧情台词，多语言 + 说话人） | `node （语料执行器已移除） --q <关键词> [--table terms\|story] [--lang zh\|en\|ja] [--speaker <人名>] [--exact] [--limit N]` |

## 4. 标准验证顺序

```
① python check_sql_exec.py --root <工程>       # SQL 跑得起来吗
② node   rgn_validate_runner.mjs <工程>/Data   # 引用闭合吗
③ python check_types_kinds.py --root <工程>    # Kind 合法吗
④ python check_proj_content.py <工程>          # 打包清单闭合吗
⑤ python check_lua_registration.py <工程>      # 每个 .lua 都有有效加载路径吗
⑥ （动过贴图时）
   python check_pantry.py --root <工程>        # pantry 卫生
   python clear_ae_cache.py --mod <工程名>     # 清 AE 缓存，再开 AssetEditor 看日志有无 CRASH
```

### ⚠ 写这类工具时的两条血泪教训（都踩过）

1. **不要用 `<Tag>…</Tag>` 成对匹配去切 `.modinfo` / `.civ6proj` 的动作段** ——
   文件里存在**自闭合**动作标签（`<UpdateAudio id="Audio" />`），成对匹配会让它一路吞到下一个同名闭合标签，
   把中间夹着的其它动作整块吃掉（实测：`UpdateAudio` 吞掉了紧随其后的 `ImportFiles` 与 `AddUserInterfaces`，
   导致这两个动作的文件全部漏判 → 一片假阳性）。**改用边界法**（本动作开标签 → 下一个动作开标签）。
2. **判据上线前先用已知样本反向校验** ——
   `check_lua_registration.py` 第一版把「同名 xml 不在 `AddUserInterfaces`」一律报错，
   结果把官方的**整体替换**写法（同名 xml + lua 一起放 `ImportFiles`，如 `GovernorAssignmentChooser`）全误报。
   静判断次必须是：**先看有没有 (b) ImportFiles 这条路径**，再看 (c) 同名 xml 自动加载。
