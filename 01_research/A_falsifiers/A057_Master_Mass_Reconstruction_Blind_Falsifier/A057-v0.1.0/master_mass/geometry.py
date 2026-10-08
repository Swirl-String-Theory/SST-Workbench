from __future__ import annotations
import numpy as np

def as_closed(points):
    p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3 or len(p)<4: raise ValueError('component must be Nx3 with N>=4')
    if np.linalg.norm(p[0]-p[-1]) < 1e-12*max(1.0,np.ptp(p,axis=0).max()): p=p[:-1]
    return p.copy()

def lengths(points):
    p=as_closed(points); d=np.roll(p,-1,axis=0)-p
    return np.linalg.norm(d,axis=1)

def total_length(components): return float(sum(lengths(c).sum() for c in components))

def resample_closed(points,n):
    p=as_closed(points); q=np.vstack([p,p[0]])
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1); s=np.concatenate([[0.0],np.cumsum(ds)])
    if s[-1]<=0:raise ValueError('zero length component')
    t=np.linspace(0.0,s[-1],int(n)+1)[:-1]
    out=np.column_stack([np.interp(t,s,q[:,k]) for k in range(3)])
    return out

def unit_tangents(points):
    p=as_closed(points); d=np.roll(p,-1,axis=0)-p
    n=np.linalg.norm(d,axis=1); return d/np.maximum(n[:,None],1e-15)

def periodic_derivatives(points):
    p=as_closed(points); n=len(p); L=lengths(p).sum(); ds=L/n
    d1=(np.roll(p,-1,axis=0)-np.roll(p,1,axis=0))/(2*ds)
    d2=(np.roll(p,-1,axis=0)-2*p+np.roll(p,1,axis=0))/(ds*ds)
    d3=(np.roll(p,-2,axis=0)-2*np.roll(p,-1,axis=0)+2*np.roll(p,1,axis=0)-np.roll(p,2,axis=0))/(2*ds**3)
    return d1,d2,d3,ds

def curvature_torsion(points):
    d1,d2,d3,ds=periodic_derivatives(points)
    cross=np.cross(d1,d2); nc=np.linalg.norm(cross,axis=1); nd=np.linalg.norm(d1,axis=1)
    k=nc/np.maximum(nd**3,1e-15)
    tau=np.einsum('ij,ij->i',cross,d3)/np.maximum(nc**2,1e-15)
    return k,tau,ds

def approximate_reach(components):
    """Approximate geometric reach/thickness radius.

    The self-distance branch uses a doubly-critical chord proxy rather than the
    nearest non-neighbour sample.  This avoids the spurious O(ds) thickness that
    a naive point-distance estimator produces under mesh refinement (e.g. a circle).
    """
    comps=[as_closed(c) for c in components]
    curv_rad=[]; tang=[]
    for c in comps:
        k,_,_=curvature_torsion(c); km=float(np.nanmax(k)) if len(k) else 0.0
        if km>0:curv_rad.append(1.0/km)
        d1,_,_,_=periodic_derivatives(c); tt=d1/np.maximum(np.linalg.norm(d1,axis=1)[:,None],1e-15);tang.append(tt)
    local=min(curv_rad) if curv_rad else np.inf
    dcrit=np.inf
    # Same-component doubly-critical distance proxy: chord approximately normal
    # to both local tangents.  The arclength-index exclusion removes the local branch.
    tol=0.18
    for ci,a in enumerate(comps):
        n=len(a);tt=tang[ci];excl=max(3,n//20)
        for i in range(n):
            for j in range(i+1,n):
                sep=min(j-i,n-(j-i))
                if sep<=excl: continue
                r=a[j]-a[i];d=float(np.linalg.norm(r))
                if d<=1e-15: continue
                u=r/d
                if abs(float(np.dot(u,tt[i])))<=tol and abs(float(np.dot(u,tt[j])))<=tol:
                    dcrit=min(dcrit,d)
    # Cross-component closest distance is a direct thickness constraint.
    for i,a in enumerate(comps):
        for j in range(i+1,len(comps)):
            b=comps[j]
            for st in range(0,len(a),128):
                d=np.linalg.norm(a[st:st+128,None,:]-b[None,:,:],axis=2)
                if d.size:dcrit=min(dcrit,float(d.min()))
    nonlocal_r=0.5*dcrit if np.isfinite(dcrit) else np.inf
    r=min(local,nonlocal_r)
    if not np.isfinite(r) or r<=1e-12:
        L=total_length(comps); r=max(L/(2.0*np.pi*max(len(comps),1)),1e-6)
    return float(r),{"curvature_radius":float(local) if np.isfinite(local) else None,"half_doubly_critical_distance":float(nonlocal_r) if np.isfinite(nonlocal_r) else None,"dcritical_tangent_tolerance":tol}

def normalize_by_reach(components):
    comps=[as_closed(c) for c in components]
    allp=np.vstack(comps); center=allp.mean(axis=0)
    centered=[c-center for c in comps]
    reach,detail=approximate_reach(centered)
    return [c/reach for c in centered],reach,detail

def bishop_frame(points):
    p=as_closed(points); t=(np.roll(p,-1,axis=0)-np.roll(p,1,axis=0));t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-15)
    # initial normal from least-aligned Cartesian axis
    axes=np.eye(3); a=axes[np.argmin(np.abs(axes@t[0]))]
    n0=a-np.dot(a,t[0])*t[0]; n0/=np.linalg.norm(n0)
    n=np.zeros_like(p);n[0]=n0
    for i in range(len(p)-1):
        u=t[i];v=t[i+1]; axis=np.cross(u,v); s=np.linalg.norm(axis); c=np.clip(np.dot(u,v),-1,1)
        if s<1e-14: nn=n[i]
        else:
            k=axis/s; ang=np.arctan2(s,c); nn=n[i]*np.cos(ang)+np.cross(k,n[i])*np.sin(ang)+k*np.dot(k,n[i])*(1-np.cos(ang))
        nn-=np.dot(nn,v)*v; nn/=max(np.linalg.norm(nn),1e-15);n[i+1]=nn
    b=np.cross(t,n); b/=np.maximum(np.linalg.norm(b,axis=1)[:,None],1e-15)
    # transport last frame once more to t0 to measure holonomy
    u=t[-1];v=t[0];axis=np.cross(u,v);ss=np.linalg.norm(axis);cc=np.clip(np.dot(u,v),-1,1);nn=n[-1]
    if ss>=1e-14:
        k=axis/ss;ang=np.arctan2(ss,cc);nn=nn*np.cos(ang)+np.cross(k,nn)*np.sin(ang)+k*np.dot(k,nn)*(1-np.cos(ang))
    nn-=np.dot(nn,v)*v;nn/=max(np.linalg.norm(nn),1e-15)
    hol=np.arctan2(np.dot(np.cross(n[0],nn),t[0]),np.dot(n[0],nn))
    return t,n,b,float(hol)

