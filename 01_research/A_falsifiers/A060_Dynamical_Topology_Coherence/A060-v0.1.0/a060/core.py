from __future__ import annotations
import numpy as np

def normalize_rows(x):
    x=np.asarray(x,dtype=np.complex128)
    n=np.linalg.norm(x,axis=1)
    return x/np.maximum(n[:,None],1e-15)

def overlap_series(x):
    x=normalize_rows(x); return np.einsum("i,ti->t",np.conj(x[0]),x)

def rate_function(g, n_eff):
    p=np.maximum(np.abs(g)**2,1e-300)
    return -np.log(p)/max(int(n_eff),1)

def critical_candidate(t,g,threshold=.05):
    a=np.abs(g)
    if len(a)<3:return {"present":False}
    idx=np.where((a[1:-1]<=a[:-2])&(a[1:-1]<=a[2:]))[0]+1
    if len(idx)==0: idx=np.array([int(np.argmin(a))])
    j=int(idx[np.argmin(a[idx])])
    return {"present":bool(a[j]<=threshold),"index":j,"t":float(t[j]),"abs_G":float(a[j])}

def two_mode_observables(m):
    z=np.asarray(m,dtype=np.complex128)
    if z.ndim!=2 or z.shape[1]<2:return None
    a,b=z[:,0],z[:,1]
    den=np.abs(a)**2+np.abs(b)**2+1e-15
    chi=2*np.imag(np.conj(a)*b)/den
    w=2*np.abs(a)*np.abs(b)/den
    ph=np.angle(b*np.conj(a))
    Z=np.sum(w*np.exp(1j*ph))/max(np.sum(w),1e-15)
    return {"chi_mean":float(np.mean(chi)),"chi_abs_mean":float(np.mean(np.abs(chi))),
            "R12":float(abs(Z)),"phi12":float(np.angle(Z))}

def spectral_pairing(M):
    if M is None:return None
    ev=np.linalg.eigvals(np.asarray(M,dtype=np.complex128))
    if len(ev)<2:return {"n":len(ev)}
    phase=np.angle(ev)
    def circ(a,b): return abs(np.angle(np.exp(1j*(a-b))))
    conj_res=[]; pi_res=[]
    for p in phase:
        conj_res.append(min(circ(q,-p) for q in phase))
        pi_res.append(min(circ(q,p+np.pi) for q in phase))
    inv_res=[]
    for z in ev:
        if abs(z)<1e-14: inv_res.append(np.inf); continue
        inv=1/z
        inv_res.append(min(abs(q-inv) for q in ev))
    return {"n":len(ev),"max_abs_mu":float(np.max(np.abs(ev))),
            "conjugate_phase_residual_median":float(np.median(conj_res)),
            "pi_shift_phase_residual_median":float(np.median(pi_res)),
            "inverse_eigenvalue_residual_median":float(np.median(inv_res))}
