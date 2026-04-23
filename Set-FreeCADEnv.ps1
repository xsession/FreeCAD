# SPDX-License-Identifier: LGPL-2.1-or-later
#
# FreeCAD Environment Setup for PowerShell
#
# Usage:
#   . .\Set-FreeCADEnv.ps1           # Dot-source to set env vars in current session
#   . .\Set-FreeCADEnv.ps1 -Launch   # Set env vars AND launch FreeCAD
#   . .\Set-FreeCADEnv.ps1 -Console  # Set env vars AND launch FreeCADCmd
#
# After dot-sourcing, you can run FreeCAD directly:
#   FreeCAD.exe
#   FreeCADCmd.exe --version
#   App_tests_run.exe

[CmdletBinding()]
param(
    [switch]$Launch,
    [switch]$Console,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $ScriptDir) { $ScriptDir = $PWD.Path }

# ---- Detect build directory ----
$BuildBin = $null
foreach ($variant in @('debug', 'release')) {
    $candidate = Join-Path $ScriptDir "build\$variant\bin\FreeCAD.exe"
    if (Test-Path $candidate) {
        $BuildBin = Join-Path $ScriptDir "build\$variant\bin"
        $BuildLib = Join-Path $ScriptDir "build\$variant\lib"
        $BuildMod = Join-Path $ScriptDir "build\$variant\Mod"
        if (-not $Quiet) { Write-Host "[FreeCAD] Using $variant build" -ForegroundColor Green }
        break
    }
}
if (-not $BuildBin) {
    Write-Error "No FreeCAD build found. Run 'build.bat' first."
    return
}

# ---- Detect pixi environment ----
$PixiEnv = Join-Path $ScriptDir ".pixi\envs\default"
if (-not (Test-Path (Join-Path $PixiEnv "Library\bin"))) {
    Write-Error "Pixi environment not found at: $PixiEnv - run 'pixi install' first."
    return
}

# ---- PATH ----
$newPaths = @(
    $BuildBin,
    $BuildLib,
    (Join-Path $PixiEnv "Library\bin"),
    (Join-Path $PixiEnv "Library\lib"),
    $PixiEnv,
    (Join-Path $PixiEnv "Scripts"),
    (Join-Path $PixiEnv "bin")
)
$currentPaths = $env:PATH -split ';'
# Prepend only paths not already present
$pathsToAdd = $newPaths | Where-Object { $_ -notin $currentPaths }
if ($pathsToAdd) {
    $env:PATH = ($pathsToAdd -join ';') + ';' + $env:PATH
}

# ---- Qt 6 (critical - FreeCAD won't start without this) ----
$env:QT_PLUGIN_PATH = Join-Path $PixiEnv "Library\lib\qt6\plugins"

# ---- Python ----
$env:PYTHONHOME = $PixiEnv
$env:PYTHONPATH = @($BuildLib, $BuildMod, (Join-Path $ScriptDir "src\Mod"), (Join-Path $ScriptDir "src\Ext"), (Join-Path $ScriptDir "src\Gui")) -join ';'

# ---- PROJ (coordinate transforms) ----
$projDir = Join-Path $PixiEnv "Library\share\proj"
if (Test-Path $projDir) {
    $env:PROJ_DATA = $projDir
}

# ---- OpenSSL (network certificate paths) ----
$sslCert = Join-Path $PixiEnv "Library\ssl\cacert.pem"
if ((Test-Path $sslCert) -and -not $env:SSL_CERT_FILE) {
    $env:SSL_CERT_FILE = $sslCert
}
$sslDir = Join-Path $PixiEnv "Library\ssl\certs"
if ((Test-Path $sslDir) -and -not $env:SSL_CERT_DIR) {
    $env:SSL_CERT_DIR = $sslDir
}

# ---- Summary ----
if (-not $Quiet) {
    Write-Host ""
    Write-Host "[FreeCAD] Environment configured:" -ForegroundColor Cyan
    Write-Host "  Build:          $BuildBin" -ForegroundColor DarkGray
    Write-Host "  QT_PLUGIN_PATH: $env:QT_PLUGIN_PATH" -ForegroundColor DarkGray
    Write-Host "  PYTHONHOME:     $env:PYTHONHOME" -ForegroundColor DarkGray
    Write-Host "  PROJ_DATA:      $env:PROJ_DATA" -ForegroundColor DarkGray
    Write-Host ""
    if (-not $Launch -and -not $Console) {
        Write-Host "  Run FreeCAD with:  FreeCAD.exe" -ForegroundColor Yellow
        Write-Host "  Run console with:  FreeCADCmd.exe" -ForegroundColor Yellow
        Write-Host "  Run tests with:    App_tests_run.exe" -ForegroundColor Yellow
    }
}

# ---- Optional launch ----
if ($Launch) {
    Write-Host "[FreeCAD] Launching FreeCAD..." -ForegroundColor Green
    & (Join-Path $BuildBin "FreeCAD.exe")
}
elseif ($Console) {
    Write-Host "[FreeCAD] Launching FreeCADCmd..." -ForegroundColor Green
    & (Join-Path $BuildBin "FreeCADCmd.exe")
}
