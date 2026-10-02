from pathlib import Path
import csv, re, numpy as np
EXTS={'.txt','.xyz','.csv','.dat','.pts'}

def numeric_xyz(path):
    pts=[]
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip().replace(',',' ')
        if not s or s.startswith(('#','//',';')): continue
        vals=[]
        for tok in s.split():
            try: vals.append(float(tok))
            except ValueError: pass
        if len(vals)>=3 and np.isfinite(vals[:3]).all(): pts.append(vals[:3])
    a=np.asarray(pts,float)
    if len(a)>2:
        sc=max(1.0,float(np.ptp(a,axis=0).max()))
        if np.linalg.norm(a[0]-a[-1])<1e-10*sc: a=a[:-1]
    if len(a)<16: raise ValueError(f'{path}: fewer than 16 XYZ points')
    return a

def arclength(x):
    y=np.vstack([x,x[0]]); ds=np.linalg.norm(np.diff(y,axis=0),axis=1); return np.r_[0.,np.cumsum(ds)],ds

def resample_closed(x,n):
    s,ds=arclength(x); y=np.vstack([x,x[0]]); tgt=np.linspace(0,s[-1],int(n),endpoint=False); out=np.empty((int(n),3))
    for d in range(3): out[:,d]=np.interp(tgt,s,y[:,d])
    return out

def centroid(x): return np.mean(np.asarray(x,float),axis=0)
def radius_gyration(x):
    y=np.asarray(x,float)-centroid(x); return float(np.sqrt(np.mean(np.sum(y*y,axis=1))))

def normalize_scale(x):
    y=np.asarray(x,float)-centroid(x); rg=radius_gyration(y)
    if rg<=0: raise ValueError('degenerate geometry')
    return y/rg,rg

def tangents(x):
    t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0); n=np.linalg.norm(t,axis=1); n[n<1e-15]=1.; return t/n[:,None]

def normal_component(v,x):
    t=tangents(x); return v-(v*t).sum(1)[:,None]*t

def kabsch_align(moving,reference):
    a=np.asarray(moving,float)-centroid(moving); b=np.asarray(reference,float)-centroid(reference)
    H=a.T@b; U,S,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    return a@R.T

def best_cyclic_align(moving,reference,allow_reverse=False):
    m=np.asarray(moving,float); r=np.asarray(reference,float); n=len(r); best=None
    candidates=[m]
    if allow_reverse: candidates.append(m[::-1].copy())
    # coarse FFT-like exhaustive on N<=256; alignment occurs only during prepare.
    for cand in candidates:
        for shift in range(n):
            a=np.roll(cand,shift,axis=0); aa=kabsch_align(a,r); err=float(np.mean(np.sum((aa-r)**2,axis=1)))
            if best is None or err<best[0]: best=(err,aa,shift,cand is not m)
    return best[1], {'mse':best[0],'shift':best[2],'reversed':best[3]}

def _decode_num(s):
    s=s.strip().lower().replace('m','-').replace('p','.')
    try: return float(s)
    except: return None

def parse_qhp_from_name(name):
    low=Path(name).stem.lower()
    out={}
    # q_-0p5 / q-0.5 / q=...
    for key in ('q','h','p'):
        # Do not consume '-' as a key/value separator: in tokens such as h-0p2 it is the sign.
        # Negative filename-safe 'm' is also accepted, e.g. h_m0p2 or hm0p2.
        num=r'(?:(?:[+-]|m)?(?:\d+(?:\.\d*)?|\d+p\d+))'
        pats=[rf'(?:^|[_-]){key}(?:=|_)?({num})(?=$|[_-])', rf'{key}=({num})']
        for pat in pats:
            m=re.search(pat,low)
            if m:
                v=_decode_num(m.group(1));
                if v is not None: out[key]=v; break
    return out

