"""Projection-first rounded 4-plat for the twist-knot family.

Word: sigma_2^(m) sigma_1^(-1) sigma_2^(+1), standard plat closure.
This is a 2-bridge twist-knot diagram; knot determinant is 2m+1.
Inputs/outputs are dimensionless geometry; no physical vortex claims.
"""
import math
import numpy as np
from scipy.interpolate import PchipInterpolator

NAMES={1:'3_1',2:'4_1',3:'5_2',4:'6_1',5:'7_2',6:'8_1',7:'9_2',8:'10_1'}

def name(m):return NAMES.get(int(m),f'Tm{int(m)}')

def word(m):
    if m<1: raise ValueError('m >= 1')
    return [(1,1)]*m+[(0,-1),(1,1)]

def smooth(u):
    u=np.asarray(u)
    return u*u*u*(u*(u*6-15)+10)

def fourplat(m,density=80,cap_pts=56,lane_spacing=0.48,z_lift=0.30,carrier_radius=17.0,angle_gap=0.43):
    """Return one polygon along its unique connected component, plus exact combinatorial certificate.
    Generate four monotonic braid strands, plat caps, then apply injective polar annular map.
    """
    w=word(m);ne=len(w)
    ys=(np.arange(4,dtype=float)-1.5)*lane_spacing
    strands=[[] for _ in range(4)]
    events=[[] for _ in range(4)]
    slots=list(range(4))
    def append(label,x,y,z):strands[label].append((float(x),float(y),float(z)))
    # x param spans [0, ne] with explicit C2 braiding at each event
    for j,(k,sgn) in enumerate(w):
        upper,lower=slots[k],slots[k+1]
        for h in range(density):
            u=h/density;f=float(smooth(u))
            for pos,label in enumerate(slots):
                y=ys[pos];z=0.
                if pos==k:
                    y=(1-f)*ys[k]+f*ys[k+1]
                    z=sgn*z_lift*math.sin(math.pi*u)**2
                if pos==k+1:
                    y=(1-f)*ys[k+1]+f*ys[k]
                    z=-sgn*z_lift*math.sin(math.pi*u)**2
                append(label,j+u,y,z)
        events[upper].append((j,'O' if sgn==1 else 'U'))
        events[lower].append((j,'U' if sgn==1 else 'O'))
        slots[k],slots[k+1]=slots[k+1],slots[k]
    for pos,label in enumerate(slots):append(label,float(ne),ys[pos],0)
    endpos={label:pos for pos,label in enumerate(slots)}
    posend={pos:label for label,pos in endpos.items()}
    # plat arcs in standard (x,y) coordinates with C1 matched axial tangents
    cap_r=0.7
    def cap(side, pos_from, pos_to):
        if abs(pos_from-pos_to)!=1 or min(pos_from,pos_to)%2!=0:
            raise ValueError('plat pairing invalid')
        x0=0.0 if side=='L' else float(ne)
        p0,p1=ys[pos_from],ys[pos_to]
        cmid=(p0+p1)/2; rad=(p0-p1)/2
        v=np.linspace(0,math.pi,cap_pts+2)[1:-1]
        # cap outward in x; sign of sin relates side
        a=-cap_r if side=='L' else cap_r
        return np.column_stack((x0+a*np.sin(v),cmid+rad*np.cos(v),np.zeros_like(v)))
    # Traversal starting at left top, along cap to L1 then strand to R, cap, etc
    traveled=[];trace=[];side='L';port=0;used=set();orientation=[]
    for _ in range(4):
        if side=='L':
            other=port^1
            if other in used: break
            traveled.extend(cap('L',port,other))
            arr=np.asarray(strands[other]);traveled.extend(arr)
            trace += events[other];used.add(other);orientation.append((other,1))
            side='R';port=endpos[other]
        else:
            other=port^1
            label=posend[other]
            if label in used:break
            traveled.extend(cap('R',port,other))
            arr=np.asarray(strands[label])[::-1];traveled.extend(arr)
            trace += events[label][::-1];used.add(label);orientation.append((label,-1))
            side='L';port=label
    if len(used)!=4:raise ValueError(f'Closure has >1 component, m={m}, traversed={used}')
    # include final cap from Lport to L0 to close; should be plat pair
    if side!='L' or port!=0:raise ValueError('closure endpoint invariant failed')
    flat=np.asarray(traveled,dtype=np.float64)
    # Ensure non-repeated zero edges; cap and braid endpoints gap may be degenerate
    flat=flat[np.r_[True,np.linalg.norm(np.diff(flat,axis=0),axis=1)>1e-10]]
    # projected event angles; twist crossings concentrated at top, clasp at lower-left
    xcenter=np.arange(ne,dtype=float)+0.5
    theta_twist=np.linspace(0.92,2.15,m)
    theta_clasp=[3.64,4.08]
    xc=np.r_[-cap_r, xcenter, ne+cap_r]
    tc=np.r_[-math.pi/2+angle_gap/2,theta_twist,theta_clasp, 3*math.pi/2-angle_gap/2]
    # For m=1 theta sequence still strictly increasing
    theta=PchipInterpolator(xc,tc)(flat[:,0])
    rad=carrier_radius+flat[:,1]
    if rad.min()<=0:raise ValueError('radius must exceed lane spread')
    three=np.column_stack([rad*np.cos(theta),rad*np.sin(theta),flat[:,2]])
    # record labels in traversal order for determinant check
    return three,{'word':[(int(k),int(s)) for k,s in w], 'traversal':trace,
                  'orientation':orientation,'crossings':ne,'m':m,
                  'lane_spacing':lane_spacing,'z_lift':z_lift,'carrier_radius':carrier_radius,
                  'angle_gap':angle_gap}

