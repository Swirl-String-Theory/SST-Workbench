from sst_counterpulley.core import DEFAULT_DATA, prepare_centerline
from sst_counterpulley.ideal_ab import parse_ideal_ab

def test_parse_trefoil():
    m=parse_ideal_ab(DEFAULT_DATA,'3:1:1')
    assert m.knot_id=='3:1:1'
    assert abs(m.L-16.371637)<1e-12
    assert abs(m.D-1.0)<1e-12
    assert len(m.harmonics)>100

def test_prepare_centerline():
    c,m=prepare_centerline(n=64)
    assert c.shape==(64,3)
    assert m['knot_id']=='3:1:1'
