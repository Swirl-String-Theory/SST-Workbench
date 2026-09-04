from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def _flatten_rows(results):
    return [{"link_id": r["link_id"], "conway": r["conway"], **r["features"]} for r in results]

def write_tables(results, outdir: Path):
    rows = _flatten_rows(results)
    summary = pd.DataFrame(rows).sort_values(["crossings", "link_id"])
    summary.to_csv(outdir/"summary.csv", index=False)
    comp_rows, sign_rows, contact_rows, conv_rows = [], [], [], []
    for r in results:
        for c in r["geometry"]["components"]:
            comp_rows.append({"link_id": r["link_id"], **c})
        for s in r.get("biot_savart", []):
            sign_rows.append({
                "link_id": r["link_id"],
                "signs": "".join("+" if x > 0 else "-" for x in s["signs"]),
                "epsilon_D": s["epsilon_D"],
                "relative_equilibrium_score": s["relative_equilibrium_score"],
                "normal_rigid_residual_rms": s["normal_rigid_residual_rms"],
                "omega_norm": s["omega_norm"],
                "translation_norm": s["translation_norm"],
                "impulse_norm_D2": s["impulse_norm_D2"],
                "neumann_energy_proxy": s["neumann_energy_proxy"],
            })
        for p in r["contacts"]["mutual_pairs"]:
            contact_rows.append({"link_id": r["link_id"], **p})
        for c in r["convergence"]:
            conv_rows.append({"link_id": r["link_id"], **c})
    pd.DataFrame(comp_rows).to_csv(outdir/"components.csv", index=False)
    pd.DataFrame(sign_rows).to_csv(outdir/"circulation_sign_configurations.csv", index=False)
    pd.DataFrame(contact_rows).to_csv(outdir/"mutual_contacts.csv", index=False)
    pd.DataFrame(conv_rows).to_csv(outdir/"convergence.csv", index=False)
    return summary

def write_plots(summary: pd.DataFrame, outdir: Path):
    plotdir = outdir/"plots"
    plotdir.mkdir(exist_ok=True)
    numeric = summary.select_dtypes(include=[np.number]).replace([np.inf,-np.inf], np.nan)
    # Correlation heatmap.
    corr = numeric.corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr.to_numpy(), aspect="auto")
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(corr.index)), corr.index, fontsize=7)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(plotdir/"feature_correlation.png", dpi=180)
    plt.close(fig)
    # Total length ranking.
    ordered = summary.sort_values("total_length_D")
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(ordered["link_id"], ordered["total_length_D"])
    ax.set_ylabel("Total centerline length / Gilbert diameter")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout()
    fig.savefig(plotdir/"total_length_ranking.png", dpi=180)
    plt.close(fig)
    # PCA from standardized finite features.
    candidates = [
        "total_length_D","length_imbalance_cv","max_curvature_Dinv","bending_integral",
        "spectral_entropy","total_abs_linking","contact_cycle_rank","mirror_proxy",
        "best_relative_equilibrium_score"
    ]
    X = summary[candidates].replace([np.inf,-np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True))
    X = (X-X.mean())/X.std(ddof=0).replace(0,1)
    U,S,Vt = np.linalg.svd(X.to_numpy(), full_matrices=False)
    coords = U[:,:2]*S[:2]
    fig, ax = plt.subplots(figsize=(9,7))
    ax.scatter(coords[:,0], coords[:,1])
    for label, x, y in zip(summary["link_id"], coords[:,0], coords[:,1]):
        ax.annotate(label, (x,y), fontsize=8)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    fig.tight_layout()
    fig.savefig(plotdir/"feature_pca.png", dpi=180)
    plt.close(fig)

def write_markdown_report(results, summary: pd.DataFrame, outdir: Path, metadata: dict):
    best_eq = summary.sort_values("best_relative_equilibrium_score").head(5)
    longest = summary.sort_values("total_length_D", ascending=False).head(5)
    linked = summary.sort_values("total_abs_linking", ascending=False).head(5)
    lines = [
        "# SST ideal-link campaign report",
        "",
        f"- Links completed: **{len(results)}**",
        f"- Preset: **{metadata.get('preset','custom')}**",
        f"- Input SHA-256: `{metadata.get('input_sha256','')}`",
        "",
        "## Interpretation boundary",
        "",
        "All source geometries use Gilbert's diameter normalization `D=1`. "
        "The mathematical ropelength based on tube **radius** is therefore twice the reported total `L/D`. "
        "Biot–Savart, contact-cycle, mirror and finite-core quantities are diagnostics/proxies unless independently closed.",
        "",
        "## Best normal relative-equilibrium fits",
        "",
        best_eq[["link_id","best_relative_equilibrium_score","total_length_D"]].to_markdown(index=False),
        "",
        "## Largest total centerline lengths",
        "",
        longest[["link_id","total_length_D","components"]].to_markdown(index=False),
        "",
        "## Largest pair-linking content",
        "",
        linked[["link_id","total_abs_linking","signed_linking"]].to_markdown(index=False),
        "",
        "## Output map",
        "",
        "- `summary.csv`: one comparative feature row per link",
        "- `components.csv`: component-resolved geometry",
        "- `circulation_sign_configurations.csv`: every ± circulation assignment",
        "- `mutual_contacts.csv`: refined inter-component distance/contact diagnostics",
        "- `convergence.csv`: resolution ladder",
        "- `per_link/*.json`: full audit ledger",
        "- `plots/`: rankings, feature correlations and PCA",
    ]
    (outdir/"REPORT.md").write_text("\n".join(lines), encoding="utf-8")
