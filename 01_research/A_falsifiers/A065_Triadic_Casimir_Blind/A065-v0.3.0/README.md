# A065 v0.3.0-r1 — unieke exports + zelfstandige LaTeX

**Maintenance patch only.** Original v0.3.0 scientific equations, source datasets, three individual seals and global commitment are unchanged. Keep your original `A065-v0.3.0` folder intact; extract this full distribution into a **new** folder `A065-v0.3.0-r1`.

## What is fixed

- Every writing run (`ALL`, `FRAMEWORK`, `BLIND`, `FULL`, `BASIC`, `REPORT`, `PARITY`, `DYNAMICS`) uses a fresh `runs/A065-v0.3.0__YYYYMMDDTHHMMSSffffffZ-<random>/` folder. The timestamp is UTC with microsecond resolution; a secure random suffix and atomic directory allocation prevent collisions.
- Every PDF, TeX, blind-results ZIP, separately sealed D01/D02/D03 ZIP, framework PDF and manifest is published under `exports/<RUN_ID>/` with `<RUN_ID>_...` filenames; exclusive create-only file modes refuse collisions.
- No writing run modifies earlier runs, earlier PDF files, existing output archives, source datasets, or source seals. These are separate per-run scientific instances; the canonical framework itself stays frozen.
- The official framework `FRAMEWORK` mode generates its own v1.0.7 `cpu` instance **inside** that run folder. `FREEZE`, `FULL` and `REVEAL_IF_ALLOWED` and its native PDF are retained and exported separately.
- The project report is generated as a **single, self-contained LaTeX `.tex`** with all formulas, gate tables, metrics and seal digests written inline: no `\input`, `\include`, bibliography files, external images or custom font files. Requires a local TeX installation to compile. When `pdflatex` is available, this `.tex` is compiled to PDF twice. When not, the original Python-stdlib PDF fallback still makes a PDF; the `.tex` is always exported.
- `REVEAL` stays blocked while the spatial G2 gate fails / physical G3 is unresolved, even if private escrow is present. No blind target is included in this public patch.

## Windows commands

```bat
run_all.cmd
run_all.cmd FRAMEWORK
run_all.cmd REPORT
run_all.cmd SELFTEST
run_all.cmd VERIFY
run_all.cmd DYNAMICS
run_all.cmd PARITY
```

