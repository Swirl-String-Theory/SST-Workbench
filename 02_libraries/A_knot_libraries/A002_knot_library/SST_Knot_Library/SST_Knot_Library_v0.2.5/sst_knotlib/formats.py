from __future__ import annotations
import hashlib
import re
import struct
from pathlib import Path
import numpy as np
from .models import GeometryAsset

TAU=2.0*np.pi


def file_sha256(path) -> str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def _source_family(path: Path, *, detected_format: str|None=None) -> str:
    s=path.name.lower(); parts=[p.lower() for p in path.parts]
    if detected_format=='gilbert_ab_fourier' or any('ideal_gilbert' in p for p in parts): return 'ideal_gilbert_fourier'
    # Fremlin_FourierSeries is a separate local source lineage.  Check it before the
    # generic 'fseries' token so it can never be mislabeled as KnotPlot provenance.
    if any(('fremlin_fourierseries' in p) or p=='fremlin' for p in parts):
        return 'fremlin_short_coordinate' if path.suffix.lower()=='.short' else 'fremlin_local'
    if 'ideal' in s: return 'ideal_txt'
    if 'fseries' in s or any('fseries' in p for p in parts): return 'knotplot_fseries'
    if 'ridgerunner' in s or any('ridgerunner' in p or p=='rr' for p in parts): return 'ridgerunner'
    if path.suffix.lower()=='.vect': return 'vect'
    if path.suffix.lower() in {'.knot','.kp','.kpf'}: return 'knotplot_binary'
    return 'coordinate_file'


def classify_non_geometry_file(path: str|Path) -> dict|None:
    """Recognize known metadata files that must not be parsed as centerlines."""
    p=Path(path); n=p.name.lower(); parts=[x.lower() for x in p.parts]
    if n=='0twelvedata.csv' and any('ridgerunner' in x for x in parts):
        return {
            'role':'metadata_table',
            'provider_id':'klotz_anderson_12crossing',
            'reason':'Knot Atlas TwelveData archive summary CSV; Cartesian centerlines are separate text files'
        }
    if 'twelvesummary' in n and p.suffix.lower()=='.csv':
        return {
            'role':'metadata_table',
            'provider_id':'klotz_anderson_12crossing',
            'reason':'12-crossing summary metadata, not XYZ geometry'
        }
    return None


def load_ascii_components(path: str|Path) -> list[np.ndarray]:
    """Load plain whitespace/comma separated XYZ coordinate data.

    Blank lines or ``component`` markers split components. Non-numeric header/comment lines are
    ignored. Unknown coefficient formats are not guessed.
    """
    path=Path(path); comps=[]; cur=[]
    for line in path.read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip()
        if not s or re.match(r'(?i)^(component|comp)\b',s):
            if cur: comps.append(np.asarray(cur,float)); cur=[]
            continue
        if s.startswith(('#','//',';')): continue
        toks=re.split(r'[\s,;]+',s)
        vals=[]
        for tok in toks:
            if not tok: continue
            try: vals.append(float(tok))
            except ValueError: break
        if len(vals)>=3 and np.all(np.isfinite(vals[:3])):
            cur.append(vals[:3])
    if cur: comps.append(np.asarray(cur,float))
    comps=[c for c in comps if len(c)>=3]
    if not comps:
        raise ValueError('no XYZ coordinate components found; file may not be a coordinate-series format')
    return comps


def _attrs(s: str) -> dict[str,str]:
    return {k:v.strip() for k,v in re.findall(r'([A-Za-z][A-Za-z0-9_]*)\s*=\s*"([^"]*)"',s)}


def _vec3_attr(value: str|None) -> np.ndarray:
    if value is None or not value.strip(): return np.zeros(3,float)
    toks=[x.strip() for x in value.split(',')]
    if len(toks)!=3: raise ValueError(f'expected 3-vector coefficient, got {value!r}')
    a=np.asarray([float(x) for x in toks],float)
    if not np.isfinite(a).all(): raise ValueError('non-finite Gilbert Fourier coefficient')
    return a


