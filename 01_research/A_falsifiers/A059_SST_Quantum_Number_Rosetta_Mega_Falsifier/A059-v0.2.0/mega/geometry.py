from __future__ import annotations
from pathlib import Path, PureWindowsPath
import hashlib, math
import numpy as np
from .common import sha256_file


def resolve_source_path(locator: dict, workbench_root: Path) -> Path|None:
    raw=str(locator.get('source_path') or '')
    if not raw:return None
    p=Path(raw)
    if p.is_file():return p
    # canonical Windows path -> relative suffix after SST-Workbench
    wp=PureWindowsPath(raw)
    parts=list(wp.parts)
    try:i=[x.casefold() for x in parts].index('sst-workbench')
    except ValueError:return None
    q=workbench_root.joinpath(*parts[i+1:])
    return q if q.is_file() else None


def _xyz_lines(text:str) -> np.ndarray:
    pts=[]
    for line in text.splitlines():
        s=line.strip()
        if not s or s.startswith(('#',';')):continue
        tok=s.replace(',',' ').split()
        if len(tok)<3:continue
        try:v=[float(tok[0]),float(tok[1]),float(tok[2])]
        except ValueError:continue
        if all(math.isfinite(x) for x in v):pts.append(v)
    if len(pts)<8:raise ValueError('too few xyz points')
    return np.asarray(pts,float)


def load_vect(path:Path) -> list[np.ndarray]:
    toks=path.read_text(encoding='utf-8',errors='ignore').split()
    if not toks or toks[0].upper()!='VECT':raise ValueError('not VECT')
    pos=1;ncomp=int(toks[pos]);nvert=int(toks[pos+1]);_ncol=int(toks[pos+2]);pos+=3
    counts=[int(toks[pos+i]) for i in range(ncomp)];pos+=ncomp
    pos+=ncomp # color counts
    comps=[]; remain=nvert
    for c in counts:
        n=abs(c); arr=[]
        for _ in range(n):
            arr.append([float(toks[pos]),float(toks[pos+1]),float(toks[pos+2])]);pos+=3
        comps.append(np.asarray(arr,float));remain-=n
    return comps


def load_geometry(locator:dict,workbench_root:Path) -> tuple[list[np.ndarray]|None,str]:
    p=resolve_source_path(locator,workbench_root)
    if p is None:return None,'source_path_unresolved'
    exp=locator.get('raw_sha256')
    if exp and sha256_file(p)!=exp:return None,'raw_sha256_mismatch'
    rep=locator.get('representation')
    try:
        if rep=='vect':return load_vect(p),'ok'
        if rep=='xyz':return [_xyz_lines(p.read_text(encoding='utf-8',errors='ignore'))],'ok'
        return None,'unsupported_representation_'+str(rep)
    except Exception as e:return None,f'parse_error:{type(e).__name__}:{e}'


def normalize_closed_curve(P:np.ndarray,nmax:int=900) -> np.ndarray:
    P=np.asarray(P,float)
    if len(P)>nmax:
        idx=np.linspace(0,len(P)-1,nmax,endpoint=False).astype(int);P=P[idx]
    P=P-P.mean(0)
    # scale total polygon length to one
    Q=np.vstack([P,P[0]])
    L=np.linalg.norm(np.diff(Q,axis=0),axis=1).sum()
    if L<=0:raise ValueError('zero length')
    return P/L


def fibonacci_sphere(n:int,radius:float) -> np.ndarray:
    i=np.arange(n,dtype=float);phi=(1+5**0.5)/2
    z=1-2*(i+0.5)/n;rr=np.sqrt(np.maximum(0,1-z*z));ang=2*np.pi*i/phi
    return radius*np.column_stack([rr*np.cos(ang),rr*np.sin(ang),z])


def biot_savart_probe(P:np.ndarray,gamma:float,probes:np.ndarray,core:float=0.003) -> np.ndarray:
    P=normalize_closed_curve(P)
    Q=np.vstack([P,P[0]])
    dl=np.diff(Q,axis=0);mid=0.5*(Q[:-1]+Q[1:])
    out=np.zeros((len(probes),3),float)
    for a in range(0,len(probes),32):
        X=probes[a:a+32,None,:]
        r=X-mid[None,:,:]
        den=(np.sum(r*r,axis=2)+core*core)**1.5
        c=np.cross(dl[None,:,:],r)
        out[a:a+32]=gamma/(4*np.pi)*np.sum(c/den[:,:,None],axis=1)
    return out


def relative_norm(a:np.ndarray,b:np.ndarray) -> float:
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))


def frame_holonomy(P:np.ndarray) -> float:
    # Discrete parallel transport of a normal around a closed polygon.
    P=normalize_closed_curve(P,nmax=1200)
    Q=np.vstack([P,P[0],P[1]])
    T=np.diff(Q,axis=0)
    T=T/np.linalg.norm(T,axis=1)[:,None]
    t0=T[0]
    basis=np.array([1.,0.,0.]) if abs(t0[0])<0.8 else np.array([0.,1.,0.])
    n=basis-t0*np.dot(basis,t0);n/=np.linalg.norm(n)
    n0=n.copy()
    for i in range(len(P)):
        a=T[i];b=T[i+1]
        v=np.cross(a,b);s=np.linalg.norm(v);c=float(np.clip(np.dot(a,b),-1,1))
        if s<1e-14:continue
        axis=v/s;theta=math.atan2(s,c)
        # Rodrigues rotate n by minimal tangent transport
        n=n*math.cos(theta)+np.cross(axis,n)*math.sin(theta)+axis*np.dot(axis,n)*(1-math.cos(theta))
        n=n-b*np.dot(n,b); nn=np.linalg.norm(n)
        if nn>0:n/=nn
    # Compare transported normal to initial normal around t0.
    n=n-t0*np.dot(n,t0);n/=np.linalg.norm(n)
    x=float(np.clip(np.dot(n0,n),-1,1));y=float(np.dot(t0,np.cross(n0,n)))
    return math.atan2(y,x)
