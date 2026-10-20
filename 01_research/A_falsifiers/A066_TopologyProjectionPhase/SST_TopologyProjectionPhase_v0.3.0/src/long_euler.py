"""Longer 3D periodic ideal-Euler comparative numerical campaign.

All lengths/times are nondimensional. No native hardware qualification or SST
calibrated core constitutive law is asserted. The evolved material curves are
passive tracers, NOT extracted time-dependent vorticity-ridge centerlines.
"""
from __future__ import annotations
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from .library_census import catalog, resample
from .euler_pilot import EulerBox, tube_omega
from .topology3d import knot_signature,gauss_link,min_curve_distance,min_nonlocal_self_distance
ROOT=Path(__file__).resolve().parents[1]

def normalize_curves(curves):
    curves=[np.asarray(x,dtype=float) for x in curves]
    p=np.concatenate(curves)
    mid=p.mean(axis=0)
    scale=1.72/max(np.max(abs(p-mid)),1e-12)
    return [(x-mid)*scale+np.pi for x in curves],dict(translation=mid.tolist(),scale=scale,box='[0,2pi)^3')

def ring_local(curve,radius,nring=32):
    p=curve[0];tangent=curve[1]-curve[-1];tangent/=np.linalg.norm(tangent)
    seed=np.eye(3)[np.argmin(np.abs(tangent))]
    e1=np.cross(tangent,seed);e1/=np.linalg.norm(e1);e2=np.cross(tangent,e1)
    th=np.arange(nring)*2*np.pi/nring
    return p+radius*(np.cos(th[:,None])*e1+np.sin(th[:,None])*e2)

def loop_circulation(box,uh,curve):
    # Circulation of a MATERIAL contour using trilinearly interpolated u.
    # Center-of-cell interpolation is not a high-order Kelvin diagnostic.
    u=box.sample(box.ifft(uh),curve)
    delta=np.roll(curve,-1,axis=0)-curve
    return float(np.sum(np.sum(0.5*(u+np.roll(u,-1,axis=0))*delta,axis=-1)))

def topology_checkpoint(curves):
    marks=[]
    for c in curves:
        # Consistent arclength-resampled diagnostic to prevent artificial
        # N-dependent knot determinant changes from raw polygon density.
        sub=resample(c,96)
        k=knot_signature(sub)
        mind=min_nonlocal_self_distance(sub,exclusion=3)
        marks.append({'alexander_det_m1':k['alexander_det_at_minus_one'],'status':k['status'],
                      'min_nonlocal_self_gap':mind})
    links=[]
    for i in range(len(curves)):
        for j in range(i+1,len(curves)):
            a=resample(curves[i],96);b=resample(curves[j],96)
            lk3=gauss_link(a,b,3);lk5=gauss_link(a,b,5);mind=min_curve_distance(a,b)
            links.append({'a':i,'b':j,'lk_q3':lk3,'lk_q5':lk5,'qualified_int':round(lk5) if mind>1e-6 and abs(lk5-round(lk5))<.075 and abs(lk5-lk3)<.075 else None,'min_gap':mind})
    return {'components':marks,'links':links}

