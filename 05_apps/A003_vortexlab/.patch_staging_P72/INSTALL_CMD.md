# A003 Twist Flow P7 v0.7.2 — Ideal Volume Transfer for Other Knot Embeddings

**Base:** P7 v0.7.1 CMD-r2 (exact source hashes), no installation on P7 v0.7.0 or unknown customized runtimes.  
**Scope:** Twist route `/twist-flow/`; original VortexLab root keeps opt-in disabled.  
**Status:** **research-track / visual reconstruction**, not physical finite-core or knot-isotopy certification.

## Scientific assumptions and formulas

For each *identified* single-component knot class `K`, use the corresponding Brian Gilbert ideal/tight Fourier source with `(L_ideal, D_ideal)` and ropelength `R_K=L_ideal/D_ideal` (diameter convention). **This is an independent reference object**, not a declaration that the selected nonideal seed is tight or correct.

Reference core radius only in the ideal reference state: `r_c = 1.40897017e-15 m`.

- `L_ref = 2 r_c R_K`
- `V_ref = π r_c² L_ref`
- For a nonideal seed, select a concrete and explicit comparison convention: **its transverse centerline radius `Rxy` equals the transverse radius of the Gilbert ideal embedding in its supplied orientation**. The ideal transverse radius is obtained by sampling the matching Gilbert Fourier curve at 512 points.
- With `q = Rxy_ideal / Rxy_source_scene` in m/scenemeter, `L_source_physical = q L_source_scene`.
- Mean-volume-equivalent initial core radius `a_source = sqrt(V_ref /(π L_source_physical)) = r_c sqrt(L_ref / L_source_physical)`.
- At subsequent accepted solver steps, material-segment radius `a_i(t) = a_source sqrt(l_i(0)/l_i(t))`; these radii are interpolated on mesh rings for display.
- Global geometric radius is measured from the *current* centerline, not from `a_i`.

**Crucial limitation:** Knot topology and ideal ropelength alone DO NOT determine the absolute physical size of another arbitrary embedding. The equal-`Rxy` mapping fixes an additional *comparison convention*. Changes to that convention alter the inferred tube diameter. P7.2 neither resolves the fluid pressure nor introduces an actual finite-core dynamical feedback. The observed `volumeRelativeError` is algebraic, not an independent physical-conservation test.

### Topology/provenance

- Accepted only for a **single component** with a recognized source label and a matching single-component Gilbert ideal reference from the shipped catalog.
- Supported examples: `ideal|3:1:1` (original rule), `fseries|3_1p`, `knotplot|knot_3.1`, `twist|KNOT_3_1_N1024_ORIG`, also other matched classes (`5_2`, `6_1`, etc. when Gilbert ideal reference exists).
- Exact source-label parsing; filenames and knot IDs are NOT proof of isotopy. Broken, folded or self-intersecting A006 candidates remain unqualified.
- N192 preview is explicitly flagged `REFERENCE_TRANSFER_PREVIEW`: downsampling might alter topology/material parameterization. Restore native N and reset for candidate qualification.
- Multi-component links, unknown labels, unqualified `.xyz`, contact/reach violations or changed material node count do **not** get the derived tube assigned automatically. For any unrecognized source, preexisting schematic-width display remains available.
- If there is strong, nonuniform stretching, the local *effective* material radius may vary along the filament. Real vortex-core cross-sections can also become noncircular; a circular visualization is only a proxy.

### Unchanged

- The velocity/Biot–Savart/local-induction kernels, `P.a`/`a_sim`, circulation, time integration, topology guard, reference source datasets and browser-rendering stack.
- Original `/` route; only `/twist-flow/` opts into the visual Model A extension.
- `package.json` is never modified and may have local changes.

## Windows CMD installation

Extract `A003_TwistFlow_P7_v0.7.2_CMD_PATCH.zip`. From **CMD** in the extracted patch directory:

```cmd
Apply-P7.2.cmd --dry-run
Apply-P7.2.cmd
cd /d C:\workspace\projects\SST-Workbench\05_apps\A003_vortexlab
npm start
```

Open `http://127.0.0.1:4173/twist-flow/`. Choose e.g. KnotPlot `3_1`, Fourier `3_1p`, or A006 `KNOT_3_1_N1024_ORIG`; under `Vortexbuis zichtbaar` verify `OVERDRACHT uit 3:1:1`. For scientific comparisons, disable N192 preview and use native resolution. The original root route remains unchanged.

Use `Apply-P7.2.cmd --target "C:\...\A003_vortexlab" --dry-run` for a nonstandard installation root. The Python 3 launcher (`py -3`) or `python` on PATH and Node.js must be available.

### Installer behavior

- Dry-run verifies all existing **exact P7.1 CMD-r2 SHA-256 baselines** and all patch payload hashes.
- Refuses unknown source modifications; never overwrites silently.
- Stores a complete backup in `.A003_P72_backups/CMD_<timestamp>` and restores files if a test fails.
- Runs P7.0, P7.1, P7.2 and relevant legacy regressions directly by Node.js; avoids reliance on modified `package.json` scripts.
- Preserves local `package.json` byte-for-byte.

### Release validation

- JavaScript `node --check` of the modified modules: PASS.
- P7.0 (10 tests), P7.1 (7), P7.2 (10), Twist P3/P4/P5, native resolution, XYZ, catalog geometry, fluid-qualification, tube/probe checks: PASS.
- `tools/verify-parity.mjs`: PASS on the exact assembled baseline.
- Browser end-to-end visual verification: **not certified** here; verify locally.

### Further falsifier gates

Test transverse-radius alignment sensitivity (alternate length/volume anchors), independent isotopy and thickness/reach verification, material conservation under true remeshing, spatial/time convergence, and self/mutual induction of live background filaments before making physical stability claims.
