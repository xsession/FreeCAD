param(
    [ValidateSet("qt", "asterforge", "dual")]
    [string]$Shell = "qt",

    [switch]$Console,

    [string[]]$QtArgs = @(),

    [ValidateSet("run", "build")]
    [string]$AsterForgeAction = "run",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$qtLauncher = Join-Path $root "run_freecad.bat"
$asterForgeBuild = Join-Path $root "variants\asterforge\build.ps1"
$powershellExe = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "$Label not found at $Path"
    }
}

function Format-ArgumentList {
    param([string[]]$Values)

    return (($Values | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        }
        else {
            $_
        }
    }) -join ' ')
}

function New-LaunchSpec {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [AllowEmptyCollection()][string[]]$ArgumentList = @(),
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    return [pscustomobject]@{
        Name = $Name
        FilePath = $FilePath
        ArgumentList = $ArgumentList
        WorkingDirectory = $WorkingDirectory
    }
}

function Show-LaunchSpec {
    param([Parameter(Mandatory = $true)]$Spec)

    $command = @($Spec.FilePath) + $Spec.ArgumentList
    Write-Host "[$($Spec.Name)] $($Spec.WorkingDirectory)> $(Format-ArgumentList $command)"
}

function Invoke-LaunchSpec {
    param([Parameter(Mandatory = $true)]$Spec)

    if ($DryRun) {
        Show-LaunchSpec $Spec
        return
    }

    Write-Host "[Launcher] Starting $($Spec.Name)..."
    Start-Process -FilePath $Spec.FilePath -ArgumentList $Spec.ArgumentList -WorkingDirectory $Spec.WorkingDirectory | Out-Null
}

Assert-PathExists -Path $qtLauncher -Label "Qt launcher"
Assert-PathExists -Path $asterForgeBuild -Label "AsterForge build script"
Assert-PathExists -Path $powershellExe -Label "Windows PowerShell"

$launchSpecs = @()

if ($Shell -in @("qt", "dual")) {
    $qtArgumentList = @()
    if ($Console) {
        $qtArgumentList += "--console"
    }
    if ($QtArgs.Count -gt 0) {
        $qtArgumentList += $QtArgs
    }

    $launchSpecs += New-LaunchSpec -Name "Qt shell" -FilePath $qtLauncher -ArgumentList $qtArgumentList -WorkingDirectory $root
}

if ($Shell -in @("asterforge", "dual")) {
    $asterForgeArguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $asterForgeBuild,
        $AsterForgeAction
    )

    $launchSpecs += New-LaunchSpec -Name "AsterForge shell" -FilePath $powershellExe -ArgumentList $asterForgeArguments -WorkingDirectory (Split-Path -Parent $asterForgeBuild)
}

if ($DryRun) {
    Write-Host "[Launcher] Dry run only. Resolved launch commands:"
}

foreach ($spec in $launchSpecs) {
    Invoke-LaunchSpec $spec
}

if (-not $DryRun) {
    switch ($Shell) {
        "qt" { Write-Host "[Launcher] Qt shell requested through run_freecad.bat." }
        "asterforge" { Write-Host "[Launcher] AsterForge shell requested through variants/asterforge/build.ps1 $AsterForgeAction." }
        "dual" { Write-Host "[Launcher] Dual-shell launch requested. Qt and AsterForge were started side by side." }
    }
}