from pathlib import Path
import json
import numpy as np
import pytest

from sst_bkm.pklsa import (
    E010Carrier, E010_VERSION, TOPOLOGY_ID, geometry_sha256,
    validate_e010_release, select_trefoil_carriers, resolve_carrier_source_path,
    canonicalize_centerline,
)
from sst_bkm.seed import base_centerline


def _write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _e010_fixture(tmp_path: Path):
    out = tmp_path / "E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs"
    _write_json(out / "RELEASE.json", {
        "e010_version": E010_VERSION, "source_native_mode": True,
        "source_contract_gate_pass": True, "a001_a008_coverage_gate_pass": True,
        "canonical_identity_admission_gate_pass": True, "identity_database_gate_pass": True,
        "topology_database_ingest_gate_pass": True, "trefoil_poc_gate_pass": True,
        "full_campaign_gate_pass": False, "publication_ready_geometry_layer": False,
    })
    top = out / "poc" / "atlas" / TOPOLOGY_ID
    carriers = [
        # unique, hard-pass upstream
        ("CAR_A", "knotplot_relaxed", "UPSTREAM_REFERENCE", None, None, True, "gA"),
        # geometry duplicate of A
        ("CAR_B", "knotplot_relaxed", "UPSTREAM_REFERENCE", "CAR_A", None, True, "gA"),
        # hard-gate fail
        ("CAR_C", "ptsa", "GENERATED_FAMILY", None, None, False, "gC"),
        # byte-identical mirror class
        ("CAR_D", "fremlin_fourier_mirror", "BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT", None, "CAR_A", True, "gD"),
        # unique, hard-pass generated
        ("CAR_E", "ptsa", "GENERATED_FAMILY", None, None, True, "gE"),
    ]
    indep_entries=[]; metric_entries=[]
    for cid, family, eclass, gdup, rdup, hardpass, group in carriers:
        envelope={
            "carrier": {
                "carrier_id":cid,"catalog_id":"A001" if family.startswith("knotplot") else "A008",
                "independence_group":group,"lineage_group":group,"method_group":"method",
                "parent_source_family":None,"provider_group":"provider","raw_sha256":"00"*32,
                "reference_id":None,"representation":"xyz","source_family":family,
                "source_path":rf"C:\workspace\projects\SST-Workbench\03_data\A_knots\{cid}.xyz",
                "source_role":"reference_embedding","topology_id":TOPOLOGY_ID,"variant_id":cid,
                "metadata":{"source_root":r"C:\workspace\projects\SST-Workbench\03_data\A_knots","relative_path":f"{cid}.xyz"}
            },
            "geometry_sha256":"11"*32,
        }
        _write_json(top / ("generated" if family=="ptsa" else "sources") / family / f"{cid}.json", envelope)
        indep_entries.append({
            "carrier_id":cid,"catalog_id":envelope["carrier"]["catalog_id"],"topology_id":TOPOLOGY_ID,
            "source_family":family,"independence_group":group,"provider_group":"provider",
            "lineage_group":group,"method_group":"method","parent_source_family":None,
            "evidence_independence_class":eclass,"geometry_duplicate_of":gdup,"raw_duplicate_of":rdup,
        })
        metric_entries.append({"carrier_id":cid,"literature_hard_gate_pass":hardpass,"literature_gate_status":{"G1":"PASS" if hardpass else "FAIL"}})
    _write_json(top/"qualification"/"summary.json", {
        "topology_id":TOPOLOGY_ID,"qualification_gate_pass":True,"discovered_carriers":5,"qualified_carriers":5,
        "error_carriers":0,"literature_hard_gate_failures":["CAR_C"]
    })
    _write_json(top/"qualification"/"source_independence.json", {"carrier_count":5,"entries":indep_entries})
    _write_json(top/"qualification"/"geometry_metrics.json", {"record_count":5,"carriers":metric_entries})
    return out


def test_release_gate_is_trefoil_scoped(tmp_path):
    out=_e010_fixture(tmp_path)
    r=validate_e010_release(out)
    # Aggregate atlas gate may be red while the explicit 3_1 source/identity gates are green.
    assert r["full_campaign_gate_pass"] is False
    assert r["trefoil_poc_gate_pass"] is True


def test_e010_selection_excludes_hard_fail_duplicates_and_mirrors(tmp_path):
    out=_e010_fixture(tmp_path)
    rows,audit,summary=select_trefoil_carriers(out,{})
    assert [r.carrier_id for r in rows]==["CAR_A","CAR_E"]
    assert audit["selected_count"]==2
    assert audit["excluded_by_reason"]["duplicate_geometry_or_raw"]==1
    assert audit["excluded_by_reason"]["literature_hard_gate_fail"]==1
    assert audit["excluded_by_reason"]["nonindependent_mirror"]==1


def test_relocated_windows_source_path(tmp_path):
    wb=tmp_path/"SST-Workbench"; target=wb/"03_data"/"A_knots"/"curve.xyz"; target.parent.mkdir(parents=True); target.write_text("0 0 0\n1 0 0\n0 1 0\n")
    c=E010Carrier("CAR_X","x","x","xyz",r"D:\old\SST-Workbench\03_data\A_knots\curve.xyz",None,"g",None,None,None,None,None,None,None,None,{},"env",True,{},None,None)
    assert resolve_carrier_source_path(c,wb)==target.resolve()


def test_geometry_hash_matches_e010_contract():
    a=np.arange(30,dtype=float).reshape(10,3)
    h=geometry_sha256([a])
    assert len(h)==64 and h==geometry_sha256([a.copy()])
    assert h!=geometry_sha256([a[::-1].copy()])


def test_centerline_canonicalization_and_native_seed():
    t=np.linspace(0,2*np.pi,128,endpoint=False)
    P=np.column_stack([(2+0.5*np.cos(3*t))*np.cos(2*t),(2+0.5*np.cos(3*t))*np.sin(2*t),0.8*np.sin(3*t)])
    C,meta=canonicalize_centerline(P,96,1.1)
    assert C.shape==(96,3); assert np.linalg.norm(C.mean(axis=0))<1e-12
    assert abs(np.sqrt(np.mean(np.sum(C*C,axis=1)))-1.1)<1e-12
    uh=base_centerline(C,12,2*np.pi,0.42)
    assert uh.shape==(3,12,12,12) and np.isfinite(uh).all()


def _summary(gid,N,tstar,group="anon"):
    return {"geometry_id":gid,"group_id":group,"N":N,"numerically_valid":True,"blowup_fit":{"candidate":True,"t_star":tstar}}


def test_convergence_never_pools_distinct_geometries_or_groups():
    from sst_bkm.campaign import convergence_assessment
    a=convergence_assessment([_summary("g1",24,1.00,"A"),_summary("g2",32,1.01,"A"),_summary("g3",40,1.02,"A")])
    assert a["verdict"]=="NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW"
    b=convergence_assessment([_summary("g1",24,1.00,"A"),_summary("g1",32,1.01,"A"),_summary("g1",40,1.02,"A")])
    assert b["verdict"]=="ESCALATE_BKM_CANDIDATE"
