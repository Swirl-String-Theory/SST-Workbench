"""Preregistered candidate discovery -> sealed boundary -> independent transport audit."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import label
from scipy.optimize import root
from skimage.measure import marching_cubes
import trimesh


def sha(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def sample_scalar(axes,values,points):
    p=np.asarray(points,float).reshape(-1,3)
    return RegularGridInterpolator(axes,values,fill_value=np.nan,bounds_error=False)(p)


def curl_div(v,axes):
    dx=[float(np.mean(np.diff(a))) for a in axes]
    der=[[np.gradient(v[...,j],dx[i],axis=i,edge_order=2) for i in range(3)] for j in range(3)]
    curl=np.stack([der[2][1]-der[1][2],der[0][2]-der[2][0],der[1][0]-der[0][1]],axis=-1)
    div=der[0][0]+der[1][1]+der[2][2]
    return curl,div


def field_data(flow,axes,t):
    v=flow.frame(axes,t)
    if not np.all(np.isfinite(v)): raise ValueError('velocity undefined on grid / out-of-bounds')
    omega,div=curl_div(v,axes)
    energy=np.einsum('...i,...i->...',omega,omega)
    return v,energy,div


def closed_components(vertices,faces):
    tm=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    components=tm.split(only_watertight=False)
    return sorted([c for c in components if c.is_watertight and len(c.faces)>100],key=lambda c:c.area,reverse=True)


def candidate_discovery(axes,scalar,percentiles=(65.,75.,85.,92.)):
    """Transport-blind discovery: vorticity-derived connected closed isosurfaces.

    The returned surface is merely a candidate; no dynamical label exists at this stage.
    """
    s=np.asarray(scalar)
    if not np.all(np.isfinite(s)) or np.max(s)<=1e-24: return None,[], 'zero_or_nonfinite_vorticity'
    spacing=tuple(float(np.mean(np.diff(a))) for a in axes)
    high=s[s>max(np.max(s)*1e-9,0.)]
    candidates=[]
    # Fixed predeclared percentile ordering; never optimized with transport metrics.
    for pct in percentiles:
        level=float(np.percentile(high,pct))
        if level<=0 or level>=np.max(s): continue
        try:
            vs,fs,_,_=marching_cubes(s.astype('float32'),level=level,spacing=spacing)
        except (ValueError,RuntimeError): continue
        vs=vs+np.array([a[0] for a in axes])
        comps=closed_components(vs,fs)
        count=int(np.sum(s>=level))
        candidates.append({'percentile':pct,'iso_enstrophy_s_inv2':level,'closed_component_count':len(comps),
                           'active_voxels':count,'largest_closed_area_m2':float(comps[0].area) if comps else 0.})
        if comps and count>24 and count<s.size-24:
            chosen=comps[0]
            if not chosen.is_watertight or not chosen.is_winding_consistent: continue
            # Largest surface component chosen without transport metrics.
            return {'vertices':np.asarray(chosen.vertices,float),'faces':np.asarray(chosen.faces,int),
                    'level':level,'percentile':pct,'component_count':len(comps),
                    'area_m2':float(chosen.area),'volume_m3':abs(float(chosen.volume)),
                    'is_watertight':bool(chosen.is_watertight),
                    'active_voxels':count},candidates,None
    return None,candidates,'no_closed_nontrivial_vorticity_isosurface'


def hyperbolic_stagnation_scan(flow,axes,t,cap=16):
    """Optional saddle screening; missing saddle is NOT proof of absent invariant tori."""
    try:
        idx=np.stack(np.meshgrid(*[np.linspace(3,len(a)-4,5,dtype=int) for a in axes],indexing='ij'),-1).reshape(-1,3)
        pts=np.column_stack([axes[j][idx[:,j]] for j in range(3)])
        speeds=np.linalg.norm(flow.velocity(pts,t),axis=1)
        seeds=pts[np.argsort(speeds)[:cap]]
        h=max(1e-9,min(np.min(np.diff(a)) for a in axes)*.03)
        lo=np.array([a[1] for a in axes]);hi=np.array([a[-2] for a in axes])
        found=[]
        for p in seeds:
            sol=root(lambda x: flow.velocity([x],t)[0],p,tol=1e-9)
            if not sol.success or np.any(sol.x<=lo) or np.any(sol.x>=hi):continue
            if np.linalg.norm(flow.velocity([sol.x],t))>1e-5*max(np.nanmax(speeds),1e-15):continue
            if any(np.linalg.norm(sol.x-np.array(f['point_m']))<4*h for f in found):continue
            cols=[(flow.velocity([sol.x+np.eye(3)[k]*h],t)[0]-flow.velocity([sol.x-np.eye(3)[k]*h],t)[0])/(2*h) for k in range(3)]
            eig=np.linalg.eigvals(np.column_stack(cols))
            # saddle = eigenvalues with both positive and negative real parts, no near-zero Re allowed for hyperbolicity
            scale=max(1e-15,float(np.max(np.abs(eig))))
            is_hyp=bool(np.min(eig.real)<-1e-3*scale and np.max(eig.real)>1e-3*scale and np.min(np.abs(eig.real))>1e-4*scale)
            found.append({'point_m':sol.x.tolist(),'eigenvalue_real_s_inv':eig.real.tolist(),
                          'eigenvalue_imag_s_inv':eig.imag.tolist(),'hyperbolic_saddle':is_hyp})
            if len(found)>=8:break
        return found
    except (ValueError, FloatingPointError,RuntimeError):
        return []


def rk4(flow,points,t0,t1,steps):
    p=np.array(points,dtype=float,copy=True);dt=(t1-t0)/steps
    for i in range(steps):
        t=t0+i*dt
        k1=flow.velocity(p,t);k2=flow.velocity(p+.5*dt*k1,t+.5*dt)
        k3=flow.velocity(p+.5*dt*k2,t+.5*dt);k4=flow.velocity(p+dt*k3,t+dt)
        p+=(dt/6.)*(k1+2*k2+2*k3+k4)
        if not np.all(np.isfinite(p)):break
    return p


def transport_audit(flow,axes,candidate,scalar0,scalar1,t0,t1,steps=28,nseeds=112,scalar_derivative=None,derivative_dt=None):
    """Flux through detected level set + actual tracer side exchange. Never fit S using these outcomes."""
    verts=candidate['vertices'];level=float(candidate['level'])
    chosen=np.unique(np.linspace(0,len(verts)-1,min(nseeds,len(verts)),dtype=int))
    points=verts[chosen]
    spacing=np.array([np.mean(np.diff(a)) for a in axes]);h=float(np.min(spacing))
    # Grid-derived gradients avoid model-specific analytic priors.
    ds=[np.gradient(scalar0,spacing[k],axis=k,edge_order=2) for k in range(3)]
    grad=np.stack([sample_scalar(axes,d,points) for d in ds],axis=1)
    gm=np.linalg.norm(grad,axis=1)
    valid=np.isfinite(gm)&(gm>max(np.nanmax(gm)*1e-5,1e-30))
    pp=points[valid];gg=grad[valid];gm=gm[valid]
    if len(pp)<30:
        return {'status':'UNRESOLVED','reason':'insufficient_finite_surface_gradients','valid_n':int(len(pp))}
    normals=gg/gm[:,None]
    # stationary source case: 0 time derivative, with frozen field explicitly declared
    s_der=scalar1 if scalar_derivative is None else scalar_derivative
    dt_der=(t1-t0) if derivative_dt is None else derivative_dt
    dsdt=(sample_scalar(axes,s_der,pp)-sample_scalar(axes,scalar0,pp))/max(dt_der,1e-30)
    vel=flow.velocity(pp,t0)
    q=(dsdt+np.sum(vel*gg,axis=1))/gm   # m/s, relative normal speed
    speed=np.linalg.norm(vel,axis=1)
    u_ref=float(max(np.nanpercentile(speed,95),1e-15))
    q95=float(np.nanpercentile(np.abs(q),95));flux_rel=q95/u_ref
    # Unbiased symmetric tracer releases, initial side known by scalar evaluation, not nearest mesh guess.
    delta=.4*h
    seeds=np.concatenate([pp+delta*normals,pp-delta*normals],axis=0)
    before=sample_scalar(axes,scalar0,seeds)-level
    end=rk4(flow,seeds,t0,t1,steps)
    after=sample_scalar(axes,scalar1,end)-level
    good=np.isfinite(before)&np.isfinite(after)&(np.abs(before)>max(abs(level)*1e-8,1e-26))
    if not good.any():
        return {'status':'UNRESOLVED','reason':'all_tracers_invalid','flux_p95_m_s':q95,
                'flux_p95_over_U':flux_rel}
    crossed=np.sign(before[good]) != np.sign(after[good])
    # Error/crossing study with smaller integration step; NOT a separate independent source.
    end2=rk4(flow,seeds,t0,t1,2*steps)
    after2=sample_scalar(axes,scalar1,end2)-level
    good2=good&np.isfinite(after2)
    discr=float(np.linalg.norm(end[good2]-end2[good2],axis=1).max()) if good2.any() else float('nan')
    fraction=float(np.mean(crossed))
    # How well the separately detected scalar feature persists when its initial surface is material-advected.
    advected=rk4(flow,pp,t0,t1,2*steps)
    residual=sample_scalar(axes,scalar1,advected)-level
    rel_feature=float(np.nanpercentile(np.abs(residual),90)/max(level,1e-30))
    return {'status':'MEASURED','flux_p95_m_s':q95,'flux_p95_over_U':flux_rel,'U_ref_m_s':u_ref,
            'tracer_cross_fraction':fraction,'tracer_cross_count':int(np.sum(crossed)),
            'valid_tracers':int(good.sum()),'rktraj_refinement_max_m':discr,
            'advected_feature_residual_rel_p90':rel_feature,'integration_steps':steps,
            'h_m':h,'time_window_s':float(t1-t0),'temporal_derivative_dt_s':float(dt_der)}


def run(flow,axes,t0,t1,output,mode,source=None,core=None,skip_stagnation=False):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    v0,s0,d0=field_data(flow,axes,t0)
    v1,s1,d1=field_data(flow,axes,t1)
    dx=min(float(np.mean(np.diff(a))) for a in axes)
    u=max(float(np.percentile(np.linalg.norm(v0.reshape(-1,3),axis=1),95)),1e-15)
    divergence_rel=float(np.percentile(np.abs(d0),95)*dx/u)
    c,alternatives,why=candidate_discovery(axes,s0)
    # Eulerian hyperbolic-set detection is also PART of the discovery stage.
    # Irrotational potential-flow separatrices may exist despite curl(v)=0.
    stagnant=hyperbolic_stagnation_scan(flow,axes,t0) if not skip_stagnation else []
    candidate={'version':'v0.2.0' if mode=='EULER_SIMULATION_MODEL' else 'v0.1.1','mode':mode,'source':source,'evidence_class':flow.evidence_class,
               'discovery_input':'curl(velocity_at_t0)_squared_isosurface','choice_policy':'fixed_percentile_first_closed_component_largest_area',
               'candidates_screened':alternatives,'hyperbolic_stagnation_candidates':stagnant,
               'accepted_enstrophy_surface':c is not None,'accepted':c is not None,'rejection_reason':why}
    if c is not None:
        candidate['selected']={k:v for k,v in c.items() if k not in ('vertices','faces')}
        np.savez_compressed(out/'CANDIDATE_SURFACE.npz',vertices_m=c['vertices'],triangles=c['faces'],
                            discovered_scalar_level_s_inv2=c['level'])
    (out/'CANDIDATE_DISCOVERY.json').write_text(json.dumps(candidate,indent=2,allow_nan=False),encoding='utf8')
    digest=sha(candidate)
    # Discovery is sealed before any material transport test is executed.
    mesh_path=out/'CANDIDATE_SURFACE.npz'
    with mesh_path.open('rb') if mesh_path.exists() else open(__file__,'rb') as fh:
        mesh_sha=hashlib.sha256(fh.read()).hexdigest() if mesh_path.exists() else None
    source_sha=getattr(flow,'sha256',None)
    seal={'candidate_json_canonical_sha256':digest,'candidate_mesh_sha256':mesh_sha,
          'input_npz_sha256':source_sha,'selected_before_transport':True,
          'framework_freeze_status':'NOT_EXECUTED_V1_0_7'}
    (out/'DISCOVERY_SEAL.json').write_text(json.dumps(seal,indent=2,allow_nan=False)+'\n',encoding='utf8')
    (out/'DISCOVERY_SEAL.sha256').write_text(digest+'  CANDIDATE_DISCOVERY.json (canonical JSON SHA256)\n',encoding='utf8')
    # Only after seal do we compute transport-related quantities. The scan does not tune candidate.
    if c is None:
        transport={'status':'NOT_RUN','reason':'enstrophy_surface_discovery_failed'}
        dynamic=('POSSIBLE_HYPERBOLIC_SEPARATRIX_MANIFOLD_UNRESOLVED'
                 if any(x['hyperbolic_saddle'] for x in stagnant) else 'NO_ENSTROPHY_SURFACE_FOUND_SEPARATRIX_NOT_EXCLUDED')
    else:
        # Derivative computed over the shortest available initial source interval, never
        # from the late-time feature unless only a two-frame source exists.
        td=t1
        if hasattr(flow,'times') and len(flow.times)>1:
            td=min(t1,float(flow.times[1]))
            if not hasattr(flow,'v'):  # analytic, not snapshots: resolve a shorter finite difference
                td=t0+min(t1-t0,(t1-t0)/40.)
        _,sd,_=field_data(flow,axes,td) if td!=t1 else (v1,s1,d1)
        transport=transport_audit(flow,axes,c,s0,s1,t0,t1,scalar_derivative=sd,derivative_dt=td-t0)
        if transport['status']!='MEASURED':dynamic='DYNAMICAL_STATUS_UNRESOLVED'
        else:
            if transport['flux_p95_over_U']<.03 and transport['tracer_cross_fraction']<.03:
                dynamic='MATERIAL_FEATURE_FINITE_TIME_SCREENING'
            elif transport['flux_p95_over_U']>.08 and transport['tracer_cross_fraction']>.07:
                dynamic='PERMEABLE_NONMATERIAL_FEATURE'
            else: dynamic='DYNAMICAL_STATUS_UNRESOLVED'
    # A materially persistent vorticity level set STILL cannot be called an invariant-manifold separatrix without a manifold gate.
    manifold='UNRESOLVED_NOT_CONSTRUCTED'
    is_direct=mode=='SNAPSHOTS'
    temporal_authority=bool(is_direct and hasattr(flow,'times') and len(flow.times)>=3)
    source_gate=('MODEL_NUMERICAL_PERIODIC_EULER_SNAPSHOTS_NOT_INDEPENDENT_PKLSA_DYNAMICS'
                 if mode=='EULER_SIMULATION_MODEL' else
                 ('DIRECT_VELOCITY_SNAPSHOTS_PRESENT_ORIGIN_NOT_INDEPENDENTLY_VERIFIED'
                 if is_direct else 'UNRESOLVED_GEOMETRY_OR_FROZEN_FLOW_ONLY'))
    qualified='UNRESOLVED'
    if c is None:qualified='UNRESOLVED_NO_CLOSED_ENSTROPHY_SURFACE'
    elif transport.get('status')=='MEASURED' and dynamic=='PERMEABLE_NONMATERIAL_FEATURE':
        qualified='CANDIDATE_FALSIFIED_AS_MATERIAL_AT_TESTED_SCALE'
    # Two-part inference: source pass cannot be silently supplied by E011 geometry.
    report={'project':'A064','version':'v0.2.0' if mode=='EULER_SIMULATION_MODEL' else 'v0.1.1','mode':mode,'source':source,'evidence_class':flow.evidence_class,
            'timestamp_rule':'deterministic_no_clock_in_scientific_evidence',
            'framework':'v1.0.7_required_for_official_certification_NOT_RUN_IN_THIS_PROTOTYPE',
            'discovery_sha256':digest,'source_gate':source_gate,'temporal_authority':temporal_authority,
            'divergence_p95_dx_over_U':divergence_rel,'divergence_screen_pass':divergence_rel<0.08,
            'candidate_detected':c is not None,'transport':transport,'dynamical_feature_status':dynamic,
            'true_separatrix_manifold_gate':manifold,'hyperbolic_stagnation_candidates':stagnant,
            'overall_scientific_gate':qualified,
            'interpretation':'No full Euler dynamical stability, invariant-manifold, or cross-provider certification. Static E010/E011 seeds alone do not supply a velocity field.'}
    (out/'GATE_RESULTS.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf8')
    (out/'GATE_RESULTS.md').write_text('\n'.join(['# A064 gate results',f"- Mode: `{mode}`",f"- Evidence: `{flow.evidence_class}`",
           f"- Discovery SHA-256: `{digest}`",f"- Divergence (p95 dx/U): `{divergence_rel:.5g}`",
           f"- Candidate identified: `{bool(c)}`",f"- Feature status: `{dynamic}`",
           f"- True separatrix manifold gate: `{manifold}`",f"- Overall: `{qualified}`",'']),encoding='utf8')
    return report
