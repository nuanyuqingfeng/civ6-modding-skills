# 类别⑩：资源图标（Resource Icon）

## 〇、入口判定（路由必读）

**先判素材属于哪一种**：

- **纯图案素材**（无底盘、无圆环/圆盘的白色或彩色图案）→ 进入本流程，底盘由本 skill 内置。
- **已含底盘成品图**（图案 + 黄盘/紫盘 + 黑圆环已经合成在一起）→ 它已经是"合成之后"的产物，
  再走一遍会把底盘当图案套进底盘（套娃）。此类"成品导入"需求走 `civ6-modding/art-pipeline.md` 的 png→dds 直转。

**引擎顺序**：判定通过后**默认先跑 PS 自动化引擎**
（`ps_place_resource.py`：预先按落位框完成构图，再交本机 Photoshop 做图层合成的原生光栅化，效果最好）；
PS 自动化通道不可用（exit 4）时**询问用户**二选一——
(a) 改走无 PS 引擎（`build_resource_icon.py`，纯 Python 按同一套构图铁律合成）；
(b) 补齐缺口后重跑 PS 引擎。不静默降级。
exit 4 分两种成因，脚本分别报出：当前解释器缺 pywin32 模块（附 `pip install pywin32` 修复命令），
或 `Photoshop.Application` ProgID 连不上（Photoshop 未安装，或未注册 Automation 接口）。

**构图唯一来源**：两个引擎共用 `build_resource_icon.place_pattern` 的
图案黑边 → 内容包围盒裁剪 → 等比缩放 → 居中 → 预乘 alpha 重采样。要改构图请改 `place_pattern`，两引擎同时生效。

> **产出**：256×256 RGBA 资源图标单元格（图案 + 类别底盘）。
> **输入**：纯图案 PNG（自带透明通道）。模板与底盘**已随 skill 内置**，无需用户提供。
> **边界**：本类只做单元格合成；PNG→DDS 与 `IconTextureAtlases` 注册走
> `civ6-modding/art-pipeline.md` 通用图标管线。

## 一、底盘（Plate）

资源图标在游戏里**永远带底盘**：加成资源是黄盘，奢侈资源是紫盘，外加一圈近乎黑色的圆环。
底盘不是装饰，是类别标识——缺底盘的单元格在游戏里表现为"图案浮在空底上"，与其它资源不成套。

底盘几何（四张内置底盘**完全共用**，仅配色与 FOW 亮度不同）：

| 项 | 值 |
|---|---|
| 画布 | 256×256 |
| 非零像素 | 33033 |
| alpha 包围盒 | `186x190@35,33` |
| 几何中心 | (128.0, 128.0)（径向对称） |

径向 alpha 剖面（到几何中心的距离，两类别一致）：

| 半径 | alpha | 含义 |
|---|---|---|
| 0 ~ 92 | 153 | 盘面（半透明） |
| 93 | 255 | 圆环内缘抗锯齿 |
| 95 ~ 110 | 255 | 圆环 |
| 111 ~ 114 | 254 → 195 | 圆环外缘抗锯齿 |
| 115 | 1 | 收尾 |

配色：

| 底盘 | 盘面 alpha | 盘面 RGB | 圆环 alpha | 圆环 RGB |
|---|---|---|---|---|
| 加成 `TEMPLATE_resource_plate_bonus.png` | 153 | (189, 141, 11) | 255 | (33, 33, 33) |
| 奢侈 `TEMPLATE_resource_plate_luxury.png` | 153 | (96, 56, 123) | 255 | (33, 33, 33) |
| 加成 FOW `TEMPLATE_resource_plate_bonus_fow.png` | 202 | (170, 124, 34) | 255 | (26, 23, 18) |
| 奢侈 FOW `TEMPLATE_resource_plate_luxury_fow.png` | 202 | (108, 73, 95) | 255 | (26, 23, 18) |

> **FOW 是独立的一套合成，不是母版的亮度变换**：迷雾底盘的盘面 alpha 是 202（母版 153），
> 圆环偏暖褐 (26,23,18)（母版中性灰），圆环覆盖面积也不同（加成 6991 px、奢侈 7597 px，
> 母版为 4465 / 5050）。生成 FOW 图集的正确路线是：**先取图案层做迷雾变换，再叠到 FOW 底盘上**。
> 直接对母版整幅做迷雾变换会同时污染底盘配色。

## 二、类别判定

一个资源属于加成还是奢侈，**以工程数据为准**（`Data/Resources_RGN.sql` 的 `ResourceClassType`），
不按图案外观推断。图集序号与类别的对应：

- **BONUS（黄盘）**：Index 0、1、3 ~ 31，共 31 格
- **LUXURY（紫盘）**：Index 2、32 ~ 38，共 8 格

