#!/usr/bin/env python3
"""A003 0.3.2. Independently audited evolving polygon snapshots, genuine C005 RK4,
spatial and temporal ladders, and source-pinned Framework 1.0.10 diagnostics.
Not a Navier-Stokes/Euler PDE or physical vortex-core certification.
"""
from __future__ import annotations
import argparse, hashlib, json, math, secrets, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from a003_diagnostic_v027 import load_framework, json_write
from fourier_atlas_adapter import resolve_atlas_root, read_xyz, safe_atlas_file, sha256_file
from g5_extended import independent_geometry_invariants, rotation_for_projection
from crossing_trace import crossing_trace
from g6_pklsa_pilot_v029 import source_check, g5_check, find_g5_summary, find_workbench, E010_REL, C005_REL, FRAMEWORK_REL, EXPECTED_MANIFEST
from g6_pklsa_temporal_v030 import SEEDS, register_e010, c005_callable, rk4, curve_length
from g6_safety_independence_v032 import (polygon_interpolant_certificate, dop853_independent_integrator,
    e010_candidate_contract, persistent_registry_readback, euler_closure_audit)
from g6_external_carriers_v032 import audit_external_carriers

VERSION = '0.3.2'
SCHEMA = 'sst.a003.g6-dynamic-qualification/2'
LEVELS = (150, 300, 600, 1200)
STEPS_LOW = (4, 8, 16)
STEPS_HIGH = (8, 16)
TIMES_INDEX = (0, 4, 8, 12, 16)
EXPECTED_DET = {'fibonacci_torus_F3': 3, 'fibonacci_torus_F4': 1}
EXPECTED_V3 = {'fibonacci_torus_F3': -1, 'fibonacci_torus_F4': -20}
EXPECTED_POLY = {'fibonacci_torus_F3': [1,-1,1], 'fibonacci_torus_F4': [1,-1,0,1,-1,1,0,-1,1]}


def _cyclic_far(i: np.ndarray, j: np.ndarray, n: int, gap: int):
    d=np.abs(i-j)
    return np.minimum(d,n-d)>gap


def _pair_segment_distances(x: np.ndarray, ia: np.ndarray, ib: np.ndarray) -> np.ndarray:
    """Exact minimum squared Euclidean distance between finite 3-D segments.
    Considers line-line interior and all four boundary projections. Independent
    of midpoint velocity / 2-D knot projection.
    """
    n=len(x)
    p=x[ia]; q=x[ib]; u=x[(ia+1)%n]-p;v=x[(ib+1)%n]-q;w=p-q
    a=np.einsum('ij,ij->i',u,u);b=np.einsum('ij,ij->i',u,v)
    c=np.einsum('ij,ij->i',v,v);d=np.einsum('ij,ij->i',u,w);e=np.einsum('ij,ij->i',v,w)
    if np.any(a<=0) or np.any(c<=0):raise ValueError('zero-length filament segment')
    den=a*c-b*b
    valid=den>1e-14*a*c
    s=np.divide(b*e-c*d,den,out=np.zeros_like(den),where=valid)
    t=np.divide(a*e-b*d,den,out=np.zeros_like(den),where=valid)
    ok=valid&(s>=0)&(s<=1)&(t>=0)&(t<=1)
    interior=np.sum((w+s[:,None]*u-t[:,None]*v)**2,axis=1)
    dist2=np.where(ok,interior,np.inf)
    # p0, p1 projected onto q-segment; q0, q1 projected onto p-segment.
    t0=np.clip(e/c,0,1)
    t1=np.clip((e+b)/c,0,1)
    s0=np.clip(-d/a,0,1)
    s1=np.clip((b-d)/a,0,1)
    dist2=np.minimum(dist2,np.sum((w-t0[:,None]*v)**2,axis=1))
    dist2=np.minimum(dist2,np.sum((w+u-t1[:,None]*v)**2,axis=1))
    dist2=np.minimum(dist2,np.sum((w+s0[:,None]*u)**2,axis=1))
    dist2=np.minimum(dist2,np.sum((w-v+s1[:,None]*u)**2,axis=1))
    return np.sqrt(np.maximum(dist2,0))


