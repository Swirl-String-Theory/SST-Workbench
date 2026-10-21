<#
Creates a NEW KnotPlot Windows shortcut for the v0.2.3 project directory.
Does not mutate the user's source .lnk or installed KnotPlot executable.
Requires Windows + WScript.Shell COM. Run inside extracted project folder.
#>
[CmdletBinding()]
param(
  [string]$OriginalShortcut = (Join-Path $PSScriptRoot '..\inputs\KnotPlot_original.lnk'),
  [string]$ProjectRoot = (Join-Path $PSScriptRoot '..'),
  [string]$OutputShortcut = (Join-Path $PSScriptRoot '..\KnotPlot_A006_v0.2.3_SmoothClasp.lnk')
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$source = (Resolve-Path -LiteralPath $OriginalShortcut).Path
$target = [System.IO.Path]::GetFullPath($OutputShortcut)
if (-not (Test-Path -LiteralPath (Join-Path $root 'run_all.cmd'))) {throw "Not a valid project root: $root"}
$wsh = New-Object -ComObject WScript.Shell
$old = $wsh.CreateShortcut($source)
$exe = [Environment]::ExpandEnvironmentVariables($old.TargetPath)
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
  throw "KnotPlot.exe not present at shortcut target: $exe. Specify a valid original shortcut."
}
if ($source -eq $target) {throw 'Cannot overwrite the supplied original shortcut'}
if (Test-Path -LiteralPath $target) {
   $bak = $target + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
   Copy-Item -LiteralPath $target -Destination $bak
   Write-Host "Existing output shortcut backed up: $bak"
}
$new = $wsh.CreateShortcut($target)
$new.TargetPath = $exe
$new.WorkingDirectory = $root
$new.Arguments = $old.Arguments
$new.Description = 'SST RoundFolded SmoothClasp v0.2.3 KnotPlot (working directory is this release)'
$new.WindowStyle = $old.WindowStyle
if ($old.IconLocation) { $new.IconLocation = $old.IconLocation }
$new.Save()
$verify = $wsh.CreateShortcut($target)
if ($verify.WorkingDirectory -ne $root -or $verify.TargetPath -ne $exe) {throw 'Shortcut verification failed'}
Write-Host "CREATED $target"
Write-Host "KnotPlot executable: $exe"
Write-Host "New working directory: $root"
