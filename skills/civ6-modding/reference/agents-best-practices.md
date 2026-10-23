# Civ6 Mod 工程 AGENTS.md 项目级约定参考

本文件提炼本机 Civ6 mod 工程 AGENTS.md 中的项目级约定，供新建工程时派生使用。通用操作约束的源头是 `~/.agents/templates/agents-rules-canonical.md`，本文件不重复其内容。

## 一、规则分层

| 内容类型 | 真源 | 同步方式 |
|---|---|---|
| 引擎行为、API、Modifier、数据表结构 | `civ6-modding/SKILL.md` 及其模块 | 随 skill 更新 |
| 操作约束、Git 授权、提交流程 | `~/.agents/templates/agents-rules-canonical.md` | 复制到各工程 AGENTS.md 焚诀节，用 `fenjue_check.py` 核对 |
| 项目级约定（缩写表、双目录路径、私有门禁） | 本文件派生到各工程 AGENTS.md | 新工程创建时人工取舍 |

工程 AGENTS.md 的结构顺序：规则优先级说明 → 命名规范与缩写表 → 焚诀节（逐字粘贴模板） → 项目约定（双目录、UI 通信、公用函数） → 项目 Gotcha → 交付门禁。

## 二、命名规范

### 主体与客体

`Type` 列的对象是主体，缩写放在名称末尾；`ID` 列的对象是客体，缩写放在类型词之后。

- 主体：`RESOURCE_AUREO_RGN`、`BUILDING_SWORD_DIVINITY_RGN`、`GREATWORK_PRODUCT_AUREO_RGN_1`
- 客体：`TRAIT_RGN_WATER_FAITH`、`REQSET_RGN_PLOT_IS_WATER`、`PROPERTY_RGN_SWORD_TIER`

框架前缀（`MOD_`、`MODIFIER_`、`REQUIREMENT_`）不承担主体角色。Modifier 专用于分发且没有明确主体时，允许使用裸缩写前缀。

### 缩写表

每个工程维护自己的缩写表，条目覆盖文明、领袖、区域等命名空间。缩写由工程作者决定，AI 不自行增补，也不把某个工程的私有缩写写进模板。

### 用户自拟命名空间

`CIVILIZATION_*`、`LEADER_*`、`TRAIT_*` 的 Type 定义由作者自拟，AI 只检查定义与引用是否闭合，不纠正命名格式。`TRAIT_*` 开头的 `ModifierId` 仍受客体命名规则约束。

### 文件名

- 数据与文本文件使用「主题 + 项目缩写」，例如 `Buildings_RGN.sql`、`Text_Leader_Cartethyia_RGN.sql`。
- Lua 文件按上下文分域命名：Core 用 `Core_<主题>.lua`，GamePlay 用 `Lua_<主题>_<缩写>.lua`，UI 用功能专名。
- 引擎 include 的 Lua 文件禁止使用通用裸名（如 `Utils.lua`），同名文件会在同一上下文互相覆盖。

## 三、双目录工作流

- 源文件目录由 git 管理，是正式改动的归宿。
- Mods 目录是游戏加载目录，只用于测试，不进入 git。
- 单次修改超过 50 行、涉及批量替换或跨 3 个以上文件时，先提示是否提交 git。
- 测试需求出现时，先确认是否同步到 Mods，复制后用哈希校验确认一致。
- 测试期间的临时改动留在 Mods，测试结束后统一回写源文件并提交，未保留项丢弃。
- 提交前检查两个目录是否一致，存在未回写改动时先回写。
- 调试输出默认只加在 Mods 目录。源文件的交付内容保持干净，先同步干净版本，再在 Mods 叠加调试信息。
- 检测到两个目录不一致时停止改动，概括差异清单后等待指示。

## 四、文件写入边界

