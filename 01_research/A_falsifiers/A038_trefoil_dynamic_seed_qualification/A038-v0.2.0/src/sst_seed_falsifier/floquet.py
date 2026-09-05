import numpy as np
from .geometry import fourier_normal_basis,align_cyclic,normalize_length
from .dynamics import simulate

def projected_floquet(x0,T,cfg):
    kmax=int(cfg.get('floquet_kmax',3)); basis,labels=fourier_normal_basis(x0,kmax); maxdim=int(cfg.get('floquet_dim',8)); basis=basis[:maxdim]; labels=labels[:maxdim]; eps=float(cfg.get('floquet_eps',2e-4));
    base=simulate(x0,cfg,T,mode='fixed',long_mesh=False,store_samples=4); xb=base['x'][-1]; xb_al,d0,sh0,R0,t0=align_cyclic(xb,x0,int(cfg.get('cyclic_stride',4))); M=np.zeros((len(basis),len(basis))); quality=True
    for i,v in enumerate(basis):
        cols=[]
        for sign in (+1,-1):
            xp=normalize_length(x0+sign*eps*v,2*np.pi); tr=simulate(xp,cfg,T,mode='fixed',long_mesh=False,store_samples=4); xf=tr['x'][-1]
            # use independent symmetry reduction to x0; central difference cancels most alignment bias
            xa,di,shi,Ri,ti=align_cyclic(xf,x0,int(cfg.get('cyclic_stride',4))); cols.append(xa)
            quality &= tr['stop_reason']=='COMPLETED'
        delta=(cols[0]-cols[1])/(2*eps)
        for j,q in enumerate(basis): M[j,i]=float(np.sum(delta*q))
    eig=np.linalg.eigvals(M); rho=float(np.max(np.abs(eig))) if len(eig) else float('inf')
    return {'base_return':float(d0),'basis_labels':labels,'matrix':M.tolist(),'eigenvalues_real':[float(z.real) for z in eig],'eigenvalues_imag':[float(z.imag) for z in eig],'spectral_radius':rho,'quality_completed':bool(quality),'dimension':len(basis)}
