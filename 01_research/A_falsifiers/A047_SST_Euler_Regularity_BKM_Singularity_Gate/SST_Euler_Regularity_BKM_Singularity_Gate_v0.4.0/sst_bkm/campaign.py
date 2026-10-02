from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

from .diagnostics import diagnostics, inverse_omega_fit, model_competition
from .mechanism import LagrangianTracker, cell_center_position, full_fields, interp_periodic
from .parent_v030 import locate_parent_output, reveal_parent_selection, select_parent_blind, sha256_file as parent_sha256_file
from .pklsa import (
    E010_VERSION, TOPOLOGY_ID, resolve_workbench_root, locate_e010, validate_e010_release,
    select_trefoil_carriers, load_carrier_centerline, canonicalize_centerline, sha256_file,
)
from .resolution import centerline_geometry_audit, seed_spectral_audit, spatial_convergence, temporal_convergence
from .seed import base_centerline, localized_packet
from .spectral import wave_numbers, dealias_mask, rk4_step

NAME = "SST_Euler_Regularity_BKM_Singularity_Gate"
VERSION = "v0.4.0"
CATALOG_ID = "A047"


def dump(path, obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")


def load_json(path):
    with Path(path).open(encoding='utf-8') as f:return json.load(f)


def stable_token(*parts,n=16):
    payload='\x1f'.join(str(x) for x in parts).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()[:n]


def make_packet_basis(principal):
    p=np.asarray(principal,float); p/=np.linalg.norm(p)
    ref=np.array([1.,0.,0.]) if abs(p[0])<0.8 else np.array([0.,1.,0.])
    a=np.cross(p,ref); a/=np.linalg.norm(a); return p,a


def create_archives(root,outbase,reveal_dir):
    root=Path(root).resolve()
    def abs_under_root(path):
        p=Path(path); return p.resolve() if p.is_absolute() else (root/p).resolve()
    outbase=abs_under_root(outbase); reveal_dir=abs_under_root(reveal_dir); archive_base=outbase.parent
    paths=[
        root.parent/f"{NAME}_{VERSION}-outputs_BLIND.zip",
        root.parent/f"{NAME}_{VERSION}-outputs_REVEALED.zip",
        root.parent/f"{NAME}_{VERSION}-outputs.zip",
    ]
    def ztree(zpath,items):
        with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
            for p in items:
                p=abs_under_root(p)
                if p.is_file(): z.write(p,p.relative_to(archive_base))
                elif p.exists():
                    for f in p.rglob('*'):
                        if f.is_file(): z.write(f,f.relative_to(archive_base))
    ztree(paths[0],[outbase/'BLIND']); ztree(paths[1],[outbase/'BLIND',reveal_dir]); ztree(paths[2],[outbase])
    return [str(p) for p in paths]



def convergence_assessment(summaries):
    """Legacy v0.3 compatibility gate: never pool distinct geometries for BKM convergence."""
    by_geometry={}
    for row in summaries:
        by_geometry.setdefault(row["geometry_id"],[]).append(row)
    per=[]; escalated=[]
    for gid,rows in sorted(by_geometry.items()):
        valid=[x for x in rows if x.get("numerically_valid")]
        cand=[x for x in valid if (x.get("blowup_fit") or {}).get("candidate",False)]
        tstars=[(x.get("blowup_fit") or {}).get("t_star") for x in cand if (x.get("blowup_fit") or {}).get("t_star") is not None]
        distinct_N=len({x.get("N") for x in cand}); spread=None; conv=False
        if len(tstars)>=3 and distinct_N>=3:
            spread=(max(tstars)-min(tstars))/max(float(np.mean(tstars)),1e-30); conv=spread<0.10
        per.append({"geometry_id":gid,"group_id":rows[0].get("group_id"),"valid_replays":len(valid),"candidate_replays":len(cand),
                    "candidate_distinct_N":distinct_N,"tstar_relative_spread":spread,"converged_candidate":bool(conv)})
        if conv:escalated.append(gid)
    return {"verdict":"ESCALATE_BKM_CANDIDATE" if escalated else "NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW",
            "geometry_count":len(by_geometry),"escalated_geometry_ids":escalated,"per_geometry":per}

def write_summary_csv(path,rows):
    fields=['case_id','geometry_id','group_id','stage','profile_id','N','dt','T','runtime_s','energy_rel_drift','max_div_rms','omega_growth','bkm_integral','numerically_valid','seed_certified']
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:w.writerow({k:r.get(k) for k in fields})


def run_one(centerline,spec,case_id,outdir,cfg):
    N=int(spec['N']); L=float(spec['L']); dt=float(spec['dt']); T=float(spec['T']); sigma=float(spec['core_sigma'])
    geom_audit=centerline_geometry_audit(centerline,L,sigma,N,cfg.get('seed_gates',{}))
    uh=base_centerline(centerline,N,L,sigma)
    d0=diagnostics(uh,L)
    if spec.get('packet_epsilon',0.0)>0:
        p,a=make_packet_basis(d0['principal_strain_vector']); kv=float(spec.get('packet_k',3.0))*p
        idx=d0['hot_index']; dx=L/N; x0=[-0.5*L+(ii+0.5)*dx for ii in idx]
        uh=localized_packet(uh,L,float(spec['packet_epsilon']),kv,a,x0,float(spec.get('packet_sigma',0.7)))
    kx,ky,kz,k2=wave_numbers(N,L); mask=dealias_mask(N,kx,ky,kz); uh*=mask[None,...]
    spectral_audit=seed_spectral_audit(uh,cfg.get('seed_gates',{}))
    seed_certified=bool(geom_audit['geometry_core_gate_pass'] and spectral_audit['spectral_bandlimit_gate_pass'])

    rows=[]; bkm=0.0; prev=None; t=0.0; steps=int(round(T/dt)); sample_every=max(1,int(spec.get('sample_every',4))); t0=time.time()
    mechanism_enabled=bool(spec.get('mechanism',False)); tracker=None
    for step in range(steps+1):
        sample=(step%sample_every==0 or step==steps)
        if sample:
            d=diagnostics(uh,L); d['t']=float(t)
            if prev is not None: bkm+=0.5*(prev['max_omega']+d['max_omega'])*(d['t']-prev['t'])
            d['bkm_integral_sampled']=float(bkm); rows.append(d); prev=d
            if mechanism_enabled:
                fields=full_fields(uh,L,pressure_hessian=True)
                if tracker is None:
                    x0=cell_center_position(d['hot_index'],N,L); w0=interp_periodic(fields['w'],x0,L); tracker=LagrangianTracker(x0,w0)
                tracker.sample(t,fields,L)
        if step<steps:
            uh=rk4_step(uh,dt,L,mask); t+=dt

    invfits=[inverse_omega_fit([r['t'] for r in rows],[r['max_omega'] for r in rows],late_fraction=f,
                               candidate_horizon_factor=float(cfg.get('inverse_fit',{}).get('candidate_horizon_factor',1.5)),
                               r2_min=float(cfg.get('inverse_fit',{}).get('r2_min',0.98)))
             for f in cfg.get('model_competition',{}).get('late_fractions',[0.35,0.45,0.55])]
    primary=min(invfits,key=lambda q:abs(float(q.get('late_fraction',0.45))-0.45))
    models=model_competition([r['t'] for r in rows],[r['max_omega'] for r in rows],cfg.get('model_competition',{}))
    e0,e1=rows[0]['energy'],rows[-1]['energy']
    summary={
        'case_id':case_id,'geometry_id':spec['geometry_id'],'group_id':spec['group_id'],'stage':spec['stage'],'profile_id':spec['profile_id'],
        'N':N,'dt':dt,'T':T,'runtime_s':time.time()-t0,
        'energy_rel_drift':abs(e1-e0)/max(abs(e0),1e-30),'max_div_rms':max(r['div_rms'] for r in rows),
        'omega_growth':max(r['max_omega'] for r in rows)/rows[0]['max_omega'],'bkm_integral':rows[-1]['bkm_integral_sampled'],
        'max_strain_lambda':max(r['strain_lambda_max'] for r in rows),
        'max_relative_vorticity_decomposition_error':max(r['relative_vorticity_decomposition_error'] for r in rows),
        'blowup_fit':primary,'inverse_omega_window_fits':invfits,'model_competition':models,
        'seed_geometry_audit':geom_audit,'seed_spectral_audit':spectral_audit,'seed_certified':seed_certified,
    }
    summary['numerically_valid']=bool(summary['energy_rel_drift']<float(spec['energy_drift_limit']) and summary['max_div_rms']<float(spec['div_rms_limit']))
    if tracker is not None:
        lag=tracker.finalize(); summary['mechanism']=lag['summary']; dump(Path(outdir)/f'case_{case_id}_lagrangian.json',lag['samples'])
    dump(Path(outdir)/f'case_{case_id}_timeseries.json',rows); dump(Path(outdir)/f'case_{case_id}_summary.json',summary)
    return summary


def _current_carrier_index(e010_out,cfg):
    carriers,audit,summary=select_trefoil_carriers(e010_out,cfg['dataset'].get('selection',{}))
    return {c.carrier_id:c for c in carriers},audit,summary


def prepare_stage(cfg,wb,e010_root,e010_out,parent_root,outbase,reset=True):
    blind=outbase/'BLIND'; reveal=outbase/'REVEALED'
    if reset and outbase.exists():shutil.rmtree(outbase)
    blind.mkdir(parents=True,exist_ok=True); reveal.mkdir(parents=True,exist_ok=True)

    release=validate_e010_release(e010_out,require_core_gates=cfg['dataset'].get('require_core_release_gates',True))
    carrier_index,selection_audit,e010_summary=_current_carrier_index(e010_out,cfg)

    # Critical ordering: freeze the selection from parent BLIND data before opening REVEALED provenance.
    frozen=select_parent_blind(parent_root,cfg.get('parent_selection',{}))
    dump(blind/'S00_parent_blind_selection.json',frozen)
    frozen_disk=load_json(blind/'S00_parent_blind_selection.json')
    reveal_sel=reveal_parent_selection(parent_root,frozen_disk)
    dump(reveal/'S00_parent_selection_reveal.json',reveal_sel)

    missing=[x['e010_carrier_id'] for x in reveal_sel['selected'] if x['e010_carrier_id'] not in carrier_index]
    if missing: raise RuntimeError(f'parent-selected carriers are no longer admitted by current E010 contract: {missing}')

    selected=[]
    parent_by_carrier={x['e010_carrier_id']:x for x in reveal_sel['selected']}
    for item in reveal_sel['selected']:
        c=carrier_index[item['e010_carrier_id']]
        selected.append((item,c))

    e010_release_path=Path(e010_out)/'RELEASE.json'
    e010_summary_path=Path(e010_out)/'poc'/'atlas'/TOPOLOGY_ID/'qualification'/'summary.json'
    manifest={
        'schema':'A047-V040-RUN-MANIFEST-1','catalog_id':CATALOG_ID,'name':NAME,'version':VERSION,
        'epistemic_status':'Resolution-certified follow-up of A047-v0.3.0; finite-window Euler/BKM mechanism falsification, not a proof of Euler regularity.',
        'parent':{'version':'v0.3.0','blind_selection_sha256':frozen['selection_sha256'],
                  'parent_summary_sha256':frozen['parent_summary_sha256'],'parent_manifest_sha256':frozen['parent_manifest_sha256']},
        'dataset':{'upstream':'E010 PKLSA v0.3.1 source-native 3_1 POC','selected_geometry_count':len(selected),
                   'e010_release_sha256':sha256_file(e010_release_path),'e010_trefoil_summary_sha256':sha256_file(e010_summary_path),
                   'selection_audit':selection_audit},
        'blind_selected_geometries':[{'geometry_id':i['geometry_id'],'group_id':i['group_id'],'selection_rank':i['selection_rank'],'selection_reason':i['selection_reason']} for i,_ in selected],
        'scientific_guards':[
            'parent selection frozen from v0.3.0 BLIND observables before reveal mapping',
            'same-geometry only spatial/temporal convergence',
            'seed/core resolution is a distinct gate and cannot be rescued by later dynamics',
            'independence groups stratify source lineages but are not replication multipliers',
            'no EULER_REGULARITY_PASS verdict exists in this release',
        ],
        'platform':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__},
    }
    dump(blind/'run_manifest.json',manifest)
    dump(reveal/'e010_pklsa_v031_provenance.json',{
        'workbench_root':str(wb),'e010_root':str(e010_root),'e010_output':str(e010_out),'parent_v030_output':str(parent_root),'e010_version':E010_VERSION,
        'e010_release':release,'e010_trefoil_poc_summary':e010_summary,'selection_audit':selection_audit,
        'selected_carriers':[{'geometry_id':i['geometry_id'],'e010_carrier_id':c.carrier_id,'source_family':c.source_family,'variant_id':c.variant_id,
                              'independence_group':c.independence_group,'catalog_id':c.catalog_id,'representation':c.representation,
                              'source_path':c.source_path,'geometry_sha256':c.geometry_sha256,'raw_sha256':c.raw_sha256} for i,c in selected],
    })
    return selected


