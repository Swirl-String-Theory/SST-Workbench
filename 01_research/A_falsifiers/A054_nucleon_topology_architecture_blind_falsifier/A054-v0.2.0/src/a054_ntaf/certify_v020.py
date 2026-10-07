from __future__ import annotations
from pathlib import Path
import json, math, numpy as np

from .blind_geometry import load_components_npz, resample_closed_curve
from .physics import induced_velocity, qualify_backend, topology_drift, circulation_vector, mutual_filament_energy
from .modes_v020 import build_mode_basis, family_indices, split_state, flatten_components, tangents
from .seal import sha256_file


def _fit_rigid(components, vel_components):
    x=flatten_components(components); u=flatten_components(vel_components); xc=x.mean(0); r=x-xc
    A=np.zeros((3*len(x),6)); b=u.reshape(-1)
    for i,(rx,ry,rz) in enumerate(r):
        M=np.array([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]],float)
        A[3*i:3*i+3,:3]=np.eye(3); A[3*i:3*i+3,3:]=M
    q,*_=np.linalg.lstsq(A,b,rcond=None); fit=(A@q).reshape(-1,3)
    return q,u-fit


def _remove_tangential_gauge(components, vel_components):
    out=[]
    for c,v in zip(components,vel_components):
        t=tangents(c); vv=np.asarray(v,float)
        out.append(vv-np.einsum('ij,ij->i',vv,t)[:,None]*t)
    return out


def _vel_components(comps,gammas,core,backend,remove_tangent=True):
    vel=[induced_velocity(c,comps,gammas,core,backend=backend) for c in comps]
    return _remove_tangential_gauge(comps,vel) if remove_tangent else vel


def _rhs_flat(Y,sizes,gammas,core,backend):
    comps=split_state(Y,sizes)
    return flatten_components(_vel_components(comps,gammas,core,backend,remove_tangent=True))


def rk4_shape(components,gammas,core,dt,steps,backend):
    sizes=[len(c) for c in components]; Y=flatten_components(components).copy()
    for _ in range(int(steps)):
        k1=_rhs_flat(Y,sizes,gammas,core,backend)
        k2=_rhs_flat(Y+0.5*dt*k1,sizes,gammas,core,backend)
        k3=_rhs_flat(Y+0.5*dt*k2,sizes,gammas,core,backend)
        k4=_rhs_flat(Y+dt*k3,sizes,gammas,core,backend)
        Y += float(dt)*(k1+2*k2+2*k3+k4)/6.0
        if not np.isfinite(Y).all(): raise FloatingPointError('non-finite gauge-cleaned RK4 state')
    return split_state(Y,sizes)


def relative_residual(components,gammas,core,backend):
    vel=_vel_components(components,gammas,core,backend,remove_tangent=True); _q,urel=_fit_rigid(components,vel)
    scale=np.sqrt(np.mean(np.sum(flatten_components(vel)**2,axis=1)))
    return float(np.sqrt(np.mean(np.sum(urel**2,axis=1)))/max(scale,1e-15))


def reduced_rhs(components,gammas,core,mode_info,backend):
    vel=_vel_components(components,gammas,core,backend,remove_tangent=True); _q,urel=_fit_rigid(components,vel)
    return np.asarray([np.sum(b*urel) for b in mode_info['basis']],float)


def perturb(components,field,amp):
    sizes=[len(c) for c in components]; X=flatten_components(components)+float(amp)*np.asarray(field,float)
    return split_state(X,sizes)


def projected_jacobian(components,gammas,core,mode_info,eps,backend):
    B=mode_info['basis']; m=len(B); J=np.zeros((m,m))
    for j in range(m):
        fp=reduced_rhs(perturb(components,B[j],eps),gammas,core,mode_info,backend)
        fm=reduced_rhs(perturb(components,B[j],-eps),gammas,core,mode_info,backend)
        J[:,j]=(fp-fm)/(2*eps)
    return J


