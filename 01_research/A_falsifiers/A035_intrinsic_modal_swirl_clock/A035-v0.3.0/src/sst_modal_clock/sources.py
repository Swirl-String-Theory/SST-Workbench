from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import gzip, hashlib, re, json
import numpy as np
import networkx as nx

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
    # Hoste--Thistlethwaite style names in the official Fremlin archive.
    m=re.search(r'(?:knot[._-]?)?(\d+)([an])[._](\d+)',s,re.I)
    if m: return f'K{int(m.group(1))}{m.group(2).upper()}{int(m.group(3))}'
    # A small number of official Fremlin files use a compact catalogue label
    # with no unambiguous Rolfsen separator (e.g. 15331). Preserve it without
    # guessing a topology mapping; it remains available for provenance audit.
    m=re.search(r'(?:knot[._-]?)(\d{4,})(?:$|\D)',path.stem,re.I)
    if m: return f'FREMLIN{m.group(1)}'
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


ROLFSEN_LINK_ALIASES = {
    # Verified Knot Atlas Thistlethwaite -> Rolfsen mappings used by the current relaxed-link catalog.
    'L2A1':'L2.2.1', 'L4A1':'L4.2.1', 'L5A1':'L5.2.1',
    'L6A3':'L6.2.1', 'L6A5':'L6.3.1', 'L6A4':'L6.3.2', 'L6N1':'L6.3.3',
    'L7A2':'L7.2.5', 'L7A1':'L7.2.6', 'L7N2':'L7.2.8',
    'L8A14':'L8.2.1',
}

def canonical_ideal_id(raw_id: str, has_strings: bool=False) -> str:
    rid=str(raw_id).strip()
    # Gilbert AB IDs: crossing:string-count:identifier. 5:1:2 == knot 5_2.
    m=re.fullmatch(r'(\d+)\s*:\s*(\d+)\s*:\s*(\d+)',rid)
    if m:
        c,nstr,idx=map(int,m.groups())
        return f'K{c}.{idx}' if nstr==1 and not has_strings else f'L{c}.{nstr}.{idx}'
    # Hoste-Thistlethwaite link forms.  The Gilbert IdealLinks database uses IDs
    # such as L2a1 / L6n1, while the relaxed catalog uses Rolfsen-style
    # crossing.component.index IDs (e.g. L6.3.3).  Use verified aliases where
    # available; otherwise retain an explicit HT identifier rather than silently
    # pretending that the HT index is the Rolfsen index.
    if rid.upper().startswith('L'):
        key=rid.upper().replace('_','')
        if key in ROLFSEN_LINK_ALIASES: return ROLFSEN_LINK_ALIASES[key]
        return 'HT'+key
    if re.fullmatch(r'K?11[an]\d+',rid,re.I):
        x=rid.upper()
        return x if x.startswith('K') else 'K'+x
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
        stem=Path(path).stem
        vm=re.search(r'(?:knot[._-]?)?\d+(?:[an])?[_.]\d+([^.]*)$',stem,re.I)
        variant=(vm.group(1) if vm else '').strip('_-.') or 'base'
        out.append(SourceGeometry(topo,'fseries',str(path),Path(path).name,rid,[x],{'header':' | '.join(head[:4]),'n_harmonics':max(coeff),'variant_label':variant,'official_fremlin_variant':True}))
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
    # Gilbert knots use AB / HT. Official Gilbert IdealLinks uses TL containers
    # with one STRING block per link component. HL/LINK are tolerated only for mirrors/conversions.
    pat=re.compile(r'<\s*(AB|HT|TL|HL|LINK)\b([^>]*)>(.*?)</\s*\1\s*>',re.I|re.S)
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



KATLAS_LIBRARY_ALIASES = {
    'FREMLIN':'fseries', 'FSERIES':'fseries',
    'GILBERT':'gilbert', 'IDEAL':'gilbert',
    'KATLAS':'katlas', 'KNOTATLAS':'katlas',
    'KNOTPLOT':'relaxed', 'RELAXED':'relaxed', 'RIDGERUNNER':'relaxed',
}

