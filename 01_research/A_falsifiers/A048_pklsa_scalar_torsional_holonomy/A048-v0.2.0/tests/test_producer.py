from pathlib import Path
import numpy as np
import pytest
from sst_torsion.geometry import trefoil
from sst_torsion.ptsa_adapter import load_ptsa_archive
from sst_torsion.euler_producer import run_euler_smoke, canonicalize_centerline, core_chart_screen


def test_real_euler_entrypoint_distinguishes_perturbation_and_keeps_scope():
    arrays,report=run_euler_smoke(trefoil(64),{'N':12,'steps':2,'dt':.001,'centerline_samples':32})
    assert np.max(arrays['baseline_div_rms'])<1e-10
    assert report['gates']['energy_drift']['status']=='PASS'
    assert arrays['delta_velocity_rms'][0]>0
    assert report['material_phase_available'] is False
    assert report['branch_claim_allowed'] is False
    assert report['gates']['localized_core_chart']['status']=='INDETERMINATE'
    assert 'material_phase' not in arrays


def test_zero_perturbation_has_identical_evolution():
    arrays,report=run_euler_smoke(trefoil(64),{'N':12,'steps':2,'dt':.001,'amplitude':0,'centerline_samples':32})
    assert np.max(arrays['delta_velocity_rms'])==0


def test_material_phase_cannot_be_requested_then_silently_ignored():
    with pytest.raises(ValueError):
        run_euler_smoke(trefoil(64),{'material_phase_amplitude':.1})


def test_core_cannot_be_widened_to_hide_bad_sampling():
    curve=canonicalize_centerline(trefoil(128),96)
    small=core_chart_screen(curve,24,2*np.pi,.01)
    large=core_chart_screen(curve,24,2*np.pi,1.1)
    assert small['cells_per_sigma']<4
    assert large['cells_per_sigma']>=4
    assert small['status']==large['status']=='INDETERMINATE'
    assert large['tube_radius_times_max_curvature']>.5


def test_unauthenticated_archive_is_rejected(tmp_path):
    path=tmp_path/'fake.zip';path.write_bytes(b'not an archive')
    with pytest.raises(ValueError,match='SHA256'):
        load_ptsa_archive(path)


def test_native_seed_matches_reference_when_built():
    pytest.importorskip('a048_seed_native')
    _,report=run_euler_smoke(trefoil(64),{'N':12,'steps':1,'dt':.001,'centerline_samples':32})
    assert report['initializer_native_parity']['status']=='PASS'
