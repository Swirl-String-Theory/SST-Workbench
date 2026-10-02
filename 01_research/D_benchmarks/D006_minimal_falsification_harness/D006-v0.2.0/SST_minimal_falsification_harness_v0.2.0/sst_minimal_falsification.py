#!/usr/bin/env python3
"""
SST minimal falsification harness
=================================

Purpose
-------
Test the proposed response model

    alpha^{-1} = (8*pi/3) L_D + Delta

with

    Delta = sum_a c_a F_a[gamma, core, twist, contact]

under a strict no-leakage rule:

1. Fit the Wilson coefficients c_a only to independent calibration observables.
2. Freeze the coefficients.
3. Predict Delta for the trefoil and optional holdout observables.
4. Compare the frozen prediction with the alpha-derived target only at the end.

This script does not claim that the implemented feature basis is the unique SST
response functional. It tests a declared finite-dimensional EFT truncation.

Dependencies
------------
Python >= 3.10
numpy

Optional input
--------------
A CSV centerline with columns x,y,z, or Brian Gilbert's ideal-knot Fourier
database. Built-in analytic curves remain smoke-test geometries.

Exit codes
----------
0 : completed; inspect verdict in report
2 : malformed input / numerical failure
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ALPHA_INV_CODATA_2022 = 137.035999177
DEFAULT_FEATURES = ["length", "bend", "twist", "contact"]
FORBIDDEN_TEXT_TOKENS = (
    "alpha",
    "fine-structure",
    "fine structure",
    "137.035999",
    "electron charge",
    "elementary charge",
    "e^2",
    "e²",
    "v_swirl",
    "swirl speed",
    "1.09384563e6",
    "1.09384563×10^6",
)


@dataclass
class GeometryFeatures:
    name: str
    L_D: float
    I_kappa2: float
    I_twist2: float | None
    C_contact: float
    thickness_method: str
    estimated_D_raw: float
    samples: int
    metadata: dict[str, Any]

    def as_model_features(self) -> dict[str, float]:
        return {
            "length": float(self.L_D),
            "bend": float(self.I_kappa2),
            "twist": float(0.0 if self.I_twist2 is None else self.I_twist2),
            "contact": float(self.C_contact),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "sst.geometry-features.v1",
            "name": self.name,
            "features": self.as_model_features(),
            "diagnostics": {
                "L_D": self.L_D,
                "I_kappa2": self.I_kappa2,
                "I_twist2": self.I_twist2,
                "C_contact": self.C_contact,
                "thickness_method": self.thickness_method,
                "estimated_D_raw": self.estimated_D_raw,
                "samples": self.samples,
            },
            "metadata": self.metadata,
        }


def fail(message: str) -> "NoReturn":
    raise RuntimeError(message)


def cyclic_index_distance(i: np.ndarray, j: np.ndarray, n: int) -> np.ndarray:
    d = np.abs(i - j)
    return np.minimum(d, n - d)


def load_centerline_csv(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            fail(f"{path}: missing CSV header")
        lower = {name.lower().strip(): name for name in reader.fieldnames}
        for required in ("x", "y", "z"):
            if required not in lower:
                fail(f"{path}: expected columns x,y,z")
        for row in reader:
            rows.append([
                float(row[lower["x"]]),
                float(row[lower["y"]]),
                float(row[lower["z"]]),
            ])
    points = np.asarray(rows, dtype=float)
    if points.ndim != 2 or points.shape[0] < 16 or points.shape[1] != 3:
        fail("Centerline must contain at least 16 three-dimensional points")
    if np.linalg.norm(points[0] - points[-1]) < 1e-12:
        points = points[:-1]
    return points


@dataclass
class GilbertRecord:
    record_id: str
    conway: str | None
    reported_length: float | None
    diameter: float
    components: list[list[tuple[int, np.ndarray, np.ndarray]]]
    raw_attributes: dict[str, str]

    @property
    def component_count(self) -> int:
        return len(self.components)

    @property
    def knot_label(self) -> str:
        parts = self.record_id.split(":")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            crossings, components, index = parts
            if components == "1":
                return f"{crossings}_{index}"
        return self.record_id

    @property
    def reported_L_D(self) -> float | None:
        if self.reported_length is None:
            return None
        return self.reported_length / self.diameter


def _parse_tag_attributes(fragment: str) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)="([^"]*)"', fragment)
    }


def _parse_coefficients(fragment: str) -> list[tuple[int, np.ndarray, np.ndarray]]:
    coeffs: list[tuple[int, np.ndarray, np.ndarray]] = []
    for match in re.finditer(r"<Coeff\b([^>]*)/>", fragment, flags=re.DOTALL):
        attrs = _parse_tag_attributes(match.group(1))
        if not {"I", "A", "B"}.issubset(attrs):
            fail("Malformed Gilbert coefficient record")
        mode = int(attrs["I"])
        A = np.fromstring(attrs["A"], sep=",", dtype=float)
        B = np.fromstring(attrs["B"], sep=",", dtype=float)
        if A.shape != (3,) or B.shape != (3,):
            fail(f"Mode {mode}: expected three A and three B coefficients")
        coeffs.append((mode, A, B))
    coeffs.sort(key=lambda item: item[0])
    if not coeffs:
        fail("Gilbert record contains no Fourier coefficients")
    return coeffs


def load_gilbert_database(path: Path) -> list[GilbertRecord]:
    """
    Parse Brian Gilbert's XML-like ideal-knot Fourier database.

    The centerline convention is

        X(t) = sum_n [A_n cos(n t) + B_n sin(n t)],  0 <= t < 2*pi.

    Coefficients in the supplied database are printed to finite decimal
    precision, so the reconstructed length need not exactly equal the reported L.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r"<AB\b.*?</AB>", raw, flags=re.DOTALL)
    if not blocks:
        fail(f"{path}: no <AB> records found")

    records: list[GilbertRecord] = []
    seen: set[str] = set()
    for block in blocks:
        header_match = re.search(r"<AB\b([^>]*)>", block, flags=re.DOTALL)
        if header_match is None:
            continue
        attrs = _parse_tag_attributes(header_match.group(1))
        record_id = attrs.get("Id")
        if not record_id:
            fail("Gilbert record missing Id")
        if record_id in seen:
            fail(f"Duplicate Gilbert Id: {record_id}")
        seen.add(record_id)

        component_blocks = re.findall(
            r"<Component\b[^>]*>(.*?)</Component>",
            block,
            flags=re.DOTALL,
        )
        if component_blocks:
            components = [_parse_coefficients(part) for part in component_blocks]
        else:
            components = [_parse_coefficients(block)]

        reported_length = (
            float(attrs["L"]) if "L" in attrs and attrs["L"].strip() else None
        )
        diameter = float(attrs.get("D", "1.0"))
        if diameter <= 0:
            fail(f"{record_id}: non-positive diameter")

        records.append(
            GilbertRecord(
                record_id=record_id,
                conway=attrs.get("Conway"),
                reported_length=reported_length,
                diameter=diameter,
                components=components,
                raw_attributes=attrs,
            )
        )
    return records


def find_gilbert_record(records: list[GilbertRecord], record_id: str) -> GilbertRecord:
    for record in records:
        if record.record_id == record_id or record.knot_label == record_id:
            return record
    available = ", ".join(record.record_id for record in records[:12])
    fail(f"Unknown Gilbert record {record_id!r}. Examples: {available}")


def evaluate_gilbert_component(
    coeffs: list[tuple[int, np.ndarray, np.ndarray]],
    samples: int,
) -> np.ndarray:
    if samples < 16:
        fail("At least 16 Fourier samples are required")
    t = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    points = np.zeros((samples, 3), dtype=float)
    for mode, A, B in coeffs:
        phase = mode * t
        points += np.cos(phase)[:, None] * A
        points += np.sin(phase)[:, None] * B
    return points


