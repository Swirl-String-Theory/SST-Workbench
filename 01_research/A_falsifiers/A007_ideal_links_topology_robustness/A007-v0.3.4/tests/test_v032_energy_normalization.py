import numpy as np
from sst_link_suite.qm_energy import assemble_reduced_energy


def test_fixed_scales_and_cancellation_ratio():
    geometric={
        "names":["length","bending","tube_repulsion"],
        "baseline":np.array([10.,20.,2.]),
        "gradient":np.array([[1.,0.],[-1.,0.],[0.,1.]]),
        "hessian":np.zeros((3,2,2)),
        "step_D":0.01,
        "compute_offdiagonal":True,
    }
    neumann={"baseline":0.1,"gradient":np.array([0.,-1.]),"hessian":np.zeros((2,2)),"backend":"python"}
    profiles={"equal":{"length":.25,"bending":.25,"tube_repulsion":.25,"neumann":.25}}
    result=assemble_reduced_energy(
        geometric, neumann, profiles,
        normalization_scales={"length":1.,"bending":1.,"tube_repulsion":1.,"neumann":1.},
        normalization_mode="fixed_reference",
    )
    assert result["normalization_mode"] == "fixed_reference"
    assert result["profile_diagnostics"]["equal"]["gradient_cancellation_ratio"] == 0.0
