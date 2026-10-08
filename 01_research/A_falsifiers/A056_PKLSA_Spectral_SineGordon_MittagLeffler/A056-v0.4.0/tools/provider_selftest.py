from pathlib import Path
import json,sys,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from a056_provider.geometry import canonicalize
from a056_provider.evolution import paired_observables
u=np.linspace(0,2*np.pi,96,endpoint=False); P=np.column_stack([(2+.55*np.cos(3*u))*np.cos(2*u),(2+.55*np.cos(3*u))*np.sin(2*u),.55*np.sin(3*u)]); P,_=canonicalize(P,96,1.0)
solver={'kind':'filament_bs','dt':.01,'T':.60,'core':.08,'sample_every':1,'max_segment_ratio':6.0}; pert={'id':'selftest_kelvin_m4_eps003','epsilon':.03,'mode':4,'min_phase_valid_fraction':.90,'amplitude_floor_fraction':.02}; o=paired_observables(P,solver,pert)
assert o['phi'].shape==(len(o['t']),len(o['s'])) and len(o['t'])>=48 and np.isfinite(o['phi']).all() and np.isfinite(o['ringdown']).all() and abs(o['ringdown'][0]-1)<1e-12
print(json.dumps({'status':'PASS','nt':len(o['t']),'ns':len(o['s']),'provider_valid':o['diagnostics']['provider_numerically_valid'],'phase_valid_fraction':o['diagnostics']['phase']['phase_valid_fraction'],'ringdown_min':float(o['ringdown'].min()),'ringdown_max':float(o['ringdown'].max())},indent=2))
