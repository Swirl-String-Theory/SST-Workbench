param(
  [ValidateSet("quick","full","max")]
  [string]$Preset = "full",
  [string]$Output = ""
)
$ArgsList = @("scripts/run_all.py", "--preset", $Preset)
if ($Output -ne "") { $ArgsList += @("--output", $Output) }
py -3 @ArgsList
