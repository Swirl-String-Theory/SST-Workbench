from __future__ import annotations
import json, math, time
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from .knot_io import load_geometry, resample_closed, concatenate_segments, list_knot_files
from .native import biot_savart_velocity, backend_status

@dataclass
class GeometryCase:
    file: str
    component_count: int
    source_vertices: int
    resample_points_per_component: int
    stations: int
    samples: int
    thickness_geom: float
    core_ratio: float
    sample_radius_factor: float
    source_residual: float | None
    source_edge_ratio: float | None
    source_ropelength: float | None
    backend: str
    elapsed_s: float
    v_unit_ref: float
    gamma_calibration: float
    median_C_blind: float
    median_delta_pa: float
    median_axisymmetry_residual: float
    median_director_alignment: float
    positive_anisotropy_fraction: float
    angular_momentum_x: float
    angular_momentum_y: float
    angular_momentum_z: float
    angular_momentum_norm: float
    kinetic_energy_j: float


def _unit(v):
    n=np.linalg.norm(v,axis=-1,keepdims=True)
    return v/np.maximum(n,np.finfo(float).tiny)

def _frames(c):
    t=_unit(np.roll(c,-1,axis=0)-np.roll(c,1,axis=0))
    n1=np.empty_like(t); n2=np.empty_like(t)
    axes=np.eye(3)
    for i,ti in enumerate(t):
        ref=axes[int(np.argmin(np.abs(ti)))]
        q=np.cross(ti,ref); q=q/max(np.linalg.norm(q),np.finfo(float).tiny)
        n1[i]=q; n2[i]=np.cross(ti,q)
    return t,n1,n2

def _sample_tube(components, stations_per_component:int, radial_samples:int, angular_samples:int, rmax:float, rref:float):
    pts=[]; tangents=[]; centers=[]; station_ids=[]; ds_geom=[]
    ref_pts=[]; ref_phi=[]; ref_ids=[]
    sid=0; cross_n=radial_samples*angular_samples
    for c in components:
        t,n1,n2=_frames(c)
        idx=np.floor(np.arange(stations_per_component)*len(c)/stations_per_component).astype(int)
        q=np.vstack([c,c[0]])
        length=float(np.sum(np.linalg.norm(np.diff(q,axis=0),axis=1)))
        dsi=length/stations_per_component
        for ii in idx:
            radii=rmax*np.sqrt((np.arange(radial_samples)+0.5)/radial_samples)
            angles=2*np.pi*(np.arange(angular_samples)+0.5)/angular_samples
            for r in radii:
                for a in angles:
                    er=math.cos(a)*n1[ii]+math.sin(a)*n2[ii]
                    p=c[ii]+r*er
                    pts.append(p); tangents.append(t[ii]); centers.append(c[ii]); station_ids.append(sid); ds_geom.append(dsi)
            # Independent characteristic-swirl calibration annulus.
            for a in angles:
                er=math.cos(a)*n1[ii]+math.sin(a)*n2[ii]
                ephi=np.cross(t[ii],er)
                ref_pts.append(c[ii]+rref*er); ref_phi.append(ephi); ref_ids.append(sid)
            sid+=1
    return (np.ascontiguousarray(pts,float),np.ascontiguousarray(tangents,float),np.ascontiguousarray(centers,float),
            np.asarray(station_ids,int),np.asarray(ds_geom,float),sid,cross_n,
            np.ascontiguousarray(ref_pts,float),np.ascontiguousarray(ref_phi,float),np.asarray(ref_ids,int))

def _station_stats(u, tangents, station_ids, u_ref, phi_ref, ref_ids, rho, v_swirl, station_count):
    # v_ref is fixed by a separate annulus at a preregistered radius, not by the
    # stress covariance itself. This avoids a tautological C_blind normalization.
    vals=[]
    for sid in range(station_count):
        m=ref_ids==sid
        signed=np.sum(u_ref[m]*phi_ref[m],axis=1)
        vals.append(abs(float(np.mean(signed))))
    v_unit_ref=float(np.median(vals))
    gamma_scale=float(v_swirl/v_unit_ref) if v_unit_ref>0 else float('nan')
    u_si=u*gamma_scale
    station=[]
    for sid in range(station_count):
        m=station_ids==sid; us=u_si[m]; t=np.mean(tangents[m],axis=0); t=t/max(np.linalg.norm(t),np.finfo(float).tiny)
        up=us-np.mean(us,axis=0)
        R=rho*(up.T@up)/len(up)
        ppar=float(t@R@t); tr=float(np.trace(R)); pperp=0.5*(tr-ppar); delta=pperp-ppar
        model=pperp*np.eye(3)+(ppar-pperp)*np.outer(t,t)
        resid=float(np.linalg.norm(R-model)/max(np.linalg.norm(R),np.finfo(float).tiny))
        vals_e,vecs=np.linalg.eigh(R); align=float(abs(vecs[:,0]@t))
        station.append((delta,resid,align,ppar,pperp))
    return gamma_scale,u_si,station,v_unit_ref

