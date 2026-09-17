# cook 层 —— 依赖声明、产物归一化、警告语义

> 本文件补的是 `chain-map.md`「四层引用链」**之上**的一层：ModBuddy 把
> `ArtDefs/*.artdef`、`XLPs/*.xlp` cook 成游戏实际加载的产物时，发生了什么、
> 报错怎么读、产物能不能直接当交付物。
>
> **全部结论为实测**（2026-09，示例工程 工程，Base + 全 DLC 环境），原始证据见文末 §七。

## 零、为什么需要这一层

四层引用链（DB Type → artdef → Xref → BLP）解决的是「**引用写对了没有**」。
但即使引用全对，cook 阶段仍可能：

1. **找不到源文件** —— 因为 mod 没声明对美术包依赖，cooker 的 pantry 搜索路径里没有那个包（§一）；
2. **悄悄降级语义** —— 解析不到的引用被替换成默认值，只在日志里留一行 warning（§三）；
3. **产出与源文件不一致** —— 归一化让 `ArtDefs/` 与游戏加载的副本逐字节不同（§二）。

**注册对了 ≠ cook 过了 ≠ 运行时对。** 三层要分别验证。

---

## 一、cook 流程与 pantry 解析

### 1.1 ModBuddy 到底执行什么（实测）

`<SDK>\ModBuddy\Civ6.targets` 里两个任务串起来：

```xml
<GeneratePantryPaths AssetsPath="$(Civ6_AssetsPath)" ArtXmlPath="$(ProjectArtXml)">
  <Output TaskParameter="PantryPath" PropertyName="PantryPath"/>
</GeneratePantryPaths>
...
<!-- ArtDef 模式 -->
<ArtDefCookerCmd>... --mode ArtDef --platform Windows
   --pantry "$(ProjectDir)" $(PantryPath)
   --banquet_hall "$(BuildDir)\ArtDefs" --config "$(CookerConfig)"</ArtDefCookerCmd>
<!-- XLP 模式 -->
<XLPCookerCmdWindows>... --mode XLP --platform Windows
   --pantry "$(ProjectDir)" $(PantryPath)
   --stewpot "$(BuildDir)\Platforms\Windows\BLPs" --config "$(CookerConfig)"</XLPCookerCmdWindows>

<Exec Command="$(ArtDefCookerCmd) &quot;%(ArtDefFiles.FullPath)&quot;"
      ConsoleToMsBuild="true" IgnoreExitCode="true" Condition="@(ArtDefFiles) != ''"/>
```

三个必须知道的点：

| 点 | 含义 |
|---|---|
| `--pantry "$(ProjectDir)"` 排在最前 | **mod 目录自己也是一个 pantry**（AGENTS 的「pantry 卫生」铁律即由此而来：cooker 会递归扫整棵工程树） |
| `$(PantryPath)` 由 `.Art.xml` 推出 | 缺声明 → 搜索路径里没有那个包的源素材 → §1.4 的一整类报错 |
| `ConsoleToMsBuild="true"` + `IgnoreExitCode="true"` | cooker 的 stderr 行被 MSBuild 重新分级为 `error …`；同时**退出码被忽略**，所以 cooker 失败（甚至 `exit 2`）时构建仍报 succeeded —— 见 §三.3 |

### 1.2 pantry 路径从哪来：`.Art.xml` 的 `<requiredGameArtIDs>`

`GeneratePantryPaths` 读 mod 的 `.Art.xml`，把 `<requiredGameArtIDs>` 里每个包
**连同其传递依赖**展开成 `<SDK Assets>\Civ6\pantry`、`<SDK Assets>\Civ6\DLC\<包>\pantry`
的路径列表，再拼进 cooker 命令行。

实测（本工程声明 `Civ6` + `Expansion2` 后，MSBuild 输出）：

```
Art Pantry Path -  "...\SDK Assets\Civ6\pantry"
                   "...\SDK Assets\Civ6\DLC\Expansion2\pantry"
                   "...\SDK Assets\Civ6\DLC\Shared\pantry"
                   "...\SDK Assets\Civ6\pantry"
```

注意：

- 声明 `Expansion2` **自动带出** `Shared`（传递闭包），无需手写；
- `Civ6\pantry` 出现两次 —— 正常，闭包展开的结果，不是 bug；
- 顺序有意义：后者只能覆盖前者没有的东西，**先声明的包优先**。

### 1.3 美术包依赖图（实测 GUID）

