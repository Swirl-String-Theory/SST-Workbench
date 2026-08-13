from __future__ import annotations
import csv, hashlib, json, math, sys
from pathlib import Path
from typing import Any
import numpy as np
from . import _config

ALLOWED_CONFIG_KEYS={
 'n_nodes','ring_radius_over_core','q_min','q_max','q_step','image_shell','fd_eps_over_core','core_model','threads','neutral_modes','eig_zero_tol','residual_max'
}
FD_NOISE_SAFETY=100.0

def write_json(path,data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,indent=2),encoding='utf-8')
def write_csv(path,rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if not rows: p.write_text('',encoding='utf-8'); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with p.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=keys); w.writeheader(); w.writerows(rows)

def validate_config(cfg:dict[str,Any])->dict[str,Any]:
    unknown=set(cfg)-ALLOWED_CONFIG_KEYS
    if unknown: raise ValueError(f'unknown/non-preregistered config keys: {sorted(unknown)}')
    out={
      'n_nodes':int(cfg.get('n_nodes',32)), 'ring_radius_over_core':float(cfg.get('ring_radius_over_core',4.0)),
      'q_min':float(cfg.get('q_min',2.31)), 'q_max':float(cfg.get('q_max',4.10)), 'q_step':float(cfg.get('q_step',0.025)),
      'image_shell':int(cfg.get('image_shell',2)), 'fd_eps_over_core':float(cfg.get('fd_eps_over_core',1e-4)),
      'core_model':int(cfg.get('core_model',0)), 'threads':int(cfg.get('threads',1)), 'neutral_modes':int(cfg.get('neutral_modes',6)),
      'eig_zero_tol':float(cfg.get('eig_zero_tol',1e-8)), 'residual_max':float(cfg.get('residual_max',5e-2)),
    }
    if out['n_nodes']<8 or out['n_nodes']%2: raise ValueError('n_nodes must be even and >=8')
    if not (out['ring_radius_over_core']>1): raise ValueError('ring_radius_over_core must be >1')
    q_geom=math.log(2*(out['ring_radius_over_core']+1))
    if out['q_min']<=q_geom: raise ValueError(f'q_min must exceed geometric non-overlap bound {q_geom:.12g}')
    if not(out['q_max']>out['q_min'] and out['q_step']>0): raise ValueError('invalid q range')
    if out['image_shell']<0 or out['image_shell']>3: raise ValueError('image_shell must be 0..3')
    if out['core_model'] not in (0,1,2): raise ValueError('core_model must be 0,1,2')
    if out['threads']<1: raise ValueError('threads must be >=1')
    if not (0.0 < out['fd_eps_over_core'] < 0.1): raise ValueError('fd_eps_over_core must lie in (0,0.1)')
    return out

def config_hash(cfg): return hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _load_cpp_backend(force_build=False,build_verbose=False):
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build,verbose=build_verbose)
        return __import__(f'{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}',fromlist=['*'])
    except Exception as exc:
        if build_verbose: print(f'{_config.LOG_PREFIX} native unavailable: {exc}',file=sys.stderr)
        return None

def _backend(force_python=False,force_build=False,build_verbose=False):
    if not force_python:
        b=_load_cpp_backend(force_build=force_build,build_verbose=build_verbose)
        if b is not None: return b,'cpp'
    from . import fallback
    return fallback,'python'

def _eig_sort(eig,vec):
    order=np.lexsort((eig.imag,eig.real,np.abs(eig)))
    return eig[order],vec[:,order]

def _normalize_columns(v):
    out=np.array(v,dtype=complex,copy=True)
    n=np.linalg.norm(out,axis=0); n=np.where(n>0,n,1.0); out/=n
    return out

