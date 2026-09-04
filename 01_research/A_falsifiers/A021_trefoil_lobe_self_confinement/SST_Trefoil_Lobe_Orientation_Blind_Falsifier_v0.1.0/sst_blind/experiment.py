from __future__ import annotations
import json, math, random, time
from pathlib import Path
from typing import Any
import numpy as np
from native_ext.core import load_native, native_info, centerline_split, biot_savart, min_nonlocal_distance
from .io import load_curve, sha256_file
from .geometry import (arclength,resample_closed,detect_lobes,build_lobe_modes,shape_field,
                       apply_mode,nearest_cross_lobe_pair,distance_rate,circle,kabsch_align,normal_component,estimate_tube_thickness)
from .pressure import periodic_pressure_poisson

DEFAULT_CONSTANTS = {
    "v_swirl_m_s": 1.09384563e6,
    "r_c_m": 1.40897017e-15,
    "rho_f_kg_m3": 7.0e-7,
}

def _jsonable(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,(np.floating,np.integer)): return x.item()
    if isinstance(x,complex): return {"re":float(x.real),"im":float(x.imag)}
    if isinstance(x,Path): return str(x)
    if isinstance(x,dict): return {str(k):_jsonable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [_jsonable(v) for v in x]
    return x

def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(_jsonable(data),indent=2,sort_keys=True),encoding='utf-8')

def rms(f): return float(np.sqrt(np.mean(np.sum(np.asarray(f,float)**2,axis=-1))))
def mode_project(modes,field): return np.array([float(np.mean(np.einsum('ij,ij->i',m,field))) for m in modes])
def eig_metrics(J):
    ev=np.linalg.eigvals(np.asarray(J,float)); scale=float(np.max(np.abs(ev))) if len(ev) else 0.0; mr=float(np.max(ev.real)) if len(ev) else 0.0
    return dict(eigenvalues=[{"re":float(z.real),"im":float(z.imag)} for z in ev],spectral_scale=scale,max_real=mr,normalized_growth=mr/max(scale,1e-12))

def split_shape_fields(x,split):
    out={}
    for k,v in split.items(): out[k]=shape_field(x,v)[0]
    return out

def resolve_core_radius(x,cfg):
    est=estimate_tube_thickness(x, stride=int(cfg.get("thickness_stride",2)), dcsc_tangent_tol=float(cfg.get("dcsc_tangent_tol",0.10)), min_separation_fraction=float(cfg.get("thickness_min_separation_fraction",0.08)), curvature_quantile=float(cfg.get("curvature_quantile",0.01)))
    mode=str(cfg.get("core_radius_mode","fixed_normalized"))
    if mode=="thickness_fraction":
        core=float(cfg.get("core_fraction_of_thickness",0.90))*est["thickness"]
    elif mode=="fixed_normalized":
        core=float(cfg["core_radius_norm"])
    else:
        raise ValueError(f"unknown core_radius_mode={mode}")
    if not np.isfinite(core) or core<=0: raise ValueError(f"invalid resolved core radius {core}")
    return core,est

