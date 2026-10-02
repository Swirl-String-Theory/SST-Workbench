from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from . import _config

ROPELENGTH_TARGETS = {
    "3_1": 32.7436,
    "trefoil": 32.7436,
    "4_1": 42.0887,
    "figure8": 42.0887,
    "figure-eight": 42.0887,
}

STATUS = {
    "rayleigh": "ORTHODOX_ANALOGUE: Rayleigh discriminant is orthodox for axisymmetric inviscid rotating flow.",
    "knot_projection": "RESEARCH_TRACK: shell-averaged knot projection is a diagnostic proxy, not a full non-axisymmetric vortex solver.",
    "rocking": "RESEARCH_TRACK: rocking/breathing are classifier observables; use Ridgerunner outputs for final claims.",
    "projection": "PROTOTYPE: Pi_I(V) support is strut-first; kink gradients are logged but not enforced in this first harness.",
}


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_cpp_backend(*, force_build: bool = False, build_verbose: bool = False):
    try:
        from .build_ext_if_needed import build_if_needed

        build_if_needed(force=force_build, verbose=build_verbose)
        mod = __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=["*"])
        return mod
    except Exception as exc:
        if build_verbose:
            print(f"{_config.LOG_PREFIX} C++ backend unavailable: {exc}", file=sys.stderr)
        return None


def _backend(*, force_python: bool, skip_build: bool, force_build: bool, build_verbose: bool):
    if force_python or skip_build:
        return None
    return _load_cpp_backend(force_build=force_build, build_verbose=build_verbose)


def load_vertices_csv(path: str | Path) -> np.ndarray:
    rows: list[list[float]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        has_header = any(c.isalpha() for c in sample.splitlines()[0]) if sample.splitlines() else False
        if has_header:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append([float(row["x"]), float(row["y"]), float(row["z"])])
        else:
            reader2 = csv.reader(fh)
            for row in reader2:
                if len(row) >= 3:
                    rows.append([float(row[0]), float(row[1]), float(row[2])])
    if len(rows) < 8:
        raise ValueError("A closed knot centerline needs at least 8 vertices")
    return np.asarray(rows, dtype=float)


def save_vertices_csv(path: str | Path, vertices: np.ndarray) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["x", "y", "z"])
        for row in np.asarray(vertices, dtype=float):
            w.writerow([f"{row[0]:.17g}", f"{row[1]:.17g}", f"{row[2]:.17g}"])


def _closed_segment_lengths(v: np.ndarray) -> np.ndarray:
    return np.linalg.norm(np.roll(v, -1, axis=0) - v, axis=1)


def polygon_length(v: np.ndarray) -> float:
    return float(np.sum(_closed_segment_lengths(v)))


def resample_closed(v: np.ndarray, n: int) -> np.ndarray:
    if n < 8:
        raise ValueError("n must be at least 8")
    v = np.asarray(v, dtype=float)
    seg = _closed_segment_lengths(v)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    if total <= 0:
        raise ValueError("degenerate centerline")
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = np.empty((n, 3), dtype=float)
    j = 0
    for k, t in enumerate(targets):
        while j + 1 < len(s) and s[j + 1] <= t:
            j += 1
        denom = s[j + 1] - s[j]
        frac = 0.0 if denom <= 0 else (t - s[j]) / denom
        out[k] = (1.0 - frac) * v[j % len(v)] + frac * v[(j + 1) % len(v)]
    return out


def normalize_centerline(v: np.ndarray, *, target_length: float | None = None) -> np.ndarray:
    out = np.asarray(v, dtype=float).copy()
    out -= np.mean(out, axis=0)
    if target_length is not None:
        length = polygon_length(out)
        if length <= 0:
            raise ValueError("cannot scale degenerate centerline")
        out *= target_length / length
    return out


def generate_torus_knot(n: int, *, p: int = 2, q: int = 3, major: float = 2.0, minor: float = 0.75) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    x = (major + minor * np.cos(q * t)) * np.cos(p * t)
    y = (major + minor * np.cos(q * t)) * np.sin(p * t)
    z = minor * np.sin(q * t)
    return np.column_stack([x, y, z])


