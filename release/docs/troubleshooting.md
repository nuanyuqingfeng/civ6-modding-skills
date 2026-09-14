# Troubleshooting

## 1. Trimmed 构建卡在 PreparingContent

现象：

```text
Status: k_EItemUpdateStatusPreparingContent
... 持续 10 分钟以上，无 bytes processed
```

原因：

- `PublishTrimmed=true` 裁剪了 Steamworks.NET 依赖的反射回调。
- `SubmitItemUpdate` 的结果回调可能永远不触发。

解决：

```powershell
dotnet publish -c Release -r win-x64
```

不要加 `-p:PublishTrimmed=true`。

## 2. k_EResultFail / No Connection

现象：

```text
Error occurred while uploading to the workshop! Result: k_EResultFail
```

Steam 日志：

```text
Failed to initialize build on server (No Connection)
Timeout uploading manifest
Failed to download manifest ... (request failed)
```

处理：

1. 等待 1–2 分钟再重试。
2. 如果持续失败，用 `clash_proxy.py` 切换节点。
3. 先传小文件（如 TEST_MOD_EMPTY）验证连通性。

## 3. UploadingContent 后失败

现象：

```text
PreparingContent -> UploadingContent -> Invalid -> k_EResultFail
```

原因：

- 大文件传输中途断连。
- 服务端 manifest 请求超时。

处理：

- 重试。
- 大文件上传建议给 30 分钟超时。
- 优先用非 Trimmed 工具，因为它会显示真实 bytes 进度。

## 4. 0 of 0 bytes -- success（假成功判断）

现象：

```text
Preparing: 1234xxxx / 1345xxxx bytes
Update   : 0 of 0 bytes -- success
```

不能直接认为内容已更新，必须验证：

```powershell
release\scripts\verify.ps1 -ItemId <id>
```

判断：

- `hcontent_file` 变了 → 内容确实更新（可能 chunk 已存在，0 字节也正常）。
- `hcontent_file` 没变 → 假成功，工坊仍是旧内容。

同时看 Steam 日志：

```text
No content change detected
Uploaded new content ( ManifestID ... )
Reverting to previous content ...
```

## 5. Steam API result 9

现象：

```json
{ "publishedfileid": "...", "result": 9 }
```

可能原因：

- 条目是 private / unlisted，匿名 API 查不到。
- 不能据此判定条目不存在。

处理：

- 用上传器以作者身份尝试。
- 用 `release\scripts\find_item_id.ps1` 从本地 Steam 日志确认。

## 6. 官方上传器对个别作品 0 字节 success

可能原因：

- 本地内容与服务端 manifest 一致。
- 之前中断上传留下的 chunk 已被 Steam 缓存。
- hijacked 版上传器封装不完整。

建议：

- 改用本文档所属的 `civ6-modding/release.md` 所述非 Trimmed 工具。
- 上传后必须 verify。
