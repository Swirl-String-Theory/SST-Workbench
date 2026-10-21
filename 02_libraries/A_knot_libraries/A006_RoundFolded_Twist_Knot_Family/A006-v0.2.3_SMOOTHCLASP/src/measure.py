"""Geometric checks; no KnotPlot dynamics or independent knot inference."""
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from shapely.strtree import STRtree

def projection_crossings(p):
    """All polygonal xy intersections with over/under vertical clearance."""
    p=np.asarray(p,dtype=float); n=len(p)
    seg=[LineString((p[i,:2],p[(i+1)%n,:2])) for i in range(n)]
    tree=STRtree(seg);found=[]
    for i,line in enumerate(seg):
        for ji in tree.query(line,predicate='intersects'):
            j=int(ji)
            if j<=i or j-i in (1,n-1):continue
            point=line.intersection(seg[j])
            if point.geom_type!='Point':
                raise ValueError(f'non-point 2D intersection between segments {i} and {j}')
            q=np.array([point.x,point.y]);
            def lifted(k):
                v=p[(k+1)%n]-p[k];vxy=v[:2]
                f=float(np.dot(q-p[k,:2],vxy)/max(np.dot(vxy,vxy),1.e-18))
                return float(p[k,2]+f*v[2])
            dz=lifted(i)-lifted(j)
            if abs(dz)<1.e-6:raise ValueError(f'3D crossing gap collapsed at {i,j}')
            if any((old['x']-point.x)**2+(old['y']-point.y)**2<1.e-12 for old in found):
                continue  # duplicate intersections when a raw crossing lies exactly at polygon vertices
            found.append({'segment_a':i,'segment_b':j,'x':float(point.x),'y':float(point.y),'dz':float(dz)})
    return found

def min_nonlocal(p,neighbor_skip=5):
    """Conservative midpoint screening with exact segment distances for local candidates.
    Excludes only neighbor_skip edges, not a certified global reach/thickness.
    """
    from scipy.spatial.distance import cdist
    p=np.asarray(p)
    v=np.roll(p,-1,axis=0)-p;c=p+v/2;n=len(p)
    tree=cKDTree(c); best=float('inf');witness=None
    # within a 2.5-unit midpoint neighborhood; if none, minimum at least 2.5 - max_edge
    for i in range(n):
        js=tree.query_ball_point(c[i],r=2.5)
        for j in js:
            cyc=min(abs(j-i),n-abs(j-i))
            if j<=i or cyc<=neighbor_skip:continue
            # exact vectorized-style iterative segment shortest distance via endpoint + interior clamp
            P=p[i];Q=p[j];a=v[i];b=v[j];w=P-Q
            A=a@a;B=a@b;C=b@b;D=a@w;E=b@w; den=A*C-B*B
            u=max(0.,min(1.,(B*E-C*D)/den)) if den>1e-16 else 0.
            t=max(0.,min(1.,(B*u+E)/C))
            u=max(0.,min(1.,(B*t-D)/A))
            t=max(0.,min(1.,(B*u+E)/C))
            d=float(np.linalg.norm(w+a*u-b*t))
            if d<best:best=d;witness=[i,j]
    return {'distance':best,'witness_segments':witness,'neighbor_skip':neighbor_skip}

def lengths(p):
    ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    return {'n':len(p),'total':float(ds.sum()),'edge_min':float(ds.min()),
            'edge_max':float(ds.max()),'edge_cv':float(ds.std()/ds.mean())}

def gauss_linking(a,b):
    A=np.roll(a,-1,axis=0)-a;B=np.roll(b,-1,axis=0)-b
    Pa=(a+np.roll(a,-1,axis=0))/2;Pb=(b+np.roll(b,-1,axis=0))/2
    acc=0.
    for i in range(0,len(a),32):
        v=Pa[i:i+32,None,:]-Pb[None,:,:];c=np.cross(A[i:i+32,None,:],B[None,:,:]);
        q=np.linalg.norm(v,axis=2);acc+=float((np.sum(c*v,axis=2)/q**3).sum())
    return float(acc/(4*np.pi))
