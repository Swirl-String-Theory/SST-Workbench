#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(ROOT / "src"))

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.perturbations import build_reduced_normal_basis
from sst_link_suite.topological_labels import circulation_sectors
from sst_link_suite.qm_energy import (
    compute_geometric_reduced_derivatives,
    compute_neumann_coupling_reduced_derivatives,
    contract_neumann_coupling_derivatives,
    compute_neumann_reduced_derivatives,
    tube_repulsion_energy,
)
from sst_link_suite.native_ext import BackendOptions


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark v0.3.6 exact performance factorization.")
    ap.add_argument("--link", default="L6a4")
    ap.add_argument("--sample-n", type=int, default=96)
    ap.add_argument("--mode-max", type=int, default=0)
    ap.add_argument("--repulsion-sample-n", type=int, default=384)
    ap.add_argument("--step", type=float, default=0.004)
    ap.add_argument("--native-threads", type=int, default=16)
    ap.add_argument("--output", default="validation/v0.3.6/performance_benchmark.json")
    args = ap.parse_args()

    import os
    os.environ["SST_NATIVE_MAX_THREADS"] = str(args.native_threads)
    options = BackendOptions(require_native=True, skip_build=True)
    link = parse_ideal_links(ROOT / "data" / "idealLinks.txt")[args.link]
    samples = [sample_component(c, args.sample_n) for c in link.components]
    curves = [s.r for s in samples]
    repulsion_curves = [sample_component(c, args.repulsion_sample_n).r for c in link.components]
    basis, _ = build_reduced_normal_basis(samples, mode_max=args.mode_max)
    sectors = [np.asarray(x["representative"], dtype=float) for x in circulation_sectors(len(samples))]
    arc = 0.20 * float(link.diameter)

    # Warm import/kernel so benchmark excludes extension import/build latency.
    tube_repulsion_energy(repulsion_curves, link.diameter, 0.04, 0.0, 0.035, options)

    # Repulsion: exact same functional, NumPy reference vs C++.
    t0 = time.perf_counter()
    rep_py = tube_repulsion_energy(repulsion_curves, link.diameter, 0.04, 0.0, 0.035, None)
    rep_py_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    rep_cpp = tube_repulsion_energy(repulsion_curves, link.diameter, 0.04, 0.0, 0.035, options)
    rep_cpp_s = time.perf_counter() - t0

    # v0.3.5.1-equivalent Neumann path: finite-difference the scalar sector energy separately.
    t0 = time.perf_counter()
    naive = []
    for signs in sectors:
        naive.append(compute_neumann_reduced_derivatives(
            samples, basis, signs, 0.1, options, args.step,
            compute_offdiagonal=True, self_exclusion_energy_arc=arc,
        ))
    naive_s = time.perf_counter() - t0

    # v0.3.6: one C(q) derivative ledger, then tiny contractions.
    t0 = time.perf_counter()
    coupling = compute_neumann_coupling_reduced_derivatives(
        samples, basis, 0.1, options, args.step,
        compute_offdiagonal=True, self_exclusion_energy_arc=arc,
    )
    optimized = [contract_neumann_coupling_derivatives(coupling, signs) for signs in sectors]
    optimized_s = time.perf_counter() - t0

    errors = []
    for a, b in zip(naive, optimized):
        errors.append({
            "baseline_abs": abs(float(a["baseline"]) - float(b["baseline"])),
            "gradient_max_abs": float(np.max(np.abs(np.asarray(a["gradient"]) - np.asarray(b["gradient"])))),
            "hessian_max_abs": float(np.max(np.abs(np.asarray(a["hessian"]) - np.asarray(b["hessian"])))),
        })

    report = {
        "link_id": args.link,
        "sample_n": args.sample_n,
        "mode_max": args.mode_max,
        "reduced_dimension": int(basis.vectors.shape[0]),
        "sector_count": len(sectors),
        "step": args.step,
        "native_threads_requested": args.native_threads,
        "tube_repulsion": {
            "sample_n": args.repulsion_sample_n,
            "numpy_s": rep_py_s,
            "cpp_s": rep_cpp_s,
            "speedup": rep_py_s / max(rep_cpp_s, 1e-300),
            "relative_error": abs(rep_cpp-rep_py)/max(abs(rep_py), 1e-300),
        },
        "neumann_sector_factorization": {
            "v0351_equivalent_s": naive_s,
            "v036_factorized_s": optimized_s,
            "speedup": naive_s / max(optimized_s, 1e-300),
            "max_baseline_abs_error": max(x["baseline_abs"] for x in errors),
            "max_gradient_abs_error": max(x["gradient_max_abs"] for x in errors),
            "max_hessian_abs_error": max(x["hessian_max_abs"] for x in errors),
        },
        "boundary": "Microbenchmark only; end-to-end spectral-ladder speedup is hardware/configuration dependent.",
    }
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
