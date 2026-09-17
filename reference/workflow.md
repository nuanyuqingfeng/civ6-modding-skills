# 美术素材配置完整流程（mod 引用原版素材）

> 场景："为 XX（区域/资源/改良/建筑/单位…）配置美术素材"。目标是让新对象直接复用
> 原版已打包的模型/贴图，**全程不解包任何 .blp**。规律细节见 `chain-map.md`。

## 流程总览

```
① 明确对象与语义 → ② 选原版参照物 → ③ 查参照物引用链 → ④ 克隆生成 mod 条目
→ ⑤ 注册 .Art.xml 消费者 → ⑥ 静态校验 → ⑦ 同步 Mods 副本测试（询问后）→ ⑧ 回写/提交
```

## ① 明确对象与语义

1. 确认对象的 DB Type 已定义（`Data/*.sql`），拿到准确 Type 名与类别。
2. 收集语义信息用于"找相近素材"：
   - 资源：陆地/海洋、地形与特征（`Resource_ValidTerrains` / `Resource_ValidFeatures`）、
     产出、是否上地图（`Frequency`/`SeaFrequency`）。
   - 区域：功能定位（学院/圣地/商业…）。
   - 名字含义：中文/英文语义（可用 dsh_validate 查语料助判）。
3. **Icon 例外规则**：默认不处理 2D Icon。仅当对象会因缺 Icon 定义而悬空（数据库
   引用了不存在的图标）时才补图标链（SQL `IconTextureAtlases`，不属 artdef）。
   本工程资源图标已全套注册，通常无需动作。

## ② 选原版参照物（"相近功能/形态"优先级）

1. 优先**同名/近义**原版对象（如橄榄→`RESOURCE_OLIVES`，海龟→`RESOURCE_TURTLES`）。
2. 其次**同类同环境**：海产在 `CRABS/PEARLS/WHALES/REEF_TURTLES/REEF_FISH/BARRIER_REEF`
   里选；林果在 `BANANAS/CITRUS/COCOA/SPICES/TRUFFLE` 里选。
3. 全量候选清单：`art_lookup.py --list <模板> --prefix <前缀>`（如 `--list Clutter --prefix CLUTTER_`）。
4. 区域类参照物直接选功能相近的原版区域（学院→Campus，圣地→HolySite）。

## ③ 查参照物完整引用链

```bash
cd <skill>/scripts
python art_lookup.py RESOURCE_OLIVES Resources     # 条目 + ArtDef 引用 + XrefName 字符串
python art_lookup.py CLUTTER_OLIVES Clutter        # 下一跳：BLP 终点（包/条目）
python art_lookup.py DISTRICT_CAMPUS Districts     # 区域三跳：Districts→Landmarks→BLP
python art_lookup.py --xlp environment/clutter     # 按包查条目清单
```

输出回答三个问题：条目在哪个 artdef 文件、引用了哪些 artdef/字符串、模型终点在哪个包。

## ④ 克隆生成 mod 条目（art_copy.py）

```bash
python art_copy.py <模板名> <原版条目> <新Type名> \
    --set-xref <目标CLUTTER_*/条目名> \
    --out "<mod>/ArtDefs/<模板名>.artdef"
```

- 行为：从原版 artdef 提取该条目**整棵子树**（含全部子集合与变体），改名后追加到
  mod artdef（文件不存在自动建骨架；已存在同名条目则跳过并 WARN）。
- `--set-xref` 统一替换条目内所有 `XrefName`（含 ClutterVariants 变体）。需要按
  地形/特征区分变体时，生成后手改各变体子条目的 `XrefName`。
- 克隆后的条目引用的是**原版已打包资产**（BLP 按名引用），mod 不携带模型文件。
- 不指定 `--out` 时打印 XML 到 stdout（预览/dry-run）。
- 若参照物本身是 Landmark 挂载型（如 `RESOURCE_TURTLES`→`RES_LM_TURTLES`），克隆后
  需要连带把 Landmarks.artdef 的目标条目也克隆或改指原版条目。
