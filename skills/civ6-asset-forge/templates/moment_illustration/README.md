# 历史时刻插画模板（18 张官方形状）

本目录随包内置 **18 张 PSD 模板**（`1.psd` … `18.psd`，共约 14 MB），来源为用户提供的
官方历史时刻模板；编号 **4 是空的工作稿**（数字层为空，脚本会自动跳过），实际可用 17 张。

## 一、模板是什么

原版 240 张 `Moment_*.dds`（456×332）对这批模板做二值 IoU，**全部 ≥0.80**（0.90–0.95 占 22.9%），
即 18 张模板覆盖了官方形状族。用法是"把源图套进模板的形状遮罩"，不需要自己画形状。

- 覆盖率对照：原版 240 张区间 **83.0% ~ 98.5%**；漏套模板的实测值是 **14.5% / 15.3%**（卡片边缘形状不对）。
- 每张模板的覆盖率/宽高比可直接列出来看：

```bash
python scripts/apply_moment_template.py --list
```

- 看清某张模板的图层语义（哪个是形状遮罩、哪个是描边）：

```bash
python scripts/psd_inspect.py templates/moment_illustration --pick 1,4,18
```

## 二、脚本用法

```bash
# 按编号套模板
python scripts/apply_moment_template.py --input <源图.png> --template 7 --out <输出目录>

# 按源图长宽比自动挑模板
python scripts/apply_moment_template.py --input <源图.png> --auto --out <输出目录>

# 批量 + 同时写单 mip RGBA8 DDS
python scripts/apply_moment_template.py --input-dir <源图目录> --auto --dds --out <输出目录>
```

模板目录**默认就是本目录**（`templates/moment_illustration/`），无需再传 `--template-dir`；
要换自己的模板时用 `--template-dir <目录>`，或在 `local_paths.json` 写 `{"moment_template_dir": "..."}`。

## 三、手工流程（Photoshop，原做法，仍然可用）

1. PS 打开一张模板；
2. 导入你要制作的图片；
3. **选中形状图层 → `Ctrl+点击` 模板的遮罩层**（载入选区）→ **`Ctrl+J`**（把选区内容复制成新层）→ 关掉多余图层；
4. 调色使其匹配历史时刻的观感：`Ctrl+U` 勾选**着色**按你的图调色，或新建纯色层用**正片叠底**再微调饱和度。

> 套版产物应当是 **456×332**、`m_ClassName=UserInterface`、`m_Tags` 单条 `UserInterface`，
> alpha 覆盖率落在上面区间内；交付前用 `python scripts/verify_moment.py --project <工程根>` 自检。

## 四、许可说明

模板形状派生自游戏内历史时刻插画的轮廓（作者整理为 PSD），按"不设版权限制"随本仓库分发，
供模组制作者直接使用；如原作者/权利方有异议请提 issue，我们会移除。
