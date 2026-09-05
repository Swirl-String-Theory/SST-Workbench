import numpy as np
from sst_link_suite.closure_robustness import simplex_weights,scan_sector_closure,borromean_sector_diagnostic


def synthetic_sector(scheme="full-central"):
    dim=2
    omega=np.array([[0.,1.],[-1.,0.]])
    terms=("length","bending","tube_repulsion","neumann")
    gradients={name:{"vector":np.array([i-1.5,0.])} for i,name in enumerate(terms)}
    hessians={name:{"matrix":np.eye(dim)*(i+1)} for i,name in enumerate(terms)}
    return {
        "sign_string":"---","signs":[-1,-1,-1],
        "energy_closure":{"finite_difference":{"gradients":gradients,"hessians":hessians,"hessian_scheme":scheme}},
        "candidate_symplectic_form":{"matrix":omega},
    }


def test_simplex_grid_count():
    assert len(simplex_weights(4,4)) == 35


def test_closure_scan_and_borromean_ledger():
    summary,rows=scan_sector_closure(synthetic_sector(),resolution=4,max_gradient_norm=1.0)
    assert len(rows)==35
    assert summary["hessian_scheme"]=="full-central"
    diag=borromean_sector_diagnostic("L6a4",[-1,1,1])
    assert diag["milnor_mu123_abs_catalog"]==1
    assert diag["circulation_product"]==-1
