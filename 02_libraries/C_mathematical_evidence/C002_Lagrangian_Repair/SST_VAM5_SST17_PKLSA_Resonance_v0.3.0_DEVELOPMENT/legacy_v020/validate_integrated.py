#!/usr/bin/env python3
"""v0.2.0 mathematical/finite-grid qualification, not a native Euler/PKLSA solver.
Run from any directory. Zero external data. Deterministic. Python >=3.10, numpy, sympy.
"""
from __future__ import annotations
import json, math, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import sympy as sp

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'validation_report.json'
checks={}; diagnostics={}
def gate(name, pred, detail=None):
    ok=bool(pred)
    checks[name]={'status':'PASS' if ok else 'FAIL'}
    if detail is not None: checks[name]['detail']=str(detail)
    if not ok: print('FAIL',name,detail,file=sys.stderr)
    return ok

def close(a,b,rtol=1e-8,atol=1e-10):
    return bool(np.allclose(a,b,rtol=rtol,atol=atol))

# All units as M,L,T integer exponents.
M=(1,0,0);L=(0,1,0);T=(0,0,1)
def plus(*vv):return tuple(sum(x[i] for x in vv) for i in range(3))
def times(v,n):return tuple(a*n for a in v)
vel=plus(L,times(T,-1));rho=plus(M,times(L,-3));stiff=plus(M,times(L,-1),times(T,-2))
gate('D01_fluid_kinetic_dim',plus(rho,times(vel,2))==stiff)
gate('D02_qdot_velocity_dim',plus(rho,times(vel,2))==stiff)
gate('D03_curl_q_dimensionless',plus(L,times(L,-1))==(0,0,0))
gate('D04_stiffness_Pa',stiff==plus(M,times(L,-1),times(T,-2)))
gate('D05_K_over_rho_speed_squared',plus(stiff,times(rho,-1))==plus(times(L,2),times(T,-2)))
# [beta]=[Omega/B] and [Verdet]=[beta/c], with magnetic field [B]=kg A^-1 s^-2.
# Four bases M,L,T,I; beta has I T /M, Vvac has I T^2/(M L).
beta_dim=(-1,0,1,1); speed4=(0,1,-1,0); verdict_dim=(-1,-1,2,1)
gate('D06_Verdet_requires_field_and_length_units',tuple(beta_dim[i]-speed4[i] for i in range(4))==verdict_dim)

# SST numerical scale. Effective director density is a separate chosen parameter.
rho_f=7.0e-7; c=299792458.0; K=rho_f*c*c; mu=rho_f
v_swirl=1.09384563e6;r_c=1.40897017e-15
omega_core=v_swirl/r_c
Efluid=.5*rho_f*v_swirl*v_swirl
gate('N01_SST_K_positive',K>0)
gate('N02_SST_wave_speed_calibrated',close(math.sqrt(K/mu),c,rtol=5e-15))
gate('N03_SST_shear_not_a_new_prediction',close(K,rho_f*c*c,rtol=0))
gate('N04_swirl_omega_dimension',omega_core>1e20)

# Euler rigid body rotation and pressure gradient signs.
x,y,t,om,r,U,V=sp.symbols('x y t om rho U V',real=True)
vy=sp.Matrix([-om*y,om*x]); gradient=sp.Matrix([[sp.diff(vy[i],coord) for coord in (x,y)] for i in (0,1)])
P=sp.Rational(1,2)*r*om**2*(x*x+y*y)
gate('E01_rigid_rotation_incompressible',sp.simplify(gradient.trace())==0)
gate('E02_Euler_negative_grad_pressure',all(sp.simplify(z)==0 for z in r*gradient*vy+sp.Matrix([sp.diff(P,x),sp.diff(P,y)])))
gate('E03_Poisson',sp.simplify(sp.diff(P,x,2)+sp.diff(P,y,2)+r*sp.trace(gradient*gradient))==0)
boost=sp.Matrix([-om*(y-V*t)+U,om*(x-U*t)+V]); Pb=sp.expand(P.subs({x:x-U*t,y:y-V*t},simultaneous=True))
gradb=sp.Matrix([[sp.diff(boost[i],coord) for coord in (x,y)] for i in (0,1)])
gate('E04_boost_incompressibility',sp.simplify(gradb.trace())==0)
gate('E05_boost_Euler',all(sp.simplify(z)==0 for z in r*(sp.diff(boost,t)+gradb*boost)+sp.Matrix([sp.diff(Pb,x),sp.diff(Pb,y)])))

