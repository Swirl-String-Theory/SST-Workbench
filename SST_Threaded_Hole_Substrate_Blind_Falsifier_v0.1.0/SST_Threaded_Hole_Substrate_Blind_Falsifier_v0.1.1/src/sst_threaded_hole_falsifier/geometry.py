from __future__ import annotations
import numpy as np
from .model import CurveSet

EPS = 1e-14

def closed_edges(c):
    return np.roll(c, -1, axis=0) - c

def closed_lengths(c):
    return np.linalg.norm(closed_edges(c), axis=1)

def arclength(c):
    return float(np.sum(closed_lengths(c)))

def resample_closed(c, n):
    c = np.asarray(c, float)
    ds = closed_lengths(c)
    s = np.r_[0.0, np.cumsum(ds)]
    L = float(s[-1])
    if not np.isfinite(L) or L <= 0:
        raise ValueError("degenerate closed curve")
    targets = np.arange(n, dtype=float) * L / n
    cp = np.vstack([c, c[0]])
    out = np.empty((n, 3), float)
    for k, t in enumerate(targets):
        j = int(np.searchsorted(s, t, side="right") - 1)
        j = min(max(j, 0), len(c)-1)
        u = (t - s[j]) / max(ds[j], EPS)
        out[k] = (1-u)*cp[j] + u*cp[j+1]
    return out

def resample_curves(cs: CurveSet, n_per_component):
    return CurveSet.from_components([resample_closed(c, n_per_component) for c in cs.components()])

def canonical_phase_orientation(c):
    """Remove arbitrary closed-curve parameter origin and traversal direction.

    The anchor is the lexicographically largest (x,y,z) vertex in the already
    rigid-canonicalized geometry.  At that anchor, traversal direction is fixed
    by the sign of the dominant tangent component.  This is a numerical gauge
    convention only; it does not alter the embedded curve.
    """
    c=np.asarray(c,float).copy();n=len(c)
    if n<4:raise ValueError('closed curve needs at least four points')
    # Lexicographic maximum without a floating scoring coefficient.
    k=max(range(n),key=lambda i:(float(c[i,0]),float(c[i,1]),float(c[i,2])))
    c=np.roll(c,-k,axis=0)
    t=c[1]-c[-1]
    j=int(np.argmax(np.abs(t)))
    if t[j]<0:
        c=np.vstack([c[:1],c[:0:-1]])
    return c

def canonicalize(cs: CurveSet, rms_radius=1.0):
    x = cs.points.copy()
    center = x.mean(0)
    x -= center
    cov = x.T @ x / max(len(x), 1)
    vals, vecs = np.linalg.eigh(cov)
    V = vecs[:, np.argsort(vals)[::-1]]
    if np.linalg.det(V) < 0:
        V[:, -1] *= -1
    x = x @ V
    for j in range(3):
        k = int(np.argmax(np.abs(x[:, j])))
        if x[k, j] < 0:
            x[:, j] *= -1
            V[:, j] *= -1
    if np.linalg.det(V) < 0:
        x[:, -1] *= -1
        V[:, -1] *= -1
    r = float(np.sqrt(np.mean(np.sum(x*x, axis=1))))
    if r <= 0:
        raise ValueError("zero RMS radius")
    scale = rms_radius / r
    x *= scale
    return CurveSet(x, cs.offsets.copy()), {"center": center.tolist(), "rms_before": r, "scale": scale, "rotation": V.tolist()}

def tangents(c):
    d = np.roll(c, -1, axis=0) - np.roll(c, 1, axis=0)
    return d / np.maximum(np.linalg.norm(d, axis=1)[:, None], EPS)

def curvature_vector(c):
    # Uniform-arclength finite difference after resampling.
    ds = arclength(c) / len(c)
    return (np.roll(c, -1, axis=0) - 2*c + np.roll(c, 1, axis=0)) / max(ds*ds, EPS)

def curvature_spectrum(c):
    kv = curvature_vector(c)
    coeff = np.fft.rfft(kv, axis=0)
    power = np.sum(np.abs(coeff)**2, axis=1)
    if len(power):
        power[0] = 0.0
    return power

def high_mode_fraction(c, frac=0.35):
    p = curvature_spectrum(c)
    if len(p) <= 2 or np.sum(p) <= EPS:
        return 0.0
    cut = max(2, int(np.ceil(frac * (len(p)-1))))
    return float(np.sum(p[cut:]) / max(np.sum(p[1:]), EPS))

def curve_roughness(c):
    k = np.linalg.norm(curvature_vector(c), axis=1)
    dk = np.roll(k, -1) - k
    return float(np.sqrt(np.mean(dk*dk)) / max(np.mean(np.abs(k)), EPS))

