from __future__ import annotations
import csv, hashlib, json, math, random, time, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import numpy as np

from native_ext.core import biot_savart, centerline_split, load_native, native_info
from .geometry import arclength, resample_closed, tangents, normal_component, rigid_fit, estimate_tube_thickness, kabsch_align
from .coupled import discrete_frame
from .io import load_fseries, load_xyz_text, sha256_file

PI=math.pi


def _jsonable(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,(np.floating,np.integer)): return x.item()
    if isinstance(x,complex): return {'re':float(x.real),'im':float(x.imag)}
    if isinstance(x,Path): return str(x)
    if isinstance(x,dict): return {str(k):_jsonable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [_jsonable(v) for v in x]
    return x

def write_json(path,data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(_jsonable(data),indent=2,sort_keys=True),encoding='utf-8')

def _rms_vec(v):
    a=np.asarray(v,float)
    return float(np.sqrt(np.mean(np.sum(a*a,axis=1)))) if len(a) else 0.0

def _segment_lengths(x): return np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)

def _total_length(comps): return float(sum(arclength(c) for c in comps))

def _concat(comps):
    offs=[0]
    for c in comps: offs.append(offs[-1]+len(c))
    return np.vstack(comps), offs

def _split(flat,offs): return [np.asarray(flat[offs[i]:offs[i+1]],float) for i in range(len(offs)-1)]

def _global_center(comps):
    q,_=_concat(comps); cen=q.mean(axis=0)
    return [c-cen for c in comps]

def normalize_components(comps,n_total=120,target_total_length=2*PI):
    comps=[np.asarray(c,float) for c in comps]
    lens=np.array([arclength(c) for c in comps],float); L=float(lens.sum())
    if L<=0: raise ValueError('zero total arclength')
    counts=np.maximum(24,np.round(float(n_total)*lens/L).astype(int))
    # exact target total point count where feasible
    while counts.sum()>n_total and np.max(counts)>24: counts[int(np.argmax(counts))]-=1
    while counts.sum()<n_total: counts[int(np.argmax(lens/counts))]+=1
    rr=[resample_closed(c,int(n),target_length=None,center=False) for c,n in zip(comps,counts)]
    rr=_global_center(rr)
    sc=float(target_total_length)/_total_length(rr)
    rr=[c*sc for c in rr]
    return rr,dict(raw_component_lengths=lens.tolist(),normalized_component_counts=counts.tolist(),scale_to_total_length=sc,total_length=float(target_total_length))


def load_multicurve(path,kind,metrics_path=None,n_raw=4096):
    p=Path(path)
    if kind=='fseries': return [load_fseries(p,n_raw)], {'component_count':1,'vertices_per_component':None}
    if kind!='knotplot': raise ValueError(kind)
    xyz=load_xyz_text(p)
    meta={'component_count':1,'vertices_per_component':[len(xyz)]}
    mp=Path(metrics_path) if metrics_path else p.with_suffix('.metrics.json')
    if mp.exists():
        m=json.loads(mp.read_text(encoding='utf-8')); meta.update(m)
        counts=m.get('vertices_per_component') or [len(xyz)]
        if sum(map(int,counts))!=len(xyz):
            raise ValueError(f'component vertex counts {counts} do not sum to {len(xyz)} for {p}')
        out=[]; a=0
        for n in counts:
            out.append(xyz[a:a+int(n)]); a+=int(n)
        return out,meta
    return [xyz],meta


def estimate_multicore(comps,meta,cfg):
    Lraw=sum(float(x) for x in meta.get('raw_component_lengths',[])) if meta.get('raw_component_lengths') else None
    norm_scale=float(meta.get('scale_to_total_length',1.0))
    # RidgeRunner thickness sidecar is the preferred tube radius estimator when available.
    if 'thickness' in meta and np.isfinite(float(meta['thickness'])):
        thick=float(meta['thickness'])*norm_scale
        method='ridgerunner_metrics'
    else:
        vals=[]
        for c in comps:
            e=estimate_tube_thickness(c,stride=int(cfg.get('thickness_stride',2)),dcsc_tangent_tol=float(cfg.get('dcsc_tangent_tol',0.1)),min_separation_fraction=float(cfg.get('thickness_min_separation_fraction',0.08)),curvature_quantile=float(cfg.get('curvature_quantile',0.01)))
            vals.append(float(e['thickness']))
        # Distinct components constrain tube radius as well.
        inter=float('inf')
        for i in range(len(comps)):
            for j in range(i+1,len(comps)):
                d=np.linalg.norm(comps[i][:,None,:]-comps[j][None,:,:],axis=2)
                inter=min(inter,float(d.min())/2.0)
        thick=min(vals+[inter])
        method='geometry_estimate'
    core=float(cfg.get('core_fraction_of_thickness',0.9))*thick
    return core,dict(thickness=float(thick),core=float(core),method=method)


def current_thickness(comps,cfg):
    vals=[]
    for c in comps:
        e=estimate_tube_thickness(c,stride=int(cfg.get('thickness_stride',2)),dcsc_tangent_tol=float(cfg.get('dcsc_tangent_tol',0.1)),min_separation_fraction=float(cfg.get('thickness_min_separation_fraction',0.08)),curvature_quantile=float(cfg.get('curvature_quantile',0.01)))
        vals.append(float(e['thickness']))
    inter=float('inf')
    for i in range(len(comps)):
        for j in range(i+1,len(comps)):
            D=np.linalg.norm(comps[i][:,None,:]-comps[j][None,:,:],axis=2)
            inter=min(inter,0.5*float(D.min()))
    return float(min(vals+[inter]))


def _shape_project(comps,vels):
    X,offs=_concat(comps); V,_=_concat(vels)
    _,_,_,res=rigid_fit(X,V)
    rs=_split(res,offs)
    return [normal_component(c,v) for c,v in zip(comps,rs)]


