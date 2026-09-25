# Remove a temporary Civ6 workshop upload workspace after a VERIFIED successful upload.
# Safety: only deletes paths strictly under $env:TEMP\civ6-ws\ (see $root below).
# Never touches the Mods source dir or D:\documents\Civ6WorkshopUploader.
#
# content 通常是「指向 Mods 副本的 junction」（见 make_workspace.ps1），因此这里有三重守卫：
#   ① 路径必须严格位于 $root\ 之下；
#   ② 工作区自身绝不能是 reparse point（否则删的就是别处）；
#   ③ 先单独摘掉内部所有链接，再递归删除 —— 链接只删链、不跟进目标。
# 实测 Remove-Item -Recurse 本身就不会跟进 junction（PS 5.1 与 7.6 均验证目标存活），
# 守卫 ③ 是纵深防御：无论 PowerShell 版本与未来改动如何，都不可能碰到 Mods。
param(
    [Parameter(Mandatory=$true)][string]$Workspace
)

$root = (Join-Path $env:TEMP "civ6-ws").TrimEnd('\')
$full = $Workspace.TrimEnd('\')

if (-not $full.StartsWith($root + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Error "拒绝删除：$full 不在临时工作区根 $root\ 之下"
    exit 1
}
if (-not (Test-Path $full)) {
    Write-Warning "workspace 不存在，无需清理：$full"
    exit 0
}

# 守卫 ②：工作区自身必须是普通目录
$self = Get-Item $full -Force
if ($self.LinkType) {
    Write-Error "拒绝删除：$full 本身是 $($self.LinkType)（指向 $($self.Target -join ', ')），不是普通目录"
    exit 1
}

# 守卫 ③：先摘链（只删链接本身，不跟进目标），再整体递归删除
$links = @(Get-ChildItem $full -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.LinkType })
foreach ($l in $links) {
    try {
        # 子项枚举出的 FileSystemInfo 其 .Target 可能未填充，重新 Get-Item 取准确值
        $tgt = @((Get-Item $l.FullName -Force).Target) -join ', '
        Remove-Item $l.FullName -Force        # 目录 junction 不带 -Recurse = 只摘链
        Write-Host "已摘除链接：$($l.FullName) -> $tgt"
    } catch {
        Write-Error "摘除链接失败，中止以免误删目标：$($l.FullName) —— $($_.Exception.Message)"
        exit 1
    }
}

Remove-Item $full -Recurse -Force
Write-Host "已删除临时 workspace：$full"
