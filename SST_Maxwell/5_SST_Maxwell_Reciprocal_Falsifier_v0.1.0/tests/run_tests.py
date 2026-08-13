from pathlib import Path
import sys, tempfile, subprocess, json
import numpy as np
from scipy.sparse import csr_matrix
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from sst_reciprocal.linear import svd_diagnostics, positive_self_stress, nnls_equilibrium
from sst_reciprocal.gates import constant_area_force_identity


def check(cond,msg):
    if not cond: raise AssertionError(msg)

# 1) Positive self-stress: three columns enclosing the origin in R^2.
A=csr_matrix(np.array([[1.0,0.0,-1.0],[0.0,1.0,-1.0]]))
sv=svd_diagnostics(A,1e-10)
check(sv['rank']==2,'rank control failed')
ps=positive_self_stress(A,1e-10,samples=4)
check(ps['feasible'],'positive self-stress control failed')
check(ps['residual']<1e-9,'self-stress residual too large')

# 2) No positive self-stress.
B=csr_matrix(np.array([[1.0,0.0],[0.0,1.0]]))
ps2=positive_self_stress(B,1e-10,samples=4)
check(not ps2['feasible'],'false positive self-stress')

# 3) NNLS exact equilibrium.
b=np.array([1.0,2.0])
lam,res,chi=nnls_equilibrium(B,b)
check(chi<1e-12 and np.allclose(lam,b),'NNLS control failed')

# 4) Canonical area-force coherence identity.
ident=constant_area_force_identity()
check(abs(ident['relative_residual'])<1e-12,'SST area-force identity mismatch')

print('All Python controls passed.')
