"""Pure mathematical diagnostics. NO validated SST particle/EM/thermal interpretation.
All SI dimensions explicit. Python standard library only.
"""
from __future__ import annotations
import math

HBAR = 1.054571817e-34       # J*s
H = 6.62607015e-34           # J*s
E_CHARGE = 1.602176634e-19  # J/eV
KB = 1.380649e-23           # J/K
C = 299792458.0              # m/s
M_E = 9.1093837139e-31      # kg
R_C = 1.40897017e-15        # m
V_SWIRL = 1.09384563e6      # m/s
RHO_F = 7.0e-7               # kg/m3
A0 = 5.29177210903e-11      # m, conventional Bohr radius as a reference

def gamma_sst() -> float:
    """m^2/s, circular core-speed *defined* relation; not a quantization proof."""
    return 2.0*math.pi*R_C*V_SWIRL

def gamma_h_over_me() -> float:
    """m^2/s, external quantum circulation prescription used by the historical paper."""
    return H/M_E

def kelvin_omega(gamma: float, L: float, xi: float, m: int, C0: float = 1.0) -> float:
    """rad/s, local-straight-filament asymptotic dispersion; NOT closed-ring eigenvalue.

    At finite L, the ring's curvature invalidates a direct eigenmode interpretation,
    especially for neutral/geometrical modes. Use m>=2 for diagnostic tables only.
    """
    if not (gamma > 0 and L > 0 and xi > 0 and m >= 1):
        raise ValueError('positive gamma,L,xi and integer m>=1 required')
    k = 2*math.pi*m/L
    if k*xi >= 0.1:
        raise ValueError('thin-filament small-kxi asymptotic regime violated')
    return gamma*k*k/(4*math.pi)*(math.log(1/(k*xi))+C0)

def kelvin_spectrum(gamma: float, L: float, xi: float, max_mode: int = 10, C0:float=1.0):
    """Geometric periodic-wavenumber surrogate, not an actual PKLSA spectral solver."""
    return [{'m':m,'k_m_inverse':2*math.pi*m/L,'kxi':2*math.pi*m*xi/L,
            'omega_rad_s':(w:=kelvin_omega(gamma,L,xi,m,C0)),
            'hbar_omega_eV':HBAR*w/E_CHARGE}
            for m in range(2,max_mode+1)]

def gap_threshold_eV(T_K:float, x_min:float=60.):
    if T_K<=0 or x_min<0:raise ValueError
    return x_min*KB*T_K/E_CHARGE

def boson_thermal_energy_J(gap_J:float,T_K:float):
    """Thermal excess energy of a single quantized harmonic oscillator, zero-point omitted."""
    if gap_J<0 or T_K<=0:raise ValueError
    if gap_J==0:return KB*T_K
    x=gap_J/(KB*T_K)
    return 0. if x>700 else gap_J/math.expm1(x)

def boson_heat_capacity_J_per_K(gap_J:float,T_K:float):
    if gap_J<0 or T_K<=0: raise ValueError
    if gap_J==0:return KB
    x=gap_J/(KB*T_K)
    if x>700:return 0.
    if x<1e-5:return KB*(1-x*x/12)
    q=math.exp(-x)
    return KB*x*x*q/((1-q)*(1-q))

def bose_thermal_upper_bound_J(gap_J:float,T_K:float,N_modes:int):
    """Every mode with E_j>=Delta has thermal excess sum <= N Delta/(e^(beta Delta)-1).
    Requires a finite number N of independent bosonic harmonic modes and Delta>0.
    """
    if N_modes<0 or gap_J<=0:raise ValueError
    return N_modes*boson_thermal_energy_J(gap_J,T_K)

def electric_like_impedance_ratio(z_s_Rayl:float,z_other_Rayl:float):
    """Dimensionless impedance-inspired candidate; no proof of two-field coupling."""
    if min(z_s_Rayl,z_other_Rayl)<=0:raise ValueError
    return 4*z_s_Rayl/z_other_Rayl

