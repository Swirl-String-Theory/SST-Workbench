from __future__ import annotations
from pathlib import Path
import re
import numpy as np
from .model import CurveSet
from .geometry import resample_closed, canonicalize, canonical_phase_orientation

TWIST_ASSETS = {"4_1":"knot.4_1.fseries","5_2":"knot.5_2.fseries","6_1":"knot.6_1.fseries","7_2":"knot.7_2.fseries"}

def torus_knot(p:int,q:int,n=192,R=1.55,r=0.46):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    c=np.c_[(R+r*np.cos(q*t))*np.cos(p*t),(R+r*np.cos(q*t))*np.sin(p*t),r*np.sin(q*t)]
    return CurveSet.from_components([c])

def torus_link_3_3(n=160,R=1.55,r=0.46):
    # T(3,3): 3 components, each a T(1,1) unknot; pairwise linked on one torus.
    comps=[];t=np.linspace(0,2*np.pi,n,endpoint=False)
    for k in range(3):
        ph=2*np.pi*k/3
        c=np.c_[(R+r*np.cos(t+ph))*np.cos(t),(R+r*np.cos(t+ph))*np.sin(t),r*np.sin(t+ph)]
        comps.append(c)
    return CurveSet.from_components(comps)

def parse_fseries(path:Path,n=192,harmonic_start=1):
    rows=[];comments=[]
    for raw in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=raw.strip()
        if not s: continue
        if s.startswith('%') or s.startswith('#'):
            comments.append(s.lstrip('%# ').strip()); continue
        vals=[]
        for x in s.replace(',',' ').split():
            try: vals.append(float(x))
            except ValueError: pass
        if len(vals)>=6: rows.append(vals[:6])
    if not rows: raise ValueError(f'No 6-column Fourier rows in {path}')
    t=np.linspace(0,2*np.pi,max(n,1024),endpoint=False);xyz=np.zeros((len(t),3))
    for j,row in enumerate(rows,start=harmonic_start):
        ax,bx,ay,by,az,bz=row;c=np.cos(j*t);s=np.sin(j*t)
        xyz[:,0]+=ax*c+bx*s;xyz[:,1]+=ay*c+by*s;xyz[:,2]+=az*c+bz*s
    return CurveSet.from_components([resample_closed(xyz,n)]),comments

def clean_carrier(cs:CurveSet,n=192):
    cs,_=canonicalize(CurveSet.from_components([resample_closed(c,max(n,512)) for c in cs.components()]),1.0)
    return CurveSet.from_components([resample_closed(canonical_phase_orientation(c),n) for c in cs.components()])

def find_thread_axis(cs:CurveSet,core=0.035,n_dirs=180):
    # Blind geometric axis search: no topology label or target value is used.
    # Candidate axes are Fibonacci-sphere directions through the carrier centroid.
    ga=np.pi*(3-np.sqrt(5));best=None
    for i in range(n_dirs):
        z=1-2*(i+.5)/n_dirs;rr=np.sqrt(max(0.,1-z*z));ph=i*ga;axis=np.array([rr*np.cos(ph),rr*np.sin(ph),z])
        x=cs.points-cs.points.mean(0);rad=np.linalg.norm(x-np.outer(x@axis,axis),axis=1);clear=float(np.min(rad))
        if clear<max(3.2*core,0.11):continue
        probe=threaded_racetrack(axis,(0.,0.),1.0,max(.5*core,.015),2.6,3.4,96)
        # Inline midpoint Gauss-link estimate to avoid a circular import.
        a=cs.components()[0];a2=np.roll(a,-1,axis=0);b=probe;b2=np.roll(b,-1,axis=0);ma=.5*(a+a2);mb=.5*(b+b2);da=a2-a;db=b2-b;tot=0.
        for j in range(len(a)):
            rv=ma[j]-mb;den=np.maximum(np.linalg.norm(rv,axis=1)**3,1e-18);tot+=np.sum(np.einsum('ij,ij->i',rv,np.cross(da[j][None,:],db))/den)
        lk=float(tot/(4*np.pi));nearest=round(lk);integer_res=abs(lk-nearest);valid=(abs(nearest)>=1 and integer_res<.12)
        score=(1 if valid else 0, clear, -integer_res, -abs(nearest))
        if best is None or score>best[0]:best=(score,axis,lk,clear)
    if best is None:return np.array([0.,0.,1.]),0.0,hole_clearance(cs,np.array([0.,0.,1.]))
    return best[1],best[2],best[3]

