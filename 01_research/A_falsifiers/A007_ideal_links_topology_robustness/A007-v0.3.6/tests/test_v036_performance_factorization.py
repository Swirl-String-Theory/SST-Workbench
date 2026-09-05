from pathlib import Path
import json
import numpy as np

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.perturbations import build_reduced_normal_basis
from sst_link_suite.qm_energy import (
    assemble_reduced_energy,
    compute_geometric_reduced_derivatives,
    compute_neumann_coupling_reduced_derivatives,
    contract_neumann_coupling_derivatives,
    finite_difference_reduced_energy,
    tube_repulsion_energy,
)
from sst_link_suite.qm_readiness import analyze_qm_readiness
from sst_link_suite.native_ext import BackendOptions, backend_status

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data" / "idealLinks.txt"
PROFILES = {
    "hybrid": {"length": 0.25, "bending": 0.25, "tube_repulsion": 0.25, "neumann": 0.25}
}


def _fixture():
    link = parse_ideal_links(DATA)["L6a4"]
    samples = [sample_component(c, 24) for c in link.components]
    basis, _ = build_reduced_normal_basis(samples, mode_max=0)
    return link, samples, basis


def test_cached_coupling_derivatives_match_direct_sector_path():
    link, samples, basis = _fixture()
    options = BackendOptions(force_python=True)
    step = 0.004
    signs = np.array([-1.0, 1.0, -1.0])
    coupling = compute_neumann_coupling_reduced_derivatives(
        samples, basis, 0.1, options, step, compute_offdiagonal=True,
        self_exclusion_energy_arc=0.20 * link.diameter,
    )
    cached = contract_neumann_coupling_derivatives(coupling, signs)
    direct, _ = finite_difference_reduced_energy(
        samples, basis, signs, link.diameter, 0.1, options, step, PROFILES,
        self_exclusion_energy_arc_D=0.20,
    )
    assert np.isclose(cached["baseline"], direct["baseline_raw"]["neumann"], rtol=0, atol=1e-12)
    assert np.allclose(cached["gradient"], direct["term_gradient_raw"]["neumann"], rtol=1e-11, atol=1e-11)
    assert np.allclose(cached["hessian"], direct["term_hessian_raw"]["neumann"], rtol=1e-9, atol=1e-9)


def test_factorized_assembly_matches_naive_energy_ledger():
    link, samples, basis = _fixture()
    options = BackendOptions(force_python=True)
    step = 0.004
    signs = np.array([-1.0, -1.0, 1.0])
    geometric = compute_geometric_reduced_derivatives(
        samples, basis, link.diameter, step, compute_offdiagonal=True,
        backend_options=options,
    )
    coupling = compute_neumann_coupling_reduced_derivatives(
        samples, basis, 0.1, options, step, compute_offdiagonal=True,
        self_exclusion_energy_arc=0.20 * link.diameter,
    )
    optimized = assemble_reduced_energy(
        geometric, contract_neumann_coupling_derivatives(coupling, signs), PROFILES
    )
    naive, _ = finite_difference_reduced_energy(
        samples, basis, signs, link.diameter, 0.1, options, step, PROFILES,
        self_exclusion_energy_arc_D=0.20,
    )
    assert np.allclose(
        optimized["gradients"]["hybrid"]["vector"],
        naive["gradients"]["hybrid"]["vector"], rtol=1e-10, atol=1e-10,
    )
    assert np.allclose(
        optimized["hessians"]["hybrid"]["matrix"],
        naive["hessians"]["hybrid"]["matrix"], rtol=1e-9, atol=1e-9,
    )


def test_native_tube_repulsion_parity():
    link = parse_ideal_links(DATA)["L2a1"]
    curves = [sample_component(c, 48).r for c in link.components]
    reference = tube_repulsion_energy(curves, link.diameter, 0.04, 0.0, 0.035, None)
    native = tube_repulsion_energy(
        curves, link.diameter, 0.04, 0.0, 0.035,
        BackendOptions(require_native=True, skip_build=False),
    )
    assert np.isclose(native, reference, rtol=5e-13, atol=5e-13)


def test_qm_readiness_reports_sector_reuse():
    cfg = json.loads((ROOT / "configs" / "qm_quick.json").read_text())
    cfg["qm_sample_n"] = 24
    cfg["mode_max"] = 0
    cfg["max_independent_sectors"] = 2
    cfg["plots"] = False
    options = BackendOptions(force_python=True)
    result = analyze_qm_readiness(
        parse_ideal_links(DATA)["L2a1"], cfg, options, backend_status(options)
    )
    perf = result["performance_ledger"]
    assert perf["physics_changed"] is False
    assert perf["sector_count"] == 2
    assert perf["neumann_coupling_evaluations_v0351_equivalent"] == 2 * perf["neumann_coupling_evaluations_optimized"]
