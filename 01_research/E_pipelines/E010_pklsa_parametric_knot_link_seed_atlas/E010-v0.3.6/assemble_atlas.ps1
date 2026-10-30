# Place this script within E010-v0.3.6 alongside its parent folder containing all downloaded ZIPs.
# Run from any working directory: powershell -ExecutionPolicy Bypass -File .\E010-v0.3.6\assemble_atlas.ps1
# It will refuse to continue if any archive is missing or fails its declared SHA-256 checksum.
param([switch]$SkipFileVerification)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$archives = @('E010_v0.3.6_KNOTS_01.zip','E010_v0.3.6_KNOTS_02.zip','E010_v0.3.6_KNOTS_03.zip','E010_v0.3.6_KNOTS_04.zip',
              'E010_v0.3.6_LINKS_01.zip','E010_v0.3.6_LINKS_02.zip','E010_v0.3.6_LINKS_03.zip')
$checksums = Join-Path $root 'E010_v0.3.6_RELEASE_ARCHIVES.sha256'
if (-not (Test-Path $checksums)) { throw "Missing release checksum file: $checksums" }
$expected = @{}
Get-Content $checksums | ForEach-Object {
    if ($_ -match '^([a-fA-F0-9]{64})  (\S+)$') { $expected[$matches[2]] = $matches[1].ToLowerInvariant() }
}
foreach ($name in $archives) {
    $zip = Join-Path $root $name
    if (-not (Test-Path $zip)) { throw "Missing archive: $zip" }
    if (-not $expected.ContainsKey($name)) { throw "Missing SHA-256 for $name" }
    $got = (Get-FileHash -Path $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($got -ne $expected[$name]) { throw "Archive SHA-256 mismatch: $name" }
    Write-Host "Verified archive: $name"
}
foreach ($name in $archives) {
    Expand-Archive -Path (Join-Path $root $name) -DestinationPath $root -Force
    Write-Host "Extracted: $name"
}
$out = Join-Path $root 'E010_Ruban_Torus_Dynamics_Family_v0.3.6-fine-outputs'
if (-not (Test-Path $out)) { throw "Missing generated atlas: $out" }
if (-not $SkipFileVerification) {
    $manifest = Join-Path $out 'MANIFEST_SHA256.txt'
    if (-not (Test-Path $manifest)) { throw "Missing per-file manifest: $manifest" }
    $count=0
    Get-Content $manifest | ForEach-Object {
        if ($_ -notmatch '^([a-fA-F0-9]{64})  (.+)$') { throw "Invalid manifest line: $_" }
        $hash = $matches[1].ToLowerInvariant()
        $rel = $matches[2].Replace('/', [IO.Path]::DirectorySeparatorChar)
        $file = Join-Path $out $rel
        if (-not (Test-Path $file)) { throw "Missing file: $rel" }
        $found = (Get-FileHash -Path $file -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($found -ne $hash) { throw "File SHA-256 mismatch: $rel" }
        $count++
    }
    Write-Host "Complete manifest verified: $count files"
}
Write-Host 'E010 v0.3.6 atlas assembled. No dynamics were run.'
