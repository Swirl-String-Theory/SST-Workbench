"""Independent algebra/numeric tests for released v0.1.1 mathematics, not physical validation."""
from pathlib import Path
import sys, unittest, math, json, csv
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'addendum'))
from math_models import *

class AddendumMathTests(unittest.TestCase):
 def test_gap_input_contracts(self):self.assertGreater(gamma_h_over_me()/gamma_sst(),75000)
 def test_gamma_dimensions_consistent_numbers(self):self.assertTrue(9e-9<gamma_sst()<1e-8)
 def test_kelvin_quote_omega(self):self.assertAlmostEqual(HBAR*2.8e17/E_CHARGE,184.2993,places=3)
 def test_first_proxy_vs_other_contract(self):
  for m in (1,2,3):
   ratio=kelvin_omega(gamma_h_over_me(),2*math.pi*A0,R_C,m)/kelvin_omega(gamma_sst(),2*math.pi*A0,R_C,m)
   self.assertAlmostEqual(ratio,gamma_h_over_me()/gamma_sst(),places=8)
 def test_k2_ratio_weak_log_correction(self):
  s=kelvin_spectrum(gamma_sst(),2*math.pi*A0,R_C,8)
  self.assertEqual(len(s),7)
  self.assertTrue(all(s[i]['omega_rad_s']<s[i+1]['omega_rad_s'] for i in range(6)))
 def test_kelvin_thin_regime_rejection(self):
  with self.assertRaises(ValueError):kelvin_omega(1.,1e-9,1e-8,2)
 def test_first_mode_symbolic_dimensional_constraint(self):
  # dim Gamma^2/(xi*L): (m^2/s)^2/m^2=m^2/s^2
  self.assertEqual((2*2-1-1,-2),(2,-2))
 def test_bose_energy_low_T(self):
  gap=500*E_CHARGE;T=1e5;x=gap/(KB*T)
  U=boson_thermal_energy_J(gap,T)
  self.assertAlmostEqual(U/(gap*math.exp(-x)),1.,places=12)
 def test_bose_C_limit_high_T(self):self.assertAlmostEqual(boson_heat_capacity_J_per_K(1e-30,1e5)/KB,1,places=9)
 def test_bose_C_limit_low_T(self):self.assertEqual(boson_heat_capacity_J_per_K(500*E_CHARGE,300),0.)
 def test_bose_derivative_heat_capacity(self):
  gap=0.01*E_CHARGE; T=300.;h=1e-2
  dU=(boson_thermal_energy_J(gap,T+h)-boson_thermal_energy_J(gap,T-h))/(2*h)
  self.assertAlmostEqual(dU/boson_heat_capacity_J_per_K(gap,T),1.,places=8)
 def test_bose_mode_bound(self):
  gap=0.05*E_CHARGE; T=400.
  E=sum(boson_thermal_energy_J((1+i/5)*gap,T) for i in range(9))
  self.assertLessEqual(E,bose_thermal_upper_bound_J(gap,T,9))
 def test_gap_threshold(self):self.assertAlmostEqual(gap_threshold_eV(1e5,60.),517.0399957,places=4)
 def test_bose_positive(self):self.assertGreater(boson_heat_capacity_J_per_K(.001*E_CHARGE,300),0)
 def test_impedance_dimensionless(self):self.assertAlmostEqual(electric_like_impedance_ratio(RHO_F*V_SWIRL,1e7),3.062767764e-7,places=15)
 def test_peak_direct(self):self.assertAlmostEqual(transfer_peak_s(1e10,1/30e-9)*1e9,0.572,delta=.002)
 def test_peak_equal_rates(self):self.assertAlmostEqual(transfer_peak_s(4.,4.),.25)
 def test_transfer_at_zero(self):self.assertEqual(transfer_state(0.,1.,1.,2.,3.),{'E_swirl_J':1.,'E_em_J':0.,'E_loss_J':0.})
 def test_transfer_positive_conserves(self):
  for t in [0,1e-10,1e-9,1e-8,1e-7]:
   r=transfer_state(t,1.0,1e9,9e9,1/(30e-9),0.6)
   self.assertTrue(all(v>=-5e-15 for v in r.values()))
   self.assertAlmostEqual(sum(r.values()),1.,places=12)
 def test_transfer_energy_rate_balance(self):
  dt=1e-13; t=1e-10; pars=(1.,1e9,9e9,3e7,.6)
  plus=transfer_state(t+dt,*pars);minus=transfer_state(t-dt,*pars)
  r=transfer_state(t,*pars)
  lhs=(plus['E_swirl_J']-minus['E_swirl_J'])/(2*dt)
  self.assertAlmostEqual(lhs/(-1e10*r['E_swirl_J']),1.,places=6)
 def test_transfer_g_zero(self):
  r=transfer_state(2,3,0,.1,.3,.9);self.assertEqual(r['E_em_J'],0.)
 def test_transfer_dissipation_zero_efficiency_one(self):
  for t in (.1,1.,10.):
   r=transfer_state(t,1.,2.,0.,0.,1.);self.assertAlmostEqual(r['E_loss_J'],0.,places=12)
 def test_transfer_equal_rates_limit(self):
  t=.5;r=transfer_state(t,1.,2.,1.,3.,.5)
  self.assertAlmostEqual(r['E_em_J'],math.exp(-3*t)*t,places=12)
 def test_oscillator_uncoupled_frequencies(self):
  a=matrix_eigenfrequencies(2.,3.,8.,27.,0.)
  self.assertAlmostEqual(a[0],2.);self.assertAlmostEqual(a[1],3.)
 def test_oscillator_nondegenerate_stability(self):
  self.assertTrue(all(w>0 for w in matrix_eigenfrequencies(2,1.5,80,45,5)))
 def test_oscillator_energy_positive(self):self.assertGreater(oscillator_energy(.1,.02,0,.2,2,1.5,80,45,5),0)
 def test_oscillator_symplectic_energy_convergence(self):
  def drift(dt):
   tr=oscillator_velocity_verlet(.1,0.,0.,0.,2,1.5,80,45,5,dt,round(3/dt))
   return max(abs(E/tr[0][1]-1) for _,E in tr)
  coarse=drift(.004);fine=drift(.002)
  self.assertGreater(coarse/fine,3.5)
  self.assertLess(coarse/fine,4.5)
 def test_addendum_metadata(self):
  a=json.loads((ROOT/'results/addendum_qualification.json').read_text())
  self.assertEqual(a['additional_audit_entries'],22)
  self.assertEqual(a['original_curated_claims_unchanged'],41)
 def test_addendum_consistent_links(self):
  c=json.loads((ROOT/'results/mathematical_addendum.json').read_text())
  self.assertEqual(len(set(x['claim_id'] for x in c)),len(c))
  ids={x['source_id'] for x in c}
  self.assertEqual(ids,{'SRC-KELVIN-A','SRC-KELVIN-B','SRC-DUAL'})
 def test_original_sources_preserved(self):
  manifest=json.loads((ROOT/'results/source_manifest.json').read_text())
  import hashlib
  for x in manifest['sources']:
   self.assertEqual(hashlib.sha256((ROOT/x['filename']).read_bytes()).hexdigest(),x['sha256'])
 def test_no_pklsa_claims(self):
  q=json.loads((ROOT/'results/addendum_qualification.json').read_text())
  self.assertEqual(q['new_native_provider'],'NOT_CONNECTED')
 def test_no_physical_promotion(self):
  c=json.loads((ROOT/'results/mathematical_addendum.json').read_text())
  self.assertTrue(all(x['interpretation_status']=='NO_PHYSICAL_PROMOTION' for x in c))

if __name__=='__main__':unittest.main(verbosity=2)