def load_gilbert_ab_components(path: str|Path, *, n_samples: int=512) -> tuple[list[np.ndarray],dict,list[str]]:
    r"""Decode one Brian Gilbert Ideal-Knots Fourier record.

    The public Knot Atlas format defines

    ``X(t) = A[0]/2 + sum_i A[i] cos(i t) + B[i] sin(i t)``.

    A file containing multiple independent database records is rejected deliberately; callers
    should extract one ``<AB>``/``<HT>`` record per geometry asset so provenance remains unique.
    """
    path=Path(path); text=path.read_text(encoding='utf-8',errors='replace')
    blocks=list(re.finditer(r'<(AB|HT)\b([^>]*)>(.*?)</\1\s*>',text,re.I|re.S))
    if not blocks:
        raise ValueError('no Brian Gilbert <AB>/<HT> Fourier record found')
    if len(blocks)!=1:
        raise ValueError(f'file contains {len(blocks)} Gilbert records; extract one record per geometry asset')
    m=blocks[0]; tag=m.group(1).upper(); head=_attrs(m.group(2)); body=m.group(3)
    coeffs={}
    for cm in re.finditer(r'<Coeff\b([^>]*)/?>',body,re.I|re.S):
        a=_attrs(cm.group(1))
        if 'I' not in a: continue
        i=int(a['I'])
        if i<0: raise ValueError('negative Gilbert coefficient index')
        coeffs[i]=(_vec3_attr(a.get('A')),_vec3_attr(a.get('B')))
    if not coeffs:
        raise ValueError('Gilbert record contains no <Coeff> entries')
    if n_samples<16: raise ValueError('n_samples must be >= 16')
    t=TAU*np.arange(n_samples,dtype=float)/float(n_samples)
    p=np.zeros((n_samples,3),float)
    if 0 in coeffs:
        p += 0.5*coeffs[0][0][None,:]
    for i,(A,B) in sorted(coeffs.items()):
        if i==0: continue
        p += np.cos(i*t)[:,None]*A[None,:] + np.sin(i*t)[:,None]*B[None,:]
    meta={
        'format_reference':'Brian Gilbert / Knot Atlas Ideal knots Fourier series',
        'record_tag':tag,
        'record_attributes':head,
        'coefficient_count':len(coeffs),
        'max_coefficient_index':max(coeffs),
        'sampling_n':n_samples,
        'equation':'X(t)=A[0]/2+sum_i(A[i] cos(i t)+B[i] sin(i t))',
    }
    warns=[]
    return [p],meta,warns


def _oogl_vect_tokens(path: str|Path) -> list[str]:
    """Tokenize Geomview/plCurve VECT while honoring ``#`` comments.

    Geomview VECT is whitespace-delimited and permits comments. Ridgerunner/plCurve
    output routinely contains comment lines, so raw ``str.split`` is not sufficient.
    """
    text=Path(path).read_text(encoding='utf-8',errors='ignore')
    toks=[]
    for line in text.splitlines():
        line=line.split('#',1)[0]
        if line.strip(): toks.extend(line.split())
    return toks


def load_vect_components(path: str|Path) -> list[np.ndarray]:
    toks=_oogl_vect_tokens(path)
    if not toks or toks[0] not in {'VECT','4VECT'}: raise ValueError('not a VECT file')
    if len(toks)<4: raise ValueError('truncated VECT header')
    k=1; npoly=int(toks[k]); nvert=int(toks[k+1]); ncolor=int(toks[k+2]); k+=3
    if npoly<0 or nvert<0 or ncolor<0: raise ValueError('invalid negative VECT header count')
    if len(toks)<k+2*npoly: raise ValueError('truncated VECT component/color counts')
    counts=[int(toks[k+i]) for i in range(npoly)]; k+=npoly
    color_counts=[int(toks[k+i]) for i in range(npoly)]; k+=npoly
    total=sum(abs(x) for x in counts)
    if total != nvert:
        raise ValueError(f'VECT vertex count mismatch: header={nvert}, components={total}')
    need=3*total
    if len(toks)<k+need: raise ValueError(f'truncated VECT vertices: need {need} coordinate values')
    vals=np.asarray([float(x) for x in toks[k:k+need]],float).reshape(total,3); k+=need
    comps=[]; pos=0
    for count in counts:
        n=abs(count); c=vals[pos:pos+n].copy(); pos+=n
        comps.append(c)
    return comps


def save_vect_components(path, components):
    comps=[np.asarray(c,float) for c in components]
    with open(path,'w',encoding='utf-8',newline='\n') as f:
        f.write('VECT\n')
        f.write(f'{len(comps)} {sum(len(c) for c in comps)} 0\n')
        f.write(' '.join(str(-len(c)) for c in comps)+'\n')
        f.write(' '.join('0' for _ in comps)+'\n')
        for c in comps:
            for x,y,z in c: f.write(f'{x:.17g} {y:.17g} {z:.17g}\n')


def _be_u32(b: bytes) -> int:
    return struct.unpack('>I',b)[0]


