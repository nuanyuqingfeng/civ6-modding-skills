# Find workshop item IDs from local Steam logs
param(
    [string]$ModName = "",
    [string]$LogDir = "F:\Steam\logs"
)
if ($ModName -ne "") {
    $pattern = [regex]::Escape($ModName)
    Get-ChildItem -Path $LogDir -Filter "content_log*.txt" | ForEach-Object {
        $pat = "(\d+)\\" + $pattern + "\.modinfo"
        Select-String -Path $_.FullName -Pattern $pat | ForEach-Object {
            if ($_.Matches[0].Groups[1].Value) { $_.Matches[0].Groups[1].Value }
        }
    } | Sort-Object -Unique
} else {
    Get-ChildItem -Path $LogDir -Filter "workshop_log*.txt" | ForEach-Object {
        Select-String -Path $_.FullName -Pattern "Create new workshop item of type Community for AppID 289070 : (\d+) \(OK\)" | ForEach-Object {
            $_.Matches[0].Groups[1].Value
        }
    } | Sort-Object -Unique
}
