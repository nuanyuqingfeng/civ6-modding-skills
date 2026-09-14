# Validate a Civ6 upload workspace before upload
param(
    [Parameter(Mandatory=$true)][string]$Workspace,
    [string]$Tool = "D:\documents\Civ6WorkshopUploader\tool\Civ6WorkshopUploader.exe"
)
if (-not (Test-Path $Tool)) { Write-Error "Tool not found: $Tool"; exit 1 }
& $Tool validate -w $Workspace
exit $LASTEXITCODE
