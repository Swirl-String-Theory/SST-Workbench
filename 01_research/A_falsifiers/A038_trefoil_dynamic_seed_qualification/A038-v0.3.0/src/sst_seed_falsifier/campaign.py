"""Reproducible frozen atlas campaign and gated Phase B entrypoint."""
from pathlib import Path
import argparse
import time
import numpy as np
from .atlas import verify_freeze
from .evidence import validate_frozen_evidence, object_sha256, tree_manifest, dynamics_contract
from .io import load_json, dump_json
from .candidates import generate
from .geometry import normalize_length, resample_closed, arclength
from .workflow import (stage_early,stage_resolution,stage_temporal,stage_core,stage_mesh_gauge,
                       stage_long,stage_rpo,stage_mechanism,_rpo_eligibility,reveal)
from .phase_b import (FlowContract, floquet_certificate, intervention_panel,
                     refine_full_state, run_ladders)


def screen(repo,atlas,out,config):
    record=verify_freeze(repo,atlas); cfg=load_json(config); atlas=Path(atlas); out=Path(out)
    if cfg.get('require_knot_library_records',False):
        from .knot_library import activate
        activate(repo,cfg)
    summary=load_json(atlas/'ATLAS_SUMMARY.json')
    if record['config']!=cfg: raise ValueError('ATLAS_SCREEN_CONFIG_MISMATCH')
    if summary['status']!='QUALIFIED_PROSPECTIVE_REALIZATION_ATLAS': raise ValueError('ATLAS_NOT_QUALIFIED')
    if summary['test_files']!=tree_manifest(atlas/'test_atlas'): raise ValueError('ATLAS_GEOMETRY_CHANGED')
    generate(atlas/'test_atlas',out,cfg,config_path=config,repo=repo)
    print('PREPARE',load_json(out/'prepare_summary.json')['source_diversity_status'],flush=True)
    # No adaptive refinement: the six registered test draws are the entire pool.
    for name,fn in [('early',stage_early),('resolution',stage_resolution),('temporal',stage_temporal),
                    ('core',stage_core),('mesh-gauge',stage_mesh_gauge),('long',stage_long),
                    ('projected-rpo',stage_rpo),('predictive-specificity',stage_mechanism)]:
        validate_frozen_evidence(out,cfg,config)
        started=time.perf_counter(); print('START',name,flush=True)
        rows=fn(out,cfg)
        print('DONE',name,'rows=',len(rows),'elapsed_s=',round(time.perf_counter()-started,3),flush=True)
    return load_json(out/'BLIND_CHAIN_SUMMARY.json')


def phase_b_from_screen(out,config,protocol,*,refine=False,ladders=False):
    out=Path(out); cfg=load_json(config); p=load_json(protocol)
    validate_frozen_evidence(out,cfg,config)
    rows=load_json(out/'stage40_long/results.json')
    expected=dynamics_contract(cfg,int(cfg['rpo_n']))[1]
    selected=[r for r in rows if _rpo_eligibility(r,cfg)[0]]
    results=[]
    for row in selected[:int(cfg['rpo_top_k'])]:
        if row.get('dynamics_contract_sha256')!=expected: raise ValueError('PHASE_B_SCREEN_CONTRACT_MISMATCH')
        x=normalize_length(resample_closed(np.load(out/'geometries'/f"{row['candidate_id']}.npy"),int(cfg['rpo_n'])))
        replay=row['dynamics_replay']; t=float(row['best_return_time'])
        steps=round(t/replay['dt'])
        if not np.isclose(steps*replay['dt'],t,rtol=1e-10,atol=1e-12): raise ValueError('PHASE_B_REPLAY_GRID_MISMATCH')
        c=FlowContract(len(x),arclength(x),gamma=cfg['gamma'],core0=cfg['core_fraction'],
                       mesh_rate=cfg['mesh_rate'],mesh_method=cfg['mesh_redistribution_method'],
                       mesh_cap=cfg['mesh_max_relative_rms'],max_ds_cv=cfg['long_hard_ds_cv'],
                       min_gap_over_ds=cfg['min_gap_over_ds'],contact_skip=cfg['contact_skip'],
                       guard_stride=replay['guard_stride'],require_native=cfg['require_native'])
        item={'candidate_id':row['candidate_id']}
        try:
            action=None
            if refine:
                x,t,action,fit=refine_full_state(x,t,steps,c,p); item['full_state_shooting']=fit
            cert=floquet_certificate(x,t,steps,c,p,action)
            item['floquet']=cert
            item['interventions']=intervention_panel(x,t,steps,c,p,baseline_certificate=cert)
            if ladders and cert['status']=='NUMERICALLY_VALIDATED_AT_DISCRETIZATION':
                item['ladders']=run_ladders(x,t,cfg,p,refine=refine)
        except (ValueError,RuntimeError,FloatingPointError,np.linalg.LinAlgError) as exc:
            item['status']='FAILED_PHASE_B_NUMERICS'; item['error']=str(exc)
        results.append(item)
    report={'format':'SST-PHASE-B-SCREEN-1','run_kind':cfg['run_kind'],
            'status':'NOT_RUN_NO_S40_ELIGIBLE_RPO' if not selected else 'PHASE_B_ATTEMPTED',
            'n_eligible':len(selected),'results':results,'protocol':p,'protocol_sha256':object_sha256(p),
            'physics_verdict':'INDETERMINATE','publication_certified':False,'causal_language_allowed':False}
    dump_json(out/'PHASE_B_SUMMARY.json',report)
    return report


def main():
    a=argparse.ArgumentParser(); a.add_argument('command',choices=['screen','phase-b','reveal'])
    a.add_argument('--repo'); a.add_argument('--atlas'); a.add_argument('--out',required=True)
    a.add_argument('--config'); a.add_argument('--protocol'); a.add_argument('--refine',action='store_true')
    a.add_argument('--ladders',action='store_true'); args=a.parse_args()
    if args.command=='screen': result=screen(args.repo,args.atlas,args.out,args.config)
    elif args.command=='phase-b':
        if not args.atlas or not args.repo: raise ValueError('PHASE_B_REQUIRES_FROZEN_ATLAS_PROTOCOL')
        frozen=verify_freeze(args.repo,args.atlas)
        cfg=load_json(args.config)
        if cfg.get('require_knot_library_records',False):
            from .knot_library import activate
            activate(args.repo,cfg)
        if frozen['phase_b_protocol']!=load_json(args.protocol): raise ValueError('PHASE_B_PROTOCOL_CHANGED')
        result=phase_b_from_screen(args.out,args.config,args.protocol,refine=args.refine,ladders=args.ladders)
    else: result=reveal(args.out)
    print({k:v for k,v in result.items() if k in ['status','verdict','n_eligible','physics_verdict','identity_commitment_verified']})


if __name__=='__main__': main()
