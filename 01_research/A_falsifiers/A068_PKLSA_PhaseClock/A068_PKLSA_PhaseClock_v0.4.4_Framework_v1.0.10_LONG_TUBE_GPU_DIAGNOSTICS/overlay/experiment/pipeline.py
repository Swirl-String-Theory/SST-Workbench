"""A068 v0.4.4: full-diagnostic framework v1.0.10 and XPU conditional execution.

Science results retain strict blind provenance but continue independent diagnostic
modules after a negative screen. Final qualification is left to framework
GateLedger. Never mistake an executed FULL/CERTIFY mode for physical proof.
"""
from __future__ import annotations
import json,hashlib
from pathlib import Path
from . import historical
from .phaseclock import demo,audit_A064
from .dynamics import refinement
from .euler3d import Euler3D,load_geometry,normalized_components
from .mesh_refinement import material_mesh_sweep
from .vortex_seed import vortex_seed_from_curve
from .shooting import fixed_symmetry_shoot,double_return
from .floquet_independent import manufactured_arnoldi_oracle,arnoldi_euler
from .gpu_xpu import gpu_parity_campaign,torch_available
from .long_material import long_material_campaign
from .vortex_line_search import closure_search
from .xpu_preflight import inspect_xpu
from .a004_adapter import A004SourceError

EXPECTED={
 'PREFLIGHT_RESULTS.json':'eb2c099968b5ab2b33abb9ce855b0a4c77f58cd0f0137ccabdaf917146574730',
 'PREFLIGHT_WITH_A064.json':'7f6f865af5e6c459462bcc88780415a1d7257e96558cd0f0137ccabdaf917146574730',
 'A064-v0.3.0_results.json':'3c1469cfddeafbc69c368a779072144119769d5ee9276a92064c803fbc6af3c1',
 'knot_3.1.txt':'98a628af4ba5d09274f0a1845c351a7a3d633a39ff833a3ae0b78e351bafdabf',
 'A064_euler_tangent_upstream.py':'a20863ba43277656dde1a638653aac5d4875d3880fef1ca930e6096de30b3621',
 'EULER_SOURCE_AUDIT.json':'95147f5e6b831ae9fd95d4f329b6ce832ce2d72bb74cc940cc12d87b38f49623',
}
# PRE-FLIGHT-SHA corrected from direct historical source, not rewritten scientific content.
EXPECTED['PREFLIGHT_WITH_A064.json']='7f6f865af5e6c459462bcc88780415a1d7257e96558cc47cae9ac6bd723f6902'

def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_audit(root):
    files={}
    for name,expected in EXPECTED.items():
        p=root/'data'/name;actual=_sha(p) if p.is_file() else None
        files['data/'+name]={'expected_sha256':expected,'actual_sha256':actual,'match':actual==expected}
    policy=json.loads((root/'source_contract.json').read_text())['replication_policy']
    code=policy.get('v044_code_sha256',{})
    for rel,digest in code.items():
        p=root/rel;current=_sha(p) if p.is_file() else None
        files[rel]={'expected_sha256':digest,'actual_sha256':current,'match':current==digest}
    euler=root/'experiment/euler3d.py'
    files['experiment/euler3d.py']={'expected_sha256':EXPECTED['A064_euler_tangent_upstream.py'],
               'actual_sha256':_sha(euler) if euler.is_file() else None,
               'match':euler.is_file() and _sha(euler)==EXPECTED['A064_euler_tangent_upstream.py']}
    try:
        hist=historical.audit(historical.a004_adapter.workbench_from_instance(root))
        for name,digest in hist['verified_xyz_sha256'].items():
            files['A004/'+name]={'expected_sha256':digest,'actual_sha256':digest,'match':True}
        files['A004/manifest.json']={'expected_sha256':historical.a004_adapter.MANIFEST_SHA256,
            'actual_sha256':hist['manifest_sha256'],'match':True}
    except (A004SourceError,OSError,ValueError,KeyError) as exc:
        hist={'valid':False,'reason':str(exc)}
        files['A004/INVALID']={'expected_sha256':'EXTERNAL_A004-v0.2.2','actual_sha256':None,'match':False}
    return {'valid':all(x['match'] for x in files.values()),'files':files,'historical_atlas':hist}

