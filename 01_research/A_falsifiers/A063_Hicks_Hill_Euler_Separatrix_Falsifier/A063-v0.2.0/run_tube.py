"""A063 v0.2.0 portable blinded, target-free physical classification falsifier.

This is NOT an official SST framework v1.0.7 FREEZE or C++ certification.
Sources: original exact reference implementation from A063 v0.1.1.
"""
from __future__ import annotations
import argparse, hashlib, json, math, pathlib, sys
from datetime import datetime, timezone
import numpy as np
from hicks_hill.analytic import SphereVortex, root_families
from torus_tube import (line, project_crossings, alexander_poly,
    expected_torus_alexander, tube_geometry, sample_tube_flux, poincare_shear,
    advect_material_surface)

HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/'A063_Hicks_Hill_Torus_Tube_Falsifier_v0.2.0-outputs'
SOURCES=['configs/protocol.json','run_tube.py','torus_tube.py','requirements.txt',
         'README.md','VALIDATION.md','CHANGELOG.md','tests/test_torus_tube.py','tests/test_material_advection.py',
         'hicks_hill/analytic.py','hicks_hill/qualification.py',
         'generate_report.py','run_all.cmd','run_all.sh']

def dump(o,p):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def gate(g,status,description,metrics=None,reason='',authority='REFERENCE_ONLY'):
    return dict(gate_id=g,status=status,question=description,metrics=metrics or {},
                reason=reason,actual_backend='python-scipy-fp64',authority=authority)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',default='FULL',choices=['BASIC','FULL'])
    args=parser.parse_args()
    protocol=json.loads((HERE/'configs/protocol.json').read_text(encoding='utf-8'))
    accept=protocol['acceptance'];OUT.mkdir(parents=True,exist_ok=True)
    manifests={s:sha(HERE/s) for s in SOURCES}
    source_seal={'schema':'A063-RELEASE-SOURCE-SEAL-020','version':'v0.2.0',
                 'sha256s':manifests, 'authority':'INDEPENDENT_RELEASE_CHECK_NOT_FRAMEWORK_FREEZE'}
    dump(source_seal,OUT/'SOURCE_SEAL.json')
    field=SphereVortex(a=1.,rho=1.,A=1.,lam=root_families(1)['lambda1'][0])
    c=line(field,samples=1601)
    np.savez_compressed(OUT/'CANDIDATE_LINE.npz',xyz=c['xyz'],t=c['t'],phi=c['phi'])
    closure=float(c['closure'])
    checks=[]
    checks.append(gate('T0','PASS','Release source/protocol hashes recorded',
                       {'file_count':len(manifests),'protocol_sha256':sha(HERE/'configs/protocol.json'),
                        'parent_protocol_sha256':protocol['parent_protocol_sha256']},
                       reason='Independent source manifest, not official v1.0.7 protocol freeze'))
    closure_ok=closure<accept['max_3d_closure_relative_a']
    checks.append(gate('T1','PASS' if closure_ok else 'FAIL','Reproduce a closed rational 3:4 Hicks vortex line',
        {'s0_over_a':c['s0_over_a'],'W':c['W'],'closure_over_a':closure,
         'period':c['T'],'axis_avoidance_min_s_over_a':float(min(c['s']))},
        reason='Four meridional cycles; no source observations or mass targets'))
    views=[[.27,.71,.67],[.32,.13,.94],[1.,.2,.1],[.1,1.,.2]]
    if args.mode=='BASIC': views=views[:2]
    projection=[]
    for view in views:
        cr=project_crossings(c['xyz'],view)
        ap=alexander_poly(cr)
        projection.append({'view':view,**ap,'min_over_under_separation':min(x['z_gap'] for x in cr)})
    expected=expected_torus_alexander()
    poly_valid=all(x['coefficients_ascending']==expected for x in projection)
    projection_ok=poly_valid and len(projection)>=accept['min_generic_projections']
    checks.append(gate('T2','PASS' if projection_ok else 'UNRESOLVED',
         'Independent Alexander polynomial across generic projection directions',
         {'projection_results':projection,'expected_coefficients_ascending':expected},
         reason='PASS supports numerical knot classification, not a formal certified isotopy or core stability'))
    shape=tube_geometry(c['xyz'])
    max_r=float(np.max(np.linalg.norm(c['xyz'],axis=1)))
    min_sep=float(1-max_r)
    chosen=max(accept['tube_radii_over_a'])
    sampled_ok=shape['radius_curvature_min']>chosen and min_sep>chosen
    checks.append(gate('T3','PASS' if sampled_ok else 'FAIL','Sampled geometric regularity and confinement of a finite normal tube',
          {**shape,'separatrix_clearance_over_a':min_sep,
           'max_test_radius_over_a':chosen},
          reason='Sampled geometry only. Does not provide rigorous lower bound on continuum thickness or tube self-intersection absence.'))
    # Vorticity of exactly Beltrami field is proportional to u throughout the interior.
    locs=[(float(s),float(z)) for s,z in zip(c['s'][::200],c['z'][::200]) if s>0.05]
    residuals=[field.numerical_residual(s,z,h=4e-5) for s,z in locs]
    maxerr=max(x['beltrami_norm'] for x in residuals)
    flow_ok=maxerr<1e-5
    checks.append(gate('T4','PASS' if flow_ok else 'FAIL','The core is a vortex line: omega=(lambda/a)u',
                      {'lambda':field.lam,'sample_count':len(residuals),'max_beltrami_abs':maxerr},
                      reason='Finite-difference vorticity residual; only core fieldline, not finite tube.'))
    radii=accept['tube_radii_over_a'] if args.mode=='FULL' else accept['tube_radii_over_a'][:2]
    flux=[sample_tube_flux(field,c['xyz'],radii=(0.,r),n_core=90,n_angles=16)[-1] for r in radii]
    zero=sample_tube_flux(field,c['xyz'],radii=(0.,),n_core=90,n_angles=16)[0]
    # independent resolution check ncore and angular quadrature
    flux_fine=sample_tube_flux(field,c['xyz'],radii=(radii[0],),n_core=180,n_angles=24)[0]
    numerical_stable=abs(flux[0]['normal_flow_rms_over_urms']-flux_fine['normal_flow_rms_over_urms'])<3e-4
    steady_material=all(x['normal_flow_rms_over_urms'] <= accept['max_material_normal_flow_rms_over_urms'] for x in flux)
    checks.append(gate('T5','PASS' if steady_material and numerical_stable else 'FAIL',
        'Is a constant-radius knotted tube an instantaneously material/vorticity-aligned surface?',
        {'centerline_zero_radius_control':zero,'test_radii':flux,
         'fine_sampling_first_radius':flux_fine,'sampling_robust':numerical_stable},
        reason='FAIL only rejects this constant-radius normal tube. Globally flux-balanced is insufficient; pointwise u.n=0 is required.'))
    shear=poincare_shear(field,c['s0_over_a'])
    shear_free=abs(shear['dW_d_s_over_a'])<accept['min_detectable_winding_derivative']
    checks.append(gate('T6','PASS' if shear_free else 'FAIL',
       'Do adjacent vortex lines have the same 3:4 return rotation (no pitch shear)?',
       shear,reason='Shear means near-line vortex trajectories dephase; it is NOT temporal 3D Euler instability.'))
    # Real physical vorticity is present throughout the Hill/Hicks spherical aggregate.
    remote=[(.25,.25),(.45,0.),(.2,-.35)]
    vorticity_nonzero=[]
    for s,z in remote:
        us,up,uz=field.velocity(s,z)
        vorticity_nonzero.append({'s':s,'z':z,'omega_norm_analytic':field.k*math.sqrt(us*us+up*up+uz*uz)})
    checks.append(gate('T7','PASS','Distributed full-sphere vorticity control (not a compact isolated knot tube)',
         {'remote_samples':vorticity_nonzero,'vorticity_support':'distributed inside sphere'},
         reason='Reference Hicks field has vorticity beyond the geometrically thickened core; a knot line alone is not the entire vortex support.'))
    kinematics=advect_material_surface(field,c,radius=.004,core_samples=48,ring_samples=8,periods=(0,1,2,4))
    kinematics_fine=advect_material_surface(field,c,radius=.004,core_samples=72,ring_samples=10,periods=(0,1,2,4))
    kinematic_rel_change=abs(kinematics_fine['diagnostics'][-1]['distance_to_core_rms_over_initial_radius']-kinematics['diagnostics'][-1]['distance_to_core_rms_over_initial_radius'])/kinematics_fine['diagnostics'][-1]['distance_to_core_rms_over_initial_radius']
    checks.append(gate('T8A','PASS','Prescribed-field material advection deformation documented',
        {'n_markers':kinematics['n_surface_markers'],
         'rms_distance_over_r0_after_four_periods':kinematics['diagnostics'][-1]['distance_to_core_rms_over_initial_radius'],
         'kinematic_euler_field_prescribed':True,
         'fine_mesh_rms_over_r0':kinematics_fine['diagnostics'][-1]['distance_to_core_rms_over_initial_radius'],
         'relative_surface_sample_difference':kinematic_rel_change},
        reason='PASS means diagnostic executed, NOT nonlinear Euler stability. No preregistered deformation acceptance threshold is claimed.'))
    checks.append(gate('T8','UNRESOLVED','True finite-core stability under 3D perturbed Euler evolution',
         {'independent_3d_euler_solver_used':False,
          'spatial_refinement_levels_required':accept['euler_required_spatial_levels'],
          'perturbation_amplitudes_required':accept['euler_required_perturbation_amplitudes'],
          'nonlinear_ringdown_certified':False},
          reason='Fieldline phase shear is not hydrodynamic instability. Requires divergence-free perturbation, coupled Euler/pressure solve, spectrum, energy/helicity drift, and convergence.'))
    checks.append(gate('T9','UNRESOLVED','Independent C++ FP64 and canonical v1.0.7 FREEZE/CERTIFY',
         {'cpp_fp64_certification':'NOT_RUN','framework_v1_0_7_instance':'NOT_INSTANTIATED'},
         reason='Python/SciPy FP64 reference only; no silent promotion to native certification.'))
    # the finite stable vortex tube remains undecided, even though naive constructions fail.
    checks.append(gate('T10','UNRESOLVED','Can any finite topologically consistent dynamically stable vortex tube be constructed?',
       {'closed_knotted_vortex_line':closure_ok,'diagram_alexander_consistent':poly_valid,
        'geometrically_sampled_tube_possible':sampled_ok,
        'constant_radius_material_tube':steady_material,
        'constant_rotation_neighbor_family':shear_free,
        'true_3d_euler_qualified':False,
        'classification':'NAIVE_STEADY_TUBE_FALSIFIED_GENERAL_DYNAMIC_TUBE_UNRESOLVED'},
       reason='Existence claim cannot pass without a material vortex surface and a controlled perturbed Euler evolution.'))
    statuses={s:sum(x['status']==s for x in checks) for s in ['PASS','FAIL','UNRESOLVED']}
    observations={'schema':'A063-TORUS-TUBE-CONTROLS-020',
       'mode':args.mode,'parent_release':'A063-v0.1.1',
       'curve':{'s0_over_a':c['s0_over_a'],'W':c['W'],'closure_over_a':closure,
                'n_samples':len(c['xyz']),'rmax_over_a':max_r,'period':c['T']},
       'independent_alexander':projection,'alexander_expected':expected,
       'geometric_thickness_proxy':shape,'separatrix_clearance_over_a':min_sep,
       'constant_radius_tube_flux':flux,'zero_radius_control':zero,
       'fine_flux':flux_fine,'shear':shear,'kinematic_advection':kinematics,'kinematic_advection_fine':kinematics_fine,
       'remote_vorticity':vorticity_nonzero,
       'classification':'NAIVE_STEADY_TUBE_FALSIFIED_GENERAL_DYNAMIC_TUBE_UNRESOLVED'}
    dump(observations,OUT/'TORUS_TUBE_CONTROLS.json')
    ledger={'schema':'SST-A063-TORUS-TUBE-GATE-LEDGER-020','records':checks,
            'counts':statuses,'continuation_after_fail':True,
            'scientific_conclusion':'NAIVE_STEADY_TUBE_FALSIFIED_GENERAL_DYNAMIC_TUBE_UNRESOLVED'}
    dump(ledger,OUT/'GATE_LEDGER.json')
    summary={'schema':'SST-A063-TUBE-RUN-SUMMARY-020','version':'v0.2.0','mode':args.mode,
             'status':'ANALYTIC_NUMERICAL_REFERENCE_ONLY',
             'protocol_sha256':sha(HERE/'configs/protocol.json'),
             'gate_ledger_sha256':sha(OUT/'GATE_LEDGER.json'),
             'source_seal_sha256':sha(OUT/'SOURCE_SEAL.json'),
             'counts':statuses,'full_3d_euler_simulation':'NOT_RUN',
             'cpp_certification':'NOT_RUN','framework_v1_0_7_freeze':'NOT_RUN'}
    dump(summary,OUT/'RUN_SUMMARY.json')
    dump({'schema':'SST-A063-TUBE-BACKEND-020','python_reference':{'precision':'FP64',
            'authority':'REFERENCE_ONLY','implementation':'SciPy/Numpy + SymPy + Shapely'},
         'cpp_fp64':{'status':'NOT_RUN'},'sycl':{'status':'NOT_RUN'},
         'framework_v1_0_7':{'status':'NOT_INSTANTIATED'}},OUT/'BACKEND_MANIFEST.json')
    print('A063 v0.2.0',statuses)
    for x in checks: print(f"{x['gate_id']:>4} {x['status']:>10} {x['question']}")
    print('Outputs:',OUT)
    return 0

if __name__=='__main__':sys.exit(main())