图集网格 6×7、单元格 256×256，画布 1536×1792（`IconSize=256` 档）。

## 三、构图铁律

1. **图案黑边（硬性，在缩放落位之后）**：按 alpha ≥ 64 取图案**主体掩码**（不补内部空洞），
   沿掩码的**全部边缘**——外轮廓、枝节边缘、内部空隙——向外铺 **5px** 纯黑
   （RGB 0,0,0、alpha 255）圆盘环带，环带 alpha 做 σ=0.6 高斯羽化后 source-over 叠回图案。
   - **宽度按成品像素计**：描边在缩放落位之后进行，各格一律 5px，
     不随源图尺寸与缩放系数变化。在源空间描边再缩放会让大图黑边被缩没
     （2048² 的源图缩到 144px 后等效只剩 0.5px），各格宽度相差 12 倍。
   - **主体阈值 64、且不补洞**：64 以下的浅阴影与软边不参与成环，否则阴影会成为轮廓
     （素材带投影时黑边描到投影上，主体边缘反被划为内部）；不补洞则枝节与镂空各自成环。
   - **黑边不侵入主体**：环带 = 掩码圆盘膨胀减去掩码本身，主体像素零覆盖。
   - 图案先按「落位框内缩 5px」等比装入，图案加黑边的总占位等于落位框。
   - 素材自身已带黑边时用 `--no-stroke` 跳过，避免叠成双圈。
2. **内容包围盒裁剪**：按 alpha ≥ 8 取源图案的紧致包围盒（黑边不计入，由描边事后铺开）。
3. **等比缩放（硬性）**：`k = min(内缩框宽/源宽, 内缩框高/源高)`，**禁止非等比拉伸**。
   拉伸会改变图案比例，与其它资源不成套。
4. **居中装入落位框**：默认落位框 = 该类底盘的 alpha 包围盒 `186x190@35,33`；
   缩放后图案的宽度或高度之一必然填满内缩框，另一维居中留白。
5. **预乘 alpha 重采样（硬性）**：先乘 alpha 再 LANCZOS，回来再除 alpha。
   未预乘时透明像素的 RGB 会混进边缘，渗出杂色。
6. **合成顺序**：图案以 source-over 叠在底盘之上。图案完全透明处，输出必须逐像素等于底盘
   （这是本类的**底盘保真判据**）。

> 黑边宽度来自原版图集实测剖面（形状 alpha ≥ 128 边界向内，逐格按本格内部亮度归一后跨格平均）。
> 两者取自同一批像素位置：
>
> | 深度 | 原始图集（原版） | 本规格（输出空间 5px） |
> |---|---|---|
> | 第 1px | 54.2% | 63.1% |
> | 第 2px | 40.1% | 59.9% |
> | 第 3px | 11.6% | 53.8% |
> | 第 4px | 0.3% | 45.3% |
> | 第 5px | 0.3% | 35.4% |
> | 第 6px | 0.7% | 26.4% |
>
> 原版暗化集中在前 3px，本规格在 3px 之后仍有明显暗化——按肉眼可辨取 5px。

> **源素材自带宽软 alpha 斜坡**时（图案边缘跨度 > 30px 的半透明带），合成后图像的中间调占比会偏低。
> 这是素材固有属性，如果原始图集里同一格也是这个结构，即为等价还原，不属于管线缺陷。

## 四、脚本（引擎顺序：PS 自动化首选，无 PS 引擎回退）

**首选：PS 自动化引擎**（需要本机安装 Photoshop + pywin32）：

```
python scripts/ps_place_resource.py --input <图案.png> --kind bonus|luxury --outdir <目录>
    [--fow] [--box WxH@X,Y] [--psd <自定义模板>] [--no-stroke]
```

- 流程：`place_pattern` 按落位框完成构图 → COM 调用本机 Photoshop 打开内置模板 →
  把已构图图案贴入 `Pattern` 组、按类别单独显示对应底盘 → 原样导出 256×256 PNG。
  Photoshop 只承担图层合成的原生光栅化，不自行缩放或居中素材。
- 产物命名：`<kind>[_Fow].png`；置入前的临时 PNG 落盘在系统临时目录。
- **exit 4 = PS 自动化通道不可用**：停下询问用户二选一（改走无 PS 引擎 / 补齐缺口后重跑），不静默降级。
  成因分两路分别提示——缺 pywin32 模块（打印该解释器的 `pip install pywin32` 命令）、
  `Photoshop.Application` 连不上（Photoshop 未安装，或未注册 Automation 接口）。

**回退：无 PS 引擎**（无 PS 环境经用户确认后使用）：

