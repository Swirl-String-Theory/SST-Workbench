#!/usr/bin/env python3
"""
SST v0.8.19 Route-A parallel derivation/falsification harness.

Goal
----
Try three pre-registered model families for the Route-A quantity
    sigma_pierce * Lambda_L  [m^-2]
without using G, L_p, or t_p as model inputs.

The orthodox Planck target is computed only after the models are evaluated,
as the comparison target:
    (sigma Lambda)_target = 1/(2 L_p^2).

Models
------
1. Onsager/KT-like vortex gas: tests whether ordinary core-cutoff vortex
   density or BKT fugacity can supply the required line density.
2. Crofton/stereology: derives the isotropic projection factor <|cos theta|>=1/2
   and tests max core packing. This is a geometry lemma, not a scale derivation.
3. Torsion-channel phase-space counting: tests Weyl-style channel counts with
   fixed coefficients. The earlier seed relation is included only as a negative
   control marked FITTED/TRIAL, not a derived model.

Status
------
[RESEARCH-TRACK] [PREREGISTERED] [FALSIFICATION-HARNESS]
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import json
import math
import random

@dataclass(frozen=True)
class Constants:
    c: float = 299_792_458.0
    hbar: float = 1.054_571_817e-34
    G_N: float = 6.67430e-11              # comparison only, not model input
    M_e: float = 9.109_383_7015e-31
    r_c: float = 1.408_970_17e-15
    vchar: float = 1.093_845_63e6
    rho_f: float = 7.0e-7
    rho_core: float = 3.893_435_826_691_8687e18

C = Constants()


def planck_length() -> float:
    return math.sqrt(C.hbar * C.G_N / C.c**3)


def planck_time() -> float:
    return math.sqrt(C.hbar * C.G_N / C.c**5)


def target_sigma_lambda() -> float:
    return 1.0 / (2.0 * planck_length()**2)


def ratio_record(name: str, family: str, sigma_lambda: float | None, status: str, formula: str, note: str, uses_fitted_kernel: bool=False) -> dict:
    target = target_sigma_lambda()
    if sigma_lambda is None or sigma_lambda <= 0:
        ratio = None
        log10_ratio = None
        tp = None
        tp_over_ref = None
        broad_hit = False
        within_1pct = False
    else:
        ratio = sigma_lambda / target
        log10_ratio = math.log10(ratio)
        tp = 1.0 / (C.c * math.sqrt(2.0 * sigma_lambda))
        tp_over_ref = tp / planck_time()
        broad_hit = 0.1 <= ratio <= 10.0
        within_1pct = abs(ratio - 1.0) <= 0.01
    return {
        'name': name,
        'family': family,
        'status': status,
        'formula': formula,
        'sigma_lambda_m^-2': sigma_lambda,
        'ratio_to_target': ratio,
        'log10_ratio_to_target': log10_ratio,
        't_from_model_s': tp,
        't_over_t_ref': tp_over_ref,
        'broad_target_hit_0p1_to_10': broad_hit,
        'within_1_percent': within_1pct,
        'uses_fitted_kernel_or_scan_motivated_factor': uses_fitted_kernel,
        'note': note,
    }


def monte_carlo_mean_abs_cos(n: int = 200_000, seed: int = 190819) -> float:
    # For isotropic directions, cos(theta) is uniform on [-1,1].
    rng = random.Random(seed)
    return sum(abs(2.0 * rng.random() - 1.0) for _ in range(n)) / n


def run_models() -> dict:
    target = target_sigma_lambda()
    Lp = planck_length()
    tp = planck_time()
    rho_ratio = C.rho_core / C.rho_f
    cv = C.c / C.vchar
    vc = C.vchar / C.c

    results = []

    # 1. Onsager/KT-like: ordinary vortex gas with core cutoff cannot exceed ~one vortex per core area.
    core_area_density = 1.0 / C.r_c**2
    disk_packing_density = 1.0 / (math.pi * C.r_c**2)
    results.append(ratio_record(
        'O1_core_cutoff_one_per_rc2', 'Onsager/KT-like vortex gas', core_area_density,
        'FAIL_DERIVED_SCALE_TOO_SMALL',
        'sigmaLambda = r_c^{-2}',
        'Maximal naive one-core-per-area sheet density. Misses Planck target by ~40 orders; no G/Lp/tp input.',
    ))
    results.append(ratio_record(
        'O2_disk_packing_one_per_pi_rc2', 'Onsager/KT-like vortex gas', disk_packing_density,
        'FAIL_DERIVED_SCALE_TOO_SMALL',
        'sigmaLambda = (pi r_c^2)^{-1}',
        'Densest non-overlap tube cross-section estimate. Even smaller than O1.',
    ))
    y_req_single = target * C.r_c**2
    y_req_pair = math.sqrt(target * C.r_c**2)

    # 2. Crofton/stereology: derives projection factor but not scale.
    mc = monte_carlo_mean_abs_cos()
    results.append(ratio_record(
        'S1_crofton_projection_factor_only', 'Crofton/stereology', None,
        'PARTIAL_LEMMA_ONLY_NO_SCALE',
        '<N_pierce>/A = <|cos theta|> Lambda_L = (1/2) Lambda_L',
        f'Monte Carlo <|cos theta|>={mc:.9f}; analytic value is 1/2. This proves the projection factor, not Lambda_L.',
    ))
    # Stereology combined with maximal core packing.
    results.append(ratio_record(
        'S2_crofton_plus_core_packing', 'Crofton/stereology', disk_packing_density,
        'FAIL_SCALE_INPUT_CORE_PACKING_TOO_SMALL',
        'sigmaLambda = (pi r_c^2)^{-1}; N/A = Lambda_L/2',
        'Stereology maps line density to piercings. If Lambda_L is only core packing, target is missed by ~40 orders.',
    ))

    # 3. Torsion-channel phase-space counting.
    gT = 2.0
    K_weyl3 = gT / (6.0 * math.pi**2)
    sigma_weyl3 = (1.0 / C.r_c**2) * rho_ratio * K_weyl3 * cv**3
    results.append(ratio_record(
        'T1_single_3D_Weyl_channel', 'torsion-channel phase-space', sigma_weyl3,
        'FAIL_PRE_REGISTERED_Weyl3D_TOO_SMALL',
        'sigmaLambda = r_c^{-2}(rho_core/rho_f)[2/(6 pi^2)](c/v)^3',
        'Direct 3D Weyl channel count with two transverse polarizations. Non-fit; misses target by many orders.',
    ))
    K_pair = (gT / (6.0 * math.pi**2))**2
    sigma_pair = (1.0 / C.r_c**2) * rho_ratio * K_pair * cv**6
    results.append(ratio_record(
        'T2_paired_3D_Weyl_channels', 'torsion-channel phase-space', sigma_pair,
        'FAIL_PRE_REGISTERED_WeylPair_TOO_SMALL',
        'sigmaLambda = r_c^{-2}(rho_core/rho_f)[2/(6 pi^2)]^2(c/v)^6',
        'Paired in/out or two-boundary Weyl count. Gets exponent 6 without a scan but coefficient is ~1.4e3 too small.',
    ))
    K_needed = target / ((1.0 / C.r_c**2) * rho_ratio * cv**6)
    K_seed = 16.0 / math.pi**2
    sigma_seed = (1.0 / C.r_c**2) * rho_ratio * K_seed * cv**6
    results.append(ratio_record(
        'T3_archived_seed_16_over_pi2', 'torsion-channel phase-space', sigma_seed,
        'TRIAL_FITTED_NEGATIVE_CONTROL_NOT_DERIVED',
        'sigmaLambda = r_c^{-2}(rho_core/rho_f)(16/pi^2)(c/v)^6',
        'Earlier seed relation. Included only as look-elsewhere controlled negative control; kernel/exponent not independently derived.',
        uses_fitted_kernel=True,
    ))

    # Required non-fit values.
    required = {
        'sigmaLambda_target_m^-2': target,
        'Lp_ref_m': Lp,
        'tp_ref_s': tp,
        'required_line_spacing_if_sigma_1_m': 1.0 / math.sqrt(target),
        'required_single_vortex_fugacity_multiplier_y_for_sigmaLambda_y_rc^-2': y_req_single,
        'required_pair_fugacity_multiplier_y_for_sigmaLambda_y2_rc^-2': y_req_pair,
        'rho_core_over_rho_f': rho_ratio,
        'c_over_vchar': cv,
        'K_needed_for_exponent6_density_contrast': K_needed,
        'K_seed_16_over_pi2': K_seed,
        'K_paired_weyl': K_pair,
        'degeneracy_multiplier_needed_over_paired_weyl': K_needed / K_pair,
        'monte_carlo_mean_abs_cos': mc,
        'analytic_mean_abs_cos': 0.5,
        'mc_abs_error': mc - 0.5,
    }

    # Main verdict rules.
    nonfit_hits = [r for r in results if (not r['uses_fitted_kernel_or_scan_motivated_factor']) and r['broad_target_hit_0p1_to_10']]
    verdict = {
        'overall': 'NO_NONFIT_MODEL_DERIVES_ROUTE_A_TARGET',
        'plain_language': 'Crofton/stereology derives the 1/2 factor only. Onsager/KT core packing fails by ~40 orders. Strict Weyl/torsion phase-space models fail by 3--9 orders. The old 16/pi^2 seed remains a fitted negative control, not evidence.',
        'nonfit_broad_hits_count': len(nonfit_hits),
        'accepted_as_derivation': False,
        'best_nonfit_model_by_abs_log_error': min([r for r in results if r['sigma_lambda_m^-2'] is not None and not r['uses_fitted_kernel_or_scan_motivated_factor']], key=lambda r: abs(r['log10_ratio_to_target'])),
        'best_any_model_by_abs_log_error': min([r for r in results if r['sigma_lambda_m^-2'] is not None], key=lambda r: abs(r['log10_ratio_to_target'])),
    }
    return {
        'status': '[RESEARCH-TRACK] [PREREGISTERED] [FALSIFICATION-HARNESS]',
        'constants': asdict(C),
        'target': required,
        'models': results,
        'verdict': verdict,
    }


def write_outputs(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    data = run_models()
    json_path = outdir / 'routeA_parallel_derivation_falsification_results.json'
    csv_path = outdir / 'routeA_parallel_derivation_falsification_models.csv'
    report_path = outdir / 'routeA_parallel_derivation_falsification_report.md'
    log_path = outdir / 'routeA_parallel_derivation_falsification.log'

    json_path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    rows = data['models']
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        fieldnames = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    t = data['target']
    lines = []
    lines.append('# Route A parallel derivation/falsification report\n')
    lines.append(f"Status: `{data['status']}`\n")
    lines.append('## Target\n')
    lines.append(f"- sigma_pierce Lambda_L target: `{t['sigmaLambda_target_m^-2']:.15e} m^-2`\n")
    lines.append(f"- target spacing if sigma=1: `{t['required_line_spacing_if_sigma_1_m']:.15e} m`\n")
    lines.append(f"- reference Planck time: `{t['tp_ref_s']:.15e} s`\n")
    lines.append('\n## Model outcomes\n')
    for r in rows:
        lines.append(f"### {r['name']}\n")
        lines.append(f"Family: `{r['family']}`  \n")
        lines.append(f"Status: `{r['status']}`  \n")
        lines.append(f"Formula: `{r['formula']}`  \n")
        if r['sigma_lambda_m^-2'] is not None:
            lines.append(f"sigmaLambda = `{r['sigma_lambda_m^-2']:.15e} m^-2`  \n")
            lines.append(f"ratio to target = `{r['ratio_to_target']:.15e}`  \n")
            lines.append(f"log10 ratio = `{r['log10_ratio_to_target']:.6f}`  \n")
            lines.append(f"t_model/t_ref = `{r['t_over_t_ref']:.15e}`  \n")
        lines.append(f"Note: {r['note']}\n\n")
    lines.append('## Verdict\n')
    lines.append(data['verdict']['plain_language'] + '\n')
    lines.append('\n## Key falsification numbers\n')
    lines.append(f"- Required BKT single-density multiplier y: `{t['required_single_vortex_fugacity_multiplier_y_for_sigmaLambda_y_rc^-2']:.15e}`\n")
    lines.append(f"- Required BKT pair fugacity y: `{t['required_pair_fugacity_multiplier_y_for_sigmaLambda_y2_rc^-2']:.15e}`\n")
    lines.append(f"- Required exponent-6 kernel K: `{t['K_needed_for_exponent6_density_contrast']:.15e}`\n")
    lines.append(f"- Strict paired-Weyl kernel: `{t['K_paired_weyl']:.15e}`\n")
    lines.append(f"- Multiplier needed over paired Weyl: `{t['degeneracy_multiplier_needed_over_paired_weyl']:.15e}`\n")
    report_path.write_text(''.join(lines), encoding='utf-8')

    log = []
    log.append('Route A parallel derivation/falsification harness\n')
    log.append('='*72 + '\n')
    log.append(data['verdict']['plain_language'] + '\n')
    log.append(f"nonfit_broad_hits_count={data['verdict']['nonfit_broad_hits_count']}\n")
    log.append(f"accepted_as_derivation={data['verdict']['accepted_as_derivation']}\n")
    log_path.write_text(''.join(log), encoding='utf-8')
    return {'json': str(json_path), 'csv': str(csv_path), 'report': str(report_path), 'log': str(log_path)}


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    outdir = here.parent / 'results'
    paths = write_outputs(outdir)
    for k, v in paths.items():
        print(f'{k}: {v}')
