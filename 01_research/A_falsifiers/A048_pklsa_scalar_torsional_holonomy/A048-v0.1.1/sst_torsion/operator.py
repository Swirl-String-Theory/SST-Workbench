import numpy as np

def torsional_operator_spectrum(kappa, tau, ds, c_phase=1.0, a_kappa=0.1, a_tau=0.1, n_modes=12):
    kappa=np.asarray(kappa,float); tau=np.asarray(tau,float)
    n=len(kappa)
    if len(tau)!=n: raise ValueError("kappa/tau length mismatch")
    D2=np.zeros((n,n),float)
    idx=np.arange(n)
    D2[idx,idx]=-2.0
    D2[idx,(idx-1)%n]=1.0
    D2[idx,(idx+1)%n]=1.0
    D2/=ds*ds
    potential=a_kappa*kappa*kappa+a_tau*tau*tau
    L=-(c_phase*c_phase)*D2+np.diag(potential)
    vals=np.linalg.eigvalsh(L)
    vals=np.maximum(vals,0.0)
    omegas=np.sqrt(vals[:min(n_modes,n)])
    return omegas
