$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$mode = if ($args.Count -gt 0) { $args[0].ToLowerInvariant() } else { "build" }

function Test-CommandAvailable {
    param([Parameter(Mandatory = $true)][string]$CommandName)

    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Add-CargoToPath {
    $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
    if ((Test-Path $cargoBin) -and (-not (($env:PATH -split ';') -contains $cargoBin))) {
        $env:PATH = "$cargoBin;$env:PATH"
    }
}

function Install-RustToolchain {
    $tempInstaller = Join-Path $env:TEMP "rustup-init.exe"
    Write-Host "[AsterForge] Rust toolchain not found. Installing Rust via rustup..."
    Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $tempInstaller
    & $tempInstaller -y --default-toolchain stable --profile minimal
    if ($LASTEXITCODE -ne 0) {
        throw "Rust installation failed with exit code $LASTEXITCODE"
    }
    Add-CargoToPath
}

function Ensure-RustToolchain {
    Add-CargoToPath
    if (Test-CommandAvailable cargo) {
        return
    }

    Install-RustToolchain

    if (-not (Test-CommandAvailable cargo)) {
        throw "cargo is still unavailable after Rust installation. Open a new shell or check %USERPROFILE%\.cargo\bin."
    }
}

function Ensure-NodeTooling {
    if (-not (Test-CommandAvailable node)) {
        throw "Node.js is required for AsterForge frontend builds but is not installed."
    }
    if ((-not (Test-CommandAvailable npm.cmd)) -and (-not (Test-CommandAvailable npm))) {
        throw "npm is required for AsterForge frontend builds but is not installed."
    }
}

function Get-NpmCommand {
    if (Test-CommandAvailable npm.cmd) {
        return "npm.cmd"
    }

    return "npm"
}

function Ensure-FrontendDependencies {
    Ensure-NodeTooling

    $frontendPath = Join-Path $root "frontend\app"
    $lockFile = Join-Path $frontendPath "package-lock.json"
    $nodeModules = Join-Path $frontendPath "node_modules"

    if (-not (Test-Path $lockFile)) {
        throw "frontend\app\package-lock.json is missing; cannot install deterministic frontend dependencies."
    }

    if (-not (Test-Path $nodeModules)) {
        Write-Host "[AsterForge] Installing frontend dependencies with npm ci..."
        $npmCommand = Get-NpmCommand
        Push-Location $frontendPath
        try {
            & $npmCommand ci
            if ($LASTEXITCODE -ne 0) {
                exit $LASTEXITCODE
            }
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-RustDependencies {
    Ensure-RustToolchain
    Write-Host "[AsterForge] Resolving Rust workspace dependencies..."
    & cargo fetch --manifest-path (Join-Path $root "Cargo.toml")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Invoke-AsterForgeBuild {
    Ensure-RustDependencies
    Ensure-FrontendDependencies

    Write-Host "[AsterForge] Building Rust workspace..."
    & cargo build --manifest-path (Join-Path $root "Cargo.toml")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $frontendPath = Join-Path $root "frontend\app"
    Write-Host "[AsterForge] Building React frontend..."
    $npmCommand = Get-NpmCommand
    Push-Location $frontendPath
    try {
        & $npmCommand run build
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "[AsterForge] Build completed successfully."
}

function Start-AsterForgeRun {
    Invoke-AsterForgeBuild

    Write-Host "[AsterForge] Starting backend and frontend in separate windows..."
    Start-Process -FilePath "cmd.exe" -ArgumentList @(
        "/k",
        "cd /d `"$root`" && cargo run --manifest-path `"$root\Cargo.toml`" -p asterforge-api-gateway"
    ) -WorkingDirectory $root | Out-Null

    $frontendPath = Join-Path $root "frontend\app"
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", "Set-Location '$frontendPath'; npm.cmd run dev -- --host 127.0.0.1 --port 4173"
    ) -WorkingDirectory $frontendPath | Out-Null

    Write-Host "[AsterForge] Backend:  http://127.0.0.1:4180"
    Write-Host "[AsterForge] Frontend: http://127.0.0.1:4173"
}

switch ($mode) {
    "build" { Invoke-AsterForgeBuild }
    "run" { Start-AsterForgeRun }
    "help" {
        Write-Host "Usage:"
        Write-Host "  build.bat         Build the Rust backend workspace and React frontend"
        Write-Host "  build.bat build   Same as default build"
        Write-Host "  build.bat run     Build, then start backend and frontend dev servers"
    }
    default {
        Write-Host "Unknown argument: $mode"
        Write-Host ""
        Write-Host "Usage:"
        Write-Host "  build.bat         Build the Rust backend workspace and React frontend"
        Write-Host "  build.bat build   Same as default build"
        Write-Host "  build.bat run     Build, then start backend and frontend dev servers"
        exit 1
    }
}
