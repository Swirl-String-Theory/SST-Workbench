import numpy as np
from a054_state.analysis import provider_convergence

def row(provider,e0,e1,stat=True):
 return {'topology_id':'3_1','provider_group':provider,'initial_energy':e0,'final_energy':e1,'stationary':stat,'stable_candidate':True,'ringdown_bounded':True,'final_descriptors':{'ropelength_proxy':10.0,'writhe_sum':1.0},'_components_for_analysis':[]}
def test_provider_converges():
 cfg={'provider_energy_cv_max':0.05,'provider_ropelength_rel_span_max':0.1,'provider_writhe_abs_span_max':0.25}
 d=provider_convergence([row('A',100,80),row('B',120,81)],cfg)['3_1'];assert d['eligible'];assert d['provider_converged']
