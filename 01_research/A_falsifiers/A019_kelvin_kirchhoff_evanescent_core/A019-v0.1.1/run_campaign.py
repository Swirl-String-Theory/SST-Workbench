from __future__ import annotations
import argparse, json, sys, time
from datetime import datetime
from pathlib import Path
from kelvin_falsifier.io import discover_cases,write_json
from kelvin_falsifier.blind import prepare_blind,run_blind
from kelvin_falsifier.scoring import score_blind
from kelvin_falsifier.report import unblind_and_report

ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description='Run complete blind Kelvin/Kirchhoff SST campaign.')
    ap.add_argument('--config',required=True)
    ap.add_argument('--knots',required=True)
    ap.add_argument('--threads',type=int,default=16)
    ap.add_argument('--out-dir')
    ap.add_argument('--require-native',action='store_true')
    ap.add_argument('--force-python',action='store_true')
    a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text(encoding='utf-8')); mode=cfg.get('mode','campaign')
    out=Path(a.out_dir) if a.out_dir else ROOT/f"outputs_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out.mkdir(parents=True,exist_ok=False)
    try:
        cases=discover_cases(a.knots,cfg.get('selection'))
        write_json(out/'datasets.private.json',{'knots_dir':str(Path(a.knots).resolve()),'mode':mode,'cases':cases})
        blind=prepare_blind(cases,out,mode,cfg,ROOT/'config'/'preregistered_gates.json')
        run_blind(blind,cfg,a.threads,require_native=a.require_native,force_python=a.force_python)
        score_blind(blind)
        rows=unblind_and_report(out)
        print(f'[KK-SST] complete: {out}')
        print(f'[KK-SST] cases={len(rows)} PASS={sum(r["overall"]=="PASS" for r in rows)} FAIL={sum(r["overall"]=="FAIL" for r in rows)} INCONCLUSIVE={sum(r["overall"]=="INCONCLUSIVE" for r in rows)}')
        return 0
    except Exception as e:
        write_json(out/'CAMPAIGN_ERROR.json',{'error_type':type(e).__name__,'error':str(e)})
        print(f'[KK-SST] ERROR: {e}',file=sys.stderr); print(f'[KK-SST] partial output: {out}',file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
