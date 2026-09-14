# convert_art.ps1 — Civ6 素材通用转换器（读 art_manifest.json 执行）
# 用法:
#   pwsh -File convert_art.ps1 [-Manifest <path>] [-ProjectRoot <path>]
# 行为:
#   1. 读 manifest（entries: tech/role/source），role 决定尺寸：
#      19 类图标 role 各有内置尺寸表（civ_icon=13 尺寸、leader_icon=8 尺寸等，
#      完整表见 art-pipeline.md「图标尺寸规格全表」），非图标 role = 原尺寸单 DDS
#      多图网格图集走 atlasEntries，由 make_atlas.py 处理（本脚本只管单图）
#   2. texconv 转 PNG -> DDS(R8G8B8A8_UNORM) 输出 Textures\，重命名为技术名
#   3. 写 asset_map.json（tech -> 源文件 basename，与既有内容合并不覆盖），供 gen_tex.py 解析源路径
#   4. 调 gen_tex.py 为每个 DDS 生成 .tex（系统 ANSI 代码页写出）
# 缺图跳过不报错；全部转换完成后打印 DDS/TEX 计数。
param(
    [string]$Manifest = "",
    [string]$ProjectRoot = ""
)
$ErrorActionPreference = "Stop"

if (-not $Manifest) { $Manifest = Join-Path (Get-Location).Path "art_manifest.json" }
if (-not (Test-Path -LiteralPath $Manifest)) { throw "manifest not found: $Manifest" }
$cfg = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json

# --- 解析各目录 ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$GenTex = Join-Path $scriptDir "gen_tex.py"
$root = if ($ProjectRoot) { $ProjectRoot } elseif ($cfg.projectRoot) { $cfg.projectRoot } else { Split-Path -Parent (Resolve-Path -LiteralPath $Manifest).Path }

$TexturesDir = $cfg.texturesDir
if (-not $TexturesDir) {
    $sln = Get-ChildItem -LiteralPath $root -Filter "*.civ6sln" -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($sln) { $modName = $sln.BaseName } else {
        $proj = Get-ChildItem -LiteralPath $root -Filter "*.civ6proj" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($proj) { $modName = $proj.Directory.Name } else { throw "cannot detect ModName: no .civ6sln/.civ6proj under $root (set texturesDir in manifest)" }
    }
    $TexturesDir = Join-Path $root "$modName\Textures"
}
$AssetsDir = if ($cfg.assetsDir) { $cfg.assetsDir } else { Join-Path $root ".assets" }
$null = New-Item -ItemType Directory -Force $TexturesDir
$Staging = Join-Path $env:TEMP ("texconv_staging_" + [guid]::NewGuid().ToString("N").Substring(0,8))
$null = New-Item -ItemType Directory -Force $Staging

# --- role -> 尺寸表（来源：Civ6 Modding Assistant 1.6.3 iconsize_data 反编译表，
#     已与本项目 Atlas_Rgn 成品实测对齐；图标每张即最终分辨率，-m 1 单 mip）---
$CivIconSizes        = @(22, 30, 32, 36, 44, 45, 48, 50, 64, 80, 128, 200, 256)
$LeaderIconSizes     = @(32, 45, 48, 50, 55, 64, 80, 256)
$BuildingIconSizes   = @(32, 38, 50, 80, 128, 256)
$CitystateIconSizes  = @(22, 30, 32, 36, 40, 44, 48, 64, 68, 80, 256)
$CivicIconSizes      = @(38, 42, 128, 160)
$DistrictIconSizes   = @(22, 32, 38, 50, 80, 128, 256)
$FeatureIconSizes    = @(50, 64, 256)
$GovernmentIconSizes = @(32, 50)
$GreatworkIconSizes  = @(45, 64, 256)
$ImprovementIconSizes = @(38, 50, 80, 256)
$PolicyIconSizes     = @(32, 38, 50, 256)
$ProjectIconSizes    = @(30, 32, 38, 50, 70, 80, 256)
$ResourceIconSizes   = @(38, 50, 64, 256)
$StatIconSizes       = @(16, 22, 32, 45, 55)
$TechIconSizes       = @(30, 38, 42, 128, 160)
$UnitActionIconSizes = @(38, 50, 80, 256)
$UnitPortraitSizes   = @(38, 50, 70, 95, 200, 256)
$UnitIconSizes       = @(22, 32, 38, 50, 80, 256)
$VictoryIconSizes    = @(64, 80, 130, 220)
$WonderIconSizes     = @(32, 38, 50, 64, 128, 256)
function Get-Sizes([string]$role) {
    switch ($role) {
        "civ_icon"          { return $CivIconSizes }
        "leader_icon"       { return $LeaderIconSizes }
        "building_icon"     { return $BuildingIconSizes }
        "citystate_icon"    { return $CitystateIconSizes }
        "civic_icon"        { return $CivicIconSizes }
        "district_icon"     { return $DistrictIconSizes }
        "feature_icon"      { return $FeatureIconSizes }
        "government_icon"   { return $GovernmentIconSizes }
        "greatwork_icon"    { return $GreatworkIconSizes }
        "improvement_icon"  { return $ImprovementIconSizes }
        "policy_icon"       { return $PolicyIconSizes }
        "project_icon"      { return $ProjectIconSizes }
        "resource_icon"     { return $ResourceIconSizes }
        "stat_icon"         { return $StatIconSizes }
        "tech_icon"         { return $TechIconSizes }
        "unit_action_icon"  { return $UnitActionIconSizes }
        "unit_portrait"     { return $UnitPortraitSizes }
        "unit_icon"         { return $UnitIconSizes }
        "victory_icon"      { return $VictoryIconSizes }
        "wonder_icon"       { return $WonderIconSizes }
        # loyalty_3d / loyalty_sv：原尺寸单 DDS（尺寸已由 civ6-loyalty-icon 管线固定）
        # fow：FOW 迷雾变体原尺寸单 DDS（源图由 apply_fow.py 生成，尺寸同普通版）
        default             { return @() }   # 原尺寸单输出
    }
}

