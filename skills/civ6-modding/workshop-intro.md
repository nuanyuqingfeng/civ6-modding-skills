# Civ6 工坊介绍与更新说明撰写

> ← 返回 `SKILL.md` 路由｜与 `release.md` 并列：本册管**上传什么文字**，`release.md` 管**怎么传上去**。

## When to Use

- 首次上传（创建新工坊条目）：撰写条目介绍（标题 + 描述）
- 更新已有条目：撰写本次更新说明（`changeNote`）与台账记录
- 声明条目依赖（官方 DLC / 资料片、其他工坊作品）

## 触发分流（硬性）

| 场景 | 判据 | 触发的流程 |
|---|---|---|
| 首次上传 | 工作区没有 `mod_id.txt`，且工坊无对应条目 | **介绍撰写流程**（本册 §一、§二）+ 依赖声明（§四） |
| 更新 | `mod_id.txt` 存在且条目已上线（台账为唯一真源） | **更新记录编写流程**（本册 §三）+ 依赖核对（§四） |

更新时不重写介绍正文；只有用户明确要求改介绍时才走 §二 的介绍撰写流程，并只改被点名的段落。

## 一、介绍的三栏口径

描述正文由三栏拼成，来源与责任互不混淆：

| 栏 | 内容 | 来源 | 缺省行为 |
|---|---|---|---|
| 甲 预置模板 | 点赞横幅、QQ 群宣传行 | `release/templates/intro-presets.md`（**本机自留**，分享 skill 时不带） | 需要时整段插入；不需要则整段不写 |
| 乙 用户提供 | 前置/依赖行、标语或引言、致谢、写在最后 | 用户逐字提供 | 用户未提供即整节不写；**不得代写、不得留占位符** |
| 丙 自动提取 | `[code]` 内部全部内容：文明能力、各领袖能力、特色区域 / 特色建筑 / 特色单位 / 声骸单位 / 特色改良设施 / 特色伟人 / 特色总督 / 特色项目 | agent 从工程 `Text/` 的本地化文本提取并整理 | 必须生成；缺项列出清单 |

标题（各语言 `title`）的来源：**作者明确指定时用指定的**；未指定时**以工程 `.civ6proj`（或派生 `.modinfo`）里的 `..._MOD_TITLE` 各语言文本为准**，取法见 §二 第 1 步。更新条目时标题不动（`update` 模式不写 `title`）。致谢、宣传、作者感想属乙栏，agent 不撰写、不补全。

## 二、首次上传：介绍撰写流程

1. **定语言档位与标题**：8 语言（english / schinese / tchinese / japanese / koreana / german / spanish / french）为默认；轻量条目可降为 5 / 3 / 2 语言。
   ```powershell
   python "$env:USERPROFILE\.agents\skills\civ6-modding\tools\workshop_intro.py" titles <源工程根> `
       --spec <workspace>\tmp\workshop.spec.json [--write]
   ```
   `titles` 按 `语言 → Locale` 映射读取 `..._MOD_TITLE`（缺该条目时退回任一 `..._TITLE`），逐语言打印字节数与超限提示，并可把规格 JSON 里的空 `title` 回填；作者已填的标题原样保留，`--write` 才写盘。标题上限 `k_cchPublishedDocumentTitleMax = 128 + 1`（含结尾的 NUL），按 UTF-8 字节判定，超限会被上传器截断或拒收（工具超 128 字节时退出码 2）。
2. **提取丙栏**：
   ```powershell
   python "$env:USERPROFILE\.agents\skills\civ6-modding\tools\workshop_intro.py" scan  <源工程根>
   python "$env:USERPROFILE\.agents\skills\civ6-modding\tools\workshop_intro.py" build <源工程根> `
       --order <order.json> --langs english,schinese,... --out <workspace>\tmp\workshop.spec.json
   ```
   `scan` 列出候选 tag（按条目类型分组），agent 据此写 `order.json`（节序与 tag 绑定）；`build` 产出各语言 `[code]` 主体、含空 `preamble` / `postamble` 字段的规格 JSON、以及缺失 tag 清单。
