#!/usr/bin/env python3
"""
Resample closed KnotPlot/Ridgerunner TXT polygons to uniform arc-length spacing.

Each component is treated separately. Cumulative polygonal arc-length:

    s_j = j * L / N,  j = 0 .. N-1

Linear interpolation between surrounding Ridgerunner vertices.
No smoothing, scaling, centering, or rotation.

Writes:
  {stem}_uniform_N{N}.txt
  {stem}_uniform_N{N}.resample.json

Does not modify the input (Ridgerunner polish stays the audit reference).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

Point = tuple[float, float, float]


def parse_xyz_txt(path: Path) -> list[list[Point]]:
    components: list[list[Point]] = []
    current: list[Point] = []
    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw.strip()
        if not line:
            if current:
                components.append(current)
                current = []
            continue
        if line.startswith("#"):
            continue
        fields = line.replace(",", " ").split()
        if len(fields) < 3:
            raise ValueError(
                f"{path}:{line_number}: expected at least three numeric fields"
            )
        try:
            pt = (float(fields[0]), float(fields[1]), float(fields[2]))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: invalid XYZ") from exc
        if not all(math.isfinite(v) for v in pt):
            raise ValueError(f"{path}:{line_number}: non-finite coordinate")
        current.append(pt)
    if current:
        components.append(current)
    if not components:
        raise ValueError(f"{path}: no XYZ coordinates found")
    return components


def write_xyz_txt(path: Path, components: list[list[Point]]) -> None:
    lines: list[str] = []
    for i, comp in enumerate(components):
        if i:
            lines.append("")
        for x, y, z in comp:
            lines.append(f"{x:.17g} {y:.17g} {z:.17g}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _dist(a: Point, b: Point) -> float:
    return math.sqrt(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
    )


def closed_length(comp: list[Point]) -> float:
    n = len(comp)
    if n < 2:
        return 0.0
    return sum(_dist(comp[i], comp[(i + 1) % n]) for i in range(n))


def edge_stats(comp: list[Point]) -> dict[str, float | None]:
    n = len(comp)
    if n < 2:
        return {
            "edge_min": None,
            "edge_max": None,
            "edge_mean": None,
            "edge_ratio": None,
            "edge_cv": None,
        }
    lengths = [_dist(comp[i], comp[(i + 1) % n]) for i in range(n)]
    mn = min(lengths)
    mx = max(lengths)
    mean = sum(lengths) / len(lengths)
    var = sum((L - mean) ** 2 for L in lengths) / len(lengths)
    std = math.sqrt(var)
    return {
        "edge_min": mn,
        "edge_max": mx,
        "edge_mean": mean,
        "edge_ratio": (mx / mn) if mn > 0 else None,
        "edge_cv": (std / mean) if abs(mean) > 1e-30 else None,
    }


def resample_closed(comp: list[Point], n_out: int) -> list[Point]:
    """Uniform arc-length resample of a closed polygon to n_out vertices."""
    if n_out < 3:
        raise ValueError("need at least 3 points per component")
    n = len(comp)
    if n < 3:
        raise ValueError("input component needs at least 3 vertices")

    edge_lens = [_dist(comp[i], comp[(i + 1) % n]) for i in range(n)]
    total = sum(edge_lens)
    if total <= 0:
        raise ValueError("degenerate component (zero length)")

    # Cumulative arc length at vertex i (s[0]=0, s[n]=total)
    cum = [0.0]
    for el in edge_lens:
        cum.append(cum[-1] + el)

    out: list[Point] = []
    for j in range(n_out):
        s = (j * total) / n_out
        # Find edge with cum[i] <= s < cum[i+1] (wrap: s==total → vertex 0)
        if s >= total or abs(s - total) < 1e-15 * total:
            out.append(comp[0])
            continue
        i = 0
        while i < n and cum[i + 1] <= s:
            i += 1
        if i >= n:
            out.append(comp[0])
            continue
        el = edge_lens[i]
        if el <= 0:
            out.append(comp[i])
            continue
        t = (s - cum[i]) / el
        a = comp[i]
        b = comp[(i + 1) % n]
        out.append(
            (
                a[0] + t * (b[0] - a[0]),
                a[1] + t * (b[1] - a[1]),
                a[2] + t * (b[2] - a[2]),
            )
        )
    return out


def resolve_counts(
    ncomp: int,
    points: int | None,
    points_per_component: list[int] | None,
) -> list[int]:
    if points_per_component is not None:
        if len(points_per_component) != ncomp:
            raise ValueError(
                f"--points-per-component has {len(points_per_component)} "
                f"entries but input has {ncomp} component(s)"
            )
        if any(p < 3 for p in points_per_component):
            raise ValueError("each component needs at least 3 points")
        return points_per_component
    if points is None:
        points = 300
    if points < 3:
        raise ValueError("--points must be at least 3")
    return [points] * ncomp


def output_stem(src: Path, counts: list[int]) -> str:
    """foo_polish.txt + all-300 → foo_polish_uniform_N300"""
    tag = counts[0] if len(set(counts)) == 1 else "mixed"
    if len(set(counts)) == 1:
        return f"{src.stem}_uniform_N{tag}"
    joined = "-".join(str(c) for c in counts)
    return f"{src.stem}_uniform_N{joined}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="closed knot/link TXT (XYZ)")
    ap.add_argument(
        "--points",
        type=int,
        default=None,
        help="vertices per component (default 300 if neither count option set)",
    )
    ap.add_argument(
        "--points-per-component",
        type=str,
        default=None,
        help="comma-separated counts, e.g. 300,300",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help="optional output TXT path (default: {stem}_uniform_N{N}.txt)",
    )
    args = ap.parse_args(argv)

    src = args.input.resolve()
    if not src.is_file():
        print(f"ERROR: input not found: {src}", file=sys.stderr)
        return 1

    ppc: list[int] | None = None
    if args.points_per_component:
        ppc = [int(x.strip()) for x in args.points_per_component.split(",") if x.strip()]

    try:
        comps = parse_xyz_txt(src)
        counts = resolve_counts(len(comps), args.points, ppc)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    src_lens = [closed_length(c) for c in comps]
    src_total = sum(src_lens)
    out_comps = [resample_closed(c, n) for c, n in zip(comps, counts)]
    out_lens = [closed_length(c) for c in out_comps]
    out_total = sum(out_lens)
    rel = (out_total - src_total) / src_total if src_total > 0 else None

    stem = output_stem(src, counts)
    out_txt = args.output.resolve() if args.output else (src.parent / f"{stem}.txt")
    out_json = out_txt.with_suffix(".resample.json")
    # Prefer …_uniform_N300.resample.json next to txt even if --output overrides
    if args.output is None:
        out_json = src.parent / f"{stem}.resample.json"

    write_xyz_txt(out_txt, out_comps)

    per_comp = []
    warnings: list[str] = []
    for i, (oc, n) in enumerate(zip(out_comps, counts)):
        st = edge_stats(oc)
        per_comp.append(
            {
                "index": i,
                "vertices": n,
                "length_in": src_lens[i],
                "length_out": out_lens[i],
                **st,
            }
        )
        er = st.get("edge_ratio")
        cv = st.get("edge_cv")
        if er is not None and er > 1.01:
            warnings.append(f"comp{i}: edge_ratio={er:.6g} > 1.01")
        if cv is not None and cv > 0.005:
            warnings.append(f"comp{i}: edge_cv={cv:.6g} > 0.5%")

    if rel is not None and abs(rel) >= 0.001:
        warnings.append(f"length change {rel:.6%} (prefer < 0.1%)")

    meta = {
        "source": str(src),
        "output": str(out_txt),
        "component_count": len(comps),
        "vertices_per_component_in": [len(c) for c in comps],
        "vertices_per_component_out": counts,
        "length_in": src_total,
        "length_out": out_total,
        "relative_length_change": rel,
        "components": per_comp,
        "validation_warnings": warnings,
        "notes": (
            "Uniform arc-length resample for VortexLab; "
            "do not re-run Ridgerunner on this file."
        ),
    }
    out_json.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote: {out_txt}")
    print(f"Wrote: {out_json}")
    if warnings:
        print("VALIDATION WARNINGS:")
        for w in warnings:
            print(f"  {w}")
    else:
        print("Validation: edge-ratio/CV/length within preferred gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
