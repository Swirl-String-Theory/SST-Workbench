# CLOCK_ORIGIN_INDEPENDENT_OBSERVABLE_CAPTURE (P2.6) — 2026-09-13

Copy-on-write `A029-v0.4.0` from `A029-v0.3.0`. Parent tree SHA-256 `6a2fe45fe8ea3ea622e70b76719bfb1d3d7ab278bb94023732c6f4fb15c9907f`. C006 / A031 / A021 / A030 / A035 were not opened. A038-v0.5.1 was **not** created: overnight geometry/mesh certs remain fixtures (`BLOCKED_PROVENANCE`).

## Delivered

- Schema `10_docs/registry/schemas/SST_RAW_MODAL_TIMESERIES-1.0.json` plus `07_scripts/validate_raw_modal_timeseries.py`.
- Writer/discovery in `raw_timeseries.py`. Extraction and \(\Delta S\) gates in `observable.py`.
- PRED_M0 remains the leave-one-carrier-out null. Physical roles: M1 advection, M2 +intrinsic at \(k_{\rm ref}\), M3 closed-loop via \(k_{\rm closed}\). Extra gate: M3 must beat advection (M1).
- No \(a_m(t)\propto e^{\lambda t}\) synthesizer.

## Run

`python -m sst_finite_core_falsifier.cli independent-residual --out outputs/p26_capture --enable --pack-root .`

Result (~1 s): 0 scientific raw series.

| Certificate | Status | SHA-256 |
|-------------|--------|---------|
| Accounting | `ACCOUNTING_IDENTITY_CONFIRMED` (6/6) | `18616d9a4c5163d6c2470d7c46bf0e87c1cc546d8eb3c5a49ad82833fdf0546d` |
| Residual | `INDETERMINATE_NO_RAW_MODAL_TIMESERIES` | `93dc87fbad2cb8d55b71a5204530ff1794bc5f90fb16f3399359ead81012f4db` |

PRED_M0–PRED_M3 were not scored. Clock-origin discrimination is still not possible.

## Tests

A029-v0.4.0: 62 passed + gate PASS. Raw-timeseries + modal-phase schema: 25 passed. Catalog regenerated (`FAMILY.yaml` latest v0.4.0). Catalog registry still fails on pre-existing A043.

## What is still required for a scientific PRED score

A producer must write \(a_m^{\rm raw}(t)=\langle q_m,\delta X(t)\rangle\) on disk **before** demodulation, predicted-\(\omega\) bandpass, \(v_g\) windowing, or synthetic packet fitting, then detect \(\tau_{\rm return,ind}\) inside a protocol-fixed window that is not \(L/|v_g|\). That producer is not A029’s present eigen-only `analyze()`. Do not open P3 until that series exists and PRED_M3 fails to beat PRED_M0 / PRED_M1.
