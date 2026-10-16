"""A063 v0.2.0: reproducible geometry and vortex-flux diagnostics.

Distinct objects: a closed vortex field line, a geometrical thickening, an
instantaneously vortex-aligned boundary, and a nonlinear Euler-stable tube.
The last requires an actual independent 3D perturbed Euler evolution and is
NOT inferred here.
"""
from __future__ import annotations
import math
from bisect import bisect_right
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from hicks_hill.qualification import poloidal_cycle


def line(field, s0_over_a=None, p=3, q=4, samples=1601, rtol=3e-11):
    """Fresh field-line integration, independently of v0.1.1's serialized data."""
    if s0_over_a is None:
        def W(x):return poloidal_cycle(field, x*field.a,rtol=rtol,atol=rtol)['W']
        s0_over_a=brentq(lambda s: W(s)-p/q, .96,.98,xtol=3e-12)
    one=poloidal_cycle(field,s0_over_a*field.a,rtol=rtol,atol=rtol)
    def rhs(t,y):
        s,z,phi=y
        us,up,uz=field.velocity(s,z)
        return [us,uz,up/s]
    T=q*one['T'];y0=[s0_over_a*field.a,0.,0.]
    sol=solve_ivp(rhs,[0,T],y0,rtol=rtol,atol=rtol,dense_output=True,
                  max_step=one['T']/180)
    if not sol.success:raise RuntimeError(sol.message)
    y=sol.sol(np.linspace(0,T,samples));s,z,phi=y
    xyz=np.column_stack([s*np.cos(phi),s*np.sin(phi),z]);
    closure=np.linalg.norm(xyz[-1]-xyz[0])/field.a
    return {'xyz':xyz,'s':s,'z':z,'phi':phi, 'T':T, 'W':one['W'],
            's0_over_a':s0_over_a,'closure':closure,'t':np.linspace(0,T,samples)}


def project_crossings(xyz,view):
    """Independent generic planar projection and over/under crossings of closed polygon."""
    pts=np.asarray(xyz,dtype=float)
    view=np.asarray(view,dtype=float);view/=np.linalg.norm(view)
    temp=np.array([0.,0.,1.]) if abs(view[2])<.8 else np.array([0.,1.,0.])
    u=np.cross(view,temp);u/=np.linalg.norm(u);v=np.cross(view,u)
    planar=np.column_stack([pts@u,pts@v]);depth=pts@view
    n=len(pts)-1
    segs=[LineString([planar[i],planar[i+1]]) for i in range(n)]
    tree=STRtree(segs)
    crosses=[]
    for i,seg in enumerate(segs):
        for j in tree.query(seg,predicate='intersects'):
            j=int(j)
            if j<=i or j-i==1 or (i==0 and j==n-1):continue
            g=seg.intersection(segs[j])
            if not isinstance(g,Point):continue
            a=np.array([g.x,g.y]);di=planar[i+1]-planar[i];dj=planar[j+1]-planar[j]
            ri=np.dot(a-planar[i],di)/np.dot(di,di)
            rj=np.dot(a-planar[j],dj)/np.dot(dj,dj)
            if not (2e-6<ri<1-2e-6 and 2e-6<rj<1-2e-6):continue
            zi=depth[i]*(1-ri)+depth[i+1]*ri
            zj=depth[j]*(1-rj)+depth[j+1]*rj
            if abs(zi-zj)<2e-5:raise ValueError('near-degenerate projection')
            over=i+ri if zi>zj else j+rj
            under=j+rj if zi>zj else i+ri
            tover=di if zi>zj else dj
            tunder=dj if zi>zj else di
            handed=np.sign(tover[0]*tunder[1]-tover[1]*tunder[0])
            crosses.append({'over':float(over),'under':float(under),
                            'handed':int(handed),'z_gap':float(abs(zi-zj))})
    crosses.sort(key=lambda c:c['under'])
    return crosses


