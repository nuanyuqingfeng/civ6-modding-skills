# 类别⑧：区域图标（District Icon）

## 〇、入口判定（路由必读）

**先快速检查素材**：已含**六边形边框**等官方区域图标显著特征的图（即官方样式的成品图标）
**不进入本流程**——它已经是"官方模板合成之后"的产物，再走一遍会把六边形当图案
套进六边形底图（套娃），且成品图案已被渐变染色，无可提取的图案形状。
此类"已有成品图标导入"需求走 `civ6-modding/art-pipeline.md` 的 png→dds 直转。

本流程只接受**纯图案素材**（无六边形等官方图标特征的白色/浅色图案）——
六边形底图、边框、三效果全部由官方模板 PSD 提供。

**引擎顺序**：判定通过后**默认先跑 PS 自动化引擎**
（`ps_place_district.py`：用内置模板打开本机 Photoshop 走智能对象置入，效果最好）；
Photoshop 不可用（exit 4）时**询问用户**二选一——
(a) 改走模拟引擎（`build_district_icon.py`，纯 Python 模拟智能对象置入，效果较差）；
(b) 下载安装 Photoshop 后重跑 PS 引擎。不静默降级。

> **产出**：256×256 区域图标母版 PNG（六边形底图 + 白色图案）。
> **输入**：白色/浅色图案素材（PNG）。模板 PSD **已随 skill 内置**
> `templates/district_icon/District_Icon_Photoshop_CC.psd`（区域底图与官方效果参数的唯一来源），
> 无需用户提供；`--psd` 可换自定义模板。
> **边界**：本类只做 PNG 母版合成；PNG→DDS/`.tex` 与 `IconTextureAtlases` 注册走
> `civ6-modding/art-pipeline.md` 通用图标管线（审核通过后进行）。

## 一、模板 PSD 结构

- 画布 **256×256**；顶层 `Choose District` 组下每个区域一个组（12 组：
  Theater / Spaceport / Neighborhood / Industrial Zone / Holy Site / Harbor /
  Entertainment Complex & Waterpark (RaF) / Encampment & Aerodrome (RaF) /
  Commercial Hub / Campus / Aqueduct / Aerodrome (Vanilla)）。
- 每个区域组三层结构：
  | 组 | 内容 | 说明 |
  |---|---|---|
  | `Icon Background` | `Background` + `Border`（个别区域叫 `Vector Smart Object`） | 六边形底图与边框，逐区域导出 |
  | `Alpha` | `District Alpha` 智能对象 | **图案形状层**，全区域共享同一个内嵌对象（单图标工作稿） |
  | `Reference` | 官方成品 76px 小图（隐藏） | 视觉对照用 |
- **图案落位框**：`(48, 48)–(209, 207)`，161×159。素材等比缩放（contain）后居中贴入。
- ⚠ **psd_tools 的 `layer.bbox` 是 `(left, top, right, bottom)`**（与常见
  `(top, left, …)` 顺序相反，实测验证：Background `bbox=(26,11,229,245)` ↔ PIL 尺寸 203×234）。
  贴图坐标写 `(bbox[0], bbox[1])`。

## 二、素材处理（合成的前置条件，两个引擎共用）

素材前置分路（`build_district_icon.prepare_pattern`，PS 引擎与模拟引擎同源）：
**删背景（原图尺度）→ 可选低画质增强 → 主体 bbox 裁剪 → 单步高质量重采样（含质心可对齐约束）
→ alpha 质心对齐落位框中心 → 原样合成**。

> **无破坏性处理铁律**：素材细节从删背景之后**原样**进入成品——不做锐化、不做中值滤波、
> 不做噪音清理、不做任何形态学加工（这类加工会把缩放产生的中间调细节当噪音清除，
> 4K 素材的效果反而不如小尺寸图标）。

1. **删背景为 alpha**，按素材类型三选一（脚本自动判定）：
   - **自带透明通道**的素材跳过删背景。
   - **纯黑白素材**（RGB 三通道几乎相等的灰度图，黑背景白图案——首选路径）：
     **亮度直接映射 alpha**——背景亮度（边缘中位数）→ 全透明，前景亮度（99 分位）→
     全不透明，中间灰阶线性过渡。素材明暗细节原样保留，不做主体域、不做闭运算填洞。
   - **通用路径**（彩色素材 / 非近黑背景）：背景色距离场软阈值（`BG_NEAR=6`/`BG_FAR=42`）
     + 低阈值主体域（`DOMAIN_NEAR=10` → 开运算去噪 → 闭运算补缺口 → 孔洞填充）拉满内部。
2. **主体 bbox 裁剪（trim）**：按 alpha > 32 的内容框裁掉透明/背景边距。
3. **单步高质量重采样（硬性）**：缩小用 OpenCV `INTER_AREA`（大比例缩小的面积平均
   最优），放大用 `INTER_CUBIC`；**禁止递归减半/多步缩放**——每步低通累积会让
   2K/4K 素材明显变模糊。Pillow 的 Lanczos 缩小时本身自动
   扩展滤波核防混叠，单步即安全，可作无 OpenCV 环境的等价实现。
