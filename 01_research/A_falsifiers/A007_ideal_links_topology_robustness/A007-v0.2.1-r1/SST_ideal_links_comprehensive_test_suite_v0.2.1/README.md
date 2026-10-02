# SST Ideal Links Comprehensive Test Suite v0.2.1

Native C++17/pybind11 analysis of the first ideal links through seven crossings, with optional
extension to all 130 links in Brian Gilbert's 2–9 crossing Fourier database.

## Ridgerunner: necessary or optional?

Ridgerunner is **not required for the primary campaign**. The primary objects are the Fourier
geometries contained in `data/idealLinks.txt`; re-tightening them before measurement would replace
the source object by an optimizer-dependent geometry.

Ridgerunner is valuable as an **independent second-stage audit**:

1. export the unchanged Fourier geometry to closed multi-component OOGL VECT;
2. run Ridgerunner in a separate directory;
3. compare topology, length, thickness and strut/contact structure;
4. retain both the Gilbert baseline and the Ridgerunner-refined result;
5. never silently overwrite the baseline.

The v0.2.1 package therefore includes a Ridgerunner export bridge, but keeps it outside the primary
pass/fail chain.

## What changed in v0.2.1

- fixes the `L2a1` recursion failure with iterative union-find;
- separates the raw contact graph from the augmented contact graph;
- clusters extended contact families into contact patches;
- adds directed jump-and-advance contact-map cycles in both orientations;
- reports candidate period-9 cycles without calling them proven billiards;
- refines curvature maxima directly on the truncated Fourier representation;
- ranks dynamics at fixed `epsilon/D = 0.1` instead of selecting the smoothest core;
- retains minimum-over-epsilon and epsilon-squared extrapolation only as diagnostics;
- adds OOGL VECT export plus source/provenance manifest for Ridgerunner;
- supplies a Windows process-isolated runner: one link per Python process, with retries and resume;
- launchers use the local `.venv` interpreter and do not bypass it with `py -3`.

## Install and validate

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[test]"
python -m sst_link_suite.cli build-native --force --strict --verbose
python -m pytest
python run_native_audit.py --force-build --build-verbose
```

After activation, use `python`, not `py -3`, so compilation, import and audit use the same ABI.
`setuptools` and `wheel` are runtime dependencies: on Windows the native extension is compiled
through a setuptools `build_ext` helper, and Python 3.12+ venvs do not ship setuptools by default.
`pip install -e ".[test]"` installs them; if a bare venv only has `requirements.txt` from an older
checkout, run `python -m pip install "setuptools>=68" wheel` before `build-native`.

## Recommended Windows campaigns

The PowerShell runner launches each link in a fresh process. This prevents one long OpenMP/native
session from contaminating later links and makes individual failures resumable.

Requested 18-link full campaign:

```powershell
.\run_all_chunked.ps1 -Preset full
```

All 130 links:

```powershell
.\run_all_chunked.ps1 -Preset full -AllDatabase
```

Maximum-resolution 18-link campaign with an explicit native thread cap:

```powershell
.\run_all_chunked.ps1 -Preset max -NativeThreads 16
```

A subset:

```powershell
.\run_all_chunked.ps1 -Preset full -Ids L2a1,L6a4,L6n1,L7a7
```

The shorter launchers dispatch to the same process-isolated runner:

```powershell
.\run_all.ps1 -Preset full
```

or:

```cmd
run_all.cmd
```

Runs resume from existing `per_link/*.json` ledgers. Use `-NoResume` only when deliberate
recomputation is required.

## Direct CLI for one controlled subset

```powershell
python -m sst_link_suite.cli run `
  --input data\idealLinks.txt `
  --output outputs_subset `
  --config configs\full.json `
  --ids L2a1 L6a4 L7n2 `
  --require-native
```

## Export for Ridgerunner

Requested 18-link set:

```powershell
python -m sst_link_suite.cli export-ridgerunner `
  --input data\idealLinks.txt `
  --output ridgerunner_inputs `
  --sample-n 2048
```

All 130 links:

```powershell
python -m sst_link_suite.cli export-ridgerunner `
  --input data\idealLinks.txt `
  --output ridgerunner_inputs_all `
  --sample-n 2048 `
  --all-database
```

Gilbert uses diameter normalization `D=1`. The corresponding tube-radius/thickness target is
`D/2 = 0.5`. See `docs/RIDGERUNNER_BRIDGE.md`.

## Primary outputs

- `summary.csv`: fixed-core ranking and comparative geometry/topology;
- `components.csv`: component geometry and refined curvature maxima;
- `contact_patches.csv`: clustered mutual/self-contact patches;
- `contact_map_orbits.csv`: closed directed contact-map cycles;
- `mutual_contacts.csv`: refined inter-component distances;
- `circulation_sign_configurations.csv`: all `2^m` circulation sectors;
- `convergence.csv`: resolution ladder including sampled/refined curvature;
- `per_link/*.json`: complete per-link audit ledgers;
- `native_audit.json`: backend provenance and C++/NumPy parity;
- `run_metadata.json`: input hash, config, completed IDs and failures.

## Interpretation boundary

Hard numerical gates include source parsing, Fourier closure, Gauss-linking convergence and
native/Python parity. Relative-equilibrium scores, regularized energy, contact-map cycles, mirror
matching, epsilon extrapolation and SST dimensional lifting remain **Research Track** diagnostics
until circulation assignment, finite-core closure and physical boundary conditions are fixed
independently.