| 包 | GUID | 声明依赖 | pantry 位置 |
|---|---|---|---|
| `Civ6`（Base） | `cb2f71b7-843e-4af3-9ca7-992acda9c195` | —（根，`Civ6.Art.xml` **无** `requiredGameArtIDs` 段） | `Civ6\pantry` |
| `Shared` | `725760e3-7fc0-4be7-abf1-17bc756d5436` | `Civ6` | `Civ6\DLC\Shared\pantry` |
| `Expansion1` | `7446c8fe-29eb-44f8-801f-098f681cc5c5` | `Shared` | `Civ6\DLC\Expansion1\pantry` |
| `Expansion2` | `b1b63999-6b16-4dd2-a5b6-eb19794aa8ca` | `Shared` | `Civ6\DLC\Expansion2\pantry` |

查法：`<SDK Assets>\Civ6\DLC\<包>\pantry\<包>.Art.xml` 的 `<requiredGameArtIDs>` 段。

> **不是所有 DLC 都有 pantry。** 实测 `KublaiKhan_Vietnam` **没有** `pantry\<包>.Art.xml`
> —— 这类包的美术源素材在 SDK 里根本不存在，引用它的 artdef 条目**无法通过补声明修好**（§1.4 末尾）。

### 1.4 症状 → 诊断对照表

| 构建日志症状 | 缺什么 | 修法 |
|---|---|---|
| `Cannot cook the ArtDef (X_Shared.artdef) since it does not exist in the pantry!` | 提供该 `_Shared.artdef` 的包（`Shared` / `Civ6`） | 在 `.Art.xml` 补声明对应包 |
| `Unable to find the XLP (DIS_Water_ENT.xlp)` | 同上（XLP 源文件在该包 pantry 里） | 同上 |
| `Unable to find the ArtDef (Buildings_Shared.artdef)` | 同上 | 同上 |
| `Dependencies for file '*_Shared.artdef' ...` | 同上 | 同上 |
| `Unable to auto-generate ArtDef dependency information.` | 同上（依赖推导整个失败） | 同上 |
| `references an ArtDef entry (X) that does not exist in the ArtDef Collection (C) of ArtDef (F)` + `has had its value replaced with its default value` | **不是**依赖问题：被引用条目真的不存在（§三） | 见 §三：要么补条目，要么接受降级并确认产物未变 |

**诊断顺序**：先看 `Art Pantry Path -` 那一行的实际路径列表，再回去看 `.Art.xml`。
声明完仍报同一类错，说明目标包在 SDK 里**没有 pantry**（如 `KublaiKhan_Vietnam`），
此时唯一出路是手动补齐缺失条目，或绕开该引用。

### 1.5 自检（改 `.Art.xml` 后必做）

1. 打开 mod 的 `.Art.xml`，列出 `<requiredGameArtIDs>`；
2. 逐一确认 `<SDK Assets>\Civ6\DLC\<包>\pantry` 目录存在；
3. 用到的每个 DLC 素材（资源/区域/建筑条目名）所属的包，**是否都在列表里**；
4. 构建后 grep 日志 `Art Pantry Path` 那行，确认展开结果符合预期。

---

## 二、cook 产物 ≠ 源文件（归一化，务必分清）

### 2.1 为什么会不同

cook 会重写 XML。实测本工程 13 个 artdef 的归一化项：

| 归一化 | 现象 | 实测覆盖 |
|---|---|---|
| 行尾 `CRLF → LF` | 产物一律 LF | 源为 CRLF 的 9 / 13 个文件全部被转 |
| 空元素收紧 | `<x />` → `<x/>`（含带属性的自闭合） | 普遍 |
| 缩进 / 空行规整 | 逐行重排 | 普遍 |
| XML 注释**全部剥离** | 源里的 `<!-- ... -->` 消失 | 有注释的文件 |
| 补结构 | 源里没声明的 `<m_RootCollections>` 会被补全 | 部分文件 |
| **引用清空** | 解析不到的引用被写成 `_MissingArt` / `text=""` | 见 §三 |

### 2.2 ★ 分级判据：先分清「编码层」还是「语义层」

**不要**把「源 ↔ Mods 副本不相同」当成一个信号 —— 它对一半以上的文件是必然的，
没有信息量。正确做法是按归一化级别逐级放宽，看差异在哪一级消失：