def reconstructed_fourier_length(
    coeffs: list[tuple[int, np.ndarray, np.ndarray]],
    samples: int,
) -> float:
    t = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    deriv = np.zeros((samples, 3), dtype=float)
    for mode, A, B in coeffs:
        phase = mode * t
        deriv += (-mode * np.sin(phase))[:, None] * A
        deriv += (mode * np.cos(phase))[:, None] * B
    return float(2.0 * np.pi * np.mean(np.linalg.norm(deriv, axis=1)))


def gilbert_record_to_features(
    record: GilbertRecord,
    component_index: int,
    samples: int,
    length_source: str,
    local_skip_fraction: float,
    orth_tol: float,
    shell_sigma: float,
    profile: str,
    gaussian_width: float,
) -> dict[str, Any]:
    if not (1 <= component_index <= record.component_count):
        fail(
            f"{record.record_id}: component {component_index} outside "
            f"1..{record.component_count}"
        )
    coeffs = record.components[component_index - 1]
    max_mode = max(mode for mode, _, _ in coeffs)
    analysis_samples = max(samples, 6 * max_mode, 512)
    reconstruction_samples = max(analysis_samples, 8 * max_mode, 1024)
    raw_points = evaluate_gilbert_component(coeffs, reconstruction_samples)
    reconstructed_L = reconstructed_fourier_length(
        coeffs, max(reconstruction_samples, 4096)
    )
    features = compute_geometry_features(
        name=f"Gilbert-{record.record_id}-component-{component_index}",
        points_raw=raw_points,
        samples=analysis_samples,
        diameter_raw=record.diameter,
        local_skip_fraction=local_skip_fraction,
        orth_tol=orth_tol,
        shell_sigma=shell_sigma,
        profile=profile,
        gaussian_width=gaussian_width,
        twist_hat=None,
    ).to_dict()

    numerical_L_D = float(features["diagnostics"]["L_D"])
    reported_L_D = record.reported_L_D
    if length_source == "reported":
        if reported_L_D is None:
            fail(f"{record.record_id}: no reported L is available")
        selected_L_D = float(reported_L_D)
    elif length_source == "reconstructed":
        selected_L_D = float(reconstructed_L / record.diameter)
    elif length_source == "polygon":
        selected_L_D = numerical_L_D
    else:
        fail(f"Unknown length source: {length_source}")

    features["name"] = record.knot_label
    features["features"]["length"] = selected_L_D
    features["diagnostics"]["L_D"] = selected_L_D
    features["diagnostics"]["reported_L_D"] = reported_L_D
    features["diagnostics"]["reconstructed_fourier_L_D"] = (
        reconstructed_L / record.diameter
    )
    features["diagnostics"]["resampled_polygon_L_D"] = numerical_L_D
    features["diagnostics"]["length_source"] = length_source
    features["diagnostics"]["requested_samples"] = samples
    features["diagnostics"]["analysis_samples"] = analysis_samples
    features["diagnostics"]["fourier_mode_count"] = len(coeffs)
    features["diagnostics"]["maximum_fourier_mode"] = max_mode
    features["metadata"]["warning"] = (
        "Gilbert Fourier reconstruction; reported L/D is retained separately "
        "from rounded-coefficient geometry diagnostics."
    )
    features["metadata"].update(
        {
            "source_database": "Brian Gilbert, Database of Ideal Knots",
            "source_record_id": record.record_id,
            "knot_label": record.knot_label,
            "conway": record.conway,
            "component_index": component_index,
            "component_count": record.component_count,
            "database_diameter": record.diameter,
            "coefficient_precision_warning": (
                "The supplied Fourier coefficients are rounded; use the reported "
                "L/D for the ropelength baseline and the reconstruction for local "
                "geometry diagnostics."
            ),
        }
    )
    return features


def write_gilbert_manifest(records: list[GilbertRecord], path: Path) -> None:
    payload = {
        "schema": "sst.gilbert-manifest.v1",
        "records": [
            {
                "id": record.record_id,
                "label": record.knot_label,
                "conway": record.conway,
                "reported_L": record.reported_length,
                "D": record.diameter,
                "reported_L_D": record.reported_L_D,
                "components": record.component_count,
                "mode_counts": [len(component) for component in record.components],
                "maximum_modes": [
                    max(mode for mode, _, _ in component)
                    for component in record.components
                ],
            }
            for record in records
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def analytic_curve(kind: str, n: int) -> np.ndarray:
    u = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    if kind == "unknot":
        return np.column_stack((np.cos(u), np.sin(u), np.zeros_like(u)))

    if kind == "trefoil":
        # Smooth torus-knot embedding T(2,3); not an ideal-knot minimizer.
        x = (2.0 + np.cos(3.0 * u)) * np.cos(2.0 * u)
        y = (2.0 + np.cos(3.0 * u)) * np.sin(2.0 * u)
        z = np.sin(3.0 * u)
        return np.column_stack((x, y, z))

    if kind == "cinquefoil":
        # Smooth torus-knot embedding T(2,5).
        x = (2.0 + np.cos(5.0 * u)) * np.cos(2.0 * u)
        y = (2.0 + np.cos(5.0 * u)) * np.sin(2.0 * u)
        z = np.sin(5.0 * u)
        return np.column_stack((x, y, z))

    if kind == "figure8":
        # Standard smooth figure-eight-knot parametrization.
        x = (2.0 + np.cos(2.0 * u)) * np.cos(3.0 * u)
        y = (2.0 + np.cos(2.0 * u)) * np.sin(3.0 * u)
        z = np.sin(4.0 * u)
        return np.column_stack((x, y, z))

    fail(f"Unknown built-in curve: {kind}")


def resample_closed(points: np.ndarray, n: int) -> tuple[np.ndarray, float]:
    p = np.asarray(points, dtype=float)
    p_ext = np.vstack((p, p[0]))
    seg = np.linalg.norm(np.diff(p_ext, axis=0), axis=1)
    if np.any(seg <= 0.0):
        keep = np.r_[True, seg[:-1] > 1e-14]
        p = p[keep]
        p_ext = np.vstack((p, p[0]))
        seg = np.linalg.norm(np.diff(p_ext, axis=0), axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg)))
    total = float(s[-1])
    if not np.isfinite(total) or total <= 0.0:
        fail("Degenerate centerline")
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = np.column_stack([
        np.interp(targets, s, p_ext[:, axis]) for axis in range(3)
    ])
    return out, total


def periodic_geometry(points: np.ndarray) -> tuple[float, float, np.ndarray, np.ndarray]:
    n = len(points)
    next_p = np.roll(points, -1, axis=0)
    prev_p = np.roll(points, 1, axis=0)
    ds = float(np.mean(np.linalg.norm(next_p - points, axis=1)))
    if ds <= 0:
        fail("Non-positive arclength spacing")
    d1 = (next_p - prev_p) / (2.0 * ds)
    speed = np.linalg.norm(d1, axis=1)
    tangent = d1 / np.maximum(speed[:, None], 1e-15)
    d2 = (next_p - 2.0 * points + prev_p) / (ds * ds)
    # Curvature for a nearly arclength-parametrized curve.
    curvature = np.linalg.norm(np.cross(d1, d2), axis=1) / np.maximum(speed, 1e-15) ** 3
    length = ds * n
    return length, ds, tangent, curvature


