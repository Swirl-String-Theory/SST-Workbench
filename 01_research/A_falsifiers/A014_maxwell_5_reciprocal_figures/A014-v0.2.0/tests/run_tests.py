from pathlib import Path
import sys,tempfile,json,time
import numpy as np
from scipy.sparse import csr_matrix
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'python'))
from sst_reciprocal.linear import svd_diagnostics,positive_self_stress,nnls_equilibrium
from sst_reciprocal.gates import constant_area_force_identity
from sst_reciprocal.io import load_xyz,native_to_sparse
from maxwell5_native import analyze_geometry,backend_status

def check(c,m):
    if not c: raise AssertionError(m)

A=csr_matrix(np.array([[1.0,0.0,-1.0],[0.0,1.0,-1.0]])); sv=svd_diagnostics(A,1e-10); check(sv['rank']==2,'rank control')
ps=positive_self_stress(A,1e-10,samples=4); check(ps['feasible'] and ps['residual']<1e-8,'positive self-stress control')
B=csr_matrix(np.eye(2)); ps2=positive_self_stress(B,1e-10,samples=4); check(not ps2['feasible'],'false positive self-stress')
lam,res,chi,solver=nnls_equilibrium(B,np.array([1.0,2.0])); check(chi<1e-10 and np.allclose(lam,[1,2],atol=1e-8),'NNLS control')
ident=constant_area_force_identity(); check(abs(ident['relative_residual'])<1e-12,'area-force identity')
# Shared-final component split guard: no blank line required when counts are supplied.
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'link.txt'; p.write_text('\n'.join(f"{i} 0 0" for i in range(8))+'\n',encoding='utf-8'); comps=load_xyz(p,[4,4]); check(len(comps)==2 and all(len(c)==4 for c in comps),'component_counts split guard')
# Native geometry smoke: two separated squares -> valid assembly and native backend.
stat=backend_status(); check(stat['available'],f"native backend unavailable: {stat}")
t=np.linspace(0,2*np.pi,64,endpoint=False); P=np.c_[2*np.cos(t),2*np.sin(t),0.2*np.sin(3*t)]
r=analyze_geometry(P,np.array([64]),radius=0.5,threads=2,require_native=True); A2,b2=native_to_sparse(r); check(A2.shape[0]==192 and len(b2)==192,'native shape'); check(r['metrics']['backend']=='cpp-pybind11','native backend tag')
print('All 5_Maxwell v0.2.0 controls passed.')
