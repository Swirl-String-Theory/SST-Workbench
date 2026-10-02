from __future__ import annotations
import math
import numpy as np
from .geometry import tangents

COMPONENT_KEYS = ('local','same_lobe','cross_lobe','transition')


def _eig_metrics(A):
    A=np.asarray(A,float)
    ev=np.linalg.eigvals(A)
    scale=float(np.max(np.abs(ev))) if len(ev) else 0.0
    mr=float(np.max(ev.real)) if len(ev) else 0.0
    return dict(
        eigenvalues=[{'re':float(z.real),'im':float(z.imag)} for z in ev],
        spectral_scale=scale,
        max_real=mr,
        normalized_growth=mr/max(scale,1e-12),
    )


def _cycdist(a:int,b:int,n:int)->int:
    d=abs(int(a)-int(b)); return min(d,n-d)


def c3_sector_participation(coeffs, names):
    z=np.asarray(coeffs,complex).reshape(-1)
    w=np.abs(z)**2; den=float(w.sum()) or 1.0
    groups={
        'm0': [i for i,n in enumerate(names) if n in ('tilt_0','breathe_0')],
        'E_tilt': [i for i,n in enumerate(names) if n in ('tilt_1','tilt_2')],
        'E_breathe': [i for i,n in enumerate(names) if n in ('breathe_1','breathe_2')],
    }
    out={k:float(w[idx].sum()/den) if idx else 0.0 for k,idx in groups.items()}
    out['E_total']=out['E_tilt']+out['E_breathe']
    out['tilt_total']=float(w[[i for i,n in enumerate(names) if n.startswith('tilt_')]].sum()/den)
    out['breathe_total']=float(w[[i for i,n in enumerate(names) if n.startswith('breathe_')]].sum()/den)
    return out


def modal_attribution(Jdict, names):
    """Exact first-order eigenvalue attribution using biorthogonal left/right eigenvectors.

    For J=sum J_c and right/left eigenvectors J v=lambda v, w^H J=lambda w^H,
    lambda_c = (w^H J_c v)/(w^H v), hence sum_c lambda_c=lambda up to roundoff.
    """
    J=np.asarray(Jdict['total'],float)
    vals, VR=np.linalg.eig(J)
    valsL, WL=np.linalg.eig(J.T.conj())
    order=np.argsort(vals.real)[::-1]
    rows=[]
    for rank,idx in enumerate(order):
        lam=vals[idx]; v=VR[:,idx]
        j=int(np.argmin(np.abs(valsL-np.conj(lam))))
        w=WL[:,j]
        den=np.vdot(w,v)
        if abs(den)<1e-12:
            den=complex(1.0,0.0)
        contrib={}
        for key in COMPONENT_KEYS:
            z=np.vdot(w,np.asarray(Jdict[key],float)@v)/den
            contrib[key]={'re':float(z.real),'im':float(z.imag)}
        s=sum(complex(contrib[k]['re'],contrib[k]['im']) for k in COMPONENT_KEYS)
        part=c3_sector_participation(v,names)
        dominant_sector=max(('m0','E_tilt','E_breathe'),key=lambda q:part[q])
        rows.append(dict(
            rank_by_real=int(rank),
            eigen_index=int(idx),
            eigenvalue={'re':float(lam.real),'im':float(lam.imag)},
            right_coefficients=[{'re':float(z.real),'im':float(z.imag)} for z in v],
            sector_participation=part,
            dominant_sector=dominant_sector,
            contributions=contrib,
            reconstruction={'re':float(s.real),'im':float(s.imag)},
            reconstruction_abs_error=float(abs(s-lam)),
        ))
    return rows


def component_ablation(Jdict):
    J=np.asarray(Jdict['total'],float)
    out={'full':_eig_metrics(J)}
    for key in COMPONENT_KEYS:
        out[f'without_{key}']=_eig_metrics(J-np.asarray(Jdict[key],float))
        out[f'{key}_only']=_eig_metrics(np.asarray(Jdict[key],float))
    return out


def c3_block_diagnostics(J, names):
    J=np.asarray(J,float)
    m0=[i for i,n in enumerate(names) if n in ('tilt_0','breathe_0')]
    E=[i for i in range(len(names)) if i not in m0]
    norm=max(float(np.linalg.norm(J)),1e-30)
    if not m0 or not E:
        return dict(block_leakage=float('nan'),m0_indices=m0,E_indices=E)
    leak=math.sqrt(float(np.linalg.norm(J[np.ix_(m0,E)])**2+np.linalg.norm(J[np.ix_(E,m0)])**2))/norm
    return dict(
        block_leakage=float(leak),
        m0_indices=m0,E_indices=E,
        m0_block_norm_fraction=float(np.linalg.norm(J[np.ix_(m0,m0)])/norm),
        E_block_norm_fraction=float(np.linalg.norm(J[np.ix_(E,E)])/norm),
    )


