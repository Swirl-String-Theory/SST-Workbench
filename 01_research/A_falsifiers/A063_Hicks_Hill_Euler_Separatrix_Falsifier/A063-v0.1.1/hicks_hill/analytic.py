"""Hill/Hicks exact steady Euler reference, no SST constants or particle labels.

Coordinates: cylindrical (s,phi,z), k=lambda/a; all velocities are in the
sphere's co-translating frame. Exterior uniform velocity approaches -U ez.
Streamfunction convention u_s=-psi_z/s, u_z=psi_s/s, u_phi=k psi/s.
Boundary r=a has psi=0, pressure continuous for chosen Bernoulli constant.
NOTE: smooth *Euler* solution is not proof of stability or stable vortex tube.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import brentq


def J(y):
    y=np.asarray(y,dtype=float)
    small=np.abs(y)<0.08
    with np.errstate(divide='ignore',invalid='ignore'):
        general=np.sin(y)/y-np.cos(y)
    ys=y*y
    series=ys*(1/3 + ys*(-1/30+ys*(1/840+ys*(-1/45360+ys/3991680))))
    r=np.where(small,series,general)
    return float(r) if r.ndim==0 else r


def Jprime(y):
    y=np.asarray(y,dtype=float)
    with np.errstate(divide='ignore',invalid='ignore'):
        general=np.sin(y)+np.cos(y)/y-np.sin(y)/(y*y)
    ys=y*y
    series=y*(2/3+ys*(-2/15+ys*(1/140+ys*(-1/5670+ys/399168))))
    r=np.where(np.abs(y)<0.08,series,general)
    return float(r) if r.ndim==0 else r


def root_families(n=3):
    """Roots of J(lambda)=0 (lambda1) and 3J-lambda sin=0 (lambda2)."""
    roots={'lambda1':[],'lambda2':[]}
    for i in range(1,n+1):
        r1=brentq(lambda x:math.sin(x)-x*math.cos(x),i*math.pi+0.01,(i+0.5)*math.pi-0.01,xtol=4e-14)
        r2=brentq(lambda x:3*J(x)-x*math.sin(x),(i+0.5)*math.pi+0.01,(i+1)*math.pi-0.01,xtol=4e-14)
        roots['lambda1'].append(r1);roots['lambda2'].append(r2)
    return roots


@dataclass(frozen=True)
class SphereVortex:
    a:float=1.0
    lam:float=0.0
    A:float=1.0
    U_hill:float=1.0
    rho:float=1.0
    p_inf:float=0.0

    def __post_init__(self):
        if self.a<=0 or self.rho<=0:raise ValueError('a,rho must be positive')
        if self.lam<0:raise ValueError('lambda must be nonnegative in this reference release')

    @property
    def k(self):return self.lam/self.a

    @property
    def U(self):
        if self.lam==0:return self.U_hill
        return (2*self.A/(3*self.a))*(3*J(self.lam)-self.lam*math.sin(self.lam))

    @property
    def B_prime(self):
        if self.lam==0:return -15*self.U_hill/(2*self.a*self.a)
        return -self.A*self.lam*self.lam*J(self.lam)/(self.a**4)

    @property
    def B0(self):return self.p_inf/self.rho+0.5*self.U*self.U

    def _F_Fprime(self,r):
        if self.lam==0:
            # psi = 3U/(4a²) s²(a²-r²) = F(r)sin²(theta)
            c=3*self.U_hill/(4*self.a**2)
            return c*r*r*(self.a*self.a-r*r),2*c*r*(self.a*self.a-2*r*r)
        y=self.k*r
        return (self.A*(J(y)-J(self.lam)*r*r/(self.a*self.a)),
                self.A*(self.k*Jprime(y)-2*J(self.lam)*r/(self.a*self.a)))

    def _f_over_r2_at_zero(self):
        if self.lam==0:return 3*self.U_hill/4
        return self.A*((self.lam*self.lam/3-J(self.lam))/(self.a*self.a))

    def psi_inside(self,s,z):
        s=np.asarray(s,dtype=float);z=np.asarray(z,dtype=float)
        r=np.hypot(s,z)
        rr=np.where(r>1e-12*self.a,r,1.)
        F,_=self._F_Fprime(rr)
        return np.where(r>1e-12*self.a,F*s*s/(rr*rr),self._f_over_r2_at_zero()*s*s)

    def velocity(self,s,z):
        """u_s,u_phi,u_z. Suitable for scalar/ndarray s,z inputs."""
        s,z=np.broadcast_arrays(np.asarray(s,dtype=float),np.asarray(z,dtype=float))
        r=np.hypot(s,z)
        small=r<1e-8*self.a
        safe=np.where(small,self.a,r)
        F,Fp=self._F_Fprime(safe)
        us=-s*z*(safe*Fp-2*F)/(safe**4)
        uz=Fp*s*s/(safe**3)+2*F*z*z/(safe**4)
        uphi=self.k*F*s/(safe**2)
        us=np.where(small,0.,us)
        uz=np.where(small,2*self._f_over_r2_at_zero(),uz)
        uphi=np.where(small,0.,uphi)
        external=(r>self.a)
        ext_us=1.5*self.U*self.a**3*s*z/(safe**5)
        ext_uz=-self.U+self.U*self.a**3*(z*z-0.5*s*s)/(safe**5)
        return tuple(float(w) if w.ndim==0 else w for w in (
                np.where(external,ext_us,us),np.where(external,0.,uphi),np.where(external,ext_uz,uz)))

    def psi(self,s,z):
        s,z=np.broadcast_arrays(np.asarray(s,dtype=float),np.asarray(z,dtype=float))
        r=np.hypot(s,z)
        safe=np.where(r>0,r,self.a)
        internal=self.psi_inside(s,z)
        ext=-0.5*self.U*s*s*(1-self.a**3/safe**3)
        w=np.where(r>self.a,ext,internal)
        return float(w) if w.ndim==0 else w

    def pressure(self,s,z):
        s,z=np.broadcast_arrays(np.asarray(s,dtype=float),np.asarray(z,dtype=float))
        us,uphi,uz=self.velocity(s,z)
        r=np.hypot(s,z)
        bern=self.B0+self.B_prime*self.psi(s,z)
        bern=np.where(r>self.a,self.B0,bern)
        w=self.rho*(bern-0.5*(us*us+uphi*uphi+uz*uz))
        return float(w) if w.ndim==0 else w

    def numerical_residual(self,s,z,h=1e-4):
        """Finite-difference cylindrical div, curl and steady Euler with centripetal terms."""
        if s<=5*h or math.hypot(s,z)>=self.a-5*h:raise ValueError('interior points away from axis/surface required')
        us,up,uz=self.velocity(s,z)
        ps=lambda x,y:np.array(self.velocity(x,y))
        ds=(ps(s+h,z)-ps(s-h,z))/(2*h)
        dz=(ps(s,z+h)-ps(s,z-h))/(2*h)
        dps=(self.pressure(s+h,z)-self.pressure(s-h,z))/(2*h)
        dpz=(self.pressure(s,z+h)-self.pressure(s,z-h))/(2*h)
        div=ds[0]+us/s+dz[2]
        omega=np.array([-dz[1],dz[0]-ds[2],ds[1]+up/s])
        adv=np.array([us*ds[0]+uz*dz[0]-up*up/s,
           us*ds[1]+uz*dz[1]+us*up/s,
           us*ds[2]+uz*dz[2]])
        euler=adv+np.array([dps/self.rho,0.,dpz/self.rho])
        return {'divergence':float(div),'euler_norm':float(np.linalg.norm(euler)),
                'beltrami_norm':float(np.linalg.norm(omega-self.k*np.array([us,up,uz]))),
                'vorticity':omega.tolist()}

    def surface_residual(self,n=61):
        angles=np.linspace(0.03,math.pi-0.03,n)
        s=self.a*np.sin(angles);z=self.a*np.cos(angles)
        us,up,uz=self.velocity(s,z)
        normal=us*np.sin(angles)+uz*np.cos(angles)
        return {'psi_abs_max':float(np.max(np.abs(self.psi(s,z)))),
                'normal_velocity_abs_max':float(np.max(np.abs(normal)))}