def generate_figure_eight(n: int) -> np.ndarray:
    # Standard smooth figure-eight-like embedding used for diagnostics; not an ideal 4_1 minimizer.
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    x = (2.0 + np.cos(2.0 * t)) * np.cos(3.0 * t)
    y = (2.0 + np.cos(2.0 * t)) * np.sin(3.0 * t)
    z = np.sin(4.0 * t)
    return np.column_stack([x, y, z])


def generate_centerline(knot_id: str, n: int) -> np.ndarray:
    key = knot_id.lower()
    if key in {"3_1", "trefoil"}:
        v = generate_torus_knot(n, p=2, q=3)
    elif key in {"4_1", "figure8", "figure-eight", "figure_eight"}:
        v = generate_figure_eight(n)
    else:
        raise ValueError(f"unknown knot_id={knot_id!r}; use 3_1 or 4_1")
    target = ROPELENGTH_TARGETS.get(key, None)
    return normalize_centerline(resample_closed(v, n), target_length=target)


def prepare_centerline(knot_id: str, n: int, input_csv: str | Path | None) -> np.ndarray:
    if input_csv:
        v = load_vertices_csv(input_csv)
        v = resample_closed(v, n)
        return normalize_centerline(v, target_length=ROPELENGTH_TARGETS.get(knot_id.lower()))
    return generate_centerline(knot_id, n)


def flatten(v: np.ndarray) -> list[float]:
    return [float(x) for x in np.asarray(v, dtype=float).reshape(-1)]


def _quadrupole_rg2_py(v: np.ndarray) -> dict[str, Any]:
    vv = np.asarray(v, dtype=float)
    c = np.mean(vv, axis=0)
    x = vv - c
    rg2 = float(np.mean(np.sum(x * x, axis=1)))
    q = np.zeros((3, 3), dtype=float)
    for row in x:
        r2 = float(np.dot(row, row))
        q += np.outer(row, row) - (r2 / 3.0) * np.eye(3)
    q /= len(vv)
    return {"Q": q.tolist(), "Rg2": rg2, "centroid": c.tolist()}


def quadrupole_rg2(v: np.ndarray, *, backend=None) -> dict[str, Any]:
    if backend is not None:
        try:
            return backend.quadrupole_rg2(flatten(v))
        except Exception as exc:
            print(f"{_config.LOG_PREFIX} C++ quadrupole failed: {exc}", file=sys.stderr)
    return _quadrupole_rg2_py(v)


def mirror_matrix(axis: str = "x") -> np.ndarray:
    p = np.eye(3)
    idx = {"x": 0, "y": 1, "z": 2}.get(axis.lower())
    if idx is None:
        raise ValueError("mirror_axis must be x, y, or z")
    p[idx, idx] = -1.0
    return p


def q_perp(q: Iterable[Iterable[float]], omega_axis: str = "z") -> np.ndarray:
    q_arr = np.asarray(q, dtype=float)
    idx = {"x": 0, "y": 1, "z": 2}[omega_axis.lower()]
    p = np.eye(3)
    p[idx, idx] = 0.0
    return p @ q_arr @ p


def fro_norm(m: np.ndarray) -> float:
    return float(np.linalg.norm(m, ord="fro"))


def _biot_savart_py(v: np.ndarray, samples: np.ndarray, gamma: float, epsilon_bs: float) -> np.ndarray:
    vv = np.asarray(v, dtype=float)
    ss = np.asarray(samples, dtype=float)
    out = np.zeros_like(ss, dtype=float)
    eps2 = epsilon_bs * epsilon_bs
    coeff = gamma / (4.0 * math.pi)
    nxt = np.roll(vv, -1, axis=0)
    dl = nxt - vv
    mid = 0.5 * (vv + nxt)
    for k, x in enumerate(ss):
        r = x[None, :] - mid
        denom = np.power(np.sum(r * r, axis=1) + eps2, 1.5)
        out[k] = coeff * np.sum(np.cross(dl, r) / denom[:, None], axis=0)
    return out


