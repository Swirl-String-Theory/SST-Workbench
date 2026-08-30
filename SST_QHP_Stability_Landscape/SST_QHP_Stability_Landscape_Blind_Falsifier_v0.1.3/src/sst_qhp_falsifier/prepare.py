from pathlib import Path
import hashlib,json,csv,numpy as np
from .geometry import load_metadata,numeric_xyz,resample_closed,normalize_scale,best_cyclic_align,radius_gyration


def _hash(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _center(x):
    x=np.asarray(x,float)
    return x-x.mean(axis=0)


def _scale_mode(cfg):
    mode=str(cfg.get('scale_normalization_mode','')).strip().lower()
    if not mode:
        # v0.1.3 compatibility rule: the historical normalize_geometry_scale=true
        # now means one common family-anchor scale, not independent candidate scales.
        mode='family_anchor' if bool(cfg.get('normalize_geometry_scale',True)) else 'none'
    aliases={'anchor':'family_anchor','family':'family_anchor','legacy':'per_candidate'}
    mode=aliases.get(mode,mode)
    if mode not in {'family_anchor','per_candidate','none'}:
        raise ValueError(f'unsupported scale_normalization_mode={mode!r}')
    return mode


def prepare(root,outdir,cfg,metadata=None):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    rows,meta_source,meta_stats=load_metadata(root,metadata,return_stats=True)
    n=int(cfg['n_points']); grouped={}
    for r in rows:
        grouped.setdefault((r['family'],r.get('replicate','0')),[]).append(r)

    blind=[]; reveal=[]; arrays={}; family_scales=[]
    mode=_scale_mode(cfg)

    for (family,replicate),rr in sorted(grouped.items()):
        # Prefer an explicit origin if present. Otherwise use coordinate median-nearest.
        c=np.array([[x['q'],x['h'],x['p']] for x in rr],float)
        zero=np.where(np.linalg.norm(c,axis=1)<=1e-14)[0]
        if len(zero):
            anchor_idx=int(zero[0])
        else:
            med=np.median(c,axis=0)
            anchor_idx=int(np.argmin(np.sum((c-med)**2,axis=1)))

        anchor0=resample_closed(numeric_xyz(rr[anchor_idx]['file']),n)
        anchor_raw_rg=radius_gyration(anchor0)
        if not np.isfinite(anchor_raw_rg) or anchor_raw_rg<=0:
            raise RuntimeError(f'{family}: invalid anchor radius of gyration')
        if mode=='family_anchor':
            anchor=_center(anchor0)/anchor_raw_rg
        elif mode=='per_candidate':
            anchor,_=normalize_scale(anchor0)
        else:
            anchor=_center(anchor0)
        family_scales.append(anchor_raw_rg)

        fb='F_'+_hash(family+'|'+str(replicate)+'|'+str(cfg.get('blind_seed',20260827)))
        for r in rr:
            x0=resample_closed(numeric_xyz(r['file']),n)
            raw_rg=radius_gyration(x0)
            if mode=='family_anchor':
                x=_center(x0)/anchor_raw_rg
                scale_used=anchor_raw_rg
            elif mode=='per_candidate':
                x,scale_used=normalize_scale(x0)
            else:
                x=_center(x0)
                scale_used=1.0

            xa,al=best_cyclic_align(x,anchor,bool(cfg.get('allow_reverse_alignment',False)))
            cid='C_'+_hash(str(Path(r['file']).resolve())+'|'+str(cfg.get('blind_seed',20260827)))
            arrays[cid]=xa
            blind.append({
                'candidate_id':cid,
                'family_blind':fb,
                'q':r['q'],'h':r['h'],'p':r['p'],'replicate':r.get('replicate','0'),
                'candidate_raw_rg':raw_rg,
                'family_anchor_raw_rg':anchor_raw_rg,
                'scale_divisor':scale_used,
                'scale_normalization_mode':mode,
                'alignment_mse':al['mse'],'alignment_shift':al['shift'],'alignment_reversed':al['reversed'],
            })
            reveal.append({
                'candidate_id':cid,'family_blind':fb,'family':family,'file':r['file'],
                'q':r['q'],'h':r['h'],'p':r['p'],'replicate':r.get('replicate','0')
            })

    np.savez_compressed(out/'blind_geometries.npz',**arrays)
    fields=list(blind[0].keys()) if blind else []
    with (out/'blind_catalog.csv').open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=fields); wr.writeheader(); wr.writerows(blind)
    (out/'reveal_key.json').write_text(json.dumps({'rows':reveal,'metadata_source':meta_source},indent=2),encoding='utf-8')
    summary={
        'format':'SST-QHP-PREPARE-1.3',
        'n_candidates':len(blind),
        'n_families':len(grouped),
        'n_points':n,
        'metadata_source':meta_source,
        'metadata_rows_total':meta_stats.get('metadata_rows_total',len(blind)),
        'geometry_rejected_excluded':meta_stats.get('geometry_rejected_excluded',0),
        'duplicate_coordinate_keys':meta_stats.get('duplicate_coordinate_keys',0),
        'duplicate_file_paths':meta_stats.get('duplicate_file_paths',0),
        'scale_normalization_mode':mode,
        'scale_policy':'one common family-anchor Rg preserves relative Q breathing' if mode=='family_anchor' else mode,
        'identities_hidden_from_worker':True,
    }
    (out/'prepare_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary
