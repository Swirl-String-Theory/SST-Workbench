"""Fast settings tests. These do NOT certify Euler convergence."""
import math
from experiment.science import PROFILES, profile_plan

def test_finer_basic_full_ladders():
    for name,low,high in [('BASIC',80,112),('FULL',96,128)]:
        p=profile_plan(name)
        assert p['coarse_grid']==low and p['refined_grid']==high
        assert p['gaussian_sigma']==0.5 and p['box']==10.0
        assert p['cells_per_sigma_coarse'] >= 4.0
        assert p['cells_per_sigma_refined'] > p['cells_per_sigma_coarse']
        assert p['dt_half_max']==p['dt_max']/2
        assert p['adaptive'] is True
        assert p['dt_max'] > p['dt_min'] and p['final_time']>0
        assert p['dt_half_max'] < p['dt_max']

def test_preview_explicitly_not_sufficient_resolution():
    p=profile_plan('PREVIEW')
    assert p['cells_per_sigma_coarse'] < 4.0
    assert p['max_CFL_screen'] <= 0.2
