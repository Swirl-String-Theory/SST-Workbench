from __future__ import annotations
import argparse,csv,json,hashlib,re,shutil
from pathlib import Path
from .geometry import load_xyz,save_xyz,arclength_resample_closed,apply_qhp,metrics

EXTS={'.txt','.xyz','.dat','.coords'}
FORMAT='SST-QHP-SWEEP-1.1'


def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def _stem_without_final(p: Path) -> str:
    s=p.stem.strip()
    s=re.sub(r'(?i)(?:[_\-.]?final)$','',s)
    return s


def seed_identity(p):
    """Unique, human-auditable identity for one source seed.

    Examples:
      knot_6.3_final.txt   -> knot_6.3
      link_6.3.1_final.txt -> link_6.3.1
      torus_2.3_final.txt  -> torus_2.3
    """
    s=_stem_without_final(Path(p)).lower()
    s=re.sub(r'\s+','_',s)
    s=re.sub(r'[^a-z0-9._-]+','_',s).strip('_.-')
    return s or Path(p).stem.lower()


def topology_class_from_name(p):
    s=Path(p).stem.lower()
    m=re.search(r'(?<!\d)(\d+)[._-](\d+)(?!\d)',s)
    return f'{m.group(1)}.{m.group(2)}' if m else Path(p).parent.name


def seed_kind_from_name(p):
    s=seed_identity(p)
    m=re.match(r'([a-z]+)',s)
    return m.group(1) if m else 'seed'


def family_from_name(p):
    # Backward-compatible function name, but v0.1.1 semantics are deliberately
    # unique per source seed to prevent knots/links/tori with the same numeric
    # topology class from being merged into one QHP manifold.
    return seed_identity(p)


def discover(root):
    root=Path(root)
    out=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.suffix.lower() in EXTS:
            try:
                x=load_xyz(p)
                out.append((p,x))
            except Exception:
                pass
    return out


def token(v):
    if abs(v)<5e-15:return '0'
    sign='m' if v<0 else ''
    return sign+(f'{abs(v):.6g}'.replace('.','p').replace('+',''))


def path_token(s):
    return re.sub(r'[^A-Za-z0-9_-]+','p',str(s)).strip('_')


def axis_points(vals):
    vals=sorted(set(float(v) for v in vals))
    pts={(0.0,0.0,0.0)}
    for v in vals:
        pts.add((v,0,0));pts.add((0,v,0));pts.add((0,0,v))
    return sorted(pts)


def full_grid(vals):
    vals=sorted(set(float(v) for v in vals))
    return [(q,h,p) for q in vals for h in vals for p in vals]


def _safe_generated_output(out: Path) -> bool:
    if not out.exists(): return True
    if not any(out.iterdir()): return True
    marker=out/'QHP_SWEEP_SUMMARY.json'
    if not marker.exists(): return False
    try:
        data=json.loads(marker.read_text(encoding='utf-8'))
        return str(data.get('format','')).startswith('SST-QHP-SWEEP-')
    except Exception:
        return False


def _clean_output(out: Path):
    if out.exists() and any(out.iterdir()):
        if not _safe_generated_output(out):
            raise SystemExit(
                f'Refusing to clean non-generator directory: {out}\n'
                'Choose an empty output directory or remove/move its contents manually.'
            )
        shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)


def _matches_filter(sp: Path, filters: set[str]) -> bool:
    if not filters: return True
    ident=seed_identity(sp)
    topo=topology_class_from_name(sp)
    kind=seed_kind_from_name(sp)
    aliases={ident,topo,f'{kind}_{topo}'}
    return bool(aliases & filters)


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('dataset')
    ap.add_argument('--out',default=None)
    ap.add_argument('--config',default='config/basic.json')
    ap.add_argument('--families',default='')
    ap.add_argument('--clean-output',action='store_true',help='Safely replace a prior QHP generator output directory.')
    ns=ap.parse_args(argv)
    cfg=json.loads(Path(ns.config).read_text())
    src=Path(ns.dataset).resolve(); out=Path(ns.out).resolve() if ns.out else src.parent/'qhp'
    fam_filter={s.strip().lower() for s in ns.families.split(',') if s.strip()}
    seeds=discover(src)
    if fam_filter: seeds=[z for z in seeds if _matches_filter(z[0],fam_filter)]
    if not seeds: raise SystemExit(f'No parseable XYZ seed files found under {src}')

    # Unique identity is a hard invariant. A collision here would make two
    # different source geometries share one QHP manifold.
    ids=[seed_identity(z[0]) for z in seeds]
    dup_ids=sorted({x for x in ids if ids.count(x)>1})
    if dup_ids:
        raise SystemExit(f'Non-unique seed identities: {dup_ids}')

    if ns.clean_output:
        _clean_output(out)
    else:
        out.mkdir(parents=True,exist_ok=True)

    vals=cfg['amplitudes']; points=full_grid(vals) if cfg.get('full_grid') else axis_points(vals)
    n=int(cfg['resample_n'])
    rows=[]; seedrows=[]; written=set()
    for sp,x0 in seeds:
        fam=seed_identity(sp)
        topo=topology_class_from_name(sp)
        kind=seed_kind_from_name(sp)
        seed_hash=sha256(sp)
        x0=arclength_resample_closed(x0,n)
        m0=metrics(x0); base_sep=m0['min_nonlocal_vertex_distance']
        famdir=out/fam; famdir.mkdir(parents=True,exist_ok=True)
        seedrows.append({'family':fam,'topology_class':topo,'seed_kind':kind,'seed':str(sp),'seed_sha256':seed_hash,**m0})
        prefix=path_token(fam)
        for q,h,p in points:
            x,B=apply_qhp(x0,q,h,p); mm=metrics(x)
            sep_ratio=mm['min_nonlocal_vertex_distance']/max(base_sep,1e-30)
            geom_ok=sep_ratio>=float(cfg['min_separation_ratio']) and mm['ds_cv']<=float(cfg['max_ds_cv'])
            name=f'{prefix}_q{token(q)}_h{token(h)}_p{token(p)}.txt'
            fp=famdir/name
            rel=fp.relative_to(out).as_posix()
            if rel in written:
                raise SystemExit(f'Duplicate output path detected before write: {rel}')
            written.add(rel)
            save_xyz(fp,x)
            rows.append({
                'file':rel,'family':fam,'topology_class':topo,'seed_kind':kind,
                'q':q,'h':h,'p':p,'replicate':0,'seed_file':str(sp),
                'seed_sha256':seed_hash,'geometry_ok':str(bool(geom_ok)).lower(),
                'separation_ratio':sep_ratio,**mm,
            })
    fields=list(rows[0].keys())
    with open(out/'qhp_metadata.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    with open(out/'seed_manifest.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(seedrows[0].keys()));w.writeheader();w.writerows(seedrows)
    summary={
        'format':FORMAT,'source':str(src),'output':str(out),'n_seeds':len(seeds),
        'n_unique_families':len(set(r['family'] for r in rows)),
        'n_points_per_seed':len(points),'n_geometries':len(rows),'n_unique_output_files':len(written),
        'config':cfg,'n_geometry_ok':sum(r['geometry_ok']=='true' for r in rows),
        'identity_policy':'family is unique source seed identity; topology_class is descriptive only',
    }
    (out/'QHP_SWEEP_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
