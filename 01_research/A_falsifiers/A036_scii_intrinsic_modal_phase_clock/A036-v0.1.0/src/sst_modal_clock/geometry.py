from pathlib import Path
import re
import numpy as np
EXTS={'.txt','.xyz','.csv','.dat','.pts'}

def read_xyz(path):
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
    if len(a)>2 and np.linalg.norm(a[0]-a[-1])<1e-10*max(1.0,float(np.ptp(a,axis=0).max())): a=a[:-1]
    if len(a)<16: raise ValueError(f'{path}: fewer than 16 XYZ points')
    return a

def read_xyz_components(path):
    """Read plain XYZ while preserving blank/component-separated link strings."""
    blocks=[]; cur=[]
    def flush():
        nonlocal cur
        if len(cur)>=3: blocks.append(np.asarray(cur,float))
        cur=[]
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        raw=line.strip()
        if not raw:
            if cur: flush()
            continue
        low=raw.lower()
        if low.startswith(('comp','component','string')) and not re.match(r'^[+-.0-9]',raw):
            if cur: flush()
            continue
        s=raw.replace(',',' ')
        if s.startswith(('#','//',';')): continue
        vals=[]
        for tok in s.split():
            try: vals.append(float(tok))
            except ValueError: pass
        if len(vals)>=3 and np.isfinite(vals[:3]).all(): cur.append(vals[:3])
    if cur: flush()
    good=[]
    for a in blocks:
        if len(a)>2 and np.linalg.norm(a[0]-a[-1])<1e-10*max(1.0,float(np.ptp(a,axis=0).max())): a=a[:-1]
        if len(a)>=16: good.append(a)
    if not good:
        a=read_xyz(path); return [a]
    return good

def discover(root,source_regex=None):
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(root)
    rx=re.compile(source_regex,re.I) if source_regex else None; out=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in EXTS: continue
        if rx and not rx.search(p.name): continue
        try: out.append((p,read_xyz(p)))
        except Exception: pass
    if not out: raise RuntimeError(f'No parseable centerlines found under {root}' + (f' matching {source_regex}' if source_regex else ''))
    return out

def resample_closed(x,n):
    x=np.asarray(x,float); y=np.vstack([x,x[0]])
    ds=np.linalg.norm(np.diff(y,axis=0),axis=1); s=np.r_[0.,np.cumsum(ds)]; L=s[-1]
    if L<=1e-15: raise ValueError('degenerate closed curve')
    tgt=np.linspace(0,L,n,endpoint=False); out=np.empty((n,3))
    for d in range(3): out[:,d]=np.interp(tgt,s,y[:,d])
    return out

def component_offsets_from_lengths(lengths):
    return np.asarray([0,*np.cumsum([int(x) for x in lengths])],dtype=np.int64)

def normalize_offsets(offsets,n):
    if offsets is None: return np.asarray([0,int(n)],dtype=np.int64)
    o=np.asarray(offsets,dtype=np.int64).ravel()
    if len(o)<2 or int(o[0])!=0 or int(o[-1])!=int(n) or np.any(np.diff(o)<3): raise ValueError('invalid component_offsets')
    return o

def component_slices(offsets,n=None):
    o=normalize_offsets(offsets,int(n if n is not None else np.asarray(offsets)[-1]))
    return [slice(int(a),int(b)) for a,b in zip(o[:-1],o[1:])]

def next_prev_indices(n,offsets=None):
    o=normalize_offsets(offsets,n); nxt=np.arange(n,dtype=np.int64)+1; prv=np.arange(n,dtype=np.int64)-1
    for a,b in zip(o[:-1],o[1:]):
        a=int(a);b=int(b);nxt[b-1]=a;prv[a]=b-1
    return nxt,prv

def flatten_components(components,n_per_component=None):
    cs=[]
    for c in components:
        c=np.asarray(c,float)
        if n_per_component is not None: c=resample_closed(c,int(n_per_component))
        cs.append(c)
    if not cs: raise ValueError('no components')
    return np.vstack(cs),component_offsets_from_lengths([len(c) for c in cs])

def resample_components_flat(x,offsets,n_per_component=None):
    x=np.asarray(x,float); o=normalize_offsets(offsets,len(x)); out=[]
    for s in component_slices(o,len(x)):
        n=int(n_per_component if n_per_component is not None else s.stop-s.start); out.append(resample_closed(x[s],n))
    return flatten_components(out,None)

def centroid(x): return np.mean(np.asarray(x,float),axis=0)
def radius_gyration(x):
    y=np.asarray(x,float)-centroid(x); return float(np.sqrt(np.mean(np.sum(y*y,axis=1))))
def normalize(x):
    y=np.asarray(x,float)-centroid(x); rg=radius_gyration(y)
    if rg<=1e-15: raise ValueError('degenerate geometry')
    return y/rg,rg

def normalize_components(components,n_per_component):
    x,o=flatten_components(components,n_per_component); y,rg=normalize(x); return y,o,rg

def tangents(x,offsets=None):
    x=np.asarray(x,float); nxt,prv=next_prev_indices(len(x),offsets); t=x[nxt]-x[prv]; n=np.linalg.norm(t,axis=1);n[n<1e-15]=1.;return t/n[:,None]
def radial_normal(x,offsets=None):
    x=np.asarray(x,float); t=tangents(x,offsets); r=x-centroid(x); n=r-(r*t).sum(1)[:,None]*t; nn=np.linalg.norm(n,axis=1)
    bad=nn<1e-10
    if bad.any():
        nxt,prv=next_prev_indices(len(x),offsets); c=t[nxt]-t[prv]; n[bad]=c[bad]; nn=np.linalg.norm(n,axis=1)
    nn[nn<1e-15]=1.; return n/nn[:,None]
