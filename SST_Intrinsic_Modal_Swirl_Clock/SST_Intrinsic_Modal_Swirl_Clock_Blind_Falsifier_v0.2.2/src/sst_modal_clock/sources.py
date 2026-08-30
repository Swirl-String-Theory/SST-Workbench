from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import gzip, hashlib, re
import numpy as np

_FLOAT=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'

@dataclass
class SourceGeometry:
    topology_id: str
    provenance: str
    source_path: str
    source_name: str
    source_record_id: str
    components: list[np.ndarray]
    metadata: dict


def _read_text_or_gzip(path: Path) -> str:
    p=Path(path)
    if p.suffix.lower()=='.gz':
        with gzip.open(p,'rt',encoding='utf-8',errors='ignore') as f: return f.read()
    return p.read_text(encoding='utf-8',errors='ignore')


def _vec(s):
    v=[float(x) for x in re.findall(_FLOAT,str(s))]
    if len(v)<3: return np.zeros(3,float)
    return np.asarray(v[:3],float)


def eval_fourier(coeff: dict[int,tuple[np.ndarray,np.ndarray]], n_points: int) -> np.ndarray:
    n=max(16,int(n_points)); t=np.linspace(0,2*np.pi,n,endpoint=False); x=np.zeros((n,3),float)
    for k,(A,B) in coeff.items():
        if int(k)==0: x += .5*np.asarray(A,float)[None,:]
        else: x += np.cos(int(k)*t)[:,None]*np.asarray(A,float)[None,:] + np.sin(int(k)*t)[:,None]*np.asarray(B,float)[None,:]
    if not np.isfinite(x).all() or np.ptp(x,axis=0).max()<1e-12: raise ValueError('degenerate Fourier reconstruction')
    return x


def _canonical_from_fseries_path(path: Path) -> str|None:
    s=(path.parent.name+' '+path.stem).lower()
    m=re.search(r'(?:knot[._-]?)?t\s*([2-9]\d*)[._](\d+)',s)
    if m: return f'T{int(m.group(1))}.{int(m.group(2))}'
    m=re.search(r'(?:knot[._-]?)?(\d+)[_.](\d+)',s)
    if m: return f'K{int(m.group(1))}.{int(m.group(2))}'
    m=re.search(r'knot[_\.-]?(\d+)\.(\d+)',s)
    if m: return f'K{int(m.group(1))}.{int(m.group(2))}'
    return None


def _canonical_relaxed(path: Path) -> str|None:
    s=path.stem.lower()
    m=re.search(r'^knot[_\.-](\d+)[\._](\d+)',s)
    if m: return f'K{int(m.group(1))}.{int(m.group(2))}'
    m=re.search(r'^link[_\.-](\d+)[\._](\d+)[\._](\d+)',s)
    if m: return f'L{int(m.group(1))}.{int(m.group(2))}.{int(m.group(3))}'
    m=re.search(r'^torus[_\.-]?(\d+)[\._](\d+)',s)
    if m: return f'T{int(m.group(1))}.{int(m.group(2))}'
    return None


def canonical_ideal_id(raw_id: str, has_strings: bool=False) -> str:
    rid=str(raw_id).strip()
    # Gilbert AB IDs: crossing:string-count:identifier. 5:1:2 == knot 5_2.
    m=re.fullmatch(r'(\d+)\s*:\s*(\d+)\s*:\s*(\d+)',rid)
    if m:
        c,nstr,idx=map(int,m.groups())
        return f'K{c}.{idx}' if nstr==1 and not has_strings else f'L{c}.{nstr}.{idx}'
    # Hoste-Thistlethwaite forms. Link databases may already prefix L.
    if rid.upper().startswith('L'): return rid.upper().replace('_','.')
    if re.fullmatch(r'11[an]\d+',rid,re.I): return 'K'+rid.lower()
    return ('L' if has_strings else 'K')+rid.replace(':','.').replace('_','.')


