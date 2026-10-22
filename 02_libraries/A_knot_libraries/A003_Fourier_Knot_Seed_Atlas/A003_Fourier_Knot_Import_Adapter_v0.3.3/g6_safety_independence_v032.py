#!/usr/bin/env python3
"""A003 v0.3.2 topology *interpolant* certificate, solver independence, registry proposal.

Absolute limit: a positive clearance certificate for the linear homotopy between
computed RK4 endpoint polygons does NOT certify the unknown continuous ODE path,
let alone continuum Euler. No claims are silently promoted.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np
from fourier_atlas_adapter import sha256_file
from g6_dynamic_qualification_v031 import segment_clearance, best_rigid_fit
from g6_pklsa_temporal_v030 import SOURCE_ID, carrier_rows

SCHEMA = 'sst.a003.g6-continuous-independent/1'


def polygon_interpolant_certificate(states: list[np.ndarray], *, gap: int=1, relative_contact_floor: float=1e-7):
    """Valid sufficient topological non-contact condition for piecewise-LINEAR vertex homotopy.

    For edge pair (i,j) at snapshot k, every point on each edge moves <= max of
    endpoint vertex displacements during linear interpolation. Thus distance of
    disjoint edges during the interpolation is >= minimum segment distance at k
    minus 2*global_max_vertex_displacement. Positive lower bound on every
    interval implies an embedded polygonal homotopy, if initial polygon embedded.
    This bound says NOTHING rigorous about unobserved true ODE trajectories.
    """
    if len(states)<2:raise ValueError('at least two snapshots required')
    n=len(states[0]); checks=[];all_ok=True;contact=False
    for k,(a,b) in enumerate(zip(states,states[1:])):
        a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
        if a.shape!=(n,3) or b.shape!=(n,3) or not (np.isfinite(a).all() and np.isfinite(b).all()):
            raise ValueError('bad trajectory state')
        ca=segment_clearance(a,skip_edges=gap);cb=segment_clearance(b,skip_edges=gap)
        displacement=float(np.max(np.linalg.norm(b-a,axis=1)))
        lower=max(0.,float(ca['min_distance'])-2*displacement)
        diameter=max(float(np.linalg.norm(np.ptp(a,axis=0))),float(np.linalg.norm(np.ptp(b,axis=0))))
        tol=relative_contact_floor*diameter
        certified=lower>tol and cb['min_distance']>tol
        observed_collision=ca['min_distance']<=tol or cb['min_distance']<=tol
        all_ok &= certified
        contact |= observed_collision
        checks.append({'interval':k,'n':n,'min_distance_at_start':ca['min_distance'],
           'min_distance_at_end':cb['min_distance'],'max_vertex_displacement':displacement,
           'interpolant_distance_lower_bound':lower,'contact_threshold':tol,
           'certified_for_linear_polygon_interpolant':bool(certified),
           'observed_endpoint_contact':bool(observed_collision)})
    return {'schema':SCHEMA,'intervals':len(checks),'status':('FAIL_OBSERVED_SEGMENT_CONTACT' if contact
        else 'PASS_INTERPOLANT_ONLY' if all_ok else 'UNRESOLVED_INTERPOLANT_BOUND'),
        'checks':checks,'all_intervals_certified_for_interpolant':bool(all_ok),
        'certifies_true_ode_path':False,'certifies_continuum_euler':False,
        'mathematical_scope':'piecewise-linear vertex homotopy between RK4 step endpoints; sufficient lower-bound only'}


def dop853_independent_integrator(rhs,initial,final_time,reference,*,rtol=1e-9,atol=1e-11):
    """Independent SciPy DOP853 time integration using the same independently pinned RHS.
    Different integration algorithm, NOT an independent physical field model or dataset.
    """
    from scipy.integrate import solve_ivp
    x=np.asarray(initial,dtype=float); ref=np.asarray(reference,dtype=float)
    if x.shape!=ref.shape or not math.isfinite(final_time) or final_time<=0:raise ValueError('invalid integration data')
    def f(t,z):return np.asarray(rhs(z.reshape(x.shape)),dtype=float).ravel()
    solve=solve_ivp(f,(0.,final_time),x.ravel(),method='DOP853',rtol=rtol,atol=atol)
    if not solve.success or not np.isfinite(solve.y[:,-1]).all():
        return {'status':'UNRESOLVED_SOLVER','reason':solve.message}
    end=solve.y[:,-1].reshape(x.shape)
    rms=float(np.sqrt(np.mean(np.sum((end-ref)**2,axis=1))))
    diameter=float(np.linalg.norm(np.ptp(x,axis=0)))
    threshold=1e-4*diameter
    return {'status':'PASS_DIAGNOSTIC_ONLY' if rms<threshold else 'FAIL_SOLVER_DISAGREEMENT',
      'method':'scipy.integrate.solve_ivp/DOP853 independent from RK4, same C005 RHS',
      'relative_tolerance':rtol,'absolute_tolerance':atol,'rhs_evaluations':int(solve.nfev),
      'rms_lab_difference':rms,'rms_nonrigid_difference':best_rigid_fit(ref,end)['rms_nonrigid_deformation'],
      'threshold_rms':threshold,'independent_numerical_solver':True,
      'independent_physical_provider':False}


def e010_candidate_contract(atlas,registry,workbench,e010,out):
    """Generate a reviewable copy of E010 source contract, never mutate frozen E010."""
    if workbench is None or e010 is None:
        return {'status':'UNRESOLVED','reason':'Workbench and E010 unavailable'}
    root=Path(e010); contract_src=root/'configs'/'source_contract_production_v2.json'
    if not contract_src.is_file():return {'status':'UNRESOLVED','reason':'E010 production source contract missing'}
    contract=json.loads(contract_src.read_text('utf-8'))
    matches=[s for s in contract.get('sources',[]) if s.get('source_id')==SOURCE_ID]
    atlas=Path(atlas).resolve(); wb=Path(workbench).resolve()
    try:relative=atlas.relative_to(wb).as_posix()
    except ValueError:raise ValueError('atlas outside Workbench')
    spec={'source_id':SOURCE_ID,'kind':'geometry_atlas','role':'generated_analytic_geometry_seed',
      'canonical_paths':[relative],'legacy_globs':[],'provider_group':'a003_analytic_seed_atlas',
      'method_group':'a003_fourier_torus','admit_geometry':True,'required':False,
      'extension_note':'Eight SHA-256-pinned analytic F3/F4 carriers; not empirical independent sources'}
    if len(matches)>1:raise RuntimeError('duplicate canonical E010 source ids')
    proposed=json.loads(json.dumps(contract))
    if not matches:proposed['sources'].append(spec)
    else:
        if matches[0].get('canonical_paths')!=[relative] or matches[0].get('provider_group')!=spec['provider_group']:
            raise RuntimeError('existing E010 entry conflicts with frozen A003 source identity')
    dst=Path(out)/'G6P8_E010_PROPOSED_SOURCE_CONTRACT.json'
    dst.write_text(json.dumps(proposed,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    rows=carrier_rows(atlas,registry)
    index={'schema':'sst.a003.e010-persistent-carrier-proposal/1',
       'proposed_catalog_path':'10_docs/registry/extensions/a003_v0.3.2_carriers.json',
       'source_id':SOURCE_ID,'source_contract_source_sha256':sha256_file(contract_src),
       'source_contract_candidate_sha256':sha256_file(dst),
       'carrier_count':len(rows),'independent_empirical_carrier_count':0,
       'carriers':rows,'authority':'PROPOSAL_ONLY_NOT_CANONICAL','e010_v031_manifest_must_not_be_mutated':True}
    idx=Path(out)/'G6P8_E010_CARRIER_INDEX_PROPOSAL.json'
    idx.write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Reading an E010 v0.3.1 contract does not prove persistent registration.
    return {'status':'UNRESOLVED','proposal_status':'PREPARED_AND_HASHED',
      'native_source_contract_already_contains_a003':bool(matches),
      'candidate_contract_sha256':sha256_file(dst),'candidate_index_sha256':sha256_file(idx),
      'e010_canonical_modified':False,
      'required_next_action':'E010 versioned registry release + native source/asset readback + source-manifest verification'}


def persistent_registry_readback(wb,e010,atlas,registry):
    """Fail-closed audit of externally published registry. It does not install/write anything."""
    if wb is None or e010 is None:return {'status':'UNRESOLVED','reason':'no E010/Workbench'}
    source=Path(e010)/'configs'/'source_contract_production_v2.json'
    target=Path(wb)/'10_docs'/'registry'/'extensions'/'a003_v0.3.2_carriers.json'
    if not (source.is_file() and target.is_file()):
        return {'status':'UNRESOLVED','reason':'no E010 production registration and persistent carrier index',
                'expected_index':str(target)}
    contract=json.loads(source.read_text('utf-8'))
    matches=[x for x in contract.get('sources',[]) if x.get('source_id')==SOURCE_ID]
    if len(matches)!=1:return {'status':'UNRESOLVED','reason':'canonical E010 source contract lacks exactly one A003 entry'}
    idx=json.loads(target.read_text('utf-8'))
    expected=carrier_rows(atlas,registry)
    # Ignore paths in comparison? No: raw source paths must be exact.
    if idx.get('source_id')!=SOURCE_ID or idx.get('carriers')!=expected or idx.get('carrier_count')!=8:
        return {'status':'FAIL','reason':'persistent source index does not match hashed A003 source geometry'}
    if matches[0].get('provider_group')!='a003_analytic_seed_atlas':
        return {'status':'FAIL','reason':'E010 source group wrong'}
    # v0.3.1 source manifest cannot be treated as re-frozen after editing.
    return {'status':'UNRESOLVED','reason':'persistent index exists but versioned E010 canonical freeze/manifest and native registered-carrier API not attested',
            'source_contract_sha256':sha256_file(source),'persistent_index_sha256':sha256_file(target)}


def euler_closure_audit(source, epsilon, source_status):
    """Requirements audit: no surrogate FFT/filament test can pass a continuum Euler gate."""
    return {'schema':'sst.a003.g6-euler-closure-audit/1','status':'UNRESOLVED',
      'existing_operator':source.get('source') if isinstance(source,dict) else None,
      'existing_model':'regularized filament Biot-Savart RHS / moving centerline',
      'checks':{
        'spatial_divergence_of_regularized_velocity':'available kernel-level diagnostic only',
        'continuum_euler_momentum_residual':'NOT_COMPUTED',
        'pressure_poisson_source_and_boundary_conditions':'NOT_IMPLEMENTED',
        'consistent_euler_initial_vorticity_field':'NOT_IMPLEMENTED',
        'finite_core_profile_physically_calibrated':'NOT_ESTABLISHED',
        'flow_map_transport_of_3d_vorticity':'NOT_COMPUTED',
        'independent_3d_euler_solver_comparison':'NOT_AVAILABLE',
        'periodic_vs_unbounded_domain_consistency':'NOT_ESTABLISHED',
        'time_and_length_unit_calibration':'NOT_ESTABLISHED'},
      'epsilon_atlas_units':epsilon,'source_status':source_status,
      'gate':'G6P9','gate_result':'UNRESOLVED',
      'reason':'A centerline RK4 filament law does not solve inviscid 3D Euler with pressure-Poisson closure',
      'required_new_upstream_production':'A separately versioned Euler/GPE solver with defined domain, core field, pressure or wavefunction, PDE residual, convergence and independent reference'}
