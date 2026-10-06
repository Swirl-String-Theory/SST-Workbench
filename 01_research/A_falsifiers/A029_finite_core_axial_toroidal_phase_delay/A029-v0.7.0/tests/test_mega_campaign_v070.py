import numpy as np
from sst_finite_core_falsifier.mega_campaign import (
    _amplitude_phase_from_record,
    _clean_reference,
    _clean_scale,
)


def test_amplitude_phase_contract_accepts_matching_complex_t0():
    rec={
        'amplitude_provenance_status':'INDEPENDENT_RAW_DYNAMICS',
        'amplitude_semantics':'core_rms_velocity_ratio_to_V0',
        'mode_normalization':'core_rms_velocity_unity',
        'amplitude_reference':'t0',
        'source_geometry_sha256':'g',
        'lagrangian_basis_hash':'b',
        't':[0.0,1.0],
        'a_real':[0.03,0.02],
        'a_imag':[0.04,0.01],
    }
    eps,phase,reasons=_amplitude_phase_from_record(rec,'g','b')
    assert not reasons
    assert abs(eps-0.05)<1e-15
    assert abs(phase-np.arctan2(0.04,0.03))<1e-15


def test_amplitude_phase_rejects_basis_mismatch():
    rec={
        'amplitude_provenance_status':'INDEPENDENT_RAW_DYNAMICS',
        'amplitude_semantics':'core_rms_velocity_ratio_to_V0',
        'mode_normalization':'core_rms_velocity_unity',
        'amplitude_reference':'t0',
        'source_geometry_sha256':'g',
        'lagrangian_basis_hash':'wrong',
        't':[0.0], 'a_real':[0.1], 'a_imag':[0.0],
    }
    eps,phase,reasons=_amplitude_phase_from_record(rec,'g','b')
    assert eps is None and phase is None and reasons


def test_clean_scale_is_fail_closed():
    ok,reasons=_clean_scale({
        'status':'INDEPENDENT_PHYSICAL_SCALE',
        'core_radius_m':1e-3,
        'velocity_scale_m_s':2.0,
        'depends_on_h':False,
        'depends_on_hbar':False,
        'depends_on_compton_radius':False,
        'depends_on_electron_mass':False,
        'depends_on_alpha':False,
        'free_fit_parameters':0,
    })
    assert ok and not reasons
    ok,_=_clean_scale({'status':'UNDECLARED'})
    assert not ok


def test_clean_reference_requires_local_curvature_contract():
    good={
        'status':'PHYSICALLY_DERIVED_REFERENCE',
        'reference_mode':'LOCAL_K_CURVATURE',
        'physical_delta_k_hat':0.01,
        'closure_displacement_independently_derived':True,
        'depends_on_attosecond_data':False,
        'depends_on_qgi_target':False,
        'free_fit_parameters':0,
    }
    ok,reasons=_clean_reference(good)
    assert ok and not reasons
    bad=dict(good, depends_on_attosecond_data=True)
    assert not _clean_reference(bad)[0]
