# BLP 素材复原与产物验收知识（门禁后内容）

> 进入条件：用户已在本会话明确授权。本文只整理判据、证据边界与验收方法，不附带任何解包器程序。
> 来源：ModTools 5.4（MIT）`skills/05-modtools-civ/art-unpack.md` 改写；上游为千川白浪
> `Civ6ArtUnpack_Handover.zip`（2026-09-17 移交包，无包级许可证——只作技术事实参考，
> 不分发其代码、工具与游戏资产）。上游未复现的条目保留「未验证」标注，禁止当已验证事实引用。

## 适用与不适用

适用于：用户授权后对 BLP / CIVBIG / SHARED_DATA 包体做定位、解码、重建、编译与游戏验收的全程判断；
FGX / GEO 重建、领袖蒙皮、预乘纹理回打包、pantry 同名遮蔽、Cooker 假成功的排错。
制作新的静态地标先走 `civ6-landmarks`；本文用于资源证据与排错，不取代任何工具链。

## 五种完成状态（验收语言）

| 状态 | 必须提供的证据 |
|---|---|
| 能定位或列出 | 实际包、DLC/路径、记录种类、名称、偏移和长度；找到字符串不等于找到可解载荷 |
| 能解码 | 解出实际数据，并与独立已知资源比较；不能只生成同名空壳 |
| 能重建 | 从明确的导出数据生成源资产；说明模板、骨架、UV、切线和未知部分 |
| 能编译 | 本次源参与了编译，产物包含目标对象；排除 SDK 同名 pantry 遮蔽及旧产物 |
| 游戏可用 | 实际几何、材质、动画、光照与触发在目标游戏中成立 |

- ModBuddy 显示 Build succeeded、Cooker 返回 0、BLP 非空、文件长度相同，都不能单独证明复原正确。
  检查完整日志及产物内部条目，再按目标比较几何或像素；字符串 grep 只能证明有文字，不能证明对应网格有效。
- 源、重建、Cooker 产物和游戏部署各保存身份、散列及验收结果。重建阶段若又从原始包复制全部字节，
  最终 SHA-256 相同只能说明直通，不能说明已经解码和重建。

## 类注册核对知识（XLP / AST / GEO / TEX）

以所用 SDK 配置（官方 `Civ6.cfg`）为准，不把固定类数量或作者机器的映射常量带入规则：

- XLP 的 `m_ClassName` 查 `m_XLPClasses`，不与 AST 或 GEO 共用一张类表。
- ASSET / TEXTURE 类型的 XLP 按 `m_ObjectName` 找本地 AST / TEX，校验其类是否在 `m_AllowedClasses` 中；
  `m_EntryID` 是外部引用名，两者可以不同。
- AST 的 `m_ClassName` 查 AssetClass，模型 `m_GeoName` 连接 GEO，再按 `m_AllowedGeoClasses` 验证几何类。
- GEO / TEX 分别查 GeometryClass / TextureClass。SDK 中同名的 AnimationClass 等不覆盖这些类别。
- 外部 pantry 才有的对象列为未验证；不能把没有扫描的外部库判成文件缺失，也不能默认它有效。
- 尚未覆盖的 XLP 实体类型、FGX 网格/骨架、实际 pantry 优先级及编译后 BLP 明确保留为未验证。
- 已知实测：LeaderFallback 允许 `Leader_Fallback`，UITexture 允许 `UISliceTexture` / `UserInterface`；
  误用 UI 贴图类可能被 Cooker 剔除。合法 DecalGeometry 也不能无条件禁止，
  但不能因为它排在允许列表第一位就拿来重建普通实体几何。

检查器未随本 skill 提供：`.tex` 类别与 XLP 注册类的核对走 `civ6-modding` 的 `art/verify_tex_class.py`；
引用链查询走 `civ6-art-reference` 的 `scripts/art_lookup.py`。AST / GEO 类规则作为手工核对依据。

## BLP 与名字的证据边界

- 区分容器头、自描述区、记录族和载荷。上游不同阶段描述了 0x70 扫描、72/104 等记录布局；
  不能将某个步长当所有 BLP 记录的统一格式。
- 同名记录可对应不同缓冲；不能按名字只留第一项。还要记录包路径、DLC、记录类型、偏移、尺寸，
  区分顶点/索引和共享池。
- 不把 SkinnedVB、AuxVertData、ResultVB、AdjacencyGraph、SharedFinIB 等内部缓冲名直接当 XLP 资产名。
- EntryID、ObjectName、文件 stem 和原始包内名称分别保留；名称可能含路径。
  磁盘安全命名需保留映射，不能洗白后再按名字错误地判缺。
