import numpy as np
from .geometry import fourier_normal_basis,align_cyclic,normalize_length,segment_lengths,tangents
from .dynamics import simulate
from .solver import rhs
from .evidence import dynamics_contract

def _project_out_neutral_modes(x0,basis,labels,cfg):
    n=len(x0); axes=np.eye(3); raw=[]; names=[]
    for j,e in enumerate(axes): raw.append(np.broadcast_to(e,(n,3)).copy()); names.append(f'translation_{j}')
    for j,e in enumerate(axes): raw.append(np.cross(np.broadcast_to(e,(n,3)),x0)); names.append(f'rotation_{j}')
    raw.append(tangents(x0)); names.append('reparameterization')
    L0=float(np.sum(segment_lengths(x0))); flow,_=rhs(x0,float(cfg.get('gamma',1.0)),float(cfg['core_fraction']),'global_volume',bool(cfg.get('require_native',True)),L0=L0)
    raw.append(flow); names.append('time_flow')
    neutral=[]; kept_names=[]
    for v,name in zip(raw,names):
        z=np.asarray(v,float).copy()
        for q in neutral: z-=np.sum(z*q)*q
        nz=np.linalg.norm(z)
        if nz>1e-10: neutral.append(z/nz); kept_names.append(name)
    projected=[]; projected_labels=[]
    for v,label in zip(basis,labels):
        z=v.copy()
        for q in neutral: z-=np.sum(z*q)*q
        for q in projected: z-=np.sum(z*q)*q
        nz=np.linalg.norm(z)
        if nz>1e-10: projected.append(z/nz); projected_labels.append(label)
    return np.asarray(projected),projected_labels,kept_names


def projected_floquet(x0,T,cfg,expected_contract_sha256=None):
    contract,contract_hash=dynamics_contract(cfg,len(x0))
    if expected_contract_sha256 is not None and contract_hash!=expected_contract_sha256:
        raise ValueError(f'DYNAMICS_CONTRACT_MISMATCH expected={expected_contract_sha256} actual={contract_hash}')
    kmax=int(cfg.get('floquet_kmax',3)); basis,labels=fourier_normal_basis(x0,kmax); basis,labels,neutral=_project_out_neutral_modes(x0,basis,labels,cfg); maxdim=int(cfg.get('floquet_dim',8)); basis=basis[:maxdim]; labels=labels[:maxdim]; eps=float(cfg.get('floquet_eps',2e-4));
    simkw={'mode':'global_volume','long_mesh':True,'store_samples':4,'max_ds_cv_override':float(cfg.get('long_hard_ds_cv',.45))}
    base=simulate(x0,cfg,T,**simkw); xb=base['x'][-1]; xb_al,d0,sh0,R0,t0=align_cyclic(xb,x0,int(cfg.get('cyclic_stride',4))); M=np.zeros((len(basis),len(basis))); quality=base['stop_reason']=='COMPLETED'
    for i,v in enumerate(basis):
        cols=[]
        for sign in (+1,-1):
            xp=normalize_length(x0+sign*eps*v,2*np.pi); tr=simulate(xp,cfg,T,**simkw); xf=tr['x'][-1]
            # use independent symmetry reduction to x0; central difference cancels most alignment bias
            xa,di,shi,Ri,ti=align_cyclic(xf,x0,int(cfg.get('cyclic_stride',4))); cols.append(xa)
            quality &= tr['stop_reason']=='COMPLETED'
        delta=(cols[0]-cols[1])/(2*eps)
        for j,q in enumerate(basis): M[j,i]=float(np.sum(delta*q))
    eig=np.linalg.eigvals(M); rho=float(np.max(np.abs(eig))) if len(eig) else float('inf')
    return {'base_return':float(d0),'basis_labels':labels,'matrix':M.tolist(),'eigenvalues_real':[float(z.real) for z in eig],'eigenvalues_imag':[float(z.imag) for z in eig],'spectral_radius':rho,'quality_completed':bool(quality),'dimension':len(basis),'floquet_scope':'projected_fourier_normal_subspace','neutral_modes_removed':neutral,'dynamics_contract':contract,'dynamics_contract_sha256':contract_hash}