def multi_velocity(comps,*,gamma,core,backend,allow_sycl_cpu,mod,local_span=4,decompose=True):
    """Velocity of every component.

    The historical CPU/OpenMP path is preserved exactly: self-induction comes
    from ``centerline_split``.  Explicit SYCL backends use the worker for self
    induction too; on hot Jacobian/RPO/ringdown calls (``decompose=False``) this
    avoids an O(N^2) CPU split that would otherwise defeat GPU acceleration.
    """
    C=len(comps); local=[]; selfnl=[]; mutual=[]; total=[]; used=set()
    use_sycl=str(backend).startswith('sycl')
    for i,c in enumerate(comps):
        lv=sn_diag=None
        if (not use_sycl) or decompose:
            lab=np.zeros(len(c),np.int32)
            split,_=centerline_split(c,lab,gamma=gamma,core=core,local_span=local_span,mod=mod)
            lv=np.asarray(split['local']); sn_diag=np.asarray(split['same_lobe'])
        if use_sycl:
            selfv,bself=biot_savart(c,c,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod); used.add(bself)
        else:
            # Exact legacy CPU/OpenMP behavior.
            selfv=lv+sn_diag
        mv=np.zeros_like(c)
        for j,src in enumerate(comps):
            if j==i: continue
            vv,b=biot_savart(src,c,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod); used.add(b); mv+=vv
        tv=selfv+mv
        total.append(tv)
        if decompose:
            # For SYCL, make the diagnostic ledger sum exactly to the selected
            # backend total; any backend rounding delta is assigned to self-nonlocal.
            sn=(np.asarray(selfv)-lv) if use_sycl else sn_diag
            local.append(lv); selfnl.append(sn); mutual.append(mv)
    if not decompose:
        return {'total':total,'local':[],'self_nonlocal':[],'mutual':[]}, sorted(used)
    return {'total':total,'local':local,'self_nonlocal':selfnl,'mutual':mutual}, sorted(used)


def _flat_inner(m,f):
    M,_=_concat(m); F,_=_concat(f)
    return float(np.mean(np.einsum('ij,ij->i',M,F)))


def _mode_rms(m):
    M,_=_concat(m); return _rms_vec(M)


def _orthonormalize_multi(comps,named_modes):
    out=[]; names=[]; fams=[]
    for name,fam,mode in named_modes:
        g=_shape_project(comps,mode)
        for q in out:
            a=_flat_inner(q,g); g=[u-a*v for u,v in zip(g,q)]
        r=_mode_rms(g)
        if r>1e-9:
            out.append([u/r for u in g]); names.append(name); fams.append(fam)
    return dict(names=names,families=fams,modes=out)


def build_generic_modes(comps,kelvin_harmonics=(2,),torsion_harmonic=1):
    named=[]; C=len(comps)
    for ci,c in enumerate(comps):
        fr=discrete_frame(c); n=len(c); s=np.linspace(0,2*PI,n,endpoint=False)
        zeros=[np.zeros_like(z) for z in comps]
        f=[z.copy() for z in zeros]; f[ci]=fr['normal']; named.append((f'breathing_c{ci}', 'breathing', f))
        for trig,a in [('cos',np.cos(torsion_harmonic*s)),('sin',np.sin(torsion_harmonic*s))]:
            f=[z.copy() for z in zeros]; f[ci]=a[:,None]*fr['binormal']; named.append((f'torsion_c{ci}_{trig}', 'torsion', f))
        for k in kelvin_harmonics:
            for direction,vec in [('N',fr['normal']),('B',fr['binormal'])]:
                for trig,a in [('cos',np.cos(k*s)),('sin',np.sin(k*s))]:
                    f=[z.copy() for z in zeros]; f[ci]=a[:,None]*vec; named.append((f'kelvin_c{ci}_k{k}_{direction}_{trig}','kelvin',f))
    mi=_orthonormalize_multi(comps,named)
    mi['component_count']=C
    return mi


def _project_modes(modes,field): return np.array([_flat_inner(m,field) for m in modes],float)


def _rescale_total(comps,target=2*PI):
    q=_global_center(comps); sc=target/max(_total_length(q),1e-30); return [x*sc for x in q]

def apply_multi_mode(comps,mode,amp): return _rescale_total([x+float(amp)*m for x,m in zip(comps,mode)])


def eig_metrics(J):
    ev=np.linalg.eigvals(np.asarray(J,float)); scale=float(np.max(np.abs(ev))) if len(ev) else 0.; mr=float(np.max(ev.real)) if len(ev) else 0.
    return dict(eigenvalues=[{'re':float(z.real),'im':float(z.imag)} for z in ev],spectral_scale=scale,max_real=mr,normalized_growth=mr/max(scale,1e-12))


def generic_jacobian(comps,mi,*,eps,gamma,core,backend,allow_sycl_cpu,mod,local_span):
    """Finite-difference Jacobian of the *total* shape velocity.

    Hot Jacobian/RPO/Floquet paths deliberately call ``multi_velocity`` with
    ``decompose=False`` so explicit SYCL backends do not pay for an additional
    O(N^2) CPU local/self-nonlocal ledger on every +/- epsilon perturbation.
    In that mode only ``total`` is populated; diagnostic component ledgers are
    intentionally empty.  v0.4.6 incorrectly iterated those empty diagnostic
    lists and attempted ``np.vstack([])``.

    The preregistered P1/P2 gates, family ablation, ringdown precondition and
    RPO/Floquet search all use the total reduced Jacobian, so this routine now
    computes exactly that quantity.  Base-state local/self-nonlocal/mutual
    diagnostics remain available from ``multi_velocity(..., decompose=True)``
    in ``dataset_analysis``.
    """
    M=len(mi['modes']); Jtotal=np.zeros((M,M))
    for b,phi in enumerate(mi['modes']):
        xp=apply_multi_mode(comps,phi,+eps); xm=apply_multi_mode(comps,phi,-eps)
        vp,_=multi_velocity(xp,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span,decompose=False)
        vm,_=multi_velocity(xm,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span,decompose=False)
        if not vp.get('total') or not vm.get('total'):
            raise RuntimeError('fast velocity path returned no total component velocities')
        fp=_shape_project(xp,vp['total']); fm=_shape_project(xm,vm['total'])
        dv=[(a-bb)/(2*eps) for a,bb in zip(fp,fm)]
        Jtotal[:,b]=_project_modes(mi['modes'],dv)
    J={'total':Jtotal}
    return dict(eps=float(eps),J=J,eigs={'total':eig_metrics(Jtotal)},component_jacobian_decomposition='base_state_only')


