#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description='Summarize one campaign output folder.')
    ap.add_argument('campaign_dir')
    args=ap.parse_args()
    d=Path(args.campaign_dir)
    results=json.loads((d/'all_results.json').read_text(encoding='utf-8'))
    c=Counter((r.get('gate_id'),r.get('verdict')) for r in results)
    print(f'Campaign: {d}')
    print(f'Results: {len(results)}')
    for (g,v),n in sorted(c.items()): print(f'{g:34s} {v:14s} {n:4d}')
    print('\nResearch/model FAILs:')
    for r in results:
        if r.get('verdict')=='FAIL' and r.get('tier') in {'MODEL_CONDITIONAL','PRIMARY_RESEARCH_HYPOTHESIS','PRIMARY_STATIC_FIELD'}:
            print(f"- {r.get('item_id')}: {r.get('gate_id')} — {r.get('hypothesis')}")
    return 0
if __name__=='__main__': raise SystemExit(main())
