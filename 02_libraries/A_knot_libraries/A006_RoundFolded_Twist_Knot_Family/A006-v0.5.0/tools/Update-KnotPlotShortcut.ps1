param([string]$SourceShortcut = "")
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $SourceShortcut) {
  Write-Host "Pass -SourceShortcut path to your EXISTING valid KnotPlot .lnk. No shortcuts changed."
  exit 2
}
if (-not (Test-Path -LiteralPath $SourceShortcut)) { throw "Missing original shortcut: $SourceShortcut" }
$shell = New-Object -ComObject WScript.Shell
$old = $shell.CreateShortcut((Resolve-Path -LiteralPath $SourceShortcut).Path)
if (-not (Test-Path -LiteralPath $old.TargetPath)) { throw "Existing link target does not exist: $($old.TargetPath)" }
$newpath = Join-Path $project 'KnotPlot_A006_v050.lnk'
if (Test-Path -LiteralPath $newpath) { throw "Refuse to overwrite: $newpath" }
$link = $shell.CreateShortcut($newpath)
$link.TargetPath=$old.TargetPath
$link.Arguments=$old.Arguments
$link.IconLocation=$old.IconLocation
$link.Description='KnotPlot A006 v0.5.0'
$link.WorkingDirectory=$project
$link.Save()
Write-Host "Created $newpath -- old shortcut untouched."
