# Wien–Planck SST Field–Matter Closure Falsifier v0.4.1

**PKLSA-2352 + GPU qualification funnel release.**

v0.4.1 replaces the trefoil-only PTSA discovery population of v0.3.x with the complete self-contained **SST Parametric Knot–Link Seed Atlas (PKLSA) v0.1.0**:

\[
49\ \text{families}\times48\ \text{variants}=2352\ \text{candidate centerlines}.
\]

The Universal-Action branch remains maximally anti-circular: pre-reveal dynamics and scoring use only dimensionless geometry and numerical controls with \(L_{\hat{}}=\Gamma_{\hat{}}=1\). No SST canonical constants, SI scale, \(h\), or \(\hbar\) enter screening, qualification, mode discovery, energy extraction, action scoring, or candidate selection.

## Why a GPU funnel

Running the full v0.3.1 frozen-mode/action campaign directly on all 2352 candidates would spend most compute on poor carriers. v0.4.1 therefore preregisters a four-stage funnel:

```text
PKLSA 2352
   |
   | Stage 1: SYCL FP32 instantaneous Biot–Savart strain screen
   | fixed quota: top 8 per family
   v
392
   |
   | Stage 2: SYCL FP32 short RK2 invariant-shape / mesh screen
   | fixed quota: top 2 per family
   v
98
   |
   | Stage 3: CPU-double C++/pybind11 dynamic seed qualification
   | max one finalist per family
   v
12 BASIC / 16 EXTENDED-HIGHRES
   |
   | Stage 4: CPU-double frozen normal mode + matched energy/frequency action test
   v
STRICT BLIND verdict
```

The GPU **never issues the final scientific PASS**. It only reduces the broad search space. Stage 3 and Stage 4 are CPU-double reference calculations. The default GPU chain also requires a CPU↔GPU parity gate before Stage 1.

## GPU screening metrics

Stage 1 ranks candidates *within each topology family* using the rigid-motion-invariant pair-distance strain rate

\[
\dot d_{ij}/d_{ij}
=\frac{(\mathbf x_j-\mathbf x_i)\cdot(\mathbf u_j-\mathbf u_i)}{|\mathbf x_j-\mathbf x_i|^2},
\]

aggregated as RMS over preregistered lags. Rigid translation and rotation give zero strain. Lower strain is preferred; speed-CV and initial mesh-CV are deterministic tie-breakers.

Stage 2 applies a short target-free RK2 screen and measures the RMS log-change of a pair-distance signature,

\[
D_{\rm shape}
=\sqrt{\left\langle \log^2\!\frac{d_{ij}(t_1)}{d_{ij}(t_0)}\right\rangle},
\]

plus final mesh CV and edge ratio. These quantities are invariant under global translation and rotation. Stage 2 is still only a coarse screen; v0.3.1's stricter adaptive-RK4 qualification is retained downstream.

## Default Windows run

Intel oneAPI/SYCL path:

```bat
run_all.cmd
```

The chain performs:

```text
run_00_setup.cmd
run_01_build_native_clean.cmd
run_02_selftest.cmd
run_03_seal.cmd
run_04_blind_guard.cmd
run_06_verify_pklsa.cmd
run_07_build_gpu.cmd
run_08_gpu_parity.cmd
run_12_gpu_funnel.cmd
run_13_inventory_staged.cmd
run_15_seed_qualify.cmd
run_20_campaign.cmd
run_30_blind.cmd
```

The GPU build searches for Intel `icx`; if necessary it initializes the standard oneAPI `setvars.bat`. The broad screen uses an FP32 SYCL executable because this stage is non-final; the selected survivors are re-evaluated in CPU double precision.

If SYCL is unavailable, the same screening metrics can be run with the much slower CPU reference implementation:

```bat
run_all_cpu_fallback.cmd
```

The output explicitly records `backend=cpu`; no GPU claim is made.

## Profiles

- `config/basic.json`: 2352 → 392 → 98 → **12 distinct-family finalists**, action resolutions 64/96.
- `config/extended.json`: 2352 → 392 → 98 → **16 distinct-family finalists**, action resolutions 96/128.
- `config/highres.json`: same broad funnel, **16 finalists**, action resolutions 128/192/256.

`EXTENDED` and especially `HIGHRES` can be computationally expensive after the funnel because frequency certification can extend the dimensionless trajectory horizon iteratively.

## Strict-blind outputs

Results use the project convention:

```text
./Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs/
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs.zip
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs_BLIND.zip
```

The two shareable archives created by the blind run exclude `private_reveal_keys`, raw identity-bearing observations, private campaign records, GPU candidate maps, and the Stage-C materialized identity mapping.

Reveal is manual:

```bat
run_40_reveal.cmd
```

which additionally creates:

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs_REVEALED.zip
```

## Reveal semantics

Reveal resolves the staged opaque finalists back through the private funnel map to their PKLSA candidate IDs, topology families, variant indices, construction method, and atlas parameter records. Absolute comparison to \(h\) or \(\hbar\) remains impossible unless an independently sourced SI normalization is deliberately supplied after the blind result has been frozen.

## Generation-time validation

The final package audit reports: PKLSA 49/49 families and 2352/2352 candidates, strict-blind leakage guard PASS, 18 Python tests with 17 PASS / 1 native-extension SKIP, and a complete 2352-candidate CPU-reference funnel traversal at reduced validation resolution. A tiny end-to-end campaign/reveal smoke test also passes the new funnel preflight and blind-seal integrity checks.

Intel oneAPI/SYCL is not installed in the generation environment, so **no SYCL compile/run PASS is claimed here**. The Windows default runner must build the GPU executable and pass GPU↔CPU-native parity before screening.

## Scientific status

This is a regularized centerline model, not a complete 3-D finite-core Euler solver. PKLSA is a constructive topology-preserving seed atlas, not an independent complete knot-invariant solver. GPU screening is explicitly approximate and non-final. A blind PASS can therefore establish only a **dimensionless numerical centerline Universal-Action candidate** pending stronger finite-core and provenance tests.

See `docs/V0.4.0_METHOD.md`, `docs/GPU_FUNNEL.md`, `PROVENANCE_AUDIT.md`, and `VALIDATION.md`.


> **v0.4.1 hotfix:** fixes interpreter-specific PKLSA bytecode-manifest failure seen on Python 3.14; scientific v0.4.0 protocol unchanged.
