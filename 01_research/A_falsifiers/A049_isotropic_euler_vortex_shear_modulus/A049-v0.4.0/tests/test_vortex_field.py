import json
from pathlib import Path

from sst_vortex_shear.euler_spectral import EulerSpectral3D, velocity_covariance_isotropy
from sst_vortex_shear.vortex_field import structured_hopf_tube_background, spectrum_matched_random_control


def _cfg():
    root = Path(__file__).resolve().parents[1]
    return json.loads((root/'configs'/'default.json').read_text(encoding='utf-8'))


def test_structured_hopf_background_is_incompressible_and_normalized():
    cfg = _cfg(); dc = dict(cfg['structured_dynamic'])
    dc['microcell_grid'] = [2,2,2]
    dc['loop_points'] = 20
    g = EulerSpectral3D(12, dc['domain_length'])
    u, meta = structured_hopf_tube_background(g, dc, cfg['seed'])
    assert g.divergence_fourier_rel(u) < 1e-12
    assert abs(g.urms(u)-dc['background_urms']) < 1e-12
    assert meta['reference_speed'] > 0.0


def test_spectrum_matched_control_keeps_total_urms():
    cfg = _cfg(); dc = dict(cfg['structured_dynamic'])
    dc['microcell_grid'] = [2,2,2]
    dc['loop_points'] = 20
    g = EulerSpectral3D(12, dc['domain_length'])
    u, _ = structured_hopf_tube_background(g, dc, cfg['seed'])
    q = spectrum_matched_random_control(g, u, cfg['seed']+991)
    assert g.divergence_fourier_rel(q) < 1e-12
    assert abs(g.urms(q)-g.urms(u)) < 1e-12
