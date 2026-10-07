from pathlib import Path
import json,sys,csv
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from a056_falsifier.blind import verify_reveal
from a056_falsifier.util import write_json
NAME='A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0'
out=ROOT/f'{NAME}-outputs'; blind=out/'BLIND'; rev=out/'REVEALED'; rev.mkdir(parents=True,exist_ok=True)
ok,expected,actual=verify_reveal(ROOT/'PRIVATE'/'smoke_reveal.json',ROOT/'reveal_commitment.sha256')
if not ok: raise SystemExit('reveal commitment mismatch')
truth={x['opaque_id']:x for x in json.loads((ROOT/'PRIVATE'/'smoke_reveal.json').read_text())['cases']}
rows=list(csv.DictReader((blind/'case_results.csv').open(encoding='utf-8')))
checks=[]
for r in rows:
    t=truth[r['opaque_id']]; phase_expected=(t['phase_truth']=='SG'); ml_expected=(t['ringdown_truth']=='ML')
    phase_got=(r['G3_phase']=='PASS'); ml_got=(r['G4_ringdown']=='PASS')
    checks.append({"opaque_id":r['opaque_id'],"phase_expected":phase_expected,"phase_got":phase_got,"memory_expected":ml_expected,"memory_got":ml_got,"pass":phase_expected==phase_got and ml_expected==ml_got})
status='IMPLEMENTATION_VALIDATED' if checks and all(x['pass'] for x in checks) else 'IMPLEMENTATION_FAILED'
write_json(rev/'smoke_control_check.json',{"status":status,"commitment":actual,"checks":checks})
print(status)