def load_prepared(cfg,e010_out,outbase):
    frozen=load_json(outbase/'BLIND'/'S00_parent_blind_selection.json')
    rev=load_json(outbase/'REVEALED'/'S00_parent_selection_reveal.json')
    if rev.get('selection_sha256')!=frozen.get('selection_sha256'):raise RuntimeError('S00 BLIND/REVEALED selection hash mismatch')
    idx,_,_=_current_carrier_index(e010_out,cfg)
    by_gid={x['geometry_id']:x for x in rev['selected']}
    out=[]
    for s in frozen['selected']:
        r=by_gid[s['geometry_id']]; cid=r['e010_carrier_id']
        if cid not in idx:raise RuntimeError(f'prepared carrier no longer admitted: {cid}')
        out.append((r,idx[cid]))
    return out


def _canonical_for_carrier(item,carrier,cfg,wb,e010_root):
    raw,source_audit=load_carrier_centerline(carrier,wb,e010_root,strict_raw_hash=cfg['dataset'].get('strict_raw_hash',True),strict_geometry_hash=cfg['dataset'].get('strict_geometry_hash',True))
    base=cfg['base']; centerline,cmeta=canonicalize_centerline(raw,int(base['centerline_samples']),float(base['target_rms_radius']))
    return centerline,cmeta,source_audit