- 工作区固定在 `.civ6sln` 所在目录的 `workspace/`，项目主体目录内不出现 workspace、gen、tmp、备份目录及资产库副本。
- 只有本次任务点名的目标文件进入项目主体目录，其余文件写入 `workspace/`。
- 项目主体内已有的文件不得擅自迁移，疑似遗留的文件先询问。
- 默认不建立备份副本。可再生文件直接修改，git 可管理的文件历史交给 git，不可再生的源文件由用户保管。
- `workspace/tmp` 在任务结束时清理，`workspace/gen` 的内容写入项目主体后清理。

## 五、UI 通信与公用函数

- 跨端通道、报错形态与术语以 `civ6-modding/reference/context-matrix.md` 为唯一真源。
- 按钮回调触发的 UI→GamePlay 调用使用 `EXECUTE_SCRIPT`。
- 被动触发需要跨端返回值时可用暴露函数，使用前取得用户同意。
- UI 端的公共暴露函数集中在一个文件，新增暴露函数放入该文件。
- 公用检测函数只做布尔判断，数值读取用引擎接口直接取得。

## 六、工程清单同步

- 修改 `.civ6proj` 或 `.modinfo` 前先读 `civ6-modding/project-setup.md` 的「文件清单同步」。
- XML、SQL、Lua 必须写入 `<Content Include="...">` 清单。
- 美术侧文件（`XLPs/*.xlp`、`ArtDefs/*.artdef`、`*.Art.xml`）不进入工程清单，由 cooker 与 AssetEditor 处理。
- 存在 `*.Art.xml` 时，`<FrontEndActionData>` 与 `<InGameActionData>` 两侧都要有 `<UpdateArt>`，文件写 ModBuddy 占位符 `(Mod Art Dependency File)`。
- 双向闭合体检使用 `check_proj_content.py`，交付包体检使用 `verify_mod_package.py`。

## 七、交付门禁

- 涉及布局、颜色、字体的视觉改动必须进游戏观察，静态校验不足以判定完成。未实机观察的改动标注「已修改，待验证」。
- 涉及 `.lua` 改动的任务运行 `check_lua_context.py`，结果须为 0 问题。
- 修改 `*_RGN.sql` 后运行 `dsh_validate` 或离线执行器，悬空引用全部处理。
- 游戏内文本必须通过 `<UpdateText>` 加载 `Text/*.sql`；`.modinfo` 的 `<LocalizedText>` 只影响 mod 选择界面。
- `.modinfo` 与 `.civ6proj` 的 `<Authors>` 使用工程作者署名；封面与预览图不署名。

## 八、编码与换行

- 文件读写使用 UTF-8，修改时保持原有编码、换行风格与无关内容。
- 代码文件使用 CRLF：`.lua`、`.sql`、`.xml`。
- 资产文件使用 LF：`.artdef`、`.xlp`、`.txt`。
- 二进制文件（`.fgx`、`.wig`、`.dds`）不按文本处理。
- 换行体检使用 `normalize_eol.py`，默认只报告，`--fix` 才写入。

## 九、旧存档

新增或修改 PROPERTY、数据结构、触发条件、注册动作时不做存档迁移，不编写兼容逻辑。测试存档默认作废，验证以新开一局为基准。

## 十、项目 Gotcha 示例

每个工程在 AGENTS.md 记录本工程特有的问题，条目包含症状、原因、正确写法与校验方式。常见条目：

- 2D 领袖纸片材质类使用 `Leader_Matte`，错用 `Leader` 会导致纸片发灰发闷。
- `Improvements.Coast` 表示沿海陆地，水域改良使用 `Domain='DOMAIN_SEA'` 且 `Coast=0`。
- `.tex` 只存放在 `Textures/` 并与 `.dds` 一一对应，其他目录的同名副本会抢占注册。
- mod 的 GUID 以本工程现网文件为准，禁止从示例或其他 mod 复制。
- 未加载 `<UpdateText>` 时游戏内只显示 `LOC_XXX` 键名，mod 列表看起来正常。