```
python scripts/build_resource_icon.py --input <图案.png> --kind bonus|luxury [--out <png>]
    [--box WxH@X,Y]      # 落位框，默认取底盘 alpha 包围盒 186x190@35,33
    [--threshold N]      # 源图内容包围盒的 alpha 阈值，默认 8
    [--fow]              # 改用迷雾（FOW）底盘
    [--pattern-only]     # 只输出落位后的图案层（透明底，供 PS 路径预构图）
    [--no-stroke]        # 跳过图案黑边（素材自身已带黑边时用）
    [--plates]           # 打印内置底盘规格后退出
```

- 依赖：PS 引擎 = pywin32 + Photoshop；两引擎共用 = psd-tools、Pillow、numpy。

## 五、模板 PSD 结构

`templates/resource_icon/Resource_Icon_Photoshop_CC.psd`，画布 256×256：

- `Choose Plate` 组：四张底盘各一像素层，层名 `bonus` / `luxury` / `bonus FOW` / `luxury FOW`，
  逐类别单独显示。层名即 `ps_place_resource.py` 写入参数文件的 `plate` 值。
- `Pattern` 组：空的图案占位组。PS 引擎把已构图图案贴入此组，渲染在底盘之上。

## 六、验证与交付

1. 脚本退出码 0。
2. **底盘保真判据**：图案透明处（图案层 alpha == 0 的像素）输出必须逐像素等于该类底盘。任何一处不等即失败。
3. **图案黑边**：逐格核验两项几何——主体（alpha ≥ 64）边界外 1px 环全部落黑、环带（向外 5px）与主体零交集。
   边缘亮度上，形状 alpha ≥ 128 边界向内 1~3px 应低于图案内部：原版实测约 54% / 40% / 12%，本规格约 63% / 60% / 54%。
4. **边缘质量**：边界像素 alpha 落在 20..235 的中间调占比、相邻像素 alpha 跳变 > 200 的硬跳占比。
   参考值由母版逐格 LANCZOS 重出给出，`civ6-modding/art/verify_icon_atlas.py --edge-qa` 可机械比对。
5. **小尺寸档必须从母版重出**：32/38/50/64 各档由 256 母版逐格 LANCZOS 重出；
   旧档与本类产出的母版内容不同，另行加工会引入不一致。
6. **人眼验收**：与游戏内其它资源图标并排对照，确认底盘配色、圆环粗细与图案黑边一致；
   审核通过前不生成 DDS/`.tex`。
7. 审核通过后走 `civ6-modding/art-pipeline.md`：
   `.dds` 为未压缩 `R8G8B8A8_UNORM`、`mips=1`，`.tex` 用 `PF_R8G8B8A8_UNORM` +
   `m_ClassName=UserInterface`，`IconTextureAtlases` 一档一行、`IconDefinitions` 一格一行。

## 七、世界地图档的 mip（`m_CookParams` 的 `IsScalable`）

大地图的资源图标只有 256 档供图：`WorldViewIconsManager.lua:94` 用 `FindIconAtlas(iconName, 256)` 取图，
`WorldViewIconsManager.xml:6` 的 `WorldAnchor UnitsPerPixel="0.06"` 让该图持续缩小采样。
`.dds` 为单 mip 时缩小采样没有更低的层级可用，边缘出现锯齿。

原版 `Resources*.tex` 的 `m_CookParams` 带 `IsScalable` / `TexturePadding` / 目标尺寸，
原版 `Resources256.dds`（2048²）本身即未压缩、带 12 级 mip。
本工程 cooker 的通路在 `IsScalable`：置 `true` 时该档被打成**未压缩基数层 + 完整 mip 金字塔**，
置 `false` 时 cooker 忽略源 `.dds` 自带的 mip 链（单档实测增量 +0）。
本类六档逐项照抄官方同名文件的参数：256 / 64 / FOW 为 `IsScalable=true`，50 / 38 为 `false`，32 留空。

- mip 由 `IsScalable=true` 生成，源 `.dds` 保持单 mip，`verify_icon_atlas.py` 的 mips=1 闸门照常通过。
- 256 / 64 / FOW 三档在 BLP 内为未压缩：`Icons.blp` 由 33618944 B 增至 58166272 B。
- 50 / 38 档与官方仍有差异：官方这两档的 `.dds` 自带 9 级 mip，本工程 cooker 在 `IsScalable=false` 下不打包，
  故这两档在 BLP 内无 mip；世界地图取图的是 256 档（`FindIconAtlas(iconName, 256)`）。
- `gen_tex.py` 生成 `.tex` 时把 `m_CookParams` 写为空块；既有 `.tex` 内容有变化时改写结果落 `workspace/gen/`，
  不覆盖工程文件，照官方复刻的参数不会被静默清除。
- **未经实机验证**：mip 链的收益按取样模型推算（本工程 64 档缩到 20px 时相邻 alpha 跳变 >200 的硬跳占比
  由 3.61% 降到 0.80%），实机效果待进游戏确认。
