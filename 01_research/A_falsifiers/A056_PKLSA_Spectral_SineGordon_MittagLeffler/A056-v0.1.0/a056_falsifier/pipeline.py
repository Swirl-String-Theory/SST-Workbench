from __future__ import annotations
from pathlib import Path
import argparse, json, math
import numpy as np
from .io import discover_cases, uniformity
from .numeric import phase_features, native_available
from .spectral import pod_metrics, derived_ringdown
from .models import phase_model_competition, ringdown_competition
from .gates import GateLedger, GateRecord
from .util import read_json, write_json, write_csv, sha256_file

NAME='A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0'

def run(input_dir, config_path, output_dir=None):
    cfg=read_json(config_path); cases=discover_cases(input_dir)
    out=Path(output_dir or f'{NAME}-outputs'); blind=out/'BLIND'; blind.mkdir(parents=True,exist_ok=True)
    ledger=GateLedger(); rows=[]; prov=[]
    ledger.add(GateRecord('G0','PASS' if cases else 'FAIL','Are source objects present and hashed?',{"case_count":len(cases)},'' if cases else 'no input cases'))
    for case in cases:
        m=case['meta']; oid=m.get('opaque_id',case['path'].stem); group=m.get('source_group','UNSPECIFIED'); boundary=m.get('boundary','periodic')
        t,s,phi=case['t'],case['s'],case['phi']; tr,dt=uniformity(t); sr,ds=uniformity(s)
        adm=(len(t)>=cfg['sampling']['min_nt'] and len(s)>=cfg['sampling']['min_ns'] and np.all(np.isfinite(phi)) and np.all(np.diff(t)>0) and np.all(np.diff(s)>0) and tr<=cfg['sampling']['uniform_rel_tol'] and sr<=cfg['sampling']['uniform_rel_tol'])
        row={"opaque_id":oid,"source_group":group,"input_sha256":case['sha256'],"boundary":boundary,"nt":len(t),"ns":len(s),"t_uniform_rel":tr,"s_uniform_rel":sr,"G1_admissible":bool(adm)}
        prov.append({"opaque_id":oid,"source_group":group,"sha256":case['sha256'],"upstream_sha256":m.get('upstream_sha256')})
        if not adm:
            row.update({"G2_spectral":"NOT_RUN_PREREQUISITE","G3_phase":"NOT_RUN_PREREQUISITE","G4_ringdown":"NOT_RUN_PREREQUISITE"}); rows.append(row); continue
        sm,q,_=pod_metrics(phi,cfg['spectral']['top_k']); spass=(sm['orthogonality_residual']<=cfg['spectral']['orthogonality_max'] and sm['split_subspace_overlap']>=cfg['spectral']['subspace_overlap_min'])
        row.update({"pod_top_energy_fraction":sm['top_energy_fraction'],"pod_orthogonality_residual":sm['orthogonality_residual'],"pod_split_overlap":sm['split_subspace_overlap'],"G2_spectral":"PASS" if spass else "FAIL"})
        y,ss,ph=phase_features(phi,dt,ds,boundary)
        pm=phase_model_competition(y,ss,ph,cfg['phase']['cv_folds']); sg=pm['SG']
        g3=bool(sg['physical_coefficients'] and sg['design_condition']<=cfg['phase']['design_condition_max'] and sg['delta_bic_vs_best']>=cfg['phase']['delta_bic_min'] and sg['nrmse_ratio_vs_best']<=cfg['phase']['nrmse_ratio_max'])
        row.update({"SG_delta_bic":sg['delta_bic_vs_best'],"SG_nrmse_ratio":sg['nrmse_ratio_vs_best'],"SG_a":sg['coef'][0],"SG_b":sg['coef'][1],"SG_design_condition":sg['design_condition'],"G3_phase":"PASS" if g3 else "FAIL","phase_best_model":min(pm,key=lambda k:pm[k]['cv_bic'])})
        rd_source='provided'
        if case['ringdown'] is not None:
            rt=case['ringdown_t'] if case['ringdown_t'] is not None else t[:len(case['ringdown'])]; rv=case['ringdown']
        else:
            rt,rv=derived_ringdown(t,q); rd_source='derived_pod_energy'
        try:
            rm,_,_=ringdown_competition(rt,rv,cfg['ringdown']['train_fraction']); ml=rm['ML']; alo,ahi=cfg['ringdown']['alpha_support_bounds']
            g4=bool(ml['delta_bic_vs_best']>=cfg['ringdown']['delta_bic_min'] and ml['nrmse_ratio_vs_best']<=cfg['ringdown']['nrmse_ratio_max'] and alo<ml['alpha']<ahi)
            row.update({"ringdown_source":rd_source,"ML_delta_bic":ml['delta_bic_vs_best'],"ML_nrmse_ratio":ml['nrmse_ratio_vs_best'],"ML_alpha":ml['alpha'],"ML_tau":ml['tau'],"G4_ringdown":"PASS" if g4 else "FAIL","ringdown_best_model":min(rm,key=lambda k:rm[k]['bic'])})
        except Exception as e:
            row.update({"ringdown_source":rd_source,"G4_ringdown":"UNRESOLVED","ringdown_error":str(e)})
        rows.append(row)
    admiss=[r for r in rows if r.get('G1_admissible')]
    ledger.add(GateRecord('G1','PASS' if admiss else 'FAIL','Are cases numerically admissible?',{"admissible":len(admiss),"total":len(rows)}))
    g2=[r for r in admiss if r.get('G2_spectral')=='PASS']; ledger.add(GateRecord('G2','PASS' if g2 else ('FAIL' if admiss else 'NOT_RUN_PREREQUISITE'),'Is spectral/POD extraction numerically qualified?',{"pass":len(g2),"admissible":len(admiss)}))
    g3=[r for r in admiss if r.get('G3_phase')=='PASS']; ledger.add(GateRecord('G3','PASS' if g3 else ('FAIL' if admiss else 'NOT_RUN_PREREQUISITE'),'Does Sine-Gordon beat preregistered phase competitors?',{"support_cases":len(g3),"admissible":len(admiss)}))
    g4=[r for r in admiss if r.get('G4_ringdown')=='PASS']; ledger.add(GateRecord('G4','PASS' if g4 else ('FAIL' if admiss else 'NOT_RUN_PREREQUISITE'),'Does Mittag-Leffler beat ordinary ringdown competitors?',{"support_cases":len(g4),"admissible":len(admiss)}))
    phase_groups=sorted({r['source_group'] for r in g3 if r['source_group']!='UNSPECIFIED'}); mem_groups=sorted({r['source_group'] for r in g4 if r['source_group']!='UNSPECIFIED'}); joint_groups=sorted(set(phase_groups)&set(mem_groups))
    g5status='PASS' if (len(phase_groups)>=2 or len(mem_groups)>=2) else 'UNRESOLVED'
    ledger.add(GateRecord('G5',g5status,'Is support independently replicated?',{"phase_groups":phase_groups,"memory_groups":mem_groups,"joint_groups":joint_groups}))
    if len(joint_groups)>=2: conclusion='JOINT_SUPPORTED'; g6='PASS'
    elif len(phase_groups)>=2: conclusion='PHASE_ONLY_SUPPORTED'; g6='FAIL'
    elif len(mem_groups)>=2: conclusion='MEMORY_ONLY_SUPPORTED'; g6='FAIL'
    elif admiss and not g3 and not g4: conclusion='FALSIFIED_FOR_TESTED_REGIME'; g6='FAIL'
    else: conclusion='UNRESOLVED'; g6='UNRESOLVED'
    ledger.add(GateRecord('G6',g6,'Do both closures replicate jointly?',{"conclusion":conclusion,"joint_groups":joint_groups}))
    write_csv(blind/'case_results.csv',rows); write_json(blind/'provenance.json',{"native_available":native_available(),"config_sha256":sha256_file(config_path),"cases":prov}); ledger.write(blind/'gate_ledger.json')
    write_json(blind/'summary.json',{"schema":"A056-BLIND-SUMMARY-1","conclusion":conclusion,"case_count":len(rows),"admissible":len(admiss),"phase_support_cases":len(g3),"memory_support_cases":len(g4),"phase_groups":phase_groups,"memory_groups":mem_groups,"joint_groups":joint_groups})
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--config',default='configs/basic.json'); p.add_argument('--output',default=None); a=p.parse_args(); out=run(a.input,a.config,a.output); print(out)
if __name__=='__main__': main()
