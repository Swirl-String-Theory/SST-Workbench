#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from sst_pf_binary_falsifier.core import write_json, write_csv
from sst_pf_binary_falsifier.ideal_db import (
    DEFAULT_IDEAL_KNOTS, DEFAULT_IDEAL_LINKS, audit_record, catalog_summary,
    list_knot_ids, list_link_ids, load_knot_record, load_link_record,
)

def ids(s): return [x.strip() for x in s.split(',') if x.strip()]

def main()->int:
    ap=argparse.ArgumentParser(description='Parse/audit Brian Gilbert Ideal.txt and IdealLinks.txt Fourier databases.')
    ap.add_argument('--knot-db',default=str(DEFAULT_IDEAL_KNOTS)); ap.add_argument('--link-db',default=str(DEFAULT_IDEAL_LINKS))
    ap.add_argument('--knot-ids',default='3:1:1'); ap.add_argument('--link-ids',default='L2a1')
    ap.add_argument('--all-knots',action='store_true'); ap.add_argument('--all-links',action='store_true')
    ap.add_argument('--samples',type=int,default=None,help='Override source sampling; default reproduces source convention.')
    ap.add_argument('--scale-mode',choices=['native','sst_core'],default='native')
    ap.add_argument('--no-linking',action='store_true'); ap.add_argument('--out-dir',default='audit_out/ideal_database')
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    summary=catalog_summary(a.knot_db,a.link_db); write_json(out/'catalog_summary.json',summary)
    k_ids=list_knot_ids(a.knot_db) if a.all_knots else ids(a.knot_ids)
    l_ids=list_link_ids(a.link_db) if a.all_links else ids(a.link_ids)
    audits=[]
    for kid in k_ids:
        audits.append(audit_record(load_knot_record(kid,a.knot_db),samples=a.samples,scale_mode=a.scale_mode,linking=False))
    for lid in l_ids:
        audits.append(audit_record(load_link_record(lid,a.link_db),samples=a.samples,scale_mode=a.scale_mode,linking=not a.no_linking))
    write_json(out/'geometry_audits.json',audits)
    rows=[]
    for r in audits:
        for c in r['curves']:
            rows.append({'kind':r['kind'],'id':r['id'],'conway':r['conway'],'component':c['index'],'samples':c['samples'],
                         'target_length':c['target_length'],'sampled_length':c['sampled_length'],'relative_length_error':c['relative_length_error'],
                         'coeff_count':c['coeff_count'],'max_harmonic':c['max_harmonic']})
    write_csv(out/'geometry_lengths.csv',rows)
    maxerr=max((abs(x['relative_length_error']) for x in rows),default=0.0)
    result={'catalog':summary,'records_audited':len(audits),'curves_audited':len(rows),'max_abs_relative_length_error':maxerr,
            'scale_mode':a.scale_mode,'ok':bool(maxerr<5e-5)}
    write_json(out/'ideal_database_summary.json',result); print(json.dumps(result,indent=2)); return 0 if result['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
