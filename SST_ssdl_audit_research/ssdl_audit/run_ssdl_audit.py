from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_ssdl_audit.core import run_ssdl_audit


def main() -> int:
    results = run_ssdl_audit()
    print(json.dumps(results, indent=2))

    print("\n" + "=" * 60)
    print(" SSDL Audit Summary")
    print("=" * 60)
    if results["results"]["theorem_A_verified"]:
        print("[PASS] Route A: DtN Monopole Normalization is EXACT.")
        print("       Tangential modes successfully projected out via Pi_0.")
    else:
        print("[FAIL] Route A: DtN projection error too high.")

    if results["results"]["theorem_B_verified"]:
        print("[PASS] Route B: Planck-Normal Mode Trace is EXACT.")
    else:
        print("[FAIL] Route B: Spectral Weyl counting mismatch.")

    print(f"\nTarget rho_f:   {results['results']['rho_f_target']:.4e} kg/m^3")
    print(f"Route A rho_f:  {results['results']['rho_f_route_A']:.4e} kg/m^3")
    print(f"Route B rho_f:  {results['results']['rho_f_route_B']:.4e} kg/m^3")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