def jacobian_convergence(jacs):
    if len(jacs)<2: return 0.0
    return float(max(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-12) for a,b in zip(jacs[:-1],jacs[1:])))


def _spectral_metrics(A):
    A=np.asarray(A,float)
    if A.size==0: return {'max_real':None,'spectral_radius':None,'normalized_max_real':None,'eigenvalues':[]}
    vals=np.linalg.eigvals(A); scale=max(float(np.max(np.abs(vals))),1e-12); order=np.argsort(vals.real)[::-1]
    return {'max_real':float(np.max(vals.real)),'spectral_radius':float(np.max(np.abs(vals))),
            'normalized_max_real':float(np.max(vals.real)/scale),
            'eigenvalues':[{'re':float(z.real),'im':float(z.imag)} for z in vals[order]]}


def spectrum_summary(J,mode_info):
    vals,vecs=np.linalg.eig(J); scale=max(float(np.max(np.abs(vals))),1e-12); order=np.argsort(vals.real)[::-1]
    kidx=family_indices(mode_info,'kelvin'); kspec=_spectral_metrics(J[np.ix_(kidx,kidx)]) if kidx else _spectral_metrics(np.zeros((0,0)))
    return vals,vecs,{
        'max_real':float(np.max(vals.real)), 'spectral_radius':float(np.max(np.abs(vals))),
        'normalized_max_real':float(np.max(vals.real)/scale),
        'oscillatory_fraction':float(np.mean(np.abs(vals.imag)>1e-7*scale)),
        'eigenvalues':[{'re':float(z.real),'im':float(z.imag)} for z in vals[order]],
        'kelvin_restricted':kspec,
    }


def family_coupling_ablation(J,mode_info):
    full_eigs=np.linalg.eigvals(J); full_max=float(np.max(full_eigs.real)); scale=max(float(np.max(np.abs(full_eigs))),1e-12)
    out={}; n=len(J); allidx=np.arange(n)
    for fam in ('breathing','torsion','kelvin','separation'):
        idx=np.asarray(family_indices(mode_info,fam),int)
        if len(idx)==0: continue
        mask=set(int(x) for x in idx); other=np.asarray([i for i in allidx if int(i) not in mask],int)
        K=J.copy()
        if len(other): K[np.ix_(idx,other)]=0.0; K[np.ix_(other,idx)]=0.0
        dec=float(np.max(np.linalg.eigvals(K).real))
        out[fam]={'max_real_decoupled':dec,'stabilization_delta_norm':float((dec-full_max)/scale)}
    return out


def separation_energy_hessian(components,gammas,core,mode_info,eps):
    idx=family_indices(mode_info,'separation'); B=mode_info['basis']; m=len(idx); H=np.zeros((m,m)); E0=mutual_filament_energy(components,gammas,core)
    for aa,i in enumerate(idx):
        ep=mutual_filament_energy(perturb(components,B[i], eps),gammas,core); em=mutual_filament_energy(perturb(components,B[i],-eps),gammas,core)
        H[aa,aa]=(ep-2*E0+em)/(eps*eps)
        for bb in range(aa+1,m):
            j=idx[bb]
            epp=mutual_filament_energy(perturb(perturb(components,B[i],eps),B[j],eps),gammas,core)
            epm=mutual_filament_energy(perturb(perturb(components,B[i],eps),B[j],-eps),gammas,core)
            emp=mutual_filament_energy(perturb(perturb(components,B[i],-eps),B[j],eps),gammas,core)
            emm=mutual_filament_energy(perturb(perturb(components,B[i],-eps),B[j],-eps),gammas,core)
            H[aa,bb]=H[bb,aa]=(epp-epm-emp+emm)/(4*eps*eps)
    scale=max(abs(E0),1e-12); Hn=H/scale; ev=np.linalg.eigvalsh(0.5*(Hn+Hn.T)) if m else np.array([])
    return {'mutual_energy':float(E0),'normalized_hessian':Hn.tolist(),'eigenvalues':ev.tolist(),
            'min_eigenvalue':None if not len(ev) else float(ev.min()),'max_eigenvalue':None if not len(ev) else float(ev.max()),
            'status':'DIAGNOSTIC_ONLY_NOT_A_HARD_HAMILTONIAN_STABILITY_PROOF'}