def normalize_library_selection(value) -> list[str]:
    """Normalize CLI/config library names while preserving user order."""
    if value is None: return []
    if isinstance(value,str): parts=[x.strip() for x in value.split(',') if x.strip()]
    else: parts=[str(x).strip() for x in value if str(x).strip()]
    out=[]
    for raw in parts:
        key=raw.upper().replace('-','').replace('_','')
        canon=KATLAS_LIBRARY_ALIASES.get(key)
        if canon is None: raise ValueError(f'Unknown library {raw!r}; use Fremlin,Gilbert,Katlas,KnotPlot')
        if canon not in out: out.append(canon)
    return out

def _canonical_katlas_id(raw_id: str, kind: str='knot') -> str:
    rid=str(raw_id).strip()
    if str(kind).lower()=='link' or rid.upper().startswith('L'):
        return canonical_ideal_id(rid,has_strings=True)
    m=re.fullmatch(r'(\d+)[_\.]([0-9]+)',rid)
    if m: return f'K{int(m.group(1))}.{int(m.group(2))}'
    m=re.fullmatch(r'(\d+)([an])[_\.]?(\d+)',rid,re.I)
    if m: return f'K{int(m.group(1))}{m.group(2).upper()}{int(m.group(3))}'
    if rid in ('0_1','0.1'): return 'K0.1'
    return 'KATLAS'+re.sub(r'[^A-Za-z0-9]+','',rid).upper()


def canonical_cli_topology(value: str|None) -> str|None:
    """Canonicalize a CLI topology selector to the internal topology id."""
    if value is None: return None
    rid=str(value).strip()
    if not rid: return None
    up=rid.upper()
    # Already-canonical internal forms.
    if re.fullmatch(r'K(?:\d+(?:\.\d+)|\d+[AN]\d+)',up): return up
    if re.fullmatch(r'L\d+\.\d+\.\d+',up): return up
    if up.startswith('HTL'): return up
    if up.startswith('L'):
        return canonical_ideal_id(rid,has_strings=True)
    m=re.fullmatch(r'(?:K)?(\d+)[_.](\d+)',rid,re.I)
    if m: return f'K{int(m.group(1))}.{int(m.group(2))}'
    m=re.fullmatch(r'(?:K)?(\d+)([an])(\d+)',rid,re.I)
    if m: return f'K{int(m.group(1))}{m.group(2).upper()}{int(m.group(3))}'
    raise ValueError(f'Unsupported --topology={value!r}; examples: 3_1, K3.1, L2a1, L2.2.1')

def parse_katlas_braid(raw: str) -> tuple[int,list[int]]|None:
    """Parse KnotTheory` BR(n,{signed Artin generators}) markup from Katlas."""
    if not raw: return None
    s=str(raw).replace('\\{','{').replace('\\}','}')
    # Katlas serializes this as \textrm{BR}(n,{...}); tolerate BR(...) mirrors.
    m=re.search(r'BR\s*\}?\s*\(\s*(\d+)\s*,\s*\{([^}]*)\}\s*\)',s,re.I|re.S)
    if not m: return None
    n=int(m.group(1)); word=[int(x) for x in re.findall(r'[-+]?\d+',m.group(2))]
    if n<1: return None
    if any(abs(g)<1 or abs(g)>=n for g in word): return None
    return n,word

def _bezier(P0,P1,P2,P3,u):
    u=np.asarray(u,float)[:,None]; v=1.0-u
    return v**3*P0 + 3*v*v*u*P1 + 3*v*u*u*P2 + u**3*P3