def analyze_geometry(path:Path,cfg:dict,*,resample_n:int|None=None,core_ratio:float=1.0,threads:int=0,force_python=False,force_build=False,mirror=False):
    g=load_geometry(path); geom=cfg['geometry']; phys=cfg['physical_constants']
    n=int(resample_n or geom['resample_points_per_component'])
    comps=[resample_closed(c,n) for c in g.components]
    if mirror:
        M=np.diag([-1.0,1.0,1.0]); comps=[c@M.T for c in comps]
    thickness=float(g.metrics.get('thickness',geom.get('fallback_thickness_geom',0.5)))
    rmax=float(geom['sample_radius_factor'])*thickness
    rref=float(geom.get('vref_radius_factor',1.0))*thickness
    samples,tangents,centers,station_ids,ds_geom,station_count,cross_n,ref_samples,ref_phi,ref_ids=_sample_tube(
        comps,int(geom['stations_per_component']),int(geom['radial_samples']),int(geom['angular_samples']),rmax,rref)
    a,b=concatenate_segments(comps)
    all_samples=np.ascontiguousarray(np.vstack([samples,ref_samples]),float)
    all_u,binfo=biot_savart_velocity(all_samples,a,b,1.0,float(core_ratio)*thickness,threads=threads,force_python=force_python,force_build=force_build,verbose=False)
    u_unit=all_u[:len(samples)]; u_ref=all_u[len(samples):]
    rho=float(phys['rho_f_kg_m3']); v_swirl=float(phys['v_swirl_m_s']); rc=float(phys['r_c_m'])
    gamma_scale,u_si,st,v_unit_ref=_station_stats(u_unit,tangents,station_ids,u_ref,ref_phi,ref_ids,rho,v_swirl,station_count)
    deltas=np.asarray([x[0] for x in st]); residuals=np.asarray([x[1] for x in st]); aligns=np.asarray([x[2] for x in st])
    median_delta=float(np.median(deltas)); C=float(median_delta/(rho*v_swirl*v_swirl))
    # Approximate tube-volume integrals, used as diagnostics/guards only.
    scale=rc/thickness
    centroid=np.mean(np.vstack(comps),axis=0)
    Rphys=rmax*scale; dA=math.pi*Rphys*Rphys/cross_n
    dV=dA*(ds_geom*scale)
    rphys=(samples-centroid)*scale
    L=rho*np.sum(np.cross(rphys,u_si)*dV[:,None],axis=0)
    E=0.5*rho*float(np.sum(np.sum(u_si*u_si,axis=1)*dV))
    return GeometryCase(
        file=path.name,component_count=len(comps),source_vertices=int(sum(len(c) for c in g.components)),resample_points_per_component=n,
        stations=station_count,samples=len(samples),thickness_geom=thickness,core_ratio=float(core_ratio),sample_radius_factor=float(geom['sample_radius_factor']),
        source_residual=float(g.metrics['residual']) if 'residual' in g.metrics else None,
        source_edge_ratio=float(g.metrics['edge_length_ratio']) if 'edge_length_ratio' in g.metrics else None,
        source_ropelength=float(g.metrics['ropelength']) if 'ropelength' in g.metrics else None,
        backend=binfo['backend'],elapsed_s=float(binfo['elapsed_s']),v_unit_ref=float(v_unit_ref),gamma_calibration=float(gamma_scale),
        median_C_blind=C,median_delta_pa=median_delta,median_axisymmetry_residual=float(np.median(residuals)),median_director_alignment=float(np.median(aligns)),
        positive_anisotropy_fraction=float(np.mean(deltas>0)),angular_momentum_x=float(L[0]),angular_momentum_y=float(L[1]),angular_momentum_z=float(L[2]),
        angular_momentum_norm=float(np.linalg.norm(L)),kinetic_energy_j=E)

