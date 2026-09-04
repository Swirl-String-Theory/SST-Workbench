import json
from pathlib import Path
import numpy as np
import pytest
from sst_modal_clock.simulate import integration_plan

ROOT=Path(__file__).resolve().parents[1]

def cfg(name):
    return json.loads((ROOT/'config'/name).read_text(encoding='utf-8'))

def test_long_horizons_are_really_long():
    assert cfg('basic.json')['t_final'] >= 12.0
    assert cfg('extended.json')['t_final'] >= 24.0
    assert cfg('extended.json')['gate_min_cycles'] >= 4.0
    assert cfg('focus_6p3.json')['t_final'] >= 18.0

def test_resolution_uses_same_long_horizon():
    vals=[cfg(f'resolution_N{n}.json')['t_final'] for n in (64,96,128)]
    assert vals == [18.0,18.0,18.0]

def test_step_cap_never_silently_coarsens_dt():
    th=np.linspace(0,2*np.pi,64,endpoint=False)
    x=np.c_[np.cos(th),np.sin(th),np.zeros_like(th)]
    c={'gamma_dimensionless':1.0,'dt_factor':0.01,'t_final':10.0,'max_steps':10,'max_samples':100}
    with pytest.raises(RuntimeError,match='refusing to enlarge dt'):
        integration_plan(x,c)

def test_plan_respects_dt_scaling_when_cap_is_sufficient():
    th=np.linspace(0,2*np.pi,64,endpoint=False)
    x=np.c_[np.cos(th),np.sin(th),np.zeros_like(th)]
    c={'gamma_dimensionless':1.0,'dt_factor':0.02,'t_final':1.0,'max_steps':1000000,'max_samples':100}
    p=integration_plan(x,c)
    assert p['dt'] <= p['dt_target']*(1+1e-12)
