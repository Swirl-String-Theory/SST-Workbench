from __future__ import annotations
import numpy as np
from .geometry import as_closed,bishop_frame


def _segments(components):
    mids=[]; dls=[]
    for c in components:
        p=as_closed(c);q=np.roll(p,-1,axis=0);mids.append(.5*(p+q));dls.append(q-p)
    return np.vstack(mids),np.vstack(dls)


def velocity_kernel(points, components, regularization=1.0):
    """Dimensionless regularized Biot--Savart velocity kernel.

    The physical factor Gamma/(4*pi*L*) is intentionally omitted.  With
    x=L* xhat the returned kernel is the dimensionless vector multiplying it.
    """
    x=np.asarray(points,dtype=float);mid,dl=_segments(components);out=np.zeros_like(x)
    a2=float(regularization)**2
    for st in range(0,len(x),128):
        xx=x[st:st+128]
        r=xx[:,None,:]-mid[None,:,:]
        den=(np.einsum('bij,bij->bi',r,r)+a2)**1.5
        cross=np.cross(dl[None,:,:],r)
        out[st:st+128]=np.sum(cross/np.maximum(den[:,:,None],1e-18),axis=1)
    return out


def tube_energy_kernel(components, core=1.0, radial_bins=2, angular_bins=8):
    """Quadrature of 0.5*|vhat|^2 over the union-by-sampling of component tubes.

    This is a core-tube diagnostic, not the complete all-space kinetic energy.
    Samples are attached to periodic Bishop frames.  Overlap is not de-duplicated;
    therefore the quantity is most reliable as a same-protocol comparative kernel.
    """
    comps=[as_closed(c) for c in components]; pts=[];weights=[]
    R=float(core); nr=int(radial_bins); nt=int(angular_bins); dr=R/nr
    for c in comps:
        _,n,b,_=bishop_frame(c);q=np.roll(c,-1,axis=0);ds=np.linalg.norm(q-c,axis=1);mid=.5*(c+q)
        # midpoint frame approximation
        nm=n;bm=b
        for ir in range(nr):
            rr=(ir+.5)*dr; area_ring=2*np.pi*rr*dr
            for ia in range(nt):
                ang=2*np.pi*(ia+.5)/nt
                off=rr*(np.cos(ang)*nm+np.sin(ang)*bm)
                pts.append(mid+off);weights.append(ds*(area_ring/nt))
    X=np.vstack(pts);W=np.concatenate(weights);V=velocity_kernel(X,comps,regularization=core)
    local=.5*np.einsum('ij,ij->i',V,V)
    return float(np.sum(local*W)),{"sample_count":int(len(X)),"radial_bins":nr,"angular_bins":nt,"core":R}
