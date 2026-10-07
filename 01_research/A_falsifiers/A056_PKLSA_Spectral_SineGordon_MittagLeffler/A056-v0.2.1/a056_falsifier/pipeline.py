from __future__ import annotations
from pathlib import Path
import argparse
import numpy as np
from .io import discover_cases, uniformity
from .numeric import phase_features, native_available
from .spectral import pod_metrics, derived_ringdown
from .models import phase_model_competition, ringdown_competition
from .certification import phase_resolution_certification, memory_resolution_certification, phase_backend_certification, memory_backend_certification
from .util import read_json, write_json, write_csv, sha256_file
from sst_falsifier_framework import __version__ as FRAMEWORK_VERSION, FRAMEWORK_SCHEMA, FRAMEWORK_PATCH_LEVEL
from sst_falsifier_framework.gates import GateLedger, GateRecord
from sst_falsifier_framework.provenance import environment_snapshot, load_json_if_exists
from sst_falsifier_framework.blindness import scan_tree
from sst_falsifier_framework.outputs import default_output_dir
from sst_falsifier_framework.replication import assess_replication, replication_group

NAME='A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.2.1'
ROOT=Path(__file__).resolve().parents[1]


def output_dir_for(package_root=ROOT):
    return default_output_dir(Path(package_root))


def _status(any_pass, prereq=True):
    if not prereq: return 'NOT_RUN_PREREQUISITE'
    return 'PASS' if any_pass else 'FAIL'


def _physical_groups(assessment):
    return assessment.get('physical_groups',[])


