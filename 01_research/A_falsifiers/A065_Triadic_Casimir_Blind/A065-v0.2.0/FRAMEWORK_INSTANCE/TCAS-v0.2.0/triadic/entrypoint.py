from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
from .runner import ROOT,run_blind,reveal,verify_predictions_against_commit
from .report_pdf import create_report


def command(args):
    mode=args[0].upper() if args else 'ALL'
    if mode in ('VERIFY','SELFTEST','PARITY','CERTIFY'):
        from .runner import main as legacy
        old=sys.argv
        try:sys.argv=['triadic.runner',mode];legacy()
        finally:sys.argv=old
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
        if mode in ('ALL','FRAMEWORK','BASIC','FULL'):
            from framework_bridge.install import run_framework
            r=run_framework(ROOT)
            (ROOT/'FRAMEWORK_STATUS.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
            print('Official SST framework status:',r['state'],r.get('detail',''))
            if mode in ('FRAMEWORK','FULL') and r['state']!='OFFICIAL_FRAMEWORK_EXECUTED':
                create_report(ROOT,label=mode,framework_status=r)
                raise SystemExit(3)
        audit=create_report(ROOT,label=mode)
        print('PDF CREATED:',audit['path']);print('PDF PUBLISHED:',audit['published_to'])
        return
    if mode=='REPORT':
        r=create_report(ROOT,label=mode)
        print('PDF PUBLISHED:',r['published_to'])
        return
    raise SystemExit('Valid modes: ALL FRAMEWORK FULL BASIC BLIND REVEAL REPORT PKLSA VERIFY SELFTEST PARITY CERTIFY')

if __name__=='__main__':command(sys.argv[1:])