def remove_tangent(v,x,offsets=None):
    t=tangents(x,offsets); return v-(v*t).sum(1)[:,None]*t

def remove_rigid(v,x):
    x=np.asarray(x,float)-centroid(x); v=np.asarray(v,float); v=v-v.mean(0)
    A=[]; b=[]
    for r,u in zip(x,v):
        rx,ry,rz=r; A.extend([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]]); b.extend(u.tolist())
    A=np.asarray(A,float); b=np.asarray(b,float); om=np.linalg.lstsq(A,b,rcond=None)[0]
    rot=np.cross(np.broadcast_to(om,x.shape),x)
    return v-rot

def broadband_probe(x,harmonics=(1,2,3,4),offsets=None):
    x=np.asarray(x,float); o=normalize_offsets(offsets,len(x)); t=tangents(x,o); n1=radial_normal(x,o); n2=np.cross(t,n1); nn=np.linalg.norm(n2,axis=1);nn[nn<1e-15]=1.;n2=n2/nn[:,None];v=np.zeros_like(x)
    for ci,s in enumerate(component_slices(o,len(x))):
        n=s.stop-s.start; th=2*np.pi*np.arange(n)/n; a=np.zeros(n);b=np.zeros(n)
        for m in harmonics:
            a+=np.cos(m*th+0.37*m+0.19*ci)/(m**1.25);b+=np.sin(m*th+0.61*m+0.13*ci)/(m**1.25)
        v[s]=a[:,None]*n1[s]+b[:,None]*n2[s]
    v=remove_tangent(remove_rigid(v,x),x,o);rms=np.sqrt(np.mean(np.sum(v*v,axis=1)))
    if rms<1e-15: raise ValueError('degenerate broadband probe')
    return v/rms

def kabsch_align(y,ref):
    y=np.asarray(y,float); ref=np.asarray(ref,float); yc=y-y.mean(0); rc=ref-ref.mean(0);H=yc.T@rc;U,S,Vt=np.linalg.svd(H);R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1;R=U@Vt
    return yc@R

def _best_cyclic_shift(aligned,ref):
    a=np.asarray(aligned,float)-np.mean(aligned,axis=0);b=np.asarray(ref,float)-np.mean(ref,axis=0);score=np.zeros(len(a),float)
    for d in range(3): score+=np.fft.ifft(np.conj(np.fft.fft(a[:,d]))*np.fft.fft(b[:,d])).real
    return int(np.argmax(score))

def _phase_align_components(cur,ref,offsets):
    cur=np.asarray(cur,float).copy();ref=np.asarray(ref,float);o=normalize_offsets(offsets,len(cur))
    # Component labels are preserved; only cyclic parameter origins are gauge.
    for s in component_slices(o,len(cur)):
        a=cur[s]-np.mean(cur[s],axis=0);b=ref[s]-np.mean(ref[s],axis=0);sa=np.linalg.norm(a,axis=1);sb=np.linalg.norm(b,axis=1)
        score=np.fft.ifft(np.fft.fft(sa)*np.conj(np.fft.fft(sb))).real;cur[s]=np.roll(cur[s],-int(np.argmax(score)),axis=0)
    return cur

def canonical_arclength_align(y,ref,iterations=2,offsets=None):
    ref=np.asarray(ref,float);o=normalize_offsets(offsets,len(ref));cur,_=resample_components_flat(np.asarray(y,float),o,None);rr,_=resample_components_flat(ref,o,None);cur=_phase_align_components(cur,rr,o)
    for _ in range(max(1,int(iterations))):
        a=kabsch_align(cur,rr);changed=False
        for s in component_slices(o,len(cur)):
            sh=_best_cyclic_shift(a[s],rr[s])
            if sh: cur[s]=np.roll(cur[s],-sh,axis=0);changed=True
        if not changed: break
    return kabsch_align(cur,rr)

def aligned_normal_displacement(y,ref,parameterization_invariant=True,offsets=None):
    ref=np.asarray(ref,float);o=normalize_offsets(offsets,len(ref));rr,_=resample_components_flat(ref,o,None);aligned=canonical_arclength_align(y,rr,offsets=o) if parameterization_invariant else kabsch_align(y,rr);return remove_tangent(aligned-rr,rr,o)

def tangential_redistribution_velocity(x,rate=2.0,method='segment_feedback',offsets=None):
    x=np.asarray(x,float);o=normalize_offsets(offsets,len(x));t=tangents(x,o);u=np.zeros_like(x);method=str(method)
    for s in component_slices(o,len(x)):
        xx=x[s];tt=t[s];n=len(xx)
        if method=='target_projection':
            target=resample_closed(xx,n);d=target-xx;u[s]=float(rate)*(np.sum(d*tt,axis=1)[:,None]*tt);continue
        if method!='segment_feedback': raise ValueError(f'unknown mesh_redistribution_method={method}')
        ds=np.linalg.norm(np.roll(xx,-1,axis=0)-xx,axis=1);err=ds-float(np.mean(ds));alpha=np.zeros(n,float)
        if n>1: alpha[1:]=-float(rate)*np.cumsum(err[:-1])
        alpha-=float(np.mean(alpha));u[s]=alpha[:,None]*tt
    return u

def synthetic_trefoil(n=192):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]
