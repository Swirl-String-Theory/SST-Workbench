# P2.6 producer-bridge qualification — 2026-09-13

Copy-on-write `C006-v0.2.1` from `C006-v0.2.0`. Parent tree SHA-256 `28bb3835e012bd0e5f7ee73cf21b9f5d1b5e2d5f567a9dab1b8c88c3eb2a801e`. A029-v0.4.0 and A038 were not modified. P3 was not opened.

## What was built

- Compatibility matrix: [C006-v0.2.1/docs/P26_COMPATIBILITY.md](../../01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.1/docs/P26_COMPATIBILITY.md)
- Frozen contract: [THRESHOLDS_FROZEN.json](../../01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.1/THRESHOLDS_FROZEN.json) and [docs/BRIDGE_CONTRACT.md](../../01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.1/docs/BRIDGE_CONTRACT.md)
- Schemas: `SST_STATE_SPACE_BRIDGE-1.0`, `SST_MODE_RECONSTRUCTION-1.0`, `SST_TUBE_VALIDITY-1.0`
- Scientific amplitude: \(a_m=p_m^\dagger W_r B\,\Pi_{m,k}P_{\rm BS}[\delta X]\), not \(q_m^\dagger\)
- `prediction_inputs_consumed = []`
- \(D_{\rm bridge}=\{\mathrm{ring},\texttt{c1630473578eb8fa}\}\), \(D_{\rm score}=\varnothing\)

## Provenance chain (this run)

| Step | Status | SHA-256 |
|---|---|---|
| Mode reconstruction | `RECONSTRUCTED_SAME_BRANCH` | `26de5f693360ed37c7f393f8eb946dfed8b9487e878fbaefd30914511de877cb` |
| Tube validity | `INDETERMINATE_TUBE_CHART_INVALID` | `92918aeb5437f660233f2520a41db88d78721d9eb48a7949533352f9d8658fe9` |
| Bridge | `INDETERMINATE_TUBE_CHART_INVALID` | `1ad3d903b2600e7ad12dbee53f8ae10bff44e6f611e3911751e950de600c54f8` |

Certificates: `C006-v0.2.1/exports/p26_bridge/`.

Rebuilt mode on `c1630473578eb8fa` matched the frozen A029-v0.2.0 case on \(\lambda,\sigma,\omega,\omega_{\rm intrinsic}\), localization, axial-energy fraction, residual, and hybrid score. \(k_{\rm hat}=0.020079883482898683\) matches the sealed case. Biorthogonality residual \(1.92\times10^{-16}\).

The unit ring passes the frozen tube gate (\(a r_{\max}\kappa_{\max}=0.249<0.30\)). The preregistered TORUS_T2_3 carrier fails it (\(0.325>0.30\)). \(r_{\max}\) stayed 5.0.

## What was not done

- No scientific `SST_RAW_MODAL_TIMESERIES-1.0` (QUALIFIED is required)
- No A029-v0.4.0 `independent-residual` / M0–M3 scoring
- No second bridge after the tube stop
- No C006-v0.3.0 science, no A021 bump, no A038 bump

`BRIDGE_REJECTED` / `INDETERMINATE_*` does **not** falsify the A029 modal clock. This run says the Bishop tube chart for the preregistered qualification carrier is not valid at the frozen \((a,r_{\max},c_\kappa)\). The next route, if this stop stands, remains a same-state finite-core time-domain producer.

## Tests

- C006-v0.2.1: 30 passed
- A029-v0.4.0: 62 passed (untouched)
- Schema validators: 15 passed (`test_validate_state_space_bridge` + raw timeseries)
- `--score-a029` exits nonzero
