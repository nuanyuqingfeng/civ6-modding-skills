← 返回 `SKILL.md` 路由

> **来源**：2026-09-17 在 `示例工程` 上首次落地并实测通过的 Suk 选人界面适配流程，
> 经泛化后固化为本 skill 的**第 5 类素材**（前四类见 `SKILL.md` §一）。
> 实测工程记录：`示例工程/workspace/specs/2026-09-17-suk-portrait-adaptation.md`。

# UI 领袖立绘与选人界面背景（Suk 适配）

## 一、这一类解决什么

**Sukritact's Civ Selection Screen**（下称 Suk）是一个流行的第三方**选人界面替换 mod**，
它用自绘的 `UI/AdvancedSetup.{lua,xml}` 整屏替换原版领袖选择界面，并改为**纯 2D 选人**。

它选人时执行（实测 `UI/AdvancedSetup.lua:1935`）：

```sql
SELECT …, Portrait, PortraitBackground
FROM Players WHERE Domain = ? AND LeaderType = ?
```

然后：

| 列 | 控件 | 说明 |
|---|---|---|
| `Portrait` | `Controls.LeaderImage:SetTexture()` | **2D 立绘纸片**（`AdvancedSetup.lua:2572-2588`） |
| `PortraitBackground` | `Controls.LeaderBG:SetTexture()` | 背景（`AdvancedSetup.lua:2600`） |

**关键**：画面比例由 `DummyImage:GetSizeX()/GetSizeY()` **运行时实测**，
所以**贴图尺寸可自由，不会被拉伸变形**——这跟原版 3D 立绘路径完全不同。

**本类不做**：
- 不做 3D 领袖模型/纸片人注册链（→ 本 skill `reference/leader-2d.md`）
- 不做总督立绘（→ `reference/governor-art.md`）
- 不负责 Suk mod 本身的分发（那是第三方 mod，用户自行订阅）

## 二、触发判定（什么时候该用这一类）

用户提到下列任一关键词时，**先判定是否与本流程关联**，不要直接开做：

| 关键词 | 关联性 |
|---|---|
| `suk selection` / `Sukritact` / `Civ Selection Screen` / `选人界面` / `领袖选择界面` | **强关联** → 走本流程 |
| `PortraitBackground` / `Players` 表的 `Portrait` 列 | **强关联** → 走本流程 |
| `UILeaders.xlp` / `FALLBACK_NEUTRAL_*_Suk` | **强关联**（这就是本流程的产物命名） |
| `领袖立绘` / `领袖选择背景`（未指明 Suk） | **弱关联** → 先问清是**原版界面**还是 **Suk 界面**：<br>原版 3D 走 `leader-2d.md`；Suk 2D 走本流程 |
| `加载界面`（`IMG_LOADING_*`） | **不关联**（那是 `LoadingInfo` 表，另一条链） |

判定为关联后，**必须先问素材来源**（第三节），再动手。

## 三、铁律：素材来源必须先问

沿用本 skill 的通用铁律（`SKILL.md` §三），本类的**询问模板**：

> 检测到本次要适配 **Suk 选人界面**。需要为每位领袖准备两张 2D 贴图：
> **立绘**（`Portrait`）与**背景**（`PortraitBackground`）。
>
> **来源请二选一：**
>
> - **A. 复用工程已有素材（推荐，零额外美术）**：脚本自动取
>   - 立绘 ← `Textures/FALLBACK_NEUTRAL_{KEY}.dds`（工程已有的 1316² 立绘）
>   - 背景 ← `Textures/IMG_LEADER_{KEY}_DIPLOMACY_BACKGROUND.dds`（外交界面背景 1920×1080）
>
> - **B. 使用你提供的新素材**：请给出**立绘**与**背景**的 PNG 目录/路径
>   （建议立绘透明背景、尺寸近似 1:1；背景建议 16:9，如 1920×1080）。
>   我会按下面的规格裁切缩放。
>
> **未提供素材、也未选 A 时，我不会擅自处理任何图片。**

选定后按第四节规格处理。**默认推荐 A**——实测 A 出来的成品观感良好，
且背景是**纯裁切、零重绘**（见下）。

## 四、素材规格（实测自兄弟工程既有产物，可确定性复现）

### 4.1 立绘 `Portrait`

**工艺**：
```
源立绘 → 等比缩到高 1024（LANCZOS）→ 按 alpha 内容定宽（内容 + 左右各 8px）
       → 内容水平居中粘贴（不裁切，垂直不动）
```

**为什么要这样定宽**：与原版 `LEADER_*_NEUTRAL` 约定一致——实测原版 44 张：
**高固定 1024/1080、下边距恒为 0（人物触底）、上边距 5~184、宽度随内容 389~803**。
即原版就是「按内容裁宽的紧致画布」，没有固定尺寸。

