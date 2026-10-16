"""A062-v0.4.0 shared-framework adapter: preserves G0-G9 vocabulary and failed gates."""
from pathlib import Path
from microgravity.energy_transport_v040 import run

def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str)->dict:
    ledger.record('G0','PASS',metrics={'framework':'1.0.8','release_status':'LOCAL_VALIDATED_CANDIDATE'},reason='Frozen protocol integrity accepted by v1.0.8')
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    q=run(out,mode)
    st={z['gate']:z for z in q['scientific_gates']}
    def add(gid,status,reason,metrics=None,authority='REFERENCE',backend='python-numpy-fp64'):
        if gid not in ledger.defs:return
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Disabled in cpu profile');return
        ledger.record(gid,status,reason=reason,metrics={'scientific_gate':gid,**(metrics or {})},authority=authority,actual_backend=backend)
    add('G1',st['V1']['status'],st['V1']['reason'],{'two_E011_providers':True})
    add('G2','PASS' if st['V2']['status']=='PASS' and st['V10']['status']=='PASS' else 'FAIL',
        'Resolved Gaussian-vorticity loop: finite positive kinetic energy, resolution and solenoidal-source qualification (not full dynamics)',
        {'V2':st['V2']['metric'],'V10':st['V10']['status']})
    add('G3',st['V3']['status'],
        'Energy-equivalent Q_E=E/c² nonzero for finite tube. Kinematic candidate only: not proven passive or gravitational mass',
        {'mass_equivalent_kg':st['V3']['metric']})
    add('G4',st['V4']['status'],st['V4']['reason'],{'stress_source_monopole':0.0})
    native=q['native_cpp_fp64']
    add('G5',native['status'],'Independent compiled C++17 FP64 finite Gaussian-vorticity self-energy integral',
        native,authority='CERTIFICATION' if native['status']=='PASS' else 'NONE',
        backend='cpp-fp64' if native['status']=='PASS' else 'unavailable')
    add('G6','UNRESOLVED','No fully resolved nonlinear Euler/NS time evolution or dynamic vortex stability qualification',
        {'enstrophy_dissipation_screen':'conditional_formula_only'},authority='NONE',backend='not_run')
    add('G7',st['V7']['status'],st['V7']['reason'],
        {'energy_provider_relative_diff':q['provider_dimensionless_energy_relative_difference']})
    add('G8','UNRESOLVED','No self-derived long-range clock mediator, dimensional gravity coupling, equivalence, macroscopic transfer or independent Newton-G',
        {'gravity_derived':False,'energy_charge_nonzero':True},authority='NONE',backend='not_available')
    return {'schema':'SST-BACKEND-MANIFEST-2',
      'python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},
      'cpp_fp64':native,
      'sycl_gpu':{'requested':False,'authority':'SCREENING_ONLY'},
      'limitations':['E011 STATIC_READY does not imply DYNAMICS_READY','No Navier-Stokes time integration','No gravitation closure'],
      'scientific_boundary':'Gauss vortex-tube energy is genuinely nonzero; identification with universal gravitational source and coupling is an untested constitutive hypothesis; stress double-divergence is zero-monopole under localization'}
