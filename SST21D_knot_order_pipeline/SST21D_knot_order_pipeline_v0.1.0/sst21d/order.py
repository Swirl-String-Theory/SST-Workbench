from __future__ import annotations
import numpy as np

def kabsch_align(reference,current):
    a=np.asarray(reference,float); b=np.asarray(current,float); ac=a-a.mean(0); bc=b-b.mean(0)
    H=bc.T@ac; U,S,Vt=np.linalg.svd(H); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    return bc@R+a.mean(0),R

def shape_order(reference,current):
    aligned,_=kabsch_align(reference,current); rmsd=float(np.sqrt(np.mean(np.sum((aligned-reference)**2,axis=1))))
    rg=float(np.sqrt(np.mean(np.sum((reference-reference.mean(0))**2,axis=1))))
    e=rmsd/max(rg,1e-15); return {'rmsd':rmsd,'normalized_rmsd':e,'Q_geom':float(np.exp(-e*e))}

def phase_order(ref,cur):
    d=np.asarray(cur)-np.asarray(ref); z=np.mean(np.exp(1j*d))
    return {'Q_phase':float(abs(z)),'global_phase_shift_rad':float(np.angle(z))}

def project_det_one(J):
    U,s,Vt=np.linalg.svd(J); s=np.maximum(s,1e-15); scale=np.prod(s)**(-1/3); P=U@np.diag(s*scale)@Vt
    if np.linalg.det(P)<0: U[:,-1]*=-1; P=U@np.diag(s*scale)@Vt
    return P

def dmin_projected_det1(reference,current,window=3):
    a=np.asarray(reference,float); b,_=kabsch_align(a,np.asarray(current,float)); n=len(a); out=np.zeros(n)
    offsets=[k for k in range(-window,window+1) if k!=0]
    for i in range(n):
        idx=[(i+k)%n for k in offsets]; X=(a[idx]-a[i]).T; Y=(b[idx]-b[i]).T
        G=X@X.T; lam=1e-8*max(float(np.trace(G))/3.0,1e-15); J=(Y@X.T+lam*np.eye(3))@np.linalg.inv(G+lam*np.eye(3)); P=project_det_one(J); res=Y-P@X
        out[i]=np.mean(np.sum(res*res,axis=0))
    ds=np.mean(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1))
    return out/max(ds*ds,1e-30)

def largest_ring_cluster_fraction(mask):
    m=np.asarray(mask,bool); n=len(m)
    if not m.any(): return 0.0
    if m.all(): return 1.0
    mm=np.concatenate([m,m]); best=cur=0
    for v in mm:
        cur=cur+1 if v else 0; best=max(best,cur)
    return float(min(best,n)/n)

