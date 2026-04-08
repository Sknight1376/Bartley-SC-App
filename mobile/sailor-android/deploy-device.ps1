param(
    [switch]$SkipInstall,
    [switch]$SkipReverse
)

$ErrorActionPreference = "Stop"

function Get-JavaMajorVersion {
    $javaVersionOutput = cmd /c "java -version 2>&1" | Select-Object -First 1
    if (-not $javaVersionOutput) { return $null }

    if ($javaVersionOutput -match '"1\.(\d+)\.') {
        return [int]$matches[1]
    }
    if ($javaVersionOutput -match '"(\d+)') {
        return [int]$matches[1]
    }
    return $null
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$localRoot = Join-Path $env:TEMP "sailor-android-build"

$javaMajor = Get-JavaMajorVersion
if (-not $javaMajor -or $javaMajor -lt 17) {
    throw "Java 17+ is required for Windows CLI build. Current Java major version: $javaMajor. Use Linux build script instead: ./deploy-device-linux.sh"
}

Write-Host "[1/5] Mirroring project to local build path..." -ForegroundColor Cyan
if (!(Test-Path $localRoot)) {
    New-Item -ItemType Directory -Path $localRoot | Out-Null
}

$null = robocopy $projectRoot $localRoot /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD ".gradle" "build" ".idea"
$robocopyCode = $LASTEXITCODE
if ($robocopyCode -ge 8) {
    throw "robocopy failed with exit code $robocopyCode"
}

Push-Location $localRoot
try {
    if (!(Test-Path ".\gradlew.bat")) {
        throw "gradlew.bat not found in local build path: $localRoot"
    }

    Write-Host "[2/5] Building debug APK..." -ForegroundColor Cyan
    & .\gradlew.bat :app:assembleDebug --stacktrace

    $apkPath = Join-Path $localRoot "app\build\outputs\apk\debug\app-debug.apk"
    if (!(Test-Path $apkPath)) {
        throw "APK not found at $apkPath"
    }

    Write-Host "[3/5] Build complete: $apkPath" -ForegroundColor Green

    $adbCmd = Get-Command adb -ErrorAction SilentlyContinue
    $adb = if ($adbCmd) { $adbCmd.Source } else { $null }
    if (-not $adb) {
        $sdkAdb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
        if (Test-Path $sdkAdb) {
            $adb = $sdkAdb
        }
    }

    if (-not $adb) {
        Write-Warning "adb not found in PATH or default SDK location. Skipping install/reverse."
        return
    }

    if (-not $SkipInstall) {
        Write-Host "[4/5] Installing APK to connected device..." -ForegroundColor Cyan
        & $adb install -r $apkPath
    }

    if (-not $SkipReverse) {
        Write-Host "[5/5] Setting port reverse tcp:5000 -> tcp:5000..." -ForegroundColor Cyan
        & $adb reverse tcp:5000 tcp:5000
    }

    Write-Host "Done." -ForegroundColor Green
}
finally {
    Pop-Location
}
