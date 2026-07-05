#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line runner for SST chi-phase package v13B.0."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
import time

from sst_chi_phase_v13B0_py import (
    PHI,
    NLS_ALPHA_LEGACY,
    RANKINE_ALPHA,
    canon_gate_status,
    summary_metrics,
    unified_reference_rows,
)


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(asdict(rows[0]).keys())
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def write_metrics_csv(path: Path, metrics):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in metrics.items():
            w.writerow([k, v])


def write_gates_csv(path: Path, gates):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gate", "status", "criterion"])
        w.writeheader()
        for row in gates:
            w.writerow(row)


def make_plots(outdir: Path, rows):
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"[warn] matplotlib unavailable, skipping plots: {exc}")
        return

    selected = [r for r in rows if r.track in {"A", "B"}]
    labels = [r.model for r in selected]
    vals = [r.alpha_ring for r in selected]
    xs = range(len(selected))

    fig = plt.figure(figsize=(11, 6))
    plt.bar(xs, vals)
    plt.axhline(NLS_ALPHA_LEGACY, linestyle="--", label="legacy NLS 1.61")
    plt.axhline(PHI, linestyle=":", label="phi")
    plt.axhline(RANKINE_ALPHA, linestyle="-.", label="Rankine 7/4")
    plt.xticks(list(xs), labels, rotation=30, ha="right")
    plt.ylabel(r"$\alpha_{\rm ring}$")
    plt.title("v13B.0 unified Track A/B ring-constant benchmark")
    plt.legend()
    fig.tight_layout()
    fig.savefig(outdir / "chi_v13B0_unified_alpha_benchmark.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(11, 5))
    deltas = [r.delta_legacy_nls_alpha for r in selected]
    plt.bar(xs, deltas)
    plt.axhline(0.0, linestyle="--")
    plt.xticks(list(xs), labels, rotation=30, ha="right")
    plt.ylabel(r"$\alpha_{\rm ring}-1.61$")
    plt.title("v13B.0 distance from legacy NLS alpha")
    fig.tight_layout()
    fig.savefig(outdir / "chi_v13B0_delta_legacy_nls.png", dpi=180)
    plt.close(fig)

    # Small comparison: Track A chi closure vs Track B GP
    fig = plt.figure(figsize=(7, 5))
    names = ["Track A\nsmooth a0*", "Track B\nGP/NLSE inf", "legacy\nNLS", "phi"]
    vals2 = []
    lookup = {r.model: r.alpha_ring for r in rows}
    vals2.append(lookup["smooth_a0star_chi_closure"])
    vals2.append(lookup["GP_NLSE_infinity_tail_corrected"])
    vals2.append(NLS_ALPHA_LEGACY)
    vals2.append(PHI)
    plt.bar(range(len(vals2)), vals2)
    plt.xticks(list(range(len(vals2))), names)
    plt.ylabel(r"$\alpha_{\rm ring}$")
    plt.title("Selector split: chi closure vs GP/NLSE ring energy")
    fig.tight_layout()
    fig.savefig(outdir / "chi_v13B0_selector_split.png", dpi=180)
    plt.close(fig)


def write_summary(path: Path, rows, metrics, gates, elapsed):
    lookup = {r.model: r for r in rows}
    lines = []
    lines.append("SST chi-phase package v13B.0 summary")
    lines.append("=" * 56)
    lines.append("")
    lines.append("Track: unified A/B alpha_ring benchmark pipeline")
    lines.append("Status: Strong Research Track synthesis; not locked CANON")
    lines.append("")
    lines.append("Purpose:")
    lines.append("  v13B.0 brings the Track A Euler/Biot-Savart and Track B GP/NLSE")
    lines.append("  alpha_ring results into one table so the selector split is explicit.")
    lines.append("")
    lines.append(f"Elapsed: {elapsed:.3f} s")
    lines.append("")
    lines.append("Principal numbers:")
    for name in ["rankine_solid", "smooth_a0star_chi_closure", "smooth_phi", "GP_NLSE_infinity_tail_corrected", "legacy_NLS_note", "golden_ratio_phi"]:
        r = lookup[name]
        sig = "" if r.alpha_sigma is None else f" ± {r.alpha_sigma:.3e}"
        lines.append(f"  {name:34s} alpha_ring={r.alpha_ring:.12f}{sig}, beta(q=0)={r.beta_ring_q0:.12f}")
    lines.append("")
    lines.append("Key deltas:")
    lines.append(f"  Track B GP/NLSE infinity - legacy NLS = {metrics['TrackB_minus_legacy_NLS']:+.9f}")
    lines.append(f"  Track B GP/NLSE infinity - phi        = {metrics['TrackB_minus_phi']:+.9f}")
    lines.append(f"  Track B GP/NLSE infinity - Track A smooth a0* = {metrics['TrackB_minus_TrackA_smooth_a0star']:+.9f}")
    lines.append(f"  Track A smooth a0* - legacy NLS = {metrics['TrackA_smooth_a0star_minus_legacy_NLS']:+.9f}")
    lines.append(f"  Track A Rankine error vs 7/4 = {metrics['TrackA_rankine_error_vs_7_4']:+.9f}")
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  - Track A validates the Euler/Biot-Savart ring-energy extractor against Rankine/7/4, but")
    lines.append("    its smooth chi-closure profiles cluster near alpha_ring≈1.47--1.51, not 1.61.")
    lines.append("  - Track B GP/NLSE with corrected energy and analytic tail gives alpha_ring≈1.61935,")
    lines.append("    close to legacy NLS 1.61 and phi, but still conditional on the SST A=B=C core-envelope gate.")
    lines.append("  - Therefore chi-closure selection and GP/NLSE ring-energy selection are distinct mechanisms.")
    lines.append("")
    lines.append("Canon gates:")
    for g in gates:
        lines.append(f"  {g['gate']}: {g['status']} — {g['criterion']}")
    lines.append("")
    lines.append("CANON-safe conclusion:")
    lines.append("  alpha_ring/beta_ring notation and beta_ring=alpha_ring-1+q are safe.")
    lines.append("  alpha_ring^GP≈1.61935 is derived-conditional / Strong Research Track.")
    lines.append("  Locked CANON requires an SST-internal proof that A_grad=B_phase=C_depletion.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", default="exports")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    t0 = time.time()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = unified_reference_rows()
    metrics = summary_metrics(rows)
    gates = canon_gate_status(rows)
    write_csv(outdir / "chi_v13B0_unified_benchmark.csv", rows)
    write_metrics_csv(outdir / "chi_v13B0_summary_metrics.csv", metrics)
    write_gates_csv(outdir / "chi_v13B0_canon_gates.csv", gates)
    if not args.no_plots:
        make_plots(outdir, rows)
    elapsed = time.time() - t0
    write_summary(outdir / "chi_v13B0_run_results_summary.txt", rows, metrics, gates, elapsed)
    print((outdir / "chi_v13B0_run_results_summary.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