def _make_spec(cfg,item,stage,profile,overrides=None):
    spec={**cfg['base'],**profile,**(overrides or {})}
    spec.update({'geometry_id':item['geometry_id'],'group_id':item['group_id'],'stage':stage,'profile_id':str(profile['id'])})
    return spec


def spatial_stage(cfg,selected,wb,e010_root,outbase):
    stage_dir=outbase/'BLIND'/'S20_spatial'; stage_dir.mkdir(parents=True,exist_ok=True)
    profiles=cfg['stages']['spatial']['profiles']; all_rows=[]; geometry_results=[]
    for item,carrier in selected:
        centerline,cmeta,source_audit=_canonical_for_carrier(item,carrier,cfg,wb,e010_root)
        rows=[]
        for p in profiles:
            spec=_make_spec(cfg,item,'S20_spatial',p)
            cid='v040_'+stable_token(item['geometry_id'],'S20',p['id'])
            r=run_one(centerline,spec,cid,stage_dir,cfg); rows.append(r); all_rows.append(r)
        conv=spatial_convergence([r for r in rows if r['numerically_valid']],cfg['stages']['spatial'].get('gate',{}))
        finest=max(rows,key=lambda r:r['N'])
        certified=bool(conv['pass'] and all(r['numerically_valid'] for r in rows) and finest['seed_certified'])
        geometry_results.append({'geometry_id':item['geometry_id'],'group_id':item['group_id'],'selection_reason':item.get('selection_reason'),
                                 'numerically_valid_all':all(r['numerically_valid'] for r in rows),'spatial_convergence':conv,
                                 'finest_seed_certified':finest['seed_certified'],'certified_spatial_pass':certified,
                                 'screen_spatial_pass':bool(conv['pass'] and all(r['numerically_valid'] for r in rows)),
                                 'finest_seed_audit':{'geometry':finest['seed_geometry_audit'],'spectral':finest['seed_spectral_audit']}})
    assessment={'schema':'A047-V040-SPATIAL-ASSESSMENT-1','geometry_count':len(geometry_results),
                'screen_spatial_survivors':[r['geometry_id'] for r in geometry_results if r['screen_spatial_pass']],
                'certified_spatial_survivors':[r['geometry_id'] for r in geometry_results if r['certified_spatial_pass']],
                'per_geometry':geometry_results}
    if assessment['certified_spatial_survivors']:assessment['verdict']='SPATIAL_CERTIFIED_SURVIVORS'
    elif assessment['screen_spatial_survivors']:assessment['verdict']='SPATIAL_SIGNAL_CONVERGED_BUT_SEED_UNCERTIFIED'
    else:assessment['verdict']='NO_SPATIALLY_CONVERGED_FOLLOWUP'
    dump(stage_dir/'assessment.json',assessment); dump(stage_dir/'summary.json',{'assessment':assessment,'runs':all_rows}); write_summary_csv(stage_dir/'summary.csv',all_rows)
    return assessment


