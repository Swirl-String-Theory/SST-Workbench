# A058 v0.2.10 — release validation

**Release category:** source + offline regression + historical-data requalification.  
**Framework pin:** SST Falsifier Framework **v1.0.8**. The actual Framework FREEZE and Windows KnotPlot science run require the user's installed Workbench. No new real KnotPlot run was performed by the release builder.

## Scientific and implementation corrections

- Eight anonymous slider axes, six sector references, one independent activation control, 264 single-slider perturbations: **271 registered conditions** (not 272).
- BASIC=32/128/512, 2048=32/128/512/2048, HEAVY up to 31=32/128/512/2048/8192/32768. Endpoints are matched-iteration observations, **not** convergence certifications.
- A numerical getter formatted with six digits after the decimal is compared with at most half a displayed unit (`5e-7`) and minimal FP parse slack. This is a **ROUNDED_GETTER** qualification, not proof of exact internal FP64 assignment.
- S3 now has a compulsory real numeric getter alias. R2 and R3 have explicit switch getter aliases. OFF/ON checks reject a missing getter when an alias is declared.
- Affected import and runtime records retain opaque IDs and hide semantic parameter mappings in `private/`.
- Historical BLIND G0–G9 ledger and v0.2.9 output ZIP/PDF are **never modified**. `IMPORT_BASIC` creates a separate local audit overlay bound to SHA-256 hashes of the original manifest, runlog, runtime, individual qualified logs and final coordinates.

## Executed checks

| Check | Observed result |
|---|---|
| Python unit and regression tests | **49/49 PASS**, with disposable import-only Framework-v1.0.8 scaffold for the test harness |
| Python compileall | PASS |
| Private material lengths | two independently generated 32-byte values |
| Public blind forbidden-term source scan | **0 hits** |
| LaTeX `pdflatex -halt-on-error` | PASS, report template 3 pages |
| Historical v0.2.9 real BASIC data requalified from supplied `campaign_private.zip` | **237/271** complete, including **143** source FAIL statuses consistent with getter rounding |
| Historical unsupported runtime | **34** (not treated as zero responses) |
| Heavy selection from requalified historical data, prior to any heavy results | **27** conditions: 5 references, 1 activation control, 7 × 3 response probes |
| Imported historical runlog and other original source files modified | **No** |
| ZIP content / package manifest SHA-256 | Verified at build time |

## Known limits and qualifications

- The framework installed on the user's Windows host is required for the actual `run_all.cmd FREEZE`, native MSVC build and Framework report/gate publication. The real Framework source modules were not installed in this Linux validation; **do not claim a completed actual v1.0.8 FREEZE for this release**.
- The drag/R4 sector still has the previously observed freeglut runtime limitation, and may remain `UNSUPPORTED_RUNTIME`.
- The previously observed `khat_mag is zero` warning remains a geometry/projection quality caveat. Its presence does not replace the explicit safety check.
- `IMPORT_BASIC` requires the original A058-v0.2.9 root with private runtime logs, 271-condition BASIC run and calibrated seed. It refuses to overwrite a pre-existing BASIC target and does not rewrite the old BLIND report.
- Newly prepared v0.2.10 seed must hash-identically match the prior v0.2.9 BASIC seed before those imported data may select a 32768 run; otherwise heavy selection fails closed.
- Because the source old BLIND ledger remains unchanged, the retrospective overlay does not turn its original G1/G2/G8 FAIL into PASS.