def parse_fseries_file(path: Path, n_points: int) -> list[SourceGeometry]:
    """Fremlin six-column format: ax bx ay by az bz per harmonic j=1..N.

    A 3-column numeric line at the start is accepted as A0. Comment/blank lines
    split blocks; multiple nonempty blocks are retained as separate seed variants.
    """
    text=Path(path).read_text(encoding='utf-8',errors='ignore')
    blocks=[]; cur=[]; headers=[]; hdr=[]
    def flush():
        nonlocal cur,hdr
        if cur: blocks.append((list(hdr),list(cur)))
        cur=[]; hdr=[]
    for line in text.splitlines():
        s=line.strip()
        if not s:
            if cur: flush()
            continue
        if s.startswith(('%','#','//',';')):
            hdr.append(s)
            continue
        nums=[]
        for tok in re.split(r'[\s,]+',s):
            try: nums.append(float(tok))
            except ValueError: pass
        if len(nums) in (3,6): cur.append(nums)
    if cur: flush()
    topo=_canonical_from_fseries_path(Path(path))
    if topo is None: return []
    out=[]
    for bi,(head,rows) in enumerate(blocks):
        coeff={}; harmonic=1
        for row in rows:
            if len(row)==3 and harmonic==1 and 0 not in coeff:
                coeff[0]=(np.asarray(row,float),np.zeros(3,float)); continue
            if len(row)<6: continue
            coeff[harmonic]=(np.asarray([row[0],row[2],row[4]],float),np.asarray([row[1],row[3],row[5]],float)); harmonic+=1
        if not coeff or not any(k>0 for k in coeff): continue
        try: x=eval_fourier(coeff,n_points)
        except Exception: continue
        rid=f'{Path(path).name}#block{bi}'
        out.append(SourceGeometry(topo,'fseries',str(path),Path(path).name,rid,[x],{'header':' | '.join(head[:4]),'n_harmonics':max(coeff)}))
    return out


def _parse_coeff_body(body: str) -> dict[int,tuple[np.ndarray,np.ndarray]]:
    coeff={}
    # XML-ish Gilbert representation; omitted zero coefficients are naturally zero.
    for m in re.finditer(r'<\s*Coeff\b([^>]*)/?>',body,re.I|re.S):
        attrs=m.group(1)
        im=re.search(r'\bI\s*=\s*["\']([^"\']+)',attrs,re.I); am=re.search(r'\bA\s*=\s*["\']([^"\']+)',attrs,re.I); bm=re.search(r'\bB\s*=\s*["\']([^"\']+)',attrs,re.I)
        if not im: continue
        i=int(float(im.group(1))); A=_vec(am.group(1)) if am else np.zeros(3); B=_vec(bm.group(1)) if bm else np.zeros(3); coeff[i]=(A,B)
    return coeff


def _ideal_records_xml(text: str, provenance: str, source_path: Path, n_points: int) -> list[SourceGeometry]:
    out=[]
    # AB / HT are used in the Gilbert files. Generic LINK is tolerated for mirrors/conversions.
    pat=re.compile(r'<\s*(AB|HT|LINK)\b([^>]*)>(.*?)</\s*\1\s*>',re.I|re.S)
    for m in pat.finditer(text):
        tag,attrs,body=m.group(1),m.group(2),m.group(3)
        im=re.search(r'\bId\s*=\s*["\']([^"\']+)',attrs,re.I)
        if not im: continue
        rid=im.group(1).strip(); string_blocks=list(re.finditer(r'<\s*STRING\b([^>]*)>(.*?)</\s*STRING\s*>',body,re.I|re.S)); comps=[]
        if string_blocks:
            for sm in string_blocks:
                co=_parse_coeff_body(sm.group(2))
                if co:
                    try: comps.append(eval_fourier(co,n_points))
                    except Exception: pass
        else:
            co=_parse_coeff_body(body)
            if co:
                try: comps=[eval_fourier(co,n_points)]
                except Exception: comps=[]
        if not comps: continue
        topo=canonical_ideal_id(rid,has_strings=len(comps)>1)
        out.append(SourceGeometry(topo,provenance,str(source_path),source_path.name,rid,comps,{'ideal_id':rid,'n_components':len(comps),'tag':tag.upper()}))
    return out


def _ideal_records_legacy(text: str, provenance: str, source_path: Path, n_points: int) -> list[SourceGeometry]:
    """Fallback for legacy/mirrored block files with numeric topology headers.

    Supports a header like 3.1.1 / 3:1:1 followed by Gilbert-style six-column
    coefficient rows. This does not reinterpret arbitrary tables as coordinates.
    """
    out=[]; current=None; rows=[]
    def flush():
        nonlocal current,rows
        if current and rows:
            coeff={}; h=1
            for r in rows:
                if len(r)==3 and h==1 and 0 not in coeff: coeff[0]=(np.asarray(r),np.zeros(3)); continue
                if len(r)>=6:
                    coeff[h]=(np.asarray([r[0],r[2],r[4]]),np.asarray([r[1],r[3],r[5]])); h+=1
            if coeff and any(k>0 for k in coeff):
                try:
                    x=eval_fourier(coeff,n_points); rid=current.replace('.',':'); topo=canonical_ideal_id(rid,False)
                    out.append(SourceGeometry(topo,provenance,str(source_path),source_path.name,current,[x],{'ideal_id':current,'legacy_block':True,'n_components':1}))
                except Exception: pass
        current=None; rows=[]
    for line in text.splitlines():
        s=line.strip()
        hm=re.fullmatch(r'(\d+)[\.:](\d+)[\.:](\d+)',s)
        if hm:
            flush(); current='.'.join(hm.groups()); continue
        if current:
            nums=[]
            for tok in re.split(r'[\s,]+',s):
                try: nums.append(float(tok))
                except ValueError: pass
            if len(nums) in (3,6): rows.append(nums)
    flush(); return out


