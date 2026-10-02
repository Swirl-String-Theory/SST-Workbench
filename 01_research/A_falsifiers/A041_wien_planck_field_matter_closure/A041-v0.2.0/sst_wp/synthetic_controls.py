from __future__ import annotations
import argparse,math,random
from .common import write_csv

def action(path,kind):
 rng=random.Random(12);rows=[]
 for carrier in range(4):
  epsRE=.02+.001*carrier; L=3e-14*(1+.05*carrier)
  for N in [64,96,128]:
   for amp in [.002,.003,.004,.006]:
    f=1.2e20*(1+.1*carrier)*(1+0.0003*(128-N))
    if kind=='positive': dE=6.62607015e-34*f*(1+rng.gauss(0,.004))
    elif kind=='classical': dE=3e-14*amp**2*(1+rng.gauss(0,.005))
    else: dE=6.62607015e-34*f*(1+rng.gauss(0,.2))
    rows.append({'case_index':carrier,'source_name':f'carrier{carrier}','source_path':'synthetic','family_hint':'synthetic','resolution_N':N,'amplitude':amp,'delta_E_J':dE,'base_energy_J':1e-12,'delta_E_over_abs_base':dE/1e-12,'energy_signal_valid':True,'frequency_Hz':f,'omega_rad_s':2*math.pi*f,'frequency_dimless':1,'spectral_power':.85,'cycles':8,'period_cv':.03,'harmonic_r2':.95,'pod_discovery_fraction':.8,'epsilon_RE':epsRE,'mesh_cv_plus':.03,'mesh_cv_minus':.03,'dt':1e-5,'n_steps':1000,'L_phys_m':L,'Gamma_phys_m2_s':1e-8,'rho_energy_kg_m3':7e-7,'temporal_frequency_rel_change':0.002})
 write_csv(path,rows)

def closure(path,good=True):
 rng=random.Random(3);rows=[]
 for i in range(20):
  a=.8+.03*i; w=2e6/a**2*(1+rng.gauss(0,.005 if good else .15));MI=9e-31*(1+.01*i);ME=MI*(1+rng.gauss(0,.01 if good else .12));Cp=2e15*MI*(1+rng.gauss(0,.01 if good else .2));bk=1e33*(1+rng.gauss(0,.01));bf=bk*(1+rng.gauss(0,.01 if good else .15));dr=rng.gauss(0,2e-7 if good else 1e-4);rows.append({'scale_a':a,'omega_rad_s':w,'M_E_kg':ME,'M_I_kg':MI,'C_p':Cp,'beta_knot':bk,'beta_fluid':bf,'energy_drift_rel':dr})
 write_csv(path,rows)

def main():
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['action-positive','action-classical','action-noisy','closure-positive','closure-negative']);p.add_argument('out');a=p.parse_args();
 if a.kind.startswith('action-'):action(a.out,a.kind.split('-',1)[1])
 else: closure(a.out,a.kind.endswith('positive'))
if __name__=='__main__':main()