def segment_clearance(x: np.ndarray, *, skip_edges: int=1) -> dict:
    """Exact segment clearance using provably exhaustive midpoint-ball broadphase.
    The center separation bound for two segments at distance <= D is
    <= D + half_length_i + half_length_j. KD-tree only selects candidates;
    all candidate distances use the finite 3-D segment formula.
    """
    from scipy.spatial import cKDTree
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or x.shape[1]!=3 or len(x)<6 or not np.isfinite(x).all():raise ValueError('invalid polygon')
    n=len(x);edge=np.roll(x,-1,axis=0)-x;length=np.linalg.norm(edge,axis=1)
    if np.any(length<=0):raise ValueError('zero-length edge')
    centers=x+0.5*edge; tree=cKDTree(centers)
    near=tree.query(centers,k=min(n, max(32,2*skip_edges+16)))[1]
    ii=np.repeat(np.arange(n,dtype=int),near.shape[1]);jj=near.reshape(-1)
    good=(ii<jj)&_cyclic_far(ii,jj,n,skip_edges)
    ii=ii[good];jj=jj[good]
    if len(ii): best=float(np.min(_pair_segment_distances(x,ii,jj)))
    else:best=float(np.linalg.norm(np.ptp(x,axis=0)))
    # upper bound on midpoint spacing using maximum entire segment length.
    radius=best+float(np.max(length)) + 1e-12
    pairs=tree.query_pairs(radius,output_type='ndarray')
    valid=_cyclic_far(pairs[:,0],pairs[:,1],n,skip_edges) if len(pairs) else np.zeros(0,dtype=bool)
    pairs=pairs[valid]
    if len(pairs):
        dist=_pair_segment_distances(x,pairs[:,0],pairs[:,1]);where=int(np.argmin(dist))
        best=min(best,float(dist[where]));closest=pairs[where].tolist()
    else:closest=None
    diameter=float(np.linalg.norm(np.ptp(x,axis=0)))
    return {'min_distance':best,'min_distance_over_diameter':best/max(diameter,1e-300),
        'skip_cyclic_edges':skip_edges,'segment_pairs_evaluated':int(len(pairs)+len(ii)),
        'closest_edge_pair':closest,'method':'exhaustive_KDTree_bounded_3D_segment_segment',
        'collision_tolerance_over_diameter':1e-7,
        'clear_of_segment_contact':bool(best>1e-7*diameter)}


def best_rigid_fit(initial:np.ndarray, final:np.ndarray)->dict:
    """Kabsch fit, orientation preserving, returns shape RMS after removing SE(3)."""
    a=initial-initial.mean(axis=0);b=final-final.mean(axis=0)
    u,_,vt=np.linalg.svd(a.T@b);D=np.diag([1.,1.,np.linalg.det(u@vt)])
    rot=u@D@vt
    residue=a@rot-b
    return {'rms_nonrigid_deformation':float(np.sqrt(np.mean(np.sum(residue**2,axis=1)))),
        'centroid_translation':float(np.linalg.norm(initial.mean(axis=0)-final.mean(axis=0))),
        'det_rotation':float(np.linalg.det(rot))}


def snapshot_screen(x:np.ndarray, sid:str, *, with_diagrams=True, clearance=True)->dict:
    x=np.asarray(x,dtype=float)
    diameter=float(np.linalg.norm(np.ptp(x,axis=0)))
    result={'N':len(x),'length':curve_length(x),'diameter':diameter,'finite':bool(np.isfinite(x).all())}
    if not result['finite']:return result
    if clearance:
        result['near_segment_clearance']=segment_clearance(x,skip_edges=1)
        result['nonlocal_segment_clearance']=segment_clearance(x,skip_edges=max(3,math.ceil(0.02*len(x))))
    if with_diagrams:
        diagrams=[]
        for proj in (0,1):
            tr=crossing_trace(x@rotation_for_projection(proj).T)
            det=tr['diagram_determinant']
            diagrams.append({'projection':proj,'crossing_count':tr['crossing_count'],
                'nearly_degenerate_crossings':tr['nearly_degenerate_crossings'],
                'determinant':det.get('value'), 'determinant_status':det.get('status'),
                'expected_determinant':EXPECTED_DET[sid],
                'comparison':'UNRESOLVED_PROJECTION_DEGENERACY' if tr['nearly_degenerate_crossings'] or det.get('value') is None
                else 'PASS_DIAGRAM_DETERMINANT' if det.get('value')==EXPECTED_DET[sid] else 'FAIL_DIAGRAM_DETERMINANT'})
        result['diagrams']=diagrams
    return result


