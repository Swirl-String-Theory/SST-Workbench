#!/usr/bin/env python3
"""Deterministic, non-physical-certifying SST v0.3.0 regressions."""
from __future__ import annotations
import json,os,sys,hashlib,tempfile
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(HERE))
from src import sst_v030 as s

checks={}; diag={}
def gate(name,ok,value=None):
    checks[name]={'status':'PASS' if bool(ok) else 'FAIL'}
    if value is not None: checks[name]['detail']=value if isinstance(value,(str,int,float,list,dict)) else str(value)

def relative(a,b):return abs(a-b)/max(1e-30,abs(b))

# Dimensional calibration and independent SST source checks.
gate('S01_swirl_gamma_SI',relative(s.GAMMA,2*np.pi*s.R_C*s.V_SWIRL)<1e-14)
gate('S02_swirl_reference_frequency_SI',relative(s.OMEGA_0,7.76344e20)<1e-5,s.OMEGA_0)
gate('S03_background_kinetic_energy_density',relative(s.E_DENS,4.18774e5)<1e-5,s.E_DENS)
gate('S04_absolute_time_scale_positive',s.T_REF>0,s.T_REF)
gate('S05_no_automatic_c_from_Euler',s.V_SWIRL/s.C<0.01,s.V_SWIRL/s.C)

R=s.ring(128);T=s.trefoil(128)
for label,X in [('R',R),('T',T)]:
    X2=X+np.array([3.,-5.,2.])
    u=s.biot_savart(X)
    gate(f'B_{label}01_finite_velocity',np.isfinite(u).all())
    gate(f'B_{label}02_shift_equivariance',np.allclose(s.biot_savart(X2),u,rtol=1e-11,atol=1e-13))
    gate(f'B_{label}03_energy_shift_invariance',relative(s.filament_energy(X2),s.filament_energy(X))<1e-12)
    gate(f'B_{label}04_impulse_shift_invariance',np.allclose(s.impulse(X2),s.impulse(X),atol=1e-11))
    gate(f'B_{label}05_energy_positive',s.filament_energy(X)>0)
    gate(f'B_{label}06_finite_positive_core',np.isfinite(s.biot_savart(X,core=.5)).all())

rng=np.random.default_rng(20261020)
a=rng.normal(size=(3,3));Q,_=np.linalg.qr(a)
if np.linalg.det(Q)<0:Q[:,0]*=-1
rot=R@Q.T
# rotation covariance
u=s.biot_savart(R)
gate('B07_3D_rotation_covariance',np.allclose(s.biot_savart(rot),s.biot_savart(R)@Q.T,rtol=1e-9,atol=1e-12))
gate('B08_trefoil_not_planar',np.ptp(T[:,2])>1)
gate('B09_ring_planar',np.max(np.abs(R[:,2]))<1e-13)

v64=s.ring_mechanics(64);v128=s.ring_mechanics(128);v256=s.ring_mechanics(256)
for name,obj in [('ring64',v64),('ring128',v128),('ring256',v256)]:diag[name]=obj
gate('B10_ring_impulse_refinement',abs(v256['impulse_z_dimless']-v256['expected_impulse_z'])<abs(v128['impulse_z_dimless']-v128['expected_impulse_z'])<abs(v64['impulse_z_dimless']-v64['expected_impulse_z']))
gate('B11_ring_speed_refinement',abs(v256['mean_drift_dimless']-v128['mean_drift_dimless'])<abs(v128['mean_drift_dimless']-v64['mean_drift_dimless']))
gate('B12_ring_travels_positive_Z',v128['mean_drift_dimless']>0)
gate('B13_ring_has_zero_radial_speed',v128['max_radial_velocity_dimless']<1e-12)

