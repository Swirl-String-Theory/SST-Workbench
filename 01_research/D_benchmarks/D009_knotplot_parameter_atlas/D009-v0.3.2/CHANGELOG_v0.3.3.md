# v0.3.3 — analysis-only metric correction

- No parameter values, KPC definitions or KnotPlot dynamics changed.
- Uniform-arclength resampling added before shape comparison.
- Cyclic origin alignment added for closed curves.
- Proper Kabsch rigid alignment retained.
- Legacy bead-index RMS retained for provenance but no longer classifies families.
- Existing v0.3.2 reports are preserved automatically as `*_v0.3.2_LEGACY.*`.
- Added `BALANCE_CANDIDATES.{json,md}` based on local one-factor
  `charge/hooke/power` endpoint slopes.
- Added `run_reanalyze_v033.cmd`; completed v0.3.2 data can be reanalyzed without
  rerunning KnotPlot.
