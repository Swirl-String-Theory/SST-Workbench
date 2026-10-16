"""Non-invasive A046/A057 analytic-reference bridge; never substitutes E013 source carriers."""
from __future__ import annotations
import numpy as np
import math
from numpy.polynomial.legendre import leggauss
from .analytic import SphereVortex


def velocity_cartesian(field:SphereVortex,x,y,z):
    s=float(math.hypot(x,y))
    if s<1e-12:raise ValueError('Away-from-axis samples only in reference bridge')
    us,uphi,uz=field.velocity(s,z)
    return np.array([(us*x-uphi*y)/s,(us*y+uphi*x)/s,uz])


def exact_vorticity_cartesian(field:SphereVortex,x,y,z):
    s=float(math.hypot(x,y))
    if s<1e-12:raise ValueError('Away-from-axis samples only in reference bridge')
    us,uphi,uz=field.velocity(s,z)
    if s>=field.a:return np.zeros(3)
    w_s=field.k*us
    w_phi=field.k*uphi-field.B_prime*s
    w_z=field.k*uz
    return np.array([(w_s*x-w_phi*y)/s,(w_s*y+w_phi*x)/s,w_z])


def strain_and_pressure_poisson(field:SphereVortex,x,y,z,h=0.0005):
    """Check div u, strain tensor, pressure Poisson equation inside homogeneous fluid.

    Stationary incompressible Euler: ∇²p = -ρ tr((∇u)^2).
    Direction index: gradU[i,j]=∂_j u_i.
    """
    q=np.array([x,y,z],dtype=float)
    if np.linalg.norm(q)>=field.a-5*h or math.hypot(x,y)<5*h:
        raise ValueError('Only supported strictly inside sphere, away from axis')
    b=np.eye(3)*h
    g=np.column_stack([(velocity_cartesian(field,*(q+v))-
                        velocity_cartesian(field,*(q-v)))/(2*h) for v in b])
    S=0.5*(g+g.T)
    p0=field.pressure(math.hypot(x,y),z)
    lap_p=0.
    for v in b:
        xp=q+v;xm=q-v
        lap_p+=(field.pressure(math.hypot(xp[0],xp[1]),xp[2])-2*p0+
                field.pressure(math.hypot(xm[0],xm[1]),xm[2]))/h**2
    forcing=field.rho*float(np.trace(g@g))
    return {'gradient':g.tolist(),'strain':S.tolist(),
            'divergence':float(np.trace(g)),'pressure_poisson_residual':float(lap_p+forcing),
            'forcing_trace_gradU_squared':float(forcing),
            'exact_vorticity':exact_vorticity_cartesian(field,x,y,z).tolist()}


def volume_energy(field:SphereVortex,order=56):
    """Absolute finite kinetic energy of laboratory-frame field.

    The co-translating exterior field approaches constant -U, and would have
    divergent un-subtracted global kinetic energy. We transform to the lab
    frame, where outside there is only the decaying dipole field.
    Gauss-Legendre integration inside and exact exterior dipole contribution.
    """
    nodes,weights=leggauss(order)
    rr=0.5*field.a*(nodes+1)
    wr=0.5*field.a*weights
    c=nodes
    s=rr[:,None]*np.sqrt(1-c[None,:]**2)
    z=rr[:,None]*c[None,:]
    us,uphi,uz=field.velocity(s,z)
    e=us**2+uphi**2+(uz+field.U)**2
    # 0.5*rho * 2pi int r² dr int_{-1}^{1} dc |u|²
    ein=float(math.pi*field.rho*np.sum(wr[:,None]*weights[None,:]*(rr[:,None]**2)*e))
    eout=float(math.pi*field.rho*field.U**2*field.a**3/3)
    return {'inside_lab_kinetic_energy':ein,'exterior_dipole_energy':eout,
            'total_lab_kinetic_energy':ein+eout,
            'quadrature_order':order,'reference':'lab frame, zero far field, no background divergence'}
