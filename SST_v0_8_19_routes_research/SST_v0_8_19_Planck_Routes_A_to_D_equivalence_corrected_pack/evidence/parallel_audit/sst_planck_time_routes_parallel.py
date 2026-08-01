#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sst_planck_time_routes_parallel.py
==================================
Parallel audit suite for four candidate SST routes to the Planck time.

Epistemic status:
  * This script is an audit/diagnostic harness, not a derivation.
  * If no independent model input is supplied for a route, the script uses the
    required target value and marks the route as REQUIRED_TARGET / OPEN.
  * A route becomes non-circular only when its input is supplied by an
    independent SST calculation that does not use G, L_p, or t_p.

Routes:
  A. Horizon-piercing line-density entropy:
       t_p = 1 / (c sqrt(2 sigma_pierce Lambda_L))
       G   = c^3 / (2 hbar sigma_pierce Lambda_L)

  B. Sakharov/induced-gravity mode count:
       G   = beta_induced r_c^2 c^3 / (hbar N)
       t_p = (r_c/c) sqrt(beta_induced/N)

  C. Coarse-grained swirl Newtonian closure:
       G_swirl = vchar c^3 t_p^2 / (r_c m_e)
       t_p     = sqrt(G_swirl r_c m_e / (vchar c^3))

  D. Maximum gravitational tension:
       F_gr^max = c^4/(4G)
       t_p      = sqrt(hbar/(4 F_gr^max c))

Usage examples:
  python sst_planck_time_routes_parallel.py
  python sst_planck_time_routes_parallel.py --lambda-L 1.9e69 --sigma-pierce 1
  python sst_planck_time_routes_parallel.py --N-mode 7.6e39
  python sst_planck_time_routes_parallel.py --G-swirl 6.67430e-11
  python sst_planck_time_routes_parallel.py --Fgr-max 3.02563e43
  python sst_planck_time_routes_parallel.py --csv planck_routes.csv --json planck_routes.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

# ---------------------------------------------------------------------------
# Constants: aligned with current SST verification-suite convention where
# possible. HBAR is the CODATA-2018 value used in earlier SST suites.
# ---------------------------------------------------------------------------
HBAR = 1.054571817e-34       # J s
C = 2.99792458e8             # m s^-1, exact
G_CODATA = 6.67430e-11       # m^3 kg^-1 s^-2
M_E = 9.1093837015e-31       # kg
VCHAR = 1.09384563e6         # m s^-1
R_C = 1.40897017e-15         # m
F_GR_MAX_CANON = 3.02563e43  # N, user/canon rounded value

# Reference Planck units from orthodox definition.
TP_REF = math.sqrt(HBAR * G_CODATA / C**5)
LP_REF = C * TP_REF
FGR_REF = C**4 / (4.0 * G_CODATA)


def rel_err(x: float, ref: float) -> float:
    if ref == 0:
        return abs(x)
    return abs(x - ref) / abs(ref)


@dataclass
class RouteResult:
    route: str
    status: str
    input_name: str
    input_value: float
    input_unit: str
    tp_s: float
    lp_m: float
    G_m3_kg_s2: float
    Fgr_N: float
    rel_tp: float
    rel_lp: float
    rel_G: float
    note: str

    def pass_fail(self, tol: float) -> str:
        return "PASS" if self.rel_tp <= tol and self.rel_G <= tol else "FAIL"


# ---------------------------------------------------------------------------
# Route A: line-density entropy / horizon piercing.
# ---------------------------------------------------------------------------
def route_A_line_density(
    sigma_pierce: float,
    lambda_L: Optional[float],
) -> RouteResult:
    required_product = 1.0 / (2.0 * LP_REF**2)  # sigma * Lambda_L
    required_lambda_L = required_product / sigma_pierce

    if lambda_L is None:
        lambda_L_eff = required_lambda_L
        status = "REQUIRED_TARGET_OPEN"
        note = (
            "No independent Lambda_L supplied; using required sigma*Lambda_L "
            "= 1/(2 L_p^2). Non-circular only if Lambda_L is derived from SST vacuum statistics."
        )
    else:
        lambda_L_eff = lambda_L
        status = "MODEL_INPUT"
        note = "Using supplied Lambda_L; compare output to CODATA Planck time."

    product = sigma_pierce * lambda_L_eff
    G = C**3 / (2.0 * HBAR * product)
    lp = 1.0 / math.sqrt(2.0 * product)
    tp = lp / C
    Fgr = C**4 / (4.0 * G)

    return RouteResult(
        route="A_line_density_entropy",
        status=status,
        input_name="sigma_pierce*Lambda_L",
        input_value=product,
        input_unit="m^-2",
        tp_s=tp,
        lp_m=lp,
        G_m3_kg_s2=G,
        Fgr_N=Fgr,
        rel_tp=rel_err(tp, TP_REF),
        rel_lp=rel_err(lp, LP_REF),
        rel_G=rel_err(G, G_CODATA),
        note=note,
    )


