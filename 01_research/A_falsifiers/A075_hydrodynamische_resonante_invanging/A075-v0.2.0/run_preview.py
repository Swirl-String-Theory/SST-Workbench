"""Scientific preflight without claiming that the locked framework was run."""
from pathlib import Path
import argparse,json
from experiment.science import run_suite
p=argparse.ArgumentParser()
p.add_argument('--profile',choices=['PREVIEW','BASIC','FULL'],default='PREVIEW')
p.add_argument('--output-root',type=Path,default=None)
a=p.parse_args()
r=run_suite(Path(__file__).resolve().parent,a.profile,a.output_root)
print(json.dumps({'physical_answer':r['physical_answer'],'cases':{k:v['status'] for k,v in r['cases'].items()},'gates':r['gates'],'elapsed_seconds':r['elapsed_seconds']},indent=2))