def _kabsch_transform(reference,current):
    X=flatten_components(reference); Y=flatten_components(current); Xc=X-X.mean(0); Yc=Y-Y.mean(0)
    U,_S,Vt=np.linalg.svd(Yc.T@Xc); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    t=X.mean(0)-Y.mean(0)@R
    return R,t


def _best_shift(ref,cur):
    n=len(ref); best=(float('inf'),0)
    for k in range(n):
        q=np.roll(cur,k,axis=0); d=float(np.mean(np.sum((ref-q)**2,axis=1)))
        if d<best[0]: best=(d,k)
    return int(best[1])


def apply_relative_group(current,shifts,R,t):
    return [np.roll(np.asarray(c,float),int(k),axis=0)@np.asarray(R,float)+np.asarray(t,float) for c,k in zip(current,shifts)]


def best_relative_alignment(reference,current,iterations=2):
    work=[np.asarray(c,float).copy() for c in current]; shifts=[0]*len(work); R=np.eye(3); tr=np.zeros(3)
    for _ in range(max(1,int(iterations))):
        R,tr=_kabsch_transform(reference,work); aligned=[c@R+tr for c in work]
        delta=[]
        for ref,cur in zip(reference,aligned): delta.append(_best_shift(np.asarray(ref,float),cur))
        if not any(delta): break
        shifts=[(a+b)%len(c) for a,b,c in zip(shifts,delta,work)]
        work=[np.roll(c,k,axis=0) for c,k in zip(work,delta)]
    R,tr=_kabsch_transform(reference,work); aligned=[c@R+tr for c in work]
    X=flatten_components(reference); Y=flatten_components(aligned); rg=np.sqrt(np.mean(np.sum((X-X.mean(0))**2,axis=1)))
    rms=float(np.sqrt(np.mean(np.sum((Y-X)**2,axis=1)))/max(rg,1e-15))
    return {'aligned':aligned,'shifts':shifts,'rotation':R,'translation':tr,'rms_over_rg':rms}


def _shape(reference,current): return best_relative_alignment(reference,current)['rms_over_rg']


def _min_intercomponent_distance(components):
    best=np.inf
    for i in range(len(components)):
        for j in range(i+1,len(components)):
            a=np.asarray(components[i]); b=np.asarray(components[j])
            best=min(best,float(np.min(np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2))))
    return float(best)


def restoring_probe(components,gammas,core,mode_info,amp,dt,steps,backend):
    idx=family_indices(mode_info,'separation'); B=mode_info['basis']; rows=[]; base_min=_min_intercomponent_distance(components)
    for i in idx:
        ratios=[]; clear=[]; signed=[]
        for sign in (-1.,1.):
            init=perturb(components,B[i],sign*amp); initial_dist=max(_shape(components,init),1e-12)
            fin=rk4_shape(init,gammas,core,dt,steps,backend); final_dist=_shape(components,fin)
            ratios.append(final_dist/initial_dist); signed.append({'sign':sign,'initial':initial_dist,'final':final_dist})
            clear.append(_min_intercomponent_distance(fin)/max(base_min,1e-12))
        rows.append({'mode':mode_info['names'][i],'return_ratio_median':float(np.median(ratios)),
                     'return_ratios':[float(x) for x in ratios],'signed':signed,'min_clearance_ratio':float(min(clear))})
    return rows


