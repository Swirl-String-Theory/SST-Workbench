from __future__ import annotations

import numpy as np

from .fourier import sample_component
from .geometry import component_geometry
from .topology import topology_summary
from .topological_labels import build_topological_label_ledger
from .perturbations import build_reduced_normal_basis
from .qm_energy import finite_difference_reduced_energy
from .symplectic import candidate_filament_symplectic_matrix, symplectic_diagnostics, linearized_hamiltonian_spectrum
from .biot_savart import analyze_sign_configurations
from .native_ext import BackendOptions


def _samples(link, n: int):
    return [sample_component(component, n) for component in link.components]


def _sector_key(signs) -> tuple[int, ...]:
    return tuple(int(x) for x in signs)


def _readiness_verdict(
    integer_lock: bool,
    equilibrium_score: float,
    gradient_norm: float,
    hessian_negative_modes: int,
    full_hessian: bool,
    symplectic_full_rank: bool,
    spectrum_stable: bool,
    cfg: dict,
) -> dict:
    gates = {
        "Q1_discrete_sector_labels": bool(integer_lock),
        "Q2_background_candidate": bool(
            equilibrium_score <= float(cfg.get("max_relative_equilibrium_score", 0.30))
            and gradient_norm <= float(cfg.get("max_reduced_gradient_norm", 1.0))
        ),
        "Q3_nonnegative_reduced_hessian": bool(full_hessian and hessian_negative_modes == 0),
        "Q4_candidate_symplectic_full_rank": bool(symplectic_full_rank),
        "Q5_linearized_spectrum_stable": bool(spectrum_stable),
    }
    ordered = list(gates.values())
    level = 0
    for passed in ordered:
        if not passed:
            break
        level += 1
    labels = {
        0: "not-ready",
        1: "topological-sector-ready",
        2: "classical-background-candidate",
        3: "quadratic-stability-candidate",
        4: "candidate-phase-space-ready",
        5: "quantization-readiness-candidate",
    }
    return {
        "gates": gates,
        "readiness_level": level,
        "readiness_label": labels[level],
        "quantization_ready_candidate": bool(level == 5),
        "status": (
            "[RESEARCH TRACK] Passing these gates does not derive quantum mechanics. It identifies "
            "a classical reduced system for which canonical/geometric quantization can be attempted."
        ),
    }