# ---------------------------------------------------------------------------
# Route B: induced gravity / mode count.
# ---------------------------------------------------------------------------
def route_B_induced_mode_count(
    N_mode: Optional[float],
    beta_induced: float,
) -> RouteResult:
    required_N = beta_induced * (R_C / LP_REF) ** 2

    if N_mode is None:
        N_eff = required_N
        status = "REQUIRED_TARGET_OPEN"
        note = (
            "No independent N supplied; using required N = beta*(r_c/L_p)^2. "
            "Non-circular only if N is derived from torsion/shear vacuum mode counting."
        )
    else:
        N_eff = N_mode
        status = "MODEL_INPUT"
        note = "Using supplied N_mode; compare output to CODATA Planck time."

    G = beta_induced * R_C**2 * C**3 / (HBAR * N_eff)
    tp = (R_C / C) * math.sqrt(beta_induced / N_eff)
    lp = C * tp
    Fgr = C**4 / (4.0 * G)

    return RouteResult(
        route="B_induced_gravity_modes",
        status=status,
        input_name="N_mode",
        input_value=N_eff,
        input_unit="dimensionless",
        tp_s=tp,
        lp_m=lp,
        G_m3_kg_s2=G,
        Fgr_N=Fgr,
        rel_tp=rel_err(tp, TP_REF),
        rel_lp=rel_err(lp, LP_REF),
        rel_G=rel_err(G, G_CODATA),
        note=note,
    )


# ---------------------------------------------------------------------------
# Route C: pressure/Newtonian closure -> G_swirl.
# ---------------------------------------------------------------------------
def route_C_swirl_closure(G_swirl: Optional[float]) -> RouteResult:
    required_G = G_CODATA

    if G_swirl is None:
        G_eff = required_G
        status = "REQUIRED_TARGET_OPEN"
        note = (
            "No independent G_swirl supplied; using required G. Non-circular only if "
            "G_swirl is derived from SST pressure/stress susceptibility without using t_p or G."
        )
    else:
        G_eff = G_swirl
        status = "MODEL_INPUT"
        note = "Using supplied G_swirl; compare output to CODATA Planck time."

    tp = math.sqrt(G_eff * R_C * M_E / (VCHAR * C**3))
    lp = C * tp
    Fgr = C**4 / (4.0 * G_eff)

    return RouteResult(
        route="C_swirl_Newtonian_closure",
        status=status,
        input_name="G_swirl",
        input_value=G_eff,
        input_unit="m^3 kg^-1 s^-2",
        tp_s=tp,
        lp_m=lp,
        G_m3_kg_s2=G_eff,
        Fgr_N=Fgr,
        rel_tp=rel_err(tp, TP_REF),
        rel_lp=rel_err(lp, LP_REF),
        rel_G=rel_err(G_eff, G_CODATA),
        note=note,
    )


# ---------------------------------------------------------------------------
# Route D: gravitational maximum tension.
# ---------------------------------------------------------------------------
def route_D_max_tension(Fgr_max: Optional[float]) -> RouteResult:
    required_Fgr = FGR_REF

    if Fgr_max is None:
        F_eff = required_Fgr
        status = "REQUIRED_TARGET_OPEN"
        note = (
            "No independent F_gr^max supplied; using required c^4/(4G). Non-circular only "
            "if gravitational horizon tension is derived independently."
        )
    else:
        F_eff = Fgr_max
        status = "MODEL_INPUT"
        note = "Using supplied F_gr^max; compare output to CODATA Planck time."

    G = C**4 / (4.0 * F_eff)
    tp = math.sqrt(HBAR / (4.0 * F_eff * C))
    lp = C * tp

    return RouteResult(
        route="D_maximum_tension",
        status=status,
        input_name="F_gr^max",
        input_value=F_eff,
        input_unit="N",
        tp_s=tp,
        lp_m=lp,
        G_m3_kg_s2=G,
        Fgr_N=F_eff,
        rel_tp=rel_err(tp, TP_REF),
        rel_lp=rel_err(lp, LP_REF),
        rel_G=rel_err(G, G_CODATA),
        note=note,
    )


def compact_float(x: float) -> str:
    return f"{x:.10e}"