| 级别 | 归一化 | 差异性质 | 处理 |
|---|---|---|---|
| **L0** | 无（原始字节） | 完全一致 | 无需处理 |
| **L1** | 统一行尾（CRLF/CR → LF） | **纯 CRLF/LF 差异** | 可忽略 |
| **L2** | L1 + 自闭合收紧 `\s+/>` → `/>` | `<x />` vs `<x/>` | 可忽略 |
| **L3** | L2 + 抹每行首尾空白 | 缩进差异 | 可忽略 |
| **L4** | L3 + 删空行 | 空行差异 | 可忽略 |
| **L5** | L4 + 剥 XML 注释 | 注释被 cook 剥离 | 可忽略 |
| **—** | L5 仍不同 | **语义层差异** | **必须人工判断**（见 2.4） |

> ⚠ 实现坑：自闭合收紧必须用 `\s+/>` → `/>` 全局替换。
> 用「标签名后紧跟空白」这类正则（如 `<([A-Za-z_][^\s>/]*)\s+/>`）**跨越不了属性里的
> 空格**，只能处理无属性空元素（`<Element />`），会把大量带属性的自闭合
> （`<m_ParamName text="X" />`）误判成「语义层差异」。这是本文件 v1 稿的真实错误。

**判据**：L1–L5 任一命中 → 差异纯属编码层，**可以忽略**；L5 仍不同 → 才需要看。

配套工具（只读，不改任何文件）：

```bash
cd <skill>/scripts
python artdef_sync_check.py <工程名>            # 单个工程
python artdef_sync_check.py --all              # 扫描工程根下全部工程
python artdef_sync_check.py <工程名> --detail 3 # 语义层差异时打印样本行
```

退出码：0 = 只有编码层差异；1 = 存在语义层差异或文件增删。可加 `--report` / `--json`。

### 2.3 彻底消除编码层差异的办法：把源统一成 cook 规范写法

**cook 的规范形式就是 LF**。若把源 artdef 存成 **LF + `<x/>` 紧凑 + 无注释**，
则 cook 不再改变它们，**源可以做到与产物逐字节相同**。

跨工程实证（12 个工程）：

| 工程 | 同名文件 | L0 字节相同 | 判定 |
|---|---|---|---|
| 工程 E / 工程 F / 工程 G / 工程 H / 工程 I | 1–2 | **全部** | 源即产物（源全是 LF） |
| **工程 C** | 12 | **11** | 唯一 CRLF 的 `FallbackLeaders.artdef` 恰好是唯一不同的那个 |
| 工程 B | 12 | 10 | 2 个语义层 |
| 工程 A | 12 | 11 | 1 个语义层 |
| 工程 D | 10 | 9 | 1 个语义层 |
| **示例工程** | 13 | 1 | 9 个编码层 + 4 个语义层 |

两条关键证据：

1. **那 5 个「源即产物」的工程，源 artdef 全部是 LF（CRLF=0）。**
2. **`工程 C` 是天然对照实验**：12 个文件里唯一的 CRLF 文件，恰好是唯一的
   L0 不同文件 —— CRLF 与「双端不一致」的因果明确。

**示例工程 之所以「几乎全部不同步」**，就是因为它的源 artdef 混了大量 CRLF
（9 个文件有 CRLF，`Resources.artdef` 多达 2161 处）。其中：

- 6 个 **纯 L1**（行尾）：`Civilizations` / `Cultures` / `FallbackLeaders` /
  `Improvements` / `Leaders`（+ 本就是 LF 的 `Units` 为 L0）
- 3 个 **L4**（行尾+自闭合+缩进+空行）：`Buildings` / `Clutter` / `Resources`
- 1 个 **L5**（再加注释剥离）：`StrategicView`
- 3 个语义层：`Districts` / `Landmarks` / `Overlay`

#### 2.3.1 ★ 怎么把「源保持 LF」**钉死**：`.gitattributes`

上面只是"结论"。真正让源不退回 CRLF 的是**版本控制侧强制** —— 本机 `core.autocrlf` 常见为 `true`，
它会**在 checkout 时把仓库里的 LF 写成工作区的 CRLF**，于是"源永远 CRLF、产物永远 LF"，
双端不一致被 git 反复制造出来。

在工程根加 `.gitattributes`（**按「换行分层铁律」分层，禁止一刀切 LF** —— 唯一真源是
`civ6-modding/gotchas.md` §68）：

