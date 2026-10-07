import numpy as np
from sst_falsifier import dd32_reference
from sst_falsifier.backends import python_ref
from sst_falsifier.backend_contract import relative_l2


def test_dd32_reference_biot_savart_is_high_precision():
    n=48;t=np.linspace(0,2*np.pi,n,endpoint=False)
    p=np.column_stack((np.cos(t),np.sin(t),0*t))
    u=np.linspace(-.5,.5,8);q=np.column_stack((.21*np.cos(2*u),.18*np.sin(3*u),u))
    ref=python_ref.biot_savart(p,q,gamma=1.23456789,core=.041)
    dd=dd32_reference.biot_savart(p,q,gamma=1.23456789,core=.041)
    assert relative_l2(dd,ref) <= 1e-8


def test_dd32_is_not_labeled_fp64_in_source_contract():
    assert dd32_reference.__doc__ and 'not IEEE binary64' in dd32_reference.__doc__