def base_metrics(x,labels,*,gamma,core,local_span,mod):
    split,comp_backend=centerline_split(x,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
    sf=split_shape_fields(x,split); total_rms=rms(split['total']); shape_rms=rms(sf['total'])
    closure=split['local']+split['same_lobe']+split['cross_lobe']+split['transition']-split['total']
    pair=nearest_cross_lobe_pair(x,labels,skip=max(local_span+2,len(x)//12,6)); i,j=pair['i'],pair['j']
    pair_rates={k:distance_rate(x,v,i,j) for k,v in split.items()} if i>=0 else {}
    mnd=min_nonlocal_distance(x,skip=max(local_span+2,len(x)//12,6),mod=mod)
    return dict(
        component_backend=comp_backend,total_velocity_rms=total_rms,shape_velocity_rms=shape_rms,
        shape_velocity_ratio=shape_rms/max(total_rms,1e-30),component_shape_rms={k:rms(v) for k,v in sf.items()},
        split_closure_rel=rms(closure)/max(total_rms,1e-30),nearest_cross_lobe_pair=pair,
        nearest_pair_distance_rates=pair_rates,min_nonlocal_distance=mnd,
    ),split,sf

def reduced_jacobian(x,mode_info,*,eps,gamma,core,local_span,mod):
    modes=mode_info['modes']; labels=mode_info['labels']; M=len(modes); keys=['total','local','same_lobe','cross_lobe','transition']
    J={k:np.zeros((M,M)) for k in keys}; pair_rows=[]
    for b,phi in enumerate(modes):
        xp=apply_mode(x,phi,+eps,target_length=2*np.pi); xm=apply_mode(x,phi,-eps,target_length=2*np.pi)
        sp,_=centerline_split(xp,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
        sm,_=centerline_split(xm,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
        for k in keys:
            dv=(shape_field(xp,sp[k])[0]-shape_field(xm,sm[k])[0])/(2*eps)
            J[k][:,b]=mode_project(modes,dv)
        pp=nearest_cross_lobe_pair(x,labels,skip=max(local_span+2,len(x)//12,6));i,j=pp['i'],pp['j']
        if i>=0:
            pair_rows.append(dict(mode=mode_info['names'][b],plus_total=distance_rate(xp,sp['total'],i,j),minus_total=distance_rate(xm,sm['total'],i,j),plus_cross=distance_rate(xp,sp['cross_lobe'],i,j),minus_cross=distance_rate(xm,sm['cross_lobe'],i,j)))
    metrics={k:eig_metrics(A) for k,A in J.items()}
    metrics['without_cross']=eig_metrics(J['total']-J['cross_lobe'])
    diag={k:{mode_info['names'][i]:float(-J[k][i,i]) for i in range(M)} for k in keys}
    return dict(eps=float(eps),J=J,eigs=metrics,direct_restoring=diag,pair_perturbations=pair_rows)

def jacobian_convergence(jacs):
    if len(jacs)<2:return float('nan')
    mats=[np.asarray(j['J']['total']) for j in jacs]; refs=[]
    for a,b in zip(mats[:-1],mats[1:]): refs.append(float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-12)))
    return float(max(refs)) if refs else float('nan')

def make_scramble(x,mode_info,amp,phase):
    names=mode_info['names']; modes=mode_info['modes']; ids=[i for i,n in enumerate(names) if n.startswith('tilt_')]
    if len(ids)<3:return x.copy()
    f=np.cos(phase)*modes[ids[1]]+np.sin(phase)*modes[ids[2]]
    f/=max(rms(f),1e-30)
    return apply_mode(x,f,amp,target_length=2*np.pi)

def control_metrics(x,*,cfg,gamma,core,mod):
    mi=build_lobe_modes(x); b,_,_=base_metrics(x,mi['labels'],gamma=gamma,core=core,local_span=cfg['local_span'],mod=mod)
    j=reduced_jacobian(x,mi,eps=cfg['control_jacobian_eps'],gamma=gamma,core=core,local_span=cfg['local_span'],mod=mod)
    return dict(base=b,jacobian_summary={k:v for k,v in j['eigs'].items()},names=mi['names'])

def ringdown(base,*,cfg,gamma,core,backend,allow_sycl_cpu,mod):
    n=int(cfg.get('ringdown_n',0)); steps=int(cfg.get('ringdown_steps',0))
    if n<=0 or steps<=0:return None
    ref=resample_closed(base,n,target_length=2*np.pi); mi=build_lobe_modes(ref); names=mi['names']; idx=names.index('tilt_1') if 'tilt_1' in names else 0; phi=mi['modes'][idx]
    amp=float(cfg['ringdown_amp']); x=apply_mode(ref,phi,amp,target_length=2*np.pi); dtmax=float(cfg['ringdown_dt_max']); cfl=float(cfg['ringdown_cfl']); stride=max(1,int(cfg.get('ringdown_stride',10)))
    hist=[]; event=None; t=0.0; backend_used=None
    def vel_shape(y):
        nonlocal backend_used
        v,backend_used=biot_savart(y,y,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
        return shape_field(y,v)[0]
    for step in range(steps+1):
        if step%stride==0 or step==steps:
            al=kabsch_align(ref,x); d=al-ref; q=float(np.mean(np.einsum('ij,ij->i',phi,d))); sr=rms(normal_component(ref,d)); md=min_nonlocal_distance(x,skip=max(cfg['local_span']+2,len(x)//12,6),mod=mod)
            hist.append(dict(step=step,t=t,mode_amplitude=q,shape_rms=sr,min_nonlocal_distance=md['distance']))
            if md['distance'] < float(cfg['core_event_factor'])*core:
                event=dict(step=step,t=t,distance=md['distance'],threshold=float(cfg['core_event_factor'])*core);break
        if step==steps:break
        v1=vel_shape(x); vmax=float(np.max(np.linalg.norm(v1,axis=1))); edge=float(np.mean(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1))); dt=min(dtmax,cfl*edge/max(vmax,1e-12))
        mid=x+0.5*dt*v1; v2=vel_shape(mid); x=x+dt*v2; x=resample_closed(x,n,target_length=None,center=True); t+=dt
    initial=abs(hist[0]['mode_amplitude']) if hist else float('nan'); final=abs(hist[-1]['mode_amplitude']) if hist else float('nan'); mx=max(abs(h['mode_amplitude']) for h in hist) if hist else float('nan')
    return dict(mode=names[idx],backend=backend_used,history=hist,core_event=event,initial_abs_amplitude=initial,final_abs_amplitude=final,max_abs_amplitude=mx,final_over_initial=final/max(initial,1e-12),max_over_initial=mx/max(initial,1e-12))

def pressure_metrics(base,mode_info,*,cfg,gamma,core,backend,allow_sycl_cpu,mod):
    N=int(cfg.get('pressure_grid_n',0));
    if N<=0:return None
    p=periodic_pressure_poisson(base,core=core,gamma=gamma,grid_n=N,padding=float(cfg.get('pressure_padding',1.0)),backend=backend,mod=mod,allow_sycl_cpu=allow_sycl_cpu)
    acc=shape_field(base,p.pop('pressure_accel'))[0]; p['mode_projection']=dict(zip(mode_info['names'],mode_project(mode_info['modes'],acc).tolist()));p['accel_shape_rms']=rms(acc);return p

def dataset_analysis(blind_id,curve,*,cfg,backend,allow_sycl_cpu,mod):
    x=resample_closed(curve,int(cfg['n_points']),target_length=2*np.pi); peaks,labels,_=detect_lobes(x); mi=build_lobe_modes(x,peaks,labels)
    core,thickness=resolve_core_radius(x,cfg)
    base,split,sf=base_metrics(x,labels,gamma=1.0,core=core,local_span=cfg['local_span'],mod=mod)
    jacs=[reduced_jacobian(x,mi,eps=e,gamma=1.0,core=core,local_span=cfg['local_span'],mod=mod) for e in cfg['eps_values']]
    conv=jacobian_convergence(jacs); mid=jacs[len(jacs)//2]; controls=[]
    rng=np.random.default_rng(int(cfg['blind_seed'])+sum(map(ord,blind_id)))
    for k in range(int(cfg['n_scrambled_controls'])):
        phase=float(rng.uniform(0,2*np.pi)); xc=make_scramble(x,mi,float(cfg['scramble_amp']),phase); cm=control_metrics(xc,cfg=cfg,gamma=1.0,core=core,mod=mod);cm['phase']=phase;controls.append(cm)
    rd=ringdown(x,cfg=cfg,gamma=1.0,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    pm=pressure_metrics(x,mi,cfg=cfg,gamma=1.0,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    return dict(blind_id=blind_id,n_points=len(x),arclength=arclength(x),core_radius_norm=core,thickness_estimate=thickness,lobe_peaks=peaks.tolist(),mode_names=mi['names'],base=base,jacobians=jacs,jacobian_convergence=conv,controls=controls,ringdown=rd,pressure_poisson=pm,geometry=x,modes=mi['modes'],labels=labels)

def score_dataset(res,cfg):
    base=res['base']; j=res['jacobians'][len(res['jacobians'])//2]; et=j['eigs']['total']; ew=j['eigs']['without_cross']; cross=j['J']['cross_lobe']; total=j['J']['total']; names=res['mode_names']; tilt=[i for i,n in enumerate(names) if n.startswith('tilt_')]
    cross_pair=float(base['nearest_pair_distance_rates'].get('cross_lobe',float('nan')))
    cross_frac=float(np.linalg.norm(cross)/max(np.linalg.norm(total),1e-12)); improvement=float(ew['max_real']-et['max_real'])/max(et['spectral_scale'],ew['spectral_scale'],1e-12)
    direct_cross=[float(-cross[i,i]) for i in tilt]; direct_total=[float(-total[i,i]) for i in tilt]
    ctrl_growth=[c['jacobian_summary']['total']['normalized_growth'] for c in res['controls']]; ctrl_shape=[c['base']['shape_velocity_ratio'] for c in res['controls']]
    ctrl_specificity=(float(np.median(ctrl_growth))-et['normalized_growth']) if ctrl_growth else float('nan')
    core=float(res['core_radius_norm']); thickness=float(res['thickness_estimate']['thickness']); core_clear=thickness/core
    gates={
      'G0_numerical_sanity': bool(base['split_closure_rel']<=cfg['split_closure_max'] and core_clear>=cfg['min_thickness_over_core']),
      'G1_relative_equilibrium': bool(base['shape_velocity_ratio']<=cfg['base_shape_ratio_max']),
      'G2_reduced_stability': bool(et['normalized_growth']<=cfg['normalized_growth_max'] and res['jacobian_convergence']<=cfg['jacobian_convergence_max']),
      'G3_cross_lobe_stabilizes': bool(cross_frac>=cfg['cross_jacobian_fraction_min'] and improvement>=cfg['cross_growth_improvement_min']),
      'G4_nearest_pair_cross_separates': bool(np.isfinite(cross_pair) and cross_pair>cfg['cross_pair_rate_min']),
      'G5_orientation_specificity': bool(np.isfinite(ctrl_specificity) and ctrl_specificity>=cfg['control_growth_delta_min']),
      'G6_ringdown_bounded': bool(res['ringdown'] is not None and res['ringdown']['core_event'] is None and res['ringdown']['max_over_initial']<=cfg['ringdown_max_over_initial']),
    }
    critical=['G0_numerical_sanity','G2_reduced_stability','G3_cross_lobe_stabilizes','G4_nearest_pair_cross_separates','G6_ringdown_bounded']
    status='PASS' if all(gates[k] for k in critical) else 'FAIL'
    if (not gates['G0_numerical_sanity']) or res['jacobian_convergence']>2*cfg['jacobian_convergence_max']: status='INCONCLUSIVE'
    return dict(status=status,gates=gates,metrics=dict(core_clearance_radii=core_clear,shape_velocity_ratio=base['shape_velocity_ratio'],normalized_growth=et['normalized_growth'],cross_jacobian_fraction=cross_frac,cross_growth_improvement=improvement,nearest_pair_cross_rate=cross_pair,direct_cross_restoring_tilt=direct_cross,direct_total_restoring_tilt=direct_total,control_growth_delta=ctrl_specificity,jacobian_convergence=res['jacobian_convergence']))

def circle_null(cfg,mod,core):
    x=circle(int(cfg['n_points'])); labels=np.zeros(len(x),np.int32); split,_=centerline_split(x,labels,gamma=1.0,core=core,local_span=cfg['local_span'],mod=mod); v=split['total']; radial=x.copy();radial[:,2]=0;radial/=np.linalg.norm(radial,axis=1)[:,None]; radial_rate=float(np.mean(np.einsum('ij,ij->i',v,radial))); sf=shape_field(x,v)[0]
    return dict(radial_velocity_mean=radial_rate,total_velocity_rms=rms(v),shape_velocity_rms=rms(sf),shape_velocity_ratio=rms(sf)/max(rms(v),1e-30),pass_null=bool(abs(radial_rate)<=cfg['circle_radial_rate_max']))

def physical_scales(cfg,a):
    c={**DEFAULT_CONSTANTS,**cfg.get('constants',{})}; a=float(a); rc=c['r_c_m']; vs=c['v_swirl_m_s']; Gamma=2*np.pi*rc*vs; ell=rc/a; t0=ell*ell/Gamma; v0=Gamma/ell; p0=c['rho_f_kg_m3']*v0*v0
    return dict(Gamma_SST_m2_s=Gamma,length_scale_m=ell,time_scale_s=t0,velocity_scale_m_s=v0,pressure_scale_Pa=p0,normalized_core=a,physical_core_m=rc,normalized_total_length=2*np.pi,physical_total_length_m=2*np.pi*ell)

def run_campaign(*,fseries_path,knotplot_path,config,out_dir,backend='auto',allow_sycl_cpu=False,force_build=False,build_verbose=False):
    cfg=json.loads(Path(config).read_text(encoding='utf-8')) if isinstance(config,(str,Path)) else dict(config); out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    write_json(out/'00_preregistered_config.json',cfg); inputs=[('fremlin_fseries','fseries',Path(fseries_path)),('knotplot_final','knotplot',Path(knotplot_path))]
    for _,_,p in inputs:
        if not p.exists(): raise FileNotFoundError(p)
    manifest=[dict(source=s,kind=k,path=str(p),sha256=sha256_file(p)) for s,k,p in inputs]
    rng=random.Random(int(cfg['blind_seed'])); order=list(range(len(inputs)));rng.shuffle(order); blind={order[i]:f"B{i+1:02d}" for i in range(len(order))}
    # Mapping is kept outside pre_unblind until scoring has completed.
    write_json(out/'blind_input_hashes.json',[{'blind_id':blind[i],'sha256':manifest[i]['sha256']} for i in range(len(inputs))])
    mod=load_native(force_build=force_build,build_verbose=build_verbose); info=native_info(mod); write_json(out/'backend_info.json',info)
    curves={}
    for idx,(source,kind,p) in enumerate(inputs): curves[blind[idx]]=load_curve(p,kind,n_raw=int(cfg.get('fseries_raw_samples',4096)))
    pre=out/'pre_unblind';pre.mkdir(exist_ok=True); results={};scores={}; t0=time.time()
    for bid in sorted(curves):
        r=dataset_analysis(bid,curves[bid],cfg=cfg,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod);results[bid]=r;scores[bid]=score_dataset(r,cfg)
        compact={k:v for k,v in r.items() if k not in ('geometry','modes','labels')};write_json(pre/f'{bid}_analysis.json',compact);write_json(pre/f'{bid}_score.json',scores[bid])
        np.savez_compressed(pre/f'{bid}_arrays.npz',geometry=r['geometry'],modes=r['modes'],labels=r['labels'],**{f"J_total_eps{i}":j['J']['total'] for i,j in enumerate(r['jacobians'])},**{f"J_cross_eps{i}":j['J']['cross_lobe'] for i,j in enumerate(r['jacobians'])})
    nulls={b:circle_null(cfg,mod,results[b]['core_radius_norm']) for b in sorted(results)};write_json(pre/'circle_nulls.json',nulls)
    critical_status=[scores[b]['status'] for b in sorted(scores)]; null_ok=all(z['pass_null'] for z in nulls.values())
    if all(s=='PASS' for s in critical_status) and null_ok: overall='PASS'
    elif any(s=='INCONCLUSIVE' for s in critical_status) or not null_ok: overall='INCONCLUSIVE'
    else: overall='FAIL'
    blind_verdict=dict(hypothesis='Tilted trefoil lobes generate orientation-dependent non-local Biot-Savart response that stabilizes the reduced deformation dynamics.',overall=overall,blind_scores=scores,circle_nulls=nulls,physical_scales={b:physical_scales(cfg,results[b]['core_radius_norm']) for b in results},runtime_s=time.time()-t0)
    write_json(pre/'blind_verdict.json',blind_verdict)
    mapping={blind[i]:manifest[i] for i in range(len(inputs))};write_json(out/'unblind_manifest.json',mapping)
    unblinded={mapping[b]['source']:scores[b] for b in scores}; final=dict(**blind_verdict,unblinded_scores=unblinded,blind_to_source={b:mapping[b]['source'] for b in mapping});write_json(out/'final_verdict.json',final)
    return final,results,mapping
