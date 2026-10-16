import math,json
from pathlib import Path
import numpy as np
from a061.science import sst28_ratio,sst28_omega_scaled,plateau_s,crystal_reconstruction,monte_carlo_search,max_sinusoid_periodogram
from framework_bootstrap import load_framework,resolve_framework_root
ROOT=Path(__file__).resolve().parents[1]
def test_framework_pin():
    fw=load_framework();assert fw.name=='SST_Falsifier_Framework_v1.0.7'
    from sst_falsifier import __version__
    assert __version__=='1.0.7'
def test_profile():assert abs(float(sst28_ratio(1))-math.sqrt(1-math.exp(-2)))<1e-13
def test_vorticity_zero():assert float(sst28_omega_scaled(2))==0 and float(sst28_ratio(2))<1
def test_plateau_printed_disagreement():assert float(plateau_s([1])[0])==0 and abs(float(plateau_s([1])[0])-.9603)>.5
def test_crystal_shift():
    a=json.loads((ROOT/'data/published/measurements.json').read_text());d=crystal_reconstruction(a);assert abs(d['offset_Hz']-558)<2
def test_periodogram_known_signal():
    t=np.linspace(0,2000,512);f=np.linspace(.002,.004,100);p=max_sinusoid_periodogram(t,np.sin(2*np.pi*.003*t),f);assert abs(f[int(np.argmax(p))]-.003)<.00004
def test_bootstrap_null():
    rng=np.random.default_rng(9);t=np.arange(120.)*11.8;y=rng.normal(size=120)
    z=monte_carlo_search(t,y,n_mc=8,n_freq=32);assert 0<=z['max_power']<=1
def test_scientific_gate_independence():
    gates=json.loads((ROOT/'gate_plan.json').read_text())['gates'];assert all(not g['requires'] for g in gates);assert len(gates)>=14