def fit_rigid_velocity(x, v, tangents_field=None):
    """Least-squares rigid motion, optionally quotienting tangential marker gauge.

    With tangents_field present, solve only the normal-plane equations
    P_i v_i = P_i [U + Omega x r_i], P_i = I - t_i t_i^T.  This prevents
    arbitrary marker-sliding velocity from contaminating the fitted rigid body
    motion and therefore the relative-equilibrium residual.
    """
    x=np.asarray(x,float);v=np.asarray(v,float)
    xc = x - x.mean(0)
    rows=[];rhs=[]
    I=np.eye(3)
    for i,r in enumerate(xc):
        rx=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0.0]])
        A=np.c_[I,-rx]  # U + Omega x r = U - [r]_x Omega
        if tangents_field is not None:
            t=np.asarray(tangents_field[i],float);P=I-np.outer(t,t);A=P@A;vv=P@v[i]
        else:vv=v[i]
        rows.append(A);rhs.append(vv)
    q=np.linalg.lstsq(np.vstack(rows),np.concatenate(rhs),rcond=None)[0]
    U,Om=q[:3],q[3:]
    rigid=U+np.cross(np.broadcast_to(Om,x.shape),xc)
    return U,Om,rigid

def shape_velocity(cs: CurveSet, v):
    T = np.vstack([tangents(c) for c in cs.components()])
    U, Om, rigid = fit_rigid_velocity(cs.points, v, T)
    w = v - rigid
    w -= T * np.sum(w*T, axis=1)[:, None]
    return w, U, Om

def kabsch(moving, reference):
    A = moving - moving.mean(0)
    B = reference - reference.mean(0)
    H = A.T @ B
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    t = reference.mean(0) - moving.mean(0) @ R.T
    return R, t

def align_cyclic(reference: CurveSet, moving: CurveSet, iterations=3):
    if reference.n_components != moving.n_components:
        raise ValueError("component mismatch")
    comps = [c.copy() for c in moving.components()]
    shifts = [0]*moving.n_components
    for _ in range(iterations):
        mov = np.vstack(comps)
        R, tr = kabsch(mov, reference.points)
        aligned = mov @ R.T + tr
        pos = 0
        new = []
        for ci, refc in enumerate(reference.components()):
            m = len(refc)
            mc = aligned[pos:pos+m]
            pos += m
            best_d = np.inf
            best_s = 0
            # FFT correlation would be faster, but exact scan is deterministic and N is modest.
            for s in range(m):
                d = float(np.mean(np.sum((refc - np.roll(mc, s, axis=0))**2, axis=1)))
                if d < best_d:
                    best_d, best_s = d, s
            shifts[ci] = (shifts[ci] + best_s) % m
            new.append(np.roll(comps[ci], best_s, axis=0))
        comps = new
    mov = np.vstack(comps)
    R, tr = kabsch(mov, reference.points)
    aligned = mov @ R.T + tr
    rms = float(np.sqrt(np.mean(np.sum((aligned-reference.points)**2, axis=1))))
    return CurveSet(aligned, reference.offsets.copy()), rms, shifts, R, tr

def min_nonlocal_vertex_distance(cs: CurveSet, adjacency=3):
    best = np.inf
    for ai, a in enumerate(cs.components()):
        for bi, b in enumerate(cs.components()[ai:], start=ai):
            if ai == bi:
                n = len(a)
                for i in range(n):
                    for j in range(i+1, n):
                        d = min(j-i, n-(j-i))
                        if d <= adjacency:
                            continue
                        best = min(best, float(np.linalg.norm(a[i]-a[j])))
            else:
                # Chunk to avoid large temporary arrays.
                for i0 in range(0, len(a), 128):
                    r = a[i0:i0+128, None, :] - b[None, :, :]
                    best = min(best, float(np.min(np.linalg.norm(r, axis=2))))
    return float(best)

def deformation_basis(cs: CurveSet, m_min=2, m_max=5, max_modes=8):
    vecs=[]; labels=[]
    for ci,c in enumerate(cs.components()):
        T=tangents(c)
        axes=np.eye(3)
        a=axes[np.argmin(np.abs(axes@T[0]))]
        n1=np.empty_like(c); n2=np.empty_like(c)
        q=a-T[0]*np.dot(a,T[0]); q/=max(np.linalg.norm(q),EPS)
        n1[0]=q; n2[0]=np.cross(T[0],q)
        for i in range(1,len(c)):
            v=np.cross(T[i-1],T[i]); s=np.linalg.norm(v); cc=np.clip(np.dot(T[i-1],T[i]),-1,1); q=n1[i-1]
            if s>1e-12:
                k=v/s; ang=np.arctan2(s,cc)
                q=q*np.cos(ang)+np.cross(k,q)*np.sin(ang)+k*np.dot(k,q)*(1-np.cos(ang))
            q-=T[i]*np.dot(q,T[i]); q/=max(np.linalg.norm(q),EPS)
            n1[i]=q; n2[i]=np.cross(T[i],q)
        th=2*np.pi*np.arange(len(c))/len(c)
        sl=slice(cs.offsets[ci],cs.offsets[ci+1])
        for m in range(m_min,m_max+1):
            for frame,fn in ((n1,'n1'),(n2,'n2')):
                for trig,tn in ((np.cos,'c'),(np.sin,'s')):
                    v=np.zeros_like(cs.points);v[sl]=trig(m*th)[:,None]*frame
                    vecs.append(v.reshape(-1));labels.append(f"c{ci}:m{m}:{fn}:{tn}")
    if not vecs:
        return np.empty((cs.points.size,0)),[]
    M=np.stack(vecs,axis=1)
    Q,R=np.linalg.qr(M)
    keep=np.abs(np.diag(R))>1e-10
    Q=Q[:,keep]; labs=[x for x,k in zip(labels,keep) if k]
    return Q[:,:max_modes],labs[:max_modes]
