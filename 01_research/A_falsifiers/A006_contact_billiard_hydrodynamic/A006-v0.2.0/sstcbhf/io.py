from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np


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
            raise ValueError("Malformed Gilbert coefficient record")
        mode = int(attrs["I"])
        a = np.fromstring(attrs["A"], sep=",", dtype=float)
        b = np.fromstring(attrs["B"], sep=",", dtype=float)
        if a.shape != (3,) or b.shape != (3,):
            raise ValueError(f"Mode {mode}: expected three A and three B coefficients")
        coeffs.append((mode, a, b))
    coeffs.sort(key=lambda item: item[0])
    if not coeffs:
        raise ValueError("Gilbert record contains no Fourier coefficients")
    return coeffs


def load_gilbert_database(path: Path) -> list[GilbertRecord]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r"<AB\b.*?</AB>", raw, flags=re.DOTALL)
    if not blocks:
        raise ValueError(f"{path}: no <AB> records found")
    records: list[GilbertRecord] = []
    seen: set[str] = set()
    for block in blocks:
        header = re.search(r"<AB\b([^>]*)>", block, flags=re.DOTALL)
        if header is None:
            continue
        attrs = _parse_tag_attributes(header.group(1))
        record_id = attrs.get("Id")
        if not record_id:
            raise ValueError("Gilbert record missing Id")
        if record_id in seen:
            raise ValueError(f"Duplicate Gilbert Id: {record_id}")
        seen.add(record_id)
        comp_blocks = re.findall(r"<Component\b[^>]*>(.*?)</Component>", block, flags=re.DOTALL)
        components = [_parse_coefficients(part) for part in comp_blocks] if comp_blocks else [_parse_coefficients(block)]
        reported_length = float(attrs["L"]) if attrs.get("L", "").strip() else None
        diameter = float(attrs.get("D", "1.0"))
        if diameter <= 0:
            raise ValueError(f"{record_id}: non-positive D")
        records.append(GilbertRecord(record_id, attrs.get("Conway"), reported_length, diameter, components, attrs))
    return records


def sample_fourier(coeffs: list[tuple[int, np.ndarray, np.ndarray]], samples: int) -> np.ndarray:
    t = 2.0 * np.pi * np.arange(samples, dtype=float) / samples
    out = np.zeros((samples, 3), dtype=float)
    for mode, a, b in coeffs:
        out += np.cos(mode * t)[:, None] * a[None, :]
        out += np.sin(mode * t)[:, None] * b[None, :]
    return out


def load_gilbert_curve(path: Path, record_id: str = "3:1:1", samples: int = 4096, component: int = 0):
    records = load_gilbert_database(path)
    matches = [r for r in records if r.record_id == record_id]
    if not matches:
        available = ", ".join(r.record_id for r in records[:20])
        raise ValueError(f"record {record_id!r} not found; first available IDs: {available}")
    rec = matches[0]
    if not (0 <= component < rec.component_count):
        raise ValueError(f"component index {component} invalid for {record_id} with {rec.component_count} components")
    return sample_fourier(rec.components[component], samples), rec


def _parse_xyz_text(raw: str, path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.replace(",", " ").split()
        if len(fields) < 3:
            continue
        try:
            xyz = [float(fields[0]), float(fields[1]), float(fields[2])]
        except ValueError:
            continue
        if all(np.isfinite(xyz)):
            rows.append(xyz)
    points = np.asarray(rows, dtype=float)
    if points.ndim != 2 or points.shape[0] < 16 or points.shape[1] != 3:
        raise ValueError(f"{path}: expected at least 16 XYZ rows")
    if np.linalg.norm(points[0] - points[-1]) <= 1e-12 * max(1.0, np.ptp(points, axis=0).max()):
        points = points[:-1]
    return points


def _parse_vect(raw: str, path: Path) -> np.ndarray:
    tokens = raw.replace("\n", " ").split()
    try:
        idx = tokens.index("VECT")
    except ValueError:
        idx = 0
    numbers = tokens[idx + 1:]
    if len(numbers) < 5:
        raise ValueError(f"{path}: malformed VECT")
    ncomp = int(numbers[0])
    total_vertices = int(numbers[1])
    pos = 3
    counts = [int(numbers[pos + i]) for i in range(ncomp)]
    pos += ncomp
    color_counts = [int(numbers[pos + i]) for i in range(ncomp)]
    pos += ncomp
    if ncomp != 1:
        raise ValueError(f"{path}: only one-component VECT inputs are supported")
    n = abs(counts[0])
    if n != total_vertices:
        raise ValueError(f"{path}: VECT vertex count mismatch")
    coords = np.asarray([float(v) for v in numbers[pos:pos + 3 * n]], dtype=float).reshape(n, 3)
    if counts[0] < 0 and np.linalg.norm(coords[0] - coords[-1]) < 1e-12:
        coords = coords[:-1]
    return coords


def load_curve(path: Path) -> np.ndarray:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    if raw.lstrip().startswith("VECT") or path.suffix.lower() == ".vect":
        return _parse_vect(raw, path)
    return _parse_xyz_text(raw, path)


def write_xyz(path: Path, points: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, points, fmt="%.17g")


def torus_trefoil(samples: int, major_radius: float = 2.0, minor_radius: float = 1.0) -> np.ndarray:
    t = 2.0 * np.pi * np.arange(samples) / samples
    p, q = 2.0, 3.0
    return np.column_stack([
        (major_radius + minor_radius * np.cos(q * t)) * np.cos(p * t),
        (major_radius + minor_radius * np.cos(q * t)) * np.sin(p * t),
        minor_radius * np.sin(q * t),
    ])
