param(
  [ValidateSet("quick", "full", "max")]
  [string]$Preset = "quick",
  [ValidateSet("raw", "filtered", "raw-resolved")]
  [string]$Spectral = "raw",
  [string[]]$Ids = @("L2a1", "L4a1", "L5a1", "L6a4", "L6n1", "L7n1"),
  [int]$NativeThreads = 16,
  [string]$Output = "",
  [switch]$ForceNativeBuild
)
Set-Location $PSScriptRoot
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$PreflightArgs = @("run_native_preflight.py")
if ($ForceNativeBuild) { $PreflightArgs += "--force" }
Write-Host "[SST] Native preflight using $Python"
& $Python @PreflightArgs
if ($LASTEXITCODE -ne 0) {
  Write-Error "Native preflight failed. The QM campaign was not started."
  exit $LASTEXITCODE
}
$ArgsList = @(
  "scripts\run_qm.py", "--preset", $Preset, "--spectral-variant", $Spectral,
  "--require-native", "--skip-native-build",
  "--native-threads", "$NativeThreads"
)
if ($Ids.Count -gt 0) { $ArgsList += @("--ids") + $Ids }
if ($Output -ne "") { $ArgsList += @("--output", $Output) }
& $Python @ArgsList
exit $LASTEXITCODE
