from pathlib import Path
import numpy as np
import pytest

from pklsa_builder.fseries import parse_fremlin_fseries, sample_fremlin_fseries


def test_optional_a0_constant_term_is_supported(tmp_path: Path):
    p=tmp_path/'offset.fseries'
    p.write_text(
        '% optional j=0 constant term\n'
        '1.0 2.0 3.0\n'
        '2.0 0.0 0.0 0.0 0.0 0.0\n',
        encoding='utf-8',
    )
    parsed=parse_fremlin_fseries(p)
    np.testing.assert_allclose(parsed['offset'], [1.0,2.0,3.0])
    assert parsed['coefficients'].shape == (1,6)
    pts=sample_fremlin_fseries(parsed,n=4)
    np.testing.assert_allclose(pts[0], [3.0,2.0,3.0], atol=1e-12)
    np.testing.assert_allclose(pts[2], [-1.0,2.0,3.0], atol=1e-12)


def test_legacy_six_column_layout_is_unchanged(tmp_path: Path):
    p=tmp_path/'legacy.fseries'
    p.write_text('2 3 5 7 11 13\n17 19 23 29 31 37\n',encoding='utf-8')
    parsed=parse_fremlin_fseries(p)
    np.testing.assert_array_equal(parsed['offset'], np.zeros(3))
    coeff=parsed['coefficients']
    pts=sample_fremlin_fseries(parsed,n=17,phase=0.123)

    t=np.linspace(0,2*np.pi,17,endpoint=False)+0.123
    k=np.arange(1,3,dtype=float)[:,None]
    ct=np.cos(k*t[None,:]); st=np.sin(k*t[None,:])
    old=np.empty((17,3),float)
    old[:,0]=(coeff[:,0,None]*ct+coeff[:,1,None]*st).sum(axis=0)
    old[:,1]=(coeff[:,2,None]*ct+coeff[:,3,None]*st).sum(axis=0)
    old[:,2]=(coeff[:,4,None]*ct+coeff[:,5,None]*st).sum(axis=0)
    np.testing.assert_array_equal(pts,old)


def test_three_column_row_after_harmonic_remains_fail_closed(tmp_path: Path):
    p=tmp_path/'bad.fseries'
    p.write_text('1 2 3 4 5 6\n7 8 9\n',encoding='utf-8')
    with pytest.raises(ValueError,match='initial three-coefficient'):
        parse_fremlin_fseries(p)
