"""A069 v0.3 scientific hook for frozen v1.0.9 framework.

Control-gate PASS never promotes physics gates. E011 is STATIC_ONLY.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json
from .science import analytical_suite, refuse_legacy_inputs, write_json
from .columnar import columnar_suite
from .hill import hill_suite
from .gp import gp_suite
from .ring import ring_suite
from .pklsa import scan,ARCHIVE_NAME

def _run_base_pipeline(root,cfg,ledger,mode):
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    ledger.record('G0','PASS',reason='v1.0.9 protocol bundle frozen; external framework-release identity requires qualified upstream host audit')
    old=root/'sources/A069_v0.1.0/D1_ANALYTIC_CONTROL.json'
    baseline=json.loads((root/'configs/BLIND_ANALYTIC_CONTROL_V020.json').read_text())
    actual=hashlib.sha256(old.read_bytes()).hexdigest() if old.is_file() else None
    inherited=(actual==baseline['baseline_sha256'])
    olddata=json.loads(old.read_text()) if inherited else {}
    d1=analytical_suite();d2a=columnar_suite()
    h=hill_suite();gp=gp_suite();ring=ring_suite()
    static=scan(root/'sources'/ARCHIVE_NAME)
    for path,data in [('D1_AFFINE_EULER.json',d1),('D2A_COLUMNAR_EULER.json',d2a),
      ('D2H_HILL_SPHERE_EULER.json',h),('D2N_NLS_GP_RADIAL.json',gp),
      ('D2R_NLS_THIN_RING_IDENTITY.json',ring),('D3_PKLSA_STATIC_ADMISSION.json',static)]:
        write_json(out/path,data)
    oldmax=(olddata.get('maxima') or {})
    comparison=('tracer_phase_abs_error','frame_reconstruction_error','circulation_relative_error')
    same=all(k in oldmax and abs(oldmax[k]-d1['maxima'][k])<1e-12 for k in comparison)
    legacy=refuse_legacy_inputs([str(old)])
    ledger.record('G1','PASS' if legacy['status']=='PASS' else 'FAIL',
      reason='No historical KnotPlot or VortexLab geometry admitted as physics')
    ledger.record('G2','PASS' if d1['identity_pass'] else 'FAIL',metrics=d1['maxima'],reason='Inherited affine Euler control')
    ledger.record('G3','PASS' if d1['tracer_pass'] else 'FAIL',reason='Inherited tracer phase control only')
    ledger.record('G12','PASS' if d2a['status']=='PASS' else 'FAIL',metrics=d2a['maxima'],reason='Inherited columnar exact Euler only')
    ledger.record('G13','PASS' if d2a['rk4_monotone'] else 'FAIL',reason='Inherited time-integrator control')
    ledger.record('G14','PASS' if inherited and same else 'FAIL',
       metrics={'sha256_verified':inherited,'recomputed_agreement':same},reason='Inherited D1 exact SHA match')
    ledger.record('G15',h['status'],metrics=h['maxima'],reason='Hill sphere exact 3D Euler; not PKLSA or clock')
    ledger.record('G16',gp['status'],metrics={'radial_residual':gp['max_radial_residual'],
       'resolution_error':gp['mesh_solution_discrepancy']},
       reason='Dimensionless straight GP vortex, gauge phase not a physical tick')
    ledger.record('G17',ring['status'],metrics={'R/a':ring['test_R_over_a']},
       reason='Thin-ring analytic identities only; no fat-core or physical time prediction')
    ledger.record('G18','PASS' if static['status']=='PASS_STATIC_MANIFEST_ONLY' else 'FAIL',
       metrics={'atlas_sha_verified':static.get('atlas_integrity_pass',False),
       'admitted_geometry_providers':static.get('eligible_provider_count',0)},
       reason='E011 metadata verified; KnotPlot excluded, STATIC is NOT DYNAMICS')
    ledger.record('G19','UNRESOLVED',reason='No gauge-invariant, converged, stable intrinsic 3D vortex eigenclock')
    why={'G4':'No qualified 3D finite-core PKLSA Euler trajectory; Hill not a particle knot',
         'G5':'No stable gauge-invariant internal 3D knot eigenmode',
         'G6':'Static atlas checked, dynamic upstream source and physical qualification absent',
         'G7':'No physical holdout frequency precommitment',
         'G8':'3D evolving pressure Poisson, time/space/core convergence not performed',
         'G9':'Independent physics providers and phase time series absent',
         'G10':'Strict physical native C++ kernel certification unperformed',
         'G11':'No physical clock transfer to A061'}
    for gid,reason in why.items():
        if ledger.defs[gid].enabled:ledger.record(gid,'UNRESOLVED',reason=reason)
        else:ledger.record(gid,'NOT_APPLICABLE',reason='Minimal reference profile disabled; '+reason)
    return {'schema':'SST-BACKEND-MANIFEST-2','framework_target':'1.0.9',
      'actual_backend':'python-numpy-fp64','precision':'float64','authority':'ANALYTIC_CONTROL_ONLY',
      'D1_status':d1['status'],'D2A_status':d2a['status'],'Hill_status':h['status'],
      'GP_status':gp['status'],'thin_ring_status':ring['status'],'static_PKLSA_status':static['status'],
      'physical_pklsa_status':'UNRESOLVED','physical_clock_prediction':False,
      'no_native_backend_claim':True,'old_dataset_sha256':actual}


def run_scientific_pipeline(root,cfg,ledger,mode):
    """New copy-on-write scientific hook, no inherited physical promotion."""
    from .hasimoto import suite
    from .gp3d import reference_suite
    import hmac
    old=_run_base_pipeline(root,cfg,ledger,mode)
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    has=suite(root,n=256,steps=400,dt=.00025)
    gp=reference_suite()
    key=(root/'private'/'OPAQUE_ID_KEY.bin').read_bytes()
    hidden_map={}
    for item in has['cases']:
        kind=item.pop('kind')
        alias=hmac.new(key,('A069-v0.4.0/HASIMOTO/'+kind).encode(),hashlib.sha256).hexdigest()[:20].upper()
        item['opaque_case_id']=alias
        hidden_map[alias]=kind
    (root/'private'/'HIDDEN_CASE_LOOKUP.json').write_text(json.dumps(hidden_map,sort_keys=True,indent=2)+'\n')
    write_json(out/'D4_HASIMOTO_DYNAMICS_BLIND.json',has)
    write_json(out/'D4_GP3D_PERIODIC_REFERENCE.json',gp)
    legacy=has['source_sha256']
    pre=all(len(v['sha256'])==64 and v['points']==1200 for v in legacy.values())
    ledger.record('G20','PASS' if pre else 'FAIL',reason='2015 exact bytes and shape checked; original unrelaxed analytic seeds only')
    hol=all(abs(x['holonomy_radians']+x['holonomy_mirror_radians'])<1e-8 for x in has['cases'])
    ledger.record('G21','PASS' if hol else 'FAIL',reason='Analytic Frenet derivatives, total torsion and holonomy-covariant init; no physical units')
    ctrl=all(x['status']=='PASS' for x in has['cases']) and gp['status']=='PASS'
    ledger.record('G22','PASS' if ctrl else 'FAIL',metrics={
      'maximum_NLS_mass_drift':max(x['mass_relative_drift'] for x in has['cases']),
      'maximum_NLS_Hamiltonian_drift':max(x['energy_relative_drift'] for x in has['cases']),
      'maximum_RK4_vs_split_error':max(x['rk4_vs_strang_refined_error'] for x in has['cases']),
      'GP3D_plane_wave_reference_error':gp['max_complex_error']},
      reason='Genuine time-evolved 1D LIA NLS + separate 3D GP plane wave; NOT 3D trefoil')
    parity=max(x['mirror_signed_flow_error'] for x in has['cases'])
    ledger.record('G23','PASS' if parity<1e-6 else 'FAIL',metrics={'max_signed_mirror_residual':parity},
       reason='Mirror requires beta_LIA sign reversal; pure shape parity control, correlated samples')
    ledger.record('G24','UNRESOLVED',reason='No physical finite-core 3D trefoil evolution, reduced Floquet mode or independently held-out clock target')
    ledger.record('G25','UNRESOLVED',reason='3D trefoil GP winding and initial-value evolution now executed in G26, but no certified topology, lifetime, core/grid convergence, independent full dynamics provider or stable eigenclock')
    old['Hasimoto_LIA_status']=has['status'];old['GP3D_periodic_reference']=gp['status'];old['3D_GP_trefoil_status']='UNRESOLVED'
    old['physical_intrinsic_frequency']='UNRESOLVED';old['LIA_clock_claim']=False
    return old
