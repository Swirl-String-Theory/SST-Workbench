"""CPU parallelism and runtime selection tests; no physical certification."""
from dataclasses import replace
import numpy as np
import pytest
from experiment.euler3d import Config,Euler3D
from experiment.science import profile_plan,run_budget
from runtime_options import parse

def test_cpu_fft_reference_parity():
    cfg=Config(n=24,dt=0.05,final_time=.10,threads=2,backend='cpu-scipy-fft')
    fast=Euler3D(cfg)
    ref=Euler3D(replace(cfg,backend='cpu-numpy-reference',threads=1))
    ufast,_=fast.initial_velocity(); uref,_=ref.initial_velocity()
    assert np.allclose(ufast,uref,rtol=4e-12,atol=1e-11)
    assert np.allclose(fast.rhs(ufast),ref.rhs(uref),rtol=8e-12,atol=2e-10)
    a=fast.rk4(ufast,.05); b=ref.rk4(uref,.05)
    assert np.allclose(a,b,rtol=3e-11,atol=2e-10)
    assert abs(fast.stats(a,[0,0,0],[0,0,0])['E_global']-
               ref.stats(b,[0,0,0],[0,0,0])['E_global'])<1e-10

def test_plan_and_multiprofile_defaults():
    opts={'grid':80,'threads':12}
    p=profile_plan('BASIC',opts)
    assert p['coarse_grid']==80 and p['refined_grid']==112
    assert p['threads']==12 and p['budget']['budget_approved']
    p2=profile_plan('FULL',{'grid':128,'threads':12})
    assert p2['coarse_grid']==128 and p2['refined_grid']>128
    assert not p2['budget']['budget_approved']

def test_bad_gpu_backend_is_explicit_error():
    with pytest.raises(RuntimeError,match='BLOCKED_UNVALIDATED_BACKEND'):
        profile_plan('BASIC',{'backend':'arc'})

def test_cli_supports_equals_and_spaces():
    a,o,_=parse(['BASIC','--grid=80','--threads','12'])
    assert o['grid']==80 and o['threads']==12
    a,o,_=parse(['FULL','--grid','128','--threads=12','--allow-expensive'])
    assert o['grid']==128 and o['allow_expensive']

def test_fixed_absolute_time_and_pinned_grid_rules():
    assert profile_plan('BASIC',{'dt':0.013,'t_end':1.2})['final_time']==1.2  # adaptive final step clipped
    with pytest.raises(ValueError):profile_plan('BASIC',{'grid':81})
    with pytest.raises(ValueError):profile_plan('BASIC',{'grid':128,'grid_up':96})

def test_frozen_policy_contains_backend_and_grid_restrictions():
    import json
    from pathlib import Path
    pol=json.loads((Path(__file__).parents[1]/'science_contract.json').read_text())['a075_execution_policy']
    assert 80 in pol['grid_choices'] and 128 in pol['grid_choices']
    assert 'arc' not in pol['allowed_backends']
