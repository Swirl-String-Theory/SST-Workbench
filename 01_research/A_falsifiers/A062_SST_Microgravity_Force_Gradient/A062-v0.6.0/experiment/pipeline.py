"""A062-v0.6.0: static E011, nonlinear Euler/NS and conditional free-space scalar field.

Failure does NOT abort later independent science gates. The gravitational
field is a POSTULATE screen (unit K=1), not a physical derivation of G.
"""
from pathlib import Path
from microgravity.energy_transport_v050 import run as static_run
from microgravity.dynamic_campaign_v050 import run_dynamic
from microgravity.gravity_closure_v060 import run_gravity

def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str)->dict:
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    old=static_run(out,mode)
    dyn=run_dynamic(out,mode)
    grav=run_gravity(out,mode)
    st={x['gate']:x for x in old['scientific_gates']}
    vs={x['gate']:x for x in grav['gates']}
    def add(gid,status,reason,metrics=None,backend='python-numpy-fp64',authority='REFERENCE'):
        if gid not in ledger.defs:return
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Disabled in profile');return
        ledger.record(gid,status,reason=reason,metrics=metrics or {},actual_backend=backend,authority=authority)
    add('G0','PASS','Framework v1.0.8 protocol, FREEZE and instance provenance; original framework included unchanged',
        {'framework_version':'1.0.8','framework_release_status':'LOCAL_VALIDATED_CANDIDATE'})
    add('G1',st['V1']['status'],'Both E011 source SHA-256 and upstream independent providers registered',
        {'providers':list(dyn['providers'])})
    add('G2',st['V2']['status'] if st['V10']['status']=='PASS' else 'FAIL','Static finite smooth Gaussian tube has finite energy and solenoidal vorticity',
        {'static':st['V2']['metric']})
    add('G3',st['V3']['status'],'Positive kinetic E/c^2 in specified scale hypothesis; not established gravitational charge',
        {'candidate_mass_kg':st['V3']['metric']})
    add('G4','FAIL','SST-73 free-space stress double divergence has zero monopole under decay assumptions (physical model route falsified)',
        {'periodic_source_zero':{k:v['periodic_stress_monopole']['source_integral'] for k,v in dyn['providers'].items()}})
    native=old['native_cpp_fp64']
    add('G5',native['status'],'C++17 FP64 agrees with Python for static Gaussian tube energy',
        {'max_relative_error':native.get('max_relative_error')},'cpp-fp64' if native['status']=='PASS' else 'unavailable',
        'CERTIFICATION' if native['status']=='PASS' else 'NONE')
    add('G6','NOT_APPLICABLE','SYCL GPU disabled in CPU profile; reserved framework gate')
    add('G7',st['V7']['status'],'Two independent E011 source providers reproduce static energy within registered 20% range',
        {'static_provider_rel_diff':old['provider_dimensionless_energy_relative_difference']})
    add('G8','UNRESOLVED','No intrinsic Swirl-Clock mediator, physical G, gravitational charge universality or Newtonian test-body force; CONDITIONAL Green success does not close this gate',
        {'full_physical_gravity_closure':False,'conditional_scalar_green':vs['V13']['status']},'not_available','NONE')
    add('G10',dyn['qualification']['status'],'Short-time 3D periodic full Euler/NS screen; exact ABC, energy/dissipation, time/space refinement',
        {'qualification':dyn['qualification'],'dynamics_ready_claim':False})
    add('G11','UNRESOLVED','No long-term topology-preserving slender E011 relative equilibrium, Kelvin/Floquet stability',{},'not_run','NONE')
    for k in ('G12','G13','G14','G15','G16','G17','G18'):
        v=vs['V'+k[1:]]
        add(k,v['status'],v['reason'],{'metric':v['metric']} if v['metric'] is not None else {},
            'python-numpy-fp64' if v['status'] in ('PASS','FAIL') else 'not_run',
            'REFERENCE' if v['status'] in ('PASS','FAIL') else 'NONE')
    vals=list(grav['native_cpp_fp64'].values())
    native_status='PASS' if vals and all(x['status']=='PASS' for x in vals) else 'UNRESOLVED' if not vals or any(x['status']=='UNRESOLVED' for x in vals) else 'FAIL'
    add('G19',native_status,'Independent C++17 kernel reproduces conditional Green potential and vector field; does NOT provide physical G',
        {'max_component_rel_error':grav['qualification']['metrics']['max_cpp_parity_rel_error']},
        'cpp-fp64' if native_status=='PASS' else 'unavailable','CERTIFICATION' if native_status=='PASS' else 'NONE')
    return {'schema':'SST-BACKEND-MANIFEST-2',
        'python_reference':{'actual_backend':'python-numpy-fp64','authority':'REFERENCE','precision':'float64'},
        'cpp_fp64':native,'cpp_gravity_green_v060':grav['native_cpp_fp64'],
        'sycl_gpu':{'requested':False,'authority':'SCREENING_ONLY'},
        'periodic_euler_ns_screen':dyn['qualification'],'conditional_free_space_gravity_screen':grav['qualification'],
        'scientific_boundary':'Conditional source lift from periodic v0.5 velocity snapshots to a separate assumed free-space scalar Poisson propagator. The 1/R2 slope is BUILT INTO that assumed propagator. Neither SST gravity nor G nor equivalence is derived.',
        'limitations':['The E011 vortex cores are heavily smoothed, periodic, short-lived solver controls',
                       'Free-space lift of periodic-cell energy is an assumption, not an isolated Euler/NS solution',
                       'G4 FAIL applies to isolated SST-73 double divergence; G14 FAIL applies only to purely algebraic local clock',
                       'G8/G11/G15/G16/G18 unresolved; no first-principles gravitational closure']}
