import numpy as np
import pytest
from a069_v061.gp_core_v062 import coupling_from_xi,step_mu,conserved_mu,planar_soliton_residual

def test_reference_healing_length():
    assert abs(coupling_from_xi(1/np.sqrt(2))-1)<1e-12

def test_dynamic_potential_changes():
    assert abs(coupling_from_xi(.28)-6.377551020408163)<1e-12

def test_planar_soliton_is_exact():
    x=np.linspace(-4,4,201)
    assert np.max(abs(planar_soliton_residual(x,.28)))<2e-14

def test_mu_1_step_matches_legacy_fft():
    from a069_v061.gp_core_v062 import kinetic
    import sys
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    from subprocess import run
    import zipfile
    runtime=root/'upstream_runtime'/'A069_3D_SwirlClock_Emergence'/'A069-v0.5.0'
    if not runtime.exists():
        run([sys.executable,str(root/'bootstrap_upstream.py')],cwd=root,check=True)
    sys.path.insert(0,str(runtime))
    from experiment.knotted_gp3d import step
    rs=np.random.default_rng(3)
    z=np.ones((16,16,16),complex)+.05*(rs.normal(size=(16,16,16))+1j*rs.normal(size=(16,16,16)))
    assert np.max(abs(step(z,10.,.003)-step_mu(z,10.,.003,1.0)))<1e-12

def test_conserved_mu_nonnegative():
    z=np.ones((8,8,8),complex)
    mass,en=conserved_mu(z,8.,coupling_from_xi(.28))
    assert abs(mass-512)<1e-9 and abs(en)<1e-12

def test_invalid_xi_rejected():
    with pytest.raises(ValueError): coupling_from_xi(0)