def temporal_stage(cfg,selected,wb,e010_root,outbase):
    scfg=cfg['stages']['temporal']
    stage_dir=outbase/'BLIND'/'S22_temporal'; stage_dir.mkdir(parents=True,exist_ok=True)
    if not scfg.get('enabled',False):
        a={'schema':'A047-V040-TEMPORAL-ASSESSMENT-1','verdict':'DISABLED','per_geometry':[],'survivors':[]}; dump(stage_dir/'assessment.json',a); return a
    spatial=load_json(outbase/'BLIND'/'S20_spatial'/'assessment.json')
    require_seed=bool(scfg.get('require_seed_certification',True))
    allowed=set(spatial['certified_spatial_survivors'] if require_seed else spatial['screen_spatial_survivors'])
    all_rows=[]; results=[]
    for item,carrier in selected:
        if item['geometry_id'] not in allowed:continue
        centerline,_,_=_canonical_for_carrier(item,carrier,cfg,wb,e010_root); rows=[]
        for p in scfg['profiles']:
            spec=_make_spec(cfg,item,'S22_temporal',p); cid='v040_'+stable_token(item['geometry_id'],'S22',p['id'])
            r=run_one(centerline,spec,cid,stage_dir,cfg); rows.append(r); all_rows.append(r)
        conv=temporal_convergence([r for r in rows if r['numerically_valid']],scfg.get('gate',{}))
        passed=bool(conv['pass'] and all(r['numerically_valid'] for r in rows) and (not require_seed or all(r['seed_certified'] for r in rows)))
        results.append({'geometry_id':item['geometry_id'],'group_id':item['group_id'],'temporal_convergence':conv,'pass':passed})
    a={'schema':'A047-V040-TEMPORAL-ASSESSMENT-1','verdict':'TEMPORAL_SURVIVORS' if any(r['pass'] for r in results) else 'NO_TEMPORALLY_CONVERGED_FOLLOWUP',
       'require_seed_certification':require_seed,'survivors':[r['geometry_id'] for r in results if r['pass']],'per_geometry':results}
    dump(stage_dir/'assessment.json',a); dump(stage_dir/'summary.json',{'assessment':a,'runs':all_rows}); write_summary_csv(stage_dir/'summary.csv',all_rows)
    return a


