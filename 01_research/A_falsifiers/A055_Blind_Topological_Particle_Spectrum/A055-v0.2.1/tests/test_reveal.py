import math
from a055_spectrum.features import FEATURE_REGISTRY
from a055_spectrum.reveal import _triplet_error, _empirical_p


def test_legacy_feature_domains_remain_fail_closed():
    assert FEATURE_REGISTRY["linking_strength"]["ratio_pools"] == ["links"]
    assert "all" not in FEATURE_REGISTRY["abs_writhe"]["ratio_pools"]
    assert FEATURE_REGISTRY["contact_ratio"]["diagnostic_only"] is True


def test_triplet_error_exact_scale_case():
    masses=[2.0, 14.0, 200.0]
    xs=[0.5, 3.5, 50.0]
    e,s=_triplet_error(xs,masses)
    assert abs(e) < 1e-14
    assert abs(s-4.0) < 1e-14


def test_empirical_p_has_plus_one_correction():
    null=[0.1,0.2,0.3,0.4]
    assert abs(_empirical_p(0.25,null)-3/5) < 1e-15
