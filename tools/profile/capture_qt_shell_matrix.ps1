param(
    [string]$ManifestPath = (Join-Path (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))) "docs\parity\fixtures\qt-shell-capture-matrix.json"),
    [string[]]$Only = @(),
    [switch]$IncludeDisabled,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$launcher = Join-Path $repoRoot "run_freecad.bat"
$captureScript = Join-Path $repoRoot "tools\profile\capture_qt_shell_parity.py"

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "$Label not found at $Path"
    }
}

function Set-OptionalEnvironmentVariable {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [AllowNull()]$Value
    )

    if ($null -eq $Value -or $Value -eq "") {
        Remove-Item "Env:$Name" -ErrorAction SilentlyContinue
        return
    }

    Set-Item -Path "Env:$Name" -Value ([string]$Value)
}

function Invoke-CaptureEntry {
    param([Parameter(Mandatory = $true)]$Entry)

    $baselineId = [string]$Entry.baseline_id
    if ([string]::IsNullOrWhiteSpace($baselineId)) {
        throw "Manifest entry is missing baseline_id."
    }

    $isEnabled = $true
    if ($null -ne $Entry.enabled) {
        $isEnabled = [bool]$Entry.enabled
    }

    if (-not $isEnabled -and -not $IncludeDisabled) {
        $reason = if ($Entry.skip_reason) { [string]$Entry.skip_reason } else { "disabled in manifest" }
        Write-Host "[Parity] Skipping $baselineId ($reason)"
        return
    }

    if ($Only.Count -gt 0 -and $Only -notcontains $baselineId) {
        return
    }

    $envMap = [ordered]@{
        PARITY_BASELINE_ID = $baselineId
        PARITY_WORKBENCH = $Entry.workbench
        PARITY_THEME = $Entry.theme
        PARITY_FIXTURE_DOCUMENT = $Entry.fixture_document
        PARITY_EDIT_OBJECT = $Entry.edit_object
        PARITY_SELECT_OBJECT = $Entry.select_object
        PARITY_SELECT_SUBELEMENT = $Entry.select_subelement
        PARITY_STEP_FILE = $Entry.step_file
        PARITY_RUN_COMMAND = $Entry.run_command
        PARITY_CAPTURE_VIEWPORT = $(if ($Entry.capture_viewport) { "1" } else { $null })
        PARITY_CAPTURE_TREE_PROPERTY = $(if ($Entry.capture_tree_property) { "1" } else { $null })
        PARITY_CAPTURE_TASK_PANEL = $(if ($Entry.capture_task_panel) { "1" } else { $null })
        PARITY_CAPTURE_DOCK_TARGET = $Entry.capture_dock_target
        PARITY_EXPAND_TREE = $(if ($Entry.expand_tree) { "1" } else { $null })
        PARITY_SELECTION_EMPHASIS = $(if ($Entry.selection_emphasis) { "1" } else { $null })
        PARITY_AUTO_ACCEPT_MODAL = $(if ($Entry.auto_accept_modal) { "1" } else { $null })
        PARITY_NOTES = $Entry.notes
    }

    Write-Host "[Parity] $(if ($DryRun) { 'Would capture' } else { 'Capturing' }) $baselineId"
    foreach ($pair in $envMap.GetEnumerator()) {
        if ($pair.Value) {
            Write-Host "[Parity]   $($pair.Key)=$($pair.Value)"
        }
    }

    if ($DryRun) {
        Write-Host "[Parity]   command=$launcher $captureScript"
        return
    }

    $savedValues = @{}
    foreach ($pair in $envMap.GetEnumerator()) {
        $savedValues[$pair.Key] = [Environment]::GetEnvironmentVariable($pair.Key, "Process")
        Set-OptionalEnvironmentVariable -Name $pair.Key -Value $pair.Value
    }

    try {
        & $launcher $captureScript
        if ($LASTEXITCODE -ne 0) {
            throw "Capture for $baselineId failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        foreach ($pair in $savedValues.GetEnumerator()) {
            Set-OptionalEnvironmentVariable -Name $pair.Key -Value $pair.Value
        }
    }
}

Assert-PathExists -Path $ManifestPath -Label "Capture manifest"
Assert-PathExists -Path $launcher -Label "FreeCAD launcher"
Assert-PathExists -Path $captureScript -Label "Qt parity capture script"

$entries = Get-Content -Raw $ManifestPath | ConvertFrom-Json
if ($entries -isnot [System.Collections.IEnumerable]) {
    throw "Capture manifest must contain a JSON array."
}

foreach ($entry in $entries) {
    Invoke-CaptureEntry -Entry $entry
}