param(
  [string]$Version = "v0.1.1",
  [string]$OwnerRepo = "Martin123132/MythMaker",
  [string]$ZipPath = "",
  [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

$safeVersion = $Version -replace "[^a-zA-Z0-9._-]", "-"
$tempBase = [System.IO.Path]::GetTempPath()
$work = Join-Path $tempBase "MythMakerReleaseVerify-$safeVersion-$([System.Guid]::NewGuid().ToString('N'))"
$downloadedZip = Join-Path $work "MythMaker-$Version.zip"
$extractDir = Join-Path $work "unzipped"
$dataDir = Join-Path $work "data"

function Remove-TempWork {
  if (-not (Test-Path -LiteralPath $work)) {
    return
  }
  $tempResolved = (Resolve-Path -LiteralPath $tempBase).Path
  $workResolved = (Resolve-Path -LiteralPath $work).Path
  if (-not $workResolved.StartsWith($tempResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside temp: $workResolved"
  }
  Remove-Item -LiteralPath $workResolved -Recurse -Force
}

try {
  New-Item -ItemType Directory -Force -Path $work, $extractDir, $dataDir | Out-Null

  if ($ZipPath) {
    $sourceZip = (Resolve-Path -LiteralPath $ZipPath).Path
    Copy-Item -LiteralPath $sourceZip -Destination $downloadedZip -Force
    Write-Host "Using local ZIP: $sourceZip"
  } else {
    $url = "https://github.com/$OwnerRepo/releases/download/$Version/MythMaker-$Version.zip"
    Write-Host "Downloading $url"
    Invoke-WebRequest -Uri $url -OutFile $downloadedZip
  }

  Expand-Archive -LiteralPath $downloadedZip -DestinationPath $extractDir -Force

  $required = @(
    "START_MythMaker_WINDOWS.bat",
    "README.md",
    "mythmaker_app\app.py",
    "mythmaker_app\seeds\bottom_house.json",
    "mythmaker_app\templates\index.html"
  )
  foreach ($relative in $required) {
    $path = Join-Path $extractDir $relative
    if (-not (Test-Path -LiteralPath $path)) {
      throw "Missing required release file: $relative"
    }
  }

  $forbidden = Get-ChildItem -LiteralPath $extractDir -Force -Recurse |
    Where-Object { $_.Name -in @(".git", "__pycache__", ".pytest_cache") }
  if ($forbidden) {
    throw "Release ZIP contains forbidden generated files: $($forbidden[0].FullName)"
  }

  if (-not $SkipDoctor) {
    Push-Location $extractDir
    try {
      $env:MYTHMAKER_HOME = $dataDir
      python -m mythmaker_app.app --doctor | Out-Host
      if ($LASTEXITCODE -ne 0) {
        throw "Doctor command failed."
      }
    } finally {
      Pop-Location
      Remove-Item Env:\MYTHMAKER_HOME -ErrorAction SilentlyContinue
    }
  }

  Write-Host "Release ZIP verified for $Version"
} finally {
  Remove-TempWork
}
