<#
.SYNOPSIS
    Full mobile build-and-deploy pipeline (Windows → WSL → device).

.DESCRIPTION
    1. Sync:     Copies mobile\sailor-android from this repo to WSL Ubuntu via robocopy.
    2. Build:    Runs Gradle assembleDebug inside WSL (mirrors source to /tmp first
                 to avoid network-share performance/permission issues).
    3. Copy:     Pulls the built APK from WSL to $ApkOutputPath on Windows.
    4. Install:  Streams the APK to the connected Android device via Windows adb.

.PARAMETER SkipSync
    Skip step 1 (useful when the WSL copy is already up-to-date).

.PARAMETER SkipInstall
    Skip step 4 (build and copy only, don't push to device).

.PARAMETER SkipReverse
    Skip the `adb reverse tcp:5000 tcp:5000` port-forward after install.

.PARAMETER WslDistro
    Name of the WSL distribution to use (default: Ubuntu).

.PARAMETER WslUser
    Linux username inside the WSL distribution (default: sjknight).

.PARAMETER ApkOutputPath
    Windows path where the built APK is copied (default: C:\Users\<you>\app-debug.apk).

.EXAMPLE
    .\build_mobile.ps1
    .\build_mobile.ps1 -SkipSync
    .\build_mobile.ps1 -SkipInstall
#>
param(
    [switch]$SkipSync,
    [switch]$SkipInstall,
    [switch]$SkipReverse,
    [string]$WslDistro = "Ubuntu",
    [string]$WslUser = "sjknight",
    [string]$ApkOutputPath = "C:\Users\$env:USERNAME\app-debug.apk"
)

$ErrorActionPreference = "Stop"

$wslMobileDir  = "/home/$WslUser/mobile/sailor-android"
$wslApkWindows = "\\wsl.localhost\$WslDistro\tmp\sailor-android-build\app\build\outputs\apk\debug\app-debug.apk"

# ---------------------------------------------------------------------------
# Step 1 — Sync Windows repo → WSL
# ---------------------------------------------------------------------------
if (-not $SkipSync) {
    Write-Host "`n[1/4] Syncing mobile project to WSL $WslDistro ..." -ForegroundColor Cyan
    & "$PSScriptRoot\sync_mobile_android.ps1" -Direction ToWsl -WslDistro $WslDistro -WslUser $WslUser
} else {
    Write-Host "`n[1/4] Skipping sync (SkipSync specified)." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# Step 2 — Gradle assembleDebug inside WSL (build-only, no adb from Linux)
# ---------------------------------------------------------------------------
Write-Host "`n[2/4] Building debug APK inside WSL ..." -ForegroundColor Cyan
$buildScript = "cd '$wslMobileDir' && SKIP_INSTALL=1 SKIP_REVERSE=1 bash deploy-device-linux.sh"
wsl -d $WslDistro -- bash -lc $buildScript
if ($LASTEXITCODE -ne 0) {
    throw "Gradle build failed (exit $LASTEXITCODE)."
}

# ---------------------------------------------------------------------------
# Step 3 — Copy APK from WSL to Windows
# ---------------------------------------------------------------------------
Write-Host "`n[3/4] Copying APK to $ApkOutputPath ..." -ForegroundColor Cyan
if (-not (Test-Path $wslApkWindows)) {
    throw "APK not found at WSL path: $wslApkWindows`nBuild may have failed silently."
}
Copy-Item -Path $wslApkWindows -Destination $ApkOutputPath -Force
Write-Host "      APK ready: $ApkOutputPath" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 4 — Stream-install to device via Windows adb
# ---------------------------------------------------------------------------
if (-not $SkipInstall) {
    Write-Host "`n[4/4] Installing APK to connected device ..." -ForegroundColor Cyan

    # Locate adb: PATH first, then known install location, then default SDK location
    $adbCmd = Get-Command adb -ErrorAction SilentlyContinue
    $adb = if ($adbCmd) { $adbCmd.Source } else { $null }
    if (-not $adb) {
        $knownAdb = "C:\Users\$env:USERNAME\cmdline_tools\bin\platform-tools\adb.exe"
        if (Test-Path $knownAdb) { $adb = $knownAdb }
    }
    if (-not $adb) {
        $sdkAdb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
        if (Test-Path $sdkAdb) { $adb = $sdkAdb }
    }
    if (-not $adb) {
        Write-Warning "adb not found. Install manually:  adb install -r `"$ApkOutputPath`""
    } else {
        $devices = & $adb devices 2>&1
        $ready   = ($devices | Select-String "`tdevice$").Count
        if ($ready -eq 0) {
            Write-Warning "No ready device detected by adb.  Connect device and accept USB debugging, then run:"
            Write-Warning "  & `"$adb`" install -r `"$ApkOutputPath`""
        } else {
            # Attempt install; if signature mismatch, uninstall first then retry
            $installOut = & $adb install -r $ApkOutputPath 2>&1
            if ($installOut -match "INSTALL_FAILED_UPDATE_INCOMPATIBLE") {
                Write-Warning "Signature mismatch — uninstalling existing app and retrying..."
                & $adb uninstall com.quicksail.sailor | Out-Null
                & $adb install -r $ApkOutputPath
                if ($LASTEXITCODE -ne 0) { throw "adb install failed after uninstall (exit $LASTEXITCODE)." }
            } elseif ($LASTEXITCODE -ne 0) {
                throw "adb install failed (exit $LASTEXITCODE): $installOut"
            } else {
                Write-Host $installOut
            }
            if (-not $SkipReverse) {
                Write-Host "      Forwarding port tcp:5000 ..." -ForegroundColor Cyan
                & $adb reverse tcp:5000 tcp:5000
            }
        }
    }
} else {
    Write-Host "`n[4/4] Skipping install (SkipInstall specified)." -ForegroundColor DarkGray
}

Write-Host "`nDone." -ForegroundColor Green
