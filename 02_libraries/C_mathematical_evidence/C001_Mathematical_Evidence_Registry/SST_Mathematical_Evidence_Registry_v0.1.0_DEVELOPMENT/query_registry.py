#!/usr/bin/env python3
"""CLI search across curated claims (and optionally raw AI-summary formula candidates)."""
import argparse,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent/'results'
parser=argparse.ArgumentParser(description='Search SST evidence claims. Raw candidates remain UNREVIEWED.')
parser.add_argument('query',nargs='?',default='',help='Regex or plain substring')
parser.add_argument('--source',choices=['curated','raw','both'],default='curated')
parser.add_argument('--status',help='Filter evidence_status/scientific_status exactly')
parser.add_argument('--paper',help='Exact paper code, e.g., SST-29 or VAM-05')
parser.add_argument('--json',action='store_true',help='Print JSON lines, full record')
args=parser.parse_args()
re_pat=re.compile(args.query,re.IGNORECASE)
rows=[]
for fn in (['curated_claims.jsonl'] if args.source=='curated' else ['raw_formula_candidates.jsonl'] if args.source=='raw' else ['curated_claims.jsonl','raw_formula_candidates.jsonl']):
 with (BASE/fn).open(encoding='utf-8') as f:
  for line in f:
   obj=json.loads(line)
   if args.paper and args.paper not in ([obj.get('paper_id')] if 'paper_id' in obj else obj.get('paper_ids',[])):continue
   if args.status and obj.get('evidence_status',obj.get('scientific_status'))!=args.status:continue
   if re_pat.search(' '.join(str(x) for x in obj.values())): rows.append(obj)
for x in rows:
 if args.json: print(json.dumps(x,ensure_ascii=False))
 else:
  print(f"{x.get('claim_id',x.get('id')):14} {x.get('paper_id',','.join(x.get('paper_ids',[]))):12} {x.get('evidence_status',x.get('scientific_status')):38} {x.get('source_locator','line '+str(x.get('source_line_start')))}")
print(f'{len(rows)} result(s)',file=__import__('sys').stderr)