def estimate_doubly_critical_distance(
    points: np.ndarray,
    tangent: np.ndarray,
    local_skip: int,
    orth_tol: float,
    block: int = 128,
) -> tuple[float | None, str]:
    """
    Approximate the shortest nonlocal doubly-critical chord.

    A candidate chord R_ij must be nearly perpendicular to both tangents:
        |Rhat . t_i| <= orth_tol
        |Rhat . t_j| <= orth_tol
    """
    n = len(points)
    best = math.inf
    found = False
    idx_all = np.arange(n)

    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        pi = points[i0:i1, None, :]
        diff = points[None, :, :] - pi
        dist = np.linalg.norm(diff, axis=2)

        ii = np.arange(i0, i1)[:, None]
        jj = idx_all[None, :]
        nonlocal_mask = cyclic_index_distance(ii, jj, n) >= local_skip
        upper_mask = jj > ii
        valid = nonlocal_mask & upper_mask & (dist > 1e-14)
        if not np.any(valid):
            continue

        rhat = diff / np.maximum(dist[:, :, None], 1e-15)
        ti = tangent[i0:i1, None, :]
        tj = tangent[None, :, :]
        oi = np.abs(np.sum(rhat * ti, axis=2))
        oj = np.abs(np.sum(rhat * tj, axis=2))
        crit = valid & (oi <= orth_tol) & (oj <= orth_tol)

        if np.any(crit):
            candidate = float(np.min(dist[crit]))
            if candidate < best:
                best = candidate
                found = True

    if found:
        return best, "doubly-critical-chord"

    # Conservative fallback: shortest nonlocal point-pair distance.
    best = math.inf
    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        dist = np.linalg.norm(points[None, :, :] - points[i0:i1, None, :], axis=2)
        ii = np.arange(i0, i1)[:, None]
        jj = idx_all[None, :]
        valid = (
            (cyclic_index_distance(ii, jj, n) >= local_skip)
            & (jj > ii)
            & (dist > 1e-14)
        )
        if np.any(valid):
            best = min(best, float(np.min(dist[valid])))
    return (best if np.isfinite(best) else None), "fallback-nonlocal-distance"


def estimate_thickness(
    points: np.ndarray,
    tangent: np.ndarray,
    curvature: np.ndarray,
    local_skip: int,
    orth_tol: float,
) -> tuple[float, str]:
    positive = curvature[curvature > 1e-12]
    rho_curv = math.inf if positive.size == 0 else float(1.0 / np.max(positive))
    dcrit, method = estimate_doubly_critical_distance(
        points, tangent, local_skip=local_skip, orth_tol=orth_tol
    )
    rho_contact = math.inf if dcrit is None else 0.5 * dcrit
    thickness = min(rho_curv, rho_contact)
    if not np.isfinite(thickness) or thickness <= 0:
        fail("Could not estimate a positive tube thickness")
    limiter = "curvature" if rho_curv <= rho_contact else method
    return thickness, limiter


def contact_feature(
    points_D1: np.ndarray,
    tangent: np.ndarray,
    ds_D: float,
    local_skip: int,
    shell_sigma: float,
    orth_tol: float,
    profile: str,
    gaussian_width: float,
    block: int = 128,
) -> float:
    """
    Finite nonlocal contact-shell proxy:

      C = 1/2 integral integral dσ dσ'
          exp[-((R/D)-1)^2/(2 shell_sigma^2)]
          max(0, -t.t')
          W_orth
          O_profile

    The centerline is scaled so D=1.
    """
    n = len(points_D1)
    idx_all = np.arange(n)
    total = 0.0

    if profile == "gaussian":
        if gaussian_width <= 0:
            fail("Gaussian profile width must be positive")
        profile_overlap = math.exp(-1.0 / (4.0 * gaussian_width * gaussian_width))
    elif profile == "tophat":
        # Exact tangent disks have zero volumetric overlap. The shell still probes
        # centerline proximity, but the profile-overlap factor is set to zero.
        profile_overlap = 0.0
    elif profile == "unit":
        profile_overlap = 1.0
    else:
        fail(f"Unknown core profile: {profile}")

    for i0 in range(0, n, block):
        i1 = min(n, i0 + block)
        diff = points_D1[None, :, :] - points_D1[i0:i1, None, :]
        dist = np.linalg.norm(diff, axis=2)
        ii = np.arange(i0, i1)[:, None]
        jj = idx_all[None, :]
        valid = (
            (cyclic_index_distance(ii, jj, n) >= local_skip)
            & (jj > ii)
            & (dist > 1e-14)
        )
        if not np.any(valid):
            continue

        rhat = diff / np.maximum(dist[:, :, None], 1e-15)
        ti = tangent[i0:i1, None, :]
        tj = tangent[None, :, :]
        dot_t = np.sum(ti * tj, axis=2)
        oi = np.abs(np.sum(rhat * ti, axis=2))
        oj = np.abs(np.sum(rhat * tj, axis=2))
        orth_weight = np.exp(-(oi * oi + oj * oj) / (2.0 * orth_tol * orth_tol))
        shell = np.exp(-((dist - 1.0) ** 2) / (2.0 * shell_sigma * shell_sigma))
        anti_parallel = np.maximum(0.0, -dot_t)
        total += float(np.sum((shell * orth_weight * anti_parallel)[valid]))

    return total * (ds_D * ds_D) * profile_overlap


def load_twist_hat(path: Path | None, n: int) -> np.ndarray | None:
    if path is None:
        return None
    values: list[float] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            fail(f"{path}: missing CSV header")
        names = {x.lower().strip(): x for x in reader.fieldnames}
        key = names.get("omega_hat") or names.get("twist_hat")
        if key is None:
            fail(f"{path}: expected omega_hat or twist_hat column")
        for row in reader:
            values.append(float(row[key]))
    arr = np.asarray(values, dtype=float)
    if len(arr) < 4:
        fail("Twist file contains too few samples")
    # Periodic interpolation by normalized sample index.
    xp = np.linspace(0.0, 1.0, len(arr), endpoint=False)
    x = np.linspace(0.0, 1.0, n, endpoint=False)
    arr_ext = np.r_[arr, arr[0]]
    xp_ext = np.r_[xp, 1.0]
    return np.interp(x, xp_ext, arr_ext)


def compute_geometry_features(
    name: str,
    points_raw: np.ndarray,
    samples: int,
    diameter_raw: float | None,
    local_skip_fraction: float,
    orth_tol: float,
    shell_sigma: float,
    profile: str,
    gaussian_width: float,
    twist_hat: np.ndarray | None,
) -> GeometryFeatures:
    points, _ = resample_closed(points_raw, samples)
    length_raw, ds_raw, tangent_raw, curvature_raw = periodic_geometry(points)

    local_skip = max(4, int(round(local_skip_fraction * samples)))
    if diameter_raw is None:
        thickness, thickness_method = estimate_thickness(
            points, tangent_raw, curvature_raw, local_skip, orth_tol
        )
        diameter_raw = 2.0 * thickness
    else:
        if diameter_raw <= 0:
            fail("Diameter must be positive")
        thickness_method = "user-supplied-diameter"

    # Scale coordinates so that D=1.
    points_D1 = points / diameter_raw
    length_D, ds_D, tangent, curvature_D1 = periodic_geometry(points_D1)
    # In D=1 coordinates, curvature_D1 = D * curvature_raw.
    L_D = float(length_D)
    I_kappa2 = float(np.sum(curvature_D1 ** 2) * ds_D)

    if twist_hat is None:
        I_twist2 = None
    else:
        if len(twist_hat) != samples:
            xp = np.linspace(0.0, 1.0, len(twist_hat), endpoint=False)
            x = np.linspace(0.0, 1.0, samples, endpoint=False)
            I_twist2 = float(np.sum(np.interp(x, xp, twist_hat) ** 2) * ds_D)
        else:
            I_twist2 = float(np.sum(twist_hat ** 2) * ds_D)

    C_contact = contact_feature(
        points_D1=points_D1,
        tangent=tangent,
        ds_D=ds_D,
        local_skip=local_skip,
        shell_sigma=shell_sigma,
        orth_tol=orth_tol,
        profile=profile,
        gaussian_width=gaussian_width,
    )

    metadata = {
        "normalization": "diameter D = 1",
        "local_skip_fraction": local_skip_fraction,
        "orthogonality_tolerance": orth_tol,
        "contact_shell_sigma": shell_sigma,
        "core_profile": profile,
        "gaussian_sigma_over_D": gaussian_width if profile == "gaussian" else None,
        "warning": (
            "Built-in analytic knots are smoke-test embeddings, not ideal-knot "
            "ropelength minimizers."
        ),
    }

    return GeometryFeatures(
        name=name,
        L_D=L_D,
        I_kappa2=I_kappa2,
        I_twist2=I_twist2,
        C_contact=C_contact,
        thickness_method=thickness_method,
        estimated_D_raw=float(diameter_raw),
        samples=samples,
        metadata=metadata,
    )