def _rel(a,b): return abs(a-b)/max(abs(a),abs(b),np.finfo(float).tiny)

def _status(gates):
    return 'FAIL' if any(x['status']=='FAIL' for x in gates) else ('INCONCLUSIVE' if any(x['status']=='INCONCLUSIVE' for x in gates) else 'PASS')

def evaluate_base(cases,cfg,input_qa=None):
    gates=[]; q=cfg['gates']; qq=q['source_quality']; gs=q['stress_structure']
    def add(name,value,ok,crit): gates.append({'name':name,'value':value,'criterion':crit,'status':'PASS' if ok else 'FAIL'})
    if input_qa is not None:
        add('input.accepted_file_count',input_qa['accepted_count'],input_qa['accepted_count']>=qq.get('min_accepted_files',1),f">= {qq.get('min_accepted_files',1)}")
        add('input.multicomponent_accepted',input_qa['accepted_multicomponent'],input_qa['accepted_multicomponent']>=qq.get('min_multicomponent_accepted',0),f">= {qq.get('min_multicomponent_accepted',0)}")
    med_res=float(np.median([x.median_axisymmetry_residual for x in cases])); med_align=float(np.median([x.median_director_alignment for x in cases])); pos=float(np.mean([x.positive_anisotropy_fraction for x in cases]))
    if gs.get('axisymmetry_role','gate')=='diagnostic':
        gates.append({'name':'stress.axisymmetry','value':med_res,'criterion':f"diagnostic target <= {gs['median_axisymmetry_residual_max']}",'status':'DIAGNOSTIC','meets_target':med_res<=gs['median_axisymmetry_residual_max']})
    else:
        add('stress.axisymmetry',med_res,med_res<=gs['median_axisymmetry_residual_max'],f"<= {gs['median_axisymmetry_residual_max']}")
    add('stress.director_alignment',med_align,med_align>=gs['median_director_alignment_min'],f">= {gs['median_director_alignment_min']}")
    add('stress.positive_anisotropy',pos,pos>=gs['positive_anisotropy_fraction_min'],f">= {gs['positive_anisotropy_fraction_min']}")
    return {'status':_status(gates),'input_qa':input_qa,'metrics':{'median_C_blind':float(np.median([x.median_C_blind for x in cases])),'C_blind_cv':float(np.std([x.median_C_blind for x in cases],ddof=1)/max(abs(np.mean([x.median_C_blind for x in cases])),1e-300)) if len(cases)>1 else 0.0,'median_axisymmetry_residual':med_res,'median_director_alignment':med_align,'positive_anisotropy_fraction':pos},'gates':gates}

