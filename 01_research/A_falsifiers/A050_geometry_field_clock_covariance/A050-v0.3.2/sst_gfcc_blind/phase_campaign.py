from __future__ import annotations
import json, hashlib, platform, sys, os
from pathlib import Path
import numpy as np
from .filament import evolve_curve
from .persistence import modal_persistence_metrics
from .nonstationary import branch_phase_metrics, branch_retained
from .io import write_json, write_csv, sha256

ROOT=Path(__file__).resolve().parents[1]


def clean(x):
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,list): return [clean(v) for v in x]
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,(np.integer,int)): return int(x)
    if isinstance(x,(np.floating,float)): return None if not np.isfinite(x) else float(x)
    return x


def env():
    return {'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'cpu_count':os.cpu_count()}


def load_manifest(cfg):
    return json.loads((ROOT/cfg['external_geometry_gate']['staged_manifest']).read_text(encoding='utf-8'))


def load_entry(e):
    p=ROOT/e['file']
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=e['sha256']:
        raise RuntimeError(f'staged hash mismatch: {e["carrier_id"]}')
    return np.asarray(np.load(p,allow_pickle=False)['points'],float)


def run_carrier(points,cfg):
    dt=float(cfg['time_step'])
    frames=evolve_curve(points,float(cfg['core_ratio']),dt,int(cfg['modal_persistence_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
    pm=modal_persistence_metrics(frames,dt,cfg['modal_persistence_gate'],cfg['kelvin_gate'])
    bp=branch_phase_metrics(frames,dt,pm,cfg['kelvin_gate'],cfg['branch_phase_gate'])
    return pm,bp


def phase_class_counts(rows):
    out={
        'STATIONARY_COHERENT':0,
        'COHERENT_DRIFTING':0,
        'COHERENT_REVERSING':0,
        'COHERENT_NONSTATIONARY_COMPLEX':0,
        'INCOHERENT_OR_UNRESOLVED':0,
    }
    for r in rows:
        c=(r.get('branch_phase') or {}).get('phase',{}).get('classification','INCOHERENT_OR_UNRESOLVED')
        out[c]=out.get(c,0)+1
    return out


def main_run(config_path,out_dir):
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8'))
    gate=cfg['branch_phase_gate']
    man=load_manifest(cfg)
    parent=json.loads((ROOT/gate['parent_evidence']).read_text(encoding='utf-8'))
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    write_json(out/'config_used.json',cfg); write_json(out/'environment.json',env()); write_json(out/'staged_manifest_used.json',man); write_json(out/'parent_v030_evidence_used.json',parent)

    groups={}
    for e in man['entries']:
        groups.setdefault(e['group_id'],[]).append(e)

    primary=[]; diagnostics=[]; flat=[]
    for gid,ents in sorted(groups.items()):
        base_e=next(e for e in ents if e['role']=='baseline')
        pm,bp=run_carrier(load_entry(base_e),cfg)
        base_rec={'carrier_id':base_e['carrier_id'],'group_id':gid,'role':'baseline','persistence':pm,'branch_phase':bp}
        flat.append(base_rec)
        holds=[]
        for e in sorted([x for x in ents if x['role']=='holdout'],key=lambda x:x['carrier_id']):
            hp,hb=run_carrier(load_entry(e),cfg)
            rec={'carrier_id':e['carrier_id'],'group_id':gid,'role':'holdout','persistence':hp,'branch_phase':hb,'perturbation_rms':e.get('perturbation_rms')}
            holds.append(rec); flat.append(rec)
        if not base_e.get('primary',False):
            diagnostics.append({'group_id':gid,'baseline':base_rec})
            print(f'[v0.3.2] {gid} diagnostic done class={bp["phase"]["classification"]}',flush=True)
            continue
        retained=[h for h in holds if branch_retained(bp['branch_identity'],h['branch_phase']['branch_identity'])]
        fraction=float(len(retained)/max(len(holds),1))
        retention_pass=bool(
            bp['branch_identity']['stable'] and
            fraction>=float(gate['minimum_holdout_branch_retention_fraction_per_base'])
        )
        primary.append({
            'group_id':gid,'source_group_id':base_e['source_group_id'],'baseline':base_rec,'holdouts':holds,
            'retained_holdout_count':len(retained),'holdout_count':len(holds),'holdout_branch_retention_fraction':fraction,
            'branch_retention_pass':retention_pass,
            'retained_holdout_ids':[h['carrier_id'] for h in retained]
        })
        print(f'[v0.3.2] {gid} primary branch={bp["selected_mode"]} retained={len(retained)}/{len(holds)} phase={bp["phase"]["classification"]}',flush=True)

    source_rows=[]
    for sid,need in sorted(cfg['external_geometry_gate']['source_group_minimum_robust_bases'].items()):
        rr=[r for r in primary if r['source_group_id']==sid]
        n=sum(r['branch_retention_pass'] for r in rr)
        source_rows.append({'source_group_id':sid,'retention_base_count':int(n),'base_count':len(rr),'minimum_required':int(need),'pass':bool(n>=int(need))})
    bases_retained=sum(r['branch_retention_pass'] for r in primary)
    source_groups_confirmed=sum(x['pass'] for x in source_rows)
    branch_gate_pass=bool(
        bases_retained>=int(gate['minimum_primary_bases_with_holdout_retention']) and
        source_groups_confirmed>=int(cfg['external_geometry_gate']['minimum_source_groups_confirmed'])
    )

    primary_baselines=[r['baseline'] for r in primary]
    base_classes=phase_class_counts(primary_baselines)
    holdouts=[h for r in primary for h in r['holdouts']]
    holdout_classes=phase_class_counts(holdouts)
    coherent_classes={'STATIONARY_COHERENT','COHERENT_DRIFTING','COHERENT_REVERSING','COHERENT_NONSTATIONARY_COMPLEX'}
    nonstationary_classes={'COHERENT_DRIFTING','COHERENT_REVERSING','COHERENT_NONSTATIONARY_COMPLEX'}
    coherent_primary=sum(base_classes.get(k,0) for k in coherent_classes)
    nonstationary_primary=sum(base_classes.get(k,0) for k in nonstationary_classes)
    if not branch_gate_pass:
        status='BRANCH_IDENTITY_NOT_RETAINED'
    elif coherent_primary<int(gate['minimum_coherent_primary_bases']):
        status='BRANCH_RETAINED_PHASE_INCOHERENT_OR_UNRESOLVED'
    elif nonstationary_primary>=int(gate['minimum_nonstationary_coherent_primary_bases']):
        status='BRANCH_RETAINED_COHERENT_NONSTATIONARITY_SUPPORTED'
    else:
        status='BRANCH_RETAINED_STATIONARY_OR_MIXED_PHASE'

    result={
        'stage':'blind_diagnostic_complete','blind':True,'version':'v0.3.2',
        'parent_version':'v0.3.0','parent_verdict_frozen':parent['parent_verdict'],
        'parent_blind_results_sha256':parent['blind_results_sha256'],
        'diagnostic_status':status,
        'does_not_modify_parent_verdict':True,
        'branch_retention_gate':{
            'pass':branch_gate_pass,'retained_primary_base_count':int(bases_retained),'primary_base_count':len(primary),
            'minimum_primary_bases_with_holdout_retention':int(gate['minimum_primary_bases_with_holdout_retention']),
            'source_groups_confirmed':int(source_groups_confirmed),'source_group_rows':source_rows,
            'definition':'branch identity is evaluated independently of the parent stationary persistence pass'
        },
        'phase_diagnostic':{
            'primary_baseline_class_counts':base_classes,'holdout_class_counts':holdout_classes,
            'coherent_primary_base_count':int(coherent_primary),'nonstationary_coherent_primary_base_count':int(nonstationary_primary),
            'minimum_coherent_primary_bases':int(gate['minimum_coherent_primary_bases']),
            'minimum_nonstationary_coherent_primary_bases':int(gate['minimum_nonstationary_coherent_primary_bases']),
            'angular_rate_definition':'omega = d(phi)/dt, in radians per dimensionless time unit; cycle rate f = omega/(2*pi)'
        },
        'primary_groups':primary,'diagnostic_groups':diagnostics,
        'limitations':[
            'v0.3.2 is post-hoc diagnostic work motivated by the frozen v0.3.0 outcome; it is not an independent confirmation.',
            'The v0.3.0 verdict remains unchanged even if v0.3.2 finds branch retention or coherent nonstationarity.',
            'No mode number is hard-coded as a target; branch identity is selected from blind checkpoint dynamics.',
            'A repeated numerical branch label does not by itself identify a physical Kelvin wave or validate SST.',
            'Angular phase rate omega is not cycle frequency f; f=omega/(2*pi).',
            'Pressure-memory, spatial, and divergence gates are inherited only as frozen parent evidence and are not rerun in this focused campaign.'
        ]
    }
    result=clean(result); write_json(out/'blind_results.json',result)

    carrier_rows=[]
    for r in flat:
        b=r['branch_phase']['branch_identity']; p=r['branch_phase']['phase']; pm=r['persistence']
        carrier_rows.append({
            'carrier_id':r['carrier_id'],'group_id':r['group_id'],'role':r['role'],
            'parent_persistence_pass':pm['pass'],'parent_persistent_mode':pm['persistent_mode'],'parent_frequency_cv':pm['frequency_cv'],
            'branch_reference_mode':b['reference_mode'],'branch_stable':b['stable'],'checkpoint_mode_fraction':b['checkpoint_mode_fraction'],'mode_switch_count':b['mode_switch_count'],
            'phase_class':p['classification'],'phase_coherent':p.get('coherent',False),'net_phase_cycles':p.get('net_phase_cycles'),
            'total_phase_path_cycles':p.get('total_phase_path_cycles'),'linear_r2':(p.get('linear_fit') or {}).get('r2'),
            'quadratic_r2':(p.get('quadratic_fit') or {}).get('r2'),'delta_bic_quadratic_over_linear':p.get('delta_bic_quadratic_over_linear'),
            'piecewise_nrmse':(p.get('segmented_angular_rate') or {}).get('piecewise_nrmse'),
            'segment_angular_rate_cv':(p.get('segmented_angular_rate') or {}).get('angular_rate_cv'),
            'angular_rate_sign_reversal_count':p.get('angular_rate_sign_reversal_count'),
            'positive_rate_segment_count':p.get('positive_rate_segment_count'),'negative_rate_segment_count':p.get('negative_rate_segment_count')
        })
    write_csv(out/'branch_phase_carriers.csv',carrier_rows)
    write_csv(out/'branch_retention_bases.csv',[{
        'group_id':r['group_id'],'source_group_id':r['source_group_id'],
        'baseline_branch_mode':r['baseline']['branch_phase']['branch_identity']['reference_mode'],
        'baseline_branch_stable':r['baseline']['branch_phase']['branch_identity']['stable'],
        'retained_holdout_count':r['retained_holdout_count'],'holdout_count':r['holdout_count'],
        'holdout_branch_retention_fraction':r['holdout_branch_retention_fraction'],'branch_retention_pass':r['branch_retention_pass'],
        'baseline_phase_class':r['baseline']['branch_phase']['phase']['classification']
    } for r in primary])
    write_csv(out/'source_group_branch_retention.csv',source_rows)
    dig=sha256(out/'blind_results.json'); (out/'blind_results.sha256').write_text(dig+'  blind_results.json\n',encoding='utf-8')
    return result


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    main_run(a.config,a.out)