3. **人工校对丙栏**：数值、术语、取代关系、标点；`[ICON_*]`、`[NEWLINE]`、`[COLOR:...]` 一类标记由工具清除，措辞与句式由 agent 整理。
4. **按需插入甲栏**：点赞横幅与 QQ 群行取自 `release/templates/intro-presets.md`。
5. **逐字写入乙栏**：用户给的前置行、标语、致谢、写在最后；未给的段落留空。
6. **长度检查**：整篇 description ≤ 8000 字节（依据见 §六）。
7. **生成 `workshop.json`**：`python "<skills>/civ6-modding/tools/workshop_meta.py" <spec.json> --out <ws>\workshop.json --record <存档路径>`。
8. **依赖声明**：按 §四 生成 `dependencies` 并写入规格 JSON 后再上传。

## 三、更新：更新记录编写流程

1. **取基线**：台账「条目详情」的 `上传基线（commit）`；缺该字段时先按台账 `time_updated` 反查提交补录，或由用户给出范围。
2. **生成草稿**：
   ```powershell
   python "$env:USERPROFILE\.agents\skills\civ6-modding\release\scripts\draft_note.py" `
       --project <源工程根> [--since <commit>] --out <workspace>\tmp\note-draft.md
   ```
   草稿含两份：`changeNote` 草稿（玩家视角、1~3 条编号、无路径无标识符）与台账「历史版本」行草稿（规模归因 + 固定小节序列）。
3. **人工精简**：按 §五 的风格与排序规则定稿；用户给了文案时以用户文案为准。
4. **写 `workshop.json`**：只更新内容时写 `{"changeNote": "..."}`；**若线上条目有依赖，必须同时写 `dependencies` 全量列表**（见 §四）。
5. **上传并验证**，把台账「上传基线」更新为本次的 `commit` / `hcontent_file` / `time_updated`。

## 四、依赖声明（首次上传必做，更新必核对）

### 4.1 两类依赖去往不同位置

| 依赖类型 | 声明位置 | 说明 |
|---|---|---|
| 工坊作品 | `workshop.json` 的 `dependencies`（数值工坊 ID 数组） | 上传器用 `SteamUGC.AddDependency` / `RemoveDependency` 写入条目页的依赖列表 |
| 官方 DLC / 资料片 | 源工程 `.civ6proj` 与派生 `.modinfo` 的 `<Dependencies>` / `<AssociationData>` | 工坊 API 不接受 DLC；条目页无法声明，只能在介绍里提示玩家 |

### 4.2 `dependencies` 是全量列表（硬性）

上传器在**每次上传**结束时都对依赖做一次增删同步：列表里没有的线上依赖会被**删除**。因此：

- 首次上传：按 `workshop_intro.py deps <源工程根>` 的结果写入全部工坊作品 ID；
- 更新：先核对台账与线上依赖，把**全量** `dependencies` 写进本次 `workshop.json`；只写 `changeNote` 会把已有依赖清空；
- 在 Steam 网页端手工添加的依赖，会被下一次上传覆盖（同一同步逻辑），以 `workshop.json` 为唯一真源。

### 4.3 生成依赖清单

```powershell
python "$env:USERPROFILE\.agents\skills\civ6-modding\tools\workshop_intro.py" deps <源工程根>
```

工具读取 `.civ6proj` 的 `<AssociationData>`，把 `type="Dlc"` 的条目列为官方依赖（进 `.modinfo`，并提示写进介绍的前置行），把工坊作品按其 GUID 在本机工坊内容目录（`_paths.py` 的 `workshop_ref`）反查数字 ID，解析不到的 GUID 单独列出要求人工确认。

## 五、更新说明（`changeNote`）的写法与排序

### 5.1 风格分类

| 风格 | 形态 | 用例 |
|---|---|---|
| A 默认 | `Update content (YYYY-MM-DD)` | 无面向玩家的实质改动时 |
| B 单句 | 一句话描述玩家可感知的现象，如 `修复魔术先生表演不触发夏空灵感的问题` | 单点修复 |
| C 编号多条 | `1、…；2、…；3、…。` | 多项改动 |
| D 双语 | 中英各一份 | 面向外文订阅者 |
| E 首传 | `首次发布 / Initial release` | 创建条目 |
| F 空对象 | `{}`（不留任何说明） | 只改内容元数据、用户明确要求不留 |
| G 用途 | `更新封面 / Updated cover art` | 只换封面或只改介绍 |
| H 短语 | `1 领袖纸片 + 2 阿漂发光读档修复` | 批量更新时多条条目共用一句 |

### 5.2 排序规则

- 单个说明内按「修复 → 新增或强化 → 平衡调整 → 文本与本地化」排列；编号用 `1、2、3` 或 `①②③`，两者不混用。
- 说明里不出现文件路径、函数名、标识符；只在台账明细里写代码级内容。
- 线上 changelog 由 Steam 按更新时间倒序展示；台账「历史版本」按版本号倒序、「操作历史」按日期倒序且新行插入表首，与线上顺序一致。
- 台账「历史版本」单行内部固定小节序列：① 本次内容改动（按子系统分组）→ ② 随行既有改动 → ③ 流程或策略变更 → ④ 工作区与元数据 → ⑤ 校验与门禁 → ⑥ 上传与验证 → ⑦ 清理；规模归因（文件数 / 字节数 / 净变化）写在版本号后的括号内。

## 六、长度上限

整篇 description 连同甲、乙栏一并计入，上限 **8000 字节**（UTF-8）。依据：`k_cchPublishedDocumentDescriptionMax = 8000`，Steamworks 文档写「创意工坊项目描述可以使用的最大字节数」，头文件对应定长字节数组 `char m_rgchDescription[8000]`；常量名里的 `cch`（字符计数）与 TF2 维基「描述字符限制 8000」的中文措辞是「8000 字符」这一说法的来源，实测按字节判定（见下）。`workshop_meta.py` 按字节判失败，同时打印字符数备查。

字节换算：汉字、假名、谚文 3 字节，ASCII 1 字节，实测成品约 2.1–2.5 字节/字符（中文约 3200 字、英文约 7900 字符可用）。本机 12 个工程的全部线上描述均在 6654–7946 字节之间。

实测记录（2026-10-21，测试条目 `3679086609`）：8000 字节的描述上传返回 OK 且 manifest 变化；8001 字节返回 `k_EResultAccessDenied`，Steam 日志记 `Upload finished ... : Access Denied`。结论：**按 UTF-8 字节判定，上限 8000 字节，超出直接拒收而非截断**；工具侧一律按字节控制。

测试期间同一作品被连续上传多次时出现条目级 `k_EResultAccessDenied`（与描述长度无关，241 字节的短描述同样被拒），属上传节流，静默数分钟后恢复；两种成因的判别与处置见 `release/docs/troubleshooting.md` 第 7 节。因此**同一作品不要在同一分钟内反复上传**，改介绍与改内容各上传一次即可。

英文与其余外文档位为精简版，压缩规则：文明能力与领袖能力保留原文；领袖名下「特色区域 / 特色单位」删首句身份句；末尾共通项并为一行摘要；致谢保留人名、去掉括注；删除 `[code]` 以外的多余空行。

## 七、节序与标记

介绍正文自顶向下：甲栏（点赞横幅 → 可选社群行）→ 乙栏（前置/依赖行 → 标语）→ `[hr][/hr]` → `[code]` → 文明块 → 各领袖块（按包内领袖顺序）→ 通用共同项块 → 致谢（乙栏）→ `[/code]` → `[hr][/hr]` → 写在最后（乙栏）。

`[code]` 内部条目顺序固定：特色区域 → 特色建筑 → 特色单位 → 声骸单位 → 特色改良设施；条目行统一为 `[h3]条目类型：名称[/h3]` 后接正文，文明用 `[h1]`、领袖用 `[h2]`。

标记用法与实测清单见 `xml-templates.md` 的工坊标记节与 `release/templates/intro-presets.md`；可用标记为 `[h1]`~`[h3]`、`[b]`、`[u]`、`[list]`、`[olist]`、`[*]`、`[hr]`、`[code]`、`[url=…] 文本 [/url]`、`[img]`。

## 八、验收清单

- `[code]` 主体逐条来自工程 `Text/`，无自拟能力描述；
- 甲栏按需插入、乙栏与用户提供内容逐字一致，未提供的段落不存在（无占位符）；
- 各语言档位齐全，标题前缀符合 `[EN] / [JP] / [KR] / [TC]` 惯例（简中与德/西/法不带前缀）；
- `workshop_meta.py` 退出码 0，且长度、占位符两项检查通过；
- 首传条目 `dependencies` 与 §四 结果一致；更新条目依赖与线上核对无丢失；
- 更新说明符合 §五，台账「历史版本」「操作历史」「上传基线」三处已回写。

## Related Skills

- `civ6-modding`（本文件所属家族）：`release.md` 上传与更新流程、`civ6-text-authoring` 文本写法规范
