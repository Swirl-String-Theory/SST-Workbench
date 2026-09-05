#!/usr/bin/env python3
"""
SST v0.8.19 Planck-route v3 audit.

Purpose
-------
This script deliberately does NOT search for new formulas. It freezes the
hypothesis-space status after the look-elsewhere audit and reproduces:

1. the A--D algebraic equivalence checks,
2. the single seed relation,
3. the look-elsewhere grid disclosure,
4. the Route-A preregistered target values.

Status: [RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED]
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class Constants:
    c: float = 299_792_458.0
    hbar: float = 1.054_571_817e-34
    G_N: float = 6.67430e-11
    M_e: float = 9.109_383_7015e-31
    r_c: float = 1.408_970_17e-15
    vchar: float = 1.093_845_63e6
    rho_f: float = 7.0e-7
    rho_core: float = 3.893_435_826_691_8687e18
    F_swirl_max: float = 29.053_507

C = Constants()


def planck_time(G: float = C.G_N) -> float:
    return math.sqrt(C.hbar * G / C.c**5)


def planck_length(G: float = C.G_N) -> float:
    return math.sqrt(C.hbar * G / C.c**3)


def route_A_sigma_lambda() -> float:
    return (16 / math.pi**2) * (C.rho_core / C.rho_f) * (C.c / C.vchar)**6 / C.r_c**2


def route_B_mode_count() -> float:
    return (32 / math.pi**2) * (C.rho_core / C.rho_f) * (C.c / C.vchar)**6


def route_C_G() -> float:
    return (math.pi**2 / 32) * (C.rho_f / C.rho_core) * (C.vchar / C.c)**5 * (C.vchar**2 * C.r_c / C.M_e)


def route_D_force() -> float:
    return (16 / math.pi**2) * C.F_swirl_max * (C.rho_core / C.rho_f) * (C.c / C.vchar)**7


def G_seed_horn_density_reduced() -> float:
    # Uses rho_core ~= M_e c^2 /(2 pi vchar^2 r_c^3).
    return (math.pi**3 / 16) * C.rho_f * C.vchar**9 * C.r_c**4 / (C.M_e**2 * C.c**7)


def G_seed_alpha_hbar_form() -> float:
    alpha_sst = 2 * C.vchar / C.c
    return (math.pi**3 / 2**17) * alpha_sst**13 * C.rho_f * C.hbar**4 / (C.M_e**6 * C.c**2)


def exact_rho_f_for_GN() -> float:
    return C.G_N * 16 * C.M_e**2 * C.c**7 / (math.pi**3 * C.vchar**9 * C.r_c**4)


def alpha_shift_to_absorb_residual() -> float:
    # If G ~ alpha^13, required fractional multiplier on alpha to map G_seed -> G_N.
    return (C.G_N / G_seed_horn_density_reduced())**(1/13) - 1


def look_elsewhere_scan(out_csv: Path) -> dict:
    G0 = C.vchar**2 * C.r_c / C.M_e
    hits5 = 0
    hits0575 = 0
    rows = []
    total = 0
    for k in range(-3, 4):
        for n in range(-20, 21):
            for p in range(-8, 9):
                for m in range(-12, 13):
                    total += 1
                    G = G0 * (C.rho_f / C.rho_core)**k * (C.vchar / C.c)**n * math.pi**p * 2.0**m
                    rel = G / C.G_N - 1.0
                    absrel = abs(rel)
                    if absrel <= 0.05:
                        hits5 += 1
                    if absrel <= 0.00575:
                        hits0575 += 1
                    rows.append({
                        'abs_rel_error': absrel,
                        'rel_error': rel,
                        'ratio': G / C.G_N,
                        'G_value': G,
                        'k_density_ratio': k,
                        'n_v_over_c': n,
                        'p_pi': p,
                        'm_two': m,
                        'complexity': abs(k) + abs(n) + abs(p) + abs(m),
                        'log_error': abs(math.log(G / C.G_N)),
                    })
    rows.sort(key=lambda r: (r['abs_rel_error'], r['complexity']))
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows[:25])
    return {
        'grid_points': total,
        'within_5_percent': hits5,
        'within_0_575_percent': hits0575,
        'best_25': rows[:25],
    }


def main() -> None:
    here = Path(__file__).resolve().parent
    outdir = here.parent / 'results'
    outdir.mkdir(parents=True, exist_ok=True)
    look_csv = outdir / 'route_ABCD_look_elsewhere_top25_v3.csv'

    A = route_A_sigma_lambda()
    B = route_B_mode_count()
    G_C = route_C_G()
    D = route_D_force()
    G_seed = G_seed_horn_density_reduced()
    G_alpha = G_seed_alpha_hbar_form()
    t_ref = planck_time(C.G_N)
    L_ref = planck_length(C.G_N)
    t_seed = planck_time(G_seed)
    t_C = planck_time(G_C)
    sigma_lambda_target = 1.0 / (2.0 * L_ref**2)
    N_target = (C.r_c / L_ref)**2

    data = {
        'status': '[RESEARCH-TRACK] [TRIAL] [NOT DERIVED] [FITTED]',
        'constants': asdict(C),
        'route_A_target': {
            'sigma_lambda_target_m2': sigma_lambda_target,
            'line_spacing_if_sigma_1_m': 1.0 / math.sqrt(sigma_lambda_target),
            'target_expression': '1/(2 L_p^2)',
        },
        'route_A_trial': {
            'sigma_lambda_A_m2': A,
            'ratio_to_target': A / sigma_lambda_target,
            't_from_A_s': 1.0 / (C.c * math.sqrt(2.0 * A)),
            't_from_A_over_t_ref': (1.0 / (C.c * math.sqrt(2.0 * A))) / t_ref,
        },
        'route_B_trial': {
            'N_B': B,
            'N_target': N_target,
            'ratio_to_target': B / N_target,
            't_from_B_s': C.r_c / (C.c * math.sqrt(B)),
            't_from_B_over_t_ref': (C.r_c / (C.c * math.sqrt(B))) / t_ref,
        },
        'route_C_trial': {
            'G_C': G_C,
            'G_C_over_G_N': G_C / C.G_N,
            't_from_G_C_s': t_C,
            't_from_G_C_over_t_ref': t_C / t_ref,
        },
        'route_D_trial': {
            'F_D': D,
            'F_gr_max_ref': C.c**4 / (4 * C.G_N),
            'F_D_over_ref': D / (C.c**4 / (4 * C.G_N)),
            't_from_F_D_s': math.sqrt(C.hbar / (4 * D * C.c)),
            't_from_F_D_over_t_ref': math.sqrt(C.hbar / (4 * D * C.c)) / t_ref,
        },
        'seed_relation': {
            'G_seed_horn_density_reduced': G_seed,
            'G_seed_over_G_N': G_seed / C.G_N,
            'G_route_C': G_C,
            'G_route_C_over_G_N': G_C / C.G_N,
            'G_seed_over_G_route_C': G_seed / G_C,
            'G_seed_alpha_hbar_form': G_alpha,
            'G_seed_alpha_over_G_seed': G_alpha / G_seed,
            't_seed_s': t_seed,
            't_seed_over_t_ref': t_seed / t_ref,
        },
        'equivalence_checks': {
            'B_over_2rc2A': B / (2 * C.r_c**2 * A),
            'A_C_duality_2_A_hbar_GC_over_c3': 2 * A * C.hbar * G_C / C.c**3,
            'D_over_c4_4GC': D / (C.c**4 / (4 * G_C)),
            'G_seed_over_G_C': G_seed / G_C,
        },
        'constant_synchronization': {
            'rho_core_from_horn_density': C.M_e * C.c**2 / (2 * math.pi * C.vchar**2 * C.r_c**3),
            'rho_core_script_over_horn': C.rho_core / (C.M_e * C.c**2 / (2 * math.pi * C.vchar**2 * C.r_c**3)),
            'hbar_from_compton_core': C.M_e * C.c**2 * C.r_c / C.vchar,
            'hbar_compton_over_CODATA': (C.M_e * C.c**2 * C.r_c / C.vchar) / C.hbar,
        },
        'degeneracy': {
            'rho_f_exact_for_G_N': exact_rho_f_for_GN(),
            'rho_f_exact_over_current': exact_rho_f_for_GN() / C.rho_f,
            'd_ln_G_d_ln_alpha_SST': 13,
            'alpha_fractional_shift_needed': alpha_shift_to_absorb_residual(),
        },
        'look_elsewhere': look_elsewhere_scan(look_csv),
    }

    json_path = outdir / 'route_ABCD_equivalence_audit_v3.json'
    json_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    report = outdir / 'route_ABCD_equivalence_audit_report_v3.md'
    report.write_text(f"""# SST v0.8.19 Planck Routes A--D v3 Audit

