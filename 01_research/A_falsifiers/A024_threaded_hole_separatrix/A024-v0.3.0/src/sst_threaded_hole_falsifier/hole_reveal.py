from __future__ import annotations
from pathlib import Path
import csv, json, math
from collections import defaultdict

import numpy as np

from .stats import exact_sign_p_ge


def _load_case(blind: Path, cid: str) -> dict:
    return json.loads((blind / 'cases' / f'{cid}.json').read_text(encoding='utf-8'))


def _f(x, default=float('nan')):
    try:
        return float(x)
    except Exception:
        return default


def _is_robust_verdict(v: str) -> bool:
    return str(v).startswith('ROBUST_')


def _sealed_winner_condition(br: dict, active: str, null: str) -> str:
    w = br.get('winner_anonymous', '')
    if w == 'A':
        cid = br['candidate_a']
    elif w == 'B':
        cid = br['candidate_b']
    else:
        return str(w).lower() if w else 'indeterminate'
    return 'active' if cid == active else 'null' if cid == null else 'unknown'


def _sealed_effect_active_over_null(br: dict, active: str) -> float:
    """Map the already-sealed A/B log-cost effect to active/null orientation."""
    z = _f(br.get('median_log_ratio_A_over_B'))
    if not (np.isfinite(z) or np.isinf(z)):
        return float('nan')
    return z if br['candidate_a'] == active else -z


