from pathlib import Path
from qhp_sweep.generate import seed_identity,topology_class_from_name,seed_kind_from_name

def test_unique_seed_identity_preserves_kind_and_full_code():
    assert seed_identity(Path('knot_6.3_final.txt'))=='knot_6.3'
    assert seed_identity(Path('link_6.3.1_final.txt'))=='link_6.3.1'
    assert seed_identity(Path('link_6.3.2_final.txt'))=='link_6.3.2'
    assert seed_identity(Path('torus_2.3_final.txt'))=='torus_2.3'
    assert len({seed_identity(Path(x)) for x in ['knot_6.3_final.txt','link_6.3.1_final.txt','link_6.3.2_final.txt']})==3

def test_topology_class_is_descriptive_not_identity():
    assert topology_class_from_name(Path('knot_6.3_final.txt'))=='6.3'
    assert topology_class_from_name(Path('link_6.3.1_final.txt'))=='6.3'
    assert seed_kind_from_name(Path('link_6.3.1_final.txt'))=='link'
