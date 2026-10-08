from __future__ import annotations
from pathlib import Path
from sst_falsifier.runner import instance_output_root
from .util import read_json,write_json
from .workbench import workbench_root,a055_v031_output
from .upstream import find_a054_campaign,verify_a054_seal,verify_framework_output
from .compound_v041 import recompute_compound_chirality
from .discovery import summarize_v031
from .native_metric import certify as certify_native_metric
from .chirality import analytic_covariance_selftest
from .implementation import verify_implementation


def _config(root,mode):
    mode=mode.upper(); name='basic' if mode=='BASIC' else 'framework_smoke' if mode=='SMOKE' else 'full'
    return read_json(Path(root)/'configs'/f'{name}.json')


def _na(ledger,gid,reason='Disabled by frozen profile/gate plan.'):
    if ledger.status(gid) is None:
        if not ledger.defs[gid].enabled: ledger.record(gid,'NOT_APPLICABLE',reason=reason)
        else: ledger.skip_due_prerequisite(gid)


def _native(root,acfg):
    try:
        r=certify_native_metric(root,acfg)
        return r
    except Exception as e:
        return {'status':'UNRESOLVED','error':f'{type(e).__name__}: {e}','authority':'CERTIFICATION'}


def _signal(comp,acfg):
    fine=[]
    for r in comp.get('rows',[]):
        s=r['levels'][-1]['summary']; fine.append((s['qualified_mode_count'],s['sector_vote_bias']))
    count=sum(n>=int(acfg['min_qualified_modes_per_sector']) and abs(float(b))>=float(acfg['min_sector_vote_bias']) for n,b in fine)
    return int(count),len(fine)


