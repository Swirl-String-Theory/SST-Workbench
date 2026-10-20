"""Biliner-intersection, failure-explicit vortex lines in a 3D complex GP field.

Each nonzero oriented plaquette contains a zero of the bilinear interpolation
of real/imag psi. Solve this zero in fractional cell coordinates and assemble
crossings into graph cycles. The bilinear zero is a *diagnostic* and is not
an isotopy-certified topological reconstruction. Ambiguity is never promoted.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np
from scipy.optimize import least_squares
from .lattice_graph_legacy import ORIENTED_FACES,windings,component_diagnostics


def bilinear_zero(corners:np.ndarray,tol:float=1e-8):
    """Unique interior zero of a bilinear complex face, or fail-closed.

    If the zero lies on the face boundary, two adjacent plaquettes may
    describe the same physical core. Signal boundary-degeneracy with
    (None, 0.0) rather than counting an apparent branching event.
    """
    a,z10,z11,z01=np.asarray(corners,dtype=complex)
    b=z10-a;c=z01-a;d=z11-z10-z01+a
    scale=max(1.,float(np.max(np.abs(corners))))
    co=[(b*np.conj(d)).imag,(a*np.conj(d)+b*np.conj(c)).imag,(a*np.conj(c)).imag]
    if abs(co[0])>1e-15:roots=np.roots(co)
    elif abs(co[1])>1e-15:roots=[-co[2]/co[1]]
    else:roots=[]
    candidates=[]
    for u in roots:
        if abs(np.imag(u))>1e-8:continue
        u=float(np.real(u)); v=-(a+b*u)/(c+d*u) if abs(c+d*u)>1e-14 else np.nan
        if not np.isfinite(v) or abs(np.imag(v))>1e-8:continue
        v=float(np.real(v))
        if not (-1e-8<=u<=1+1e-8 and -1e-8<=v<=1+1e-8):continue
        residual=abs(a+b*u+c*v+d*u*v)/scale
        if residual<tol:candidates.append((u,v,residual))
    if len(candidates)==1:
        u,v,r=candidates[0]
        if min(u,v,1-u,1-v)<1e-7:return None,0.0
        return np.array([u,v],float),r
    if len(candidates)>1:return None,0.0
    # Numeric fallback for poorly conditioned coefficients; no extrapolation.
    def f(uv):
        u,v=uv;z=a+b*u+c*v+d*u*v
        return np.array([z.real,z.imag])/scale
    def jac(uv):
        u,v=uv;zu=b+d*v;zv=c+d*u
        return np.array([[zu.real,zv.real],[zu.imag,zv.imag]])/scale
    best=None
    for guess in ([.5,.5],[.2,.2],[.8,.8],[.2,.8],[.8,.2]):
        res=least_squares(f,guess,jac=jac,bounds=([0.,0.],[1.,1.]),
                          xtol=1e-12,gtol=1e-12,ftol=1e-12,max_nfev=45)
        err=float(np.linalg.norm(f(res.x)))
        if best is None or err<best[1]:best=(res.x,err)
        if err<tol:break
    uv,err=best
    if err>=tol:return None,err
    if min(*uv,1-uv[0],1-uv[1])<1e-7:return None,0.0
    return uv,err


def _corner(psi,p,axis):
    q=list(p);q[axis]=(q[axis]+1)%len(psi);return psi[tuple(q)]


def subgrid_filaments(psi:np.ndarray,box:float=2*np.pi):
    psi=np.asarray(psi);w=windings(psi);n=len(psi);dx=box/n
    # Coordinates of zero-crossings on each oriented face, in grid units.
    oriented=[];ad=defaultdict(list);fail=[];all_res=[]
    for ia,ja,norm,name in ORIENTED_FACES:
        for idx in np.argwhere(w[name]!=0):
            p=tuple(map(int,idx));q=list(p);q[ia]=(q[ia]+1)%n
            z00=psi[p];z10=psi[tuple(q)];q[ja]=(q[ja]+1)%n
            z11=psi[tuple(q)];q=list(p);q[ja]=(q[ja]+1)%n
            z01=psi[tuple(q)]
            uv,res=bilinear_zero(np.array([z00,z10,z11,z01]))
            all_res.append(res)
            if uv is None:
                fail.append({'face':name,'index':list(p),'residual':float(res),
                             'reason':'BOUNDARY_DEGENERATE' if res==0. else 'NO_UNIQUE_INTERIOR_BILINEAR_ZERO'})
                continue
            loc=np.array(p,float);loc[ia]+=uv[0];loc[ja]+=uv[1]
            other=list(p);other[norm]=(other[norm]-1)%n
            a,b=tuple(other),p;sign=int(w[name][p]);
            if sign<0:a,b=b,a
            eid=len(oriented);oriented.append({'a':a,'b':b,'cross':loc,'normal':norm,'sign':sign,'eid':eid})
            ad[a].append(eid);ad[b].append(eid)
    incoming=defaultdict(list);outgoing=defaultdict(list)
    for edge in oriented:
        outgoing[edge['a']].append(edge['eid']);incoming[edge['b']].append(edge['eid'])
    nodes=set(ad)
    defective=[p for p in nodes if len(ad[p])!=2 or len(incoming[p])!=1 or len(outgoing[p])!=1]
    seen=set();components=[]
    for start in sorted(nodes):
        if start in seen:continue
        todo=[start];verts={start};edges=set()
        while todo:
            p=todo.pop();seen.add(p)
            for eid in ad[p]:
                edges.add(eid);e=oriented[eid];q=e['b'] if e['a']==p else e['a']
                if q not in verts:verts.add(q);todo.append(q)
        simple=all(len(ad[p])==2 and len(incoming[p])==1 and len(outgoing[p])==1 for p in verts)
        points=[];h=None;stepmax=None;length=None
        if simple and edges:
            p=min(verts);origin=p;walk=[];touched=set()
            for _ in range(len(edges)+1):
                if p in touched:break
                touched.add(p);eid=outgoing[p][0];walk.append(eid);p=oriented[eid]['b']
            simple=p==origin and len(walk)==len(edges) and len(touched)==len(verts)
            if simple:
                pts=np.array([oriented[eid]['cross'] for eid in walk]);raw=np.roll(pts,-1,axis=0)-pts
                dif=raw-n*np.rint(raw/n)
                winding_vec=np.rint(np.sum(dif,axis=0)/n).astype(int)
                if not np.allclose(np.sum(dif,axis=0)/n,winding_vec,atol=1e-6):simple=False
                else:
                    h=winding_vec.tolist()
                    path=np.vstack([pts[0],pts[0]+np.cumsum(dif[:-1],axis=0)])
                    points=(path*dx).tolist()
                    length=float(np.linalg.norm(dif,axis=1).sum()*dx)
                    stepmax=float(np.linalg.norm(dif,axis=1).max()*dx)
        components.append({'edges':len(edges),'vertices':len(verts),
                           'simple_oriented_cycle':bool(simple),'periodic_homology':h,
                           'subgrid_polyline':points if simple else None,
                           'subgrid_length':length,'max_edge_step':stepmax,
                           'isotopy_certified':False,'knot_type':None})
    graph=component_diagnostics(psi)
    return {'schema':'A069-V061-SUBGRID-ZEROS-1','grid_n':n,'box':box,'dx':dx,
      'faces_with_winding':int(sum(int(np.count_nonzero(a)) for a in w.values())),
      'localized_crossings':len(oriented),'unlocalized_faces':len(fail),'boundary_degenerate_faces':sum(f['reason']=='BOUNDARY_DEGENERATE' for f in fail),
      'max_bilinear_zero_residual':max(all_res) if all_res else 0.,
      'failures':fail[:24],'components':components,'components_count':len(components),
      'ambiguous_lattice_junctions':len(defective),'dual_graph_consistent':graph['graph_consistent'],
      'subgrid_reconstruction_qualified':bool(not fail and not defective and all(c['simple_oriented_cycle'] for c in components)),
      'knot_type_certified':False,'physical_reconnection_certified':False,
      'status':'SUBGRID_GEOMETRY_DIAGNOSTIC_ONLY'}


def compare_filaments(a:dict,b:dict):
    """Conservative multi-snapshot diagnostics, not GP material tracer identity."""
    ca=[x for x in a['components'] if x['simple_oriented_cycle']]; cb=[x for x in b['components'] if x['simple_oriented_cycle']]
    ok=a['subgrid_reconstruction_qualified'] and b['subgrid_reconstruction_qualified'] and len(ca)==len(cb)
    return {'schema':'A069-V061-SUBGRID-SNAPSHOT-COMPARISON-1',
        'before_components':len(ca),'after_components':len(cb),
        'before_lengths':[c['subgrid_length'] for c in ca],
        'after_lengths':[c['subgrid_length'] for c in cb],
        'graph_correspondence_possible':bool(ok),'ambient_isotopy_certified':False,
        'reconnection_certified':False,
        'topology_status':'UNRESOLVED',
        'reason':'Subgrid face zeros and matching component counts are insufficient for ambient isotopy and reconnection claims.'}


def spectral_grid_shift(psi:np.ndarray,box:float, shift_cells=(.37,.29,.41)):
    """Coordinate-origin diagnostic using the existing periodic Fourier basis.

    Returns psi(x + delta); changing the sampled origin must not be mistaken
    for a new independent physical simulation. Compare phase-defect graphs
    under modest subcell shifts to expose grid-aligned aliasing.
    """
    n=len(psi);k=2*np.pi*np.fft.fftfreq(n,d=box/n)
    delta=np.asarray(shift_cells,float)*box/n
    factor=np.exp(1j*(k[:,None,None]*delta[0]+k[None,:,None]*delta[1]+k[None,None,:]*delta[2]))
    return np.fft.ifftn(np.fft.fftn(psi)*factor)
