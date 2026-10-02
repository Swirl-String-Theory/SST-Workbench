from __future__ import annotations
import argparse
from .common import load_json

def main():
 p=argparse.ArgumentParser();p.add_argument('json');p.add_argument('--out',required=True);p.add_argument('--title',default='SST Wien–Planck report');a=p.parse_args();d=load_json(a.json);lines=[f'# {a.title}','',f'Format: `{d.get("format")}`','']
 if 'gates' in d:
  lines+=['## Gates','']+[f'- **{k}**: `{v}`' for k,v in d['gates'].items()]+['']
 if 'summary' in d: lines+=['## Summary','', '```json', __import__('json').dumps(d['summary'],indent=2), '```','']
 if 'target_comparison' in d: lines+=['## Target comparison','', '```json',__import__('json').dumps(d['target_comparison'],indent=2),'```','']
 if 'interpretation' in d: lines+=['## Interpretation','',d['interpretation'],'']
 open(a.out,'w',encoding='utf-8').write('\n'.join(lines))
if __name__=='__main__':main()