def braid_to_components(n_strands: int, word: list[int], n_points: int, samples_per_generator: int=12) -> list[np.ndarray]:
    """Canonical smooth 3-D closed-braid embedding.

    This is a *translator-generated* geometry, not a Katlas coordinate dataset.
    The rectangular braid realizes the signed Artin word exactly; closures are
    routed outside the braid box. Component cycles are obtained from the braid
    permutation. The result is then uniform-arclength resampled downstream.
    """
    n=int(n_strands); word=[int(g) for g in word]
    if n==1 and not word:
        t=np.linspace(0,2*np.pi,max(64,int(n_points)),endpoint=False)
        return [np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])]
    L=max(1,len(word)); spp=max(6,int(samples_per_generator)); spacing=1.0; h=.38
    yslots=(np.arange(n,dtype=float)-.5*(n-1))*spacing
    occupant=list(range(n))                 # slot -> physical strand
    paths=[[np.array([0.0,yslots[p],0.0])] for p in range(n)]
    for k,g in enumerate(word):
        i=abs(g)-1; left=occupant[i]; right=occupant[i+1]
        us=np.linspace(0,1,spp+1)[1:]
        sm=us*us*(3-2*us); bump=np.sin(np.pi*us)**2
        for p in range(n):
            slot=occupant.index(p)
            if p==left:
                yy=yslots[i] + (yslots[i+1]-yslots[i])*sm
                zz=(1 if g>0 else -1)*h*bump
            elif p==right:
                yy=yslots[i+1] + (yslots[i]-yslots[i+1])*sm
                zz=(-1 if g>0 else 1)*h*bump
            else:
                yy=np.full_like(us,yslots[slot]); zz=np.zeros_like(us)
            xx=k+us
            paths[p].extend(np.column_stack([xx,yy,zz]))
        occupant[i],occupant[i+1]=occupant[i+1],occupant[i]
    # physical strand p ends in this slot; closure at that slot joins to strand with same initial slot.
    end_slot=[0]*n
    for slot,p in enumerate(occupant): end_slot[p]=slot
    # Smooth two-piece cubic Bezier closure outside the braid box, tangent +x at both joins.
    margin=max(1.5,.35*L); zc=1.8+.12*n
    closures={}
    ub=np.linspace(0,1,max(10,2*spp)+1)[1:]
    for slot in range(n):
        y=yslots[slot]; P0=np.array([float(L),y,0.]); Pm=np.array([.5*L,y,zc])
        A1=np.array([L+margin,y,0.]); A2=np.array([L+margin,y,zc])
        B1=np.array([-margin,y,zc]); B2=np.array([-margin,y,0.]); P3=np.array([0.,y,0.])
        q1=_bezier(P0,A1,A2,Pm,ub); q2=_bezier(Pm,B1,B2,P3,ub)
        closures[slot]=np.vstack([q1,q2])
    seen=set(); comps=[]
    for p0 in range(n):
        if p0 in seen: continue
        chunks=[]; p=p0
        while p not in seen:
            seen.add(p); chunks.append(np.asarray(paths[p],float)); slot=end_slot[p]; chunks.append(closures[slot]); p=slot
        c=np.vstack([q if j==0 else q[1:] for j,q in enumerate(chunks)])
        # Remove accidental exact duplicates before downstream arclength normalization.
        keep=np.ones(len(c),dtype=bool); keep[1:]=np.linalg.norm(np.diff(c,axis=0),axis=1)>1e-12; c=c[keep]
        if len(c)>=8: comps.append(c)
    return comps



def parse_katlas_pd(raw: str) -> list[tuple[int,int,int,int]]|None:
    """Parse KnotTheory` PD X[i,j,k,l] markup, including compact subscripts.

    Compact forms such as X<sub>8192</sub> are globally disambiguated by the
    PD invariant that every edge label 1..2c occurs exactly twice.
    """
    if not raw: return None
    toks=re.findall(r'X\s*<sub>(.*?)</sub>',str(raw),re.I|re.S)
    if not toks:
        toks=re.findall(r'X\s*[\[(]([^]\)]*)[]\)]',str(raw),re.I|re.S)
    c=len(toks)
    if c<1: return None
    maxlab=2*c; options=[]
    for tok in toks:
        clean=re.sub(r'<[^>]+>','',tok).strip()
        if ',' in clean:
            vals=[int(x) for x in re.findall(r'\d+',clean)]
            options.append([tuple(vals)] if len(vals)==4 and all(1<=x<=maxlab for x in vals) else [])
            continue
        digits=re.sub(r'\D','',clean); opts=[]
        def rec(pos,parts):
            if len(parts)==4:
                if pos==len(digits): opts.append(tuple(parts))
                return
            rem=4-len(parts)
            for width in (1,2):
                if pos+width>len(digits): continue
                left=len(digits)-(pos+width)
                if left<rem-1 or left>2*(rem-1): continue
                ss=digits[pos:pos+width]
                if not ss or ss[0]=='0': continue
                v=int(ss)
                if 1<=v<=maxlab: rec(pos+width,parts+[v])
        rec(0,[]); options.append(opts)
    if any(not x for x in options): return None
    counts={i:0 for i in range(1,maxlab+1)}; chosen=[]; solution=None
    def bt(k):
        nonlocal solution
        if solution is not None: return
        if k==c:
            if all(v==2 for v in counts.values()): solution=list(chosen)
            return
        for op in options[k]:
            if any(counts[e]>=2 for e in op): continue
            for e in op: counts[e]+=1
            chosen.append(op); bt(k+1); chosen.pop()
            for e in op: counts[e]-=1
    bt(0)
    return solution

