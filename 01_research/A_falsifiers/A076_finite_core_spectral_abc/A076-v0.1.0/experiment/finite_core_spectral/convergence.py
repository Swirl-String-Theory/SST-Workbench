from __future__ import annotations
import math
from typing import Any
from .core import run_scan, validate_config

PRIMARY_KINDS={'full_spectrum_isolated_gap_minimum','full_spectrum_marginal_stability_transition'}

def _fine_cfg(base:dict[str,Any],q0:float,q1:float,fine_step:float):
    c=dict(base); c['q_min']=max(base['q_min'],q0); c['q_max']=min(base['q_max'],q1); c['q_step']=fine_step
    return validate_config(c)

def _refine_gap_candidate(base_cfg,cand,coarse_step,fine_step,**run_kw):
    q0=max(base_cfg['q_min'],float(cand['q'])-coarse_step)
    q1=min(base_cfg['q_max'],float(cand['q'])+coarse_step)
    if q1<=q0: return None,None
    res=run_scan(_fine_cfg(base_cfg,q0,q1,fine_step),**run_kw)
    if len(res['rows'])<3: return None,res
    i=min(range(1,len(res['rows'])-1),key=lambda j:res['rows'][j]['gap_after_neutral'])
    m=res['rows'][i]
    if not (m['gap_after_neutral']<res['rows'][i-1]['gap_after_neutral'] and m['gap_after_neutral']<res['rows'][i+1]['gap_after_neutral']):
        return None,res
    branch=m['gap_mode_branch']; ov_prev=m['gap_mode_overlap_prev']
    ov_next=None
    if i+1<len(res['mode_tracking']) and branch>=0:
        ovs=res['mode_tracking'][i+1]['overlap_prev']
        if branch<len(ovs): ov_next=float(ovs[branch])
    out={'kind':'full_spectrum_isolated_gap_minimum','q':m['q'],'cell_over_core':m['cell_over_core'],'gap':m['gap_after_neutral'],
         'spectral_abscissa':m['spectral_abscissa'],'unstable_count':m['unstable_count'],'gap_mode_branch':branch,
         'mode_overlap_prev':ov_prev,'mode_overlap_next':ov_next,'equilibrium_gate_ok':m['equilibrium_gate_ok'],
         'fine_q_step':fine_step,'source_coarse_q':cand['q']}
    return out,res

def _refine_marginal_candidate(base_cfg,cand,fine_step,**run_kw):
    q0,q1=map(float,cand['q_bracket'])
    res=run_scan(_fine_cfg(base_cfg,q0,q1,fine_step),**run_kw)
    root=None
    for a,b in zip(res['rows'],res['rows'][1:]):
        fa,fb=a['spectral_abscissa'],b['spectral_abscissa']
        if fa==0: root=a['q']; break
        if fa*fb<0:
            root=a['q']+(b['q']-a['q'])*(-fa)/(fb-fa); break
    if root is None: return None,res
    return {'kind':'full_spectrum_marginal_stability_transition','q':float(root),'cell_over_core':math.exp(float(root)),
            'fine_q_step':fine_step,'source_q_bracket':[q0,q1]},res

def adaptive_case(cfg:dict[str,Any],fine_step:float=0.0025,*,force_python=False,force_build=False,build_verbose=False,progress=True):
    base=validate_config(cfg); coarse=run_scan(base,force_python=force_python,force_build=force_build,build_verbose=build_verbose,progress=progress)
    refined=[]; fine_runs=[]
    for cand in coarse['candidates']:
        if cand['kind']=='full_spectrum_isolated_gap_minimum':
            rc,rr=_refine_gap_candidate(base,cand,base['q_step'],fine_step,force_python=force_python,force_build=False,build_verbose=build_verbose,progress=False)
        elif cand['kind']=='full_spectrum_marginal_stability_transition':
            rc,rr=_refine_marginal_candidate(base,cand,fine_step,force_python=force_python,force_build=False,build_verbose=build_verbose,progress=False)
        else:
            continue
        if rr is not None: fine_runs.append(rr)
        if rc is not None: refined.append(rc)
    return {'config':base,'coarse':coarse,'refined_primary_candidates':refined,'fine_runs':fine_runs}

def _cluster(entries,tol=0.02):
    groups=[]
    for e in sorted(entries,key=lambda x:x['q']):
        if not groups or abs(e['q']-sum(x['q'] for x in groups[-1])/len(groups[-1]))>tol:
            groups.append([e])
        else: groups[-1].append(e)
    return groups

def _evaluate_kind(case_results:list[dict[str,Any]],candidate_kind:str,q_tol:float):
    entries=[]
    for case in case_results:
        for c in case['result']['refined_primary_candidates']:
            if c['kind']==candidate_kind:
                entries.append({'case':case['case'],'axis':case['axis'],'value':case['value'],**c})
    clusters=[]
    for group in _cluster(entries,q_tol):
        qs=[e['q'] for e in group]; axes={e['axis'] for e in group}
        by_axis={a:[e for e in group if e['axis']==a] for a in axes}
        res=by_axis.get('resolution',[]); sh=by_axis.get('image_shell',[]); fd=by_axis.get('fd_eps',[])
        def find_value(rows,v):
            return next((e for e in rows if e['value']==v),None)
        r64,r96=find_value(res,64),find_value(res,96)
        s2,s3=find_value(sh,2),find_value(sh,3)
        fd_q=[e['q'] for e in fd]
        gate_resolution=bool(r64 and r96 and abs(r64['q']-r96['q'])<q_tol)
        gate_shell=bool(s2 and s3 and abs(s2['q']-s3['q'])<q_tol)
        gate_fd=bool(len(fd)>=3 and (max(fd_q)-min(fd_q)<q_tol))
        clusters.append({
          'kind':candidate_kind+'_cluster','q_mean':sum(qs)/len(qs),'q_min':min(qs),'q_max':max(qs),'n_entries':len(group),
          'gate_resolution_N64_N96':gate_resolution,'gate_image_shell_2_3':gate_shell,'gate_fd_at_least_3':gate_fd,
          'promote_converged_candidate':bool(gate_resolution and gate_shell and gate_fd),
          'entries':group,
        })
    return clusters

def evaluate_primary_convergence(case_results:list[dict[str,Any]],q_tol=0.02):
    clusters=[]
    for kind in ('full_spectrum_marginal_stability_transition','full_spectrum_isolated_gap_minimum'):
        clusters.extend(_evaluate_kind(case_results,kind,q_tol))
    return sorted(clusters,key=lambda c:(c['q_mean'],c['kind']))

def evaluate_gap_convergence(case_results:list[dict[str,Any]],q_tol=0.02):
    # Backward-compatible helper used by the regression test.
    return _evaluate_kind(case_results,'full_spectrum_isolated_gap_minimum',q_tol)
