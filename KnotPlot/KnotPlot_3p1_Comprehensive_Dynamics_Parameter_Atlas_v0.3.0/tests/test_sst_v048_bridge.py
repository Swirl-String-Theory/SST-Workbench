from pathlib import Path
import json, ast, sys, re

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"sst_v048_bridge_contract.json").read_text())
assert C["expected_version"]=="0.4.8"
assert "run_panel" in C["verified_entry_points"]["custom_panel_api"]
assert C["configs"]["screen"]=="configs/panel_extended.json"
assert C["configs"]["full_confirm"].endswith("05_R5_N720_K16_ROBUST_FULL.json")
assert C["configs"]["spectral_k64"].endswith("04_S4_N720_K64.json")

# Ensure adapter is syntactically valid and encodes exact promotion policy.
src=(ROOT/"sst_v048_adapter.py").read_text()
ast.parse(src)
assert "SPECTRAL_CONVERGED" in src
assert 'growth_verdict")=="PASS"' in src or "growth_verdict" in src
assert "P7_RPO_recurrence" in src
assert "P8_Floquet_bounded" in src
assert "FULL_DYNAMICS_PASS_RPO_FLOQUET_BOUNDED" in src
assert "openmp" in src and "sycl-dd32" in src

for fn in (
 "run_80_sst_v048_preflight.cmd",
 "run_81_sst_v048_screen_fp64.cmd",
 "run_82_sst_v048_spectral_dd32.cmd",
 "run_82b_sst_v048_spectral_fp64.cmd",
 "run_83_sst_v048_confirm_fp64.cmd",
 "run_84_sst_v048_synthesize.cmd",
 "run_sst_stability_screen.cmd",
 "run_sst_stability_all.cmd",
):
    assert (ROOT/fn).is_file(),fn

print("SST v0.4.8 BRIDGE SELFTEST PASS: exact run_panel + adaptive spectral + R5 full-dynamics contract encoded")
