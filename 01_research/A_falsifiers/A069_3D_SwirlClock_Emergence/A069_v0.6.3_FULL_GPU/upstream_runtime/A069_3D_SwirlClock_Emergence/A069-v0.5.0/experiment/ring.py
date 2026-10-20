"""Thin vortex-ring asymptotics and Hamiltonian identity, not thick-core physics."""
from __future__ import annotations
import numpy as np

def energy(R,a,rho,gamma,alpha):return .5*rho*gamma**2*R*(np.log(8*R/a)-alpha)
def impulse(R,rho,gamma):return rho*gamma*np.pi*R*R
def velocity(R,a,gamma,beta):return gamma/(4*np.pi*R)*(np.log(8*R/a)-beta)
def check_case(alpha,geometry='fixed_core'):
    R=40.;a0=1.;rho=1.1;gamma=0.7;h=1.e-3
    if geometry=='fixed_core':
        a=lambda R:a0; beta=alpha-1
    elif geometry=='constant_core_volume':
        a=lambda R:a0*np.sqrt(40./R);beta=alpha-1.5
    else:raise ValueError(geometry)
    dE=(energy(R+h,a(R+h),rho,gamma,alpha)-energy(R-h,a(R-h),rho,gamma,alpha))/(2*h)
    dP=(impulse(R+h,rho,gamma)-impulse(R-h,rho,gamma))/(2*h)
    U=velocity(R,a(R),gamma,beta)
    return {'geometry':geometry,'alpha':alpha,'beta':beta,'R_over_a':R/a(R),
            'finite_difference_velocity':float(dE/dP),'formula_velocity':float(U),
            'relative_error':float(abs(dE/dP-U)/max(abs(U),1e-15))}
def ring_suite():
    cases=[check_case(1.615,geometry) for geometry in ('fixed_core','constant_core_volume')]
    passed=all(c['relative_error']<3e-8 for c in cases)
    return {'schema':'A069-NLS-THIN-RING-REFERENCE-1','status':'PASS' if passed else 'FAIL',
     'classification':'ANALYTIC_CONTROL_ONLY',
     'thin_core_required':True,'test_R_over_a':40.,
     'roberts_grant_reference_alpha':1.615,'roberts_grant_reference_beta':.615,
     'fat_core_R_over_a_0_898_is_excluded':True,'predicted_clock_frequency':False,
     'energy_impulse_derivative_checks':cases}
