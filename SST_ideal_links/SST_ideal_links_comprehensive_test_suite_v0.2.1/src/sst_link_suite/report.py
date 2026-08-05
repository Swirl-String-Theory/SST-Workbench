from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _flatten_rows(results):
    return [{"link_id": row["link_id"], "conway": row["conway"], **row["features"]} for row in results]


def write_tables(results, outdir: Path):
    rows = _flatten_rows(results)
    summary = pd.DataFrame(rows).sort_values(["crossings", "link_id"])
    summary.to_csv(outdir / "summary.csv", index=False)
    component_rows, sign_rows, contact_rows, convergence_rows = [], [], [], []
    for result in results:
        for component in result["geometry"]["components"]:
            component_rows.append({"link_id": result["link_id"], **component})
        for sector in result.get("biot_savart", []):
            sign_rows.append({
                "link_id": result["link_id"],
                "backend": sector["backend"],
                "circulation_class": sector["circulation_class"],
                "signs": "".join("+" if x > 0 else "-" for x in sector["signs"]),
                "epsilon_D": sector["epsilon_D"],
                "relative_equilibrium_score": sector["relative_equilibrium_score"],
                "normal_rigid_residual_rms": sector["normal_rigid_residual_rms"],
                "omega_norm": sector["omega_norm"],
                "translation_norm": sector["translation_norm"],
                "impulse_norm_D2": sector["impulse_norm_D2"],
                "neumann_energy_proxy": sector["neumann_energy_proxy"],
                "neumann_self_energy_proxy": sector["neumann_self_energy_proxy"],
                "neumann_mutual_energy_proxy": sector["neumann_mutual_energy_proxy"],
                "mutual_energy_fraction": sector["mutual_energy_fraction"],
                "pair_helicity_proxy_Gamma2": sector["pair_helicity_proxy_Gamma2"],
            })
        for pair in result["contacts"]["mutual_pairs"]:
            contact_rows.append({"link_id": result["link_id"], **pair})
        for row in result["convergence"]:
            convergence_rows.append({"link_id": result["link_id"], **row})
    pd.DataFrame(component_rows).to_csv(outdir / "components.csv", index=False)
    pd.DataFrame(sign_rows).to_csv(outdir / "circulation_sign_configurations.csv", index=False)
    pd.DataFrame(contact_rows).to_csv(outdir / "mutual_contacts.csv", index=False)
    pd.DataFrame(convergence_rows).to_csv(outdir / "convergence.csv", index=False)
    return summary


def write_plots(summary: pd.DataFrame, outdir: Path):
    plotdir = outdir / "plots"
    plotdir.mkdir(exist_ok=True)
    numeric = summary.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)
    corr = numeric.corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    image = ax.imshow(corr.to_numpy(), aspect="auto")
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(corr.index)), corr.index, fontsize=7)
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(plotdir / "feature_correlation.png", dpi=180)
    plt.close(fig)

    ordered = summary.sort_values("total_length_D")
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(ordered["link_id"], ordered["total_length_D"])
    ax.set_ylabel("Total centerline length / Gilbert diameter")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout()
    fig.savefig(plotdir / "total_length_ranking.png", dpi=180)
    plt.close(fig)

    candidates = [
        "total_length_D", "length_imbalance_cv", "max_curvature_Dinv", "bending_integral",
        "spectral_entropy", "total_abs_linking", "contact_cycle_rank", "mirror_proxy",
        "best_relative_equilibrium_score",
    ]
    matrix = summary[candidates].replace([np.inf, -np.inf], np.nan)
    matrix = matrix.fillna(matrix.median(numeric_only=True))
    matrix = (matrix - matrix.mean()) / matrix.std(ddof=0).replace(0, 1)
    u, singular_values, _ = np.linalg.svd(matrix.to_numpy(), full_matrices=False)
    coordinates = u[:, :2] * singular_values[:2]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(coordinates[:, 0], coordinates[:, 1])
    for label, x, y in zip(summary["link_id"], coordinates[:, 0], coordinates[:, 1]):
        ax.annotate(label, (x, y), fontsize=8)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    fig.tight_layout()
    fig.savefig(plotdir / "feature_pca.png", dpi=180)
    plt.close(fig)


def write_markdown_report(results, summary: pd.DataFrame, outdir: Path, metadata: dict):
    best_eq = summary.sort_values("best_relative_equilibrium_score").head(5)
    longest = summary.sort_values("total_length_D", ascending=False).head(5)
    linked = summary.sort_values("total_abs_linking", ascending=False).head(5)
    backend = metadata.get("backend", {})
    native_audit = metadata.get("native_audit", {})
    lines = [
        "# SST ideal-link campaign report",
        "",
        f"- Links completed: **{len(results)}**",
        f"- Preset: **{metadata.get('preset', 'custom')}**",
        f"- Compute backend: **{backend.get('backend', 'unknown')}**",
        f"- Native parity gate: **{'PASS' if native_audit.get('ok') else 'FAIL/SKIP'}**",
        f"- Native source hash: `{backend.get('source_hash', '')}`",
        f"- Input SHA-256: `{metadata.get('input_sha256', '')}`",
        "",
        "## Interpretation boundary",
        "",
        "All source geometries use Gilbert's diameter normalization `D=1`. "
        "The mathematical ropelength based on tube **radius** is therefore twice the reported total `L/D`. "
        "Biot–Savart, contact-cycle, mirror and finite-core quantities remain diagnostics unless independently closed.",
        "",
        "## Best normal relative-equilibrium fits",
        "",
        best_eq[["link_id", "best_relative_equilibrium_score", "total_length_D"]].to_markdown(index=False),
        "",
        "## Largest total centerline lengths",
        "",
        longest[["link_id", "total_length_D", "components"]].to_markdown(index=False),
        "",
        "## Largest pair-linking content",
        "",
        linked[["link_id", "total_abs_linking", "signed_linking"]].to_markdown(index=False),
        "",
        "## Output map",
        "",
        "- `native_audit.json`: C++/Python parity ledger",
        "- `summary.csv`: one comparative feature row per link",
        "- `components.csv`: component-resolved geometry",
        "- `circulation_sign_configurations.csv`: every circulation assignment and backend",
        "- `mutual_contacts.csv`: refined inter-component distance/contact diagnostics",
        "- `convergence.csv`: resolution ladder",
        "- `per_link/*.json`: complete backend-stamped audit ledger",
        "- `plots/`: rankings, feature correlations and PCA",
    ]
    (outdir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
