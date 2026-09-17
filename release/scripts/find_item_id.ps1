# Find workshop item IDs from local Steam logs
param(
    [string]$ModName = "",
    [string]$LogDir = "F:\Steam\logs"
)
# 日志目录缺失时 PowerShell 只会报非终止错误 -> 无输出、无退出码，容易被误读成「没有条目 ID」
if (-not (Test-Path -LiteralPath $LogDir)) {
    Write-Error (("找不到 Steam 日志目录: {0}`n" +
        "  F:\Steam\logs 只是作者机器的示例默认值，别人机器上通常不存在；请用 -LogDir 指定你的 Steam 日志目录。`n" +
        "  怎么找：Steam 安装目录下的 logs 子目录（每个 Steam 库文件夹各有一份），例如`n" +
        "          D:\Steam\logs / C:\Program Files (x86)\Steam\logs；content_log*.txt、workshop_log*.txt 就在那里。`n" +
        "  用法示例: .\find_item_id.ps1 -ModName <你的mod名> -LogDir 'D:\Steam\logs'") -f $LogDir)
    exit 1
}
if ($ModName -ne "") {
    $pattern = [regex]::Escape($ModName)
    Get-ChildItem -Path $LogDir -Filter "content_log*.txt" | ForEach-Object {
        $pat = "(\d+)\\" + $pattern + "\.modinfo"
        Select-String -Path $_.FullName -Pattern $pat | ForEach-Object {
            if ($_.Matches[0].Groups[1].Value) { $_.Matches[0].Groups[1].Value }
        }
    } | Sort-Object -Unique
} else {
    Get-ChildItem -Path $LogDir -Filter "workshop_log*.txt" | ForEach-Object {
        Select-String -Path $_.FullName -Pattern "Create new workshop item of type Community for AppID 289070 : (\d+) \(OK\)" | ForEach-Object {
            $_.Matches[0].Groups[1].Value
        }
    } | Sort-Object -Unique
}
