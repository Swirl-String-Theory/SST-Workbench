from __future__ import annotations
import math
import numpy as np
from .geometry import resample_closed_component


def unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if not np.isfinite(n) or n <= 0.0:
        raise ValueError("zero/invalid direction")
    return v / n


def transverse_basis(axis):
    n = unit(axis)
    seed = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
    e1 = unit(np.cross(n, seed))
    e2 = unit(np.cross(n, e1))
    return e1, e2


def fibonacci_directions(count, phase=0.0):
    """Nearly uniform unit directions; deterministic before the hidden global rotation."""
    count = max(1, int(count))
    ga = math.pi * (3.0 - math.sqrt(5.0))
    out = []
    for k in range(count):
        z = 1.0 - 2.0 * (k + 0.5) / count
        r = math.sqrt(max(0.0, 1.0 - z*z))
        a = phase + ga * k
        out.append([r*math.cos(a), r*math.sin(a), z])
    return np.asarray(out, dtype=float)


def secondary_direction(primary, angle_deg=60.0, phase=0.0):
    n = unit(primary)
    e1, e2 = transverse_basis(n)
    th = math.radians(float(angle_deg))
    t = math.cos(float(phase))*e1 + math.sin(float(phase))*e2
    return unit(math.cos(th)*n + math.sin(th)*t)


def hex_offsets(rings, radius):
    """Centered hexagonal cross-section: 1+3r(r+1) local thread legs."""
    rings = max(0, int(rings))
    radius = float(radius)
    vals=[]
    for q in range(-rings, rings+1):
        for s in range(-rings, rings+1):
            t=-q-s
            if max(abs(q),abs(s),abs(t)) <= rings:
                vals.append((q,s))
    pts=np.asarray(vals,dtype=float)
    # axial -> Cartesian triangular lattice
    x = pts[:,0] + 0.5*pts[:,1]
    y = (math.sqrt(3.0)/2.0)*pts[:,1]
    xy = np.c_[x,y]
    m = float(np.max(np.linalg.norm(xy,axis=1))) if len(xy)>1 else 1.0
    if m > 0:
        xy *= radius/m
    return xy

def _stadium_loop(center, axis, e_return, local_offset, half_length, return_distance,
                  local_leg_points=64, remote_leg_points=32, arc_points=32):
    """Smooth closed loop with an invariant local +axis leg and remote return.

    Crucially, the local-leg sampling is independent of `return_distance`; the
    return-flux convergence gate therefore changes only the remote closure, not the
    locally sampled vortex thread.
    """
    c=np.asarray(center,float); n=unit(axis); er=unit(e_return)
    d=np.asarray(local_offset,float)
    L=float(half_length); W=float(return_distance)
    if L <= 0 or W <= 0: raise ValueError("half_length and return_distance must be positive")
    nleg=max(12,int(local_leg_points)); nret=max(12,int(remote_leg_points)); narc=max(12,int(arc_points))
    z=np.linspace(-L,L,nleg,endpoint=False)
    leg1=c+d+z[:,None]*n
    th=np.linspace(0.0,math.pi,narc,endpoint=False)
    top=c+d + (L + 0.5*W*np.sin(th))[:,None]*n + (0.5*W*(1.0-np.cos(th)))[:,None]*er
    z2=np.linspace(L,-L,nret,endpoint=False)
    leg2=c+d+W*er+z2[:,None]*n
    th2=np.linspace(0.0,math.pi,narc,endpoint=False)
    bottom=c+d + (-L - 0.5*W*np.sin(th2))[:,None]*n + (0.5*W*(1.0+np.cos(th2)))[:,None]*er
    return np.vstack([leg1,top,leg2,bottom])


