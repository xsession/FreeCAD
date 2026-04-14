param(
    [Parameter(Mandatory = $true)]
    [string]$ExePath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]+$')]
    [string]$AffinityMaskHex,

    [string[]]$ArgumentList = @(),

    [ValidateSet("Normal", "AboveNormal", "High")]
    [string]$PriorityClass = "High"
)

$resolvedExe = (Resolve-Path -LiteralPath $ExePath).Path
$workingDir = Split-Path -Parent $resolvedExe

Write-Host "Launching $resolvedExe"
Write-Host "Affinity mask: 0x$AffinityMaskHex"
Write-Host "Priority class: $PriorityClass"

$proc = Start-Process `
    -FilePath $resolvedExe `
    -ArgumentList $ArgumentList `
    -WorkingDirectory $workingDir `
    -PassThru

Start-Sleep -Milliseconds 250

if ($proc.HasExited) {
    Write-Error "Process exited before affinity could be applied (exit code: $($proc.ExitCode))"
    exit 1
}

try {
    $maskValue = [Convert]::ToInt64($AffinityMaskHex, 16)
    $proc.ProcessorAffinity = $maskValue
    $proc.PriorityClass = $PriorityClass
    Write-Host "Applied affinity and priority to PID $($proc.Id)"
}
catch {
    Write-Error "Failed to apply affinity: $($_.Exception.Message)"
    exit 1
}
