from __future__ import annotations
from pathlib import Path
import json,numpy as np
from .geometry import curve_length,resample_closed,closure_gap_ratio,normalized_mode_power,mode_corr,gauss_linking
from .phase import winding,sampling_windings,phase_purity
from .pressure import poisson_residual,green_relative
from .spectral import peak_set,peak_cv,finite_size_collapse,dominant_mode_under_sampling
from .representation import relative_difference,even_odd,commutator_scaled

try:
    from native_ext import native
except Exception:
    native=None

def gate(status,name,**metrics): return {'gate':name,'status':status,'metrics':metrics}

def _load_components(casefile):
    z=np.load(casefile)
    return [z[k] for k in sorted(z.files) if k.startswith('component_')]

def _scalar(z,key,default=None):
    if key not in z.files: return default
    a=z[key]
    if np.asarray(a).ndim==0: return np.asarray(a).item()
    return a

def run_case(cdir:Path,case_id:str,cfg:dict,mode='basic'):
    out=[]; comps=_load_components(cdir/f'{case_id}.npz')
    # G00 data integrity/closure
    gaps=[closure_gap_ratio(c) for c in comps]
    finite=all(np.isfinite(c).all() and len(c)>=16 for c in comps)
    ok=finite and max(gaps)<=cfg['closure_gap_rel_max']
    out.append(gate('PASS' if ok else 'FAIL','G00_geometry_input',n_components=len(comps),closure_gap_ratios=gaps,finite=finite))
    # G01 resampling convergence and low-mode stability
    ns=cfg['resample_ns']; all_len=[]; corrs=[]
    for c in comps:
        lengths=[]; powers=[]
        for n in ns:
            r=resample_closed(c,n); lengths.append(curve_length(r)); powers.append(normalized_mode_power(r))
        all_len.append(lengths)
        corrs.extend(mode_corr(powers[i],powers[i+1]) for i in range(len(powers)-1))
    rels=[]
    for L in all_len:
        rels.append(abs(L[-1]-L[-2])/(abs(L[-1])+1e-300) if len(L)>1 else 0.)
    ok=max(rels)<=cfg['length_conv_rel_max'] and (min(corrs) if corrs else 1)>=cfg['mode_shape_corr_min']
    out.append(gate('PASS' if ok else 'FAIL','G01_resolution_convergence',lengths=all_len,last_step_relative=rels,mode_correlations=corrs))
    # G02 topology-layer epistemic guard: static curves never promote phase/vorticity claims
    phasefile=cdir/f'{case_id}.phase.npy'
    out.append(gate('REFERENCE_ONLY','G02_topology_layer_guard',centerline_available=True,phase_available=phasefile.exists(),vorticity_volume_available=(cdir/f'{case_id}.field.npz').exists(),claim='no cross-layer equality inferred'))
    # G03 centerline linking: geometric diagnostic only
    pair_links=[]
    for i in range(len(comps)):
        for j in range(i+1,len(comps)):
            if native is not None:
                lk=float(native.gauss_linking(np.asarray(comps[i],float),np.asarray(comps[j],float)))
                backend='cpp'
            else:
                lk=float(gauss_linking(comps[i],comps[j])); backend='python'
            pair_links.append({'i':i,'j':j,'gauss_linking':lk,'nearest_integer':int(round(lk)),'integer_residual':abs(lk-round(lk))})
    out.append(gate('REFERENCE_ONLY','G03_centerline_linking',pairs=pair_links,backend=('none' if not pair_links else backend),claim='centerline-only; no phase/vorticity identification'))
    # phase
    if phasefile.exists():
        phi=np.load(phasefile); ww=sampling_windings(phi,tuple(n for n in (32,64,128,256,512) if n<=len(phi)))
        vals=np.array([x[1] for x in ww]); wfinal=float(vals[-1]); nearest=round(wfinal)
        spread=float(np.ptp(vals)) if len(vals)>1 else 0.
        ok=abs(wfinal-nearest)<=cfg['phase_integer_tol'] and spread<=cfg['phase_sampling_spread_max']
        purity=phase_purity(phi,32)
        out.append(gate('PASS' if ok else 'FAIL','G10_phase_closure',sampling=ww,nearest_integer=int(nearest),spread=spread,purity=purity))
        aliases=dominant_mode_under_sampling(phi,tuple(n for n in (32,64,128,256,512) if n<=len(phi)))
        modes=[x[1] for x in aliases]
        aok=(len(modes)>0 and len(set(modes))==1 and modes[-1]==nearest)
        out.append(gate('PASS' if aok else 'FAIL','G11_phase_sampling_alias_guard',dominant_modes=aliases,target_integer=int(nearest)))
    else:
        out.append(gate('INDETERMINATE','G10_phase_closure',reason='no .phase.npy sidecar'))
        out.append(gate('INDETERMINATE','G11_phase_sampling_alias_guard',reason='no .phase.npy sidecar'))
    # Euler field
    fieldfile=cdir/f'{case_id}.field.npz'
    if fieldfile.exists():
        z=np.load(fieldfile,allow_pickle=True); v=z['v']; p=z['p']; dx=_scalar(z,'dx',1.0); rho=float(_scalar(z,'rho_f',cfg.get('rho_f',7e-7))); boundary=str(_scalar(z,'boundary','nonperiodic'))
        pr=poisson_residual(v,p,dx,rho,boundary)
        ok=pr['relative']<=cfg['pressure_poisson_rel_max']
        out.append(gate('PASS' if ok else 'FAIL','G20_pressure_poisson',relative=pr['relative'],div_relative=pr['div_relative'],boundary=boundary,rho_f=rho))
        out.append(gate('REFERENCE_ONLY','G22_pressure_source_ledger',qomega_l2=pr['qomega_l2'],qstrain_l2=pr['qstrain_l2'],net_source_l2=pr['source_l2'],vorticity_dominated_fraction=pr['vorticity_dominated_fraction'],enstrophy_over_strain=pr['qomega_l2']/(pr['qstrain_l2']+1e-300)))
        if boundary.lower()=='periodic':
            gr=green_relative(pr['source'],pr['pi'],dx); ok2=gr<=cfg['green_rel_max']
            out.append(gate('PASS' if ok2 else 'FAIL','G21_green_closure',relative=gr,boundary='periodic'))
        else: out.append(gate('INDETERMINATE','G21_green_closure',reason='v0.1.1 implements Green closure only for periodic domains'))
    else:
        out.append(gate('INDETERMINATE','G20_pressure_poisson',reason='no .field.npz sidecar'))
        out.append(gate('INDETERMINATE','G21_green_closure',reason='no .field.npz sidecar'))
        out.append(gate('INDETERMINATE','G22_pressure_source_ledger',reason='no .field.npz sidecar'))
    # dynamic spectroscopy
    tsfile=cdir/f'{case_id}.timeseries.npz'
    if tsfile.exists():
        z=np.load(tsfile,allow_pickle=True); peaks=peak_set(z['t'],z['signals']); cv=peak_cv(peaks)
        met={'peaks':peaks.tolist(),'peak_cv':None if np.isnan(cv) else cv}
        if 'L' in z.files:
            # Finite-size campaigns are expected to move in raw frequency.  Do not
            # misclassify that physical scaling as failed run-to-run repeatability.
            fc=finite_size_collapse(peaks,z['L']); met['freq_times_L_cv']=None if np.isnan(fc) else fc
            out.append(gate('REFERENCE_ONLY','G30_spectral_repeatability',**met,note='raw peak CV is descriptive because L varies'))
            fmax=cfg.get('spectral_collapse_cv_max',cfg['spectral_peak_cv_max'])
            fok=(not np.isnan(fc) and fc<=fmax)
            out.append(gate('PASS' if fok else 'FAIL','G31_finite_size_spectral_collapse',freq_times_L_cv=None if np.isnan(fc) else fc,threshold=fmax))
        else:
            ok=np.isnan(cv) or cv<=cfg['spectral_peak_cv_max']
            out.append(gate('PASS' if ok else 'FAIL','G30_spectral_repeatability',**met))
            out.append(gate('INDETERMINATE','G31_finite_size_spectral_collapse',reason='no L array in .timeseries.npz'))
    else:
        out.append(gate('INDETERMINATE','G30_spectral_repeatability',reason='no .timeseries.npz sidecar'))
        out.append(gate('INDETERMINATE','G31_finite_size_spectral_collapse',reason='no .timeseries.npz sidecar'))
    # circulation reversal classifier
    ppfile=cdir/f'{case_id}.probe_pair.npz'
    if ppfile.exists():
        z=np.load(ppfile); eo=even_odd(z['plus'],z['minus'])
        out.append(gate('REFERENCE_ONLY','G40_even_odd_reversal',even_norm=eo['even_norm'],odd_norm=eo['odd_norm'],odd_over_even=eo['odd_over_even']))
    else: out.append(gate('INDETERMINATE','G40_even_odd_reversal',reason='no .probe_pair.npz sidecar'))
    # representation invariance and commutator
    rfile=cdir/f'{case_id}.repr.npz'
    if rfile.exists():
        z=np.load(rfile); rel=relative_difference(z['A'],z['B']); ok=rel<=cfg['representation_rel_max']; met={'relative':rel}
        if 'residual' in z.files: met['difference_over_residual']=float(np.linalg.norm((z['A']-z['B']).ravel())/(np.linalg.norm(z['residual'].ravel())+1e-300))
        if all(k in z.files for k in ('AB','BA','eps')): met['commutator_over_eps2']=commutator_scaled(z['AB'],z['BA'],np.asarray(z['eps']).item())
        out.append(gate('PASS' if ok else 'FAIL','G50_representation_invariance',**met))
        if all(k in z.files for k in ('AB_seq','BA_seq','eps_seq')):
            epss=np.asarray(z['eps_seq'],float).reshape(-1); ABs=np.asarray(z['AB_seq']); BAs=np.asarray(z['BA_seq'])
            vals=[commutator_scaled(ABs[i],BAs[i],epss[i]) for i in range(len(epss))]
            tail=np.asarray(vals[-min(3,len(vals)):],float); cv=float(np.std(tail)/(np.mean(np.abs(tail))+1e-300))
            thresh=cfg.get('commutator_tail_cv_max',0.1); cok=cv<=thresh
            out.append(gate('PASS' if cok else 'FAIL','G51_commutator_refinement',eps=epss.tolist(),commutator_over_eps2=vals,tail_cv=cv,threshold=thresh))
        else:
            out.append(gate('INDETERMINATE','G51_commutator_refinement',reason='no AB_seq/BA_seq/eps_seq arrays'))
    else:
        out.append(gate('INDETERMINATE','G50_representation_invariance',reason='no .repr.npz sidecar'))
        out.append(gate('INDETERMINATE','G51_commutator_refinement',reason='no .repr.npz sidecar'))
    return out

def summarize_case(gates):
    hard={'G00_geometry_input','G01_resolution_convergence','G10_phase_closure','G11_phase_sampling_alias_guard','G20_pressure_poisson','G21_green_closure','G30_spectral_repeatability','G31_finite_size_spectral_collapse','G50_representation_invariance','G51_commutator_refinement'}
    fails=[g for g in gates if g['gate'] in hard and g['status']=='FAIL']
    available=[g for g in gates if g['gate'] in hard and g['status'] in ('PASS','FAIL')]
    if fails: return 'FAIL'
    # Static-centerline completion alone is a computational PASS, not a physical SST closure.
    if len(available)<=2: return 'INDETERMINATE'
    return 'PASS_WITH_AVAILABLE_GATES'
