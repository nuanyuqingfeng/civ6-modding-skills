param(
    [Parameter(Mandatory = $true)][string]$Subject,
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$SdDir = "",
    [string]$Magick = "",
    [int]$Seed = 42
)
# Civ6 白色扁平图标管线（v2 阈值版）：
#   本地扩散模型生成黑底白实心剪影 -> 灰度阈值二值化 -> 黑色转透明 -> 裁边
#
# 依赖（都不随本 skill 分发，需自备）：
#   - stable-diffusion.cpp 的 sd-cli.exe + FLUX.2-klein-4B 权重（Apache-2.0 模型）
#   - ImageMagick 的 magick.exe
# 路径解析：-SdDir / -Magick 参数 > 环境变量 SD_CPP / MAGICK > 常见安装位置。
#
# 用法:
#   powershell -File make-icon.ps1 -Subject "a lighthouse" -Out "D:\out\icon.png" [-Seed 42]
#   powershell -File make-icon.ps1 -Subject "a sword" -Out out.png -SdDir "D:\sd-cpp"

# 注意：不要设 $ErrorActionPreference = "Stop" —— sd-cli.exe 把进度写到 stderr，
# 在 Stop 偏好下会被当成终止性错误，导致生成中断（实测踩过）。

if (-not $SdDir) { $SdDir = $env:SD_CPP }
if (-not $SdDir) {
    foreach ($c in @("$env:USERPROFILE\sd-cpp", "D:\sd-cpp", "C:\sd-cpp")) {
        if (Test-Path -LiteralPath (Join-Path $c "sd-cli.exe") -ErrorAction SilentlyContinue) { $SdDir = $c; break }
    }
}
$sdCli = ""
if ($SdDir) { try { $sdCli = Join-Path $SdDir "sd-cli.exe" } catch { $sdCli = "" } }
if (-not $sdCli -or -not (Test-Path -LiteralPath $sdCli -ErrorAction SilentlyContinue)) {
    Write-Error ("找不到 sd-cli.exe（stable-diffusion.cpp）。`n" +
        "  用 -SdDir <目录> 指定，或设环境变量 SD_CPP。`n" +
        "  目录里应含 sd-cli.exe 与 models\flux2-klein4b\{flux-2-klein-4b-Q4_0.gguf, vae_small_decoder.safetensors, qwen3-4b-Q4_K_M.gguf}。`n" +
        "  获取方式见 stable-diffusion.cpp 的 README（模型 FLUX.2-klein-4B 为 Apache-2.0）。")
    exit 1
}

if (-not $Magick) { $Magick = $env:MAGICK }
if (-not $Magick) {
    $cmd = Get-Command magick.exe -ErrorAction SilentlyContinue
    if ($cmd) { $Magick = $cmd.Source }
}
if (-not $Magick) {
    $cand = Get-ChildItem "$env:ProgramFiles\ImageMagick*" -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending | Select-Object -First 1
    if ($cand) { $Magick = Join-Path $cand.FullName "magick.exe" }
}
if (-not $Magick -or -not (Test-Path -LiteralPath $Magick -ErrorAction SilentlyContinue)) {
    Write-Error "找不到 magick.exe（ImageMagick）。用 -Magick <路径> 指定，或设环境变量 MAGICK。"
    exit 1
}

$models = Join-Path $SdDir "models\flux2-klein4b"
$tmp = Join-Path $env:TEMP "flux_icon_raw.png"

$prompt = "a solid white filled silhouette of $Subject, completely filled solid shape, no outline, no line art, no drawing, flat game icon style, pure white on pure black background"

& (Join-Path $SdDir "sd-cli.exe") --diffusion-model "$models\flux-2-klein-4b-Q4_0.gguf" `
    --vae "$models\vae_small_decoder.safetensors" `
    --llm "$models\qwen3-4b-Q4_K_M.gguf" `
    -p $prompt --cfg-scale 1.0 --steps 4 -H 512 -W 512 `
    --diffusion-fa --offload-to-cpu --seed $Seed -o $tmp 2>&1 | Select-String 'generate_image completed' | Out-Null
if (-not (Test-Path $tmp)) { Write-Error "生成失败（可能是显存不足，可调低模型量化或加大 --offload-to-cpu）"; exit 1 }
& $Magick $tmp -colorspace Gray -threshold 45% -transparent black -trim +repage $Out
Remove-Item $tmp -ErrorAction SilentlyContinue
$info = & $Magick $Out -format "%wx%h" info:
$cols = & $Magick $Out -format "%k" info:
Write-Output "saved: $Out (${info}, $cols 色, 透明背景白色实心图标)"