- 同 stem 的 LeaderFallbackImages、light_rigs 等可能来自不同 DLC。输出和缓存按来源相对路径/DLC 隔离，
  避免累积或覆盖。
- 统计覆盖率要说明分母是包、资产、子网格、三角还是已解释载荷；历史样本数字（如 99.07%）
  是原作者某次样本和判据的结果，不得当作承诺。

## 几何、蒙皮与重新烤制

上游较新的 LEADER_GEOMETRY_SPEC 与 multimesh.py 描述按子网格处理 SkinnedVB / AuxVertData / ResultVB，
记录了 80 / 36 / 8 字节流与 8 个骨骼影响。它们与较早 README 的「领袖不可用」或「合并为单网格」不一致，
必须连同来源版本阅读，不把旧假设用于新资产。

这些是待目标样本复验的技术线索，不能直接推成所有资源都需 152 字节 FGX 顶点或所有 UV 池都按同一种方式切分。
逐子网格核对索引范围、位置、法线/切线、权重、骨架、材质槽和 UV；缺 UV 时可记录几何已解，不能宣称完整外观复原。

GEO 的网格声明要与 FGX 实际网格对应。编译器可能按接缝拆分/合并顶点，因此顶点数相同不是充分判据；
同样，三角数相同也不能证明位置正确。点云容差匹配、索引/拓扑、材质绑定和视觉对照各有作用，
NaN 与量化误差需单独记账。

验收自建资源时，给资源唯一测试名，记录实际使用的本地文件和外部依赖，做最小对照构建以排除 pantry 同名遮蔽。
按包隔离 Cooker 进程和输出有利于定位崩溃；遇到中文路径编码问题使用独立 ASCII 暂存，不改用户正式路径。

## 纹理与回打包

上游将预乘 RGBA 载荷与 PNG 视图分开保存：低 alpha 的反预乘可能丢失信息，预览 PNG 不一定能重建原始字节。
不要因此给普通 HTML/PNG 源图自动预乘；原始载荷的域、格式和 mip 链必须先确认。

字节一致只适用于已明确可逆的范围。记录 mip 数量、每级尺寸、压缩/未压缩格式和色彩空间；
不能用一个纹理族的不可逆结论覆盖另一个族。BC5 法线等需要在正确的向量/着色语义下比较，
普通 RGB 相似度不能证明切线空间正确。

回打包验收分开报告实际重建载荷、可再生对齐/填充、自描述骨架直通和未知间隙；
0% 载荷覆盖即使散列一致，也不是完整复原成功。

## 使用移交包时

原包作为用户本地参考保留。按其路径移植清单检查游戏、SDK、SDK Assets、FBX 模板及工具路径，
只在隔离工作副本中适配必要入口；不全局替换仓库或 SDK，也不盲目 import 批处理脚本。

已静态核对 blpkit/cli.py 的 header、entries、meshes、obj、fgx、chain、sweep、fgxsec、selftest、env 入口。
原包需要自己的 NumPy/Pillow 及部分外部工具。完整依赖和执行副作用按具体入口检查后才能执行。

已确认的移交冲突：

| 冲突 | 处理 |
|---|---|
| 文档提到 batch_extract_leaders.py / batch_cook_pantry_leaders.py，包内缺失 | 不把这两个命令当可用能力；其他同名近似脚本不视为替代 |
| SESSION_STATE 记 extract_leader_submeshes(blp_path) | 实际函数参数是 blp_bytes, descs；引用代码签名 |
| README、GOAL、SESSION 对领袖/动画和完成率前后不同 | 保留时间与证据级别；有提取代码不等于整条重建/游戏链已验证 |
| 源资料曾建议把 XLP 列入 civ6proj Content | 按现行美术源目录与 SDK targets 契约执行，不导入旧临时规避方案 |
| 上游复原实验禁止复制 SDK 资产 | 是其「独立复原」验收条件，不改成一般禁令；引用和分发仍遵守各自许可 |

## 上下文口径

Lua 与玩法旁支遵循家族口径：端内跨上下文只有 `LuaEvents`；跨端只有 `EXECUTE_SCRIPT`（UI→GP）、
`ReportingEvents.SendLuaEvent`（GP→UI 推送）、PROPERTY 读取（双向）三个固定通道
→ `civ6-modding/reference/context-matrix.md`。

## 来源

- ModTools 5.4（MIT）：本文的判据结构与验收分层改写自其知识库；未复制其代码。
- 千川白浪移交包（无许可证）：技术事实来源；不复制其 blpkit、Oodle/Granny 辅助程序、
  `.git` 历史、索引库存或游戏资产。
- 详见本仓库 `THIRD_PARTY_NOTICES.md`。
