# 构建 Civ6 工坊上传工作区：content = 指向 Mods 副本的 junction（不物理复制 mod）
#
# 为什么要 junction：
#   1. 上传器要求 <ws>/content 是 mod 目录本身（UploadCommand.cs 硬编码），但它不关心
#      content 是不是链接 —— 实测 validate/upload 走 junction 与走真目录完全等价。
#   2. 一次 751 MB 的 Copy-Item 既慢又制造版本漂移窗口（复制完 Mods 又改了，工作区就是旧
#      版）；junction 下工作区与 Mods 恒等，零复制、零漂移。
#
# ★ 语义变化（必须知道）：strip_comments.py 是**就地写盘**的不可逆操作（没有 dry-run）。
#   因此 content 是 junction 时，剥离**直接改的就是 Mods 副本本体**，不是「改副本再回拷」。
#   二者最终状态相同（发布口径本就是「Mods 副本 == strip(源工程)」），但「就地」这个性质别忘。
#
# 用法：
#   powershell -File make_workspace.ps1 -ModDir <Mods/<ModName>> [-ItemId <工坊ID>]
#            [-WsRoot <工作区根>] [-Src <源工程>] [-NoStrip] [-Force] [-SkipValidate]
#   例：powershell -File make_workspace.ps1 -ModDir "D:/.../Mods/示例工程" -ItemId 1051125146 -Src "D:/.../示例工程/示例工程"
param(
    [Parameter(Mandatory=$true)][string]$ModDir,
    [string]$WsRoot  = "",
    [string]$ItemId  = "",
    [string]$Src     = "",
    [switch]$NoStrip,
    [switch]$Force,
    [switch]$SkipValidate
)

$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding($false)   # 无 BOM，与 skill 仓库既有文件一致

function Fail([string]$msg) { Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }
function Info([string]$msg) { Write-Host "[INFO] $msg" }
function Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }

function Get-SkillPath([string]$key) {
    $py = Join-Path $PSScriptRoot "../../tools/_paths.py"
    $py = [System.IO.Path]::GetFullPath($py)
    if (Test-Path $py) {
        try {
            $v = & python $py --tool $key 2>$null
            if ($LASTEXITCODE -eq 0 -and $v) { return $v.Trim() }
        } catch { }
    }
    return $null
}
function Get-WsRoot {
    if ($WsRoot) { return $WsRoot }
    # ws_root 是「待创建的目录」而非「已装好的工具」：不存在时 _paths.py --tool 会以 exit 1
    # 表示 MISSING（它走 must_exist 语义），此时退回同一默认值即可，取值完全一致。
    $r = Get-SkillPath "ws_root"
    if ($r) { return $r }
    return (Join-Path $env:TEMP "civ6-ws")
}

# ---------- 1. 规格化路径 ----------
if (-not (Test-Path $ModDir)) { Fail "Mods 副本目录不存在：$ModDir" }
$modDirFull = (Get-Item $ModDir).FullName
$modName = Split-Path $modDirFull -Leaf

$modinfo = Join-Path $modDirFull "$modName.modinfo"
if (-not (Test-Path $modinfo)) {
    $alt = Get-ChildItem $modDirFull -Filter "*.modinfo" -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($alt) { Warn "未找到 $modName.modinfo，改用 $($alt.Name)" }
    else { Fail "目录里没有 .modinfo：$modDirFull" }
}

$root = Get-WsRoot
$ws = Join-Path $root $modName
if (-not (Test-Path $ws)) { New-Item -ItemType Directory -Force -Path $ws | Out-Null }
$ws = (Get-Item $ws).FullName
$content = Join-Path $ws "content"
Info "工作区：$ws"
Info "Mods  ：$modDirFull"

