import numpy as np
from sst_counterpulley.monodromy import full_relative_monodromy_fd


def test_zero_period_relative_return_derivative_is_identity():
    th=np.linspace(0,2*np.pi,4,endpoint=False)
    p=np.column_stack([np.cos(th),np.sin(th),np.zeros_like(th)])
    m=np.column_stack([1.5*np.cos(th),1.5*np.sin(th),0.2*np.ones_like(th)])
    x=np.stack([p,m])
    r=full_relative_monodromy_fd(x,D=1.0,period_hat=0.0,dt_hat=0.01,shift=0,
        rotation=np.eye(3),translation=np.zeros(3),eps_over_D=0.1,fd_step_over_D=1e-5,
        max_n=8,force_python=True,skip_build=True)
    assert np.linalg.norm(r['monodromy']-np.eye(x.size)) < 1e-8
