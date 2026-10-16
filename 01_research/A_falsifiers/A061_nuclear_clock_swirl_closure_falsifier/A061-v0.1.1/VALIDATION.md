# A061 v0.1.1 — Release validation

**Scientific state:** IMPLEMENTATION AND FRAMEWORK INTEGRATION VERIFIED; PHYSICAL SST CLOSURE NOT ESTABLISHED.

- Framework: v1.0.7 CANONICAL_FROZEN, exact user-supplied archive SHA-256: `139800c75be8fea0b581c3a7c5db96d29c9231d7b9e30e9fdbc1888e741a6462`.
- Framework source-manifest check: **PASS** (92 source records).
- Official framework unit tests: **56 passed**.
- A061 science regression tests: **8 passed**.
- Official protocol freeze bundle SHA-256: `4069ca3ca2bde5fa8822ad67181e693bc47a8aa9c25da01ff5bedfaa3e3d94fd`.
- Official FULL blind run completed, 14 independent gates recorded; downstream gates executed despite G3 failure.
- Published measurement algebra G1: PASS (not a physics conclusion).
- SST-28 printed circulation plateau G3: FAIL (formula inconsistency under cited assumptions).
- C++/pybind official certification G5: UNRESOLVED on build host because `pybind11` not installed; source included for target build.
- Raw chronometric source G11: UNRESOLVED (no raw time series fetched in sandbox).
- Differential susceptibility G12: UNRESOLVED; no source-derived preregistered SST species prediction.
- PDF report: **PASS**, 4-page A4 render visually inspected.
- REVEAL_IF_ALLOWED: correctly WITHHELD because G12 UNRESOLVED.
- Wrapper CERTIFY fails closed when critical science/backend gates are not PASS.
- `src` bundle includes no altered framework. Source paper PDFs accompany release.

The manuscript's $S_n(r_c)$ discrepancy is a local source-expression audit and must not be used to claim the entire SST theory is disproved. Neither synthetic controls nor numerical parity, if available, constitutes an observed nuclear-clock effect.
