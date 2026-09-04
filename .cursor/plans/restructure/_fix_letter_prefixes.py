"""Fix letter-prefix mismatches left by slug-only ID remapping."""
from __future__ import annotations

import csv
import re
from pathlib import Path

PLAN = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PATH_MAP = ROOT / "10_docs" / "migration" / "path_map.csv"

# (wrong_fragment, correct_fragment)
FIXES = [
    # domain letter vs catalog letter mismatches
    ("R/B/A001_route_a_parallel_derivation_falsification", "R/A/A001_route_a_parallel_derivation_falsification"),
    ("R/F/A002_nonfit_prediction_routes_control", "R/A/A002_nonfit_prediction_routes_control"),
    ("R/F/A003_dark_knot_rayleigh", "R/A/A003_dark_knot_rayleigh"),
    ("R/D/A007_ideal_links_topology_robustness", "R/A/A007_ideal_links_topology_robustness"),
    ("R/A/D004_minimal_falsification_harness", "R/D/D004_minimal_falsification_harness"),
    ("R/A/D005_sutcliffe_hss_feasibility_gate", "R/D/D005_sutcliffe_hss_feasibility_gate"),
    ("01_research/B_closures/A001_route_a_parallel_derivation_falsification", "01_research/A_falsifiers/A001_route_a_parallel_derivation_falsification"),
    ("01_research/F_exploratory/A002_nonfit_prediction_routes_control", "01_research/A_falsifiers/A002_nonfit_prediction_routes_control"),
    ("01_research/F_exploratory/A003_dark_knot_rayleigh", "01_research/A_falsifiers/A003_dark_knot_rayleigh"),
    ("01_research/D_benchmarks/A007_ideal_links_topology_robustness", "01_research/A_falsifiers/A007_ideal_links_topology_robustness"),
    ("01_research/A_falsifiers/D004_minimal_falsification_harness", "01_research/D_benchmarks/D004_minimal_falsification_harness"),
    ("01_research/A_falsifiers/D005_sutcliffe_hss_feasibility_gate", "01_research/D_benchmarks/D005_sutcliffe_hss_feasibility_gate"),
    # F renumbers that were missed in some docs
    ("R/F/F007_route_i_relative_entropy", "R/F/F005_route_i_relative_entropy"),
    ("R/F/F008_contra_swirl_bridge", "R/F/F006_contra_swirl_bridge"),
    ("R/F/F009_taxonomy_starter", "R/F/F007_taxonomy_starter"),
    ("R/F/F010_sycl_probes", "R/F/F008_sycl_probes"),
    ("01_research/F_exploratory/F007_route_i_relative_entropy", "01_research/F_exploratory/F005_route_i_relative_entropy"),
    ("01_research/F_exploratory/F008_contra_swirl_bridge", "01_research/F_exploratory/F006_contra_swirl_bridge"),
    ("01_research/F_exploratory/F009_taxonomy_starter", "01_research/F_exploratory/F007_taxonomy_starter"),
    ("01_research/F_exploratory/F010_sycl_probes", "01_research/F_exploratory/F008_sycl_probes"),
    # B renumbers
    ("R/B/B006_horn_dirichlet_bem", "R/B/B005_horn_dirichlet_bem"),
    ("R/B/B007_horn_neumann_bem", "R/B/B006_horn_neumann_bem"),
    ("R/B/B008_ssdl_audit", "R/B/B007_ssdl_audit"),
    ("01_research/B_closures/B006_horn_dirichlet_bem", "01_research/B_closures/B005_horn_dirichlet_bem"),
    ("01_research/B_closures/B007_horn_neumann_bem", "01_research/B_closures/B006_horn_neumann_bem"),
    ("01_research/B_closures/B008_ssdl_audit", "01_research/B_closures/B007_ssdl_audit"),
    # D hopf cpp
    ("R/D/D004_hopf_cpp_pybind", "R/D/D003_hopf_cpp_pybind"),
    ("01_research/D_benchmarks/D004_hopf_cpp_pybind", "01_research/D_benchmarks/D003_hopf_cpp_pybind"),
    # prose leftovers
    ("F009_taxonomy_starter", "F007_taxonomy_starter"),
    ("F010_sycl_probes", "F008_sycl_probes"),
]


def apply_text(text: str) -> str:
    for old, new in sorted(FIXES, key=lambda kv: -len(kv[0])):
        text = text.replace(old, new)
    return text


def main() -> None:
    for path in list(PLAN.glob("*.plan.md")) + list(PLAN.glob("CATALOG_v0.1.md")) + list(
        PLAN.glob("README.md")
    ):
        t = path.read_text(encoding="utf-8")
        nt = apply_text(t)
        if nt != t:
            path.write_text(nt, encoding="utf-8")
            print("fixed", path.name)

    rows = list(csv.DictReader(PATH_MAP.open(encoding="utf-8")))
    fields = list(rows[0].keys())
    changed = 0
    for row in rows:
        before = dict(row)
        row["new_path"] = apply_text(row["new_path"])
        row["note"] = apply_text(row.get("note") or "")
        # fix letter/domain for known moves
        if "A002_nonfit" in row["new_path"] or row["old_path"].find("nonfit") >= 0:
            if "A002" in row["new_path"]:
                row["domain"] = "01_research"
                row["letter"] = "A_falsifiers"
                row["catalog_id"] = "A002"
                row["new_path"] = (
                    "01_research/A_falsifiers/A002_nonfit_prediction_routes_control"
                )
        if row != before:
            changed += 1
    with PATH_MAP.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("path_map rows touched", changed)


if __name__ == "__main__":
    main()