def writhe(points):
    p=as_closed(points); q=np.roll(p,-1,axis=0); dl=q-p; mid=.5*(p+q); n=len(p); val=0.0
    for i in range(n):
        r=mid[i]-mid; den=np.linalg.norm(r,axis=1)**3
        idx=np.arange(n); sep=np.minimum((idx-i)%n,(i-idx)%n); mask=sep>1
        num=np.einsum('ij,ij->i',np.cross(dl[i],dl),r)
        val+=np.sum(np.where(mask,num/np.maximum(den,1e-18),0.0))
    return float(val/(4*np.pi))

def linking_number(a,b):
    a=as_closed(a);b=as_closed(b); da=np.roll(a,-1,axis=0)-a;db=np.roll(b,-1,axis=0)-b;ma=.5*(a+np.roll(a,-1,axis=0));mb=.5*(b+np.roll(b,-1,axis=0));v=0.0
    for i in range(len(a)):
        r=ma[i]-mb; den=np.linalg.norm(r,axis=1)**3; num=np.einsum('ij,ij->i',np.cross(da[i],db),r);v+=np.sum(num/np.maximum(den,1e-18))
    return float(v/(4*np.pi))

def descriptors(components):
    comps=[as_closed(c) for c in components]; reach,rd=approximate_reach(comps); L=total_length(comps)
    bend=tors=tot_tau=wr=0.0; hol=[]
    for c in comps:
        k,tau,ds=curvature_torsion(c); bend+=float(np.sum(k*k)*ds*reach);tors+=float(np.sum(tau*tau)*ds*reach);tot_tau+=float(np.sum(tau)*ds);wr+=writhe(c);hol.append(bishop_frame(c)[3])
    links=[]
    for i in range(len(comps)):
        for j in range(i+1,len(comps)):links.append(linking_number(comps[i],comps[j]))
    return {"component_count":len(comps),"length":L,"reach":reach,"ropelength_proxy":L/reach,"bending":bend,"torsion2":tors,"total_torsion":tot_tau,"writhe_sum":wr,"bishop_holonomy_abs_sum":float(np.sum(np.abs(hol))),"pairwise_linking":links,"linking_abs_sum":float(np.sum(np.abs(links))),"mutual_helicity_unit_circulation":float(2.0*np.sum(links)),"reach_detail":rd}

def rigid_transform(components):
    # deterministic proper rotation and translation
    ax=np.array([0.3,-0.5,0.8]);ax/=np.linalg.norm(ax);ang=0.731
    K=np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])
    R=np.eye(3)+np.sin(ang)*K+(1-np.cos(ang))*(K@K);tr=np.array([1.7,-0.9,0.4])
    return [np.asarray(c)@R.T+tr for c in components]