def alexander_poly(crosses):
    """Compute normalized Alexander polynomial from diagram's Wirtinger arcs.

    Each underpass terminates an arc; overstrands pass through unbroken.
    The Alexander matrix is (1-t)*over + t*incoming_under - outgoing_under.
    This determines the polynomial up to ±t^k. Symmetry and determinant are
    checked independently at multiple projection directions.
    """
    import sympy as sp
    m=len(crosses)
    if m<3:raise ValueError('too few undercrossings')
    unders=[c['under'] for c in crosses]
    t=sp.Symbol('t'); M=sp.zeros(m,m)
    for j,c in enumerate(crosses):
        over=(bisect_right(unders,c['over'])-1)%m
        incoming=(j-1)%m; outgoing=j
        if c['handed']>0:
            M[j,over]+=1-t;M[j,incoming]+=t;M[j,outgoing]-=1
        else:
            M[j,over]+=1-t;M[j,incoming]-=1;M[j,outgoing]+=t
    delta=sp.factor(M[1:,1:].det(method='domain-ge'))
    if delta==0:raise ValueError('zero Alexander polynomial: projection/arc convention failure')
    poly=sp.Poly(delta,t)
    terms=poly.terms(); min_exp=min(exp[0] for exp,_ in terms)
    poly=sp.Poly(sp.cancel(poly.as_expr()/t**min_exp),t)
    # Normalize the sign by the value at t=1, which must equal +1.
    val=poly.eval(1)
    if abs(val)!=1:raise ValueError(f'bad knot Alexander normalization: delta(1)={val}')
    poly=sp.Poly(poly.as_expr()/val,t)
    return {'n_crossings':m,'coefficients_ascending':[int(x) for x in reversed(poly.all_coeffs())],
            'degree':poly.degree(),'determinant':abs(int(poly.eval(-1))),
            'delta_1':int(poly.eval(1))}


def expected_torus_alexander(p=3,q=4):
    import sympy as sp
    t=sp.Symbol('t')
    f=sp.cancel(((t**(p*q)-1)*(t-1))/((t**p-1)*(t**q-1)))
    poly=sp.Poly(f,t)
    if poly.eval(1)==-1:poly=-poly
    return [int(x) for x in reversed(poly.all_coeffs())]


def tube_geometry(xyz,skip=40):
    """Conservative sampled geometric thickness diagnostics, not certified reach.

    Curvature bound and approximate doubly-critical-distance proxies; do not
    conflate point distance for nearby curve parameters with true tube reach.
    """
    pts=np.asarray(xyz[:-1]);n=len(pts)
    d=np.linalg.norm(np.roll(pts,-1,axis=0)-pts,axis=1)
    ds=np.mean(d)
    tang=np.roll(pts,-1,axis=0)-np.roll(pts,1,axis=0)
    tang/=np.linalg.norm(tang,axis=1)[:,None]
    dd=(np.roll(tang,-1,axis=0)-np.roll(tang,1,axis=0))/(2*ds)
    k=np.linalg.norm(dd,axis=1)
    # Nearest non-local point: ignore a modest arc neighborhood.
    tree=cKDTree(pts); mins=[]
    for i,p in enumerate(pts):
        inds=tree.query(p,k=min(n,100))[1]
        good=[j for j in np.atleast_1d(inds) if min(abs(j-i),n-abs(j-i))>=skip]
        if good:mins.append(np.linalg.norm(pts[i]-pts[good[0]]))
    return {'sample_count':n,'mean_ds':float(ds),'radius_curvature_min':float(1/np.max(k)),
            'nonlocal_distance_proxy_min':float(min(mins)) if mins else None,
            'exclusion_segments':skip,'closed_curve_residual':float(np.linalg.norm(xyz[0]-xyz[-1])),
            'certified_reach':False}


def sample_tube_flux(field, xyz, radii=(0.002,0.004,0.008),n_core=90,n_angles=16):
    """Test omega-normal flux through an explicit constant-radius knotted tube.

    Normals are constructed with a smoothly varying approximation, but the
    *sign* is obtained from finite core tangent and radial direction, not
    from tube-face discretization alone. Actual material boundary requires
    u.n=0 pointwise, not merely globally zero net flux.
    """
    pts=np.asarray(xyz[:-1]); n=len(pts)
    idx=np.linspace(0,n-1,n_core,endpoint=False,dtype=int)
    tang=np.zeros_like(pts)
    for i,xyz0 in enumerate(pts):
        s=math.hypot(xyz0[0],xyz0[1]);z=xyz0[2]
        us,uphi,uz=field.velocity(s,z)
        phi=math.atan2(xyz0[1],xyz0[0])
        u=np.array([us*math.cos(phi)-uphi*math.sin(phi),us*math.sin(phi)+uphi*math.cos(phi),uz])
        tang[i]=u/np.linalg.norm(u)
    rec=[]
    for radius in radii:
        dots=[];speeds=[];pressures=[]
        for i in idx:
            T=tang[i]
            ref=np.array([0.,0.,1.]) if abs(T[2])<.75 else np.array([0.,1.,0.])
            N=np.cross(T,ref);N/=np.linalg.norm(N)
            B=np.cross(T,N)
            for th in np.linspace(0,2*math.pi,n_angles,endpoint=False):
                normal=math.cos(th)*N+math.sin(th)*B
                q=pts[i]+radius*normal
                s=math.hypot(q[0],q[1]);z=q[2]
                us,uphi,uz=field.velocity(s,z)
                phi=math.atan2(q[1],q[0])
                u=np.array([us*math.cos(phi)-uphi*math.sin(phi),us*math.sin(phi)+uphi*math.cos(phi),uz])
                dots.append(np.dot(u,normal));speeds.append(np.linalg.norm(u))
                pressures.append(field.psi(s,z))
        dots=np.array(dots);scale=np.sqrt(np.mean(np.asarray(speeds)**2))
        rec.append({'radius_over_a':radius/field.a,
                    'normal_flow_rms_over_urms':float(np.sqrt(np.mean(dots*dots))/scale),
                    'normal_flow_max_over_urms':float(np.max(np.abs(dots))/scale),
                    'signed_flux_mean_over_urms':float(np.mean(dots)/scale),
                    'psi_on_surface_span':float(np.ptp(pressures)),
                    'surface_points':len(dots)})
    return rec


