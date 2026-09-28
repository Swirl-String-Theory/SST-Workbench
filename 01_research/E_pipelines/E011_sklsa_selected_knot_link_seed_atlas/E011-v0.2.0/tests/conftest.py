from __future__ import annotations
from pathlib import Path
import csv, json
import pytest


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


@pytest.fixture
def synthetic_workbench(tmp_path: Path) -> Path:
    wb = tmp_path / "SST-Workbench"
    family = wb / "01_research" / "E_pipelines" / "E010_pklsa_parametric_knot_link_seed_atlas" / "E010-v0.3.1"
    out = family / "E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs"
    out.mkdir(parents=True)
    _write_json(out / "RELEASE.json", {
        "e010_version": "0.3.1",
        "publication_ready_geometry_layer": False,
        "full_campaign_gate_pass": False,
        "failed_topology_count": 1,
        "topology_count": 2227,
        "a001_a008_coverage_gate_pass": True,
        "identity_database_gate_pass": True,
        "source_contract_gate_pass": True,
        "canonical_identity_admission_gate_pass": True,
        "topology_database_ingest_gate_pass": True,
        "trefoil_poc_gate_pass": True,
    })
    _write_json(out / "FAILED_TOPOLOGIES.json", ["3_1"])
    _write_json(out / "CAMPAIGN_INDEX.json", {"passed": ["8_5"], "failed": ["3_1"]})

    for topo, lit_pass in [("8_5", True), ("3_1", False)]:
        q = out / "atlas" / topo / "qualification"
        q.mkdir(parents=True)
        _write_json(q / "PRODUCTION_GATE.json", {
            "topology_id": topo, "pass": lit_pass,
            "geometry_qualification_pass": lit_pass,
            "identity_database_pass": True,
        })
        _write_json(q / "summary.json", {
            "topology_id": topo, "qualified_carriers": 3,
            "qualification_gate_pass": lit_pass,
            "literature_hard_gate_pass": lit_pass,
            "literature_hard_gate_failures": [] if lit_pass else [f"F_{topo}"],
        })
        _write_csv(q / "source_matrix.csv", [
            {"source_family":"fremlin_fourier","catalog_ids":"A006","discovered":1,"qualified":1,"errors":0,"independence_groups":1,"provider_groups":1},
            {"source_family":"knotplot_fourier_series","catalog_ids":"A002","discovered":1,"qualified":1,"errors":0,"independence_groups":1,"provider_groups":1},
            {"source_family":"gilbert_ideal","catalog_ids":"A004","discovered":1,"qualified":1,"errors":0,"independence_groups":1,"provider_groups":1},
        ])
        _write_json(q / "source_independence_ledger.json", {
            "strict_upstream_independent_provider_count": 2,
            "entries": [
                {"carrier_id":f"F_{topo}","catalog_id":"A006","source_family":"fremlin_fourier","provider_group":"fremlin","independence_group":f"fremlin:{topo}","lineage_group":f"fremlin:{topo}","method_group":"fremlin-fourier","evidence_independence_class":"UPSTREAM_REFERENCE","contributes_new_upstream_provider":True},
                {"carrier_id":f"K_{topo}","catalog_id":"A002","source_family":"knotplot_fourier_series","provider_group":"fremlin","independence_group":f"fremlin:{topo}","lineage_group":f"fremlin:{topo}","method_group":"fourier-series","evidence_independence_class":"MIRROR_NOT_INDEPENDENT","parent_source_family":"fremlin_fourier"},
                {"carrier_id":f"G_{topo}","catalog_id":"A004","source_family":"gilbert_ideal","provider_group":"gilbert","independence_group":f"gilbert:{topo}","lineage_group":f"gilbert:{topo}","method_group":"gilbert-fourier-ideal","evidence_independence_class":"UPSTREAM_REFERENCE","contributes_new_upstream_provider":True},
            ]
        })
        statuses = {"Rop":"RESOLVED","Thi":"RESOLVED","Wr":"RESOLVED","ACN":"RESOLVED","dcsd":"RESOLVED","reach":"RESOLVED","kappa_max":"RESOLVED","kappa_rms":"RESOLVED","sigma_kappa":"RESOLVED","tau_rms":"RESOLVED"}
        pass_status = {"G1_isotopy_safe_sampling":"PASS","G2_writhe_quadratic_convergence":"PASS","G3_signed_frenet_chirality_completeness":"PASS"}
        fail_status = {"G1_isotopy_safe_sampling":"PASS","G2_writhe_quadratic_convergence":"FAIL","G3_signed_frenet_chirality_completeness":"PASS"}
        def row(cid, cat, fam, vals, is_failed=False):
            return {"carrier_id":cid,"catalog_id":cat,"source_family":fam,"finest_resolution":4096,"overall_convergence":"RESOLVED","observable_status":statuses,"finest_metrics":vals,"literature_hard_gate_pass":not is_failed,"literature_gate_status":fail_status if is_failed else pass_status}
        _write_json(q / "geometry_metrics.json", {"carriers": [
            row(f"F_{topo}","A006","fremlin_fourier",{"Rop":16.4,"Thi":0.061,"Wr":3.2,"ACN":5.1,"dcsd":0.07,"reach":0.0305,"kappa_max":40,"kappa_rms":12,"sigma_kappa":4,"tau_rms":20}, is_failed=not lit_pass),
            row(f"K_{topo}","A002","knotplot_fourier_series",{"Rop":16.4,"Thi":0.061,"Wr":3.2,"ACN":5.1,"dcsd":0.07,"reach":0.0305,"kappa_max":40,"kappa_rms":12,"sigma_kappa":4,"tau_rms":20}),
            row(f"G_{topo}","A004","gilbert_ideal",{"Rop":16.5,"Thi":0.060,"Wr":-3.25,"ACN":5.2,"dcsd":0.071,"reach":0.030,"kappa_max":41,"kappa_rms":12.2,"sigma_kappa":4.2,"tau_rms":21}),
        ]})
        _write_json(q / "convergence.json", {})
    return wb
