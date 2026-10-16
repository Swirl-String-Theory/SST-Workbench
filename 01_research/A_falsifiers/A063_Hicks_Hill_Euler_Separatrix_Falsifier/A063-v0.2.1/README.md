# A063 v0.2.1 — Hicks/Hill invariant surfaces and knotted-core falsifier

**Release class:** analytical/numerical reference, source-sealed locally; **not** an official SST Falsifier Framework v1.0.7 frozen instance. The user requested that legacy instances need not be migrated merely to generate a report; this instance produces a PDF directly.

## Falsification question

Is the numerical closed `T(3,4)` vortex line of the first Hicks-Beltrami spherical vortex enclosed by a finite smooth **stationary knotted material and vortex-aligned tube**, whose **core** is itself `T(3,4)`? If not, which weaker stationary invariant objects do exist? Whether any such tube is stable under 3D nonlinear Euler perturbations is separately tested and marked unresolved when no coupled solver is used.

The selection of the rational `3/4` orbit was performed in the **parent release**. This is a *target-labelled* analytic reference study, not a blind protected observation campaign or independent physical replication.

## Scientific result

- The axisymmetric first Hicks-Beltrami flow has smooth regular level surfaces `psi=constant`. The registered `psi0 = 0.138575114976...` of the `T(3,4)` trajectory is one such surface.
- In the co-moving frame, `u . grad(psi) = 0`. For the first Beltrami mode, `omega = lambda/a * u`, so the same stationary surface has zero vorticity-normal flux.
- A **closed star-shaped planar contour** of `psi=psi0`, revolved around the axis without intersection, is a **standard unknotted torus**, not a knotted toroidal tube around the `T(3,4)` orbit. A `T(3,4)` trajectory lies *on its boundary*. Its solid-torus core is a planar circle (unknot).
- Registered neighboring levels `(0.9, 1.0, 1.1)*psi0` possess different field-line winding numbers; not all trajectories close after four meridional circuits. This does **not** falsify the exact material invariance of the level surfaces.
- These results do not qualify a localized knotted finite-core vortex, a self-consistent perturbed 3D Euler solution, or any particle identification.

### Parent evidence held immutable

The ZIP embeds the frozen original `v0.2.0` outputs, including its `GATE_LEDGER.json`, `RUN_SUMMARY.json`, `SOURCE_SEAL.json`, `TORUS_TUBE_CONTROLS.json`, and `CANDIDATE_LINE.npz`. `baseline/BASELINE_IMPORT_SHA256.json` checks exact source artifact bytes before every run. Parent failures `T5=FAIL` and `T6=FAIL` persist; parent stability gate `T8=UNRESOLVED` persists. These historical gates are not counted as fresh gates.

## Run on Windows

From the `A063-v0.2.1` directory:

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd FULL
```

`BASIC` reduces mesh ray count. `FULL` computes 384-meridional-point meshes per level, additional 96/192/384 refinement checks, and writes:

- `A063_Hicks_Invariant_Surface_v0.2.1-outputs/INVARIANT_SURFACE_CONTROLS.json`
- `.../GATE_LEDGER.json`, `RUN_SUMMARY.json`, `SOURCE_SEAL.json`, `PSI_LEVEL_MESH.npz`, `CANDIDATE_LINE.npz`
- `A063-v0.2.1-reports/A063-v0.2.1_FALSIFIER_REPORT.tex`
- `A063-v0.2.1-reports/A063-v0.2.1_FALSIFIER_REPORT.pdf` (uses `pdflatex`, or ReportLab as automatic fallback when LaTeX is absent)
- Three reproducible graphs in `A063-v0.2.1-reports/`.

For Linux/macOS: `python -m pip install -r requirements.txt && bash run_all.sh FULL`.

## Current FULL gate summary

**7 PASS; 2 FAIL (S6, S7); 3 UNRESOLVED (S9, S10, S11); 17/17 pytest tests.**

`S6=FAIL` only invalidates **the ordinary axisymmetric psi-level torus as an isolated T(3,4)-knotted core**. It does **not** prove all nonaxisymmetric or time-dependent knotted material tubes impossible.

`S7=FAIL` means neighboring invariant tori do not all carry same rational closed-line winding. It does **not** prove instability in 3D Euler.

`S9=UNRESOLVED` remains a strict blocker for the general 3D finite-core existence and stability claim. `S10=UNRESOLVED` records that independent C++ FP64 and framework v1.0.7 FREEZE/CERTIFY are **not** executed.

## Build and provenance

The locally sealed source files have SHA-256 hashes in `SOURCE_SEAL.json`; this is **not equivalent to v1.0.7 blind protocol FREEZE**. E013 independent provider geometries are **not** silently inserted. This package is a mathematical reference input to potential A046/A054/A055/A057 successors only, not a claim that those falsifiers were rerun.
