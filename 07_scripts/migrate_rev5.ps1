# SST-Workbench migration rev.5 — move-only, no git commits
param(
    [ValidateSet('inventory', 'move-swirl-derive', 'merge-core-derive', 'move-swirl-rest', 'move-sstcore-rest', 'reorganize-bem', 'verify', 'restore-sstcore-examples', 'restore-verify', 'extract-sstcore-docs-workbench', 'relocate-sstcore-docs-build-scripts')]
    [string]$Phase = 'inventory'
)

$ErrorActionPreference = 'Stop'
$wb    = 'c:\workspace\projects\SST-Workbench'
$swirl = 'c:\workspace\projects\SwirlStringTheory'
$core  = 'c:\workspace\projects\SSTcore'

function Get-FileCount([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    return (Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
}

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
}

function Log-Conflict([string]$Line) {
    $f = Join-Path $wb 'CONFLICT_RESOLUTION.md'
    if (-not (Test-Path $f)) {
        Set-Content $f "# Conflict resolution log`n`nrelative_path | swirl_mtime | sstcore_mtime | winner | reason`n---|---|---|---|---`n"
    }
    Add-Content $f $Line
}

function Log-Move([string]$From, [string]$To) {
    $f = Join-Path $wb 'MOVE_SOURCE_MANIFEST.md'
    if (-not (Test-Path $f)) {
        Set-Content $f "# Move source manifest`n`nfrom | to`n---|---`n"
    }
    Add-Content $f "$From | $To"
}

function Move-Tree([string]$Src, [string]$Dst) {
    if (-not (Test-Path $Src)) { return }
    Ensure-Dir $Dst
    # robocopy /MOV moves files then deletes from source (handles locked __pycache__ better than Move-Item)
    $rc = robocopy $Src $Dst /E /MOV /R:2 /W:2 /NFL /NDL /NJH /NJS /nc /ns /np
    if ($rc -ge 8) { throw "robocopy failed ($rc): $Src -> $Dst" }
    Log-Move $Src $Dst
    # Remove empty leftover directories (not files)
    if (Test-Path $Src) {
        Get-ChildItem $Src -Recurse -Directory -ErrorAction SilentlyContinue |
            Sort-Object { $_.FullName.Length } -Descending |
            ForEach-Object {
                if ((Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
                    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
                }
            }
        if ((Get-ChildItem $Src -Force -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0) {
            Remove-Item $Src -Force -ErrorAction SilentlyContinue
        }
    }
}

function Resolve-DeriveConflict {
    param(
        [string]$SwirlFile,
        [string]$CoreFile,
        [string]$RelPath,
        [string]$TargetRoot,
        [string]$LosersRoot
    )
    $sw = (Get-Item $SwirlFile).LastWriteTime
    $sc = (Get-Item $CoreFile).LastWriteTime
    $destDir = Split-Path (Join-Path $TargetRoot $RelPath) -Parent
    Ensure-Dir $destDir
    $loserDir = Split-Path (Join-Path $LosersRoot $RelPath) -Parent
    Ensure-Dir $loserDir

    if ($sc -gt $sw.AddDays(30)) {
        Move-Item -LiteralPath $CoreFile -Destination (Join-Path $TargetRoot $RelPath) -Force
        Move-Item -LiteralPath $SwirlFile -Destination (Join-Path $LosersRoot $RelPath) -Force
        Log-Conflict "$RelPath | $sw | $sc | sstcore | sstcore >=30d newer"
        return 'sstcore-newer'
    }
    Move-Item -LiteralPath $CoreFile -Destination (Join-Path $LosersRoot $RelPath) -Force
    Log-Conflict "$RelPath | $sw | $sc | swirl | canonical default"
    return 'swirl-canonical'
}

function Log-Restore([string]$From, [string]$To) {
    $f = Join-Path $core 'EXAMPLES_RESTORE_LOG.md'
    if (-not (Test-Path $f)) {
        Set-Content $f "# Examples restore log`n`nfrom | to`n---|---`n"
    }
    Add-Content $f "$From | $To"
}

function Log-DocsExtract([string]$From, [string]$To) {
    $f = Join-Path $wb 'DOCS_EXTRACT_MANIFEST.md'
    if (-not (Test-Path $f)) {
        Set-Content $f "# SSTcore/docs extract manifest`n`nfrom | to`n---|---`n"
    }
    Add-Content $f "$From | $To"
}

$script:RestoreFiles = @(
    'example_ab_initio.py', 'example_biot_savart.py', 'example_enstrophy_circulation.py',
    'example_fetching_knots.py', 'example_fluid_rotation.py', 'example_fremlin_4_1_showcase.py',
    'example_golden_nls.py', 'example_heavy_knot.py', 'example_ideal_knot_showcase.py',
    'example_knot_visualization.py', 'example_magnus_integrator.py', 'example_particle_zoo_eval.py',
    'example_potential_flow.py', 'example_radiation_flow.py', 'example_relative_vorticity.py',
    'example_sst_gravity.py', 'example_sst_integrator.py', 'example_vortex_ring.py',
    'example_vorticity_transport.py',
    'sstcore_resource_helpers.py', 'export_sstcore_resources.py',
    'fourier_knot.example.py', 'showcase_ideal_txt_figure8.py', 'biot-savart_on_fseries.py',
    'sstBindings.py', 'inspectSSTfunctions.py', 'knot_pd_and_volume_example.py',
    'test_ab_initio.py',
    'trefoil.py', 'trefoil_fields.py', 'trefoil_field_lines.py', 'taiChiTesting.py'
)

$script:WorkbenchStayExamples = @(
    'knots.py', 'helicity2.py', 'HelicityCalculation.py', 'knots-toggle-autoknot.py',
    'braid_search_engine.py', 'braid_generator.py', 'braid_search_log.txt',
    'search_particles.py', 'eval_ab_initio.py',
    'investigate_knots.py', 'investigate_no_knotinfo.py',
    'hydrogen_spectrum_simulator.py', 'get_energy_rankine_core.py',
    'taichi_swirl_particles.py', 'wave_analysis.py', 'sphSimulator.py',
    'neonKnot.6_2.py', 'knot_6_2.py', 'VorticityExample.py'
)

switch ($Phase) {
    'inventory' {
        $baseline = @{
            swirl_derive = Get-FileCount "$swirl\papers\SST-CANON\Derive_Constants"
            core_derive  = Get-FileCount "$core\SST_Dashboard\Derive_Constants"
            papers_vam   = Get-FileCount "$swirl\papers\VAM"
            swirl_dash   = Get-FileCount "$swirl\SST_Dashboard"
            core_dash    = Get-FileCount "$core\SST_Dashboard"
            swirl_code   = Get-FileCount "$swirl\code"
            core_examples = Get-FileCount "$core\examples"
        }
        $baseline | ConvertTo-Json | Set-Content (Join-Path $wb 'BASELINE_COUNTS.json')
        Write-Host ($baseline | ConvertTo-Json)
    }
    'move-swirl-derive' {
        Ensure-Dir "$wb\experiments"
        $src = "$swirl\papers\SST-CANON\Derive_Constants"
        $dst = "$wb\experiments\derive_constants"
        if (-not (Test-Path $src)) { throw "Missing $src" }
        if (Test-Path $dst) { throw "Target already exists: $dst" }
        Move-Item -LiteralPath $src -Destination $dst
        Log-Move $src $dst
        Write-Host "Moved swirl Derive_Constants -> $dst (files: $(Get-FileCount $dst))"
    }
    'merge-core-derive' {
        $coreDC = "$core\SST_Dashboard\Derive_Constants"
        $target = "$wb\experiments\derive_constants"
        $losers = "$wb\archive\conflict-losers\sstcore-derive"
        Ensure-Dir $losers
        if (-not (Test-Path $coreDC)) { Write-Host "No SSTcore Derive_Constants to merge"; break }
        if (-not (Test-Path $target)) { throw "Missing canonical target $target" }

        $coreFiles = Get-ChildItem $coreDC -Recurse -File
        foreach ($cf in $coreFiles) {
            $rel = $cf.FullName.Substring($coreDC.Length).TrimStart('\', '/')
            $swirlPath = Join-Path $target $rel
            if (Test-Path $swirlPath) {
                Resolve-DeriveConflict -SwirlFile $swirlPath -CoreFile $cf.FullName -RelPath $rel -TargetRoot $target -LosersRoot $losers | Out-Null
            } else {
                $destDir = Split-Path $swirlPath -Parent
                Ensure-Dir $destDir
                Move-Item -LiteralPath $cf.FullName -Destination $swirlPath
                Log-Move $cf.FullName $swirlPath
            }
        }
        # Move empty dirs leftover in coreDC if any files remain (shouldn't)
        if ((Get-FileCount $coreDC) -eq 0) {
            Remove-Item $coreDC -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Merged SSTcore Derive_Constants"
    }
    'move-swirl-rest' {
        $moves = @(
            @{ src = "$swirl\SST_Dashboard"; dst = "$wb\gui\dashboard\swirl" },
            @{ src = "$swirl\code"; dst = "$wb\proof-scripts\swirl" },
            @{ src = "$swirl\data"; dst = "$wb\datasets" },
            @{ src = "$swirl\resources"; dst = "$wb\datasets\resources-swirl" },
            @{ src = "$swirl\3d-prints"; dst = "$wb\hardware\3d-prints" },
            @{ src = "$swirl\archive"; dst = "$wb\archive\swirl" },
            @{ src = "$swirl\docs\images"; dst = "$wb\media\images" },
            @{ src = "$swirl\docs\Presentation_PDF"; dst = "$wb\media\presentations" }
        )
        foreach ($m in $moves) {
            if (-not (Test-Path $m.src)) { Write-Host "Skip missing $($m.src)"; continue }
            Ensure-Dir (Split-Path $m.dst -Parent)
            Move-Tree $m.src $m.dst
            Write-Host "Moved $($m.src) -> $($m.dst)"
        }
        if (Test-Path "$swirl\trefoil_closure.zip") {
            Ensure-Dir "$wb\bundles"
            Move-Item "$swirl\trefoil_closure.zip" "$wb\bundles\trefoil_closure.zip"
            Log-Move "$swirl\trefoil_closure.zip" "$wb\bundles\trefoil_closure.zip"
        }
        if (Test-Path "$swirl\SSTcore_full_probe.py") {
            Ensure-Dir "$wb\proof-scripts"
            Move-Item "$swirl\SSTcore_full_probe.py" "$wb\proof-scripts\SSTcore_full_probe.py"
            Log-Move "$swirl\SSTcore_full_probe.py" "$wb\proof-scripts\SSTcore_full_probe.py"
        }
    }
    'move-sstcore-rest' {
        $coreDash = "$core\SST_Dashboard"
        if (Test-Path $coreDash) {
            Ensure-Dir "$wb\gui\dashboard"
            Move-Tree $coreDash "$wb\gui\dashboard\sstcore"
        }
        if (Test-Path "$core\examples") {
            Ensure-Dir "$wb\proof-scripts\sstcore"
            Move-Tree "$core\examples" "$wb\proof-scripts\sstcore\examples"
        }
        if (Test-Path "$core\resources\Results") {
            Ensure-Dir "$wb\generated-figures"
            Move-Tree "$core\resources\Results" "$wb\generated-figures\resources-results"
        }
        $voice = "$core\docs\Generate_Audio_Voiceovers"
        if (Test-Path $voice) {
            Ensure-Dir "$wb\media"
            Move-Tree $voice "$wb\media\audio-voiceovers"
        }
    }
    'reorganize-bem' {
        $derive = "$wb\experiments\derive_constants"
        $routeB = Join-Path $derive 'routeB_RT_bem'
        if (-not (Test-Path $routeB)) { Write-Host "No routeB_RT_bem to reorganize"; break }
        $bem = Join-Path $derive 'bem'
        Ensure-Dir "$bem\coillab"
        Ensure-Dir "$bem\outputs"
        Ensure-Dir "$bem\demos"
        Ensure-Dir "$bem\knot-data"
        Ensure-Dir "$bem\root"

        Get-ChildItem $routeB -Directory | ForEach-Object {
            $n = $_.Name
            $dest = switch -Regex ($n) {
                '^SST_CoilLab' { Join-Path "$bem\coillab" $n }
                '^outputs_routeB_BEM|^outputs_v\d|^outputs_routeB|^demo_outputs' { Join-Path "$bem\outputs" $n }
                '^demo$|^demo_fastv' { Join-Path "$bem\demos" $n }
                '^(knotplot|Knots_FourierSeries)$' { Join-Path "$bem\knot-data" $n }
                default { $null }
            }
            if ($dest) {
                Move-Item -LiteralPath $_.FullName -Destination $dest
                Log-Move $_.FullName $dest
            }
        }
        Get-ChildItem $routeB -File | ForEach-Object {
            $dest = Join-Path "$bem\root" $_.Name
            Move-Item -LiteralPath $_.FullName -Destination $dest
            Log-Move $_.FullName $dest
        }
        if ((Get-ChildItem $routeB -Force | Measure-Object).Count -eq 0) {
            Remove-Item $routeB -Force
        }
        $manuscripts = Join-Path $derive 'Manuscripts'
        if (Test-Path $manuscripts) {
            $newM = Join-Path $derive 'manuscripts'
            if (-not (Test-Path $newM)) { Move-Item $manuscripts $newM; Log-Move $manuscripts $newM }
        }
        # trefoil_closure from dashboards
        foreach ($dash in @("$wb\gui\dashboard\sstcore\trefoil_closure", "$wb\gui\dashboard\swirl\trefoil_closure")) {
            if (Test-Path $dash) {
                $parent = Split-Path $dash -Parent | Split-Path -Leaf
                $dest = "$wb\experiments\trefoil\closure\$parent"
                Ensure-Dir (Split-Path $dest -Parent)
                if (-not (Test-Path $dest)) {
                    Move-Item -LiteralPath $dash -Destination $dest
                    Log-Move $dash $dest
                }
            }
        }
        Write-Host "BEM reorganized"
    }
    'verify' {
        $baseline = Get-Content (Join-Path $wb 'BASELINE_COUNTS.json') | ConvertFrom-Json
        $derive = Get-FileCount "$wb\experiments\derive_constants"
        $losers = Get-FileCount "$wb\archive\conflict-losers"
        $vam = Get-FileCount "$swirl\papers\VAM"
        $expectedDerive = [int]$baseline.swirl_derive + [int]$baseline.core_derive
        Write-Host "derive_constants=$derive"
        Write-Host "conflict_losers=$losers"
        Write-Host "expected_derive_merge_total=$expectedDerive actual=$($derive + $losers)"
        if (($derive + $losers) -ne $expectedDerive) {
            throw "Derive merge file count mismatch: $($derive + $losers) != $expectedDerive"
        }
        if ($vam -ne $baseline.papers_vam) { throw "papers/VAM count changed: $vam != $($baseline.papers_vam)" }
        if (Test-Path "$swirl\papers\SST-CANON\Derive_Constants") { throw "Swirl Derive_Constants still at source" }
        foreach ($frozen in @("$swirl\papers\VAM", "$swirl\tools", "$swirl\out")) {
            if (-not (Test-Path $frozen)) { Write-Host "WARN missing frozen path $frozen" }
        }
        if (Test-Path "$swirl\SST_Dashboard") { throw "Swirl SST_Dashboard still at source" }
        if (Test-Path "$swirl\code") { throw "Swirl code/ still at source" }
        if (Test-Path "$core\SST_Dashboard") { throw "SSTcore SST_Dashboard still at source" }
        if (Test-Path "$core\examples") { throw "SSTcore examples still at source" }
        if (-not (Test-Path "$wb\experiments\derive_constants\bem\coillab")) { throw "BEM coillab missing" }
        Write-Host "VERIFY OK"
    }
    'restore-sstcore-examples' {
        $coreEx = Join-Path $core 'examples'
        $wbEx   = Join-Path $wb 'proof-scripts\sstcore\examples'
        Ensure-Dir $coreEx
        if (-not (Test-Path $wbEx)) { throw "Missing workbench examples: $wbEx" }

        foreach ($f in $script:RestoreFiles) {
            $src = Join-Path $wbEx $f
            $dst = Join-Path $coreEx $f
            if (-not (Test-Path $src)) { Write-Host "Skip missing $f"; continue }
            if (Test-Path $dst) { throw "Target exists: $dst" }
            Move-Item -LiteralPath $src -Destination $dst
            Log-Restore $src $dst
        }

        $nodeSrc = Join-Path $wbEx 'node_examples'
        $nodeDst = Join-Path $coreEx 'node_examples'
        if (Test-Path $nodeSrc) {
            if (Test-Path $nodeDst) { throw "node_examples target exists" }
            Move-Item -LiteralPath $nodeSrc -Destination $nodeDst
            Log-Restore $nodeSrc $nodeDst
        }

        $outSrc = Join-Path $wbEx 'output'
        if (Test-Path $outSrc) {
            $outDst = Join-Path $coreEx 'output'
            if (-not (Test-Path $outDst)) {
                Move-Item -LiteralPath $outSrc -Destination $outDst
                Log-Restore $outSrc $outDst
            } else {
                Move-Tree $outSrc $outDst
            }
        }

        Write-Host "Restored examples to $coreEx (files: $(Get-FileCount $coreEx))"
        Write-Host "Workbench examples remaining: $(Get-FileCount $wbEx)"
    }
    'restore-verify' {
        $coreEx = Join-Path $core 'examples'
        $wbEx   = Join-Path $wb 'proof-scripts\sstcore\examples'
        $exCount = (Get-ChildItem $coreEx -Filter 'example_*.py' -File -ErrorAction SilentlyContinue | Measure-Object).Count
        if ($exCount -ne 19) { throw "Expected 19 example_*.py in SSTcore, got $exCount" }
        if (-not (Test-Path (Join-Path $coreEx 'node_examples'))) { throw 'node_examples missing in SSTcore' }
        if (-not (Test-Path (Join-Path $coreEx 'sstcore_resource_helpers.py'))) { throw 'sstcore_resource_helpers missing' }
        foreach ($stay in $script:WorkbenchStayExamples) {
            if (-not (Test-Path (Join-Path $wbEx $stay))) {
                Write-Host "WARN expected workbench file missing: $stay"
            }
        }
        if (Test-Path (Join-Path $wbEx 'example_fluid_rotation.py')) { throw 'example still in workbench' }
        Write-Host "RESTORE VERIFY OK: core=$exCount examples, wb_remaining=$(Get-FileCount $wbEx)"
    }
    'extract-sstcore-docs-workbench' {
        $coreDocs = Join-Path $core 'docs'
        Ensure-Dir "$wb\experiments\sycl"
        Ensure-Dir "$wb\verification-suites\embedded-knots"
        foreach ($cpp in @('main_sycl.cpp', 'list_sycl_devices.cpp', 'vec_add.cpp')) {
            $src = Join-Path $coreDocs $cpp
            if (Test-Path $src) {
                $dst = Join-Path "$wb\experiments\sycl" $cpp
                Move-Item -LiteralPath $src -Destination $dst
                Log-DocsExtract $src $dst
            }
        }
        $py = Join-Path $coreDocs 'test_embedded_knots.py'
        if (Test-Path $py) {
            $dst = Join-Path "$wb\verification-suites\embedded-knots" 'test_embedded_knots.py'
            Move-Item -LiteralPath $py -Destination $dst
            Log-DocsExtract $py $dst
        }
        Write-Host "Extracted workbench scripts from SSTcore/docs"
    }
    'relocate-sstcore-docs-build-scripts' {
        $coreDocs = Join-Path $core 'docs'
        $scripts  = Join-Path $core 'scripts'
        Ensure-Dir $scripts
        foreach ($name in @('build_wheels_local.py', 'build_wheels_conda.py', 'build_wheels_conda.ps1', 'build_wheels_conda.bat', 'build_linux_wheels.sh')) {
            $src = Join-Path $coreDocs $name
            if (Test-Path $src) {
                $dst = Join-Path $scripts $name
                if (Test-Path $dst) { throw "Script target exists: $dst" }
                Move-Item -LiteralPath $src -Destination $dst
                Log-DocsExtract $src $dst
            }
        }
        Write-Host "Relocated wheel build scripts to SSTcore/scripts"
    }
}
