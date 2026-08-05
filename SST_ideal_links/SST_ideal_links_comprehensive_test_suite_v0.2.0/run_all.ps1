param(
  [ValidateSet("quick","full","max")]
  [string]$Preset = "full",
  [string]$Output = "",
  [switch]$AllowPythonFallback,
  [switch]$ForceBuild
)
$ArgsList = @("scripts/run_all.py", "--preset", $Preset)
if (-not $AllowPythonFallback) { $ArgsList += "--require-native" }
if ($ForceBuild) { $ArgsList += "--force-build" }
if ($Output -ne "") { $ArgsList += @("--output", $Output) }
py -3 @ArgsList