def ringdown_probe(components,gammas,core,mode_info,vec,amp,dt,steps,stride,backend):
    field=np.tensordot(np.asarray(vec),mode_info['basis'],axes=(0,0)).real; field/=max(np.linalg.norm(field),1e-12)
    init=perturb(components,field,amp); cur=[c.copy() for c in init]; vals=[_shape(components,cur)]; topo=[topology_drift(components,cur)]
    base_min=_min_intercomponent_distance(components); clears=[_min_intercomponent_distance(cur)/max(base_min,1e-12)]
    for s in range(int(steps)):
        cur=rk4_shape(cur,gammas,core,dt,1,backend)
        if (s+1)%max(1,int(stride))==0:
            vals.append(_shape(components,cur)); topo.append(topology_drift(components,cur)); clears.append(_min_intercomponent_distance(cur)/max(base_min,1e-12))
    initial=max(vals[0],1e-12)
    return {'initial_shape':float(vals[0]),'max_shape':float(max(vals)),'final_shape':float(vals[-1]),
            'max_over_initial':float(max(vals)/initial),'final_over_initial':float(vals[-1]/initial),
            'max_linking_drift':float(max(topo)),'min_clearance_ratio':float(min(clears)),'trace':[float(x) for x in vals]}


def choose_oscillatory_mode(vals,vecs,mode_info):
    best=None; scale=max(float(np.max(np.abs(vals))),1e-12)
    for i,z in enumerate(vals):
        if abs(z.imag)<1e-7*scale: continue
        v=vecs[:,i]; den=max(float(np.sum(np.abs(v)**2)),1e-30); fam={}
        for f in ('breathing','torsion','kelvin'):
            ix=family_indices(mode_info,f); fam[f]=float(np.sum(np.abs(v[ix])**2)/den) if ix else 0.0
        score=min(fam.values())
        item=(score,abs(z.imag),i,fam)
        if best is None or item[:2]>best[:2]: best=item
    return best


def rpo_scan(components,gammas,core,mode_info,vals,vecs,cfg,backend):
    sel=choose_oscillatory_mode(vals,vecs,mode_info)
    if sel is None: return {'accepted':False,'reason':'no_oscillatory_mode'}
    score,_omega,ii,fam=sel; v=vecs[:,ii]; phases=int(cfg['rpo_phase_count']); amp=float(cfg['rpo_amp']); dt=float(cfg['rpo_dt']); steps=int(cfg['rpo_steps']); stride=int(cfg['rpo_stride'])
    best=None; rows=[]; base_min=_min_intercomponent_distance(components)
    for p in range(phases):
        phi=2*np.pi*p/phases; vr=(np.exp(1j*phi)*v).real; f=np.tensordot(vr,mode_info['basis'],axes=(0,0)); f/=max(np.linalg.norm(f),1e-12)
        init=perturb(components,f,amp); cur=[c.copy() for c in init]; trace=[]
        for s in range(steps):
            cur=rk4_shape(cur,gammas,core,dt,1,backend)
            if (s+1)%stride==0:
                al=best_relative_alignment(init,cur); trace.append((s+1,al['rms_over_rg'],topology_drift(init,cur),_min_intercomponent_distance(cur)/max(base_min,1e-12),al))
        if not trace: continue
        peak=max(x[1] for x in trace); start=max(1,int(math.ceil(cfg['rpo_min_step_fraction']*len(trace)))); later=trace[start:]; ret=min(later,key=lambda x:x[1]) if later else trace[-1]
        ok=bool(peak>=cfg['rpo_excursion_min'] and ret[1]<=cfg['rpo_recurrence_max'] and ret[1]/max(peak,1e-12)<=cfg['rpo_return_ratio_max'] and ret[2]<=cfg['max_linking_drift'] and ret[3]>=cfg['min_clearance_ratio_min'])
        row={'phase_index':p,'peak_shape':float(peak),'best_step':int(ret[0]),'best_time':float(ret[0]*dt),'recurrence':float(ret[1]),'linking_drift':float(ret[2]),'clearance_ratio':float(ret[3]),'accepted':ok,
             'relative_group':{'shifts':[int(x) for x in ret[4]['shifts']],'rotation':np.asarray(ret[4]['rotation']).tolist(),'translation':np.asarray(ret[4]['translation']).tolist()}}
        rows.append(row)
        if ok and (best is None or row['recurrence']<best['recurrence']): best=row|{'initial':init}
    return {'accepted':best is not None,'selected_eigenvalue':{'re':float(vals[ii].real),'im':float(vals[ii].imag)},'family_participation':fam,'coupling_score':float(score),'scan':rows,'best':best}


