import numpy as np
from .spectral import wave_numbers, curl_hat


def diagnostics(uh,L):
    N=uh.shape[1]
    kx,ky,kz,k2=wave_numbers(N,L)
    u=np.fft.ifftn(uh,axes=(1,2,3)).real
    wh=curl_hat(uh,kx,ky,kz)
    w=np.fft.ifftn(wh,axes=(1,2,3)).real
    umag=np.sqrt(np.sum(u*u,axis=0)); wmag=np.sqrt(np.sum(w*w,axis=0))
    energy=0.5*np.mean(np.sum(u*u,axis=0))
    helicity=np.mean(np.sum(u*w,axis=0))
    divh=1j*(kx*uh[0]+ky*uh[1]+kz*uh[2])
    div=np.fft.ifftn(divh).real
    idx=np.unravel_index(np.argmax(wmag),wmag.shape)
    # Velocity gradient at max-vorticity point.
    G=np.empty((3,3),float)
    ks=(kx,ky,kz)
    for a in range(3):
        for b in range(3):
            G[a,b]=np.fft.ifftn(1j*ks[b]*uh[a]).real[idx]
    S=0.5*(G+G.T)
    evals,evecs=np.linalg.eigh(S)
    wv=w[:,idx[0],idx[1],idx[2]]
    wn=np.linalg.norm(wv)
    align=float((wv/wn)@S@(wv/wn)) if wn>0 else 0.0
    return {
        "energy":float(energy),"helicity":float(helicity),"max_u":float(umag.max()),
        "max_omega":float(wmag.max()),"div_rms":float(np.sqrt(np.mean(div*div))),
        "strain_lambda_max":float(evals[-1]),"omega_strain_alignment":align,
        "hot_index":[int(x) for x in idx],"principal_strain_vector":[float(x) for x in evecs[:,-1]],
    }


def blowup_fit(times,maxomega,late_fraction=0.45):
    t=np.asarray(times,float); m=np.asarray(maxomega,float)
    n=len(t); i=max(0,int((1.0-late_fraction)*n))
    x=t[i:]; y=1.0/np.maximum(m[i:],1e-300)
    if len(x)<5: return {"candidate":False,"reason":"too_few_points"}
    p=np.polyfit(x,y,1); pred=np.polyval(p,x)
    ssr=float(np.sum((y-pred)**2)); sst=float(np.sum((y-y.mean())**2))
    r2=1.0-ssr/sst if sst>0 else 0.0
    slope,intercept=float(p[0]),float(p[1])
    tstar=-intercept/slope if slope<0 else None
    tend=float(t[-1])
    candidate=bool(tstar is not None and tstar>tend and tstar<=1.5*tend and r2>=0.98)
    return {"candidate":candidate,"slope":slope,"intercept":intercept,"r2":r2,"t_star":tstar}
