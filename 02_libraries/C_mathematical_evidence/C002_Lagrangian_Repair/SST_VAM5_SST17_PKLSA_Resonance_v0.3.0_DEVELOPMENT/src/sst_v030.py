"""SST v0.3.0: geometric finite-core surrogate and spectral/thermo diagnostics.

NOT PKLSA native; NOT exact incompressible Euler; NOT EM or Swirl Clock closure.
Inputs normalized by SST canonical r_c and Gamma. Absolute t is background time.
"""
from __future__ import annotations
import numpy as np
from scipy.special import wofz
from scipy.integrate import quad
from scipy.optimize import least_squares

R_C = 1.40897017e-15
V_SWIRL = 1.09384563e6
RHO_F = 7.0e-7
C = 299792458.0
GAMMA = 2.0 * np.pi * R_C * V_SWIRL
OMEGA_0 = V_SWIRL / R_C
E_DENS = RHO_F * V_SWIRL**2 / 2.0
T_REF = R_C**2 / GAMMA  # rescale dimensionless filament time


def ring(n=128, R=8.0):
    t=np.arange(n,dtype=float)*2*np.pi/n
    return np.stack((R*np.cos(t),R*np.sin(t),np.zeros_like(t)),axis=-1)


def trefoil(n=128, R=5., r=2.):
    t=np.arange(n,dtype=float)*2*np.pi/n
    return np.stack(((R+r*np.cos(3*t))*np.cos(2*t),
                     (R+r*np.cos(3*t))*np.sin(2*t),r*np.sin(3*t)),axis=-1)


def read_xyz(path):
    """External XYZ polyline; dimensional coordinates must be pre-normalized by r_c.
    No generated data are called PKLSA native. Mandatory explicit provenance supplied outside.
    """
    a=np.loadtxt(path, comments='#')
    if a.ndim!=2 or a.shape[1]!=3 or len(a)<16 or not np.isfinite(a).all():
        raise ValueError('Require finite N>=16 XYZ rows in r_c units, no header except #')
    return a


def segments(X):
    Y=np.roll(X,-1,axis=0)
    return .5*(X+Y), Y-X


def biot_savart(X, probe=None, core=1.0):
    """Regularized *segment midpoint* Biot-Savart; dimensionless speed Gamma/r_c.
    Kernel is Rosenhead-type surrogate, not a source-native PKLSA implementation.
    """
    mid, dX=segments(np.asarray(X,dtype=float))
    P=np.asarray(X if probe is None else probe,dtype=float)
    delta=P[:,None,:]-mid[None,:,:]
    denom=(np.sum(delta*delta,axis=-1)+core**2)**1.5
    return np.sum(np.cross(dX[None,:,:],delta)/denom[:,:,None],axis=1)/(4*np.pi)


def filament_energy(X,core=1.0):
    """Positive-definite smoothed double-integral proxy; units rho_f Gamma² r_c.
    Background subtraction, twist energy and core thermodynamics NOT included.
    """
    mid,dX=segments(X)
    d=mid[:,None,:]-mid[None,:,:]
    e=np.sum((dX@dX.T)/np.sqrt(np.sum(d*d,axis=-1)+core**2))
    return e/(8*np.pi)


def impulse(X):
    """Hydrodynamic filament impulse proxy; units rho_f Gamma r_c²."""
    _,dX=segments(X)
    return np.sum(np.cross(X,dX),axis=0)/2


def rk4_step(X,dt,core=1.):
    f=lambda a:biot_savart(a,core=core)
    k1=f(X);k2=f(X+dt*k1/2);k3=f(X+dt*k2/2);k4=f(X+dt*k3)
    return X+(dt/6)*(k1+2*k2+2*k3+k4)


def evolve(X,dt=0.01,steps=10,core=1.):
    X=np.array(X,copy=True)
    e0=filament_energy(X,core)
    i0=impulse(X)
    c0=np.mean(X,axis=0)
    for _ in range(steps):X=rk4_step(X,dt,core)
    return {'X':X,'relative_energy_drift':float((filament_energy(X,core)-e0)/e0),
            'relative_impulse_drift':float(np.linalg.norm(impulse(X)-i0)/max(np.linalg.norm(i0),1e-14)),
            'center_displacement':(np.mean(X,axis=0)-c0).tolist(),
            'dimensionless_time':dt*steps,'time_seconds':dt*steps*T_REF}