def _mechanism_gate(summary,cfg):
    m=summary.get('mechanism') or {}; g=cfg['stages']['long'].get('mechanism_gate',{})
    checks={
        'relative_vorticity_decomposition': summary.get('max_relative_vorticity_decomposition_error',1e99)<=float(g.get('decomposition_error_max',1e-10)),
        'detF_incompressibility': (m.get('max_detF_minus_1_abs') is not None and m['max_detF_minus_1_abs']<=float(g.get('detF_error_max',0.08))),
        'cauchy_vorticity': (m.get('max_cauchy_vorticity_relative_error') is not None and m['max_cauchy_vorticity_relative_error']<=float(g.get('cauchy_error_max',0.20))),
        'alpha_logstretch': (m.get('final_alpha_logstretch_closure_abs') is not None and m['final_alpha_logstretch_closure_abs']<=float(g.get('alpha_logstretch_error_max',0.20))),
    }
    # F_tt=-H F is retained as a diagnostic because sample-time differencing is lower-order.
    return {'checks':checks,'pass':bool(all(checks.values())),'pressure_hessian_Ftt_diagnostic':m.get('median_Ftt_pressure_hessian_relative_residual')}


def long_stage(cfg,selected,wb,e010_root,outbase):
    lcfg=cfg['stages']['long']; stage_dir=outbase/'BLIND'/'S30_S50_long_mechanism'; stage_dir.mkdir(parents=True,exist_ok=True)
    if not lcfg.get('enabled',False):
        a={'schema':'A047-V040-LONG-ASSESSMENT-1','verdict':'DISABLED','per_geometry':[],'model_candidates':[]}; dump(stage_dir/'assessment.json',a); return a
    temporal=load_json(outbase/'BLIND'/'S22_temporal'/'assessment.json')
    allowed=set(temporal.get('survivors',[]))
    if lcfg.get('allow_spatial_only_if_temporal_disabled') and temporal.get('verdict')=='DISABLED':
        spatial=load_json(outbase/'BLIND'/'S20_spatial'/'assessment.json'); allowed=set(spatial.get('certified_spatial_survivors',[]))
    rows=[]; results=[]
    profile=lcfg['profile']
    for item,carrier in selected:
        if item['geometry_id'] not in allowed:continue
        centerline,_,_=_canonical_for_carrier(item,carrier,cfg,wb,e010_root)
        spec=_make_spec(cfg,item,'S30_S50_long',profile,{'mechanism':True}); cid='v040_'+stable_token(item['geometry_id'],'LONG',profile['id'])
        r=run_one(centerline,spec,cid,stage_dir,cfg); rows.append(r)
        mech=_mechanism_gate(r,cfg); modelpass=bool(r['model_competition']['finite_time_model_gate_pass'])
        candidate=bool(r['numerically_valid'] and r['seed_certified'] and mech['pass'] and modelpass)
        results.append({'geometry_id':item['geometry_id'],'group_id':item['group_id'],'numerically_valid':r['numerically_valid'],'seed_certified':r['seed_certified'],
                        'mechanism_gate':mech,'model_competition_gate_pass':modelpass,'pre_robustness_candidate':candidate,
                        'omega_growth':r['omega_growth'],'bkm_integral':r['bkm_integral']})
    candidates=[x['geometry_id'] for x in results if x['pre_robustness_candidate']]
    a={'schema':'A047-V040-LONG-ASSESSMENT-1','verdict':'PRE_ROBUSTNESS_BKM_MODEL_CANDIDATES' if candidates else 'NO_CERTIFIED_FINITE_TIME_BKM_MODEL_CANDIDATE',
       'model_candidates':candidates,'per_geometry':results}
    dump(stage_dir/'assessment.json',a); dump(stage_dir/'summary.json',{'assessment':a,'runs':rows}); write_summary_csv(stage_dir/'summary.csv',rows)
    return a


