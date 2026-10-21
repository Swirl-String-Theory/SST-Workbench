#!/usr/bin/env python3
"""v0.1.1 math addendum to immutable v0.1.0 registry; no external packages."""
from __future__ import annotations
import csv, json, math, hashlib
from pathlib import Path
from math_models import *
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results'; RES.mkdir(exist_ok=True)
def write_json(name,obj):
    (RES/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_csv(name,items,cols):
    with (RES/name).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows(items)

claims=[]
def claim(id,source,location,original,repair,status,assumptions,units,gate):
    claims.append(dict(claim_id=id,source_id=source,source_locator=location,
       formula_or_statement_in_source=original,independent_analysis_or_repair=repair,
       status=status,scope_and_assumptions=assumptions,dimensions=units,
       test_or_gate=gate,review_version='0.1.1',interpretation_status='NO_PHYSICAL_PROMOTION'))

claim('A001','SRC-KELVIN-A','p. 2 eq. 1','omega=Gamma*k^2/(4*pi)*(ln(1/(|k|xi))+C0)',
      'same equation; require |k|xi << 1, straight-core limit','CONDITIONAL_VALID',
      'small-amplitude Kelvin waves, asymptotic straight filament','rad/s','K1_DISPERSION')
claim('A002','SRC-KELVIN-A','p. 2 eq. 2','k_m=2*pi*m/L','periodic wavenumber proxy; actual loop eigenmodes are geometry-dependent',
      'CONDITIONAL_VALID','arclength-periodic ansatz only','1/m','K2_GEOMETRY')
claim('A003','SRC-KELVIN-A','p. 8 Appendix A','Gamma=h/m_e','Gamma_canon=2*pi*r_c*v_swirl is different by 75,115x',
      'INCOMPATIBLE_INPUT_CONTRACT','two historical and present constant prescriptions cannot both be silently used','m^2/s','K3_INPUT_BLIND')
claim('A004','SRC-KELVIN-A','p. 8 eqs. 21-22','omega=2.8e17 rad/s; energy=29.5 eV',
      'hbar*omega/eV=184.30 eV; the two printed numbers disagree','NUMERICALLY_INCORRECT',
      'using conventional hbar and electronvolt','J = J*s * s^-1','K4_NUMERIC')
claim('A005','SRC-KELVIN-A','p. 3 text before eq. 6','Delta~Gamma^2/(4*pi*xi*L)',
      'units are m^2/s^2, NOT energy; requires independently defined effective mass scale',
      'DIMENSIONALLY_INVALID','Gamma circulation m^2/s; xi,L in m','m^2/s^2, not J','K5_DIMENSIONS')
claim('A006','SRC-KELVIN-A','p. 3 proposed tension','T_f~rho*Gamma^2/(4*pi*xi^2)',
      'dimensions are pressure N/m^2, not line tension N; standard straight filament energy/length depends on rho*Gamma^2*log',
      'DIMENSIONALLY_INVALID','rho mass density kg/m^3','Pa rather than N','K5_DIMENSIONS')
claim('A007','SRC-KELVIN-B','p. 4 proposed Delta_K','Topologically generated 100-1000 eV Kelvin gap',
      'no derivation from Euler spectrum; finite arclength mode spacing is not a proven topological gap',
      'UNVERIFIED_PHYSICAL_HYPOTHESIS','must remove global symmetry zero modes and specify coupling to thermal excitations',
      'eV is energy but magnitude unproved','K6_NATIVE_GAP')
claim('A008','SRC-KELVIN-B','p. 5 eqs. 11-14','Z=1/(1-e^-beta Delta); U=Delta/(e^(beta Delta)-1)',
      'correct thermal-excitation Bose oscillator; C=k_B x^2 exp(-x)/(1-exp(-x))^2, x=Delta/k_BT',
      'MATHEMATICALLY_VALID_CONDITIONAL','quantized harmonic oscillator, positive independent excitation energy, thermal equilibrium',
      'U[J], C[J/K]','K7_THERMAL')
claim('A009','SRC-KELVIN-B','p. 5 eq. 14','U_K <= N Delta exp(-Delta/k_BT)',
      'rigorous finite-mode bound: U_K<=N*Delta/(exp(Delta/k_BT)-1), with exponential expression asymptotic only',
      'CONDITIONAL_BOUND_REPAIRED','N modes each E_j >= Delta > 0, positive independent bosonic excitations',
      'J','K7_THERMAL')
claim('A010','SRC-KELVIN-B','p. 5-6 eqs. 16-18','Delta/k_BT>=60 gives Delta~500eV at 100000K',
      '60*k_B*100000K = 517.04 eV; threshold 60 and T_eff remain unverified external assumptions',
      'NUMERICALLY_VALID_CONDITIONAL','T_eff=100000K and dimensionless suppression ratio 60 separately imposed',
      'eV','K8_SPECTROSCOPY')
claim('A011','SRC-KELVIN-B','p. 5 eqs. 19-20','delta F/delta psi yields stationary Schrodinger equation',
      'mathematically correct if Schrodinger functional and normalization are inputs; no Euler->Schrodinger derivation',
      'VARIATIONAL_IDENTITY_ONLY','hbar,m_e,V imposed in functional','J','K9_EULER_DERIVATION')
claim('A012','SRC-KELVIN-A','pp. 2-7','U_K in a thermal bath for ideal inviscid Euler vortex',
      'closed inviscid Euler has no built-in heat bath, relaxation or thermal occupation; add independent statistical model',
      'MODEL_EXTENSION_REQUIRED','statistical equilibrium and mode quantization not derived from Euler','not applicable','K10_BATH')
claim('A013','SRC-DUAL','p. 3 eq. 3','D omega/Dt=(omega.dot grad)v',
      'valid under incompressible Euler; uniform acceleration alone need not stretch vortices',
      'ESTABLISHED_WITH_ASSUMPTIONS','smooth incompressible inviscid flow with conservative body forces','s^-2','D1_EULER_STRETCH')
claim('A014','SRC-DUAL','p. 3 eq. 8-9','kappa_se=4Zs/Zb','dimensionless impedance-inspired number, NOT transfer rate; direct use in ODE is invalid',
      'DIMENSIONLESS_PARAMETER_ONLY','requires boundary/interface law and compatible excitations','1','D2_RATE_UNITS')
claim('A015','SRC-DUAL','p. 4 eq. 11-13','dot nS=-(GammaS+gdiss+kappa_se)nS',
      'introduce independent g_SE [s^-1]; correct analytic two-pool solution and peak formula',
      'DIMENSIONALLY_INVALID_ORIGINAL','uncoupled positive decay rates, unidirectional transfer','s^-1','D2_RATE_UNITS')
claim('A016','SRC-DUAL','p. 4 purported echo','peak ~30ns from 0.1 ns precursor and 30ns photon lifetime',
      'for two-pool model with inverse lifetimes 0.1ns and 30ns: t_peak=0.572ns, not 30ns',
      'NOT_DERIVED_FROM_STATED_MODEL','peak formula assumes positive transfer and two constant decay rates','seconds','D3_PEAK')
claim('A017','SRC-DUAL','p. 3 eq. 10','Faraday: -G partial_t(curl v) n-hat',
      'vector-vector product undefined; B_eff=B+chi*curl(v) is a closed field-definition, not new EM dynamics',
      'ILL_DEFINED_OPERATOR','chi must have Tesla*seconds; curl v is 1/s','T/s in Faraday equation','D4_TENSOR')
claim('A018','SRC-DUAL','p. 3-4 eqs. 7-13','hydrodynamic and EM energy transduction',
      'two-Hamiltonian-oscillator conservative benchmark is mathematically distinct from irreversible rate model',
      'INDEPENDENT_MATHEMATICAL_BASELINE','positive masses, stiffnesses and coupling; not derived from vortex dynamics','J','D5_HAMILTONIAN')
claim('A019','SRC-DUAL','p. 2 eq. 2 and p. 3 eq. 7','eta=c/vs; tauS=tauEM/eta',
      'ratio arithmetic holds but no independent derivation of either propagation or rate scaling',
      'SCALING_ANSATZ','tangential swirl speed is not a signal propagation speed','dimensionless','D6_DELAY')
claim('A020','SRC-DUAL','p. 3-4 discussion','vacuum Unruh echo already detected',
      'paper cites theoretical Unruh-superradiance studies, not measurement of a 30ns swirl photon echo',
      'UNVERIFIED_EMPIRICAL_PREMISE','experimental proof not supplied in source','not applicable','D7_REAL_DATA')
claim('A021','SRC-DUAL','new mathematical baseline, not in paper','coupled positive-energy 2-DOF oscillator',
      'L=1/2 ms qs_dot^2+1/2 me qe_dot^2-1/2 ks qs^2-1/2 ke qe^2-1/2 g(qs-qe)^2',
      'INDEPENDENT_MATHEMATICAL_CONSTRUCTION','positive masses, stiffnesses, g>=0; explicitly not Euler/EM proven','J','D5_HAMILTONIAN')
claim('A022','SRC-DUAL','independent repaired model','rate dynamics for energy with E_loss',
      'dEs/dt=-(ds+g)Es; dEe/dt=eta*g*Es-de*Ee; dEloss/dt=ds*Es+(1-eta)*g*Es+de*Ee',
      'INDEPENDENT_MATHEMATICAL_CONSTRUCTION','0<=eta<=1; nonnegative rates, irreversible effective model','J/s','D8_ENERGY_BALANCE')

write_json('mathematical_addendum.json',claims)
write_csv('mathematical_addendum.csv',claims,list(claims[0]))

numeric={
 'label':'MATHEMATICAL_TESTS_ONLY_NOT_PKLSA_MEASUREMENTS',
 'kelvin_gamma_canon_m2_s':gamma_sst(),
 'kelvin_gamma_h_over_me_m2_s':gamma_h_over_me(),
 'kelvin_circulation_ratio':gamma_h_over_me()/gamma_sst(),
 'quoted_omega_energy_eV':HBAR*2.8e17/E_CHARGE,
 'gap_threshold_ratio_60_at_1e5K_eV':gap_threshold_eV(1e5),
 'first_mode_frequency_proxy_gamma_canon_rad_s':kelvin_omega(gamma_sst(),2*math.pi*A0,R_C,1),
 'first_mode_proxy_energy_eV':HBAR*kelvin_omega(gamma_sst(),2*math.pi*A0,R_C,1)/E_CHARGE,
 'mode_index_caveat':'m=1 straight-filament proxy NOT actual ring eigenmode; mode symmetries must be removed from real spectrum',
 'impedance_z_s_Rayl':RHO_F*V_SWIRL,
 'impedance_ratio_for_z_bound_1e7':electric_like_impedance_ratio(RHO_F*V_SWIRL,1e7),
 'peak_two_lifetimes_0p1ns_30ns_ns':transfer_peak_s(1/(.1e-9),1/(30e-9))*1e9,
 'unverified_claims':['topological kelvin gap >0','spectroscopic coefficient 1e-62 J/K2','distinct two-vacuum EM medium','30ns Unruh echo','light-wave speed from Euler'],
 'native_pklsa':'NOT_CONNECTED'
}
write_json('independent_numeric_checks.json',numeric)
rows=[]
for name,gam in (('SST_CANON_DEFINITION',gamma_sst()),('H_OVER_ME_HISTORICAL_INPUT',gamma_h_over_me())):
  for r in kelvin_spectrum(gam,2*math.pi*A0,R_C,max_mode=10):
    rows.append({'circulation_contract':name,'gamma_m2_per_s':gam,'loop_length_m':2*math.pi*A0,
       'core_length_m':R_C,**r,'spectrum_origin':'STRAIGHT_FILAMENT_PERIODIC_PROXY_NOT_PKLSA'})
write_csv('kelvin_periodic_proxy.csv',rows,list(rows[0]))
grid=[]
for gap_eV in (0.001, 0.01, 1.0, 100.0, 500.0):
  for TK in (1.0,300.0,1e5,1e7):
    E=gap_eV*E_CHARGE
    grid.append({'gap_eV':gap_eV,'T_K':TK,'x':E/(KB*TK),'U_J':boson_thermal_energy_J(E,TK),
                 'C_J_per_K':boson_heat_capacity_J_per_K(E,TK),'status':'ASSUMED_GAP_QUANTIZED_OSCILLATOR'})
write_csv('conditional_thermal_grid.csv',grid,list(grid[0]))
examples=[]
for t_ns in (0,0.1,0.25,0.572,1,5,30,60):
   out=transfer_state(t_ns*1e-9,1.0,g_per_s=1e9,d_s_per_s=9e9,d_e_per_s=1/(30e-9),efficiency=0.6)
   examples.append({'t_ns':t_ns,**out,'total_J':sum(out.values()),'model':'IRREVERSIBLE_ENERGY_RATE_MATH'})
write_csv('two_sector_energy_rate_example.csv',examples,list(examples[0]))
ms,me,ks,ke,g=2.0,1.5,80.0,45.0,5.0
traj=oscillator_velocity_verlet(.1,0.,0.,0.,ms,me,ks,ke,g,dt=0.0005,steps=10000)
write_csv('conservative_oscillator_energy_trace.csv',
    [{'t_s':t,'energy_J':E,'fractional_drift':(E/traj[0][1]-1),'interpretation':'HAMILTONIAN_2DOF_TOY_ONLY'} for t,E in traj],
    ['t_s','energy_J','fractional_drift','interpretation'])
numeric['conservative_frequencies_rad_s']=list(matrix_eigenfrequencies(ms,me,ks,ke,g))
numeric['max_conservative_energy_drift']=max(abs(E/traj[0][1]-1) for _,E in traj)
write_json('independent_numeric_checks.json',numeric)
write_json('addendum_qualification.json',{'version':'0.1.1','parent_version':'0.1.0',
    'release_status':'DEVELOPMENT_NOT_PHYSICALLY_CERTIFIED',
    'original_curated_claims_unchanged':41,'original_summary_raw_formulas_unchanged':379,
    'additional_audit_entries':len(claims),'new_native_provider':'NOT_CONNECTED',
    'math_modules':['kelvin asymptotic proxy','conditional Bose thermal oscillator',
                    'repaired irreversible two-sector energy rates','Hamiltonian two-oscillator conservative baseline'],
    'scopes_not_proven':['electron hypothesis','Kelvin topological gap size','thermal spectroscopy bound',
                         'PKLSA eigenspectra','photon torsion','two-vacuum constitutive law','Unruh echo']})
print(json.dumps({'additional_entries':len(claims),'peak_ns':numeric['peak_two_lifetimes_0p1ns_30ns_ns']},indent=2))
