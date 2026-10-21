"""Independent discrete 3D segment proximity diagnostic for closed knot centerlines.

This tests geometry at one snapshot, not continuous-time nonreconnection or topology.
It does not replace KnotPlot's `safe` or a native collision integrator audit.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b,scale):return tuple(x+scale*y for x,y in zip(a,b))

def distance_segments(p1,q1,p2,q2):
    """Minimum Euclidean distance of two closed 3D finite line segments.

    Handles parallel/degenerate segments (Ericson-like clamped closest points).
    """
    u=sub(q1,p1);v=sub(q2,p2);w=sub(p1,p2)
    a=dot(u,u); b=dot(u,v); c=dot(v,v);d=dot(u,w);e=dot(v,w)
    eps=1e-14*max(a,c,1.0)
    if a<=eps and c<=eps:return math.sqrt(dot(w,w))
    if a<=eps:
        t=max(0.,min(1.,e/c))
        w2=sub(p1,add(p2,v,t));return math.sqrt(dot(w2,w2))
    if c<=eps:
        s=max(0.,min(1.,-d/a))
        w2=sub(add(p1,u,s),p2);return math.sqrt(dot(w2,w2))
    D=a*c-b*b
    sN,sD=D,D;tN,tD=D,D
    if D<=eps:
        sN=0.;sD=1.;tN=e;tD=c
    else:
        sN=b*e-c*d;tN=a*e-b*d
        if sN<0.:sN=0.;tN=e;tD=c
        elif sN>sD:sN=sD;tN=e+b;tD=c
    if tN<0.:
        tN=0.
        if -d<0:sN=0.
        elif -d>a:sN=sD
        else:sN=-d;sD=a
    elif tN>tD:
        tN=tD
        if (-d+b)<0:sN=0.
        elif (-d+b)>a:sN=sD
        else:sN=-d+b;sD=a
    s=0. if abs(sN)<eps else sN/sD
    t=0. if abs(tN)<eps else tN/tD
    w2=sub(add(p1,u,s),add(p2,v,t))
    return math.sqrt(max(0.,dot(w2,w2)))

def assess(xyz,close=None,crossing_tol=1e-10):
    """Closed single-component point list, includes segment n-1 -> 0."""
    points=[tuple(float(v) for v in r) for r in xyz]
    n=len(points)
    if n<4:raise ValueError('Need at least 4 vertices for a closed polyline')
    if any(len(p)!=3 or not all(math.isfinite(x) for x in p) for p in points):raise ValueError('Non-3D or nonfinite input')
    if close is not None and (not math.isfinite(close) or close<=0):raise ValueError('close must be positive finite')
    segments=[(points[i],points[(i+1)%n]) for i in range(n)]
    best=math.inf;pair=None;count=0
    for i in range(n):
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            d=distance_segments(*segments[i],*segments[j]);count+=1
            if d<best:best=d;pair=(i,j)
    scale=max(math.dist(points[i],points[(i+1)%n]) for i in range(n))
    tolerance=max(crossing_tol,32*math.ulp(max(scale,1.0)))
    label='POSSIBLE_CENTERLINE_INTERSECTION' if best<=tolerance else ('CLOSE_THRESHOLD_VIOLATION' if close is not None and best<close else 'SNAPSHOT_CLEAR')
    return {'schema':'A058-3D-CENTERLINE-PROXIMITY-1','nbeads':n,'tested_nonadjacent_pairs':count,
            'minimum_distance':best,'closest_segment_indices':list(pair), 'close_threshold':close,
            'crossing_tolerance':tolerance,'status':label,'certifies_continuous_time_no_reconnection':False,
            'certifies_topological_invariance':False,'geometry_units':'same units as XYZ export'}

def read_xyz(path):
    coords=[]
    for index,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        s=line.strip()
        if not s or s.startswith('#'):continue
        parts=s.split()
        if len(parts)!=3:raise ValueError(f'line {index}: expected exactly three numeric columns')
        try:row=tuple(float(v) for v in parts)
        except ValueError as e:raise ValueError(f'line {index}: not numeric') from e
        coords.append(row)
    return coords

def main():
    ap=argparse.ArgumentParser();ap.add_argument('xyz',type=Path);ap.add_argument('--close',type=float)
    ap.add_argument('--out',type=Path);args=ap.parse_args()
    result=assess(read_xyz(args.xyz),args.close)
    if args.out:
        if args.out.exists():raise FileExistsError(args.out)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,allow_nan=False))
if __name__=='__main__':main()