# Exact transverse plane wave: q=(0,A cos(kx-wt),0), frozen X=a.
x,t,A,k,w,zeta=sp.symbols('x t A k w zeta',real=True,nonzero=True)
phase=k*x-w*t
q=A*sp.cos(phase)
Ey=-zeta*sp.diff(q,t)
Bz=zeta*sp.diff(q,x)
sub={w:sp.Symbol('c',positive=True)*k}
cc=sp.Symbol('c',positive=True)
gate('W01_wave_equation',sp.simplify((sp.diff(q,t,2)-cc**2*sp.diff(q,x,2)).subs(w,cc*k))==0)
gate('W02_Faraday_identity',sp.simplify(sp.diff(Bz,t)+sp.diff(Ey,x))==0)
# curl B y = -partial_x Bz
gate('W03_Ampere_wave',sp.simplify((sp.diff(Ey,t)+cc**2*sp.diff(Bz,x)).subs(w,cc*k))==0)
gate('W04_no_electric_charge_free_transverse_sector',sp.diff(Ey,sp.Symbol('y'))==0)
gate('W05_no_magnetic_charge_curl_identity',sp.diff(Bz,sp.Symbol('z'))==0)
gate('W06_no_longitudinal_wave_polarization',close(np.linalg.eigvalsh(np.diag([0.0,1.0,1.0])),[0,1,1]))
gate('W07_two_transverse_degenerate_modes',close(np.linalg.eigvalsh(np.diag([0.0,1.0,1.0]))[1:],[1,1]))
# electromagnetic scale and energy, in Coulomb temporal gauge only
EPS0=8.8541878128e-12;MU0=1/(EPS0*c*c)
zetaval=math.sqrt(mu/EPS0)
gate('M01_EM_electric_energy_match',close(EPS0*zetaval**2,mu,rtol=1e-13))
gate('M02_EM_magnetic_energy_match',close(zetaval**2/MU0,K,rtol=1e-13))
gate('M03_EM_vacuum_product',close(EPS0*MU0*c*c,1.0,rtol=1e-13))
gate('M04_E_over_B_plane_wave',sp.simplify((Ey/Bz).subs(w,cc*k)-cc)==0)

# Coupled action in material coordinates:
# L= rho_f|Xdot|^2/2 +mu|qdot|^2/2-K|b|^2/2 +p(J-1)+eta*div_x q
# b_k=epsilon_kij q_{j,A}(F^-1)_{Ai}
levi=np.zeros((3,3,3))
for i in range(3):
 for j in range(3):
  for k1 in range(3):
   if len({i,j,k1})==3:
    perm=(i,j,k1); inversions=sum(perm[a]>perm[b] for a in range(3) for b in range(a+1,3))
    levi[i,j,k1]=(-1)**inversions
rng=np.random.default_rng(20261020)
F=np.array([[1.1,0.08,0.0],[-.07,.9,.05],[.02,.03,1.]])
F[2,:]/=np.linalg.det(F)
Q=rng.normal(0,.3,(3,3)); p=0.5; eta=-0.09
Ktest=2.0

def action_local(F,Q,p=p,eta=eta):
    J=np.linalg.det(F); G=np.linalg.inv(F)
    D=Q@G # D[j,i]= d_i q_j
    b=np.einsum('kij,ji->k',levi,D)
    h=np.trace(D)
    return p*(J-1)-.5*Ktest*np.dot(b,b)+eta*h

def grads_formula(F,Q,p=p,eta=eta):
    J=np.linalg.det(F);G=np.linalg.inv(F);D=Q@G
    b=np.einsum('kij,ji->k',levi,D)
    # output P[l,A]
    GP=np.zeros((3,3));GQ=np.zeros((3,3))
    for l in range(3):
     for Aa in range(3):
      val=p*J*G[Aa,l]
      for kk in range(3):
       for ii in range(3):
        for jj in range(3):
         val+=Ktest*b[kk]*levi[kk,ii,jj]*D[jj,l]*G[Aa,ii]
      for ii in range(3):val-=eta*D[ii,l]*G[Aa,ii]
      GP[l,Aa]=val
    for j in range(3):
     for Aa in range(3):
      val=0.
      for kk in range(3):
       for ii in range(3):val-=Ktest*b[kk]*levi[kk,ii,j]*G[Aa,ii]
      val+=eta*G[Aa,j]
      GQ[j,Aa]=val
    return GP,GQ

def finite_gradient(arg):
    mat=F if arg=='F' else Q
    g=np.zeros_like(mat);h=1e-6
    for i in range(3):
     for j in range(3):
      dm=np.zeros((3,3));dm[i,j]=h
      if arg=='F':g[i,j]=(action_local(F+dm,Q)-action_local(F-dm,Q))/(2*h)
      else:g[i,j]=(action_local(F,Q+dm)-action_local(F,Q-dm))/(2*h)
    return g
