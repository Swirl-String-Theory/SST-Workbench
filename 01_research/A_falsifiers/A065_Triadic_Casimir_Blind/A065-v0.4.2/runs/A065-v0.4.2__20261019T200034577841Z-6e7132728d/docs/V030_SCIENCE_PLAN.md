# A065-v0.3.0 scientific protocol and source trace

## 1. Model hierarchy

- **A0:** incompressible Euler: `div u=0`, `∂t u+(u·∇)u=-∇p/ρ`, `ω=curl u`, `Δp/ρ=|ω|²/2-||S||²`; analytic controls only.
- **A1:** a real, stored **KnotPlot N300 3_1 centerline** (300 coordinates) gives a regularized finite-segment Biot–Savart velocity. It is a geometric diagnostics model; not a certified vortex core.
- **A2:** an explicitly *exploratory* filament ODE `dX_i/dt = B_ε[X](X_i)`, integrated with RK4 and fixed physical simulation end time. `B_ε` uses circulation `Γ=1`, isotropic regularization `ε=0.12`, and midpoint-segment quadrature. No fundamental parameter is fitted to observed Casimir forces.
- **A3:** Euler matter clock and compact U(1) link field have a formal gauge-covariant relative phase `Θ_AB=θ_B-θ_A-Σ_e ϑ_e`; actual matter-link source term and atomic modes are not yet derived.
- **A4:** a two-sheet classical thermal scalar toy can be evaluated from given one-body susceptibilities and reflectivities, providing independent force/stress numerical controls. This is neither the metallic Casimir effect nor quantum zero-point physics.

## 2. Filament equations and numerical gates

`B_ε[X](x) = Γ/(4π) Σ_j [ (X_(j+1)-X_j) × (x-(X_j+X_(j+1))/2) ] / ( |x-(X_j+X_(j+1))/2|² + ε² )^(3/2)`.

Four-stage RK4 on the 75-node point subset; compare `N_t=4` and `N_t=8` time steps, fixed `T=0.04`:

`E_t=RMS[X^(4)(T)-X^(8)(T)]/RMS[X^(8)(T)-X(0)]`, preregistered tolerance `E_t < 10^-3`.

Separate 75/150-node spatial scan with the same `T`, `ε` and `N_t=8`:

`E_x=RMS[X_75(T)-downsample_2(X_150(T))]/RMS[X_75(T)-X_75(0)]`, preregistered tolerance `E_x < 0.05`.

**Observed:** `E_t=2.0246e-11` PASS; `E_x=0.0872896` FAIL. No threshold retuning within this version. Although the dt control passes, the discrete velocity/trajectory has not reached required spatial convergence; a physics claim is invalid. Further work should test N=150/300 and core scaling, *in a new preregistered version*, and independent provider plus boundary conditions.

## 3. E010 independent-source gate

The E010 production metadata identifies independent upstream geometry family `fremlin:3_1`, carrier `CAR_d8a316361e0941af` (catalog `A006`), source `03_data/A_knots/02_fourier/resources_swirl/3_1/knot.3_1u.short`, raw SHA256 `73cd5304e79a9cf52b71c88d1d7ebc21948a6d87526b0e95ba5aa6f257150e80`.

The raw file is **not** in the public v0.3.0 release. `PROVIDER` looks for those exact original bytes and reports one of: `UNRESOLVED_SOURCE_MISSING`, `FAIL_RAW_HASH_MISMATCH`, `UNRESOLVED_PARSER_REQUIREMENT`, `PASS_RAW_HASH_AND_XYZ_PARSER_ONLY`. Nothing here yields independent physics validation. Source records and references are in D01 and must be SHA256 verified before interpretation.

See E010 v0.3.1 source metadata and its source-independence ledger. The `knotplot_fourier_series` copies tied to Fremlin are mirrors, **not** independent families; the v0.2.0 source is `knotplot_relaxed:3_1` only.

## 4. Official framework gates

- **G0:** freeze protocol integrity. PASS only after v1.0.7 verifies source, science, gate, report and commitments.
- **G1:** verify all three bundled source datasets; registered-but-unavailable Fremlin is NOT a second qualified source.
- **G2:** all analytic and numerical gates; **FAIL** because `D01_G08` fails spatial refinement.
- **G3:** `NOT_RUN_PREREQUISITE`; no target-free physical Casimir prediction, G2 FAILED.
- **G4/G5:** independent source confirmation and CPU-native physical FP64 certification remain closed behind G3. Dedicated C++17 velocity-kernel parity is an auxiliary *numerical* test, not G5.
- **G6/G7/G8:** GPU screening, multi-family and physical mechanism not promoted.
- **G9:** reveal policy: fail closed; compare neither physical nor toy targets until preregistered gates permit.

Framework version v1.0.7 is `CANONICAL_FROZEN` and must remain unmodified. This ZIP provides the **scientific instance adapter**, not a vendored or reconstructed framework.

## 5. Blind data separation

Dataset seals D01/D02/D03 are independent manifests; source reference SHA256 is committed separately. The private target (historical analytic comparator) is intentionally omitted from public ZIP and supplied in a separate escrow ZIP. Hash commitments are not signatures. Any mutation in a dataset or in a blind output causes verification failure. New physics must be introduced as A065 v0.4.0 or later, not by overwriting v0.3.0 source or relaxing the gate.
