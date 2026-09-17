# Build non-trimmed Civ6WorkshopUploader
param(
    [string]$Source = "$env:USERPROFILE\AppData\Local\Temp\Civ6WorkshopUploader",
    [string]$ArtifactsPath = "artifacts"
)
if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
    exit 1
}
Push-Location $Source
try {
    dotnet publish -c Release -r win-x64 --artifacts-path $ArtifactsPath
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Build OK. Publish output under $ArtifactsPath\publish\Civ6WorkshopUploader\release_win-x64"
} finally {
    Pop-Location
}
