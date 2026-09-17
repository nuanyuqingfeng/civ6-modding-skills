param(
    [string]$To = "$env:USERPROFILE\Civ6WorkshopUploader",
    [string]$Repo = "https://github.com/Jianbao233/Civ6WorkshopUploader",
    [switch]$Confirmed,
    [switch]$SkipBuild
)
# ensure_uploader.ps1 —— 工坊上传器的"自适应保障"（与音频模板 ensure_template.py 同口径）
#
# 背景：Civ6WorkshopUploader 是第三方工具（作者 Jianbao233，MIT），**不随本 skill 分发**。
#   与上游逐字节同版（本机实测：commit e7dc27a，无本地改动）。
# 本脚本：① 检查本机是否已有可用工具；② 缺则询问后从上游 clone 并构建（非 Trimmed）；
#         ③ 组装 tool\ 目录（exe + steam_api64.dll + steam_appid.txt + template\）并打印路径。
#
# 用法:
#   powershell -File ensure_uploader.ps1                 # 只检查，缺就提示（exit 2）
#   powershell -File ensure_uploader.ps1 -Confirmed      # 允许联网 clone + 构建
#   powershell -File ensure_uploader.ps1 -Confirmed -To "D:\tools\Civ6WorkshopUploader"
#
# 依赖：git；构建需 .NET SDK（dotnet）。构建产物路径：
#   <To>\artifacts\publish\Civ6WorkshopUploader\release_win-x64\Civ6WorkshopUploader.exe
#
# 注意：不要加 -p:PublishTrimmed=true（会卡在 PreparingContent）。

$ErrorActionPreference = "Continue"

function Find-Existing {
    $cands = @(
        (Join-Path $To "tool\Civ6WorkshopUploader.exe"),
        (Join-Path $To "artifacts\publish\Civ6WorkshopUploader\release_win-x64\Civ6WorkshopUploader.exe")
    )
    foreach ($c in $cands) { if (Test-Path -LiteralPath $c) { return $c } }
    $cmd = Get-Command Civ6WorkshopUploader.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$exe = Find-Existing
if ($exe) {
    Write-Output "[OK] 已找到上传器: $exe"
    Write-Output ('     在 civ6-modding/local_paths.json 里写： {"uploader": "' + $exe + '"}')
    exit 0
}

Write-Output "[ASK] 未找到 Civ6WorkshopUploader.exe（第三方工具，不随 skill 分发）。"
Write-Output "      上游：$Repo"
Write-Output "      允许后将从上游 clone 并构建：powershell -File ensure_uploader.ps1 -Confirmed"
if (-not $Confirmed) { exit 2 }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 git。请安装 git 后重试，或手动 clone $Repo 并按 release.md 构建。"
    exit 1
}
if (-not $SkipBuild -and -not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 dotnet（.NET SDK）。构建需要它；或加 -SkipBuild 只取源码。"
    exit 1
}

$src = Join-Path $To "src_repo"
if (Test-Path -LiteralPath $src) { Remove-Item -LiteralPath $src -Recurse -Force }
Write-Output "[1/3] clone $Repo -> $src"
git clone --depth 1 $Repo $src
if ($LASTEXITCODE -ne 0) { Write-Error "git clone 失败（检查网络/代理）"; exit 1 }

if ($SkipBuild) {
    Write-Output "[DONE] 仅取到源码：$src（自行构建，见 release.md）"
    exit 0
}

Write-Output "[2/3] dotnet publish（非 Trimmed）"
Push-Location $src
dotnet publish -c Release -r win-x64
$rc = $LASTEXITCODE
Pop-Location
if ($rc -ne 0) { Write-Error "dotnet publish 失败（rc=$rc）"; exit 1 }

$pub = Join-Path $src "artifacts\publish\Civ6WorkshopUploader\release_win-x64"
if (-not (Test-Path -LiteralPath (Join-Path $pub "Civ6WorkshopUploader.exe"))) {
    $found = Get-ChildItem -Path (Join-Path $src "artifacts") -Recurse -Filter "Civ6WorkshopUploader.exe" -ErrorAction SilentlyContinue |
             Select-Object -First 1
    if ($found) { $pub = $found.DirectoryName } else { Write-Error "未找到构建产物（检查 csproj/global.json）"; exit 1 }
}

Write-Output "[3/3] 组装 tool 目录"
$tool = Join-Path $To "tool"
New-Item -ItemType Directory -Path $tool -Force | Out-Null
Copy-Item (Join-Path $pub "*") $tool -Recurse -Force
foreach ($f in @("steam_api64.dll", "steam_appid.txt")) {
    $s = Join-Path $src "steam\$f"
    if (Test-Path -LiteralPath $s) { Copy-Item $s $tool -Force }
}
$tpl = Join-Path $src "template"
if (Test-Path -LiteralPath $tpl) { Copy-Item $tpl $tool -Recurse -Force }

$exe = Join-Path $tool "Civ6WorkshopUploader.exe"
Write-Output "[DONE] 上传器就位: $exe"
Write-Output ('       在 civ6-modding/local_paths.json 里写： {"uploader": "' + $exe + '"}')
Write-Output "       上游许可：见 $src\LICENSE（MIT，作者 Jianbao233）"