def normalized_voigt(delta,sigma,gamma):
    """Unit-area Voigt profile, dimension (angular frequency)^-1."""
    z=(np.asarray(delta)+1j*gamma)/(sigma*np.sqrt(2.0))
    return np.real(wofz(z))/(sigma*np.sqrt(2*np.pi))


def overlap(w0,sigma,lines,amp=1.0):
    """S=A exp[-(w-w0)^2/(2 sigma^2)], L=sum B gamma²/[(w-wn)²+gamma²].
    Normalization requires factor sqrt(2pi)*sigma*pi*gamma times unit-area Voigt.
    """
    return float(np.sum([amp*B*np.sqrt(2*np.pi)*sigma*np.pi*gamma*normalized_voigt(w0-wn,sigma,gamma)
                         for wn,gamma,B in lines]))


def overlap_quad(w0,sigma,lines,amp=1.):
    def fn(w):
        s=amp*np.exp(-0.5*((w-w0)/sigma)**2)
        return s*sum(B*gamma**2/((w-wn)**2+gamma**2) for wn,gamma,B in lines)
    # scipy quad infinite domains with high center near 1e20 unstable; use normalized coordinates.
    low=min([w0-15*sigma]+[wn-15*max(sigma,g) for wn,g,_ in lines]);hi=max([w0+15*sigma]+[wn+15*max(sigma,g) for wn,g,_ in lines])
    return quad(fn,low,hi,epsabs=1e-11,epsrel=1e-10)[0]


def fisher_design(center=0.,gamma=.35,B=1.,noise=.01):
    # Normalize reference resonances to dimensionless angular frequencies.
    scan=np.array([-1.7,-1.,-.55,-.25,0.,.25,.55,1.,1.7,2.0])
    sigmas=np.tile([.25,.5,1.0],len(scan))
    omegas=np.repeat(scan,3)
    def predict(p): return np.array([overlap(w,s,[(p[0],p[1],p[2])]) for w,s in zip(omegas,sigmas)])
    p=np.array([center,gamma,B]); Jacob=np.zeros((len(omegas),3))
    for j,step in enumerate([1e-5,1e-5,1e-5]):
        dp=np.zeros(3);dp[j]=step
        Jacob[:,j]=(predict(p+dp)-predict(p-dp))/(2*step)
    info=Jacob.T@Jacob/noise**2
    fit=least_squares(lambda params:(predict(params)-predict(p))/noise,p+[.05,.08,.1],
                      bounds=([-3,.001,.001],[3,5,10]),xtol=1e-12,ftol=1e-12,gtol=1e-12)
    return {'rank':int(np.linalg.matrix_rank(info)), 'condition_number':float(np.linalg.cond(info)),
            'eig_min':float(np.linalg.eigvalsh(info)[0]),'fit':fit.x.tolist(),
            'truth':p.tolist(), 'max_residual':float(np.max(np.abs(predict(fit.x)-predict(p))))}


def thermal_bar(P,L,kappa,area,d_kappa_fraction):
    if min(P,L,kappa,area)<=0 or d_kappa_fraction<=-1:
        raise ValueError('positive scales and effective kappa are required')
    baseline=P*L/(kappa*area)
    perturbed=baseline/(1+d_kappa_fraction)
    return {'baseline_K':baseline,'perturbed_K':perturbed,'change_K':perturbed-baseline,
            'linear_approx_K':-d_kappa_fraction*baseline}


def ring_mechanics(n=128,core=1.):
    X=ring(n)
    U=biot_savart(X,core=core)
    return {'n':n,'mean_drift_dimless':float(np.mean(U[:,2])),
            'max_radial_velocity_dimless':float(np.max(np.linalg.norm(U[:,:2],axis=1))),
            'energy_dimless':float(filament_energy(X,core)),
            'impulse_z_dimless':float(impulse(X)[2]),
            'expected_impulse_z':float(np.pi*8.0**2)}
