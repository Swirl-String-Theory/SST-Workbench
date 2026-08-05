#!/usr/bin/env python3
"""
Resample closed KnotPlot/Ridgerunner TXT polygons to uniform arc-length spacing.

Each component is treated separately.

Methods:
  linear         — piecewise-linear along the polygon (exact for same-N VortexLab copies)
  spline         — periodic cubic spline, then uniform arc-length sample
  spline_repair  — spline + iterative MinRad restore (default ladder upsample)
  subdivide      — edge midpoints (PL support unchanged; halves Rawdon MinRad — avoid for RR)
  auto           — spline_repair when upsampling, else linear

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

# Quality gates (strict mode, typically for upsample)
EDGE_RATIO_MAX = 1.05
LENGTH_REL_MAX = 5.0e-3
MINRAD_RATIO_MIN = 0.90
ROP_REL_MAX = 1.0e-3
SPLINE_DENSE_FACTOR = 32  # dense polyline samples per input edge before reparam

_RR_DIR = Path(__file__).resolve().parent / "ridgerunner"
if str(_RR_DIR) not in sys.path:
    sys.path.insert(0, str(_RR_DIR))


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


def polygonal_minrad(comp: list[Point]) -> float | None:
    """Discrete Rawdon min-radius over vertices (curvature part of thickness).

    At vertex i with adjacent edge lengths l_prev, l_next and turning angle
    alpha between unit edge directions:
        r_i = min(l_prev, l_next) / (2 * tan(alpha/2))
    """
    n = len(comp)
    if n < 3:
        return None
    best = float("inf")
    for i in range(n):
        p_prev = comp[(i - 1) % n]
        p = comp[i]
        p_next = comp[(i + 1) % n]
        ax, ay, az = p[0] - p_prev[0], p[1] - p_prev[1], p[2] - p_prev[2]
        bx, by, bz = p_next[0] - p[0], p_next[1] - p[1], p_next[2] - p[2]
        la = math.sqrt(ax * ax + ay * ay + az * az)
        lb = math.sqrt(bx * bx + by * by + bz * bz)
        if la <= 0.0 or lb <= 0.0:
            return 0.0
        ux, uy, uz = ax / la, ay / la, az / la
        vx, vy, vz = bx / lb, by / lb, bz / lb
        dot = max(-1.0, min(1.0, ux * vx + uy * vy + uz * vz))
        alpha = math.acos(dot)
        if alpha < 1e-12:
            continue  # nearly straight → infinite local radius
        half = alpha * 0.5
        tan_h = math.tan(half)
        if tan_h <= 0.0:
            continue
        r = min(la, lb) / (2.0 * tan_h)
        if r < best:
            best = r
    if best == float("inf"):
        return None
    return best


def resolve_method(n_in: int, n_out: int, method: str) -> str:
    m = method.lower().strip()
    if m == "auto":
        return "spline_repair" if n_out > n_in else "linear"
    if m in ("linear", "spline", "spline_repair", "subdivide"):
        return m
    raise ValueError(
        f"unknown --method {method!r}; "
        "use auto|linear|spline|spline_repair|subdivide"
    )


def resample_closed(comp: list[Point], n_out: int) -> list[Point]:
    """Uniform arc-length linear resample of a closed polygon to n_out vertices."""
    if n_out < 3:
        raise ValueError("need at least 3 points per component")
    n = len(comp)
    if n < 3:
        raise ValueError("input component needs at least 3 vertices")

    edge_lens = [_dist(comp[i], comp[(i + 1) % n]) for i in range(n)]
    total = sum(edge_lens)
    if total <= 0:
        raise ValueError("degenerate component (zero length)")

    cum = [0.0]
    for el in edge_lens:
        cum.append(cum[-1] + el)

    out: list[Point] = []
    for j in range(n_out):
        s = (j * total) / n_out
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


def _solve_periodic_tridiag(
    lower: list[float], diag: list[float], upper: list[float], rhs: list[float]
) -> list[float]:
    """Solve cyclic tridiagonal system (Sherman–Morrison / corner elimination)."""
    n = len(diag)
    if n == 1:
        return [rhs[0] / diag[0]]

    # Corners: lower[0] couples x[n-1], upper[n-1] couples x[0]
    gamma = -diag[0]
    a = list(diag)
    a[0] -= gamma
    a[n - 1] -= lower[0] * upper[n - 1] / gamma

    # Thomas on modified system
    c = list(upper)
    b = list(lower)
    d = list(rhs)
    for i in range(1, n):
        w = b[i] / a[i - 1]
        a[i] -= w * c[i - 1]
        d[i] -= w * d[i - 1]
    x = [0.0] * n
    x[n - 1] = d[n - 1] / a[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = (d[i] - c[i] * x[i + 1]) / a[i]

    # Solve for u (right-hand side of rank-1 update)
    u = [0.0] * n
    u[0] = gamma
    u[n - 1] = upper[n - 1]
    d2 = list(u)
    a2 = list(diag)
    a2[0] -= gamma
    a2[n - 1] -= lower[0] * upper[n - 1] / gamma
    c2 = list(upper)
    b2 = list(lower)
    for i in range(1, n):
        w = b2[i] / a2[i - 1]
        a2[i] -= w * c2[i - 1]
        d2[i] -= w * d2[i - 1]
    z = [0.0] * n
    z[n - 1] = d2[n - 1] / a2[n - 1]
    for i in range(n - 2, -1, -1):
        z[i] = (d2[i] - c2[i] * z[i + 1]) / a2[i]

    fact = (x[0] + lower[0] * x[n - 1] / gamma) / (
        1.0 + z[0] + lower[0] * z[n - 1] / gamma
    )
    return [xi - fact * zi for xi, zi in zip(x, z)]


def _periodic_cubic_moments(s: list[float], y: list[Point], axis: int) -> list[float]:
    """Second-derivative moments M[i] for periodic cubic spline on one axis."""
    n = len(y)
    h = [s[i + 1] - s[i] for i in range(n)]
    # Periodic: point n identified with 0; use y[0] as y[n]
    lower = [0.0] * n
    diag = [0.0] * n
    upper = [0.0] * n
    rhs = [0.0] * n
    for i in range(n):
        im = (i - 1) % n
        ip = (i + 1) % n
        hi = h[i]
        hm = h[im]
        yi = y[i][axis]
        yim = y[im][axis]
        yip = y[ip][axis]
        lower[i] = hm / 6.0
        diag[i] = (hm + hi) / 3.0
        upper[i] = hi / 6.0
        rhs[i] = (yip - yi) / hi - (yi - yim) / hm
    # Wrap corners into lower[0] / upper[n-1] convention used by solver:
    # row 0: lower[0]*x[n-1] + diag[0]*x[0] + upper[0]*x[1]
    # row n-1: lower[n-1]*x[n-2] + diag[n-1]*x[n-1] + upper[n-1]*x[0]
    # Our arrays already encode that if lower[0]=h[n-1]/6 and upper[n-1]=h[n-1]/6
    # Fix: for i=0, hm = h[n-1], so lower[0] = h[n-1]/6 couples M[n-1] — good.
    # for i=n-1, upper[n-1] = h[n-1]/6 couples M[0] — good.
    return _solve_periodic_tridiag(lower, diag, upper, rhs)


def _eval_cubic(
    s0: float,
    s1: float,
    y0: float,
    y1: float,
    m0: float,
    m1: float,
    s: float,
) -> float:
    h = s1 - s0
    t = (s - s0) / h
    a = 1.0 - t
    return (
        a * y0
        + t * y1
        + ((a * a * a - a) * m0 + (t * t * t - t) * m1) * (h * h) / 6.0
    )


def _spline_dense_polyline(comp: list[Point], dense_per_edge: int) -> list[Point]:
    n = len(comp)
    edge_lens = [_dist(comp[i], comp[(i + 1) % n]) for i in range(n)]
    s_knots = [0.0]
    for el in edge_lens:
        s_knots.append(s_knots[-1] + el)
    total = s_knots[-1]
    if total <= 0:
        raise ValueError("degenerate component (zero length)")

    mx = _periodic_cubic_moments(s_knots, comp, 0)
    my = _periodic_cubic_moments(s_knots, comp, 1)
    mz = _periodic_cubic_moments(s_knots, comp, 2)

    # Extend moments periodically for last segment (index n-1 → n≡0)
    mx_ext = mx + [mx[0]]
    my_ext = my + [my[0]]
    mz_ext = mz + [mz[0]]
    y_ext = list(comp) + [comp[0]]

    dense: list[Point] = []
    for i in range(n):
        s0, s1 = s_knots[i], s_knots[i + 1]
        steps = max(2, dense_per_edge)
        for k in range(steps):
            # skip duplicate knot at start of each edge except first
            if i > 0 and k == 0:
                continue
            t = k / steps
            s = s0 + t * (s1 - s0)
            dense.append(
                (
                    _eval_cubic(
                        s0, s1, y_ext[i][0], y_ext[i + 1][0], mx_ext[i], mx_ext[i + 1], s
                    ),
                    _eval_cubic(
                        s0, s1, y_ext[i][1], y_ext[i + 1][1], my_ext[i], my_ext[i + 1], s
                    ),
                    _eval_cubic(
                        s0, s1, y_ext[i][2], y_ext[i + 1][2], mz_ext[i], mz_ext[i + 1], s
                    ),
                )
            )
    return dense


def resample_closed_spline(comp: list[Point], n_out: int) -> list[Point]:
    """Periodic cubic spline → dense polyline → uniform arc-length sample."""
    if n_out < 3:
        raise ValueError("need at least 3 points per component")
    if len(comp) < 3:
        raise ValueError("input component needs at least 3 vertices")
    dense = _spline_dense_polyline(comp, SPLINE_DENSE_FACTOR)
    return resample_closed(dense, n_out)


def resample_closed_subdivide(comp: list[Point], n_out: int) -> list[Point]:
    """Insert one midpoint per edge (N → 2N). Preserves the PL curve exactly.

    Warning: Rawdon MinRad halves when incident edges shorten, so discrete
    ropelength roughly doubles — unsuitable as a Ridgerunner seed.
    """
    n = len(comp)
    if n < 3:
        raise ValueError("input component needs at least 3 vertices")
    if n_out != 2 * n:
        raise ValueError(
            f"subdivide requires n_out == 2*n_in (got n_in={n}, n_out={n_out})"
        )
    out: list[Point] = []
    for i in range(n):
        a = comp[i]
        b = comp[(i + 1) % n]
        out.append(a)
        out.append(
            (
                0.5 * (a[0] + b[0]),
                0.5 * (a[1] + b[1]),
                0.5 * (a[2] + b[2]),
            )
        )
    return out


def _vertex_minrad_and_straighten_dir(
    comp: list[Point], i: int
) -> tuple[float, Point]:
    """Rawdon radius at vertex i and a unit direction that reduces turning."""
    n = len(comp)
    p_prev = comp[(i - 1) % n]
    p = comp[i]
    p_next = comp[(i + 1) % n]
    ax, ay, az = p[0] - p_prev[0], p[1] - p_prev[1], p[2] - p_prev[2]
    bx, by, bz = p_next[0] - p[0], p_next[1] - p[1], p_next[2] - p[2]
    la = math.sqrt(ax * ax + ay * ay + az * az)
    lb = math.sqrt(bx * bx + by * by + bz * bz)
    if la <= 0.0 or lb <= 0.0:
        return 0.0, (0.0, 0.0, 0.0)
    ux, uy, uz = ax / la, ay / la, az / la
    vx, vy, vz = bx / lb, by / lb, bz / lb
    dot = max(-1.0, min(1.0, ux * vx + uy * vy + uz * vz))
    alpha = math.acos(dot)
    if alpha < 1e-12:
        return float("inf"), (0.0, 0.0, 0.0)
    r = min(la, lb) / (2.0 * math.tan(alpha * 0.5))
    nx, ny, nz = ux - vx, uy - vy, uz - vz
    nn = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return r, (-nx / nn, -ny / nn, -nz / nn)


def restore_minrad(
    comp: list[Point],
    target: float,
    *,
    max_iters: int = 4000,
    step: float = 5.0e-5,
) -> list[Point]:
    """Nudge sharpest vertices to recover Rawdon MinRad after smooth upsample."""
    if target <= 0:
        raise ValueError("minrad restore target must be positive")
    out = [list(p) for p in comp]
    mean_e = closed_length(comp) / max(len(comp), 1)
    step = max(step, 5.0e-5 * mean_e)
    best_pts: list[Point] = [tuple(p) for p in out]  # type: ignore[misc]
    best_mr = polygonal_minrad(best_pts) or 0.0
    for _ in range(max_iters):
        pts: list[Point] = [tuple(p) for p in out]  # type: ignore[misc]
        mr = polygonal_minrad(pts)
        if mr is not None and mr >= target:
            return pts
        if mr is not None and mr > best_mr:
            best_mr = mr
            best_pts = list(pts)
        worst_i = None
        worst_r = float("inf")
        worst_d = (0.0, 0.0, 0.0)
        for i in range(len(out)):
            r, d = _vertex_minrad_and_straighten_dir(pts, i)
            if r < worst_r:
                worst_r = r
                worst_i = i
                worst_d = d
        if worst_i is None or worst_r == float("inf"):
            break
        out[worst_i][0] += step * worst_d[0]
        out[worst_i][1] += step * worst_d[1]
        out[worst_i][2] += step * worst_d[2]
    # Prefer best MinRad seen if target not reached
    final: list[Point] = [tuple(p) for p in out]  # type: ignore[misc]
    final_mr = polygonal_minrad(final) or 0.0
    return best_pts if best_mr >= final_mr else final


def resample_closed_spline_repair(comp: list[Point], n_out: int) -> list[Point]:
    """Spline upsample, then restore source MinRad (keeps discrete Rop near source)."""
    mr_in = polygonal_minrad(comp)
    spl = resample_closed_spline(comp, n_out)
    if mr_in is None or mr_in <= 0:
        return spl
    mr_spl = polygonal_minrad(spl)
    if mr_spl is not None and mr_spl >= mr_in:
        return spl
    return restore_minrad(spl, mr_in)


def resample_component(
    comp: list[Point], n_out: int, *, method: str
) -> tuple[list[Point], str]:
    chosen = resolve_method(len(comp), n_out, method)
    if chosen == "spline":
        return resample_closed_spline(comp, n_out), chosen
    if chosen == "spline_repair":
        return resample_closed_spline_repair(comp, n_out), chosen
    if chosen == "subdivide":
        return resample_closed_subdivide(comp, n_out), chosen
    return resample_closed(comp, n_out), chosen


def thickness_proxies_stable(
    components: list[list[Point]],
    *,
    arc_window: float,
    include_minrad: bool = True,
) -> dict[str, float | None]:
    """D_proxy / R_proxy with a fixed arc-length exclusion window.

    Unlike select_knotplot_seed.thickness_proxies (window ~ 4·mean_edge), this
    is stable across vertex doubling. Set include_minrad=False when comparing
    PL-preserving subdivide (Rawdon minrad halves when edge lengths halve).
    """
    from select_knotplot_seed import (
        d_inter,
        d_self_nonlocal,
        minrad_component,
        total_length,
    )

    minrads = [minrad_component(c) for c in components]
    minrad = min(minrads) if minrads else float("inf")
    self_ds = [d_self_nonlocal(c, arc_window) for c in components]
    d_self = min(self_ds) if self_ds else float("inf")
    d_ic = float("inf")
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            d_ic = min(d_ic, d_inter(components[i], components[j]))
    candidates: list[float] = [d_self]
    if include_minrad:
        candidates.append(2.0 * minrad)
    if len(components) > 1 and math.isfinite(d_ic):
        candidates.append(d_ic)
    finite = [x for x in candidates if math.isfinite(x) and x > 0]
    d_proxy = min(finite) if finite else None
    L = total_length(components)
    r_proxy = (L / d_proxy) if d_proxy and d_proxy > 0 else None
    return {
        "minrad_min": minrad if math.isfinite(minrad) else None,
        "d_self_nonlocal": d_self if math.isfinite(d_self) else None,
        "d_inter": d_ic if math.isfinite(d_ic) and len(components) > 1 else None,
        "D_proxy": d_proxy,
        "length_over_diameter_proxy": r_proxy,
        "arc_window": arc_window,
        "include_minrad": include_minrad,
    }


def relative_rop_change(
    comps_in: list[list[Point]],
    comps_out: list[list[Point]],
    *,
    include_minrad: bool = True,
) -> tuple[float | None, dict[str, float | None], dict[str, float | None]]:
    """Return (δ_R = R_out/R_in - 1, proxy_in, proxy_out).

    Uses the same absolute arc window (5% of source length) on both sides so
    vertex doubling does not spuriously change nonlocal self-distance.
    """
    L_in = sum(closed_length(c) for c in comps_in)
    window = max(0.05 * L_in, 1e-15)
    pin = thickness_proxies_stable(
        comps_in, arc_window=window, include_minrad=include_minrad
    )
    pout = thickness_proxies_stable(
        comps_out, arc_window=window, include_minrad=include_minrad
    )
    r_in = pin.get("length_over_diameter_proxy")
    r_out = pout.get("length_over_diameter_proxy")
    if r_in is None or r_out is None or r_in <= 0:
        return None, pin, pout
    return (r_out / r_in) - 1.0, pin, pout


def transfer_sidecar_path(u_txt: Path) -> Path:
    """u1200.txt → u1200.resample.json"""
    return u_txt.with_name(u_txt.stem + ".resample.json")


def transfer_sidecar_is_stale(u_or_json: Path) -> bool:
    """True if upsample transfer sidecar is missing or fails Rop-preservation policy.

    Stale when:
      - sidecar JSON missing
      - upsampled with bare spline or subdivide (no MinRad repair)
      - relative_rop_change missing or δ >= ROP_REL_MAX (collapse; negative OK)
      - validation_errors non-empty
    """
    path = Path(u_or_json)
    if path.suffix.lower() == ".json" or path.name.endswith(".resample.json"):
        meta_path = path
    else:
        meta_path = transfer_sidecar_path(path)
    if not meta_path.is_file():
        return True
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    if meta.get("validation_errors"):
        return True
    upsampled = bool(meta.get("upsampled"))
    methods = meta.get("method_per_component") or []
    if upsampled and any(m in ("spline", "subdivide") for m in methods):
        return True
    rel = meta.get("relative_rop_change")
    if rel is None:
        return True
    try:
        # One-sided: only Rop *increase* (thinning/collapse) marks stale.
        if float(rel) >= ROP_REL_MAX:
            return True
    except (TypeError, ValueError):
        return True
    return False


def clear_stale_ladder_rung(sdir: Path, n: int) -> list[str]:
    """Remove u{N} transfer and n{N}c/s/e/p aliases so the rung can rebuild."""
    sdir = Path(sdir)
    deleted: list[str] = []
    patterns = [
        f"u{n}.txt",
        f"u{n}.resample.json",
        f"n{n}c.txt",
        f"n{n}s.txt",
        f"n{n}e.txt",
        f"n{n}p.txt",
        f"n{n}c.metrics.json",
        f"n{n}s.metrics.json",
        f"n{n}e.metrics.json",
        f"n{n}p.metrics.json",
    ]
    for name in patterns:
        p = sdir / name
        if p.is_file():
            p.unlink()
            deleted.append(str(p))
    return deleted


def files_byte_identical(a: Path, b: Path) -> bool:
    return Path(a).read_bytes() == Path(b).read_bytes()


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


def evaluate_gates(
    *,
    comps_in: list[list[Point]],
    comps_out: list[list[Point]],
    counts: list[int],
    strict: bool,
    upsampled: bool,
    methods: list[str] | None = None,
) -> tuple[list[str], list[str], list[dict], dict]:
    """Return (warnings, errors, per_comp meta, rop_meta)."""
    warnings: list[str] = []
    errors: list[str] = []
    per_comp: list[dict] = []
    src_total = sum(closed_length(c) for c in comps_in)
    out_total = sum(closed_length(c) for c in comps_out)
    rel = (out_total - src_total) / src_total if src_total > 0 else None
    methods = list(methods or [])
    all_subdivide = bool(methods) and all(m == "subdivide" for m in methods)

    for i, (cin, cout, n) in enumerate(zip(comps_in, comps_out, counts)):
        st = edge_stats(cout)
        mr_in = polygonal_minrad(cin)
        mr_out = polygonal_minrad(cout)
        mr_ratio = (
            (mr_out / mr_in)
            if (mr_in is not None and mr_out is not None and mr_in > 0)
            else None
        )
        per_comp.append(
            {
                "index": i,
                "vertices_in": len(cin),
                "vertices_out": n,
                "length_in": closed_length(cin),
                "length_out": closed_length(cout),
                "minrad_in": mr_in,
                "minrad_out": mr_out,
                "minrad_ratio": mr_ratio,
                **st,
            }
        )
        er = st.get("edge_ratio")
        cv = st.get("edge_cv")
        if er is not None and er > 1.01:
            warnings.append(f"comp{i}: edge_ratio={er:.6g} > 1.01")
        if cv is not None and cv > 0.005:
            warnings.append(f"comp{i}: edge_cv={cv:.6g} > 0.5%")
        if er is not None and er >= EDGE_RATIO_MAX:
            msg = f"comp{i}: edge_ratio={er:.6g} >= {EDGE_RATIO_MAX}"
            (errors if strict else warnings).append(msg)
        if mr_ratio is not None and mr_ratio < MINRAD_RATIO_MIN:
            msg = (
                f"comp{i}: minrad_ratio={mr_ratio:.6g} < {MINRAD_RATIO_MIN} "
                f"(minrad_in={mr_in:.6g}, minrad_out={mr_out:.6g})"
            )
            # Midpoint subdivide halves Rawdon minrad (shorter edges, same turn);
            # that is not geometric thickness loss — warn only.
            if all_subdivide:
                warnings.append(msg + " (expected for subdivide)")
            elif strict and upsampled:
                errors.append(msg)
            else:
                warnings.append(msg)

    if rel is not None and abs(rel) >= 0.001:
        warnings.append(f"length change {rel:.6%} (prefer < 0.1%)")
    if rel is not None and abs(rel) >= LENGTH_REL_MAX:
        msg = f"length change {rel:.6%} >= {LENGTH_REL_MAX:.3%}"
        (errors if strict else warnings).append(msg)

    # Prefer radius-style Rop = L / min(MinRad, d_self/2) via include_minrad.
    delta_r, pin, pout = relative_rop_change(
        comps_in, comps_out, include_minrad=True
    )
    # Also record MinRad-only Rop (matches RR when MinRad binds).
    mr_in = min(
        (polygonal_minrad(c) for c in comps_in if polygonal_minrad(c) is not None),
        default=None,
    )
    mr_out = min(
        (polygonal_minrad(c) for c in comps_out if polygonal_minrad(c) is not None),
        default=None,
    )
    rop_mr_in = (src_total / mr_in) if mr_in and mr_in > 0 else None
    rop_mr_out = (out_total / mr_out) if mr_out and mr_out > 0 else None
    delta_rop_mr = (
        (rop_mr_out / rop_mr_in) - 1.0
        if rop_mr_in and rop_mr_out and rop_mr_in > 0
        else None
    )
    # Gate on MinRad-rop when available (RR thickness on tight knots); else proxy.
    # spline_repair intentionally restores MinRad, so MinRad-Rop can move slightly
    # even when the geometric thickness proxy is preserved — gate on proxy then.
    all_repair = bool(methods) and all(m == "spline_repair" for m in methods)
    if all_repair and delta_r is not None:
        gate_delta = delta_r
        rop_gate = "proxy_spline_repair"
    elif delta_rop_mr is not None:
        gate_delta = delta_rop_mr
        rop_gate = "minrad"
    else:
        gate_delta = delta_r
        rop_gate = "proxy"
    r_in = pin.get("length_over_diameter_proxy")
    r_out = pout.get("length_over_diameter_proxy")
    rop_meta = {
        "D_proxy_in": pin.get("D_proxy"),
        "D_proxy_out": pout.get("D_proxy"),
        "R_proxy_in": r_in,
        "R_proxy_out": r_out,
        "relative_rop_change": gate_delta,
        "relative_rop_proxy_change": delta_r,
        "relative_rop_minrad_change": delta_rop_mr,
        "rop_minrad_in": rop_mr_in,
        "rop_minrad_out": rop_mr_out,
        "rop_gate": rop_gate,
    }
    if gate_delta is None:
        msg = "Rop unavailable (cannot enforce ropelength-preservation gate)"
        if strict and upsampled:
            errors.append(msg)
        else:
            warnings.append(msg)
    else:
        if abs(gate_delta) >= 0.001:
            warnings.append(
                f"Rop change {gate_delta:.6%} (prefer |d| < {ROP_REL_MAX:.1%})"
            )
        # One-sided strict gate: reject collapse (Rop up), allow thickening
        # from denser sampling / MinRad restore (Rop down).
        if gate_delta >= ROP_REL_MAX:
            msg = f"Rop change {gate_delta:.6%} >= {ROP_REL_MAX:.3%} (collapse)"
            if strict and upsampled:
                errors.append(msg)
            else:
                warnings.append(msg)

    return warnings, errors, per_comp, rop_meta


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
    ap.add_argument(
        "--method",
        choices=("auto", "linear", "spline", "spline_repair", "subdivide"),
        default="auto",
        help=(
            "resample method (default: auto = spline_repair when upsampling)"
        ),
    )
    ap.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="fail on gate violations (default: on when any component upsamples)",
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

    upsampled = any(n_out > len(c) for c, n_out in zip(comps, counts))
    strict = args.strict if args.strict is not None else upsampled

    methods_used: list[str] = []
    try:
        out_comps = []
        for c, n in zip(comps, counts):
            oc, chosen = resample_component(c, n, method=args.method)
            out_comps.append(oc)
            methods_used.append(chosen)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    src_lens = [closed_length(c) for c in comps]
    out_lens = [closed_length(c) for c in out_comps]
    src_total = sum(src_lens)
    out_total = sum(out_lens)
    rel = (out_total - src_total) / src_total if src_total > 0 else None

    warnings, errors, per_comp, rop_meta = evaluate_gates(
        comps_in=comps,
        comps_out=out_comps,
        counts=counts,
        strict=strict,
        upsampled=upsampled,
        methods=methods_used,
    )

    stem = output_stem(src, counts)
    out_txt = args.output.resolve() if args.output else (src.parent / f"{stem}.txt")
    out_json = transfer_sidecar_path(out_txt)
    if args.output is None:
        out_json = src.parent / f"{stem}.resample.json"

    meta = {
        "source": str(src),
        "output": str(out_txt),
        "method_requested": args.method,
        "method_per_component": methods_used,
        "strict": strict,
        "upsampled": upsampled,
        "component_count": len(comps),
        "vertices_per_component_in": [len(c) for c in comps],
        "vertices_per_component_out": counts,
        "length_in": src_total,
        "length_out": out_total,
        "relative_length_change": rel,
        "D_proxy_in": rop_meta.get("D_proxy_in"),
        "D_proxy_out": rop_meta.get("D_proxy_out"),
        "R_proxy_in": rop_meta.get("R_proxy_in"),
        "R_proxy_out": rop_meta.get("R_proxy_out"),
        "relative_rop_change": rop_meta.get("relative_rop_change"),
        "relative_rop_proxy_change": rop_meta.get("relative_rop_proxy_change"),
        "relative_rop_minrad_change": rop_meta.get("relative_rop_minrad_change"),
        "rop_gate": rop_meta.get("rop_gate"),
        "components": per_comp,
        "validation_warnings": warnings,
        "validation_errors": errors,
        "gates": {
            "edge_ratio_max": EDGE_RATIO_MAX,
            "length_rel_max": LENGTH_REL_MAX,
            "minrad_ratio_min": MINRAD_RATIO_MIN,
            "rop_rel_max": ROP_REL_MAX,
            "rop_gate_mode": "collapse_only",
        },
        "notes": (
            "Ladder upsample uses spline_repair (cubic spline + MinRad restore). "
            "Strict Rop gate is one-sided: error only if Rop increases "
            f"(>= {ROP_REL_MAX:.1%}, collapse); negative dR (apparent thickening) "
            "warns only. Metric: thickness proxy for spline_repair, else "
            "MinRad-Rop. Bare spline / subdivide sidecars are treated as stale."
        ),
    }

    print(f"Method: requested={args.method} used={methods_used} strict={strict}")
    if warnings:
        print("VALIDATION WARNINGS:")
        for w in warnings:
            print(f"  {w}")
    if errors:
        # Sidecar only — do not leave a failing transfer TXT for ladder resume.
        out_json.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote: {out_json}")
        print("VALIDATION ERRORS:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        print(
            "ERROR: resample quality gates failed "
            "(use --no-strict to write anyway, or --method spline_repair).",
            file=sys.stderr,
        )
        return 2

    write_xyz_txt(out_txt, out_comps)
    out_json.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote: {out_txt}")
    print(f"Wrote: {out_json}")
    if not warnings:
        print("Validation: edge-ratio / length / minrad / Rop within gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
