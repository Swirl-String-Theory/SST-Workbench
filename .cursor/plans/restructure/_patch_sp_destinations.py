"""Patch SP06/SP07 destinations to match 01/02/03 freeze."""
from pathlib import Path

PLAN = Path(__file__).resolve().parent

REPLACEMENTS = [
    # SP07 data / pipelines
    ("03_data/A_knots/A001_knotplot_relaxed/", "03_data/A_knots/04_knotplot/"),
    ("03_data/A_knots/A002_knotplot_fourier_series/", "03_data/A_knots/02_fourier/knotplot_legacy/"),
    ("03_data/A_knots/A003_knotplot_qhp/", "03_data/D_generated/qhp/"),
    ("03_data\\A_knots\\A001_knotplot_relaxed\\", "03_data\\A_knots\\04_knotplot\\"),
    ("01_research/E_pipelines/E004_knotplot_trefoil_balance_point/", "01_research/E_pipelines/E004_trefoil_balance_point_campaign/"),
    ("01_research/E_pipelines/E005_knotplot_trefoil_seed/", "01_research/E_pipelines/E003_knotplot_trefoil_seed_campaign/"),
    ("01_research/E_pipelines/E006_knotplot_multidynamics_relaxation_matrix/", "01_research/E_pipelines/E002_knotplot_multidynamics_relaxation_matrix/"),
    (".../E008_knotplot_command_certification/", "01_research/D_benchmarks/D008_knotplot_missingparameter_certification/"),
    ("01_research/E_pipelines/E008_knotplot_command_certification/", "01_research/D_benchmarks/D008_knotplot_missingparameter_certification/"),
    ("01_research/E_pipelines/E007_knotplot_dynamics_parameter_atlas/", "01_research/D_benchmarks/D009_knotplot_parameter_atlas/"),
    ("01_research/E_pipelines/E009_knotplot_multitopology_qhp_sweep/", "01_research/E_pipelines/E006_knotplot_multitopology_qhp_sweep/"),
    # SP06
    ("R/D/D002_hopf_benchmark_packet/", "R/D/D005_hopf_benchmark/"),
    ("R/D/D003_hopf_cpp_pybind/", "R/D/D005_hopf_benchmark/"),
    ("R/B/A001_route_a_parallel_derivation_falsification/", "R/A/A001_route_a_parallel_derivation_falsification/"),
    ("R/B/B003_planck_routes_a_to_d_equivalence/", "R/B/B002_planck_routes_a_to_d/"),
    ("R/B/B004_planck_routes_v3_preregistered/", "R/B/B002_planck_routes_a_to_d/"),
    ("R/B/B005_horn_dirichlet_bem/", "R/B/B003_horn_bem/"),
    ("R/B/B006_horn_neumann_bem/", "R/B/B003_horn_bem/"),
    ("R/F/F005_route_i_relative_entropy/", "R/F/F002_route_i_relative_entropy_poc/"),
    ("R/F/F004_route_i_heat_guard_patch/", "R/F/F002_route_i_relative_entropy_poc/variants/"),
    ("R/F/F007_taxonomy_starter/", "R/F/F004_taxonomy_starter/"),
    ("R/F/F008_sycl_probes/", "04_tools/D_compute/sycl_probes/"),
    ("04_tools/A_geometry/A003_knotplot_qhp_sweep_generator/", "01_research/E_pipelines/E007_knotplot_qhp_sweep_generator/"),
    ("R/A/A034_qhp_stability_landscape/", "R/A/A034_qhp_stability_landscape/"),  # keep
    # soft delete wording leftovers
    ("pending_delete/", "DELETE/"),
]


def main() -> None:
    for name in ("SP06_container_splits.plan.md", "SP07_knotplot_refactor.plan.md", "SP05_clean_family_moves.plan.md", "SP04_low_risk_moves.plan.md"):
        path = PLAN / name
        if not path.exists():
            continue
        t = path.read_text(encoding="utf-8")
        nt = t
        for a, b in REPLACEMENTS:
            nt = nt.replace(a, b)
        if nt != t:
            path.write_text(nt, encoding="utf-8")
            print("patched", name)
        else:
            print("no change", name)


if __name__ == "__main__":
    main()
