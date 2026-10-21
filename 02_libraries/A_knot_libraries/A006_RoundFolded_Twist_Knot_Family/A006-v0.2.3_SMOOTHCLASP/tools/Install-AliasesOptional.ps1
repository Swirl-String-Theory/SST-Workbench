<# Appends version-specific aliases to a provided local KnotPlot startup file.
No guessing of the install's startup RC location; requires -KnotplotRc.
Backs up input; idempotent by a release marker. #>
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$KnotplotRc)
$ErrorActionPreference='Stop'
$dst=(Resolve-Path -LiteralPath $KnotplotRc).Path
$source=Join-Path $PSScriptRoot '..\presets\sst_smoothclasp_v023.kps'
if (-not (Test-Path -LiteralPath $source)) {throw "Preset not found: $source"}
$old=Get-Content -LiteralPath $dst -Raw
$tag='% SST-SMOOTHCLASP-v0.2.3 BEGIN'
if ($old.Contains($tag)) {Write-Host 'Already installed; no changes';return}
$backup=$dst+'.before-v023-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.bak'
Copy-Item -LiteralPath $dst -Destination $backup
Add-Content -LiteralPath $dst -Value ("`r`n" + (Get-Content -LiteralPath $source -Raw)) -Encoding ascii
Write-Host "Appended aliases, backup: $backup"
