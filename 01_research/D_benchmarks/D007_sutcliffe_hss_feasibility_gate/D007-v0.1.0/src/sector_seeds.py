#!/usr/bin/env python3
"""Generate simple topology-sector seeds for an independent rod relaxer."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def circle(n: int = 200, radius: float = 2.0, z: float = 0.0) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return np.column_stack((radius * np.cos(t), radius * np.sin(t), z + 0.0 * t))


def buckled_circle(
    n: int = 200, radius: float = 2.0, amplitude: float = 0.25, mode: int = 2
) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return np.column_stack(
        (radius * np.cos(t), radius * np.sin(t), amplitude * np.cos(mode * t))
    )


def torus_knot(
    p: int, q: int, n: int = 400, major: float = 3.0, minor: float = 1.0
) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    rho = major + minor * np.cos(q * t)
    return np.column_stack(
        (rho * np.cos(p * t), rho * np.sin(p * t), minor * np.sin(q * t))
    )


def hopf_link(n: int = 200, radius: float = 1.5, offset: float = 0.75):
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    c1 = np.column_stack(
        (radius * np.cos(t), radius * np.sin(t), np.zeros_like(t))
    )
    c2 = np.column_stack(
        (
            np.full_like(t, offset),
            radius * np.cos(t),
            radius * np.sin(t),
        )
    )
    return [c1, c2]


def write_xyz(path: Path, components: list[np.ndarray]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for index, component in enumerate(components):
            handle.write(f"# component {index}\n")
            np.savetxt(handle, component, fmt="%.12g")
            handle.write("\n")


def main(outdir: str = "outputs/seeds") -> None:
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    write_xyz(root / "Q1_circle.xyz", [circle()])
    write_xyz(root / "Q3_buckled.xyz", [buckled_circle()])
    write_xyz(root / "Q5_hopf_link.xyz", hopf_link())
    write_xyz(root / "K3_2_trefoil.xyz", [torus_knot(2, 3)])
    write_xyz(root / "K5_2.xyz", [torus_knot(2, 5)])
    metadata = {
        "warning": (
            "These are topology-sector seeds only. They are not HSS minima, "
            "Skyrme-Faddeev preimages, or framed solutions."
        )
    }
    (root / "README.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
