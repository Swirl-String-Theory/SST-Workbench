# A003 v0.3.1 — Dynamic Topology & Spatial Convergence Qualification

**Development / qualified diagnostic, NOT a physically certified Euler/PKLSA theory.**

This release extends A003 v0.3.0 without changing the frozen **A003-v0.1.2** atlas, earlier G5 baseline, E010 v0.3.1 source files, C005 v0.6.1 kernel, or the source-pinned **SST Falsifier Framework v1.0.10**. A local Framework with status `CANONICAL_FROZEN` is admitted by its *actual* RELEASE_INFO status and pinned `sst_falsifier/gates.py` SHA256. The earlier Google Drive maintenance snapshot stated `LOCAL_VALIDATED_CANDIDATE`; this package does not fabricate formal release certification.

## New in v0.3.1

1. **Four-mesh, common-final-time trajectory qualification**, both F3=T(2,3) and F4=T(3,5), using exactly N=150/300/600/1200 *nested decimations of the verified N1200 `uniform_t` source*. The existing four-resolution static G5 source family is unchanged. No N1200 data is created from interpolation or relaxed derivatives.
2. **RK4 C005-v0.6.1 external provider** at every stage, preserving source-unit time T=2. N150/300/600 execute fixed-T steps 4,8,16. N1200 executes 8 and 16 steps, so an order-of-four claim is not inferred from N1200 alone. Temporal residual comparisons and three spatial errors (150→300, 300→600, 600→1200) have separate pass/fail gates. Spatial PASS means **strictly monotone RMS errors**, not a demonstrated asymptotic order or an Euler result.
3. **40 actual snapshots** (F3/F4 × four meshes × t/T=0,1/4,1/2,3/4,1). Output includes all 40 XYZ arrays in `G6_DYNAMIC_TRAJECTORIES.npz`, plus t, curve length, rigid-fit deformation, centroid shift, and segment clearance diagnostics in JSON.
4. **3-D finite segment–segment minimum distance**, not misleading vertex-only distance. SciPy KD-tree is used **only as an exhaustive candidate-selection accelerator**: every segment pair capable of beating the provisional minimum lies inside an analytically conservative midpoint radius, and all candidate distances use exact segment endpoint/interior minimization. Both global nonincident separation and arclength-remote separation are recorded; synthetic crossing tests and exhaustive brute-force comparisons are included. The numerical contact tolerance `1e-7 × bounding diameter` is a source-unit screening threshold, not a physically derived vortex-core radius.
5. **Two primary independent raw polygon projection diagrams** per snapshot (`P0`,`P1` frozen); compute the integer Fox/Wirtinger determinant from Gauss code, depth/angle degeneracy flags, and compare to F3=3 / F4=1. A constant determinant, particularly F4's determinant 1, does *not* prove knottedness or ambient isotopy.
6. **Optional corrected pyknotid 0.5.3 Alexander + Vassiliev v3** on actual evolved polygons, via the same temporary scale-invariant crossing correction used in previous G5. Default `endpoints` mode checks P0 at t/T=0,1/2,1 and P1 at 0,1 for N600/N1200 (20 independent invariant observations total for F3/F4). `all` checks P0/P1 for all 40 snapshots (80 observations); `off` is explicitly UNRESOLVED. Missing/unknown provider, changed source guard, or numerical exceptions fail closed or remain UNRESOLVED, **never PASS**. The instrument does not patch site-packages permanently.
7. **E010 v0.3.1 native Workbench source resolver** continues to verify the run-local A003 source contract overlay with eight SHA256-pinned analytic carriers and two correlated source families. It does **not** commit canonical E010 registry modifications.
8. **Framework v1.0.10 GateLedger** with G6P10 (3D segment clearance), G6P11 (two projected diagrams), G6P12 (measured Alexander and v3), G6P13 (four-level spatial convergence), alongside G6P0/P1/P6/P7/P8/P9 and the unresolved physical G6. All gates continue diagnostic evaluation after a scientific FAIL (`strict_dependencies=False`); SHA256 or external source integrity violations abort.
9. **Historical endpoint replay** of v0.3.0 trajectory NPZ, if provided: extra 3-D and projected diagnostics of the 12 available original/final snapshot polygons only. This replay *does not generate* five snapshots, call C005, or promote new v0.3.1 evidence.

## Install

Unpack as a sibling of `A003-v0.1.2` (do NOT overlay v0.3.0):

```bat
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.3.1
```

Use your Workbench `.venv` with NumPy, **SciPy**, and ReportLab for the PDF; `pyknotid==0.5.3` and SymPy are needed for the live dynamic invariant gate.

```bat
set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
set "SST_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"

run_all.cmd                  REM legacy 384-file geometry audit + regression tests
run_all.cmd G6               REM new dynamic four-mesh qualification + measured topology
run_all.cmd COMPLETE         REM fresh bounded G5, then new dynamic G6
run_all.cmd G6_FULL          REM extra expensive full provider snapshot screen
run_all.cmd G6_LEGACY        REM original v0.3.0 temporal path, unchanged
```