def run(curves,*,name,grid=24,steps=72,duration=2.4,sigma=.5,ring_radius=.42,output=None,source_sha256=None):
    t0=time.perf_counter();p,trans=normalize_curves(curves)
    B=EulerBox(grid)
    if sigma<=0 or duration<=0 or steps<4:raise ValueError('invalid experiment controls')
    dt=duration/steps
    omega=np.zeros((grid,grid,grid,3))
    for c in p:omega+=tube_omega(B,c,sigma)
    u=B.velocity_from_vorticity(omega);uh=B.project(B.fft(u))
    u_max=float(np.linalg.norm(u,axis=-1).max())
    dt_cfl=.1*B.h/u_max
    if dt>dt_cfl:raise ValueError(f'dt {dt:.4g} exceeds registered .1 dx/Umax CFL cap {dt_cfl:.4g}')
    lengths=[len(x) for x in p]
    material=np.concatenate(p)
    rings=[ring_local(c,ring_radius) for c in p]
    rlength=[len(q) for q in rings]
    points=np.concatenate([material,*rings]);markers=len(material)
    idx=np.cumsum([0]+lengths)
    ring_idx=np.cumsum([markers]+rlength)
    chk_steps=sorted(set([0,steps//4,steps//2,3*steps//4,steps]))
    snapshots=[];track_dict={}
    energy0=None;hel0=None; circ0=None
    for k in range(steps+1):
        if k in chk_steps:
            uf=B.ifft(uh);wf=B.curl(uh)
            energy=float(.5*np.mean(np.sum(uf*uf,axis=-1)))
            hel=float(np.mean(np.sum(uf*wf,axis=-1)))
            rmsw=float(np.sqrt(np.mean(np.sum(wf*wf,axis=-1))))
            div=float(np.max(np.abs(B.K[...,0]*uh[...,0]+B.K[...,1]*uh[...,1]+B.K[...,2]*uh[...,2])))
            curn=[points[idx[i]:idx[i+1]].copy() for i in range(len(p))]
            rng=[points[ring_idx[i]:ring_idx[i+1]] for i in range(len(p))]
            circulation=[loop_circulation(B,uh,x) for x in rng]
            topology=topology_checkpoint(curn)
            alignment=[]
            for component in curn:
                tang=np.roll(component,-1,axis=0)-np.roll(component,1,axis=0)
                wn=B.sample(wf,component)
                good=(np.linalg.norm(wn,axis=1)>1e-12)&(np.linalg.norm(tang,axis=1)>1e-12)
                if good.any():
                    cos=np.abs(np.sum(wn[good]*tang[good],axis=1)/(np.linalg.norm(wn[good],axis=1)*np.linalg.norm(tang[good],axis=1)))
                    alignment.append({'mean_abs_cos':float(cos.mean()),'p10_abs_cos':float(np.quantile(cos,.1)),'n':int(good.sum())})
                else:alignment.append({'mean_abs_cos':None,'p10_abs_cos':None,'n':0})
            if energy0 is None:energy0=energy;hel0=hel;circ0=circulation
            drift_c=[(v-v0)/max(abs(v0),1e-14) for v,v0 in zip(circulation,circ0)]
            hit_boundary=any((x.min()<.02 or x.max()>(2*np.pi-.02)) for x in curn)
            snapshots.append(dict(step=k,t_model=k*dt,energy=energy,helicity=hel,enstrophy_rms=rmsw,
                div_fourier_max=div,kelvin_material_circulation=circulation,kelvin_relative_drift=drift_c,
                topology=topology,vorticity_tangent_alignment=alignment,periodic_boundary_marker_risk=hit_boundary))
            for j,curve in enumerate(curn):track_dict[f'component_{j}_step_{k}']=curve
        if k<steps:uh,points=B.step(uh,points,dt)
    final=snapshots[-1];begin=snapshots[0]
    dE=(final['energy']-energy0)/energy0
    dH=(final['helicity']-hel0)/max(abs(hel0),1e-12)
    invariants_stable=all(
        s['topology']['components'][j]['alexander_det_m1']==begin['topology']['components'][j]['alexander_det_m1']
        and s['topology']['components'][j]['status']=='QUALIFIED'
        for s in snapshots for j in range(len(p)))
    if len(p)>1:
        invariants_stable=invariants_stable and all(
            s['topology']['links'][j]['qualified_int']==begin['topology']['links'][j]['qualified_int']
            and s['topology']['links'][j]['qualified_int'] is not None
            for s in snapshots for j in range(len(begin['topology']['links'])))
    cmax=max(abs(d) for s in snapshots for d in s['kelvin_relative_drift'])
    result=dict(name=name,source_sha256=source_sha256,provider_description='See source registry',
        grid=grid,steps=steps,dt_model=dt,duration_model=duration,sigma_model=sigma,
        sigma_over_dx=sigma/B.h,initial_velocity_max=u_max,core_advective_time_units=duration*u_max/sigma,
        cfl_ratio=dt/dt_cfl,max_energy_relative_drift=abs(dE),max_helicity_relative_drift=abs(dH),
        max_kelvin_loop_relative_drift=cmax,initial_kelvin_circulation=circ0,initial_vorticity_tangent_alignment=begin['vorticity_tangent_alignment'],final_vorticity_tangent_alignment=final['vorticity_tangent_alignment'],topology_unchanged_screen=invariants_stable,
        initial_knot_dets=[x['alexander_det_m1'] for x in begin['topology']['components']],
        final_knot_dets=[x['alexander_det_m1'] for x in final['topology']['components']],
        initial_linking=[x['qualified_int'] for x in begin['topology']['links']],
        final_linking=[x['qualified_int'] for x in final['topology']['links']],
        periodic_boundary_risk=any(x['periodic_boundary_marker_risk'] for x in snapshots),
        snapshots=snapshots,geometry_normalization=trans,elapsed_wall_seconds=time.perf_counter()-t0,
        method='Projected Euler RK4 2/3 dealiased periodic, gaussian deposited curl and passive material markers',
        physical_status='EXPLORATORY_NUMERICAL_SCREEN_ONLY',
        warning='Passive curves are not automatically exact vortex centerlines. Finite core uncalibrated; trilinear material loop interpolation biases Kelvin drift. Diagnostic topological determinant incomplete. Periodic Euler cannot model physical reconnection of smooth vortex tubes.'
    )
    if output:
        out=Path(output);out.mkdir(parents=True,exist_ok=True)
        tag=name.replace('/','_')+f'_N{grid}_S{steps}_T{duration:g}_SG{sigma:g}'
        (out/(tag+'.json')).write_text(json.dumps(result,indent=2))
        np.savez_compressed(out/(tag+'.npz'),**track_dict)
    return result

def selected_cases(root=ROOT):
    by_id={x['id']:x for x in catalog(root)}
    names=['KP_3_1_N300','FS_knot_3_1','FS_knot_4_1','FS_knot_7_1','IL_L4a1']
    return {n:by_id[n] for n in names}

def campaign(root=ROOT,selected=None,quick=False):
    cases=selected_cases(root)
    if selected:cases={k:v for k,v in cases.items() if k in selected}
    out=root/'results/EULER_LONG'
    manifests=[]
    settings=([ (24,48,1.2,.5),(32,64,1.2,.5) ] if quick else [
        (24,72,2.4,.5),(32,96,2.4,.5),(40,120,2.4,.5)])
    for name,it in cases.items():
        if not it['curves']:continue
        for grid,steps,duration,sigma in settings:
            print('RUN',name,grid,steps,duration,flush=True)
            try:
                r=run(it['curves'],name=name,grid=grid,steps=steps,duration=duration,sigma=sigma,output=out,source_sha256=it['sha256'])
                manifests.append({k:r[k] for k in ['name','grid','steps','duration_model','sigma_model','cfl_ratio','initial_velocity_max','core_advective_time_units','max_energy_relative_drift','max_helicity_relative_drift','max_kelvin_loop_relative_drift','topology_unchanged_screen','initial_knot_dets','final_knot_dets','initial_linking','final_linking','periodic_boundary_risk','elapsed_wall_seconds','physical_status']})
                print('DONE',name,grid,'dE',r['max_energy_relative_drift'],'dGamma',r['max_kelvin_loop_relative_drift'],flush=True)
            except Exception as exc:
                manifests.append(dict(name=name,grid=grid,steps=steps,status='UNRESOLVED_RUN_ERROR',reason=str(exc)))
                print('ERROR',name,grid,exc,flush=True)
    if not quick and 'KP_3_1_N300' in cases:
        it=cases['KP_3_1_N300']
        for grid,steps,duration,sigma in [(32,192,2.4,.5),(32,96,2.4,.4),(32,96,2.4,.6)]:
            print('REFINEMENT',grid,steps,sigma,flush=True)
            try:
                r=run(it['curves'],name='KP_3_1_N300',grid=grid,steps=steps,duration=duration,sigma=sigma,output=out,source_sha256=it['sha256'])
                manifests.append({k:r[k] for k in ['name','grid','steps','duration_model','sigma_model','cfl_ratio','initial_velocity_max','core_advective_time_units','max_energy_relative_drift','max_helicity_relative_drift','max_kelvin_loop_relative_drift','topology_unchanged_screen','initial_knot_dets','final_knot_dets','initial_linking','final_linking','periodic_boundary_risk','elapsed_wall_seconds','physical_status']})
                print('DONE REFINE',grid,steps,sigma,flush=True)
            except Exception as exc:
                manifests.append(dict(name='KP_3_1_N300',grid=grid,steps=steps,status='UNRESOLVED_RUN_ERROR',reason=str(exc)))
    (root/'results/EULER_CAMPAIGN_SUMMARY.json').write_text(json.dumps(manifests,indent=2))
    return manifests

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--quick',action='store_true');p.add_argument('--case',action='append');a=p.parse_args()
    print(json.dumps(campaign(selected=a.case,quick=a.quick),indent=2))