def poincare_shear(field, s0, ds_values=(-.002,-.001,0.,.001,.002)):
    res=[]
    for ds in ds_values:
        w=poloidal_cycle(field,(s0+ds)*field.a,rtol=2e-10,atol=2e-10)
        res.append({'ds_over_a':ds,'W':w['W'],
                    'four_cycle_phase_slip_rad':float(2*math.pi*4*(w['W']-.75))})
    deriv=(res[3]['W']-res[1]['W'])/(.002)
    return {'samples':res,'dW_d_s_over_a':float(deriv),
            'nonzero_shear':bool(abs(deriv)>1e-4),
            'interpretation':'field-line pitch shear, NOT time-dependent Euler stability'}


def advect_material_surface(field, curve, radius=.004, core_samples=60,
                            ring_samples=10, periods=(0,1,2,4)):
    """Exact prescribed-steady-field material advection of a knotted surface.

    This is kinematic Lagrangian advection. It does NOT perturb/recompute
    velocity, vorticity, or pressure via the coupled Euler PDE. Results are
    finite-time localization diagnostics, not nonlinear Euler stability.
    """
    xyz=curve['xyz']; N=len(xyz)-1
    idx=np.linspace(0,N-1,core_samples,endpoint=False,dtype=int)
    seed=[]
    for i in idx:
        p=xyz[i];s=math.hypot(p[0],p[1]);phi=math.atan2(p[1],p[0]);z=p[2]
        us,uphi,uz=field.velocity(s,z)
        vel=np.array([us*math.cos(phi)-uphi*math.sin(phi),us*math.sin(phi)+uphi*math.cos(phi),uz])
        T=vel/np.linalg.norm(vel)
        ref=np.array([0.,0.,1.]) if abs(T[2])<.75 else np.array([0.,1.,0.])
        e1=np.cross(T,ref);e1/=np.linalg.norm(e1);e2=np.cross(T,e1)
        for th in np.linspace(0,2*math.pi,ring_samples,endpoint=False):
            seed.append(p+radius*(math.cos(th)*e1+math.sin(th)*e2))
    seed=np.array(seed);num=len(seed)
    def rhs(t,v):
        y=v.reshape(num,3)
        s=np.hypot(y[:,0],y[:,1]);z=y[:,2]
        us,uphi,uz=field.velocity(s,z)
        cp=y[:,0]/s;sp=y[:,1]/s
        return np.column_stack([us*cp-uphi*sp,us*sp+uphi*cp,uz]).ravel()
    period=curve['T'];times=np.array(periods,dtype=float)*period
    sol=solve_ivp(rhs,(0.,times[-1]),seed.ravel(),t_eval=times,
                  rtol=1e-8,atol=1e-9,max_step=min(.03,period/40))
    if not sol.success:raise RuntimeError(sol.message)
    tree=cKDTree(xyz[:-1]);data=[]
    for tick,vec in zip(times,sol.y.T):
        pts=vec.reshape(num,3);dist=tree.query(pts)[0]
        data.append({'core_periods':float(tick/period),
                     'distance_to_core_rms_over_initial_radius':float(np.sqrt(np.mean(dist**2))/radius),
                     'distance_to_core_max_over_initial_radius':float(np.max(dist)/radius),
                     'max_outside_separatrix':float(max(0.,np.max(np.linalg.norm(pts,axis=1))-field.a))})
    return {'schema':'A063-KINEMATIC-ADVECTION-020','tube_radius_over_a':radius/field.a,
            'n_surface_markers':num,'integrator':'scipy solve_ivp RK45',
            'self_consistent_3d_euler':False,
            'diagnostics':data}
