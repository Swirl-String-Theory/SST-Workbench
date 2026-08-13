from __future__ import annotations
import csv
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from .numerics import periodic_box_filter, curl_periodic

@dataclass
class StressCaseResult:
    case_id: str
    rho_kg_m3: float
    v_ref_m_s: float
    geom_scale: float
    family_id: str
    resolution: float
    pair_id: str
    handedness: int
    filter_radius_cells: int
    points_used: int
    median_delta_pa: float
    median_C_blind: float
    median_axisymmetry_residual: float
    median_director_alignment: float
    positive_anisotropy_fraction: float
    angular_momentum_x: float
    angular_momentum_y: float
    angular_momentum_z: float
    angular_momentum_norm: float
    kinetic_energy_j: float


def _load_velocity(path: Path):
    z = np.load(path, allow_pickle=False)
    if "u" not in z:
        raise ValueError(f"{path}: missing array 'u'")
    u = np.asarray(z["u"], float)
    if u.ndim != 4 or u.shape[-1] != 3:
        raise ValueError(f"{path}: u must have shape (nx,ny,nz,3), got {u.shape}")
    if "spacing" in z:
        sp = np.asarray(z["spacing"], float).ravel()
        if sp.size == 1: spacing = (float(sp[0]),)*3
        elif sp.size == 3: spacing = tuple(float(x) for x in sp)
        else: raise ValueError(f"{path}: spacing must be scalar or length 3")
    else:
        spacing = (1.0,1.0,1.0)
    return u, spacing


def _coarse_stress(u: np.ndarray, rho: float, radius: int) -> tuple[np.ndarray,np.ndarray]:
    ub = periodic_box_filter(u, radius)
    R = np.empty(u.shape[:-1] + (3,3), dtype=float)
    for i in range(3):
        for j in range(3):
            R[...,i,j] = rho * (periodic_box_filter(u[...,i]*u[...,j], radius) - ub[...,i]*ub[...,j])
    return ub, R


def _angular_momentum(u: np.ndarray, spacing, rho: float):
    nx,ny,nz,_ = u.shape
    dx,dy,dz = spacing
    x = (np.arange(nx) - 0.5*(nx-1))*dx
    y = (np.arange(ny) - 0.5*(ny-1))*dy
    z = (np.arange(nz) - 0.5*(nz-1))*dz
    X,Y,Z = np.meshgrid(x,y,z,indexing="ij")
    r = np.stack((X,Y,Z), axis=-1)
    dV = dx*dy*dz
    L = rho * np.sum(np.cross(r,u), axis=(0,1,2)) * dV
    E = 0.5*rho*float(np.sum(u*u))*dV
    return L, E


