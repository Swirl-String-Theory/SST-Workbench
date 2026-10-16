"""Explicit Newton comparator and instantaneous Euler-Poisson Gaussian vortex candidate.

This is a *restricted and deliberately falsifiable* source. The Gaussian azimuthal
field is divergence-free but is NOT claimed to be a steady Euler solution, a knot,
or a micro-to-macroscale SST derivation.
"""
from __future__ import annotations
import math
from functools import lru_cache
import numpy as np

G_REF = 6.67430e-11             # m^3 kg^-1 s^-2; never fed to the vortex model
LIGHT = 299792458.0           # m s^-1
RHO_F = 7.0e-7                # kg m^-3
V_SWIRL = 1.09384563e6       # m s^-1
R_CORE = 1.40897017e-15      # m (not confused with Gaussian a)
RHO_CORE = 3.8934358266918687e18
F_SWIRL_MAX = 29.053507
F_GR_MAX = 3.02563e43


def newton_force(ms: float, mt: float, r: float) -> float:
    if min(ms, mt, r) <= 0:
        raise ValueError("positive masses and separation required")
    return G_REF * ms * mt / r**2


def newton_gradient(ms: float, mt: float, r: float) -> float:
    return 2.0*newton_force(ms, mt, r)/r


def newton_modulation_exact(ms: float, mt: float, r: float, displacement: float) -> float:
    """Peak-to-baseline force difference of attraction over radial approach +dr."""
    if displacement < 0 or displacement >= r:
        raise ValueError("0 <= displacement < separation")
    return newton_force(ms, mt, r-displacement)-newton_force(ms, mt, r)


def vortex_omega(a: float, rho: float=RHO_F, vmax: float=V_SWIRL) -> float:
    """Centerline Gaussian swirl: |v| achieves vmax at cylindrical r=a, z=0."""
    if min(a, rho, vmax) <= 0:
        raise ValueError("positive physical inputs required")
    return math.sqrt(math.e)*vmax/a


def energy_mass(a: float, rho: float=RHO_F, vmax: float=V_SWIRL) -> float:
    """E_kin/c^2 with Gaussian velocity and infinite-domain integral, NOT SST canon."""
    om = vortex_omega(a, rho, vmax)
    return 0.5*rho*om**2*(math.pi**1.5)*a**5/LIGHT**2


def source_integral_monopole_discrete(grid: tuple[np.ndarray,...]) -> float:
    s, xx, yy, zz, h = grid
    return float(s.sum()*h**3)


@lru_cache(maxsize=8)
def quadrature_grid(a: float, n: int, extent_a: float=5.5,
                    rho: float=RHO_F, vmax: float=V_SWIRL):
    """Midpoint-cell grid with sampled Poisson source S = -rho trace(grad v)^2.

    Pure NumPy FP64. Cube side 2*extent_a*a with n midpoint cells per side.
    """
    if n < 12 or n % 2:
        raise ValueError("even n>=12 required")
    if a <= 0 or extent_a < 4:
        raise ValueError("positive a and extent>=4a required")
    h=2*extent_a*a/n
    axis=(np.arange(n,dtype=np.float64)+0.5)*h - extent_a*a
    xx,yy,zz=np.meshgrid(axis,axis,axis,indexing='ij')
    r2=xx*xx+yy*yy+zz*zz
    xy2=xx*xx+yy*yy
    om=vortex_omega(a, rho, vmax)
    src=2*rho*om**2*np.exp(-r2/a**2)*(1-xy2/a**2)
    return src,xx,yy,zz,h


def divergence_velocity(x, y, z, a):
    """Analytic divergence of v_theta=Omega*r_perp*exp(-r^2/(2a^2))."""
    _ = (x, y, z, a)
    return 0.0


def pressure_gradient(point: tuple[float,float,float], *, a: float, n: int,
                      rho: float=RHO_F, vmax: float=V_SWIRL) -> np.ndarray:
    """Infinite-space Green integral (midpoint quadrature), returns Pa/m.

    p(x)= -1/(4pi) integral S(y)/|x-y| d^3y
    grad p(x)=+1/(4pi) integral S(y)*(x-y)/|x-y|^3 d^3y.
    For points outside the source cuboid, the kernel is smooth.
    """
    src,xx,yy,zz,h=quadrature_grid(a,n,rho=rho,vmax=vmax)
    px,py,pz=point
    if np.linalg.norm(point) <= 5.5*a*math.sqrt(3):
        raise ValueError("point too near/in Gaussian integration cube")
    dx=px-xx;dy=py-yy;dz=pz-zz
    inv3=(dx*dx+dy*dy+dz*dz)**(-1.5)
    factor=h**3/(4*math.pi)
    return factor*np.array([np.sum(src*dx*inv3), np.sum(src*dy*inv3),np.sum(src*dz*inv3)])


def pressure_force_component(r: float, axis: str, *, a: float, n: int,
                             rtest: float|None=None) -> float:
    """-V_t * grad p along selected axis, not force on a self-organised knotted loop."""
    if axis not in ('x','z'):
        raise ValueError('axis must be x or z')
    point=(r,0.,0.) if axis=='x' else (0.,0.,r)
    grad=pressure_gradient(point,a=a,n=n)
    vol=4*math.pi/3*(a if rtest is None else rtest)**3
    return -vol*grad[0 if axis=='x' else 2]


def force_radial_exponent(rs: np.ndarray, fs: np.ndarray) -> float:
    if np.any(np.abs(fs)<=0) or np.any(rs<=0):
        raise ValueError("nonzero forces and positive distances required")
    x=np.log(rs);y=np.log(np.abs(fs))
    return float(-np.polyfit(x,y,1)[0])


def finite_difference_newton(ms: float, mt:float, r:float, h:float=1e-5)->float:
    return (newton_force(ms,mt,r-h)-newton_force(ms,mt,r+h))/(2*h)


def dims_consistency() -> dict:
    # SI dimension algebra: M,L,T powers
    dims={"rho":(1,-3,0),"omega":(0,0,-1),"a":(0,1,0),"p":(1,-1,-2)}
    def add(*terms):return tuple(sum(c[i] for c in terms) for i in range(3))
    source=add(dims['rho'],(0,0,-2))
    laplacep=add(dims['p'],(0,-2,0))
    gradp=add(dims['p'],(0,-1,0))
    force=add(gradp,(0,3,0))
    return {"source":"M L^-3 T^-2","laplacian_p":"M L^-3 T^-2", "force":"M L T^-2", "source_matches":source==laplacep,"force_matches":force==(1,1,-2)}
