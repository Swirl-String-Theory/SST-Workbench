from __future__ import annotations
from pathlib import Path
from typing import Any
import json, os
import numpy as np
from a056_science.io import discover_cases, uniformity
from a056_science.numeric import phase_features, native_info, mittag_leffler_python
from a056_science.spectral import pod_metrics, derived_ringdown
from a056_science.models import phase_model_competition, ringdown_competition
from a056_science.certification import phase_resolution_certification, memory_resolution_certification, phase_backend_certification, memory_backend_certification
from a056_science.util import write_json, write_csv, sha256_file
from sst_falsifier.blind import assert_blind_tree
from sst_falsifier.replication import assess_replication
from sst_falsifier.util import read_json


def _cfg(root: Path, cfg: dict[str,Any], mode: str):
    a=cfg.get('a056',{})
    override=os.environ.get('A056_CONFIG')
    rel=override or (a.get('basic_config') if mode=='BASIC' else a.get('full_config')) or 'configs/full.json'
    p=Path(rel); p=p if p.is_absolute() else root/p
    return json.loads(p.read_text(encoding='utf-8')),p


def _input(root: Path,cfg: dict[str,Any]):
    raw=os.environ.get('A056_INPUT_DIR') or cfg.get('a056',{}).get('default_input','data/synthetic_blind')
    p=Path(raw); return p if p.is_absolute() else root/p


def _out(root: Path,cfg: dict[str,Any]):
    p=cfg['project']; return root/f"{p['name']}_{p['version']}-outputs"


def _latex_escape(v):
    s=str(v); repl={"\\":r"\textbackslash{}","&":r"\&","%":r"\%","$":r"\$","#":r"\#","_":r"\_","{":r"\{","}":r"\}","~":r"\textasciitilde{}","^":r"\textasciicircum{}"}
    return ''.join(repl.get(ch,ch) for ch in s)


def _write_fragments(out: Path, rows, summary):
    rdir=out/'report'; rdir.mkdir(parents=True,exist_ok=True)
    lines=[r'\begin{longtable}{lllll}',r'\toprule Case & Evidence & Phase winner & Relaxation winner & Certified \\',r'\midrule']
    for r in rows:
        lines.append(f"{_latex_escape(r.get('opaque_id'))} & {_latex_escape(r.get('evidence_class'))} & {_latex_escape(r.get('phase_best_model','-'))} & {_latex_escape(r.get('ringdown_best_model','-'))} & {_latex_escape(r.get('certified',False))} \\\\")
    lines += [r'\bottomrule',r'\end{longtable}']
    (rdir/'A056_CASE_RESULTS.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (rdir/'A056_SUMMARY.tex').write_text(
        r'\begin{description}'+'\n'+
        rf"\item[Implementation conclusion] {_latex_escape(summary['implementation_conclusion'])}"+'\n'+
        rf"\item[Physical conclusion] {_latex_escape(summary['physical_conclusion'])}"+'\n'+
        rf"\item[Certified cases] {summary['certified_cases']} / {summary['case_count']}"+'\n'+
        r'\end{description}'+'\n',encoding='utf-8')