```gitattributes
# 资产类 cook 输入：LF（AssetEditor / cooker 输出恒为 LF）
*.artdef  text eol=lf
*.xlp     text eol=lf
*.txt     text eol=lf

# 代码 / 配置类：CRLF（原版实测 .lua 40/40、.xml 40/40、.sql 17/17 均为 CRLF）
*.lua     text eol=crlf
*.sql     text eol=crlf
*.xml     text eol=crlf

# 美术二进制资产：禁止 git 做任何换行/编码转换
*.dds  -text -diff -merge binary
*.tex  -text -diff -merge binary
*.ast  -text -diff -merge binary
*.mtl  -text -diff -merge binary
*.geo  -text -diff -merge binary
*.blp  -text -diff -merge binary
*.blb  -text -diff -merge binary
```

- ⚠ **绝不要给 `*.xml` / `*.sql` / `*.lua` 写 `text eol=lf`**：那是 2026-09-16 之前的旧口径
  （本 skill 1.3 之前的版本教过这条），会让源与原版/引擎（CRLF）分层相反，并制造新的伪差异。
- `示例工程` 的实际做法即上表（`.artdef` = LF、`.lua`/`.sql`/`.xml` = CRLF；其 `.gitattributes`
  首行注释直接引用「换行分层铁律」，并注明跨工程 5 例 + 本工程 11/13 的实测支撑）。
- 加完规则后工作区若出现大批"看似被改动"的文件，**先跑
  `python civ6-modding/scripts/normalize_eol.py <工程目录>` 看报告**（默认只报告、`--fix` 才写盘），
  确认差异确实只是行尾、且方向符合上表，再决定是否写盘。
  **不要用 `git add --renormalize .` 一把梭** —— 在 `eol=lf` 规则下它会把 Lua/SQL/XML 全部烘成 LF
  写进索引，等于亲手把分层推倒。
- 对**不入 git 的工程**：等价手段是在编辑器/生成脚本里显式写目标行尾
  （`.artdef` → `newline='\n'`；`.lua`/`.sql`/`.xml` → `newline='\r\n'`）。

> 推论：凡是"改了编码/格式想让源与产物一致"的任务，**先问"是谁在把 CRLF 塞回工作区"**，
> 再决定是统一源写法还是加 `.gitattributes` —— 只改一次文件不改供给链，下次 checkout 就打回原形。

### 2.4 语义层差异：两类，只有一类是真缺陷

| 子类 | 表现 | 性质 |
|---|---|---|
| **cook 补结构** | 产物**多出** `<m_RootCollections>` / `<Element>` / `<m_CollectionName>` 等声明 | 无害，**但永久**（源缺声明，产物补全），无法靠统一编码消除 |
| **引用被清空** | 源里的值在产物中变成 **`_MissingArt`** 或 **`text=""`** | ★ **真实缺陷信号** |

「引用被清空」的两个具体默认值（实测）：

- artdef 条目引用不到 → **`_MissingArt`**
  （示例工程 `Districts.artdef`：`Preserve` / `Preserve_Pillaged` /
  `Preserve_UnderConstruction` → 三处 `_MissingArt`）
- 条目名 / XLP 引用不到 → **`text=""`**
  （示例工程 `Landmarks.artdef` 的 `BUILDING_GROVE` / `BUILDING_SANCTUARY`；
  工程 B `StrategicView.artdef` 的 `StrategicView_DISTRICT_HIGHTECH_INDUSTRIAL_QYQXP`）

**因此**：`districts.artdef` / `Landmarks.artdef` 这类文件**永远不可能靠统一编码
变成与产物一致** —— 只有修掉那些解析不到的引用才会一致（示例工程 的那 3+4 处
根因是 `KublaiKhan_Vietnam` 无 pantry，见 §1.3）。

> 反过来用：**「双端不一致」里的语义层部分是一个免费的缺陷探测器。**
> 本 skill 用这套判据反查出两个兄弟工程的真实缺陷（`工程 A` /
> `工程 D` 的 `.Art.xml` 只声明了 `Civ6`，导致 `StrategicView_Shared.artdef`
> 的引用在产物中被清空）—— 详见 `CHANGELOG.md` 1.3 的证据来源。

### 2.5 与「双目录一致性」怎么共存

- **artdef 源 ↔ Mods 副本不一致，不构成**「双目录不一致」告警 —— 但**要跑
  `artdef_sync_check.py` 分级**，只看 L5 仍不同的那些。
