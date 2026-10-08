import numpy as np
from a055_science.chirality import circulation_relative_spectrum,metamorphic_errors,analytic_covariance_selftest,sector_bias_qualified
from a055_science.traveling import periodic_bishop_frame

def _fixture(n=144):
    th=2*np.pi*np.arange(n)/n; comps=[]; fs=[]
    for i,cx in enumerate((-3.,0.,3.)):
        c=np.c_[np.cos(th)+cx,np.sin(th),.1*np.sin(2*th)]; comps.append(c); _t,nv,b,_=periodic_bishop_frame(c); z=np.exp(1j*2*th); fs.append(z[:,None]*nv+0.2j*z[:,None]*b)
    return np.vstack(fs),comps,np.array([1.,-1.,1.])

def test_analytic_covariance_selftest(): assert analytic_covariance_selftest()['pass']
def test_gauge_equivalent_transforms_leave_circulation_relative_purity_invariant():
    f,c,g=_fixture(); h=circulation_relative_spectrum(f,c,g,(2,))[2]; m=metamorphic_errors(f,c,g,2); assert m['max_abs_error']<1e-10; assert abs(h['circulation_relative_purity'])<=1.0+1e-12
def test_sector_bias_requires_population_not_single_mode():
    assert not sector_bias_qualified({'qualified_mode_count':1,'sector_vote_bias':1.0},3,.5)
    assert sector_bias_qualified({'qualified_mode_count':4,'sector_vote_bias':.5},3,.5)