def fox_determinant(trace,n):
    """Integer Fox-coloring determinant from full over/under encounter sequence.
    Validates topological projection combinatorics, independent of spatial sampling.
    """
    if len(trace)!=2*n or sorted(x for x,k in trace if k=='U')!=list(range(n)):
        raise ValueError('underpass count invalid')
    arclabel={}; count=0
    for ix,(j,kind) in enumerate(trace):
        if kind=='U': count+=1
        arclabel[(j,kind)]=(count-1)%n
    M=np.zeros((n,n),dtype=np.int64)
    for j in range(n):
        o=arclabel[(j,'O')];uout=arclabel[(j,'U')];uin=(uout-1)%n
        M[j,o]+=2;M[j,uin]-=1;M[j,uout]-=1
    # fraction-free determinant (tiny matrices, exact integer via sympy)
    import sympy as sp
    return abs(int(sp.Matrix(M[:-1,:-1]).det()))

def resample_closed(arr,n):
    p=np.asarray(arr,dtype=np.float64);v=np.roll(p,-1,axis=0)-p
    d=np.linalg.norm(v,axis=1)
    if (d<1e-10).any():raise ValueError('zero length edge in geometry')
    s=np.r_[0.,np.cumsum(d)];t=np.arange(n)*s[-1]/n
    i=np.minimum(np.searchsorted(s,t,side='right')-1,len(d)-1)
    return p[i]+((t-s[i])/d[i])[:,None]*v[i]

def alexander_coefficients(diag):
    """Compute a representative Alexander polynomial from oriented Wirtinger/Fox relations.
    Returns ascending polynomial coefficients after removing monomial/unit ambiguity.
    Determinant = |Delta(-1)|. For these twist knots Delta = k-(2k+/-1)t+k t^2.
    """
    import sympy as sp
    m=diag['m'];n=m+2
    trace=diag['traversal']; orientations=dict(diag['orientation'])
    slots=list(range(4));signs=[]
    for j,(k,sgn) in enumerate(word(m)):
        upper,lower=slots[k],slots[k+1]
        over,under=(upper,lower) if sgn==1 else (lower,upper)
        signs.append(-sgn*orientations[over]*orientations[under])
        slots[k],slots[k+1]=slots[k+1],slots[k]
    labels={};num=0
    for j,kind in trace:
        if kind=='U':num+=1
        labels[(j,kind)]=(num-1)%n
    t=sp.Symbol('t')
    mat=sp.zeros(n,n)
    for j in range(n):
        ov=labels[(j,'O')]; post=labels[(j,'U')];pre=(post-1)%n
        tj=t if signs[j]>0 else t**(-1)
        mat[j,ov]+=1-tj;mat[j,pre]+=tj;mat[j,post]-=1
    poly=sp.cancel(mat[:-1,:-1].det())
    numerator=sp.together(poly).as_numer_denom()[0]
    p=sp.Poly(numerator,t)
    coeffs=[int(p.nth(i)) for i in range(p.degree()+1)]
    while coeffs and coeffs[0]==0:coeffs.pop(0)
    while coeffs and coeffs[-1]==0:coeffs.pop()
    if coeffs and coeffs[-1]<0:coeffs=[-v for v in coeffs]
    return coeffs

def expected_alexander(m):
    k=(m+1)//2
    return [k,-(2*k+(1 if m%2==0 else -1)),k]
