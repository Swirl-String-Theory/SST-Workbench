from __future__ import annotations
from pathlib import Path
from sst_falsifier.runner import instance_output_root
from .util import read_json,write_json
from .workbench import workbench_root,a055_v031_output
from .upstream import find_a054_campaign,verify_a054_seal,verify_framework_output
from .compound_v040 import recompute_compound_chirality
from .discovery import summarize_v031
from .native_metric import certify as certify_native_metric

def _config(root,mode):
    mode=mode.upper(); name='basic' if mode=='BASIC' else 'framework_smoke' if mode=='SMOKE' else 'full'; return read_json(Path(root)/'configs'/f'{name}.json')

def _skip(ledger,gids):
    for gid in gids:
        if not ledger.defs[gid].enabled: ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by frozen profile/gate plan.')
        else: ledger.skip_due_prerequisite(gid)

def run(root,cfg,ledger,mode):
    out=instance_output_root(root,cfg); out.mkdir(parents=True,exist_ok=True); acfg=_config(root,mode); ledger.record('G0','PASS',metrics={'mode':mode,'framework_version':cfg['framework']['version']},reason='Framework verified frozen protocol.')
    wb=workbench_root()
    try:
        a054=find_a054_campaign(wb,acfg['a054_preset']); s054=verify_a054_seal(a054); old=a055_v031_output(wb); s031=verify_framework_output(old,'FULL')
        ledger.record('G1','PASS',metrics={'a054_campaign':str(a054),'a054_seal_schema':s054['schema'],'v031_output':str(old),'v031_protocol':s031['protocol_bundle_sha256']},reason='Sealed A054 and completed v0.3.1 discovery baseline are provenance-valid.')
    except Exception as e:
        ledger.record('G1','UNRESOLVED',reason=f'{type(e).__name__}: {e}'); _skip(ledger,('G2','G3','G4','G5','G6','G7','G8')); return {'schema':'A055-BACKEND-MANIFEST-040','status':'UPSTREAM_UNRESOLVED'}
    discovery=summarize_v031(old); write_json(out/'A055_V031_DISCOVERY_BASELINE_BLIND.json',discovery)
    try:
        comp=recompute_compound_chirality(a054,acfg); write_json(out/'A055_CHIRAL_COVARIANCE_BLIND.json',comp)
        maxmeta=float(comp['max_metamorphic_abs_error'])
        g2=bool(comp['analytic_covariance_selftest']['pass'] and comp['max_recompute_eigenvalue_assignment_relative_error']<=float(acfg['recompute_eigenvalue_assignment_rel_max']) and maxmeta<=float(acfg['metamorphic_abs_tol']))
        ledger.record('G2','PASS' if g2 else 'FAIL',metrics={'analytic_covariance_selftest':comp['analytic_covariance_selftest'],'max_eigenvalue_assignment_relative_error':comp['max_recompute_eigenvalue_assignment_relative_error'],'spectrum_tolerance':acfg['recompute_eigenvalue_assignment_rel_max'],'max_metamorphic_abs_error':maxmeta,'metamorphic_tolerance':acfg['metamorphic_abs_tol']},reason='' if g2 else 'Reference selftest, sealed-spectrum recomputation, or real-mode representation covariance failed.')
    except Exception as e:
        ledger.record('G2','UNRESOLVED',reason=f'{type(e).__name__}: {e}'); _skip(ledger,('G3','G4','G5','G6','G7','G8')); return {'schema':'A055-BACKEND-MANIFEST-040','status':'NUMERICAL_UNRESOLVED'}
    if not g2:
        _skip(ledger,('G3','G4','G5','G6','G7','G8')); return {'schema':'A055-BACKEND-MANIFEST-040','status':'REFERENCE_FAIL'}
    # G3: canonical circulation-relative signal before invariance/convergence promotion
    fine_rows=[]
    for r in comp['rows']:
        s=r['levels'][-1]['summary']; fine_rows.append((s['qualified_mode_count'],s['sector_vote_bias']))
    signal=sum(n>=int(acfg['min_qualified_modes_per_sector']) and abs(float(b))>=float(acfg['min_sector_vote_bias']) for n,b in fine_rows)
    ledger.record('G3','PASS' if signal>0 else 'FAIL',metrics={'fine_directionally_biased_sectors':signal,'evaluated_sectors':len(fine_rows),'min_qualified_modes':acfg['min_qualified_modes_per_sector'],'min_abs_vote_bias':acfg['min_sector_vote_bias']},reason='' if signal else 'No fine-resolution sector exhibits the frozen circulation-relative directional bias.')
    ledger.record('G4','NOT_APPLICABLE',reason='No independent held-out physical confirmation source is claimed in v0.4.0.')
    # G5 is reserved by framework for C++ CPU certification
    try:
        native=certify_native_metric(root,acfg); ledger.record('G5','PASS' if native['status']=='PASS' else 'FAIL',metrics=native,reason='' if native['status']=='PASS' else 'Native signed-power metric failed parity.',requested_backend='cpp',actual_backend=native.get('actual_backend'),authority='CERTIFICATION')
    except Exception as e:
        native={'status':'UNRESOLVED','error':f'{type(e).__name__}: {e}'}; ledger.record('G5','UNRESOLVED',metrics=native,reason=native['error'],requested_backend='cpp',authority='CERTIFICATION')
    ledger.record('G6','NOT_APPLICABLE',reason='CPU profile: GPU screening disabled.')
    ledger.record('G7','NOT_APPLICABLE',reason='No independent physical confirmation source is claimed; v0.3.1 is discovery evidence from the same upstream simulation family.')
    robust=int(comp['robust_candidate_count'])
    if ledger.status('G3')=='PASS' and ledger.status('G5')=='PASS':
        ledger.record('G8','PASS' if robust>0 else 'FAIL',metrics={'resolution_and_epsilon_robust_candidates':robust,'robust_sector_count_min':acfg['robust_sector_count_min'],'mechanism_promoted_sectors':comp['mechanism_promoted_sector_count']},reason='' if robust else 'Fine directional bias did not survive the frozen resolution/epsilon recurrence rule in any anonymous candidate.')
    else: ledger.skip_due_prerequisite('G8')
    summary={'schema':'A055-BLIND-SUMMARY-040','framework_version':cfg['framework']['version'],'mode':mode,'discovery_baseline':discovery,
      'chiral_covariance':{'row_count':len(comp['rows']),'fine_biased_sector_count':signal,'max_metamorphic_abs_error':maxmeta,'robust_candidate_count':robust,'mechanism_promoted_sector_count':comp['mechanism_promoted_sector_count']},
      'interpretation':'A v0.4.0 robust candidate is evidence only for a representation-covariant, resolution/epsilon-stable circulation-relative traveling-wave bias in the finite projected model.'}
    write_json(out/'A055_BLIND_SUMMARY.json',summary)
    return {'schema':'A055-BACKEND-MANIFEST-040','framework_version':cfg['framework']['version'],'a054_backend':{'sealed':comp['a054_sealed_backend'],'actual':comp['a054_actual_backend']},'instance_cpp_metric':native,'summary':summary}