def run(input_dir, config_path, output_dir=None):
    cfg=read_json(config_path); cases=discover_cases(input_dir)
    out=Path(output_dir) if output_dir is not None else output_dir_for(ROOT)
    blind=out/'BLIND'; blind.mkdir(parents=True,exist_ok=True)
    ledger=GateLedger(); rows=[]; prov=[]

    blind_hits=scan_tree(ROOT/'a056_falsifier', forbidden=cfg['blindness']['forbidden_terms']) + scan_tree(ROOT/'sst_falsifier_framework', forbidden=cfg['blindness']['forbidden_terms'])
    source_contract_ok=bool(cases) and all(c['contract']['pass'] for c in cases)
    g0='PASS' if source_contract_ok and not blind_hits else 'FAIL'
    ledger.add(GateRecord('G0_PROVENANCE',g0,'Are source, provider-contract, hashing and blind-boundary checks satisfied?',
        {"case_count":len(cases),"provider_contract_pass":source_contract_ok,"blind_scan_hits":blind_hits,
         "config_sha256":sha256_file(config_path)}, '' if g0=='PASS' else 'missing/invalid cases or blind-scan hit'))

    for case in cases:
        m=case['meta']; oid=m.get('opaque_id',case['path'].stem); group=m.get('source_group','UNSPECIFIED'); boundary=m.get('boundary','periodic')
        evidence_class=m.get('evidence_class','UNSPECIFIED')
        t,s,phi=case['t'],case['s'],case['phi']; tr,dt=uniformity(t); sr,ds=uniformity(s)
        adm=(case['contract']['pass'] and len(t)>=cfg['sampling']['min_nt'] and len(s)>=cfg['sampling']['min_ns'] and
             np.all(np.isfinite(phi)) and np.all(np.diff(t)>0) and np.all(np.diff(s)>0) and
             tr<=cfg['sampling']['uniform_rel_tol'] and sr<=cfg['sampling']['uniform_rel_tol'])
        row={"opaque_id":oid,"source_group":group,"evidence_class":evidence_class,
             "solver_id":m.get('solver_id'),"generator_id":m.get('generator_id'),
             "replication_group":m.get('replication_group'),"simulation_independence_group":m.get('simulation_independence_group'),
             "input_sha256":case['sha256'],"metadata_sha256":case['meta_sha256'],
             "boundary":boundary,"nt":len(t),"ns":len(s),"t_uniform_rel":tr,"s_uniform_rel":sr,"G1_admissible":bool(adm)}
        row['effective_replication_group']=replication_group(row)
        prov.append({"opaque_id":oid,"source_group":group,"evidence_class":evidence_class,"effective_replication_group":row['effective_replication_group'],
                     "sha256":case['sha256'],"metadata_sha256":case['meta_sha256'],
                     "upstream_geometry_sha256":m.get('upstream_geometry_sha256'),"carrier_sha256":m.get('carrier_sha256'),
                     "phase_definition_id":m.get('phase_definition_id'),"perturbation_id":m.get('perturbation_id'),
                     "solver_id":m.get('solver_id'),"generator_id":m.get('generator_id'),"provider_version":m.get('provider_version')})
        if not adm:
            row.update({"G2_spectral":"NOT_RUN_PREREQUISITE","G2_phase_discovery":"NOT_RUN_PREREQUISITE","G3_phase_confirmation":"NOT_RUN_PREREQUISITE",
                        "G2_memory_discovery":"NOT_RUN_PREREQUISITE","G3_memory_confirmation":"NOT_RUN_PREREQUISITE","G4_numerical":"NOT_RUN_PREREQUISITE"})
            rows.append(row); continue

        sm,q,_=pod_metrics(phi,cfg['spectral']['top_k'],cfg['phase']['discovery_fraction'])
        spass=(sm['orthogonality_residual']<=cfg['spectral']['orthogonality_max'] and sm['discovery_confirmation_subspace_overlap']>=cfg['spectral']['subspace_overlap_min'])
        row.update({"pod_top_energy_fraction":sm['top_energy_fraction'],"pod_orthogonality_residual":sm['orthogonality_residual'],
                    "pod_split_overlap":sm['discovery_confirmation_subspace_overlap'],"G2_spectral":"PASS" if spass else "FAIL"})

        y,ss,ph=phase_features(phi,dt,ds,boundary,'python'); pm=phase_model_competition(y,ss,ph,cfg['phase']['discovery_fraction']); sg=pm['SG']
        g2p=bool(sg['physical_coefficients'] and sg['design_condition']<=cfg['phase']['design_condition_max'] and sg['delta_bic_vs_best']>=cfg['phase']['delta_bic_min'])
        g3p=bool(g2p and sg['nrmse_ratio_vs_best']<=cfg['phase']['nrmse_ratio_max'])
        row.update({"SG_delta_bic":sg['delta_bic_vs_best'],"SG_nrmse_ratio":sg['nrmse_ratio_vs_best'],"SG_a":sg['coef'][0],"SG_b":sg['coef'][1],
                    "SG_design_condition":sg['design_condition'],"G2_phase_discovery":"PASS" if g2p else "FAIL",
                    "G3_phase_confirmation":"PASS" if g3p else ("FAIL" if g2p else "NOT_RUN_PREREQUISITE"),
                    "phase_best_model":min(pm,key=lambda k:pm[k]['discovery_bic'])})

        rd_source='provided'
        if case['ringdown'] is not None:
            rt=case['ringdown_t'] if case['ringdown_t'] is not None else t[:len(case['ringdown'])]; rv=case['ringdown']
        else: rt,rv=derived_ringdown(t,q); rd_source='derived_pod_energy'
        g2m=False; g3m=False; ml=None
        try:
            rm,_,_=ringdown_competition(rt,rv,cfg['ringdown']['train_fraction']); ml=rm['ML']; alo,ahi=cfg['ringdown']['alpha_support_bounds']
            g2m=bool(ml['delta_bic_vs_best']>=cfg['ringdown']['delta_bic_min'] and alo<ml['alpha']<ahi)
            g3m=bool(g2m and ml['nrmse_ratio_vs_best']<=cfg['ringdown']['nrmse_ratio_max'])
            row.update({"ringdown_source":rd_source,"ML_delta_bic":ml['delta_bic_vs_best'],"ML_nrmse_ratio":ml['nrmse_ratio_vs_best'],
                        "ML_alpha":ml['alpha'],"ML_tau":ml['tau'],"G2_memory_discovery":"PASS" if g2m else "FAIL",
                        "G3_memory_confirmation":"PASS" if g3m else ("FAIL" if g2m else "NOT_RUN_PREREQUISITE"),
                        "ringdown_best_model":min(rm,key=lambda k:rm[k]['bic'])})
        except Exception as e:
            row.update({"ringdown_source":rd_source,"G2_memory_discovery":"UNRESOLVED","G3_memory_confirmation":"UNRESOLVED","ringdown_error":str(e)})

        phase_rc=phase_resolution_certification(phi,dt,ds,boundary,cfg) if g3p else None
        phase_bc=phase_backend_certification(phi,dt,ds,boundary,cfg) if g3p else None
        mem_rc=memory_resolution_certification(rt,rv,cfg) if g3m else None
        mem_bc=memory_backend_certification(rt,ml['tau'],ml['alpha'],cfg) if g3m and ml is not None else None
        phase_certified=(not g3p) or bool(phase_rc and phase_rc.get('pass') and phase_bc and phase_bc.get('pass'))
        memory_certified=(not g3m) or bool(mem_rc and mem_rc.get('pass') and mem_bc and mem_bc.get('pass'))
        any_confirmed=bool(g3p or g3m); ncert=bool(any_confirmed and phase_certified and memory_certified)
        row.update({"phase_resolution_sg_coeff_rel_l2":phase_rc.get('sg_coeff_relative_l2') if phase_rc else None,
                    "memory_resolution_alpha_abs_delta":mem_rc.get('alpha_abs_delta') if mem_rc else None,
                    "memory_resolution_tau_rel_delta":mem_rc.get('tau_relative_delta') if mem_rc else None,
                    "native_available":(phase_bc or mem_bc or {}).get('available'),
                    "phase_native_parity_relative_l2":phase_bc.get('relative_l2') if phase_bc else None,
                    "memory_native_parity_relative_l2":mem_bc.get('relative_l2') if mem_bc else None,
                    "G4_phase_numerical":"PASS" if g3p and phase_certified else ("UNRESOLVED" if g3p else "NOT_RUN_PREREQUISITE"),
                    "G4_memory_numerical":"PASS" if g3m and memory_certified else ("UNRESOLVED" if g3m else "NOT_RUN_PREREQUISITE"),
                    "G4_numerical":"PASS" if ncert else ("UNRESOLVED" if any_confirmed else "NOT_RUN_PREREQUISITE")})
        rows.append(row)

    admiss=[r for r in rows if r.get('G1_admissible')]
    ledger.add(GateRecord('G1_ADMISSIBILITY',_status(bool(admiss),g0=='PASS'),'Are cases numerically and contractually admissible?',
        {"admissible":len(admiss),"total":len(rows)},depends_on=('G0_PROVENANCE',)))

    disc=[r for r in admiss if r.get('G2_spectral')=='PASS' and (r.get('G2_phase_discovery')=='PASS' or r.get('G2_memory_discovery')=='PASS')]
    ledger.add(GateRecord('G2_DISCOVERY',_status(bool(disc),bool(admiss)),'Does preregistered blind discovery identify SG and/or ML candidates after spectral qualification?',
        {"candidate_cases":len(disc),"admissible":len(admiss)},depends_on=('G1_ADMISSIBILITY',)))

    conf=[r for r in disc if r.get('G3_phase_confirmation')=='PASS' or r.get('G3_memory_confirmation')=='PASS']
    ledger.add(GateRecord('G3_CONFIRMATION',_status(bool(conf),bool(disc)),'Do discovered candidates survive the frozen held-out temporal block?',
        {"confirmed_cases":len(conf),"discovered":len(disc)},depends_on=('G2_DISCOVERY',)))

    cert=[r for r in conf if r.get('G4_numerical')=='PASS']
    g4status='PASS' if cert else ('UNRESOLVED' if conf else 'NOT_RUN_PREREQUISITE')
    ledger.add(GateRecord('G4_NUMERICAL_CERTIFICATION',g4status,'Are confirmed candidates resolution-stable and CPU/native parity-qualified?',
        {"certified_cases":len(cert),"confirmed":len(conf),"native_module_available":native_available(),"native_required":cfg['numerics']['native_required']},
        depends_on=('G3_CONFIRMATION',)))

    phase_cert=[r for r in cert if r.get('G3_phase_confirmation')=='PASS']
    mem_cert=[r for r in cert if r.get('G3_memory_confirmation')=='PASS']
    joint_cases=[r for r in cert if r.get('G3_phase_confirmation')=='PASS' and r.get('G3_memory_confirmation')=='PASS']
    min_groups=cfg['replication']['min_independent_groups']
    phase_rep=assess_replication(phase_cert,min_groups)
    memory_rep=assess_replication(mem_cert,min_groups)
    joint_rep=assess_replication(joint_cases,min_groups)

    any_control=phase_rep['control_recovered'] or memory_rep['control_recovered']
    g5_control='PASS' if any_control else ('UNRESOLVED' if cert else 'NOT_RUN_PREREQUISITE')
    ledger.add(GateRecord('G5_CONTROL_REPLICATION',g5_control,
        'Do certified synthetic controls recover the intended implementation behavior without being treated as physical replication?',
        {"phase":phase_rep,"memory":memory_rep,"joint":joint_rep},depends_on=('G4_NUMERICAL_CERTIFICATION',)))

    physical_rep=phase_rep['cross_source_pass'] or memory_rep['cross_source_pass']
    physical_present=phase_rep['physical_evidence_present'] or memory_rep['physical_evidence_present']
    g5='PASS' if physical_rep else ('UNRESOLVED' if physical_present else 'NOT_RUN_PREREQUISITE')
    ledger.add(GateRecord('G5_CROSS_SOURCE_REPLICATION',g5,'Does certified support replicate across physically independent source groups?',
        {"phase":phase_rep,"memory":memory_rep,"joint":joint_rep,
         "excluded_evidence_classes":["synthetic_control","simulation"]},depends_on=('G4_NUMERICAL_CERTIFICATION',)))

    implementation_conclusion='UNRESOLVED'
    if joint_rep['control_recovered']: implementation_conclusion='JOINT_CONTROL_RECOVERED'
    elif phase_rep['control_recovered']: implementation_conclusion='PHASE_CONTROL_RECOVERED'
    elif memory_rep['control_recovered']: implementation_conclusion='MEMORY_CONTROL_RECOVERED'

    if g5=='PASS':
        if len(_physical_groups(joint_rep))>=min_groups: conclusion='JOINT_SUPPORTED'; g6='PASS'
        elif len(_physical_groups(phase_rep))>=min_groups: conclusion='PHASE_ONLY_SUPPORTED'; g6='FAIL'
        elif len(_physical_groups(memory_rep))>=min_groups: conclusion='MEMORY_ONLY_SUPPORTED'; g6='FAIL'
        else: conclusion='UNRESOLVED'; g6='UNRESOLVED'
    elif any_control and not physical_present:
        conclusion=implementation_conclusion; g6='NOT_RUN_PREREQUISITE'
    elif phase_rep['simulation_groups'] or memory_rep['simulation_groups']:
        conclusion='SIMULATION_SUPPORTED_NOT_PHYSICAL_REPLICATION'; g6='NOT_RUN_PREREQUISITE'
    else:
        conclusion='UNRESOLVED'; g6='NOT_RUN_PREREQUISITE'
    ledger.add(GateRecord('G6_MECHANISM_PHYSICS',g6,'Do SG phase closure and fractional-memory closure co-occur and replicate in physical independent evidence?',
        {"conclusion":conclusion,"implementation_conclusion":implementation_conclusion,"joint_physical_groups":_physical_groups(joint_rep)},
        depends_on=('G5_CROSS_SOURCE_REPLICATION',)))

    build_prov=load_json_if_exists(ROOT/'build/COMPILER_PROVENANCE.json')
    backend_selftest=load_json_if_exists(ROOT/'build/BACKEND_SELFTEST.json')
    dd32_selftest=load_json_if_exists(ROOT/'build/DD32_BACKEND_SELFTEST.json')
    write_csv(blind/'case_results.csv',rows)
    write_json(blind/'provenance.json',{
      "framework_version":FRAMEWORK_VERSION,"framework_patch_level":FRAMEWORK_PATCH_LEVEL,
      "environment":environment_snapshot(),"native_available":native_available(),
      "backend_authority":{"python_fp64":"reference","cpp_fp64":"confirmatory","sycl_fp32":"screening-only","sycl_dd32":"experimental-screening-not-IEEE-FP64"},
      "compiler_provenance":build_prov,"backend_selftest":backend_selftest,"dd32_selftest":dd32_selftest,
      "config_sha256":sha256_file(config_path),"cases":prov})
    ledger.write(blind/'gate_ledger.json')
    write_json(blind/'summary.json',{
      "schema":"A056-BLIND-SUMMARY-3","framework_schema":FRAMEWORK_SCHEMA,"framework_version":FRAMEWORK_VERSION,
      "framework_patch_level":FRAMEWORK_PATCH_LEVEL,"conclusion":conclusion,"implementation_conclusion":implementation_conclusion,
      "case_count":len(rows),"admissible":len(admiss),"discovery_cases":len(disc),"confirmation_cases":len(conf),"certified_cases":len(cert),
      "phase_replication":phase_rep,"memory_replication":memory_rep,"joint_replication":joint_rep})
    return out


def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--config',default='configs/basic.json'); p.add_argument('--output',default=None)
    a=p.parse_args(); print(run(a.input,a.config,a.output))
if __name__=='__main__': main()
