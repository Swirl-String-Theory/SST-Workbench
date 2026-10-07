from pathlib import Path
import argparse,csv,json,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.blindness import verify_reveal
from sst_falsifier_framework.outputs import default_output_dir
p=argparse.ArgumentParser(); p.add_argument('--output',default=str(default_output_dir(ROOT))); a=p.parse_args(); out=Path(a.output)
ok,exp,act=verify_reveal(ROOT/'PRIVATE/smoke_reveal.json',ROOT/'reveal_commitment.sha256')
if not ok: raise SystemExit('reveal commitment mismatch')
truth={x['opaque_id']:x for x in json.loads((ROOT/'PRIVATE/smoke_reveal.json').read_text())['cases']}
rows=list(csv.DictReader((out/'BLIND/case_results.csv').open(encoding='utf-8'))); checks=[]
for r in rows:
    t=truth[r['opaque_id']]; checks.append({"opaque_id":r['opaque_id'],"phase_truth":t['phase_truth'],"phase_selected":r.get('phase_best_model'),
      "ringdown_truth":t['ringdown_truth'],"ringdown_selected":r.get('ringdown_best_model'),
      "phase_correct":r.get('phase_best_model')==t['phase_truth'],"ringdown_correct":r.get('ringdown_best_model')==t['ringdown_truth']})
status='IMPLEMENTATION_VALIDATED' if all(c['phase_correct'] and c['ringdown_correct'] for c in checks) else 'IMPLEMENTATION_CHECK_FAILED'
(out/'REVEALED').mkdir(parents=True,exist_ok=True); (out/'REVEALED/smoke_validation.json').write_text(json.dumps({"schema":"A056-REVEAL-2","status":status,"checks":checks},indent=2)+"\n")
print(status); raise SystemExit(0 if status=='IMPLEMENTATION_VALIDATED' else 3)
