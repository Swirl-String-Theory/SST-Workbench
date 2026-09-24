from pathlib import Path
import csv,json
import numpy as np
from sst_bkm.pklsa import (trefoil_candidates,verify_trefoil_bundle,canonicalize_centerline,select_variants,
                           EXPECTED_BUNDLE_SHA256)
from sst_bkm import _native


def _fixture(tmp_path:Path):
    (tmp_path/"manifests").mkdir(); (tmp_path/"families").mkdir()
    rows=[]; points=[]
    baseRs=[3.5,4.08248290463863,4.6]; bulges=[1.4,1.8,2.2,2.6]; weaves=[2.2,3.0,3.8,4.6]
    idx=0
    for R in baseRs:
      for a in bulges:
        for b in weaves:
          t=np.linspace(0,2*np.pi,512,endpoint=False); rr=R+a*np.cos(3*t)
          P=np.column_stack([rr*np.cos(2*t),rr*np.sin(2*t),b*np.sin(3*t)])
          points.append(P[None,...])
          rows.append({"candidate_id":f"FIX_{idx:02d}","family":"knot_3.1","canonical_id":"3_1","topology_class":"knot","family_index":14,
                       "variant_index":idx,"component_count":1,"points_per_component":512,
                       "construction_method":"PTSA-v1.0.0-exact-shape-up-to-global-similarity-normalization","source_record":"PTSA-v1.0.0/48-candidate-family",
                       "legacy_ptsa_id":f"PTSA_FIX_{idx:02d}","parameters_json":json.dumps({"ptsa_baseR":R,"ptsa_bulge_R":a,"ptsa_z_weave":b})})
          idx+=1
    with (tmp_path/"manifests"/"CANDIDATES_FULL.csv").open("w",newline="",encoding="utf-8") as f:
      w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    np.savez_compressed(tmp_path/"families"/"14_knot_3p1.npz",points=np.stack(points))
    return tmp_path


def test_pklsa_fixture_contract(tmp_path):
    root=_fixture(tmp_path); rows=trefoil_candidates(root); assert len(rows)==48
    info=verify_trefoil_bundle(root,strict_hash=False); assert info["shape"]==[48,1,512,3]
    assert [x.variant_index for x in select_variants(rows,[0,23,47])]==[0,23,47]


def test_centerline_canonicalization_and_native_seed(tmp_path):
    root=_fixture(tmp_path); rows=trefoil_candidates(root)
    z=np.load(root/"families"/"14_knot_3p1.npz",allow_pickle=False); P=z["points"][rows[0].variant_index,0]
    C,meta=canonicalize_centerline(P,96,1.1)
    assert C.shape==(96,3); assert np.linalg.norm(C.mean(axis=0))<1e-12
    assert abs(np.sqrt(np.mean(np.sum(C*C,axis=1)))-1.1)<1e-12
    w=np.asarray(_native.centerline_vorticity_seed(C,12,2*np.pi,0.42,1.0))
    assert w.shape==(3,12,12,12) and np.isfinite(w).all()


def _summary(gid,N,tstar):
    return {"geometry_id":gid,"N":N,"numerically_valid":True,"blowup_fit":{"candidate":True,"t_star":tstar}}


def test_convergence_never_pools_distinct_geometries():
    from sst_bkm.campaign import convergence_assessment
    a=convergence_assessment([_summary("g1",24,1.00),_summary("g2",32,1.01),_summary("g3",40,1.02)])
    assert a["verdict"]=="NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW"
    b=convergence_assessment([_summary("g1",24,1.00),_summary("g1",32,1.01),_summary("g1",40,1.02)])
    assert b["verdict"]=="ESCALATE_BKM_CANDIDATE"