Status: {data['status']}.

## Executive verdict

The Planck routes A--D are retained as a target-generating audit artifact, not as evidence.  They are algebraic representations of one trial seed relation.  The previous four-route convergence framing is rejected.

## Single seed relation

```text
G_* = (pi^3/16) rho_f vchar^9 r_c^4 /(M_e^2 c^7)
    = {G_seed:.15e} m^3 kg^-1 s^-2
G_*/G_N = {G_seed/C.G_N:.15f}
t_p(G_*) = {t_seed:.15e} s
t_p(G_*)/t_p = {t_seed/t_ref:.15f}
```

Route-C's unreduced expression gives `G_C = {G_C:.15e}` and `G_C/G_N = {G_C/C.G_N:.15f}`.  The difference between `G_*` and `G_C` is a constant-synchronization artifact, not physics.

## Equivalence checks

```text
B / [2 r_c^2 A] = {data['equivalence_checks']['B_over_2rc2A']:.15f}
2 A hbar G_C / c^3 = {data['equivalence_checks']['A_C_duality_2_A_hbar_GC_over_c3']:.15f}
D / [c^4/(4G_C)] = {data['equivalence_checks']['D_over_c4_4GC']:.15f}
G_* / G_C = {data['equivalence_checks']['G_seed_over_G_C']:.15f}
```

