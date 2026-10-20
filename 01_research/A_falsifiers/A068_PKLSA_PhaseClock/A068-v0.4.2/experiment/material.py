"""A068 v0.4.2 - advected Lagrangian toroidal surface diagnostics.

Material surface != vorticity tube: qualify omega dot n separately at each time.
All coordinates and times are dimensionless, periodic box [0,2pi)^3.
"""
from __future__ import annotations
import numpy as np
from scipy.ndimage import map_coordinates
from .euler3d import L, normalized_components


def sample_vector(grid, vec, positions):
    """Trilinear, cell-centred, periodic samples of grid vector field."""
    pts=np.asarray(positions,float).reshape(-1,3)
    coords=((pts%L)/grid.dx-0.5).T
    # scipy ndimage wrap differs at seam: use modulo n, grid-padding for exact periodicity
    padded=np.pad(vec,((0,0),(1,1),(1,1),(1,1)),mode='wrap')
    shifted=(coords%grid.n)+1
    return np.stack([map_coordinates(padded[c],shifted,order=1,mode='nearest') for c in range(3)],axis=-1).reshape(np.shape(positions))


def create_torus(components, radius=0.12, sections=32, sides=10):
    """Piecewise-linear closed centerline, parallel-transport frame; no assumed vortex property."""
    c=normalized_components(components)[0][0]
    if c.shape[0]<8: raise ValueError('At least eight native vertices needed')
    # Unwrap centreline in periodic box before arclength parameterization.
    diff=(np.roll(c,-1,axis=0)-c+L/2)%L-L/2
    edges=np.linalg.norm(diff,axis=1)
    if np.any(edges<1e-9): raise ValueError('Degenerate native geometry')
    arc=np.r_[0,np.cumsum(edges)]; total=arc[-1]
    pts=np.vstack([c[0]+np.cumsum(np.vstack([np.zeros(3),diff]),axis=0)])
    s=np.linspace(0,total,sections,endpoint=False)
    xyz=np.stack([np.interp(s,arc,pts[:,j]) for j in range(3)],axis=1)
    d=np.roll(xyz,-1,axis=0)-np.roll(xyz,1,axis=0)
    tangent=d/np.linalg.norm(d,axis=1)[:,None]
    v=np.array([0.,0.,1.]);
    if abs(np.dot(v,tangent[0]))>.9: v=np.array([0.,1.,0.])
    v-=np.dot(v,tangent[0])*tangent[0];v/=np.linalg.norm(v)
    normals=[v.copy()]
    def rotate(n,a,b):
        axis=np.cross(a,b); cs=float(np.clip(np.dot(a,b),-1,1));sn=np.linalg.norm(axis)
        if sn<1e-12:return n.copy()
        axis/=sn; angle=np.arctan2(sn,cs)
        return n*np.cos(angle)+np.cross(axis,n)*np.sin(angle)+axis*np.dot(axis,n)*(1-np.cos(angle))
    for j in range(1,sections):
        v=rotate(v,tangent[j-1],tangent[j]);v-=np.dot(v,tangent[j])*tangent[j];v/=np.linalg.norm(v);normals.append(v.copy())
    residual=rotate(v,tangent[-1],tangent[0]);
    angle=np.arctan2(np.dot(np.cross(residual,normals[0]),tangent[0]),np.dot(residual,normals[0]))
    # Distribute seam twist; avoids a frame jump, does not certify topology.
    nn=[]
    for j,n in enumerate(normals):
        theta=angle*j/sections; b=np.cross(tangent[j],n)
        nn.append(np.cos(theta)*n+np.sin(theta)*b)
    nn=np.array(nn);b=np.cross(tangent,nn)
    a=2*np.pi*np.arange(sides)/sides
    surface=xyz[:,None,:]+radius*(np.cos(a)[None,:,None]*nn[:,None,:]+np.sin(a)[None,:,None]*b[:,None,:])
    if radius<=0 or radius>=L/4: raise ValueError('Invalid tube radius')
    # toroidal quads; both wrap, no artificial caps
    return surface,{'sections':sections,'sides':sides,'radius':radius,'length':float(total),'seam_twist':float(angle)}


def geometry(surface):
    """Triangle area normals and signed enclosed volume, periodic-unwrapped mesh."""
    A=np.asarray(surface,float); m,k,_=A.shape
    a=A
    b=np.roll(a,-1,axis=0)
    c=np.roll(a,-1,axis=1)
    d=np.roll(b,-1,axis=1)
    p=np.concatenate([a.reshape(-1,3),b.reshape(-1,3)],axis=0)
    q=np.concatenate([b.reshape(-1,3),d.reshape(-1,3)],axis=0)
    r=np.concatenate([c.reshape(-1,3),c.reshape(-1,3)],axis=0)
    area_vec=.5*np.cross(q-p,r-p)
    centroids=(p+q+r)/3
    area=np.linalg.norm(area_vec,axis=1)
    # Signed volume with translated origin for better conditioning.
    center=np.mean(a.reshape(-1,3),axis=0)
    vol=float(np.sum(np.einsum('ij,ij->i',p-center,np.cross(q-center,r-center)))/6)
    return {'volume_signed':vol,'volume_abs':abs(vol),'area':float(np.sum(area)),'area_vec':area_vec,'centroids':centroids,'triangle_areas':area}


def diagnostics(grid,U,surface,volume0=None):
    geom=geometry(surface)
    omega=sample_vector(grid,grid.curl(U),geom['centroids'])
    avec=geom['area_vec']; strength=np.linalg.norm(omega,axis=1)
    normals=avec/np.maximum(geom['triangle_areas'][:,None],1e-30)
    cos=np.abs(np.sum(omega*normals,axis=1))/np.maximum(strength,1e-12)
    weights=geom['triangle_areas'];mean_cos=float(np.average(cos,weights=weights))
    rms_cos=float(np.sqrt(np.average(cos*cos,weights=weights)))
    # Closed-surface net vortex flux approaches zero even if locally non-tangent;
    # DO NOT use it as a vortex-tube qualification condition.
    net_flux=float(np.sum(np.sum(omega*avec,axis=1)))
    out={'volume_abs':geom['volume_abs'],'area':geom['area'],
         'vorticity_tangency_mean_abs_cos':mean_cos,'vorticity_tangency_rms_abs_cos':rms_cos,
         'vorticity_tangency_max_abs_cos':float(np.max(cos)),
         'closed_surface_net_vorticity_flux':net_flux}
    if volume0 is not None:
        out['material_volume_relative_drift']=abs(geom['volume_abs']-volume0)/max(abs(volume0),1e-30)
    return out


def rk4_advect(grid,U,surface,dt):
    """Advance Euler and material nodes through same classical RK4 stage states."""
    empty=np.empty((0,3,grid.n,grid.n,grid.n),dtype=float)
    k1,_=grid.rhs(U,empty);h1=sample_vector(grid,U,surface)
    U2=U+dt*k1/2; X2=surface+dt*h1/2
    k2,_=grid.rhs(U2,empty);h2=sample_vector(grid,U2,X2)
    U3=U+dt*k2/2; X3=surface+dt*h2/2
    k3,_=grid.rhs(U3,empty);h3=sample_vector(grid,U3,X3)
    U4=U+dt*k3; X4=surface+dt*h3
    k4,_=grid.rhs(U4,empty);h4=sample_vector(grid,U4,X4)
    next_U=grid.project(U+dt*(k1+2*k2+2*k3+k4)/6)
    next_s=surface+dt*(h1+2*h2+2*h3+h4)/6
    return next_U,next_s
