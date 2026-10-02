from __future__ import annotations
import numpy as np

EPS=1e-14

def closed_edges(c): return np.roll(c,-1,axis=0)-c

def arclength(c): return float(np.sum(np.linalg.norm(closed_edges(c),axis=1)))

def resample_closed(c,n):
    c=np.asarray(c,float); e=closed_edges(c); ds=np.linalg.norm(e,axis=1); s=np.r_[0.0,np.cumsum(ds)]; L=float(s[-1])
    if L<=0 or not np.isfinite(L): raise ValueError('degenerate closed curve')
    q=np.arange(int(n),dtype=float)*L/int(n); cp=np.vstack([c,c[0]]); out=np.empty((int(n),3),float)
    for i,x in enumerate(q):
        j=min(max(int(np.searchsorted(s,x,side='right')-1),0),len(c)-1); u=(x-s[j])/max(ds[j],EPS); out[i]=(1-u)*cp[j]+u*cp[j+1]
    return out

def torus_knot(p,q,n=384,R=1.55,r=0.46):
    t=np.linspace(0,2*np.pi,int(n),endpoint=False)
    return np.c_[(R+r*np.cos(q*t))*np.cos(p*t),(R+r*np.cos(q*t))*np.sin(p*t),r*np.sin(q*t)]

def torus_link_3_3(n=320,R=1.55,r=0.46):
    t=np.linspace(0,2*np.pi,int(n),endpoint=False); out=[]
    for j in range(3):
        ph=2*np.pi*j/3
        out.append(np.c_[(R+r*np.cos(t+ph))*np.cos(t),(R+r*np.cos(t+ph))*np.sin(t),r*np.sin(t+ph)])
    return out

def parse_fseries(path,n=384,harmonic_start=1):
    rows=[];comments=[]
    for raw in open(path,encoding='utf-8',errors='ignore'):
        s=raw.strip()
        if not s: continue
        if s.startswith('%') or s.startswith('#'): comments.append(s.lstrip('%# ').strip()); continue
        vals=[]
        for x in s.replace(',',' ').split():
            try: vals.append(float(x))
            except ValueError: pass
        if len(vals)>=6: rows.append(vals[:6])
    if not rows: raise ValueError(f'no Fourier rows in {path}')
    t=np.linspace(0,2*np.pi,max(int(n),2048),endpoint=False); xyz=np.zeros((len(t),3))
    for j,row in enumerate(rows,start=int(harmonic_start)):
        ax,bx,ay,by,az,bz=row; co=np.cos(j*t); si=np.sin(j*t)
        xyz[:,0]+=ax*co+bx*si; xyz[:,1]+=ay*co+by*si; xyz[:,2]+=az*co+bz*si
    return resample_closed(xyz,int(n)),comments

def canonicalize(c):
    c=np.asarray(c,float)-np.mean(c,axis=0); C=c.T@c/len(c); w,V=np.linalg.eigh(C); V=V[:,np.argsort(w)[::-1]]
    if np.linalg.det(V)<0: V[:,-1]*=-1
    c=c@V
    scale=np.sqrt(np.mean(np.sum(c*c,axis=1)))
    c=c/max(scale,EPS)
    # deterministic sign gauge
    for ax in range(3):
        k=np.argmax(np.abs(c[:,ax]));
        if c[k,ax]<0: c[:,ax]*=-1
    return c

def carrier_catalog(asset_root,n=384):
    out={}
    for q in (3,5,7,9): out[f'TORUS_T2_{q}']={'family':'torus','components':[canonicalize(resample_closed(torus_knot(2,q,max(n,768)),n))],'source':f'analytic T(2,{q})'}
    for kid in ('4_1','5_2','7_2'):
        c,comments=parse_fseries(f'{asset_root}/knot.{kid}.fseries',max(n,768),1); prov=' '.join(comments).lower(); bad=any(x in prov for x in ('must be checked','converted to 6-column','data source: brian gilbert','fourier projection'))
        out[f'TWIST_{kid}']={'family':'twist','components':[canonicalize(resample_closed(c,n))],'source':f'Fremlin knot.{kid}.fseries','source_qualified':not bad,'comments':comments}
    comps=torus_link_3_3(max(n,640)); out['TRIPLE_GEAR_T3_3']={'family':'triple_gear','components':[canonicalize(resample_closed(c,n)) for c in comps],'source':'analytic T(3,3) three-unknot-link proxy'}
    return out

def unit_tangents(c):
    c=np.asarray(c,float); d=np.roll(c,-1,axis=0)-np.roll(c,1,axis=0); n=np.linalg.norm(d,axis=1); return d/np.maximum(n[:,None],EPS)

def curvature(c):
    c=resample_closed(c,len(c)); L=arclength(c); ds=L/len(c); t=unit_tangents(c); dt=np.roll(t,-1,axis=0)-np.roll(t,1,axis=0); return np.linalg.norm(dt,axis=1)/(2*ds)

def _rotation_axis_angle(v,axis,ang):
    axis=np.asarray(axis,float); na=np.linalg.norm(axis)
    if na<EPS: return np.asarray(v,float)
    a=axis/na; v=np.asarray(v,float); return v*np.cos(ang)+np.cross(a,v)*np.sin(ang)+a*np.dot(a,v)*(1-np.cos(ang))

def bishop_holonomy(c):
    """Parallel-transport a normal around the closed polygon and return holonomy angle."""
    t=unit_tangents(c); t0=t[0]; seed=np.array([1.,0.,0.]) if abs(t0[0])<.8 else np.array([0.,1.,0.]); n0=seed-t0*np.dot(seed,t0); n0/=np.linalg.norm(n0); n=n0.copy()
    for i in range(len(t)):
        a=t[i]; b=t[(i+1)%len(t)]; cr=np.cross(a,b); sn=np.linalg.norm(cr); cs=float(np.clip(np.dot(a,b),-1,1))
        if sn>1e-12: n=_rotation_axis_angle(n,cr/sn,np.arctan2(sn,cs))
        # numerical re-projection
        n=n-b*np.dot(n,b); n/=max(np.linalg.norm(n),EPS)
    # compare around t0
    x=float(np.dot(n,n0)); y=float(np.dot(t0,np.cross(n0,n))); return float(np.arctan2(y,x))

def geometry_stats(components):
    Ls=np.array([arclength(c) for c in components],float); ks=np.concatenate([curvature(c) for c in components]); hol=np.array([bishop_holonomy(c) for c in components],float)
    return {'length_total':float(Ls.sum()),'length_components':Ls.tolist(),'curvature_rms':float(np.sqrt(np.mean(ks*ks))),'curvature_max':float(np.max(ks)),'bend_radius_min':float(1/max(np.max(ks),EPS)),'bishop_holonomy_components':hol.tolist(),'bishop_holonomy_mean':float(np.angle(np.mean(np.exp(1j*hol))))}