def relative_return_monodromy(components,gammas,core,mode_info,rpo,cfg,backend):
    """Finite-difference derivative of the nonlinear time-T relative return map.

    This is a *projected physical-subspace* monodromy: the flow map is nonlinear and evolved for
    the accepted RPO period, while input/output variations are restricted to the preregistered
    non-rigid/tangential-quotiented mode basis. It is not a proof of the infinite-dimensional
    Euler spectrum.
    """
    if not rpo.get('accepted'): return {'evaluated':False,'status':'NOT_EVALUATED_NO_RPO'}
    base=rpo['best']['initial']; steps=int(rpo['best']['best_step']); dt=float(cfg['rpo_dt']); group=rpo['best']['relative_group']
    shifts=group['shifts']; R=np.asarray(group['rotation'],float); tr=np.asarray(group['translation'],float)
    terminal=rk4_shape(base,gammas,core,dt,steps,backend); baseR=apply_relative_group(terminal,shifts,R,tr); rec=_shape(base,baseR)
    if rec>float(cfg['floquet_base_recurrence_max']):
        return {'evaluated':False,'status':'NOT_EVALUATED_BASE_CLOSURE_FAILED','base_relative_map_residual':float(rec)}
    m=min(int(cfg['floquet_modes_max']),len(mode_info['basis'])); idx=list(range(m)); eps=float(cfg['floquet_eps']); M=np.zeros((m,m)); B=mode_info['basis']
    for jj,j in enumerate(idx):
        fp=rk4_shape(perturb(base,B[j],eps),gammas,core,dt,steps,backend); fm=rk4_shape(perturb(base,B[j],-eps),gammas,core,dt,steps,backend)
        fp=apply_relative_group(fp,shifts,R,tr); fm=apply_relative_group(fm,shifts,R,tr)
        dp=flatten_components(fp)-flatten_components(base); dm=flatten_components(fm)-flatten_components(base)
        for ii,i in enumerate(idx): M[ii,jj]=(np.sum(B[i]*dp)-np.sum(B[i]*dm))/(2*eps)
    mu=np.linalg.eigvals(M); neutral=int(np.argmin(np.abs(mu-1))) if len(mu) else -1; remain=np.delete(mu,neutral) if len(mu)>1 else np.array([]); mx=float(np.max(np.abs(remain))) if len(remain) else 0.0
    return {'evaluated':True,'status':'PROJECTED_RELATIVE_MONODROMY_EVALUATED','base_relative_map_residual':float(rec),
            'period_steps':steps,'period_time':float(steps*dt),'mode_indices':idx,
            'multipliers':[{'re':float(z.real),'im':float(z.imag),'abs':float(abs(z))} for z in mu],
            'neutral_index':neutral,'max_nontrivial_abs':mx,'monodromy':M.tolist(),
            'scope':'NONLINEAR_TIME_T_RETURN_MAP_PROJECTED_TO_PREREGISTERED_PHYSICAL_SUBSPACE'}


# Backward-compatible explicit scientific name used by tests/documentation.
projected_relative_monodromy = relative_return_monodromy


def _timed_cfg(cfg,n):
    x=dict(cfg); scale=(float(cfg['n_ref'])/float(n))**2
    for name in ('restoring','ringdown','rpo'):
        dt=float(cfg[f'{name}_dt_ref'])*scale; T=float(cfg[f'{name}_T_final']); steps=max(1,int(math.ceil(T/dt))); dt=T/steps
        x[f'{name}_dt']=dt; x[f'{name}_steps']=steps
    return x