def reveal_hole(blind_dir, private_dir, cfg: dict, out_dir) -> dict:
    """Post-seal identity reveal for the v0.3.0 central-hole gate.

    Two questions remain separate:
      1. Existence: does either anonymous realization exhibit a robust Lagrangian
         hole/atmosphere, beyond geometric centerline clearance?
      2. Causality: after identity reveal, does nonzero central-thread circulation
         improve the preregistered *sealed* blind cost vector versus the identical
         zero-circulation visual control?

    The causal sign test uses the anonymous winner/effect written before reveal;
    it does not select a favorable metric after identities are known.
    """
    blind = Path(blind_dir)
    private = Path(private_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    pkey = {r['pair_id']: r for r in csv.DictReader(open(private/'pair_key.csv', encoding='utf-8'))}
    brows = list(csv.DictReader(open(blind/'blind_pair_results.csv', encoding='utf-8')))
    rows = []

    for br in brows:
        k = pkey[br['pair_id']]
        active, null = k['candidate_active'], k['candidate_null']
        ra, rn = _load_case(blind, active), _load_case(blind, null)
        if 'hole_gate' not in ra or 'hole_gate' not in rn:
            continue
        ha, hn = ra['hole_gate'], rn['hole_gate']
        cost_a = _f(ha.get('hole_robustness_cost'))
        cost_n = _f(hn.get('hole_robustness_cost'))
        rows.append({
            'pair_id': br['pair_id'],
            'carrier_id': k['carrier_id'],
            'family': k['family'],
            'beta_parameter': _f(k.get('beta_parameter')),
            'beta_total_thread_over_core': _f(k.get('beta_total_thread_over_core')),
            'n_threads': int(k['n_threads']),
            'helix_turns': _f(k['helix_turns']),
            'sealed_decision_basis': br.get('decision_basis',''),
            'sealed_winner_condition': _sealed_winner_condition(br, active, null),
            'sealed_log_ratio_active_over_null': _sealed_effect_active_over_null(br, active),
            'active_cost': cost_a,
            'null_cost': cost_n,
            'active_minus_null_robustness_cost': cost_a - cost_n,
            'active_score': _f(ha.get('hole_robustness_score')),
            'null_score': _f(hn.get('hole_robustness_score')),
            'active_verdict': ha.get('verdict',''),
            'null_verdict': hn.get('verdict',''),
            'active_initial_class': ha.get('initial_transport_class',''),
            'null_initial_class': hn.get('initial_transport_class',''),
            'active_final_class': ha.get('final_transport_class',''),
            'null_final_class': hn.get('final_transport_class',''),
            'active_clearance_ratio': _f(ha.get('clearance_ratio_final_over_initial')),
            'null_clearance_ratio': _f(hn.get('clearance_ratio_final_over_initial')),
            'active_perturb_same_class_fraction': _f(ha.get('perturb_same_class_fraction')),
            'null_perturb_same_class_fraction': _f(hn.get('perturb_same_class_fraction')),
            'active_perturb_robust_fraction': _f(ha.get('perturb_robust_class_fraction')),
            'null_perturb_robust_fraction': _f(hn.get('perturb_robust_class_fraction')),
            'active_dynamic_status': ha.get('dynamic',{}).get('dynamic_status',''),
            'null_dynamic_status': hn.get('dynamic',{}).get('dynamic_status',''),
            'active_robust': _is_robust_verdict(ha.get('verdict','')),
            'null_robust': _is_robust_verdict(hn.get('verdict','')),
        })

    csv_path = out/'hole_revealed_pairs.csv'
    fields = list(rows[0].keys()) if rows else ['pair_id']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    # Causal inference uses one sealed anonymous vote per carrier after repeated
    # beta/pitch/gamma settings are collapsed.  No repeated condition is treated
    # as an independent knot sample.
    by_vote = defaultdict(list)
    by_effect = defaultdict(list)
    for r in rows:
        wc = r['sealed_winner_condition']
        if wc in ('active','null'):
            by_vote[r['carrier_id']].append(-1 if wc == 'active' else 1)
        e = r['sealed_log_ratio_active_over_null']
        if np.isfinite(e):
            by_effect[r['carrier_id']].append(float(e))
    carrier_votes = {cid:int(np.sign(np.median(v))) for cid,v in by_vote.items() if v}
    active_wins = sum(v < 0 for v in carrier_votes.values())
    null_wins = sum(v > 0 for v in carrier_votes.values())
    nonzero = active_wins + null_wins
    p_active = exact_sign_p_ge(active_wins, nonzero)
    p_null = exact_sign_p_ge(null_wins, nonzero)
    carrier_median_effect = {cid:float(np.median(v)) for cid,v in by_effect.items() if v}
    alpha = float(cfg.get('reveal_alpha', 0.05))

    if nonzero and p_active <= alpha and active_wins > null_wins:
        causal_status = 'SUPPORTS_THREAD_CIRCULATION_STABILIZES_DYNAMICAL_HOLE'
    elif nonzero and p_null <= alpha and null_wins > active_wins:
        causal_status = 'FALSIFIES_THREAD_CIRCULATION_AS_HOLE_STABILIZER'
    else:
        causal_status = 'INDETERMINATE_THREAD_CIRCULATION_CAUSAL_EFFECT'

    # Existence is deliberately separate from the active/null causal comparison.
    # A robust hole in both arms is evidence that the carrier flow itself can
    # produce it, not evidence that the threaded circulation caused it.
    robust_active_carriers = 0
    robust_null_carriers = 0
    robust_any_carriers = 0
    robust_both_carriers = 0
    robust_by_carrier = {}
    all_carriers = sorted(set(r['carrier_id'] for r in rows))
    for cid in all_carriers:
        rr = [r for r in rows if r['carrier_id'] == cid]
        af = float(np.mean([bool(r['active_robust']) for r in rr])) if rr else 0.0
        nf = float(np.mean([bool(r['null_robust']) for r in rr])) if rr else 0.0
        ar = af > 0.5
        nr = nf > 0.5
        robust_by_carrier[cid] = {
            'active_robust_fraction':af,
            'null_robust_fraction':nf,
            'active_majority_robust':ar,
            'null_majority_robust':nr,
        }
        robust_active_carriers += int(ar)
        robust_null_carriers += int(nr)
        robust_any_carriers += int(ar or nr)
        robust_both_carriers += int(ar and nr)

    if rows and robust_any_carriers == 0:
        existence_status = 'VISUAL_HOLE_ONLY_WITHIN_TESTED_MODEL_AND_HORIZON'
    elif robust_both_carriers > 0:
        existence_status = 'DYNAMICAL_HOLE_DETECTED_ALSO_IN_ZERO_CIRCULATION_CONTROL'
    elif robust_active_carriers > 0 and robust_null_carriers == 0:
        existence_status = 'DYNAMICAL_HOLE_DETECTED_IN_ACTIVE_THREAD_ARM'
    elif robust_null_carriers > 0 and robust_active_carriers == 0:
        existence_status = 'DYNAMICAL_HOLE_DETECTED_IN_ZERO_CIRCULATION_CONTROL_ONLY'
    elif robust_any_carriers > 0:
        existence_status = 'DYNAMICAL_HOLE_DETECTED_WITH_MIXED_CARRIER_DEPENDENCE'
    else:
        existence_status = 'INDETERMINATE_DYNAMICAL_HOLE_EXISTENCE'

    # The primary answer to the user's physical question is existence.  The
    # causal status answers the distinct follow-up: what, if anything, does the
    # central thread circulation contribute?
    status = existence_status

    summary = {
        'campaign_format':'SST-THREADED-HOLE-REVEAL-3.0',
        'question':'Is the central threaded hole a robust dynamical structure or only a visual gap in centerline geometry?',
        'n_pairs':len(rows),
        'n_carriers':len(all_carriers),
        'existence_status':existence_status,
        'thread_circulation_causal_status':causal_status,
        'carrier_sealed_votes':carrier_votes,
        'carrier_median_sealed_log_ratio_active_over_null':carrier_median_effect,
        'n_carriers_nonzero_causal_vote':nonzero,
        'carrier_active_wins':active_wins,
        'carrier_null_wins':null_wins,
        'one_sided_exact_sign_p_active':p_active,
        'one_sided_exact_sign_p_null':p_null,
        'robust_by_carrier':robust_by_carrier,
        'robust_any_carriers_majority_conditions':robust_any_carriers,
        'robust_both_carriers_majority_conditions':robust_both_carriers,
        'robust_active_carriers_majority_conditions':robust_active_carriers,
        'robust_null_carriers_majority_conditions':robust_null_carriers,
        'status':status,
        'blind_inference_guard':(
            'Causal carrier votes come from the anonymous winner and preregistered multi-cost decision sealed before identity reveal. '
            'The post-reveal code does not select a favorable hole metric.'
        ),
        'interpretation_guard':(
            'The null has the same visible carrier and closed thread centerlines as the active condition, '
            'but thread circulation is exactly zero. A robust result in both arms establishes a carrier-generated '
            'dynamical transport structure but does not attribute it to thread circulation. A pass remains conditional '
            'on the regularized filament model, finite integration horizon, geometry-only axis estimator, and preregistered thresholds.'
        ),
    }
    (out/'HOLE_REVEAL_SUMMARY.json').write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=True)+'\n', encoding='utf-8')

    lines = [
        '# Kelvin–M\'Farlane Threaded-Hole Gate — post-seal reveal',
        '',
        f'Existence verdict: **{existence_status}**.',
        f'Thread-circulation causal verdict: **{causal_status}**.',
        '',
        '## Blind-control logic',
        '- Active and null candidates have identical visible carrier/thread centerline geometry.',
        '- Only the closed central-thread circulation differs, and that identity was hidden during scoring.',
        '- Causal carrier votes use the anonymous multi-cost winner sealed before identity reveal.',
        '- Existence and causal attribution are reported separately.',
        '',
        '## Carrier-clustered result',
        f'- Carriers with a majority-robust hole in either arm: {robust_any_carriers}/{len(all_carriers)}.',
        f'- Robust in both active and zero-circulation control: {robust_both_carriers}.',
        f'- Active-favorable sealed carrier votes: {active_wins}.',
        f'- Null-favorable sealed carrier votes: {null_wins}.',
        f'- One-sided exact sign p(active): {p_active:.6g}.',
        f'- One-sided exact sign p(null): {p_null:.6g}.',
        '',
        '## Meaning of a robust candidate',
        'A positive geometric clearance is insufficient. The candidate must show a coherent open channel or captured atmosphere, survive finite carrier evolution, preserve hole clearance and transport class, and survive both signs of preregistered normal perturbations.',
        '',
        '## Scope guards',
        summary['blind_inference_guard'],
        summary['interpretation_guard'],
    ]
    (out/'HOLE_CONCLUSIONS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return summary
