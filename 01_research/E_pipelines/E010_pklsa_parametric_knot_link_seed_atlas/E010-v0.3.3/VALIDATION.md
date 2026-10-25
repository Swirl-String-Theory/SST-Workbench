# A058-v0.3.7 — Independent release validation

**22 October 2026 — DEVELOPMENT diagnostic package.** This is neither a physics certificate nor a new native 2026 execution.

## Actual local tests

- `A058_KPDIST_ZIP=/mnt/data/kpdist-23mar2025.zip python -m unittest discover -s tests -v`: **66/66 PASS**; uses the genuine uploaded 2025 KnotPlot distribution for static tests.
- Mocked full four-case native diagnostic passed in the regression suite. The mock validates relative vs absolute I/O and receipt writing only; it is **not** proof that the genuine Windows binary accepts or successfully evaluates the new scripts.
- v0.3.7 read-only historical qualifier executed on **both authentic user-uploaded** `A058_probes3.zip` and `A058_probes4.zip`; generated separate unchanged-source receipts under `evidence/2026_historical_qualification/`.
- Each archive: 2/2 original run receipt hash chains verified (original console log, native script, ASCII coordinates, original generator script, shared KPF seed). Native CSV `/l`, `/g` both zero while XYZ and console nonzero; **FAIL_MEASUREMENT_QUALIFICATION** for both dstep 1/4. `KP-alex.exe` helper opening failure captured. `dstep` getter **UNRESOLVED**, not PASS.
- The old 271-condition preregistered blind experiment has **not** been rerun, modified, reinterpreted, or promoted. A058-v0.3.7 inherits original v1.0.8 framework pin from the coordinator; no framework upgrade or physical solver replacement.

## Open before certification

1. Run fresh four-case diagnostic on the real October 2026 KnotPlot version using the `.lnk` and its genuine Start-in; inspect raw logs privately.
2. Determine whether native `data open` ordering changes `/l` and `/g` zeroing; require numeric CSV/XYZ agreement with bounded tolerance.
3. Confirm `dstep` is actually in `parameters` output with correct value; otherwise mark state unverified. No assumption that issuing `dstep = 1` proves assignment.
4. Determine dependency search path for `KP-alex.exe` and verify `alex -1` independently in a *separate* run if needed (not required for core length/Rg qualification).
5. Positive `safe` on two snapshots and static XYZ nonintersection **do not** certify no crossings during integration.
6. No SST vortex-fluid/Euler/PKLSA physics inference from KnotPlot relaxations, display-only control, or native data syntax qualification.

**Result status:** OFFLINE_QUALIFICATION_VALIDATED; NEW_NATIVE_DIAGNOSTIC_NOT_RUN; INDEPENDENT_PHYSICS_UNRESOLVED.
