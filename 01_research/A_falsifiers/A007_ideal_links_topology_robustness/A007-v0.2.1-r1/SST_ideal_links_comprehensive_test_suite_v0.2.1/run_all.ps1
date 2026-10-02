param(
  [ValidateSet("quick","full","max")]
  [string]$Preset = "full",
  [string]$Output = "",
  [switch]$AllDatabase,
  [string[]]$Ids = @(),
  [int]$NativeThreads = 0,
  [int]$Retries = 2,
  [switch]$NoResume
)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ArgsList = @("-ExecutionPolicy", "Bypass", "-File", "$Root\run_all_chunked.ps1", "-Preset", $Preset)
if ($Output -ne "") { $ArgsList += @("-Output", $Output) }
if ($AllDatabase) { $ArgsList += "-AllDatabase" }
if ($Ids.Count -gt 0) { $ArgsList += @("-Ids") + $Ids }
if ($NativeThreads -gt 0) { $ArgsList += @("-NativeThreads", $NativeThreads) }
if ($Retries -ne 2) { $ArgsList += @("-Retries", $Retries) }
if ($NoResume) { $ArgsList += "-NoResume" }
& powershell @ArgsList
exit $LASTEXITCODE
