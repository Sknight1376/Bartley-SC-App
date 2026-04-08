param(
    [ValidateSet("ToWsl", "FromWsl")]
    [string]$Direction = "ToWsl",
    [string]$WslDistro = "Ubuntu",
    [string]$WslProjectPath = "/home/sjknight/mobile/sailor-android"
)

$ErrorActionPreference = "Stop"

$repoProjectPath = Join-Path $PSScriptRoot "mobile\sailor-android"
if (!(Test-Path $repoProjectPath)) {
    throw "Repo mobile project not found: $repoProjectPath"
}

function Convert-ToWslPath([string]$path) {
    $resolved = (Resolve-Path $path).Path
    $normalized = $resolved -replace '\\', '/'
    if ($normalized -match '^([A-Za-z]):/(.*)$') {
        $drive = $matches[1].ToLower()
        $rest = $matches[2]
        return "/mnt/$drive/$rest"
    }
    throw "Unable to convert path to WSL format: $path"
}

$repoWslPath = Convert-ToWslPath $repoProjectPath
$sourcePath = if ($Direction -eq "ToWsl") { $repoWslPath } else { $WslProjectPath }
$targetPath = if ($Direction -eq "ToWsl") { $WslProjectPath } else { $repoWslPath }

$rsyncCommand = @"
mkdir -p '$targetPath'
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.gradle/' \
  --exclude '.idea/' \
  --exclude 'build/' \
  --exclude '**/build/' \
  --exclude 'local.properties' \
  --exclude '*.iml' \
  '$sourcePath/' '$targetPath/'
"@

Write-Host "Syncing mobile project $Direction ..." -ForegroundColor Cyan
wsl -d $WslDistro bash -lc $rsyncCommand

Write-Host "Sync complete." -ForegroundColor Green
Write-Host "Source: $sourcePath"
Write-Host "Target: $targetPath"