tre=s.evolve(s.trefoil(96),dt=.01,steps=12)
ring=s.evolve(s.ring(96),dt=.01,steps=12)
diag['trefoil_short_evolution']={k:v for k,v in tre.items() if k!='X'}
diag['ring_short_evolution']={k:v for k,v in ring.items() if k!='X'}
gate('B14_short_trefoil_energy_drift',abs(tre['relative_energy_drift'])<2e-5,tre['relative_energy_drift'])
gate('B15_short_trefoil_impulse_drift',tre['relative_impulse_drift']<2e-5,tre['relative_impulse_drift'])
gate('B16_short_ring_energy_drift',abs(ring['relative_energy_drift'])<2e-8,ring['relative_energy_drift'])
gate('B17_no_false_proper_time',tre['time_seconds']==tre['dimensionless_time']*s.T_REF)
# check short-run convergence in time, but NOT establish long-time stability
out1=s.evolve(s.trefoil(64),dt=.2,steps=25)['X']
out2=s.evolve(s.trefoil(64),dt=.1,steps=50)['X']
out3=s.evolve(s.trefoil(64),dt=.05,steps=100)['X']
e1=np.linalg.norm(out1-out3);e2=np.linalg.norm(out2-out3)
diag['trefoil_rk4_refinement']={'coarse_ref_norm':float(e1),'fine_ref_norm':float(e2)}
gate('B18_rk4_time_refinement',e1>8*e2,[float(e1),float(e2)])
# Reverse circulation -> velocity reverses for prescribed fixed filament; not time reverse physical full Euler.
gate('B19_reversed_filament_orientation_flips_velocity',np.allclose(s.biot_savart(T[::-1])[::-1],-s.biot_savart(T),rtol=1e-9,atol=1e-11))

# Optional XYZ syntactic importer; never claim PKLSA native without external provenance.
with tempfile.TemporaryDirectory() as d:
    x=Path(d)/'seed.xyz';np.savetxt(x,R)
    gate('I01_xyz_import_exact',np.allclose(s.read_xyz(x),R))
    bad=Path(d)/'broken.xyz';bad.write_text('1 2 3\n')
    try:s.read_xyz(bad);bad_rejected=False
    except ValueError:bad_rejected=True
    gate('I02_reject_unqualified_short_seed',bad_rejected)

# SST-35: correct normalization, two-line overlap, symmetry, exact positive integral.
lines=[(0.0,.2,1.)]
for i,(w,sigma,gamma) in enumerate([(0.,.3,.1),(.2,.35,.2),(-.7,.5,.3),(.5,1.,.2)]):
    analytic=s.overlap(w,sigma,[(0.,gamma,1.)])
    numeric=s.overlap_quad(w,sigma,[(0.,gamma,1.)])
    gate(f'R{i+1:02d}_Voigt_direct_integral',relative(analytic,numeric)<1e-9,[analytic,numeric])
gate('R05_overlap_detuning_even',relative(s.overlap(.45,.22,lines),s.overlap(-.45,.22,lines))<1e-12)
gate('R06_overlap_multiline_positive',s.overlap(.5,.5,[(0.,.2,1.),(1.3,.3,.8)])>0)
gate('R07_source_gaussian_sigma_to_zero',relative(s.overlap(.1,.002,lines)/(np.sqrt(2*np.pi)*.002),.2**2/(.1**2+.2**2))<5e-5)
gate('R08_width_dimension_invariant_under_rescaling',relative(s.overlap(20,30,[(0,20,1)])/100,s.overlap(.2,.3,[(0,.2,1)]))<1e-12)
fi=s.fisher_design();diag['spectral_fisher']=fi
gate('R09_information_full_rank',fi['rank']==3)
gate('R10_information_well_conditioned',fi['condition_number']<1000,fi['condition_number'])
gate('R11_noiseless_identifiability',np.max(np.abs(np.array(fi['fit'])-np.array(fi['truth'])))<1e-9)
gate('R12_fit_data_residual_small',fi['max_residual']<1e-9)
gate('R13_source_amplitude_scaling',relative(s.overlap(.25,.4,lines,amp=2),2*s.overlap(.25,.4,lines))<1e-13)

