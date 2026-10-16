from __future__ import annotations
import json,subprocess,sys,os
from pathlib import Path
from .runner import ROOT,run_blind,reveal,verify_predictions_against_commit
from .report_pdf import create_report


def command(args):
    mode=args[0].upper() if args else 'ALL'
    if mode not in ('VERIFY','SELFTEST','PROVIDER','PKLSA','CERTIFY','REVEAL') and os.getenv('SST_A065_ISOLATED_RUN')!='1':
        raise SystemExit('Direct write blocked; run run_all.cmd or run_all.sh to obtain a unique no-overwrite run')
    if mode=='DYNAMICS':
        # A dedicated, machine-readable artifact must exist even for a
        # standalone dynamics-only run. No stdout-only success claims.
        from .dynamics import run
        from .security import sha
        from .provider_manifest import verify as verify_provider
        result=run(ROOT)
        manifest=verify_provider(ROOT)
        payload={'schema':'A065-DYNAMICS-RUN-1','scientific_status':'FILAMENT_ODE_SIMULATION_ONLY',
                 'provider_manifest_sha256':manifest['manifest_sha256'],
                 'provider_status':manifest['status'], 'result':result}
        destination=ROOT/'outputs'/'DYNAMICS_RESULT.json'
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as handle:
            json.dump(payload,handle,indent=2,sort_keys=True,ensure_ascii=False)
            handle.write('\n')
        print(json.dumps({'status':result['numerical_gate'],
                          'file':str(destination),
                          'sha256':sha(destination.read_bytes()),
                          'spatial_pairs':result['spatial_pairs']},indent=2))
        return
    if mode in ('VERIFY','SELFTEST','PARITY','CERTIFY'):
        from .runner import main as legacy
        old=sys.argv
        try:sys.argv=['triadic.runner',mode];legacy()
        finally:sys.argv=old
        return
    if mode=='PROVIDER':
        from .providers import check
        print(json.dumps(check(ROOT,raw_override=args[1] if len(args)>1 else None),indent=2))
        return
    if mode=='PKLSA':
        from .pklsa import bridge
        print(json.dumps(bridge(ROOT),indent=2))
        return
    if mode in ('BLIND','ALL','FRAMEWORK','REVEAL','BASIC','FULL'):
        if mode=='REVEAL':
            reveal(ROOT)
        else:
            if mode=='ALL':
                from .runner import main as legacy
                old=sys.argv
                try:sys.argv=['triadic.runner','SELFTEST'];legacy()
                finally:sys.argv=old
            run_blind(ROOT)
            # ALL intentionally keeps both physics and toy comparator blinded;
            # toy REVEAL is an explicit separate command, never an automatic side effect.
        framework_result=None
        if mode in ('ALL','FRAMEWORK','BASIC','FULL'):
            from framework_bridge.install import run_framework
            framework_result=run_framework(ROOT)
            (ROOT/'FRAMEWORK_STATUS.json').write_text(json.dumps(framework_result,indent=2)+'\n',encoding='utf-8')
            print('Official SST framework status:',framework_result['state'],framework_result.get('detail',''))
        audit=create_report(ROOT,label=mode,framework_status=framework_result)
        print('PDF CREATED:',audit['path']);print('PDF PUBLISHED:',audit['published_to'])
        # A completed portable PDF is never a substitute for failed/missing
        # official framework work. ALL, BASIC, FULL and FRAMEWORK fail closed.
        if framework_result and framework_result['state']!='OFFICIAL_FRAMEWORK_EXECUTED':
            raise SystemExit(3)
        return
    if mode=='REPORT':
        r=create_report(ROOT,label=mode)
        print('PDF PUBLISHED:',r['published_to'])
        return
    raise SystemExit('Valid modes: ALL FRAMEWORK FULL BASIC BLIND REVEAL REPORT PKLSA PROVIDER DYNAMICS VERIFY SELFTEST PARITY CERTIFY')

if __name__=='__main__':command(sys.argv[1:])
