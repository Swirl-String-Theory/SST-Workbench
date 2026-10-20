"""A070 preliminary falsifier pilot: exact affine Euler flow + operational clocks/rods + SN opacity.
No physical PKLSA vortex data, photon dynamics, or observational raw data is used.
"""
from __future__ import annotations
import json, math, hashlib, csv
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parents[1]
C=299792458.0; GYR=365.25*86400*1e9
H0=70*1000/(1e6*3.085677581491367e16) # s^-1
SIGMA=0.12  # dimensionless s*T
ST=SIGMA/GYR
RHO=7e-7
RCORE=1.40897017e-15
VSWIRL=1.09384563e6
OMEGA0=VSWIRL/RCORE # convention: core angular velocity, not vorticity (factor 2)

# exact u=A(t)x; div A=0, Omega' = s Omega; Euler gradient pressure known.
def A(t):
    w=OMEGA0*math.exp(ST*t)
    return np.array([[-ST/2, -w, 0],[w, -ST/2,0],[0,0,ST]],float)
def analytic_acceleration_matrix(t):
    w=OMEGA0*math.exp(ST*t)
    return np.diag([ST**2/4-w*w,ST**2/4-w*w,ST**2])
def f(t): return math.exp(ST*t)
def tau(t): return math.expm1(ST*t)/ST

def eds_E(z): return (1+z)**1.5
def lcdm_E(z): return math.sqrt(0.3*(1+z)**3+0.7)
def DL(z, model):
    e=eds_E if model=='EdS' else lcdm_E
    return (1+z)*C/H0*quad(lambda q: 1/e(q),0,z,epsabs=1e-11,epsrel=1e-12)[0]
def target_tau(z):return 2*math.log(DL(z,'LCDM')/DL(z,'EdS'))
def mag_from_tau(tau):return (2.5/math.log(10))*tau  # since Δm=5 log10(exp(tau/2))

