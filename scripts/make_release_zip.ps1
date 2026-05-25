param(
  [string]$Version = "v0.1.0"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$dist = Join-Path $repoRoot "dist"
$packageName = "MythMaker-$Version"
$stage = Join-Path $dist $packageName
$zipPath = Join-Path $dist "$packageName.zip"

New-Item -ItemType Directory -Force -Path $dist | Out-Null

function Remove-If-In-Dist($PathToRemove) {
  if (-not (Test-Path -LiteralPath $PathToRemove)) {
    return
  }
  $distResolved = (Resolve-Path -LiteralPath $dist).Path
  $targetResolved = (Resolve-Path -LiteralPath $PathToRemove).Path
  if (-not $targetResolved.StartsWith($distResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside dist: $targetResolved"
  }
  Remove-Item -LiteralPath $targetResolved -Recurse -Force
}

Remove-If-In-Dist $stage
if (Test-Path -LiteralPath $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $stage | Out-Null

$files = git -C $repoRoot ls-files
foreach ($file in $files) {
  $source = Join-Path $repoRoot $file
  $target = Join-Path $stage $file
  $targetDir = Split-Path -Parent $target
  New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
  Copy-Item -LiteralPath $source -Destination $target -Force
}

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -Force

$size = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1KB, 1)
Write-Host "Created $zipPath ($size KB)"
