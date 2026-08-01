from __future__ import annotations

import argparse
import json

from sst_ssdl_audit.core import run_ssdl_audit


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the SST SSDL research-track audit harness.")
    ap.add_argument("--force-python", action="store_true", help="Use numpy BEM fallback instead of C++/pybind11 backend.")
    ap.add_argument("--n-theta", type=int, default=40, help="BEM theta panels for Route A cross-check.")
    ap.add_argument("--n-phi", type=int, default=80, help="BEM phi panels for Route A cross-check.")
    args = ap.parse_args()

    results = run_ssdl_audit(force_python=args.force_python, n_theta=args.n_theta, n_phi=args.n_phi)
    print(json.dumps(results, indent=2))

    route_a = results["route_a_dtn"]["bem_crosscheck"]
    route_b = results["route_b_mode_count"]
    res = results["results"]

    print("\n" + "=" * 60)
    print(" SSDL Audit Summary")
    print("=" * 60)
    if res["route_A_bem_within_tolerance"]:
        print("[PASS] Route A: Pi_0 Lambda^{-1} Pi_0 recovered R_e within tolerance.")
    else:
        print("[WARN] Route A: BEM projector error exceeds tolerance; refine mesh or inspect backend.")
    print(f"       relative error: {route_a['projection_error']:.6e}")
    print("       Interpretation: numerical BEM consistency check, not constitutive proof.")

    if res["route_B_cell_count_verified"]:
        print("\n[PASS] Route B: analytic Planck-normal cell count N_perp = R_e / ell_P.")
    print(f"       analytic count: {route_b['N_perp_analytic_float']:.12e}")
    print(f"       floor count:    {route_b['N_perp_integer_floor']}")
    print(f"       FD toy check:   {route_b['fd_toy_crosscheck']['fd_trace_error_percent']:.6g}% error")
    print("       Interpretation: analytic normal-stack count with toy finite-difference sanity check.")

    print(f"\nTarget rho_f:        {res['rho_f_target']:.4e} kg/m^3")
    print(f"SSDL analytic rho_f: {res['rho_f_ssdl_analytic']:.4e} kg/m^3")
    print(f"Route A BEM rho_f:   {res['rho_f_route_A_bem_crosscheck']:.4e} kg/m^3")
    print(f"Route B rho_f:       {res['rho_f_route_B_mode_count']:.4e} kg/m^3")
    print(f"analytic error:      {res['error_analytic_percent']:.4f}%")
    print("=" * 60)
    print("OPEN LEMMAS:")
    for lemma in results["open_lemmas"]:
        print(f"  {lemma}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
