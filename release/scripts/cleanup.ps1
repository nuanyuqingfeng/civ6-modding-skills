# Remove a temporary Civ6 workshop upload workspace after a VERIFIED successful upload.
# Safety: only deletes paths strictly under $env:TEMP\Civ6WorkshopUploader\.
# Never touches the Mods source dir or D:\documents\Civ6WorkshopUploader.
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
Remove-Item $full -Recurse -Force
Write-Host "已删除临时 workspace：$full"