def run(root,cfg,ledger,mode):
    out=instance_output_root(root,cfg); out.mkdir(parents=True,exist_ok=True); acfg=_config(root,mode)
    diag={'schema':'A055-DIAGNOSTIC-LEDGER-041','mode':mode,'official_gate_semantics_unchanged_by_diagnostics':True,
          'analytic_covariance_selftest':analytic_covariance_selftest()}
    try:
        impl=verify_implementation(root)
        ledger.record('G0','PASS',metrics={'mode':mode,'framework_version':cfg['framework']['version'],'implementation_commitment':impl},reason='Framework v1.0.6 verified the frozen protocol and the instance implementation commitment is byte-identical.')
    except Exception as e:
        ledger.record('G0','FAIL',reason=f'{type(e).__name__}: {e}')
        diag['implementation_error']=f'{type(e).__name__}: {e}'
        for gid in ('G1','G2','G3','G5','G8'):
            _na(ledger,gid)
        _na(ledger,'G4','No independent held-out physical confirmation source is claimed in v0.4.1.')
        _na(ledger,'G6','CPU profile: GPU screening disabled.')
        _na(ledger,'G7','No independent physical confirmation source is claimed; v0.3.1 is discovery evidence from the same upstream simulation family.')
        write_json(out/'A055_DIAGNOSTIC_LEDGER.json',diag)
        summary={'schema':'A055-BLIND-SUMMARY-041','framework_version':cfg['framework']['version'],'mode':mode,'status':'IMPLEMENTATION_MISMATCH','diagnostic_only':diag,'interpretation':'No science conclusion is allowed because the frozen instance implementation commitment failed.'}
        write_json(out/'A055_BLIND_SUMMARY.json',summary)
        return {'schema':'A055-BACKEND-MANIFEST-041','status':'IMPLEMENTATION_MISMATCH','framework_version':cfg['framework']['version'],'summary':summary}
    wb=workbench_root(); a054=None; old=None; comp=None; discovery=None
    try:
        a054=find_a054_campaign(wb,acfg['a054_preset']); s054=verify_a054_seal(a054); old=a055_v031_output(wb); s031=verify_framework_output(old,'FULL')
        ledger.record('G1','PASS',metrics={'a054_campaign':str(a054),'a054_seal_schema':s054['schema'],'v031_output':str(old),'v031_protocol':s031['protocol_bundle_sha256']},reason='Sealed A054 and completed v0.3.1 discovery baseline are provenance-valid.')
        discovery=summarize_v031(old); write_json(out/'A055_V031_DISCOVERY_BASELINE_BLIND.json',discovery)
    except Exception as e:
        ledger.record('G1','UNRESOLVED',reason=f'{type(e).__name__}: {e}')
        diag['upstream_error']=f'{type(e).__name__}: {e}'

    # G5 is intentionally independent of G2 in v0.4.1: it is a deterministic local kernel test.
    native=_native(root,acfg); diag['instance_cpp_metric']=native
    if ledger.defs['G5'].enabled:
        st=native.get('status','UNRESOLVED')
        if st not in {'PASS','FAIL'}: st='UNRESOLVED'
        ledger.record('G5',st,metrics=native,reason='' if st=='PASS' else native.get('error','Native signed-power metric failed parity.'),requested_backend='cpp',actual_backend=native.get('actual_backend'),authority='CERTIFICATION')
    else:
        ledger.record('G5','NOT_APPLICABLE',reason='C++ certification disabled by the selected framework profile.')

    # Disabled framework slots are recorded even if upstream science is unresolved.
    _na(ledger,'G4','No independent held-out physical confirmation source is claimed in v0.4.1.')
    _na(ledger,'G6','CPU profile: GPU screening disabled.')
    _na(ledger,'G7','No independent physical confirmation source is claimed; v0.3.1 is discovery evidence from the same upstream simulation family.')

    if ledger.status('G1')!='PASS':
        _na(ledger,'G2'); _na(ledger,'G3'); _na(ledger,'G8')
        write_json(out/'A055_DIAGNOSTIC_LEDGER.json',diag)
        summary={'schema':'A055-BLIND-SUMMARY-041','framework_version':cfg['framework']['version'],'mode':mode,'status':'UPSTREAM_UNRESOLVED','diagnostic_only':diag,
                 'interpretation':'No chirality conclusion is allowed because upstream provenance did not close; independent local diagnostics are reported without promoting blocked science gates.'}
        write_json(out/'A055_BLIND_SUMMARY.json',summary)
        return {'schema':'A055-BACKEND-MANIFEST-041','status':'UPSTREAM_UNRESOLVED','framework_version':cfg['framework']['version'],'instance_cpp_metric':native,'summary':summary}

    try:
        comp=recompute_compound_chirality(a054,acfg); write_json(out/'A055_CHIRAL_COVARIANCE_BLIND.json',comp)
        maxmeta=float(comp['max_metamorphic_abs_error']); maxeig=float(comp['max_recompute_eigenvalue_assignment_relative_error'])
        g2=bool(comp['analytic_covariance_selftest']['pass'] and maxeig<=float(acfg['recompute_eigenvalue_assignment_rel_max']) and maxmeta<=float(acfg['metamorphic_abs_tol']))
        ledger.record('G2','PASS' if g2 else 'FAIL',metrics={'analytic_covariance_selftest':comp['analytic_covariance_selftest'],'max_eigenvalue_assignment_relative_error':maxeig,'spectrum_tolerance':acfg['recompute_eigenvalue_assignment_rel_max'],'max_metamorphic_abs_error':maxmeta,'metamorphic_tolerance':acfg['metamorphic_abs_tol'],'a054_runner_import_provenance':comp.get('a054_runner_import_provenance')},reason='' if g2 else 'Reference selftest, sealed-spectrum recomputation, or real-mode representation covariance failed.')
        signal,eval_sectors=_signal(comp,acfg); robust=int(comp['robust_candidate_count'])
        diag['computed_despite_later_gate_outcomes']={'fine_directionally_biased_sectors':signal,'evaluated_sectors':eval_sectors,'robust_candidate_count':robust,'mechanism_promoted_sector_count':comp['mechanism_promoted_sector_count'],'max_metamorphic_abs_error':maxmeta,'max_eigenvalue_assignment_relative_error':maxeig}
    except Exception as e:
        ledger.record('G2','UNRESOLVED',reason=f'{type(e).__name__}: {e}')
        diag['g2_computation_error']=f'{type(e).__name__}: {e}'
        _na(ledger,'G3'); _na(ledger,'G8')
        write_json(out/'A055_DIAGNOSTIC_LEDGER.json',diag)
        summary={'schema':'A055-BLIND-SUMMARY-041','framework_version':cfg['framework']['version'],'mode':mode,'status':'NUMERICAL_UNRESOLVED','discovery_baseline':discovery,'diagnostic_only':diag,
                 'interpretation':'No chirality conclusion is allowed because G2 is numerically/provenance unresolved; independent diagnostics remain diagnostic only.'}
        write_json(out/'A055_BLIND_SUMMARY.json',summary)
        return {'schema':'A055-BACKEND-MANIFEST-041','status':'NUMERICAL_UNRESOLVED','framework_version':cfg['framework']['version'],'instance_cpp_metric':native,'summary':summary}

    if ledger.status('G2')=='PASS':
        ledger.record('G3','PASS' if signal>0 else 'FAIL',metrics={'fine_directionally_biased_sectors':signal,'evaluated_sectors':eval_sectors,'min_qualified_modes':acfg['min_qualified_modes_per_sector'],'min_abs_vote_bias':acfg['min_sector_vote_bias']},reason='' if signal else 'No fine-resolution sector exhibits the frozen circulation-relative directional bias.')
        # G8 no longer depends on G3 PASS. A clean G3 FAIL therefore propagates to a formal G8 FAIL rather than stopping the campaign.
        if ledger.status('G5')=='PASS':
            ledger.record('G8','PASS' if robust>0 else 'FAIL',metrics={'resolution_and_epsilon_robust_candidates':robust,'robust_sector_count_min':acfg['robust_sector_count_min'],'mechanism_promoted_sectors':comp['mechanism_promoted_sector_count'],'fine_directionally_biased_sectors':signal},reason='' if robust else 'No anonymous candidate satisfies the frozen resolution/epsilon recurrence rule.')
        else:
            _na(ledger,'G8')
    else:
        _na(ledger,'G3'); _na(ledger,'G8')

    write_json(out/'A055_DIAGNOSTIC_LEDGER.json',diag)
    status='CERTIFIED_SIGNAL' if ledger.status('G8')=='PASS' else 'CHIRALITY_NOT_CERTIFIED' if ledger.status('G8')=='FAIL' else 'REFERENCE_FAIL' if ledger.status('G2')=='FAIL' else 'NUMERICAL_UNRESOLVED'
    summary={'schema':'A055-BLIND-SUMMARY-041','framework_version':cfg['framework']['version'],'mode':mode,'status':status,'discovery_baseline':discovery,
      'chiral_covariance':{'row_count':len(comp['rows']),'fine_biased_sector_count':signal,'max_metamorphic_abs_error':maxmeta,'robust_candidate_count':robust,'mechanism_promoted_sector_count':comp['mechanism_promoted_sector_count']},
      'diagnostic_only':diag,
      'interpretation':'A G8 PASS is evidence only for a representation-covariant, resolution/epsilon-stable circulation-relative traveling-wave bias in the finite projected model. G2 failure/unresolved status blocks physical interpretation even when later diagnostics were computable.'}
    write_json(out/'A055_BLIND_SUMMARY.json',summary)
    return {'schema':'A055-BACKEND-MANIFEST-041','status':status,'framework_version':cfg['framework']['version'],'a054_backend':{'sealed':comp['a054_sealed_backend'],'actual':comp['a054_actual_backend']},'instance_cpp_metric':native,'summary':summary}
