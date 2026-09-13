# Build zip bundles for rclone one-way Drive sync (many small files -> few zips).
# Output: 03_data/_rclone_bundles/  (gitignored)
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'
Set-Location $RepoRoot

$bundleRoot = Join-Path $RepoRoot '03_data\_rclone_bundles'
New-Item -ItemType Directory -Force -Path `
  (Join-Path $bundleRoot 'knotplot'), `
  (Join-Path $bundleRoot 'campaign'), `
  (Join-Path $bundleRoot 'generated'), `
  (Join-Path $bundleRoot 'archive') | Out-Null

function New-DirZip([string]$SourceDir, [string]$ZipPath) {
  if (-not (Test-Path -LiteralPath $SourceDir)) {
    Write-Host "SKIP missing $SourceDir"
    return
  }
  $zipFull = [IO.Path]::GetFullPath($ZipPath)
  $srcFull = [IO.Path]::GetFullPath($SourceDir)
  $parent = Split-Path $srcFull -Parent
  $leaf = Split-Path $srcFull -Leaf
  if (Test-Path -LiteralPath $zipFull) { Remove-Item -LiteralPath $zipFull -Force }
  Write-Host "ZIP $leaf -> $zipFull"
  & tar.exe -a -cf $zipFull -C $parent $leaf
  if ($LASTEXITCODE -ne 0) { throw "tar failed for $SourceDir rc=$LASTEXITCODE" }
  Write-Host ("  OK {0:N1} MiB" -f ((Get-Item -LiteralPath $zipFull).Length / 1MB))
}

Get-ChildItem (Join-Path $RepoRoot '03_data\A_knots\04_knotplot') -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like 'knot_*' -or $_.Name -eq 'final' } |
  ForEach-Object { New-DirZip $_.FullName (Join-Path $bundleRoot "knotplot\$($_.Name).zip") }

$campaign = Join-Path $RepoRoot '03_data\D_generated\knotplot_campaign_outputs'
Get-ChildItem $campaign -Directory -ErrorAction SilentlyContinue |
  ForEach-Object { New-DirZip $_.FullName (Join-Path $bundleRoot "campaign\$($_.Name).zip") }

$summaryDir = Join-Path $env:TEMP 'rclone_campaign_summaries'
Remove-Item $summaryDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null
Get-ChildItem $campaign -File -ErrorAction SilentlyContinue | Copy-Item -Destination $summaryDir
if ((Get-ChildItem $summaryDir -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0) {
  New-DirZip $summaryDir (Join-Path $bundleRoot 'campaign\_summaries.zip')
}

@(
  'qhp', 'trefoil_closure', 'figures', '3d', 'D001_3d_exports',
  'vortexlab_spec_clock_runs', 'legacy_resources_swirl_results',
  'legacy_dataset_exports', 'research_outputs', 'knotplot_reference'
) | ForEach-Object {
  $p = Join-Path $RepoRoot "03_data\D_generated\$_"
  if (Test-Path $p) { New-DirZip (Resolve-Path $p).Path (Join-Path $bundleRoot "generated\$_.zip") }
}

@(
  @{ Rel = '09_archive\restore'; Name = 'restore.zip' },
  @{ Rel = '09_archive\trefoil_closure'; Name = 'trefoil_closure.zip' }
) | ForEach-Object {
  $p = Join-Path $RepoRoot $_.Rel
  if (Test-Path $p) { New-DirZip (Resolve-Path $p).Path (Join-Path $bundleRoot "archive\$($_.Name)") }
}

$all = Get-ChildItem $bundleRoot -Recurse -File
Write-Host ("TOTAL: {0} zips, {1:N2} GiB" -f $all.Count, (($all | Measure-Object Length -Sum).Sum / 1GB))