def print_results(results: List[RouteResult], tol: float) -> None:
    print("#" * 88)
    print("# SST Planck-time route audit: four parallel candidate routes")
    print("#" * 88)
    print(f"Reference t_p = {TP_REF:.12e} s")
    print(f"Reference L_p = {LP_REF:.12e} m")
    print(f"Reference G   = {G_CODATA:.12e} m^3 kg^-1 s^-2")
    print(f"Reference Fgr = {FGR_REF:.12e} N")
    print(f"Tolerance     = {tol:.1e}")
    print()

    header = (
        f"{'Route':32s} {'Status':22s} {'Verdict':7s} "
        f"{'t_p [s]':>14s} {'rel_t':>10s} {'G':>14s} {'rel_G':>10s} {'Input':>14s}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r.route:32s} {r.status:22s} {r.pass_fail(tol):7s} "
            f"{r.tp_s:14.6e} {r.rel_tp:10.3e} {r.G_m3_kg_s2:14.6e} "
            f"{r.rel_G:10.3e} {r.input_value:14.6e}"
        )

    print("\nRequired target inputs for exact CODATA matching:")
    sigma_default = 1.0
    lambda_req = 1.0 / (2.0 * sigma_default * LP_REF**2)
    d_req = 1.0 / math.sqrt(lambda_req)
    N_req = (R_C / LP_REF) ** 2
    G_req = G_CODATA
    F_req = FGR_REF
    print(f"  A: Lambda_L_required(sigma=1) = {lambda_req:.12e} m^-2")
    print(f"     spacing d_Lambda = Lambda_L^(-1/2) = {d_req:.12e} m = {d_req/LP_REF:.8f} L_p")
    print(f"  B: N_required(beta=1)          = {N_req:.12e}")
    print(f"  C: G_swirl_required            = {G_req:.12e} m^3 kg^-1 s^-2")
    print(f"  D: F_gr^max_required           = {F_req:.12e} N")

    print("\nEpistemic notes:")
    for r in results:
        print(f"  - {r.route}: {r.note}")


def write_json(path: str, results: List[RouteResult], tol: float) -> None:
    payload: Dict[str, Any] = {
        "reference": {
            "HBAR_J_s": HBAR,
            "C_m_s": C,
            "G_CODATA_m3_kg_s2": G_CODATA,
            "M_E_kg": M_E,
            "VCHAR_m_s": VCHAR,
            "R_C_m": R_C,
            "TP_REF_s": TP_REF,
            "LP_REF_m": LP_REF,
            "FGR_REF_N": FGR_REF,
            "tolerance": tol,
        },
        "results": [asdict(r) | {"verdict": r.pass_fail(tol)} for r in results],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_csv(path: str, results: List[RouteResult], tol: float) -> None:
    rows = []
    for r in results:
        d = asdict(r)
        d["verdict"] = r.pass_fail(tol)
        rows.append(d)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="Parallel audit of four SST candidate routes to Planck time")
    ap.add_argument("--sigma-pierce", type=float, default=1.0, help="Route A entropy per horizon piercing, dimensionless")
    ap.add_argument("--lambda-L", type=float, default=None, help="Route A vortex line density Lambda_L in m^-2")
    ap.add_argument("--N-mode", type=float, default=None, help="Route B induced-gravity mode count N")
    ap.add_argument("--beta-induced", type=float, default=1.0, help="Route B prefactor beta in G=beta*r_c^2*c^3/(hbar*N)")
    ap.add_argument("--G-swirl", type=float, default=None, help="Route C independently supplied G_swirl")
    ap.add_argument("--Fgr-max", type=float, default=None, help="Route D independently supplied F_gr^max in N")
    ap.add_argument("--tol", type=float, default=1e-6, help="relative PASS tolerance for t_p and G")
    ap.add_argument("--json", type=str, default=None, help="write JSON results")
    ap.add_argument("--csv", type=str, default=None, help="write CSV results")
    args = ap.parse_args()

    results = [
        route_A_line_density(args.sigma_pierce, args.lambda_L),
        route_B_induced_mode_count(args.N_mode, args.beta_induced),
        route_C_swirl_closure(args.G_swirl),
        route_D_max_tension(args.Fgr_max),
    ]

    print_results(results, args.tol)

    if args.json:
        write_json(args.json, results, args.tol)
        print(f"\n[wrote JSON] {args.json}")
    if args.csv:
        write_csv(args.csv, results, args.tol)
        print(f"[wrote CSV ] {args.csv}")

    # Return failure only if supplied MODEL_INPUT routes fail. Required-target routes are not derivations.
    supplied = [r for r in results if r.status == "MODEL_INPUT"]
    if supplied and any(r.pass_fail(args.tol) == "FAIL" for r in supplied):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
