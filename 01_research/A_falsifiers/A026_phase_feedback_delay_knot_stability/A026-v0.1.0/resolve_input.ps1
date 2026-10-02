# Legacy v0.1.2 resolver retained for audit only.
# v0.1.3 launchers do NOT execute this PowerShell file.
param(
    [string]$Explicit = "",
    [Parameter(Mandatory=$true)][string]$RepoDir,
    [string]$Pattern = "*_i10000.txt",
    [Parameter(Mandatory=$true)][string]$OutFile
)

$ErrorActionPreference = "SilentlyContinue"

function Full([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return $null }
    try { return [System.IO.Path]::GetFullPath($p) } catch { return $p }
}

function Add-Unique([System.Collections.Generic.List[string]]$list, [string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return }
    $f = Full $p
    if (-not $f) { return }
    foreach ($x in $list) {
        if ([string]::Equals($x, $f, [System.StringComparison]::OrdinalIgnoreCase)) { return }
    }
    $list.Add($f)
}

function Match-Files([string]$dir, [string]$pattern) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { return @() }
    return @(Get-ChildItem -LiteralPath $dir -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue)
}

function Checkpoint-Summary([string]$dir) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { return @() }
    $files = @(Get-ChildItem -LiteralPath $dir -Recurse -File -Filter '*_i*.txt' -ErrorAction SilentlyContinue)
    $counts = @{}
    foreach ($f in $files) {
        if ($f.Name -match '_i([0-9]+)\.txt$') {
            $k = 'i' + $Matches[1]
            if (-not $counts.ContainsKey($k)) { $counts[$k] = 0 }
            $counts[$k]++
        }
    }
    return $counts.GetEnumerator() | Sort-Object Name
}

$repo = Full $RepoDir
$candidates = New-Object 'System.Collections.Generic.List[string]'
$roots = New-Object 'System.Collections.Generic.List[string]'

if ($Explicit) { Add-Unique $candidates $Explicit }

# Normal layouts: falsifier one or two levels below SST-Workbench.
Add-Unique $candidates (Join-Path $repo '..\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0')
Add-Unique $candidates (Join-Path $repo '..\..\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0')
Add-Unique $candidates (Join-Path $repo '..\KnotPlot\KnotPlot\_3p1\_MultiDynamics\_Relaxation\_Matrix\_v0.1.0')
Add-Unique $candidates (Join-Path $repo '..\..\KnotPlot\KnotPlot\_3p1\_MultiDynamics\_Relaxation\_Matrix\_v0.1.0')

Add-Unique $roots (Join-Path $repo '..\KnotPlot')
Add-Unique $roots (Join-Path $repo '..\..\KnotPlot')

# Compatibility for the two workspace spellings seen in this campaign:
#   C:\workspace\projects\...   vs   C:\workspace\projects\...
$repoText = $repo
if ($repoText -match '\\projects\\') {
    $alt = $repoText -replace '\\projects\\','\\projects\\'
    Add-Unique $roots (Join-Path $alt '..\..\KnotPlot')
    Add-Unique $roots (Join-Path $alt '..\KnotPlot')
}
if ($repoText -match '\\projects\\') {
    $alt = $repoText -replace '\\projects\\','\\projects\\'
    Add-Unique $roots (Join-Path $alt '..\..\KnotPlot')
    Add-Unique $roots (Join-Path $alt '..\KnotPlot')
}

# Explicit campaign roots, only used when they exist.
Add-Unique $roots 'C:\workspace\projects\SST-Workbench\KnotPlot'
Add-Unique $roots 'C:\workspace\projects\SST-Workbench\KnotPlot'

