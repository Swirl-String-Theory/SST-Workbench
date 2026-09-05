#!/usr/bin/env python3
"""Optional bridge from an installed SSTcore package to the ratio harness.

The bridge is deliberately conservative. SSTcore's native VortexKnotSystem may
use an internal evolution model whose core kernel is not identical to the
standalone harness. Therefore its output is stored as a separate backend branch
and must not be mixed into a same-protocol ratio without an explicit audit.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
HARNESS_PATH = HERE / "sst_dimensionless_ratios.py"
spec = importlib.util.spec_from_file_location("sst_dimensionless_ratios", HARNESS_PATH)
harness = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = harness
assert spec.loader is not None
spec.loader.exec_module(harness)


def load_sstcore() -> Any:
    try:
        import SSTcore as sst  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "SSTcore is not installed in this Python environment. Install the matching "
            "SSTcore wheel or run the standalone harness instead."
        ) from exc
    return sst


def native_curve(sst: Any, knot: str, resolution: int, circulation: float) -> tuple[Any, np.ndarray]:
    if not hasattr(sst, "VortexKnotSystem"):
        raise RuntimeError("installed SSTcore does not export VortexKnotSystem")
    system = sst.VortexKnotSystem(circulation)
    if knot == "trefoil":
        system.initialize_trefoil_knot(resolution)
    elif knot in {"figure8", "figure_eight"}:
        system.initialize_figure8_knot(resolution)
    else:
        # Available in SSTcore v0.8.28; may vary in other releases.
        system.initialize_knot_from_name(knot, resolution)
    points = np.asarray(system.get_positions(), dtype=float)
    return system, points


def run(args: argparse.Namespace) -> dict[str, Any]:
    sst = load_sstcore()
    system, initial_raw = native_curve(sst, args.knot, args.resolution, args.circulation)
    initial = harness.uniform_arclength_resample(initial_raw, args.resolution)
    initial = harness.normalize_curve(initial, args.normalization, target_length=args.target_length)
    initial = harness.uniform_arclength_resample(initial, args.resolution)

    protocol = harness.NumericalProtocol(
        resolution=args.resolution,
        epsilon=args.epsilon,
        kernel=args.kernel,
        circulation=args.circulation,
        normalization=args.normalization,
        target_length=args.target_length,
    )
    source = harness.CurveSource(args.knot, f"sstcore_{args.knot}", "generator", args.knot)
    before = harness.static_diagnostics(source, initial, protocol).to_dict()

    system.evolve(args.dt, args.steps)
    final_raw = np.asarray(system.get_positions(), dtype=float)
    final = harness.uniform_arclength_resample(final_raw, args.resolution)
    # Compare native final shape after scale normalization to remove a possible
    # backend-specific global scale convention.
    final = harness.normalize_curve(final, args.normalization, target_length=args.target_length)
    final = harness.uniform_arclength_resample(final, args.resolution)
    after = harness.static_diagnostics(source, final, protocol).to_dict()
    recurrence = harness.best_cyclic_recurrence(initial, final)

    return {
        "epistemic_status": "OPTIONAL_CROSS_BACKEND_DIAGNOSTIC",
        "warning": (
            "SSTcore native evolution and standalone Biot-Savart diagnostics may use "
            "different regularization and integration conventions. Do not interpret "
            "this as a same-operator prediction without auditing the native backend."
        ),
        "sstcore_version": getattr(sst, "__version__", None),
        "arguments": vars(args),
        "before": before,
        "after": after,
        "native_recurrence": recurrence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional SSTcore bridge for dimensionless ratio diagnostics")
    parser.add_argument("--knot", default="trefoil")
    parser.add_argument("--resolution", type=int, default=128)
    parser.add_argument("--circulation", type=float, default=1.0)
    parser.add_argument("--dt", type=float, default=1e-4)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--epsilon", type=float, default=0.08)
    parser.add_argument("--kernel", choices=["rosenhead", "rankine", "winckelmans"], default="rosenhead")
    parser.add_argument("--normalization", choices=["fixed_length", "fixed_rms_radius"], default="fixed_length")
    parser.add_argument("--target-length", type=float, default=2.0 * np.pi)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        payload = run(args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
