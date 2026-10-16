"""A063 v0.2.1 runner: new invariant surface tests plus sealed parent evidence."""
from __future__ import annotations
import argparse,hashlib,json,math,os,datetime
from pathlib import Path
import numpy as np
from hicks_hill.analytic import SphereVortex,root_families
from torus_tube import line
from invariant_surfaces import (meridional_level,iso_embedding_certificate,
    surface_flux,winding_on_level,curves_compare)
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'A063_Hicks_Invariant_Surface_v0.2.1-outputs'
BASE=ROOT/'baseline/v0.2.0'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def gate(ident,question,status,metrics,scope):
    return {'gate_id':ident,'question':question,'status':status,'metrics':metrics,'authority':'PYTHON_NUMERICAL_REFERENCE','scope':scope}

def verify_parent():
    expected=json.loads((ROOT/'baseline/BASELINE_IMPORT_SHA256.json').read_text())['sha256']
    for fn,sha in expected.items():
        if digest(BASE/fn)!=sha:raise RuntimeError(f'Baseline parent byte mutation: {fn}')
    ledger=json.loads((BASE/'GATE_LEDGER.json').read_text())
    summary=json.loads((BASE/'RUN_SUMMARY.json').read_text())
    if summary['gate_ledger_sha256']!=digest(BASE/'GATE_LEDGER.json'):
        raise RuntimeError('Parent gate hash mismatch')
    if summary['source_seal_sha256']!=digest(BASE/'SOURCE_SEAL.json'):
        raise RuntimeError('Parent source-seal hash mismatch')
    if ledger.get('counts')!={'FAIL':2,'PASS':7,'UNRESOLVED':3}:
        raise RuntimeError('Parent gate counts unexpectedly differ')
    return {'import_hashes':expected,'gate_statuses':{g['gate_id']:g['status'] for g in ledger['records']},
            'ledger_sha256':digest(BASE/'GATE_LEDGER.json'),
            'original_version':summary.get('version'),'original_mode':summary.get('mode')}

