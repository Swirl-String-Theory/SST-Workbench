"""A062-v0.5.0: independently gate static physics and genuine short-time 3D Euler/NS."""
from pathlib import Path
from microgravity.energy_transport_v050 import run as static_run
from microgravity.dynamic_campaign_v050 import run_dynamic

def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str)->dict:
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    # Non-aborting: scientific FAIL does not suppress later gates
    old=static_run(out,mode)
    dyn=run_dynamic(out,mode)
    st={x['gate']:x for x in old['scientific_gates']}
    def add(gid,status,reason,metrics=None,backend='python-numpy-fp64',authority='REFERENCE'):
        if gid not in ledger.defs:return
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Disabled in profile');return
        ledger.record(gid,status,reason=reason,metrics=metrics or {},actual_backend=backend,authority=authority)
    add('G0','PASS','Framework 1.0.8 protocol provenance and FREEZE/PUBLISH integrity (separate from science)',
        {'framework_version':'1.0.8','candidate_status':'LOCAL_VALIDATED_CANDIDATE'})
    add('G1',st['V1']['status'],'Both E011 source raw hashes and independent providers authenticated',
        {'providers':list(dyn['providers']),'both_source_pins':True})
    add('G2',st['V2']['status'] if st['V10']['status']=='PASS' else 'FAIL',
        'Static finite Gaussian-vorticity tube source: positivity, resolution, solenoidal identity',
        {'static_V2':st['V2']['metric'],'static_V10':st['V10']['status']})
    add('G3',st['V3']['status'],'Nonzero hydrodynamic energy-equivalent E/c^2; NOT certified active/passive gravitational mass',
        {'mass_equivalent_candidate_kg':st['V3']['metric']})
    add('G4',st['V4']['status'],'SST-73 double-divergence stress has zero integrated monopole under localized or periodic closed boundaries',
        {'periodic_stress_monopoles':{k:v['periodic_stress_monopole']['source_integral'] for k,v in dyn['providers'].items()}})
    native=old['native_cpp_fp64']
    add('G5',native['status'],'Independent C++17 FP64 reproduces static Gaussian tube self-energy (not the 3D time integrator)',
        {'max_relative_error':native.get('max_relative_error')},'cpp-fp64' if native['status']=='PASS' else 'unavailable',
        'CERTIFICATION' if native['status']=='PASS' else 'NONE')
    add('G6','NOT_APPLICABLE','CPU-only profile: SYCL is not requested')
    add('G10',dyn['qualification']['status'],
        '3D periodic short-time Euler/NS screen: ABC exact solution, div=0, energy/dissipation and space/time convergence; no full particle stability',
        {'metrics':dyn['qualification']['metrics'],'limits':'short-time, Gaussian width=0.11, periodic domain, NO Floquet/long-time stability'})
    add('G11','UNRESOLVED','Long-time knot core/topology persistence, relative equilibria and Floquet spectrum were not calculated',
        {'short_time_pass':dyn['qualification']['status']=='PASS','dynamic_equilibrium_certified':False},'not_run','NONE')
    add('G7',st['V7']['status'],'Independent E011 providers reproduce normalized STATIC energy within preregistered tolerance; dynamics independently screened',
        {'provider_static_energy_relative_difference':old['provider_dimensionless_energy_relative_difference']})
    add('G8','UNRESOLVED','Energy equivalent is nonzero but physical Swirl-Clock mediator, universal passive/source coupling, free-space 1/R, SI G and mass closure have NOT been derived',
        {'gravity_derived':False,'long_term_stable_knot_proven':False,'periodic_poisson_zero_mode_guard':True},'not_available','NONE')
    return {'schema':'SST-BACKEND-MANIFEST-2',
        'python_reference':{'actual_backend':'python-numpy-fp64','authority':'REFERENCE','precision':'float64'},
        'cpp_fp64':native,
        'sycl_gpu':{'requested':False,'authority':'SCREENING_ONLY'},
        'periodic_euler_ns_screen':dyn['qualification'],
        'scientific_boundary':'Actual projected 3D periodic Euler/NS time integration has only been tested in a short-time, heavily smoothed E011 tube regime; neither stable knotted particle nor Newtonian gravity follows.',
        'limitations':['Periodized large-width Gaussian tube != dynamically stable finite-core SST particle',
          'G10 PASS is a short-time solver screen only','SST gravity, equivalence and G remain UNRESOLVED']}
