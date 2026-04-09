param(
    [ValidateSet("ToWsl", "FromWsl")]
    [string]$Direction = "ToWsl",
    [string]$WslDistro = "Ubuntu",
    [string]$WslUser = "sjknight",
    [string]$WslProjectSubPath = "mobile\sailor-android"
)

$ErrorActionPreference = "Stop"

$repoProjectPath = Join-Path $PSScriptRoot "mobile\sailor-android"
if (!(Test-Path $repoProjectPath)) {
    throw "Repo mobile project not found: $repoProjectPath"
}

# Access the WSL filesystem directly via the Windows \\wsl.localhost\ UNC path.
# This avoids any /mnt/drive conversion which breaks for network-share (UNC) project paths.
$wslWindowsPath = "\\wsl.localhost\$WslDistro\home\$WslUser\$WslProjectSubPath"

if ($Direction -eq "ToWsl") {
    $source = $repoProjectPath
    $target = $wslWindowsPath
} else {
    $source = $wslWindowsPath
    $target = $repoProjectPath
}

Write-Host "Syncing mobile project $Direction ..." -ForegroundColor Cyan
Write-Host "  Source: $source"
Write-Host "  Target: $target"

if (!(Test-Path $target)) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}

$null = robocopy $source $target /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP `
    /XD ".git" ".gradle" ".idea" "build" `
    /XF "*.iml" "local.properties"
$robocopyCode = $LASTEXITCODE
if ($robocopyCode -ge 8) {
    throw "robocopy failed with exit code $robocopyCode"
}

Write-Host "Sync complete." -ForegroundColor Green