def _gauss_component_count(raw: str) -> int|None:
    if not raw: return None
    groups=re.findall(r'\{[^{}]*\}',str(raw))
    return len(groups) if groups else 1

def pd_to_components(pd: list[tuple[int,int,int,int]], n_points: int, samples_per_segment: int=10) -> list[np.ndarray]:
    """Translate a KnotTheory planar diagram into smooth-ish 3-D link components.

    KnotTheory defines X[i,j,k,l] counterclockwise from incoming lower edge i.
    Thus (i,k) is the under strand and (j,l) the over strand.  The exact PD
    rotation system is embedded planarly; only intended crossings get a z lift.
    This is generated geometry, never source coordinates.
    """
    pd=[tuple(map(int,x)) for x in pd]; c=len(pd)
    inc={}
    for ci,t in enumerate(pd):
        if len(t)!=4: raise ValueError('PD crossing must have four edge labels')
        for e in t: inc.setdefault(e,[]).append(ci)
    if set(inc)!=set(range(1,2*c+1)) or any(len(v)!=2 for v in inc.values()):
        raise ValueError('invalid PD edge incidence')
    # Build the exact combinatorial rotation system. PlanarEmbedding expects CW;
    # Katlas gives the X tuple CCW, hence reversed(t). Subdivision avoids multiedges.
    data={}
    for ci,t in enumerate(pd): data[('c',ci)]=[('e',e) for e in reversed(t)]
    for e,cs in inc.items(): data[('e',e)]=[('c',q) for q in cs]
    emb=nx.PlanarEmbedding(); emb.set_data(data); emb.check_structure()
    pos=nx.combinatorial_embedding_to_pos(emb,fully_triangulate=False)
    xy={k:np.asarray(v,float) for k,v in pos.items()}
    dists=[]
    for ci,t in enumerate(pd):
        C=xy[('c',ci)]
        for e in t: dists.append(float(np.linalg.norm(xy[('e',e)]-C)))
    med=max(float(np.median(dists)),1e-6); radius=.18*med; lift=.25*med
    endpoints={}; pair={}; is_over={}
    for ci,(i,j,k,l) in enumerate(pd):
        pair[(ci,i)]=k; pair[(ci,k)]=i; pair[(ci,j)]=l; pair[(ci,l)]=j
        for e in (i,k): is_over[(ci,e)]=False
        for e in (j,l): is_over[(ci,e)]=True
        C=xy[('c',ci)]
        for e in (i,j,k,l):
            d=xy[('e',e)]-C; d=d/(np.linalg.norm(d)+1e-15)
            endpoints[(ci,e)]=np.r_[C+radius*d, lift if is_over[(ci,e)] else -lift]
    other={}
    for e,(a,b) in inc.items(): other[(a,e)]=b; other[(b,e)]=a
    spp=max(6,int(samples_per_segment)); comps=[]; visited_edges=set()
    for start in sorted(inc):
        if start in visited_edges: continue
        c0=inc[start][0]; ci=c0; ein=start; chunks=[]; guard=0
        while True:
            guard+=1
            if guard>4*len(inc)+8: raise ValueError('PD component traversal did not close')
            visited_edges.add(ein); eout=pair[(ci,ein)]
            z=lift if is_over[(ci,ein)] else -lift
            a=endpoints[(ci,ein)]; b=endpoints[(ci,eout)]; C=np.r_[xy[('c',ci)],z]
            u=np.linspace(0,1,spp,endpoint=False)[:,None]
            chunks.append((1-u)**2*a+2*(1-u)*u*C+u**2*b)
            cj=other[(ci,eout)]; b2=endpoints[(cj,eout)]; M=np.r_[xy[('e',eout)],0.0]
            chunks.append((1-u)**2*b+2*(1-u)*u*M+u**2*b2)
            ci=cj; ein=eout
            if ci==c0 and ein==start: break
        q=np.vstack(chunks)
        keep=np.ones(len(q),dtype=bool); keep[1:]=np.linalg.norm(np.diff(q,axis=0),axis=1)>1e-12
        q=q[keep]
        if len(q)<8: raise ValueError('degenerate PD component')
        comps.append(q)
    return comps

