"""A075 v0.2.9 science gates under pinned, unmodified Framework v1.1.0."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any
from .science import run_suite, run_matrix, save
from .qualification import inspect_sources, parity_screen, topology_inputs, domain_gate


def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    root=Path(root).resolve()
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"/'science'
    out.mkdir(parents=True,exist_ok=True)
    ledger.record('G0','PASS',metrics={'actual_mode':mode,'framework_version':'1.1.0'},
        reason='Frozen protocol verified upstream by authentic v1.1.0 runner',authority='SOFTWARE_ONLY')
    sources=inspect_sources(root)
    save(out/'SOURCE_QUALIFICATION.json',sources)
    if not sources['passed']:
        ledger.record('G1','FAIL',metrics={'sources':sources['sources']},
                      reason='One or more real Workbench-relative source files missing or hash mismatch')
        raise RuntimeError('A075 SOURCE RESOLUTION BLOCKED: see science/SOURCE_QUALIFICATION.json')

    overrides=json.loads(os.environ.get('A075_RUNTIME_OPTIONS_JSON','{}'))
    profile=mode if mode in ('BASIC','EXTENDED','FULL') else 'PREVIEW'
    if overrides.get('ruban_study'):
        from .science import _resolve
        resolved=_resolve(profile,overrides)
        result={'gates':{'G2':{'status':'UNRESOLVED'}},'cases':{},
                'resolved_options':resolved, 'science_mode':'RUBAN_T23_SOURCE_FREE_ONLY'}
    elif overrides.get('domain_study_only'):
        from .science import _resolve
        from .domain import run_domain_study
        resolved=_resolve(profile,overrides)
        domain=run_domain_study(root,profile,out/'domain_study',resolved)
        result={'gates':{'G2':{'status':'UNRESOLVED'}},'cases':{},
                'resolved_options':resolved,'domain_study':domain}
    elif overrides.get('backends'):
        backend_debug=run_matrix(root,profile,out,overrides)
        result={'gates':{'G2':{'status':'UNRESOLVED'}},'cases':{},
                'resolved_options':overrides,'matrix':backend_debug}
    else:
        result=run_suite(root,profile,out,overrides=overrides)
    ruban=None
    if overrides.get('ruban_study'):
        from .ruban_study import run_ruban_study
        ruban=run_ruban_study(root,out/'ruban_study',result['resolved_options'])
        result['ruban_study']=ruban
    else:
        from .ruban import verify_geometry,PRIMARY
        ruban={'geometry':verify_geometry(root/'inputs/ruban_t23'/PRIMARY),
               'refinement_executed':False,'stability_certified':False,
               'physical_answer':'UNRESOLVED','requested':False}
    filament=None
    if overrides.get('ruban_filament') and overrides.get('ruban_study'):
        from .ruban_filament import run_filament_study
        filament=run_filament_study(root,out/'ruban_filament',
                n=int(overrides.get('filament_points') or 128),
                T=float(overrides.get('filament_t_end') or .04),
                dt=float(overrides.get('filament_dt') or .005))
    save(out/'RUBAN_FILAMENT_GATE_EVIDENCE.json',
         {'executed':bool(filament),'summary':filament,'scientific_status':'UNRESOLVED'})
    save(out/'RUBAN_GATE_EVIDENCE.json',ruban)
    save(out/'EXECUTION_OPTIONS.json',{'schema':'A075-EXECUTION-OPTIONS-1',
        'requested':overrides,'resolved':result['resolved_options'],
        'qualification':'EXPLORATORY_RUNTIME_CHOICES_NOT_POSTHOC_CERTIFICATION'})

    from .heartbeat import phase
    parity={}
    for kind in ('cpp','gpu'):
        phase('numerical_parity_operator',backend=kind,grid=16,
              message='Two analytic Euler RHS fields; diagnostic operator parity only')
        parity[kind]=parity_screen(root,kind)
    save(out/'BACKEND_OPERATOR_PARITY.json',{'schema':'A075-OPERATOR-PARITY-SUITE-1',
         'framework':'1.1.0','screen_only':True,'parity':parity})
    knots=topology_inputs(root)
    save(out/'KNOT_SOURCE_QUALIFICATION.json',knots)
    optional_domain=domain_gate(result.get('domain_study'))
    save(out/'PERIODIC_DOMAIN_QUALIFICATION.json',optional_domain)
    src_metrics={s['source_id']:{'path':s['path'],'exists':s['exists'],'sha256':s.get('sha256'),
                    'expected_sha256':s.get('expected_sha256'),'hash_match':s['hash_match']}
                 for s in sources['sources']}
    status=result['gates']['G2']['status']

    def parity_gate(kind):
        audit=parity[kind]
        return {'status':audit['status'],
            'metrics':{'operator':'Euler_RHS','precision':audit['precision'],
                       'threshold_relative_l2':audit['threshold_relative_l2'],
                       'cases':audit['cases'],'compiled_binary_sha256':audit.get('compiled_binary_sha256'),
                       'gpu_device':audit.get('gpu_device'),'numerical_screen_only':True},
            'reason':audit.get('reason','Two fixed Euler RHS fields checked; no full-trajectory or physical certification'),
            'actual_backend':audit.get('actual_backend'),
            'authority':'NUMERICAL_OPERATOR_DIAGNOSTIC_ONLY'}

    ledger.run_evaluators({
      'G1':lambda:{'status':'PASS','metrics':src_metrics,
          'reason':'Six source artifacts resolved with expected SHA-256, including analytic Ruban data; not an independent physical replication',
          'authority':'SOURCE_BYTE_INTEGRITY_ONLY'},
      'G2':lambda:{'status':status,'metrics':{k:v.get('diagnostics',{}) for k,v in result['cases'].items()},
          'reason':'Fixed-T Euler spatial/temporal screening only; physical convergence not established',
          'actual_backend':result['resolved_options']['backend'],'authority':'NUMERICAL_SCREENING_ONLY'},
      'G3':lambda:{'status':'UNRESOLVED','metrics':{'retention_qualified':False,'post_exit_clock_cycles':None},
          'reason':'No verified source exit, independent clock or hundred-cycle tail','authority':'NO_PHYSICAL_CLAIM'},
      'G4':lambda:{'status':'UNRESOLVED','reason':'Independent preregistered holdout not performed',
                   'authority':'NOT_EXECUTED'},
      'G5':lambda:parity_gate('cpp'),
      'G6':lambda:parity_gate('gpu'),
      'G7':lambda:{'status':knots['status'],'metrics':{'files':knots['files']},
          'reason':knots['reason'],'authority':'NO_TOPOLOGICAL_CLAIM'},
      'G10':lambda:{**optional_domain,'authority':'PERIODIC_BOX_DIAGNOSTIC_ONLY'},
      'G11':lambda:{'status':'PASS' if ruban['geometry']['geometric_fidelity_pass'] else 'FAIL',
          'metrics':ruban['geometry'],
          'reason':'Hash-pinned analytic T(2,3) with exact B0=77/500; author perturbation unknown',
          'authority':'MATHEMATICAL_GEOMETRY_ONLY'},
      'G13':lambda:{'status':'UNRESOLVED',
          'metrics':{'filament_eq9_diagnostic_executed':bool(filament),
             'filament_lifetime_not_paper_reproduced':True,
             'author_initial_random_noise_unknown':True,
             'evidence':filament},
          'reason':'Finite-difference/midpoint Ruban Eq9 is a short numerical check, not author pseudo-spectral method or t=320 longevity',
          'authority':'FILAMENT_MODEL_DIAGNOSTIC_ONLY'},
      'G12':lambda:{'status':'UNRESOLVED',
          'metrics':{'executed':bool(overrides.get('ruban_study')),
              'refinement_executed':bool(ruban.get('refinement_executed',False)),
              'spectral_diagnostics':ruban.get('levels',{}),
              'periodic_images_present':True,'true_free_space_euler':False},
          'reason':'Source-free Ruban Euler screen is not filament model, no material-tube topology or core/domain convergence',
          'authority':'DEVELOPMENT_STABILITY_DIAGNOSTIC_ONLY'},
      'G8':lambda:{'status':'UNRESOLVED',
          'metrics':{'periodic_3d_euler_run':True,'pressure_poisson_implemented':True,
                     'weak_window_flux_implemented':True,
                     'periodic_domain_sensitivity_completed':bool(result.get('domain_study',{}).get('executed')),
                     'free_space_provider':False,'spatial_continuum_converged':False,'finite_core_converged':False,
                     'source_departure_certified':False,'long_term_retention_certified':False},
          'reason':'Nonperiodic/open-boundary solution and source departure/clock/core/box convergence remain unverified',
          'authority':'PARTIAL_EULER_PROVIDER'}})
    return {'schema':'SST-BACKEND-MANIFEST-2',
        'python_reference':{'actual_backend':result['resolved_options']['backend'],
            'precision':'float64','authority':'DEVELOPMENT_ONLY'},
        'sources_resolved':sources['passed'],
        'source_hashes':{k:v['sha256'] for k,v in src_metrics.items()},
        'native_cpp_parity':parity['cpp']['status'],
        'torch_xpu_parity':parity['gpu']['status'],
        'runtime_options':result['resolved_options'],
        'physical_answer':'UNRESOLVED',
        'domain_study':result.get('domain_study',{}),
        'ruban_seed_fidelity':ruban['geometry']['geometric_fidelity_pass'],
        'ruban_euler_stability':'UNRESOLVED',
        'science_gate_file':str(out/'A075_GATES.json'),
        'status':'DEVELOPMENT_ONLY'}
