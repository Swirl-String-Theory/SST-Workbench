"""A068 v0.3.0: frozen SST Falsifier Framework 1.0.8-compatible science pipeline.

G2 computes real, dimensionless, unforced Euler trajectories from original native
KnotPlot XYZ. G3 physical inference FAILS CLOSED due unqualified material tube,
no relative periodic orbit, no held-out Floquet and only one geometry provider.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
from .phaseclock import demo, audit_A064
from .dynamics import refinement

EXPECTED={
 'PREFLIGHT_RESULTS.json':'eb2c099968b5ab2b33abb9ce855b0a4c77f58cd0f0137ccabdaf917146574730',
 'PREFLIGHT_WITH_A064.json':'7f6f865af5e6c459462bcc88780415a1d7257e96558cc47cae9ac6bd723f6902',
 'A064-v0.3.0_results.json':'3c1469cfddeafbc69c368a779072144119769d5ee9276a92064c803fbc6af3c1',
 'knot_3.1.txt':'98a628af4ba5d09274f0a1845c351a7a3d633a39ff833a3ae0b78e351bafdabf',
 'A064_euler_tangent_upstream.py':'a20863ba43277656dde1a638653aac5d4875d3880fef1ca930e6096de30b3621',
 'EULER_SOURCE_AUDIT.json':'95147f5e6b831ae9fd95d4f329b6ce832ce2d72bb74cc940cc12d87b38f49623',
}

def _sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def source_audit(root:Path)->dict:
 files={}
 for name,expected in EXPECTED.items():
    p=root/'data'/name; actual=_sha(p) if p.is_file() else None
    files[name]={'expected_sha256':expected,'actual_sha256':actual,'match':actual==expected}
 src=root/'experiment/euler3d.py'
 files['experiment/euler3d.py']={'expected_sha256':EXPECTED['A064_euler_tangent_upstream.py'],
                                 'actual_sha256':_sha(src) if src.is_file() else None,
                                 'match':src.is_file() and _sha(src)==EXPECTED['A064_euler_tangent_upstream.py']}
 return {'valid':all(x['match'] for x in files.values()),'files':files}

def controls(root:Path)->dict:
 a=json.loads((root/'data/PREFLIGHT_RESULTS.json').read_text());
 e=json.loads((root/'data/PREFLIGHT_WITH_A064.json').read_text());
 d=demo()
 valid= (a.get('test_type')=='UNBLINDED_METHOD_DEVELOPMENT_NOT_PHYSICAL_VALIDATION'
        and d['positive_two_shape_signals']['G3_phase_reproducibility']=='PASS_NUMERICAL_ONLY'
        and d['negative_rigid_rotation_shape_invariants']['G3_phase_reproducibility']=='SCREEN_FAIL'
        and d['negative_beating']['G3_phase_reproducibility']=='SCREEN_FAIL'
        and audit_A064(root/'data/A064-v0.3.0_results.json')['overall']=='NO_PHYSICAL_CLOCK_INFERENCE_POSSIBLE'
        and e['existing_A064_source_audit']['G0_real_PKLSA_clock_data']=='UNRESOLVED_GEOMETRY_ONLY')
 return {'valid':bool(valid),'controls':d,'source_prior':'A064 has nonstationary Galerkin eigenpairs; not a certified Kelvin frequency'}

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
 ledger.record('G0','PASS',metrics={'mode':mode},reason='Official pinned framework verified frozen protocol before invoking pipeline.')
 source=source_audit(root)
 ledger.record('G1','PASS' if source['valid'] else 'FAIL',
    metrics={'verified_hashes':sum(int(v['match']) for v in source['files'].values()),'total_hashes':len(source['files'])},
    reason='Exact native geometry, solver provenance, A064 evidence and preflight hash matches.' if source['valid'] else 'Hash mismatch or missing file; fail closed.')
 if ledger.status('G1')!='PASS':
    for k in ('G2','G3','G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(k,'G1 not PASS')
    return {'schema':'SST-BACKEND-MANIFEST-2','authority':'NO_SCIENCE_RUN_G1_FAIL','sources':source}
 method=controls(root)
 if not method['valid']:
    ledger.record('G2','FAIL',reason='Preflight controls not reproducible.')
    for k in ('G3','G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(k,'G2 not PASS')
    return {'schema':'SST-BACKEND-MANIFEST-2','authority':'INVALID_PREFLIGHT','sources':source,'method':method}
 out=root/'PKLSA_PhaseClock_v0.3.0-outputs' # canonical v1.0.8 working output
 model=refinement(root/'data/knot_3.1.txt',mode,out)
 cases=model['runs']; base=cases['primary']
 conservation=all(c['conservation_screen_pass'] for c in cases.values())
 ledger.record('G2','PASS' if conservation else 'FAIL',metrics={
   '3d_euler_evolutions':len(cases),'primary_grid':base['n'],'primary_steps':base['n_steps'],
   'primary_snapshots':base['snapshots'],'energy_drift':base['max_energy_rel_drift'],
   'helicity_drift':base['max_helicity_rel_drift'],'max_divergence':base['max_relative_divergence'],
   'max_CFL':base['max_cfl'], 'end_velocity_relative_change':base['end_velocity_relative_change']},
   reason='Numerically evolved, unforced, dealiased 3D Euler from native KnotPlot trefoil. This validates simulation screens, not physical PKLSA.' if conservation else 'Numerical dynamics conservation/CFL/nontrivial evolution screen failed.')
 if ledger.status('G2')=='PASS':
    ledger.record('G3','UNRESOLVED',metrics={
       'actual_3d_euler_evolution':True,
       'phase_from_computed_flow':True,
       'q_shape_phase':base['shape_q1_clock'].get('status'),
       'q_enstrophy_phase':base['enstrophy_clock'].get('status'),
       'material_vortex_tube_qualified':False,
       'full_field_relative_periodic_orbit_qualified':False,
       'si_core_time_calibrated':False},
       reason='Single KnotPlot seed, no certified 3D material tube/relative periodic orbit or independent dynamic PKLSA source. A synthetic/model phase cannot establish a physical clock.')
 else:ledger.skip_due_prerequisite('G3','G2 numerical dynamics failed')
 for k in ('G4','G5','G6','G7','G8'):
    if not ledger.defs[k].enabled:ledger.record(k,'NOT_APPLICABLE',reason='Disabled by official framework backend/source profile; never a physical PASS.')
    else:ledger.skip_due_prerequisite(k,reason='Scientific G3 physical qualification unresolved; available refinement diagnostics recorded separately.')
 cv=model.get('convergence',{})
 return {
  'schema':'SST-BACKEND-MANIFEST-2','version':'A068-v0.3.0',
  'actual_backend':'python-numpy-fp64','authority':'EULER_MODEL_SIMULATION_ONLY',
  'precision':'float64', 'simulation_model':'PERIODIC_DEALIASED_3D_EULER_RK4',
  'full_3d_trajectory_file':'EULER_3D_FIELDS_MODEL_ONLY.npz',
  'source_hash_ok':source['valid'],'preflight_controls_ok':method['valid'],
  'primary_run':{k:base[k] for k in ('n','dt','T','n_steps','snapshots','max_relative_divergence','max_energy_rel_drift','max_helicity_rel_drift','max_cfl','initial_enstrophy','final_enstrophy','end_velocity_relative_change')},
  'refinement_convergence':cv,
  'real_PKLSA_material_vortex':'UNRESOLVED',
  'physical_intrinsic_clock':'UNRESOLVED',
  'no_cpp_native_backend_or_gpu_certification_claim':True,
  'operator_floquet_prediction':'NOT_EXECUTED',
 }
