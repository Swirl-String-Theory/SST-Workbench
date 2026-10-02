from pathlib import Path
import csv,json

def reveal(prepared,analysis,outdir):
    prep=Path(prepared); ana=Path(analysis); out=Path(outdir); out.mkdir(parents=True,exist_ok=True); key=json.loads((prep/'reveal_key.json').read_text(encoding='utf-8')); mp={r['candidate_id']:r for r in key['rows']}; fam={r['family_blind']:r['family'] for r in key['rows']}
    produced=[]
    for name in ['blind_zero_crossings.csv','blind_fixed_point_candidates.csv','blind_affine_fixed_point_candidates.csv']:
        src=ana/name
        if not src.exists(): continue
        with src.open(newline='',encoding='utf-8') as f: rr=list(csv.DictReader(f))
        for r in rr:
            if 'candidate_id' in r and r['candidate_id'] in mp: r['family']=mp[r['candidate_id']]['family']; r['file']=mp[r['candidate_id']]['file']
            elif 'family_blind' in r: r['family']=fam.get(r['family_blind'],'UNKNOWN')
        dest=out/name.replace('blind_','revealed_'); fields=sorted(set().union(*(r.keys() for r in rr))) if rr else ['family'];
        with dest.open('w',newline='',encoding='utf-8') as f: wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(rr)
        produced.append(dest.name)
    summary={'format':'SST-QHP-REVEAL-1','produced':produced,'metadata_source':key.get('metadata_source')}; (out/'reveal_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); return summary
