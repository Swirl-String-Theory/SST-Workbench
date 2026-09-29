from pathlib import Path
import json, math
from sst_vortex_shear.campaign import verify_seal
from sst_vortex_shear.reveal_constants import C, ALPHA, V_CIRCLEARROW, R_C, RHO_F

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'A049_Isotropic_Euler_Vortex_Shear_Modulus_Falsifier_v0.3.0-outputs'
BLIND=BASE/'BLIND'; OUT=BASE/'REVEALED'; OUT.mkdir(parents=True,exist_ok=True)
ok,errors=verify_seal(BLIND)
if not ok: raise SystemExit('Blind seal verification failed: '+'; '.join(errors))
py=json.loads((BLIND/'python_backend'/'blind_summary.json').read_text(encoding='utf-8'))
native_path=BLIND/'native_backend'/'blind_summary.json'; parity_path=BLIND/'backend_parity_summary.json'
native=json.loads(native_path.read_text(encoding='utf-8')) if native_path.exists() else None
parity=json.loads(parity_path.read_text(encoding='utf-8')) if parity_path.exists() else None
release_mode='FULL_PYTHON_NATIVE_QUALIFIED' if native is not None and parity is not None and parity.get('status')=='PASS' else 'PYTHON_REFERENCE_ONLY'

top=py['topological_filament_campaign']; mf=py['master_factor_wave_gate']
ratio=float(mf['measured_cT_over_reference_speed'])
cT=ratio*V_CIRCLEARROW
mu=RHO_F*cT*cT
target_cT=0.5*V_CIRCLEARROW
target_mu=RHO_F*target_cT*target_cT
master_target=4.0/ALPHA
c_over_cT=C/cT
master_rel=abs(c_over_cT-master_target)/master_target
Gamma=2.0*math.pi*R_C*V_CIRCLEARROW
# Blind a/R=0.18. Identifying a with r_c sets the dimensionless ring radius R to r_c/0.18.
core_over_R=0.18
R_phys=R_C/core_over_R
spacing_phys=top['static_linked']['spacing_over_R']*R_phys
required_spacing_phys=mf['required_spacing_over_R_for_target']*R_phys

revealed={
 'catalog_id':'A049','version':'v0.3.0','blind_seal_verified':True,'release_mode':release_mode,
 'blind_pipeline_status':py['pipeline_status'],'research_question_status':py['research_question_status'],
 'linking_specific_interpretation':py['linking_specific_interpretation'],'master_factor_wave_closure_status':mf['overall'],
 'canonical_constants':{'c_m_s':C,'alpha':ALPHA,'v_circlearrow_m_s':V_CIRCLEARROW,'r_c_m':R_C,'rho_f_kg_m3':RHO_F,'Gamma_m2_s':Gamma},
 'strict_scale_map':{
   'mapping':'blind core radius a -> r_c; blind v_ref=Gamma/(2*pi*a) -> v_circlearrow',
   'candidate_cT_over_v_circlearrow':ratio,'candidate_cT_m_s':cT,'candidate_mu_if_rho_eff_equals_rho_f_Pa':mu,
   'c_over_candidate_cT':c_over_cT,'target_4_over_alpha':master_target,'relative_master_factor_mismatch':master_rel,
   'target_cT_m_s':target_cT,'target_mu_Pa':target_mu,
   'ring_radius_m_under_a_equals_r_c':R_phys,'tested_dense_nonoverlap_spacing_m':spacing_phys,
   'required_spacing_m_for_target_by_density_scaling':required_spacing_phys
 },
 'topological_result':{
   'initial_linking_mean':top['initial_linking_mean'],'link_change_abs_max':top['link_change_abs_max'],
   'linked_mu_over_rho_blind':top['static_linked']['mu_over_rho_mean'],'unlinked_mu_over_rho_blind':top['static_unlinked']['mu_over_rho_mean'],
   'linking_excess_fraction':top['topological_linking_excess_fraction'],
   'modulus_persistence_ratio_min':top['modulus_persistence_ratio_min'],'shear_stress_persistence_ratio_min':top['shear_stress_persistence_ratio_min'],
   'stored_shear_energy_relative_drift_max':top['stored_shear_energy_relative_drift_max']
 },
 'interpretation':(
   'The explicit Hopf-linked regularized Biot-Savart microcells retain a positive conservative affine shear curvature and a persistent odd shear stress over the tested interval. '
   'However, an unlinked control has nearly the same modulus, so linking itself is not identified as the source. The Master-Factor speed ratio fails at the densest non-overlapping packing, and the density extrapolation would require overlapping cells. '
   'No independent bulk propagating transverse pole is established in v0.3.0, so Master-Factor Wave Closure remains NOT_CLOSED.'
 )
}
(OUT/'reveal_summary.json').write_text(json.dumps(revealed,indent=2),encoding='utf-8')
lines=[
 '# A049 v0.3.0 reveal report','', 'Blind seal: **VERIFIED**',f'Release mode: **{release_mode}**',
 f"Pipeline: **{py['pipeline_status']}**",f"Research question: **{py['research_question_status']}**",f"Linking-specific source: **{py['linking_specific_interpretation']}**",f"Master-Factor Wave Closure: **{mf['overall']}**",'',
 '## Strict canonical scale map','',f'- candidate c_T/v_circlearrow = {ratio:.12e}',f'- candidate c_T = {cT:.12e} m s^-1',f'- candidate mu = {mu:.12e} Pa (if rho_eff=rho_f)',f'- c/c_T = {c_over_cT:.12e}',f'- target 4/alpha = {master_target:.12e}',f'- relative Master-Factor mismatch = {master_rel:.12e}',f'- target c_T = {target_cT:.12e} m s^-1','',
 '## Geometry density check','',f'- a/R = {core_over_R:.6g}',f'- R = {R_phys:.12e} m when a=r_c',f'- densest tested non-overlap spacing = {spacing_phys:.12e} m',f'- target-by-density spacing = {required_spacing_phys:.12e} m',f"- MF03 = {mf['MF03_NONOVERLAP_GEOMETRY']}",'',
 '## Topological persistence','',f"- initial mean Lk = {top['initial_linking_mean']:.12e}",f"- max |Delta Lk| = {top['link_change_abs_max']:.12e}",f"- modulus persistence min = {top['modulus_persistence_ratio_min']:.12e}",f"- applied shear-stress persistence min = {top['shear_stress_persistence_ratio_min']:.12e}",f"- stored shear-energy drift max = {top['stored_shear_energy_relative_drift_max']:.12e}",f"- linked-vs-unlinked modulus excess = {top['topological_linking_excess_fraction']:.12e}",'',revealed['interpretation']]
(OUT/'reveal_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(revealed,indent=2))
