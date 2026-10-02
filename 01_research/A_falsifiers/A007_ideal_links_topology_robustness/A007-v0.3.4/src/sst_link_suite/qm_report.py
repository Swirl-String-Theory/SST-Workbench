from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from . import __version__


def write_qm_tables(results: list[dict], outdir: Path) -> pd.DataFrame:
    summary_rows, sector_rows, mode_rows = [], [], []
    symplectic_rows, holonomy_rows, topological_rows = [], [], []
    for result in results:
        best = result["best_sector"]
        labels = result["topological_quantum_labels"]
        spectral_guard = result.get("spectral_sampling_guard", {})
        spectral_source = result.get("spectral_source_audit", {})
        summary_rows.append({
            "link_id": result["link_id"],
            "common_name": result.get("common_name"),
            "conway": result["conway"],
            "components": labels["component_count"],
            "topology_sample_n": labels.get("topology_sample_n"),
            "source_active_mode_max": spectral_source.get("source_active_mode_max"),
            "spectral_cutoff_mode": spectral_guard.get("spectral_cutoff_mode"),
            "working_active_mode_max": spectral_guard.get("working_active_mode_max"),
            "qm_sample_n": spectral_guard.get("qm_sample_n"),
            "spectral_strict_nyquist_pass": spectral_guard.get("strict_nyquist_pass"),
            "spectral_nonlinear_sampling_pass": spectral_guard.get("nonlinear_geometry_sampling_pass"),
            "spectral_tail_contaminated_risk": spectral_source.get("spectral_tail_contaminated_risk"),
            "all_circulation_sectors": labels.get("all_circulation_sector_count", labels["independent_circulation_sector_count"]),
            "automorphism_order_proxy": labels["component_automorphism_order_proxy"],
            "automorphism_quotient_applied": labels.get("automorphism_quotient_applied", False),
            "higher_linking_required": labels["higher_linking_invariant_required"],
            "higher_linking_computed": labels.get("higher_linking_invariant_computed", False),
            "best_signs": best["sign_string"],
            "readiness_level": best["readiness"]["readiness_level"],
            "readiness_label": best["readiness"]["readiness_label"],
            "blocking_warnings": ";".join(best["readiness"].get("blocking_warnings", [])),
            "relative_equilibrium_score": best["relative_equilibrium_score"],
            "primary_gradient_norm": best["primary_gradient_norm"],
            "primary_gradient_cancellation_ratio": best.get("primary_gradient_cancellation_ratio"),
            "primary_negative_modes": best["primary_negative_modes"],
            "hessian_scheme": best["hessian_scheme"],
            "step_convergence_pass": best.get("step_convergence_pass"),
            "symplectic_rank": best["symplectic_rank"],
            "symplectic_dimension": best["symplectic_dimension"],
            "unstable_linear_modes": best["unstable_linear_modes"],
            "lowest_frequency_ratio_count": len(best["frequency_ratios"]),
            "quantization_ready_candidate": best["readiness"]["quantization_ready_candidate"],
        })
        topological_rows.append({
            "link_id": result["link_id"],
            "common_name": result.get("common_name"),
            "topology_sample_n": labels.get("topology_sample_n"),
            "source_active_mode_max": spectral_source.get("source_active_mode_max"),
            "spectral_cutoff_mode": spectral_guard.get("spectral_cutoff_mode"),
            "working_active_mode_max": spectral_guard.get("working_active_mode_max"),
            "qm_sample_n": spectral_guard.get("qm_sample_n"),
            "spectral_strict_nyquist_pass": spectral_guard.get("strict_nyquist_pass"),
            "spectral_nonlinear_sampling_pass": spectral_guard.get("nonlinear_geometry_sampling_pass"),
            "spectral_tail_contaminated_risk": spectral_source.get("spectral_tail_contaminated_risk"),
            "linking_integer_error": labels["linking_integer_error"],
            "integer_lock_pass": labels["integer_lock_pass"],
            "pair_linking_sector_resolved": labels.get("pair_linking_sector_resolved"),
            "linking_rank": labels["linking_form"]["rank"],
            "linking_nullity": labels["linking_form"]["nullity"],
            "linking_determinant": labels["linking_form"]["determinant"],
            "pair_linking_gcd": labels["linking_form"]["offdiagonal_gcd"],
            "total_abs_pair_linking_integer": labels["linking_form"]["total_abs_pair_linking_integer"],
            "all_pairwise_linking_zero": labels["linking_form"]["all_pairwise_linking_zero"],
            "higher_linking_required": labels["higher_linking_invariant_required"],
            "higher_linking_required_family": labels.get("higher_linking_required_family"),
            "higher_linking_computed": labels.get("higher_linking_invariant_computed", False),
            "automorphism_order_proxy": labels["component_automorphism_order_proxy"],
            "automorphism_quotient_applied": labels.get("automorphism_quotient_applied", False),
            "component_automorphisms_proxy_json": json.dumps(labels.get("component_automorphisms_proxy", []), separators=(",", ":")),
            "linking_matrix_json": json.dumps(labels["linking_matrix_rounded"], separators=(",", ":")),
        })
        for holonomy in result["normal_bundle_holonomy"]:
            holonomy_rows.append({"link_id": result["link_id"], **holonomy})
        for sector in result["sector_results"]:
            signs = sector["sign_string"]
            primary = sector["energy_closure"]["primary_profile"]
            finite = sector["energy_closure"]["finite_difference"]
            convergence = sector["energy_closure"].get("finite_difference_convergence", {})
            symp = sector["candidate_symplectic_form"]
            spectrum = sector["linearized_spectra"][primary]
            hessian = finite["hessians"][primary]
            gradient = finite["gradients"][primary]
            profile_diag = finite.get("profile_diagnostics", {}).get(primary, {})
            dynamics = sector["fixed_core_dynamics"]
            verdict = sector["readiness"]
            sector_rows.append({
                "link_id": result["link_id"],
                "common_name": result.get("common_name"),
                "signs": signs,
                "global_reversal_partner": "".join("+" if x > 0 else "-" for x in sector.get("global_reversal_partner", [])),
                "circulation_class": sector["circulation_class"],
                "primary_profile": primary,
                "normalization_mode": finite.get("normalization_mode"),
                "epsilon_D": sector["energy_closure"]["epsilon_D"],
                "relative_equilibrium_score": dynamics["relative_equilibrium_score"],
                "primary_gradient_norm": gradient["norm"],
                "primary_gradient_cancellation_ratio": profile_diag.get("gradient_cancellation_ratio"),
                "hessian_scheme": finite["hessian_scheme"],
                "step_convergence_pass": convergence.get("pass"),
                "step_gradient_relative_difference": convergence.get("gradient_relative_difference"),
                "step_hessian_relative_difference": convergence.get("hessian_frobenius_relative_difference"),
                "hessian_minimum_eigenvalue": hessian["minimum_eigenvalue"],
                "hessian_negative_modes": hessian["negative_mode_count"],
                "hessian_positive_gap": hessian["spectral_gap_positive"],
                "symplectic_rank": symp["rank"],
                "symplectic_dimension": symp["dimension"],
                "symplectic_full_rank": symp["full_rank"],
                "symplectic_antisymmetry_error": symp["antisymmetry_error"],
                "unstable_linear_modes": spectrum["unstable_mode_count"],
                "spectrally_stable_screen": spectrum.get("spectrally_stable_screen"),
                "spectrally_stable_claim": spectrum["spectrally_stable"],
                "stability_claim_eligible": spectrum.get("stability_claim_eligible"),
                "lowest_positive_frequency": spectrum["lowest_positive_frequency"],
                "readiness_level": verdict["readiness_level"],
                "readiness_label": verdict["readiness_label"],
                "blocking_warnings": ";".join(verdict.get("blocking_warnings", [])),
            })
            for profile, profile_spectrum in sector["linearized_spectra"].items():
                frequencies = profile_spectrum["positive_frequencies_dimensionless"]
                ratios = profile_spectrum["frequency_ratios_to_lowest"]
                for index, frequency in enumerate(frequencies):
                    mode_rows.append({
                        "link_id": result["link_id"], "signs": signs, "profile": profile,
                        "mode_index": index + 1, "frequency_dimensionless": frequency,
                        "frequency_ratio_to_lowest": ratios[index] if index < len(ratios) else np.nan,
                        "spectrally_stable_screen": profile_spectrum.get("spectrally_stable_screen"),
                        "spectrally_stable_claim": profile_spectrum["spectrally_stable"],
                        "stability_claim_eligible": profile_spectrum.get("stability_claim_eligible"),
                        "used_pseudoinverse": profile_spectrum["used_pseudoinverse"],
                    })
            symplectic_rows.append({
                "link_id": result["link_id"], "signs": signs,
                "dimension": symp["dimension"], "rank": symp["rank"], "nullity": symp["nullity"],
                "full_rank": symp["full_rank"], "antisymmetry_error": symp["antisymmetry_error"],
                "pfaffian_abs_proxy": symp["pfaffian_abs_proxy"],
                "singular_values_json": json.dumps(symp["singular_values"], separators=(",", ":")),
            })

    summary = pd.DataFrame(summary_rows).sort_values(
        ["readiness_level", "relative_equilibrium_score"], ascending=[False, True]
    )
    summary.to_csv(outdir / "qm_readiness_summary.csv", index=False)
    pd.DataFrame(topological_rows).to_csv(outdir / "topological_quantum_labels.csv", index=False)
    pd.DataFrame(sector_rows).to_csv(outdir / "sector_readiness.csv", index=False)
    pd.DataFrame(mode_rows).to_csv(outdir / "normal_modes.csv", index=False)
    pd.DataFrame(symplectic_rows).to_csv(outdir / "candidate_symplectic_forms.csv", index=False)
    pd.DataFrame(holonomy_rows).to_csv(outdir / "normal_bundle_holonomy.csv", index=False)
    return summary