- **同步 Mods 测试副本时必须拷 cook 产物**，不能拷裸源。若要拷裸源，前提是
  2.3 的规范写法已统一（此时两者本就相同）。
- 判断「有人手改过 Mods 副本」的正确信号是 **L0–L5 全部不同 + 产物侧出现源里没有的
  非结构性内容**，或**文件增删**（`仅源有` / `仅 Mods 有`，脚本会单独报）。

---

## 三、警告语义：解析失败 = 静默降级

### 3.1 逐字措辞（ArtDef 模式，实测）

```
 >> Districts.artdef >> District >> DISTRICT_X >> StrategicView >> Y >>
    XrefName references an ArtDef entry (Preserve) that does not exist in the
    ArtDef Collection (Districts) of ArtDef (StrategicView.artdef).
 >> Districts.artdef >> District >> DISTRICT_X >> StrategicView >> Y >>
    XrefName has had its value replaced with its default value.
```

```
 >> Landmarks.artdef >> Districts >> DISTRICT_X >> BuildingVariants >> Z >>
    Tag_HeroBuilding references an ArtDef entry (BUILDING_GROVE) that does not
    exist in the ArtDef Collection (Building) of ArtDef (Buildings.artdef).
 >> Landmarks.artdef >> Districts >> DISTRICT_X >> BuildingVariants >> Z >>
    Tag_HeroBuilding has had its value replaced with its default value.
```

**关键短语是第二行**：`has had its value replaced with its default value`。
这行的意思不是「跳过」也不是「报错退出」，而是**引擎静默把该引用清成默认值**——
即那个引用点实际上没有美术了。第一行只说明「哪个引用、找的是谁」。

读法：**一行 `references … that does not exist` 对应一行 `replaced with its default
value`，成对出现**。数对子即可数出「有几个引用点被降级了」。

本工程集成 Vietnam DLC 素材后剩余 7 对（`Landmarks.artdef` 4 对：
`BUILDING_GROVE` ×2 + `BUILDING_SANCTUARY`；`Districts.artdef` 3 对：
`Preserve` / `Preserve_Pillaged` / `Preserve_UnderConstruction`），全部指向
`DISTRICT_PROTOVENO_RGN`，根因是 §1.3 末尾的「该 DLC 无 pantry」。

### 3.2 判据：改动有没有运行时影响

**不要靠日志判断，靠产物**：

> 重新 cook → 比对产物的 `.blp` / `.artdef` 与改动前是否**逐字节相同**。
> 相同 = 该改动对运行时**零影响**（哪怕日志变吵或变安静）。

（注意这里比的是「**改动前的产物** ↔ 改动后的产物」，不是「源 ↔ 产物」；
后者请用 §2.2 的分级判据。）

本工程实证：XLP 登记改动后 `landmarks/tilebases.blp` 稳定在 34,816 B、
SHA256 `CC549F071B50ADDF…`，与改动前完全一致 → 零运行时影响，尽管日志新增了
4 条 `Removing package asset entry`（§四）。

### 3.3 两个会误导人的日志噪声

1. **`EXEC(0,0): error asset: (Error/TileBase_Error_Asset)`**
   —— 这是 §1.1 的 `ConsoleToMsBuild="true"` 把 cooker 的
   `Loading error asset: (Error/TileBase_Error_Asset)` 行重新分级成 error。
   加上 `IgnoreExitCode="true"`，**构建依旧报 `1 succeeded, 0 failed`**。不是真错。
2. **`Argument '--shaders' has been deprecated and is no longer used.`**
   —— `Civ6.targets` 仍在传 `--shaders`；无害，每次 cook 都会打印。
   同理 `Could not load digest key: ''. Using mod key to sign BLP.` 也是正常的
   本地未配置签名密钥提示。

---

## 四、XLP 条目的「可解析性」与打包后果（反直觉，必读）

### 4.1 三层解析

```
artdef 里 m_XLPPath + m_EntryName
    │  必须在某个 *.xlp 的 m_EntryID 集合里查到
    ▼
xlp 条目 m_EntryID → m_ObjectName
    │  m_ObjectName 被当作 <pantry>/Assets/<m_ObjectName>.ast 去找
    ▼
该 .ast（及它引用的几何/材质/贴图）存在 → 真的打进 .blp
```

### 4.2 解析不了会怎样（实测）

`XLPs/tilebases.xlp` 里登记了 4 条 `DIS_Preserve_*`，而 pantry 里没有对应
`.ast`（Vietnam 包无 pantry）。XLP cook 输出：