def provider_snapshot_screen(npz:dict,*, mode='endpoints') -> dict:
    """Version-guarded pyknotid on measured evolving polygons; never mocks/fabricated PASS.
    When absent, explicit UNRESOLVED. F4 determinant one is NOT sufficient;
    Alexander + v3 are required on checked polygons.
    """
    if mode=='off':return {'status':'UNRESOLVED','reason':'provider disabled explicitly','observations':[]}
    try:
        import importlib.metadata
        if importlib.metadata.version('pyknotid')!='0.5.3':
            return {'status':'UNRESOLVED','reason':'pyknotid version must be exactly 0.5.3','observations':[]}
        from g5_crossing_tolerance_v027 import scoped_pyknotid_crossing_fix
    except (ImportError,importlib.metadata.PackageNotFoundError) as exc:
        return {'status':'UNRESOLVED','reason':f'provider not available: {type(exc).__name__}', 'observations':[]}
    observations=[];errors=[]
    # endpoints and middle at N600/N1200, primary P0; independent P1 at endpoints.
    requested=[(600,j,0) for j in (0,8,16)]+[(1200,j,0) for j in (0,8,16)]
    requested+= [(600,j,1) for j in (0,16)]+[(1200,j,1) for j in (0,16)]
    if mode=='all':
        requested=[(n,j,p) for n in LEVELS for j in TIMES_INDEX for p in (0,1)]
    with scoped_pyknotid_crossing_fix() as provider_meta:
        for sid in SEEDS:
            for n,j,proj in requested:
                key=f'{sid}_N{n}_t{j:02d}'
                if key not in npz:
                    errors.append(f'missing snapshot {key}');continue
                try:
                    data=npz[key]@rotation_for_projection(proj).T
                    measured=independent_geometry_invariants(data)
                    passed=(measured['alexander_coefficients']==EXPECTED_POLY[sid] and measured['vassiliev_3']==EXPECTED_V3[sid])
                    observations.append({'seed':sid,'N':n,'step_index':j,'projection':proj,
                        'alexander_coefficients':measured['alexander_coefficients'],'v3':measured['vassiliev_3'],
                        'match':passed})
                except Exception as exc:
                    errors.append(f'{sid}/{n}/{j}/{proj}: {type(exc).__name__}: {exc}')
    return {'status':'UNRESOLVED' if errors else 'PASS_DIAGNOSTIC_ONLY' if all(o['match'] for o in observations) else 'FAIL_INVARIANT_DRIFT',
        'observations':observations,'errors':errors,'provider_meta':provider_meta,
        'claim_boundary':'bounded Alexander + v3 projected polygons, not complete dynamic ambient isotopy proof'}


