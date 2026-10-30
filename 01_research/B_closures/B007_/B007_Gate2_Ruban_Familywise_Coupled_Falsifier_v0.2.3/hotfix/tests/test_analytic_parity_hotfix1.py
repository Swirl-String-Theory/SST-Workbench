"""B007 hotfix1: cross-platform float64 roundoff must not block faithful sources."""
import numpy as np
import pytest
from src.atlas_perturbation import compare_analytic_source
from src.geometry import generate


def test_exact_source_is_recorded_exact():
    x=generate(2,3,.2,128,True)[0]
    assert compare_analytic_source('test',len(x),x,x)['status']=='EXACT'


def test_one_ulp_platform_roundoff_is_accepted_without_disabling_audit():
    x=generate(2,3,.2,128,True)[0]
    y=x.copy()
    y[17,2]=np.nextafter(y[17,2],np.inf)
    check=compare_analytic_source('test',len(x),y,x)
    assert check['status']=='BOUNDED_FLOAT64_ROUNDOFF'
    assert not check['bitwise_equal']
    assert check['max_abs_error']>0


def test_many_small_platform_errors_are_allowed_only_inside_rms_limit():
    x=generate(2,3,.2,128,True)[0]
    y=x.copy()+2*np.finfo(np.float64).eps
    assert compare_analytic_source('test',len(x),y,x)['status']=='BOUNDED_FLOAT64_ROUNDOFF'


@pytest.mark.parametrize('delta',[1.e-10,1.e-8,1.e-4])
def test_real_analytic_mismatch_is_rejected(delta):
    x=generate(2,3,.2,128,True)[0]
    y=x.copy();y[0,0]+=delta
    with pytest.raises(ValueError,match='max_abs_error='):
        compare_analytic_source('test',len(x),y,x)


def test_nonfinite_and_shape_mismatch_rejected():
    x=generate(2,3,.2,128,True)[0]
    with pytest.raises(ValueError,match='shape mismatch'):
        compare_analytic_source('test',128,x[:-1],x)
    y=x.copy();y[2,1]=np.nan
    with pytest.raises(ValueError,match='Nonfinite'):
        compare_analytic_source('test',128,y,x)
