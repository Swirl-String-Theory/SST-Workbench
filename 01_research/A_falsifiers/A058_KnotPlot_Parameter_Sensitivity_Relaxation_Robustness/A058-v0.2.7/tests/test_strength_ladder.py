import math
def test_ladder_exact():
    vals=[2**(k/4) for k in range(-16,17)]
    assert len(vals)==33
    for k in range(1,17): assert math.isclose(2**(k/4)*2**(-k/4),1.0,rel_tol=0,abs_tol=1e-15)
