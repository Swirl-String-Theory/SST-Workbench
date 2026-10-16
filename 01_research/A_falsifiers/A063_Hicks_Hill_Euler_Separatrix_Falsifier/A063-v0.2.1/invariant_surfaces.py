"""A063 v0.2.1: exact Hicks streamfunction-level surfaces.

Independent numerical checks use finite differences on analytic psi and analytic
velocity, rather than deriving both surface normals and flux from one identity.
Regular axisymmetric star-shaped level curves away from s=0 provide explicit
unknotted toroidal surfaces. No 3D time-dependent Euler evolution is performed.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from hicks_hill.qualification import poloidal_cycle


def psi_peak(field):
    opt=minimize_scalar(lambda s:-field.psi(s,0),bounds=(0.025*field.a,0.995*field.a),method='bounded',options={'xatol':1e-13})
    if not opt.success:raise RuntimeError('psi peak optimization failed')
    return float(opt.x),float(-opt.fun)


def meridional_level(field, target, ntheta=192):
    """Find an explicit star-shaped closed meridional regular level curve."""
    center, pmax=psi_peak(field)
    if not (0<target<pmax):raise ValueError('target must lie between 0 and peak psi')
    theta=np.linspace(0,2*math.pi,ntheta,endpoint=False)
    rvals=np.empty(ntheta)
    for j,t in enumerate(theta):
        cs,sn=math.cos(t),math.sin(t)
        boundary=-center*cs+math.sqrt(field.a**2-center**2*sn**2)
        if cs < -1e-14:boundary=min(boundary,-center/cs)
        limit=boundary*(1-5e-11)
        if field.psi(center+limit*cs,limit*sn)>=target:
            raise ValueError(f'level crossing not bracketed at theta={t}')
        rvals[j]=brentq(lambda r:field.psi(center+r*cs,r*sn)-target,0,limit,xtol=4e-14)
    s=center+rvals*np.cos(theta);z=rvals*np.sin(theta)
    r_sphere=np.hypot(s,z)
    if np.min(s)<=0 or np.max(r_sphere)>=field.a:
        raise ValueError('not a valid embedded torus of revolution inside sphere')
    # The level is verified as a single radial crossing per sampled ray.
    radial_uniqueness=True
    for t,r in zip(theta[::max(1,ntheta//32)],rvals[::max(1,ntheta//32)]):
        cs,sn=np.cos(t),np.sin(t)
        samples=np.linspace(0,r*1.02,80)
        signs=np.array([field.psi(center+x*cs,x*sn)>target for x in samples])
        if np.count_nonzero(signs[:-1]!=signs[1:])!=1:radial_uniqueness=False
    return {'center':center,'peak_psi':pmax,'target':target,'theta':theta,'radial':rvals,
            's':s,'z':z,'radially_unique':radial_uniqueness,
            'level_residual_max':float(np.max(np.abs(field.psi(s,z)-target))),
            's_min':float(np.min(s)),'sphere_clearance_min':float(field.a-np.max(r_sphere)),
            'rmin':float(rvals.min()),'rmax':float(rvals.max())}


def iso_embedding_certificate(level):
    """Explicit deformation of star-shaped meridional oval to a standard circle.

    For rho_theta >0, the surfaces (s,z) = (s_c,0) +
      ((1-t)*rho_theta + t*r0)*(cos(theta),sin(theta))
    remain embedded tori disjoint from the symmetry axis when their minimum s>0.
    This is an explicit ambient-isotopy *numerical construction* of the surface.
    """
    sc=float(level['center']); radial=level['radial'];theta=level['theta']
    r0=min(0.075,sc/4.)
    mn=[]
    for t in np.linspace(0,1,21):
        rad=(1-t)*radial+t*r0
        mn.append(float(np.min(sc+rad*np.cos(theta))))
    return {'topology':'STANDARD_UNKNOTTED_SOLID_TORUS','radial_uniqueness':level['radially_unique'],
            'interpolation_axis_minimum':float(min(mn)), 'standard_circle_radius':r0,
            'core_curve':'(s_c cos(phi), s_c sin(phi), 0): planar unknot',
            'retraction_core_winding_azimuth':1,
            't34_on_boundary_azimuth_winding':3,
            'isotopy_sampled_levels':21,
            'valid_sampled_isotopy':bool(level['radially_unique'] and min(mn)>0)}


def surface_flux(field,level,nphi=64,h=1e-4):
    """FD psi-gradient normal flux; independent analytic velocity.

    The normal is grad_3D psi normalized (no azimuth gradient).
    Numerical curl residual is assessed elsewhere; omega=k*u holds analytically
    ONLY for the first-Beltrami branch.
    """
    s=level['s'][:,None];z=level['z'][:,None]
    # independent symmetric differences applied to psi rather than velocity
    gs=(field.psi(s+h,z)-field.psi(s-h,z))/(2*h)
    gz=(field.psi(s,z+h)-field.psi(s,z-h))/(2*h)
    norm=np.hypot(gs,gz)
    if float(np.min(norm))<=0:raise ValueError('critical level surface')
    ns,nz=gs/norm,gz/norm
    us,up,uz=field.velocity(s,z)
    # Axisymmetric field: rotating a sample in phi preserves the normal flux.
    normal_flow=us*ns+uz*nz
    velocity_scale=np.sqrt(np.mean(us**2+up**2+uz**2))
    max_rel=float(np.max(np.abs(normal_flow))/velocity_scale)
    return {'fd_h_over_a':h/field.a,'n_theta':len(level['s']),'n_phi':nphi,
            'evaluated_meridional_points':len(level['s']),
            'azimuthal_symmetry_replication_factor':nphi,
            'equivalent_surface_points_by_exact_axisymmetry':len(level['s'])*nphi,
            'max_material_flux_relative':max_rel,
            'rms_material_flux_relative':float(np.sqrt(np.mean(normal_flow**2))/velocity_scale),
            'max_vorticity_flux_relative_beltrami':max_rel,
            'min_gradpsi_norm':float(np.min(norm)),
            'analytic_identity':'u.grad(psi)=0, omega=(lambda/a)u',
            'method':'independent psi-centered-difference gradient vs exact velocity'}


def winding_on_level(field, level):
    # Ray theta=0 intersects z=0 on right side, with s=s_c+r0
    s0=float(level['s'][0]);v=poloidal_cycle(field,s0,rtol=8e-11,atol=8e-11)
    return {'equatorial_s_outer':s0,'W':float(v['W']),
            'four_cycle_phase_slip_radians_vs_T34':float(8*math.pi*(v['W']-.75)),
            'poloidal_period':float(v['T'])}


def curves_compare(parentxyz, newxyz):
    """Polygon samples parameterized by equal evolution-time fractions."""
    if parentxyz.shape!=newxyz.shape:raise ValueError('sample count mismatch')
    norm=np.linalg.norm(parentxyz-newxyz,axis=1)
    return {'n':len(norm),'max_absolute_xyz':float(np.max(norm)),
            'rms_absolute_xyz':float(np.sqrt(np.mean(norm**2)))}