def analyze_qm_readiness(link, cfg: dict, backend_options: BackendOptions, backend_metadata: dict) -> dict:
    n = int(cfg.get("qm_sample_n", 96))
    samples = _samples(link, n)
    geometry = [component_geometry(sample, int(cfg.get("curvature_refine_peaks", 8))) for sample in samples]
    topo = topology_summary(
        [sample.r for sample in samples],
        bool(cfg.get("compute_writhe", False)),
        int(cfg.get("chunk", 128)),
        backend_options,
    )
    labels = build_topological_label_ledger(
        np.asarray(topo["linking_matrix"]),
        [row["numerical_length_D"] for row in geometry],
        integer_tolerance=float(cfg.get("linking_integer_tolerance", 1.5e-2)),
        relative_length_tolerance=float(cfg.get("component_symmetry_length_tolerance", 2.5e-3)),
    )
    basis, holonomies = build_reduced_normal_basis(
        samples,
        mode_max=int(cfg.get("mode_max", 1)),
        remove_rigid_gauge=bool(cfg.get("remove_rigid_gauge", True)),
        basis_tolerance=float(cfg.get("basis_tolerance", 1e-9)),
    )
    profiles = cfg.get("energy_profiles", {
        "geometric_tube": {"length": 1.0, "bending": 1.0, "tube_repulsion": 1.0, "neumann": 0.0},
        "hydrodynamic_proxy": {"length": 0.0, "bending": 0.0, "tube_repulsion": 0.0, "neumann": 1.0},
        "hybrid_equal_normalized": {"length": 0.25, "bending": 0.25, "tube_repulsion": 0.25, "neumann": 0.25},
    })
    primary_profile = str(cfg.get("primary_energy_profile", "hybrid_equal_normalized"))
    if primary_profile not in profiles:
        raise KeyError(f"primary_energy_profile={primary_profile!r} is not in energy_profiles")
    epsilon = float(cfg.get("qm_epsilon_D", 0.10))

    # Baseline classical relative-equilibrium scores for all signs at the fixed finite-core value.
    bs_rows, bs_diagnostics = analyze_sign_configurations(
        samples, [epsilon], backend_options,
        linking_matrix=np.asarray(topo["linking_matrix"]),
        local_skip_velocity=int(cfg.get("local_skip_velocity", 3)),
        local_skip_energy=int(cfg.get("local_skip_energy", 2)),
    )
    bs_by_signs = {_sector_key(row["signs"]): row for row in bs_rows}

    sector_orbits = labels["circulation_sector_orbits"]
    max_sectors = int(cfg.get("max_independent_sectors", len(sector_orbits)))
    sector_orbits = sector_orbits[:max_sectors]
    sector_results = []
    geometric_derivatives = None
    for orbit in sector_orbits:
        signs = np.asarray(orbit["representative"], dtype=float)
        reduced, geometric_derivatives = finite_difference_reduced_energy(
            samples, basis, signs, link.diameter, epsilon, backend_options,
            step=float(cfg.get("finite_difference_step_D", 2.0e-3)),
            profiles=profiles,
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
            repulsion_softness=float(cfg.get("repulsion_softness_D", 0.04)),
            repulsion_margin=float(cfg.get("repulsion_margin", 0.0)),
            geometric_derivatives=geometric_derivatives,
            compute_offdiagonal=bool(cfg.get("hessian_offdiagonal", True)),
        )
        omega = candidate_filament_symplectic_matrix(samples, basis, signs)
        omega_diag = symplectic_diagnostics(
            omega, rank_tolerance=float(cfg.get("symplectic_rank_tolerance", 1e-8))
        )
        spectra = {}
        for profile_name in profiles:
            hessian = np.asarray(reduced["hessians"][profile_name]["matrix"])
            spectra[profile_name] = linearized_hamiltonian_spectrum(
                omega, hessian,
                rank_tolerance=float(cfg.get("symplectic_rank_tolerance", 1e-8)),
                stability_tolerance=float(cfg.get("spectrum_stability_tolerance", 1e-6)),
            )
        primary_hessian = reduced["hessians"][primary_profile]
        primary_gradient = reduced["gradients"][primary_profile]
        primary_spectrum = spectra[primary_profile]
        baseline_dynamics = bs_by_signs[_sector_key(signs)]
        verdict = _readiness_verdict(
            labels["integer_lock_pass"],
            float(baseline_dynamics["relative_equilibrium_score"]),
            float(primary_gradient["norm"]),
            int(primary_hessian["negative_mode_count"]),
            bool(reduced.get("hessian_scheme") == "full-central"),
            bool(omega_diag["full_rank"]),
            bool(primary_spectrum["spectrally_stable"]),
            cfg,
        )
        sector_results.append({
            "signs": [int(x) for x in signs],
            "sign_string": "".join("+" if x > 0 else "-" for x in signs),
            "orbit_degeneracy": int(orbit["degeneracy"]),
            "orbit_members": orbit["members"],
            "circulation_class": orbit["circulation_class"],
            "fixed_core_dynamics": baseline_dynamics,
            "energy_closure": {
                "primary_profile": primary_profile,
                "profiles": profiles,
                "epsilon_D": epsilon,
                "finite_difference": reduced,
                "status": (
                    "[DIAGNOSTIC/RESEARCH TRACK] Termwise normalized line, bending, tube-repulsion "
                    "and regularized Neumann closures. Profile weights are explicit assumptions."
                ),
            },
            "candidate_symplectic_form": omega_diag,
            "linearized_spectra": spectra,
            "readiness": verdict,
        })

    best = sorted(
        sector_results,
        key=lambda row: (
            -row["readiness"]["readiness_level"],
            row["fixed_core_dynamics"]["relative_equilibrium_score"],
            row["energy_closure"]["finite_difference"]["gradients"][primary_profile]["norm"],
        ),
    )[0]
    return {
        "suite_version": "0.3.0",
        "link_id": link.link_id,
        "conway": link.conway,
        "diameter_D": link.diameter,
        "backend": backend_metadata,
        "qm_config": cfg,
        "geometry_baseline": geometry,
        "topology_baseline": topo,
        "topological_quantum_labels": labels,
        "reduced_basis": {
            "dimension": int(basis.vectors.shape[0]),
            "mode_max": int(cfg.get("mode_max", 1)),
            "gauge_rank_removed": int(basis.gauge_rank),
            "metadata": list(basis.metadata),
            "discarded_small_vector_count": len(basis.discarded_singular_values),
            "status": (
                "[GEOMETRIC] Low-harmonic normal deformations with translation/rotation gauge removed."
            ),
        },
        "normal_bundle_holonomy": holonomies,
        "biot_savart_diagnostics": bs_diagnostics,
        "sector_results": sector_results,
        "best_sector": {
            "signs": best["signs"],
            "sign_string": best["sign_string"],
            "readiness": best["readiness"],
            "relative_equilibrium_score": best["fixed_core_dynamics"]["relative_equilibrium_score"],
            "primary_gradient_norm": best["energy_closure"]["finite_difference"]["gradients"][primary_profile]["norm"],
            "primary_negative_modes": best["energy_closure"]["finite_difference"]["hessians"][primary_profile]["negative_mode_count"],
            "hessian_scheme": best["energy_closure"]["finite_difference"]["hessian_scheme"],
            "symplectic_rank": best["candidate_symplectic_form"]["rank"],
            "symplectic_dimension": best["candidate_symplectic_form"]["dimension"],
            "unstable_linear_modes": best["linearized_spectra"][primary_profile]["unstable_mode_count"],
            "frequency_ratios": best["linearized_spectra"][primary_profile]["frequency_ratios_to_lowest"],
        },
        "interpretation_boundary": (
            "This ledger tests QM-readiness of a reduced classical link model. It does not derive Born "
            "probabilities, Hilbert space, hbar, operator commutators, or empirical particle spectra."
        ),
    }
