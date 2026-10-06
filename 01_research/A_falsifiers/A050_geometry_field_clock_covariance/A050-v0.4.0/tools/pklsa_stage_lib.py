from __future__ import annotations
from pathlib import Path
import gzip, re, hashlib, json
import numpy as np

_ATTR_RE=re.compile(r'([A-Za-z_][A-Za-z0-9_.:-]*)\s*=\s*"([^"]*)"')
_RECORD_START_RE=re.compile(r'^\s*<(AB|HT|TL)\b([^>]*)>')
_COEFF_RE=re.compile(r'<Coeff\b([^>]*)/?>',re.I)
_STRING_RE=re.compile(r'<STRING\b([^>]*)>(.*?)</STRING\s*>',re.I|re.S)
_STRING_START_RE=re.compile(r'<STRING\b([^>]*)>',re.I)
_COLON_ID_RE=re.compile(r'^(\d+):(\d+):(\d+)$')

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def load_xyz(path):
 comps=[]; cur=[]
 for raw in Path(path).read_text(encoding='utf-8',errors='replace').splitlines():
  s=raw.strip()
  if not s:
   if cur: comps.append(np.asarray(cur,float)); cur=[]
   continue
  if s.lower().startswith(('component','curve','vect')) or s.startswith(('#','%','//')):
   if s.lower().startswith(('component','curve')) and cur: comps.append(np.asarray(cur,float)); cur=[]
   continue
  vals=s.replace(',',' ').split()
  if len(vals)>=3:
   try: cur.append([float(vals[0]),float(vals[1]),float(vals[2])])
   except ValueError: pass
 if cur: comps.append(np.asarray(cur,float))
 comps=[c for c in comps if len(c)>=3 and np.isfinite(c).all()]
 if not comps: raise ValueError(f'no XYZ component in {path}')
 return comps

def load_vect(path):
 lines=[]
 for raw in Path(path).read_text(encoding='utf-8',errors='replace').splitlines():
  s=raw.split('#',1)[0].strip()
  if s: lines.append(s)
 toks=' '.join(lines).split()
 if not toks or toks[0] not in ('VECT','4VECT'): raise ValueError('not VECT')
 i=1; ncomp=int(toks[i]); nvert=int(toks[i+1]); i+=3
 counts=[int(toks[i+j]) for j in range(ncomp)]; i+=ncomp; i+=ncomp
 if sum(abs(x) for x in counts)!=nvert: raise ValueError('VECT vertex count mismatch')
 comps=[]
 for count in counts:
  m=abs(count); pts=[]
  for _ in range(m): pts.append([float(toks[i]),float(toks[i+1]),float(toks[i+2])]); i+=3
  a=np.asarray(pts,float)
  if count<0 and len(a)>1 and np.linalg.norm(a[0]-a[-1])<1e-14: a=a[:-1]
  comps.append(a)
 return comps

def _attrs(s): return {k:v for k,v in _ATTR_RE.findall(s or '')}
def _canonical_id(record_id):
 m=_COLON_ID_RE.fullmatch(str(record_id or '').strip())
 if not m:return None
 c,ns,i=map(int,m.groups()); return f'{c}_{i}' if ns==1 else None

def _read_records(path):
 p=Path(path); opener=gzip.open if p.suffix.lower()=='.gz' else open; out=[]
 with opener(p,'rt',encoding='utf-8',errors='strict') as f:
  active=None; attrs=None; buf=[]
  for line in f:
   if active is None:
    m=_RECORD_START_RE.match(line)
    if not m: continue
    active=m.group(1).upper(); attrs=_attrs(m.group(2)); tail=line[m.end():]
    em=re.search(fr'</{active}\s*>',tail,re.I)
    if em:
     out.append((active,attrs,tail[:em.start()])); active=None; attrs=None; buf=[]
    else:
     buf=[tail]
    continue
   em=re.search(fr'</{active}\s*>',line,re.I)
   if em:
    buf.append(line[:em.start()]); out.append((active,attrs,''.join(buf))); active=None; attrs=None; buf=[]
   else: buf.append(line)
 if active is not None: raise ValueError('unterminated catalog record')
 return out

def _parse_coeff(text):
 out=[]
 for raw in _COEFF_RE.findall(text or ''):
  a=_attrs(raw)
  if not {'I','A','B'}<=set(a): continue
  I=int(a['I']); A=np.fromstring(a['A'],sep=',',dtype=float); B=np.fromstring(a['B'],sep=',',dtype=float)
  if A.shape!=(3,) or B.shape!=(3,): raise ValueError('bad Gilbert coefficient')
  out.append((I,A,B))
 return out

def find_gilbert_record(path,canonical_id):
 for tag,attrs,text in _read_records(path):
  if _canonical_id(attrs.get('Id'))!=canonical_id: continue
  comps=[]; matches=list(_STRING_RE.finditer(text))
  if matches:
   for m in matches:
    c=_parse_coeff(m.group(2))
    if c: comps.append(c)
  elif _STRING_START_RE.search(text):
   m=_STRING_START_RE.search(text); c=_parse_coeff(text[m.end():]);
   if c: comps.append(c)
  else:
   c=_parse_coeff(text)
   if c: comps.append(c)
  if not comps: raise ValueError('Gilbert record contains no Fourier components')
  return comps
 raise KeyError(canonical_id)

def sample_coeff(coeff,n=4096):
 t=np.linspace(0,2*np.pi,int(n),endpoint=False); out=np.zeros((int(n),3),float)
 for I,A,B in coeff:
  if I==0: out+=0.5*A[None,:]
  else: out+=np.cos(I*t)[:,None]*A[None,:]+np.sin(I*t)[:,None]*B[None,:]
 return out

def load_source(entry,workbench_root):
 p=Path(workbench_root)/entry['relative_source_path']; rep=entry['representation']
 if not p.exists(): raise FileNotFoundError(p)
 got=sha256(p)
 if got!=entry['raw_sha256']: raise RuntimeError(f'raw SHA mismatch for {entry["carrier_id"]}: {got}')
 if rep=='gilbert_ab_record': comps=[sample_coeff(x,4096) for x in find_gilbert_record(p,entry['topology_id'])]
 elif p.suffix.lower()=='.vect' or rep=='vect': comps=load_vect(p)
 else: comps=load_xyz(p)
 if len(comps)!=1: raise RuntimeError(f'v0.3.0 expects one component, got {len(comps)} for {entry["carrier_id"]}')
 return np.asarray(comps[0],float),p,got