def recursively_collect_text(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(recursively_collect_text(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(recursively_collect_text(v))
    return out


def recursively_collect_numbers(obj: Any) -> list[float]:
    out: list[float] = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)) and np.isfinite(float(obj)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(recursively_collect_numbers(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(recursively_collect_numbers(v))
    return out


def leakage_findings(calibration_doc: dict[str, Any], alpha_inv: float) -> list[str]:
    """
    Inspect the actual calibration provenance and numerical rows.

    Compliance keys such as "target_coupling_may_be_used_in_calibration" are
    intentionally not scanned as evidence, because their names merely state
    the rule. Narrative phrases "without alpha" and "alpha-independent" are
    also treated as declarations, not as use of the constant.
    """
    findings: list[str] = []

    all_text = "\n".join(recursively_collect_text(calibration_doc))
    if "REPLACE" in all_text.upper():
        findings.append("unresolved placeholder token: REPLACE")

    evidence_texts: list[str] = []
    for row in calibration_doc.get("rows", []):
        if not isinstance(row, dict):
            continue
        evidence_texts.append(str(row.get("observable", "")))
        provenance = row.get("provenance", {})
        if isinstance(provenance, dict):
            evidence_texts.append(str(provenance.get("source", "")))
            evidence_texts.append(str(provenance.get("derivation", "")))
            used = provenance.get("used_constants", [])
            if isinstance(used, list):
                evidence_texts.extend(str(x) for x in used)
            else:
                evidence_texts.append(str(used))

    texts = "\n".join(evidence_texts).lower()
    # Remove explicit no-use declarations before token scanning.
    for declaration in (
        "alpha-independent",
        "alpha independent",
        "without alpha",
        "does not use alpha",
        "not using alpha",
    ):
        texts = texts.replace(declaration, "")

    for token in FORBIDDEN_TEXT_TOKENS:
        if token.lower() in texts:
            findings.append(f"forbidden calibration evidence: {token}")

    # Detect direct numerical insertion of alpha^{-1} in row values/features.
    for row in calibration_doc.get("rows", []):
        for value in recursively_collect_numbers(row):
            if abs(value - alpha_inv) < 1e-8:
                findings.append(f"numeric alpha^-1 leakage: {value:.12g}")
    return sorted(set(findings))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        fail(f"{path}: expected a JSON object")
    return doc


def build_design(
    calibration_doc: dict[str, Any],
    feature_names: list[str],
    role: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    rows = [r for r in calibration_doc.get("rows", []) if r.get("role", "calibration") == role]
    A: list[list[float]] = []
    y: list[float] = []
    sigma: list[float] = []
    ids: list[str] = []

    for idx, row in enumerate(rows):
        rid = str(row.get("id", f"{role}_{idx}"))
        value = float(row["value"])
        uncertainty = float(row.get("sigma", 1.0))
        if uncertainty <= 0:
            fail(f"Row {rid}: sigma must be positive")
        features = row.get("features")
        if not isinstance(features, dict):
            fail(f"Row {rid}: missing features object")
        try:
            vector = [float(features[name]) for name in feature_names]
        except KeyError as exc:
            raise RuntimeError(
                f"Row {rid}: missing model feature {exc.args[0]}"
            ) from exc
        if not np.all(np.isfinite(vector + [value, uncertainty])):
            fail(f"Row {rid}: non-finite numerical value")
        A.append(vector)
        y.append(value)
        sigma.append(uncertainty)
        ids.append(rid)

    if not A:
        return (
            np.empty((0, len(feature_names))),
            np.empty(0),
            np.empty(0),
            [],
        )
    return np.asarray(A), np.asarray(y), np.asarray(sigma), ids


def weighted_fit(A: np.ndarray, y: np.ndarray, sigma: np.ndarray) -> dict[str, Any]:
    if A.ndim != 2:
        fail("Design matrix must be two-dimensional")
    n, p = A.shape
    if n == 0:
        fail("No calibration rows")
    Aw = A / sigma[:, None]
    yw = y / sigma
    rank = int(np.linalg.matrix_rank(Aw))
    singular = np.linalg.svd(Aw, compute_uv=False)
    cond = math.inf if singular[-1] <= 0 else float(singular[0] / singular[-1])

    coef, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    residual = y - A @ coef
    chi2 = float(np.sum((residual / sigma) ** 2))
    dof = n - p
    red_chi2 = math.inf if dof <= 0 else chi2 / dof

    covariance = None
    if rank == p:
        normal = Aw.T @ Aw
        covariance = np.linalg.inv(normal)

    return {
        "coef": coef,
        "rank": rank,
        "condition_number": cond,
        "residual": residual,
        "chi2": chi2,
        "dof": dof,
        "reduced_chi2": red_chi2,
        "covariance": covariance,
    }


def leave_one_out(
    A: np.ndarray,
    y: np.ndarray,
    sigma: np.ndarray,
    ids: list[str],
) -> list[dict[str, Any]]:
    n, p = A.shape
    results: list[dict[str, Any]] = []
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        if np.sum(mask) < p:
            results.append({
                "id": ids[i],
                "status": "unavailable",
                "reason": "fewer remaining rows than coefficients",
            })
            continue
        fit = weighted_fit(A[mask], y[mask], sigma[mask])
        if fit["rank"] < p or fit["covariance"] is None:
            results.append({
                "id": ids[i],
                "status": "unavailable",
                "reason": "rank-deficient leave-one-out fit",
            })
            continue
        pred = float(A[i] @ fit["coef"])
        pred_var = float(A[i] @ fit["covariance"] @ A[i])
        z = (y[i] - pred) / math.sqrt(sigma[i] ** 2 + max(pred_var, 0.0))
        results.append({
            "id": ids[i],
            "status": "ok",
            "observed": float(y[i]),
            "predicted": pred,
            "z": float(z),
        })
    return results


def monte_carlo_prediction(
    A: np.ndarray,
    y: np.ndarray,
    sigma: np.ndarray,
    x_test: np.ndarray,
    draws: int,
    seed: int,
) -> tuple[float, float, list[float]]:
    rng = np.random.default_rng(seed)
    Aw = A / sigma[:, None]
    pinv = np.linalg.pinv(Aw)
    predictions = np.empty(draws, dtype=float)
    for k in range(draws):
        y_draw = y + rng.normal(0.0, sigma)
        coef = pinv @ (y_draw / sigma)
        predictions[k] = float(x_test @ coef)
    mean = float(np.mean(predictions))
    std = float(np.std(predictions, ddof=1)) if draws > 1 else 0.0
    quantiles = [float(q) for q in np.quantile(predictions, [0.025, 0.5, 0.975])]
    return mean, std, quantiles


def gate(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"gate": name, "pass": bool(passed), "detail": detail}


def audit(
    calibration_path: Path,
    geometry_path: Path,
    output_path: Path,
    alpha_inv: float,
    abs_tol: float,
    max_condition: float,
    max_reduced_chi2: float,
    max_z: float,
    mc_draws: int,
    seed: int,
) -> dict[str, Any]:
    cal = load_json(calibration_path)
    geom = load_json(geometry_path)
    feature_names = list(cal.get("model", {}).get("features", DEFAULT_FEATURES))
    if not feature_names:
        fail("Model feature list is empty")

    geometry_features = geom.get("features")
    if not isinstance(geometry_features, dict):
        fail("Geometry file lacks features object")
    missing = [name for name in feature_names if name not in geometry_features]
    if missing:
        fail(f"Trefoil geometry lacks model features: {missing}")
    x_trefoil = np.asarray([float(geometry_features[name]) for name in feature_names])

    L_D = float(geom.get("diagnostics", {}).get("L_D", geometry_features.get("length")))
    baseline = (8.0 * math.pi / 3.0) * L_D
    delta_target = alpha_inv - baseline

    findings = leakage_findings(cal, alpha_inv)
    gates: list[dict[str, Any]] = []
    gates.append(gate(
        "G0_NO_ALPHA_LEAKAGE",
        len(findings) == 0,
        "clean" if not findings else "; ".join(findings),
    ))

    A, y, sigma, ids = build_design(cal, feature_names, "calibration")
    n, p = A.shape
    gates.append(gate(
        "G1_ENOUGH_CALIBRATION_ROWS",
        n >= p + 1,
        f"rows={n}, coefficients={p}; require at least p+1 for a residual test",
    ))

    fit = None
    loo: list[dict[str, Any]] = []
    pred_delta = math.nan
    pred_sigma = math.nan
    pred_ci = [math.nan, math.nan, math.nan]
    holdout_results: list[dict[str, Any]] = []

    if n > 0:
        fit = weighted_fit(A, y, sigma)
        gates.append(gate(
            "G2_FULL_RANK",
            fit["rank"] == p,
            f"rank={fit['rank']}, required={p}",
        ))
        gates.append(gate(
            "G3_NUMERICAL_CONDITIONING",
            np.isfinite(fit["condition_number"]) and fit["condition_number"] <= max_condition,
            f"condition_number={fit['condition_number']:.6g}, limit={max_condition:.6g}",
        ))
        gates.append(gate(
            "G4_CALIBRATION_GOODNESS",
            np.isfinite(fit["reduced_chi2"]) and fit["reduced_chi2"] <= max_reduced_chi2,
            f"reduced_chi2={fit['reduced_chi2']:.6g}, limit={max_reduced_chi2:.6g}",
        ))

        loo = leave_one_out(A, y, sigma, ids)
        loo_ok = [
            r for r in loo if r.get("status") == "ok"
        ]
        max_abs_loo_z = max((abs(float(r["z"])) for r in loo_ok), default=math.inf)
        gates.append(gate(
            "G5_LEAVE_ONE_OUT",
            len(loo_ok) == n and max_abs_loo_z <= max_z,
            f"usable={len(loo_ok)}/{n}, max|z|={max_abs_loo_z:.6g}, limit={max_z:.6g}",
        ))

        if fit["rank"] == p:
            pred_delta = float(x_trefoil @ fit["coef"])
            pred_mean, pred_sigma, pred_ci = monte_carlo_prediction(
                A, y, sigma, x_trefoil, mc_draws, seed
            )
            # Keep the point estimate from the original data; MC mean is a diagnostic.
            error = pred_delta - delta_target
            z_target = (
                error / pred_sigma if pred_sigma > 0 else
                (0.0 if error == 0 else math.copysign(math.inf, error))
            )
            gates.append(gate(
                "G6_FROZEN_TREFOIL_PREDICTION",
                abs(error) <= abs_tol and abs(z_target) <= max_z,
                (
                    f"predicted={pred_delta:.12g}, target={delta_target:.12g}, "
                    f"error={error:.6g}, abs_tol={abs_tol:.6g}, "
                    f"MC_sigma={pred_sigma:.6g}, z={z_target:.6g}"
                ),
            ))

            Ah, yh, sh, hids = build_design(cal, feature_names, "holdout")
            if len(yh):
                for row, obs, unc, rid in zip(Ah, yh, sh, hids):
                    pred = float(row @ fit["coef"])
                    pred_var = 0.0
                    if fit["covariance"] is not None:
                        pred_var = float(row @ fit["covariance"] @ row)
                    z = (obs - pred) / math.sqrt(unc * unc + max(pred_var, 0.0))
                    holdout_results.append({
                        "id": rid,
                        "observed": float(obs),
                        "predicted": pred,
                        "z": float(z),
                    })
                max_holdout_z = max(abs(r["z"]) for r in holdout_results)
                gates.append(gate(
                    "G7_INDEPENDENT_HOLDOUTS",
                    max_holdout_z <= max_z,
                    f"holdouts={len(holdout_results)}, max|z|={max_holdout_z:.6g}",
                ))
            else:
                gates.append(gate(
                    "G7_INDEPENDENT_HOLDOUTS",
                    False,
                    "no holdout rows supplied",
                ))
    else:
        for name, detail in (
            ("G2_FULL_RANK", "no calibration rows"),
            ("G3_NUMERICAL_CONDITIONING", "no calibration rows"),
            ("G4_CALIBRATION_GOODNESS", "no calibration rows"),
            ("G5_LEAVE_ONE_OUT", "no calibration rows"),
            ("G6_FROZEN_TREFOIL_PREDICTION", "no fitted coefficients"),
            ("G7_INDEPENDENT_HOLDOUTS", "no holdout rows supplied"),
        ):
            gates.append(gate(name, False, detail))

    preprediction_gate_names = {
        "G0_NO_ALPHA_LEAKAGE",
        "G1_ENOUGH_CALIBRATION_ROWS",
        "G2_FULL_RANK",
        "G3_NUMERICAL_CONDITIONING",
        "G4_CALIBRATION_GOODNESS",
        "G5_LEAVE_ONE_OUT",
    }
    preprediction_ok = all(
        g["pass"] for g in gates if g["gate"] in preprediction_gate_names
    )
    trefoil_gate = next(g for g in gates if g["gate"] == "G6_FROZEN_TREFOIL_PREDICTION")
    holdout_gate = next(g for g in gates if g["gate"] == "G7_INDEPENDENT_HOLDOUTS")

    if not preprediction_ok:
        verdict = "INCONCLUSIVE_UNDERDETERMINED"
        interpretation = (
            "The declared response truncation has not earned an independent "
            "trefoil prediction. This does not falsify SST; it falsifies the "
            "claim that the present calibration is sufficient."
        )
    elif not trefoil_gate["pass"]:
        verdict = "FALSIFIED_AT_DECLARED_TOLERANCE"
        interpretation = (
            "The independently calibrated, frozen response functional misses "
            "the trefoil target at the preregistered tolerance."
        )
    elif not holdout_gate["pass"]:
        verdict = "TREFOIL_MATCH_BUT_CROSS_OBSERVABLE_FAILURE"
        interpretation = (
            "The trefoil target is matched, but the same fixed coefficients do "
            "not pass independent holdouts. The truncation is not predictive."
        )
    else:
        verdict = "NOT_FALSIFIED"
        interpretation = (
            "The declared truncation passes calibration, leave-one-out, trefoil, "
            "and holdout gates. This is not proof of SST; it is survival of the "
            "specified falsification test."
        )

    coefficients = {}
    if fit is not None:
        coefficients = {
            name: float(value) for name, value in zip(feature_names, fit["coef"])
        }

    report = {
        "schema": "sst.minimal-falsification-report.v1",
        "verdict": verdict,
        "interpretation": interpretation,
        "preregistered_thresholds": {
            "alpha_inverse_final_test_only": alpha_inv,
            "absolute_trefoil_tolerance": abs_tol,
            "max_condition_number": max_condition,
            "max_reduced_chi2": max_reduced_chi2,
            "max_absolute_z": max_z,
            "monte_carlo_draws": mc_draws,
            "seed": seed,
        },
        "model": {
            "features": feature_names,
            "equation": "Delta = sum_a c_a F_a",
            "baseline": "(8*pi/3) L_D",
        },
        "trefoil": {
            "L_D": L_D,
            "baseline_alpha_inverse": baseline,
            "target_delta_from_alpha": delta_target,
            "predicted_delta_frozen": pred_delta,
            "prediction_mc_sigma": pred_sigma,
            "prediction_mc_quantiles_2p5_50_97p5": pred_ci,
        },
        "fit": None if fit is None else {
            "coefficients": coefficients,
            "rank": fit["rank"],
            "condition_number": fit["condition_number"],
            "chi2": fit["chi2"],
            "dof": fit["dof"],
            "reduced_chi2": fit["reduced_chi2"],
            "calibration_row_ids": ids,
        },
        "leave_one_out": loo,
        "holdouts": holdout_results,
        "gates": gates,
        "leakage_findings": findings,
        "input_files": {
            "calibration": str(calibration_path),
            "geometry": str(geometry_path),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=False)

    return report


def make_template(path: Path) -> None:
    template = {
        "schema": "sst.calibration.v1",
        "model": {
            "features": ["length", "bend", "twist", "contact"],
            "description": (
                "Linear EFT matching model. Each independent observable must "
                "supply its design-row coefficients for the same Wilson basis."
            ),
        },
        "rules": {
            "alpha_may_be_used_in_calibration": False,
            "coefficients_are_frozen_before_trefoil_test": True,
            "provenance_is_required": True,
        },
        "rows": [
            {
                "id": "REPLACE_ring_observable_1",
                "role": "calibration",
                "observable": "REPLACE_WITH_ALPHA_INDEPENDENT_OBSERVABLE",
                "value": 0.0,
                "sigma": 1.0,
                "features": {
                    "length": 1.0,
                    "bend": 0.0,
                    "twist": 0.0,
                    "contact": 0.0,
                },
                "provenance": {
                    "source": "REPLACE",
                    "derivation": "REPLACE",
                    "used_constants": ["REPLACE_WITH_NON_ALPHA_INPUTS"],
                },
            },
            {
                "id": "REPLACE_kelvin_observable_2",
                "role": "calibration",
                "observable": "REPLACE_WITH_ALPHA_INDEPENDENT_OBSERVABLE",
                "value": 0.0,
                "sigma": 1.0,
                "features": {
                    "length": 0.0,
                    "bend": 1.0,
                    "twist": 0.0,
                    "contact": 0.0,
                },
                "provenance": {
                    "source": "REPLACE",
                    "derivation": "REPLACE",
                    "used_constants": ["REPLACE_WITH_NON_ALPHA_INPUTS"],
                },
            },
            {
                "id": "REPLACE_core_observable_3",
                "role": "calibration",
                "observable": "REPLACE_WITH_ALPHA_INDEPENDENT_OBSERVABLE",
                "value": 0.0,
                "sigma": 1.0,
                "features": {
                    "length": 0.0,
                    "bend": 0.0,
                    "twist": 1.0,
                    "contact": 0.0,
                },
                "provenance": {
                    "source": "REPLACE",
                    "derivation": "REPLACE",
                    "used_constants": ["REPLACE_WITH_NON_ALPHA_INPUTS"],
                },
            },
            {
                "id": "REPLACE_contact_observable_4",
                "role": "calibration",
                "observable": "REPLACE_WITH_ALPHA_INDEPENDENT_OBSERVABLE",
                "value": 0.0,
                "sigma": 1.0,
                "features": {
                    "length": 0.0,
                    "bend": 0.0,
                    "twist": 0.0,
                    "contact": 1.0,
                },
                "provenance": {
                    "source": "REPLACE",
                    "derivation": "REPLACE",
                    "used_constants": ["REPLACE_WITH_NON_ALPHA_INPUTS"],
                },
            },
            {
                "id": "REPLACE_mixed_observable_5",
                "role": "calibration",
                "observable": "REPLACE_WITH_ALPHA_INDEPENDENT_OBSERVABLE",
                "value": 0.0,
                "sigma": 1.0,
                "features": {
                    "length": 1.0,
                    "bend": 1.0,
                    "twist": 1.0,
                    "contact": 1.0,
                },
                "provenance": {
                    "source": "REPLACE",
                    "derivation": "REPLACE",
                    "used_constants": ["REPLACE_WITH_NON_ALPHA_INPUTS"],
                },
            },
            {
                "id": "REPLACE_holdout_1",
                "role": "holdout",
                "observable": "REPLACE_WITH_HELD_OUT_OBSERVABLE",
                "value": 0.0,
                "sigma": 1.0,
                "features": {
                    "length": 0.5,
                    "bend": 0.5,
                    "twist": 0.0,
                    "contact": 1.0,
                },
                "provenance": {
                    "source": "REPLACE",
                    "derivation": "REPLACE",
                    "used_constants": ["REPLACE_WITH_NON_ALPHA_INPUTS"],
                },
            },
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)


def make_synthetic_demo(cal_path: Path, geom_path: Path) -> None:
    """
    Produce a nonphysical self-test dataset. It verifies the software pipeline,
    not SST. The token 'alpha' is intentionally absent from the calibration file.
    """
    features = ["length", "bend", "twist", "contact"]
    true_c = np.array([-0.0015, -0.0040, 0.0008, -0.0200])
    A = np.array([
        [1.0, 0.2, 0.0, 0.0],
        [0.5, 1.0, 0.1, 0.0],
        [0.0, 0.2, 1.0, 0.1],
        [0.2, 0.0, 0.2, 1.0],
        [1.0, 1.0, 0.5, 0.3],
        [0.3, 0.7, 1.2, 0.4],
        [0.8, 0.4, 0.3, 1.1],
    ])
    sigma = np.full(len(A), 2e-5)
    y = A @ true_c

    rows = []
    for i in range(6):
        rows.append({
            "id": f"synthetic_cal_{i+1}",
            "role": "calibration",
            "observable": "dimensionless synthetic matching datum",
            "value": float(y[i]),
            "sigma": float(sigma[i]),
            "features": {k: float(v) for k, v in zip(features, A[i])},
            "provenance": {
                "source": "software self-test only",
                "derivation": "generated from frozen hidden coefficients",
                "used_constants": ["none"],
            },
        })
    rows.append({
        "id": "synthetic_holdout_1",
        "role": "holdout",
        "observable": "dimensionless synthetic holdout",
        "value": float(y[6]),
        "sigma": float(sigma[6]),
        "features": {k: float(v) for k, v in zip(features, A[6])},
        "provenance": {
            "source": "software self-test only",
            "derivation": "generated from frozen hidden coefficients",
            "used_constants": ["none"],
        },
    })

    cal = {
        "schema": "sst.calibration.v1",
        "model": {"features": features},
        "rules": {
            "target_coupling_may_be_used_in_calibration": False,
            "coefficients_are_frozen_before_final_test": True,
        },
        "rows": rows,
    }

    # Choose non-length features and solve self-consistently for L_D:
    #
    #   alpha_inv - (8*pi/3)L_D
    #       = c_length L_D + c_bend F_bend + c_twist F_twist + c_contact F_contact.
    #
    other = float(np.array([18.0, 2.0, 0.8]) @ true_c[1:])
    L_D = (ALPHA_INV_CODATA_2022 - other) / (
        (8.0 * math.pi / 3.0) + true_c[0]
    )
    x = np.array([L_D, 18.0, 2.0, 0.8])
    delta = float(x @ true_c)
    geom = {
        "schema": "sst.geometry-features.v1",
        "name": "synthetic-selftest",
        "features": {
            "length": float(x[0]),
            "bend": float(x[1]),
            "twist": float(x[2]),
            "contact": float(x[3]),
        },
        "diagnostics": {
            "L_D": float(L_D),
            "note": "nonphysical self-test geometry",
        },
        "metadata": {
            "purpose": "software pipeline test only",
        },
    }

    cal_path.parent.mkdir(parents=True, exist_ok=True)
    with cal_path.open("w", encoding="utf-8") as f:
        json.dump(cal, f, indent=2)
    with geom_path.open("w", encoding="utf-8") as f:
        json.dump(geom, f, indent=2)


def print_report_summary(report: dict[str, Any]) -> None:
    print("=" * 72)
    print("SST MINIMAL FALSIFICATION REPORT")
    print("=" * 72)
    print("Verdict:", report["verdict"])
    print(report["interpretation"])
    print()
    tr = report["trefoil"]
    print(f"L_D                         = {tr['L_D']:.12g}")
    print(f"(8*pi/3) L_D                = {tr['baseline_alpha_inverse']:.12g}")
    print(f"target Delta                = {tr['target_delta_from_alpha']:.12g}")
    pred = tr["predicted_delta_frozen"]
    if np.isfinite(pred):
        print(f"frozen predicted Delta      = {pred:.12g}")
        print(f"prediction MC sigma         = {tr['prediction_mc_sigma']:.6g}")
    else:
        print("frozen predicted Delta      = unavailable")
    print()
    for g in report["gates"]:
        mark = "PASS" if g["pass"] else "FAIL"
        print(f"[{mark}] {g['gate']}: {g['detail']}")
    print("=" * 72)


def command_geometry(args: argparse.Namespace) -> None:
    if args.curve_csv is not None:
        points = load_centerline_csv(Path(args.curve_csv))
        name = Path(args.curve_csv).stem
    else:
        points = analytic_curve(args.kind, max(args.samples, 512))
        name = args.kind

    twist = load_twist_hat(Path(args.twist_csv) if args.twist_csv else None, args.samples)
    features = compute_geometry_features(
        name=name,
        points_raw=points,
        samples=args.samples,
        diameter_raw=args.diameter,
        local_skip_fraction=args.local_skip_fraction,
        orth_tol=args.orth_tol,
        shell_sigma=args.contact_shell_sigma,
        profile=args.core_profile,
        gaussian_width=args.gaussian_width,
        twist_hat=twist,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(features.to_dict(), f, indent=2)
    print(json.dumps(features.to_dict(), indent=2))
    print(f"\nWrote: {out}")


def command_audit(args: argparse.Namespace) -> None:
    report = audit(
        calibration_path=Path(args.calibration),
        geometry_path=Path(args.geometry),
        output_path=Path(args.out),
        alpha_inv=args.alpha_inv,
        abs_tol=args.abs_tol,
        max_condition=args.max_condition,
        max_reduced_chi2=args.max_reduced_chi2,
        max_z=args.max_z,
        mc_draws=args.mc_draws,
        seed=args.seed,
    )
    print_report_summary(report)
    print(f"Report: {args.out}")


def command_gilbert_list(args: argparse.Namespace) -> None:
    records = load_gilbert_database(Path(args.database))
    out = Path(args.out)
    write_gilbert_manifest(records, out)
    print(f"Loaded {len(records)} Gilbert records")
    for record in records:
        length = (
            "n/a" if record.reported_L_D is None
            else f"{record.reported_L_D:.9f}"
        )
        print(
            f"{record.record_id:10s}  {record.knot_label:8s}  "
            f"components={record.component_count}  L/D={length}"
        )
    print(f"Manifest: {out}")


def command_gilbert_geometry(args: argparse.Namespace) -> None:
    records = load_gilbert_database(Path(args.database))
    record = find_gilbert_record(records, args.id)
    payload = gilbert_record_to_features(
        record=record,
        component_index=args.component,
        samples=args.samples,
        length_source=args.length_source,
        local_skip_fraction=args.local_skip_fraction,
        orth_tol=args.orth_tol,
        shell_sigma=args.contact_shell_sigma,
        profile=args.core_profile,
        gaussian_width=args.gaussian_width,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"\nWrote: {out}")


def command_gilbert_batch(args: argparse.Namespace) -> None:
    records = load_gilbert_database(Path(args.database))
    requested = None
    if args.ids:
        requested = {item.strip() for item in args.ids.split(",") if item.strip()}

    selected: list[GilbertRecord] = []
    for record in records:
        if requested is not None and (
            record.record_id not in requested and record.knot_label not in requested
        ):
            continue
        if record.component_count != 1:
            continue
        if record.reported_L_D is None and args.length_source == "reported":
            continue
        selected.append(record)

    if not selected:
        fail("No single-component Gilbert records matched the selection")

    outputs: list[dict[str, Any]] = []
    for record in selected:
        payload = gilbert_record_to_features(
            record=record,
            component_index=1,
            samples=args.samples,
            length_source=args.length_source,
            local_skip_fraction=args.local_skip_fraction,
            orth_tol=args.orth_tol,
            shell_sigma=args.contact_shell_sigma,
            profile=args.core_profile,
            gaussian_width=args.gaussian_width,
        )
        outputs.append(payload)
        print(
            f"{record.record_id:10s} {record.knot_label:8s} "
            f"L/D={payload['diagnostics']['L_D']:.9f} "
            f"I_kappa2={payload['features']['bend']:.9f} "
            f"C_contact={payload['features']['contact']:.9f}"
        )

    bundle = {
        "schema": "sst.gilbert-feature-batch.v1",
        "database": str(args.database),
        "length_source": args.length_source,
        "samples": args.samples,
        "records": outputs,
    }
    out_json = Path(args.out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    out_csv = Path(args.csv_out) if args.csv_out else out_json.with_suffix(".csv")
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "record_id",
                "knot_label",
                "L_D",
                "I_kappa2",
                "I_twist2",
                "C_contact",
                "reported_L_D",
                "reconstructed_fourier_L_D",
                "resampled_polygon_L_D",
                "fourier_mode_count",
                "maximum_fourier_mode",
            ],
        )
        writer.writeheader()
        for payload in outputs:
            diagnostics = payload["diagnostics"]
            metadata = payload["metadata"]
            model = payload["features"]
            writer.writerow(
                {
                    "record_id": metadata["source_record_id"],
                    "knot_label": metadata["knot_label"],
                    "L_D": model["length"],
                    "I_kappa2": model["bend"],
                    "I_twist2": model["twist"],
                    "C_contact": model["contact"],
                    "reported_L_D": diagnostics["reported_L_D"],
                    "reconstructed_fourier_L_D": diagnostics[
                        "reconstructed_fourier_L_D"
                    ],
                    "resampled_polygon_L_D": diagnostics[
                        "resampled_polygon_L_D"
                    ],
                    "fourier_mode_count": diagnostics["fourier_mode_count"],
                    "maximum_fourier_mode": diagnostics["maximum_fourier_mode"],
                }
            )
    print(f"JSON batch: {out_json}")
    print(f"CSV table:  {out_csv}")


def command_batch_predict(args: argparse.Namespace) -> None:
    cal = load_json(Path(args.calibration))
    batch = load_json(Path(args.batch))
    feature_names = list(cal.get("model", {}).get("features", DEFAULT_FEATURES))
    findings = leakage_findings(cal, args.alpha_inv)
    if findings:
        fail("Calibration leakage/placeholder findings: " + "; ".join(findings))

    A, y, sigma, ids = build_design(cal, feature_names, "calibration")
    if len(y) < len(feature_names) + 1:
        fail(
            f"Need at least p+1 calibration rows; got {len(y)} for "
            f"p={len(feature_names)}"
        )
    fit = weighted_fit(A, y, sigma)
    if fit["rank"] != len(feature_names):
        fail("Calibration design matrix is rank deficient")
    if not np.isfinite(fit["condition_number"]) or (
        fit["condition_number"] > args.max_condition
    ):
        fail(f"Calibration matrix condition number too large: {fit['condition_number']}")

    rows: list[dict[str, Any]] = []
    for record in batch.get("records", []):
        model = record.get("features", {})
        x = np.asarray([float(model[name]) for name in feature_names], dtype=float)
        delta = float(x @ fit["coef"])
        L_D = float(record["diagnostics"]["L_D"])
        baseline = (8.0 * math.pi / 3.0) * L_D
        rows.append(
            {
                "record_id": record["metadata"].get("source_record_id"),
                "knot_label": record["metadata"].get("knot_label", record.get("name")),
                "L_D": L_D,
                "baseline": baseline,
                "predicted_delta_frozen": delta,
                "predicted_response": baseline + delta,
                "model_features": {
                    name: float(value) for name, value in zip(feature_names, x)
                },
            }
        )

    report = {
        "schema": "sst.cross-knot-predictions.v1",
        "status": "PREDICTIONS_FROZEN_NOT_YET_TESTED",
        "warning": (
            "These are cross-knot predictions from independently fitted and frozen "
            "coefficients. They become falsification tests only when compared with "
            "predeclared independent observations."
        ),
        "calibration_row_ids": ids,
        "features": feature_names,
        "coefficients": {
            name: float(value)
            for name, value in zip(feature_names, fit["coef"])
        },
        "condition_number": fit["condition_number"],
        "reduced_chi2": fit["reduced_chi2"],
        "records": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Frozen predictions for {len(rows)} knots written to: {out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Independent-calibration falsification harness for an SST response functional."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_geom = sub.add_parser("geometry", help="Extract dimensionless knot/core features")
    source = p_geom.add_mutually_exclusive_group(required=True)
    source.add_argument("--curve-csv", help="CSV centerline with x,y,z columns")
    source.add_argument(
        "--kind",
        choices=["unknot", "trefoil", "figure8", "cinquefoil"],
        help="Built-in smoke-test curve",
    )
    p_geom.add_argument("--samples", type=int, default=1200)
    p_geom.add_argument(
        "--diameter",
        type=float,
        default=None,
        help="Tube diameter in the raw coordinate units; otherwise estimated",
    )
    p_geom.add_argument("--twist-csv", default=None, help="CSV with omega_hat column")
    p_geom.add_argument("--local-skip-fraction", type=float, default=0.02)
    p_geom.add_argument("--orth-tol", type=float, default=0.12)
    p_geom.add_argument("--contact-shell-sigma", type=float, default=0.08)
    p_geom.add_argument(
        "--core-profile",
        choices=["unit", "gaussian", "tophat"],
        default="unit",
    )
    p_geom.add_argument(
        "--gaussian-width",
        type=float,
        default=0.25,
        help="Gaussian sigma/D for the contact overlap factor",
    )
    p_geom.add_argument("--out", default="geometry_features.json")
    p_geom.set_defaults(func=command_geometry)

    p_glist = sub.add_parser(
        "gilbert-list",
        help="Inventory Brian Gilbert ideal-knot Fourier records",
    )
    p_glist.add_argument("--database", required=True)
    p_glist.add_argument("--out", default="gilbert_manifest.json")
    p_glist.set_defaults(func=command_gilbert_list)

    p_ggeom = sub.add_parser(
        "gilbert-geometry",
        help="Extract response features directly from a Gilbert Fourier record",
    )
    p_ggeom.add_argument("--database", required=True)
    p_ggeom.add_argument("--id", default="3:1:1")
    p_ggeom.add_argument("--component", type=int, default=1)
    p_ggeom.add_argument("--samples", type=int, default=1600)
    p_ggeom.add_argument(
        "--length-source",
        choices=["reported", "reconstructed", "polygon"],
        default="reported",
    )
    p_ggeom.add_argument("--local-skip-fraction", type=float, default=0.02)
    p_ggeom.add_argument("--orth-tol", type=float, default=0.12)
    p_ggeom.add_argument("--contact-shell-sigma", type=float, default=0.08)
    p_ggeom.add_argument(
        "--core-profile",
        choices=["unit", "gaussian", "tophat"],
        default="unit",
    )
    p_ggeom.add_argument("--gaussian-width", type=float, default=0.25)
    p_ggeom.add_argument("--out", default="gilbert_geometry_features.json")
    p_ggeom.set_defaults(func=command_gilbert_geometry)

    p_gbatch = sub.add_parser(
        "gilbert-batch",
        help="Extract a cross-knot feature table from all single-component records",
    )
    p_gbatch.add_argument("--database", required=True)
    p_gbatch.add_argument(
        "--ids",
        default=None,
        help="Optional comma-separated Gilbert IDs or knot labels",
    )
    p_gbatch.add_argument("--samples", type=int, default=600)
    p_gbatch.add_argument(
        "--length-source",
        choices=["reported", "reconstructed", "polygon"],
        default="reported",
    )
    p_gbatch.add_argument("--local-skip-fraction", type=float, default=0.02)
    p_gbatch.add_argument("--orth-tol", type=float, default=0.12)
    p_gbatch.add_argument("--contact-shell-sigma", type=float, default=0.08)
    p_gbatch.add_argument(
        "--core-profile",
        choices=["unit", "gaussian", "tophat"],
        default="unit",
    )
    p_gbatch.add_argument("--gaussian-width", type=float, default=0.25)
    p_gbatch.add_argument("--out", default="gilbert_feature_batch.json")
    p_gbatch.add_argument("--csv-out", default=None)
    p_gbatch.set_defaults(func=command_gilbert_batch)

    p_bpredict = sub.add_parser(
        "batch-predict",
        help="Apply independently fitted frozen coefficients to a Gilbert knot batch",
    )
    p_bpredict.add_argument("--calibration", required=True)
    p_bpredict.add_argument("--batch", required=True)
    p_bpredict.add_argument("--out", default="cross_knot_predictions.json")
    p_bpredict.add_argument("--alpha-inv", type=float, default=ALPHA_INV_CODATA_2022)
    p_bpredict.add_argument("--max-condition", type=float, default=1e8)
    p_bpredict.set_defaults(func=command_batch_predict)

    p_template = sub.add_parser("template", help="Write a calibration JSON template")
    p_template.add_argument("--out", default="calibration_template.json")
    p_template.set_defaults(func=lambda a: make_template(Path(a.out)))

    p_demo = sub.add_parser("demo", help="Write nonphysical software self-test inputs")
    p_demo.add_argument("--calibration-out", default="synthetic_calibration.json")
    p_demo.add_argument("--geometry-out", default="synthetic_geometry.json")
    p_demo.set_defaults(
        func=lambda a: make_synthetic_demo(
            Path(a.calibration_out), Path(a.geometry_out)
        )
    )

    p_audit = sub.add_parser("audit", help="Fit independently, freeze, and falsify")
    p_audit.add_argument("--calibration", required=True)
    p_audit.add_argument("--geometry", required=True)
    p_audit.add_argument("--out", default="falsification_report.json")
    p_audit.add_argument("--alpha-inv", type=float, default=ALPHA_INV_CODATA_2022)
    p_audit.add_argument(
        "--abs-tol",
        type=float,
        default=1e-3,
        help="Preregistered absolute tolerance for Delta",
    )
    p_audit.add_argument("--max-condition", type=float, default=1e8)
    p_audit.add_argument("--max-reduced-chi2", type=float, default=3.0)
    p_audit.add_argument("--max-z", type=float, default=3.0)
    p_audit.add_argument("--mc-draws", type=int, default=2000)
    p_audit.add_argument("--seed", type=int, default=20260801)
    p_audit.set_defaults(func=command_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except (RuntimeError, ValueError, KeyError, np.linalg.LinAlgError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
