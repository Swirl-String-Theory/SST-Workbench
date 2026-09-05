from __future__ import annotations
import math
import numpy as np
from . import native

def edge_stats(p):
    e=np.roll(p,-1,axis=0)-p; d=np.linalg.norm(e,axis=1)
    return {'length':float(d.sum()),'edge_mean':float(d.mean()),'edge_std':float(d.std()),'edge_cv':float(d.std()/d.mean()) if d.mean()>0 else math.nan,'edge_ratio':float(d.max()/d.min()) if d.min()>0 else math.inf}

def curvature(p):
    pm=np.roll(p,1,axis=0); pp=np.roll(p,-1,axis=0)
    u=p-pm; v=pp-p; chord=pp-pm
    den=np.linalg.norm(u,axis=1)*np.linalg.norm(v,axis=1)*np.linalg.norm(chord,axis=1)
    num=2.0*np.linalg.norm(np.cross(u,v),axis=1)
    return np.divide(num,den,out=np.zeros_like(num),where=den>1e-15)

def torsion(p):
    em=p-np.roll(p,1,axis=0); ep=np.roll(p,-1,axis=0)-p; epp=np.roll(p,-2,axis=0)-np.roll(p,-1,axis=0)
    b0=np.cross(em,ep); b1=np.cross(ep,epp)
    n0=np.linalg.norm(b0,axis=1); n1=np.linalg.norm(b1,axis=1)
    good=(n0>1e-12)&(n1>1e-12)
    b0[good]/=n0[good,None]; b1[good]/=n1[good,None]
    t=ep/np.maximum(np.linalg.norm(ep,axis=1)[:,None],1e-15)
    ang=np.arctan2(np.einsum('ij,ij->i',t,np.cross(b0,b1)),np.einsum('ij,ij->i',b0,b1))
    ds=0.5*(np.linalg.norm(em,axis=1)+np.linalg.norm(ep,axis=1))
    out=np.zeros(len(p)); out[good]=ang[good]/np.maximum(ds[good],1e-15)
    return out

def _segment_distance(a,b,c,d):
    # compact exact fallback
    u=b-a; v=d-c; w=a-c; A=u@u; B=u@v; C=v@v; D=u@w; E=v@w; den=A*C-B*B; eps=1e-15
    if A<eps and C<eps: return float(np.linalg.norm(a-c))
    if A<eps: s=0.; t=np.clip(E/C,0,1)
    elif C<eps: t=0.; s=np.clip(-D/A,0,1)
    else:
        s=np.clip((B*E-C*D)/den,0,1) if abs(den)>eps else 0.
        t=(B*s+E)/C
        if t<0: t=0.; s=np.clip(-D/A,0,1)
        elif t>1: t=1.; s=np.clip((B-D)/A,0,1)
    return float(np.linalg.norm((a+s*u)-(c+t*v)))

def sampled_dcsd_python(p,skip=4):
    p=np.asarray(p,float); n=len(p); best=math.inf
    def d(i,j): return float(np.linalg.norm(p[i%n]-p[j%n]))
    for i in range(n):
        for j in range(i+1,n):
            if min(abs(i-j),n-abs(i-j))<=skip: continue
            dij=d(i,j)
            if dij<=d(i-1,j) and dij<=d(i+1,j) and dij<=d(i,j-1) and dij<=d(i,j+1): best=min(best,dij)
    return best

def writhe_python(p,skip=4):
    n=len(p); wr=acn=0.0
    for i in range(n):
        di=p[(i+1)%n]-p[i]; mi=0.5*(p[(i+1)%n]+p[i])
        for j in range(i+1,n):
            if min(abs(i-j),n-abs(i-j))<=skip: continue
            dj=p[(j+1)%n]-p[j]; mj=0.5*(p[(j+1)%n]+p[j]); r=mi-mj; rn=np.linalg.norm(r)
            if rn<1e-14: continue
            val=float(r@np.cross(di,dj)/(rn**3)); wr+=2*val; acn+=2*abs(val)
    f=1/(4*np.pi); return wr*f,acn*f

def flatness(p):
    c=p-p.mean(axis=0); vals=np.linalg.eigvalsh(c.T@c/len(c)); vals=np.maximum(vals,0); vals.sort()
    return float(np.sqrt(vals[0]/vals[-1])) if vals[-1]>0 else 0.0, vals

def radius_gyration(p): return float(np.sqrt(np.mean(np.sum((p-p.mean(axis=0))**2,axis=1))))