def run():
    out=HERE/'results'; out.mkdir(exist_ok=True)
    logs={}
    # REGRESSION E0 exact divergence and Euler pressure compatibility
    values=[]
    for t in [0,GYR/2,GYR]:
        w=OMEGA0*f(t)
        At=A(t)
        Aprime=np.array([[0,-ST*w,0],[ST*w,0,0],[0,0,0]],float)
        acc=Aprime+At@At
        exact=analytic_acceleration_matrix(t)
        # scale-normalized residual; important: omega very large and tiny s cancellation uses no mixed precision convention
        resid=np.linalg.norm(acc-exact)/np.linalg.norm(exact)
        values.append(resid)
        assert np.trace(At)==0
        assert resid<1e-13
        assert math.isclose(2*ST*w, ST*(2*w),rel_tol=1e-15)
    logs['G0_exact_affine_euler']={'status':'PASS_REFERENCE','max_pressure_accel_matrix_rel_residual':max(values),'divergence_s_inv':0.0,'flow_domain':'local affine unbounded not finite energy','clock_rate_f_at_T':f(GYR)}
    # REGRESSION E1 exact clock and rod, absolute Euclidean distance held fixed
    ts=np.linspace(0,GYR,201)
    ul=np.exp(ST*ts)
    l_fixed=ul.copy() # radar = D_abs*f (D_abs=1)
    tau_dimless=np.expm1(ST*ts)/SIGMA # tau/GYR
    # exact radar=(1+SIGMA tau/GYR); finite diff discrete second derivative
    d2=np.gradient(np.gradient(l_fixed,tau_dimless,edge_order=2),tau_dimless,edge_order=2)
    logs['G1_clock_only_fixed_absolute_distance']={'status':'NULL_RETAINED','acceleration_d2_Dper_tau_over_Gyr2_exact':0.0,'numeric_max_abs_accel_scaled':float(np.max(abs(d2[4:-4]))),'summary':'exponential stretch-driven swirl clock does NOT create accelerating radar distance at fixed absolute separation'}
    assert np.max(abs(d2[4:-4]))<5e-7
    # G2 rod from core radius a/a0 = exp(-s t/2) and f=exp(s t) => c_local/c=e^(-s t/2)
    rod=np.exp(-ST*ts/2)
    c_local_over_c=1/(ul*rod)
    disagreement_radrod=ul/(1/rod)
    logs['G2_clock_rod_light_closure']={'status':'FAIL_MODEL_CLOSURE','c_local_over_c_at_T':float(c_local_over_c[-1]),'radar_rod_disagreement_at_T':float(disagreement_radrod[-1]),'required_rod_scale_for_constant_c_at_T':float(1/ul[-1]),'derived_core_scale_at_T':float(rod[-1]),'qualification':'assuming constant signal speed in absolute coordinates and rod length equals vortex core radius'}
    # G3 anisotropy: separations of comoving tracers in z and transverse x
    D_z=ul.copy(); D_x=ul**(-0.5)
    D_radar_z=ul*D_z;D_radar_x=ul*D_x
    # analytic derivatives w.r.t local clock tloc/GYR at t=0 and t=T
    acc_z=2*SIGMA**2
    acc_x0=-SIGMA**2/4
    logs['G3_angular_anisotropy']={'status':'FAIL_ISOTROPIC_EXPANSION','absolute_z_separation_ratio_at_T':float(D_z[-1]),'absolute_x_separation_ratio_at_T':float(D_x[-1]),'radar_z_at_T':float(D_radar_z[-1]),'radar_x_at_T':float(D_radar_x[-1]),'local_clock_accel_z_at_t0_per_Gyr2':acc_z,'local_clock_accel_x_at_t0_per_Gyr2':acc_x0,'3d_volume_ratio':float(D_z[-1]*D_x[-1]**2)}
    assert abs(D_z[-1]*D_x[-1]**2-1)<1e-12
    # G4 prescribed optical opacity: reproduce LCDM from EdS: tautology, no prediction
    zgrid=np.array([0.1,0.2,0.35,0.5,0.8,1,1.5,2.0])
    true=np.array([target_tau(float(z)) for z in zgrid])
    pred_tau=true.copy()
    exact_resid=np.max(abs(pred_tau-true))
    logs['G4_constructed_opacity_degeneracy']={'status':'PASS_IDENTITY_ONLY','max_abs_tau_reconstruction':float(exact_resid),'tau_at_z1':target_tau(1),'eta_at_z1':math.exp(target_tau(1)/2),'fractional_flux_suppression_z1':float(1-math.exp(-target_tau(1))),'qualification':'constructed from LCDM target, not physical or predictive'}
    # G5 1-param optical depth tau=a z fit only on synthetic training at z<=0.5; holdout >0.5
    tr=zgrid<=0.5; hold=zgrid>0.5
    alpha=float(np.sum(zgrid[tr]*true[tr])/np.sum(zgrid[tr]**2))
    extrap=alpha*zgrid
    residual_mags=np.array([mag_from_tau(v) for v in extrap-true])
    hold_rms=float(np.sqrt(np.mean(residual_mags[hold]**2)))
    prereg_tolerance_mag=0.02
    logs['G5_one_parameter_opacity_holdout']={'status':'FAIL_SYNTHETIC_HOLDOUT' if hold_rms>prereg_tolerance_mag else 'PASS_SYNTHETIC_HOLDOUT','fit_alpha':alpha,'test_rms_residual_mag':hold_rms,'predefined_tolerance_mag':prereg_tolerance_mag,'dataset':'synthetic LCDM distances; physical observational validation NOT performed','n_train':int(tr.sum()),'n_holdout':int(hold.sum())}
    # G6 conceptual reproducibility status; no physical PKLSA, no calibrated source-native light law
    logs['G6_physical_provider']={'status':'UNRESOLVED','missing':['source-native finite-core PKLSA geometry and dynamics','independent photon transport law','operational rod construction independent of clocks','full BAO/SNe/CMB measured likelihoods','framework-v1.0.7 generated/certified instance','source independence']}
    # Write full data (no hidden labels; this is synthetic pilot NOT blind scientific test)
    with (out/'clock_distance.csv').open('w',newline='') as fp:
        writer=csv.writer(fp);writer.writerow(['absolute_t_Gyr','local_tau_Gyr','clock_ratio_f','rod_radius_ratio','fixed_absolute_distance','fixed_radar_distance','fixed_rod_count_distance','local_speed_c_over_c','z_material_distance','x_material_distance','z_radar_distance','x_radar_distance'])
        for i,t in enumerate(ts):writer.writerow([t/GYR,tau_dimless[i],ul[i],rod[i],1,l_fixed[i],1/rod[i],c_local_over_c[i],D_z[i],D_x[i],D_radar_z[i],D_radar_x[i]])
    with (out/'optical_distance.csv').open('w',newline='') as fp:
        w=csv.writer(fp);w.writerow(['redshift','D_L_EdS_Mpc','D_L_LCDM_Mpc','required_tau_constructed','eta_distance_duality','flux_suppression','tau_linear_training_fit','mag_residual_1par'])
        for z,t,guess,res in zip(zgrid,true,extrap,residual_mags):w.writerow([z,DL(z,'EdS')/3.085677581491367e22,DL(z,'LCDM')/3.085677581491367e22,t,math.exp(t/2),1-math.exp(-t),guess,res])
    (out/'metrics.json').write_text(json.dumps({'pilot_version':'v0.1.0','dataset_evidence_class':'synthetic_control','date_utc':'2026-10-18','framework_certification':'NOT_RUN','physical_claims':'UNRESOLVED','parameters':{'rho_f_kg_m3':RHO,'r_c_m':RCORE,'v_swirl_m_s':VSWIRL,'omega_core_rad_s':OMEGA0,'strain_s_inv':ST,'strain_T':SIGMA,'T_s':GYR,'signal_speed_assumed_m_s':C,'H0_km_s_Mpc':70,'LCDM_omega_m':0.3,'EdS_omega_m':1.0},'gates':logs},indent=2)+'\n')
    print(json.dumps({k:v['status'] for k,v in logs.items()},indent=2)); print('holdout RMS mag',hold_rms)
    return logs
if __name__=='__main__':run()
