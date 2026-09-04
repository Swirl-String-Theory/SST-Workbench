from __future__ import annotations
import math
import numpy as np

from native_ext.core import centerline_split, biot_savart, min_nonlocal_distance
from .geometry import (
    tangents, normal_component, rigid_fit, build_lobe_modes, lobe_windows,
    detect_lobes, shape_field, resample_closed, apply_mode, kabsch_align, arclength,
)


def _rms(f):
    f=np.asarray(f,float)
    return float(np.sqrt(np.mean(np.sum(f*f,axis=-1))))


def _orthonormalize(x, named):
    out=[]; names=[]
    for name,f in named:
        g=normal_component(x,np.asarray(f,float))
        _,_,_,g=rigid_fit(x,g)
        g=normal_component(x,g)
        for q in out:
            g-=q*float(np.mean(np.einsum('ij,ij->i',g,q)))
        r=_rms(g)
        if r>1e-9:
            out.append(g/r); names.append(name)
    return names,np.asarray(out,float)


def discrete_frame(x):
    x=np.asarray(x,float); n=len(x)
    t=tangents(x)
    ds=0.5*(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)+np.linalg.norm(x-np.roll(x,1,axis=0),axis=1))
    dt=np.roll(t,-1,axis=0)-np.roll(t,1,axis=0)
    curv=np.linalg.norm(dt,axis=1)/np.maximum(2*ds,1e-12)
    nn=np.zeros_like(x)
    good=np.linalg.norm(dt,axis=1)>1e-12
    nn[good]=dt[good]/np.linalg.norm(dt[good],axis=1)[:,None]
    # robust fallback for locally tiny curvature
    if np.any(~good):
        c=x-x.mean(axis=0); tmp=c-t*np.einsum('ij,ij->i',c,t)[:,None]
        q=np.linalg.norm(tmp,axis=1)>1e-12
        nn[~good & q]=tmp[~good & q]/np.linalg.norm(tmp[~good & q],axis=1)[:,None]
    b=np.cross(t,nn); bn=np.linalg.norm(b,axis=1); ok=bn>1e-12; b[ok]/=bn[ok,None]
    db=np.roll(b,-1,axis=0)-np.roll(b,1,axis=0)
    tau=-np.einsum('ij,ij->i',db,nn)/np.maximum(2*ds,1e-12)
    return dict(tangent=t,normal=nn,binormal=b,curvature=curv,torsion=tau,ds=ds)


def build_coupled_modes(x, *, kelvin_harmonics=(2,3,4), peaks=None, labels=None):
    x=np.asarray(x,float); n=len(x)
    if peaks is None or labels is None:
        peaks,labels,_=detect_lobes(x)
    legacy=build_lobe_modes(x,peaks,labels)
    fr=discrete_frame(x); W=lobe_windows(x,peaks,labels)
    P=np.array([[1,1,1],[2,-1,-1],[0,1,-1]],float); P/=np.linalg.norm(P,axis=1)[:,None]
    named=[]
    for nm,md in zip(legacy['names'],legacy['modes']): named.append((nm,md))
    # Out-of-plane lobe perturbations: binormal displacements are the minimal centerline perturbations
    # that strongly modify local torsion while remaining distinct from radial breathing.
    for m,pat in enumerate(P):
        f=np.zeros_like(x)
        for k in range(3): f += pat[k]*W[k][:,None]*fr['binormal']
        named.append((f'torsion_{m}',f))
    s=np.linspace(0,2*np.pi,n,endpoint=False)
    for k in kelvin_harmonics:
        for trig,amp in [('cos',np.cos(k*s)),('sin',np.sin(k*s))]:
            named.append((f'kelvin_k{k}_N_{trig}',amp[:,None]*fr['normal']))
            named.append((f'kelvin_k{k}_B_{trig}',amp[:,None]*fr['binormal']))
    names,modes=_orthonormalize(x,named)
    families=[]
    for nm in names:
        if nm.startswith('tilt_'): families.append('tilt')
        elif nm.startswith('breathe_'): families.append('breathing')
        elif nm.startswith('torsion_'): families.append('torsion')
        elif nm.startswith('kelvin_'): families.append('kelvin')
        else: families.append('other')
    return dict(names=names,modes=modes,families=families,peaks=np.asarray(peaks),labels=np.asarray(labels),frame=fr)