## Look-elsewhere disclosure

```text
Scan family: G = G0 (rho_f/rho_core)^k (v/c)^n pi^p 2^m
Ranges: k=[-3,3], n=[-20,20], p=[-8,8], m=[-12,12]
Grid points: {data['look_elsewhere']['grid_points']}
Hits within 5%: {data['look_elsewhere']['within_5_percent']}
Hits within 0.575%: {data['look_elsewhere']['within_0_575_percent']}
Best hit: k={data['look_elsewhere']['best_25'][0]['k_density_ratio']}, n={data['look_elsewhere']['best_25'][0]['n_v_over_c']}, p={data['look_elsewhere']['best_25'][0]['p_pi']}, m={data['look_elsewhere']['best_25'][0]['m_two']}, rel_error={data['look_elsewhere']['best_25'][0]['rel_error']:.15e}
SST seed rank in top-25: 5 in the current scan output.
```

## Route-A preregistered target

The useful non-circular target is not the scanned formula.  It is:

```text
sigma_pierce * Lambda_L = 1/(2 L_p^2)
                          = {sigma_lambda_target:.15e} m^-2
```

The next valid move is to derive `Lambda_L` and `sigma_pierce` independently from a vacuum-tangle model, without using `G`, `L_p`, or `t_p` as inputs.  No further coefficient search should be counted as evidence.

## Degeneracy disclosure

```text
rho_f exact for G_N closure = {exact_rho_f_for_GN():.15e} kg m^-3
rho_f exact/current = {exact_rho_f_for_GN()/C.rho_f:.15f}
d ln G_*/d ln alpha_SST = 13
alpha fractional shift needed = {alpha_shift_to_absorb_residual():.15e}
```
""", encoding='utf-8')
    print(report)
    print(json_path)
    print(look_csv)

if __name__ == '__main__':
    main()
