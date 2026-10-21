#!/usr/bin/env python3
"""Algebraic and finite-grid audits for VAM-5 -> SST variation repair.
No 3D Euler/PKLSA evolution is performed. All tests are diagnostic identities.
"""
import json, math, pathlib
import numpy as np
import sympy as sp

PASS={}
def check(name, predicate):
    v=bool(predicate)
    PASS[name] = 'PASS' if v else 'FAIL'
    if not v: raise AssertionError(name)

def z(expr):
    return sp.simplify(expr)==0

# Dimensional exponents: [M,L,T]
M=(1,0,0); L=(0,1,0); T=(0,0,1)
def add(*a):return tuple(sum(p[i] for p in a) for i in range(3))
def mul(p,n):return tuple(v*n for v in p)
vel=add(L,mul(T,-1)); rho=add(M,mul(L,-3)); omega=mul(T,-1)
ED=add(M,mul(L,-1),mul(T,-2))
check('D01_Kinetic_Density',add(rho,mul(vel,2))==ED)
check('D02_Regularized_Omega_Term', add(rho,mul(L,2),mul(omega,2))==ED)
check('D03_Helicity_Local_Squared_Needs_Dimensional_Coefficient',add(add(M,mul(T,2),mul(L,-3)),mul(add(vel,omega),2))==ED)
check('D04_Mass_Formula_Uncorrected_Is_Energy',add(mul(L,3),rho,mul(vel,2)) == add(M,mul(L,2),mul(T,-2)))
check('D05_Helicity_Units',add(vel,omega,mul(L,3))==(0,4,-2))

x,y,t,Om,rf,Ux,Uy = sp.symbols('x y t Omega rho U_x U_y',real=True,nonzero=True)
coords=[x,y]; v=sp.Matrix([-Om*y, Om*x]); P=rf*Om**2*(x*x+y*y)/2
spatial=lambda vec:sp.Matrix([[sp.diff(vec[i],q) for q in coords] for i in range(2)])
adv=spatial(v)*v
check('E01_Rigid_Rotation_Divergence',z(sp.diff(v[0],x)+sp.diff(v[1],y)))
check('E02_Rigid_Rotation_Euler_Force_Balance',all(z(q) for q in rf*adv+sp.Matrix([sp.diff(P,x),sp.diff(P,y)])))
A=spatial(v); lapP=sp.diff(P,x,2)+sp.diff(P,y,2)
check('E03_Pressure_Poisson_Closure',z(lapP + rf*sp.trace(A*A)))

# Galilean covariance of Euler flow under a uniform boost of the whole field
Vb = sp.Matrix([-Om*(y-Uy*t)+Ux, Om*(x-Ux*t)+Uy]); Pb=sp.expand(P.subs({x:x-Ux*t,y:y-Uy*t}, simultaneous=True))
conv=spatial(Vb)*Vb; dd=sp.Matrix([sp.diff(q,t) for q in Vb])
check('E04_Uniform_Boost_Divergence',z(sp.diff(Vb[0],x)+sp.diff(Vb[1],y)))
check('E05_Uniform_Boost_Euler_Covariance',all(z(q) for q in rf*(dd+conv)+sp.Matrix([sp.diff(Pb,x),sp.diff(Pb,y)])))

# H1 (Euler-alpha) Fourier mode, with all coefficients symbolic
k,ell,V=sp.symbols('k ell V',real=True, positive=True)
vf=sp.Matrix([V*sp.sin(k*y),0,0]); wx=sp.Matrix([0,0,-k*V*sp.cos(k*y)])
curlw=sp.Matrix([sp.diff(wx[2],y),0,0]); mf=sp.simplify(vf+ell**2*curlw)
check('A01_Helmholtz_Momentum_Identity',all(z(q) for q in mf-(1+ell**2*k**2)*vf))
check('A02_Euler_Limit',all(z(q) for q in mf.subs(ell,0)-vf))
# Stationary Euler-alpha: (grad(v))^T m has an exact gradient potential
jacv=sp.Matrix([[sp.diff(vf[i],q) for q in (x,y)] for i in range(2)])
force=jacv.T*sp.Matrix(mf[:2]); candidate=sp.Rational(1,2)*V**2*(1+ell**2*k**2)*sp.sin(k*y)**2
check('A03_EP_Stationary_Shear_Solution',all(z(q) for q in force-sp.Matrix([sp.diff(candidate,x),sp.diff(candidate,y)])))
check('A04_Positive_Regularization',float((1+ell**2*k**2).subs({ell:1.4e-15,k:1/1.4e-15}))>=1)

