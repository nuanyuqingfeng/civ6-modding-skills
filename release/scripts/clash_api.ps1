# Clash Verge named-pipe API helper (returns raw HTTP response)
# Usage:
#   powershell -File clash_api.ps1 -Method GET -Path "/proxies" -OutFile "resp.txt"
#   powershell -File clash_api.ps1 -Method PUT -Path "/proxies/GLOBAL" -Body '{"name":"node"}' -OutFile "resp.txt"
param(
    [string]$Method = 'GET',
    [string]$Path = '/proxies',
    [string]$Body = '',
    [string]$OutFile = ''
)
$pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "verge-mihomo", [System.IO.Pipes.PipeDirection]::InOut, [System.IO.Pipes.PipeOptions]::None)
try {
    $pipe.Connect(5000)
    $sw = New-Object System.IO.StreamWriter($pipe)
    $sw.AutoFlush = $true
    $req = "$Method $Path HTTP/1.1`r`nHost: localhost`r`nAuthorization: Bearer set-your-secret`r`nConnection: close`r`n"
    if ($Body -ne '') {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Body)
        $req += "Content-Type: application/json`r`nContent-Length: $($bytes.Length)`r`n"
    }
    $req += "`r`n"
    if ($Body -ne '') { $req += $Body }
    $sw.Write($req)
    $pipe.Flush()
    $sr = New-Object System.IO.StreamReader($pipe, [System.Text.Encoding]::UTF8)
    $resp = $sr.ReadToEnd()
    if ($OutFile -ne '') {
        [System.IO.File]::WriteAllText($OutFile, $resp, [System.Text.Encoding]::UTF8)
        Write-Output "saved to $OutFile"
    } else {
        Write-Output $resp
    }
} catch {
    Write-Output "ERROR: $_"
    exit 1
} finally {
    if ($pipe) { $pipe.Dispose() }
}