def simulate_dynamic(atlas,registry,c005,out,*,epsilon=.05,final_time=2.,provider_mode='endpoints',
                     levels=LEVELS, steps_low=STEPS_LOW, steps_high=STEPS_HIGH) -> dict:
    levels=tuple(levels)
    if levels!=LEVELS:raise ValueError('science contract requires 150,300,600,1200 fixed ladder')
    if steps_low!=(4,8,16) or steps_high!=(8,16):raise ValueError('science contract timestep ladder modified')
    if not math.isfinite(epsilon) or not 0<epsilon<100 or not math.isfinite(final_time) or not 0<final_time<100:
        raise ValueError('invalid epsilon/final time')
    rhs,source=c005_callable(c005,epsilon)
    npz={};events=[];time_checks=[];spatial=[];snapshot_checks=[];continuous_checks=[];independent_solver_checks=[]
    for sid in SEEDS:
        r=next(r for r in registry['records'] if r['id']==sid and r['points']==1200 and r['sampling']=='uniform_t')
        src=safe_atlas_file(atlas,r['file']); h=sha256_file(src)
        if h!=r['sha256']:raise RuntimeError('A003 source hash changed during run')
        original=read_xyz(src,1200)
        finals={}
        for n in levels:
            initial=original[::1200//n].copy()
            steps=steps_low if n!=1200 else steps_high
            term={}
            for nstep in steps:
                final,snap=rk4(rhs,initial,final_time,nstep,snapshot_every=(1 if nstep==16 else 0))
                term[nstep]=final
                if nstep==16:
                    finals[n]=final
                    # Save *every* frozen five-snapshot phase for replay and forensic audit.
                    if len(snap)!=17:raise RuntimeError('missing every RK4 step endpoint')
                    certificate=polygon_interpolant_certificate([x for _,x in snap],gap=1)
                    continuous_checks.append({'seed':sid,'N':n,**certificate})
                    for k,(t,x) in enumerate(snap[::4]):
                        j=4*k;npz[f'{sid}_N{n}_t{j:02d}']=x.copy()
                        diag=snapshot_screen(x,sid)
                        diag.update({'seed':sid,'N':n,'step_index':j,'t':float(t),'t_over_T':k/4,
                            'shape_from_initial':best_rigid_fit(initial,x),'length_change_relative':(curve_length(x)-curve_length(initial))/curve_length(initial)})
                        snapshot_checks.append(diag)
                events.append({'seed':sid,'N':n,'steps':nstep,'dt':final_time/nstep,
                    'T':final_time,'initial_source_sha256':h,
                    'final_length':curve_length(final),'max_point_displacement':float(np.max(np.linalg.norm(final-initial,axis=1)))})
            if n in (150,300):
                try:
                    ctl=dop853_independent_integrator(rhs,initial,final_time,term[16])
                except (ImportError,ValueError,RuntimeError) as exc:
                    ctl={'status':'UNRESOLVED','reason':type(exc).__name__+': '+str(exc)}
                independent_solver_checks.append({'seed':sid,'N':n,**ctl})
            if len(steps)==3:
                ea=float(np.linalg.norm(term[4]-term[8]));eb=float(np.linalg.norm(term[8]-term[16]))
                ratio=eb/max(float(np.linalg.norm(term[16]-initial)),1e-15)
                observed=math.log2(ea/eb) if ea>0 and eb>0 else None
                passed=eb<max(1e-10,.6*ea) and ratio<1e-3
                time_checks.append({'seed':sid,'N':n,'steps':list(steps),'error_4_8':ea,'error_8_16':eb,
                    'relative_8_16':ratio,'observed_order':observed,'PASS':passed})
            else:
                eb=float(np.linalg.norm(term[8]-term[16]))
                ratio=eb/max(float(np.linalg.norm(term[16]-initial)),1e-15)
                time_checks.append({'seed':sid,'N':n,'steps':list(steps),'error_8_16':eb,
                    'relative_8_16':ratio,'observed_order':None, 'PASS':bool(ratio<1e-3),
                    'note':'two levels cannot establish RK4 temporal order'})
        abs_errors=[];shape_errors=[]
        for a,b in zip(levels,levels[1:]):
            # Exact nested samples from common frozen N=1200 seed.
            i=finals[a];j=finals[b][::b//a]
            abs_errors.append(float(np.sqrt(np.mean(np.sum((j-i)**2,axis=1)))))
            shape_errors.append(best_rigid_fit(i,j)['rms_nonrigid_deformation'])
        orders=[math.log2(abs_errors[k]/abs_errors[k+1]) if abs_errors[k]>0 and abs_errors[k+1]>0 else None for k in (0,1)]
        # No asymptotic second-order claim: prior observations order 0.68--1.13.
        spatial.append({'seed':sid,'levels':list(levels),'fixed_T':final_time,'fixed_fine_steps':16,
          'rms_lab_frame':abs_errors,'rms_shape_after_rigid_fit':shape_errors,
          'observed_orders':orders,'monotonic':bool(abs_errors[0]>abs_errors[1]>abs_errors[2]>0),
          'PASS':bool(abs_errors[0]>abs_errors[1]>abs_errors[2]>0)})
    outpath=out/'G6_DYNAMIC_TRAJECTORIES.npz';np.savez_compressed(outpath,**npz)
    diag_bad=[s for s in snapshot_checks for d in s['diagrams'] if d['comparison']=='FAIL_DIAGRAM_DETERMINANT']
    diag_unresolved=[s for s in snapshot_checks for d in s['diagrams'] if d['comparison']=='UNRESOLVED_PROJECTION_DEGENERACY']
    clear_bad=[s for s in snapshot_checks if not s['near_segment_clearance']['clear_of_segment_contact']]
    topo_diag_status='FAIL' if diag_bad else 'UNRESOLVED' if diag_unresolved else 'PASS_DIAGNOSTIC_ONLY'
    clearance_status='FAIL' if clear_bad else 'PASS_SAMPLED_ONLY'
    numerical_status='PASS' if all(z['PASS'] for z in time_checks+spatial) else 'FAIL'
    provider=provider_snapshot_screen(npz,mode=provider_mode)
    data={'schema':SCHEMA,'status':'QUALIFIED_DIAGNOSTICS_NOT_EULER' if numerical_status=='PASS' and topo_diag_status!='FAIL' and clearance_status!='FAIL' and provider['status']!='FAIL_INVARIANT_DRIFT' else 'FAIL_OR_UNRESOLVED',
        'model':'C005 Rosenhead-midpoint regularized filament dX/dt=u_eps[X], NOT Euler PDE',
        'epsilon_source_units':epsilon,'final_source_model_time':final_time,
        'temporal_integrator':'classical RK4 C005 externally imported RHS at all stages',
        'source_kernel':source,'genuine_external_c005':bool(source.get('source')=='fermat_ext.core.backend_biot_savart' and len(str(source.get('source_sha256','')))==64),'levels':list(levels),'time_step_low':list(steps_low),'time_step_N1200':list(steps_high),
        'snapshots_per_level':len(TIMES_INDEX),'trajectory_npz_sha256':sha256_file(outpath),
        'events':events,'time_checks':time_checks,'spatial_checks':spatial,
        'continuous_interpolant_checks':continuous_checks,'independent_solver_checks':independent_solver_checks,
        'continuous_interpolant_status':('PASS_INTERPOLANT_ONLY' if len(continuous_checks)==8 and all(q['status']=='PASS_INTERPOLANT_ONLY' for q in continuous_checks) else
           'FAIL_OBSERVED_CONTACT' if any(q['status'].startswith('FAIL') for q in continuous_checks) else 'UNRESOLVED'),
        'independent_solver_status':('PASS_DIAGNOSTIC_ONLY' if len(independent_solver_checks)==4 and all(q['status']=='PASS_DIAGNOSTIC_ONLY' for q in independent_solver_checks) else
           'FAIL_SOLVER_DISAGREEMENT' if any(q['status'].startswith('FAIL') for q in independent_solver_checks) else 'UNRESOLVED'),
        'snapshots':snapshot_checks,'diagram_screen_status':topo_diag_status,'diagram_bad_count':len(diag_bad),
        'diagram_unresolved_count':len(diag_unresolved),'clearance_status':clearance_status,
        'contact_snapshot_count':len(clear_bad),'temporal_spatial_status':numerical_status,
        'provider_invariants':provider,'no_reconnection_certified':False,'linear_interpolant_no_contact_checked':True,
        'finite_core_physical_calibration':False,'euler_pressure_poisson_closure':False}
    json_write(out/'G6_DYNAMIC_DIAGNOSTICS.json',data)
    return data


def generate_pdf(out,summary,ledger):
    try:
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:return {'status':'UNRESOLVED_REPORTLAB_MISSING'}
    dst=out/'A003_v0.3.2_DYNAMIC_QUALIFICATION_REPORT.pdf';c=Canvas(str(dst),pagesize=A4)
    w,h=A4;c.setFont('Helvetica-Bold',15);c.drawString(42,h-53,'A003 v0.3.2 - Continuous Safety / Independent Dynamics')
    c.setFont('Helvetica',9)
    d=summary['dynamic'];lines=[f"Run: {summary['run_id']}",f"G5: {summary['g5']['status']}",
       f"E010 source overlay: {summary['registration']['status']}",f"Framework: {summary['framework']['status']}",
       f"Temporal/spatial: {d.get('temporal_spatial_status','UNRESOLVED')}",
       f"3D segment clearance: {d.get('clearance_status','UNRESOLVED')}",
       f"Projected diagram screen: {d.get('diagram_screen_status','UNRESOLVED')}",
       f"Alexander/v3 provider: {d.get('provider_invariants',{}).get('status','UNRESOLVED')}",
       f"G6 physics: {summary['overall_g6_status']}",'','Spatial ladder: N=150,300,600,1200; T=2 source units',
       'RK4: 4/8/16 steps (N<=600), 8/16 steps (N=1200).','', 'Per-seed final shape RMS discrepancies:']
    for e in d.get('spatial_checks',[]):lines.append(f"{e['seed']}: {', '.join(f'{x:.5g}' for x in e['rms_lab_frame'])}")
    lines.extend(['','Actual v1.0.10 GateLedger:'])
    lines += [f"{r['gate_id']}: {r['status']} / {r['qualification']}" for r in ledger['records']]
    lines.extend(['','Scientific boundaries:',
        'Projected determinants, Alexander and v3 are diagnostics, not full isotopy proof.',
        '17 RK4 endpoints; only linear interpolant non-contact can be certified.',
        'A003 analytical seeds are NOT independent experiment carriers.',
        'E010 v0.3.1 runtime contract and proposed index do not commit canonical registry.',
        'No continuous true-ODE path bound, pressure Poisson or full Euler PDE.'])
    y=h-78
    for s in lines:
        if y<52:c.showPage();c.setFont('Helvetica',9);y=h-54
        c.drawString(42,y,s[:112]);y-=14
    c.save();return {'status':'PASS','file':dst.name,'sha256':sha256_file(dst)}


def main(argv=None):
    p=argparse.ArgumentParser(description='A003 0.3.2 interval safety + independent solver and carrier controls')
    p.add_argument('--atlas',type=Path);p.add_argument('--workbench',type=Path)
    p.add_argument('--framework-root',type=Path);p.add_argument('--e010-root',type=Path);p.add_argument('--c005-root',type=Path)
    p.add_argument('--g5-summary',type=Path)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'A003_Fourier_Knot_Import_Adapter_v0.3.2-outputs')
    p.add_argument('--epsilon',type=float,default=.05);p.add_argument('--final-time',type=float,default=2.)
    p.add_argument('--provider-topology',choices=('endpoints','all','off'),default='endpoints')
    p.add_argument('--preflight-only',action='store_true')
    p.add_argument('--independent-carriers',type=Path,help='source-native independently hashed KnotPlot/Ridgerunner carrier manifest')
    a=p.parse_args(argv)
    atlas=a.atlas.resolve() if a.atlas else resolve_atlas_root(None)
    wb=find_workbench(atlas,a.workbench)
    fw,meta,mod,fw_hash=load_framework(a.framework_root or (wb/FRAMEWORK_REL if wb else None))
    registry,_=source_check(atlas)
    g5_path=find_g5_summary(atlas,a.g5_summary,wb)
    g5=g5_check(g5_path)
    # A failed scientific gate can continue. A broken or substituted ledger cannot.
    if g5_path is not None and g5_path.is_file():
        ledger_path=g5_path.parent/'GATE_LEDGER.json'
        raw_path=g5_path.parent/'g5_corrected_four_resolutions.json'
        if not ledger_path.is_file() or not raw_path.is_file():
            raise RuntimeError('G5 receipt lacks ledger or raw provider data; integrity abort')
        prior=json.loads(ledger_path.read_text(encoding='utf-8'))
        unsigned={k:v for k,v in prior.items() if k!='ledger_sha256'}
        calculated=hashlib.sha256((json.dumps(unsigned,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()
        if calculated!=prior.get('ledger_sha256'):
            raise RuntimeError('G5 GateLedger tampered or noncanonical; integrity abort')
    if g5['status']=='FAIL' and 'file' not in g5:
        raise RuntimeError('G5 negative result without verifiable complete receipt')
    e010=a.e010_root.resolve() if a.e010_root else (wb/E010_REL if wb else None)
    c005=a.c005_root.resolve() if a.c005_root else (wb/C005_REL if wb else None)
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'_'+secrets.token_hex(5)
    out=a.out.resolve()/run;out.mkdir(parents=True,exist_ok=False)
    registration=({'status':'UNRESOLVED','reason':'preflight only'} if a.preflight_only else register_e010(atlas,registry,wb,e010,out))
    if a.preflight_only or c005 is None or not (c005/'fermat_ext'/'core.py').is_file():
        dyn={'status':'UNRESOLVED','reason':'preflight only or C005 unavailable',
             'provider_invariants':{'status':'UNRESOLVED'},'temporal_spatial_status':'UNRESOLVED',
             'diagram_screen_status':'UNRESOLVED','clearance_status':'UNRESOLVED'}
    else:dyn=simulate_dynamic(atlas,registry,c005,out,epsilon=a.epsilon,final_time=a.final_time,provider_mode=a.provider_topology)
    prepared=e010_candidate_contract(atlas,registry,wb,e010,out) if not a.preflight_only else {'status':'UNRESOLVED'}
    persisted=persistent_registry_readback(wb,e010,atlas,registry) if not a.preflight_only else {'status':'UNRESOLVED'}
    independent_carriers=audit_external_carriers(a.independent_carriers,wb,c005,out,a.epsilon,a.final_time) if not a.preflight_only else {'status':'UNRESOLVED'}
    euler=euler_closure_audit(dyn.get('source_kernel'),a.epsilon,dyn.get('status'))
    json_write(out/'G6P9_EULER_CLOSURE_AUDIT.json',euler)
    json_write(out/'G6P8_CANONICAL_REGISTRY_PROPOSAL_STATUS.json',{'prepared':prepared,'readback':persisted})
    GD=mod.GateDefinition;D=[
      GD('G6P0','Framework v1.0.10 exact gate source, release freeze status'),
      GD('G6P1','A003 manifest and unmodified original G5 evidence',('G6P0',)),
      GD('G6P6','E010 v0.3.1 native source overlay + eight SHA-256 analytic carriers',('G6P1',)),
      GD('G6P7','C005 v0.6.1 true RK4 dynamic time and spatial convergence',('G6P6',)),
      GD('G6P10','3D segment-segment clearance at five actual times',('G6P7',)),
      GD('G6P11','Two independent projected diagram determinants per snapshot',('G6P7',)),
      GD('G6P12','Corrected pyknotid Alexander + v3 of evolving polygons',('G6P11',)),
      GD('G6P13','F3/F4 same-T four-mesh monotone spatial convergence',('G6P7',)),
      GD('G6P14','Certified no-contact for piecewise-linear homotopy of ALL RK4 step endpoints',('G6P10',)),
      GD('G6P15','Independent DOP853 numerical solver versus RK4 for same C005 RHS',('G6P7',)),
      GD('G6P16','Independent provenance-separated external knot families from E010',('G6P6',)),
      GD('G6P8','Versioned E010 persistent source+carrier registry independently qualified',('G6P6',)),
      GD('G6P9','Incompressible Euler PDE and physically calibrated vortex core',('G6P7',)),
      GD('G6','Physical PKLSA-Euler dynamic qualification',('G6P1','G6P6','G6P7','G6P10','G6P11','G6P12','G6P13','G6P14','G6P15','G6P16','G6P8','G6P9'))]
    ledger=mod.GateLedger(D,strict_dependencies=False)
    def norm(st):return 'PASS' if st.startswith('PASS') else 'FAIL' if st.startswith('FAIL') else 'UNRESOLVED'
    has_data=isinstance(dyn.get('time_checks'),list)
    ev={'G6P0':lambda:{'status':'PASS' if meta.get('status')=='CANONICAL_FROZEN' else 'UNRESOLVED',
                          'metrics':{'gates_sha256':fw_hash,'release_status':meta.get('status')}},
        'G6P1':lambda:{'status':g5['status'],'metrics':g5},
        'G6P6':lambda:{'status':registration['status'],'metrics':registration},
        'G6P7':lambda:{'status':dyn.get('temporal_spatial_status','UNRESOLVED') if dyn.get('genuine_external_c005') else 'UNRESOLVED',
                         'reason':'C005 native import required: a test-double never qualifies scientific gate'},
        'G6P10':lambda:{'status':norm(dyn['clearance_status']),'metrics':{'sampled_only':True}},
        'G6P11':lambda:{'status':norm(dyn['diagram_screen_status']),'metrics':{'determinant_cannot_certify_F4':True}},
        'G6P12':lambda:{'status':norm(dyn['provider_invariants']['status']),
                        'metrics':{'provider_status':dyn['provider_invariants']['status']}},
        'G6P13':lambda:{'status':'PASS' if has_data and all(s['PASS'] for s in dyn['spatial_checks']) else 'FAIL' if has_data else 'UNRESOLVED'},
        'G6P14':lambda:{'status':norm(dyn.get('continuous_interpolant_status','UNRESOLVED')),
             'metrics':{'scope':'polygonal linear interpolant, not true ODE path',
                        'certified_levels':sum(q['status']=='PASS_INTERPOLANT_ONLY' for q in dyn.get('continuous_interpolant_checks',[]))}},
        'G6P15':lambda:{'status':norm(dyn.get('independent_solver_status','UNRESOLVED')),
             'metrics':{'independent_integrator_not_independent_physics':True}},
        'G6P16':lambda:{'status':norm(independent_carriers.get('status','UNRESOLVED')),'metrics':independent_carriers},
        'G6P8':lambda:{'status':persisted['status'],'reason':'Proposal is never a canonical source commit'},
        'G6P9':lambda:{'status':euler['status'],'metrics':euler},
        'G6':lambda:{'status':'UNRESOLVED','reason':'No true ODE interval enclosure, canonical E010 production registry, or Euler PDE closure'}}
    ledger.run_evaluators(ev);record=ledger.to_dict();ledger.write(out/'GATE_LEDGER.json')
    summary={'schema':SCHEMA,'run_id':run,'version':VERSION,'overall_g6_status':'UNRESOLVED',
      'framework':{'version':'1.0.10','status':meta.get('status'),'gates_sha256':fw_hash},
      'atlas_manifest_sha256':EXPECTED_MANIFEST,'g5':g5,'registration':registration,
      'persistent_e010_registry':{'proposal':prepared,'readback':persisted},'euler_closure_audit':euler,
      'independent_external_carriers':independent_carriers,
      'dynamic':{k:v for k,v in dyn.items() if k not in ('snapshots','events')},
      'gate_results':{q['gate_id']:q['status'] for q in record['records']},
      'gate_ledger_sha256':sha256_file(out/'GATE_LEDGER.json'),
      'all_scientific_gates_qualified':False,'physical_euler_certified':False,'continuous_topology_preservation_certified':False,
      'interpolant_topology_preservation_only':dyn.get('continuous_interpolant_status')=='PASS_INTERPOLANT_ONLY'}
    json_write(out/'G6_DYNAMIC_SUMMARY.json',summary)
    pdf=generate_pdf(out,summary,record);json_write(out/'PDF_RENDER.json',pdf)
    print(json.dumps({'out':str(out),'g5':g5['status'],'dynamic':dyn['status'],
        'topology_provider':dyn['provider_invariants']['status'],'g6':'UNRESOLVED',
        'gates':summary['gate_results'],'pdf':pdf['status']},indent=2))
    return 2 if any(q['status']=='FAIL' for q in record['records']) else 3

if __name__=='__main__':raise SystemExit(main())