def analyze_case(case: dict[str,str], base_dir: Path, cfg: dict, seed: str) -> StressCaseResult:
    p = (base_dir / case["file"]).resolve()
    u, spacing = _load_velocity(p)
    rho = float(case["rho_kg_m3"]); vref = float(case["v_ref_m_s"]); geom = float(case["geom_scale"])
    nmin = min(u.shape[:3])
    if case.get("filter_radius_cells", "").strip():
        radius = int(case["filter_radius_cells"])
    else:
        radius = max(int(cfg["min_filter_radius_cells"]), int(round(float(cfg["filter_fraction"])*nmin)))
    ub, R = _coarse_stress(u, rho, radius)
    w = curl_periodic(ub, spacing)
    wmag = np.linalg.norm(w, axis=-1)
    margin = radius + int(cfg.get("trim_extra_cells",2))
    mask = np.ones(wmag.shape, dtype=bool)
    if 2*margin < min(wmag.shape):
        mask[:] = False
        mask[margin:-margin,margin:-margin,margin:-margin] = True
    vals = wmag[mask]
    positive_vals = vals[vals > 0]
    if positive_vals.size == 0:
        raise ValueError(f"{case['case_id']}: no nonzero coarse vorticity")
    q = float(cfg["vorticity_quantile"])
    threshold = float(np.quantile(positive_vals, q))
    mask &= wmag >= threshold
    idx = np.argwhere(mask)
    maxp = int(cfg["max_points_per_case"])
    if idx.shape[0] > maxp:
        # deterministic evenly spread subsample, independent of theoretical targets
        take = np.linspace(0, idx.shape[0]-1, maxp, dtype=int)
        idx = idx[take]
    t = tuple(idx[:,k] for k in range(3))
    ws = w[t]
    ns = ws / np.linalg.norm(ws,axis=-1)[:,None]
    Rs = R[t]
    ppar = np.einsum("ni,nij,nj->n",ns,Rs,ns)
    tr = np.trace(Rs,axis1=1,axis2=2)
    pperp = 0.5*(tr-ppar)
    delta = pperp-ppar
    I = np.eye(3)[None,:,:]
    model = pperp[:,None,None]*I + (ppar-pperp)[:,None,None]*(ns[:,:,None]*ns[:,None,:])
    denom = np.linalg.norm(Rs,axis=(1,2))
    resid = np.linalg.norm(Rs-model,axis=(1,2))/np.maximum(denom, np.finfo(float).tiny)
    eigvals,eigvecs = np.linalg.eigh(Rs)
    minvec = eigvecs[:,:,0]
    align = np.abs(np.sum(minvec*ns,axis=1))
    med_delta = float(np.median(delta))
    C = med_delta/(rho*vref*vref) if rho>0 and vref!=0 else float("nan")
    L,E = _angular_momentum(u,spacing,rho)
    return StressCaseResult(
        case_id=case["case_id"],rho_kg_m3=rho,v_ref_m_s=vref,geom_scale=geom,
        family_id=case.get("family_id",case["case_id"]),resolution=float(case.get("resolution") or nmin),
        pair_id=case.get("pair_id",""),handedness=int(case.get("handedness") or 0),filter_radius_cells=radius,
        points_used=int(idx.shape[0]),median_delta_pa=med_delta,median_C_blind=C,
        median_axisymmetry_residual=float(np.median(resid)),median_director_alignment=float(np.median(align)),
        positive_anisotropy_fraction=float(np.mean(delta>0)),angular_momentum_x=float(L[0]),angular_momentum_y=float(L[1]),
        angular_momentum_z=float(L[2]),angular_momentum_norm=float(np.linalg.norm(L)),kinetic_energy_j=float(E))


def read_campaign(path: Path) -> list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    req={"case_id","file","rho_kg_m3","v_ref_m_s","geom_scale"}
    if not rows or not req.issubset(rows[0]):
        raise ValueError(f"campaign must contain {sorted(req)}")
    return rows


def _log_scaling_fit(results: list[StressCaseResult]):
    good=[r for r in results if r.median_delta_pa>0 and r.rho_kg_m3>0 and r.v_ref_m_s>0 and r.geom_scale>0]
    if len(good)<6:
        return {"status":"INCONCLUSIVE","reason":"need >=6 positive cases for 3-exponent fit"}
    y=np.log([r.median_delta_pa for r in good])
    X=np.column_stack([np.ones(len(good)),np.log([r.rho_kg_m3 for r in good]),np.log([r.v_ref_m_s for r in good]),np.log([r.geom_scale for r in good])])
    rank=int(np.linalg.matrix_rank(X))
    if rank<4:
        return {"status":"INCONCLUSIVE","reason":f"rank-deficient scan matrix rank={rank}; independently vary rho, v_ref, geom_scale"}
    b,*_=np.linalg.lstsq(X,y,rcond=None)
    yhat=X@b
    ssr=float(np.sum((y-yhat)**2)); sst=float(np.sum((y-np.mean(y))**2)); r2=1.0-ssr/sst if sst>0 else 1.0
    return {"status":"OK","intercept_log":float(b[0]),"rho_exponent":float(b[1]),"velocity_exponent":float(b[2]),"geometry_exponent":float(b[3]),"r2":r2}


def _pair_metrics(results: list[StressCaseResult]):
    groups={}
    for r in results:
        if r.pair_id: groups.setdefault(r.pair_id,[]).append(r)
    rows=[]
    for pid,rr in groups.items():
        pos=[r for r in rr if r.handedness>0]; neg=[r for r in rr if r.handedness<0]
        if not pos or not neg: continue
        a,b=pos[0],neg[0]
        La=np.array([a.angular_momentum_x,a.angular_momentum_y,a.angular_momentum_z]); Lb=np.array([b.angular_momentum_x,b.angular_momentum_y,b.angular_momentum_z])
        cancel=float(np.linalg.norm(La+Lb)/max(np.linalg.norm(La)+np.linalg.norm(Lb),np.finfo(float).tiny))
        stress_rel=abs(a.median_delta_pa-b.median_delta_pa)/max(abs(a.median_delta_pa),abs(b.median_delta_pa),np.finfo(float).tiny)
        rows.append({"pair_id":pid,"L_cancellation":cancel,"stress_invariance_rel":float(stress_rel)})
    return rows


