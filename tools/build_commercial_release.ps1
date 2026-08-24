$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dist = Join-Path $Root "dist\KidAcidsMusicVault"
$Exe = Join-Path $Dist "KidAcidsMusicVault.exe"
$Installer = Join-Path $Root "installer\KidAcidsMusicVault.iss"
$ReleaseDir = Join-Path $Root "release"

if (-not (Test-Path $Exe)) {
    throw "Tested build not found: $Exe. Build the application first with the verified PyInstaller configuration."
}

if (-not (Test-Path $Installer)) {
    throw "Installer definition not found: $Installer"
}

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)

$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    throw "Inno Setup 6 (ISCC.exe) is not installed. Install Inno Setup 6 and run this script again."
}

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

& $Iscc $Installer

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}

Write-Host "Commercial installer created in: $ReleaseDir" -ForegroundColor Green
Get-ChildItem $ReleaseDir -Filter "KidAcidsMusicVault-Setup-*.exe" | Select-Object FullName, Length
