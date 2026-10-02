"""Versioned synthetic qualification; no independent dynamical physics claim."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import os
import platform
import secrets
import statistics
import sys
import numpy as np
import scipy
from .run_contract import (assert_unsealed, commit_preparation, create_run, load_config,
    mark_revealed, read_json, sha256_file, verify_reveal, verify_seal, write_json)


def prepare(root, suite='qualification', output_parent=None):
    root = Path(root)
    config = read_json(root / 'configs' / 'default.json')
    run = create_run(root, config['version'], suite, config, output_parent)
    template=read_json(root/'GATE_STATUS_MATRIX.json')
    write_json(run/'BLIND'/'gate_template.json', {key:template[key] for key in ('schema','source_conversation','allowed_statuses','items')})
    seed = secrets.randbits(63)
    rng = np.random.default_rng(seed)
    count = int(config['synthetic_case_count'])
    modes = np.array(config['modes'], float)
    labels = ['KELVIN_QUADRATIC'] * (count // 2) + ['TORSIONAL_LINEAR_GAPPED'] * (count - count // 2)
    rng.shuffle(labels)
    salt = secrets.token_hex(16)
    key = {'seed': seed, 'salt': salt, 'cases': {}}
    (run / 'BLIND' / 'input').mkdir()
    for index, label in enumerate(labels):
        case = hashlib.sha256(f'{salt}:{index}'.encode()).hexdigest()[:16]
        if label == 'KELVIN_QUADRATIC':
            beta = float(rng.uniform(.08, .30))
            true = beta * modes * modes
            parameters, exponent = {'beta': beta}, 2.
        else:
            speed, gap = float(rng.uniform(.7, 1.4)), float(rng.uniform(.02, .25))
            true = np.sqrt((speed * modes) ** 2 + gap ** 2)
            parameters, exponent = {'c_phase': speed, 'gap': gap}, 1.
        observed = true * (1 + rng.normal(0, config['relative_noise_sigma'], len(modes)))
        with (run / 'BLIND' / 'input' / f'case_{case}.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['k', 'omega'])
            writer.writerows(zip(modes, observed))
        key['cases'][case] = {'label': label, 'parameters': parameters, 'target_exponent': exponent}
    commit_preparation(run, key)
    return run


def analyze(run, backend='python'):
    from .campaign import analyze_input
    run = Path(run)
    assert_unsealed(run)
    folder = run / 'BLIND' / f'{backend}_backend'
    if folder.exists():
        raise FileExistsError('backend evidence already exists; create a new run')
    previous = os.environ.get('SST_BACKEND')
    try:
        os.environ['SST_BACKEND'] = backend
        return analyze_input(run / 'BLIND' / 'input', folder, load_config(run))[0]
    finally:
        if previous is None:
            os.environ.pop('SST_BACKEND', None)
        else:
            os.environ['SST_BACKEND'] = previous


def record_environment(run):
    run = Path(run)
    assert_unsealed(run)
    write_json(run / 'BLIND' / 'runtime_python.json', {'python': sys.version,
               'platform': platform.platform(), 'numpy': np.__version__, 'scipy': scipy.__version__})


def record_native(run):
    run = Path(run)
    assert_unsealed(run)
    spec = importlib.util.find_spec('torsion_native')
    if spec is None or not spec.origin:
        raise RuntimeError('native backend is unavailable')
    path = Path(spec.origin)
    write_json(run / 'BLIND' / 'runtime_native.json', {'module_name': path.name,
               'size_bytes': path.stat().st_size, 'sha256': sha256_file(path)})


def parity(run):
    import torsion_native
    from .models import kelvin_omega, torsion_omega, power_law_fit
    run = Path(run)
    assert_unsealed(run)
    modes = np.arange(1., 11.)
    checks = {}
    for label, python, native in [
        ('kelvin', kelvin_omega(modes, .17), torsion_native.kelvin_omega(modes, .17)),
        ('torsion', torsion_omega(modes, 1.1, .2), torsion_native.torsion_omega(modes, 1.1, .2))]:
        checks[label] = float(np.max(np.abs(python - native)))
    checks['slope_abs_error'] = abs(float(torsion_native.loglog_slope(modes, kelvin_omega(modes, .17))) - power_law_fit(modes, kelvin_omega(modes, .17))['p'])
    python_rows = read_json(run / 'BLIND' / 'python_backend' / 'case_metrics.json')
    native_rows = read_json(run / 'BLIND' / 'native_backend' / 'case_metrics.json')
    same_labels = len(python_rows) == len(native_rows) and all(a['anonymous_case_id'] == b['anonymous_case_id'] and a['classification'] == b['classification'] for a, b in zip(python_rows, native_rows))
    summary = {'passed': max(checks.values()) < 1e-12 and same_labels, 'checks': checks,
               'production_classifications_equal': same_labels}
    write_json(run / 'BLIND' / 'backend_parity_summary.json', summary)
    if not summary['passed']:
        raise RuntimeError('backend parity failed')
    return summary


def _evaluate(folder, key):
    rows = read_json(folder / 'case_metrics.json')
    if {row['anonymous_case_id'] for row in rows} != set(key['cases']) or len(rows) != len(key['cases']):
        raise RuntimeError('case inventory differs from committed private key')
    errors = [abs(row['power_exponent_p'] - key['cases'][row['anonymous_case_id']]['target_exponent']) for row in rows]
    correct = sum(row['classification'] == key['cases'][row['anonymous_case_id']]['label'] for row in rows)
    return {'count': len(rows), 'accuracy': correct / len(rows),
            'ambiguous': sum(row['classification'] == 'AMBIGUOUS' for row in rows),
            'median_abs_exponent_error': statistics.median(errors)}


def reveal(run):
    run = Path(run)
    verify_seal(run)
    from .reveal_constants import derived_scales
    if (run / 'REVEAL_COMMITMENT.json').exists():
        verify_reveal(run)
        return read_json(run / 'REVEALED' / 'reveal_report.json')
    if any((run / 'REVEALED').iterdir()):
        raise RuntimeError('partial reveal exists; refusing to overwrite')
    config = load_config(run)
    key = read_json(run / 'PRIVATE' / 'reveal_key.json')
    python = _evaluate(run / 'BLIND' / 'python_backend', key)
    controls = read_json(run / 'BLIND' / 'python_backend' / 'blind_summary.json')['controls']
    tests = {
        'classification_accuracy': python['accuracy'] >= config['classification_accuracy_gate'],
        'median_exponent_error': python['median_abs_exponent_error'] <= config['median_exponent_error_gate'],
        'circle_curvature': controls['circle_curvature_mean_abs_error'] <= config['circle_curvature_error_gate'],
        'circle_torsion': controls['circle_torsion_max_abs'] <= config['circle_torsion_gate'],
        'winding_gauge': controls['winding_gauge_error'] <= config['winding_gauge_error_gate']}
    native = None
    if (run / 'BLIND' / 'native_backend').exists():
        native = _evaluate(run / 'BLIND' / 'native_backend', key)
        tests['native_classification_accuracy'] = native['accuracy'] >= config['classification_accuracy_gate']
        tests['native_backend_parity'] = read_json(run / 'BLIND' / 'backend_parity_summary.json')['passed']
    gates = {name: 'PASS' if passed else 'FAIL' for name, passed in tests.items()}
    if native is None:
        gates['native_backend_parity'] = 'INDETERMINATE'
    gates['independent_dynamical_material_phase_branch'] = 'NOT-IMPLEMENTED'
    status = 'SYNTHETIC_DISCRIMINATOR_QUALIFIED' if all(tests.values()) else 'SYNTHETIC_DISCRIMINATOR_FAILED'
    report = {'run_id': run.name, 'status': status,
              'physics_status': 'NOT_YET_TESTED_ON_INDEPENDENT_DYNAMICAL_PKLSA_OBSERVATIONS',
              'python': python, 'native': native, 'gates': gates, 'sst_scale_mapping': derived_scales()}
    write_json(run / 'REVEALED' / 'reveal_report.json', report)
    write_json(run / 'REVEALED' / 'reveal_key.json', key)
    from .gate_matrix import from_evidence
    write_json(run / 'REVEALED' / 'gate_status_matrix.json', from_evidence(run, report))
    mark_revealed(run)
    return report