> ⚠ **不要照搬兄弟工程的固定 781 宽窗口**。兄弟工程用固定宽度会把内容裁掉
> （实测某工程 CANTARELLA 会裁掉 21.4%、FLEURDELYS 23.7%、CIACCONA 11.1%）。
> 本流程改为**按内容自适应**，实测六位领袖**全部零裁切**。

**实测产出示例**（内容宽 → 画布）：

| 领袖 | 内容宽@1024 | 画布 | 比例 | 裁切 |
|---|---|---|---|---|
| CARTETHYIA | 788 | 804×1024 | 0.785 | 0 |
| CANTARELLA | 994 | 1010×1024 | 0.986 | 0 |
| CIACCONA | 879 | 895×1024 | 0.874 | 0 |
| FLEURDELYS | 1024 | 1024×1024 | 1.000 | 0（内容顶满，裁切即切人） |
| PHOEBE | 715 | 731×1024 | 0.714 | 0 |
| ROCCIA | 711 | 727×1024 | 0.710 | 0 |

### 4.2 背景 `PortraitBackground`

**工艺（纯裁切、零缩放、零重绘）**：
```
源外交背景 1920×1080 → 中心横裁 x = 240..1680，全高 → 1440×1080（4:3）
```

这条**已由两个兄弟工程逐像素复现**（工程 A 与 工程 D，
`meanAbsErr = 0.00`）——即背景素材不需要新画，外交背景裁一刀就是 Suk 背景。

### 4.3 `.tex` / DDS 规格

| 项 | 值 |
|---|---|
| DDS | 未压缩 RGBA8、**单 mip**、128 字节头带 `FTXT` 签名 |
| `m_ClassName` | **`UserInterface`**（⚠ 见 4.4） |
| `m_Tags` | `UserInterface`（单条） |
| `bUseMips` / `m_NumMipMaps` | `false` / `0` |
| `m_Width` / `m_Height` | 必须与 DDS 实际宽高**逐位一致**（不一致 → AssetEditor 裁/拉伸） |
| `m_SourceFilePath` | `D:\desktop\<stem>.png`（ASCII 虚拟路径，pantry 铁律） |
| 行尾 | `.tex` / `.xlp` = **LF**；`.sql` = **CRLF** |

### 4.4 ⚠ 类别陷阱（本类最容易踩的坑）

素材名是 `FALLBACK_NEUTRAL_{KEY}_Suk`，**与 3D 回退贴图同前缀，但类别完全不同**：

| 贴图 | 用途 | `m_ClassName` | 注册在 |
|---|---|---|---|
| `FALLBACK_NEUTRAL_CARTETHYIA_QYQXP` | 3D 领袖回退 | `Leader_Fallback` | `LeaderFallbacks.xlp` |
| `FALLBACK_NEUTRAL_CARTETHYIA_QYQXP_Suk` | **Suk 2D 立绘** | **`UserInterface`** | `UILeaders.xlp`（`UITexture`） |

`civ6-modding/art/gen_tex.py` 的 `is_fallback()` 原本是**纯前缀判断**，
会把 `_Suk` 误判成 `Leader_Fallback` → 产生「类别与所绑定 XLP 参数不匹配」，
cooker 报 `has class 'X', but is bound to parameter 'Y' which does not accept this class`，
**且 XLP cook 仍显示 success**，条目被静默替换成 error asset（界面立绘空白）。

> 该判断已在 2026-09-17 修正（`gen_tex.py` 的 `_UI_PORTRAIT_SUFFIXES` 显式排除 `_Suk`）。
> **新增同类 UI 立绘后缀时，往 `_UI_PORTRAIT_SUFFIXES` 里加**，不要再写前缀特例。
> 交付前务必自查：`grep m_ClassName` 确认 `_Suk` 贴图是 `UserInterface`。

### 4.5 连线（接线）

| # | 位置 | 要做什么 |
|---|---|---|
| 1 | `Textures/` | 新增 `FALLBACK_NEUTRAL_{KEY}_Suk.{dds,tex}` + `PORTRAIT_{KEY}_BACKGROUND_Suk.{dds,tex}` |
| 2 | `Mod_Adaptation/Suk/Suk_Portrait_RGN.sql` | `UPDATE Players SET Portrait=…, PortraitBackground=… WHERE LeaderType=…` |
| 3 | `XLPs/*.xlp`（`UITexture` 类） | 每个贴图一条 `<m_EntryID>` + `<m_ObjectName>` |
| 4 | `*.civ6proj` | Folder + Content + `FrontEndAction`（带 `Criteria`，见下） |

`FrontEndAction` 的写法（与兄弟工程同款语义）：

```xml
<UpdateDatabase id="RGN_Suk_Portrait">
  <Properties><LoadOrder>999999</LoadOrder></Properties>
  <Criteria>Suk_Portrait</Criteria>
  <File>Mod_Adaptation/Suk/Suk_Portrait_RGN.sql</File>
</UpdateDatabase>
```

配合判据（GUID = Suk mod 本体）：