def biot_savart_velocity(v: np.ndarray, samples: np.ndarray, gamma: float, epsilon_bs: float, *, backend=None) -> np.ndarray:
    if backend is not None:
        try:
            flat = backend.biot_savart_velocity(flatten(v), flatten(samples), float(gamma), float(epsilon_bs))
            return np.asarray(flat, dtype=float).reshape((-1, 3))
        except Exception as exc:
            print(f"{_config.LOG_PREFIX} C++ Biot-Savart failed: {exc}", file=sys.stderr)
    return _biot_savart_py(v, samples, gamma, epsilon_bs)


def cylindrical_basis(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = v[:, 0]
    y = v[:, 1]
    r = np.sqrt(x * x + y * y)
    e_theta = np.zeros_like(v)
    ok = r > 1e-14
    e_theta[ok, 0] = -y[ok] / r[ok]
    e_theta[ok, 1] = x[ok] / r[ok]
    return r, e_theta


def shell_average_u_theta(
    v: np.ndarray,
    *,
    epsilon_bs: float,
    shell_dr: float,
    shell_h: float,
    gamma: float,
    backend=None,
) -> dict[str, Any]:
    if epsilon_bs <= 0 or shell_dr <= 0 or shell_h <= 0:
        raise ValueError("epsilon_bs, shell_dr, shell_h must be positive")
    u = biot_savart_velocity(v, v, gamma, epsilon_bs, backend=backend)
    radii, e_theta = cylindrical_basis(v)
    u_theta = np.sum(u * e_theta, axis=1)
    r_max = float(np.max(radii))
    r_min = max(shell_dr, float(np.min(radii[radii > 1e-12])) if np.any(radii > 1e-12) else shell_dr)
    shells = np.arange(r_min, r_max + 0.5 * shell_dr, shell_dr)
    if shells.size < 4:
        shells = np.linspace(max(shell_dr, 0.25 * r_max), r_max, 8)
    bars = []
    weights_sum = []
    for rc in shells:
        w = np.exp(-0.5 * ((radii - rc) / shell_h) ** 2)
        sw = float(np.sum(w))
        bars.append(float(np.sum(w * u_theta) / sw) if sw > 0 else 0.0)
        weights_sum.append(sw)
    bars_arr = np.asarray(bars, dtype=float)
    shells_arr = np.asarray(shells, dtype=float)
    du_dr = np.gradient(bars_arr, shells_arr, edge_order=1)
    A = du_dr + 3.0 * bars_arr / shells_arr
    B = 2.0 * (bars_arr / shells_arr) * du_dr + 2.0 * (bars_arr * bars_arr) / (shells_arr * shells_arr)
    return {
        "shell_r": shells_arr,
        "u_theta_bar": bars_arr,
        "du_dr": du_dr,
        "A_K": A,
        "B_K": B,
        "weight_sum": np.asarray(weights_sum, dtype=float),
    }


def rayleigh_diagnostics(shell: dict[str, Any], omega: float) -> dict[str, Any]:
    A = np.asarray(shell["A_K"], dtype=float)
    B = np.asarray(shell["B_K"], dtype=float)
    phi_plus = 4.0 * omega * omega + 2.0 * omega * A + B
    phi_minus = 4.0 * omega * omega - 2.0 * omega * A + B
    delta = float(np.mean(phi_plus - phi_minus))
    if omega == 0:
        sigma_hat = float("nan")
    else:
        sigma_hat = float(np.mean(phi_plus + phi_minus - 8.0 * omega * omega) / (8.0 * omega * omega))
    return {
        "Delta_Omega": delta,
        "Sigma_hat_Omega": sigma_hat,
        "mean_A_K": float(np.mean(A)),
        "mean_B_K": float(np.mean(B)),
        "rms_A_K": float(np.sqrt(np.mean(A * A))),
        "rms_B_K": float(np.sqrt(np.mean(B * B))),
        "Phi_plus_mean": float(np.mean(phi_plus)),
        "Phi_minus_mean": float(np.mean(phi_minus)),
        "Phi_plus_min": float(np.min(phi_plus)),
        "Phi_minus_min": float(np.min(phi_minus)),
    }


def load_optional_response_vertices(path: str | Path | None, n: int, target_length: float | None) -> np.ndarray | None:
    if not path:
        return None
    return normalize_centerline(resample_closed(load_vertices_csv(path), n), target_length=target_length)


def _path_str(path: str | Path | None) -> str | None:
    return None if path is None or str(path) == "" else str(path)


def _same_file_hint(a: str | Path | None, b: str | Path | None) -> bool:
    """Best-effort comparison for user-supplied paths in reports.

    The proxy generator may store relative paths while run_example receives absolute
    paths, so compare both normalized strings and basenames.
    """
    if not a or not b:
        return False
    pa = Path(str(a))
    pb = Path(str(b))
    try:
        if pa.resolve() == pb.resolve():
            return True
    except Exception:
        pass
    return pa.name == pb.name or str(pa).replace("\\", "/") == str(pb).replace("\\", "/")


def _candidate_proxy_reports(*paths: str | Path | None) -> list[Path]:
    candidates: list[Path] = [Path.cwd() / "response_pair_proxy_report.json"]
    for raw in paths:
        if raw:
            p = Path(raw)
            candidates.append(p.parent / "response_pair_proxy_report.json")
    out: list[Path] = []
    seen: set[str] = set()
    for c in candidates:
        try:
            key = str(c.resolve())
        except Exception:
            key = str(c)
        if key not in seen and c.exists():
            seen.add(key)
            out.append(c)
    return out


def detect_proxy_report(vertices_plus: str | Path | None, vertices_minus: str | Path | None) -> dict[str, Any] | None:
    """Detect whether supplied Vplus/Vminus were generated by make_response_pair_proxy.py."""
    for report_path in _candidate_proxy_reports(vertices_plus, vertices_minus):
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = str(data.get("status", "")) + " " + str(data.get("warning", ""))
        if "PROXY_ONLY" not in status:
            continue
        if _same_file_hint(data.get("out_plus"), vertices_plus) and _same_file_hint(data.get("out_minus"), vertices_minus):
            return {
                "detected": True,
                "report": str(report_path),
                "status": data.get("status"),
                "gain": data.get("gain"),
                "omega": data.get("omega"),
            }
    return None


def build_source_metadata(
    *,
    knot_id: str,
    input_csv: str | Path | None,
    vertices_plus: str | Path | None,
    vertices_minus: str | Path | None,
    response_source: str,
    proxy_response_gain: float,
    proxy_status: str,
) -> dict[str, Any]:
    base_source_type = "csv_input" if input_csv else "generated_diagnostic_embedding"
    proxy_report = detect_proxy_report(vertices_plus, vertices_minus) if (vertices_plus and vertices_minus) else None

    if proxy_response_gain != 0.0 and "PROXY_ONLY" in proxy_status:
        inferred_response_source = "proxy_internal"
    elif proxy_report is not None:
        inferred_response_source = "proxy_report_detected"
    elif vertices_plus and vertices_minus:
        inferred_response_source = "external_csv_unverified"
    else:
        inferred_response_source = "not_supplied"

    if response_source != "auto":
        response_source_type = response_source
    else:
        response_source_type = inferred_response_source

    is_proxy = response_source_type in {"proxy", "proxy_internal", "proxy_report_detected"}
    has_response_pair = bool(vertices_plus and vertices_minus) or response_source_type == "proxy_internal"
    claim_ready = response_source_type in {"ridgerunner", "projected_ridgerunner", "solver"}

    return {
        "knot_id": knot_id,
        "base_source_type": base_source_type,
        "base_path": _path_str(input_csv),
        "response_source_type": response_source_type,
        "response_source_inferred": inferred_response_source,
        "vertices_plus_path": _path_str(vertices_plus),
        "vertices_minus_path": _path_str(vertices_minus),
        "has_response_pair": bool(has_response_pair),
        "proxy_detected": bool(is_proxy),
        "proxy_report": proxy_report,
        "claim_ready_for_rocking_breathing": bool(claim_ready),
        "claim_readiness_note": (
            "Rocking/breathing may be used for Research-Track physical claims only when response_source_type is ridgerunner/projected_ridgerunner/solver."
            if not claim_ready else
            "Response source is explicitly marked as solver-derived; verify solver log, thickness constraints, and consistent orientation before canon use."
        ),
    }


def proxy_response_vertices(v: np.ndarray, omega: float, *, gain: float, knot_id: str) -> tuple[np.ndarray, np.ndarray, str]:
    """Small deterministic proxy deformation for smoke testing observables.

    This is not a physics solver. It only keeps the file runnable before real
    Ridgerunner + forcing outputs are supplied.
    """
    if gain == 0.0 or omega == 0.0:
        return v.copy(), v.copy(), "NONE: no proxy deformation applied"
    x = v - np.mean(v, axis=0)
    radii = np.linalg.norm(x[:, :2], axis=1)
    scale = np.max(radii) if np.max(radii) > 0 else 1.0
    lobe = np.sign(x[:, 2])
    lobe[lobe == 0] = 1.0
    # quadrupolar rocking: opposite z-lobes receive opposite in-plane twist.
    angle = gain * math.tanh(abs(omega)) * lobe
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    plus = x.copy()
    minus = x.copy()
    plus[:, 0] = cos_a * x[:, 0] - sin_a * x[:, 1]
    plus[:, 1] = sin_a * x[:, 0] + cos_a * x[:, 1]
    minus[:, 0] = cos_a * x[:, 0] + sin_a * x[:, 1]
    minus[:, 1] = -sin_a * x[:, 0] + cos_a * x[:, 1]
    # tiny achiral breathing probe, same sign for +/-.
    er = np.zeros_like(x)
    ok = radii > 1e-12
    er[ok, 0] = x[ok, 0] / radii[ok]
    er[ok, 1] = x[ok, 1] / radii[ok]
    breath = 0.25 * gain * math.tanh(abs(omega)) * (radii / scale)[:, None] * er
    plus += breath
    minus += breath
    return plus, minus, "PROXY_ONLY: replace with V(+Omega), V(-Omega) from projected Ridgerunner for claims"


def rocking_breathing_diagnostics(
    v0: np.ndarray,
    v_plus: np.ndarray | None,
    v_minus: np.ndarray | None,
    *,
    omega: float,
    mirror_axis: str,
    omega_axis: str,
    backend=None,
) -> dict[str, Any]:
    q0 = quadrupole_rg2(v0, backend=backend)
    if v_plus is None or v_minus is None:
        return {
            "available": False,
            "reason": "No response vertices supplied. Provide --vertices-plus and --vertices-minus, or use --proxy-response-gain for smoke-only observables.",
            "Q0": q0["Q"],
            "Rg2_0": q0["Rg2"],
        }
    qp = quadrupole_rg2(v_plus, backend=backend)
    qm = quadrupole_rg2(v_minus, backend=backend)
    Q0 = q_perp(q0["Q"], omega_axis)
    Qp = q_perp(qp["Q"], omega_axis)
    Qm = q_perp(qm["Q"], omega_axis)
    P = mirror_matrix(mirror_axis)
    mirrored_Qm = P @ Qm @ P.T
    eps = 1e-15
    rrock = 0.5 * (fro_norm(Qp - Q0) + fro_norm(mirrored_Qm - Q0))
    eps_rock = fro_norm(Qp - mirrored_Qm) / (fro_norm(Qp) + fro_norm(Qm) + eps)
    bbreath = 0.5 * ((float(qp["Rg2"]) - float(q0["Rg2"])) / float(q0["Rg2"]) + (float(qm["Rg2"]) - float(q0["Rg2"])) / float(q0["Rg2"]))
    return {
        "available": True,
        "R_rock": float(rrock),
        "epsilon_P_rock": float(eps_rock),
        "B_breath": float(bbreath),
        "Rg2_0": float(q0["Rg2"]),
        "Rg2_plus": float(qp["Rg2"]),
        "Rg2_minus": float(qm["Rg2"]),
        "Q0": np.asarray(q0["Q"], dtype=float).tolist(),
        "Q_plus": np.asarray(qp["Q"], dtype=float).tolist(),
        "Q_minus": np.asarray(qm["Q"], dtype=float).tolist(),
    }


def minrad_values(v: np.ndarray) -> np.ndarray:
    prev = np.roll(v, 1, axis=0)
    nxt = np.roll(v, -1, axis=0)
    a = prev - v
    b = nxt - v
    la = np.linalg.norm(a, axis=1)
    lb = np.linalg.norm(b, axis=1)
    dot = np.sum(a * b, axis=1) / np.maximum(la * lb, 1e-30)
    # turning angle between incoming and outgoing tangents: pi - angle(a,b)
    theta = math.pi - np.arccos(np.clip(dot, -1.0, 1.0))
    return np.minimum(la, lb) / np.maximum(2.0 * np.tan(theta / 2.0), 1e-30)


def active_constraint_summary(v: np.ndarray, *, tau: float = 1.0, tol: float = 0.05) -> dict[str, Any]:
    n = len(v)
    minrad = minrad_values(v)
    kink_idx = np.where(minrad <= tau + tol)[0]
    # lightweight vertex-vertex strut proxy; true Ridgerunner uses point-pair dcsd and MinRad+/- gradients.
    dmin = float("inf")
    struts: list[tuple[int, int, float]] = []
    skip = max(3, int(0.02 * n))
    for i in range(n):
        for j in range(i + skip, n):
            if i == 0 and j > n - skip:
                continue
            d = float(np.linalg.norm(v[i] - v[j]))
            if d < dmin:
                dmin = d
            if d <= 2.0 * tau + tol:
                struts.append((i, j, d))
    return {
        "tau": tau,
        "tol": tol,
        "min_vertex_distance_proxy": dmin,
        "kink_count_proxy": int(len(kink_idx)),
        "strut_count_vertex_proxy": int(len(struts)),
        "kink_indices_proxy_first20": [int(x) for x in kink_idx[:20]],
        "struts_proxy_first20": [[int(i), int(j), float(d)] for i, j, d in struts[:20]],
        "limitation": "Proxy only: replace with Ridgerunner dcsd/MinRad constraints for final Pi_I(V).",
    }


def run(
    *,
    knot_id: str = "4_1",
    n: int = 256,
    omega: float = 1.0,
    epsilon_bs: float = 1.0,
    shell_dr: float = 0.25,
    shell_h: float = 0.5,
    gamma: float = 1.0,
    input_csv: str | Path | None = None,
    vertices_plus: str | Path | None = None,
    vertices_minus: str | Path | None = None,
    proxy_response_gain: float = 0.0,
    response_source: str = "auto",
    mirror_axis: str = "x",
    omega_axis: str = "z",
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
) -> dict[str, Any]:
    be = _backend(force_python=force_python, skip_build=skip_build, force_build=force_build, build_verbose=build_verbose)
    backend_name = "cpp" if be is not None else "python"
    target = ROPELENGTH_TARGETS.get(knot_id.lower())
    v0 = prepare_centerline(knot_id, n, input_csv)
    vplus = load_optional_response_vertices(vertices_plus, n, target)
    vminus = load_optional_response_vertices(vertices_minus, n, target)
    proxy_status = "not_used"
    if (vplus is None or vminus is None) and proxy_response_gain != 0.0:
        vplus, vminus, proxy_status = proxy_response_vertices(v0, omega, gain=proxy_response_gain, knot_id=knot_id)
    shell = shell_average_u_theta(
        v0,
        epsilon_bs=epsilon_bs,
        shell_dr=shell_dr,
        shell_h=shell_h,
        gamma=gamma,
        backend=be,
    )
    rd = rayleigh_diagnostics(shell, omega)
    rb = rocking_breathing_diagnostics(
        v0,
        vplus,
        vminus,
        omega=omega,
        mirror_axis=mirror_axis,
        omega_axis=omega_axis,
        backend=be,
    )
    constraints = active_constraint_summary(v0, tau=1.0, tol=0.05)
    source_meta = build_source_metadata(
        knot_id=knot_id,
        input_csv=input_csv,
        vertices_plus=vertices_plus,
        vertices_minus=vertices_minus,
        response_source=response_source,
        proxy_response_gain=proxy_response_gain,
        proxy_status=proxy_status,
    )
    classification = classify(knot_id, rd, rb, omega=omega, source_meta=source_meta)
    return {
        "audit_name": "SST dark-knot Rayleigh/rocking harness",
        "schema_version": "0.2.0",
        "backend": backend_name,
        "knot_id": knot_id,
        "status": STATUS,
        "source": source_meta,
        "parameters": {
            "n": n,
            "omega": omega,
            "epsilon_bs": epsilon_bs,
            "shell_dr": shell_dr,
            "shell_h": shell_h,
            "gamma": gamma,
            "tau": 1.0,
            "mirror_axis": mirror_axis,
            "omega_axis": omega_axis,
            "proxy_response_gain": proxy_response_gain,
            "response_source": response_source,
        },
        "geometry": {
            "length": polygon_length(v0),
            "target_ropelength_if_tau_1": target,
            "centroid_norm": float(np.linalg.norm(np.mean(v0, axis=0))),
            "n_vertices": int(len(v0)),
        },
        "rayleigh": rd,
        "rocking_breathing": rb,
        "active_constraints": constraints,
        "classification": classification,
        "proxy_response_status": proxy_status,
        "ok": bool(np.isfinite(rd["Delta_Omega"]) and (not rb.get("available") or np.isfinite(rb.get("R_rock", 0.0)))),
    }


def classify(
    knot_id: str,
    rd: dict[str, Any],
    rb: dict[str, Any],
    *,
    omega: float,
    source_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    delta = abs(float(rd["Delta_Omega"]))
    rms_a = max(abs(float(rd["rms_A_K"])), 1e-15)
    normalized_delta = delta / (4.0 * max(abs(float(omega)), 1e-15) * rms_a)
    is_4 = knot_id.lower() in {"4_1", "figure8", "figure-eight", "figure_eight"}
    is_3 = knot_id.lower() in {"3_1", "trefoil"}
    rocking_available = bool(rb.get("available"))
    source_meta = source_meta or {}
    claim_ready = bool(source_meta.get("claim_ready_for_rocking_breathing", False))
    proxy_detected = bool(source_meta.get("proxy_detected", False))

    if is_4:
        canon_safe_claim = (
            "4_1 is first-order chirality-blind when Delta_Omega is numerically small under parity-controlled alignment; "
            "local rocking/breathing response may remain nonzero, so it is not dynamically inert."
        )
        if delta < 1e-3 or normalized_delta < 0.05:
            provisional = "dark-candidate diagnostic"
        elif delta < 1e-2:
            provisional = "dark-candidate with asymmetry-check"
        else:
            provisional = "quasi-dark / asymmetry-check"
    elif is_3:
        canon_safe_claim = (
            "3_1 is the chiral-control knot: a nonzero Delta_Omega is expected under the shell-averaged Rayleigh diagnostic."
        )
        provisional = "chiral-control diagnostic"
    else:
        canon_safe_claim = "Unregistered knot id: no canon-safe parity classification is assigned by this harness."
        provisional = "unclassified diagnostic"

    if proxy_detected:
        response_evidence_label = "PROXY_ONLY: response observables validate plumbing only; do not use rocking/breathing as physical evidence."
    elif rocking_available and claim_ready:
        response_evidence_label = "SOLVER_MARKED: response observables may be evaluated as Research-Track evidence after solver-log/thickness/orientation checks."
    elif rocking_available:
        response_evidence_label = "UNVERIFIED_EXTERNAL_RESPONSE: response CSVs supplied, but source is not marked as Ridgerunner/solver."
    else:
        response_evidence_label = "BASE_ONLY: Rayleigh base diagnostic only; no V(+Omega)/V(-Omega) response evidence."

    return {
        "canon_safe_claim": canon_safe_claim,
        "delta_abs": delta,
        "delta_over_4omega_rmsA": normalized_delta,
        "expected_research_track": "4_1: Delta≈0 with parity-even/local response allowed; 3_1: Delta nonzero.",
        "provisional_label": provisional,
        "response_evidence_label": response_evidence_label,
        "claim_ready_for_rocking_breathing": claim_ready,
    }


def run_audit(**kwargs: Any) -> dict[str, Any]:
    return run(**kwargs)


def _flatten_row(result: dict[str, Any]) -> dict[str, Any]:
    rb = result.get("rocking_breathing", {})
    rd = result.get("rayleigh", {})
    return {
        "knot_id": result.get("knot_id"),
        "backend": result.get("backend"),
        "n": result["parameters"]["n"],
        "omega": result["parameters"]["omega"],
        "epsilon_bs": result["parameters"]["epsilon_bs"],
        "shell_h": result["parameters"]["shell_h"],
        "Delta_Omega": rd.get("Delta_Omega"),
        "Sigma_hat_Omega": rd.get("Sigma_hat_Omega"),
        "mean_A_K": rd.get("mean_A_K"),
        "mean_B_K": rd.get("mean_B_K"),
        "R_rock": rb.get("R_rock"),
        "epsilon_P_rock": rb.get("epsilon_P_rock"),
        "B_breath": rb.get("B_breath"),
        "strut_count_vertex_proxy": result["active_constraints"].get("strut_count_vertex_proxy"),
        "kink_count_proxy": result["active_constraints"].get("kink_count_proxy"),
        "response_source_type": result.get("source", {}).get("response_source_type"),
        "proxy_detected": result.get("source", {}).get("proxy_detected"),
        "provisional_label": result.get("classification", {}).get("provisional_label"),
        "claim_ready_for_rocking_breathing": result.get("classification", {}).get("claim_ready_for_rocking_breathing"),
        "ok": result.get("ok"),
    }


def run_sweep(
    *,
    knot_ids: list[str],
    omegas: list[float],
    epsilons: list[float],
    n: int = 192,
    shell_dr: float = 0.25,
    shell_h: float = 0.5,
    gamma: float = 1.0,
    proxy_response_gain: float = 0.0,
    response_source: str = "auto",
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for knot_id in knot_ids:
        for omega in omegas:
            for eps in epsilons:
                res = run(
                    knot_id=knot_id,
                    n=n,
                    omega=omega,
                    epsilon_bs=eps,
                    shell_dr=shell_dr,
                    shell_h=shell_h,
                    gamma=gamma,
                    proxy_response_gain=proxy_response_gain,
                    response_source=response_source,
                    force_python=force_python,
                    skip_build=skip_build,
                    force_build=force_build,
                    build_verbose=build_verbose,
                )
                rows.append(_flatten_row(res))
    return rows


def run_all_checks(
    *,
    out_dir: str | Path = "audit_out",
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    smoke4 = run_audit(knot_id="4_1", n=160, omega=1.0, epsilon_bs=1.0, proxy_response_gain=0.02, force_python=force_python, force_build=force_build)
    write_json(out / "smoke_4_1.json", smoke4)
    smoke3 = run_audit(knot_id="3_1", n=160, omega=1.0, epsilon_bs=1.0, proxy_response_gain=0.02, force_python=force_python, skip_build=True)
    write_json(out / "smoke_3_1.json", smoke3)
    py = run_audit(knot_id="4_1", n=120, omega=1.0, epsilon_bs=1.0, proxy_response_gain=0.02, force_python=True, skip_build=True)
    write_json(out / "smoke_python.json", py)
    sweep = run_sweep(knot_ids=["3_1", "4_1"], omegas=[0.5, 1.0], epsilons=[0.5, 1.0, 2.0], n=128, proxy_response_gain=0.02, force_python=force_python, skip_build=True)
    write_json(out / "sweep.json", sweep)
    write_csv(out / "sweep.csv", sweep)
    summary = {
        "audit_name": "SST dark-knot Rayleigh/rocking check battery",
        "out_dir": str(out),
        "smoke_4_1_ok": smoke4["ok"],
        "smoke_3_1_ok": smoke3["ok"],
        "smoke_python_ok": py["ok"],
        "sweep_ok": all(bool(r.get("ok")) for r in sweep),
        "ok": bool(smoke4["ok"] and smoke3["ok"] and py["ok"] and all(bool(r.get("ok")) for r in sweep)),
        "note": "Proxy response is enabled only for smoke-testing rocking/breathing. Use real V(+Omega), V(-Omega) for final claims.",
    }
    write_json(out / "audit_summary.json", summary)
    return summary
