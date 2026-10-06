from e012_dynamic.util import centered_slopes, relative_shift

def test_centered_slopes():
    s=centered_slopes([1,2,3],[2,4,8])
    assert len(s)==1
    assert s[0]["slope"]==3.0

def test_relative_shift():
    assert relative_shift(10,11) < 0.1
