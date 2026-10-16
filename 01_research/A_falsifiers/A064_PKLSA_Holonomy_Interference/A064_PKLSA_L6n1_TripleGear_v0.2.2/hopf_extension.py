"""A064 v0.2.2 native L6n1, native T(3,3), and published Triple Gear Hopf proxy.

All three are the L6n1/three-component Hopf link class; mechanical meshing
is not simulated. The source-native KnotPlot XYZ components are separated
by validated inter-component export jumps, not assumed index positions.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from three_core import (ROOT as PARENT_ROOT,PeriodicEulerFlow,gauss_lk,knot_determinant,determinant_multiview,
                        init_three_core,iso_scan,first_genus_one_feature,exchange_probe,
                        canonical_hash,input_hashes)
from a064.flow import file_hash
from a064.analysis import field_data,transport_audit
from euler_extension.spectral import SpectralEuler3D,evolve

ROOT=Path(__file__).resolve().parent
CASES=('L6n1_KNOTPLOT','T33_KNOTPLOT','TRIPLE_GEAR_HOPF_PROXY')
SOURCES={'L6n1_KNOTPLOT':'link_6.3.3.txt','T33_KNOTPLOT':'torus_3.3.txt'}
CLASS='geometry_initialized_periodic_3d_euler_model_no_mechanical_contact'

def split_native(path):
    coords=np.loadtxt(path,dtype=np.float64)
    if coords.ndim!=2 or coords.shape[1]!=3:raise ValueError('XYZ must be Nx3')
    ds=np.linalg.norm(np.diff(coords,axis=0),axis=1)
    med=np.median(ds)
    jumps=np.flatnonzero(ds>2.5*med)+1
    if len(jumps)!=2:raise ValueError(f'expected exactly two component jumps; got {jumps.tolist()}')
    parts=np.split(coords,jumps)
    if min(map(len,parts))<12:raise ValueError('insufficient source component resolution')
    # Closed segments must match the scale of sampled neighbor chords.
    if any(np.linalg.norm(p[0]-p[-1])>2.5*med for p in parts):
        raise ValueError('source component endpoint closure screen failed')
    return parts,{'source_file':path.name,'source_sha256':file_hash(path),'source_segments':[len(p) for p in parts],
                  'source_seam_indices':jumps.tolist(),'native_jump_median_ratio':(ds[jumps-1]/med).tolist(),
                  'component_detection':'source_gap_gt_2.5_median_and_closed_segment_screen'}

def resample_closed(p,n=160):
    p=np.asarray(p,float)
    ring=np.vstack((p,p[0]));ds=np.linalg.norm(np.diff(ring,axis=0),axis=1)
    if np.min(ds)<1e-12:raise ValueError('degenerate source segment')
    cum=np.r_[0.,np.cumsum(ds)];samples=np.linspace(0,cum[-1],n,endpoint=False)
    return np.stack([np.interp(samples,cum,ring[:,j]) for j in range(3)],axis=-1)

def published_gear_centers(n=160):
    # Schleimer & Segerman 2013 section 3, paper's maximal three-circle Hopf layout.
    # Gear teeth, swept rigid-body meshing, driving loads, and central helical rod are NOT present.
    r=.4950197;theta=-.8560281
    t=np.linspace(0.,2*np.pi,n,endpoint=False)
    curves=[]
    for k in range(3):
        a=2*np.pi*k/3
        rot=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
        local=np.stack([r+np.cos(t),np.sin(theta)*np.sin(t),np.cos(theta)*np.sin(t)],axis=-1)
        local[:,2]*=-1. # match the negative-chirality L6n1/T(3,3) source geometry for the contrast
        curves.append(local@rot.T)
    return curves,{'construction':'Schleimer_Segerman_three_Hopf_circles',
                   'circle_center_radius_r':r,'plane_theta_rad':theta,
                   'mirror_z_for_source_chirality_matching':True,
                   'model_exclusion':'NO_MECHANICAL_TEETH_NO_DRIVE_NO_FORCE_NO_HELIX_NO_PHASE_LOCK',
                   'source_url':'https://arxiv.org/abs/1304.6859'}

def geometry(case,npoints=160):
    if case not in CASES:raise ValueError('unknown case')
    if case in SOURCES:
        p=ROOT/'data/native'/SOURCES[case]
        raw,pr=split_native(p)
        curves=[resample_closed(c,npoints) for c in raw]
        if case=='L6n1_KNOTPLOT':
            # Reorient one component to share all-negative signed Gauss linking with T(3,3).
            curves[1]=curves[1][::-1].copy()
            pr['orientation_reversed_components']=[1]
        else:pr['orientation_reversed_components']=[]
    else:
        curves,pr=published_gear_centers(npoints)
        pr['orientation_reversed_components']=[]
    # Normalize *collectively* so each entire link has the same max axis half-width.
    allp=np.concatenate(curves,axis=0)
    origin=(allp.max(axis=0)+allp.min(axis=0))*0.5
    factor=2.35/np.max(np.abs(allp-origin))
    curves=[np.ascontiguousarray((c-origin)*factor) for c in curves]
    pr.update({'common_geometry_scale':float(factor),'global_origin_native':origin.tolist(),
               'coordinate_units':'ARBITRARY_PERIODIC_2PI_BOX',
               'source_class':'SOURCE_NATIVE_KNOTPLOT' if case in SOURCES else 'PUBLISHED_PARAMETRIC_PROXY'})
    return curves,pr

def audit(curves,pr,case):
    det=[determinant_multiview(c) for c in curves]
    pairs=[]
    for i,j in ((0,1),(0,2),(1,2)):
        lk=gauss_lk(curves[i],curves[j]);d=cKDTree(curves[i]).query(curves[j])[0].min()
        pairs.append({'pair':[i,j],'linking':lk,'sampled_separation':float(d)})
    status={
      'case':case,'n_components':3,'component_knot_determinant_multiview':det,
      'pairwise_gauss':pairs,'determinant_screen_pass':det==[[1]*3]*3,
      'pairwise_linking_screen_pass':all(abs(abs(p['linking'])-1)<.07 for p in pairs),
      'source_chirality_matched_screen':all(abs(p['linking']+1)<.07 for p in pairs),
      'pairwise_separation_screen_pass':all(p['sampled_separation']>.12 for p in pairs),
      'geometry_sha256':input_hashes(curves),'source_provenance':pr,
      'knot_atlas_id':'L6n1_6^3_3','link_class':'THREE_COMPONENT_HOPF_LINK_T_3_3',
      'milnor_mu123_gate':'NOT_A_FREE_INTEGER_WHEN_PAIRWISE_LINKING_NONZERO',
      'mechanical_tracked_axiom':'NOT_TESTED_GEAR_TEETH_AND_RIGID_BODY_FORCES_ABSENT',
      'physical_PKLSA_evidence':'NONE','E011_PROVIDER_GATE':'NOT_MAPPED_TO_STATIC_READY'}
    return status

def run_case(case,n=24,duration=.32,frames=13,core=.42,force=False):
    if n%2 or n<20 or frames<3 or duration<=0 or core<=0:raise ValueError('invalid grid/time/core')
    out=ROOT/'outputs'/f'{case}_N{n}'
    out.mkdir(parents=True,exist_ok=True)
    (out/'geometry').mkdir(exist_ok=True)
    curves,pr=geometry(case)
    geoaudit=audit(curves,pr,case)
    (out/'GEOMETRY_TOPOLOGY_AUDIT.json').write_text(json.dumps(geoaudit,indent=2,allow_nan=False)+'\n')
    for i,c in enumerate(curves):np.savetxt(out/'geometry'/f'component_{i}.xyz',c,fmt='%.14g')
    if not all((geoaudit['determinant_screen_pass'],geoaudit['pairwise_linking_screen_pass'],
                geoaudit['source_chirality_matched_screen'],geoaudit['pairwise_separation_screen_pass'])):
        raise ValueError('FAIL CLOSED topology screen: '+json.dumps(geoaudit))
    cfg={'case':case,'grid':n,'duration':duration,'frames':frames,'core':core,
         'geometry_sha256':geoaudit['geometry_sha256']}
    npz=out/'THREE_CORE_EULER_MODEL.npz';side=out/'THREE_CORE_EULER_MODEL.source.json'
    if npz.exists() and side.exists() and not force:
        doc=json.loads(side.read_text())
        if file_hash(npz)!=doc.get('npz_sha256') or doc.get('build_cfg')!=cfg:raise ValueError('NPZ source mismatch; --force required')
        diag=doc['euler_diagnostics']
    else:
        solver=SpectralEuler3D(n)
        v0=init_three_core(solver,curves,core=core)
        t,v,diag=evolve(solver,v0,duration=duration,frame_count=frames,cfl_limit=.14)
        xyz=(np.arange(n)-n//2)*solver.dx
        np.savez_compressed(npz,x=xyz,y=xyz,z=xyz,t=t,v=v,source_type=np.array(CLASS),
          calibration=np.array('DIMENSIONLESS_PERIODIC_PROXY_NOT_SST_SI'))
        doc={'schema':'A064-HOPF3-EULER-v1','source_type':CLASS,
             'science_tier':'SIMULATED_INITIAL_VALUE_PROTOTYPE','npz_sha256':file_hash(npz),
             'build_cfg':cfg,'euler_diagnostics':diag,
             'geometry_provenance':pr,'e011_provider_qualified':False,
             'mechanical_gear_contact_modeled':False,'phase_lock_test':'NOT_PERFORMED',
             'framework_v1_0_7_freeze':'NOT_EXECUTED',
             'SST_physical_claim':'NONE','invariant_manifold_gate':'UNRESOLVED'}
        side.write_text(json.dumps(doc,indent=2,allow_nan=False)+'\n')
    if file_hash(npz)!=json.loads(side.read_text())['npz_sha256']:raise ValueError('invalid NPZ checksum')
    flow=PeriodicEulerFlow(npz)
    # discovery FIRST; no transport observables are examined before seal write.
    _,s0,_=field_data(flow,flow.axes,float(flow.times[0]))
    scan=iso_scan(flow.v[0],flow.axes)
    torus=first_genus_one_feature(s0,flow.axes,curves)
    mesh=out/'DISCOVERED_GENUS1_ISOSURFACE.npz'
    torus_meta=None
    if torus:
        np.savez_compressed(mesh,vertices=torus['vertices'],faces=torus['faces'],level=torus['level'])
        torus_meta={k:v for k,v in torus.items() if k not in ('vertices','faces')}
    elif mesh.exists():mesh.unlink()
    discoveries={'case':case,'npz_sha256':file_hash(npz),'geometry_sha256':geoaudit['geometry_sha256'],
                 'time_index':0,'scanned_percentiles':[65,75,85,92,96,98,99,99.5],
                 'scan':scan,'first_genus_one':torus_meta,
                 'separatrix_claim':'NO_INVARIANT_MANIFOLD_IDENTIFIED'}
    (out/'DISCOVERY_ONLY.json').write_text(json.dumps(discoveries,indent=2,allow_nan=False)+'\n')
    seal={'canonical_discovery_sha256':canonical_hash(discoveries),'npz_sha256':file_hash(npz),
          'mesh_sha256':file_hash(mesh) if mesh.exists() else None,
          'transport_audit_computed_at_seal_write':False,'formal_blind_certification':'NOT_EXECUTED'}
    (out/'DISCOVERY_SEAL.json').write_text(json.dumps(seal,indent=2,allow_nan=False)+'\n')
    # Transport stage begins ONLY after discovery sealing.
    from a064.analysis import run as original_a064_run
    prev=original_a064_run(flow,flow.axes,float(flow.times[0]),float(flow.times[-1]),
            out/'ENSTROPHY_ENVELOPE','HOPF_THREECORE_SIMULATION',doc,skip_stagnation=True)
    torus_t={'status':'NO_WATERTIGHT_GENUS_ONE_CANDIDATE'}
    if torus:
        _,s1,_=field_data(flow,flow.axes,float(flow.times[-1]))
        _,s2,_=field_data(flow,flow.axes,float(flow.times[1]))
        torus_t=transport_audit(flow,flow.axes,torus,s0,s1,float(flow.times[0]),
             float(flow.times[-1]),scalar_derivative=s2,derivative_dt=float(flow.times[1]))
    exchange=exchange_probe(flow,curves,float(flow.times[0]),float(flow.times[-1]))
    result={'case':case,'model':'PERIODIC_INCOMPRESSIBLE_3D_EULER_INITIALIZED_FROM_UNQUALIFIED_3CORE_LINK',
            'time_frames':frames,'grid':n,'euler_diagnostics':diag,
            'outer_enstrophy':prev['transport'],'outer_candidate_detected':prev['candidate_detected'],
            'genus_one_feature':torus_meta,'genus_one_transport':torus_t,
            'kinematic_nearest_core_exchange':exchange,
            'geometry_topology':geoaudit,
            'genuine_separatrix_gate':'UNRESOLVED_NO_INDEPENDENT_INVARIANT_MANIFOLD',
            'gear_force_phase_lock_gate':'UNRESOLVED_MECHANICAL_FORCES_NOT_SIMULATED',
            'convergence_gate':'UNRESOLVED_TWO_GRIDS_ONLY',
            'provider_gate':'UNRESOLVED_E011_NOT_ANCHORED',
            'blind_framework_gate':'NOT_EXECUTED',
            'discovery_sha256':seal['canonical_discovery_sha256']}
    (out/'GATE_RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result
