# Resolve a Civ6 workshop item id for a mod name.
# Sources, in order:
#   1 account workshop list (steamcommunity profile page, appid 289070) - titles matched against the mod name
#   2 project ledger <p1>/<project>/<mod>/workshop-ledger.md
#   3 Steam content_log*.txt "<id>/<mod>.modinfo"
# Exit 1 when nothing is found: ask the user for the id.
# Never run 'new' on a workspace to discover an id (that publishes a duplicate item).
param(
    [string]$ModName = "",
    [string]$SteamId = "",
    [string]$Proxy = "http://127.0.0.1:7897",
    [string]$P1Root = "",
    [string]$LogDir = "",
    [switch]$Account
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Get-P1Root {
    param([string]$Given)
    if ($Given) { return $Given }
    $py = Join-Path $PSScriptRoot "../../tools/_paths.py"
    $py = [System.IO.Path]::GetFullPath($py)
    if (Test-Path $py) {
        $v = & python $py --tool p1 2>$null
        if ($LASTEXITCODE -eq 0 -and $v) { return $v.Trim() }
    }
    return "D:\documents\Firaxis ModBuddy\Civilization VI"
}

function Get-SteamIdFromLogs {
    $candidates = @("D:\documents\Civ6WorkshopUploader\tool\logs") + @($script:LogDir)
    foreach ($dir in $candidates) {
        if (-not $dir -or -not (Test-Path -LiteralPath $dir)) { continue }
        $files = @(Get-ChildItem -LiteralPath $dir -Filter "*.err.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
        foreach ($file in $files) {
            $m = Select-String -LiteralPath $file.FullName -Pattern "Caching Steam ID:\s*(\d{17})" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($m) { return $m.Matches[0].Groups[1].Value }
        }
    }
    return ""
}

function Get-Html {
    param([string]$Url, [string]$ProxyUrl)
    foreach ($p in @($ProxyUrl, "")) {
        try {
            if ($p) { $r = Invoke-WebRequest -Uri $Url -Proxy $p -UseBasicParsing -TimeoutSec 30 -UserAgent "Mozilla/5.0" }
            else { $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30 -UserAgent "Mozilla/5.0" }
            if ($r -and $r.Content) { return $r.Content }
        } catch { }
    }
    return $null
}

function Convert-HtmlText {
    param([string]$Text)
    return $Text.Replace("&amp;", "&").Replace("&quot;", '"').Replace("&#39;", "'").Replace("&lt;", "<").Replace("&gt;", ">")
}

function Get-AccountItems {
    param([string]$Id, [string]$ProxyUrl)
    if (-not $Id) { return @() }
    $items = @()
    for ($page = 1; $page -le 10; $page++) {
        $url = "https://steamcommunity.com/profiles/$Id/myworkshopfiles/?appid=289070&p=$page"
        $html = Get-Html -Url $url -ProxyUrl $ProxyUrl
        if (-not $html) { break }
        $found = 0
        foreach ($m in [regex]::Matches($html, 'data-publishedfileid="(\d+)"[\s\S]{0,1200}?workshopItemTitle[^>]*>([^<]*)<')) {
            $items += [pscustomobject]@{ Id = $m.Groups[1].Value; Title = (Convert-HtmlText $m.Groups[2].Value).Trim() }
            $found++
        }
        if ($found -eq 0) { break }
        $total = 0
        if ($html -match 'Showing \d+-\d+ of (\d+)') { $total = [int]$Matches[1] }
        if ($total -gt 0 -and $items.Count -ge $total) { break }
    }
    return @($items | Sort-Object Id -Unique)
}

function Get-TitleScore {
    param([string]$Title, [string]$Name)
    if (-not $Title -or -not $Name) { return 0 }
    $t = $Title.ToLower()
    $score = 0
    foreach ($tok in ($Name.ToLower() -split '[^a-z0-9]+')) {
        if ($tok.Length -ge 3 -and $t.Contains($tok)) { $score++ }
    }
    return $score
}

function Read-LedgerIds {
    param([string]$Path)
    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $ids = @()
    foreach ($m in [regex]::Matches($text, 'filedetails/\?id=(\d{6,12})')) { $ids += $m.Groups[1].Value }
    foreach ($m in [regex]::Matches($text, '\u6761\u76EE\s*ID[\s\uFF1A:]*`?(\d{9,12})`?')) { $ids += $m.Groups[1].Value }
    return @($ids | Sort-Object -Unique)
}

$p1 = Get-P1Root $P1Root
if (-not $LogDir) { $LogDir = "F:\Steam\logs" }
$rows = @()

# 1 account workshop list (authoritative: the account owns every item below)
if (-not $SteamId) { $SteamId = Get-SteamIdFromLogs }
$acctItems = Get-AccountItems -Id $SteamId -ProxyUrl $Proxy
if ($acctItems.Count -eq 0) {
    [Console]::Error.WriteLine("WARN: account workshop list unavailable (steamid='$SteamId'); falling back to ledger and Steam logs.")
}
foreach ($it in $acctItems) {
    $score = 0
    if ($ModName) { $score = Get-TitleScore -Title $it.Title -Name $ModName }
    if ($Account -or (-not $ModName) -or $score -gt 0) {
        $rows += [pscustomobject]@{ Id = $it.Id; Score = $score; Weight = 3; Source = "account"; Title = $it.Title }
    }
}
if ($Account -or -not $ModName) {
    $rows | Sort-Object Id | ForEach-Object { "{0}`t{1}`t{2}" -f $_.Id, $_.Source, $_.Title }
    exit 0
}

# 2 project ledger
if ($ModName) {
    $candidates = @()
    $candidates += (Join-Path $p1 "$ModName\$ModName\workshop-ledger.md")
    Get-ChildItem -Path $p1 -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $candidates += (Join-Path $_.FullName "$ModName\workshop-ledger.md")
    }
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) {
            foreach ($id in Read-LedgerIds $c) { $rows += [pscustomobject]@{ Id = $id; Score = 0; Weight = 2; Source = "ledger"; Title = $c } }
        }
    }
}

# 3 Steam content logs
if ($rows.Count -eq 0 -and $ModName -and (Test-Path -LiteralPath $LogDir)) {
    $pattern = [regex]::Escape($ModName)
    Get-ChildItem -Path $LogDir -Filter "content_log*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
        Select-String -Path $_.FullName -Pattern ("(\d+)\\" + $pattern + "\.modinfo") -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.Matches[0].Groups[1].Value) { $rows += [pscustomobject]@{ Id = $_.Matches[0].Groups[1].Value; Score = 0; Weight = 1; Source = "steam log"; Title = $_.Path } }
        }
    }
}

if (-not $rows) {
    [Console]::Error.WriteLine("No workshop item resolved for '$ModName' (steamid='$SteamId', account items=$($acctItems.Count), p1='$p1').")
    [Console]::Error.WriteLine("List the account items with: find_item_id.ps1 -Account")
    [Console]::Error.WriteLine("Ask the user for the id; do not run 'new' to probe it.")
    exit 1
}
$best = @{}
foreach ($r in $rows) {
    $cur = $best[$r.Id]
    if (-not $cur -or $r.Score -gt $cur.Score -or ($r.Score -eq $cur.Score -and $r.Weight -gt $cur.Weight)) { $best[$r.Id] = $r }
}
$best.Values | Sort-Object -Property @{Expression={$_.Score};Descending=$true}, @{Expression={$_.Weight};Descending=$true}, @{Expression={[long]$_.Id};Descending=$false} | ForEach-Object { "{0}`t{1}`t{2}" -f $_.Id, $_.Source, $_.Title }
exit 0
