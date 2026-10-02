from pathlib import Path
import hashlib,json,csv,numpy as np
from .geometry import load_metadata,numeric_xyz,resample_closed,normalize_scale,best_cyclic_align

def _hash(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def prepare(root,outdir,cfg,metadata=None):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); rows,meta_source,meta_stats=load_metadata(root,metadata,return_stats=True)
    n=int(cfg['n_points']); grouped={}
    for r in rows: grouped.setdefault(r['family'],[]).append(r)
    blind=[]; reveal=[]; arrays={}
    for family,rr in sorted(grouped.items()):
        # deterministic anchor: coordinate median-nearest, not filename.
        c=np.array([[x['q'],x['h'],x['p']] for x in rr],float); med=np.median(c,axis=0); anchor_idx=int(np.argmin(np.sum((c-med)**2,axis=1)))
        anchor0=resample_closed(numeric_xyz(rr[anchor_idx]['file']),n); anchor,anchor_scale=normalize_scale(anchor0) if bool(cfg.get('normalize_geometry_scale',True)) else (anchor0-anchor0.mean(0),1.0)
        fb='F_'+_hash(family+'|'+str(cfg.get('blind_seed',20260827)))
        for r in rr:
            xraw=numeric_xyz(r['file']); x=resample_closed(xraw,n); x,scale=normalize_scale(x) if bool(cfg.get('normalize_geometry_scale',True)) else (x-x.mean(0),1.0); xa,al=best_cyclic_align(x,anchor,bool(cfg.get('allow_reverse_alignment',False)))
            cid='C_'+_hash(str(Path(r['file']).resolve())+'|'+str(cfg.get('blind_seed',20260827)))
            arrays[cid]=xa
            blind.append({'candidate_id':cid,'family_blind':fb,'q':r['q'],'h':r['h'],'p':r['p'],'replicate':r.get('replicate','0'),'scale_removed_rg':scale,'alignment_mse':al['mse'],'alignment_shift':al['shift'],'alignment_reversed':al['reversed']})
            reveal.append({'candidate_id':cid,'family_blind':fb,'family':family,'file':r['file'],'q':r['q'],'h':r['h'],'p':r['p'],'replicate':r.get('replicate','0')})
    np.savez_compressed(out/'blind_geometries.npz',**arrays)
    fields=list(blind[0].keys()) if blind else []
    with (out/'blind_catalog.csv').open('w',newline='',encoding='utf-8') as f: wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(blind)
    (out/'reveal_key.json').write_text(json.dumps({'rows':reveal,'metadata_source':meta_source},indent=2),encoding='utf-8')
    summary={'format':'SST-QHP-PREPARE-1.2','n_candidates':len(blind),'n_families':len(grouped),'n_points':n,'metadata_source':meta_source,'metadata_rows_total':meta_stats.get('metadata_rows_total',len(blind)),'geometry_rejected_excluded':meta_stats.get('geometry_rejected_excluded',0),'duplicate_coordinate_keys':meta_stats.get('duplicate_coordinate_keys',0),'duplicate_file_paths':meta_stats.get('duplicate_file_paths',0),'identities_hidden_from_worker':True}
    (out/'prepare_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); return summary
