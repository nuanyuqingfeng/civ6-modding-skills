# screenshot.ps1 —— 全屏截图（不经 tuner 通道的视觉证据采集）
# 用法：
#   powershell -NoProfile -ExecutionPolicy Bypass -File snippets\screenshot.ps1 ^
#       [-OutFile <png 路径>]
# 缺省落到 %TEMP%\civ6_snap.png（合规中间目录）；同一文件反复覆盖。
# 判读用途：镜头位置 / 浮字与 VFX / HUD 完整性 / 弹窗与菜单残留（2026-10-03 实测可用）。
# 注意：截的是整个主屏；需要游戏窗口内容时把游戏窗口置于前台或用窗口句柄裁剪。
param(
    [string]$OutFile = (Join-Path $env:TEMP "civ6_snap.png")
)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save($OutFile, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "saved $OutFile ($($bounds.Width)x$($bounds.Height))"
