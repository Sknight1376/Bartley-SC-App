param(
    [int]$BackendPort = 5000,
    [string]$ApiBase = "http://127.0.0.1:5000",
    [string]$ProbePath = "/api/mobile/clubs"
)

$ErrorActionPreference = "Stop"

function Find-WindowsAdb {
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\adb.exe",
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        "$env:ANDROID_HOME\platform-tools\adb.exe",
        "$env:ANDROID_SDK_ROOT\platform-tools\adb.exe",
        "C:\Android\platform-tools\adb.exe"
    )

    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }

    $wingetAdb = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter adb.exe -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    if ($wingetAdb) { return $wingetAdb }

    return $null
}

function Find-WslAdb {
    $current = Get-Location
    try {
        Push-Location $env:TEMP
        $path = wsl sh -lc "if command -v adb >/dev/null 2>&1; then command -v adb; elif [ -x /root/Android/Sdk/platform-tools/adb ]; then echo /root/Android/Sdk/platform-tools/adb; fi" 2>$null
        if ($LASTEXITCODE -eq 0 -and $path) {
            return ($path | Select-Object -First 1).Trim()
        }
    } catch {
        # ignore and return null
    } finally {
        Pop-Location
    }
    return $null
}

function Run-WindowsAdb([string]$adb, [string[]]$adbArgs) {
    & $adb @adbArgs
    return $LASTEXITCODE
}

function Run-WslAdb([string]$adbPath, [string[]]$adbArgs) {
    $joined = ($adbArgs -join " ")
    $current = Get-Location
    try {
        Push-Location $env:TEMP
        wsl sh -lc "`"$adbPath`" $joined"
        return $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

function Invoke-Adb([string[]]$adbArgs) {
    if ($mode -eq "windows") {
        return Run-WindowsAdb -adb $winAdb -adbArgs $adbArgs
    }
    return Run-WslAdb -adbPath $wslAdb -adbArgs $adbArgs
}

Write-Host "== Reconnecting Android phone to backend =="

$winAdb = Find-WindowsAdb
$wslAdb = $null
$mode = $null

if ($winAdb) {
    $mode = "windows"
    Write-Host "Using adb:" $winAdb
} else {
    $wslAdb = Find-WslAdb
    if ($wslAdb) {
        $mode = "wsl"
        Write-Host "Using adb from WSL:" $wslAdb
    }
}

if (-not $mode) {
    Write-Error "adb not found. Install Android platform-tools or add adb to PATH."
    exit 1
}

Invoke-Adb @("start-server") | Out-Host

$devicesOutput = if ($mode -eq "windows") {
    & $winAdb devices -l
} else {
    $joined = "devices -l"
    Push-Location $env:TEMP
    try {
        wsl sh -lc "`"$wslAdb`" $joined"
    } finally {
        Pop-Location
    }
}

$devicesOutput | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Unable to list devices." }
if (-not ($devicesOutput -match "\sdevice\b")) {
    throw "No authorized device connected. Check USB mode and device authorization prompt."
}

Invoke-Adb @("wait-for-device") | Out-Host
if ($LASTEXITCODE -ne 0) { throw "No authorized device connected." }

Invoke-Adb @("reverse", "--remove-all") | Out-Host
Invoke-Adb @("reverse", "tcp:$BackendPort", "tcp:$BackendPort") | Out-Host
if ($LASTEXITCODE -ne 0) { throw "adb reverse failed for port $BackendPort." }

Write-Host "Reverse mappings:"
Invoke-Adb @("reverse", "--list") | Out-Host

Write-Host "Checking backend API:" "$ApiBase/api/health"
try {
    $health = Invoke-RestMethod -Method Get -Uri "$ApiBase/api/health" -TimeoutSec 5
    Write-Host "Health OK:" ($health | ConvertTo-Json -Compress)
} catch {
    Write-Warning "Health check failed. Checking mobile probe endpoint: $ApiBase$ProbePath"
    try {
        $probe = Invoke-WebRequest -Method Get -Uri "$ApiBase$ProbePath" -TimeoutSec 8
        Write-Host "Probe status:" $probe.StatusCode
    } catch {
        $msg = $_.Exception.Message
        $body = $null
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $body = $_.ErrorDetails.Message
        }
        if ($_.Exception.Response) {
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $streamBody = $reader.ReadToEnd()
                if ($streamBody) { $body = $streamBody }
            } catch {
                $body = $null
            }
        }

        if ($body -and ($body -match 'connection to server at "localhost"' -or $body -match "OperationalError")) {
            Write-Warning "HTTP 500 is from database connectivity. Start PostgreSQL, then retry this script."
        } else {
            Write-Warning "Backend probe failed. Ensure Flask backend is running on port $BackendPort."
        }

        if ($body) {
            Write-Host "Probe response:" $body
        } else {
            Write-Host $msg
        }
    }
}

Write-Host "Done."
