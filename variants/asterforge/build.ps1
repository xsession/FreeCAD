$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$mode = if ($args.Count -gt 0) { $args[0].ToLowerInvariant() } else { "build" }

function Invoke-AsterForgeBuild {
    Write-Host "[AsterForge] Building Rust workspace..."
    & cargo build --manifest-path (Join-Path $root "Cargo.toml")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $frontendPath = Join-Path $root "frontend\app"
    if (-not (Test-Path (Join-Path $frontendPath "node_modules"))) {
        Write-Host "[AsterForge] Frontend dependencies are missing. Run npm install in frontend\app first."
        exit 1
    }

    Write-Host "[AsterForge] Building React frontend..."
    Push-Location $frontendPath
    try {
        & npm run build
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
        "-Command", "Set-Location '$frontendPath'; npm run dev -- --host 127.0.0.1 --port 4173"
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