def closest_cross_lobe_pairs(x, labels, split, *, top_k=12, skip=8, exclusion=4):
    x=np.asarray(x,float); labels=np.asarray(labels,int); n=len(x); t=tangents(x)
    candidates=[]
    for i in range(n):
        for j in range(i+1,n):
            if _cycdist(i,j,n)<=skip or labels[i]==labels[j]:
                continue
            d=float(np.linalg.norm(x[i]-x[j]))
            candidates.append((d,i,j))
    candidates.sort(key=lambda z:z[0])
    selected=[]
    for d,i,j in candidates:
        duplicate=False
        for _,a,b in selected:
            same=(_cycdist(i,a,n)<=exclusion and _cycdist(j,b,n)<=exclusion)
            swap=(_cycdist(i,b,n)<=exclusion and _cycdist(j,a,n)<=exclusion)
            if same or swap:
                duplicate=True; break
        if duplicate: continue
        selected.append((d,i,j))
        if len(selected)>=int(top_k): break
    rows=[]
    for d,i,j in selected:
        nh=(x[i]-x[j])/max(d,1e-30)
        cos=float(np.dot(t[i],t[j])); cos=max(-1.0,min(1.0,cos))
        rates={k:float(np.dot(nh,np.asarray(v)[i]-np.asarray(v)[j])) for k,v in split.items()}
        rows.append(dict(
            i=int(i),j=int(j),lobe_i=int(labels[i]),lobe_j=int(labels[j]),distance=d,
            tangent_cos=cos,tangent_angle_deg=float(np.degrees(np.arccos(cos))),
            antiparallelness=float(-cos),distance_rates=rates,
        ))
    cr=np.asarray([r['distance_rates'].get('cross_lobe',np.nan) for r in rows],float)
    anti=np.asarray([r['antiparallelness'] for r in rows],float)
    finite=np.isfinite(cr)
    if finite.any():
        pos=float(np.mean(cr[finite]>0)); med=float(np.median(cr[finite])); mean=float(np.mean(cr[finite]))
    else:
        pos=med=mean=float('nan')
    corr=float('nan')
    if finite.sum()>=3 and np.std(cr[finite])>1e-15 and np.std(anti[finite])>1e-15:
        corr=float(np.corrcoef(cr[finite],anti[finite])[0,1])
    return dict(pairs=rows,positive_fraction=pos,median_cross_rate=med,mean_cross_rate=mean,antiparallelness_rate_correlation=corr)


def _segment_field_from_lobe(x, labels, source_lobe, *, gamma=1.0, core=0.04):
    """Velocity from only original segments wholly inside source_lobe; no artificial closure segment."""
    x=np.asarray(x,float); labels=np.asarray(labels,int); n=len(x)
    a=x; b=np.roll(x,-1,axis=0); lab2=np.roll(labels,-1)
    mask=(labels==int(source_lobe))&(lab2==int(source_lobe))
    aa=a[mask]; bb=b[mask]
    if not len(aa): return np.zeros_like(x)
    dl=bb-aa; mid=.5*(aa+bb); scale=float(gamma)/(4*np.pi); a2=float(core)**2
    out=np.zeros_like(x)
    for i,q in enumerate(x):
        r=q-mid; den=(np.einsum('ij,ij->i',r,r)+a2)**1.5
        out[i]=scale*np.sum(np.cross(dl,r)/den[:,None],axis=0)
    return out


def lobe_pair_centroid_rates(x, labels, *, gamma=1.0, core=0.04):
    x=np.asarray(x,float); labels=np.asarray(labels,int)
    lobes=sorted(int(k) for k in np.unique(labels) if k>=0)
    centers={k:x[labels==k].mean(axis=0) for k in lobes}
    fields={k:_segment_field_from_lobe(x,labels,k,gamma=gamma,core=core) for k in lobes}
    rows=[]
    for ai,a in enumerate(lobes):
        for b in lobes[ai+1:]:
            dv=centers[a]-centers[b]; d=float(np.linalg.norm(dv)); nh=dv/max(d,1e-30)
            va=np.mean(fields[b][labels==a],axis=0)  # source b -> receiver a
            vb=np.mean(fields[a][labels==b],axis=0)  # source a -> receiver b
            rate=float(np.dot(nh,va-vb))
            rows.append(dict(lobe_a=a,lobe_b=b,centroid_distance=d,separation_rate=rate,
                             velocity_a_from_b=va.tolist(),velocity_b_from_a=vb.tolist()))
    arr=np.asarray([r['separation_rate'] for r in rows],float)
    return dict(
        pairs=rows,
        positive_fraction=float(np.mean(arr>0)) if len(arr) else float('nan'),
        median_separation_rate=float(np.median(arr)) if len(arr) else float('nan'),
        mean_separation_rate=float(np.mean(arr)) if len(arr) else float('nan'),
    )


def curvature_signature(x):
    x=np.asarray(x,float); e1=x-np.roll(x,1,axis=0); e2=np.roll(x,-1,axis=0)-x
    a=np.linalg.norm(e1,axis=1); b=np.linalg.norm(e2,axis=1); c=np.linalg.norm(np.roll(x,-1,axis=0)-np.roll(x,1,axis=0),axis=1)
    cross=np.linalg.norm(np.cross(e1,e2),axis=1)
    kappa=2*cross/np.maximum(a*b*c,1e-30)
    q=np.quantile(kappa,[.1,.25,.5,.75,.9])
    return dict(mean=float(np.mean(kappa)),rms=float(np.sqrt(np.mean(kappa*kappa))),quantiles=[float(z) for z in q])


def signature_distance(a,b):
    av=np.asarray([a['mean'],a['rms'],*a['quantiles']],float)
    bv=np.asarray([b['mean'],b['rms'],*b['quantiles']],float)
    return float(np.linalg.norm((bv-av)/np.maximum(np.abs(av),1e-12))/math.sqrt(len(av)))
