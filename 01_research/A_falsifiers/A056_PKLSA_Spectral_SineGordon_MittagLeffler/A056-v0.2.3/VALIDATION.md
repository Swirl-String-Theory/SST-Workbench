# A056 v0.2.3 validation

**Release:** A056-v0.2.3  
**Framework:** SST Falsifier Framework **v1.0.4 CANONICAL_FROZEN**  
**Validation date:** 2026-10-07  
**Status:** **IMPLEMENTATION_VALIDATED / PHYSICS NOT ESTABLISHED**

## Canonical framework pin

A056 v0.2.3 was regenerated as a thin scientific instance of the user-supplied frozen framework, not patched forward from A056 v0.2.2.

- framework version: `1.0.4`
- status: `CANONICAL_FROZEN`
- canonical Workbench path: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.4`
- supplied framework ZIP SHA-256: `1bdf8a20f0f0cbdf86ab89fb198d1930e0694579dee8d5dcd35149972c0d2104`
- framework package-manifest SHA-256: `1a9e98ee7762ab12746e5327a6552348d5e2edbee8ddaebc557ebaeb261e7452`
- frozen A056 protocol bundle SHA-256: `37fba708c58fbc7edc2068dd06157928841c3b09cb5280f4506faa29b9e14426`

The frozen A056 protocol was re-verified after all non-protocol release/packaging changes. No frozen threshold, gate definition, science contract, source contract, blind policy, commitment, or report source was modified after freeze.

## Static and protocol validation

- A056 public tests: **10 passed**.
- SST Falsifier Framework v1.0.4 selftests: **37 passed**.
- Python compile check: **PASS**.
- canonical science contract validation: **PASS**.
- canonical source contract validation: **PASS**.
- canonical gate-plan validation: **PASS**.
- canonical report-contract validation: **PASS**.
- public-source blind scan: **PASS**, zero forbidden-term hits.
- blind commitment SHA-256: `66a077233038ec60322d94fcbdd442456c2c84d3b0477971db11ea2aca2e8048`.
- frozen protocol verification after release assembly: **PASS**.

## FULL synthetic acceptance campaign

The five bundled synthetic provider cases are implementation controls only. They are not physical SST evidence.

The private reveal validator matched all five hidden phase labels and all five hidden relaxation labels (**10/10 classifications correct**). Individual synthetic truth labels remain confined to the private/revealed boundary and are intentionally not reproduced in this public validation document.

The private reveal validator therefore returned `IMPLEMENTATION_VALIDATED`.

### Gate result

| gate | result | interpretation |
|---|---|---|
| G0 | PASS | frozen protocol and blind commitment verified |
| G1 | PASS | 5/5 provider cases admissible |
| G2 | PASS | 5/5 spectral cases qualified; ML alpha=1 null limit verified |
| G3 | PASS | 4 discovery cases; 3 phase, 3 memory |
| G4 | PASS | 4 confirmed cases; 3 phase, 3 memory |
| G5 | PASS | 4 confirmed cases certified; C++/OpenMP FP64 parity executed |
| G6 | DEFERRED | optional SYCL FP32/DD32 screening not run in this container |
| G7 | NOT_RUN_PREREQUISITE | only synthetic-control evidence is present |
| G8 | NOT_RUN_PREREQUISITE | no eligible physical cross-source replication |
| G9 | PASS | reveal and forbidden-term commitments verified |

Final synthetic conclusion:

```text
implementation_conclusion = JOINT_CONTROL_RECOVERED
physical_conclusion       = NOT_ESTABLISHED
certified_cases           = 4 / 5
```

This is the intended v1.0.4 Gate-5/Gate-7 behavior: synthetic controls may validate implementation replication but cannot promote themselves to physical cross-source evidence.

## Numerical certification

The Mittag-Leffler exponential null limit satisfied

\[
\max_t\left|E_{1,1}(-t/\tau)-e^{-t/\tau}\right|
=1.1102230246251565\times10^{-16}.
\]

For the confirmed Sine-Gordon cases, C++/OpenMP FP64 phase-feature parity relative \(L_2\) errors were approximately

\[
4.40\times10^{-18},\quad 4.14\times10^{-18},\quad 5.04\times10^{-18},
\]

and the confirmed Mittag-Leffler cases gave approximately

\[
1.20\times10^{-14},\quad 9.49\times10^{-15},\quad 3.97\times10^{-15},
\]

all far below the preregistered \(10^{-10}\) certification tolerance.

The local validation host compiled the instance backend as C++17/OpenMP FP64 with GCC 14.2. The package itself declares `pybind11>=2.12`; for this isolated container run, already-installed pybind11-compatible headers were exposed through a temporary validation-only shim because the `pybind11` Python package itself was not installed. No shim or compiled artifact is included in the source release. The user's canonical Windows framework remains responsible for normal MSVC/setuptools provenance on the Workbench machine.

## GPU/DD32 status

A056 inherits the canonical v1.0.4 precision policy unchanged:

- Python/NumPy FP64: `REFERENCE`;
- C++17/OpenMP FP64: `CERTIFICATION`;
- SYCL FP32: `SCREENING_ONLY`;
- SYCL DD32/FP32x2: `SCREENING_ONLY`, not IEEE FP64.

No Intel Arc/oneAPI device was available in this container, so A056 G6 was intentionally `DEFERRED`. `FRAMEWORK_PIN.json` preserves the canonical framework's supplied target-machine backend-selftest and DD32 validation hashes; those are framework provenance, not a claim that this A056 container run repeated the Arc campaign.

## PDF/report validation

The framework published `A056-v0.2.3_FALSIFIER_REPORT.pdf`. The final revealed report was rendered to page images at 160 DPI and all **8 pages** were visually inspected. The original generic auto-results table exposed long gate/provenance fields beyond the A4 margin. A056 now performs a local **post-run presentation-only** replacement of generated `AUTO_RESULTS.tex` with wrapped tables, republishes the PDF, refreshes the output manifest and repackages the corresponding archive. The frozen v1.0.4 framework and frozen A056 scientific protocol remain untouched.

Final PDF visual check: **PASS** — no clipping, overlapping text, or broken glyphs observed.

## Packaging validation

- `A056-v0.2.3-outputs_BLIND.zip` is generated before reveal and remains blind.
- `A056-v0.2.3-outputs_REVEALED.zip` is refreshed after the private smoke validator, so it contains `revealed/A056_SMOKE_VALIDATION.json`.
- `A056-v0.2.3-outputs.zip` is the complete revealed output tree.
- all release ZIPs receive SHA-256 sidecars.
- source packaging excludes `.venv`, build products, compiled native modules, caches and generated output folders.

## Scientific boundary

A056 v0.2.3 has validated the implementation and canonical framework integration. It has **not** established Sine-Gordon or fractional-memory physics for SST. The first physical campaign must supply provider-native dynamics satisfying `A056-DYNAMIC-PROVIDER-4`, pass G5 C++/OpenMP FP64 certification, and provide eligible `independent_source`/`experimental` evidence sufficient for canonical G7 cross-source replication.