def _track_modes(prev_vecs,eig,vecs):
    """Greedy phase-invariant eigenvector-overlap tracking. Diagnostic, not a theorem."""
    cur=_normalize_columns(vecs)
    if prev_vecs is None:
        e,v=_eig_sort(eig,cur)
        return e,v,[1.0]*len(e)
    prev=_normalize_columns(prev_vecs)
    overlap=np.abs(prev.conj().T@cur)**2
    unused=set(range(cur.shape[1])); chosen=[]; scores=[]
    for i in range(prev.shape[1]):
        if not unused: break
        j=max(unused,key=lambda k: float(overlap[i,k])); unused.remove(j)
        chosen.append(j); scores.append(float(overlap[i,j]))
    chosen.extend(sorted(unused))
    if len(scores)<len(chosen): scores.extend([0.0]*(len(chosen)-len(scores)))
    return eig[chosen],cur[:,chosen],scores

def _neutral_basis(Jself,c):
    _,svals,vh=np.linalg.svd(Jself)
    kn=min(max(c['neutral_modes'],1),Jself.shape[0]); idx=np.argsort(svals)[:kn]
    return vh.T[:,idx]

def _spectrum_with_backend(c,q,b,bname,Jself,Q,*,prev_vecs=None,save_eigs=False):
    cell=math.exp(float(q))
    if c['image_shell']>0:
        Jint=np.asarray(b.ring_normal_jacobian(c['n_nodes'],c['ring_radius_over_core'],cell,c['image_shell'],c['fd_eps_over_core'],c['core_model'],c['threads'],True),dtype=float)
    else:
        Jint=np.zeros_like(Jself)
    J=Jself+Jint
    eig_raw,vec_raw=np.linalg.eig(J)
    eig,vec,branch_overlap=_track_modes(prev_vecs,eig_raw,vec_raw)
    order=np.argsort(np.abs(eig)); k=min(max(c['neutral_modes'],0),len(eig)-1); non=eig[order[k:]]
    gap=float(abs(non[0])) if len(non) else float('nan'); gap_branch=int(order[k]) if len(non) else -1
    sigma=float(np.max(eig.real)); unstable=int(np.sum(eig.real>c['eig_zero_tol']))

    Jeff=Q.T@Jint@Q
    int_norm=float(np.linalg.norm(Jint,ord='fro')); self_norm=float(np.linalg.norm(Jself,ord='fro')); eff_norm=float(np.linalg.norm(Jeff,ord='fro'))
    fd_floor=float(np.finfo(float).eps/c['fd_eps_over_core'])
    neutral_signal_ratio=eff_norm/max(fd_floor,1e-300)
    neutral_signal_gate=bool(neutral_signal_ratio>=FD_NOISE_SAFETY)
    if eff_norm>0:
        Jeffn=Jeff/eff_norm; ee=np.linalg.eigvals(Jeffn)
        ee_order=np.argsort(np.abs(ee)); ee_non=ee[ee_order[min(3,len(ee)-1):]]
        neutral_gap=float(np.min(np.abs(ee_non))) if len(ee_non) else 0.0
        neutral_abscissa=float(np.max(ee_non.real)) if len(ee_non) else 0.0
        neutral_positive=int(np.sum(ee_non.real>1e-8))
    else:
        ee=np.zeros(Q.shape[1],dtype=complex); neutral_gap=0.0; neutral_abscissa=0.0; neutral_positive=0

    metrics=dict(b.ring_base_metrics(c['n_nodes'],c['ring_radius_over_core'],cell,c['image_shell'],c['core_model']))
    row={
      'q':float(q),'cell_over_core':cell,'backend':bname,'n_nodes':c['n_nodes'],'ring_radius_over_core':c['ring_radius_over_core'],
      'image_shell':c['image_shell'],'core_model':c['core_model'],'fd_eps_over_core':c['fd_eps_over_core'],
      'spectral_abscissa':sigma,'gap_after_neutral':gap,'gap_mode_branch':gap_branch,'unstable_count':unstable,
      'mode_min_overlap_prev':float(min(branch_overlap)) if branch_overlap else 1.0,
      'mode_median_overlap_prev':float(np.median(branch_overlap)) if branch_overlap else 1.0,
      'gap_mode_overlap_prev':float(branch_overlap[gap_branch]) if gap_branch>=0 and gap_branch<len(branch_overlap) else 1.0,
      'self_jacobian_norm':self_norm,'interaction_jacobian_norm':int_norm,'interaction_to_self_norm':int_norm/max(self_norm,1e-300),
      'neutral_effective_norm':eff_norm,'fd_roundoff_floor':fd_floor,'neutral_signal_to_fd_floor':neutral_signal_ratio,'neutral_signal_gate_ok':neutral_signal_gate,
      'neutral_gap_normalized':neutral_gap,'neutral_abscissa_normalized':neutral_abscissa,'neutral_positive_count':neutral_positive,
      'raw_rms':float(metrics['raw_rms']),'shape_rms':float(metrics['shape_rms']),'relative_shape_residual':float(metrics['relative_shape_residual']),
      'equilibrium_gate_ok':bool(metrics['relative_shape_residual']<=c['residual_max'])
    }
    branch={
      'q':float(q),
      'eigenvalues':[[float(z.real),float(z.imag)] for z in eig],
      'overlap_prev':[float(x) for x in branch_overlap],
      'gap_mode_branch':gap_branch,
    }
    if save_eigs:
        row['eigenvalues']=branch['eigenvalues']
        row['neutral_effective_eigenvalues_normalized']=[[float(z.real),float(z.imag)] for z in ee]
    return row,vec,branch

