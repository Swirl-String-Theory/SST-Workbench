# SST Swirl Clock - Bohr Delay Action Closure v0.1.0

**Status:** Executed standalone reference and synthetic-control tranche. Physically `UNRESOLVED`; **not** yet a certified v1.0.7 framework execution. Designed to be integrated into the canonical frozen framework without changing its source.

## Scientific question

Can a 3D material vortex loop governed by incompressible inviscid Euler dynamics independently furnish a clock reading tau_K(T), physically measurable return delay, attracting/long-lived feedback-selected modal frequencies, and a target-blind canonical-action spacing? The first two may occur without the third.

## Delivered

- `src/core.py`: SST-60 roots/stability, delayed-phase time integration, harmonic/rotor action controls, Euler continuous-scaling null.
- `src/run.py`: blind input SHA256 verification, independent control-case metrics, nine non-short-circuiting gates.
- `src/inspect_pklsa.py`: authentic PKLSA static surface guard; refuses to certify phase/clock from mesh alone.
- `src/generate_controls.py`: **development only**. Generates 3 anonymized SHA256-sealed synthetic controls. Do not rerun over frozen controls; generates a new random permutation.
- `inputs/S01.npz`, `S02.npz`, `S03.npz`: distinct synthetic control data files; `inputs/SEALED_INPUT_MANIFEST.json` hashes.
- `private/CONTROL_REVEAL_ONLY.json`: **do not copy into blind ZIP**; stores synthetic control labels only, never physical truth.
- `outputs/`: completed gate results; report PDF and images created by `src/make_report.py`.
- `framework_adapter/`: exact integration instructions for official frozen framework.
- `preregistration/`: science contract and hold conditions.

## Run on Windows

```bat
py -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd BASIC
```

Linux/macOS: `bash run_all.sh SELFTEST`, `bash run_all.sh BASIC`.

## Non-claim guard

The 3 synthetic sources are **not** 3 independent physical providers. Analytic proof-of-implementation PASS_CONTROL does **not** qualify SST Swirl Clock; G7-G9 MUST be UNRESOLVED until real qualified temporal PKLSA inputs and true canonical actions exist. The single downloaded static PKLSA surface below cannot fill this gap.

### Grounded PKLSA source from Google Drive

Bundled under `inputs/PKLSA_STATIC_CANDIDATE_SURFACE.npz` and inspected fail-closed by `src/inspect_pklsa.py`. Origin: `CANDIDATE_SURFACE.npz`, source item `1w8_Q9fOUdLvfeB6REL-dl-exsYaFOf1P`, SHA256 `9f745ebdf546deafc7f10ffa7ecf3d86c191b1e85f405646985b3aa66e56d108`; contains `vertices_m` `(2056,3)` and `triangles` `(4108,3)`. It is a geometry surface, not a resolved 3D time-series. A separate A064 Euler simulation source audit in Drive (`EULER_SOURCE_AUDIT.json`, ID `1B7n0f55jzW4jl6ZtDqMbXLsyCQUzE2Ee`) records a conditional Euler model, but spatial and temporal convergence are unresolved. Do not upgrade its evidence status.

## Theoretical guard

The asymptotic relation `theta_n=Omega_n*tau ~= 2*pi*n` concerns an effective delayed phase model. A frequency ladder does not certify `J_n=n*h`. The mechanical assumption `J_rotor=2*pi*I*Omega` is different from the harmonic coordinate `J_harmonic=pi*m*Omega*A^2` and must be justified independently in any 3D vortex reduction. In inviscid Euler equations, continuous amplitude/speed rescaling is a null requiring a new selector beyond ideal hydrodynamics.

## Framework provenance

Canonical framework location in user's Windows Workbench:
`06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.7`
Its documented status `CANONICAL_FROZEN`, 56 regressions PASS. This output is **standalone DEVELOPMENT**, not a falsely attributed `FULL` framework run, and MUST remain separate from official `GATE_LEDGER.json` / `OUTPUT_MANIFEST.json` until the native framework is actually executed. See `framework_adapter/INSTALL.md`.
