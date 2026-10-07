from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment

def normalized_eigenvalue_distance(a,b,floor=1e-12):
    return float(abs(a-b)/max(abs(a),abs(b),floor))
def normalize_vector(v):
    z=np.asarray(v,dtype=complex).reshape(-1); n=float(np.linalg.norm(z))
    if n<=0: raise ValueError("zero eigenvector")
    return z/n
def subspace_overlap(a,b):
    return float(min(1.0,abs(np.vdot(normalize_vector(a),normalize_vector(b)))))
def match_modes(rv,R,cv,C,eigenvalue_weight=.5,overlap_weight=.5):
    rv=np.asarray(rv,complex).reshape(-1); cv=np.asarray(cv,complex).reshape(-1)
    R=np.asarray(R,complex); C=np.asarray(C,complex)
    cost=np.empty((len(rv),len(cv))); det={}
    for i,a in enumerate(rv):
        for j,b in enumerate(cv):
            d=normalized_eigenvalue_distance(a,b); o=subspace_overlap(R[:,i],C[:,j])
            q=eigenvalue_weight*d+overlap_weight*(1-o)
            cost[i,j]=q; det[(i,j)]=(d,o,q)
    rr,cc=linear_sum_assignment(cost)
    return [{"reference_index":int(i),"candidate_index":int(j),"eigenvalue_shift":float(det[(i,j)][0]),
             "overlap":float(det[(i,j)][1]),"cost":float(det[(i,j)][2])} for i,j in sorted(zip(rr,cc))]
def track_from_finest(levels,rel_tol,overlap_min,eigenvalue_weight=.5,overlap_weight=.5):
    ordered=sorted(levels,key=lambda z:z["label"])
    if not ordered: return {"branches":[]}
    fine=ordered[-1]; fvals=np.asarray(fine["eigenvalues"],complex); fvec=np.asarray(fine["eigenvectors"],complex)
    branches=[{"fine_index":i,"points":[{"label":fine["label"],"index":i,"lambda":complex(fvals[i]),
              "overlap_to_finer":None,"shift_to_finer":None}]} for i in range(len(fvals))]
    vals=fvals; vecs=fvec; mapping=list(range(len(fvals)))
    for lev in reversed(ordered[:-1]):
        cv=np.asarray(lev["eigenvalues"],complex); C=np.asarray(lev["eigenvectors"],complex)
        ms=match_modes(vals,vecs,cv,C,eigenvalue_weight,overlap_weight)
        mm={m["reference_index"]:m for m in ms}; new=[]
        for bi,ri in enumerate(mapping):
            m=mm.get(ri)
            if m is None: new.append(-1); continue
            j=m["candidate_index"]; new.append(j)
            branches[bi]["points"].append({"label":lev["label"],"index":j,"lambda":complex(cv[j]),
                "overlap_to_finer":m["overlap"],"shift_to_finer":m["eigenvalue_shift"]})
        if any(j<0 for j in new): break
        vals=np.asarray([cv[j] for j in new],complex)
        vecs=np.column_stack([C[:,j] for j in new]); mapping=list(range(len(new)))
    for b in branches:
        b["points"]=list(reversed(b["points"]))
        shifts=[p["shift_to_finer"] for p in b["points"] if p["shift_to_finer"] is not None]
        ovs=[p["overlap_to_finer"] for p in b["points"] if p["overlap_to_finer"] is not None]
        b["complete"]=len(b["points"])==len(ordered)
        b["max_eigenvalue_shift"]=max(shifts) if shifts else 0.0
        b["min_eigenvector_overlap"]=min(ovs) if ovs else 1.0
        b["positive_frequency_all_levels"]=all(complex(p["lambda"]).imag>0 for p in b["points"])
        b["persistent"]=bool(b["complete"] and b["positive_frequency_all_levels"]
            and all(x<=rel_tol for x in shifts) and all(x>=overlap_min for x in ovs))
    return {"branches":branches,"persistent_count":sum(int(b["persistent"]) for b in branches)}
def select_fine_anchored_branch(tr,fine_selected_index):
    for b in tr.get("branches",[]):
        if int(b["fine_index"])==int(fine_selected_index): return b
    raise KeyError(f"fine index {fine_selected_index} not found")