def certify_case(components,sector,cfg,backend,full_nonlinear=True):
    total_L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in components); core=float(cfg['core_ratio'])*total_L; gammas=circulation_vector(3,sector)
    mi=build_mode_basis(components,tuple(cfg['kelvin_harmonics']),True,True); rel=relative_residual(components,gammas,core,backend)
    jacs=[projected_jacobian(components,gammas,core,mi,float(e),backend) for e in cfg['jacobian_eps_values']]; conv=jacobian_convergence(jacs); J=jacs[-1]; vals,vecs,spec=spectrum_summary(J,mi)
    hess=separation_energy_hessian(components,gammas,core,mi,float(cfg['hessian_eps'])); ablation=family_coupling_ablation(J,mi)
    restore=restoring_probe(components,gammas,core,mi,float(cfg['restoring_amp']),float(cfg['restoring_dt']),int(cfg['restoring_steps']),backend); restore_max=max(r['return_ratio_median'] for r in restore); clear_min=min(r['min_clearance_ratio'] for r in restore)
    kelvin_norm=(spec['kelvin_restricted'] or {}).get('normalized_max_real')
    gates={
        'C0_jacobian_epsilon_converged':conv<=cfg['jacobian_convergence_max'],
        'C1_relative_equilibrium_diagnostic':bool(np.isfinite(rel)),
        'C2_restoring_bounded':restore_max<=cfg['restoring_return_ratio_max'] and clear_min>=cfg['min_clearance_ratio_min'],
        'C3_kelvin_local_bounded':spec['normalized_max_real']<=cfg['normalized_growth_max'] and (kelvin_norm is None or kelvin_norm<=cfg['kelvin_restricted_normalized_growth_max']),
    }
    out={'mode_count':len(mi['basis']),'mode_names':mi['names'],'families':mi['families'],'relative_equilibrium_residual':rel,
         'jacobian_convergence':conv,'spectrum':spec,'family_coupling_ablation':ablation,'separation_energy_hessian':hess,'restoring':restore,'gates':gates,
         'relative_equilibrium_method_band':bool(rel<=cfg['relative_equilibrium_residual_diagnostic_max']),'C1_policy':'DIAGNOSTIC_ONLY_NOT_USED_IN_CERTIFICATION'}
    if not full_nonlinear:
        out['status']='LOCAL_NUMERICALLY_QUALIFIED' if gates['C0_jacobian_epsilon_converged'] else 'INCONCLUSIVE_NUMERICAL'; return out
    dom=int(np.argmax(vals.real)); ring=ringdown_probe(components,gammas,core,mi,vecs[:,dom],float(cfg['ringdown_amp']),float(cfg['ringdown_dt']),int(cfg['ringdown_steps']),int(cfg['ringdown_stride']),backend)
    rpo=rpo_scan(components,gammas,core,mi,vals,vecs,cfg,backend); floq=relative_return_monodromy(components,gammas,core,mi,rpo,cfg,backend)
    gates['C4_ringdown_bounded']=bool(ring['max_over_initial']<=cfg['ringdown_max_over_initial'] and ring['max_linking_drift']<=cfg['max_linking_drift'] and ring['min_clearance_ratio']>=cfg['min_clearance_ratio_min'])
    gates['C5_RPO_recurrence']=bool(rpo.get('accepted'))
    gates['C6_projected_relative_Floquet_bounded']=None if not floq.get('evaluated') else bool(floq.get('max_nontrivial_abs',np.inf)<=cfg['floquet_spectral_radius_max'])
    hard_keys=['C0_jacobian_epsilon_converged','C2_restoring_bounded','C3_kelvin_local_bounded','C4_ringdown_bounded']
    hard=all(bool(gates[k]) for k in hard_keys)
    if not gates['C0_jacobian_epsilon_converged']: status='INCONCLUSIVE_NUMERICAL'
    elif hard: status='CERTIFIED_RESTORING_KELVIN_RINGDOWN_BRANCH'
    else: status='NOT_CERTIFIED_DYNAMICAL'
    if hard and gates['C5_RPO_recurrence'] and gates['C6_projected_relative_Floquet_bounded'] is True:
        status='CERTIFIED_RPO_PROJECTED_FLOQUET_BRANCH'
    out.update({'status':status,'ringdown':ring,'rpo':{k:v for k,v in rpo.items() if k!='best'},'floquet':floq})
    return out