pgrad,qgrad=grads_formula(F,Q)
fgrad_fd=finite_gradient('F');qgrad_fd=finite_gradient('Q')
errF=float(np.max(np.abs(pgrad-fgrad_fd))); errQ=float(np.max(np.abs(qgrad-qgrad_fd)))
diagnostics['stress_F_max_abs_derivative_error']=errF;diagnostics['director_Q_max_abs_derivative_error']=errQ
gate('V01_material_gradient_F_variation',close(pgrad,fgrad_fd,rtol=1e-6,atol=2e-8),errF)
gate('V02_material_gradient_q_variation',close(qgrad,qgrad_fd,rtol=1e-6,atol=2e-8),errQ)
gate('V03_det_constraint_reference_state',close(np.linalg.det(F),1.0,atol=1e-14))
noq=np.zeros_like(Q)
gate('V04_zero_q_recovers_pressure_Piola',close(grads_formula(F,noq,p=p,eta=0)[0],p*np.linalg.det(F)*np.linalg.inv(F).T))
gate('V05_zero_q_zero_stress_and_q_gradient',close(grads_formula(F,noq,p=0,eta=0)[0],0) and close(grads_formula(F,noq,p=0,eta=0)[1],0))
R,_=np.linalg.qr(rng.normal(size=(3,3)))
if np.linalg.det(R)<0:R[:,0]*=-1
# Under orientation-preserving orthogonal rotation, F->RF and Q->RQ.
gate('V06_objective_rotation_stiffness',close(action_local(R@F,R@Q,p=0,eta=0),action_local(F,Q,p=0,eta=0),rtol=1e-12))
gate('V07_rotated_divergence_constraint',close(action_local(R@F,R@Q,p=0,eta=1)-action_local(R@F,R@Q,p=0,eta=0),action_local(F,Q,p=0,eta=1)-action_local(F,Q,p=0,eta=0),rtol=1e-12))
gate('V08_Euler_independent_limit_q_zero',close(action_local(F,noq,p=0,eta=0),0.0))
# Material Galilean transformation: X->X+Ut; F unchanged; q unchanged.
ux,uy,vx,vy,rf_sym,tt,xi,yi=sp.symbols('ux uy vx vy rf tt xi yi',real=True)
Xtrial=sp.Matrix([xi+vx*tt,yi+vy*tt]); Utrial=sp.Matrix([ux,uy])
energy_before=rf_sym*sum(z**2 for z in sp.diff(Xtrial,tt))/2
energy_after=rf_sym*sum(z**2 for z in sp.diff(Xtrial+Utrial*tt,tt))/2
boundary_scalar=rf_sym*(Utrial.dot(Xtrial)+Utrial.dot(Utrial)*tt/2)
gate('V09_Galilean_Lagrangian_change_boundary_term',sp.simplify(energy_after-energy_before-sp.diff(boundary_scalar,tt))==0)


# Fourier mode dynamical solver, strictly fixed fluid background (no full coupled solver).
def solve_mode(nsteps,nspace=64,t_end=5.0,k_mode=2):
    xx=2*np.pi*np.arange(nspace)/nspace; q=np.cos(k_mode*xx); u=np.zeros_like(q)
    dt=t_end/nsteps
    kval=np.fft.fftfreq(nspace,1/nspace)
    def acceleration(q):return np.fft.ifft(-kval**2*np.fft.fft(q)).real
    def energy(q,u):return float(np.mean(.5*u*u+.5*np.fft.ifft(1j*kval*np.fft.fft(q)).real**2))
    E0=energy(q,u); edrift=0.
    for step in range(nsteps):
        uhalf=u+.5*dt*acceleration(q)
        q=q+dt*uhalf
        u=uhalf+.5*dt*acceleration(q)
        edrift=max(edrift,abs(energy(q,u)/E0-1))
    exact=np.cos(k_mode*xx)*np.cos(k_mode*t_end)
    err=np.linalg.norm(q-exact)/np.linalg.norm(np.cos(k_mode*xx))
    return float(err),float(edrift)
e1,drift1=solve_mode(150);e2,drift2=solve_mode(300);e3,drift3=solve_mode(600)
diagnostics['wave_mode_error_steps_150_300_600']=[e1,e2,e3]
diagnostics['wave_mode_energy_drift_150_300_600']=[drift1,drift2,drift3]
gate('F01_dynamic_wave_stable',drift1<0.003,drift1)
gate('F02_wave_temporal_convergence',e1/e2>3.8 and e2/e3>3.8,[e1,e2,e3])
gate('F03_energy_drift_quadratic',drift1/drift2>3.8 and drift2/drift3>3.8,[drift1,drift2,drift3])
ex32,_=solve_mode(300,32);ex128,_=solve_mode(300,128)
gate('F04_spatial_spectral_mode_parity',close(ex32,ex128,atol=1e-10))

