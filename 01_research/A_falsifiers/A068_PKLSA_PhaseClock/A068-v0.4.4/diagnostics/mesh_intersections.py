"""EXHAUSTIVE candidate enumeration of polygon-surface triangles (development).

Every topologically DISJOINT triangle pair is checked using an enclosing-sphere
cKDTree broadphase (no subsampling), exact AABB reject and floating-point SAT.
Shared-edge/vertex pairs need separate nonlocal-overlap geometry, so those are
reported and NOT falsely promoted to exact CGAL-style certification.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree


def torus_triangles(surface):
    s=np.asarray(surface,float); m,k,_=s.shape
    ids=np.arange(m*k).reshape(m,k)
    a=ids; b=np.roll(ids,-1,axis=0); c=np.roll(ids,-1,axis=1)
    d=np.roll(b,-1,axis=1)
    tri=np.concatenate([np.stack([a,b,c],axis=-1).reshape(-1,3),
                        np.stack([b,d,c],axis=-1).reshape(-1,3)],axis=0)
    return s.reshape(-1,3),tri


def intersects_sat(A,B,eps=1e-12):
    """Triangle-triangle SAT, including coplanar axes; numerical not exact predicates.
    """
    A=np.asarray(A,float);B=np.asarray(B,float)
    ea=np.roll(A,-1,axis=0)-A; eb=np.roll(B,-1,axis=0)-B
    na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1])
    scale=max(float(np.max(np.abs(A-B.mean(axis=0)))),float(np.max(np.abs(B-A.mean(axis=0)))),1.0)
    if np.linalg.norm(na)<eps*scale**2 or np.linalg.norm(nb)<eps*scale**2:
        raise ValueError('DEGENERATE_TRIANGLE')
    axes=[na,nb]
    axes.extend(np.cross(na,e) for e in ea)
    axes.extend(np.cross(nb,e) for e in eb)
    axes.extend(np.cross(x,y) for x in ea for y in eb)
    for axis in axes:
        norm=np.linalg.norm(axis)
        if norm<eps*scale**2:continue
        ah=A@axis;bh=B@axis
        if ah.max() < bh.min()-eps*scale*norm or bh.max() < ah.min()-eps*scale*norm:
            return False
    return True


def all_nonincident_intersections(vertices,triangles,eps=1e-12,max_reports=100):
    """No sample/subset selection; handles *all* disjoint-vertex pairs.

    Raises on nonfinite / degenerate triangles. Adjacent faces are not certified
    free of nonlocal overlaps: this is a high-value diagnostic, not a proof of
    global embeddedness. Report test coverage and candidate counts explicitly.
    """
    v=np.asarray(vertices,float);t=np.asarray(triangles,dtype=np.int64)
    if v.ndim!=2 or v.shape[1]!=3 or t.ndim!=2 or t.shape[1]!=3:raise ValueError('Invalid mesh')
    if not np.all(np.isfinite(v)):raise ValueError('Nonfinite vertex')
    if (t<0).any() or (t>=len(v)).any():raise ValueError('Invalid vertex index')
    faces=v[t]; cent=faces.mean(axis=1)
    rad=np.linalg.norm(faces-cent[:,None,:],axis=2).max(axis=1)
    areas=np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1)*.5
    if np.min(areas)<=eps:raise ValueError('Degenerate triangle')
    low=faces.min(axis=1); high=faces.max(axis=1)
    tree=cKDTree(cent); maxrad=float(rad.max());N=len(t)
    hits=[];broad=0; narrow=0;incident=0;disjoint_count=0
    for i in range(N):
        # A necessary condition for overlapping triangles is overlapping bounding spheres.
        js=tree.query_ball_point(cent[i],r=float(rad[i]+maxrad+eps))
        for j in js:
            if j<=i:continue
            common=len(set(map(int,t[i])) & set(map(int,t[j])))
            if common:
                incident+=1;continue
            if np.linalg.norm(cent[i]-cent[j])>rad[i]+rad[j]+eps:continue
            broad+=1
            if (high[i]+eps<low[j]).any() or (high[j]+eps<low[i]).any():continue
            narrow+=1
            if intersects_sat(faces[i],faces[j],eps=eps):
                if len(hits)<max_reports:hits.append([int(i),int(j)])
                disjoint_count+=1
    return {'schema':'A068-DEVELOPMENT-GLOBAL-PAIRWISE-v0.4.5',
            'triangle_count':N,'all_faces_enumerated':True,
            'candidate_disjoint_pairs_after_sphere_broadphase':broad,
            'tested_disjoint_pairs_after_AABB':narrow,
            'topologically_incident_pair_candidates_excluded':incident,
            'nonincident_intersection_count':disjoint_count,'sample_intersection_pairs':hits,
            'no_nonincident_intersection':disjoint_count==0,
            'full_surface_certified':False,
            'limitation':'Topologically incident face nonlocal collisions, numerical degeneracies and exact-predicate robustness require independent CGAL self_intersections confirmation',
            'authority':'DIAGNOSTIC_ONLY'}


def inspect_torus(surface):
    return all_nonincident_intersections(*torus_triangles(surface))