def robustness_stage(cfg,selected,wb,e010_root,outbase):
    rcfg=cfg['stages'].get('robustness',{}); stage_dir=outbase/'BLIND'/'S60_robustness'; stage_dir.mkdir(parents=True,exist_ok=True)
    if not rcfg.get('enabled',False):
        a={'schema':'A047-V040-ROBUSTNESS-ASSESSMENT-1','verdict':'DISABLED','per_geometry':[],'survivors':[]}; dump(stage_dir/'assessment.json',a); return a
    long=load_json(outbase/'BLIND'/'S30_S50_long_mechanism'/'assessment.json'); allowed=set(long.get('model_candidates',[]))
    rows=[]; results=[]
    for item,carrier in selected:
        if item['geometry_id'] not in allowed:continue
        raw,_=load_carrier_centerline(carrier,wb,e010_root,strict_raw_hash=cfg['dataset'].get('strict_raw_hash',True),strict_geometry_hash=cfg['dataset'].get('strict_geometry_hash',True))
        grows=[]
        for samples in rcfg.get('centerline_samples',[256,384,512]):
            centerline,_=canonicalize_centerline(raw,int(samples),float(cfg['base']['target_rms_radius']))
            for mult in rcfg.get('sigma_multipliers',[0.85,1.0,1.15]):
                p=dict(rcfg['profile']); p['id']=f"robust_M{samples}_S{mult:g}"
                spec=_make_spec(cfg,item,'S60_robustness',p,{'core_sigma':float(cfg['base']['core_sigma'])*float(mult),'centerline_samples':int(samples)})
                cid='v040_'+stable_token(item['geometry_id'],'ROB',p['id']); r=run_one(centerline,spec,cid,stage_dir,cfg); rows.append(r); grows.append(r['omega_growth'])
        spread=(max(grows)-min(grows))/max(float(np.mean(grows)),1e-30) if grows else None
        passed=bool(grows and spread<=float(rcfg.get('omega_growth_relative_spread_max',0.12)) and all(r['numerically_valid'] for r in rows if r['geometry_id']==item['geometry_id']))
        results.append({'geometry_id':item['geometry_id'],'omega_growth_relative_spread':spread,'pass':passed})
    survivors=[r['geometry_id'] for r in results if r['pass']]
    a={'schema':'A047-V040-ROBUSTNESS-ASSESSMENT-1','verdict':'ROBUST_BKM_SCALING_CANDIDATE' if survivors else 'NO_ROBUST_BKM_SCALING_CANDIDATE',
       'survivors':survivors,'per_geometry':results}
    dump(stage_dir/'assessment.json',a); dump(stage_dir/'summary.json',{'assessment':a,'runs':rows}); write_summary_csv(stage_dir/'summary.csv',rows)
    return a