def jacobian_convergence(js):
    q=[]
    for a,b in zip(js[:-1],js[1:]):
        A=a['J']['total'];B=b['J']['total'];q.append(float(np.linalg.norm(A-B)/max(np.linalg.norm(A),np.linalg.norm(B),1e-12)))
    return max(q) if q else 0.0


def family_groups(mi):
    d={}
    for i,f in enumerate(mi['families']): d.setdefault(f,[]).append(i)
    return d

def _decouple(J,idx):
    A=np.array(J,float,copy=True); idx=np.asarray(idx,int); rest=np.setdiff1d(np.arange(len(A)),idx)
    if len(idx) and len(rest): A[np.ix_(idx,rest)]=0; A[np.ix_(rest,idx)]=0
    return A

def family_ablation(J,mi):
    base=eig_metrics(J); scale=max(base['spectral_scale'],1e-12); out={'full':base}
    for fam,idx in family_groups(mi).items():
        e=eig_metrics(_decouple(J,idx)); e['growth_penalty_vs_full']=float((e['max_real']-base['max_real'])/scale); out['decouple_'+fam]=e
    # remove all cross-family blocks
    G=family_groups(mi); B=np.zeros_like(J)
    for idx in G.values(): B[np.ix_(idx,idx)]=J[np.ix_(idx,idx)]
    e=eig_metrics(B);e['growth_penalty_vs_full']=float((e['max_real']-base['max_real'])/scale);out['block_diagonal_families']=e
    return out


def gauss_link(c1,c2):
    a1=c1; b1=np.roll(c1,-1,axis=0); dl1=b1-a1; m1=.5*(a1+b1)
    a2=c2; b2=np.roll(c2,-1,axis=0); dl2=b2-a2; m2=.5*(a2+b2)
    val=0.0
    for i in range(len(c1)):
        r=m1[i]-m2; den=np.linalg.norm(r,axis=1)**3
        val+=float(np.sum(np.einsum('ij,ij->i',np.cross(np.repeat(dl1[i][None,:],len(c2),axis=0),dl2),r)/np.maximum(den,1e-30)))
    return val/(4*PI)

def linking_matrix(comps):
    C=len(comps); A=np.zeros((C,C))
    for i in range(C):
        for j in range(i+1,C): A[i,j]=A[j,i]=gauss_link(comps[i],comps[j])
    return A


def nearest_pairs(comps,skip=6):
    best_self=(float('inf'),-1,-1,-1)
    for ci,c in enumerate(comps):
        n=len(c)
        for i in range(n):
            js=np.arange(i+1,n); cyc=np.minimum(js-i,n-(js-i)); js=js[cyc>skip]
            if not len(js): continue
            d=np.linalg.norm(c[js]-c[i],axis=1); z=int(np.argmin(d))
            if d[z]<best_self[0]: best_self=(float(d[z]),ci,i,int(js[z]))
    best_inter=(float('inf'),-1,-1,-1,-1)
    for ci in range(len(comps)):
        for cj in range(ci+1,len(comps)):
            D=np.linalg.norm(comps[ci][:,None,:]-comps[cj][None,:,:],axis=2); q=np.unravel_index(int(np.argmin(D)),D.shape)
            if D[q]<best_inter[0]: best_inter=(float(D[q]),ci,int(q[0]),cj,int(q[1]))
    return {'self':dict(distance=best_self[0],component=best_self[1],i=best_self[2],j=best_self[3]),'inter':dict(distance=best_inter[0],component_i=best_inter[1],i=best_inter[2],component_j=best_inter[3],j=best_inter[4])}


def pair_rate(comps,vels,pair,kind):
    if kind=='self':
        ci=pair['component']; i=pair['i'];j=pair['j']
        if ci<0:return float('nan')
        d=comps[ci][i]-comps[ci][j]; n=np.linalg.norm(d); return float(np.dot(d/n,vels[ci][i]-vels[ci][j])) if n else float('nan')
    ci=pair['component_i'];cj=pair['component_j'];i=pair['i'];j=pair['j']
    if ci<0:return float('nan')
    d=comps[ci][i]-comps[cj][j]; n=np.linalg.norm(d); return float(np.dot(d/n,vels[ci][i]-vels[cj][j])) if n else float('nan')


def align_multi(reference,mobile):
    R,offs=_concat(reference); M,_=_concat(mobile); A=kabsch_align(R,M); return _split(A,offs)

def recurrence(reference,mobile):
    al=align_multi(reference,mobile); D,_=_concat([a-b for a,b in zip(al,reference)]); X,_=_concat(reference); X=X-X.mean(0)
    return _rms_vec(D)/max(_rms_vec(X),1e-12)