def parse_ideal_catalog(path: Path, provenance: str, n_points: int) -> list[SourceGeometry]:
    text=_read_text_or_gzip(path); out=_ideal_records_xml(text,provenance,Path(path),n_points)
    return out if out else _ideal_records_legacy(text,provenance,Path(path),n_points)


def _find_ideal_file(root: Path, stem: str) -> Path|None:
    root=Path(root)
    candidates=[root/f'{stem}.txt',root/f'{stem}.txt.gz',root/f'{stem}.gz',root/stem]
    for p in candidates:
        if p.exists() and p.is_file(): return p
    # Case-insensitive fallback.
    if root.exists():
        for p in root.iterdir():
            if p.is_file() and p.name.lower() in {f'{stem.lower()}.txt',f'{stem.lower()}.txt.gz',f'{stem.lower()}.gz',stem.lower()}: return p
    return None


def discover_relaxed(root: Path) -> list[SourceGeometry]:
    from .geometry import read_xyz_components,read_xyz
    root=Path(root); out=[]
    if not root.exists(): return out
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in {'.txt','.xyz','.csv','.dat','.pts'}: continue
        topo=_canonical_relaxed(p)
        if topo is None: continue
        try: comps=read_xyz_components(p) if topo.startswith('L') else [read_xyz(p)]
        except Exception: continue
        out.append(SourceGeometry(topo,'relaxed',str(p),p.name,p.name,comps,{'n_components':len(comps)}))
    return out


def discover_fseries(root: Path,n_points: int) -> list[SourceGeometry]:
    root=Path(root); out=[]
    if not root.exists(): return out
    for p in sorted(root.rglob('*.fseries')): out.extend(parse_fseries_file(p,n_points))
    return out


def discover_all_sources(cfg: dict, config_base: Path|None=None) -> tuple[list[SourceGeometry],dict]:
    """Discover relaxed/Fremlin/Gilbert sources using config-relative roots."""
    base=Path(config_base or '.').resolve()
    def resolve(v):
        p=Path(str(v)); return p if p.is_absolute() else (base/p).resolve()
    n=int(cfg.get('n_points',64))
    roots=cfg.get('source_roots',{})
    rr=resolve(roots.get('relaxed','../../KnotPlot/knots/final'))
    fr=resolve(roots.get('fseries','../../KnotPlot/Knots_FourierSeries'))
    ir=resolve(roots.get('ideal','../../Ideal_Sources'))
    rows=[]; errors=[]
    relaxed=discover_relaxed(rr); rows.extend(relaxed)
    fseries=discover_fseries(fr,n); rows.extend(fseries)
    ik=_find_ideal_file(ir,'Ideal'); il=_find_ideal_file(ir,'IdealLinks')
    ideal=[]; ideal_links=[]
    if ik:
        try: ideal=parse_ideal_catalog(ik,'ideal',n); rows.extend(ideal)
        except Exception as e: errors.append({'source':'ideal','path':str(ik),'error':repr(e)})
    if il:
        try: ideal_links=parse_ideal_catalog(il,'ideal_links',n); rows.extend(ideal_links)
        except Exception as e: errors.append({'source':'ideal_links','path':str(il),'error':repr(e)})
    # Keep only topologies represented by relaxed seeds by default, making this a true provenance comparison.
    ref=set(r.topology_id for r in relaxed)
    if bool(cfg.get('provenance_reference_relaxed_only',True)): rows=[r for r in rows if r.topology_id in ref]
    trx=cfg.get('source_topology_regex')
    if trx:
        rx=re.compile(str(trx),re.I); rows=[r for r in rows if rx.search(r.topology_id)]
    maxv=int(cfg.get('max_variants_per_topology_per_provenance',1)); kept=[]; count={}
    for r in sorted(rows,key=lambda z:(z.topology_id,z.provenance,z.source_record_id)):
        k=(r.topology_id,r.provenance); count[k]=count.get(k,0)+1
        if count[k]<=maxv: kept.append(r)
    summary={'roots':{'relaxed':str(rr),'fseries':str(fr),'ideal':str(ir)},'ideal_file':str(ik) if ik else None,'ideal_links_file':str(il) if il else None,'discovered_counts':{'relaxed':len(relaxed),'fseries':len(fseries),'ideal':len(ideal),'ideal_links':len(ideal_links)},'kept_records':len(kept),'reference_topologies':len(ref),'errors':errors}
    return kept,summary
