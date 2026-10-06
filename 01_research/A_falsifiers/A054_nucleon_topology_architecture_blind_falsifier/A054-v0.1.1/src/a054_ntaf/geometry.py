from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import numpy as np

Array = np.ndarray


def close_curve(x: Array) -> Array:
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or len(x) < 8:
        raise ValueError("curve must be Nx3 with N>=8")
    if np.linalg.norm(x[0] - x[-1]) < 1e-12:
        x = x[:-1]
    return x.copy()


def curve_length(x: Array) -> float:
    x = close_curve(x)
    d = np.roll(x, -1, axis=0) - x
    return float(np.linalg.norm(d, axis=1).sum())


def total_length(components: Iterable[Array]) -> float:
    return float(sum(curve_length(c) for c in components))


def resample_closed_curve(x: Array, n: int) -> Array:
    x = close_curve(x)
    if n < 8:
        raise ValueError("n must be >= 8")
    y = np.vstack([x, x[0]])
    seg = np.linalg.norm(np.diff(y, axis=0), axis=1)
    if np.any(seg <= 0):
        keep = np.r_[True, seg[:-1] > 1e-14]
        x = x[keep]
        y = np.vstack([x, x[0]])
        seg = np.linalg.norm(np.diff(y, axis=0), axis=1)
    s = np.r_[0.0, np.cumsum(seg)]
    target = np.linspace(0.0, s[-1], n, endpoint=False)
    out = np.empty((n, 3), float)
    for j in range(3):
        out[:, j] = np.interp(target, s, y[:, j])
    return out


def center_components(components: list[Array]) -> list[Array]:
    allx = np.vstack(components)
    ctr = allx.mean(axis=0)
    return [np.asarray(c, float) - ctr for c in components]


def normalize_total_length(components: list[Array], L: float = 1.0) -> list[Array]:
    comps = center_components([close_curve(c) for c in components])
    lt = total_length(comps)
    if not np.isfinite(lt) or lt <= 0:
        raise ValueError("invalid total length")
    sc = L / lt
    return [c * sc for c in comps]


def rotate_components(components: list[Array], R: Array) -> list[Array]:
    R = np.asarray(R, float)
    return [np.asarray(c) @ R.T for c in components]


def unlinked_three_rings(n: int = 192) -> list[Array]:
    """Compact but unlinked three-circle control."""
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    r = 0.72
    centers = np.array([
        [-1.55, -0.75, 0.0],
        [ 1.55, -0.75, 0.0],
        [ 0.00,  1.75, 0.0],
    ])
    comps = []
    for k, ctr in enumerate(centers):
        # Alternating planes suppress an accidental symmetry advantage while staying unlinked.
        if k == 0:
            x = np.c_[r*np.cos(t), r*np.sin(t), np.zeros_like(t)]
        elif k == 1:
            x = np.c_[r*np.cos(t), np.zeros_like(t), r*np.sin(t)]
        else:
            x = np.c_[np.zeros_like(t), r*np.cos(t), r*np.sin(t)]
        comps.append(x + ctr)
    return normalize_total_length(comps)


def torus_link_3_3(n: int = 192, R: float = 2.0, r: float = 0.62) -> list[Array]:
    """Analytic T(3,3) three-component link; every component is a (1,1) unknot."""
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    comps = []
    for k in range(3):
        ph = 2*np.pi*k/3
        rr = R + r*np.cos(t + ph)
        comps.append(np.c_[rr*np.cos(t), rr*np.sin(t), r*np.sin(t + ph)])
    return normalize_total_length(comps)


def _braid_paths(word: list[int], n_strands: int = 3, samples_per_generator: int = 48,
                 spacing: float = 0.72) -> tuple[list[Array], list[int]]:
    """Return label trajectories in a braid cylinder and endpoint slot of each label.

    generator +i means sigma_i; -i means sigma_i^{-1}; i is 1-based.
    """
    slots = np.linspace(-(n_strands-1)*spacing/2, (n_strands-1)*spacing/2, n_strands)
    pos = np.c_[slots, np.zeros(n_strands)]
    labels_in_slot = list(range(n_strands))
    paths = [[pos[i].copy()] for i in range(n_strands)]
    total_steps = len(word) * samples_per_generator
    step_global = 0
    for g in word:
        i = abs(g) - 1
        if i < 0 or i >= n_strands-1:
            raise ValueError(f"bad braid generator {g}")
        p0 = pos[i].copy(); p1 = pos[i+1].copy()
        mid = 0.5*(p0+p1); v0 = p0-mid; v1 = p1-mid
        sign = 1.0 if g > 0 else -1.0
        lab0, lab1 = labels_in_slot[i], labels_in_slot[i+1]
        for q in range(1, samples_per_generator+1):
            a = sign*np.pi*q/samples_per_generator
            ca, sa = np.cos(a), np.sin(a)
            Rot = np.array([[ca,-sa],[sa,ca]])
            curr = pos.copy()
            curr[i] = mid + Rot@v0
            curr[i+1] = mid + Rot@v1
            # labels not involved remain in their current slot positions.
            label_pos = np.empty_like(curr)
            for s, lab in enumerate(labels_in_slot):
                label_pos[lab] = curr[s]
            label_pos[lab0] = curr[i]
            label_pos[lab1] = curr[i+1]
            for lab in range(n_strands):
                paths[lab].append(label_pos[lab].copy())
            step_global += 1
        # Slot coordinates are fixed; only strand labels exchange slots.
        labels_in_slot[i], labels_in_slot[i+1] = labels_in_slot[i+1], labels_in_slot[i]
    end_slot_of_label = [None]*n_strands
    for s, lab in enumerate(labels_in_slot):
        end_slot_of_label[lab] = s
    return [np.asarray(p) for p in paths], [int(x) for x in end_slot_of_label]