def make_local_thread_bundle(center, axis, rg, *, rings=1, bundle_radius_rg=1.5,
                             local_half_length_rg=4.0, return_distance_rg=24.0,
                             points_per_loop=None, local_leg_points=64, remote_leg_points=32,
                             arc_points=32, gamma_per_thread=0.01,
                             gradient_strength=0.0, gradient_phase=0.0,
                             return_phase=0.0):
    """Construct a source-anchored local patch of explicit closed vortex threads.

    This is the large-source-radius limit of radial source threads: over a
    particle-sized laboratory patch the Earth-like radial directions are effectively
    parallel. Each local +axis leg closes through a remote -axis return leg.
    Density gradients are circulation-weight gradients; no vortex filament terminates.
    """
    c=np.asarray(center,float); rg=float(rg); n=unit(axis)
    e1,e2=transverse_basis(n)
    er=unit(math.cos(float(return_phase))*e1 + math.sin(float(return_phase))*e2)
    eg=unit(math.cos(float(gradient_phase))*e1 + math.sin(float(gradient_phase))*e2)
    if points_per_loop is not None:
        # Backward-compatible compact knob; local leg gets half the budget.
        ppl=max(48,int(points_per_loop)); local_leg_points=max(local_leg_points,ppl//2)
        remote_leg_points=max(remote_leg_points,ppl//4); arc_points=max(arc_points,ppl//4)
    xy=hex_offsets(int(rings), float(bundle_radius_rg)*rg)
    loops=[]; gammas=[]; offsets_meta=[]
    for x,y in xy:
        d=x*e1+y*e2
        q=_stadium_loop(c,n,er,d,float(local_half_length_rg)*rg,float(return_distance_rg)*rg,
                        local_leg_points,remote_leg_points,arc_points)
        proj=float(np.dot(d,eg))/(max(float(bundle_radius_rg)*rg,1e-15))
        weight=max(0.05,1.0+float(gradient_strength)*proj)
        loops.append(q); gammas.append(float(gamma_per_thread)*weight); offsets_meta.append(d)
    offsets=[0]
    for q in loops: offsets.append(offsets[-1]+len(q))
    return {
        "points":np.vstack(loops).astype(float),
        "offsets":np.asarray(offsets,dtype=np.int64),
        "gammas":np.asarray(gammas,dtype=float),
        "axis":n,
        "return_direction":er,
        "gradient_direction":eg,
        "local_offsets":np.asarray(offsets_meta,dtype=float),
        "sampling":{"local_leg_points":int(local_leg_points),"remote_leg_points":int(remote_leg_points),"arc_points":int(arc_points)},
    }

def combine_bundles(*bundles):
    bundles=[b for b in bundles if b is not None and len(np.asarray(b.get("points",[])))>0]
    if not bundles:
        return {"points":np.zeros((0,3),float),"offsets":np.asarray([0],np.int64),"gammas":np.zeros(0,float)}
    pts=[]; gam=[]; offsets=[0]
    for b in bundles:
        p=np.asarray(b["points"],float); o=np.asarray(b["offsets"],np.int64); g=np.asarray(b["gammas"],float)
        if len(g) != len(o)-1: raise ValueError("bundle gamma/component mismatch")
        pts.append(p); gam.extend(g.tolist())
        for a,bb in zip(o[:-1],o[1:]): offsets.append(offsets[-1]+int(bb-a))
    return {"points":np.vstack(pts),"offsets":np.asarray(offsets,np.int64),"gammas":np.asarray(gam,float)}


def transform_bundle(bundle, R=None, translation=None, center=None):
    b={k:(np.array(v,copy=True) if isinstance(v,np.ndarray) else v) for k,v in bundle.items()}
    p=np.asarray(bundle["points"],float)
    if R is not None:
        R=np.asarray(R,float); c=np.zeros(3) if center is None else np.asarray(center,float)
        p=(p-c)@R.T+c
        for k in ("axis","return_direction","gradient_direction"):
            if k in b: b[k]=np.asarray(b[k],float)@R.T
        if "local_offsets" in b: b["local_offsets"]=np.asarray(b["local_offsets"],float)@R.T
    if translation is not None:
        p=p+np.asarray(translation,float)
    b["points"]=p
    return b


def closure_diagnostics(points, offsets):
    p=np.asarray(points,float); o=np.asarray(offsets,np.int64)
    close_local=[]; closing=[]; maxseg=0.0; minseg=float("inf")
    for a,b in zip(o[:-1],o[1:]):
        q=p[a:b]
        if len(q)<3: continue
        seg=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        neigh=np.r_[seg[:4],seg[-5:-1]] if len(seg)>=10 else seg[:-1]
        scale=max(float(np.max(neigh)) if len(neigh) else float(np.median(seg)),1e-300)
        close_local.append(float(seg[-1]/scale)); closing.append(float(seg[-1]))
        minseg=min(minseg,float(np.min(seg))); maxseg=max(maxseg,float(np.max(seg)))
    return {
        "component_count":int(max(0,len(o)-1)),
        "closing_edge_over_neighbor_max":float(max(close_local) if close_local else 0.0),
        "closing_edge_length_max":float(max(closing) if closing else 0.0),
        "segment_max_over_min_diagnostic":float(maxseg/max(minseg,1e-300)) if np.isfinite(minseg) else 0.0,
        "implicit_closed_polygon":True,
        "endpoint_count":0,
    }

