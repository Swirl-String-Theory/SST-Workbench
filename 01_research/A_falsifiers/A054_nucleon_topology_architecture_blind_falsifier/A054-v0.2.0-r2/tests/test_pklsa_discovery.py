from pathlib import Path
from a054_ntaf.pklsa import find_e011_output, find_e010_version, PKLSAError


def _mk_e011(p: Path):
    p.mkdir(parents=True)
    (p/'STATIC_READY_INDEX.json').write_text('[]', encoding='utf-8')
    (p/'STATIC_READY_PROVIDER_ANCHORS.jsonl').write_text('', encoding='utf-8')
    return p


def _mk_e010(p: Path):
    q=p/'pklsa_builder'; q.mkdir(parents=True)
    for f in ('io_geometry.py','gilbert.py','hashing.py'): (q/f).write_text('',encoding='utf-8')
    return p


def test_exact_canonical_discovery(tmp_path):
    e011=_mk_e011(tmp_path/'01_research'/'E_pipelines'/'E011_sklsa_selected_knot_link_seed_atlas'/'E011-v0.3.0'/'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs')
    e010=_mk_e010(tmp_path/'01_research'/'E_pipelines'/'E010_pklsa_parametric_knot_link_seed_atlas'/'E010-v0.3.1')
    assert find_e011_output(tmp_path)==e011
    assert find_e010_version(tmp_path)==e010


def test_marker_fallback_discovery(tmp_path):
    e011=_mk_e011(tmp_path/'moved_family'/'E011-v0.3.0'/'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs')
    e010=_mk_e010(tmp_path/'moved_pklsa'/'E010-v0.3.1')
    assert find_e011_output(tmp_path)==e011
    assert find_e010_version(tmp_path)==e010


def test_duplicate_fallback_fails_closed(tmp_path):
    _mk_e011(tmp_path/'a'/'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs')
    _mk_e011(tmp_path/'b'/'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs')
    try: find_e011_output(tmp_path)
    except PKLSAError as e: assert 'found 2' in str(e)
    else: raise AssertionError('duplicate E011 outputs must fail closed')
