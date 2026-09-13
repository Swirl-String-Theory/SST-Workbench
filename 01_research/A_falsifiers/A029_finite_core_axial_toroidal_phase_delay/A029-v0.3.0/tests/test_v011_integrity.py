import numpy as np
from sst_finite_core_falsifier.workflow import _decision
from sst_finite_core_falsifier.profiles import profile,profile_metrics
from sst_finite_core_falsifier.geometry import carrier_catalog
from sst_finite_core_falsifier.delay import loop_wavenumber


def test_neutral_neutral_is_tie_not_tiny_ratio_artifact():
    cfg={'neutral_growth_epsilon':1e-8,'growth_tie_fraction':.05}
    a={'eigenmode_gate_valid':True,'growth_metric':1e-12}
    b={'eigenmode_gate_valid':True,'growth_metric':4e-13}
    d=_decision(a,b,cfg)
    assert d['winner_anonymous']=='TIE'
    assert d['basis']=='NEUTRAL_NEUTRAL'
    assert d['growth_A_over_B']==1.0


def test_symmetric_closure_offsets_cancel_first_order_k_shift():
    L=80.0;m=1;n=2;h=.31;off=.37
    k0=loop_wavenumber(L,m,n,h,0.0)
    km=loop_wavenumber(L,m,n,h,-off)
    kp=loop_wavenumber(L,m,n,h,+off)
    assert abs(.5*(km+kp)-k0)<1e-14


def test_swirl_clock_profile_metrics_are_finite():
    r=np.linspace(0,5,201)
    for name in ('gaussian','smooth_rankine','compact_poly'):
        U,V=profile(name,r,.75); pm=profile_metrics(r,U,V)
        assert np.isfinite(pm['omega_swirl_rms_core'])
        assert pm['omega_swirl_rms_core']>0


def test_new_confirmatory_carriers_exist():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    c=carrier_catalog(root/'assets'/'fseries',96)
    for k in ('TORUS_T2_5','TORUS_T2_7','TORUS_T3_4','TORUS_T3_5','TWIST_4_1','TWIST_7_2'):
        assert k in c

def test_confirmatory_phase_target_cannot_enter_dynamics_modules():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]/'src'/'sst_finite_core_falsifier'
    for name in ('analyze.py','eigen.py','delay.py','workflow.py'):
        text=(root/name).read_text(encoding='utf-8')
        assert 'confirmatory_phase_target' not in text
        for forbidden in ('tau_delay','feedback_delay','user_delay'):
            assert forbidden not in text

def test_preregistered_target_phase_carrier_sign_test():
    from sst_finite_core_falsifier.reveal import _target_phase_carrier_test
    target=2.72; rows=[]
    phases=[0.2,1.5,2.7,-2.0, -0.5]
    for j in range(6):
        for ph in phases:
            x=np.cos(np.angle(np.exp(1j*(ph-target))))
            rows.append({'carrier_id':f'C{j}','m':1,'both_valid':True,'neutral_pair':False,'closed_loop_phase':ph,'log_growth_ratio':-0.4*x+0.01*j})
    r=_target_phase_carrier_test(rows,target,1,4)
    assert r['n_carriers']==6
    assert r['direction_correct_carriers']==6
    assert abs(r['one_sided_sign_p']-1/64)<1e-15
    assert r['median_carrier_slope']<0