- **克隆单位（含伟人）条目前的必做体检**：原版条目「存在」不等于「能正常渲染」——
  原版自身有引用了不存在 bin 的成员类型。按 `chain-map.md` §5.2 校验成员类型的
  `Attachments → Bins` 每一段都落在合并集 bin 名全集里，**不通过就换一个成员类型**，
  否则实机表现是单位渲染残缺（典型「只剩一个头」，因为 Head bin 独立于 Armor bin）。
  伟人条目名还是运行时按 `UnitType + Gender + Era` 拼出来的，见 `chain-map.md` §5.3。

## ④′ 分支：替换型建筑（取代原版建筑）上 3D 模型

适用：新建筑**取代**某原版建筑（结社建筑 / 特色建筑 …）。
**不要**套 ①②③④ 的资源套路 —— 建筑链以「区域」为中枢，机制见 `chain-map.md` §三.3。

1. **先确认建筑条目与是否走这条链**：

   ```bash
   python art_lookup.py --building BUILDING_BASE
   ```

   看 `AffectsDistrictBuildingSet` 是否为 `true`（是才走这条链），
   并直接得到「哪些区域的 BuildingSets 引用了它、模型资产落在哪个包」。

2. **反查 `DistrictReplaces`**：原建筑所在区域可能被文明特色区域取代
   （希腊卫城取代剧院广场；本工程 `DISTRICT_ODYSSEY_RGN` 取代 `DISTRICT_THEATER`）。
   游戏侧的由工具自动反查；**mod 侧区域不在索引里，必须先自己查清并用 `--district` 传进去**。

3. **一键生成**（先 `--dry-run` 看反查结果与目标区域列表）：

   ```bash
   python art_copy_building.py BUILDING_BASE BUILDING_NEW        --buildings-out "<mod>/ArtDefs/Buildings.artdef"        --landmarks-out "<mod>/ArtDefs/Landmarks.artdef"        --district DISTRICT_MY_RGN
   ```

   工具会：克隆建筑条目 → 逐区域从「该区域自己的子条目」推导形状 →
   改标签 / `Tag_HeroBuilding` / `Set` 引用 → **增量追加**（同名子条目自动跳过，幂等）。

4. **必须过 ⑥ 的「原有内容零丢失」自检**（工具自带，输出 `原有内容丢失 = 0`）。
   区域条目是增量追加进已有 `Landmarks.artdef` 的，通常不需要改 `.Art.xml`。

## ⑤ 注册 .Art.xml 消费者

新 artdef 文件必须挂进 mod 的 `.Art.xml`（构建时进 `.dep`）：

| 新增文件 | 挂到 consumer | 参照 |
|---|---|---|
| `Resources.artdef` | `Resources`（vanilla 还同时挂 Landmarks / WorldView_Translate） | Expansion1.dep |
| `Clutter.artdef` | `Clutter` | 同上 |
| `Districts.artdef` | `Districts` 相关消费者（Audio / StrategicView_Translate / WorldView_Translate） | 本工程现状 |
| `Units.artdef` | `Units` | 本工程现状 |
| `Landmarks.artdef` | `Landmarks` | 本工程现状 |

- `.civ6proj` **不需要**新增条目（ArtDefs/XLPs 由 ModBuddy 自动打包）。
- 已有 artdef 文件追加条目不需要改 `.Art.xml`。
- 编辑 `.Art.xml` 时注意它是 ModBuddy 管的文件，保持既有排版，只加
  `<Element text="Resources.artdef"/>` 一行到对应 consumer 的 `relativeArtDefPaths`。

## ⑥ 静态校验（交付前必做）

1. 生成的 artdef 能被 XML 解析（`art_copy.load_xml` 即可）；
2. 条目 `m_Name` 与 DB Type 完全一致（区分大小写）；
3. `XrefName` 目标存在于原版索引（`art_lookup.py <目标> <模板>` 能查到）；
4. `--list` 复查没有把同一对象配两条；
5. 引用 DLC 素材时确认 mod 依赖（`.civ6proj` AssociationData）已声明，
   **且该素材所属包已写进 `.Art.xml` 的 `<requiredGameArtIDs>`**（两者是两回事：
   前者管游戏侧加载，后者管 ModBuddy cook 时的 pantry 搜索路径）→ `cook-layer.md` §一。
