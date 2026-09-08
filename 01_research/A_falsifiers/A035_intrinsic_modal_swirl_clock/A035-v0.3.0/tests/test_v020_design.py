import json
from pathlib import Path
import numpy as np
from sst_modal_clock.geometry import resample_closed,tangential_redistribution_velocity
from sst_modal_clock.simulate import integration_plan
ROOT=Path(__file__).resolve().parents[1]
def cfg(n): return json.loads((ROOT/'config'/n).read_text())

def test_absolute_discovery_window_not_fractional():
 for name in ('basic.json','extended.json','focus_6p3.json'):
  c=cfg(name); assert c['discovery_time']==1.2; assert 'discovery_fraction' not in c

def test_stage_a_horizons_and_cycles():
 assert cfg('basic.json')['stage_a_t_final']>=24
 assert cfg('extended.json')['stage_a_t_final']>=36
 assert cfg('basic.json')['gate_min_cycles']>=4
 assert cfg('extended.json')['gate_min_cycles']>=6

def test_resolution_same_stage_a_horizon():
 assert [cfg(f'resolution_N{n}.json')['stage_a_t_final'] for n in (64,96,128)]==[24.0]*3

def test_dt_scaling_cap_still_hard():
 th=np.linspace(0,2*np.pi,64,endpoint=False); x=np.c_[np.cos(th),np.sin(th),np.zeros_like(th)]
 c={'gamma_dimensionless':1,'dt_factor':.01,'stage_a_t_final':10,'max_steps':10,'max_samples':100}
 try: integration_plan(x,c,'stage_a_t_final')
 except RuntimeError as e: assert 'refusing to enlarge dt' in str(e)
 else: raise AssertionError('expected hard step-cap failure')

def test_redistribution_reduces_parameter_error_directionally():
 th=np.linspace(0,2*np.pi,64,endpoint=False); ph=th+.35*np.sin(th); x=np.c_[np.cos(ph),np.sin(ph),np.zeros_like(ph)]
 def cv(z):
  ds=np.linalg.norm(np.roll(z,-1,axis=0)-z,axis=1); return ds.std()/ds.mean()
 c0=cv(x)
 for _ in range(100): x=x+.01*tangential_redistribution_velocity(x,4.0)
 assert cv(x)<c0
