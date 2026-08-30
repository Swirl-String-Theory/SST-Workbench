from __future__ import annotations
import hashlib
import io as _io
import re
import struct
from pathlib import Path
from typing import Iterable
import numpy as np
from .models import GeometryAsset
from .library_root import resolve_path_provenance


def file_sha256(path) -> str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def _source_family(path: Path) -> str:
    """Legacy path heuristic for format-ish family labels.

    Prefer provider_id from SOURCE.json via resolve_path_provenance(). This heuristic
    is only a fallback for paths outside Knot_Library/Sources and must never certify topology.
    """
    s=path.name.lower(); parts=[p.lower() for p in path.parts]
    if 'ideal' in s: return 'ideal_txt'
    if 'fseries' in s or any('fseries' in p for p in parts): return 'knotplot_fseries'
    if 'ridgerunner' in s or any('ridgerunner' in p or p=='rr' for p in parts): return 'ridgerunner'
    if path.suffix.lower()=='.vect': return 'vect'
    if path.suffix.lower() in {'.knot','.kp','.kpf'}: return 'knotplot_binary'
    return 'coordinate_file'


def load_ascii_components(path: str|Path) -> list[np.ndarray]:
    """Load plain coordinate data.

    Supports whitespace/comma separated XYZ. Blank lines or 'component' markers split components.
    Non-numeric header/comment lines are ignored. This deliberately does not guess unknown
    Fourier coefficient formats: at least 3 finite numeric values per data line are required.
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


def load_vect_components(path: str|Path) -> list[np.ndarray]:
    toks=Path(path).read_text(encoding='utf-8',errors='ignore').split()
    if not toks or toks[0] != 'VECT': raise ValueError('not a VECT file')
    k=1; npoly=int(toks[k]); nvert=int(toks[k+1]); ncolor=int(toks[k+2]); k+=3
    counts=[int(toks[k+i]) for i in range(npoly)]; k+=npoly
    color_counts=[int(toks[k+i]) for i in range(npoly)]; k+=npoly
    total=sum(abs(x) for x in counts)
    vals=np.asarray([float(x) for x in toks[k:k+3*total]],float).reshape(total,3); k+=3*total
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

    LOCS/LOCC are intentionally rejected by default because they are quantized and their exact
    scale/offset layout is not documented sufficiently here. This is a safety feature: no silent
    lossy decoding inside a falsifier.
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
        # Mixed case fields contain exactly four bytes.
        if pos+4>len(raw): raise ValueError(f'truncated KnotPlot field {tag}')
        data=raw[pos:pos+4]; pos+=4
        if tag=='Attr': meta.setdefault('attributes',[]).append(_be_u32(data))
    out=[]
    for chunks in comps:
        if chunks: out.append(np.vstack(chunks))
    if not out: raise ValueError('KnotPlot file contains no supported LOCD/LOCF coordinates')
    return out,meta,warns


def load_geometry(path: str|Path, *, format: str='auto', allow_lossy_knotplot: bool=False) -> GeometryAsset:
    path=Path(path); fmt=format.lower()
    if fmt=='auto':
        head=path.read_bytes()[:32]
        if head.startswith(b'KnotPlot 1.0'): fmt='knotplot'
        elif path.suffix.lower()=='.vect' or head.lstrip().startswith(b'VECT'): fmt='vect'
        else: fmt='ascii'
    meta={}; warns=[]
    if fmt in {'ascii','xyz','txt','csv','ideal','fseries'}:
        comps=load_ascii_components(path); actual='ascii_xyz'
    elif fmt=='vect':
        comps=load_vect_components(path); actual='vect'
    elif fmt in {'knotplot','kpf','knot'}:
        comps,meta,warns=load_knotplot_binary(path,allow_lossy=allow_lossy_knotplot); actual='knotplot_1.0'
    else: raise ValueError(f'unsupported format {format}')
    prov=resolve_path_provenance(path)
    family=_source_family(path)
    if prov.get('provider_id'):
        # Provenance-native label; keep legacy heuristic only as metadata fallback key.
        family=prov['provider_id']
    elif prov.get('quarantine_hint'):
        warns=list(warns)+[f"no provider_id; quarantine_hint={prov['quarantine_hint']}"]
        meta=dict(meta); meta['quarantine_hint']=prov['quarantine_hint']
    meta=dict(meta); meta['provider_resolution']=prov.get('resolved_from')
    return GeometryAsset(
        components=[np.asarray(c,float) for c in comps], source_path=str(path),
        source_family=family, source_format=actual, source_sha256=file_sha256(path),
        provider_id=prov.get('provider_id'), provider_name=prov.get('provider_name'),
        provider_class=prov.get('class'),
        warnings=warns, metadata=meta,
    )