def final_assessment(outbase):
    spatial=load_json(outbase/'BLIND'/'S20_spatial'/'assessment.json') if (outbase/'BLIND'/'S20_spatial'/'assessment.json').exists() else None
    temporal=load_json(outbase/'BLIND'/'S22_temporal'/'assessment.json') if (outbase/'BLIND'/'S22_temporal'/'assessment.json').exists() else None
    long=load_json(outbase/'BLIND'/'S30_S50_long_mechanism'/'assessment.json') if (outbase/'BLIND'/'S30_S50_long_mechanism'/'assessment.json').exists() else None
    robust=load_json(outbase/'BLIND'/'S60_robustness'/'assessment.json') if (outbase/'BLIND'/'S60_robustness'/'assessment.json').exists() else None
    if robust and robust.get('survivors'):
        verdict='ESCALATE_ROBUST_BKM_SCALING_CANDIDATE'
    elif long and long.get('model_candidates'):
        verdict='BKM_MODEL_CANDIDATE_PENDING_ROBUSTNESS'
    elif temporal and temporal.get('survivors'):
        verdict='TEMPORALLY_CONVERGED_AMPLIFICATION_NO_CERTIFIED_BKM_MODEL'
    elif spatial and spatial.get('certified_spatial_survivors'):
        verdict='SPATIALLY_CERTIFIED_AMPLIFICATION'
    elif spatial and spatial.get('screen_spatial_survivors'):
        verdict='CONVERGED_TRANSIENT_AMPLIFICATION_SEED_UNCERTIFIED'
    else:
        verdict='SCREEN_ONLY_NO_CERTIFIED_ESCALATION'
    obj={'schema':'A047-V040-FINAL-ASSESSMENT-1','verdict':verdict,'spatial':None if spatial is None else spatial.get('verdict'),
         'temporal':None if temporal is None else temporal.get('verdict'),'long':None if long is None else long.get('verdict'),
         'robustness':None if robust is None else robust.get('verdict'),
         'interpretation':'No verdict in A047-v0.4.0 establishes global Euler regularity. A later dynamical stage cannot rescue a failed seed/core or convergence gate.'}
    dump(outbase/'BLIND'/'final_assessment.json',obj); return obj


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',default='config/v040_basic.json')
    ap.add_argument('--stage',choices=['prepare','spatial','temporal','long','robustness','all'],default='all')
    ap.add_argument('--workbench-root',default=None); ap.add_argument('--e010-root',default=None); ap.add_argument('--e010-output',default=None)
    ap.add_argument('--parent-v030-output',default=None); ap.add_argument('--out',default=None); ap.add_argument('--no-archives',action='store_true')
    args=ap.parse_args(); cfg=load_json(args.config)
    wb=resolve_workbench_root(args.workbench_root); e010_root,e010_out=locate_e010(wb,args.e010_root,args.e010_output)
    outbase=Path(args.out or f'{NAME}_{VERSION}-outputs')
    parent=locate_parent_output(args.parent_v030_output,Path.cwd())

    if args.stage in ('prepare','all'):
        selected=prepare_stage(cfg,wb,e010_root,e010_out,parent,outbase,reset=True)
        if args.stage=='prepare':
            print(json.dumps({'stage':'prepare','selected':len(selected),'output':str(outbase)},indent=2)); return
    else:
        selected=load_prepared(cfg,e010_out,outbase)

    if args.stage in ('spatial','all'): spatial_stage(cfg,selected,wb,e010_root,outbase)
    if args.stage in ('temporal','all'): temporal_stage(cfg,selected,wb,e010_root,outbase)
    if args.stage in ('long','all'): long_stage(cfg,selected,wb,e010_root,outbase)
    if args.stage in ('robustness','all'): robustness_stage(cfg,selected,wb,e010_root,outbase)
    final=final_assessment(outbase)

    # Post-hoc SST scaling only; none of these constants enter BLIND selection or Euler evolution.
    reveal=outbase/'REVEALED'; reveal.mkdir(parents=True,exist_ok=True)
    v_swirl=1.09384563e6; r_c=1.40897017e-15; rho_f=7.0e-7
    dump(reveal/'sst_scale_mapping.json',{'v_swirl_m_s':v_swirl,'r_c_m':r_c,'rho_f_kg_m3':rho_f,'t_c_s':r_c/v_swirl,'omega_c_s_inv':2*v_swirl/r_c,
                                         'mapping_note':'BLIND selection, resolution gates, convergence, Euler evolution and BKM model competition use none of these values.'})
    archives=[] if args.no_archives else create_archives(Path.cwd(),outbase,reveal)
    print(json.dumps({'assessment':final,'archives':archives,'output':str(outbase)},indent=2))


if __name__=='__main__':main()