def evaluate_stress(results: list[StressCaseResult], cfg: dict):
    g=cfg["gates"]
    metrics={
      "median_axisymmetry_residual":float(np.median([r.median_axisymmetry_residual for r in results])),
      "median_director_alignment":float(np.median([r.median_director_alignment for r in results])),
      "positive_anisotropy_fraction":float(np.mean([r.positive_anisotropy_fraction for r in results])),
      "median_C_blind":float(np.median([r.median_C_blind for r in results])),
    }
    gates=[]
    def gate(name,value,ok,detail): gates.append({"name":name,"value":value,"status":"PASS" if ok else "FAIL","criterion":detail})
    gate("stress.axisymmetry",metrics["median_axisymmetry_residual"],metrics["median_axisymmetry_residual"]<=g["median_axisymmetry_residual_max"],f"<= {g['median_axisymmetry_residual_max']}")
    gate("stress.director_alignment",metrics["median_director_alignment"],metrics["median_director_alignment"]>=g["median_director_alignment_min"],f">= {g['median_director_alignment_min']}")
    gate("stress.positive_anisotropy",metrics["positive_anisotropy_fraction"],metrics["positive_anisotropy_fraction"]>=g["positive_anisotropy_fraction_min"],f">= {g['positive_anisotropy_fraction_min']}")
    scaling=_log_scaling_fit(results); metrics["scaling"]=scaling
    if scaling["status"]=="OK":
        gate("stress.rho_exponent",scaling["rho_exponent"],g["density_exponent_min"]<=scaling["rho_exponent"]<=g["density_exponent_max"],f"in [{g['density_exponent_min']},{g['density_exponent_max']}]")
        gate("stress.velocity_exponent",scaling["velocity_exponent"],g["velocity_exponent_min"]<=scaling["velocity_exponent"]<=g["velocity_exponent_max"],f"in [{g['velocity_exponent_min']},{g['velocity_exponent_max']}]")
        gate("stress.geometry_exponent",scaling["geometry_exponent"],g["geometry_exponent_min"]<=scaling["geometry_exponent"]<=g["geometry_exponent_max"],f"in [{g['geometry_exponent_min']},{g['geometry_exponent_max']}]")
        gate("stress.scaling_r2",scaling["r2"],scaling["r2"]>=g["regression_r2_min"],f">= {g['regression_r2_min']}")
    else:
        gates.append({"name":"stress.scaling_fit","status":"INCONCLUSIVE","criterion":"full-rank preregistered log scaling scan","detail":scaling["reason"]})
    pairs=_pair_metrics(results); metrics["handedness_pairs"]=pairs
    if pairs:
        mL=float(np.median([p["L_cancellation"] for p in pairs])); ms=float(np.median([p["stress_invariance_rel"] for p in pairs]))
        gate("stress.handedness_L_reversal",mL,mL<=g["pair_L_cancellation_max"],f"<= {g['pair_L_cancellation_max']}")
        gate("stress.handedness_stress_even",ms,ms<=g["pair_stress_invariance_rel_max"],f"<= {g['pair_stress_invariance_rel_max']}")
    else:
        gates.append({"name":"stress.handedness_pairs","status":"INCONCLUSIVE","criterion":"at least one +/- handedness pair"})
    status="FAIL" if any(x["status"]=="FAIL" for x in gates) else ("INCONCLUSIVE" if any(x["status"]=="INCONCLUSIVE" for x in gates) else "PASS")
    return {"status":status,"metrics":metrics,"gates":gates}


def run_stress(campaign: Path, outdir: Path, cfg: dict, seed: str):
    rows=read_campaign(campaign); base=campaign.parent
    results=[analyze_case(r,base,cfg,seed) for r in rows]
    outdir.mkdir(parents=True,exist_ok=True)
    with (outdir/"stress_cases.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(asdict(results[0]).keys())); w.writeheader(); [w.writerow(asdict(r)) for r in results]
    verdict=evaluate_stress(results,cfg)
    (outdir/"stress_verdict.json").write_text(json.dumps(verdict,indent=2),encoding="utf-8")
    return verdict