```xml
<Criteria id="Suk_Portrait"><ModInUse>60092bdd-ce39-4319-aef6-baea505c7c45</ModInUse></Criteria>
```

**必须挂 `Criteria`**：这样未启用 Suk 时该 SQL 根本不加载，
`Players` 保持原值，**原版界面行为完全不变**。

> **`Textures/` 不需要写进 civ6proj 的 Content**：本工程及兄弟工程均依赖引擎自动打包
> （`Materials/`/`Assets/`/`Textures/` 构建时自动扫描进 BLP，见 `SKILL.md` §6.2 第 1 条）。
> 但 **`.xlp` 必须注册**（`SKILL.md` §6.2 第 2 条）。

### 4.6 领袖名文本（可选，视项目而定）

兄弟工程额外引入了 `LOC_..._NAME_SUK` 新文案。**本项目不需要**——
它已用反向条件实现了同一目的：Suk 开 → 纯名；Suk 关 → 带 `[COLOR]` 的名。

> 移植到新工程时**先查该项目是否已有同类开关**，避免重复引入两套名字机制互相冲突。

## 五、标准工作流

```bash
# ① 预演（不写盘）—— 先看会产出什么、尺寸多少
python <skill>/scripts/gen_suk_portrait.py --project "<工程根>" --check

# ② 落盘
python <skill>/scripts/gen_suk_portrait.py --project "<工程根>" --write

# ③ 只处理指定领袖
python <skill>/scripts/gen_suk_portrait.py --project "<工程根>" \
    --leaders LEADER_X_QYQXP,LEADER_Y_QYQXP --write

# ④ 用用户素材（目录内 PNG 文件名含领袖名片段即可）
python <skill>/scripts/gen_suk_portrait.py --project "<工程根>" \
    --portrait-dir D:/art/lith --bg-dir D:/art/bg --write
```

脚本行为：
- 自动从 `Data/*.sql` 的 `('LEADER_X', 'KIND_LEADER')` 探测领袖
  （**不认** `'LEADER_DEFAULT'` 这类「继承模板」引用值；被注释的可选领袖也会被命中，这是有意的）；
- 缺源素材的领袖**跳过并告警**，不中断其余领袖；
- **幂等**：SQL / XLP / civ6proj 三处重复运行不会产生重复条目。

## 六、验证顺序（缺一不可）

```
1. python <skill>/scripts/gen_suk_portrait.py --project <工程根> --check   # 尺寸先过目
2. python civ6-modding/scripts/check_pantry.py                             # 0 error
3. python civ6-modding/scripts/clear_ae_cache.py                           # 清 AE 缓存
4. 启动 AssetEditor，确认日志无 CRASH
5. 自查类别：grep m_ClassName Textures/*_Suk.tex  → 必须全是 UserInterface
6. 自查接线：*.civ6proj 的 FrontEndAction 带 Criteria；XLP 条目数 == 贴图数
7. python <skill>/scripts/verify_suk_portrait.py --project <工程根>         # 专用校验器
8. ModBuddy Rebuild All → 同步 Mods → 进游戏**双态验证**：
     - Suk 开：2D 立绘 + 宽背景
     - Suk 关：回到原版行为（3D 模型 / 原背景）
```

### 6.1 专用校验器 `verify_suk_portrait.py`

检查（只读，不写盘）：

1. 每张 `_Suk` 贴图 `.dds` ↔ `.tex` 成对，且 `.tex` 声明的 `m_Width/m_Height` == DDS 实际；
2. `m_ClassName` == `UserInterface`、`m_Tags` 只有 `UserInterface`（**4.4 的类别陷阱**）；
3. 每个 `_Suk` 贴图都被某个 `UITexture` XLP 登记（否则不会进 BLP = 界面空白）；
4. SQL 里 `Portrait`/`PortraitBackground` 指向的贴图**在磁盘存在**（无悬空）；
5. `.tex`/`.xlp` 为 LF、SQL 为 CRLF。

## 七、实测记录（为什么这些数字可信）

| 结论 | 证据 |
|---|---|
| 背景 = 外交背景中心裁 4:3 | 兄弟工程两例逐像素 `meanAbsErr = 0.00` |
| 立绘 = 缩到高 1024 + 内容定宽 | 兄弟工程产物复现 `meanAbsErr ≈ 2.7`（固定 781 宽） |
| 原版 `LEADER_*_NEUTRAL` 是「内容定宽 + 触底」 | SDK pantry 44 张实测：高恒 1024/1080、下边距恒 0、宽 389~803 |
| 比例可自由、不会拉伸 | Suk `AdvancedSetup.lua:2572-2588` 运行时实测 `DummyImage` 比例 |
| `_Suk` 必须是 `UserInterface` | 兄弟工程既有 `.tex` 实测 `m_ClassName=UserInterface`，注册在 `UITexture` XLP |
| 本流程产物可逐字节复现 | `gen_suk_portrait.py` 对 `示例工程` 既有 12 组交付物 **逐字节一致** |