Find all exported artifacts by unique name in `exports\<RUN_ID>\`; complete per-run workspaces are in `runs\<RUN_ID>\`. No generated data are written to the release root. `REPORT` performs a fresh blind computation in a separate run rather than reusing or overwriting a previous PDF.

The official v1.0.7 framework is looked up from the Workbench under `06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7`, or by setting `SST_FALSIFIER_FRAMEWORK_ROOT`. It is never packaged or modified.

## Scientific qualification

The dynamic filament spatial convergence gate remains `FAIL` (roughly 8.73% versus pre-registered 5%). The time-step gate and analytical controls are reproducible, but geometry does not certify Euler dynamics or a metallic Casimir response. Fremlin A006 source bytes still require authentic upstream import. D01/D02/D03 are independently **sealed**, not three independent physical-source families.

## Security

SHA-256 manifests detect unexpected byte changes but do not authenticate third-party data origin. A user with access to the public source can recompute outputs; the physical target remains outside the public release and reveals are blocked.


---

# A065 v0.3.0 — Triadic–Casimir / PKLSA dynamische falsifier

**Status:** *scientific G2 FAIL; G3 NOT_RUN_PREREQUISITE; physical Casimir unresolved*. This release is built directly on the user-run A065-v0.2.0 baseline. The earlier baseline is not overwritten. Version v0.3.0 is a new preregistered experiment; gates continue after numerical failures.

## Changes since v0.2.0

1. Added a genuine **time-dependent** regularized 3D vortex-filament ODE, integrated with fourth-order Runge–Kutta (RK4); 75 nodes selected from the actual source N300 trefoil. This is a numerical reduced model, **not** a time-dependent Euler PDE solution.
2. Fixed-final-time temporal convergence: 4 versus 8 RK4 steps at `T=0.04` and `eps=0.12` (dimensionless). The two runs agree to relative displacement error `~2.02e-11`.
3. New preregistered **spatial** convergence gate, comparing 75 versus 150 filament nodes: relative deviation `~0.08729` vs threshold `0.05`; **FAIL**. No post-hoc change to that tolerance.
4. Independently derived C++17 binary64 filament-velocity kernel with 225-component Python–C++ parity. This is kernel numerical validation, **not** qualification of framework physical backend G5.
5. E010 `A006` Fremlin/Fourier 3_1 source candidate registered with exact raw SHA-256, upstream carrier ID and independence group. Actual raw source not present in the accessible Google Drive material: `UNRESOLVED_SOURCE_MISSING`, never counted as a second source.
6. The official **SST Framework v1.0.7** generated instance uses `cpu` profile and `pdf_required=true`. Freeze and gate ledger, protocol commitment, reveal policy and LaTeX PDF belong to the user's installed frozen framework; the portable PDF is a fallback only.
7. Three independent `D01_EULER`, `D02_CLOCK_LINK`, `D03_TWO_SURFACE` SHA-256 seals are newly issued and checked on every run. Reference targets are removed from the public distribution; available only in the **separate private escrow archive**. All reveals remain blocked in v0.3.0 because G2 failed and G3 cannot be promoted.

## Windows commands

Unzip to a new folder under `01_research/A_falsifiers/`. The portable entry point is:

```bat
run_all.cmd
run_all.cmd FRAMEWORK
run_all.cmd DYNAMICS
run_all.cmd PROVIDER
run_all.cmd PROVIDER "C:\workspace\projects\SST-Workbench\03_data\A_knots\02_fourier\resources_swirl\3_1\knot.3_1u.short"
run_all.cmd PKLSA
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd PARITY
run_all.cmd REPORT
```

If the framework is elsewhere, set `SST_FALSIFIER_FRAMEWORK_ROOT` to **the actual, unchanged** `SST_Falsifier_Framework_v1.0.7`. The `FRAMEWORK` mode requires it and exits nonzero if it cannot run. The default `ALL` mode runs even without it and emits an honest `FRAMEWORK_NOT_FOUND` status while still producing the PDF.

A current PDF **always** appears after `ALL`/`FRAMEWORK`/`BLIND`:

```
A065-v0.3.0\reports\TRIADIC_CASIMIR_v0.3.0_FALSIFIER_REPORT.pdf
..\A065-v0.3.0_FALSIFIER_REPORT.pdf
```

The genuine framework generates an *additional* PDF at `FRAMEWORK_INSTANCE/A065-v0.3.0_FALSIFIER_REPORT.pdf`; `pdf_required=true` makes a missing framework-native PDF a hard framework failure. The portable fallback is generated without LaTeX.

On Linux, `./run_all.sh ALL` requires Python >=3.10. C++17 parity requires `g++` (override `CXX` with a compatible GCC/Clang compiler). Otherwise it remains `NOT_RUN`, never `PASS`.

## PKLSA first source

- `data/D01_EULER/pklsa/trefoil_KnotPlot_relaxed_N300.txt` has 300 actual source coordinates, downloaded from a prior KnotPlot source export, and is verified via `source.json` SHA-256 and D01 seal.
- E010/CAR Fremlin A006 independent **registered candidate**: `fremlin_provider_contract.json` with `expected_raw_sha256=73cd5304e79a9cf52b71c88d1d7ebc21948a6d87526b0e95ba5aa6f257150e80`. No raw bytes available, no source or mechanism qualification. `PROVIDER` checks the local file without altering any sealed dataset.
- Reusing one provider with different point counts only tests discretization, never independent replication.

## Scientific gates and outputs

`D01_G08_FILAMENT_SPATIAL_REFINEMENT` is deliberately `FAIL`. The official framework's G2 must therefore be `FAIL`; downstream G3 must be `NOT_RUN_PREREQUISITE`, and G4/G5 cannot become proof by running an unrelated parity check. `CERTIFY` is blocked.

`outputs/BLIND/*.json` and the official `GATE_LEDGER.json` retain all failures, even when a different gate passes. The pressure-Poisson test is *kinematical*; the toy two-sheet thermal interaction is *not* metallic Casimir physics. No physical quantum fluctuation normalization, physical wall stress, force amplitude, gravitational equivalence or PKLSA atomic clock has been established.

For the exact equations, gates, upstream provenance, and next research tranche read `docs/V030_SCIENCE_PLAN.md`. PDF is an execution artifact, not a certification of a physical force.

## Blindness

Each D01/D02/D03 archive has its own manifest and a global commitment; those are **tamper-evident hashes**, not third-party signatures. The private comparator is NOT included in the public ZIP and is separately packaged as `A065-v0.3.0_PRIVATE_ESCROW.zip`. Keep the escrow away from the blind evaluator. `REVEAL` is fail-closed even with escrow because G2 failed and G3 remains unqualified. The canonical framework's own reveal contract is separately enforced.

### Source package hygiene

The public ZIP deliberately excludes generated framework instance folders, virtual environments, binary extensions, `private_reveal/targets.json` and stale reveal output. It does include the preregistration, source geometry, source hashes, three seals, numerical output ledger and portable PDF source.
