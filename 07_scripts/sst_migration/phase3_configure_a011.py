"""Create explicit A011 v0.4.0 geometry contracts before any smoke measurements."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha
from phase3_prepare import create_json as write_unique, PHASE2, FAMILY

DEST = FAMILY / 'A011-v0.4.0'


def create_json(path, value):
    if path.exists():
        if read(path) != value:
            raise RuntimeError('Refusing to replace a different preregistered input: ' + str(path))
        return
    write_unique(path, value)


def main():
    admission = [json.loads(s) for s in (DEST / 'provenance/a011_geometry_admission.jsonl').read_text().splitlines()]
    eligible = {(x['topology_id'], x['carrier_id']) for x in admission if x['admit_geometry_diagnostic']}
    geometry = [json.loads(s) for s in (DEST / 'provenance/geometry_hashes.jsonl').read_text().splitlines()]
    selected = []
    for topology in ['0_1', '3_1', '4_1']:
        options = [r for r in geometry if r['topology_id'] == topology and (topology, r['carrier_id']) in eligible
                   and r['status'] == 'PASS' and r['active_view'] and len(r['component_shapes']) == 1
                   and r['component_shapes'][0][0] <= 4096 and str(r['source_path']).endswith('.vect')]
        row = min(options, key=lambda r: r['carrier_id'])
        source = Path(row['source_path']).resolve()
        selected.append({'topology_id': topology, 'carrier_id': row['carrier_id'], 'source_path': str(source), 'record': row['record'],
                         'raw_sha256': row['raw_actual_sha256'], 'geometry_sha256': row['geometry_actual_sha256']})
    contract = read(DEST / 'provenance/A011_DATASET_ADMISSION.json')
    plan = {'schema': 'A011-CONTROLLED-GEOMETRY-SMOKE-1', 'selection_policy': 'Fixed representative unknot/trefoil/figure-eight topology coverage, then lexicographically first admitted single-component VECT carrier with <=4096 source points; no metric/target optimization',
            'seeds': selected, 'maximum_seeds': 3, 'maximum_input_points_per_seed': 4096, 'resolution_ladder': [64, 128],
            'wall_clock_timeout_seconds': 120, 'threads': 1, 'random_selection': False,
            'native_parity': {k: contract['native_parity'][k] for k in ['velocity_rtol', 'velocity_atol', 'writhe_abs', 'distance_abs']},
            'parity_probe_offset': [3.0, 0.2, 0.1], 'parity_probe_scope': 'Nondimensional kernel comparison with Gamma=1 and smoothing=0.05 in native coordinate units, no physical velocity claim',
            'convergence_claim': False, 'physical_inputs_supplied': False, 'reveal_allowed': False}
    create_json(DEST / 'config/geometry_smoke_v040.json', plan)
    create_json(DEST / 'E010_SOURCE_PIN.json', {'loader_root': '01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1',
                'loader_pins': read(PHASE2 / 'geometry_integrity.json')['loader_pins']})
    native = DEST / 'src/maxwell_sst_falsifier/native_ext/_native.cp314-win_amd64.pyd'
    parent = FAMILY / 'A011-v0.3.1'
    stamp = read(parent / 'build/maxwell_sst_native.stamp.json')
    cpp = DEST / 'cpp/native.cpp'
    stamp_hash = hashlib.sha256(str(Path('cpp') / 'native.cpp').encode() + b'\0' + cpp.read_bytes() + b'\0').hexdigest()
    if stamp_hash != stamp['hash']:
        raise RuntimeError('Inherited binary build stamp does not bind inherited C++ source')
    create_json(DEST / 'NATIVE_SOURCE_PIN.json', {'binary_path': native.relative_to(DEST).as_posix(), 'binary_sha256': sha(native),
                'cpp_sha256': sha(cpp), 'parent_build_stamp': stamp, 'parent_build_stamp_sha256': sha(parent / 'build/maxwell_sst_native.stamp.json'),
                'source_stamp_hash_verified': True, 'build_performed_in_this_tranche': False})
    inputs = ['provenance/A011_DATASET_ADMISSION.json', 'provenance/a011_geometry_admission.jsonl', 'provenance/geometry_hashes.jsonl',
              'E010_SOURCE_PIN.json', 'NATIVE_SOURCE_PIN.json', 'config/geometry_smoke_v040.json']
    create_json(DEST / 'ADAPTER_INPUT_PINS.json', {'package_files': {p: sha(DEST / p) for p in inputs}})
    gates = [
        ('G0', 'Are the qualified framework and dedicated adapter protocol byte-exact?', []),
        ('G1', 'Do all selected geometry sources satisfy exact admission and hashes?', ['G0']),
        ('G2', 'Are inherited geometry metrics finite under the fixed bounded ladder?', ['G1']),
        ('G3', 'Are independent physical discovery inputs available and qualified?', ['G2']),
        ('G4', 'Does independent physical held-out evidence confirm a mechanism?', ['G3']),
        ('G5', 'Does the inherited native geometry kernel match reference tolerances?', ['G4']),
        ('G6', 'GPU screening (disabled in this CPU geometry tranche)', ['G5']),
        ('G7', 'Is independent physical replication available?', ['G6']),
        ('G8', 'Is physical mechanism and convergence evidence available?', ['G7']),
        ('G9', 'Reveal is separate and not allowed in this geometry-only tranche', ['G8'])]
    create_json(DEST / 'gate_plan.json', {'schema': 'SST-GATE-PLAN-2', 'gates': [{'gate_id': gid, 'question': q, 'requires': deps, 'enabled': gid != 'G6'} for gid, q, deps in gates]})
    science = {'schema': 'SST-SCIENCE-CONTRACT-2',
               'research_question': 'Does the v1.0.10 adapter retain inherited A011 geometry definitions and Python/native consistency on exact admitted PKLSA inputs?',
               'objective': 'Qualify software migration and bounded geometry diagnostics while explicitly withholding physical closure.',
               'null_hypothesis': 'Adapter source admission or the inherited native/reference tolerances fail on the preregistered geometry set.',
               'alternative_hypothesis': 'Exact admitted geometry is processed with finite inherited diagnostics and existing native/reference tolerances; no physical prediction follows.',
               'assumptions': ['Input coordinate units are source-native and have no certified SI scale.', 'Closed polygon curves are resampled by the unchanged A011 reference definition.', 'Two resolutions expose sensitivity only.', 'No energy spectrum, gravity or thermodynamic state-count evidence is inferred from curves.'],
               'symbols': [{'symbol': 'p_i', 'meaning': 'Source-native polygon vertex', 'si_unit': 'Uncalibrated source coordinate unit', 'dimensions': 'L in a declared native unit'},
                           {'symbol': 'L', 'meaning': 'Resampled polygon length', 'si_unit': 'Uncalibrated source coordinate unit', 'dimensions': 'L'},
                           {'symbol': 'Wr', 'meaning': 'Inherited midpoint writhe diagnostic', 'si_unit': '1', 'dimensions': '1'}],
               'equations': [{'id': 'E1', 'purpose': 'Inherited polygon length', 'latex': r'L=\sum_i\|p_{i+1}-p_i\|', 'inputs': ['p_i'], 'outputs': ['L'], 'dimensional_check': 'Coordinate length; no SI conversion without calibration.'},
                             {'id': 'E2', 'purpose': 'Existing componentwise velocity parity criterion', 'latex': r'|v_{cpp,j}-v_{py,j}|\le 10^{-12}+10^{-11}|v_{py,j}|', 'inputs': ['v_cpp', 'v_py'], 'outputs': ['parity'], 'dimensional_check': 'Same nondimensional test-kernel convention on both implementations; no physical velocity claim.'}],
               'observables': [{'id': 'O1', 'definition': 'Unchanged A011 length, curvature and midpoint writhe diagnostics at N=64,128', 'equation_refs': ['E1'], 'unit': 'native units; writhe dimensionless'},
                               {'id': 'O2', 'definition': 'Native/reference velocity, writhe and distance deltas at unchanged v0.3.1 tolerances', 'equation_refs': ['E2'], 'unit': 'nondimensional kernel-test convention'}],
               'steps': [{'id': 'S1', 'operation': 'Rehash qualified source, protocol, exact admitted raw and parsed geometry inputs', 'formula_refs': ['E1'], 'gate': 'G1'},
                         {'id': 'S2', 'operation': 'Apply unchanged A011 resampling and geometry definitions', 'formula_refs': ['E1'], 'gate': 'G2'},
                         {'id': 'S3', 'operation': 'Compare inherited native and transparent reference kernels despite missing physical prerequisites', 'formula_refs': ['E2'], 'gate': 'G5'}],
               'falsification_criteria': [{'id': 'F1', 'criterion': 'Any source hash/capability mismatch aborts execution; no substitution.', 'conclusion_if_met': 'FAIL_INFRASTRUCTURE'},
                                         {'id': 'F2', 'criterion': 'Native parity outside original tolerances is a failed implementation smoke.', 'conclusion_if_met': 'FAIL'},
                                         {'id': 'F3', 'criterion': 'Unavailable independent physical inputs cannot support physical discovery or closure.', 'conclusion_if_met': 'NOT_RUN_PREREQUISITE'}],
               'edge_cases': ['Missing native ABI-compatible binary', 'Raw/geometry hash drift', 'Nonfinite or degenerate geometry', 'Existing output directory', 'No calibrated SI scale'],
               'predictions': ['No new physical prediction; software consistency and input-integrity diagnostics only.'],
               'provenance': ['src/maxwell_sst_falsifier/geometry.py unchanged from v0.3.1', 'tests/test_native_parity_v02.py unchanged from v0.3.1', 'provenance/PARENT_README.md']}
    create_json(DEST / 'science_contract.json', science)
    print(json.dumps({'seeds': selected, 'resolutions': [64, 128]}, indent=2))


if __name__ == '__main__':
    main()