def _spatial_convergence(rows,cfg):
    if len(rows)<2: return True,[]
    a,b=rows[-2],rows[-1]; reasons=[]
    metrics=[
        ('normalized_growth',a['spectrum']['normalized_max_real'],b['spectrum']['normalized_max_real'],cfg['spatial_normalized_growth_abs_max']),
        ('kelvin_growth',a['spectrum']['kelvin_restricted'].get('normalized_max_real'),b['spectrum']['kelvin_restricted'].get('normalized_max_real'),cfg['spatial_kelvin_growth_abs_max']),
        ('relative_equilibrium',a['relative_equilibrium_residual'],b['relative_equilibrium_residual'],cfg['spatial_rel_eq_abs_max']),
        ('restoring_ratio',max(r['return_ratio_median'] for r in a['restoring']),max(r['return_ratio_median'] for r in b['restoring']),cfg['spatial_restoring_ratio_abs_max']),
    ]
    for name,x,y,tol in metrics:
        if x is None or y is None: continue
        d=abs(float(x)-float(y))
        if d>float(tol): reasons.append(f'{name}:{d:.6g}>{tol}')
    return not reasons,reasons


def run_certification(campaign:Path,config_path:Path):
    campaign=Path(campaign); cfg=json.loads(Path(config_path).read_text(encoding='utf-8')); frozen=campaign/'CERT_CONFIG.json'; frozen.write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    manifest=json.loads((campaign/'BLIND_MANIFEST.json').read_text(encoding='utf-8')); bq=qualify_backend(cfg.get('backend_policy','prefer_native')); (campaign/'BACKEND_QUALIFICATION.json').write_text(json.dumps(bq,indent=2)+'\n')
    if not bq['qualified']: raise RuntimeError('backend qualification failed: '+str(bq))
    backend=bq['backend']; results=[]; ladder=sorted(int(x) for x in cfg['n_ladder']); maxN=max(ladder)
    for row in manifest['candidates']:
        base=load_components_npz(campaign/'blind_inputs'/row['file'])
        for sec in cfg['circulation_sectors']:
            sector_rows=[]
            for n in ladder:
                comps=[resample_closed_curve(c,n) for c in base]; cn=_timed_cfg(cfg,n)
                try: rec=certify_case(comps,sec,cn,backend,full_nonlinear=(n==maxN))
                except Exception as e: rec={'status':'INCONCLUSIVE_NUMERICAL','error':f'{type(e).__name__}: {e}','gates':{}}
                rr={'anonymous_id':row['anonymous_id'],'sector':sec,'N':n,**rec}; results.append(rr); sector_rows.append(rr)
            valid=[r for r in sector_rows if 'spectrum' in r]
            ok,reasons=_spatial_convergence(valid,cfg) if valid else (False,['no_valid_resolution'])
            results.append({'anonymous_id':row['anonymous_id'],'sector':sec,'N':'SUMMARY','spatial_converged':ok,'spatial_reasons':reasons})
    out={'schema':'A054-CERT-BLIND-RESULTS-2.0','backend':backend,'results':results}; rp=campaign/'CERT_RESULTS_BLIND.json'; rp.write_text(json.dumps(out,indent=2)+'\n')
    ana=analyze_certification(out,cfg); ap=campaign/'CERT_ANALYSIS_BLIND.json'; ap.write_text(json.dumps(ana,indent=2)+'\n'); reportp=campaign/'CERT_REPORT_BLIND.md'; reportp.write_text(render_cert_report(ana),encoding='utf-8')
    seal={'schema':'A054-CERT-BLIND-SEAL-2.0','manifest_sha256':sha256_file(campaign/'BLIND_MANIFEST.json'),'results_sha256':sha256_file(rp),'analysis_sha256':sha256_file(ap),'report_sha256':sha256_file(reportp),'config_sha256':sha256_file(frozen),'backend_qualification_sha256':sha256_file(campaign/'BACKEND_QUALIFICATION.json'),'private_mapping_commitment':manifest['private_mapping_sha256']}
    (campaign/'CERT_BLIND_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n'); return ana


