from pathlib import Path
import argparse, json


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output-dir',default='A056_v0.4.0-outputs')
    a=ap.parse_args()
    p=Path(a.output_dir)/'GATE_LEDGER.json'
    if not p.exists():
        raise SystemExit(f'missing gate ledger: {p}')
    obj=json.loads(p.read_text(encoding='utf-8'))
    print('[A056] blind gate summary')
    for r in obj.get('records',[]):
        gid=str(r.get('gate_id','?')); status=str(r.get('status','?')); reason=str(r.get('reason','')).strip()
        print(f'  {gid}: {status}' + (f' -- {reason}' if reason else ''))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