```
Starting 'landmarks/tilebases'
Loading error asset: (Error/TileBase_Error_Asset)
Removing package asset entry: (DIS_Preserve_Base_01) due to errors in (DIS_Preserve_Base_01)
... ×4 ...
****** Log from Asset: 'DIS_Preserve_Base_01' (ERRORS!!) ********
I/O error reading XML: <mod>/Assets/DIS_Preserve_Base_01.ast
BLP: '...\landmarks\tilebases.blp' HAS MISSING ENTRIES!
```

要点：

- 根因是 **`Assets/<m_ObjectName>.ast` 的 I/O 错误**（找不到文件）；
- **整条条目被从 .blp 里移除**（`Removing package asset entry`）；
- 产物 BLP 与「不登记这些条目」时**逐字节相同**（34,816 B / `CC549F071B50ADDF…`）；
- **cooker 退出码 = 2**，但 `IgnoreExitCode="true"` 让构建仍然 succeeded。

**结论**：登记一条 `m_ObjectName` 解析不了的条目，运行时**零影响**，代价只是日志变吵。
这可以作为「让某个 artdef 引用有个名字可指，但不改变任何几何体」的手段。

### 4.3 反例（千万不要为了消音这么做）

把 `m_ObjectName` 填成一个**真实存在**的资产名（例如拿 `WORKAROUND_Empty_TileBase`
之类凑数）→ 条目会**成功打包**，BLP 体积变化，并且因为 mod 最后挂载，
**同名条目会覆盖 DLC 的几何体** → 实机表现被改坏。

> 口诀：**消音的唯一安全方式是让它解析失败**，而不是让它解析成功。

### 4.4 命名约定

`m_EntryID` 与 `m_ObjectName` 通常同名。实测 SDK pantry 全部 262 个 xlp、16,358 条条目：

| 关系 | 占比 |
|---|---|
| `EntryID == ObjectName` | **93.4%**（15,272 条） |
| `EntryID != ObjectName` | 6.6%（1,086 条） |
| `ObjectName` 为空 | 0 条 |

新写条目按 `EntryID == ObjectName` 走最省事；不一致的属于少数特例，遇到以实际
资产名（`Assets/*.ast`）为准。

---

## 五、本地复现 cook（排错用）

ModBuddy 的构建日志不好拿时，可以手工重放同一条 cook 命令。**注意产物落点**：

```powershell
$proj = "<mod 工程目录>"                       # 自己就是第一个 --pantry
$sdk  = "F:\...\Sid Meier's Civilization VI SDK"
$assets = "F:\...\Sid Meier's Civilization VI SDK Assets"
$cookerDir = "$sdk\AssetModTools\Cooker"
$out = "<mod>\workspace\tmp\verify"            # 必须是临时目录

# ArtDef 模式：--banquet_hall 指向临时目录
& "$cookerDir\Civ6AssetCooker_FinalRelease.exe" --absolute_paths --no_mt `
  --mode ArtDef --platform Windows `
  --pantry $proj "$assets\Civ6\pantry" "$assets\Civ6\DLC\Expansion2\pantry" "$assets\Civ6\DLC\Shared\pantry" `
  --banquet_hall "$out\ArtDefs" --config "$cookerDir\Civ6.cfg" (Get-ChildItem "<mod>\ArtDefs" -Filter *.artdef).FullName

# XLP 模式：--stewpot 指向临时目录
& "$cookerDir\Civ6AssetCooker_FinalRelease.exe" --absolute_paths --no_mt `
  --mode XLP --platform Windows `
  --pantry $proj "$assets\Civ6\pantry" "$assets\Civ6\DLC\Expansion2\pantry" "$assets\Civ6\DLC\Shared\pantry" `
  --stewpot "$out\Platforms\Windows\BLPs" --config "$cookerDir\Civ6.cfg" "<mod>\XLPs\某文件.xlp"
```

注意事项：

1. **`--banquet_hall` / `--stewpot` 必须指临时目录**。cook 会顺带写出
   `<项目名>.dep`，指到实机 Mods 目录会用「单个 artdef 的 cook」覆盖掉整套依赖清单。
2. cooker 会在**当前工作目录**写 `cooker.log`（完整日志，比控制台全）。
   先切到临时目录再执行，别把工程的 `cooker.log` 覆盖掉。