# If an explicit path has real final-checkpoint files, it wins.
if ($Explicit -and (Test-Path -LiteralPath $Explicit -PathType Container)) {
    $hits = Match-Files $Explicit $Pattern
    if ($hits.Count -gt 0) {
        $resolved = Full $Explicit
        Set-Content -LiteralPath $OutFile -Value $resolved -Encoding ASCII
        Write-Host "[PFD] Input: $resolved"
        Write-Host "[PFD] Final-checkpoint files: $($hits.Count) matching $Pattern"
        exit 0
    }
    Write-Host "[PFD] Requested input exists but contains 0 files matching $Pattern:"
    Write-Host "      $(Full $Explicit)"
    Write-Host "[PFD] Searching nearby KnotPlot roots instead..."
}

# Add named matrix-like directories found near candidate roots.
foreach ($root in @($roots)) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    foreach ($d in @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Depth 5 -ErrorAction SilentlyContinue)) {
        if ($d.Name -match 'MultiDynamics|Relaxation|Matrix|_3p1') { Add-Unique $candidates $d.FullName }
    }
}

$scored = @()
foreach ($c in @($candidates)) {
    if (-not (Test-Path -LiteralPath $c -PathType Container)) { continue }
    $hits = Match-Files $c $Pattern
    if ($hits.Count -gt 0) {
        $scored += [pscustomobject]@{ Path=(Full $c); Count=$hits.Count }
    }
}

# Last-resort content discovery: group matching files by parent directory.
foreach ($root in @($roots)) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    $hits = Match-Files $root $Pattern
    foreach ($g in ($hits | Group-Object DirectoryName)) {
        $scored += [pscustomobject]@{ Path=(Full $g.Name); Count=$g.Count }
    }
}

# De-duplicate scored paths, retaining max count.
$bestByPath = @{}
foreach ($s in $scored) {
    $k = $s.Path.ToLowerInvariant()
    if (-not $bestByPath.ContainsKey($k) -or $s.Count -gt $bestByPath[$k].Count) { $bestByPath[$k] = $s }
}
$scored = @($bestByPath.Values | Sort-Object Count -Descending, Path)

if ($scored.Count -gt 0) {
    $topCount = $scored[0].Count
    $top = @($scored | Where-Object { $_.Count -eq $topCount })
    if ($top.Count -gt 1) {
        # Prefer a directory whose basename explicitly names the campaign output.
        $preferred = @($top | Where-Object { [System.IO.Path]::GetFileName($_.Path) -match '^KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0\.1\.0$' })
        if ($preferred.Count -eq 1) { $top = $preferred }
    }
    if ($top.Count -ne 1) {
        Write-Host "ERROR: Multiple input directories tie with $topCount final-checkpoint files."
        foreach ($x in $top) { Write-Host "  [$($x.Count)] $($x.Path)" }
        Write-Host "Pass the desired directory explicitly to run_all.cmd."
        exit 3
    }
    $resolved = $top[0].Path
    Set-Content -LiteralPath $OutFile -Value $resolved -Encoding ASCII
    Write-Host "[PFD] Auto-resolved by file content: $resolved"
    Write-Host "[PFD] Final-checkpoint files: $($top[0].Count) matching $Pattern"
    exit 0
}

Write-Host "ERROR: No files matching $Pattern were found in any candidate KnotPlot dataset."
Write-Host ""
Write-Host "Checkpoint diagnostics:"
$reported = $false
foreach ($root in @($roots)) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
    $sum = @(Checkpoint-Summary $root)
    if ($sum.Count -gt 0) {
        $reported = $true
        Write-Host "  Root: $(Full $root)"
        foreach ($kv in $sum) { Write-Host ("    {0,-10} {1,6} files" -f $kv.Name,$kv.Value) }
    }
}
if (-not $reported) {
    Write-Host "  No *_i*.txt KnotPlot checkpoints were found under the searched roots."
}
Write-Host ""
Write-Host "The blind preregistration requires a common i10000 checkpoint; it will not silently fall back to i04000 or i01000."
Write-Host "Either finish the KnotPlot relaxation matrix to i10000, or pass the directory that already contains those files:"
Write-Host '  run_all.cmd "C:\path\to\matrix-output" basic'
exit 2