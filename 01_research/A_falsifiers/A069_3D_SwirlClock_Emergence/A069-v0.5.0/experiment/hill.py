"""Hill's spherical vortex: exact axisymmetric translating 3D Euler control.

Velocity is expressed in the frame translating at U along the z axis;
there is uniform -U e_z flow at infinity. The vorticity is azimuthal
omega_phi=(15U/2a^2)*s inside a sphere, zero outside. p is continuous.
No internal clock, no PKLSA knots, no uncalibrated SST force claims.
"""
from __future__ import annotations
import math
import numpy as np

def hill_field(x, U=0.9, a=1.3, rho=1.):
    if a<=0 or rho<=0:raise ValueError('positive radius and density required')
    X,Y,Z=map(float,x);s2=X*X+Y*Y;r2=s2+Z*Z
    if r2<a*a:
        usfac=1.5*U*Z/(a*a)
        ux,uy=usfac*X,usfac*Y
        uz=1.5*U*(1.-(2*s2+Z*Z)/(a*a))
        A=7.5*U/(a*a)
        omega=np.array([-A*Y,A*X,0.])
        chi=(3*A*U/4.)*s2*(r2/(a*a)-1.)
    else:
        r=math.sqrt(r2)
        if r==0:raise AssertionError('unreachable exterior origin')
        k=1.5*U*a**3/(r**5)
        ux,uy=k*X*Z,k*Y*Z
        uz=-U+U*a**3*(1/r**3-1.5*s2/r**5)
        omega=np.zeros(3);chi=0.
    u=np.array([ux,uy,uz])
    pressure=rho*(.5*(U*U-float(u@u))+chi)
    return u,omega,pressure

def differential_metrics(x,step=2.e-5,U=.9,a=1.3,rho=1.):
    p=np.asarray(x,dtype=float)
    v,w,pressure=hill_field(p,U,a,rho)
    h=step*a
    V=np.column_stack([(hill_field(p+np.eye(3)[i]*h,U,a,rho)[0]-hill_field(p-np.eye(3)[i]*h,U,a,rho)[0])/(2*h) for i in range(3)])
    gp=np.array([(hill_field(p+np.eye(3)[i]*h,U,a,rho)[2]-hill_field(p-np.eye(3)[i]*h,U,a,rho)[2])/(2*h) for i in range(3)])
    curl=np.array([V[2,1]-V[1,2],V[0,2]-V[2,0],V[1,0]-V[0,1]])
    return {'divergence':abs(float(np.trace(V))),
       'curl_absolute_error':float(np.max(np.abs(curl-w))),
       'steady_euler_residual':float(np.linalg.norm(rho*(V@v)+gp)),
       'pressure':pressure,
       'speed':float(np.linalg.norm(v))}

def hill_suite():
    U=.9;a=1.3;rho=1.2
    positions=[(.13,.25,.3),(.35,-.18,-.17),(.5,.2,.1),(.2,.25,.8),(1.8,.24,.2),(.1,.3,1.7)]
    v=[differential_metrics(x,U=U,a=a,rho=rho) for x in positions]
    limits={'divergence':3.e-8,'curl_absolute_error':3.e-8,'steady_euler_residual':3.e-8}
    maxima={k:max(t[k] for t in v) for k in limits}
    A=15*U/(2*a*a)
    circulation=2*A*a**3/3
    relation_err=abs(circulation/(5*a)-U)
    # Boundary matching checked at off-axis points approaching the sphere in fixed polar directions.
    mismatch=[]
    for theta in [.25,.65,1.1,2.3]:
        h=2.e-7
        pin=np.array([a*math.sin(theta)*(1-h),0.,a*math.cos(theta)*(1-h)])
        pout=np.array([a*math.sin(theta)*(1+h),0.,a*math.cos(theta)*(1+h)])
        va,_,pa=hill_field(pin,U,a,rho)
        vb,_,pb=hill_field(pout,U,a,rho)
        mismatch.append({'velocity':float(np.linalg.norm(va-vb)),'pressure':abs(pa-pb)})
    boundary_v=max(x['velocity'] for x in mismatch)
    boundary_p=max(x['pressure'] for x in mismatch)
    ok=(all(maxima[k]<limits[k] for k in limits) and relation_err<1e-12
       and boundary_v<5e-6 and boundary_p<5e-6)
    return {'schema':'A069-HILL-EXACT-3D-EULER-1','status':'PASS' if ok else 'FAIL',
      'classification':'ANALYTIC_CONTROL_ONLY','finite_vorticity_support':True,
      'is_knotted':False,'self_clock_predicted':False,'source_is_pklsa':False,
      'A':A,'radius':a,'U':U,'Gamma_meridional':circulation,
      'Gamma_over_5R_error':relation_err,'maxima':maxima,'limits':limits,
      'boundary_velocity_jump_approach':boundary_v,'boundary_pressure_jump_approach':boundary_p,
      'interior_exterior_samples':v}
