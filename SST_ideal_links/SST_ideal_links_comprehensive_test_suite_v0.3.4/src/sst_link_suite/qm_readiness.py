from __future__ import annotations

import numpy as np

from . import __version__
from .fourier import sample_component
from .spectral import prepare_qm_link, spectral_tail_audit
from .geometry import component_geometry
from .topology import topology_summary
from .topological_labels import build_topological_label_ledger
from .perturbations import build_reduced_normal_basis
from .qm_energy import finite_difference_reduced_energy
from .symplectic import (
    candidate_filament_symplectic_matrix,
    symplectic_diagnostics,
    linearized_hamiltonian_spectrum,
    symplectic_kernel_quotient,
    quotient_linearized_spectrum,
)
from .stationary import stationary_newton_probe
from .biot_savart import analyze_sign_configurations
from .native_ext import BackendOptions


def _samples(link, n: int):
    return [sample_component(component, n) for component in link.components]


def _sector_key(signs) -> tuple[int, ...]:
    return tuple(int(x) for x in signs)


def _relative_difference(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(np.linalg.norm(np.asarray(b)), 1e-300))


def _step_convergence(primary: str, base: dict, refined: dict | None, cfg: dict) -> dict:
    if refined is None:
        return {
            "requested": False,
            "pass": None,
            "status": "Not requested for this preset.",
        }
    g0 = np.asarray(base["gradients"][primary]["vector"])
    g1 = np.asarray(refined["gradients"][primary]["vector"])
    h0 = np.asarray(base["hessians"][primary]["matrix"])
    h1 = np.asarray(refined["hessians"][primary]["matrix"])
    grad_rel = _relative_difference(g0, g1)
    hess_rel = _relative_difference(h0, h1)
    neg_agree = int(base["hessians"][primary]["negative_mode_count"]) == int(
        refined["hessians"][primary]["negative_mode_count"]
    )
    passed = (
        grad_rel <= float(cfg.get("max_step_gradient_relative_error", 0.15))
        and hess_rel <= float(cfg.get("max_step_hessian_relative_error", 0.25))
        and neg_agree
    )
    return {
        "requested": True,
        "coarse_step_D": float(base["step_D"]),
        "refined_step_D": float(refined["step_D"]),
        "gradient_relative_difference": grad_rel,
        "hessian_frobenius_relative_difference": hess_rel,
        "negative_mode_count_agreement": bool(neg_agree),
        "pass": bool(passed),
        "status": "[NUMERICAL] Central-difference step-halving comparison for the primary closure.",
    }


def _readiness_verdict(
    integer_lock: bool,
    higher_required: bool,
    higher_computed: bool,
    equilibrium_score: float,
    gradient_norm: float,
    cancellation_ratio: float,
    hessian_negative_modes: int,
    full_hessian: bool,
    step_convergence_pass: bool | None,
    symplectic_full_rank: bool,
    spectrum_stable: bool,
    cfg: dict,
    spectral_sampling_blocked: bool = False,
) -> dict:
    convergence_ok = (step_convergence_pass is not False)
    gates = {
        "Q1_pair_linking_sector_resolved": bool(integer_lock),
        "Q1b_higher_topology_resolved_if_required": bool((not higher_required) or higher_computed),
        "Q2_background_candidate": bool(
            equilibrium_score <= float(cfg.get("max_relative_equilibrium_score", 0.30))
            and gradient_norm <= float(cfg.get("max_reduced_gradient_norm", 1.0))
        ),
        "Q2b_closure_cancellation_not_extreme": bool(
            cancellation_ratio >= float(cfg.get("min_gradient_cancellation_ratio", 0.15))
        ),
        "Q3_nonnegative_converged_full_hessian": bool(
            full_hessian and hessian_negative_modes == 0 and convergence_ok
        ),
        "Q4_candidate_symplectic_full_rank": bool(symplectic_full_rank),
        "Q5_linearized_full_hessian_spectrum_stable": bool(full_hessian and spectrum_stable),
    }
    # Sequential readiness uses the main Q1-Q5 chain; Q1b/Q2b remain explicit blockers/warnings.
    ordered = [
        gates["Q1_pair_linking_sector_resolved"],
        gates["Q2_background_candidate"],
        gates["Q3_nonnegative_converged_full_hessian"],
        gates["Q4_candidate_symplectic_full_rank"],
        gates["Q5_linearized_full_hessian_spectrum_stable"],
    ]
    level = 0
    for passed in ordered:
        if not passed:
            break
        level += 1
    labels = {
        0: "not-ready",
        1: "pair-linking-sector-resolved",
        2: "classical-background-candidate",
        3: "quadratic-stability-candidate",
        4: "candidate-phase-space-ready",
        5: "quantization-readiness-candidate",
    }
    blockers = []
    if spectral_sampling_blocked:
        blockers.append("spectral_sampling_or_tail_gate_not_resolved")
    if higher_required and not higher_computed:
        blockers.append("higher_link_invariant_required_but_not_computed")
    if not gates["Q2b_closure_cancellation_not_extreme"]:
        blockers.append("primary_stationarity_depends_on_strong_term_cancellation")
    return {
        "gates": gates,
        "readiness_level": level,
        "readiness_label": labels[level],
        "blocking_warnings": blockers,
        "quantization_ready_candidate": bool(level == 5 and not blockers),
        "status": (
            "[RESEARCH TRACK] Passing these gates does not derive quantum mechanics. It identifies "
            "a reduced classical system for which a quantization attempt may be formulated."
        ),
    }


