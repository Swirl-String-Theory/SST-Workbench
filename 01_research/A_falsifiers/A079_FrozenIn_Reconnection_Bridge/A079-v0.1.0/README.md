# SST Topological Transport Certificate (STTC) — concept v0.1.0

**Status: DEVELOPMENT / ANALYTIC_CONTROLS_ONLY** — no inference about physical gravity, intrinsic knot stability, full Euler reconnection, or SST verification.

This isolated, install-free (apart from `numpy`) concept bridges the two 2026 gravitational field-transport papers to the classical Euler vorticity structure. It includes a **counterexample** demonstrating that non-ideal helicity change is not, by itself, reconnection.

## Commands (Windows)

```bat
python -m pip install numpy
run_all.cmd SELFTEST
run_all.cmd BASIC
run_all.cmd FULL
```

`FULL` deliberately does not run a physical knot simulation without source-qualified trajectories. An optional `--e011 PATH` performs **metadata precheck only** (not source/geometry verification). It does not confer physics admission.

Results: `./SST_FrozenIn_Reconnection_Bridge_v0.1.0-outputs/` and archive `../SST_FrozenIn_Reconnection_Bridge_v0.1.0-outputs.zip` with `.sha256`.

## Mathematical concept

For constant-density unforced incompressible inviscid Euler:

    dv/dt + (v.grad)v = -grad(p)/rho_f,  div v = 0

The fluid one-form `alpha = v_i dx^i` has vorticity two-form `beta=d alpha` and

    (partial_t + Lie_v) beta = 0.

Equivalently, with `B = p/rho_f + |v|^2/2`, `A = v_i dx^i - B dt`, `F=dA`, and `U=partial_t+v^i partial_i`:

    interior_U(F) = 0; Lie_U(F)=0.

These are *formal analogues* of the paper's tetrad-valued gravitational frozen-in equations, **not** a derivation that its `F^(a)` equals physical fluid vorticity.

For a non-ideal vector residual `r = partial_t v - v x omega + grad B`:

    partial_t omega = curl(v x omega) + curl r,
    dH/dt = 2 int r.omega dV     (no net boundary helicity flux),
    dPhi/dt = int_S curl r.dS   (material surface).

A smooth field `zeta` with `r=zeta x omega+grad(chi)` may re-express vorticity transport with `w=v+zeta`. Failure of that local representation is **not by itself** sufficient for topological reconnection, which requires proof that the vector field's connectivity actually changes.

## Checked gates

* ABC Beltrami stationary incompressible Euler solution; spectral curl and divergence; helicity integral; independent central-difference convergence.
* Exactly decaying viscous Beltrami field: nonideal helicity loss, but fixed field-line directions; negative reconnection control. Independent RK4 temporal-convergence check at fixed final time.
* Kinematic induction-only slippage manufactured field: nonzero `curl(r)` and a different smooth transporting `w` but no line reconnection. **This is not an Euler vorticity solution.**
* Two linked rings Gauss linking under a volume-preserving invertible affine deformation.
* Material trefoil local Cauchy circulation, flux and material tube volume under the same deformation (kinematic test, **not** self-consistent Euler knotted dynamics).
* Minkowski local rotating tetrad: flat metric but nonzero tetrad `dA` and frame helicity, exposing a frame-choice caveat.

## Existing family read-only integration map

* `A016-v0.2.2` H0–H4 / P0–P6: add **new** transport differential-form validation *without changing any preregistered gates*; respect the E011-v0.3.0 STATIC_READY admission and source hashes.
* `A007-v0.4.0-alpha.1` Q1: pair-linking and higher-invariant-needed flag. Milnor triple invariant is *not implemented here*, do not claim Borromean certification.
* `A037-v0.3.3` PC02: helicity proxy operator, mirror/parity and finite-core line reconstruction. No mechanical transport polarity is inferred from helicity.
* `A038-v0.5.1` PC04: use fully qualified, non-remapped or operator-split remap-corrected trajectories for time transport; avoid artificial continuous tangential motion.
* `A047` Euler regularity BKM: precondition on smoothness; currently inventoried/unqualified.
* `A060-v0.3.0` read-only cross-falsifier aggregator: consume evidence snapshots; never promote analytical PASS to physical PASS.
* `E010-v0.4.0`: source-native combined archive with development-only Ruban geometries. Not a substitute for E011 STATIC_READY or independent full 3D Euler dynamics.

## Workbench integration restriction

No source, catalog family, `FAMILY.yaml`, `project.json`, framework manifest, frozen thresholds, reveal key, or original output on Google Drive has been modified. Before a real Workbench release, revalidate the canonical framework v1.0.10 byte mismatch and source/version registry. This is a concept/proof-of-test, **not** a registered A-family version.

## References

* F. A. Asenjo, M. A. Winkler and L. Comisso, *Frozen-In Gravitational Fields*, PRL 136, 161401 (2026), doi:10.1103/6c4q-kx6f.
* L. Comisso and F. A. Asenjo, *Reconnection of Gravitational Fields*, PRD 114, 084095 (2026), doi:10.1103/lmqy-pf9k.
* H. K. Moffatt, *The Degree of Knottedness of Tangled Vortex Lines*, JFM 35, 117–129 (1969), doi:10.1017/S0022112069000991.
* W. A. Newcomb, *Motion of Magnetic Lines of Force*, Ann. Phys. 3, 347–385 (1958), doi:10.1016/0003-4916(58)90024-1.

### Real read-only E011 v0.3.0 source test

Supply the original E011 output ZIP and its `.sha256` sidecar:

```bat
run_all.cmd FULL --e011-zip "C:\path\to\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip" --e011-sha256 "C:\path\to\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip.sha256"
```

This verifies archive hash, CRC, release metadata, source/admission flags and compares provider-anchor writhe and the *existing* E011 provider-agreement verdicts for `3_1`, `5_2` and `6_1`. No actual XYZ coordinates or 3D dynamics are contained in this selected metadata-only ZIP. No new knot-topology certification is made.

## Portable verification package

The complete release archive contains the original verified E011-v0.3.0 static metadata ZIP and its exact upstream `.sha256` sidecar under `inputs/`. On Windows, double-click `run_all.cmd` (no arguments) to run the 20 analytical gates **and** the E011 read-only static metadata precheck, if that `inputs/` ZIP exists. Explicit `SELFTEST`, `BASIC` and `FULL` arguments still work.

For a full replay independent of the command wrapper:

```bat
python run_all.py SELFTEST
python run_all.py FULL --e011-zip "inputs\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip" --e011-sha256 "inputs\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip.sha256"
```

Five Python unit regressions pass, and the FULL gate ledger records 20 analytical controls. Two regressions explicitly reject a bad archive checksum and an ineligible source contract. The included E011 archive contains source metadata; it does not supply physical time trajectories. `INTEGRATION_PROTOCOL.md` details existing family adapter contracts, physical stop criteria and the need for independent 3D Euler knot trajectories.
