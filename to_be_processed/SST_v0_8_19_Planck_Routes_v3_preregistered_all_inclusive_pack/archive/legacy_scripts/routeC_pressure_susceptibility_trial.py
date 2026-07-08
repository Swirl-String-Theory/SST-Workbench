#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routeC_pressure_susceptibility_trial.py
======================================
Research-track trial scan for SST Route C:
coarse-grained pressure/stress susceptibility -> G_swirl -> t_p.

Status: [RESEARCH-TRACK / NUMEROLOGICAL-CANDIDATE]
No G, L_p, or t_p is used inside the candidate formulae except as the
comparison target in the audit output.

Main candidate found by low-complexity dimensional search:
    G_C = (pi^2/32) * (rho_f/rho_core) * (vchar/c)^5 * (vchar^2*r_c/M_e)

Interpretive placeholders:
    vchar^2*r_c/M_e          : natural core acceleration-potential coupling
    rho_f/rho_core           : bulk/core pressure susceptibility contrast
    (vchar/c)^5              : causal/core impedance suppression
    pi^2/32                  : angular / Green-kernel normalization candidate
"""

import math
import json
import csv
import argparse
from dataclasses import dataclass, asdict

# -----------------------------
# Canon / orthodox audit inputs
# -----------------------------
C = 299792458.0
HBAR = 1.054571817e-34
G_REF = 6.67430e-11
M_E = 9.1093837015e-31
VCHAR = 1.09384563e6
R_C = 1.40897017e-15
RHO_F = 7.0e-7
RHO_CORE = 3.8934358266918687e18

@dataclass
class Candidate:
    name: str
    formula: str
    G_value: float
    G_ratio: float
    G_rel_error: float
    t_p_value: float
    t_p_ratio: float
    t_p_rel_error: float
    L_p_value: float
    Fgr_max_value: float
    status: str
    comment: str


def planck_time_from_G(G: float) -> float:
    return math.sqrt(HBAR * G / C**5)


def planck_length_from_G(G: float) -> float:
    return math.sqrt(HBAR * G / C**3)


def max_tension_from_G(G: float) -> float:
    return C**4 / (4.0 * G)


def make_candidate(name: str, formula: str, G_value: float, status: str, comment: str) -> Candidate:
    t_ref = planck_time_from_G(G_REF)
    t_val = planck_time_from_G(G_value)
    L_val = planck_length_from_G(G_value)
    F_val = max_tension_from_G(G_value)
    return Candidate(
        name=name,
        formula=formula,
        G_value=G_value,
        G_ratio=G_value/G_REF,
        G_rel_error=G_value/G_REF - 1.0,
        t_p_value=t_val,
        t_p_ratio=t_val/t_ref,
        t_p_rel_error=t_val/t_ref - 1.0,
        L_p_value=L_val,
        Fgr_max_value=F_val,
        status=status,
        comment=comment,
    )


def low_complexity_scan(max_abs_n=20, max_abs_pi=8, max_abs_two=12):
    """Scan factors of the form
        G = G0 * (rho_f/rho_core)^k * (v/c)^n * pi^p * 2^m
    with G0 = v^2 r_c / M_e.

    This is NOT a proof. It is a controlled dimensional/numerical discovery tool.
    """
    G0 = VCHAR**2 * R_C / M_E
    dr = RHO_F / RHO_CORE
    rows = []
    for k in range(-3, 4):
        for n in range(-max_abs_n, max_abs_n+1):
            for p in range(-max_abs_pi, max_abs_pi+1):
                for m in range(-max_abs_two, max_abs_two+1):
                    G_trial = G0 * (dr**k) * ((VCHAR/C)**n) * (math.pi**p) * (2.0**m)
                    if not math.isfinite(G_trial) or G_trial <= 0:
                        continue
                    ratio = G_trial/G_REF
                    rel = ratio - 1.0
                    logerr = abs(math.log(ratio))
                    complexity = abs(k) + abs(n) + abs(p) + abs(m)
                    if logerr < 0.05:
                        rows.append({
                            "log_error": logerr,
                            "rel_error": rel,
                            "complexity": complexity,
                            "k_density_ratio": k,
                            "n_v_over_c": n,
                            "p_pi": p,
                            "m_two": m,
                            "G_value": G_trial,
                            "G_ratio": ratio,
                            "factor_value": (dr**k) * ((VCHAR/C)**n) * (math.pi**p) * (2.0**m),
                        })
    rows.sort(key=lambda r: (r["complexity"], r["log_error"]))
    return rows


def main():
    ap = argparse.ArgumentParser(description="SST Route C pressure-susceptibility trial scan")
    ap.add_argument("--json", default="/mnt/data/routeC_pressure_trial_candidates.json")
    ap.add_argument("--csv", default="/mnt/data/routeC_pressure_trial_candidates.csv")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    G0 = VCHAR**2 * R_C / M_E
    dr = RHO_F / RHO_CORE
    beta = VCHAR / C

    candidates = []

    G_canonical_target = G_REF
    candidates.append(make_candidate(
        "orthodox target",
        "G_N (comparison only; not an SST derivation)",
        G_canonical_target,
        "TARGET",
        "Reference value used only for error measurement.",
    ))

    G_c1 = (math.pi**2/32.0) * dr * beta**5 * G0
    candidates.append(make_candidate(
        "C1_pi2_over_32_pressure_candidate",
        "(pi^2/32)*(rho_f/rho_core)*(vchar/c)^5*(vchar^2*r_c/M_e)",
        G_c1,
        "RESEARCH_TRACK_CANDIDATE",
        "Low-complexity Route-C candidate; no G,Lp,tp input; -0.5716% in G, -0.2862% in t_p.",
    ))

    G_c0 = (1.0/math.pi) * dr * beta**5 * G0
    candidates.append(make_candidate(
        "C0_inverse_pi_pressure_candidate",
        "(1/pi)*(rho_f/rho_core)*(vchar/c)^5*(vchar^2*r_c/M_e)",
        G_c0,
        "RESEARCH_TRACK_CANDIDATE",
        "Simpler angular factor; +2.615% in G.",
    ))

    k_fit = G_REF/(dr*beta**5*G0)
    candidates.append(make_candidate(
        "Cfit_exact_dimensionless_kernel",
        "K_fit*(rho_f/rho_core)*(vchar/c)^5*(vchar^2*r_c/M_e)",
        G_REF,
        "EXACT_FIT_NOT_DERIVED",
        f"Required dimensionless kernel K_fit={k_fit:.15g}; compare pi^2/32={math.pi**2/32:.15g}, 1/pi={1/math.pi:.15g}.",
    ))

    scan_rows = low_complexity_scan()
    top_rows = scan_rows[:args.top]

    # Write JSON
    payload = {
        "constants": {
            "c": C,
            "hbar": HBAR,
            "G_ref": G_REF,
            "M_e": M_E,
            "vchar": VCHAR,
            "r_c": R_C,
            "rho_f": RHO_F,
            "rho_core": RHO_CORE,
            "G0_v2rc_over_Me": G0,
            "rho_ratio": dr,
            "beta_v_over_c": beta,
            "K_fit": k_fit,
            "pi2_over_32": math.pi**2/32.0,
            "inverse_pi": 1.0/math.pi,
        },
        "candidates": [asdict(c) for c in candidates],
        "top_scan_rows": top_rows,
    }
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Write CSV with candidates + top scan rows in simple flat rows
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "name", "formula_or_exponents", "G_value", "G_ratio", "G_rel_error", "t_p_value", "t_p_ratio", "status", "comment"])
        for cnd in candidates:
            writer.writerow(["candidate", cnd.name, cnd.formula, cnd.G_value, cnd.G_ratio, cnd.G_rel_error, cnd.t_p_value, cnd.t_p_ratio, cnd.status, cnd.comment])
        for i, r in enumerate(top_rows, start=1):
            expstr = f"G0*(rho_f/rho_core)^{r['k_density_ratio']}*(v/c)^{r['n_v_over_c']}*pi^{r['p_pi']}*2^{r['m_two']}"
            writer.writerow(["scan", f"scan_{i:02d}", expstr, r["G_value"], r["G_ratio"], r["rel_error"], "", "", "SCAN", f"complexity={r['complexity']}; log_error={r['log_error']}"])

    # Print compact report
    print("# SST Route C: pressure/stress susceptibility trial")
    print(f"G_ref          = {G_REF:.15e} m^3 kg^-1 s^-2")
    print(f"t_p_ref        = {planck_time_from_G(G_REF):.15e} s")
    print(f"G0=v^2*r_c/M_e = {G0:.15e}")
    print(f"rho_f/rho_core = {dr:.15e}")
    print(f"beta=v/c       = {beta:.15e}")
    print(f"K_fit          = {k_fit:.15e}")
    print(f"pi^2/32        = {math.pi**2/32.0:.15e}")
    print(f"1/pi           = {1.0/math.pi:.15e}")
    print()
    for cnd in candidates:
        print(f"[{cnd.status}] {cnd.name}")
        print(f"  {cnd.formula}")
        print(f"  G      = {cnd.G_value:.15e}  ratio={cnd.G_ratio:.12f}  rel={cnd.G_rel_error:+.6%}")
        print(f"  t_p    = {cnd.t_p_value:.15e}  ratio={cnd.t_p_ratio:.12f}  rel={cnd.t_p_rel_error:+.6%}")
        print(f"  L_p    = {cnd.L_p_value:.15e}")
        print(f"  Fgrmax = {cnd.Fgr_max_value:.15e} N")
        print(f"  note   = {cnd.comment}")
    print()
    print("Top low-complexity scan rows:")
    for i, r in enumerate(top_rows[:10], start=1):
        print(f"  {i:02d}. complexity={r['complexity']:2d}, ratio={r['G_ratio']:.9f}, rel={r['rel_error']:+.4%}, "
              f"k={r['k_density_ratio']}, n={r['n_v_over_c']}, p={r['p_pi']}, m={r['m_two']}")
    print(f"\nWrote: {args.json}")
    print(f"Wrote: {args.csv}")


if __name__ == "__main__":
    main()
