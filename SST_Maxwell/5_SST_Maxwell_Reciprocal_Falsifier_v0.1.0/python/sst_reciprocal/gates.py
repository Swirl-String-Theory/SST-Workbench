from __future__ import annotations
import math
import numpy as np
from .linear import svd_diagnostics, nnls_equilibrium, positive_self_stress, duplicate_column_count

SST_CONSTANTS = {
    "v_swirl_m_s": 1.09384563e6,
    "r_c_m": 1.40897017e-15,
    # In v0.8.35 this numerical density is used as the horn-envelope normalization.
    "rho_horn_eff_kg_m3": 3.8934358266918687e18,
    "F_swirl_max_N": 29.053507,
}


def constant_area_force_identity():
    c=SST_CONSTANTS
    Pi=c["rho_horn_eff_kg_m3"]*c["v_swirl_m_s"]**2
    Ac=math.pi*c["r_c_m"]**2
    F=Pi*Ac
    return {"Pi_star_Pa":Pi,"A_c_m2":Ac,"Pi_Ac_N":F,"F_swirl_max_N":c["F_swirl_max_N"],
            "relative_residual":F/c["F_swirl_max_N"]-1.0}


def rigid_kernel_basis(points):
    X=np.asarray(points,float)
    n=len(X); C=X.mean(axis=0); Y=X-C
    modes=[]
    for ax in range(3):
        v=np.zeros((n,3)); v[:,ax]=1; modes.append(v.reshape(-1))
    axes=np.eye(3)
    for w in axes:
        v=np.cross(np.tile(w,(n,1)),Y); modes.append(v.reshape(-1))
    Q=[]
    for v in modes:
        for q in Q: v=v-q*np.dot(q,v)
        nv=np.linalg.norm(v)
        if nv>1e-12: Q.append(v/nv)
    return np.column_stack(Q) if Q else np.zeros((3*n,0))


def projection_closure(residual, seed=1864, projections=12):
    R=np.asarray(residual,float).reshape(-1,3)
    base=np.linalg.norm(R)
    rng=np.random.default_rng(seed)
    ratios=[]
    for _ in range(projections):
        q,_=np.linalg.qr(rng.normal(size=(3,3)))
        P=q[:,:2]
        ratios.append(float(np.linalg.norm(R@P)/(base+1e-300)))
    return {"projection_count":projections,"ratios":ratios,"max_ratio":max(ratios,default=0.0)}


def analyze_matrix(A,b,points,cfg):
    sv=svd_diagnostics(A,cfg["sv_rel_tol"])
    lam,resid,chi=nnls_equilibrium(A,b)
    pss=positive_self_stress(A,cfg["sv_rel_tol"],cfg.get("self_stress_lp_samples",16),cfg.get("random_seed",2401864))
    R=resid.reshape(-1,3)
    local=np.linalg.norm(R,axis=1)
    b_local=np.linalg.norm(np.asarray(b).reshape(-1,3),axis=1)
    scale=np.maximum(b_local, np.median(b_local[b_local>0]) if np.any(b_local>0) else 1.0)
    local_rel=local/scale
    Q=rigid_kernel_basis(points)
    if Q.shape[1]:
        Aq=A.T@Q
        rigid_res=float(np.linalg.norm(Aq)/(np.linalg.norm(A.toarray() if hasattr(A,"toarray") else A)+1e-300))
        rigid_dim=Q.shape[1]
    else: rigid_res=0.0; rigid_dim=0
    mech_excess=max(0,sv["left_nullity"]-rigid_dim)
    return {
        "svd":sv,
        "nnls":{"chi_kkt":chi,"lambda_nonnegative":True,"lambda":[float(x) for x in lam],
                "active_multiplier_count":int(np.count_nonzero(lam>cfg.get("lambda_positive_tol",1e-10))),
                "residual_norm":float(np.linalg.norm(resid)),
                "max_local_closure_rel":float(np.max(local_rel) if len(local_rel) else 0.0),
                "rms_local_closure_rel":float(np.sqrt(np.mean(local_rel**2)) if len(local_rel) else 0.0)},
        "positive_self_stress":pss,
        "duplicate_column_pairs":duplicate_column_count(A,cfg.get("duplicate_cosine_tol",1e-8)),
        "mechanism_audit":{"left_nullity_raw":sv["left_nullity"],"rigid_mode_dimension":rigid_dim,
                           "left_nullity_minus_rigid":mech_excess,"rigid_kernel_residual":rigid_res,
                           "guard":"contact-network nullity is not a full dynamical instability unless the declared mechanical model is complete"},
        "projection_sanity":projection_closure(resid,cfg.get("random_seed",2401864)),
        "area_force_identity":constant_area_force_identity(),
    }


def classify(metrics,cfg,complete_mechanical_model=False):
    chi=metrics["nnls"]["chi_kkt"]
    smin=metrics["svd"]["sigma_min_positive"]
    smax=metrics["svd"]["sigma_max"]
    ratio=smin/smax if smax>0 else 0.0
    close=metrics["nnls"]["max_local_closure_rel"]
    out={}
    out["equilibrium_gate"]="PASS" if chi<=cfg["chi_kkt_pass"] else ("WARN" if chi<=cfg["chi_kkt_warn"] else "FAIL")
    out["local_reciprocal_closure_gate"]="PASS" if close<=cfg["local_closure_pass"] else ("WARN" if close<=cfg["local_closure_warn"] else "FAIL")
    out["near_singular_gate"]="WARN" if ratio<cfg["sigma_ratio_warn"] else "PASS"
    out["positive_self_stress_gate"]="PRESENT" if metrics["positive_self_stress"]["feasible"] else "ABSENT"
    if complete_mechanical_model:
        out["mechanism_gate"]="PASS" if metrics["mechanism_audit"]["left_nullity_minus_rigid"]==0 else "FAIL"
    else:
        out["mechanism_gate"]="INFORMATIONAL_ONLY"
    out["strict_reciprocity_gate"]="UNTESTED_NO_DUAL_CELL_INCIDENCE"
    return out
