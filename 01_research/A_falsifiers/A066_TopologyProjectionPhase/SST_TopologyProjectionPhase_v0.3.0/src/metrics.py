"""Blind metrics for cross-domain topology/projection/phase tests.
No truth labels, simulator IDs or private metadata are read.
"""
from __future__ import annotations
import numpy as np


def winding_charges(re: np.ndarray, im: np.ndarray) -> list[tuple[int,int,int]]:
    """Integer lattice-plaquette phase winding; returns (j, i, charge)."""
    z = re.astype(np.float64) + 1j*im.astype(np.float64)
    a, b, c, d = z[:-1,:-1],z[:-1,1:],z[1:,1:],z[1:,:-1]
    # Closed plaquette: four principal angle differences.
    w = np.angle(b*np.conj(a))+np.angle(c*np.conj(b))+np.angle(d*np.conj(c))+np.angle(a*np.conj(d))
    q = np.rint(w/(2*np.pi)).astype(int)
    js,is_ = np.where(q!=0)
    return [(int(j),int(i),int(q[j,i])) for j,i in zip(js,is_)]


def segment_plane_hits(curve: np.ndarray, z0: float=0.) -> np.ndarray:
    """Exact signed segment/plane crossing points for a polygonal CLOSED 3D loop.
    Tangential zero endpoints are intentionally excluded (ambiguous); tests bracket them.
    """
    p=np.asarray(curve, dtype=float)
    zz=p[:,2]-z0
    nxt=np.roll(p,-1,axis=0)
    zz2=np.roll(zz,-1)
    indices=np.flatnonzero((zz<0)&(zz2>0) | (zz>0)&(zz2<0))
    points=[]
    for i in indices:
        f=-zz[i]/(zz2[i]-zz[i])
        points.append(p[i]+f*(nxt[i]-p[i]))
    return np.asarray(points,dtype=float).reshape((-1,3))


def plane_hits(filaments: np.ndarray, present: np.ndarray, t: int) -> np.ndarray:
    pts=[segment_plane_hits(filaments[t,j]) for j in range(present.shape[1]) if present[t,j]]
    if not pts:return np.empty((0,3))
    return np.concatenate(pts,axis=0)


def closed_polygon_diagnostic(curve: np.ndarray) -> dict:
    p=np.asarray(curve,dtype=float)
    seg=np.roll(p,-1,axis=0)-p
    lengths=np.linalg.norm(seg,axis=1)
    return {"length":float(lengths.sum()),"min_segment_length":float(lengths.min()),"max_segment_length":float(lengths.max()),"finite":bool(np.isfinite(p).all()),"N":len(p)}


def characteristic_projection_velocity(x1: np.ndarray, x2: np.ndarray, t: np.ndarray) -> dict:
    """Fit R^2=A*(t*-t)+B*(t*-t)^2 using only valid paired slice intersections."""
    times=[]; square=[]; separations=[]
    for idx,(aa,bb) in enumerate(zip(x1,x2)):
        if np.isfinite(aa) and np.isfinite(bb):
            r=abs(aa-bb);times.append(t[idx]);square.append(r*r);separations.append(r)
    if len(times)<4:return {"status":"UNRESOLVED","n":len(times)}
    coef=np.polyfit(times,square,1)
    fit=np.polyval(coef,times)
    sst=float(1.0- np.sum((np.asarray(square)-fit)**2)/(np.sum((np.asarray(square)-np.mean(square))**2)+1e-30))
    return {"status":"QUALIFIED" if coef[0]<0 and sst>0.99 else "FAILED", "n":len(times),"slope_R2_per_t":float(coef[0]),"R2_linear":sst}


