import numpy as np
from a056_falsifier.numeric import mittag_leffler_relax

def test_exponential_limit():
    t=np.linspace(0,4,20); y=mittag_leffler_relax(t,2.0,1.0); assert np.max(np.abs(y-np.exp(-t/2.0)))<1e-10