# ---------- 2. 建立 junction ----------
# 幂等：已指向同一目标就跳过；指向别处 / 是普通目录都要先摘掉链路或旧副本再重建。
# ★ 摘链路一律用【不带 -Recurse】的 Remove-Item —— 对目录 junction 它只删链接本身，
#   绝不递归进目标。（实测即便 -Recurse 也不会跟进 junction，但不带 -Recurse 是零歧义写法。）
if (Test-Path $content) {
    $item = Get-Item $content -Force
    $isLink = [bool]$item.LinkType
    $target = @($item.Target)[0]

    if ($isLink -and $target -and ($target.TrimEnd("\") -ieq $modDirFull.TrimEnd("\"))) {
        Info "content 已是 -> $modDirFull 的 junction，跳过建链"
    }
    else {
        if (-not $isLink -and -not $Force) {
            Fail "content 是普通目录（本体可能就在里面！）：$content"
            Fail "  确认它只是旧的物理复制后，加 -Force 替换为 junction。"
        }
        if ($isLink) { Warn "content 原指向 $target，改指向 $modDirFull" }
        else { Warn "content 是普通目录，按 -Force 移除（若里面是 mod 本体，请先移走）" }
        if ($isLink) { Remove-Item $content -Force }
        else { Remove-Item $content -Recurse -Force }
        New-Item -ItemType Junction -Path $content -Target $modDirFull | Out-Null
        Info "已建 junction：content -> $modDirFull"
    }
}
else {
    New-Item -ItemType Junction -Path $content -Target $modDirFull | Out-Null
    Info "已建 junction：content -> $modDirFull"
}

# 任何清理脚本都必须能认出这是链接（cleanup.ps1 的守卫依赖同一判据）
if (-not (Get-Item $content -Force).LinkType) { Fail "content 建链后仍不是 reparse point，中止" }

# ---------- 3. workshop.json ----------
# 只写 changeNote：省略的字段上传器不触碰（release.md Hard Rules ④）。
$jsonPath = Join-Path $ws "workshop.json"
if (Test-Path $jsonPath) {
    Info "workshop.json 已存在，保留不动（内容如下，确认是想要的更新说明）"
    Get-Content $jsonPath -Raw -Encoding UTF8 | Write-Host
}
else {
    $note = "Update content ({0})" -f (Get-Date -Format "yyyy-MM-dd")
    [System.IO.File]::WriteAllText($jsonPath, ("{{""changeNote"": ""{0}""}}" -f $note), $utf8)
    Info "已写 workshop.json：changeNote = $note"
}

# ---------- 4. mod_id.txt ----------
# 缺失 = upload 会【另建一个新条目】（最贵的失误），所以这一步刻意做成硬门。
$idPath = Join-Path $ws "mod_id.txt"
if ($ItemId) {
    [System.IO.File]::WriteAllText($idPath, $ItemId.Trim(), $utf8)
    Info "已写 mod_id.txt = $($ItemId.Trim())（来自 -ItemId）"
}
elseif (Test-Path $idPath) {
    Info "mod_id.txt 已存在 = $((Get-Content $idPath -Raw).Trim())"
}
else {
    Warn "没有 mod_id.txt 且未给 -ItemId -> upload 会【新建条目】！"
    Warn "  更新已有条目：从 workshop-ledger.md 取 ID 后重跑本脚本并加 -ItemId <ID>"
}

# ---------- 5. 剥离注释（就地作用于 Mods 副本，见文件头说明） ----------
if ($NoStrip) {
    Warn "已指定 -NoStrip：跳过剥离。发布前必须补跑，否则工坊包会带内部注释。"
}
else {
    $strip = Join-Path $PSScriptRoot "../../tools/strip_comments.py"
    $strip = [System.IO.Path]::GetFullPath($strip)
    if (-not (Test-Path $strip)) { Fail "找不到 strip_comments.py：$strip" }
    Info "剥离注释（就地写盘，改的是 Mods 副本本体）..."
    if ($Src) { & python $strip $modDirFull --src $Src }
    else {
        Warn "未给 -Src：只剥离，不做「Mods == strip(源工程)」核对（建议补 -Src <源工程>）"
        & python $strip $modDirFull
    }
    if ($LASTEXITCODE -ne 0) { Fail "剥离失败（exit $LASTEXITCODE）" }
}

# ---------- 6. 预览图提示 ----------
if (-not (Test-Path (Join-Path $ws "image.png"))) {
    Info "无 image.png -> 不改线上预览图（要放图见 release.md 3.2 节）"
}

# ---------- 7. validate（建议性；硬门仍是 verify_mod_package.py） ----------
if ($SkipValidate) { Warn "已指定 -SkipValidate，跳过 validate" }
else {
    $exe = Get-SkillPath "uploader"
    if (-not $exe) { Warn "未解析到 uploader 路径（tools/_paths.py 的 uploader 键），跳过 validate" }
    elseif (-not (Test-Path $exe)) { Warn "uploader 不存在：$exe，跳过 validate" }
    else {
        Info "validate..."
        & $exe validate -w $ws
        $code = $LASTEXITCODE
        # 0=通过；2=提示级（上传器的 validate 是 advisory，「引用了不存在的文件」也只判 2）；
        # 1=硬错误（缺 workshop.json / 参数错 / SteamAPI 初始化失败）。
        if ($code -eq 0) { Info "validate 通过" }
        elseif ($code -eq 2) { Warn "validate exit 2（提示级，不阻断）—— 逐条看上面的输出再决定" }
        else { Fail "validate exit $code（硬错误，必须先修）" }
    }
}

Write-Host ""
Write-Host "工作区就绪：$ws" -ForegroundColor Green
Write-Host ("上传：  powershell -File upload.ps1   -Workspace ""{0}"" -TimeoutSeconds 1800" -f $ws)
Write-Host "验证：  powershell -File verify.ps1   -ItemId <id>"
Write-Host ("清理：  powershell -File cleanup.ps1  -Workspace ""{0}""   # 仅真成功后" -f $ws)
exit 0