def _mode_project(modes, field):
    return np.array([float(np.mean(np.einsum('ij,ij->i',m,field))) for m in modes])


def _eig_metrics(J):
    ev=np.linalg.eigvals(np.asarray(J,float)); scale=float(np.max(np.abs(ev))) if len(ev) else 0.0
    mr=float(np.max(ev.real)) if len(ev) else 0.0
    return dict(eigenvalues=[{'re':float(z.real),'im':float(z.imag)} for z in ev],spectral_scale=scale,max_real=mr,normalized_growth=mr/max(scale,1e-12))


def coupled_jacobian(x, mode_info, *, eps, gamma, core, local_span, mod):
    x=np.asarray(x,float); modes=np.asarray(mode_info['modes'],float); labels=np.asarray(mode_info['labels'],int)
    M=len(modes); keys=['total','local','same_lobe','cross_lobe','transition']
    J={k:np.zeros((M,M),float) for k in keys}
    for b,phi in enumerate(modes):
        xp=apply_mode(x,phi,+eps,target_length=2*np.pi); xm=apply_mode(x,phi,-eps,target_length=2*np.pi)
        sp,_=centerline_split(xp,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
        sm,_=centerline_split(xm,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
        for k in keys:
            fp=shape_field(xp,sp[k])[0]; fm=shape_field(xm,sm[k])[0]
            J[k][:,b]=_mode_project(modes,(fp-fm)/(2*eps))
    return dict(eps=float(eps),J=J,eigs={k:_eig_metrics(A) for k,A in J.items()})


def family_indices(mode_info):
    out={}
    for i,f in enumerate(mode_info['families']): out.setdefault(f,[]).append(i)
    return out


def family_participation(coeffs, mode_info):
    z=np.asarray(coeffs,complex); w=np.abs(z)**2; den=float(np.sum(w)) or 1.0
    idx=family_indices(mode_info)
    return {f:float(np.sum(w[ii])/den) for f,ii in idx.items()}


def coupled_spectrum_analysis(J, mode_info):
    A=np.asarray(J,float); vals,vecs=np.linalg.eig(A); order=np.argsort(vals.real)[::-1]
    rows=[]
    for rank,ii in enumerate(order):
        v=vecs[:,ii]; part=family_participation(v,mode_info)
        rows.append(dict(rank=int(rank),eigenvalue={'re':float(vals[ii].real),'im':float(vals[ii].imag)},
                         family_participation=part,
                         coefficients=[{'re':float(z.real),'im':float(z.imag)} for z in v]))
    return rows


def _decouple_family(J, idx):
    A=np.array(J,float,copy=True); allidx=np.arange(A.shape[0]); idx=np.asarray(idx,int); other=np.setdiff1d(allidx,idx)
    if len(idx) and len(other):
        A[np.ix_(idx,other)]=0.0; A[np.ix_(other,idx)]=0.0
    return A


def _block_diagonal_families(J, groups):
    A=np.zeros_like(J,dtype=float)
    for idx in groups.values():
        if idx: A[np.ix_(idx,idx)]=np.asarray(J)[np.ix_(idx,idx)]
    return A


def family_coupling_ablation(J, mode_info):
    J=np.asarray(J,float); groups=family_indices(mode_info)
    out={'full':_eig_metrics(J)}
    for fam in ('breathing','torsion','kelvin','tilt'):
        if fam in groups: out[f'decouple_{fam}']=_eig_metrics(_decouple_family(J,groups[fam]))
    out['block_diagonal_families']=_eig_metrics(_block_diagonal_families(J,groups))
    base=out['full']['max_real']; scale=max(out['full']['spectral_scale'],1e-12)
    for k,v in list(out.items()):
        if k=='full': continue
        v['growth_penalty_vs_full']=float((v['max_real']-base)/scale)
    return out


def choose_coupled_oscillatory_mode(rows, min_family=0.02):
    best=None; bestscore=-1.0
    for r in rows:
        z=complex(r['eigenvalue']['re'],r['eigenvalue']['im'])
        if abs(z.imag)<1e-8: continue
        p=r['family_participation']; b=p.get('breathing',0.0); t=p.get('torsion',0.0); k=p.get('kelvin',0.0)
        geom=(max(b,1e-9)*max(t,1e-9)*max(k,1e-9))**(1/3)
        score=abs(z.imag)/(abs(z.real)+0.05*abs(z.imag)+1e-12)*geom
        if min(b,t,k)<min_family: score*=0.25
        if score>bestscore: bestscore=score; best=r
    if best is None and rows: best=max(rows,key=lambda r:abs(r['eigenvalue']['im']))
    return best,float(bestscore)


def eigenvector_fields(row, mode_info):
    z=np.asarray([complex(c['re'],c['im']) for c in row['coefficients']])
    modes=np.asarray(mode_info['modes'])
    fr=np.tensordot(z.real,modes,axes=(0,0)); fi=np.tensordot(z.imag,modes,axes=(0,0))
    rr=_rms(fr); ri=_rms(fi)
    if rr>1e-12: fr/=rr
    if ri>1e-12: fi/=ri
    return fr,fi


def evolve_shape(x0, *, steps, dt_max, cfl, gamma, core, backend, allow_sycl_cpu, mod, stride=1, ref=None, modes=None, local_span=5, core_event_factor=1.8):
    x=np.asarray(x0,float).copy(); n=len(x); t=0.0; hist=[]; event=None; backend_used=None
    ref=np.asarray(ref if ref is not None else x0,float)
    for step in range(int(steps)+1):
        if step%max(1,int(stride))==0 or step==steps:
            al=kabsch_align(ref,x); d=normal_component(ref,al-ref); rec=_rms(d)/max(_rms(ref-ref.mean(axis=0)),1e-12)
            row=dict(step=int(step),t=float(t),recurrence=float(rec))
            if modes is not None:
                q=_mode_project(modes,d); row['mode_projection']=q.tolist(); row['modal_norm']=float(np.linalg.norm(q))
            md=min_nonlocal_distance(x,skip=max(local_span+2,n//12,6),mod=mod); row['min_nonlocal_distance']=float(md['distance'])
            hist.append(row)
            if md['distance']<float(core_event_factor)*core:
                event=dict(step=int(step),t=float(t),distance=float(md['distance']),threshold=float(core_event_factor*core)); break
        if step==steps: break
        v1,backend_used=biot_savart(x,x,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
        v1=shape_field(x,v1)[0]
        vmax=float(np.max(np.linalg.norm(v1,axis=1))); edge=float(np.mean(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)))
        dt=min(float(dt_max),float(cfl)*edge/max(vmax,1e-12))
        mid=x+0.5*dt*v1
        v2,backend_used=biot_savart(mid,mid,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
        v2=shape_field(mid,v2)[0]
        x=resample_closed(x+dt*v2,n,target_length=None,center=True); t+=dt
    return dict(final=x,history=hist,core_event=event,backend=backend_used)


def rpo_phase_scan(base, mode_info, spectrum_rows, *, cfg, gamma, core, backend, allow_sycl_cpu, mod):
    row,score=choose_coupled_oscillatory_mode(spectrum_rows,float(cfg.get('coupled_family_participation_min',0.02)))
    if row is None: return dict(candidate=None,scan=[],reason='no_eigenmode')
    fr,fi=eigenvector_fields(row,mode_info); amp=float(cfg.get('rpo_amp',0.004)); phases=int(cfg.get('rpo_phase_count',6))
    steps=int(cfg.get('rpo_steps',120)); stride=max(1,int(cfg.get('rpo_stride',4))); min_frac=float(cfg.get('rpo_min_step_fraction',0.35))
    scan=[]; best=None
    for p in range(phases):
        phi=2*np.pi*p/phases
        field=math.cos(phi)*fr-math.sin(phi)*fi
        if _rms(field)<1e-12: field=fr
        x0=apply_mode(base,field,amp,target_length=2*np.pi)
        ev=evolve_shape(x0,steps=steps,dt_max=float(cfg.get('rpo_dt_max',5e-4)),cfl=float(cfg.get('rpo_cfl',0.1)),gamma=gamma,core=core,
                        backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,stride=stride,ref=x0,modes=mode_info['modes'],local_span=int(cfg['local_span']),core_event_factor=float(cfg.get('core_event_factor',1.8)))
        exc_min=float(cfg.get('rpo_excursion_min',0.012)); return_ratio_max=float(cfg.get('rpo_return_ratio_max',0.65))
        h=ev['history']; first_exc=next((ii for ii,z in enumerate(h) if z['recurrence']>=exc_min),None)
        cand=None; peak_before=float('nan'); return_ratio=float('inf')
        if first_exc is not None:
            min_step=max(int(steps*min_frac),h[first_exc]['step']+stride)
            eligible=[z for z in h if z['step']>=min_step]
            if eligible:
                cand=min(eligible,key=lambda z:z['recurrence'])
                prior=[z['recurrence'] for z in h if z['step']<=cand['step']]
                peak_before=max(prior) if prior else float('nan')
                return_ratio=float(cand['recurrence']/max(peak_before,1e-12))
        rr=dict(phase=float(phi),phase_index=int(p),eigenvalue=row['eigenvalue'],coupling_score=score,core_event=ev['core_event'],
                excursion_reached=first_exc is not None,excursion_min=exc_min,peak_before_return=peak_before,return_ratio=return_ratio,return_ratio_max=return_ratio_max,
                best_recurrence=(cand['recurrence'] if cand else float('inf')),best_step=(cand['step'] if cand else None),best_time=(cand['t'] if cand else None),history=h)
        scan.append(rr)
        valid_return=(cand is not None and return_ratio<=return_ratio_max)
        if valid_return and ev['core_event'] is None and (best is None or cand['recurrence']<best['best_recurrence']):
            best={**rr,'initial_geometry':x0,'final_geometry':ev['final']}
    return dict(candidate=best,scan=scan,selected_mode=row,selected_mode_coupling_score=score)


def phase_lock_diagnostics(rpo, mode_info, *, windows=3):
    cand=rpo.get('candidate') if rpo else None
    if not cand or not cand.get('history'): return dict(valid=False,reason='no_rpo_candidate')
    hist=[h for h in cand['history'] if 'mode_projection' in h]
    if len(hist)<12:return dict(valid=False,reason='too_few_samples')
    t=np.asarray([h['t'] for h in hist],float); Q=np.asarray([h['mode_projection'] for h in hist],float)
    if np.ptp(t)<=0:return dict(valid=False,reason='zero_time_span')
    groups=family_indices(mode_info); chosen={}
    for fam in ('breathing','torsion','kelvin'):
        idx=groups.get(fam,[])
        if not idx:return dict(valid=False,reason=f'missing_{fam}')
        var=np.var(Q[:,idx],axis=0); chosen[fam]=idx[int(np.argmax(var))]
    n=len(t); edges=np.linspace(0,n,int(windows)+1,dtype=int); specs=[]
    for w in range(int(windows)):
        a,b=edges[w],edges[w+1]
        if b-a<4: continue
        tw=t[a:b]; tu=np.linspace(tw[0],tw[-1],b-a)
        row={}
        for fam,idx in chosen.items():
            y=np.interp(tu,tw,Q[a:b,idx]); y=y-np.mean(y); F=np.fft.rfft(y); f=np.fft.rfftfreq(len(y),d=max((tu[-1]-tu[0])/max(len(y)-1,1),1e-12))
            if len(F)<=1: continue
            j=1+int(np.argmax(np.abs(F[1:])**2)); row[fam]=dict(freq=float(f[j]),phase=float(np.angle(F[j])),power=float(np.abs(F[j])**2))
        if len(row)==3: specs.append(row)
    if len(specs)<2:return dict(valid=False,reason='insufficient_windows')
    freqs={fam:np.asarray([r[fam]['freq'] for r in specs]) for fam in chosen}
    means={fam:float(np.mean(v)) for fam,v in freqs.items()}; fm=np.asarray(list(means.values())); freq_spread=float((fm.max()-fm.min())/max(np.mean(fm),1e-12))
    pairs=[]; locks=[]
    fams=['breathing','torsion','kelvin']
    for i in range(3):
        for j in range(i+1,3):
            a,b=fams[i],fams[j]; d=np.asarray([np.angle(np.exp(1j*(r[a]['phase']-r[b]['phase']))) for r in specs]); R=abs(np.mean(np.exp(1j*d)))
            pairs.append(dict(pair=f'{a}-{b}',phase_lock_strength=float(R),mean_phase_difference=float(np.angle(np.mean(np.exp(1j*d)))))); locks.append(R)
    return dict(valid=True,chosen_mode_indices=chosen,window_spectra=specs,mean_frequencies=means,relative_frequency_spread=freq_spread,pairs=pairs,phase_lock_strength=float(np.mean(locks)))


def floquet_monodromy(base, mode_info, rpo, *, cfg, gamma, core, backend, allow_sycl_cpu, mod):
    cand=rpo.get('candidate') if rpo else None
    if not cand:return dict(valid=False,reason='no_rpo_candidate')
    rec=float(cand['best_recurrence']); maxrec=float(cfg.get('rpo_recurrence_max',0.05)); rr=float(cand.get('return_ratio',float('inf'))); rrmax=float(cfg.get('rpo_return_ratio_max',0.65))
    if not np.isfinite(rec) or rec>maxrec:return dict(valid=False,reason='rpo_recurrence_above_threshold',recurrence=rec,threshold=maxrec)
    if not np.isfinite(rr) or rr>rrmax:return dict(valid=False,reason='rpo_return_ratio_above_threshold',return_ratio=rr,threshold=rrmax)
    Tsteps=int(cand['best_step']); x0=np.asarray(cand['initial_geometry'],float); maxm=int(cfg.get('floquet_modes_max',8)); eps=float(cfg.get('floquet_eps',0.0015))
    # Select highest-participation coupled modes while keeping family coverage; deterministic order from basis.
    names=mode_info['names']; fam=mode_info['families']; preferred=[]
    for target in ('breathing','torsion','kelvin','tilt'):
        preferred += [i for i,f in enumerate(fam) if f==target][:max(1,maxm//4)]
    for i in range(len(names)):
        if i not in preferred: preferred.append(i)
    idx=preferred[:maxm]
    modes=np.asarray(mode_info['modes'])[idx]
    ce=float(cfg.get('core_event_factor',1.8))
    ref_ev=evolve_shape(x0,steps=Tsteps,dt_max=float(cfg.get('rpo_dt_max',5e-4)),cfl=float(cfg.get('rpo_cfl',0.1)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,stride=max(1,Tsteps),ref=x0,modes=None,local_span=int(cfg['local_span']),core_event_factor=ce)
    if ref_ev['core_event'] is not None:return dict(valid=False,reason='core_event_on_reference_return',core_event=ref_ev['core_event'])
    ref=ref_ev['final']; M=np.zeros((len(idx),len(idx)),float)
    for c,phi in enumerate(modes):
        xp=apply_mode(x0,phi,+eps,target_length=2*np.pi); xm=apply_mode(x0,phi,-eps,target_length=2*np.pi)
        ep=evolve_shape(xp,steps=Tsteps,dt_max=float(cfg.get('rpo_dt_max',5e-4)),cfl=float(cfg.get('rpo_cfl',0.1)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,stride=max(1,Tsteps),ref=xp,modes=None,local_span=int(cfg['local_span']),core_event_factor=ce)
        em=evolve_shape(xm,steps=Tsteps,dt_max=float(cfg.get('rpo_dt_max',5e-4)),cfl=float(cfg.get('rpo_cfl',0.1)),gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod,stride=max(1,Tsteps),ref=xm,modes=None,local_span=int(cfg['local_span']),core_event_factor=ce)
        if ep['core_event'] is not None or em['core_event'] is not None:return dict(valid=False,reason='core_event_in_floquet_perturbation',column=int(c),plus_event=ep['core_event'],minus_event=em['core_event'])
        yp=kabsch_align(ref,ep['final']); ym=kabsch_align(ref,em['final']); dv=normal_component(ref,(yp-ym)/(2*eps)); M[:,c]=_mode_project(modes,dv)
    mu=np.linalg.eigvals(M); rho=float(np.max(np.abs(mu))) if len(mu) else float('nan')
    jneutral=int(np.argmin(np.abs(mu-1))) if len(mu) else -1
    mu_non=np.delete(mu,jneutral) if len(mu)>1 else mu
    rho_non=float(np.max(np.abs(mu_non))) if len(mu_non) else float('nan')
    return dict(valid=True,recurrence=rec,period_steps=Tsteps,period_time=float(cand['best_time']),mode_indices=idx,mode_names=[names[i] for i in idx],eps=eps,monodromy=M,
                multipliers=[{'re':float(z.real),'im':float(z.imag),'abs':float(abs(z))} for z in mu],spectral_radius=rho,neutral_index=jneutral,spectral_radius_excluding_neutral=rho_non)


def coupled_analysis(base, *, cfg, gamma, core, backend, allow_sycl_cpu, mod):
    n=int(cfg.get('coupled_n_points',192)); x=resample_closed(base,n,target_length=2*np.pi); peaks,labels,_=detect_lobes(x)
    mi=build_coupled_modes(x,kelvin_harmonics=tuple(cfg.get('kelvin_harmonics',[2,3,4])),peaks=peaks,labels=labels)
    eps_values=[float(z) for z in cfg.get('coupled_eps_values',[cfg.get('coupled_jacobian_eps',0.004)])]
    cjs=[coupled_jacobian(x,mi,eps=e,gamma=gamma,core=core,local_span=int(cfg.get('coupled_local_span',cfg['local_span'])),mod=mod) for e in eps_values]
    mid=cjs[len(cjs)//2]
    convs=[]
    for a,b in zip(cjs[:-1],cjs[1:]):
        A=np.asarray(a['J']['total']); B=np.asarray(b['J']['total']); convs.append(float(np.linalg.norm(A-B)/max(np.linalg.norm(A),np.linalg.norm(B),1e-12)))
    conv=float(max(convs)) if convs else 0.0
    rows=coupled_spectrum_analysis(mid['J']['total'],mi); abl=family_coupling_ablation(mid['J']['total'],mi)
    rpo=rpo_phase_scan(x,mi,rows,cfg=cfg,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    pl=phase_lock_diagnostics(rpo,mi,windows=int(cfg.get('phase_lock_windows',3)))
    fl=floquet_monodromy(x,mi,rpo,cfg=cfg,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    return dict(n_points=n,mode_names=mi['names'],mode_families=mi['families'],frame_stats={
        'curvature_mean':float(np.mean(mi['frame']['curvature'])),'curvature_rms':float(np.sqrt(np.mean(mi['frame']['curvature']**2))),
        'torsion_mean':float(np.mean(mi['frame']['torsion'])),'torsion_rms':float(np.sqrt(np.mean(mi['frame']['torsion']**2)))},
        jacobian_eps_values=eps_values,jacobian_convergence=conv,eigs=mid['eigs'],spectrum=rows,family_coupling_ablation=abl,rpo=rpo,phase_lock=pl,floquet=fl,
        jacobian_total=mid['J']['total'],jacobian_cross=mid['J']['cross_lobe'],modes=mi['modes'],geometry=x)