# --- texconv 自检（winget 安装后当前会话 PATH 不刷新，补探测 WinGet Links 目录）---
function Find-Texconv {
    if (Get-Command "texconv" -ErrorAction SilentlyContinue) { return "texconv" }
    $links = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\texconv.exe"
    if (Test-Path $links) { return $links }
    $pkg = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "texconv.exe" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pkg) { return $pkg.FullName }
    return $null
}
$Texconv = Find-Texconv
if (-not $Texconv) {
    Write-Host "texconv not found; installing via winget..." -ForegroundColor Yellow
    winget install Microsoft.DirectXTex.Texconv --accept-source-agreements --accept-package-agreements
    $Texconv = Find-Texconv
    if (-not $Texconv) { throw "texconv installed but not found; open a new shell and rerun." }
}

# --- python 解析 ---
$PythonCmd = $null
foreach ($c in @("python", "python3", "py")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $PythonCmd = $c; break }
}

# --- 转换 ---
$assetMap = [ordered]@{}
$ok = 0; $skip = 0
foreach ($e in $cfg.entries) {
    $src = if ([System.IO.Path]::IsPathRooted($e.source)) { $e.source } else { Join-Path $AssetsDir $e.source }
    if (-not (Test-Path -LiteralPath $src)) { Write-Host "  skip (missing): $($e.tech) <- $src"; $skip++; continue }
    $srcBase = [System.IO.Path]::GetFileNameWithoutExtension($src)
    $assetMap[$e.tech] = $srcBase

    $sizes = Get-Sizes $e.role
    if ($sizes.Count -eq 0) {
        & $Texconv -y $src -f R8G8B8A8_UNORM -m 1 -o $Staging 2>&1 | Out-Null
        Move-Item -Force (Join-Path $Staging "$srcBase.dds") (Join-Path $TexturesDir "$($e.tech).dds")
        Write-Host "  ok: $($e.tech).dds"
        $ok++
    } else {
        foreach ($s in $sizes) {
            & $Texconv -y $src -o $Staging -f R8G8B8A8_UNORM -m 1 --suffix "_$s" -w $s -h $s 2>&1 | Out-Null
            Move-Item -Force (Join-Path $Staging "${srcBase}_$s.dds") (Join-Path $TexturesDir "$($e.tech)_$s.dds")
        }
        Write-Host "  ok: $($e.tech) x$($sizes.Count) sizes"
        $ok++
    }
}

# --- asset_map.json + gen_tex ---
# 合并而非覆盖：保留 make_atlas.py 写入的图集条目（键 = gen_tex 的 base 规则）
$mapPath = Join-Path (Split-Path -Parent (Resolve-Path -LiteralPath $Manifest).Path) "asset_map.json"
$existingMap = [ordered]@{}
if (Test-Path -LiteralPath $mapPath) {
    try {
        (Get-Content -LiteralPath $mapPath -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties | ForEach-Object {
            $existingMap[$_.Name] = $_.Value
        }
    } catch { }
}
foreach ($k in $assetMap.Keys) { $existingMap[$k] = $assetMap[$k] }
$existingMap | ConvertTo-Json | Set-Content -LiteralPath $mapPath -Encoding UTF8

if ($PythonCmd) {
    & $PythonCmd $GenTex $TexturesDir $AssetsDir $mapPath
} else {
    Write-Warning "python not found; skipped .tex generation (DDS done)"
}

Remove-Item -Recurse -Force $Staging -ErrorAction SilentlyContinue
$dds = (Get-ChildItem $TexturesDir -Filter "*.dds" -File).Count
$tex = (Get-ChildItem $TexturesDir -Filter "*.tex" -File).Count
Write-Host "`nDone. entries ok=$ok skip=$skip | Textures: DDS=$dds TEX=$tex" -ForegroundColor Green
