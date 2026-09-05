param(
  [string[]]$Ids = @("L2a1", "L4a1", "L6a4", "L6n1", "L7n2"),
  [ValidateSet("quick", "full", "max")]
  [string]$Preset = "full",
  [string]$Output = ""
)
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
& $Python run_native_preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($Output -eq "") { $Output = "outputs_continuum_$Preset" }
$ArgsList = @(
  "scripts\run_continuum.py",
  "--config", "configs\qm_$Preset.json",
  "--output", $Output,
  "--require-native", "--skip-native-build"
)
if ($Ids.Count -gt 0) { $ArgsList += @("--ids") + $Ids }
& $Python @ArgsList
exit $LASTEXITCODE
