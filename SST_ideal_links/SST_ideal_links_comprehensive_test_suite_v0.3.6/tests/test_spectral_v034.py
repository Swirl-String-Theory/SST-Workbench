import numpy as np
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.spectral import (
    spectral_tail_audit, active_mode_max_link, nyquist_min_samples,
    analytic_link_length_bending, truncate_link,
)
from pathlib import Path

DATA=Path(__file__).parents[1]/"data"/"idealLinks.txt"

def test_borromean_high_mode_and_nyquist_guard():
    link=parse_ideal_links(DATA)["L6a4"]
    assert active_mode_max_link(link)==255
    assert nyquist_min_samples(255)==512


def test_borromean_analytic_bending_converges_at_high_n():
    link=parse_ideal_links(DATA)["L6a4"]
    _,b1=analytic_link_length_bending(link,2048)
    _,b2=analytic_link_length_bending(link,4096)
    assert abs(b2-b1)/abs(b2) < 2e-3


def test_cutoff_audit_exposes_borromean_tail_sensitivity():
    link=parse_ideal_links(DATA)["L6a4"]
    out=spectral_tail_audit(link,{"spectral_reference_cutoff":192})
    assert out["spectral_tail_sensitive"]
    assert out["aggregate_d2_power_tail_fraction_above_reference"] > 0.4
    assert out["full_vs_reference_bending_relative_difference"] > 0.2


def test_truncation_changes_active_mode():
    link=parse_ideal_links(DATA)["L4a1"]
    filtered=truncate_link(link,64)
    assert active_mode_max_link(filtered)<=64


def test_qm_sampling_guard_blocks_unresolved_raw_borromean():
    from sst_link_suite.spectral import prepare_qm_link
    link=parse_ideal_links(DATA)["L6a4"]
    _,guard=prepare_qm_link(link,{"qm_sample_n":96,"spectral_guard_policy":"block-readiness"})
    assert not guard["strict_nyquist_pass"]
    assert guard["readiness_blocked"]


def test_qm_sampling_guard_accepts_explicit_resolved_cutoff():
    from sst_link_suite.spectral import prepare_qm_link
    link=parse_ideal_links(DATA)["L6a4"]
    filtered,guard=prepare_qm_link(link,{"qm_sample_n":256,"spectral_cutoff_mode":32,"spectral_guard_policy":"error"})
    assert guard["strict_nyquist_pass"]
    assert guard["nonlinear_geometry_sampling_pass"]
    assert not guard["readiness_blocked"]
