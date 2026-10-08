from __future__ import annotations
from pathlib import Path
from sst_falsifier.runner import instance_output_root
from .util import read_json,write_json
from .workbench import workbench_root,a055_v030_output
from .upstream import find_a054_campaign,verify_a054_seal,verify_a055_v030_output
from .compound import recompute_compound_signed
from .legacy import summarize_legacy_controls
from .native_metric import certify as certify_native_metric


def _config(root,mode):
    mode=mode.upper(); name='basic' if mode=='BASIC' else 'framework_smoke' if mode=='SMOKE' else 'full'
    return read_json(Path(root)/'configs'/f'{name}.json')

def run(root,cfg,ledger,mode):
    out=instance_output_root(root,cfg); out.mkdir(parents=True,exist_ok=True); acfg=_config(root,mode)
    ledger.record('G0','PASS',metrics={'mode':mode,'framework_version':cfg['framework']['version']},reason='Framework verified the frozen protocol before pipeline entry.')
    wb=workbench_root()
    try:
        a054=find_a054_campaign(wb,acfg['a054_preset']); a054_seal=verify_a054_seal(a054)
        old=a055_v030_output(wb); old_seal=verify_a055_v030_output(old)
        ledger.record('G1','PASS',metrics={'a054_campaign':str(a054),'a054_seal_schema':a054_seal['schema'],'legacy_output':str(old)},reason='Both upstream campaigns are complete and seal-valid.')
    except Exception as e:
        ledger.record('G1','UNRESOLVED',reason=f'{type(e).__name__}: {e}')
        for gid in ('G2','G3','G4','G5','G6','G7','G8'):
            if not ledger.defs[gid].enabled: ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by frozen profile/gate plan.')
            else: ledger.skip_due_prerequisite(gid)
        return {'schema':'A055-BACKEND-MANIFEST-031','framework_version':cfg['framework']['version'],'status':'UPSTREAM_UNRESOLVED'}
    legacy=summarize_legacy_controls(old); write_json(out/'A055_LEGACY_CONTROL_BLIND.json',legacy)
    try:
        comp=recompute_compound_signed(a054,acfg); write_json(out/'A055_SIGNED_TRAVEL_BLIND.json',comp)
        maxerr=float(comp['max_recompute_eigenvalue_assignment_relative_error']); selfok=bool(comp['analytic_selftest']['pass'])
        g2=bool(selfok and maxerr<=float(acfg['recompute_eigenvalue_assignment_rel_max']))
        ledger.record('G2','PASS' if g2 else 'FAIL',metrics={'analytic_selftest':comp['analytic_selftest'],'max_eigenvalue_assignment_relative_error':maxerr,'tolerance':acfg['recompute_eigenvalue_assignment_rel_max']},reason='' if g2 else 'Signed-diagnostic selftest or sealed-spectrum recomputation parity failed.')
    except Exception as e:
        ledger.record('G2','UNRESOLVED',reason=f'{type(e).__name__}: {e}')
        for gid in ('G3','G4','G5','G6','G7','G8'):
            if not ledger.defs[gid].enabled: ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by frozen profile/gate plan.')
            else: ledger.skip_due_prerequisite(gid)
        return {'schema':'A055-BACKEND-MANIFEST-031','framework_version':cfg['framework']['version'],'status':'NUMERICAL_UNRESOLVED'}
    if not g2:
        for gid in ('G3','G4','G5','G6','G7','G8'):
            if not ledger.defs[gid].enabled: ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by frozen profile/gate plan.')
            else: ledger.skip_due_prerequisite(gid)
        return {'schema':'A055-BACKEND-MANIFEST-031','framework_version':cfg['framework']['version'],'status':'NUMERICAL_FAIL'}
    robust=int(comp['robust_candidate_count'])
    ledger.record('G3','PASS' if robust>0 else 'FAIL',metrics={'robust_anonymous_candidates':robust,'evaluated_candidates':len(comp['candidate_summaries']),'robust_sector_count_min':acfg['robust_sector_count_min']},reason='' if robust>0 else 'No anonymous candidate satisfied the frozen bidirectional traveling-pair recurrence rule.')
    ledger.record('G4','NOT_APPLICABLE',reason='No independent held-out physical confirmation source is claimed in v0.3.1.')
    try:
        native=certify_native_metric(root,acfg); ledger.record('G5','PASS' if native['status']=='PASS' else 'FAIL',metrics=native,reason='' if native['status']=='PASS' else 'Instance-local C++ signed-harmonic metric failed parity.',requested_backend='cpp',actual_backend=native.get('actual_backend'),authority='CERTIFICATION')
    except Exception as e:
        native={'status':'UNRESOLVED','error':f'{type(e).__name__}: {e}'}; ledger.record('G5','UNRESOLVED',metrics=native,reason=native['error'],requested_backend='cpp',actual_backend=None,authority='CERTIFICATION')
    ledger.record('G6','NOT_APPLICABLE',reason='CPU profile: GPU screening disabled.')
    ledger.record('G7','NOT_APPLICABLE',reason='No independent physical replication source is claimed; historical control reuse is not replication.')
    if ledger.status('G3')=='PASS' and ledger.status('G5')=='PASS':
        promoted=int(comp['mechanism_promoted_sector_count'])
        ledger.record('G8','PASS' if promoted>0 else 'FAIL',metrics={'mechanism_promoted_sectors':promoted,'requires_spatial_convergence':True,'requires_RPO':True},reason='' if promoted>0 else 'Traveling-wave evidence did not coincide with sealed upstream spatial convergence and accepted RPO in any sector.')
    else:
        ledger.skip_due_prerequisite('G8')
    summary={'schema':'A055-BLIND-SUMMARY-031','framework_version':cfg['framework']['version'],'mode':mode,'signed_travel':{
      'row_count':len(comp['rows']),'robust_candidate_count':robust,'mechanism_promoted_sector_count':comp['mechanism_promoted_sector_count']},
      'legacy_control':{k:legacy[k] for k in ('unique_mode_resolution_cells','qualified_modes','accepted_rpo','particle_promotions')},
      'interpretation':'A signed traveling pair is a linear projected-mode diagnostic only; physical particle identity is not established.'}
    write_json(out/'A055_BLIND_SUMMARY.json',summary)
    return {'schema':'A055-BACKEND-MANIFEST-031','framework_version':cfg['framework']['version'],'a054_backend':{'sealed':comp['a054_sealed_backend'],'actual':comp['a054_actual_backend']},'instance_cpp_metric':native,'summary':summary}
