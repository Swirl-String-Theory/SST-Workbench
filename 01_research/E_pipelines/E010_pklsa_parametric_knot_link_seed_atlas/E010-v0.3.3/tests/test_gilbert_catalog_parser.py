from pathlib import Path
import gzip
import numpy as np

from pklsa_builder.gilbert import (
    canonical_id_from_gilbert,
    iter_gilbert_records,
    sample_gilbert_components,
)


def test_gilbert_id_namespaces_are_not_swapped():
    assert canonical_id_from_gilbert('3:1:1') == '3_1'
    assert canonical_id_from_gilbert('5:1:2') == '5_2'
    assert canonical_id_from_gilbert('10:1:166') == '10_166'
    assert canonical_id_from_gilbert('6:2:3') is None
    assert canonical_id_from_gilbert('K11a247') == '11a_247'
    assert canonical_id_from_gilbert('K11n185') == '11n_185'
    assert canonical_id_from_gilbert('L10a174') == 'L10a174'
    assert canonical_id_from_gilbert('L11n459') == 'L11n459'


def test_tl_multicomponent_and_a0_half_convention(tmp_path: Path):
    p = tmp_path / 'links.txt.gz'
    text = '''<DATA Title="fixture">\n<TL Id="L2a1" D="1.000000">\n<STRING I="1" L="6.283185">\n<Coeff I="0" A="-1,0,0" B="0,0,0" />\n<Coeff I="1" A="1,0,0" B="0,1,0" />\n</STRING>\n<STRING I="2" L="6.283185">\n<Coeff I="0" A="1,0,0" B="0,0,0" />\n<Coeff I="1" A="1,0,0" B="0,0,1" />\n</STRING>\n</TL>\n</DATA>\n'''
    with gzip.open(p, 'wt', encoding='utf-8') as f:
        f.write(text)
    records = list(iter_gilbert_records(p))
    assert len(records) == 1
    r = records[0]
    assert r['canonical_id'] == 'L2a1'
    assert len(r['components']) == 2
    assert abs(r['reference_length'] - 12.56637) < 1e-8
    comps = sample_gilbert_components(r, n=256)
    centers = [c.mean(axis=0) for c in comps]
    assert np.allclose(centers[0], [-0.5, 0.0, 0.0], atol=1e-12)
    assert np.allclose(centers[1], [0.5, 0.0, 0.0], atol=1e-12)
    assert abs(centers[1][0] - centers[0][0] - 1.0) < 1e-12


def test_malformed_single_string_ht_is_record_local_tolerant(tmp_path: Path):
    p = tmp_path / '11n.txt.gz'
    text = '''<DATA Title="fixture">\n<HT Id="K11n1" L="1.0" D="1.0">\n<STRING I="1" L="1.0">\n<Coeff I="1" A="1,0,0" B="0,1,0" />\n</HT>\n<HT Id="K11n2" L="1.0" D="1.0">\n<Coeff I="1" A="1,0,0" B="0,1,0" />\n</HT>\n</DATA>\n'''
    with gzip.open(p, 'wt', encoding='utf-8') as f:
        f.write(text)
    records = list(iter_gilbert_records(p))
    assert [r['canonical_id'] for r in records] == ['11n_1', '11n_2']
    assert all(len(r['components']) == 1 for r in records)


def test_link_qualification_preserves_relative_component_placement(tmp_path: Path):
    from pklsa_builder.models import QualificationConfig
    from pklsa_builder.qualification import qualify_components

    p = tmp_path / 'hopf.txt.gz'
    text = '''<DATA Title="fixture">\n<TL Id="L2a1" D="1.000000">\n<STRING I="1" L="6.283185">\n<Coeff I="0" A="-1,0,0" B="0,0,0" />\n<Coeff I="1" A="1,0,0" B="0,1,0" />\n</STRING>\n<STRING I="2" L="6.283185">\n<Coeff I="0" A="1,0,0" B="0,0,0" />\n<Coeff I="1" A="1,0,0" B="0,0,1" />\n</STRING>\n</TL>\n</DATA>\n'''
    with gzip.open(p, 'wt', encoding='utf-8') as f:
        f.write(text)
    r = list(iter_gilbert_records(p))[0]
    comps = sample_gilbert_components(r, n=512)
    cfg = QualificationConfig(
        resolution_ladder=[64], min_levels_for_resolution=1,
        resolved_rel_tol=0.2, converging_rel_tol=0.3,
        normalize_length=1.0, expensive_metrics=True,
        adaptive_stop=False, minimum_resolution_for_stop=64,
    )
    q = qualify_components(comps, cfg)
    inter = q['levels'][0]['intercomponent_dmin']
    # Native total length = 4*pi, native inter-component minimum distance = 1.
    expected = 1.0 / (4.0 * np.pi)
    assert abs(inter - expected) < 2e-4
    assert inter > 0.07