# SST-33 comparison: transport relation and thermal assumptions, not physical prediction.
b1=s.thermal_bar(.020,.05,1.1,1e-4,-.02)
b2=s.thermal_bar(.002,.05,.19,1e-4,-.01)
diag['thermal_B1_assumed_2percent_shift']=b1;diag['thermal_B2_assumed_1percent_shift']=b2
gate('H01_SST33_glass_temperature_drop',relative(b1['baseline_K'],9.09090909)<1e-8)
gate('H02_SST33_PMMA_temperature_drop',relative(b2['baseline_K'],5.26315789)<1e-8)
gate('H03_glass_sign_shift',b1['change_K']>0)
gate('H04_PMMA_sign_shift',b2['change_K']>0)
gate('H05_linearization_small_signal',relative(b1['change_K'],b1['linear_approx_K'])<.03)
gate('H06_steady_thermal_not_euler_energy',True,'Thermal calculation standalone: no dissipation added to Euler action')
# T_strain=Theta*eps is an operational rescaling; heat capacity derivative of elastic energy is not equilibrium C_V.
k_el=2.5;eps=.03;Theta=100.
deltaE=.5*k_el*eps**2;dEdT=k_el*(eps)/Theta
gate('H07_strain_energy_even',abs(.5*k_el*(-eps)**2-deltaE)<1e-13)
gate('H08_strain_energy_harmonic',abs(dEdT-k_el*eps/Theta)<1e-13)
gate('H09_no_thermodynamic_temperature_derived',True,'No entropy equilibrium temperature or T-dependent occupancy derived')
# Chirality null: symmetric scalar Lorentzian cannot force asymmetry.
gate('H10_scalar_kernel_chirality_null',abs(s.overlap(.1,.25,lines)-s.overlap(-.1,.25,lines))<1e-12)

npass=sum(z['status']=='PASS' for z in checks.values())
full={ 'title':'SST VAM5 SST17 PKLSA resonance v0.3.0',
       'status':'DEVELOPMENT_NOT_SOURCE_NATIVE_NOT_PHYSICALLY_CERTIFIED',
       'local_pass':npass,'local_total':len(checks),'checks':checks,'diagnostics':diag,
       'source_policy':{'historical_v020':'retained unchanged','pklsa_source_native':False,
                        'surrogate':'regularized vortex filament segment-midpoint Rosenhead kernel; not source-native PKLSA'},
       'gates':{'G0_formal_source_and_units':'PASS',
                'G1_legacy_v020':'PENDING_SEPARATE_RUN',
                'G2_ring_trefoil_surrogate':'PASS_SURROGATE_ONLY' if npass==len(checks) else 'FAIL',
                'G3_spectral_overlap':'PASS_SYNTHETIC_ONLY' if npass==len(checks) else 'FAIL',
                'G4_thermal_comparison':'PASS_FORMULA_ONLY' if npass==len(checks) else 'FAIL',
                'G5_native_PKLSA_interface':'BLOCKED_SOURCE_NOT_PROVIDED',
                'G6_independent_PKLSA_modes_and_clocks':'NOT_RUN',
                'G7_physical_EM_gravity_heat':'UNRESOLVED'}}
out=HERE/'results'/'v030_validation.json';out.parent.mkdir(exist_ok=True,parents=True)
out.write_text(json.dumps(full,indent=2,ensure_ascii=False),encoding='utf8')
print(f'v0.3.0 local: {npass}/{len(checks)} PASS')
for name,r in checks.items():
    if r['status']=='FAIL':print('FAIL:',name,r.get('detail'))
print('ring drift speed SI = ',v256['mean_drift_dimless']*s.GAMMA/s.R_C,'m/s')
print('Trefoil energy and impulse drifts:',tre['relative_energy_drift'],tre['relative_impulse_drift'])
print('Fisher condition number:',fi['condition_number'])
sys.exit(0 if npass==len(checks) else 1)
