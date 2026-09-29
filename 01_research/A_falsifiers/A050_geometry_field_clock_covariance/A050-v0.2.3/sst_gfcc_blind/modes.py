import numpy as np
from .geometry import resample_closed


def _unit(v, eps=1e-15):
    n=np.linalg.norm(v,axis=-1,keepdims=True)
    return v/np.maximum(n,eps)


def kabsch_align(points, reference):
    p=np.asarray(points,float); q=np.asarray(reference,float)
    pc=p-p.mean(axis=0,keepdims=True); qc=q-q.mean(axis=0,keepdims=True)
    h=pc.T@qc
    u,_,vt=np.linalg.svd(h)
    r=u@vt
    if np.linalg.det(r)<0:
        u[:,-1]*=-1.0
        r=u@vt
    return pc@r + q.mean(axis=0,keepdims=True)


def bishop_frame(points):
    p=np.asarray(points,float); npt=len(p)
    t=_unit(np.roll(p,-1,axis=0)-np.roll(p,1,axis=0))
    n=np.zeros_like(t); b=np.zeros_like(t)
    axes=np.eye(3)
    a=axes[int(np.argmin(np.abs(axes@t[0])))]
    n[0]=_unit((a-np.dot(a,t[0])*t[0])[None,:])[0]
    b[0]=np.cross(t[0],n[0]); b[0]=b[0]/max(np.linalg.norm(b[0]),1e-15)
    for i in range(1,npt):
        v=n[i-1]-np.dot(n[i-1],t[i])*t[i]
        if np.linalg.norm(v)<1e-12:
            v=np.cross(b[i-1],t[i])
        n[i]=v/max(np.linalg.norm(v),1e-15)
        b[i]=np.cross(t[i],n[i]); b[i]/=max(np.linalg.norm(b[i]),1e-15)
    # distribute closure mismatch to make the frame approximately periodic
    v=n[-1]-np.dot(n[-1],t[0])*t[0]
    v=v/max(np.linalg.norm(v),1e-15)
    ang=np.arctan2(np.dot(t[0],np.cross(n[0],v)),np.dot(n[0],v))
    for i in range(npt):
        th=-ang*(i/(npt-1 if npt>1 else 1))
        c,s=np.cos(th),np.sin(th)
        ni=c*n[i]+s*b[i]
        bi=-s*n[i]+c*b[i]
        n[i],b[i]=ni,bi
    return t,n,b


def transverse_mode_series(frames, reference, mode_min=2, mode_max=8):
    ref=resample_closed(np.asarray(reference,float),len(reference))
    t,n,b=bishop_frame(ref)
    modes=np.arange(int(mode_min),int(mode_max)+1,dtype=int)
    coeff=[]
    for p in frames:
        pp=resample_closed(np.asarray(p,float),len(ref))
        pp=kabsch_align(pp,ref)
        d=pp-ref
        # remove tangential gauge
        d=d-np.sum(d*t,axis=1,keepdims=True)*t
        z=np.sum(d*n,axis=1)+1j*np.sum(d*b,axis=1)
        h=np.fft.fft(z)/len(z)
        coeff.append(np.asarray([h[m%len(h)] for m in modes],complex))
    return modes,np.asarray(coeff,complex)


def phase_linearity(times, coeff):
    t=np.asarray(times,float); z=np.asarray(coeff,complex)
    amp=np.abs(z)
    if len(t)<4 or np.nanmax(amp)<=1e-14:
        return {'frequency':float('nan'),'phase_r2':float('nan'),'phase_cycles':0.0,'amplitude_rms':float(np.sqrt(np.mean(amp*amp)))}
    floor=max(1e-14,0.15*float(np.nanmax(amp)))
    m=np.isfinite(amp)&(amp>=floor)
    if np.sum(m)<4:
        m=np.isfinite(amp)
    ph=np.unwrap(np.angle(z[m])); tt=t[m]
    if len(tt)<4:
        return {'frequency':float('nan'),'phase_r2':float('nan'),'phase_cycles':0.0,'amplitude_rms':float(np.sqrt(np.mean(amp*amp)))}
    slope,intercept=np.polyfit(tt,ph,1)
    pred=slope*tt+intercept
    ssr=float(np.sum((ph-pred)**2)); sst=float(np.sum((ph-ph.mean())**2))
    r2=float(1.0-ssr/sst) if sst>0 else 1.0
    cycles=float(abs(ph[-1]-ph[0])/(2*np.pi))
    return {'frequency':float(slope),'phase_r2':r2,'phase_cycles':cycles,'amplitude_rms':float(np.sqrt(np.mean(amp*amp)))}


def kelvin_metrics_from_series(modes, coeff, dt, cfg):
    modes=np.asarray(modes,int); c=np.asarray(coeff,complex)
    e=np.mean(np.abs(c)**2,axis=0)
    total=float(np.sum(e))
    k=int(np.argmax(e)) if len(e) else 0
    frac=float(e[k]/total) if total>0 else 0.0
    times=np.arange(len(c),dtype=float)*float(dt)
    ph=phase_linearity(times,c[:,k] if len(e) else np.zeros(len(c),complex))
    passed=bool(
        total>float(cfg['energy_floor']) and
        frac>=float(cfg['dominant_fraction_min']) and
        ph['phase_r2']>=float(cfg['phase_r2_min']) and
        ph['phase_cycles']>=float(cfg['phase_cycles_min'])
    )
    return {
        'status':'KELVIN_MODE_RESOLVED' if passed else 'KELVIN_MODE_NOT_RESOLVED',
        'pass':passed,
        'selected_mode':int(modes[k]) if len(modes) else None,
        'dominant_fraction':frac,
        'total_modal_energy':total,
        'mode_numbers':modes.tolist(),
        'mean_mode_energy':e.tolist(),
        **ph,
    }

def kelvin_metrics(frames, dt, cfg):
    modes,c=transverse_mode_series(frames,frames[0],cfg['mode_min'],cfg['mode_max'])
    return kelvin_metrics_from_series(modes,c,dt,cfg)

def helical_basis(reference, modes):
    ref=np.asarray(reference,float); _,n,b=bishop_frame(ref); nn=len(ref); s=np.arange(nn,dtype=float)
    vec=[]; labels=[]
    for m in modes:
        ph=2*np.pi*int(m)*s/nn
        v1=np.cos(ph)[:,None]*n+np.sin(ph)[:,None]*b
        v2=-np.sin(ph)[:,None]*n+np.cos(ph)[:,None]*b
        for tag,v in (('q0',v1),('q1',v2)):
            # Gram-Schmidt against previous basis vectors
            w=v.copy()
            for q in vec:
                w-=np.sum(w*q)/max(np.sum(q*q),1e-30)*q
            norm=np.sqrt(np.mean(np.sum(w*w,axis=1)))
            if norm>1e-12:
                vec.append(w/norm); labels.append(f'm{int(m)}_{tag}')
    return labels,np.asarray(vec,float)
