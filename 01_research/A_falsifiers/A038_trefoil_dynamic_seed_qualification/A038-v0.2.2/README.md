# Trefoil Mega Falsifier v0.2.2 — prospective atlas and Phase B

This version preserves v0.2.1 and adds a prospective **realization-level** atlas
from three construction lineages, full-state shooting/monodromy diagnostics, and
paired model interventions. It does not establish physical SST or claim a
publication-ready trefoil Floquet certificate.

## Designated local atlas

`artifacts/prospective_atlas_20260830/test_atlas` contains six fresh draws from
Fremlin Fourier, Gilbert/SONO Fourier, and an independently constructed SST
two-strand braid closure. Three lineages are not three statistically independent
physical data sources. The historical parents are **not held out**. Novel draws
were generated only after code, source hashes, configuration, thresholds and
random-seed commitments were frozen. Two draws per lineage are correlated.

The test shard is consumed after screening. A separate reserve seed is committed
in `sealed/seeds.json`; its geometries have not been generated or scored. Keep
that file private. Do not redraw failures, reuse the scored test shard as new
evidence, or call the existing library's 48 track variants 48 source families.

The diagram checker supplies a float64, margin-checked three-crossing trefoil
witness at N=64,96,128. It is not an external-provider or interval-arithmetic
topology certificate. Vertex contact guards also do not prove continuous
topology preservation between time samples.

## Run locally (PowerShell)

From this package directory, the repository's existing Python 3.14 `.venv` has
NumPy, SciPy, pytest and the compatible native extension. No packages were
installed into that environment by this release.

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$python = 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe'
& $python -m pytest tests -q --basetemp '<new-empty-test-temp-directory>'
```

Do not overwrite the archived campaign. For a newly authorized campaign use new
paths, freeze first, then generate, screen and verify:

```powershell
& $python -m sst_seed_falsifier.atlas freeze 'C:\workspace\projects\SST-Workbench' artifacts\NEW_ATLAS --config config\prospective_atlas.json --protocol config\phase_b.json
& $python -m sst_seed_falsifier.atlas generate-test 'C:\workspace\projects\SST-Workbench' artifacts\NEW_ATLAS
& $python -u -m sst_seed_falsifier.campaign screen --repo 'C:\workspace\projects\SST-Workbench' --atlas artifacts\NEW_ATLAS --out artifacts\NEW_RUN --config config\prospective_atlas.json
& $python -m sst_seed_falsifier.campaign phase-b --repo 'C:\workspace\projects\SST-Workbench' --atlas artifacts\NEW_ATLAS --out artifacts\NEW_RUN --config config\prospective_atlas.json --protocol config\phase_b.json
& $python -m sst_seed_falsifier.campaign reveal --out artifacts\NEW_RUN
```

`phase-b --refine` enables bounded full-state shooting; `--ladders` additionally
enumerates all 81 N × timestep × core × mesh cells after baseline qualification.
These options can be expensive. No near-RPO means no monodromy or intervention
test. A partial Arnoldi spectrum never certifies stability of its unseen modes.

## Interpretation

See `docs/PHASE_B_LIMITS.md`. BASIC S37 remains 0.035. The atlas campaign changes
only the pool definition: six preregistered draws, no adaptive refinements, no
post-failure threshold adjustment. Numerical validation, model-intervention
effects, and physical evidence have separate statuses.

The inherited `run_all*.cmd` remain generic Phase-A entrypoints; use the Python
campaign commands above for the designated atlas and Phase B.
