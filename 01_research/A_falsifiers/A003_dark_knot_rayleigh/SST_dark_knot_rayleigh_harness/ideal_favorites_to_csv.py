#!/usr/bin/env python3
"""Convert Brian Gilbert ideal-knot Fourier coefficients to vertex CSV.

Input format: ideal_favorites.txt XML-like database with <AB Id="3:1:1" ...>
entries containing <Coeff I="k" A="ax,ay,az" B="bx,by,bz"/>.

Fourier convention used here:
    X(t) = sum_k A_k cos(k t) + B_k sin(k t),   t in [0, 2*pi)

For the Gilbert database, the declared L is the centerline length for D=1
(tube/contact diameter convention). In SST harness terms this makes:
    ropelength proxy = 2*L/D
for single-component knots.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class Coeff:
    i: int
    a: Vec3
    b: Vec3


@dataclass(frozen=True)
class Entry:
    knot_id: str
    conway: str | None
    declared_L: float | None
    declared_D: float | None
    coeffs: list[Coeff]


def parse_vec3(text: str) -> Vec3:
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 3:
        raise ValueError(f"expected 3-vector, got {text!r}")
    return (float(parts[0]), float(parts[1]), float(parts[2]))


def load_entry(path: Path, knot_id: str, component: int | None = None) -> Entry:
    root = ET.parse(path).getroot()
    ab = None
    for node in root.findall(".//AB"):
        if (node.get("Id") or "").strip() == knot_id:
            ab = node
            break
    if ab is None:
        available = [node.get("Id") for node in root.findall(".//AB")[:20]]
        raise KeyError(f"knot id {knot_id!r} not found. First entries: {available}")

    coeff_parent = ab
    components = ab.findall("Component")
    if components:
        if component is None:
            raise ValueError(
                f"entry {knot_id!r} has {len(components)} components; pass --component N"
            )
        for comp in components:
            if int((comp.get("I") or "0").strip()) == component:
                coeff_parent = comp
                break
        else:
            raise ValueError(f"component {component} not found in {knot_id!r}")

    coeffs: list[Coeff] = []
    for c in coeff_parent.findall("Coeff"):
        i = int((c.get("I") or "0").strip())
        a = parse_vec3(c.get("A") or "0,0,0")
        b = parse_vec3(c.get("B") or "0,0,0")
        coeffs.append(Coeff(i=i, a=a, b=b))
    coeffs.sort(key=lambda c: c.i)
    if not coeffs:
        raise ValueError(f"entry {knot_id!r} contains no coefficients")

    def fattr(name: str) -> float | None:
        val = ab.get(name)
        if val is None:
            return None
        return float(val.strip())

    return Entry(
        knot_id=knot_id,
        conway=ab.get("Conway"),
        declared_L=fattr("L"),
        declared_D=fattr("D"),
        coeffs=coeffs,
    )


def eval_curve(coeffs: Iterable[Coeff], n: int) -> list[Vec3]:
    pts: list[Vec3] = []
    coeffs = list(coeffs)
    for j in range(n):
        t = 2.0 * math.pi * j / n
        x = y = z = 0.0
        for c in coeffs:
            ct = math.cos(c.i * t)
            st = math.sin(c.i * t)
            x += c.a[0] * ct + c.b[0] * st
            y += c.a[1] * ct + c.b[1] * st
            z += c.a[2] * ct + c.b[2] * st
        pts.append((x, y, z))
    return pts


def sub(u: Vec3, v: Vec3) -> Vec3:
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


def norm(u: Vec3) -> float:
    return math.sqrt(u[0] * u[0] + u[1] * u[1] + u[2] * u[2])


def add(u: Vec3, v: Vec3) -> Vec3:
    return (u[0] + v[0], u[1] + v[1], u[2] + v[2])


def mul(s: float, u: Vec3) -> Vec3:
    return (s * u[0], s * u[1], s * u[2])


def center_points(pts: list[Vec3]) -> list[Vec3]:
    n = len(pts)
    c = (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)
    return [sub(p, c) for p in pts]


def length_closed(pts: list[Vec3]) -> float:
    n = len(pts)
    return sum(norm(sub(pts[(i + 1) % n], pts[i])) for i in range(n))


def edge_stats(pts: list[Vec3]) -> tuple[float, float, float]:
    n = len(pts)
    edges = [norm(sub(pts[(i + 1) % n], pts[i])) for i in range(n)]
    return min(edges), max(edges), sum(edges) / n


def min_nonlocal_vertex_distance(pts: list[Vec3], skip: int = 4) -> float:
    """Crude vertex-only nonlocal distance. Not exact polygonal thickness."""
    n = len(pts)
    best = float("inf")
    for i in range(n):
        for j in range(i + 1, n):
            sep = min((j - i) % n, (i - j) % n)
            if sep <= skip:
                continue
            d = norm(sub(pts[i], pts[j]))
            if d < best:
                best = d
    return best


def write_csv(path: Path, pts: list[Vec3], header: bool = True) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if header:
            w.writerow(["x", "y", "z"])
        for p in pts:
            w.writerow([f"{p[0]:.17g}", f"{p[1]:.17g}", f"{p[2]:.17g}"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path, help="ideal_favorites.txt")
    ap.add_argument("--id", required=True, help="Gilbert knot id, e.g. 3:1:1 or 4:1:1")
    ap.add_argument("--component", type=int, default=None, help="component number for links")
    ap.add_argument("--n", type=int, default=512, help="number of vertices to sample")
    ap.add_argument("--out", type=Path, required=True, help="output CSV path")
    ap.add_argument("--no-header", action="store_true", help="omit x,y,z header")
    ap.add_argument("--center", action="store_true", help="subtract centroid")
    ap.add_argument(
        "--scale-to-declared-L",
        action="store_true",
        help="uniformly rescale sampled polygon so closed polyline length equals declared L",
    )
    ap.add_argument(
        "--skip-min-dist",
        action="store_true",
        help="skip O(n^2) crude nonlocal vertex-distance estimate",
    )
    args = ap.parse_args(argv)

    if args.n < 16:
        raise SystemExit("--n must be at least 16")

    entry = load_entry(args.source, args.id, args.component)
    pts = eval_curve(entry.coeffs, args.n)
    if args.center:
        pts = center_points(pts)

    length_before = length_closed(pts)
    if args.scale_to_declared_L:
        if not entry.declared_L or entry.declared_L <= 0:
            raise SystemExit("declared L is missing or invalid")
        scale = entry.declared_L / length_before
        pts = [mul(scale, p) for p in pts]

    write_csv(args.out, pts, header=not args.no_header)

    length_after = length_closed(pts)
    emin, emax, eavg = edge_stats(pts)
    declared_D = entry.declared_D if entry.declared_D is not None else float("nan")
    rop_proxy = (2.0 * entry.declared_L / declared_D) if entry.declared_L and entry.declared_D else float("nan")
    min_nonlocal = None if args.skip_min_dist else min_nonlocal_vertex_distance(pts)

    print(f"source: {args.source}")
    print(f"id: {entry.knot_id}")
    print(f"conway: {entry.conway}")
    print(f"coefficients: {len(entry.coeffs)}")
    print(f"vertices_written: {len(pts)}")
    print(f"out: {args.out}")
    print(f"declared_L: {entry.declared_L}")
    print(f"declared_D: {entry.declared_D}")
    print(f"declared_ropelength_proxy_2L_over_D: {rop_proxy:.9f}")
    print(f"sampled_closed_polyline_length: {length_after:.9f}")
    if entry.declared_L:
        print(f"sampled_L_minus_declared_L: {length_after - entry.declared_L:+.9e}")
    print(f"edge_length_min: {emin:.9g}")
    print(f"edge_length_avg: {eavg:.9g}")
    print(f"edge_length_max: {emax:.9g}")
    if min_nonlocal is not None:
        print(f"crude_min_nonlocal_vertex_distance_skip4: {min_nonlocal:.9g}")
        if entry.declared_D:
            print(f"crude_min_nonlocal_over_D: {min_nonlocal / entry.declared_D:.9g}")
    print("status: wrote vertex CSV for SST harness V0 input")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