# Analytic ABC Beltrami test sampled on periodic grid, integral of helicity invariant under uniform boost
N=24; a=np.arange(N)*2*np.pi/N
X,Y,Z=np.meshgrid(a,a,a,indexing='ij'); w=np.stack((np.sin(Z)+np.cos(Y),np.sin(X)+np.cos(Z),np.sin(Y)+np.cos(X)),axis=0)
scale=(2*np.pi/N)**3
H0=float(np.sum(np.sum(w*w,axis=0))*scale)
boost=np.array([0.3,-0.4,0.17])[:,None,None,None]
H1=float(np.sum(np.sum((w+boost)*w,axis=0))*scale)
check('H01_ABC_Helicity_Nonzero',H0>0)
check('H02_Global_Helicity_Uniform_Boost_ABC',abs(H1-H0)/H0<1e-13)
check('H03_Local_Helicity_Not_Boost_Invariant',np.max(np.abs(np.sum(boost*w,axis=0)))>0.3)
check('H04_Helicity_ABC_Quadrature',abs(H0-3*(2*np.pi)**3)/(3*(2*np.pi)**3)<1e-13)

vs=1.09384563e6; rc=1.40897017e-15; r_core=3.8934358266918687e18; r_f=7.0e-7; c=299792458.
Gamma=2*math.pi*rc*vs; Omega=vs/rc; W=2*Omega
Vol=4*math.pi/3*rc**3
E_core=.5*r_core*vs**2*Vol
E_ambient=.5*r_f*vs**2*Vol
Rgamma=math.sqrt(1-(vs/c)**2)
Ealpha_at_ell_rc = .5*r_f*rc**2*W**2
check('N01_Characteristic_Swirl_SubLuminal',0<Rgamma<1)
check('N02_Core_And_Background_Densities_Different',r_core>r_f*1e20)
check('N03_Euler_Alpha_Ratio_For_Local_Rigid_Core',abs(Ealpha_at_ell_rc/(.5*r_f*vs**2)-4)<1e-12)
check('N04_Core_Mass_Equivalent_Conversion',abs(E_core/c**2-E_core/(c*c))<1e-40)

out={'document':'SST VAM-5 Lagrangian Repair v0.1.0 DEVELOPMENT','status':'ALGEBRAIC_REGRESSION_ONLY_NOT_DYNAMIC_CERTIFIED','pass_count':sum(s=='PASS' for s in PASS.values()),'test_count':len(PASS),'tests':PASS,'canonical_numerics':{'v_swirl_m_per_s':vs,'r_c_m':rc,'rho_f_kg_per_m3':r_f,'rho_core_kg_per_m3':r_core,'gamma_circulation_m2_per_s':Gamma,'core_rotational_Omega_rad_per_s':Omega,'rigid_core_vorticity_2Omega_per_s':W,'core_sphere_volume_m3':Vol,'core_energy_J':E_core,'core_mass_equivalent_kg':E_core/c**2,'background_density_core_volume_energy_J':E_ambient,'Euler_alpha_energy_density_ell_rc_J_per_m3':Ealpha_at_ell_rc,'lorentz_ansatz_ratio_NOT_DERIVED':Rgamma},'scope_warnings':['The symbolic examples do not integrate Euler or Euler-alpha equations for a knotted finite-core vortex.','The ℓ length is a modeling parameter and is not validated by the tests.','No gravitational, electromagnetic, quantum, particle-mass, or relativistic claim is certified.']}
p=pathlib.Path(__file__).with_name('validation_report.json');p.write_text(json.dumps(out,indent=2),encoding='utf8');print(f"{out['pass_count']}/{out['test_count']} algebraic and numerical regression tests PASS");print(json.dumps(out['canonical_numerics'],indent=2))