def carrier_catalog(asset_root:Path,n=192):
    out={}
    for q in (3,5,7,9):
        out[f'TORUS_T2_{q}']={'family':'torus','geometry':clean_carrier(torus_knot(2,q,max(n,512)),n),'source':'analytic T(2,q)','hole_axis':[0,0,1]}
    for kid,fn in TWIST_ASSETS.items():
        p=Path(asset_root)/fn
        cs,comments=parse_fseries(p,max(n,512),1)
        provenance=' '.join(comments).lower()
        bad=any(x in provenance for x in ('must be checked','converted to 6-column','data source: brian gilbert','fourier projection'))
        geom=clean_carrier(cs,n);axis,lk,clr=find_thread_axis(geom)
        out[f'TWIST_{kid}']={'family':'twist','geometry':geom,'source':fn,'source_qualified':not bad,'comments':comments,'hole_axis':axis.tolist(),'axis_probe_gauss_link':lk,'axis_probe_clearance':clr}
    out['TRIPLE_GEAR_T3_3']={'family':'triple_gear','geometry':clean_carrier(torus_link_3_3(max(n,512)),n),'source':'analytic T(3,3) three-unknot-link proxy','hole_axis':[0,0,1],'mechanical_proxy_only':True}
    return out

def hole_clearance(cs:CurveSet,axis=np.array([0.,0.,1.])):
    axis=np.asarray(axis,float);axis/=np.linalg.norm(axis)
    x=cs.points-cs.points.mean(0);rad=np.linalg.norm(x-np.outer(x@axis,axis),axis=1)
    return float(np.quantile(rad,0.08))

def _orthobasis(axis):
    n=np.asarray(axis,float);n/=np.linalg.norm(n)
    a=np.array([1.,0.,0.]) if abs(n[0])<0.8 else np.array([0.,1.,0.])
    e1=a-n*np.dot(a,n);e1/=np.linalg.norm(e1);e2=np.cross(n,e1)
    return e1,e2,n

def threaded_racetrack(axis=(0,0,1),offset=(0,0),helix_turns=1.0,central_radius=0.04,L=2.5,return_radius=3.3,n=96):
    """Closed thread loop: a central helical pass plus a far return leg.
    It has no endpoints; the far return keeps div(omega)=0 in the filament model.
    """
    e1,e2,ez=_orthobasis(axis);u,v=offset
    base=u*e1+v*e2
    n1=max(16,n//2);z=np.linspace(-L,L,n1,endpoint=False);ph=2*np.pi*helix_turns*(z+L)/(2*L)
    # Integer helix_turns makes start/end phase identical, so the central pass
    # closes smoothly into the two far-return bridges.
    central=base+z[:,None]*ez+central_radius*(np.cos(ph)[:,None]*e1+np.sin(ph)[:,None]*e2)
    x0=central_radius
    side_x=return_radius
    rad=.5*(side_x-x0);cx=.5*(side_x+x0)
    n2=max(8,n//8);ang=np.linspace(np.pi,0,n2,endpoint=False)
    top=base+(cx+rad*np.cos(ang))[:,None]*e1+(L+rad*np.sin(ang))[:,None]*ez
    n3=max(16,n//4);zr=np.linspace(L,-L,n3,endpoint=False);ret=base+side_x*e1+zr[:,None]*ez
    ang2=np.linspace(0,-np.pi,n2,endpoint=False)
    bot=base+(cx+rad*np.cos(ang2))[:,None]*e1+(-L+rad*np.sin(ang2))[:,None]*ez
    c=np.vstack([central,top,ret,bot])
    return resample_closed(c,n)

def make_thread_bundle(carrier:CurveSet,n_threads=3,helix_turns=1.0,n=96,axis=(0,0,1),core=0.035):
    clear=hole_clearance(carrier,np.asarray(axis,float));bundle_r=max(2.8*core,min(0.30*clear,0.18))
    comps=[]
    if n_threads<=1: offsets=[(0.,0.)]
    else:
        offsets=[(bundle_r*np.cos(2*np.pi*k/n_threads),bundle_r*np.sin(2*np.pi*k/n_threads)) for k in range(n_threads)]
    for off in offsets: comps.append(threaded_racetrack(axis,off,helix_turns,max(1.2*core,0.018),2.6,3.4,n))
    return CurveSet.from_components(comps),{'hole_clearance':clear,'bundle_radius':bundle_r}

def combine(carrier:CurveSet,threads:CurveSet):
    return CurveSet.from_components(carrier.components()+threads.components())
