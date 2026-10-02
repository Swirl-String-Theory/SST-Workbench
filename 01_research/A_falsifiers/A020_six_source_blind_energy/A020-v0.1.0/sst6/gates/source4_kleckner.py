from __future__ import annotations
import math
import numpy as np
from sst6.blind import stable_seed
from sst6.geometry import pack_components, min_curvature_radius, transverse_random_perturbation
from .common import result, prepared, native


def _local_exclusion(comps, requested=3):
    # Exclude a few core diameters of arclength so near-neighbour segments are not
    # mistaken for doubly-critical self contacts after resampling.
    vals=[]
    for p in comps:
        edge=float(np.mean(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)))
        vals.append(int(math.ceil(2.5/max(edge,1e-12))))
    return max(int(requested), max(vals, default=int(requested)))

def _reach_from_contacts(backend, comps, top_k=8, requested_exclusion=3):
    v,o=pack_components(comps); excl=_local_exclusion(comps,requested_exclusion); contacts=list(backend.nearest_segment_contacts(v,o,excl,top_k)); dmin=float(contacts[0]["distance"]) if contacts else float("inf"); rcur=min_curvature_radius(comps); return min(rcur,0.5*dmin),rcur,dmin,contacts


def contact_precursor(dataset,cfg):
    comps,v,o,_=prepared(dataset,int(cfg["n_per_component"])); backend,bname=native(cfg)
    excl=_local_exclusion(comps,int(cfg.get("adjacency_exclusion",3)))
    contacts=list(backend.nearest_segment_contacts(v,o,excl,int(cfg.get("top_k",48))))
    close=[c for c in contacts if c["distance"]<=2.0*float(cfg.get("close_ratio",1.10))]
    anti=max([-float(c["tangent_dot"]) for c in close],default=float("nan")); mind=float(contacts[0]["distance"]) if contacts else float("nan")
    risk=bool(close) and anti>=float(cfg.get("antiparallel_score",0.8))
    return result(4,"K4_ANTIPARALLEL_CONTACT","Static relaxed geometry contains or avoids close antiparallel strand pairs associated with GP-like reconnection precursors.","DIAGNOSTIC","OBSERVED" if risk else "NOT_OBSERVED",{"backend":bname,"min_distance_core":mind,"min_distance_over_2a":mind/2 if math.isfinite(mind) else None,"close_contact_count":len(close),"max_antiparallel_score":anti,"adjacency_exclusion_used":excl,"nearest_contacts":contacts[:12]},{"close_distance_over_2a":cfg.get("close_ratio",1.10),"antiparallel_score":cfg.get("antiparallel_score",0.8)},[
        "A close antiparallel pair is a precursor diagnostic, not evidence that ideal Euler SST reconnects."
    ])


def perturbation_robustness(dataset,cfg):
    comps,_,_,_=prepared(dataset,int(cfg["n_per_component"])); backend,bname=native(cfg)
    # Kleckner: RMS displacement 0.25 rope diameter; here rope diameter=2a, so RMS=0.5a. smoothing sigma=0.5 diameter=a.
    rms=float(cfg.get("rms_core",0.5)); sigma=float(cfg.get("sigma_core",1.0)); variants=int(cfg.get("variants",4)); reach_min=float(cfg.get("reach_core_min",0.98)); seed=stable_seed(dataset.sha256,"K4P"); rows=[]
    for k in range(variants):
        rng=np.random.default_rng(seed+k); pert=[transverse_random_perturbation(p,rms,sigma,rng) for p in comps]; pc=[p+d for p,d in zip(comps,pert)]; reach,rcur,dmin,_=_reach_from_contacts(backend,pc,requested_exclusion=int(cfg.get("adjacency_exclusion",3)))
        rows.append({"variant":k,"reach_core":reach,"curvature_radius_core":rcur,"half_contact_distance_core":0.5*dmin,"admissible":bool(reach>=reach_min)})
    frac=float(np.mean([r["admissible"] for r in rows])); fracmin=float(cfg.get("admissible_fraction_min",0.75))
    # First-hitting amplitude along one preregistered random direction.
    rng=np.random.default_rng(seed+10007); dirs=[transverse_random_perturbation(p,1.0,sigma,rng) for p in comps]
    lo,hi=0.0,float(cfg.get("critical_search_max_core",1.5))
    rhi=_reach_from_contacts(backend,[p+hi*d for p,d in zip(comps,dirs)],requested_exclusion=int(cfg.get("adjacency_exclusion",3)))[0]
    if rhi>=reach_min: crit=hi
    else:
        for _ in range(18):
            mid=0.5*(lo+hi); rr=_reach_from_contacts(backend,[p+mid*d for p,d in zip(comps,dirs)],requested_exclusion=int(cfg.get("adjacency_exclusion",3)))[0]
            if rr>=reach_min: lo=mid
            else: hi=mid
        crit=lo
    ok=frac>=fracmin
    return result(4,"K4_PERTURBATION_ROBUSTNESS","The hard finite-core embedding remains admissible under the preregistered Kleckner-scale transverse perturbation ensemble.","MODEL_CONDITIONAL","PASS" if ok else "FAIL",{"backend":bname,"rms_core":rms,"sigma_core":sigma,"variants":rows,"admissible_fraction":frac,"critical_rms_core_first_hit":crit},{"admissible_fraction_min":fracmin,"reach_core_min":reach_min},[
        "This is a geometric first-hitting barrier, not a dynamical Euler stability theorem."
    ])