def spectrum_at_q(cfg,q,*,force_python=False,force_build=False,build_verbose=False,save_eigs=False):
    c=validate_config(cfg); b,bname=_backend(force_python,force_build,build_verbose)
    cell=math.exp(float(q))
    Jself=np.asarray(b.ring_normal_jacobian(c['n_nodes'],c['ring_radius_over_core'],cell,0,c['fd_eps_over_core'],c['core_model'],c['threads'],False),dtype=float)
    Q=_neutral_basis(Jself,c)
    row,_,_= _spectrum_with_backend(c,q,b,bname,Jself,Q,save_eigs=save_eigs)
    return row

def q_values(c):
    vals=[]; q=c['q_min']
    while q<=c['q_max']+0.5*c['q_step']:
        vals.append(round(q,12)); q+=c['q_step']
    return vals

def detect_candidates(rows):
    # Internal criteria only. Neutral diagnostics are suppressed below a computed FD roundoff signal gate.
    out=[]
    for i in range(1,len(rows)):
        a,b=rows[i-1],rows[i]
        if a['spectral_abscissa']*b['spectral_abscissa']<0 and a['equilibrium_gate_ok'] and b['equilibrium_gate_ok']:
            out.append({'kind':'full_spectrum_marginal_stability_transition','q_bracket':[a['q'],b['q']],
                        'cell_over_core_bracket':[a['cell_over_core'],b['cell_over_core']],
                        'abscissa':[a['spectral_abscissa'],b['spectral_abscissa']]})
        if a['unstable_count']!=b['unstable_count'] and a['equilibrium_gate_ok'] and b['equilibrium_gate_ok']:
            out.append({'kind':'full_spectrum_unstable_count_transition','q_bracket':[a['q'],b['q']],'cell_over_core_bracket':[a['cell_over_core'],b['cell_over_core']], 'counts':[a['unstable_count'],b['unstable_count']]})
        if (a['neutral_positive_count']!=b['neutral_positive_count'] and a['neutral_signal_gate_ok'] and b['neutral_signal_gate_ok']):
            out.append({'kind':'neutral_interaction_signature_transition','q_bracket':[a['q'],b['q']],'cell_over_core_bracket':[a['cell_over_core'],b['cell_over_core']], 'counts':[a['neutral_positive_count'],b['neutral_positive_count']]})
    for i in range(1,len(rows)-1):
        l,m,r=rows[i-1],rows[i],rows[i+1]
        if m['equilibrium_gate_ok'] and m['gap_after_neutral']<l['gap_after_neutral'] and m['gap_after_neutral']<r['gap_after_neutral']:
            depth=m['gap_after_neutral']/max(min(l['gap_after_neutral'],r['gap_after_neutral']),1e-300)
            if depth<0.8:
                out.append({'kind':'full_spectrum_isolated_gap_minimum','q':m['q'],'cell_over_core':m['cell_over_core'],'gap':m['gap_after_neutral'],'depth_ratio':depth,
                            'gap_mode_branch':m['gap_mode_branch'],'gap_mode_overlap_prev':m['gap_mode_overlap_prev']})
        if (m['neutral_signal_gate_ok'] and l['neutral_signal_gate_ok'] and r['neutral_signal_gate_ok'] and
            m['neutral_gap_normalized']<l['neutral_gap_normalized'] and m['neutral_gap_normalized']<r['neutral_gap_normalized']):
            depth=m['neutral_gap_normalized']/max(min(l['neutral_gap_normalized'],r['neutral_gap_normalized']),1e-300)
            if depth<0.8:
                out.append({'kind':'neutral_interaction_isolated_gap_minimum','q':m['q'],'cell_over_core':m['cell_over_core'],'gap_normalized':m['neutral_gap_normalized'],'depth_ratio':depth})
    return out