def run_scientific_pipeline(root: Path, cfg: dict[str,Any], ledger, mode: str) -> dict[str,Any]:
    acfg,config_path=_cfg(root,cfg,mode); input_dir=_input(root,cfg); out=_out(root,cfg); out.mkdir(parents=True,exist_ok=True)
    blind=assert_blind_tree(root)
    ledger.record('G0','PASS',metrics={"mode":mode,"blind":blind,"config_sha256":sha256_file(config_path)},reason='Framework verified frozen protocol; A056 blind commitment also verified.')

    cases=discover_cases(input_dir); rows=[]; provider_manifest=[]; all_admissible=bool(cases)
    for case in cases:
        m=case['meta']; oid=m.get('opaque_id',case['path'].stem); boundary=m.get('boundary','periodic')
        t,s,phi=case['t'],case['s'],case['phi']; tr,dt=uniformity(t); sr,ds=uniformity(s)
        adm=bool(case['contract']['pass'] and len(t)>=acfg['sampling']['min_nt'] and len(s)>=acfg['sampling']['min_ns'] and
                 np.all(np.isfinite(phi)) and np.all(np.diff(t)>0) and np.all(np.diff(s)>0) and
                 tr<=acfg['sampling']['uniform_rel_tol'] and sr<=acfg['sampling']['uniform_rel_tol'])
        all_admissible &= adm
        row={"opaque_id":oid,"source_group":m.get('source_group'),"evidence_class":m.get('evidence_class'),
             "independence_family":m.get('independence_unit') or m.get('source_group'),"provenance_family":m.get('provenance_family'),
             "generator_id":m.get('generator_id'),"solver_id":m.get('solver_id'),"boundary":boundary,
             "input_sha256":case['sha256'],"metadata_sha256":case['meta_sha256'],"nt":len(t),"ns":len(s),
             "t_uniform_rel":tr,"s_uniform_rel":sr,"admissible":adm}
        provider_manifest.append({k:row.get(k) for k in ('opaque_id','source_group','evidence_class','independence_family','provenance_family','generator_id','solver_id','input_sha256','metadata_sha256')})
        if not adm:
            rows.append(row); continue
        sm,q,_=pod_metrics(phi,acfg['spectral']['top_k'],acfg['phase']['discovery_fraction'])
        spass=bool(sm['orthogonality_residual']<=acfg['spectral']['orthogonality_max'] and sm['discovery_confirmation_subspace_overlap']>=acfg['spectral']['subspace_overlap_min'])
        row.update({"spectral_pass":spass,"pod_top_energy_fraction":sm['top_energy_fraction'],"pod_orthogonality_residual":sm['orthogonality_residual'],"pod_split_overlap":sm['discovery_confirmation_subspace_overlap']})
        y,ss,ph=phase_features(phi,dt,ds,boundary,'python'); pm=phase_model_competition(y,ss,ph,acfg['phase']['discovery_fraction']); sg=pm['SG']
        pdisc=bool(spass and sg['physical_coefficients'] and sg['design_condition']<=acfg['phase']['design_condition_max'] and sg['delta_bic_vs_best']>=acfg['phase']['delta_bic_min'])
        pconf=bool(pdisc and sg['nrmse_ratio_vs_best']<=acfg['phase']['nrmse_ratio_max'])
        row.update({"phase_best_model":min(pm,key=lambda k:pm[k]['discovery_bic']),"phase_discovery":pdisc,"phase_confirmation":pconf,
                    "SG_delta_bic":sg['delta_bic_vs_best'],"SG_nrmse_ratio":sg['nrmse_ratio_vs_best'],"SG_a":sg['coef'][0],"SG_b":sg['coef'][1],"SG_design_condition":sg['design_condition']})
        rd_source='provided'
        if case['ringdown'] is not None:
            rt=case['ringdown_t'] if case['ringdown_t'] is not None else t[:len(case['ringdown'])]; rv=case['ringdown']
        else:
            rt,rv=derived_ringdown(t,q); rd_source='derived_pod_energy'
        try:
            rm,_,_=ringdown_competition(rt,rv,acfg['ringdown']['train_fraction']); ml=rm['ML']; alo,ahi=acfg['ringdown']['alpha_support_bounds']
            mdisc=bool(spass and ml['delta_bic_vs_best']>=acfg['ringdown']['delta_bic_min'] and alo<ml['alpha']<ahi)
            mconf=bool(mdisc and ml['nrmse_ratio_vs_best']<=acfg['ringdown']['nrmse_ratio_max'])
            row.update({"ringdown_source":rd_source,"ringdown_best_model":min(rm,key=lambda k:rm[k]['bic']),"memory_discovery":mdisc,"memory_confirmation":mconf,
                        "ML_delta_bic":ml['delta_bic_vs_best'],"ML_nrmse_ratio":ml['nrmse_ratio_vs_best'],"ML_alpha":ml['alpha'],"ML_tau":ml['tau']})
        except Exception as e:
            ml=None; mdisc=mconf=False; row.update({"ringdown_source":rd_source,"memory_discovery":False,"memory_confirmation":False,"ringdown_error":f"{type(e).__name__}: {e}"})
        row['_phi']=phi; row['_dt']=dt; row['_ds']=ds; row['_rt']=rt; row['_rv']=rv; row['_ml']=ml
        rows.append(row)

    ledger.record('G1','PASS' if all_admissible else 'FAIL',metrics={"input_dir":str(input_dir),"case_count":len(cases),"admissible":sum(bool(r.get('admissible')) for r in rows),"all_admissible":all_admissible},reason='' if all_admissible else 'One or more preregistered runtime cases failed the provider/sampling contract.')
    if ledger.status('G1')!='PASS':
        for gid in ('G2','G3','G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(gid)
        write_json(out/'A056_PROVIDER_MANIFEST.json',{"schema":"A056-PROVIDER-MANIFEST-4","cases":provider_manifest})
        return {"schema":"A056-BACKEND-MANIFEST-4","framework_version":cfg['framework']['version'],"note":"Stopped at G1."}

    tcheck=np.linspace(0,2,41); mlerr=float(np.max(np.abs(mittag_leffler_python(tcheck,2.0,1.0)-np.exp(-tcheck/2.0))))
    spectral_pass=sum(bool(r.get('spectral_pass')) for r in rows)
    g2=bool(mlerr<=1e-12 and spectral_pass>0)
    ledger.record('G2','PASS' if g2 else 'FAIL',metrics={"ml_alpha1_exponential_max_abs":mlerr,"spectrally_qualified_cases":spectral_pass,"case_count":len(rows)},reason='' if g2 else 'Reference analytic/spectral qualification failed.')
    if not g2:
        for gid in ('G3','G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(gid)
        return {"schema":"A056-BACKEND-MANIFEST-4","framework_version":cfg['framework']['version'],"python_reference":{"actual_backend":"python-numpy-fp64","authority":"REFERENCE"}}

    disc=[r for r in rows if r.get('phase_discovery') or r.get('memory_discovery')]
    ledger.record('G3','PASS' if disc else 'FAIL',metrics={"discovery_cases":len(disc),"phase":sum(bool(r.get('phase_discovery')) for r in rows),"memory":sum(bool(r.get('memory_discovery')) for r in rows)},reason='' if disc else 'No candidate cleared preregistered discovery thresholds.')
    if not disc:
        for gid in ('G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(gid)
        return {"schema":"A056-BACKEND-MANIFEST-4","framework_version":cfg['framework']['version'],"python_reference":{"actual_backend":"python-numpy-fp64","authority":"REFERENCE"}}

    conf=[r for r in disc if r.get('phase_confirmation') or r.get('memory_confirmation')]
    ledger.record('G4','PASS' if conf else 'FAIL',metrics={"confirmed_cases":len(conf),"phase":sum(bool(r.get('phase_confirmation')) for r in rows),"memory":sum(bool(r.get('memory_confirmation')) for r in rows)},reason='' if conf else 'Discovery candidates did not survive held-out confirmation.')
    if not conf:
        for gid in ('G5','G6','G7','G8'): ledger.skip_due_prerequisite(gid)
        return {"schema":"A056-BACKEND-MANIFEST-4","framework_version":cfg['framework']['version'],"python_reference":{"actual_backend":"python-numpy-fp64","authority":"REFERENCE"}}

    native=native_info(); parity_fail=False; any_native=False
    for r in conf:
        phi,dt,ds,boundary=r['_phi'],r['_dt'],r['_ds'],r['boundary']; phase_ok=True; mem_ok=True
        if r.get('phase_confirmation'):
            pr=phase_resolution_certification(phi,dt,ds,boundary,acfg); pb=phase_backend_certification(phi,dt,ds,boundary,acfg)
            r.update({"phase_resolution_pass":pr.get('pass'),"phase_resolution_sg_coeff_rel_l2":pr.get('sg_coeff_relative_l2'),"phase_cpp_parity_pass":pb.get('pass'),"phase_cpp_parity_relative_l2":pb.get('relative_l2')})
            phase_ok=bool(pr.get('pass') and pb.get('pass')); any_native |= bool(pb.get('available')); parity_fail |= bool(pb.get('available') and not pb.get('pass'))
        if r.get('memory_confirmation'):
            ml=r['_ml']; mr=memory_resolution_certification(r['_rt'],r['_rv'],acfg); mb=memory_backend_certification(r['_rt'],ml['tau'],ml['alpha'],acfg)
            r.update({"memory_resolution_pass":mr.get('pass'),"memory_resolution_alpha_abs_delta":mr.get('alpha_abs_delta'),"memory_resolution_tau_rel_delta":mr.get('tau_relative_delta'),"memory_cpp_parity_pass":mb.get('pass'),"memory_cpp_parity_relative_l2":mb.get('relative_l2')})
            mem_ok=bool(mr.get('pass') and mb.get('pass')); any_native |= bool(mb.get('available')); parity_fail |= bool(mb.get('available') and not mb.get('pass'))
        r['certified']=bool((not r.get('phase_confirmation') or phase_ok) and (not r.get('memory_confirmation') or mem_ok))

    if parity_fail: g5='FAIL'; reason='C++ FP64 parity failed registered tolerance on at least one confirmed candidate.'
    elif not any_native: g5='UNRESOLVED'; reason='Strict C++/OpenMP FP64 certification backend unavailable.'
    else: g5='PASS'; reason='C++ FP64 parity executed; case-level resolution failures remain excluded from replication.'
    certified=[r for r in conf if r.get('certified')]
    ledger.record('G5',g5,metrics={"native":native,"confirmed_cases":len(conf),"certified_cases":len(certified),"resolution_or_parity_rejected":len(conf)-len(certified)},reason=reason,requested_backend='cpp',actual_backend=(native.get('backend_info') or {}).get('backend'),authority='CERTIFICATION')

    # GPU is an optional side branch. It never blocks G7 in this A056 gate plan.
    dd_path=root/'build/DD32_PARITY_SMOKE.json'; be_path=root/'build/BACKEND_SELFTEST.json'
    gpu_payload=None
    for p in (dd_path,be_path):
        if p.exists():
            try: gpu_payload=json.loads(p.read_text(encoding='utf-8')); break
            except Exception: pass
    if g5!='PASS': ledger.skip_due_prerequisite('G6')
    elif gpu_payload is None: ledger.record('G6','DEFERRED',metrics={"authority":"SCREENING_ONLY"},reason='No instance-local SYCL/DD32 smoke supplied; screening is optional and non-blocking.')
    else:
        ok=bool(gpu_payload.get('overall_pass',gpu_payload.get('pass',False)))
        ledger.record('G6','PASS' if ok else 'FAIL',metrics={"authority":"SCREENING_ONLY","smoke":gpu_payload},reason='GPU evidence is screening-only.',requested_backend='sycl-dd32',actual_backend='sycl-worker-dd32',authority='SCREENING_ONLY')

    # Clean private working keys from rows before persistence.
    for r in rows:
        for k in list(r):
            if k.startswith('_'): r.pop(k,None)
    phase=[{**r,"qualified":True} for r in certified if r.get('phase_confirmation')]
    memory=[{**r,"qualified":True} for r in certified if r.get('memory_confirmation')]
    joint=[{**r,"qualified":True} for r in certified if r.get('phase_confirmation') and r.get('memory_confirmation')]
    min_groups=int(acfg['replication']['min_independent_groups'])
    phase_rep=assess_replication(phase,min_independent_groups=min_groups); mem_rep=assess_replication(memory,min_independent_groups=min_groups); joint_rep=assess_replication(joint,min_independent_groups=min_groups)
    control_pass=any(x['G5_CONTROL_REPLICATION']=='PASS' for x in (phase_rep,mem_rep,joint_rep))
    physical_statuses=[x['G5_CROSS_SOURCE_REPLICATION'] for x in (phase_rep,mem_rep,joint_rep)]
    physical_pass='PASS' in physical_statuses
    physical_present=any(x['independent_rows']>0 for x in (phase_rep,mem_rep,joint_rep))
    if g5!='PASS':
        ledger.skip_due_prerequisite('G7')
    elif physical_pass:
        ledger.record('G7','PASS',metrics={"control_replication_pass":control_pass,"phase":phase_rep,"memory":mem_rep,"joint":joint_rep},reason='At least one candidate replicates across eligible independent/experimental evidence.')
    elif physical_present:
        ledger.record('G7','UNRESOLVED',metrics={"control_replication_pass":control_pass,"phase":phase_rep,"memory":mem_rep,"joint":joint_rep},reason='Physical evidence is present but does not meet the frozen cross-source independence threshold.')
    else:
        ledger.record('G7','NOT_RUN_PREREQUISITE',metrics={"control_replication_pass":control_pass,"phase":phase_rep,"memory":mem_rep,"joint":joint_rep},reason='Only implementation-control/simulation evidence is available; physical cross-source replication is ineligible.')

    implementation='UNRESOLVED'
    if joint_rep['G5_CONTROL_REPLICATION']=='PASS': implementation='JOINT_CONTROL_RECOVERED'
    elif phase_rep['G5_CONTROL_REPLICATION']=='PASS': implementation='PHASE_CONTROL_RECOVERED'
    elif mem_rep['G5_CONTROL_REPLICATION']=='PASS': implementation='MEMORY_CONTROL_RECOVERED'
    physical='NOT_ESTABLISHED'
    if ledger.status('G7')=='PASS':
        if joint_rep['G5_CROSS_SOURCE_REPLICATION']=='PASS': physical='JOINT_SUPPORTED'; ledger.record('G8','PASS',metrics={"conclusion":physical},reason='Both candidate mechanisms jointly replicate in eligible physical evidence.')
        elif phase_rep['G5_CROSS_SOURCE_REPLICATION']=='PASS': physical='PHASE_ONLY_SUPPORTED'; ledger.record('G8','FAIL',metrics={"conclusion":physical},reason='Only phase closure replicates; joint mechanism criterion is not met.')
        elif mem_rep['G5_CROSS_SOURCE_REPLICATION']=='PASS': physical='MEMORY_ONLY_SUPPORTED'; ledger.record('G8','FAIL',metrics={"conclusion":physical},reason='Only memory closure replicates; joint mechanism criterion is not met.')
        else: ledger.record('G8','UNRESOLVED',metrics={"conclusion":physical},reason='Replication gate passed but mechanism classification is indeterminate.')
    else:
        ledger.skip_due_prerequisite('G8',reason='Physical cross-source replication did not PASS.')

    summary={"schema":"A056-BLIND-SUMMARY-4","framework_version":cfg['framework']['version'],"a056_version":"v0.2.3","mode":mode,
             "case_count":len(rows),"certified_cases":len(certified),"implementation_conclusion":implementation,"physical_conclusion":physical,
             "phase_replication":phase_rep,"memory_replication":mem_rep,"joint_replication":joint_rep}
    write_json(out/'A056_PROVIDER_MANIFEST.json',{"schema":"A056-PROVIDER-MANIFEST-4","cases":provider_manifest})
    write_csv(out/'A056_CASE_RESULTS.csv',rows); write_json(out/'A056_SUMMARY.json',summary); _write_fragments(out,rows,summary)
    return {"schema":"A056-BACKEND-MANIFEST-4","framework_version":cfg['framework']['version'],"a056_version":"v0.2.3",
            "python_reference":{"actual_backend":"python-numpy-fp64","precision":"float64","authority":"REFERENCE"},
            "cpp_certification":{"requested_backend":"cpp","authority":"CERTIFICATION","native":native,"gate_status":ledger.status('G5')},
            "gpu_screening":{"authority":"SCREENING_ONLY","gate_status":ledger.status('G6')},
            "input_dir":str(input_dir),"config":str(config_path),"summary":summary}