def analyze_qm_readiness(link, cfg: dict, backend_options: BackendOptions, backend_metadata: dict) -> dict:
    source_link = link
    spectral_source = spectral_tail_audit(source_link, cfg)
    link, spectral_sampling = prepare_qm_link(source_link, cfg)
    n = int(cfg.get("qm_sample_n", 96))
    topology_n = int(cfg.get("topology_sample_n", max(n, 256)))
    samples = _samples(link, n)
    # Topology is evaluated on the original source geometry unless an explicit topology cutoff is requested.
    topology_link = source_link
    topology_samples = _samples(topology_link, topology_n)
    geometry = [component_geometry(sample, int(cfg.get("curvature_refine_peaks", 8))) for sample in samples]
    topo = topology_summary(
        [sample.r for sample in topology_samples],
        bool(cfg.get("compute_writhe", False)),
        int(cfg.get("chunk", 128)),
        backend_options,
    )
    topo["sample_n"] = topology_n
    labels = build_topological_label_ledger(
        np.asarray(topo["linking_matrix"]),
        [row["numerical_length_D"] for row in geometry],
        link_id=link.link_id,
        integer_tolerance=float(cfg.get("linking_integer_tolerance", 1.5e-2)),
        relative_length_tolerance=float(cfg.get("component_symmetry_length_tolerance", 2.5e-3)),
        topology_sample_n=topology_n,
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
    normalization_mode = str(cfg.get("energy_normalization_mode", "diameter_dimensional"))
    normalization_reference = cfg.get("energy_normalization_reference")
    if normalization_mode == "diameter_dimensional":
        D = float(link.diameter)
        normalization_scales = {
            "length": D,
            "bending": 1.0 / max(D, 1e-300),
            "tube_repulsion": 1.0,
            "neumann": D,
        }
        normalization_reference = "D-dimensionalization: L/D, D*int(kappa^2 ds), dimensionless repulsion, E_N/D"
    else:
        normalization_scales = cfg.get("energy_normalization_scales")

    bs_rows, bs_diagnostics = analyze_sign_configurations(
        samples, [epsilon], backend_options,
        linking_matrix=np.asarray(topo["linking_matrix"]),
        local_skip_velocity=int(cfg.get("local_skip_velocity", 3)),
        local_skip_energy=int(cfg.get("local_skip_energy", 2)),
        self_exclusion_velocity_arc_D=cfg.get("self_exclusion_velocity_arc_D"),
        self_exclusion_energy_arc_D=cfg.get("self_exclusion_energy_arc_D"),
        diameter=float(link.diameter),
    )
    bs_by_signs = {_sector_key(row["signs"]): row for row in bs_rows}

    sectors = labels["circulation_sector_orbits"]
    if "max_independent_sectors" in cfg:
        max_sectors = int(cfg["max_independent_sectors"])
    else:
        max_sectors = int(cfg.get("max_circulation_sectors", len(sectors)))
    sectors = sectors[:max_sectors]
    sector_results = []
    geometric_derivatives = None
    step = float(cfg.get("finite_difference_step_D", 2.0e-3))
    refine_step = cfg.get("finite_difference_refined_step_D")
    for orbit in sectors:
        signs = np.asarray(orbit["representative"], dtype=float)
        reduced, geometric_derivatives = finite_difference_reduced_energy(
            samples, basis, signs, link.diameter, epsilon, backend_options,
            step=step,
            profiles=profiles,
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
            repulsion_softness=float(cfg.get("repulsion_softness_D", 0.04)),
            repulsion_margin=float(cfg.get("repulsion_margin", 0.0)),
            geometric_derivatives=geometric_derivatives,
            self_exclusion_energy_arc_D=cfg.get("self_exclusion_energy_arc_D"),
            compute_offdiagonal=bool(cfg.get("hessian_offdiagonal", True)),
            normalization_scales=normalization_scales,
            normalization_mode=normalization_mode,
            normalization_reference=normalization_reference,
            derivative_method=str(cfg.get("geometric_derivative_method", "spectral_fft")),
        )
        refined = None
        if refine_step is not None:
            refined, _ = finite_difference_reduced_energy(
                samples, basis, signs, link.diameter, epsilon, backend_options,
                step=float(refine_step),
                profiles=profiles,
                local_skip_energy=int(cfg.get("local_skip_energy", 2)),
                repulsion_softness=float(cfg.get("repulsion_softness_D", 0.04)),
                repulsion_margin=float(cfg.get("repulsion_margin", 0.0)),
                geometric_derivatives=None,
                self_exclusion_energy_arc_D=cfg.get("self_exclusion_energy_arc_D"),
                compute_offdiagonal=bool(cfg.get("hessian_offdiagonal", True)),
                normalization_scales=normalization_scales,
                normalization_mode=normalization_mode,
                normalization_reference=normalization_reference,
            )
        convergence = _step_convergence(primary_profile, reduced, refined, cfg)
        omega = candidate_filament_symplectic_matrix(samples, basis, signs)
        omega_diag = symplectic_diagnostics(
            omega, rank_tolerance=float(cfg.get("symplectic_rank_tolerance", 1e-8))
        )
        kernel_diag = symplectic_kernel_quotient(
            omega, metadata=basis.metadata,
            rank_tolerance=float(cfg.get("symplectic_rank_tolerance", 1e-8)),
        )
        spectra = {}
        quotient_spectra = {}
        for profile_name in profiles:
            hessian = np.asarray(reduced["hessians"][profile_name]["matrix"])
            spectra[profile_name] = linearized_hamiltonian_spectrum(
                omega, hessian,
                rank_tolerance=float(cfg.get("symplectic_rank_tolerance", 1e-8)),
                stability_tolerance=float(cfg.get("spectrum_stability_tolerance", 1e-6)),
                hessian_scheme=str(reduced["hessian_scheme"]),
            )
            if reduced.get("hessian_scheme") == "full-central":
                quotient_spectra[profile_name] = quotient_linearized_spectrum(
                    omega, hessian,
                    rank_tolerance=float(cfg.get("symplectic_rank_tolerance", 1e-8)),
                    stability_tolerance=float(cfg.get("spectrum_stability_tolerance", 1e-6)),
                )
        primary_hessian = reduced["hessians"][primary_profile]
        primary_gradient = reduced["gradients"][primary_profile]
        primary_diag = reduced["profile_diagnostics"][primary_profile]
        primary_spectrum = spectra[primary_profile]
        baseline_dynamics = bs_by_signs[_sector_key(signs)]
        verdict = _readiness_verdict(
            labels["integer_lock_pass"],
            labels["higher_linking_invariant_required"],
            labels["higher_linking_invariant_computed"],
            float(baseline_dynamics["relative_equilibrium_score"]),
            float(primary_gradient["norm"]),
            float(primary_diag["gradient_cancellation_ratio"]),
            int(primary_hessian["negative_mode_count"]),
            bool(reduced.get("hessian_scheme") == "full-central"),
            convergence.get("pass"),
            bool(omega_diag["full_rank"]),
            bool(primary_spectrum["spectrally_stable"]),
            cfg,
            spectral_sampling_blocked=bool(
                spectral_sampling["readiness_blocked"]
                or spectral_source["spectral_tail_contaminated_risk"]
                or spectral_sampling.get("spectral_cutoff_mode") is not None
            ),
        )
        sector_results.append({
            "signs": [int(x) for x in signs],
            "sign_string": "".join("+" if x > 0 else "-" for x in signs),
            "orbit_degeneracy": int(orbit["degeneracy"]),
            "orbit_members": orbit["members"],
            "global_reversal_partner": orbit.get("global_reversal_partner"),
            "circulation_class": orbit["circulation_class"],
            "fixed_core_dynamics": baseline_dynamics,
            "energy_closure": {
                "primary_profile": primary_profile,
                "profiles": profiles,
                "epsilon_D": epsilon,
                "finite_difference": reduced,
                "finite_difference_refined": refined,
                "finite_difference_convergence": convergence,
                "status": (
                    "[DIAGNOSTIC/RESEARCH TRACK] D-dimensionalized length, bending, tube-repulsion "
                    "and regularized Neumann closures with fixed physical self-exclusion arc. Profile weights remain assumptions."
                ),
            },
            "candidate_symplectic_form": omega_diag,
            "symplectic_kernel_quotient": kernel_diag,
            "linearized_spectra": spectra,
            "quotient_linearized_spectra": quotient_spectra,
            "readiness": verdict,
        })

    best = sorted(
        sector_results,
        key=lambda row: (
            -row["readiness"]["readiness_level"],
            len(row["readiness"]["blocking_warnings"]),
            row["fixed_core_dynamics"]["relative_equilibrium_score"],
            row["energy_closure"]["finite_difference"]["gradients"][primary_profile]["norm"],
        ),
    )[0]
    best_finite = best["energy_closure"]["finite_difference"]
    stationary_probe = {"requested": False, "status": "Disabled for this preset."}
    if bool(cfg.get("stationary_newton_probe", False)) and best_finite.get("hessian_scheme") == "full-central":
        best_signs = np.asarray(best["signs"], dtype=float)
        stationary_probe = stationary_newton_probe(
            samples, basis, best_signs, float(link.diameter), epsilon, backend_options,
            profiles[primary_profile], normalization_scales,
            np.asarray(best_finite["gradients"][primary_profile]["vector"], dtype=float),
            np.asarray(best_finite["hessians"][primary_profile]["matrix"], dtype=float),
            cfg,
        )
    return {
        "suite_version": __version__,
        "link_id": source_link.link_id,
        "common_name": labels.get("common_name"),
        "spectral_source_audit": spectral_source,
        "spectral_sampling_guard": spectral_sampling,
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
            "status": "[GEOMETRIC] Low-harmonic normal deformations with translation/rotation gauge removed.",
        },
        "normal_bundle_holonomy": holonomies,
        "biot_savart_diagnostics": bs_diagnostics,
        "stationary_newton_probe_best_sector": stationary_probe,
        "sector_results": sector_results,
        "best_sector": {
            "signs": best["signs"],
            "sign_string": best["sign_string"],
            "readiness": best["readiness"],
            "relative_equilibrium_score": best["fixed_core_dynamics"]["relative_equilibrium_score"],
            "primary_gradient_norm": best_finite["gradients"][primary_profile]["norm"],
            "primary_gradient_cancellation_ratio": best_finite["profile_diagnostics"][primary_profile]["gradient_cancellation_ratio"],
            "primary_negative_modes": best_finite["hessians"][primary_profile]["negative_mode_count"],
            "hessian_scheme": best_finite["hessian_scheme"],
            "step_convergence_pass": best["energy_closure"]["finite_difference_convergence"].get("pass"),
            "symplectic_rank": best["candidate_symplectic_form"]["rank"],
            "symplectic_dimension": best["candidate_symplectic_form"]["dimension"],
            "unstable_linear_modes": best["linearized_spectra"][primary_profile]["unstable_mode_count"],
            "frequency_ratios": best["linearized_spectra"][primary_profile]["frequency_ratios_to_lowest"],
            "symplectic_nullity": best["symplectic_kernel_quotient"]["nullity"],
            "quotient_dimension": best["symplectic_kernel_quotient"]["quotient_dimension"],
            "stationary_probe_gradient_norm": (
                stationary_probe.get("best", {}).get("gradient_norm") if stationary_probe.get("requested") else None
            ),
        },
        "interpretation_boundary": (
            "This ledger tests QM-readiness of a reduced classical link model. v0.3.4 adds analytic-Fourier/spectral "
            "derivative guards, fixed physical self-exclusion arcs and D-dimensionalized energy terms. A separate N- and spectral-cutoff audit is still "
            "required before closure comparisons. It does not derive Born probabilities, Hilbert space, hbar, "
            "operator commutators, or empirical particle spectra."
        ),
    }
