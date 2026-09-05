param(
  [ValidateSet("quick", "full", "max")]
  [string]$Preset = "quick",
  [string[]]$Ids = @("L2a1", "L4a1", "L5a1", "L6a4", "L6n1", "L7n1"),
  [int]$NativeThreads = 16,
  [int]$Retry = 1,
  [string]$Output = ""
)
$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }
$ArgsList = @("scripts\run_qm_chunked.py", "--preset", $Preset, "--native-threads", "$NativeThreads", "--retry", "$Retry")
if ($Ids.Count -gt 0) { $ArgsList += @("--ids") + $Ids }
if ($Output -ne "") { $ArgsList += @("--output", $Output) }
& $Python @ArgsList
exit $LASTEXITCODE
