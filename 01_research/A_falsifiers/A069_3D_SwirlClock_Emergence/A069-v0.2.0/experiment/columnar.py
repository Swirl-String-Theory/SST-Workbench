"""A069 v0.2.0 D2A: exact smooth columnar stationary Euler control.

This is 2D flow embedded in 3D (u_z=0 and d/dz=0), not a finite-length
3D knotted vortex, nor a physically validated vortex clock. The azimuthal
tracer is a fluid particle orbit, not an independent atomic eigenmode.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class SmoothColumn:
    rate: float = 1.13
    core: float = 0.8
    density: float = 1.0
    background: float = 0.0
    def _q(self,r):return (r/self.core)**2
    def local_rate(self,r):return self.rate*math.exp(-self._q(r))
    def total_rate(self,r):return self.background+self.local_rate(r)
    def circulation(self,r):return 2*math.pi*r*r*self.total_rate(r)
    def perturbation_circulation(self,r):return 2*math.pi*r*r*self.local_rate(r)
    def vorticity_abs(self,r):return 2*self.background+2*self.local_rate(r)*(1-self._q(r))
    def vorticity_relative(self,r):return self.vorticity_abs(r)-2*self.background
    def pressure_diff(self,r):
        # p(r)-p(0) for the bg=0 profile: integrate dp/dr=r*Omega(r)^2.
        if self.background != 0: raise ValueError('exact pressure used only with background=0')
        return self.density*self.rate*self.rate*self.core*self.core/4 *(-math.expm1(-2*self._q(r)))
    def velocity(self,p):
        x,y,z=map(float,p);rate=self.total_rate(math.hypot(x,y))
        return np.array([-rate*y,rate*x,0.0],dtype=float)
    def energy_per_length(self):
        if self.background!=0:raise ValueError('infinite background energy; not finite excess energy')
        return math.pi*self.density*self.rate*self.rate*self.core**4/8

def tracer(flow,r=0.5,t_end=2.,steps=320,method='rk4'):
    """Integrate full Cartesian velocity, never set theta or expected rate as solver input."""
    if not (steps>=16 and t_end>0 and r>0):raise ValueError('invalid tracer parameters')
    p=np.array([r,0.,0.],dtype=float);dt=t_end/steps;phases=[0.]
    for _ in range(steps):
        f=flow.velocity;k1=f(p);k2=f(p+dt*k1/2)
        if method=='rk4':
            k3=f(p+dt*k2/2);k4=f(p+dt*k3);p+=dt*(k1+2*k2+2*k3+k4)/6
        elif method=='midpoint':p+=dt*k2
        else:raise ValueError('unknown integrator')
        phases.append(math.atan2(p[1],p[0]))
    observed=float(np.unwrap(phases)[-1]);pred=flow.total_rate(r)*t_end
    return {'phase_observed':observed,'phase_predicted':pred,
            'phase_absolute_error':abs(observed-pred),
            'radius_relative_error':abs(float(np.linalg.norm(p[:2]))/r-1),
            'signed_rate_observed':observed/t_end,'signed_rate_predicted':flow.total_rate(r),
            'steps':steps,'method':method,'r':r,'t_end':t_end}

def columnar_suite():
    cases=[]; residuals=[]
    for signed in (1.,-1.):
        flow=SmoothColumn(rate=signed*1.13, core=0.8)
        for ratio in (0.25,0.75,1.5):
            r=flow.core*ratio
            t=tracer(flow,r,2.,640,'rk4')
            mid=tracer(flow,r,2.,2560,'midpoint')
            c160=tracer(flow,r,2.,160,'rk4')
            c320=tracer(flow,r,2.,320,'rk4')
            h=1e-5*flow.core
            pdiff=(flow.pressure_diff(r+h)-flow.pressure_diff(r-h))/(2*h)
            radial=flow.density*r*flow.total_rate(r)**2
            # verify Euler via symmetric Cartesian directional finite difference.
            p=np.array([r*0.8,r*0.6,0.]);eps=1e-5*flow.core;u=flow.velocity(p)
            dx=np.array([eps,0.,0.]);dy=np.array([0.,eps,0.]);
            Dux=(flow.velocity(p+dx)-flow.velocity(p-dx))/(2*eps)
            Duy=(flow.velocity(p+dy)-flow.velocity(p-dy))/(2*eps)
            div=Dux[0]+Duy[1]
            adv=u[0]*Dux+u[1]*Duy
            gradp=flow.density*flow.total_rate(r)**2*p
            euler=float(np.linalg.norm(adv+gradp/flow.density))
            q=flow._q(r)
            curlnum=Dux[1]-Duy[0]
            residuals.append({'divergence':abs(float(div)),
                              'vorticity_curl_absolute_error':abs(float(curlnum-flow.vorticity_abs(r))),
                              'pressure_gradient_relative_error':abs(pdiff/radial-1),
                              'euler_momentum_residual':euler,
                              'phase_absolute_error':t['phase_absolute_error'],
                              'radius_relative_error':t['radius_relative_error']})
            cases.append({'signed_rate':signed*1.13,'r_over_core':ratio,'tracer':t,
                          'rk4_coarse':c160,'rk4_medium':c320,'midpoint':mid,
                          'vorticity_abs':flow.vorticity_abs(r),
                          'circulation':flow.circulation(r),
                          'energy_per_axial_length':flow.energy_per_length()})
    limits= {'divergence':2e-8,'vorticity_curl_absolute_error':2e-8,
             'pressure_gradient_relative_error':3e-9,
             'euler_momentum_residual':2e-8,
             'phase_absolute_error':2e-7,'radius_relative_error':2e-7}
    maxima={k:max(x[k] for x in residuals) for k in limits}
    convergence=all(c['tracer']['phase_absolute_error']<=c['rk4_medium']['phase_absolute_error']+2e-12 and
                    c['rk4_medium']['phase_absolute_error']<=c['rk4_coarse']['phase_absolute_error']+2e-12 for c in cases)
    # No simultaneous increase in all radii is demanded: it is a numerical reference, not physical stability.
    flow=SmoothColumn(rate=1.13,core=.8,background=.37)
    frameerr=max(abs(flow.vorticity_abs(r)-(flow.vorticity_relative(r)+2*flow.background)) for r in (.1,.6,1.2))
    bgproof={'frame_reconstruction_max_error':frameerr,
             'zero_swirl_rate':SmoothColumn(rate=0,core=.8).total_rate(.4),
             'column_total_circulation_asymptote':SmoothColumn(rate=1.13,core=.8).perturbation_circulation(10.)}
    passed=all(maxima[k]<lim for k,lim in limits.items()) and convergence and frameerr<1e-12 and bgproof['zero_swirl_rate']==0
    return {'schema':'SST-COLUMNAR-EULER-CONTROL-2','status':'PASS' if passed else 'FAIL',
            'evidence_class':'analytic_control','not_full_3d':True,'not_pklsa':True,
            'physical_clock_claim':False,'energy_per_axial_length_finite':True,
            'total_energy_in_R3_finite':False,
            'model':'u_theta(r)=C*r*exp(-(r/a)^2), u_z=0, steady incompressible Euler',
            'limits':limits,'maxima':maxima,'rk4_monotone':convergence,
            'frame_and_null':bgproof,'cases':cases}
