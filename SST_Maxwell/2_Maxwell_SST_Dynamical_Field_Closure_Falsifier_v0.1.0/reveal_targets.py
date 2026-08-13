from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sst_maxwell_falsifier.freeze import sha256_file

C_SI = 299_792_458.0


def main():
    ap = argparse.ArgumentParser(description="Reveal post-freeze orthodox comparison targets")
    ap.add_argument("result", type=Path)
    ap.add_argument("--gravity-exponent-tol", type=float, default=0.15)
    ap.add_argument("--c-relative-tol", type=float, default=1e-3)
    args = ap.parse_args()
    sidecar = args.result.with_suffix(args.result.suffix + ".sha256")
    if not sidecar.exists():
        raise SystemExit("Refusing reveal: missing SHA256 sidecar")
    recorded = sidecar.read_text(encoding="ascii").split()[0]
    actual = sha256_file(args.result)
    if recorded != actual:
        raise SystemExit("Refusing reveal: frozen result hash mismatch")
    result = json.loads(args.result.read_text(encoding="utf-8"))
    gates = {g["gate"]: g for g in result["gates"]}
    g = gates["DFC-G"]["metrics"]
    nU, nF = g["blind_potential_exponent_n_U"], g["blind_force_exponent_n_F"]
    reveal = {
        "frozen_result_sha256": actual,
        "blind_overall_status": result["overall_status"],
        "gravity_secondary_comparison": {
            "target_n_U": 1.0,
            "observed_n_U": nU,
            "within_tolerance": abs(nU - 1.0) <= args.gravity_exponent_tol,
            "target_n_F": 2.0,
            "observed_n_F": nF,
            "within_tolerance_force": abs(nF - 2.0) <= args.gravity_exponent_tol,
            "tolerance": args.gravity_exponent_tol
        }
    }
    t = gates["DFC-T"]["metrics"]
    unit_system = t.get("unit_system", "unspecified")
    if unit_system == "SI":
        cfit = t["transverse_speed_blind"]
        reveal["transverse_speed_secondary_comparison"] = {
            "target_c_m_per_s": C_SI,
            "observed_c_m_per_s": cfit,
            "relative_error": abs(cfit - C_SI) / C_SI,
            "within_tolerance": abs(cfit - C_SI) / C_SI <= args.c_relative_tol,
            "tolerance": args.c_relative_tol
        }
    else:
        reveal["transverse_speed_secondary_comparison"] = {"status": "SKIP", "reason": f"unit_system={unit_system}, not SI"}
    out = args.result.with_name(args.result.stem + "_revealed.json")
    out.write_text(json.dumps(reveal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(reveal, indent=2, sort_keys=True))
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