6. **替换型建筑专项**：① 原有子条目**零丢失**（结构化比对：读改写前后各区域内
   `m_ChildCollections` 的子条目名集合，旧集合必须是新集合的子集）；
   ② **所有取代该区域的 District 都已挂**（`DistrictReplaces` 反查）；
   ③ 自闭合标签风格与文件既有风格一致（项目多数文件用 `"/>`，无空格）。
7. **cook 层校验**（改动 artdef / xlp / `.Art.xml` 后必做，详见 `cook-layer.md`）：
   ① 构建日志 `Art Pantry Path` 展开符合预期；
   ② 数清 `references an ArtDef entry ... that does not exist` 与
   `has had its value replaced with its default value` 的**对子数**，每对都能解释
   （真没美术 / 忘补条目）—— 这是「静默降级」，不是无害警告；
   ③ **重新 cook 一次，把产物与 Mods 副本逐字节比对** —— 判断本次改动有没有运行时
   影响的唯一可靠依据（日志级别会骗人，见 `cook-layer.md` §三.2）。

## ⑦⑧ 测试与落库

- 询问用户后同步到 Mods 测试副本（哈希校验 MATCH），新开局验证：
  模型出现、战略视图正常、无 art 报错日志。
- **⚠ artdef 的同步对象是 cook 产物，不是裸源文件**：cook 会归一化（行尾 LF 化、
  空元素收紧、剥注释、结构重排），拷裸源会让 Mods 副本与下一次构建结果漂移。
  正确做法是**手工 cook 一次到临时 `--banquet_hall`**（别覆盖实机 `.dep`），
  再把产物拷进 Mods 副本，然后哈希校验。详见 `cook-layer.md` §二、§五。
- **拷完/构建后跑一次分级体检**：

  ```bash
  python scripts/artdef_sync_check.py <工程名>          # 或 --all 扫全部工程
  ```

  L1–L5 命中 = 纯编码层差异（行尾/自闭合写法/缩进/空行/注释），**可忽略**；
  只有 L5 仍不同的语义层差异才需要看，其中 `引用被清空`（产物出现 `_MissingArt`
  或 `text=""`）是**真实缺陷信号**。详见 `cook-layer.md` §2.2–2.4。
- 测试改动只留 Mods 的，结束后按双目录工作流统一回写源文件并 git 提交。

## 附：本 skill 工具一览

| 脚本 | 作用 |
|---|---|
| `artdef_indexer.py` | 扫描游戏+SDK 全部 artdef/xlp，建引用链索引（assets/art_index.json.gz，可随时重建） |
| `art_lookup.py` | 查条目引用链 / 列模板条目 / 列 XLP 包内容；`--building B` 反查建筑 3D 模型链；`--district-buildings D` 列区域 hero 组合表 |
| `art_copy.py` | 克隆原版条目为 mod 条目（改名 + 换 Xref + 合并/跳重） |
| `art_copy_building.py` | **替换型建筑 3D 注册**：反查相关区域 → 生成 BuildingSets/BuildingVariants/BaseVariants 三组子条目 → 增量追加（自带零丢失自检）|
| `artdef_sync_check.py` | **源 vs Mods 副本差异分级判定**（只读）：L0–L5 编码层 / 语义层，识别 `cook 补结构` 与 `引用被清空`（`_MissingArt` / 空值）。`--all` 扫全工程，`--report` / `--json` 出报告，退出码 1 = 有语义层差异 |

索引覆盖：`Base/ArtDefs` + `DLC/**/ArtDefs`（运行时真实合并集）+ SDK pantry 全部 xlp。
游戏更新后重建：`python artdef_indexer.py --out ../assets/art_index.json.gz`。
