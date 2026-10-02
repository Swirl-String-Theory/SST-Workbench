#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
routeB_induced_mode_count_trial.py
=================================
Route B trial scan for SST Planck-time derivation via Sakharov/induced-gravity
mode counting.

Goal:
    Replace the open input
        N_req = (r_c / L_p)^2
    in
        t_p = r_c / (c sqrt(N_mode))
    by a dimensionless SST expression using no G, L_p, or t_p as input.

This script compares candidates against the orthodox reference ONLY as an audit target.
Any expression using the fitted coefficient K_fit is labelled FIT_ONLY/CIRCULAR.
"""

import math
import json
import csv
from pathlib import Path

# --- Canon / orthodox constants for audit target ---
HBAR = 1.054571817e-34
C = 2.99792458e8
G = 6.67430e-11
M_E = 9.1093837015e-31
VCHAR = 1.09384563e6
R_C = 1.40897017e-15
RHO_CORE = 3.8934358266918687e18
RHO_F = 7.0e-7

OUT = Path('/mnt/data')


def rel_dev(x, y):
    return (x - y) / y


def fmt(x):
    return f"{x:.12e}"


def candidate_record(name, coefficient_expr, coefficient, rho_exp, speed_exp, status, comment):
    rho_ratio = RHO_CORE / RHO_F
    speed_ratio = C / VCHAR
    N = coefficient * (rho_ratio ** rho_exp) * (speed_ratio ** speed_exp)
    L_p_ref = math.sqrt(HBAR * G / C**3)
    t_p_ref = math.sqrt(HBAR * G / C**5)
    N_req = (R_C / L_p_ref) ** 2
    t_p_candidate = R_C / (C * math.sqrt(N))
    return {
        'name': name,
        'coefficient_expr': coefficient_expr,
        'coefficient': coefficient,
        'rho_exp': rho_exp,
        'speed_exp': speed_exp,
        'N_mode': N,
        'N_req': N_req,
        'N_ratio': N / N_req,
        'N_rel_dev': rel_dev(N, N_req),
        't_p_candidate_s': t_p_candidate,
        't_p_ref_s': t_p_ref,
        't_p_ratio': t_p_candidate / t_p_ref,
        't_p_rel_dev': rel_dev(t_p_candidate, t_p_ref),
        'status': status,
        'comment': comment,
    }


def simple_scan():
    """Scan small integer powers of 2 and pi for coefficient matches.

    We hold the physically motivated base rho_ratio^1 * (c/v)^6 fixed and scan
    K = 2^a*pi^b for compact angular/heat-kernel constants.
    """
    L_p_ref = math.sqrt(HBAR * G / C**3)
    N_req = (R_C / L_p_ref) ** 2
    base = (RHO_CORE / RHO_F) * (C / VCHAR) ** 6
    rows = []
    for a in range(-8, 9):
        for b in range(-8, 9):
            K = (2.0 ** a) * (math.pi ** b)
            N = K * base
            rows.append({
                'coefficient_expr': f"2^{a} pi^{b}",
                'coefficient': K,
                'N_ratio': N / N_req,
                'abs_log_error': abs(math.log(N / N_req)),
                'rel_dev': rel_dev(N, N_req),
            })
    rows.sort(key=lambda r: r['abs_log_error'])
    return rows[:25]


def main():
    L_p_ref = math.sqrt(HBAR * G / C**3)
    t_p_ref = math.sqrt(HBAR * G / C**5)
    N_req = (R_C / L_p_ref) ** 2
    rho_ratio = RHO_CORE / RHO_F
    speed_ratio = C / VCHAR
    base = rho_ratio * speed_ratio**6
    K_fit = N_req / base

    candidates = []
    candidates.append(candidate_record(
        name='B0_base_no_angular_kernel',
        coefficient_expr='1', coefficient=1.0,
        rho_exp=1, speed_exp=6,
        status='BASELINE_NOT_ENOUGH',
        comment='Pure density contrast times sixfold causal/core phase-space; misses angular/kernel normalization.'
    ))
    candidates.append(candidate_record(
        name='B1_pi_coefficient',
        coefficient_expr='pi', coefficient=math.pi,
        rho_exp=1, speed_exp=6,
        status='TRIAL_SIMPLE',
        comment='Very compact coefficient; within a few percent, but not as accurate as 32/pi^2.'
    ))
    candidates.append(candidate_record(
        name='B2_32_over_pi2_candidate',
        coefficient_expr='32/pi^2', coefficient=32.0 / math.pi**2,
        rho_exp=1, speed_exp=6,
        status='RESEARCH_TRACK_CANDIDATE',
        comment='Best compact coefficient found; same residual factor as Route A/C trials.'
    ))
    candidates.append(candidate_record(
        name='B3_fit_kernel_exact_target',
        coefficient_expr='K_fit=N_req/(rho_ratio*(c/v)^6)', coefficient=K_fit,
        rho_exp=1, speed_exp=6,
        status='FIT_ONLY_CIRCULAR',
        comment='Exact target coefficient; not a derivation because N_req uses L_p/G.'
    ))

    scan = simple_scan()

    result = {
        'reference': {
            'L_p_ref_m': L_p_ref,
            't_p_ref_s': t_p_ref,
            'N_req': N_req,
            'rho_ratio': rho_ratio,
            'speed_ratio_c_over_vchar': speed_ratio,
            'base_rho_ratio_speed6': base,
            'K_fit': K_fit,
            'compact_kernel_32_over_pi2': 32.0 / math.pi**2,
            'compact_kernel_ratio_to_fit': (32.0 / math.pi**2) / K_fit,
        },
        'candidates': candidates,
        'scan_top25': scan,
    }

    # write artifacts
    with open(OUT / 'routeB_induced_mode_count_trial.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    with open(OUT / 'routeB_induced_mode_count_trial_candidates.csv', 'w', newline='', encoding='utf-8') as f:
        fields = list(candidates[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(candidates)

    with open(OUT / 'routeB_induced_mode_count_scan_top25.csv', 'w', newline='', encoding='utf-8') as f:
        fields = list(scan[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(scan)

    lines = []
    lines.append('Route B induced-mode-count trial')
    lines.append('='*72)
    lines.append(f"L_p_ref              = {fmt(L_p_ref)} m")
    lines.append(f"t_p_ref              = {fmt(t_p_ref)} s")
    lines.append(f"N_req=(r_c/L_p)^2    = {fmt(N_req)}")
    lines.append(f"rho_core/rho_f       = {fmt(rho_ratio)}")
    lines.append(f"c/vchar              = {fmt(speed_ratio)}")
    lines.append(f"base=rho_ratio*(c/v)^6 = {fmt(base)}")
    lines.append(f"K_fit                = {fmt(K_fit)}")
    lines.append(f"32/pi^2              = {fmt(32.0/math.pi**2)}")
    lines.append(f"(32/pi^2)/K_fit      = {(32.0/math.pi**2)/K_fit:.12f}")
    lines.append('')
    for r in candidates:
        lines.append(f"[{r['status']}] {r['name']}: {r['coefficient_expr']}")
        lines.append(f"  N_mode        = {fmt(r['N_mode'])}")
        lines.append(f"  N/N_req       = {r['N_ratio']:.12f}")
        lines.append(f"  rel.dev(N)    = {100*r['N_rel_dev']:.6f}%")
        lines.append(f"  t_p_candidate = {fmt(r['t_p_candidate_s'])} s")
        lines.append(f"  t_p/t_p_ref   = {r['t_p_ratio']:.12f}")
        lines.append(f"  rel.dev(t_p)  = {100*r['t_p_rel_dev']:.6f}%")
        lines.append(f"  note          = {r['comment']}")
        lines.append('')
    lines.append('Top compact 2^a*pi^b scan for K on base=rho_ratio*(c/v)^6')
    for i, row in enumerate(scan[:10], 1):
        lines.append(f"  {i:02d}. {row['coefficient_expr']:<12} K={row['coefficient']:.12g} N/N_req={row['N_ratio']:.12f} rel.dev={100*row['rel_dev']:.6f}%")

    (OUT / 'routeB_induced_mode_count_trial.txt').write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
