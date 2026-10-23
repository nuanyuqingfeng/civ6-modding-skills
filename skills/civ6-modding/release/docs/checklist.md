# Upload Checklist

## 上传前

- [ ] Steam 客户端已运行并登录（**刚启动 1–2 分钟内上传会撞 Steamworks 断言**，见下）
- [ ] 账号拥有 Civ6
- [ ] 已使用非 Trimmed 构建工具
- [ ] 本地 mod 目录包含 `.modinfo`
- [ ] 已创建 workspace（**首选** `make_workspace.ps1`，一条命令走完建链/元数据/validate）：
  - [ ] `content/` 是**指向 Mods 副本的 junction**，不是物理复制
        （`(Get-Item "$ws\content" -Force).LinkType` 应为 `Junction`；重建成本 1 MB，别复制 751 MB）
  - [ ] 工作区在 `$env:TEMP\civ6-ws\<ModName>`（★ DSH 会话的 TEMP 每会话独立，**跨会话别想复用**，直接重建）
  - [ ] `workshop.json` 已写：
    - 仅更新内容 → 只写 `changeNote`
    - **完全不想留更新说明 → 写空对象 `{}`**（不写任何字段则一切 metadata 不被触碰）
    - ★ 线上条目**有工坊依赖**时，无论上面哪种写法都要把 `dependencies` 全量写出（不写 = 依赖被清空）
- [ ] **首次上传**：介绍按 `workshop-intro.md` 的三栏口径写好
  - [ ] 丙栏 `[code]` 主体由 `tools/workshop_intro.py build` 从工程 `Text/` 提取
  - [ ] 甲栏点赞横幅 / QQ 群行按需取自 `release/templates/intro-presets.md`（本机自留）
  - [ ] 乙栏（前置行、标语、致谢、写在最后）与用户提供的内容逐字一致；未提供的段落**不存在**
  - [ ] 无占位符残留（`TODO` / `<待填>` / `{{` 一类由 `workshop_meta.py` 判失败）
  - [ ] 整篇 description ≤ **8000 字节**（UTF-8；超出会被服务端整次拒收，见 `troubleshooting.md` 第 7 节）
  - [ ] 各语言 `title` ≤ **128 字节**（UTF-8；作者未指定时取模组 modinfo 的 `..._MOD_TITLE`，用 `workshop_intro.py titles` 回填）
  - [ ] `dependencies` 与 `workshop_intro.py deps <源工程根>` 的结果一致
- [ ] **更新已有条目**：更新说明按 `workshop-intro.md` §三 产生
  - [ ] `release/scripts/draft_note.py --project <源工程根>` 已跑出草稿（基线取自台账「上传基线」）
  - [ ] `changeNote` 已人工定稿（玩家视角、1~3 条、无路径与标识符）
  - [ ] 条目编号按 `release/scripts/find_item_id.ps1 -ModName <mod>` 核对，命中顺序为
        ① 账户工坊列表（`-Account` 列出全部条目；来源 `steamcommunity.com/profiles/<steamid>/myworkshopfiles/?appid=289070`，直连不通时走本地代理 `127.0.0.1:7897`）
        ② 项目台账 `<p1>\<工程>\<mod>\workshop-ledger.md`
        ③ Steam `content_log*.txt` 的 `<id>\<mod>.modinfo`
        三处都没有 → 向用户索要；台账只作为记录与复制来源，不作为唯一来源。
        **禁止用 `new` 建工作区探编号**，那会另建重复条目
  - [ ] `mod_id.txt` 已存在且 ID 正确
        （★ 缺失会被当成新条目**另建一个**，上传前先 `Test-Path "$ws\mod_id.txt"`；
        用 `make_workspace.ps1 -ItemId <ID>` 可显式写入，省略它会打 WARN 提醒）
  - [ ] `image.png`（可选）：要换预览图才放，规格 **PNG / 512×512 / ≤ 1 MB**，
        由 `art/make_workshop_preview.py` 产出（**执行端在 art/**；`tools/workshop_cover.py`
        已委托同一管线）。**不放 = 保留线上原图，不算错**
  - [ ] 预览图**未二次缩放**（输入已是 512 成品 → 工具默认直通；别用 `magick -resize` 裸缩，
        默认 Mitchell 滤镜偏软就是封面发糊的根因）
  - [ ] 预览图**未署名**（项目约定：作者只写在 `.modinfo` 的 `Authors` 与代码里）
- [ ] `validate` **exit 0**（exit 2 = 提示级，确认后可继续；exit 1 必须先修）

## 上传中

- [ ] 大文件给足超时（建议 30 分钟）
- [ ] 输出日志已保存（注意：**直调 exe 不写 `tool/logs/`**，只有 `release/scripts/upload.ps1` 包装才写）
- [ ] 若失败，间隔 1–2 分钟再试

## 上传后

- [ ] 验证 `time_updated` 变化
- [ ] 验证 `hcontent_file` 变化（**没变 = 假成功**，见 `No content change detected`）
- [ ] 检查 Steam 日志 `workshop_log.txt` 中是否有 `Upload finished ... : OK`
- [ ] 确认可见性未被意外修改（应为 0 = public）
- [ ] 确认标题/描述/标签未被覆盖（空 `{}` 时日志应显示 `Uploading ''`，标题不变）
- [ ] 放了 `image.png` 时确认预览图已更新（日志出现 `k_EItemUpdateStatusUploadingPreviewFile`）
- [ ] 确认**没有多出重复条目**（缺 `mod_id.txt` 的症状，见「上传前」）
- [ ] 更新 `workshop-ledger.md`（版本号 / 内容规模 / 历史版本 / 操作历史四段）

## 下架（可选，不可逆）

- [ ] 台账 + `mod_id.txt` **双向核对**条目 ID
- [ ] `remove -w <ws> -i <id>`（**只删线上条目**，本地 workspace / Mods 副本不受影响）
      —— `-w` 只是让工具能读到 `mod_id.txt` 之类的上下文；也可直接 `-i <id>`
- [ ] 回写台账「操作历史」表（下架日期 + 原因）

## 网络差时

- [ ] 运行 `release\scripts\clash_proxy.py --url https://steamcommunity.com/sharedfiles/filedetails/?id=<id>`
- [ ] 确认 GLOBAL 已切换到低延迟节点
- [ ] 可先用 TEST_MOD_EMPTY 验证连通性