3. **不要用管道或重定向捕获 cooker 输出**（`| Out-Null`、`> file.txt`
   `2>$null` 等）。原生 exe 在这种捕获下会以「拒绝访问」类错误启动失败，
   看起来像 cooker 坏了，其实是宿主环境的限制。让它直接继承控制台输出即可，
   需要完整记录就读它自己写的 `cooker.log`。

---

## 六、检查清单（改 artdef / xlp / .Art.xml 后）

- [ ] `.Art.xml` 的 `<requiredGameArtIDs>` 覆盖了所有用到的 DLC 素材所属包
- [ ] 构建日志 `Art Pantry Path` 展开符合预期（没有 `does not exist in the pantry!`）
- [ ] 日志里 `references … that does not exist` 的**对子数**已知，且每对都能解释
      （是「本来就没有美术」还是「忘了补条目」）
- [ ] 跑 `python artdef_sync_check.py <工程名>`：
      - 全部为 **L0–L5** → 只有编码层差异，**可忽略**（要想彻底消除见 §2.3）
      - 出现 **语义层差异** → 逐个看：`cook 补结构` = 无害；`引用被清空`
        （`_MissingArt` / `text=""`）= **真实缺陷，去查引用**
      - 报告里出现 `仅源有` / `仅 Mods 有` → 文件级增删，单独处理
- [ ] 重新 cook 一次，产物与 Mods 副本逐字节比对 → 确认本次改动的真实影响面
- [ ] 若改了 XLP：确认新增条目的 `m_ObjectName` 指向的 `.ast` 是否真存在；
      不存在则接受日志噪声（零影响），**绝不能**填一个真实资产名来消音
- [ ] 同步 Mods 测试副本时拷的是 **cook 产物**，不是裸源

---

## 七、证据来源（2026-09 实测）

| 结论 | 证据 |
|---|---|
| §1.1 任务与命令行 | `<SDK>\ModBuddy\Civ6.targets` 的 `GeneratePantryPaths` / `ArtDefCookerCmd` / `XLPCookerCmdWindows` / `<Exec ConsoleToMsBuild IgnoreExitCode>` |
| §1.2 pantry 展开 | MSBuild 输出 `Art Pantry Path -` 行（4 条路径，`Civ6\pantry` 重复） |
| §1.3 依赖图 | SDK pantry 内 `Civ6.Art.xml`（无 requiredGameArtIDs）、`Shared.Art.xml`(→Civ6)、`Expansion1.Art.xml`(→Shared)、`Expansion2.Art.xml`(→Shared)；`KublaiKhan_Vietnam` 无 pantry Art.xml |
| §2.1 归一化 | 本工程 13 个 artdef 的源 / 新 cook 产物 / Mods 副本三方比对（**13/13** 新 cook 产物与实机副本逐字节相同） |
| §2.3 编码层结论 | 12 个工程源 vs Mods 副本分级比对：5 个工程源全是 LF 且 L0 全同；`工程 C` 唯一 CRLF 文件恰为唯一 L0 不同文件；示例工程 源 9 个文件含 CRLF（`Resources.artdef` 2161 处） |
| §2.4 语义层两类 | 示例工程 `Districts.artdef` 三处 → `_MissingArt`；`Landmarks.artdef` 五处源值变空；`Overlay.artdef` 产物多 3 行 `<m_CollectionName>`；`StrategicView.artdef` 仅注释被剥 |
| §2.4 反查兄弟工程 | `StrategicView_Shared.artdef` 由 `Civ6\DLC\Expansion2\pantry` 提供（其中 L27 定义 `LoyaltyPressure`、L35 定义 `LoyaltyWarning`）；`工程 A` / `工程 D` 的 `.Art.xml` **只声明 `Civ6`**，产物中该引用被清空；对照 `工程 B` 声明了 `Expansion2`，产物保留 → 因果吻合 |
| §3.1 逐字措辞 | 手工重放 ArtDef cook 的完整输出（7 对降级警告） |
| §4.2 XLP 行为 | 手工重放 XLP cook：4 × `Removing package asset entry` + `HAS MISSING ENTRIES!` + `exit 2`；产物 `landmarks/tilebases.blp` = 34,816 B / SHA256 `CC549F071B50ADDF…` 与改动前及实机副本逐字节相同 |
| §4.4 命名约定 | SDK pantry 全部 262 个 xlp 统计：16,358 条条目，`EntryID == ObjectName` 15,272 条 |