4. **缩放系数含质心可对齐约束**：contain 基础上取
   `scale = min(contain, 框宽/(2·max(fcx,w−fcx)), 框高/(2·max(fcy,h−fcy)))`
   ——质心不在 bbox 中心（构图不对称）时自动缩小留出平移余地。
5. **alpha 质心对齐（硬性）**：贴图位置 = 落位框中心 − 质心，越界钳制。
   **视觉重心以 alpha 加权质心为准**——素材构图质量分布不均时（大件+装饰类图标），
   几何中心对齐（bbox/画布居中）会造成视觉重心偏移（PS 画布居中流程实测偏 2~3px 且
   硬 alpha 素材更显眼）；质心对齐后残差 <1px。
6. **素材无法认定**：落位框内 alpha > 128 占比 < 10% → 退出码 3 停下询问。
7. **低画质增强（`--enhance`，须用户授权）**：在删背景之后、trim/缩放之前执行——
   小图（长边 < 280）先 Lanczos 放大到 280；alpha 非零像素按 1%~99% 分位线性拉伸
   （收紧软边）；RGB 与 alpha 分通道 UnsharpMask 轻度锐化（半径 = min(边长)/512，下限 2）。
   适用于低分辨率小图与边缘发软的大图。

## 三、合成规格

渲染顺序：底图 → 边框 → 外发光 → 图案渐变 → 内描边。图案素材提供 alpha 形状
（模拟智能对象置入：原样细节），颜色全部由模板官方三效果接管。

| 步骤 | 来源 | 处理 |
|---|---|---|
| 底图 | `Background`（白色内容） | 按**自带** `GradientOverlay` 染区域主题色渐变（角度 −90°，位置0 色在**顶部**）+ `InnerGlow`（黑，13%，blur 11） |
| 边框 | `Border` / `Vector Smart Object` | 自带颜色（区域主题色边框环），原样贴上 |
| 外发光 | `Alpha` 组 `OuterGlow` | 紫黑 (43,29,81)，multiply，45%，size 3（全区域相同），画在图案之下 |
| 图案 | 处理后素材的 alpha | `GradientOverlay`（每区域主题色双色渐变，−90°，100% 填充染色） |
| 描边 | `Alpha` 组 `Stroke` | 内描边 size 3，渐变填充（每区域色标），方向同图案渐变 |

> 渐变方向：位置0 深色在顶部。`Reference` 小图同时可作人眼对照。
>
> ⚠ **形状掩码阈值 = alpha ≥ 128（PS 效果渲染语义）**：GradientOverlay 的填充范围、
> Stroke 的描边环带、OuterGlow 的外扩环带都以 50% alpha 为形状边界。若用 `>0` 判定，
> 缩放软边的极淡像素全部被当成形状边缘，描边亮色会沿软边噪声在图案内部织成网状亮纹。

## 四、脚本（引擎顺序：PS 自动化首选，模拟引擎回退）

**首选：PS 自动化引擎**（效果最好，需要本机安装 Photoshop + pywin32）：

```
python scripts/ps_place_district.py --input <图案.png> --outdir <目录> [--enhance] [--psd <自定义模板>]
```

- 流程：COM 调用本机 Photoshop → 编辑内置模板的 `District Alpha` 智能对象 →
  置入素材（非破坏变换，PS 亲自重采样）→ 保存写回 → 逐区域导出 256×256 PNG。
- 产物命名：`<区域组名>.png`；素材置入前由 `prepare_pattern` 做前置分路并落盘临时 PNG。
- **exit 4 = 本机 Photoshop 不可用**：停下询问用户二选一（模拟引擎 / 安装 PS），不静默降级。

**回退：模拟引擎**（无 PS 环境经用户确认后使用，效果较差）：

```
python scripts/build_district_icon.py --input <图案.png> --outdir <目录> [--preview]
    [--districts "Theater,Holy Site"]   # 默认全部 12 区域
    [--enhance]                         # 低画质素材预处理（小图放大+alpha 对比度+锐化）
    [--psd <自定义模板>]                 # 默认内置模板
    [--list]                            # 只列出 PSD 里的区域组
```

- 产物命名：`<区域组名>_256.png`；退出码 0 成功 / 2 输入或自检失败 / 3 素材无法认定。
- 内置自检：每张 256×256、全图不透明占比 45~85%（六边形正常区间）。
- 依赖：PS 引擎 = pywin32、Photoshop；两引擎共用 = psd-tools、Pillow、numpy、scipy、opencv-python。
  除内置模板外**不依赖 skill 外的任何文件**。

## 五、验证与交付

1. 脚本自检退出码 0（含处理路径说明与清理报告）。
2. 数值抽查（可选项，抽 1~2 张）：**图案质心相对落位框中心偏移 < 1.5px**（视觉重心对齐）；
   成品图案不透明区颜色 ≈ 该区域 `grad` 色标区间；底色 ≈ 该区域 `bg_grad` 中段色、
   边框 ≈ `Border` 原色。
3. **人眼验收**：与 PSD `Reference` 组官方小图对照底图与边框配色；审核通过前不生成 DDS/`.tex`。
4. 审核通过后：走 `civ6-modding/art-pipeline.md`（png→dds、`ICON_DISTRICT_*` 命名、
   `IconTextureAtlases`/`IconDefinitions` 注册；注意"同名重复注册会静默劫持图标"）。