def _katlas_invariant_subset(obj: dict) -> dict:
    inv=obj.get('invariants',{}) or {}; keys=['Crossings','BraidIndex','Determinant','KnotSignature','Alexander_Polynomial','Jones_Polynomial','Conway_Polynomial','HyperbolicVolume','SymmetryType','UnknottingNumber']
    return {k:inv.get(k) for k in keys if k in inv}

def discover_katlas(root: Path,n_points: int) -> tuple[list[SourceGeometry],dict]:
    """Translate Katlas knots from braid words and links from exact PD data.

    Knots without an explicit braid remain metadata-only. Links are translated
    only when a valid PD is present; Gauss component count is used as an
    independent structural cross-check.
    """
    root=Path(root); out=[]; stat={'records_total':0,'knot_records':0,'link_records':0,'braid_records':0,'pd_link_records':0,'conditioned_link_records':0,'geometry_records':0,'knot_geometry_records':0,'link_geometry_records':0,'metadata_only_no_supported_geometry':0,'metadata_only_no_braid':0,'parse_errors':0,'component_mismatch':0}
    if not root.exists(): return out,stat
    seen_ids=set()
    for p in sorted(root.rglob('katlas.json')):
        stat['records_total']+=1
        try: obj=json.loads(p.read_text(encoding='utf-8',errors='ignore'))
        except Exception: stat['parse_errors']+=1; continue
        ident=obj.get('identity',{}) or {}; kind=str(ident.get('kind','knot')).lower(); is_link=(kind=='link'); stat['link_records' if is_link else 'knot_records']+=1
        rawid=str(ident.get('katlas_id') or p.parent.name); dedupe_key=(kind,rawid)
        if dedupe_key in seen_ids: continue
        seen_ids.add(dedupe_key); topo=_canonical_katlas_id(rawid,kind)
        presentations=obj.get('presentations',{}) or {}; comps=None; meta={}; translator=None
        if is_link:
            raw_pd=next((x for x in (presentations.get('pd') or []) if str(x).strip()),None)
            pd=parse_katlas_pd(raw_pd) if raw_pd else None
            conditioned=p.parent/'conditioned_geometry.npz'
            if conditioned.exists():
                try:
                    z=np.load(conditioned,allow_pickle=False); pts=np.asarray(z['points'],float); offs=np.asarray(z['component_offsets'],dtype=np.int64)
                    if len(offs)<2 or offs[0]!=0 or offs[-1]!=len(pts): raise ValueError('invalid conditioned component offsets')
                    comps=[pts[int(offs[i]):int(offs[i+1])] for i in range(len(offs)-1)]
                    raw_gauss=next((x for x in (presentations.get('gauss') or []) if str(x).strip()),None); expected=_gauss_component_count(raw_gauss)
                    if expected is not None and len(comps)!=expected:
                        stat['component_mismatch']+=1; comps=None
                    else:
                        stat['conditioned_link_records']+=1; translator='SST-KATLAS-ISOTOPY-HARMONIC-2.0'
                        meta.update({'geometry_origin':'generated_from_katlas_pd_conditioned','source_coordinates':False,'translator':translator,'raw_translator':'SST-KATLAS-PD-3D-1.0','conditioned_geometry_file':str(conditioned),'pd_crossings':[list(x) for x in pd] if pd else None,'gauss_component_count':expected})
                except Exception:
                    stat['parse_errors']+=1; comps=None
            elif pd:
                try:
                    comps=pd_to_components(pd,n_points); stat['pd_link_records']+=1
                    raw_gauss=next((x for x in (presentations.get('gauss') or []) if str(x).strip()),None)
                    expected=_gauss_component_count(raw_gauss)
                    if expected is not None and len(comps)!=expected:
                        stat['component_mismatch']+=1; comps=None
                    else:
                        translator='SST-KATLAS-PD-3D-1.0'; meta.update({'geometry_origin':'generated_from_katlas_pd','source_coordinates':False,'translator':translator,'pd_crossings':[list(x) for x in pd],'gauss_component_count':expected})
                except Exception:
                    stat['parse_errors']+=1; comps=None
        else:
            parsed=None; raw_braid=None
            for b in presentations.get('braid') or []:
                parsed=parse_katlas_braid(b)
                if parsed: raw_braid=b; break
            if parsed:
                stat['braid_records']+=1; ns,word=parsed
                try: comps=braid_to_components(ns,word,n_points)
                except Exception: stat['parse_errors']+=1; comps=None
                if comps and len(comps)!=1:
                    stat['component_mismatch']+=1; comps=None
                if comps:
                    translator='SST-KATLAS-BRAID-1.0'; meta.update({'geometry_origin':'generated_from_katlas_braid','source_coordinates':False,'translator':translator,'braid_n_strands':ns,'braid_word':word,'braid_raw':raw_braid})
        if not comps:
            stat['metadata_only_no_supported_geometry']+=1; stat['metadata_only_no_braid']+=1 if not is_link else 0; continue
        stat['geometry_records']+=1; stat['link_geometry_records' if is_link else 'knot_geometry_records']+=1
        meta.update({'katlas_id':rawid,'katlas_kind':kind,'table':ident.get('table'),'crossings':ident.get('crossings'),'pd':presentations.get('pd',[])[:1],'gauss':presentations.get('gauss',[])[:1],'dt':presentations.get('dt',[])[:1],'invariants':_katlas_invariant_subset(obj),'n_components':len(comps)})
        out.append(SourceGeometry(topo,'katlas',str(p),p.name,rawid,comps,meta))
    return out,stat

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


