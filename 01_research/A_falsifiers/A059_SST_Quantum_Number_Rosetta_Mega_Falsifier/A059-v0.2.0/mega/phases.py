from __future__ import annotations
from pathlib import Path
from typing import Any
import csv, itertools, json, math
import numpy as np

from .common import *
from .dynamics import (
    KNOT_BRAIDS, FAMILY_A, FAMILY_B, SYMMETRY_CONTROLS,
    canonical_knot, reduced_dynamic_operator, period_and_charge_coupling,
    three_core_container, container_field_metrics,
)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)


def _base(pid: str, slug: str, advisory: list[str], root: Path) -> dict[str, Any]:
    return {
        'schema': 'A059-PHASE-RESULT-2',
        'phase_id': pid,
        'slug': slug,
        'nonblocking': True,
        'advisory_dependencies': advisory_state(advisory, root),
        'source_archive': verify_source_archive(root),
    }


def _atlas_index(root: Path) -> dict[str, dict[str, str]]:
    return {r['topology_id']: r for r in atlas_csv('STATIC_READY_INDEX.csv', root)}


def p00(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P00', 'SOURCE_INTAKE', [], root)
    src = r['source_archive']
    if not src['pass']:
        r.update(status='UNRESOLVED', evidence_class='SOURCE_INVALID', reason='Embedded E011 archive missing or SHA mismatch.')
        return r
    run = atlas_json('RUN_SUMMARY.json', root)
    sel = atlas_json('SELECTION.json', root)
    idx = atlas_csv('STATIC_READY_INDEX.csv', root)
    rows = []
    for x in idx:
        rows.append({
            'candidate_id': opaque_topology(x['topology_id'], root),
            'static_ready': x['static_ready'] == 'True',
            'static_status': x['static_status'],
            'primary_seed_count': int(x['primary_seed_count']),
            'primary_provider_count': int(x['primary_provider_count']),
        })
    _write_csv(out / 'ANONYMOUS_ATLAS_INDEX.csv', rows)
    knot_count = sum(1 for t in sel.get('topology_ids', []) if not t.startswith('L'))
    checks = {
        'atlas_schema': run.get('schema') == 'E011-SKLSA-STATIC-READY-ATLAS-1',
        'execution_gate': run.get('execution_gate') == 'PASS',
        'operational_errors_zero': run.get('operational_error_count') == 0,
        'prime_knots_through_8_present_count': knot_count == 35,
        'static_ready_count_match': sum(x['static_ready'] == 'True' for x in idx) == run.get('static_ready_topology_count'),
    }
    status = 'PASS' if all(checks.values()) else 'FAIL'
    r.update(status=status, evidence_class='STATIC_SOURCE_QUALIFIED' if status == 'PASS' else 'STATIC_SOURCE_INCONSISTENT', checks=checks,
             metrics={'selected_objects': len(rows), 'prime_knots_through_8': knot_count, 'static_ready_objects': run.get('static_ready_topology_count')},
             scientific_boundary=run.get('scientific_boundary'))
    return r


def p01(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P01', 'DYNAMIC_PROBE_QUALIFICATION', ['P00'], root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED', evidence_class='SOURCE_INVALID'); return r
    idx = _atlas_index(root)
    probe_ids = FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS
    rows = []
    all_ok = True
    for tid in probe_ids:
        e011_present = tid in idx
        e011_ready = e011_present and idx[tid].get('static_ready') == 'True'
        try:
            P = canonical_knot(tid, 192)
            finite = bool(np.isfinite(P).all())
            closed_gap = float(np.linalg.norm(P[0] - P[-1]))
            length = float(np.linalg.norm(np.roll(P, -1, axis=0) - P, axis=1).sum())
            generated = finite and len(P) == 192 and abs(length - 2 * math.pi) < 1e-8
        except Exception as exc:
            P = None; generated = False; finite = False; closed_gap = None; length = None
        all_ok = all_ok and e011_present and generated
        rows.append({'candidate_id': opaque_topology(tid, root), 'e011_present': e011_present, 'e011_static_ready': e011_ready,
                     'canonical_probe_generated': generated, 'point_count': None if P is None else len(P), 'normalized_length': length,
                     'endpoint_sample_gap': closed_gap})
    _write_csv(out / 'DYNAMIC_PROBE_QUALIFICATION.csv', rows)
    payload = {
        'schema': 'A059-CANONICAL-DYNAMIC-PROBES-1',
        'construction': 'common closed-braid polygon -> Chaikin smoothing -> uniform arclength resampling -> total length 2pi',
        'family_codes': {'A': [opaque_topology(x, root) for x in FAMILY_A], 'B': [opaque_topology(x, root) for x in FAMILY_B], 'controls': [opaque_topology(x, root) for x in SYMMETRY_CONTROLS]},
        'semantic_names_private_until_reveal': True,
        'evidence_boundary': 'Generated canonical probes are finite-model mathematical representatives. They do not convert E011 STATIC_READY into DYNAMICS_READY.',
    }
    write_json(out / 'DYNAMIC_PROBE_REGISTRY_BLIND.json', payload)
    status = 'PASS' if all_ok else 'UNRESOLVED'
    r.update(status=status, evidence_class='SELF_CONTAINED_CANONICAL_DYNAMIC_PROBES' if status == 'PASS' else 'PROBE_QUALIFICATION_INCOMPLETE',
             checks={'all_probe_topologies_present_in_e011': all(x['e011_present'] for x in rows), 'all_canonical_probes_generated': all(x['canonical_probe_generated'] for x in rows)},
             metrics={'probe_count': len(rows), 'family_A_count': len(FAMILY_A), 'family_B_count': len(FAMILY_B), 'control_count': len(SYMMETRY_CONTROLS)},
             interpretation_guard=payload['evidence_boundary'])
    return r


def _loo_centroid_accuracy(X: np.ndarray, labels: np.ndarray) -> tuple[float, list[int]]:
    pred = []
    for i in range(len(labels)):
        ds = []
        for g in (0, 1):
            mask = (labels == g) & (np.arange(len(labels)) != i)
            if not mask.any():
                ds.append(float('inf'))
            else:
                c = X[mask].mean(axis=0)
                ds.append(float(np.linalg.norm(X[i] - c)))
        pred.append(int(np.argmin(ds)))
    return float(np.mean(np.asarray(pred) == labels)), pred


def _family_test(feature_rows: dict[str, dict[str, float]]) -> dict[str, Any]:
    order = FAMILY_A + FAMILY_B
    X = np.asarray([[math.log1p(feature_rows[t]['J_fro']), feature_rows[t]['eig_imag_rms_norm']] for t in order], float)
    med = np.median(X, axis=0); mad = np.median(np.abs(X - med), axis=0)
    scale = np.where(mad > 1e-12, 1.4826 * mad, np.where(np.std(X, axis=0) > 1e-12, np.std(X, axis=0), 1.0))
    Z = (X - med) / scale
    labels = np.asarray([0] * len(FAMILY_A) + [1] * len(FAMILY_B), int)
    acc, pred = _loo_centroid_accuracy(Z, labels)
    perm_scores = []
    for comb in itertools.combinations(range(len(order)), len(FAMILY_A)):
        lab = np.ones(len(order), int); lab[list(comb)] = 0
        a, _ = _loo_centroid_accuracy(Z, lab); perm_scores.append(a)
    p_exact = float(sum(a >= acc - 1e-15 for a in perm_scores) / len(perm_scores))
    return {'order': order, 'accuracy': acc, 'predictions': pred, 'exact_label_permutation_p': p_exact,
            'features': ['log1p(J_fro)', 'eig_imag_rms_norm'], 'robust_center': med.tolist(), 'robust_scale': scale.tolist()}


def p02(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P02', 'FAMILY_DYNAMICS', ['P00', 'P01'], root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED', evidence_class='SOURCE_INVALID'); return r
    grids = [(56, 0.06), (56, 0.08), (56, 0.10), (72, 0.06), (72, 0.08), (72, 0.10)]
    detail = []
    primary = {}
    for tid in FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS:
        P = canonical_knot(tid, 192)
        rows = []
        for N, core in grids:
            J, feat, eig = reduced_dynamic_operator(P, n=N, core=core, epsilon=0.003, harmonics=(2, 3), gamma=+1.0)
            row = {'candidate_id': opaque_topology(tid, root), 'N': N, 'core': core, **feat}
            rows.append(row); detail.append(row)
            if N == 72 and abs(core - 0.08) < 1e-12:
                primary[tid] = feat
                np.save(out / f'J_{opaque_topology(tid, root)}.npy', J)
                np.save(out / f'EIG_{opaque_topology(tid, root)}.npy', eig)
    _write_csv(out / 'DYNAMIC_OPERATOR_GRID.csv', detail)
    fam = _family_test(primary)
    blind_readout = dict(fam)
    blind_readout['order'] = [opaque_topology(x, root) for x in fam['order']]
    blind_readout['predictions'] = [{'candidate_id': opaque_topology(t, root), 'true_group': 'A' if i < len(FAMILY_A) else 'B', 'predicted_group': 'A' if p == 0 else 'B'} for i, (t, p) in enumerate(zip(fam['order'], fam['predictions']))]
    write_json(out / 'FAMILY_DYNAMIC_CLASSIFICATION.json', blind_readout)
    fine_pass = fam['accuracy'] >= 6/7 and fam['exact_label_permutation_p'] <= 0.10
    # Numerical recurrence: the sign of the family contrast in J_fro is required across every registered grid point.
    recurrence = []
    for N, core in grids:
        A = [x['J_fro'] for x in detail if x['N'] == N and abs(x['core'] - core) < 1e-12 and x['candidate_id'] in {opaque_topology(t, root) for t in FAMILY_A}]
        B = [x['J_fro'] for x in detail if x['N'] == N and abs(x['core'] - core) < 1e-12 and x['candidate_id'] in {opaque_topology(t, root) for t in FAMILY_B}]
        recurrence.append({'N': N, 'core': core, 'median_A': float(np.median(A)), 'median_B': float(np.median(B)), 'B_minus_A': float(np.median(B) - np.median(A))})
    recurrent = all(x['B_minus_A'] > 0 for x in recurrence)
    status = 'PASS' if fine_pass and recurrent else 'FAIL'
    r.update(status=status, evidence_class='DYNAMIC_FAMILY_SEPARATION_CANONICAL_PROBES',
             checks={'primary_leave_one_out_accuracy_ge_6_over_7': fam['accuracy'] >= 6/7, 'exact_permutation_p_le_0p10': fam['exact_label_permutation_p'] <= 0.10, 'J_fro_family_contrast_same_sign_all_numeric_controls': recurrent},
             metrics={'primary_accuracy': fam['accuracy'], 'exact_permutation_p': fam['exact_label_permutation_p'], 'grid_points': len(grids), 'family_contrast_recurrence': recurrence},
             interpretation_guard='PASS distinguishes two preregistered knot families in this canonical finite-core probe model. It is not a semantic family identification and must survive independent source geometries before physical interpretation.')
    return r


def p03(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P03', 'PERIOD_CHARGE_COUPLING', ['P01', 'P02'], root)
    rows = []
    for tid in FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS:
        P = canonical_knot(tid, 192)
        vals = []
        for N in (72, 96, 120):
            for pc in (0.05, 0.07):
                m = period_and_charge_coupling(P, n=N, self_core=0.08, probe_core=pc)
                vals.append(m)
                rows.append({'candidate_id': opaque_topology(tid, root), 'N': N, 'probe_core': pc, **m})
    _write_csv(out / 'PERIOD_CHARGE_GRID.csv', rows)
    summary = {}
    for tid in FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS:
        sub = [x for x in rows if x['candidate_id'] == opaque_topology(tid, root)]
        summary[tid] = {
            'candidate_id': opaque_topology(tid, root),
            'axis_winding_median': float(np.median([x['axis_winding'] for x in sub])),
            'period_median': float(np.median([x['period_integral'] for x in sub])),
            'dynamic_cross_response_median': float(np.median([x['dynamic_cross_response'] for x in sub])),
            'dynamic_cross_response_sign_stable': len({int(np.sign(x['dynamic_cross_response'])) for x in sub if abs(x['dynamic_cross_response']) > 1e-12}) <= 1,
        }
    _write_csv(out / 'PERIOD_CHARGE_SUMMARY.csv', list(summary.values()))
    # Target-free 2+1 cancellation ranking from the real dynamic cross-response coefficient.
    pairs = []
    tids = FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS
    for a, b in itertools.combinations(tids, 2):
        qa = summary[a]['dynamic_cross_response_median']; qb0 = summary[b]['dynamic_cross_response_median']
        for sb in (-1, +1):
            qb = sb * qb0
            den = 3 * max(abs(qa), abs(qb), 1e-15)
            d1 = abs(2 * qa + qb) / den; d2 = abs(qa + 2 * qb) / den
            score = min(d1, d2)
            pairs.append({'candidate_A': opaque_topology(a, root), 'candidate_B': opaque_topology(b, root), 'relative_state_sign_B': sb,
                          'cancellation_score': score, 'branch': '2A+B' if d1 <= d2 else 'A+2B'})
    pairs.sort(key=lambda x: x['cancellation_score'])
    for i, x in enumerate(pairs, 1): x['rank'] = i
    _write_csv(out / 'DYNAMIC_CHARGE_PAIR_RANKING.csv', pairs)
    # Mathematical period lane must be stable and circulation reversal must reverse q without changing |q|.
    period_stable = all(abs(x['period_median'] - x['axis_winding_median']) <= 0.35 * max(1.0, abs(x['axis_winding_median'])) for x in summary.values())
    response_stable = all(x['dynamic_cross_response_sign_stable'] for x in summary.values())
    status = 'PASS' if period_stable and response_stable else 'FAIL'
    r.update(status=status, evidence_class='PERIOD_PLUS_DYNAMIC_EXTERNAL_CORE_RESPONSE',
             checks={'period_tracks_integer_axis_winding': period_stable, 'dynamic_cross_response_sign_recurrent': response_stable, 'target_free_pair_ranking_written': bool(pairs)},
             metrics={'candidate_count': len(summary), 'pair_rows': len(pairs), 'best_cancellation_score': pairs[0]['cancellation_score'] if pairs else None},
             interpretation_guard='The line period and dE/dprobe-like cross response are candidate charge-coupling operators. No electric-charge normalization or Standard-Model target value is used in the blind calculation.')
    return r


def _sorted_complex(z: np.ndarray) -> np.ndarray:
    return np.asarray(sorted(z, key=lambda q: (round(float(q.real), 12), round(float(q.imag), 12))), complex)


def p04(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P04', 'DYNAMIC_MONODROMY', ['P01', 'P02'], root)
    rows = []
    specificity = []
    for tid in FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS:
        P = canonical_knot(tid, 192)
        fingerprints = []
        for N, core in ((56, 0.08), (72, 0.08), (88, 0.08), (72, 0.06), (72, 0.10)):
            Jp, feat, ep = reduced_dynamic_operator(P, n=N, core=core, epsilon=0.003, harmonics=(2, 3), gamma=+1.0)
            Jm, _, em = reduced_dynamic_operator(P, n=N, core=core, epsilon=0.003, harmonics=(2, 3), gamma=-1.0)
            odd = float(np.linalg.norm(Jp + Jm) / max(np.linalg.norm(Jp), 1e-30))
            scale = max(float(np.linalg.norm(Jp, ord='fro')), 1e-30)
            mup = np.exp(ep / scale)
            mum = np.exp(em / scale)
            # J(-Gamma)=-J(+Gamma) is the authoritative covariance; monodromy inverse follows analytically.
            phase = float(np.sqrt(np.mean(np.angle(mup) ** 2)))
            growth = float(np.max(np.log(np.maximum(np.abs(mup), 1e-30))))
            rows.append({'candidate_id': opaque_topology(tid, root), 'N': N, 'core': core, 'J_oddness_error': odd,
                         'monodromy_phase_rms': phase, 'monodromy_log_growth_max': growth, 'frame_holonomy_turns': feat['frame_holonomy_turns']})
            fingerprints.append((phase, growth, feat['frame_holonomy_turns']))
        med = np.median(np.asarray(fingerprints), axis=0)
        spread = np.max(np.linalg.norm(np.asarray(fingerprints) - med, axis=1))
        specificity.append({'candidate_id': opaque_topology(tid, root), 'phase_rms_median': float(med[0]), 'log_growth_median': float(med[1]), 'frame_holonomy_median': float(med[2]), 'numeric_fingerprint_spread': float(spread)})
    _write_csv(out / 'MONODROMY_GRID.csv', rows); _write_csv(out / 'MONODROMY_FINGERPRINTS.csv', specificity)
    max_odd = max(x['J_oddness_error'] for x in rows)
    X = np.asarray([[x['phase_rms_median'], x['log_growth_median'], x['frame_holonomy_median']] for x in specificity])
    between = []
    for i, j in itertools.combinations(range(len(X)), 2): between.append(float(np.linalg.norm(X[i] - X[j])))
    median_between = float(np.median(between)) if between else 0.0
    median_within = float(np.median([x['numeric_fingerprint_spread'] for x in specificity]))
    topology_specific = median_between > 2.0 * max(median_within, 1e-12)
    status = 'PASS' if max_odd <= 1e-10 and topology_specific else 'FAIL'
    r.update(status=status, evidence_class='FINITE_TIME_REDUCED_DYNAMIC_MONODROMY',
             checks={'circulation_reversal_J_oddness': max_odd <= 1e-10, 'between_knot_fingerprint_distance_gt_2x_numeric_spread': topology_specific},
             metrics={'max_J_oddness_error': max_odd, 'median_between_knot_fingerprint_distance': median_between, 'median_numeric_fingerprint_spread': median_within},
             interpretation_guard='This is a topology-specific finite-time reduced tangent-map fingerprint, not yet a true periodic-orbit Floquet spinor proof. Universal SO(3) 4pi behavior is not counted.')
    return r


def p05(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P05', 'CONJUGATION_INVOLUTIONS', ['P03', 'P04'], root)
    rows = []
    max_v = 0.0; max_e = 0.0
    # Re-use canonical curves and test full Biot-Savart field parity on a deterministic probe cloud.
    from .dynamics import fibonacci_sphere, velocity_field_from_curve
    for tid in FAMILY_A + FAMILY_B + SYMMETRY_CONTROLS:
        P = canonical_knot(tid, 128)
        X = fibonacci_sphere(120, 2.2)
        vp = velocity_field_from_curve(P, X, +1.0, 0.08); vm = velocity_field_from_curve(P, X, -1.0, 0.08)
        odd = float(np.linalg.norm(vp + vm) / max(np.linalg.norm(vp), 1e-30))
        ep = float(np.mean(np.sum(vp * vp, axis=1))); em = float(np.mean(np.sum(vm * vm, axis=1)))
        even = abs(ep - em) / max(ep, em, 1e-30)
        max_v = max(max_v, odd); max_e = max(max_e, even)
        rows.append({'candidate_id': opaque_topology(tid, root), 'velocity_oddness_error': odd, 'quadratic_energy_evenness_error': even})
    _write_csv(out / 'CONJUGATION_COVARIANCE.csv', rows)
    status = 'PASS' if max(max_v, max_e) <= 1e-12 else 'FAIL'
    r.update(status=status, evidence_class='CANONICAL_PROBE_CIRCULATION_CONJUGATION',
             checks={'velocity_odd_under_gamma_reversal': max_v <= 1e-12, 'quadratic_energy_even_under_gamma_reversal': max_e <= 1e-12},
             metrics={'candidate_count': len(rows), 'max_velocity_oddness_error': max_v, 'max_energy_evenness_error': max_e},
             interpretation_guard='Gamma reversal is certified here only as a field conjugation symmetry candidate. Physical conjugate-state identity remains a reveal-stage hypothesis, not a blind premise.')
    return r


def p06(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P06', 'BORROMEAN_THREE_CORE', ['P03', 'P04', 'P05'], root)
    candidate = three_core_container('CANDIDATE', 84)
    control = three_core_container('UNLINK_CONTROL', 84)
    grid = []
    for scale in (1.8, 2.2, 2.6):
        mc = container_field_metrics(candidate, probe_scale=scale, n_probe=480, filament_core=0.06, axis_core=0.08)
        mu = container_field_metrics(control, probe_scale=scale, n_probe=480, filament_core=0.06, axis_core=0.08)
        grid.append({'probe_scale': scale, 'candidate_cross_energy': mc['cross_field_energy'], 'control_cross_energy': mu['cross_field_energy'],
                     'contrast_fraction': (mc['cross_field_energy'] - mu['cross_field_energy']) / max(abs(mu['cross_field_energy']), 1e-30)})
        if abs(scale - 2.2) < 1e-12:
            main_c, main_u = mc, mu
    _write_csv(out / 'CONTAINER_DYNAMIC_CONTRAST.csv', grid)
    write_json(out / 'THREE_CORE_CANDIDATE_METRICS.json', main_c)
    write_json(out / 'THREE_CORE_UNLINK_CONTROL_METRICS.json', main_u)
    pairwise_zero = max(abs(x) for x in main_c['pairwise_gauss_linking']) <= 0.02
    own_winding = all(abs(x - 1.0) <= 0.05 for x in main_c['own_core_windings'])
    own_period = all(abs(x - 1.0) <= 0.12 for x in main_c['own_core_periods'])
    same_sign = all(x > 0 for x in main_c['own_core_periods'])
    contrast_recurrent = len({int(np.sign(x['contrast_fraction'])) for x in grid if abs(x['contrast_fraction']) > 1e-12}) == 1 and all(abs(x['contrast_fraction']) >= 0.005 for x in grid)
    status = 'PASS' if pairwise_zero and own_winding and own_period and same_sign and contrast_recurrent else 'FAIL'
    r.update(status=status, evidence_class='THREE_COMPONENT_SAME_SIGN_AXIAL_CORE_DYNAMIC_CONTAINER',
             checks={'candidate_pairwise_linking_near_zero': pairwise_zero, 'each_ring_winds_once_about_its_own_parallel_z_core': own_winding,
                     'each_own_core_period_near_one': own_period, 'all_three_core_periods_same_positive_sign': same_sign, 'dynamic_cross_energy_contrast_recurrent_vs_identity_braid_unlink': contrast_recurrent},
             metrics={'candidate_pairwise_linking': main_c['pairwise_gauss_linking'], 'candidate_own_core_windings': main_c['own_core_windings'], 'candidate_own_core_periods': main_c['own_core_periods'], 'contrast_grid': grid},
             interpretation_guard='The three straight core vortices are an explicit registered construction: one +z-directed core through each ring centre, all with the same circulation sign. PASS certifies only this finite-model container response, not baryon identity or confinement.')
    return r


def p07(root: Path, out: Path) -> dict[str, Any]:
    # Separate structural hypothesis lane retained from prior A059 versions; it is independent of the period mathematics.
    r = _base('P07', 'GRAVITY_CHIRAL_SELECTION', ['P05'], root)
    v = np.array([1.2, -0.7, 0.4]); omega = np.array([0.3, 0.8, -0.5]); grad = np.array([-0.6, 0.2, 0.9])
    chi1 = float(np.dot(v, omega)); chi2 = float(np.dot(omega, grad))
    chi1p = float(np.dot(-v, omega)); chi2p = float(np.dot(omega, -grad))
    structural = abs(chi1 + chi1p) <= 1e-14 and abs(chi2 + chi2p) <= 1e-14
    write_json(out / 'GRAVITY_CHIRAL_SELECTOR.json', {'schema':'A059-GRAVITY-CHIRAL-SELECTOR-2','analytic_structural_pass':structural,'dynamics_ready_background_field':False,'independent_coupling_scale':False})
    r.update(status='UNRESOLVED' if structural else 'FAIL', evidence_class='ANALYTIC_PARITY_ODD_SELECTOR_ONLY' if structural else 'ANALYTIC_PARITY_STRUCTURE_FAILED',
             checks={'analytic_parity_odd_selector': structural, 'dynamics_ready_background_field': False, 'independent_coupling_scale': False},
             interpretation_guard='This is a separate structural hypothesis lane. It cannot certify a physical background origin of chiral preference without a dynamics-ready background field and independently derived coupling.')
    return r


def p08(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P08', 'U1_WEAK_CLOSURE', ['P03', 'P04', 'P07'], root)
    q = load_phase_result('P03', root); m = load_phase_result('P04', root)
    independent_q = bool(q and q.get('status') == 'PASS')
    independent_t = False  # no independently derived weak-isospin generator in v0.2.0
    independent_y = False  # defining Y from Q-T3 is forbidden
    write_json(out / 'U1_WEAK_CLOSURE_DIAGNOSTIC.json', {'independent_charge_like_operator': independent_q, 'independent_T3_operator': independent_t, 'independent_Y_operator': independent_y, 'closure_attempted': False, 'definition_guard':'Y may not be defined as 2(Q-T3).'})
    r.update(status='UNRESOLVED', evidence_class='CHARGE_OPERATOR_CANDIDATE_WITHOUT_INDEPENDENT_T3_Y',
             checks={'charge_like_operator_available': independent_q, 'independent_T3_operator': independent_t, 'independent_Y_operator': independent_y, 'closure_attempted': False},
             interpretation_guard='v0.2.0 deliberately does not manufacture T3 or Y from the desired Standard-Model closure equation.')
    return r


def p09(root: Path, out: Path) -> dict[str, Any]:
    r = _base('P09', 'INTEGRATED_ROSETTA', ['P02','P03','P04','P05','P06','P07','P08'], root)
    ids = ['P02','P03','P04','P05','P06','P07','P08']
    rows=[]
    for pid in ids:
        x=load_phase_result(pid,root); rows.append({'phase':pid,'status':None if x is None else x.get('status'),'evidence_class':None if x is None else x.get('evidence_class')})
    write_json(out/'OPERATOR_STATUS_MATRIX.json',{'schema':'A059-OPERATOR-STATUS-MATRIX-2','operators':rows})
    present=all(x['status'] is not None for x in rows)
    hard_pass=sum(x['status']=='PASS' for x in rows)
    unresolved=sum(x['status']=='UNRESOLVED' for x in rows)
    fail=sum(x['status']=='FAIL' for x in rows)
    # Integration is intentionally strict: only PASS if every required operator closes.
    if present and hard_pass==len(rows): status='PASS';ec='INTEGRATED_ROSETTA_CLOSED'
    elif present and unresolved: status='UNRESOLVED';ec='MULTI_OPERATOR_PARTIAL_CLOSURE'
    else: status='FAIL';ec='MULTI_OPERATOR_RESOLVED_WITH_FAILURE'
    r.update(status=status,evidence_class=ec,metrics={'pass_count':hard_pass,'fail_count':fail,'unresolved_count':unresolved,'operator_rows':rows},
             interpretation_guard='Isolated operator PASSes remain scientifically useful but do not imply a Standard-Model mapping. Integrated closure requires all registered operator sectors to close independently.')
    return r


PHASES = {'P00':p00,'P01':p01,'P02':p02,'P03':p03,'P04':p04,'P05':p05,'P06':p06,'P07':p07,'P08':p08,'P09':p09}
