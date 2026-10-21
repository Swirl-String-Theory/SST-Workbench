"""Projection-first 5_2 and 6_1 from supplied TikZ Hobby control vertices.

CubicSpline is an explicitly-labelled approximation to the *Hobby* shortcut;
not a claim of mathematically identical PDF paths. The 2D projection has
5/6 transverse crossings with alternating crossing assignment, and its
Fox/Alexander polynomial is checked from this actual crossing trace.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString
from shapely.strtree import STRtree
import sympy as sp

POINTS={
'5_2':[(2,-1.50),(1.50,1),(0,2),(-2,1),(-1,-1.50),(.50,-2),(-1.25,-2.25),(-2,-1.50),(-1.50,1),(0,2),(2,1),(1,-1.50),(-.50,-2),(1.25,-2.25)],
'6_1':[(0,2),(-2,2),(-1.50,-1),(.50,-2),(-1.50,-2),(-2.50,-.50),(-2,1),(0,3),(2,1),(2.50,-.50),(1.50,-2),(-.50,-2),(1.50,-1),(2,2)]}
EXPECTED={'5_2':(5,[2,-3,2],7),'6_1':(6,[2,-5,2],9)}

def points(label,jitter=0.07):
    p=np.array(POINTS[label],dtype=np.float64)
    if label=='5_2':
        # P3 and P10 exactly coincide in supplied TikZ. Topologically generic
        # projection requires transverse intersections, not coincident nodes.
        p[9,1]+=jitter
    return p

def xy_curve(label,per_segment=100,jitter=.07):
    p=points(label,jitter)
    cs=CubicSpline(np.arange(15),np.vstack([p,p[0]]),bc_type='periodic')
    u=np.arange(14*per_segment)/per_segment
    return u,cs(u)

def projected_crossings(xy):
    n=len(xy)
    seg=[LineString([xy[i],xy[(i+1)%n]]) for i in range(n)]
    tree=STRtree(seg)
    cr=[]
    for i,g in enumerate(seg):
        for j in tree.query(g,predicate='intersects'):
            j=int(j)
            if j<=i or min((j-i)%n,(i-j)%n)<=2:continue
            hit=g.intersection(seg[j])
            if hit.geom_type!='Point':
                raise ValueError('Nontransverse / overlapping projection segments')
            vv=xy[(i+1)%n]-xy[i];ww=xy[(j+1)%n]-xy[j]
            if abs(np.linalg.det(np.stack([vv,ww])))<1e-12:continue
            H=np.array([hit.x,hit.y])
            v=(H-xy[i])@vv/(vv@vv)
            w=(H-xy[j])@ww/(ww@ww)
            cr.append({'i':int(i),'j':int(j),'s':(i+v)/n,'t':(j+w)/n,
                       'signed_xy':int(np.sign(np.linalg.det(np.stack([vv,ww]))))})
    cr.sort(key=lambda c:c['s'])
    return cr

def assigned_events(cr):
    ev=sorted([(c['s'],i,'a') for i,c in enumerate(cr)]+[(c['t'],i,'b') for i,c in enumerate(cr)])
    by={}
    trace=[]
    for k,(s,j,side) in enumerate(ev):
        kind='O' if k%2==0 else 'U'
        if j in by and by[j]==kind:raise ValueError('Not alternating diagram')
        by[j]=kind;trace.append((j,kind))
    return ev,trace

def alexander(trace,cr):
    n=len(cr);t=sp.Symbol('t');M=sp.zeros(n,n)
    labels={};num=0
    for j,kind in trace:
        if kind=='U':num+=1
        labels[(j,kind)]=(num-1)%n
    ev,_=assigned_events(cr)
    for j,c in enumerate(cr):
        is_a_over=next(k%2==0 for k,(_,idx,side) in enumerate(ev) if idx==j and side=='a')
        sign=c['signed_xy']*(1 if is_a_over else -1)
        tj=t if sign>0 else 1/t
        over=labels[(j,'O')];post=labels[(j,'U')];pre=(post-1)%n
        M[j,over]+=1-tj;M[j,pre]+=tj;M[j,post]-=1
    f=sp.factor(M[:-1,:-1].det());pol=sp.Poly(sp.fraction(sp.cancel(f))[0],t)
    co=[int(pol.nth(i)) for i in range(pol.degree()+1)]
    while co and co[0]==0:co.pop(0)
    while co and co[-1]==0:co.pop()
    # primitive normalization by global sign; Alexander defined up to ±t^k
    if co[-1]<0:co=[-i for i in co]
    determinant=abs(int(sp.cancel(f).subs(t,-1)))
    return co,determinant

def gaussian(u,center,width):
    d=np.abs(u-center);d=np.minimum(d,1.-d)
    return np.exp(-0.5*(d/width)**2)

def dense_xyz(label,density=180,width=.011,height=.10,jitter=.07):
    u,xy=xy_curve(label,density,jitter)
    cr=projected_crossings(xy)
    exp_n,expected_poly,exp_det=EXPECTED[label]
    if len(cr)!=exp_n:raise ValueError(f'{label}: expected {exp_n} crossings got {len(cr)}')
    ev,trace=assigned_events(cr)
    coeff,det=alexander(trace,cr)
    if coeff!=expected_poly or det!=exp_det:
        raise ValueError(f'{label}: knot invariant mismatch coeff={coeff},det={det}')
    s=np.arange(len(u))/len(u)
    z=np.zeros(len(u))
    for k,(ss,j,which) in enumerate(ev):
        sign=1 if k%2==0 else -1
        z+=height*sign*gaussian(s,ss,width)
    xyz=np.column_stack([xy,z])
    return xyz, {'label':label,'crossings':len(cr),'alexander_coefficients':coeff,'determinant':det,
                 'control_points_original':POINTS[label],'control_points_after_regularization':points(label,jitter).tolist(),
                 'interpolant':'periodic cubic spline approximation; original TikZ uses Hobby shortcut',
                 'regularization_P10_dy':jitter if label=='5_2' else 0,
                 'lift':'alternating crossings, cyclic Gaussian 3D lifts','lift_height':height,
                 'lift_width_fraction':width,'crossing_records':cr,'encounters':trace}

def resample3(x,n):
    v=np.roll(x,-1,axis=0)-x;d=np.linalg.norm(v,axis=1)
    if d.min()<1e-13:raise ValueError('zero edge')
    s=np.r_[0.,np.cumsum(d)];q=np.arange(n)*s[-1]/n
    ix=np.minimum(np.searchsorted(s,q,side='right')-1,len(x)-1)
    return x[ix]+((q-s[ix])/d[ix])[:,None]*v[ix]