def write_qm_plots(summary: pd.DataFrame, outdir: Path) -> None:
    plotdir = outdir / "plots"; plotdir.mkdir(exist_ok=True)
    ordered = summary.sort_values(["readiness_level", "relative_equilibrium_score"], ascending=[False, True])
    fig, ax = plt.subplots(figsize=(11, 6)); ax.bar(ordered["link_id"], ordered["readiness_level"])
    ax.set_ylabel("Sequential QM-readiness level (0–5)"); ax.tick_params(axis="x", rotation=60)
    fig.tight_layout(); fig.savefig(plotdir / "qm_readiness_levels.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(11, 6)); ax.scatter(summary["relative_equilibrium_score"], summary["primary_gradient_norm"])
    for _, row in summary.iterrows(): ax.annotate(row["link_id"], (row["relative_equilibrium_score"], row["primary_gradient_norm"]), fontsize=8)
    ax.set_xlabel("Fixed-core relative-equilibrium residual"); ax.set_ylabel("Fixed-reference reduced primary-energy gradient norm")
    fig.tight_layout(); fig.savefig(plotdir / "background_stationarity_map.png", dpi=180); plt.close(fig)


def write_qm_markdown_report(results: list[dict], summary: pd.DataFrame, outdir: Path, metadata: dict) -> None:
    columns = [
        "link_id", "common_name", "best_signs", "readiness_level", "readiness_label",
        "relative_equilibrium_score", "primary_gradient_norm", "primary_gradient_cancellation_ratio",
        "primary_negative_modes", "hessian_scheme", "symplectic_rank", "symplectic_dimension",
    ]
    top = summary.head(12); unresolved = summary[summary["higher_linking_required"]]
    lines = [
        f"# SST ideal links — QM-readiness campaign v{__version__}", "",
        f"- Links completed: **{len(results)}**", f"- Preset: **{metadata.get('preset', 'custom')}**",
        f"- Backend: **{metadata.get('backend', {}).get('backend', 'unknown')}**",
        f"- Input SHA-256: `{metadata.get('input_sha256', '')}`", "",
        "## Scientific boundary", "",
        "This campaign does not derive quantum mechanics. Quick/diagonal Hessians are screening-only. "
        "Pairwise-zero links require higher link invariants even when their catalog identity is known.", "",
        "## Highest-readiness candidates", "", top[columns].to_markdown(index=False), "",
        "## Pairwise-linking insufficiency flags", "",
        (unresolved[["link_id", "common_name", "components", "higher_linking_required", "higher_linking_computed"]].to_markdown(index=False)
         if len(unresolved) else "No pairwise-zero multi-component cases were flagged."), "",
        "## v0.3.4 interpretation rules", "",
        "- Topology uses an independent higher-resolution sampling grid.",
        "- Raw Fourier geometry is guarded against sub-Nyquist QM sampling; filtered presets are numerical regularizations only.",
        "- Bending/curvature uses analytic Fourier derivatives for source audits and FFT spectral derivatives for resolved perturbed curves.",
        "- Every 2^m circulation assignment is retained; candidate automorphisms do not quotient sectors.",
        "- Energy terms use preregistered fixed reference scales rather than per-sector baselines.",
        "- `spectrally_stable_claim=true` is possible only with a full off-diagonal Hessian.",
        "- L6a4 is catalogued as the Borromean rings; its Milnor triple invariant is not computed here.",
    ]
    (outdir / "QM_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