def load_knotplot_binary(path: str|Path, *, allow_lossy: bool=False) -> tuple[list[np.ndarray],dict,list[str]]:
    """Read the documented KnotPlot 1.0 container, supporting LOCF and LOCD coordinates.

    LOCS/LOCC remain fail-closed because they are quantized and are not needed for a falsifier
    when a lossless LOCD/LOCF/ASCII export can be used instead.
    """
    raw=Path(path).read_bytes()
    ff=raw.find(b'\x0c')
    if ff<0 or not raw[:ff].startswith(b'KnotPlot 1.0'):
        raise ValueError('not a KnotPlot 1.0 file')
    header=raw[:ff].decode('latin1',errors='replace')
    pos=ff+2 if ff+1<len(raw) else ff+1
    comps=[[]]; meta={'header':header}; warns=[]
    current=0
    while pos+4<=len(raw):
        tag=raw[pos:pos+4].decode('latin1',errors='replace'); pos+=4
        if tag=='endf': break
        if tag=='comp':
            comps.append([]); current+=1; continue
        if len(tag)<2: break
        if tag[:2].islower():
            continue
        if tag[:2].isupper():
            if pos+4>len(raw): raise ValueError('truncated KnotPlot field length')
            nbytes=_be_u32(raw[pos:pos+4]); pos+=4
            data=raw[pos:pos+nbytes]; pos+=nbytes
            if len(data)!=nbytes: raise ValueError(f'truncated KnotPlot field {tag}')
            if tag=='LOCF':
                if nbytes%12: raise ValueError('LOCF byte count not divisible by 12')
                arr=np.frombuffer(data,dtype='>f4').astype(float).reshape(-1,3); comps[current].append(arr)
            elif tag=='LOCD':
                if nbytes%24: raise ValueError('LOCD byte count not divisible by 24')
                arr=np.frombuffer(data,dtype='>f8').astype(float).reshape(-1,3); comps[current].append(arr)
            elif tag in {'LOCS','LOCC'}:
                msg=f'{tag} is quantized KnotPlot coordinate data; safe decoder disabled'
                if not allow_lossy: raise ValueError(msg+' (export as LOCD/LOCF/raw ASCII instead)')
                warns.append(msg+'; field skipped')
            elif tag in {'NAME','META','COMM','Date'}:
                meta[tag]=data.decode('utf-8',errors='replace').rstrip('\x00')
            continue
        if pos+4>len(raw): raise ValueError(f'truncated KnotPlot field {tag}')
        data=raw[pos:pos+4]; pos+=4
        if tag=='Attr': meta.setdefault('attributes',[]).append(_be_u32(data))
    out=[]
    for chunks in comps:
        if chunks: out.append(np.vstack(chunks))
    if not out: raise ValueError('KnotPlot file contains no supported LOCD/LOCF coordinates')
    return out,meta,warns


def load_geometry(path: str|Path, *, format: str='auto', allow_lossy_knotplot: bool=False,
                  gilbert_samples: int=512) -> GeometryAsset:
    path=Path(path); fmt=format.lower()
    nong=classify_non_geometry_file(path)
    if nong:
        raise ValueError(f'known non-geometry file ({nong["role"]}): {nong["reason"]}')
    if fmt=='auto':
        head=path.read_bytes()[:4096]
        if head.startswith(b'KnotPlot 1.0'): fmt='knotplot'
        elif path.suffix.lower()=='.vect' or head.lstrip().startswith(b'VECT'): fmt='vect'
        elif (b'<AB' in head or b'<HT' in head) and b'<Coeff' in head: fmt='gilbert-ab'
        else: fmt='ascii'
    meta={}; warns=[]
    if fmt in {'ascii','xyz','txt','csv','ideal','fseries'}:
        comps=load_ascii_components(path); actual='ascii_xyz'
    elif fmt in {'gilbert-ab','gilbert','ideal-gilbert'}:
        comps,meta,warns=load_gilbert_ab_components(path,n_samples=gilbert_samples); actual='gilbert_ab_fourier'
    elif fmt=='vect':
        comps=load_vect_components(path); actual='vect'
    elif fmt in {'knotplot','kpf','knot'}:
        comps,meta,warns=load_knotplot_binary(path,allow_lossy=allow_lossy_knotplot); actual='knotplot_1.0'
    else: raise ValueError(f'unsupported format {format}')
    return GeometryAsset(
        components=[np.asarray(c,float) for c in comps], source_path=str(path),
        source_family=_source_family(path,detected_format=actual), source_format=actual, source_sha256=file_sha256(path),
        warnings=warns, metadata=meta,
    )
