#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from sst_link_suite.models import jsonable
from sst_link_suite.parser import parse_ideal_links, select_links
from sst_link_suite.spectral import spectral_tail_audit


def main()->int:
    ap=argparse.ArgumentParser(description='v0.3.5 analytic-Fourier spectral-tail / source-precision audit')
    ap.add_argument('--input',default=str(ROOT/'data'/'idealLinks.txt'))
    ap.add_argument('--output',default=str(ROOT/'outputs_spectral'))
    ap.add_argument('--config',default=str(ROOT/'configs'/'spectral_audit.json'))
    ap.add_argument('--ids',nargs='*',default=['L2a1','L4a1','L6a4','L6n1','L7n2'])
    ap.add_argument('--all-database',action='store_true')
    args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text(encoding='utf-8'))
    links=select_links(parse_ideal_links(args.input),args.ids,args.all_database)
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True); per=out/'per_link'; per.mkdir(exist_ok=True)
    results=[]
    for i,link in enumerate(links,1):
        print(f'[{i}/{len(links)}] spectral {link.link_id}',flush=True)
        result=spectral_tail_audit(link,cfg)
        (per/f'{link.link_id}.json').write_text(json.dumps(jsonable(result),indent=2),encoding='utf-8')
        results.append(result)
    rows=[]
    cutoff_rows=[]
    for result in results:
        rows.append({
            'link_id':result['link_id'],
            'source_active_mode_max':result['source_active_mode_max'],
            'strict_nyquist_min_sample_n':result['strict_nyquist_min_sample_n'],
            'recommended_nonlinear_geometry_sample_n':result['recommended_nonlinear_geometry_sample_n'],
            'reference_cutoff_mode_used':result['reference_cutoff_mode_used'],
            'full_vs_reference_bending_relative_difference':result['full_vs_reference_bending_relative_difference'],
            'aggregate_d2_power_tail_fraction_above_reference':result['aggregate_d2_power_tail_fraction_above_reference'],
            'aggregate_d2_power_precision_suspect_fraction':result['aggregate_d2_power_precision_suspect_fraction'],
            'spectral_tail_sensitive':result['spectral_tail_sensitive'],
            'source_precision_risk':result['source_precision_risk'],
            'spectral_tail_contaminated_risk':result['spectral_tail_contaminated_risk'],
        })
        for row in result['cutoff_rows']:
            cutoff_rows.append({'link_id':result['link_id'],**row})
    pd.DataFrame(rows).to_csv(out/'spectral_summary.csv',index=False)
    pd.DataFrame(cutoff_rows).to_csv(out/'spectral_cutoff_ladder.csv',index=False)
    (out/'spectral_metadata.json').write_text(json.dumps({'config':cfg,'ids':[r['link_id'] for r in results]},indent=2),encoding='utf-8')
    return 0

if __name__=='__main__': raise SystemExit(main())
