import numpy as np, pandas as pd
from sst_v_arrow_falsifier.models import fit_models

def test_linear_recovery():
    v=7.5e5; k=np.arange(1,20)*1e7; y=2e9+v*k
    df=pd.DataFrame({"abs_k_rad_m":k,"omega_rad_s":y,"power":np.ones_like(k)})
    m=fit_models(df)
    assert abs(m["linear"]["params"]["v_m_s"]/v-1)<1e-10
