"""Controlled A011 geometry adapter to the qualified v1.0.10 GateLedger.

The inherited reference and native kernels are unchanged. This is a dedicated
geometry runner, not the framework's complete blind/reveal campaign runner.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import uuid

import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = PACKAGE_ROOT.parents[3]


class AdmissionError(RuntimeError):
    """Input bytes or registered capabilities do not satisfy the frozen contract."""


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_new(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write('\n')


def bounded_path(root, relative):
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise AdmissionError('Path escapes admitted source root')
    return path


def verify_file_pins(root, pins):
    for relative, expected in pins.items():
        path = bounded_path(root, relative)
        if not path.is_file() or digest(path) != expected:
            raise AdmissionError('Pinned source drift: ' + relative)


def qualified_framework(root=PACKAGE_ROOT):
    pin = read(root / 'FRAMEWORK_SOURCE_PIN.json')
    path = (root / (root / '.sst_framework_root').read_text(encoding='utf-8').strip()).resolve()
    if path != (WORKBENCH / pin['selected_source']).resolve() or pin['status'] != 'PASS':
        raise AdmissionError('Unqualified framework locator')
    if pin['manifest_entries_verified'] != 112:
        raise AdmissionError('Framework qualification must contain 112 verified entries')
    verify_file_pins(path, pin['all_files_sha256'])
    if digest(path / 'PACKAGE_MANIFEST.json') != pin['manifest_sha256']:
        raise AdmissionError('Framework manifest pin mismatch')
    sys.path.insert(0, str(path))
    import sst_falsifier
    if sst_falsifier.__version__ != '1.0.10' or Path(sst_falsifier.__file__).parent.parent.resolve() != path:
        raise AdmissionError('Framework import resolved outside qualified source')
    return path, pin


def verify_protocol(root=PACKAGE_ROOT):
    protocol = read(root / 'preregistration/GEOMETRY_PROTOCOL.json')
    verify_file_pins(root, {r['path']: r['sha256'] for r in protocol['files']})
    from sst_falsifier.protocol import build_protocol_bundle
    actual = build_protocol_bundle(root, [r['path'] for r in protocol['files']])
    if actual['bundle_sha256'] != protocol['bundle_sha256']:
        raise AdmissionError('Geometry protocol bundle mismatch')
    return protocol


def select_native(root=PACKAGE_ROOT):
    """Require existing pinned binary; never silently rebuild or use fallback."""
    from .native_ext import core
    binary = importlib.import_module('maxwell_sst_falsifier.native_ext._native')
    pin = read(root / 'NATIVE_SOURCE_PIN.json')
    if Path(binary.__file__).resolve() != (root / pin['binary_path']).resolve() or digest(binary.__file__) != pin['binary_sha256']:
        raise AdmissionError('Native binary identity mismatch')
    if digest(root / 'cpp/native.cpp') != pin['cpp_sha256']:
        raise AdmissionError('Inherited C++ source drift')
    core._BACKEND, core._BACKEND_NAME = binary, 'cpp'
    return core.backend_info(), pin


def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s.strip()]


def verify_admission(root=PACKAGE_ROOT):
    inputs = read(root / 'ADAPTER_INPUT_PINS.json')
    verify_file_pins(root, inputs['package_files'])
    contract = read(root / 'provenance/A011_DATASET_ADMISSION.json')
    if contract['permitted_lane'] != 'GEOMETRY_AND_IMPLEMENTATION_DIAGNOSTIC_ONLY' or contract['no_scientific_promotion'] is not True:
        raise AdmissionError('Unsupported admission authority')
    verify_file_pins(WORKBENCH, contract['dataset_pins'])
    if digest(root / 'provenance/geometry_hashes.jsonl') != contract['geometry_audit_sha256']:
        raise AdmissionError('Geometry audit binding mismatch')
    e010 = read(root / 'E010_SOURCE_PIN.json')
    verify_file_pins(WORKBENCH, e010['loader_pins'])
    plan = read(root / 'config/geometry_smoke_v040.json')
    if plan['maximum_seeds'] != 3 or len(plan['seeds']) != 3 or plan['resolution_ladder'] != [64, 128]:
        raise AdmissionError('Smoke budget differs from registered tranche')
    admission = {(x['topology_id'], x['carrier_id']): x for x in rows(root / 'provenance/a011_geometry_admission.jsonl')}
    audit = {(x['topology_id'], x['carrier_id']): x for x in rows(root / 'provenance/geometry_hashes.jsonl')}
    sys.path.insert(0, str(WORKBENCH / e010['loader_root']))
    from pklsa_builder.io_geometry import load_geometry
    from pklsa_builder.hashing import geometry_sha256
    accepted = []
    for selected in plan['seeds']:
        key = (selected['topology_id'], selected['carrier_id'])
        decision, proof = admission.get(key, {}), audit.get(key, {})
        if decision.get('admit_geometry_diagnostic') is not True or proof.get('status') != 'PASS' or not proof.get('active_view'):
            raise AdmissionError('Carrier not admitted: ' + str(key))
        record = bounded_path(WORKBENCH, selected['record'])
        if digest(record) != proof['record_sha256']:
            raise AdmissionError('Carrier descriptor changed')
        descriptor = read(record)
        carrier = descriptor['carrier']
        source = bounded_path(WORKBENCH, carrier['source_path'])
        if str(source) != selected['source_path'] or digest(source) != selected['raw_sha256'] or selected['raw_sha256'] != proof['raw_expected_sha256']:
            raise AdmissionError('Source raw bytes/locator changed')
        qualification = bounded_path(WORKBENCH, decision['qualification_evidence'])
        if digest(qualification) != decision['qualification_evidence_sha256']:
            raise AdmissionError('Prior geometry qualification changed')
        prior = next(x for x in read(qualification)['carriers'] if x['carrier_id'] == key[1])
        if prior.get('literature_hard_gate_pass') is not True or any(prior['observable_status'].get(m) != 'RESOLVED' for m in contract['predicate']['required_observables']):
            raise AdmissionError('Required admitted capability unavailable')
        components = load_geometry(source, representation=carrier['representation'])
        if len(components) != 1 or not all(np.isfinite(c).all() for c in components) or len(components[0]) > plan['maximum_input_points_per_seed']:
            raise AdmissionError('Non-finite/multicomponent/oversized smoke source')
        actual = geometry_sha256(components)
        if actual != selected['geometry_sha256'] or actual != descriptor['geometry_sha256'] or actual != proof['geometry_expected_sha256']:
            raise AdmissionError('Source-native geometry digest changed')
        accepted.append((selected, np.asarray(components[0], dtype=float)))
    return contract, plan, accepted


def measure(accepted, plan):
    from .geometry import CurveRecord, geometry_metrics, resample_uniform
    from .native_ext import core, fallback
    results, parity = [], []
    for selected, points in accepted:
        levels = []
        for n in plan['resolution_ladder']:
            rec = CurveRecord(selected['carrier_id'], selected['carrier_id'], Path(selected['source_path']), points, True, 0)
            metrics, sampled = geometry_metrics(rec, n)
            numeric = [v for v in metrics.values() if isinstance(v, (float, int)) and not isinstance(v, bool)]
            if not all(np.isfinite(v) for v in numeric):
                raise ValueError('Non-finite inherited geometry metric')
            evaluation = sampled[:8] + np.asarray(plan['parity_probe_offset'])
            q = sampled + np.asarray(plan['parity_probe_offset'])
            native = np.asarray(core.biot_savart_velocity(sampled, evaluation, 1.0, 0.05, True))
            reference = np.asarray(fallback.biot_savart_velocity(sampled, evaluation, 1.0, 0.05, True))
            wr = abs(core.writhe_midpoint(sampled, True) - fallback.writhe_midpoint(sampled, True))
            distance = abs(core.min_segment_distance(sampled, q, True, True) - fallback.min_segment_distance(sampled, q, True, True))
            tolerances = plan['native_parity']
            passed = bool(np.isfinite(native).all() and np.isfinite(reference).all() and np.allclose(native, reference, rtol=tolerances['velocity_rtol'], atol=tolerances['velocity_atol']) and wr < tolerances['writhe_abs'] and distance < tolerances['distance_abs'])
            parity.append({'carrier_id': selected['carrier_id'], 'resolution': n, 'velocity_max_abs_delta': float(np.max(np.abs(native-reference))),
                           'writhe_abs_delta': float(wr), 'distance_abs_delta': float(distance), 'pass': passed})
            levels.append(metrics)
        deltas = {k: levels[1][k] - levels[0][k] for k in ['length_units', 'curvature_mean', 'writhe_midpoint']}
        results.append({'seed': selected, 'metrics_by_resolution': levels, 'resolution_deltas': deltas,
                        'convergence_authority': 'Two-level sensitivity diagnostic only; no convergence or physical certification'})
    return results, parity


def run(root=PACKAGE_ROOT, output=None):
    started = time.monotonic()
    framework, pin = qualified_framework(root)
    protocol = verify_protocol(root)
    from sst_falsifier.gates import GateLedger, GateInputsUnavailable, load_gate_plan
    from sst_falsifier.science_contract import assert_science_contract
    assert_science_contract(root / 'science_contract.json')
    native, native_pin = select_native(root)
    contract, plan, accepted = verify_admission(root)
    out = Path(output) if output else root / '1_Maxwell_SST_Kinetic_Falsifier_v0.4.0-outputs'
    # Exclusive output reservation: even another successful smoke is a new run,
    # never an invitation to overwrite the first retained result.
    out.mkdir(parents=True, exist_ok=False)
    run_id = 'A011-v0.4.0__' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    ledger = GateLedger(load_gate_plan(root / 'gate_plan.json'))
    cache = {}
    def geometry():
        cache['results'], cache['parity'] = measure(accepted, plan)
        return {'status': 'PASS', 'metrics': {'seeds': len(accepted), 'resolutions': plan['resolution_ladder'], 'finite_metrics': True},
                'authority': 'GEOMETRY_DIAGNOSTIC_ONLY', 'reason': 'Inherited geometry definitions, native units and registered smoke budget; no physical closure.'}
    def unavailable():
        raise GateInputsUnavailable('Independent physical energies, gaps, relaxation/couplings, sampled state counts, force/pressure holdouts and calibrated SI scale are not supplied by the admitted geometry atlas.')
    def parity():
        records = cache['parity']
        return {'status': 'PASS' if all(r['pass'] for r in records) else 'FAIL', 'metrics': {'comparisons': records, 'tolerances': plan['native_parity']},
                'requested_backend': 'cpp-fp64', 'actual_backend': native['version'], 'authority': 'GEOMETRY_KERNEL_ONLY',
                'reason': 'Measured despite unavailable physical prerequisites; parity never certifies physical SST.'}
    try:
        ledger.run_evaluators({
            'G0': lambda: {'status': 'PASS', 'metrics': {'framework_manifest_files': 112, 'geometry_protocol_sha256': protocol['bundle_sha256']}, 'reason': 'Qualified framework and dedicated adapter protocol verified; not the full framework blind/reveal FREEZE.'},
            'G1': lambda: {'status': 'PASS', 'metrics': {'admitted_seed_ids': [s['carrier_id'] for s, _ in accepted]}, 'reason': 'Rehashed exact admitted geometry and prior capability evidence; geometry authority only.'},
            'G2': geometry, 'G3': unavailable, 'G4': unavailable, 'G5': parity, 'G7': unavailable, 'G8': unavailable,
        })
        ledger.record('G9', 'DEFERRED', reason='No reveal requested or permitted by this geometry-only tranche.')
        if not all(x['pass'] for x in cache['parity']):
            raise RuntimeError('Native/reference parity failed; do not qualify execution')
        # Source TOCTOU check and input refresh before publishing a successful run.
        qualified_framework(root)
        verify_admission(root)
        ledger.write(out / 'GATE_LEDGER.json')
        write_new(out / 'GEOMETRY_RESULTS.json', cache['results'])
        write_new(out / 'PARITY_RESULTS.json', cache['parity'])
        write_new(out / 'SELECTED_SEEDS.json', plan)
        environment = {'python': sys.version, 'executable': sys.executable, 'numpy': np.__version__, 'platform': platform.platform(),
                       'machine': platform.machine(), 'native_backend': native, 'native_pin': native_pin,
                       'framework_root': str(framework), 'threads': 1, 'gpu_used': False,
                       'full_compiler_rebuild_performed': False, 'binary_lineage': 'Byte-identical inherited cp314 Windows binary; backend reports v0.3.1-cpp17'}
        write_new(out / 'ENVIRONMENT.json', environment)
        summary = {'schema': 'A011-CONTROLLED-MIGRATION-SMOKE-1', 'run_id': run_id, 'version': 'v0.4.0',
                   'created_utc': datetime.now(timezone.utc).isoformat(), 'duration_seconds': time.monotonic()-started,
                   'migration_gate': 'PASS_GEOMETRY_ADAPTER', 'execution_gate': 'PASS_BOUNDED_GEOMETRY_SMOKE',
                   'scientific_gate': 'UNRESOLVED_MISSING_PHYSICAL_INPUTS', 'scientific_status_promoted': False,
                   'framework_distribution_sha256': pin['distribution_sha256'], 'framework_source_tree_sha256': pin['source_tree_sha256'],
                   'protocol_bundle_sha256': protocol['bundle_sha256'], 'admission_contract_sha256': digest(root / 'provenance/A011_DATASET_ADMISSION.json'),
                   'seed_ids': [s['carrier_id'] for s, _ in accepted], 'resolution_ladder': plan['resolution_ladder'],
                   'rng_used': False, 'full_physical_campaign': False, 'reveal_performed': False,
                   'runner_kind': 'Dedicated A011 adapter using genuine v1.0.10 GateLedger; not full framework run_mode',
                   'missing_scientific_evidence': ['Calibrated physical length and SI source scale', 'Independent physical energy spectrum/gaps and relaxation/couplings', 'Independent thermodynamic sampled state counts', 'Held-out force/pressure and mechanism validation', 'Spatial/time/solver/regularization convergence beyond this two-level geometry smoke'],
                   'errors': [], 'warnings': ['Two resolutions are sensitivity diagnostics, not a convergence proof.', 'G5 raw PASS is DIAGNOSTIC_ONLY because physical prerequisites are unavailable.']}
        write_new(out / 'RUN_SUMMARY.json', summary)
        return summary
    except Exception as error:
        ledger.write(out / 'PARTIAL_GATE_LEDGER.json')
        write_new(out / 'EXECUTION_ERROR.json', {'run_id': run_id, 'type': type(error).__name__, 'error': str(error), 'execution_gate': 'FAIL_INFRASTRUCTURE_OR_NUMERICS', 'scientific_status_promoted': False})
        raise