The previous `run_all.cmd G6_FULL` meaning (one extra N1200 trajectory diagnostic) is subsumed into the new v0.3.1 default four-mesh/2-time-step qualification. The inherited v0.3.0 runner remains accessible via `G6_LEGACY` and `TEMPORAL`.

Customize without editing sources:

```bat
run_g6_dynamic.cmd --g5-summary "C:\path\QUALIFICATION_SUMMARY.json" --epsilon 0.05 --final-time 2
run_g6_dynamic.cmd --provider-topology off
run_g6_dynamic.cmd --provider-topology all
run_g6_dynamic.cmd --preflight-only
```

`--provider-topology off` does NOT certify topology. All `--epsilon` values are hypotheses in **dimensionless source atlas units**, and T is an **uncalibrated model time**. A repeated run always creates a new unique output directory outside the versioned adapter source:

```text
../A003_Fourier_Knot_Import_Adapter_v0.3.1-outputs/<UTC_RUN_ID>/
  GATE_LEDGER.json
  G6_DYNAMIC_SUMMARY.json
  G6_DYNAMIC_DIAGNOSTICS.json
  G6_DYNAMIC_TRAJECTORIES.npz
  E010_A003_RUNTIME_SOURCE_CONTRACT.json
  E010_A003_CARRIER_LEDGER.json
  A003_v0.3.1_DYNAMIC_QUALIFICATION_REPORT.pdf
  PDF_RENDER.json
```

`run_all.cmd COMPLETE` writes a new G5 release-compatible receipt in the same sibling `-outputs` root before doing G6. Failures of scientific gates do not silently overwrite earlier evidence.

Exit codes: `2` = at least one scientific FAIL; `3` = numerically successful but G6 unresolved (the normal current overall outcome); `4`/exception = infrastructure/hash/version failure. The physical G6 status is always **UNRESOLVED** in this release, regardless of other PASS values.

## Reference gate meaning

| Gate | Tested property | Scientific limit |
|---|---|---|
| G6P0 | exact v1.0.10 gate source + local freeze status | local metadata not independently authoritative freeze audit |
| G6P1 | frozen 384-record atlas + measured corrected G5 ledger | only bounded F3/F4 static G5 screen |
| G6P6 | E010 v0.3.1 native source contract overlay | not persistent canonical PKLSA registration |
| G6P7 | actual C005 v0.6.1 source kernel + RK4 at fixed T | no pressure-Poisson/Euler closure |
| G6P10 | true 3-D segment–segment gap at five sampled times | no *continuous-in-time* intersection exclusion |
| G6P11 | independent Gauss-code/Fox determinant on P0/P1 | F4 determinant1 not identifying knot |
| G6P12 | corrected pyknotid Alexander and signed v3 | bounded numerical invariant screen; not mathematical proof |
| G6P13 | same-T nested 150/300/600/1200 final RMS monotonicity | not established second-order spatial convergence |
| G6P8 | permanent canon E010 carrier index | UNRESOLVED — no upstream mutation |
| G6P9 | continuum Euler finite-core calibrated time dynamics | UNRESOLVED — no PDE solver |
| G6 | physical SST knot/clock gravity claim | UNRESOLVED |

Additional caveats: the dynamical 3-D filament model does not implement adaptive remeshing, reconnective core physics, helicity/energy closure, pressure boundaries, physical circulation calibration, independent ensemble data, or finite-time certified separation bounds. Shape after optimal rigid fit is a *diagnostic*, not a physical force or frequency measurement. Numerically perfect divergence of the instant C005 kernel is not independently validated Euler dynamics.

## Historical v0.3.0 evidence replay (optional)

```bat
python g6_dynamic_replay_v031.py --v030-run "C:\path\A003_v0.3.0_G6_RUN" --out "C:\path\replay_endpoint_v031.json"
```

It verifies the exact v0.3.0 saved NPZ checksum against `G6_TEMPORAL_SUMMARY.json` and independently computes both projection determinants and exact finite 3-D segment distances at t=0 and t=T for N=150/300/600. The 12 comparisons can be diagnostically PASS; **neither t=1/4 nor t=1/2 nor t=3/4 exists in the inherited NPZ**, and N1200 was not archived. Do not report this as a completed v0.3.1 FULL run.

## Scientific evidence status

Previous Windows v0.3.0 G5/G6 outputs are genuine source evidence. The new v0.3.1 algorithm is software-tested using synthetic torus knots and mathematical RHS test doubles that cannot promote a real provider PASS, and a separate replay re-evaluates historical v0.3.0 *endpoints*. The **actual native v0.3.1 time evolution at N1200 plus pyknotid-evolving invariants must run on your Windows Workbench** before its new empirical gates can be evaluated.
