# A064 v0.1.0 — PKLSA Geometric Holonomy & Interference

**Status:** numerical pilot, `GEOMETRY_ONLY_NOT_PUBLICATION_READY`; **not** an SST phase/gauge/dynamic-stability discovery, **not** a framework-certified blind result.

This release contains four **actual SHA-256-verified geometry files** sourced from the registered `PKLSA_KnotPlot_Native_Census_v0.1.2` Google Drive folder. They are native KnotPlot coordinate geometry, not a new generated knot atlas or independent providers. The E010 v0.3.1 release metadata shows `full_campaign_gate_pass=false`, `publication_ready_geometry_layer=false`. The contemporary PKLSA v0.4.0 **integration contract** has been read, but a certified v0.4.0 carrier release itself was not available to ingest in this session.

## Actual bundle

- `data/native_census/knot_3.1.txt`: 47 beads, meridional-probe geometry control.
- `data/native_census/knot_5.2.txt`: 81 beads, meridional-probe geometry control.
- `data/native_census/knot_6.1.txt`: 96 beads, meridional-probe geometry control.
- `data/native_census/link_6.3.3.txt`: 97 beads, 3 components (35, 30, 32); separate pairwise linking estimates.
- `data/registry.json` and `data/RELEASE.json`, `data/CAMPAIGN_INDEX.json`: read-only provenance and release gates.
- `src/holonomy.py`: polygonal Gauss linking quadrature, regulated circulation, synthetic controls, probe construction.
- `src/runner.py`: numerical pilot & gate evaluation.
- `src/production_import.py`: **strict optional** PKLSA 0.4.0 manifest; requires release certification, qualification per carrier, source SHA, independent provider groups; generated providers rejected.
- `src/render_report.py`: reproduce `outputs/A064-v0.1.0_FALSIFIER_REPORT.pdf`.
- `docs/SCIENTIFIC_METHOD.tex`: full equations and LaTeX `\bibitem` references.
- `outputs/`: already executed local results.

## Run locally

On Windows with Python 3.10+ and the frozen SST Falsifier Framework v1.0.7 installed at the canonical Workbench `06_templates` path:

```bat
run_all.cmd
```

The launcher verifies `CANONICAL_FREEZE.json` and the existence of the installed framework. **It does not run the formal framework gate runner or inherit its blind/reveal machinery.** Such integration remains `G9 UNRESOLVED` and must be added without modifying canonical v1.0.7. The pilot uses its own numerical science runner, so numerical PASS is not framework certification.

Portable pilot (Linux/macOS, or Windows outside Workbench):

```sh
python -m pip install -r requirements.txt
python -m pytest tests -q
python src/runner.py --order 4
python src/render_report.py
```

`run_all.cmd` sets up a dedicated `.venv` and automatically generates PDF. Output is in `outputs/` and command returns nonzero on required-gate failure. All gates execute regardless of an earlier failure when the input for that gate is available.

### Qualified PKLSA 0.4.0 source import

`docs/PKLSA_0.4.0_manifest.schema.example.json` is an **example contract, not actual measured data**. Pin actual carrier paths and SHA values locally, including source role and independent provider. Then run:

```bat
.venv\Scripts\python.exe src\runner.py --pklsa-manifest "D:\path\to\qualified\manifest.json"
```

Compatible geometry inputs: `.npy`, `.npz` with `component_0, component_1, ...`, native text XYZ or JSON component arrays. A manifold/source without a valid qualification gate is **rejected**, not silently admitted. No file name fuzzy search or fabricated carrier metadata. A blind follow-on release should HMAC-pseudonymize provider and topology identities separately from a sealed reveal package.

## Numerical results of included input

| Carrier / probe | Lk (order 4) | Meaning |
|---|---:|---|
| `3_1` constructed meridian | +0.99990783 | Local linking positive control, **not trefoil-specific** |
| `5_2` constructed meridian | +0.99990814 | Local linking positive control, **not a spectrum** |
| `6_1` constructed meridian | +0.99990977 | Local linking positive control, **not a spectrum** |
| `link_6.3.3` components 0–1 | +0.9999999985 | Pairwise linking |
| `link_6.3.3` components 0–2 | -0.9999999993 | Pairwise linking |
| `link_6.3.3` components 1–2 | +0.9999999986 | Pairwise linking |

Synthetic Hopf and unlinked circles also pass. These numerical values result from the existing **native** coordinates, not from a fit to a physics model. `link_6.3.3` is **not** Borromean `L6a4`.

The optional diagnostic `P_toy=(1+cos(2π q Lk))/2` fixes `q=1/2` in advance to give `Z2` parity. It is an **algebraically guaranteed constructed control**: zero or unit probability is not evidence that vortex modes physically interfere. The dynamical phase connection remains an upstream unsolved problem. The finite-core regulator is expressed relative to native bead spacing, not the SST canonical SI core radius; there is **no justified SI conversion** for these coordinates.

## Gates

- `G0` source SHA-256, native component counts, and segment-pair clearance.
- `G1` integer linking residual < 0.035 (polygonal quadrature).
- `G2` order-2/order-4 convergence < 0.035.
- `G3` reversal, simultaneous translation, cyclic indexing.
- `GCTRL` Hopf and unlink references.
- `G4` Z2 toy interference arithmetic only.
- `G5` independent provider admission: unresolved for bundled data.
- `G6` physical phase-connection derivation: unresolved.
- `G7` physical interference and time-evolution measurement: unresolved.
- `G8` higher-order multi-component holonomy (e.g. Brunnian or Milnor invariant): unresolved.
- `G9` canonical v1.0.7 framework runner integration: unresolved.
- `G10` publication-grade PKLSA source certification: unresolved.

**Required numerical gates:** 33 PASS / 0 FAIL. **Science/source gates:** 6 UNRESOLVED. **Tests:** 12 PASS (12 of 12). These are separate counts and must not be conflated.

## Scientific interpretation

A candidate SST physical connection must be derived from an incompressible Euler/finite-core model and have units `m^-1`. One may form `A_eff=(2π q/Γ) v` algebraically using a filament Biot-Savart velocity, but this does not derive `q=1/2`, a `Z2` gauge group, quantum superposition, or actual propagation suppression. A chosen representation is a **hypothesis**, not a physical prediction.

The next required test is a preregistered mode-evolution experiment: use independently qualified PKLSA carriers, derive the mode and phase dynamics from the fluid equations (or explicitly label a surrogate wave equation), compare computed transfer functions to zero-field and random-phase controls, vary core and resolution independently, and require cross-provider stability before opening any physical interpretation gate.

## Provenance

- Frozen framework metadata: `https://drive.google.com/drive/folders/1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE` (`CANONICAL_FROZEN`, 56 v1.0.7 regression tests claimed by its own validation log; not rerun here).
- KnotPlot native census: `https://drive.google.com/drive/folders/1UeFlJjAAFiNQEKvr9fBRrh4UlTyr4UHV`.
- E010 v0.3.1 output: `https://drive.google.com/drive/folders/1ZD55-oQ0F_RQpHh5uBlP7CWn0Z3_I_QD`.
- Saner et al., *Nature Physics* (2026), `https://doi.org/10.1038/s41567-026-03400-6`.

This A064 label is **provisional**; no Workbench registry was modified and absence of collision in full registry was not certified.