def run_scan(cfg,*,force_python=False,force_build=False,build_verbose=False,progress=True,track_modes=True):
    c=validate_config(cfg); rows=[]; branches=[]; qs=q_values(c)
    b,bname=_backend(force_python,force_build,build_verbose)
    reference_cell=math.exp(qs[0])
    Jself=np.asarray(b.ring_normal_jacobian(c['n_nodes'],c['ring_radius_over_core'],reference_cell,0,c['fd_eps_over_core'],c['core_model'],c['threads'],False),dtype=float)
    Q=_neutral_basis(Jself,c); prev_vecs=None
    for idx,q in enumerate(qs,1):
        row,vec,branch=_spectrum_with_backend(c,q,b,bname,Jself,Q,prev_vecs=prev_vecs if track_modes else None)
        prev_vecs=vec if track_modes else None
        if rows and row['interaction_jacobian_norm']>0 and rows[-1]['interaction_jacobian_norm']>0:
            row['interaction_decay_exponent']=-math.log(row['interaction_jacobian_norm']/rows[-1]['interaction_jacobian_norm'])/(row['q']-rows[-1]['q'])
        else:
            row['interaction_decay_exponent']=None
        rows.append(row); branches.append(branch)
        if progress:
            de=row['interaction_decay_exponent']; detxt='-' if de is None else f'{de:.3f}'
            print(f"[{idx:03d}/{len(qs):03d}] q={q:.6g} L/a={row['cell_over_core']:.6g} gap={row['gap_after_neutral']:.3e} sigma={row['spectral_abscissa']:.3e} int/self={row['interaction_to_self_norm']:.3e} p={detxt} overlap={row['gap_mode_overlap_prev']:.3f} neutralSNR={row['neutral_signal_to_fd_floor']:.2e} residual={row['relative_shape_residual']:.3e}")
    return {'config':c,'config_sha256':config_hash(c),'dimensionless_only':True,'fd_noise_safety':FD_NOISE_SAFETY,
            'rows':rows,'mode_tracking':branches,'candidates':detect_candidates(rows)}

def independence_manifest(cfg):
    c=validate_config(cfg)
    return {
      'protocol':'dimensionless-blind-v1.1','dimensionless_only':True,
      'fixed_units':{'core_radius_unit':1.0,'circulation_unit':1.0},
      'external_physical_constants_used':[], 'external_target_values_used':[],
      'allowed_runtime_keys':sorted(ALLOWED_CONFIG_KEYS),'config':c,'config_sha256':config_hash(c),
      'candidate_logic':{'neutral_signal_fd_floor_safety':FD_NOISE_SAFETY,'external_target_matching':False},
      'scientific_claim':'Outputs are dimensionless spectral and convergence diagnostics only; no external model comparison is performed by this package.'
    }