def discover_all_sources(cfg: dict, config_base: Path|None=None, libraries=None, min_carriers=None, kind=None, topology=None) -> tuple[list[SourceGeometry],dict]:
    """Discover selected geometry libraries and build a matched provenance set.

    Library names accepted by CLI/config: Fremlin, Gilbert, Katlas, KnotPlot.
    If --libraries is explicit, unselected libraries are not read at all. Without
    an explicit selection the legacy v0.2.2.2 behavior is preserved.
    """
    base=Path(config_base or '.').resolve()
    def resolve(v):
        p=Path(str(v)); return p if p.is_absolute() else (base/p).resolve()
    n=int(cfg.get('n_points',64)); roots=cfg.get('source_roots',{})
    rr=resolve(roots.get('relaxed','../../KnotPlot/knots/final'))
    fr=resolve(roots.get('fseries','../../Ideal_Fremlin_Fseries/fremlin'))
    ir=resolve(roots.get('ideal','../../Ideal_Sources'))
    kr=resolve(roots.get('katlas','../../Katlas_Sources_v0.2.2_Outputs'))
    explicit=normalize_library_selection(libraries if libraries is not None else cfg.get('libraries'))
    selected=explicit or ['relaxed','fseries','gilbert']
    rows=[]; errors=[]; relaxed=[]; fseries=[]; ideal=[]; ideal_links=[]; katlas=[]; katlas_stats={}
    if 'relaxed' in selected:
        relaxed=discover_relaxed(rr); rows.extend(relaxed)
    if 'fseries' in selected:
        fseries=discover_fseries(fr,n); rows.extend(fseries)
    knot_stems=['Ideal','Ideal_11a','Ideal_11n']; link_stems=['IdealLinks','IdealLinks_10a','IdealLinks_10n','IdealLinks_11a1','IdealLinks_11a2','IdealLinks_11n1','IdealLinks_11n2']
    ideal_files=[]; ideal_links_files=[]
    if 'gilbert' in selected:
        for stem in knot_stems:
            pp=_find_ideal_file(ir,stem)
            if not pp: continue
            ideal_files.append(str(pp))
            try: rrk=parse_ideal_catalog(pp,'ideal',n); ideal.extend(rrk); rows.extend(rrk)
            except Exception as e: errors.append({'source':'ideal','catalog':stem,'path':str(pp),'error':repr(e)})
        for stem in link_stems:
            pp=_find_ideal_file(ir,stem)
            if not pp: continue
            ideal_links_files.append(str(pp))
            try: rrl=parse_ideal_catalog(pp,'ideal_links',n); ideal_links.extend(rrl); rows.extend(rrl)
            except Exception as e: errors.append({'source':'ideal_links','catalog':stem,'path':str(pp),'error':repr(e)})
    if 'katlas' in selected:
        try: katlas,katlas_stats=discover_katlas(kr,n); rows.extend(katlas)
        except Exception as e: errors.append({'source':'katlas','path':str(kr),'error':repr(e)})
    ik=Path(ideal_files[0]) if ideal_files else None; il=Path(ideal_links_files[0]) if ideal_links_files else None
    def family(r): return {'relaxed':'KnotPlot','fseries':'Fremlin','ideal':'Gilbert','ideal_links':'Gilbert','katlas':'Katlas'}.get(r.provenance,r.provenance)
    source_kind=str(kind or cfg.get('source_kind','all')).strip().lower()
    if source_kind not in {'all','knots','knot','links','link'}: raise ValueError('--kind must be all, knots, or links')
    if source_kind in {'knots','knot'}: rows=[r for r in rows if not r.topology_id.startswith(('L','HTL'))]
    elif source_kind in {'links','link'}: rows=[r for r in rows if r.topology_id.startswith(('L','HTL'))]
    requested_topology=canonical_cli_topology(topology)
    if requested_topology is not None: rows=[r for r in rows if r.topology_id.upper()==requested_topology.upper()]
    # Legacy mode: relaxed topology set remains reference. Explicit library mode:
    # retain topologies shared by >=N selected families (default 2), so Katlas/Gilbert
    # catalog size cannot explode the physics campaign.
    if not explicit and bool(cfg.get('provenance_reference_relaxed_only',True)):
        ref=set(r.topology_id for r in relaxed); rows=[r for r in rows if r.topology_id in ref]
    elif explicit:
        fams={}
        for r in rows: fams.setdefault(r.topology_id,set()).add(family(r))
        if min_carriers is not None:
            need=max(1,int(min_carriers))
        elif bool(cfg.get('require_all_selected_libraries',True)):
            need=len(selected)
        else:
            need=int(cfg.get('gate_min_selected_library_matches',2 if len(selected)>=2 else 1))
        if need>len(selected): raise ValueError(f'--min-carriers={need} exceeds selected library count {len(selected)}')
        eligible={k for k,v in fams.items() if len(v)>=need}; rows=[r for r in rows if r.topology_id in eligible]; ref=eligible
    else: ref=set(r.topology_id for r in rows)
    trx=cfg.get('source_topology_regex')
    if trx:
        rx=re.compile(str(trx),re.I); rows=[r for r in rows if rx.search(r.topology_id)]
    maxv=int(cfg.get('max_variants_per_topology_per_provenance',16)); kept=[]; count={}
    for r in sorted(rows,key=lambda z:(z.topology_id,z.provenance,z.source_record_id)):
        k=(r.topology_id,r.provenance); count[k]=count.get(k,0)+1
        if count[k]<=maxv: kept.append(r)
    bytop={}
    for r in kept: bytop.setdefault(r.topology_id,set()).add(family(r))
    summary={'selected_libraries':[{'relaxed':'KnotPlot','fseries':'Fremlin','gilbert':'Gilbert','katlas':'Katlas'}[x] for x in selected],'explicit_library_selection':bool(explicit),'source_kind':source_kind,'requested_topology':requested_topology,'min_carriers_required':(int(min_carriers) if min_carriers is not None else (len(selected) if explicit and bool(cfg.get('require_all_selected_libraries',True)) else int(cfg.get('gate_min_selected_library_matches',2 if len(selected)>=2 else 1)))),'roots':{'relaxed':str(rr),'fseries':str(fr),'ideal':str(ir),'katlas':str(kr)},'ideal_file':str(ik) if ik else None,'ideal_links_file':str(il) if il else None,'ideal_files':ideal_files,'ideal_links_files':ideal_links_files,'discovered_counts':{'relaxed':len(relaxed),'fseries':len(fseries),'ideal':len(ideal),'ideal_links':len(ideal_links),'katlas_geometry':len(katlas)},'katlas_translation':katlas_stats,'kept_records':len(kept),'reference_topologies':len(ref),'matched_topologies_ge2':sum(len(v)>=2 for v in bytop.values()),'matched_topologies_ge3':sum(len(v)>=3 for v in bytop.values()),'errors':errors}
    return kept,summary