def closed_braid_torus(word: list[int], n: int = 192, R: float = 2.2,
                       tube_scale: float = 0.40) -> list[Array]:
    """Embed a closed braid in a solid torus and return its components."""
    spp = max(16, int(np.ceil(n/max(1, len(word)))))
    paths2, end_slot = _braid_paths(word, 3, spp, spacing=0.85)
    m = len(paths2[0])
    theta = np.linspace(0, 2*np.pi, m, endpoint=True)
    label_curves = []
    for uv in paths2:
        u = tube_scale*uv[:,0]
        v = tube_scale*uv[:,1]
        rr = R + u
        label_curves.append(np.c_[rr*np.cos(theta), rr*np.sin(theta), v])

    # Closure connects a label ending in slot j to label j at theta=0.
    seen = set(); components = []
    for start in range(3):
        if start in seen:
            continue
        cyc=[]; cur=start
        while cur not in seen:
            seen.add(cur); cyc.append(cur); cur=end_slot[cur]
        pts=[]
        for lab in cyc:
            seg=label_curves[lab]
            pts.append(seg[:-1])
        comp=np.vstack(pts)
        components.append(resample_closed_curve(comp, n))
    return normalize_total_length(components)


def borromean_braid(n: int = 192) -> list[Array]:
    # Standard 3-braid closure (sigma_1^{-1} sigma_2)^3.
    return closed_braid_torus([-1, 2, -1, 2, -1, 2], n=n)


def _segments(x: Array):
    a = close_curve(x)
    b = np.roll(a, -1, axis=0)
    return a, b, b-a, 0.5*(a+b)


def gauss_linking_number(c1: Array, c2: Array) -> float:
    """Midpoint Gauss integral; converges to integer for disjoint smooth polygons."""
    a1,b1,dl1,m1=_segments(c1); a2,b2,dl2,m2=_segments(c2)
    diff=m1[:,None,:]-m2[None,:,:]
    cross=np.cross(dl1[:,None,:], dl2[None,:,:])
    den=np.linalg.norm(diff,axis=2)**3
    val=np.sum(np.einsum('ijk,ijk->ij',cross,diff)/np.maximum(den,1e-18))/(4*np.pi)
    return float(val)


def pairwise_link_matrix(components: list[Array]) -> Array:
    k=len(components); M=np.zeros((k,k),float)
    for i in range(k):
        for j in range(i+1,k):
            M[i,j]=M[j,i]=gauss_linking_number(components[i],components[j])
    return M


def min_intercomponent_distance(components: list[Array]) -> float:
    best=np.inf
    for i in range(len(components)):
        for j in range(i+1,len(components)):
            d=np.linalg.norm(components[i][:,None,:]-components[j][None,:,:],axis=2)
            best=min(best,float(d.min()))
    return best


def geometry_sha256(components: list[Array]) -> str:
    import hashlib
    h=hashlib.sha256(b"A054-GEOMETRY-SHA256-v1\0")
    for c in components:
        a=np.ascontiguousarray(np.asarray(c,dtype='<f8'))
        h.update(np.array(a.shape,dtype='<i8').tobytes()); h.update(a.tobytes())
    return h.hexdigest()


def save_components_npz(path, components: list[Array]):
    payload={f"c{i}":np.asarray(c,float) for i,c in enumerate(components)}
    np.savez_compressed(path, **payload)


def load_components_npz(path) -> list[Array]:
    z=np.load(path)
    keys=sorted(z.files,key=lambda s:int(s[1:]) if s.startswith('c') and s[1:].isdigit() else 999)
    return [close_curve(z[k]) for k in keys]
