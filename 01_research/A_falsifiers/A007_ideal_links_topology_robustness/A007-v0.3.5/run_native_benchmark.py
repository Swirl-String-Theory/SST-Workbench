#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.biot_savart import sign_matrix
from sst_link_suite.native_ext import BackendOptions
from sst_link_suite.native_ext.core import link_velocity_batch, backend_status


def timed(callable_, repetitions: int) -> tuple[float, object]:
    best = float("inf")
    value = None
    for _ in range(repetitions):
        start = time.perf_counter()
        value = callable_()
        best = min(best, time.perf_counter() - start)
    return best, value


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark native versus NumPy Biot-Savart batches.")
    parser.add_argument("--input", default=str(ROOT / "data" / "idealLinks.txt"))
    parser.add_argument("--link-id", default="L6a4")
    parser.add_argument("--sample-n", type=int, default=256)
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--native-repetitions", type=int, default=3)
    parser.add_argument("--python-repetitions", type=int, default=1)
    parser.add_argument("--out", default=str(ROOT / "native_benchmark.json"))
    args = parser.parse_args()

    link = parse_ideal_links(args.input)[args.link_id]
    curves = [sample_component(component, args.sample_n).r for component in link.components]
    sectors = sign_matrix(len(curves))
    native_options = BackendOptions(require_native=True)
    python_options = BackendOptions(force_python=True)

    # Warm the extension and caches.
    link_velocity_batch(curves, sectors, args.epsilon, 3, native_options)
    native_seconds, native_value = timed(
        lambda: link_velocity_batch(curves, sectors, args.epsilon, 3, native_options)[0],
        args.native_repetitions,
    )
    python_seconds, python_value = timed(
        lambda: link_velocity_batch(curves, sectors, args.epsilon, 3, python_options)[0],
        args.python_repetitions,
    )
    delta = np.concatenate([
        np.asarray(a) - np.asarray(b) for a, b in zip(native_value, python_value)
    ])
    reference = np.concatenate([np.asarray(x) for x in python_value])
    report = {
        "link_id": args.link_id,
        "sample_n_per_component": args.sample_n,
        "components": len(curves),
        "sign_sectors": len(sectors),
        "epsilon_D": args.epsilon,
        "native_seconds_best": native_seconds,
        "python_seconds_best": python_seconds,
        "speedup_python_over_native": python_seconds / max(native_seconds, 1e-300),
        "abs_max_error": float(np.max(np.abs(delta))),
        "relative_l2_error": float(np.linalg.norm(delta) / max(np.linalg.norm(reference), 1e-300)),
        "backend": backend_status(native_options),
    }
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