def analyze_certification(out,cfg):
    fine=max(int(x) for x in cfg['n_ladder']); by={}; summaries={}
    for r in out['results']: by.setdefault((r['anonymous_id'],r['sector']),[]).append(r)
    peraid={}
    for (aid,sec),rows in by.items():
        sr=next((r for r in rows if r.get('N')=='SUMMARY'),None); fr=next((r for r in rows if r.get('N')==fine),None)
        if fr is None: continue
        status=fr['status']
        if sr and not sr['spatial_converged']: status='INCONCLUSIVE_NUMERICAL'
        peraid.setdefault(aid,{})[sec]={'status':status,'spatial_converged':None if sr is None else sr['spatial_converged'],'spatial_reasons':[] if sr is None else sr['spatial_reasons'],'fine_gates':fr.get('gates',{}),'fine_metrics':{'normalized_growth':(fr.get('spectrum') or {}).get('normalized_max_real'),'kelvin_growth':((fr.get('spectrum') or {}).get('kelvin_restricted') or {}).get('normalized_max_real'),'rel_eq':fr.get('relative_equilibrium_residual'),'ringdown_max_over_initial':(fr.get('ringdown') or {}).get('max_over_initial'),'floquet_max_abs':(fr.get('floquet') or {}).get('max_nontrivial_abs'),'floquet_status':(fr.get('floquet') or {}).get('status')}}
    for aid,secs in peraid.items():
        opp=[secs.get(q,{}) for q in ('Q1','Q2','Q3')]
        cert=sum(str(x.get('status','')).startswith('CERTIFIED_') for x in opp)
        floq=sum(x.get('status')=='CERTIFIED_RPO_PROJECTED_FLOQUET_BRANCH' for x in opp)
        summaries[aid]={'sectors':secs,'one_opposed_certified_count':cert,'one_opposed_floquet_count':floq,'at_least_two_one_opposed_certified':cert>=2,'all_same_status':secs.get('Q0',{}).get('status')}
    return {'schema':'A054-CERT-BLIND-ANALYSIS-2.0','backend':out['backend'],'summaries':summaries,
            'interpretation_guard':'No semantic identity or designated slot is available to the blind certification layer. Spatial convergence is required before physical status. The Floquet gate is evaluated only after an accepted nontrivial RPO and is the nonlinear relative time-T map projected to a preregistered physical subspace; it is not an infinite-dimensional Euler stability proof.'}


def render_cert_report(a):
    lines=['# A054 v0.2.0 — BLIND dynamical certification','',
           'No semantic skeleton/knot mapping is available to this runner. Spatial convergence precedes interpretation. Floquet is evaluated only after accepted RPO recurrence and refers to the nonlinear relative return map projected to the preregistered physical subspace.','',
           '| anonymous | opposed certified | opposed projected-Floquet | +++ status |','|---|---:|---:|---|']
    for aid,s in sorted(a['summaries'].items()): lines.append(f"| `{aid}` | {s['one_opposed_certified_count']} | {s['one_opposed_floquet_count']} | {s['all_same_status']} |")
    return '\n'.join(lines)+'\n'
