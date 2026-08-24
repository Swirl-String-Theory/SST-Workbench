import numpy as np
from sst_finite_core_falsifier.delay import wavepacket_return,wrap
from sst_finite_core_falsifier.eigen import solve_spectrum,mode_at_axial
from sst_finite_core_falsifier.reveal import _bounded_growth_effect,_phase_discovery
from sst_finite_core_falsifier.analyze import _clock_regime


def test_phase_refinement_respects_sampling_target_and_is_valid_for_exact_linear_dispersion():
    L=40.0; vg=1.7; k0=.2; omega0=.9; co=[vg,omega0]
    r=wavepacket_return(L,k0,omega0,co,vg,31,301,.05,.35,0.0,.5)
    assert r['available'] and r['continuous_peak_refined']
    assert r['phase_sampling_step_rad'] <= .05*(1+1e-12)
    assert r['phase_valid']
    assert r['phase_uncertainty_rad'] < .05


def test_dispersion_uncertainty_can_falsify_absolute_phase_without_falsifying_delay():
    L=40.0; vg=1.7; k0=.2; omega0=.9; co=[vg,omega0]
    r=wavepacket_return(L,k0,omega0,co,vg,31,301,.05,.20,.05,.5)
    assert r['available']
    assert r['tau_relative_error'] < .03
    assert not r['phase_valid']
    assert r['phase_uncertainty_from_dispersion_rad'] > .20


def test_intrinsic_frequency_is_exported_by_eigenmode_solver():
    sp=solve_spectrum('gaussian',-.75,1,.08,24,5.0)
    assert sp['modes']
    m=sp['modes'][0]
    assert np.isfinite(m['advective_frequency'])
    assert np.isfinite(m['omega_intrinsic'])
    assert abs(m['omega']-m['advective_frequency']-m['omega_intrinsic']) < 1e-10


def test_axial_branch_continuation_returns_overlap_history():
    cfg={'min_localization':.2,'min_axial':.02,'max_axial':.98,'max_residual':1e-6,
         'branch_continuation_enabled':True,'branch_anchor_axial_ratio':-1.0,
         'branch_axial_steps':3,'branch_min_overlap':.01,'min_overlap':.01}
    md,meta=mode_at_axial('gaussian',-.5,1,.08,22,5.0,cfg)
    assert meta['enabled']
    if md is not None:
        assert meta['success']
        assert len(meta['path'])==3
        assert meta['min_overlap']>=.01


def test_clock_regime_separates_fast_locked_and_slow_modes():
    cfg={}
    assert _clock_regime({'mode_over_swirl_frequency_ratio':1.05,'group_velocity':-.5},cfg)=='FAST_SWIRL_LOCKED'
    assert _clock_regime({'mode_over_swirl_frequency_ratio':.05,'group_velocity':.004},cfg)=='SLOW_MODE'
    assert _clock_regime({'mode_over_swirl_frequency_ratio':2.0,'group_velocity':.5},cfg)=='OTHER_BRANCH'


def test_bounded_growth_effect_has_no_neutral_log_singularity():
    z=_bounded_growth_effect(0.0,.003,1e-6)
    assert -1.0 < z < 0.0
    assert np.isfinite(z)
    assert _bounded_growth_effect(.003,0.0,1e-6)==-z


def test_phase_discovery_recovers_synthetic_minimum_without_preregistered_target():
    target=1.35; rows=[]; phases=np.linspace(-np.pi,np.pi,10,endpoint=False)
    for j in range(6):
        for ph in phases:
            # minimum at target
            y=-.25*np.cos(ph-target)+.01*j
            rows.append({'carrier_id':f'C{j}','m':1,'both_valid':True,'closed_phase_valid':True,
                         'neutral_pair':False,'clock_regime':'FAST_SWIRL_LOCKED','closed_loop_phase':float(ph),
                         'growth_effect_bounded':float(y)})
    cfg={'phase_discovery_min_rows_per_carrier':4,'phase_permutations':19,
         'phase_discovery_bootstrap':19,'phase_discovery_seed':12}
    d=_phase_discovery(rows,1,'FAST_SWIRL_LOCKED',cfg)
    assert d['available'] and d['n_carriers']==6
    err=abs(wrap(d['fit']['phase_min_rad']-target))
    assert err<.08
