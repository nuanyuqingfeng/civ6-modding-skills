# Upload Checklist

## 上传前

- [ ] Steam 客户端已运行并登录（**刚启动 1–2 分钟内上传会撞 Steamworks 断言**，见下）
- [ ] 账号拥有 Civ6
- [ ] 已使用非 Trimmed 构建工具
- [ ] 本地 mod 目录包含 `.modinfo`
- [ ] **发布前剥离注释**（默认只剥 `.lua`）：
  - [ ] `python strip_comments.py <Mods副本> --src <源工程>` → exit 0
  - [ ] 确认 `OK 目标目录 == strip(源工程)`
  - [ ] 注：每次 `modinfo_build.py --deploy` 或 ModBuddy `Rebuild All` 都会**把注释带回来**，故本步**必跑**
  - [ ] （`luac -p` 是差分判定：`Civ6 类型标注` 类既存误报会被跳过并计数，不算失败）
- [ ] 已创建 workspace：
  - [ ] `content/` 已复制最新 mod（**剥离之后**的版本）
  - [ ] `workshop.json` 已写：
    - 仅更新内容 → 只写 `changeNote`
    - **完全不想留更新说明 → 写空对象 `{}`**（不写任何字段则一切 metadata 不被触碰）
  - [ ] `mod_id.txt` 已写入正确 ID（台账是唯一真源）
- [ ] `validate` exit 0

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
- [ ] 更新 `workshop-ledger.md`（版本号 / 内容规模 / 历史版本 / 操作历史四段）

## 网络差时

- [ ] 运行 `release\scripts\clash_proxy.py --url https://steamcommunity.com/sharedfiles/filedetails/?id=<id>`
- [ ] 确认 GLOBAL 已切换到低延迟节点
- [ ] 可先用 TEST_MOD_EMPTY 验证连通性

