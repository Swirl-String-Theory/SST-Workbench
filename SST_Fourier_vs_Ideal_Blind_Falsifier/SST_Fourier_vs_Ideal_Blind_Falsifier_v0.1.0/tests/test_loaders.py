from pathlib import Path
import tempfile
from sst_fourier_ideal_falsifier.loaders import parse_fseries, normalize_topology, topology_from_relaxed_filename


def test_topology_normalization_and_relaxed_mapping():
    assert normalize_topology('3.1')=='3_1'
    assert normalize_topology('3:1:1')=='3_1'
    assert normalize_topology('10:1:124')=='10_124'
    assert normalize_topology('6:2:3')=='6:2:3'
    assert topology_from_relaxed_filename('torus_2.5_final.txt')=='5_1'


def test_minimal_fseries_parser():
    # Fremlin format is six implicit-harmonic coefficients per line:
    # ax bx ay by az bz. The harmonic index starts at 1 for this catalog.
    text='''1 0 0 1 0 0\n0.2 0 0 0.2 0 0\n0 0.1 0 0 0 0.1\n'''
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'3_1';d.mkdir();p=d/'knot.3_1.fseries';p.write_text(text)
        e=parse_fseries(p,64,harmonic_start=1)
        assert e['topology']=='3_1'
        assert len(e['components'])==1
        assert e['components'][0].shape==(64,3)