def bishop_closure_mismatch(p):
    t=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0); t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-15)
    axes=np.eye(3); a=axes[np.argmin(np.abs(axes@t[0]))]; n=a-(a@t[0])*t[0]; n/=np.linalg.norm(n); n0=n.copy()
    for i in range(len(p)):
        ta=t[i]; tb=t[(i+1)%len(p)]; v=np.cross(ta,tb); s=np.linalg.norm(v); c=float(np.clip(ta@tb,-1,1))
        if s>1e-14:
            axis=v/s; ang=np.arctan2(s,c)
            n=n*np.cos(ang)+np.cross(axis,n)*np.sin(ang)+axis*(axis@n)*(1-np.cos(ang))
        n=n-(n@tb)*tb; n/=max(np.linalg.norm(n),1e-15)
    return float(abs(np.arctan2(t[0]@np.cross(n0,n),np.clip(n0@n,-1,1))))

def inter_component_min(a,b):
    best=math.inf
    for i in range(len(a)):
        for j in range(len(b)):
            best=min(best,_segment_distance(a[i],a[(i+1)%len(a)],b[j],b[(j+1)%len(b)]))
    return best

def linking_python(a,b):
    lk=acn=0.0
    for i in range(len(a)):
        di=a[(i+1)%len(a)]-a[i]; mi=.5*(a[(i+1)%len(a)]+a[i])
        for j in range(len(b)):
            dj=b[(j+1)%len(b)]-b[j]; mj=.5*(b[(j+1)%len(b)]+b[j]); r=mi-mj; rn=np.linalg.norm(r)
            if rn<1e-14: continue
            v=float(r@np.cross(di,dj)/(rn**3)); lk+=v; acn+=abs(v)
    f=1/(4*np.pi); return lk*f,acn*f

def analyze_components(components,neighbor_skip=4,auto_build_native=True):
    native_ok=native.load(auto_build_native) is not None
    cs=[]
    for p in components:
        p=np.asarray(p,float); es=edge_stats(p); k=curvature(p); tau=torsion(p); fl,eigs=flatness(p)
        md=native.sampled_dcsd(p,neighbor_skip) if native_ok else sampled_dcsd_python(p,neighbor_skip)
        wa=native.writhe_acn(p,neighbor_skip) if native_ok else writhe_python(p,neighbor_skip)
        rcurv=float(1/k.max()) if k.max()>0 else math.inf
        reach=min(rcurv,0.5*md)
        cs.append({**es,'point_count':len(p),'centroid':p.mean(axis=0),'radius_gyration':radius_gyration(p),
                   'curvature_mean':float(k.mean()),'curvature_rms':float(np.sqrt(np.mean(k*k))),'curvature_max':float(k.max()),'min_curvature_radius':rcurv,
                   'torsion_mean':float(tau.mean()),'torsion_rms':float(np.sqrt(np.mean(tau*tau))),'torsion_max_abs':float(np.max(np.abs(tau))),
                   'flatness':fl,'covariance_eigenvalues':eigs,'sampled_dcsd_proxy':float(md),'sampled_reach_proxy':float(reach),
                   'length_over_diameter_proxy':float(es['length']/(2*reach)) if reach>0 else math.inf,
                   'ropelength_radius_proxy':float(es['length']/reach) if reach>0 else math.inf,
                   'writhe_midpoint_proxy':wa[0],'acn_midpoint_proxy':wa[1],'bishop_closure_mismatch_rad':bishop_closure_mismatch(p)})
    m=len(components); lmat=np.zeros((m,m)); acnmat=np.zeros((m,m)); inter=math.inf
    for i in range(m):
        for j in range(i+1,m):
            val=native.linking_acn(components[i],components[j]) if native_ok else linking_python(components[i],components[j])
            lmat[i,j]=lmat[j,i]=val[0]; acnmat[i,j]=acnmat[j,i]=val[1]
            inter=min(inter,native.inter_min_distance(components[i],components[j]) if native_ok else inter_component_min(components[i],components[j]))
    total_length=sum(c['length'] for c in cs)
    reach=min([c['sampled_reach_proxy'] for c in cs]+([0.5*inter] if math.isfinite(inter) else []))
    return {'native_backend':native_ok,'native_backend_error':native.last_error(),'component_count':m,'components':cs,'total_length':total_length,
            'inter_component_min_distance':inter if math.isfinite(inter) else None,'linking_matrix_midpoint_proxy':lmat,'inter_acn_matrix_midpoint_proxy':acnmat,
            'global_sampled_reach_proxy':reach,'global_length_over_diameter_proxy':total_length/(2*reach) if reach>0 else math.inf,
            'global_ropelength_radius_proxy':total_length/reach if reach>0 else math.inf}
