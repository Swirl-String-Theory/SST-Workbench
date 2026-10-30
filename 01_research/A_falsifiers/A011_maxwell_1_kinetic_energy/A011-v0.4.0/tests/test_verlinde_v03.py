import math
from maxwell_sst_falsifier.constants import C_LIGHT,G_NEWTON,HBAR,K_B_J_PER_K,M_E_SST
from maxwell_sst_falsifier.verlinde import (
    canonical_holographic_scale_check,
    entropy_displacement_audit,
    integrability_audit,
    newton_power_law_audit,
    screen_audit,
)


def test_core_holographic_hierarchy_is_huge():
    r=canonical_holographic_scale_check()
    assert 7e39 < r['r_c2_over_lP2'] < 8e39


def test_entropy_displacement_exact_pass():
    pred=2*math.pi*K_B_J_PER_K*M_E_SST*C_LIGHT/HBAR
    r=entropy_displacement_audit([{'sample_id':'x','probe_mass_kg':str(M_E_SST),'dSdx_J_per_K_m':str(pred)}],1e-9)[0]
    assert r['status']=='PASS'


def test_integrability_parallel_and_perpendicular():
    rows=[
      {'sample_id':'a','gradT_x_K_per_m':'1','gradT_y_K_per_m':'0','gradT_z_K_per_m':'0','gradp_x_Pa_per_m':'2','gradp_y_Pa_per_m':'0','gradp_z_Pa_per_m':'0'},
      {'sample_id':'b','gradT_x_K_per_m':'0','gradT_y_K_per_m':'1','gradT_z_K_per_m':'0','gradp_x_Pa_per_m':'2','gradp_y_Pa_per_m':'0','gradp_z_Pa_per_m':'0'},
    ]
    r=integrability_audit(rows,0.01)
    assert r[0]['status']=='PASS' and r[1]['status']=='FAIL'


def test_screen_area_equipartition_pass():
    E=C_LIGHT**2; rows=[]
    for R in [0.5,1,2,4]:
        A=4*math.pi*R**2; N=A*C_LIGHT**3/(G_NEWTON*HBAR); T=2*E/(N*K_B_J_PER_K)
        rows.append({'screen_series_id':'s','radius_m':str(R),'area_m2':str(A),'bits_N':str(N),'energy_J':str(E),'T_K':str(T)})
    r=screen_audit(rows,1e-8,1e-8,1e-8)[0]
    assert r['status']=='PASS'
    assert abs(r['area_scaling_slope_dlogN_dlogA']-1)<1e-12


def test_inverse_square_fit():
    rows=[{'series_id':'s','radius_m':str(r),'observed_force_N':str(1e-10/r**2)} for r in [1,2,4,8]]
    assert newton_power_law_audit(rows,1e-9)[0]['status']=='PASS'