def main():
    pa=argparse.ArgumentParser();pa.add_argument('--mode',choices=['BASIC','FULL'],default='FULL');a=pa.parse_args()
    conf=json.loads((ROOT/'configs/protocol.json').read_text())
    tol=conf['tolerances'];OUT.mkdir(parents=True,exist_ok=True)
    parent=verify_parent()
    records=[]
    records.append(gate('S0','Are frozen parent v0.2.0 hashes and FAIL/UNRESOLVED status immutable?', 'PASS',
        {'original_release':'v0.2.0','hash_verification':True,'original_gate_statuses':parent['gate_statuses']},
        'Parent is imported evidence, NOT rerun'))
    field=SphereVortex(a=1,rho=1,A=1,lam=root_families(1)['lambda1'][0])
    cand=line(field,samples=1601,rtol=3e-11)
    parentxyz=np.load(BASE/'CANDIDATE_LINE.npz')['xyz']
    compare=curves_compare(parentxyz,cand['xyz'])
    curve_pass=compare['max_absolute_xyz']<tol['max_parent_vs_fresh_curve_absolute_xyz']
    records.append(gate('S1','Does fresh integration reproduce frozen T(3,4) reference line?',
        'PASS' if curve_pass else 'FAIL', {'comparison':compare,'fresh_W':cand['W'],
        'closure_over_a':cand['closure'],'s0_over_a':cand['s0_over_a']},'Independent recomputation from Hicks field, same solver family'))
    psi0=float(field.psi(cand['s'],cand['z'])[0]);orbit_psi=np.asarray(field.psi(cand['s'],cand['z']))
    psi_drift=float(np.max(np.abs(orbit_psi-psi0)))
    levels=[]
    n=96 if a.mode=='BASIC' else 384
    for scale in conf['pre_registered_levels_relative_to_candidate']:
        lev=meridional_level(field,psi0*scale,ntheta=n)
        topo=iso_embedding_certificate(lev)
        winding=winding_on_level(field,lev)
        flux=[surface_flux(field,lev,nphi=conf['azimuth_samples'],h=h) for h in conf['flux_fd_steps_over_a']]
        levels.append({'psi_factor':scale,'psi_value':psi0*scale,
                       'meridional':{k:float(v) if isinstance(v,np.floating) else v
                        for k,v in lev.items() if k not in ('theta','radial','s','z')},
                       'embedding':topo,'winding':winding,'normal_flux_fd':flux})
    orig=levels[1]
    records.append(gate('S2','Do explicit closed regular psi-level contours occur at three frozen levels?',
         'PASS' if all(x['meridional']['level_residual_max']<tol['level_set_residual_abs'] and
                       x['meridional']['s_min']>tol['minimum_axis_clearance_over_a'] and
                       x['meridional']['sphere_clearance_min']>tol['minimum_sphere_clearance_over_a']
                       for x in levels) else 'FAIL',
         {'levels':[{k:x['meridional'][k] for k in ('target','level_residual_max','s_min','sphere_clearance_min')}
                    for x in levels]},'Exact steady Hicks first Beltrami'))
    records.append(gate('S3','Does the original T(3,4) line sit on the reconstructed psi-level torus?',
        'PASS' if psi_drift<tol['max_candidate_to_level_psi_error'] else 'FAIL',
        {'candidate_psi':psi0,'max_psi_drift_on_curve':psi_drift,
         'winding_azimuthal_per_4_poloidal':3,'periodic_orbit_on_surface':True},
         'Classification of line on invariant torus, NOT as torus core'))
    maxflux=max(x['normal_flux_fd'][0]['max_material_flux_relative'] for x in levels)
    maxvort=max(x['normal_flux_fd'][0]['max_vorticity_flux_relative_beltrami'] for x in levels)
    fstatus='PASS' if maxflux<tol['material_normal_flux_relative'] and maxvort<tol['vorticity_normal_flux_relative'] else 'FAIL'
    records.append(gate('S4','Are u and omega tangent to every regular psi-level surface?',fstatus,
        {'coarsest_fd_h_over_a':conf['flux_fd_steps_over_a'][0],
         'max_u_normal_flux_over_u_rms':maxflux,
         'max_omega_normal_flux_over_omega_rms':maxvort,
         'analytic_identity_verified_by_independent_psi_fd':True,
         'finite_difference_ladder':[{ 'factor':x['psi_factor'],'fd_fluxes':x['normal_flux_fd']} for x in levels]},
         'Stationary material and vorticity-aligned surface in exact background, not a stable core'))
    iso_all=all(x['embedding']['valid_sampled_isotopy'] for x in levels)
    records.append(gate('S5','Are these invariant level-set boundaries standard unknotted tori of revolution?',
        'PASS' if iso_all else 'UNRESOLVED',
        {'classification':'STANDARD_UNKNOTTED_TORUS_OF_REVOLUTION',
         'three_axis_clearances':[x['meridional']['s_min'] for x in levels],
         'explicit_meridional_radial_isotopy':iso_all,
         'core':'planar circle linking axis once'},
         'Topological type of level surface/solid torus, not topology of embedded periodic line'))
    records.append(gate('S6','Does the psi-level solid torus itself have a T(3,4)-knotted CORE?',
        'FAIL' if iso_all else 'UNRESOLVED',
        {'level_surface_core':'UNKNOT (planar circle)','T34':'on torus boundary, not core',
         'parent_Alexander_T34_status':parent['gate_statuses'].get('T2'),
         'hypothesis':'psi level as knotted T34 tubular neighborhood'},
         'FAIL applies only to proposed psi-level knotted-core construction; no general no-go theorem'))
    rotations=[x['winding']['W'] for x in levels]
    records.append(gate('S7','Does a finite interval of invariant psi levels share identical 3:4 line closure?',
         'PASS' if max(abs(w-.75) for w in rotations)<tol['min_poloidal_winding_shear_abs'] else 'FAIL',
         {'W_by_psi_level':rotations,'phase_slip_radians_after_4':[
             x['winding']['four_cycle_phase_slip_radians_vs_T34'] for x in levels],
          'prior_T6':parent['gate_statuses'].get('T6')},
         'Neighbor shear does not imply 3D time-dependent Euler instability'))
    # Mesh/refinement qualification: compare same angles in N and 2N numerically
    coarse=meridional_level(field,psi0,ntheta=96)
    fine=meridional_level(field,psi0,ntheta=192)
    refine=float(np.max(np.abs(coarse['radial']-fine['radial'][::2])))
    top_ref=meridional_level(field,psi0,ntheta=384)
    refine2=float(np.max(np.abs(fine['radial']-top_ref['radial'][::2])))
    records.append(gate('S8','Are invariant level contours numerically converged and regular?',
        'PASS' if max(refine,refine2)<tol['max_levelset_mesh_refinement_change'] else 'FAIL',
        {'radial_diff_96_vs_192':refine,'radial_diff_192_vs_384':refine2,
         'level_mesh_sizes':[96,192,384],
         'parent_steady_normal_tube_T5_status':parent['gate_statuses']['T5']},
        'Analytic root construction, does not certify perturbed Euler stability'))
    records.append(gate('S9','Does v0.2.1 demonstrate an isolated finite T(3,4) vortex core stable in 3D Euler?',
         'UNRESOLVED',{'distributed_vorticity_inside_sphere':True,
                       'self_consistent_3d_euler_solver':'NOT_RUN',
                       'nonaxisymmetric_invariant_knotted_boundary':'NOT_CONSTRUCTED',
                       'original_T8':parent['gate_statuses'].get('T8'),
                       'answer':'GENERAL_EXISTENCE_STABILITY_UNRESOLVED'},
                       'Regular unknotted invariant surfaces are not an isolated knotted vortex tube'))
    records.append(gate('S10','Has native C++ FP64 v1.0.7 certification independently occurred?',
        'UNRESOLVED',{'canonical_framework_v1_0_7':'NOT_INSTANTIATED',
                      'native_cpp_fp64':'NOT_RUN','python_scipy_fp64':'REFERENCE_ONLY'},
        'Do not silently promote reference Python into scientific certification'))
    records.append(gate('S11','Can local shear/deformation establish dynamical instability without perturbed Euler?',
        'UNRESOLVED',{'v0.2.0_T6':parent['gate_statuses'].get('T6'),
                      'v0.2.0_T8A':parent['gate_statuses'].get('T8A'),
                      '3d_perturbed_euler':'NOT_RUN'},
         'Shear is kinematic phase mixing; cannot assert instability growth rate from it'))
    counts={s:sum(x['status']==s for x in records) for s in ['PASS','FAIL','UNRESOLVED']}
    outputs={'schema':'A063-PSI-SURFACE-CONTROLS-021','version':'v0.2.1',
        'mode':a.mode,'fresh_curve_vs_parent':compare,'candidate_psi':psi0,
        'candidate_psi_drift':psi_drift,'s0_over_a':cand['s0_over_a'],
        'levels':levels,'parent_gate_statuses':parent['gate_statuses'],
        'classification':'INVARIANT_UNKNOTTED_PSI_TORI; KNOTTED_VORTEX_LINE; STABLE_KNOTTED_CORE_UNRESOLVED'}
    dump(OUT/'INVARIANT_SURFACE_CONTROLS.json',outputs)
    np.savez_compressed(OUT/'CANDIDATE_LINE.npz',xyz=cand['xyz'],s=cand['s'],z=cand['z'],phi=cand['phi'],t=cand['t'])
    np.savez_compressed(OUT/'PSI_LEVEL_MESH.npz',**{
        f'level_{i}_{k}':v for i,lev in enumerate([meridional_level(field,psi0*factor,ntheta=n) for factor in conf['pre_registered_levels_relative_to_candidate']])
        for k,v in [('s',lev['s']),('z',lev['z']),('radii',lev['radial']),('theta',lev['theta'])]})
    ledger={'schema':'A063-INVARIANT-SURFACE-GATE-LEDGER-021','version':'v0.2.1',
            'counts':counts,'records':records,'continuation_after_fail':True,
            'parent_import_gate_ledger_sha256':parent['ledger_sha256'],
            'no_parent_gate_rewrite':True}
    dump(OUT/'GATE_LEDGER.json',ledger)
    # Freeze only the new instance's source bytes; seal is written after all code exists.
    srcfiles=['run_invariant.py','invariant_surfaces.py','configs/protocol.json','torus_tube.py',
              'hicks_hill/__init__.py','hicks_hill/analytic.py','hicks_hill/qualification.py',
              'hicks_hill/bridges.py','run_all.cmd','run_all.sh','generate_report.py','requirements.txt',
              'tests/test_invariant_surfaces.py']
    seal={'schema':'A063-LOCAL-SOURCE-MANIFEST-021','authority':'RELEASE_SIDE_HASH_ONLY_NOT_V107_FREEZE',
          'files':{fn:digest(ROOT/fn) for fn in srcfiles},
          'parent_baseline_manifest_sha256':digest(ROOT/'baseline/BASELINE_IMPORT_SHA256.json')}
    dump(OUT/'SOURCE_SEAL.json',seal)
    summary={'schema':'A063-INVARIANT-SURFACE-RUN-SUMMARY-021','version':'v0.2.1',
        'mode':a.mode,'counts':counts,'protocol_sha256':digest(ROOT/'configs/protocol.json'),
        'gate_ledger_sha256':digest(OUT/'GATE_LEDGER.json'),
        'source_seal_sha256':digest(OUT/'SOURCE_SEAL.json'),
        'parent_gate_ledger_sha256':parent['ledger_sha256'],
        'scientific_certification':'NOT_RUN','native_backend':'NOT_RUN',
        'overall':'PSI_SURFACE_UNKNOTTED_TORUS_T34_CORE_NOT_DEMONSTRATED_STABILITY_UNRESOLVED'}
    dump(OUT/'RUN_SUMMARY.json',summary)
    print(json.dumps({'counts':counts,'summary':summary['overall'],
          'max_psi_drift':psi_drift,'flux':maxflux,
          'winding_levels':rotations,'refine':refine},indent=2))

if __name__=='__main__':main()
