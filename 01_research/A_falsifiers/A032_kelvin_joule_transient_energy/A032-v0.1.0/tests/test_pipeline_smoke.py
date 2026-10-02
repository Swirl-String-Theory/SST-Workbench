import json
from pathlib import Path
import numpy as np
from kj_sst.blind import prepare
from kj_sst.campaign import run_campaign,unblind

def test_tiny_pipeline_python(tmp_path):
 d=tmp_path/'data';d.mkdir();t=np.linspace(0,2*np.pi,96,endpoint=False);p=np.c_[(3+np.cos(3*t))*np.cos(2*t),(3+np.cos(3*t))*np.sin(2*t),np.sin(3*t)];np.savetxt(d/'knot.txt',p)
 cfg={
  'resolutions':[32], 'perturbations':[{'kind':'normal','mode':2,'amplitude_rc':0.01},{'kind':'normal','mode':2,'amplitude_rc':-0.01}],
  'exclude_fraction':0.08,'cfl':0.2,'dt_tau':0.01,'t_end_tau':0.04,'max_steps':20,'sample_stride':1,
  'energy_tol_rel':0.2,'impulse_tol_rel':0.2,'kelvin_window_tol_rel':1.0,'run_constriction_release':False,'constriction_streamtube_depth':0.5,
  'omega_sign_tol_rel':1.0,'resolution_convergence_tol_rel':1.0}
 out=tmp_path/'out';prepare(d,out,cfg);rows=run_campaign(out,'python',False);s=unblind(out);assert rows;assert s['n_samples']==1;assert (out/'results_unblinded.csv').exists()
