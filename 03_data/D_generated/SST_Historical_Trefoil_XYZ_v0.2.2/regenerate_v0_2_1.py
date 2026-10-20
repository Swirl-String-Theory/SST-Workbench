#!/usr/bin/env python3
"""Generate 2015 historical trefoil XYZ geometries and their chirality/orientation variants.

Original mathematical seeds:
  A: (cos(t)+1.5*cos(2t), sin(t)-1.5*sin(2t), 0.35*sin(3t))
  B: ((2+cos(3t))*cos(2t), (2+cos(3t))*sin(2t), sin(3t))
  with 0 <= t < 2*pi.

For each seed and each resolution N, write:
  orig_ccw      original chirality, natural t direction
  orig_cw       original chirality, reversed vertex order
  mirrorX_ccw   opposite chirality, natural t direction
  mirrorX_cw    opposite chirality, reversed vertex order

"cw" and "ccw" are traversal labels relative to the *parameter direction*,
NOT an absolute geometric definition of clockwise in 3D (which requires a view).
Reflection x -> -x changes chirality; reversing vertices does not.

Geometry-only seeds: no vortex core, circulation, density, flow or phase clock.
Files use three headerless ASCII columns x y z, without a duplicate endpoint.

Dependencies: numpy, scipy
Usage:
  python -m pip install numpy scipy
  python regenerate.py                    # N = 600, 1200
  python regenerate.py --n 600 1200 2400
  python regenerate.py --n 1200 --out ./my_seeds
  python regenerate.py --n 599             # rejected
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.integrate import cumulative_trapezoid, quad
from scipy.interpolate import PchipInterpolator

VERSION = "0.2.1"
MIN_N = 600
DEFAULT_N = (600, 1200)
TWO_PI = 2.0 * np.pi
SEEDS = ("A_Fourier_2015_p32", "B_Torus_2015_p66")


def coordinates(name: str, t: np.ndarray) -> np.ndarray:
    """Evaluate the original analytic 3D centerline (dimensionless)."""
    if name == "A_Fourier_2015_p32":
        return np.column_stack((
            np.cos(t) + 1.5 * np.cos(2 * t),
            np.sin(t) - 1.5 * np.sin(2 * t),
            0.35 * np.sin(3 * t),
        ))
    if name == "B_Torus_2015_p66":
        r = 2.0 + np.cos(3 * t)
        return np.column_stack((r * np.cos(2 * t),
                                r * np.sin(2 * t),
                                np.sin(3 * t)))
    raise ValueError(f"Unknown seed: {name}")


def derivative(name: str, t: np.ndarray) -> np.ndarray:
    """Analytic derivative with respect to the dimensionless parameter t."""
    if name == "A_Fourier_2015_p32":
        return np.column_stack((
            -np.sin(t) - 3.0 * np.sin(2 * t),
            np.cos(t) - 3.0 * np.cos(2 * t),
            1.05 * np.cos(3 * t),
        ))
    if name == "B_Torus_2015_p66":
        r = 2.0 + np.cos(3 * t)
        dr = -3.0 * np.sin(3 * t)
        return np.column_stack((
            dr * np.cos(2 * t) - 2 * r * np.sin(2 * t),
            dr * np.sin(2 * t) + 2 * r * np.cos(2 * t),
            3.0 * np.cos(3 * t),
        ))
    raise ValueError(f"Unknown seed: {name}")


def exact_arclength(name: str) -> float:
    def speed(t: float) -> float:
        return float(np.linalg.norm(derivative(name, np.array([t]))[0]))
    return float(quad(speed, 0.0, TWO_PI, epsabs=1e-12,
                      epsrel=1e-12, limit=500)[0])


def sample_uniform_arclength(name: str, n: int) -> tuple[np.ndarray, float]:
    if n < MIN_N:
        raise ValueError(f"N must be >= {MIN_N}; received {n}")
    # Dense monotone lookup of s(t) = integral |X'(t)| dt; invert it.
    grid_n = max(262_144, 32 * n)
    t_grid = np.linspace(0.0, TWO_PI, grid_n + 1)
    speeds = np.linalg.norm(derivative(name, t_grid), axis=1)
    s_grid = np.concatenate(([0.0], cumulative_trapezoid(speeds, t_grid)))
    arc_length = float(s_grid[-1])
    s_target = arc_length * np.arange(n, dtype=float) / n
    t_sample = np.asarray(PchipInterpolator(s_grid, t_grid)(s_target))
    xyz = coordinates(name, t_sample)
    if xyz.shape != (n, 3) or not np.isfinite(xyz).all():
        raise AssertionError("Invalid XYZ sampling")
    if not np.all(np.diff(t_sample) > 0):
        raise AssertionError("Sampling is not monotonic")
    return xyz, arc_length


def mirror_x(xyz: np.ndarray) -> np.ndarray:
    """Reflect in the yz plane: opposite chirality."""
    result = xyz.copy()
    result[:, 0] *= -1.0
    return result


def reverse_orientation(xyz: np.ndarray) -> np.ndarray:
    """Reverse traversal while retaining the same starting vertex."""
    return np.concatenate((xyz[:1], xyz[:0:-1]), axis=0)


def all_variants(xyz: np.ndarray) -> dict[str, np.ndarray]:
    mirrored = mirror_x(xyz)
    return {
        "orig_ccw": xyz.copy(),
        "orig_cw": reverse_orientation(xyz),
        "mirrorX_ccw": mirrored,
        "mirrorX_cw": reverse_orientation(mirrored),
    }


def write_xyz(filename: Path, xyz: np.ndarray) -> str:
    """Write exactly three floating-point columns, without headers or endpoint repeats."""
    with filename.open("w", encoding="ascii", newline="\n") as f:
        for x, y, z in xyz:
            f.write(f"{x:.16e} {y:.16e} {z:.16e}\n")
    return hashlib.sha256(filename.read_bytes()).hexdigest()


def generate(sizes: tuple[int, ...], output_dir: Path) -> dict:
    if not sizes or any(not isinstance(n, int) or n < MIN_N for n in sizes):
        raise ValueError(f"Every resolution N must be an integer >= {MIN_N}")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "version": VERSION,
        "classification": "HISTORICAL_GEOMETRY_SEED",
        "physical_pklsa_dynamics_qualified": False,
        "units": "dimensionless historical coordinates",
        "format": "ASCII XYZ, 3 columns, no header, no repeated endpoint",
        "sampling": "equal analytic arc-length spacing (numerical inverse of s(t))",
        "minimum_points": MIN_N,
        "resolutions": list(sizes),
        "chirality_convention": "mirrorX: reflect x -> -x",
        "orientation_convention": "ccw: t increasing; cw: reversed point order, first vertex preserved",
        "warning": "CW and CCW depend on the 3D viewing direction. Point order is not physical circulation.",
        "seeds": {},
    }
    for seed in SEEDS:
        length = exact_arclength(seed)
        data = {"historical_page": 32 if seed.startswith("A_") else 66,
                "exact_arclength_dimensionless": length, "files": {}}
        # Verify the parametric loop closes analytically before omitting its last vertex.
        if np.linalg.norm(coordinates(seed, np.array([0.0]))[0] -
                          coordinates(seed, np.array([TWO_PI]))[0]) > 1e-12:
            raise AssertionError(f"Curve does not close: {seed}")
        for n in sizes:
            xyz, numerical_length = sample_uniform_arclength(seed, n)
            if abs(numerical_length - length) / length > 1e-9:
                raise AssertionError(f"Arc-length quadrature mismatch: {seed}, N={n}")
            variants = all_variants(xyz)
            assert np.array_equal(variants["orig_ccw"], reverse_orientation(variants["orig_cw"]))
            assert np.array_equal(variants["mirrorX_ccw"], mirror_x(variants["orig_ccw"]))
            for label, arr in variants.items():
                edges = np.linalg.norm(np.roll(arr, -1, axis=0) - arr, axis=1)
                cv = float(edges.std() / edges.mean())
                if cv > 1e-3:
                    raise AssertionError(f"Uneven edge lengths: {seed}, {label}, N={n}, CV={cv}")
                filename = f"{seed}_{label}_N{n}_arclength.xyz"
                sha = write_xyz(output_dir / filename, arr)
                data["files"][filename] = {
                    "N": n,
                    "variant": label,
                    "sha256": sha,
                    "polygon_length_dimensionless": float(edges.sum()),
                    "closed_edge_cv": cv,
                    "closure_edge_length_dimensionless": float(edges[-1]),
                }
        manifest["seeds"][seed] = data
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, nargs="+", default=list(DEFAULT_N),
                        help=f"Points per closed curve, >= {MIN_N}; default: 600 1200")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent,
                        help="Directory for XYZ files and manifest.json")
    args = parser.parse_args()
    if any(n < MIN_N for n in args.n):
        parser.error(f"N cannot be lower than {MIN_N}; got {args.n}")
    manifest = generate(tuple(dict.fromkeys(args.n)), args.out)
    total = sum(len(row["files"]) for row in manifest["seeds"].values())
    print(f"Generated {total} XYZ files in {args.out.resolve()}")
    for seed, details in manifest["seeds"].items():
        print(f"  {seed}: length = {details['exact_arclength_dimensionless']:.9f} (dimensionless)")
    print("Static geometry only; no Euler/PKLSA/Swirl Clock certification.")


if __name__ == "__main__":
    main()
