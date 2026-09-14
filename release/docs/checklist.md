# Upload Checklist

## 上传前

- [ ] Steam 客户端已运行并登录
- [ ] 账号拥有 Civ6
- [ ] 已使用非 Trimmed 构建工具
- [ ] 本地 mod 目录包含 `.modinfo`
- [ ] 已创建 workspace：
  - [ ] `content/` 已复制最新 mod
  - [ ] `workshop.json` 已写（仅更新时只写 changeNote）
  - [ ] `mod_id.txt` 已写入正确 ID
- [ ] `validate` exit 0

## 上传中

- [ ] 大文件给足超时（建议 30 分钟）
- [ ] 输出日志已保存
- [ ] 若失败，间隔 1–2 分钟再试

## 上传后

- [ ] 使用 `verify.ps1` 验证 `time_updated` 变化
- [ ] 使用 `verify.ps1` 验证 `hcontent_file` 变化
- [ ] 检查 `workshop_log.txt` 中是否有：
  - [ ] `Uploaded new content`
  - [ ] `Upload finished ... : OK`
- [ ] 确认可见性未被意外修改（应为 0 = public）
- [ ] 确认标题/描述/标签未被覆盖

## 网络差时

- [ ] 运行 `release\scripts\clash_proxy.py --url https://steamcommunity.com/sharedfiles/filedetails/?id=<id>`
- [ ] 确认 GLOBAL 已切换到低延迟节点
- [ ] 可先用 TEST_MOD_EMPTY 验证连通性
