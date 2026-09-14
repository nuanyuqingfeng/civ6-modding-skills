# Verify a workshop item after upload using Steam API
param(
    [Parameter(Mandatory=$true)][string]$ItemId
)
$body = "itemcount=1&publishedfileids[0]=$ItemId"
try {
    $r = Invoke-RestMethod -Method Post -Uri "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/" -Body $body -TimeoutSec 30
} catch {
    Write-Error "Steam API request failed: $_"
    exit 1
}
$d = $r.response.publishedfiledetails[0]
if ($null -eq $d.title) {
    Write-Warning "Item $ItemId returned no public details (result may be private or not found)."
}
[pscustomobject]@{
    publishedfileid = $d.publishedfileid
    title           = $d.title
    visibility      = $d.visibility
    time_updated    = $d.time_updated
    hcontent_file   = $d.hcontent_file
    result          = $d.result
} | Format-List