def evolve_multi(x0,*,steps,dt_max,cfl,gamma,core,backend,allow_sycl_cpu,mod,local_span,stride=4,ref=None,modes=None,core_event_factor=1.8):
    x=[z.copy() for z in x0]; ref=[z.copy() for z in (ref or x0)]; t=0.; hist=[]; event=None
    L0=linking_matrix(ref) if len(ref)>1 else np.zeros((1,1))
    for step in range(int(steps)+1):
        if step%max(1,int(stride))==0 or step==steps:
            pp=nearest_pairs(x,skip=max(local_span+2,min(len(c) for c in x)//12,5)); md=min(pp['self']['distance'],pp['inter']['distance'])
            thick_now=current_thickness(x,{'thickness_stride':2,'dcsc_tangent_tol':0.10,'thickness_min_separation_fraction':0.08,'curvature_quantile':0.01})
            clearance=float(thick_now/max(core,1e-30))
            row={'step':step,'t':t,'recurrence':recurrence(ref,x),'min_nonlocal_distance':md,'tube_clearance_ratio':clearance}
            if modes is not None:
                al=align_multi(ref,x); diff=_shape_project(ref,[a-b for a,b in zip(al,ref)]); row['mode_projection']=_project_modes(modes,diff).tolist()
            if len(x)>1:
                lk=linking_matrix(x); row['linking_matrix']=lk.tolist(); row['linking_drift_max']=float(np.max(np.abs(lk-L0)))
            hist.append(row)
            # A core event is based on tube-thickness loss, not an arbitrary chord distance.
            # Adjacent portions of a thick smooth tube can have centerline distance < 2a without self-intersection.
            clearance_min=1.0/max(float(core_event_factor),1e-12) if float(core_event_factor)<1.0 else 1.0
            if clearance<clearance_min:
                event={'step':step,'t':t,'tube_clearance_ratio':clearance,'threshold_ratio':clearance_min}; break
        if step==steps: break
        v1,_=multi_velocity(x,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span,decompose=False); s1=_shape_project(x,v1['total'])
        S,_=_concat(s1); X,_=_concat(x); edge=float(np.mean(np.concatenate([_segment_lengths(c) for c in x]))); vmax=float(np.max(np.linalg.norm(S,axis=1)))
        dt=min(float(dt_max),float(cfl)*edge/max(vmax,1e-12))
        mid=[a+0.5*dt*b for a,b in zip(x,s1)]
        v2,_=multi_velocity(mid,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span,decompose=False); s2=_shape_project(mid,v2['total'])
        x=[resample_closed(a+dt*b,len(a),target_length=None,center=False) for a,b in zip(x,s2)]; x=_global_center(x); t+=dt
    return {'final':x,'history':hist,'core_event':event}


def choose_oscillatory(J,mi):
    vals,vec=np.linalg.eig(J); order=np.argsort(vals.real)[::-1]
    for ii in order:
        if abs(vals[ii].imag)>1e-8:
            z=vec[:,ii]; return vals[ii],z
    ii=int(order[0]) if len(order) else 0
    return (vals[ii] if len(vals) else 0j),(vec[:,ii] if len(vals) else np.zeros(len(mi['modes'])))

def combine_mode(mi,coeff):
    z=np.asarray(coeff); real=[]; imag=[]
    for ci in range(mi['component_count']):
        r=np.zeros_like(mi['modes'][0][ci]); q=np.zeros_like(r)
        for a,m in zip(z,mi['modes']): r+=a.real*m[ci]; q+=a.imag*m[ci]
        real.append(r);imag.append(q)
    rr=_mode_rms(real);ii=_mode_rms(imag)
    if rr>0:real=[x/rr for x in real]
    if ii>0:imag=[x/ii for x in imag]
    return real,imag


def rpo_scan(comps,mi,J,*,cfg,gamma,core,backend,allow_sycl_cpu,mod):
    eig,coeff=choose_oscillatory(J,mi); fr,fi=combine_mode(mi,coeff); phases=int(cfg.get('panel_rpo_phase_count',3)); rows=[];best=None
    for p in range(phases):
        ph=2*PI*p/phases; field=[math.cos(ph)*a-math.sin(ph)*b for a,b in zip(fr,fi)]; x0=apply_multi_mode(comps,field,float(cfg.get('panel_rpo_amp',0.004)))
        ev=evolve_multi(x0,steps=int(cfg.get('panel_rpo_steps',60)),dt_max=float(cfg.get('panel_dt_max',5e-4)),cfl=float(cfg.get('panel_cfl',0.12)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=int(cfg.get('panel_local_span',4)),stride=int(cfg.get('panel_rpo_stride',4)),ref=x0,modes=mi['modes'],core_event_factor=float(cfg.get('core_event_factor',1.8)))
        h=ev['history']; ex=float(cfg.get('rpo_excursion_min',0.01)); first=next((i for i,z in enumerate(h) if z['recurrence']>=ex),None); cand=None; ratio=float('inf')
        if first is not None:
            minstep=max(int(cfg.get('panel_rpo_steps',60)*float(cfg.get('rpo_min_step_fraction',0.35))),h[first]['step']+int(cfg.get('panel_rpo_stride',4)))
            elig=[z for z in h if z['step']>=minstep]
            if elig:
                cand=min(elig,key=lambda z:z['recurrence']); peak=max(z['recurrence'] for z in h if z['step']<=cand['step']); ratio=cand['recurrence']/max(peak,1e-12)
        row={'phase_index':p,'phase':ph,'eigenvalue':{'re':float(eig.real),'im':float(eig.imag)},'excursion_reached':first is not None,'best_recurrence':float(cand['recurrence']) if cand else float('inf'),'best_step':int(cand['step']) if cand else None,'best_time':float(cand['t']) if cand else None,'return_ratio':float(ratio),'core_event':ev['core_event'],'history':h}
        rows.append(row)
        if cand and ratio<=float(cfg.get('rpo_return_ratio_max',0.65)) and cand['recurrence']<=float(cfg.get('rpo_recurrence_max',0.05)) and ev['core_event'] is None:
            if best is None or cand['recurrence']<best['best_recurrence']: best={**row,'initial_geometry':x0,'final_geometry':ev['final']}
    return {'candidate':best,'scan':rows}


def floquet_multi(comps,mi,rpo,*,cfg,gamma,core,backend,allow_sycl_cpu,mod):
    cand=rpo.get('candidate') if rpo else None
    if not cand: return {'valid':False,'reason':'no_rpo_candidate'}
    T=int(cand['best_step']); eps=float(cfg.get('panel_floquet_eps',0.0015)); maxm=int(cfg.get('panel_floquet_modes_max',6))
    if T<=0:return {'valid':False,'reason':'invalid_period_steps'}
    groups=family_groups(mi); idx=[]
    for fam in ('breathing','torsion','kelvin'):
        idx += groups.get(fam,[])[:2]
    for i in range(len(mi['modes'])):
        if i not in idx: idx.append(i)
    idx=idx[:maxm]; modes=[mi['modes'][i] for i in idx]
    x0=cand['initial_geometry']
    ref_ev=evolve_multi(x0,steps=T,dt_max=float(cfg.get('panel_dt_max',5e-4)),cfl=float(cfg.get('panel_cfl',0.12)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=int(cfg.get('panel_local_span',4)),stride=max(1,T),ref=x0,modes=None,core_event_factor=float(cfg.get('core_event_factor',1.0)))
    if ref_ev['core_event'] is not None:return {'valid':False,'reason':'core_event_on_reference_return','core_event':ref_ev['core_event']}
    ref=ref_ev['final']; M=np.zeros((len(idx),len(idx)))
    for col,phi in enumerate(modes):
        xp=apply_multi_mode(x0,phi,+eps);xm=apply_multi_mode(x0,phi,-eps)
        ep=evolve_multi(xp,steps=T,dt_max=float(cfg.get('panel_dt_max',5e-4)),cfl=float(cfg.get('panel_cfl',0.12)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=int(cfg.get('panel_local_span',4)),stride=max(1,T),ref=xp,modes=None,core_event_factor=float(cfg.get('core_event_factor',1.0)))
        em=evolve_multi(xm,steps=T,dt_max=float(cfg.get('panel_dt_max',5e-4)),cfl=float(cfg.get('panel_cfl',0.12)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=int(cfg.get('panel_local_span',4)),stride=max(1,T),ref=xm,modes=None,core_event_factor=float(cfg.get('core_event_factor',1.0)))
        if ep['core_event'] is not None or em['core_event'] is not None:return {'valid':False,'reason':'core_event_in_perturbation','column':col}
        yp=align_multi(ref,ep['final']);ym=align_multi(ref,em['final'])
        dv=_shape_project(ref,[(a-b)/(2*eps) for a,b in zip(yp,ym)])
        M[:,col]=np.array([_flat_inner(m,dv) for m in modes])
    mu=np.linalg.eigvals(M); neutral=int(np.argmin(np.abs(mu-1))) if len(mu) else -1; non=np.delete(mu,neutral) if len(mu)>1 else mu
    rho=float(np.max(np.abs(mu))) if len(mu) else float('nan');rho_non=float(np.max(np.abs(non))) if len(non) else float('nan')
    return {'valid':True,'period_steps':T,'period_time':cand.get('best_time'),'mode_indices':idx,'mode_names':[mi['names'][i] for i in idx],'monodromy':M,'multipliers':[{'re':float(z.real),'im':float(z.imag),'abs':float(abs(z))} for z in mu],'spectral_radius':rho,'neutral_index':neutral,'spectral_radius_excluding_neutral':rho_non}


def dataset_analysis(entry,cfg,*,backend,allow_sycl_cpu,mod):
    comps_raw,meta0=load_multicurve(entry['path'],entry['kind'],entry.get('metrics_path'),n_raw=int(cfg.get('fseries_raw_samples',4096)))
    lk_highres=linking_matrix(comps_raw) if len(comps_raw)>1 else np.zeros((1,1))
    comps,norm=normalize_components(comps_raw,n_total=int(cfg.get('panel_n_total',96)),target_total_length=2*PI); meta={**meta0,**norm}
    core,coreinfo=estimate_multicore(comps,meta,cfg); gamma=1.0; local_span=int(cfg.get('panel_local_span',4))
    mi=build_generic_modes(comps,kelvin_harmonics=tuple(cfg.get('panel_kelvin_harmonics',[2])))
    vv,backs=multi_velocity(comps,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span); sf={k:_shape_project(comps,v) for k,v in vv.items()}
    pp=nearest_pairs(comps,skip=max(local_span+2,min(len(c) for c in comps)//12,5))
    rates={kind:{k:pair_rate(comps,v,p,kind) for k,v in vv.items()} for kind,p in pp.items()}
    eps=[float(x) for x in cfg.get('panel_eps_values',[0.004,0.008])]; js=[generic_jacobian(comps,mi,eps=e,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span) for e in eps]; mid=js[len(js)//2]
    abl=family_ablation(mid['J']['total'],mi); conv=jacobian_convergence(js); lk0=linking_matrix(comps)
    ev=eig_metrics(mid['J']['total']); vals,vec=np.linalg.eig(mid['J']['total']); imax=int(np.argmax(vals.real)) if len(vals) else 0; field=combine_mode(mi,vec[:,imax] if len(vals) else np.zeros(len(mi['modes'])))[0]
    xstart=apply_multi_mode(comps,field,float(cfg.get('panel_ringdown_amp',0.006)))
    rd=evolve_multi(xstart,steps=int(cfg.get('panel_ringdown_steps',50)),dt_max=float(cfg.get('panel_dt_max',5e-4)),cfl=float(cfg.get('panel_cfl',0.12)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,local_span=local_span,stride=int(cfg.get('panel_ringdown_stride',5)),ref=xstart,modes=mi['modes'],core_event_factor=float(cfg.get('core_event_factor',1.8)))
    rpo_enabled=bool(cfg.get('panel_enable_rpo',True))
    rpo_precondition=bool(cfg.get('panel_rpo_only_if_linear_candidate',False))
    rpo_growth_max=float(cfg.get('panel_rpo_growth_precondition_max',cfg.get('panel_normalized_growth_max',0.12)))
    rpo_eligible=bool(rpo_enabled and (not rpo_precondition or ev['normalized_growth']<=rpo_growth_max))
    if rpo_eligible:
        rpo=rpo_scan(comps,mi,mid['J']['total'],cfg=cfg,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
        rpo['eligible']=True
    else:
        rpo={'candidate':None,'scan':[],'eligible':False,'skip_reason':('disabled' if not rpo_enabled else f'normalized_growth>{rpo_growth_max:g}')}
    floquet=floquet_multi(comps,mi,rpo,cfg=cfg,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod) if rpo.get('candidate') else {'valid':False,'reason':('no_rpo_candidate' if rpo_eligible else 'rpo_not_eligible')}
    linkdrift=max((z.get('linking_drift_max',0.) for z in rd['history']),default=0.) if len(comps)>1 else 0.
    recs=[z['recurrence'] for z in rd['history']]; bounded=(max(recs)<=float(cfg.get('panel_ringdown_recurrence_max',0.25))) if recs else False
    blockpen=float(abl['block_diagonal_families'].get('growth_penalty_vs_full',float('nan')))
    nearest_kind='inter' if len(comps)>1 else 'self'; nearest_rate=float(rates[nearest_kind]['mutual' if len(comps)>1 else 'self_nonlocal'])
    metrics={
      'component_count':len(comps),'core_radius_norm':core,'thickness_norm':coreinfo['thickness'],'core_clearance_radii':float(current_thickness(comps,cfg)/max(core,1e-30)),
      'shape_velocity_ratio':_rms_vec(_concat(sf['total'])[0])/max(_rms_vec(_concat(vv['total'])[0]),1e-30),'normalized_growth':ev['normalized_growth'],'jacobian_convergence':conv,
      'nearest_self_distance':pp['self']['distance'],'nearest_inter_distance':pp['inter']['distance'],'nearest_relevant_rate':nearest_rate,
      'TBK_block_diagonal_growth_penalty':blockpen,'ringdown_max_recurrence':max(recs) if recs else float('nan'),'ringdown_core_event':rd['core_event'] is not None,
      'linking_drift_max':linkdrift,'rpo_found':rpo['candidate'] is not None,'floquet_valid':bool(floquet.get('valid')),'floquet_rho_non':float(floquet.get('spectral_radius_excluding_neutral',float('nan'))),
    }
    gates={
      'P0_geometry_core_clear': bool(metrics['core_clearance_radii']>=float(cfg.get('panel_min_core_clearance',1.05))),
      'P1_jacobian_converged': bool(conv<=float(cfg.get('panel_jacobian_convergence_max',0.30))),
      'P2_linear_growth_bounded': bool(ev['normalized_growth']<=float(cfg.get('panel_normalized_growth_max',0.12))),
      'P3_nearest_relevant_separates': bool(nearest_rate>=float(cfg.get('panel_nearest_rate_min',0.0))),
      'P4_TBK_collective_stabilizes': bool(blockpen>=float(cfg.get('panel_collective_stabilization_min',0.02))),
      'P5_short_ringdown_bounded': bool(bounded and rd['core_event'] is None),
      'P6_linking_preserved': bool(linkdrift<=float(cfg.get('panel_linking_drift_max',0.15))) if len(comps)>1 else None,
      'P7_RPO_recurrence': (bool(rpo['candidate'] is not None) if rpo_eligible else None),
      'P8_Floquet_bounded': (bool(floquet.get('spectral_radius_excluding_neutral',float('inf'))<=float(cfg.get('panel_floquet_spectral_radius_max',1.05))) if floquet.get('valid') else None),
    }
    critical=['P0_geometry_core_clear','P1_jacobian_converged','P2_linear_growth_bounded','P5_short_ringdown_bounded']
    status='PASS' if all(gates[g] for g in critical) else 'FAIL'
    return {'blind_id':entry['blind_id'],'status':status,'gates':gates,'metrics':metrics,'meta':meta,'core_info':coreinfo,'mode_names':mi['names'],'mode_families':mi['families'],'eigs':mid['eigs'],'family_ablation':abl,'nearest_pairs':pp,'nearest_pair_rates':rates,'linking_matrix_initial':lk0,'linking_matrix_highres':lk_highres,'ringdown':rd,'rpo':rpo,'floquet':floquet,'backend_used':backs,'jacobian_eps_values':eps,'jacobian_component_decomposition':mid.get('component_jacobian_decomposition','unknown'),'jacobian_total':mid['J']['total']}


def gate_conclusion(name,val,m):
    if name=='P0_geometry_core_clear': return f"Tube-thickness/core-radius clearance = {m['core_clearance_radii']:.3f}; " + ('initial geometry is core-clear.' if val else 'initial geometry is already inside the preregistered near-core zone.')
    if name=='P1_jacobian_converged': return f"Jacobian convergence error = {m['jacobian_convergence']:.4g}; " + ('finite-difference spectrum is resolution-consistent.' if val else 'linear spectrum is not sufficiently converged.')
    if name=='P2_linear_growth_bounded': return f"Normalized max real eigenvalue = {m['normalized_growth']:.4g}; " + ('no strong growing reduced mode is detected.' if val else 'a growing reduced deformation mode is detected.')
    if name=='P3_nearest_relevant_separates': return f"Nearest relevant nonlocal/mutual distance rate = {m['nearest_relevant_rate']:.6g}; " + ('the nearest interaction is separating at t=0.' if val else 'the nearest interaction is approaching at t=0.')
    if name=='P4_TBK_collective_stabilizes': return f"TBK block-diagonal ablation penalty = {m['TBK_block_diagonal_growth_penalty']:.4g}; " + ('cross-family coupling is stabilizing by the preregistered sign test.' if val else 'cross-family coupling is not stabilizing by the preregistered sign test.')
    if name=='P5_short_ringdown_bounded': return f"Short-ringdown max recurrence = {m['ringdown_max_recurrence']:.4g}; core_event={m['ringdown_core_event']}; " + ('bounded over the short campaign.' if val else 'not bounded over the short campaign.')
    if name=='P6_linking_preserved': return f"Max pairwise Gauss-linking drift = {m['linking_drift_max']:.4g}; " + ('pairwise linking is numerically preserved.' if val else 'pairwise linking drift exceeds tolerance.')
    if name=='P7_RPO_recurrence': return ('RPO scan not evaluated because the preregistered compute precondition was not met.' if val is None else ('A valid excursion-and-return RPO candidate was found.' if val else 'No valid excursion-and-return RPO candidate was found in the preregistered phase scan.'))
    if name=='P8_Floquet_bounded': return ('Floquet multipliers excluding the neutral return mode are within the preregistered bound.' if val else ('Floquet multipliers exceed the bound.' if val is False else 'Floquet not evaluated because no valid RPO existed.'))
    return ''


def make_panel_reports(out,final,results,mapping):
    out=Path(out); lines=['# SST Multi-Topology Panel Report','',f"Overall panel classification: **{final['overall']}**",'', '> Overall is descriptive: individual topologies are classified independently; one unstable topology does not invalidate the panel.','', '## Unblinded summary','', '| source | class | components | status | growth | nearest rate | TBK penalty | ringdown | RPO |', '|---|---|---:|---|---:|---:|---:|---|---|']
    rows=[]
    for bid,r in results.items():
        mm=mapping[bid]; m=r['metrics']; src=mm['source']; cls=mm['topology_class'];
        lines.append(f"| {src} | {cls} | {m['component_count']} | {r['status']} | {m['normalized_growth']:.4f} | {m['nearest_relevant_rate']:.5g} | {m['TBK_block_diagonal_growth_penalty']:.4f} | {'PASS' if r['gates']['P5_short_ringdown_bounded'] else 'FAIL'} | {'YES' if m['rpo_found'] else 'NO'} |")
        rows.append({'blind_id':bid,'source':src,'topology_class':cls,'components':m['component_count'],'status':r['status'],**{k:v for k,v in m.items() if np.isscalar(v) or isinstance(v,(str,bool,type(None)))}})
    lines += ['', '## Interpretation', '', '- `P2` tests reduced linear shape stability, not topological conservation.', '- `P3` is a local sign test: positive separation does **not** imply global stability.', '- `P4` asks whether coupling between the operational breathing/torsion/Kelvin families reduces the dominant growth rate.', '- For links, `P6` checks pairwise Gauss-linking conservation during the short no-reconnection evolution.', '- `P7` is deliberately strict: Floquet analysis is not claimed unless a genuine excursion-and-return is first found.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    gl=['# Gate Conclusions','']
    for bid,r in results.items():
        mm=mapping[bid];gl += [f"## {bid} → {mm['source']}",'']
        for g,val in r['gates'].items():
            state='N/A' if val is None else ('PASS' if val else 'FAIL');gl += [f"### {g}: {state}",gate_conclusion(g,val,r['metrics']),'']
    (out/'GATE_CONCLUSIONS.md').write_text('\n'.join(gl),encoding='utf-8')
    # Comparative post-unblind report: descriptive ranking, not a preregistered decision rule.
    cr=['# Comparative Conclusions','', 'These comparisons are generated only after unblinding and do not alter any gate threshold.','', '## Linear-growth ranking','', '| rank | source | class | components | normalized growth | status |', '|---:|---|---|---:|---:|---|']
    ranked=sorted([(r['metrics']['normalized_growth'],mapping[b]['source'],mapping[b]['topology_class'],r['metrics']['component_count'],r['status'],b) for b,r in results.items()],key=lambda z:z[0])
    for k,(g,src,cls,c,st,b) in enumerate(ranked,1): cr.append(f'| {k} | {src} | {cls} | {c} | {g:.6g} | {st} |')
    cr += ['', '## Link topology diagnostics','', '| source | pairwise high-resolution Gauss linking | nearest mutual rate | linking drift |', '|---|---|---:|---:|']
    for b,r in results.items():
        if r['metrics']['component_count']<=1: continue
        A=np.asarray(r.get('linking_matrix_highres',r.get('linking_matrix_initial')),float); vals=[]
        for i in range(len(A)):
            for j in range(i+1,len(A)): vals.append(f'{A[i,j]:+.5f}')
        cr.append(f"| {mapping[b]['source']} | {', '.join(vals)} | {r['metrics']['nearest_relevant_rate']:.6g} | {r['metrics']['linking_drift_max']:.3g} |")
    cr += ['', '## Interpretation guardrails','', '- A positive nearest-pair rate is local separation only; it is not equivalent to global spectral stability.', '- `P2` is basis-dependent. The generic v0.4 Frenet/Fourier basis is complementary to, not a replacement for, the trefoil-specific lobe basis of v0.3.', '- An RPO/Floquet conclusion is permitted only after the excursion-and-return gate succeeds.', '- Pairwise Gauss linking distinguishes Hopf-like/linking structure from unlinks, but pairwise linking alone does not characterize higher-order links such as Borromean-type structures.']
    (out/'COMPARATIVE_CONCLUSIONS.md').write_text('\n'.join(cr)+'\n',encoding='utf-8')
    with open(out/'summary_metrics.csv','w',newline='',encoding='utf-8') as f:
        fields=list(rows[0].keys()) if rows else []; w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def run_panel(entries,cfg_path,out_dir,*,backend='auto',allow_sycl_cpu=False,force_build=False,build_verbose=False,resume=True):
    cfg=json.loads(Path(cfg_path).read_text()) if isinstance(cfg_path,(str,Path)) else dict(cfg_path);out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    cfgfile=out/'00_preregistered_config.json'
    if cfgfile.exists() and resume:
        oldcfg=json.loads(cfgfile.read_text())
        if oldcfg!=cfg: raise RuntimeError('Refusing resume: existing preregistered config differs from requested config')
    else: write_json(cfgfile,cfg)
    rng=random.Random(int(cfg.get('panel_blind_seed',40401))); idx=list(range(len(entries)));rng.shuffle(idx); blind={orig:f'B{k+1:02d}' for k,orig in enumerate(idx)}
    manifest=[]
    for i,e in enumerate(entries):
        q=dict(e);q['blind_id']=blind[i];q['sha256']=sha256_file(q['path']);
        if q.get('metrics_path') and Path(q['metrics_path']).exists():q['metrics_sha256']=sha256_file(q['metrics_path'])
        manifest.append(q)
    write_json(out/'blind_input_hashes.json',[{'blind_id':e['blind_id'],'sha256':e['sha256']} for e in manifest])
    print(f"[SST] initializing host native support for backend={backend}", flush=True)
    mod=load_native(force_build=force_build,build_verbose=build_verbose)
    is_sycl_backend=str(backend).startswith('sycl')
    print(f"[SST] host native loaded={mod is not None}; probing external SYCL worker={is_sycl_backend}", flush=True)
    binfo=native_info(mod, probe_sycl_worker=is_sycl_backend)
    binfo['requested_backend']=backend
    if backend=='sycl-dd32': binfo['sycl_numeric_role']='experimental_dd32_fp32x2_reference_pending'
    elif backend in ('sycl','sycl-fp32') and not binfo.get('sycl_native_fp64',False): binfo['sycl_numeric_role']='screening_fp32_only'
    write_json(out/'backend_info.json',binfo)
    print(f"[SST] backend initialization complete: sycl_worker={binfo.get('sycl_worker_available',False)} device={binfo.get('sycl_device_name','n/a')}", flush=True)
    if backend in ('sycl','sycl-fp32') and binfo.get('sycl_numeric_role')=='screening_fp32_only':
        (out/'GPU_PRECISION_NOTICE.md').write_text('# GPU precision notice\n\nThis campaign used the external SYCL worker on a device without native FP64. Biot--Savart evaluations are FP32 and results are **screening/diagnostic only**. CPU/OpenMP FP64 remains confirmatory for preregistered scientific PASS/FAIL near thresholds, RPO recurrence and Floquet claims.\n',encoding='utf-8')
    if backend=='sycl-dd32':
        (out/'GPU_PRECISION_NOTICE_DD32.md').write_text('# DD32 / FP32x2 precision notice\n\nThis campaign used experimental double-single arithmetic: every device scalar is represented by two FP32 values (hi + lo), with compensated addition/multiplication/division/sqrt and DD accumulation. This is **not IEEE FP64**. CPU/OpenMP FP64 remains the reference until campaign-level parity is demonstrated.\n',encoding='utf-8')
        smoke=Path('build/sycl_dd32_smoke.json')
        if smoke.exists(): (out/'DD32_PARITY_SMOKE.json').write_bytes(smoke.read_bytes())
    pre=out/'pre_unblind';pre.mkdir(exist_ok=True)
    results={};t0=time.time(); ordered=sorted(manifest,key=lambda z:z['blind_id']); total_n=len(ordered)
    print(f"[SST] campaign backend={backend} datasets={total_n} (blind; source names withheld until final report)", flush=True)
    for pos,e in enumerate(ordered,1):
        af=pre/f"{e['blind_id']}_analysis.json"
        if resume and af.exists():
            r=json.loads(af.read_text(encoding='utf-8')); results[e['blind_id']]=r
            print(f"[SST] [{pos:03d}/{total_n:03d}] {e['blind_id']} RESUME status={r.get('status','?')}", flush=True)
            continue
        ds_t0=time.time()
        print(f"[SST] [{pos:03d}/{total_n:03d}] {e['blind_id']} START", flush=True)
        try:
            r=dataset_analysis(e,cfg,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
        except BaseException as exc:
            print(f"[SST] [{pos:03d}/{total_n:03d}] {e['blind_id']} ERROR {type(exc).__name__}: {exc}", flush=True, file=sys.stderr)
            raise
        results[e['blind_id']]=r
        compact={k:v for k,v in r.items() if k!='jacobian_total'};write_json(af,compact);np.savez_compressed(pre/f"{e['blind_id']}_arrays.npz",J_total=r['jacobian_total'])
        growth=r.get('metrics',{}).get('normalized_growth',float('nan'))
        print(f"[SST] [{pos:03d}/{total_n:03d}] {e['blind_id']} DONE status={r.get('status','?')} growth={growth:.6g} dt={time.time()-ds_t0:.1f}s", flush=True)
    mapping={e['blind_id']:{k:v for k,v in e.items() if k not in ('blind_id',)} for e in manifest};write_json(out/'unblind_manifest.json',mapping)
    passes=sum(r['status']=='PASS' for r in results.values());fails=len(results)-passes
    final={'version':str(cfg.get('version','0.4.1')),'overall':f'{passes}_PASS_{fails}_FAIL','dataset_count':len(results),'pass_count':passes,'fail_count':fails,'runtime_s':time.time()-t0,'blind_scores':{b:{'status':r['status'],'gates':r['gates'],'metrics':r['metrics']} for b,r in results.items()}}
    write_json(pre/'blind_verdict.json',final);write_json(out/'final_verdict.json',{**final,'blind_to_source':{b:m['source'] for b,m in mapping.items()}});make_panel_reports(out,final,results,mapping)
    return final,results,mapping