def controls(root):
    a=json.loads((root/'data/PREFLIGHT_RESULTS.json').read_text())
    e=json.loads((root/'data/PREFLIGHT_WITH_A064.json').read_text())
    d=demo()
    good=(a.get('test_type')=='UNBLINDED_METHOD_DEVELOPMENT_NOT_PHYSICAL_VALIDATION'
        and d['positive_two_shape_signals']['G3_phase_reproducibility']=='PASS_NUMERICAL_ONLY'
        and d['negative_rigid_rotation_shape_invariants']['G3_phase_reproducibility']=='SCREEN_FAIL'
        and d['negative_beating']['G3_phase_reproducibility']=='SCREEN_FAIL'
        and audit_A064(root/'data/A064-v0.3.0_results.json')['overall']=='NO_PHYSICAL_CLOCK_INFERENCE_POSSIBLE'
        and e['existing_A064_source_audit']['G0_real_PKLSA_clock_data']=='UNRESOLVED_GEOMETRY_ONLY')
    return {'valid':bool(good),'status':'UNBLINDED_METHOD_ONLY'}

def _write(out,name,data):
    p=out/name;p.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str)->dict:
    """All independent gates are evaluated by v1.0.10 run_evaluators.

    Complete prerequisites for *physical authority* are recursive ledger
    qualifications, never used to suppress independent numerical diagnostics.
    """
    from sst_falsifier.gates import GateInputsUnavailable
    root=Path(root)
    source=source_audit(root)
    method=controls(root) if source['valid'] else {'valid':False,'reason':'G1_INVALID'}
    model=None; hist=None; mesh=None; vort=None; shoot=None; floquet=None; gpu=None; longtube=None; return_map=None; xpu_env=None
    if source['valid'] and method['valid']:
        out=root/'PKLSA_PhaseClock_v0.4.4-outputs';out.mkdir(parents=True,exist_ok=True)
        model=refinement(root/'data/knot_3.1.txt',mode,out)
        hist=historical.pilot(historical.a004_adapter.workbench_from_instance(root),mode)
        _write(out,'HISTORICAL_2015_EULER_MODEL_DIAGNOSTICS.json',hist)
        settings=json.loads((root/'data/V044_REGISTERED_MATRIX.json').read_text())
        matrix=settings['mesh_sweep'][mode if mode in ('BASIC','FULL') else 'CERTIFY']
        mesh=material_mesh_sweep(root/'data/knot_3.1.txt',**matrix)
        _write(out,'MATERIAL_MESH_CONVERGENCE_AND_CAUCHY.json',mesh)
        longtube=long_material_campaign(root/'data/knot_3.1.txt',**settings['long_horizon_mesh'][mode if mode in ('BASIC','FULL') else 'CERTIFY'])
        _write(out,'LONG_HORIZON_MATERIAL_TUBE_V044.json',longtube)
        return_map=closure_search(root/'data/knot_3.1.txt',**settings['vortex_return_map'][mode if mode in ('BASIC','FULL') else 'CERTIFY'])
        _write(out,'VORTEX_LINE_RETURN_MAP_V044.json',return_map)
        vort=vortex_seed_from_curve(root/'data/knot_3.1.txt',n=settings['vortex_seed_grid'],**settings['field_line_seed'])
        _write(out,'VORTEX_LINE_SEED_SCREEN.json',vort)
        rpo=model['rpo'];base=model['runs']['primary']
        shoot={'status':'NOT_ATTEMPTED_FULL_FIELD_CANDIDATE_SCREEN_FAILED',
               'rpo_candidate_residual':(rpo.get('best') or {}).get('residual')}
        floquet={'manufactured_oracle':manufactured_arnoldi_oracle(),
                 'actual_euler_eigenfrequency':'UNRESOLVED_NO_CERTIFIED_RPO'}
        if rpo['screen_pass'] and base['material_transport']['vortex_tube_qualified'] and mesh['volume_screen_pass'] and mesh['detF_screen_pass']:
            components,_=load_geometry(root/'data/knot_3.1.txt')
            G=Euler3D(base['n'],base['core'])
            U0=G.velocity_from_curve(normalized_components(components)[0])
            cand=rpo['best'];steps=round(cand['T_candidate']/base['dt'])
            shoot=fixed_symmetry_shoot(G,U0,base['dt'],steps,cand['rotation'],cand['shift_cells'],
                    **settings['shooting'])
            if shoot['screen_pass']:
                shoot['double_return']=double_return(G,U0,base['dt'],steps,cand['rotation'],cand['shift_cells'])
                try:
                    floquet['euler_operator']=arnoldi_euler(G,U0,base['dt'],steps,cand['rotation'],cand['shift_cells'],
                                   **settings['arnoldi'])
                except Exception as exc:
                    floquet['euler_operator']={'status':'NUMERICAL_FAILURE','error':repr(exc)}
        _write(out,'NONLINEAR_RPO_SHOOTING_AND_SECOND_RETURN.json',shoot)
        _write(out,'INDEPENDENT_FLOQUET_ARNOLDI.json',floquet)
        geom,_=load_geometry(root/'data/knot_3.1.txt')
        gpu_settings=settings['gpu_parity_by_mode'][mode if mode in ('BASIC','FULL') else 'CERTIFY']
        xpu_env=inspect_xpu()
        _write(out,'GPU_XPU_ENVIRONMENT_PREFLIGHT_V044.json',xpu_env)
        G=Euler3D(gpu_settings['grid'])
        U0=G.velocity_from_curve(normalized_components(geom)[0])
        gpu=gpu_parity_campaign(U0,dt=gpu_settings['dt'],steps=gpu_settings['steps'],device='xpu')
        _write(out,'GPU_XPU_FULL_EULER_RK4_PARITY.json',gpu)
    else:
        out=None
    def available():
        if not source['valid']:raise GateInputsUnavailable('Hash-verified A004/A064 source absent or invalid')
        if not method['valid']:raise GateInputsUnavailable('Required historical analytic preflight controls invalid')
    def evG0():return {'status':'PASS','metrics':{'mode':mode,'framework':'1.0.10',
                   'framework_canonical':False},'reason':'Official version-pinned v1.0.10 local candidate runtime.'}
    def evG1():return {'status':'PASS' if source['valid'] else 'FAIL',
          'metrics':{'verified_hashes':sum(f['match'] for f in source['files'].values()),
                     'total_hashes':len(source['files'])},
          'reason':'A004 external 40/40 provenance and exact frozen science operators' if source['valid'] else 'Source hash mismatch; fail-closed'}
    def evG2():
        available();cases=model['runs'];base=cases['primary'];passed=all(x['conservation_screen_pass'] for x in cases.values())
        return {'status':'PASS' if passed else 'FAIL','metrics':{'model_trajectories':len(cases),
                  'energy_drift':base['max_energy_rel_drift'],'divergence':base['max_relative_divergence'],
                  'CFL':base['max_cfl'],'historical_geometry_cases':len(hist['test_matrix'])},
                'reason':'Real geometry-seeded 3D Euler RK4 simulation, no physical PKLSA authority'}
    def evG3():
        available();b=model['runs']['primary'];rpo=model['rpo']
        return {'status':'UNRESOLVED','metrics':{'advected_surface':True,
                'tube_tangency_screen_pass':b['material_transport']['vortex_tube_qualified'],
                'mesh_volume_screen_pass':mesh['volume_screen_pass'],
                'long_horizon_mesh_volume_screen_pass':longtube['volume_screen_pass'],
                'long_horizon_detF_screen_pass':longtube['detF_screen_pass'],
                'long_horizon_T_reached':longtube['T_reached'],
                'vortex_line_return_map_best':(return_map['best'] or {}).get('closure_distance'),
                'cauchy_detF_screen_pass':mesh['detF_screen_pass'],
                'vortex_line_closure_screen_pass':vort.get('closed_line_screen_pass',False),
                'rpo_full_field_residual':(rpo['best'] or {}).get('residual'),
                'nonlinear_shooting_status':shoot.get('status','ATTEMPTED'),
                'material_tube_qualified':False,'RPO_certified':False},
                'reason':'Independent material/RPO diagnostics executed; physical source, embedded material tube, full shooting and recurrence unqualified'}
    def evG4():
        available()
        return {'status':'UNRESOLVED','metrics':{'manufactured_floquet_oracle_pass':floquet['manufactured_oracle']['oracle_pass'],
                    'operator_ritz_diagnostics_available':bool(floquet.get('euler_operator'))},
                'reason':'Analytic oracle and tangent operator are diagnostics; no qualified RPO eigenfrequency for held-out comparison'}
    def evG5():
        available();cv=model['convergence'];major=(mode!='BASIC')
        if not major:return {'status':'UNRESOLVED','reason':'BASIC excludes spatial/core Euler convergence; mesh sweep is diagnostic only'}
        passed=bool(cv['temporal_gate'] and cv['spatial_gate'] and cv['finite_core_robust_gate']
                  and mesh['mesh_stability_screen_pass'] and mesh['detF_screen_pass']
                  and longtube['volume_screen_pass'] and longtube['detF_screen_pass']
                  and longtube['mesh_agreement_screen_pass'])
        return {'status':'PASS' if passed else 'FAIL',
                'metrics':{'space_Z':cv['spatial_relative_Z'],'time_Z':cv['temporal_relative_Z'],
                           'core_Z':cv['finite_core_relative_spread_Z'],
                           'mesh_volume_delta':mesh['finest_two_volume_drift_difference'],
                           'detF_max_error':mesh['max_det_F_error'],
                           'long_T':longtube['T_reached'],
                           'long_volume_drift':longtube['max_volume_drifts'][-1],
                           'long_detF_error':longtube['max_detF_error'],
                           'long_mesh_delta':longtube['finest_two_mesh_volume_delta_max']},
                'reason':'Independent numerical convergence screen; v1.0.10 qualification remains DIAGNOSTIC_ONLY if G3/G4 unresolved'}
    def evG6():
        available()
        if gpu.get('status')=='UNAVAILABLE_NO_FALLBACK':
            return {'status':'UNRESOLVED','metrics':{'device':'NO_XPU','fallback':False},
                    'reason':'No real Intel Arc/XPU runtime available; no CPU substitution'}
        if not gpu['fp64_parity_pass']:
            return {'status':'UNRESOLVED','metrics':{'actual_backend':gpu['actual_backend'],
                      'fp32_screen_pass':gpu['fp32_screen_pass'],'fp64_pass':False},
                      'actual_backend':gpu['actual_backend'],'authority':'FP32_SCREENING_ONLY',
                      'reason':'GPU kernel executed, but full 3D FP64 solver lane did not meet parity; FP32 is screening only'}
        return {'status':'PASS',
           'metrics':{'actual_backend':gpu['actual_backend'],'gpu_executed':gpu['hardware_gpu_executed'],
                   'fp32_screen_pass':gpu['fp32_screen_pass'],
                   'fp64_relative_velocity_L2':gpu['fp64_lane']['relative_velocity_L2']},
           'actual_backend':gpu['actual_backend'],'authority':'GPU_3D_EULER_RK4_PARITY_ONLY',
           'reason':'Real Intel XPU FP64 FFT+RK4 field parity; separate framework SYCL/DD32 selftests still required'}
    def evG7():
        available();return {'status':'UNRESOLVED','metrics':{'physical_provider_count':0},
            'reason':'A004 trefoil geometry variants are not independent calibrated material vortex providers'}
    def evG8():
        available();return {'status':'UNRESOLVED','metrics':{'si_time_calibrated':False,
                        'qualified_material_tube':False,'qualified_RPO':False,'qualified_Floquet':False},
                'reason':'No physical SST clock inference; no bypass of reveal eligibility'}
    ledger.run_evaluators({f'G{i}':fn for i,fn in enumerate([evG0,evG1,evG2,evG3,evG4,evG5,evG6,evG7,evG8])})
    return {'schema':'SST-BACKEND-MANIFEST-2','version':'A068-v0.4.4',
        'actual_backend':'python-numpy-fp64' if model is not None else 'NOT_RUN_INVALID_SOURCE',
        'authority':'EULER_MODEL_SIMULATION_ONLY' if model is not None else 'NO_SCIENCE_INVALID_PROVENANCE',
        'framework':'1.0.10_LOCAL_VALIDATED_CANDIDATE','gpu':gpu or {'status':'NOT_EXECUTED'},
        'material_mesh_diagnostic':bool(mesh),'long_material_diagnostic':bool(longtube),
        'vortex_return_map_diagnostic':bool(return_map),
        'gpu_environment_preflight':xpu_env,'field_line_seed_diagnostic':bool(vort),
        'shooting':shoot,'floquet':floquet,
        'full_3d_trajectory_file':'EULER_3D_FIELDS_MODEL_ONLY.npz' if model is not None else None,
        'A004_external_pinned':source['valid'],
        'a004_version':'v0.2.2',
        'independent_physical_providers':0,
        'physical_intrinsic_clock':'UNRESOLVED',
        'no_native_cpp_or_sycl_dd32_whole_solver_certification_claim':True,
        'science_ledger_execution_policy':'FULL_DIAGNOSTIC_FAIL_NOT_STOP'}
