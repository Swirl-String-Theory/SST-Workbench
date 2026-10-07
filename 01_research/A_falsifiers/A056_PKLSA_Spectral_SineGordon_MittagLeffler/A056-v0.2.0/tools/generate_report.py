from pathlib import Path
import argparse,json,csv
ROOT=Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.outputs import default_output_dir
p=argparse.ArgumentParser(); p.add_argument('--output',default=str(default_output_dir(ROOT))); a=p.parse_args(); out=Path(a.output)
summary=json.loads((out/'BLIND/summary.json').read_text()); ledger=json.loads((out/'BLIND/gate_ledger.json').read_text())
rows=list(csv.DictReader((out/'BLIND/case_results.csv').open(encoding='utf-8')))
tpl=(ROOT/'reports/A056_FALSIFIER_REPORT_TEMPLATE.tex').read_text(encoding='utf-8')
gates='\n'.join([f"{r['gate_id']} & {r['status']} \\\\" for r in ledger['records']])
cases='\n'.join([f"{r['opaque_id']} & {r.get('phase_best_model','--')} & {r.get('ringdown_best_model','--')} & {r.get('G4_numerical','--')} \\\\" for r in rows])
text=tpl.replace('{{CONCLUSION}}',summary['conclusion']).replace('{{GATE_ROWS}}',gates).replace('{{CASE_ROWS}}',cases)
(out/'BLIND/A056_FALSIFIER_REPORT.tex').write_text(text,encoding='utf-8'); print(out/'BLIND/A056_FALSIFIER_REPORT.tex')