def transfer_state(t:float, E_s0_J:float, g_per_s:float, d_s_per_s:float,
                   d_e_per_s:float, efficiency:float=1.0):
    """Coarse-grained UNIDIRECTIONAL energy-transfer model (not Euler dynamics).

    dE_s/dt=-(d_s+g)E_s
    dE_e/dt=eta*g*E_s-d_e*E_e
    E_loss=E_s0-E_s-E_e (dE_loss/dt >=0)
    """
    if t<0 or E_s0_J<0 or min(g_per_s,d_s_per_s,d_e_per_s)<0 or not (0<=efficiency<=1):
        raise ValueError
    a=d_s_per_s+g_per_s; b=d_e_per_s
    s=E_s0_J*math.exp(-a*t)
    if abs(a-b)<1e-12*max(1,a,b):
        e=efficiency*g_per_s*E_s0_J*t*math.exp(-a*t)
    else:
        e=efficiency*g_per_s*E_s0_J*(math.exp(-a*t)-math.exp(-b*t))/(b-a)
    l=E_s0_J-s-e
    return {'E_swirl_J':s,'E_em_J':e,'E_loss_J':l}

def transfer_peak_s(a:float,b:float):
    """Peak time of response with nonzero positive source/transfer: 2 positive inverse lifetimes."""
    if a<=0 or b<=0:raise ValueError
    if abs(a-b)<1e-12*max(a,b):return 1./a
    return math.log(b/a)/(b-a)

def matrix_eigenfrequencies(ms:float,me:float,ks:float,ke:float,g:float):
    """rad/s, two coupled conservative oscillators with position variables in metres.
    V = 1/2 ks xs²+1/2 ke xe²+1/2 g(xs-xe)²; g is N/m.
    """
    if min(ms,me,ks,ke)<0 or ms==0 or me==0 or g<0:raise ValueError
    aa=(ks+g)/ms; dd=(ke+g)/me; off=g/math.sqrt(ms*me)
    d=math.sqrt((aa-dd)**2+4*off**2)
    vals=((aa+dd-d)/2,(aa+dd+d)/2)
    if any(x< -1e-12 for x in vals):raise ValueError('unstable stiffness')
    return tuple(math.sqrt(max(0,x)) for x in vals)

def oscillator_energy(qs:float,qe:float,vs:float,ve:float,ms:float,me:float,ks:float,ke:float,g:float)->float:
    return .5*ms*vs**2+.5*me*ve**2+.5*ks*qs**2+.5*ke*qe**2+.5*g*(qs-qe)**2

def oscillator_acc(qs:float,qe:float,ms:float,me:float,ks:float,ke:float,g:float):
    return (-(ks*qs+g*(qs-qe))/ms,-(ke*qe+g*(qe-qs))/me)

def oscillator_velocity_verlet(qs,qe,vs,ve,ms,me,ks,ke,g,dt,steps):
    """Return [(t,E)], for a 2-DOF symplectic mathematical baseline."""
    if dt<=0 or steps<0:raise ValueError
    entries=[(0.,oscillator_energy(qs,qe,vs,ve,ms,me,ks,ke,g))]
    for i in range(steps):
        a,b=oscillator_acc(qs,qe,ms,me,ks,ke,g)
        vhalf_s=vs+.5*dt*a;vhalf_e=ve+.5*dt*b
        qs+=dt*vhalf_s; qe+=dt*vhalf_e
        a,b=oscillator_acc(qs,qe,ms,me,ks,ke,g)
        vs=vhalf_s+.5*dt*a;ve=vhalf_e+.5*dt*b
        if (i+1)%max(1,steps//100)==0 or i==steps-1:
            entries.append(((i+1)*dt,oscillator_energy(qs,qe,vs,ve,ms,me,ks,ke,g)))
    return entries
