# Upload/update a Civ6 workshop workspace
param(
    [Parameter(Mandatory=$true)][string]$Workspace,
    [int]$TimeoutSeconds = 1800,
    [string]$Tool = "D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe",
    [string]$LogDir = ""
)
if (-not (Test-Path $Tool)) { Write-Error "Tool not found: $Tool"; exit 1 }
if (-not (Test-Path $Workspace)) { Write-Error "Workspace not found: $Workspace"; exit 1 }
if ($LogDir -eq "") { $LogDir = Join-Path (Split-Path $Tool -Parent) "logs" }
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $LogDir "upload-$stamp.log"
$err = Join-Path $LogDir "upload-$stamp.err.log"
$args = @('upload','-w',$Workspace)
$p = Start-Process -FilePath $Tool -ArgumentList $args -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError $err -PassThru
if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
    try { $p.Kill() } catch {}
    Write-Error "Upload timed out after ${TimeoutSeconds}s. Log: $log"
    exit 124
}
$code = $p.ExitCode
Write-Host "Exit code: $code"
Write-Host "Log: $log"
if (Test-Path $err) {
    $errText = Get-Content $err -Raw -ErrorAction SilentlyContinue
    if ($errText) { Write-Host "STDERR:"; Write-Host $errText }
}
exit $code
