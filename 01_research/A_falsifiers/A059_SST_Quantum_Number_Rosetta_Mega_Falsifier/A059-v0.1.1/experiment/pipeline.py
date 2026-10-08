from __future__ import annotations
from pathlib import Path
from typing import Any
from mega.common import implementation_verify, verify_source_archive, load_phase_result, phase_dir, verify_local_manifest

DISCOVERY_PHASES=['P02','P03','P04','P05','P06','P07']
MECHANISM_PHASES=['P02','P03','P04','P05','P06','P07','P08']

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
    ledger.record('G0','PASS' if impl.get('pass') else 'FAIL',metrics=impl,reason='Framework verified frozen protocol before pipeline entry; A056 additionally verifies its implementation manifest.')
    if ledger.status('G0')=='PASS':
        src=verify_source_archive(root)
        ledger.record('G1','PASS' if src.get('pass') else 'UNRESOLVED',metrics=src,reason='Embedded E011 archive must match its preregistered SHA-256 exactly.')
    else:
        # This path is normally unreachable in a valid frozen instance; keep fail-closed.
        return {'schema':'A056-BACKEND-MANIFEST-1','framework_version':'1.0.6','status':'IMPLEMENTATION_INVALID','implementation':impl}
    if ledger.status('G1')=='PASS':
        # G2: source/static sanity. P00/P01 failures do not block later G3/G8 because those gates depend only on G1.
        srows=_rows(['P00','P01'],root);sst=[None if x['result'] is None else x['result'].get('status') for x in srows]
        if any(x['result'] is None or not x['manifest'].get('pass') for x in srows):g2='UNRESOLVED';why='P00/P01 missing or phase-manifest invalid.'
        elif all(s=='PASS' for s in sst):g2='PASS';why='P00 source intake and P01 static structure both PASS.'
        elif any(s=='FAIL' for s in sst):g2='FAIL';why='At least one static foundation phase FAIL; later discovery remains executable by nonblocking design.'
        else:g2='UNRESOLVED';why='Static foundation contains UNRESOLVED status.'
        ledger.record('G2',g2,metrics={'phases':_summary(srows)},reason=why)
        # G3: target-free discovery exists if all requested phase outputs are integrity-valid and at least one lane PASSes.
        drows=_rows(DISCOVERY_PHASES,root);valid=all(x['result'] is not None and x['manifest'].get('pass') for x in drows);dst=[x['result'].get('status') if x['result'] else None for x in drows]
        if not valid:g3='UNRESOLVED';why='One or more discovery phases are missing or manifest-invalid.'
        elif 'PASS' in dst:g3='PASS';why='At least one target-free operator lane PASSes; non-PASS sibling lanes remain explicitly preserved and prevent integrated mechanism closure.'
        elif 'FAIL' in dst:g3='FAIL';why='Discovery phases executed but none PASSed and at least one FAILed.'
        else:g3='UNRESOLVED';why='Discovery phases contain only unresolved/deferred outcomes.'
        ledger.record('G3',g3,metrics={'phases':_summary(drows),'pass_count':dst.count('PASS'),'fail_count':dst.count('FAIL'),'unresolved_count':dst.count('UNRESOLVED')},reason=why)
        # Canonical framework lanes unused in this version.
        for gid,reason in [('G4','No independent held-out physical confirmation source is claimed in v0.1.1.'),('G5','No native C++ certification lane is enabled in v0.1.1.'),('G6','GPU screening is disabled in v0.1.1.'),('G7','E011 provider multiplicity is provenance structure, not an independent physical replication.')]:
            ledger.record(gid,'NOT_APPLICABLE',reason=reason)
        # G8 integrated mechanism deliberately hard: every mechanism phase must PASS.
        mrows=_rows(MECHANISM_PHASES,root);valid=all(x['result'] is not None and x['manifest'].get('pass') for x in mrows);mst=[x['result'].get('status') if x['result'] else None for x in mrows]
        if not valid:g8='UNRESOLVED';why='One or more mechanism phases are missing or manifest-invalid.'
        elif all(s=='PASS' for s in mst):g8='PASS';why='All preregistered mechanism sectors PASS.'
        elif 'UNRESOLVED' in mst or 'DEFERRED' in mst:g8='UNRESOLVED';why='Integrated mechanism cannot close while any required sector remains UNRESOLVED/DEFERRED; explicit FAILs remain preserved in metrics.'
        else:g8='FAIL';why='All mechanism sectors resolved, but at least one explicit FAIL prevents integrated closure.'
        ledger.record('G8',g8,metrics={'phases':_summary(mrows),'pass_count':mst.count('PASS'),'fail_count':mst.count('FAIL'),'unresolved_count':mst.count('UNRESOLVED')},reason=why)
        ledger.record('G9','DEFERRED',reason='Semantic reveal is separate and commitment-verified.')
    else:
        # In a source-invalid run, standard dependencies prevent scientific gates; record via prerequisite skips.
        for gid in ('G2','G3','G8'): ledger.skip_due_prerequisite(gid,reason='E011 source gate did not PASS.')
        for gid in ('G4','G5','G6','G7'): ledger.record(gid,'NOT_APPLICABLE',reason='Disabled in v0.1.1.')
        ledger.skip_due_prerequisite('G9',reason='Source gate did not PASS.')
    return {'schema':'A056-BACKEND-MANIFEST-1','framework_version':'1.0.6','authority':'PYTHON_NUMPY_FP64_STATIC_AND_DIAGNOSTIC','note':'No native/GPU lane is promoted in v0.1.1. Phase-specific evidence classes define the allowed scientific interpretation.','implementation':impl}
