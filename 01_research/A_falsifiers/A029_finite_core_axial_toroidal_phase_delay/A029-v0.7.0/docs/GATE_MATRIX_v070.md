# A029-v0.7.0 gate matrix

| Stage | Gate | Pass condition | Absence/failure semantics |
|---|---|---|---|
| 00 | Parent producer integrity | exact sealed v0.6 `sst_lagrangian.py` SHA-256 | abort before run |
| 00 | Production backend | full run + C++/pybind11 backend | diagnostic class otherwise |
| 01 | Parent mode convergence | CLOSED and both ± controls pass frozen parent convergence | diagnostic/not qualified |
| 01 | Action branch overlap | both CLOSED↔control overlaps ≥ 0.95 | diagnostic/not qualified |
| 02 | Symmetric detuning null | `K_rms ∝ delta_k^p`, `|p-2|≤0.25`, monotone toward zero | FAIL |
| 02 | Offset curvature stability | last 3 `C_k` RMS values relative span ≤ 0.15 | FAIL |
| 02 | Radial curvature convergence | Richardson `C_k0` last-3 RMS relative span ≤ 0.30 | FAIL |
| 02 | Radial shape convergence | phase-aligned time-series overlap ≥ 0.98 | FAIL |
| 03 | Raw series independence | `scientific=true`, predictor-clean, non-synthetic raw dynamics | NOT_RUN |
| 03 | Geometry/basis identity | exact geometry SHA + exact lagrangian basis SHA | NOT_RUN |
| 03 | Complex amplitude contract | `a(t0)=epsilon exp(i phase0)`, core-RMS/V0 semantics | NOT_RUN |
| 03 | Linear-window consistency | `epsilon × max_growth_gain ≤ 0.10` | NOT_RUN |
| 04 | Physical scale provenance | independent positive `a,V0`; target-dependency flags false; no fit | NOT_RUN/INVALID |
| 04 | Physical closure reference | independently derived `physical_delta_k_hat`; no QGI/attosecond dependence; no fit | NOT_RUN/INVALID |
| 04 | Certified reference range | physical `delta_k_hat` not larger than tested detuning range | NOT_RUN |
| 04 | QGI action scale | `status=READY`, no Planck target in inference | NOT_RUN |
| 05 | Radial coherence | characterized by default; optional preregistered threshold | CHARACTERIZED/PASS/FAIL |
| 06 | Rigid rotation | curvature magnitude ratio within 1e-6 and shape overlap ≥ 0.999 | PASS/FAIL |
| 06 | Mirror/orientation | characterized only; no chirality-sign verdict without external orientation convention | CHARACTERIZED |
| 07 | Mapping provenance | physically derived/frozen mapping manifest, zero fitted phase parameters | NOT_RUN/INVALID |
| 07 | Source lineage | action source SHA in mapping must equal sealed Stage-04 action file | NOT_RUN/INVALID |
| 07 | Global-phase null | pure factorable phase leaves intensity invariant ≤ 1e-12 relative | PASS/FAIL |
