# Trefoil v0.2.1 metric-neutral continuation patch

Confirmed defect in the original v0.2.1 extended generator:

```text
load ..._i30000.k
mode cb
centre
fitto mindist 1.05
...
```

`fitto mindist` rescales the saved state, so the 40k/50k/60k metric sequence is
not a strict continuation of the 0..30k trajectory.

This runtime patch:

- leaves all preregistered q/h/p points and scientific thresholds unchanged;
- leaves the original locked `generate_kpc.py` unchanged;
- preserves the validity of `PREREGISTRATION_LOCK.json`;
- regenerates only the extended KPC scripts;
- after `load i30000.k`, restores only non-geometric runtime settings;
- does not call `fitto`, `refine`, or `centre` before the first resumed `ago`;
- writes an immediate reload coordinate snapshot;
- verifies length and radius-of-gyration continuity against the original i30000
  checkpoint before accepting the repaired extension;
- includes the earlier Windows-safe generator patch cumulatively.

Existing 0..30k results remain valid and are reused.