def load_metadata(root,metadata_path=None,return_stats=False):
    root=Path(root); mp=Path(metadata_path) if metadata_path else root/'qhp_metadata.csv'
    rows=[]
    stats={'metadata_rows_total':0,'geometry_rejected_excluded':0,'duplicate_coordinate_keys':0,'duplicate_file_paths':0}
    if mp.exists():
        raw=[]
        with mp.open(newline='',encoding='utf-8-sig') as f:
            raw=list(csv.DictReader(f))
        stats['metadata_rows_total']=len(raw)
        # File-path duplication is never valid for one concrete geometry catalog.
        resolved=[]
        for r in raw:
            fp=(root/r['file']).resolve() if not Path(r['file']).is_absolute() else Path(r['file']).resolve()
            resolved.append(str(fp))
        from collections import Counter
        cfiles=Counter(resolved)
        dup_files=sorted(k for k,v in cfiles.items() if v>1)
        stats['duplicate_file_paths']=len(dup_files)
        if dup_files:
            raise RuntimeError(
                'Metadata integrity failure: duplicate geometry file paths detected. '
                f'First duplicates: {dup_files[:5]}'
            )
        # One coordinate per family/replicate manifold node. Duplicate nodes make finite
        # differences ambiguous even if files differ.
        keys=[]
        for r in raw:
            keys.append((r.get('family','default') or 'default', r.get('replicate','0') or '0',
                         float(r['q']),float(r['h']),float(r['p'])))
        ckeys=Counter(keys)
        dup_keys=sorted(k for k,v in ckeys.items() if v>1)
        stats['duplicate_coordinate_keys']=len(dup_keys)
        if dup_keys:
            raise RuntimeError(
                'Metadata integrity failure: duplicate (family, replicate, q, h, p) nodes detected. '
                f'First duplicates: {dup_keys[:5]}'
            )
        for r,fp in zip(raw,resolved):
            gok=str(r.get('geometry_ok','')).strip().lower()
            if gok in {'false','0','no','reject','rejected'}:
                stats['geometry_rejected_excluded']+=1
                continue
            rows.append({'file':fp,'family':r.get('family','default') or 'default','q':float(r['q']),'h':float(r['h']),'p':float(r['p']),'replicate':r.get('replicate','0') or '0'})
        if not rows:
            raise RuntimeError('No usable QHP geometries remain after metadata integrity/geometry_ok filtering.')
        result=(rows,str(mp),stats)
        return result if return_stats else result[:2]
    # filename inference only when all q,h,p tokens are present
    for pth in sorted(root.rglob('*')):
        if not pth.is_file() or pth.suffix.lower() not in EXTS: continue
        vals=parse_qhp_from_name(pth.name)
        if all(k in vals for k in ('q','h','p')):
            try: numeric_xyz(pth)
            except: continue
            rows.append({'file':str(pth.resolve()),'family':pth.parent.name,'q':vals['q'],'h':vals['h'],'p':vals['p'],'replicate':'0'})
    if rows:
        stats['metadata_rows_total']=len(rows)
        result=(rows,'filename-inference',stats)
        return result if return_stats else result[:2]
    raise RuntimeError('No qhp_metadata.csv and no files with parseable q/h/p filename tokens. Run: python -m sst_qhp_falsifier.cli metadata-template <QHP_ROOT>')

def write_metadata_template(root,out_path=None):
    root=Path(root); out=Path(out_path) if out_path else root/'qhp_metadata_template.csv'; rec=[]
    for pth in sorted(root.rglob('*')):
        if pth.is_file() and pth.suffix.lower() in EXTS:
            try: numeric_xyz(pth)
            except: continue
            vals=parse_qhp_from_name(pth.name)
            rec.append({'file':str(pth.relative_to(root)),'family':pth.parent.name,'q':vals.get('q',''),'h':vals.get('h',''),'p':vals.get('p',''),'replicate':'0'})
    with out.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate']); wr.writeheader(); wr.writerows(rec)
    return out,len(rec)

def bootstrap_metadata(root):
    """Return a usable qhp_metadata.csv path or create an incomplete template.

    Policy: never invent Q/H/P from row order. Existing metadata wins. Otherwise
    automatic promotion is allowed only when every parseable XYZ geometry has
    explicit q,h,p filename tokens. If not, write qhp_metadata_template.csv and
    report that manual metadata is required before physics may run.
    """
    root=Path(root)
    mp=root/'qhp_metadata.csv'
    if mp.exists():
        rows,_=load_metadata(root,mp)
        return {'ready':True,'source':'qhp_metadata.csv','metadata':str(mp),'n_rows':len(rows),'template':None}
    rec=[]
    complete=True
    for pth in sorted(root.rglob('*')):
        if not pth.is_file() or pth.suffix.lower() not in EXTS:
            continue
        try:
            numeric_xyz(pth)
        except Exception:
            continue
        vals=parse_qhp_from_name(pth.name)
        row={'file':str(pth.relative_to(root)),'family':pth.parent.name,
             'q':vals.get('q',''),'h':vals.get('h',''),'p':vals.get('p',''),'replicate':'0'}
        rec.append(row)
        complete = complete and all(k in vals for k in ('q','h','p'))
    if not rec:
        raise RuntimeError(f'No parseable XYZ geometries found under {root}')
    if complete:
        with mp.open('w',newline='',encoding='utf-8') as f:
            wr=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate'])
            wr.writeheader(); wr.writerows(rec)
        return {'ready':True,'source':'filename-inference-promoted','metadata':str(mp),'n_rows':len(rec),'template':None}
    tp=root/'qhp_metadata_template.csv'
    with tp.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate'])
        wr.writeheader(); wr.writerows(rec)
    n_complete=sum(bool(str(r['q']).strip()) and bool(str(r['h']).strip()) and bool(str(r['p']).strip()) for r in rec)
    return {'ready':False,'source':'template-required','metadata':None,'n_rows':len(rec),
            'n_complete_rows':n_complete,'template':str(tp)}

