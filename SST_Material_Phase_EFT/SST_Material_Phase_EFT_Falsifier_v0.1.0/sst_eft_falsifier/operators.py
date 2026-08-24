import numpy as np
from .geometry import frenet_geometry,periodic_derivative
EPS=1e-15
def redundancy_residuals(x):
    ds,_,k,t=frenet_geometry(x); kp=periodic_derivative(k,ds,1); kpp=periodic_derivative(kp,ds,1); tp=periodic_derivative(t,ds,1); tpp=periodic_derivative(tp,ds,1)
    td_k=abs(float(np.sum(kp)*ds))/max(float(np.sum(np.abs(kp))*ds),EPS); td_t=abs(float(np.sum(tp)*ds))/max(float(np.sum(np.abs(tp))*ds),EPS)
    a=float(np.sum(k*kpp)*ds); b=float(np.sum(kp*kp)*ds); ibk=abs(a+b)/max(abs(a)+abs(b),EPS); a=float(np.sum(t*tpp)*ds); b=float(np.sum(tp*tp)*ds); ibt=abs(a+b)/max(abs(a)+abs(b),EPS)
    return {"total_derivative_kappa":td_k,"total_derivative_tau":td_t,"ibp_kappa":ibk,"ibp_tau":ibt}
def local_operator_vector(x):
    ds,_,k,t=frenet_geometry(x); kp=periodic_derivative(k,ds,1); tp=periodic_derivative(t,ds,1)
    return {"O_k2":float(np.sum(k**2)*ds),"O_t2":float(np.sum(t**2)*ds),"O_k4":float(np.sum(k**4)*ds),"O_dk2":float(np.sum(kp**2)*ds),"O_dt2":float(np.sum(tp**2)*ds),"O_k2t2":float(np.sum(k*k*t*t)*ds)}