def analyze_arrays(d: dict) -> dict:
    required={"t","re","im","filaments","present","gamma","x","y"}
    missing=sorted(required-set(d))
    if missing:raise ValueError(f"missing observable arrays: {missing}")
    t,re,im=np.asarray(d['t']),np.asarray(d['re']),np.asarray(d['im'])
    fil,pres,gamma=np.asarray(d['filaments']),np.asarray(d['present']),np.asarray(d['gamma'])
    if t.ndim!=1 or re.shape!=im.shape or re.shape[0]!=len(t) or re.ndim!=3:
        raise ValueError('invalid time/phase dimensions')
    if fil.ndim!=4 or fil.shape[0]!=len(t) or fil.shape[-1]!=3 or pres.shape!=fil.shape[:2] or gamma.shape!=pres.shape:
        raise ValueError('invalid 3D observability dimensions')
    if not np.all(np.diff(t)>0):raise ValueError('nonmonotonic time grid')
    if not np.all(np.isfinite(re)) or not np.all(np.isfinite(im)) or not np.all(np.isfinite(fil[pres])):
        raise ValueError('nonfinite active observations')
    if np.any(np.sum(pres,axis=1)==0):raise ValueError('3D acquisition coverage gap')
    pre=int(np.flatnonzero(t<0)[-2]);post=int(np.flatnonzero(t>0)[1])
    q_pre=winding_charges(re[pre],im[pre]);q_post=winding_charges(re[post],im[post]);
    l_pre=int(pres[pre].sum());l_post=int(pres[post].sum())
    vpre=float(np.sum(gamma[pre,pres[pre]]));vpost=float(np.sum(gamma[post,pres[post]]))
    hits=np.array([len(plane_hits(fil,pres,j)) for j in range(len(t))])
    # Principal 3D evidence must dominate phase morphology.
    if l_pre!=l_post:
        cls='THREED_CONNECTIVITY_CHANGE_CANDIDATE'
        physically_qualified=False
    elif hits[pre]>=2 and hits[post]==0:
        cls='TWO_D_SECTION_TANGENCY'
        physically_qualified=True
    elif hits[pre]==0 and hits[post]==0:
        cls='PHASE_PATTERN_NO_MATERIAL_PAIR'
        physically_qualified=True
    else:
        cls='UNRESOLVED'
        physically_qualified=False
    xs1=np.full(len(t),np.nan);xs2=xs1.copy()
    for k in range(len(t)):
        h=plane_hits(fil,pres,k)
        if len(h)==2:
            xs1[k]=min(h[:,0]);xs2[k]=max(h[:,0])
    geometric_fit=characteristic_projection_velocity(xs1,xs2,t)
    curves=[closed_polygon_diagnostic(fil[k,j]) for k in [pre,post] for j in range(pres.shape[1]) if pres[k,j]]
    g0=all(c['finite'] and c['min_segment_length']>1e-8 for c in curves)
    g1=len(q_pre)>=2 and sum(q for _,_,q in q_pre)==0 and len(q_post)==0
    # Separate a successful mechanism classification from physical Euler admissibility.
    g2=(l_pre==l_post and abs(vpre-vpost)<1e-10)
    flags={
      'G00_OBSERVABILITY': 'PASS' if g0 else 'FAIL',
      'G01_PHASE_PAIR_ANNIHILATION':'PASS' if g1 else 'FAIL',
      'G02_MATERIAL_TOPOLOGY_INVARIANTS':'PASS' if g2 else 'FAIL_NONIDEAL_OR_GEOMETRY_INCOMPLETE',
      'G03_THREE_WAY_MECHANISM':'PASS' if cls!='UNRESOLVED' else 'UNRESOLVED',
      'G04_PROJECTION_FOLD':'PASS' if cls=='TWO_D_SECTION_TANGENCY' and geometric_fit['status']=='QUALIFIED' else ('NOT_APPLICABLE' if cls!='TWO_D_SECTION_TANGENCY' else 'FAIL'),
      'G05_PHYSICAL_RECONNECTION':'UNRESOLVED_NO_NONIDEAL_PDE',
      'G06_PKL_SA_DYNAMIC_CERTIFICATION':'UNRESOLVED_NO_QUALIFIED_TRAJECTORY',
      'G07_REAL_WORLD_REPLICATION':'UNRESOLVED_SYNTHETIC_ONLY'
    }
    return {"prediction":cls,"predicted_physical_status":"UNQUALIFIED" if not physically_qualified else "SYNTHETIC_GEOMETRY_ONLY",
            "time_pre":float(t[pre]),"time_post":float(t[post]),"phase_charges_pre":[int(q) for _,_,q in q_pre],
            "phase_charges_post":[int(q) for _,_,q in q_post],"component_counts_pre_post":[l_pre,l_post],
            "slice_hits":hits.tolist(),"signed_gamma_pre_post":[vpre,vpost],"projection_fold":geometric_fit,
            "geometry_checks":curves,"gates":flags}
