from __future__ import annotations
from pathlib import Path
from typing import Any
from mega.common import implementation_verify, verify_source_archive, load_phase_result, phase_dir, verify_local_manifest

DISCOVERY_PHASES=['P02','P03','P04','P05','P06']
MECHANISM_PHASES=['P02','P03','P04','P05','P06','P07','P08','P09']

def _rows(pids,root):
    rows=[]
    for p in pids:
        r=load_phase_result(p,root);m=verify_local_manifest(phase_dir(p,root)) if r else {'pass':False,'reason':'missing'}
        rows.append({'phase':p,'result':r,'manifest':m})
    return rows

def _summary(rows):
    return [{'phase':x['phase'],'status':None if x['result'] is None else x['result'].get('status'),'evidence_class':None if x['result'] is None else x['result'].get('evidence_class'),'manifest_ok':x['manifest'].get('pass')} for x in rows]

def run_scientific_pipeline(root:Path,cfg:dict[str,Any],ledger,mode:str)->dict[str,Any]:
    impl=implementation_verify(root)
    ledger.record('G0','PASS' if impl.get('pass') else 'FAIL',metrics=impl,reason='Framework v1.0.6 and the A059 v0.2.0 implementation commitment are byte-consistent.')
    if ledger.status('G0')!='PASS':
        return {'schema':'A059-BACKEND-MANIFEST-2','framework_version':'1.0.6','status':'IMPLEMENTATION_INVALID','implementation':impl}
    src=verify_source_archive(root)
    ledger.record('G1','PASS' if src.get('pass') else 'UNRESOLVED',metrics=src,reason='Embedded E011 v0.3.0 STATIC_READY archive must match its preregistered SHA-256 exactly.')
    if ledger.status('G1')!='PASS':
        for gid in ('G2','G3','G8'): ledger.skip_due_prerequisite(gid,reason='E011 source gate did not PASS.')
        for gid in ('G4','G5','G6','G7'): ledger.record(gid,'NOT_APPLICABLE',reason='Disabled or not independently sourced in A059 v0.2.0.')
        ledger.skip_due_prerequisite('G9',reason='Source gate did not PASS.')
        return {'schema':'A059-BACKEND-MANIFEST-2','framework_version':'1.0.6','authority':'PYTHON_NUMPY_FP64_DYNAMIC_PROBES','implementation':impl}

    foundations=_rows(['P00','P01'],root); fst=[None if x['result'] is None else x['result'].get('status') for x in foundations]
    if any(x['result'] is None or not x['manifest'].get('pass') for x in foundations): g2='UNRESOLVED'; why='P00/P01 missing or manifest-invalid.'
    elif all(s=='PASS' for s in fst): g2='PASS'; why='Source intake and self-contained dynamic probe qualification both PASS.'
    elif any(s=='FAIL' for s in fst): g2='FAIL'; why='At least one foundation phase FAILed; later siblings still execute by nonblocking design.'
    else: g2='UNRESOLVED'; why='Foundation contains unresolved status.'
    ledger.record('G2',g2,metrics={'phases':_summary(foundations)},reason=why)

    drows=_rows(DISCOVERY_PHASES,root); valid=all(x['result'] is not None and x['manifest'].get('pass') for x in drows); dst=[x['result'].get('status') if x['result'] else None for x in drows]
    if not valid: g3='UNRESOLVED'; why='One or more dynamic operator phases are missing or manifest-invalid.'
    elif 'PASS' in dst: g3='PASS'; why='At least one target-free dynamic operator lane PASSes; non-PASS sibling lanes remain preserved.'
    elif 'FAIL' in dst: g3='FAIL'; why='Dynamic operator phases executed but none PASSed.'
    else: g3='UNRESOLVED'; why='Dynamic operator phases contain only unresolved/deferred outcomes.'
    ledger.record('G3',g3,metrics={'phases':_summary(drows),'pass_count':dst.count('PASS'),'fail_count':dst.count('FAIL'),'unresolved_count':dst.count('UNRESOLVED')},reason=why)

    ledger.record('G4','NOT_APPLICABLE',reason='No independent held-out physical experiment is claimed in v0.2.0.')
    ledger.record('G5','NOT_APPLICABLE',reason='Python/NumPy FP64 is authoritative in v0.2.0; no native C++ certification lane is promoted.')
    ledger.record('G6','NOT_APPLICABLE',reason='GPU screening is disabled in v0.2.0.')
    ledger.record('G7','NOT_APPLICABLE',reason='E011 provider multiplicity and canonical braid probes are not independent physical replication.')

    mrows=_rows(MECHANISM_PHASES,root); valid=all(x['result'] is not None and x['manifest'].get('pass') for x in mrows); mst=[x['result'].get('status') if x['result'] else None for x in mrows]
    if not valid: g8='UNRESOLVED'; why='One or more mechanism phases are missing or manifest-invalid.'
    elif all(s=='PASS' for s in mst): g8='PASS'; why='Every registered dynamic/operator mechanism sector PASSes.'
    elif 'UNRESOLVED' in mst or 'DEFERRED' in mst: g8='UNRESOLVED'; why='Integrated Rosetta cannot close while required sectors remain UNRESOLVED/DEFERRED; explicit FAILs remain preserved.'
    else: g8='FAIL'; why='All sectors resolved but at least one explicit FAIL prevents integrated closure.'
    ledger.record('G8',g8,metrics={'phases':_summary(mrows),'pass_count':mst.count('PASS'),'fail_count':mst.count('FAIL'),'unresolved_count':mst.count('UNRESOLVED')},reason=why)
    ledger.record('G9','DEFERRED',reason='Semantic reveal is separate and commitment-verified.')
    return {'schema':'A059-BACKEND-MANIFEST-2','framework_version':'1.0.6','authority':'PYTHON_NUMPY_FP64_DYNAMIC_PROBES','note':'A059 v0.2.0 promotes self-contained finite-core dynamic operators on canonical closed-braid probes; E011 remains STATIC_READY provenance rather than independent dynamic evidence.','implementation':impl}
