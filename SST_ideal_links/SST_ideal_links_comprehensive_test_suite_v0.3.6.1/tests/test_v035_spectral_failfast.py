from pathlib import Path
import json
from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.spectral import prepare_qm_link, spectral_qm_preflight, SpectralSamplingError

ROOT=Path(__file__).parents[1]
DATA=ROOT/'data'/'idealLinks.txt'


def test_raw_borromean_fixed_full_is_rejected_before_qm():
    link=parse_ideal_links(DATA)['L6a4']
    cfg=json.loads((ROOT/'configs'/'qm_full.json').read_text())
    row=spectral_qm_preflight(link,cfg)
    assert not row['pass']
    assert row['guard']['configured_qm_sample_n']==96
    assert row['guard']['recommended_nonlinear_geometry_sample_n']==1024
    try:
        prepare_qm_link(link,cfg,enforce=True)
    except SpectralSamplingError:
        pass
    else:
        raise AssertionError('Expected fail-fast SpectralSamplingError')


def test_raw_resolved_borromean_auto_promotes_without_filtering():
    link=parse_ideal_links(DATA)['L6a4']
    cfg=json.loads((ROOT/'configs'/'qm_full_raw_resolved.json').read_text())
    working,guard=prepare_qm_link(link,cfg,enforce=True)
    assert guard['effective_qm_sample_n']==1024
    assert guard['strict_nyquist_pass'] and guard['nonlinear_geometry_sampling_pass']
    assert guard['spectral_cutoff_mode'] is None
    assert len(working.components[0].A)==len(link.components[0].A)


def test_matched_filtered_ladder_configs_are_sampling_safe():
    link=parse_ideal_links(DATA)['L6a4']
    for cutoff,n in [(64,384),(96,512),(128,768)]:
        cfg=json.loads((ROOT/'configs'/f'qm_full_filtered_m{cutoff}.json').read_text())
        _,guard=prepare_qm_link(link,cfg,enforce=True)
        assert guard['effective_qm_sample_n']==n
        assert guard['working_active_mode_max']<=cutoff
        assert guard['nonlinear_geometry_sampling_pass']