def run_geometry(knots_dir:Path,outdir:Path,cfg:dict,threads=0,force_python=False,force_build=False):
    outdir.mkdir(parents=True,exist_ok=True)
    files=list_knot_files(knots_dir,cfg)
    if not files: raise ValueError(f'no knot/link files selected under {knots_dir}')
    qq=cfg['gates']['source_quality']; accepted=[]; rejected=[]
    for p in files:
        gg=load_geometry(p); m=gg.metrics
        residual=m.get('residual'); edge=m.get('edge_length_ratio')
        ok=(residual is not None and edge is not None and float(residual)<=qq['residual_max'] and float(edge)<=qq['edge_length_ratio_max'])
        row={'file':p.name,'accepted':ok,'residual':residual,'edge_length_ratio':edge,'component_count':len(gg.components)}
        (accepted if ok else rejected).append((p,row))
    input_qa={'selected_count':len(files),'accepted_count':len(accepted),'rejected_count':len(rejected),'accepted_multicomponent':sum(1 for p,r in accepted if r['component_count']>1),'eligibility':{'residual_max':qq['residual_max'],'edge_length_ratio_max':qq['edge_length_ratio_max']},'rejected':[r for p,r in rejected]}
    files=[p for p,r in accepted]
    if not files: raise ValueError('all selected geometries failed preregistered source-quality eligibility')
    native=backend_status(force_build=force_build,verbose=False)
    if cfg.get('runtime',{}).get('require_native',False) and not native.get('native_available') and not force_python:
        raise RuntimeError('profile requires C++ backend; run run_00_install.cmd and ensure MSVC C++ Build Tools are installed')
    base=[]; t0=time.perf_counter()
    for i,p in enumerate(files,1):
        print(f"[3_MAXWELL] base {i}/{len(files)} {p.name}",flush=True)
        base.append(analyze_geometry(p,cfg,threads=threads,force_python=force_python,force_build=False))
    verdict=evaluate_base(base,cfg,input_qa=input_qa)
    anchors=[knots_dir/x for x in cfg.get('robustness',{}).get('anchor_files',[]) if (knots_dir/x).exists()]
    robust={'core_sweep':[],'convergence':[],'parity':[],'gates':[]}
    rq=cfg['gates']['robustness']
    # Core regularization robustness, target-independent and predeclared.
    ratios=cfg.get('robustness',{}).get('core_ratios',[1.0])
    for p in anchors:
        vals=[]
        for cr in ratios:
            if float(cr)==1.0:
                c=next((x for x in base if x.file==p.name),None) or analyze_geometry(p,cfg,core_ratio=1.0,threads=threads,force_python=force_python)
            else: c=analyze_geometry(p,cfg,core_ratio=float(cr),threads=threads,force_python=force_python)
            vals.append(c); robust['core_sweep'].append(asdict(c))
        if len(vals)>=2:
            Cs=[x.median_C_blind for x in vals]; spread=(max(Cs)-min(Cs))/max(abs(np.median(Cs)),1e-300)
            robust['gates'].append({'name':f'robustness.core.{p.stem}','value':float(spread),'criterion':f"<= {rq['core_C_relative_spread_max']}",'status':'PASS' if spread<=rq['core_C_relative_spread_max'] else 'FAIL'})
    # Resolution convergence.
    n_hi=int(cfg.get('robustness',{}).get('convergence_resample_points',0) or 0)
    if n_hi>0:
        for p in anchors:
            lo=next((x for x in base if x.file==p.name),None)
            if lo is None: continue
            hi=analyze_geometry(p,cfg,resample_n=n_hi,threads=threads,force_python=force_python)
            d=_rel(lo.median_C_blind,hi.median_C_blind)
            robust['convergence'].append({'file':p.name,'low':asdict(lo),'high':asdict(hi),'C_relative_change':d})
            robust['gates'].append({'name':f'robustness.resolution.{p.stem}','value':d,'criterion':f"<= {rq['resolution_C_relative_change_max']}",'status':'PASS' if d<=rq['resolution_C_relative_change_max'] else 'FAIL'})
    # Parity-null test on first anchor. C should be even under mirror for this parity-even kernel class.
    if anchors and cfg.get('robustness',{}).get('parity_mirror_test',True):
        p=anchors[0]; a=next((x for x in base if x.file==p.name),None) or analyze_geometry(p,cfg,threads=threads,force_python=force_python)
        b=analyze_geometry(p,cfg,threads=threads,force_python=force_python,mirror=True)
        d=_rel(a.median_C_blind,b.median_C_blind); robust['parity'].append({'file':p.name,'original_C_blind':a.median_C_blind,'mirror_C_blind':b.median_C_blind,'relative_change':d})
        robust['gates'].append({'name':'robustness.parity_even_C','value':d,'criterion':f"<= {rq['parity_C_relative_change_max']}",'status':'PASS' if d<=rq['parity_C_relative_change_max'] else 'FAIL'})
    robust['status']=_status(robust['gates']) if robust['gates'] else 'INCONCLUSIVE'
    verdict['robustness']=robust
    if robust['status']=='FAIL': verdict['status']='FAIL'
    elif robust['status']=='INCONCLUSIVE' and verdict['status']=='PASS': verdict['status']='INCONCLUSIVE'
    verdict['runtime']={'backend':native,'threads':threads,'elapsed_s':time.perf_counter()-t0,'files_analyzed':len(files),'files_selected':input_qa['selected_count'],'files_rejected_qa':input_qa['rejected_count']}
    verdict['interpretation']='Centerline-derived regularized Biot-Savart surrogate. PASS supports only the tested geometric/mechanical closure class; it is not a resolved Euler proof.'
    (outdir/'geometry_cases.json').write_text(json.dumps([asdict(x) for x in base],indent=2),encoding='utf-8')
    (outdir/'geometry_verdict.json').write_text(json.dumps(verdict,indent=2),encoding='utf-8')
    return verdict