def dynamic_analyze(points,times=None,phase=None,window=3,defect_threshold=0.05):
    P=np.asarray(points,float)
    if P.ndim==3: P=P[:,None,:,:]
    if P.ndim!=4 or P.shape[-1]!=3: raise ValueError('points must be (T,N,3) or (T,C,N,3)')
    T,C,N,_=P.shape
    if times is None: times=np.arange(T,dtype=float)
    times=np.asarray(times,float)
    PH=None if phase is None else np.asarray(phase,float)
    if PH is not None and PH.ndim==2: PH=PH[:,None,:]
    rows=[]
    for t in range(T):
        for c in range(C):
            s=shape_order(P[0,c],P[t,c]); d=dmin_projected_det1(P[0,c],P[t,c],window); defect=d>defect_threshold
            row={'frame':t,'time':float(times[t]),'component':c,**s,'dmin_mean':float(d.mean()),'dmin_max':float(d.max()),
                 'defect_fraction':float(defect.mean()),'largest_defect_cluster_fraction':largest_ring_cluster_fraction(defect)}
            if PH is not None: row.update(phase_order(PH[0,c],PH[t,c]))
            else: row.update({'Q_phase':None,'global_phase_shift_rad':None})
            rows.append(row)
    summary={'trajectory_shape':list(P.shape),'phase_present':PH is not None,'rows':rows,
             'Q_geom_min':min(r['Q_geom'] for r in rows),'dmin_max':max(r['dmin_max'] for r in rows),
             'Q_phase_min':min((r['Q_phase'] for r in rows if r['Q_phase'] is not None),default=None)}
    if PH is not None:
        d=np.unwrap(PH-PH[0:1],axis=0); d=d-d.mean(axis=-1,keepdims=True)
        F=np.fft.rfft(d,axis=-1); S=np.mean(np.abs(F)**2,axis=(0,1))/N
        k=np.arange(len(S)); valid=(k>=1)&(S>max(float(S.max())*1e-10,0.0))
        if valid.sum()>=3:
            use=np.where(valid)[0][:min(8,valid.sum())]; slope=np.polyfit(np.log(k[use]),np.log(S[use]),1)[0]; summary['phase_structure_ir_exponent']=float(-slope)
        summary['phase_structure_factor']=S
        # Dynamic structure factor and empirical mode dispersion.
        if T >= 8 and len(times)==T:
            dt=np.diff(times)
            uniform=bool(np.all(np.isfinite(dt)) and np.allclose(dt,dt.mean(),rtol=1e-5,atol=max(abs(float(dt.mean()))*1e-8,1e-15)) and dt.mean()>0)
            summary['uniform_time_grid']=uniform
            if uniform:
                spatial=np.fft.rfft(d,axis=-1)  # (T,C,K), complex
                spatial=spatial-spatial.mean(axis=0,keepdims=True)
                win=np.hanning(T)[:,None,None]
                temporal=np.fft.fft(spatial*win,axis=0)
                freq=np.fft.fftfreq(T,d=float(dt.mean()))
                freq_s=np.fft.fftshift(freq)
                power=np.fft.fftshift(np.mean(np.abs(temporal)**2,axis=1),axes=0)  # (W,K)
                lengths=[]
                for c in range(C):
                    edge=np.roll(P[0,c],-1,axis=0)-P[0,c]
                    lengths.append(float(np.linalg.norm(edge,axis=1).sum()))
                Lmean=float(np.mean(lengths))
                disp=[]
                global_peak=float(power.max()) if power.size else 0.0
                for m in range(1,min(power.shape[1],9)):
                    spec=power[:,m].copy()
                    spec[np.isclose(freq_s,0.0)]=0.0
                    if spec.size==0 or float(spec.max())<=max(global_peak*1e-12,0.0): continue
                    ip=int(np.argmax(spec)); fpk=abs(float(freq_s[ip])); half=0.5*float(spec[ip])
                    left=right=ip
                    while left>0 and spec[left-1]>=half: left-=1
                    while right+1<len(spec) and spec[right+1]>=half: right+=1
                    if right>left: fwhm=abs(float(freq_s[right]-freq_s[left]))
                    else: fwhm=float(1.0/(T*dt.mean()))
                    disp.append({'mode_m':m,'k_per_coordinate_unit':float(2*np.pi*m/max(Lmean,1e-15)),
                                 'omega_per_time_unit':float(2*np.pi*fpk),'spectral_fwhm_per_time_unit':float(2*np.pi*fwhm),
                                 'damping_proxy_per_time_unit':float(np.pi*fwhm),'peak_signed_frequency_per_time_unit':float(freq_s[ip]),
                                 'peak_power':float(spec[ip])})
                summary['dispersion_rows']=disp
                fit=[r for r in disp if r['omega_per_time_unit']>0 and r['k_per_coordinate_unit']>0]
                if len(fit)>=3:
                    x=np.log([r['k_per_coordinate_unit'] for r in fit]); y=np.log([r['omega_per_time_unit'] for r in fit])
                    pfit,logA=np.polyfit(x,y,1); summary['dispersion_exponent_p']=float(pfit); summary['dispersion_prefactor_A']=float(np.exp(logA))
    return summary