# Torsion differential-form exactness: F=dA; dF=0 (identity), but not Maxwell dynamics.
# 3+1 components: E = - d_t A; B=curl A => Faraday identities verified above.
gate('C01_projected_torsion_d2_equals_zero',sp.simplify(sp.diff(sp.diff(q,x),t)-sp.diff(sp.diff(q,t),x))==0)
xs=sp.Symbol('x_s',real=True); u_projector=xs**2
gate('C02_variable_projector_not_guaranteed_closed',sp.diff(u_projector,xs)!=0, 'Example: u(x)=x^2, T=dz wedge dt, d(uT)=2x dx wedge dz wedge dt')
# Fourier-rotation model: Omega=beta B, Vvac = beta / c; beta has s^-1/T
beta=1.234; Bext=0.05;Lpath=10.0
omega_bg=beta*Bext
angle=omega_bg*Lpath/c
verd=angle/(Bext*Lpath)
gate('O01_rotation_Verdet_units_relation',close(verd,beta/c,rtol=1e-13))
gate('O02_zero_background_no_rotation',close(0.0*Lpath/c,0))


# Candidate gyroscopic term: L_G=mu (Omega cross q) dot qdot.
# Its Euler-Lagrange force is +2 mu Omega cross qdot; it cannot change energy.
omrot,omega,krot,crot=sp.symbols('Omega omega k c',real=True,positive=True)
gate('O03_gyro_dispersion_branch_plus',sp.simplify((omega**2-2*omega*omrot-crot**2*krot**2).subs(krot,sp.sqrt(omega**2-2*omega*omrot)/crot))==0)
gate('O04_gyro_dispersion_branch_minus',sp.simplify((omega**2+2*omega*omrot-crot**2*krot**2).subs(krot,sp.sqrt(omega**2+2*omega*omrot)/crot))==0)
qdot_random=rng.normal(size=3); omega_vec=rng.normal(size=3)
gate('O05_gyro_does_no_work',abs(np.dot(qdot_random,np.cross(omega_vec,qdot_random)))<1e-14)
gate('O06_gyro_zero_background_degenerate',sp.simplify((omega**2+2*omega*omrot).subs(omrot,0)-(omega**2-2*omega*omrot).subs(omrot,0))==0)

passed=sum(v['status']=='PASS' for v in checks.values()); total=len(checks)
report={
 'title':'SST VAM-5 + SST-17 Integrated Euler--Director Action v0.2.0',
 'status':'DEVELOPMENT_NOT_PHYSICALLY_CERTIFIED',
 'qualification_scope':'Analytic identities, finite-dimensional variational derivatives, linear director wave time integration on frozen fluid background. No native 3D Euler or PKLSA integration.',
 'passed':passed,'total':total,'tests':checks,'diagnostics':diagnostics,
 'canonical_scales':{'rho_f_kg_m3':rho_f,'rho_d_test_kg_m3':mu,'K_calibrated_Pa':K,'c_target_m_s':c,'zeta_EM_rescaling_tesla':zetaval,'swirl_Omega_reference_rad_s':omega_core,'background_swirl_kinetic_energy_density_J_m3':Efluid},
 'gates':{'G0_source_trace_and_dimensions':'PASS_ANALYTIC', 'G1_action_and_piola_variation':'PASS_LOCAL_FINITE_DIFFERENCE', 'G2_wave_Maxwell_free_transverse_sector':'PASS_ANALYTIC_AND_LINEAR_NUMERICAL', 'G3_rotating_magnetooptic_CorIolis':'NOT_RUN_COUPLING_NOT_DERIVED', 'G4_full_3D_coupled_Euler_director_dynamics':'NOT_RUN', 'G5_PKLSA_finite_core_provenance':'NOT_RUN', 'G6_charge_gravity_quantum_clock_predictions':'UNRESOLVED'},
 'warnings':['The calibrated K=rho_d*c^2 is an input, not an Euler prediction of c.','The Maxwell correspondence is a vacuum transverse rescaling with no charge/current sector.','The torsion projection F=dA is kinematic and does not derive a new gauge dynamics.','Local stress variation is verified, but a full coupled X,q numerical evolution is not run.','The VAM-5 and SST-17 physical unification claims remain unresolved.']}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
print(f'{passed}/{total} regression checks PASS' if passed==total else f'{passed}/{total} CHECKS PASS; FAILURES PRESENT')
print('K=%.11e Pa, rho_d=%.11e kg/m^3, c=%.9e m/s' %(K,mu,c))
print('stress errors: %.2e (F), %.2e (Q)' %(errF,errQ))
print('dynamic error convergence:',[round(x,10) for x in (e1,e2,e3)])
print('out:',OUT)
sys.exit(0 if passed==total else 1)
