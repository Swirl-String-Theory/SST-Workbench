from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from typing import Iterable

import numpy as np

from .geometry import analyze_components
from .gilbert import uniform_resample_closed
from .io_xyz import write_xyz, write_vect
from .util import json_safe, write_json

_FLOAT_RE = re.compile(r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[EeDd][+-]?\d+)?$")
_CONSTANT_RE = re.compile(r"constant\s+term\s+(?:is\s+)?set\s+to\s+0|j\s*=\s*0|zero\s+harmonic", re.I)


@dataclass(frozen=True)
class SourceFile:
    relative_path: str
    data: bytes

    @property
    def text(self) -> str:
        return self.data.decode("utf-8-sig", errors="replace")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


@dataclass(frozen=True)
class ParsedFSeries:
    relative_path: str
    topology_key: str
    variant_key: str
    comments: tuple[str, ...]
    coefficients: np.ndarray
    raw_first_numeric_tokens: tuple[str, ...]
    zero_token_styles: tuple[str, ...]
    sha256: str

    @property
    def row_count(self) -> int:
        return int(self.coefficients.shape[0])

    @property
    def first_row_all_zero(self) -> bool:
        return bool(np.all(np.abs(self.coefficients[0]) <= 1e-15))

    @property
    def first_row_zero_fields(self) -> int:
        return int(np.count_nonzero(np.abs(self.coefficients[0]) <= 1e-15))


@dataclass(frozen=True)
class ParsedShort:
    relative_path: str
    topology_key: str
    variant_key: str
    comments: tuple[str, ...]
    points: np.ndarray
    raw_first_numeric_tokens: tuple[str, ...]
    zero_token_styles: tuple[str, ...]
    sha256: str


@dataclass(frozen=True)
class OriginDecision:
    harmonic_origin: int
    method: str
    status: str
    rmsd_j0: float | None
    rmsd_j1: float | None
    confidence_ratio: float | None


def _norm_rel(name: str) -> str:
    return str(PurePosixPath(name.replace("\\", "/")))


def load_source_files(source: str | Path) -> dict[str, SourceFile]:
    p = Path(source)
    out: dict[str, SourceFile] = {}
    if p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file():
                rel = _norm_rel(str(f.relative_to(p)))
                out[rel] = SourceFile(rel, f.read_bytes())
        return out
    if p.is_file() and p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = _norm_rel(info.filename)
                out[rel] = SourceFile(rel, zf.read(info))
        return out
    if p.is_file():
        out[p.name] = SourceFile(p.name, p.read_bytes())
        return out
    raise FileNotFoundError(source)


def _variant_and_topology(relative_path: str) -> tuple[str, str]:
    pp = PurePosixPath(relative_path)
    stem = pp.stem
    if stem.lower().startswith("knot."):
        variant = stem[5:]
    elif stem.lower().startswith("knot_"):
        variant = stem[5:]
    else:
        variant = stem
    parent = pp.parent.name
    topology = parent if parent and parent not in (".", "") else re.sub(r"[a-z]\d*$", "", variant)
    return topology, variant


def _numeric_rows(text: str, width: int, path: str) -> tuple[list[str], np.ndarray, tuple[str, ...], tuple[str, ...]]:
    comments: list[str] = []
    rows: list[list[float]] = []
    first_tokens: tuple[str, ...] = ()
    zero_styles: set[str] = set()
    for ln, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s:
            continue
        if s.startswith(("%", "#", ";", "//")):
            comments.append(s)
            continue
        # tolerate trailing legacy comments
        for marker in ("%", "#", ";"):
            if marker in s:
                s = s.split(marker, 1)[0].strip()
        if not s:
            continue
        toks = s.replace(",", " ").split()
        if len(toks) != width:
            raise ValueError(f"{path}:{ln}: expected exactly {width} numeric fields, got {len(toks)}")
        vals = []
        for tok in toks:
            normalized = tok.replace("D", "E").replace("d", "e")
            if not _FLOAT_RE.match(normalized):
                raise ValueError(f"{path}:{ln}: invalid numeric token {tok!r}")
            v = float(normalized)
            if not math.isfinite(v):
                raise ValueError(f"{path}:{ln}: non-finite value")
            vals.append(v)
            if abs(v) <= 1e-15:
                zero_styles.add(tok)
        if not first_tokens:
            first_tokens = tuple(toks)
        rows.append(vals)
    if not rows:
        raise ValueError(f"{path}: no numeric rows")
    return comments, np.asarray(rows, dtype=float), first_tokens, tuple(sorted(zero_styles))


def parse_fseries_file(src: SourceFile) -> ParsedFSeries:
    comments, rows, first, zero_styles = _numeric_rows(src.text, 6, src.relative_path)
    topology, variant = _variant_and_topology(src.relative_path)
    return ParsedFSeries(src.relative_path, topology, variant, tuple(comments), rows, first, zero_styles, src.sha256)


def parse_short_file(src: SourceFile) -> ParsedShort:
    comments, rows, first, zero_styles = _numeric_rows(src.text, 3, src.relative_path)
    if len(rows) < 3:
        raise ValueError(f"{src.relative_path}: short curve needs at least 3 points")
    topology, variant = _variant_and_topology(src.relative_path)
    return ParsedShort(src.relative_path, topology, variant, tuple(comments), rows, first, zero_styles, src.sha256)


def evaluate_fseries(fs: ParsedFSeries, samples: int, harmonic_origin: int, oversample: int = 4) -> np.ndarray:
    if harmonic_origin not in (0, 1):
        raise ValueError("harmonic_origin must be 0 or 1")
    dense = max(int(samples) * int(oversample), int(samples) + 8)
    t = np.linspace(0.0, 2.0 * np.pi, dense, endpoint=False)
    j = np.arange(harmonic_origin, harmonic_origin + fs.row_count, dtype=float)
    phase = np.outer(t, j)
    c = np.cos(phase)
    s = np.sin(phase)
    a = fs.coefficients
    p = np.column_stack((
        c @ a[:, 0] + s @ a[:, 1],
        c @ a[:, 2] + s @ a[:, 3],
        c @ a[:, 4] + s @ a[:, 5],
    ))
    return uniform_resample_closed(p, int(samples))


def sample_short(sh: ParsedShort, samples: int) -> np.ndarray:
    return uniform_resample_closed(sh.points, int(samples))


def _unit_shape(points: np.ndarray, n: int = 128) -> np.ndarray:
    p = uniform_resample_closed(points, n)
    p = p - p.mean(axis=0)
    scale = float(np.sqrt(np.mean(np.sum(p * p, axis=1))))
    if scale <= 1e-15:
        raise ValueError("degenerate zero-scale curve")
    return p / scale


def _kabsch_rmsd(a: np.ndarray, b: np.ndarray) -> float:
    h = a.T @ b
    u, _, vt = np.linalg.svd(h)
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1, :] *= -1.0
        r = vt.T @ u.T
    d = a @ r.T - b
    return float(np.sqrt(np.mean(np.sum(d * d, axis=1))))


def closed_procrustes_rmsd(a: np.ndarray, b: np.ndarray, n: int = 128) -> float:
    aa = _unit_shape(a, n)
    bb0 = _unit_shape(b, n)
    best = math.inf
    for reverse in (False, True):
        bb = bb0[::-1].copy() if reverse else bb0
        for shift in range(n):
            best = min(best, _kabsch_rmsd(aa, np.roll(bb, shift, axis=0)))
    return float(best)


def read_origin_overrides(path: str | Path | None) -> dict[str, int]:
    if not path:
        return {}
    out: dict[str, int] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = _norm_rel(row.get("relative_path", "").strip())
            if not key:
                continue
            origin = int(row["harmonic_origin"])
            if origin not in (0, 1):
                raise ValueError(f"override {key}: harmonic_origin must be 0 or 1")
            out[key] = origin
    return out


def infer_harmonic_origin(
    fs: ParsedFSeries,
    paired_short: ParsedShort | None,
    override: int | None = None,
    compare_samples: int = 128,
) -> OriginDecision:
    if override is not None:
        return OriginDecision(int(override), "USER_OVERRIDE", "RESOLVED", None, None, None)

    comments = "\n".join(fs.comments)
    if paired_short is not None:
        p0 = evaluate_fseries(fs, max(compare_samples, 128), 0)
        p1 = evaluate_fseries(fs, max(compare_samples, 128), 1)
        e0 = closed_procrustes_rmsd(p0, paired_short.points, compare_samples)
        e1 = closed_procrustes_rmsd(p1, paired_short.points, compare_samples)
        best = min(e0, e1)
        other = max(e0, e1)
        ratio = other / max(best, 1e-15)
        origin = 0 if e0 < e1 else 1
        status = "RESOLVED" if best <= 0.20 and ratio >= 1.5 else "LOW_CONFIDENCE"
        return OriginDecision(origin, "PAIRED_SHORT_PROCRUSTES", status, e0, e1, ratio)

    if _CONSTANT_RE.search(comments):
        return OriginDecision(0, "EXPLICIT_CONSTANT_TERM_COMMENT", "RESOLVED", None, None, None)

    if not fs.first_row_all_zero:
        return OriginDecision(1, "NO_EXPLICIT_ZERO_ROW_ASSUME_J1", "RESOLVED", None, None, None)

    return OriginDecision(0, "AMBIGUOUS_ALL_ZERO_FIRST_ROW_DEFAULT_J0", "AMBIGUOUS", None, None, None)


def _length(points: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1).sum())


def _rms_radius(points: np.ndarray) -> float:
    q = points - points.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum(q * q, axis=1))))


def _geometry_fields(g: dict) -> dict:
    cs = g["components"]
    return {
        "sampled_total_length": g["total_length"],
        "edge_cv_max": max(c["edge_cv"] for c in cs),
        "edge_ratio_max": max(c["edge_ratio"] for c in cs),
        "flatness_min": min(c["flatness"] for c in cs),
        "curvature_max": max(c["curvature_max"] for c in cs),
        "curvature_rms_max": max(c["curvature_rms"] for c in cs),
        "torsion_rms_max": max(c["torsion_rms"] for c in cs),
        "torsion_max_abs": max(c["torsion_max_abs"] for c in cs),
        "min_curvature_radius": min(c["min_curvature_radius"] for c in cs),
        "sampled_dcsd_proxy": min(c["sampled_dcsd_proxy"] for c in cs),
        "sampled_reach_proxy": g["global_sampled_reach_proxy"],
        "length_over_diameter_proxy": g["global_length_over_diameter_proxy"],
        "ropelength_radius_proxy": g["global_ropelength_radius_proxy"],
        "writhe_sum_midpoint_proxy": sum(c["writhe_midpoint_proxy"] for c in cs),
        "acn_self_sum_midpoint_proxy": sum(c["acn_midpoint_proxy"] for c in cs),
        "bishop_closure_mismatch_max_rad": max(c["bishop_closure_mismatch_rad"] for c in cs),
        "native_backend": g["native_backend"],
        "native_backend_error": g.get("native_backend_error"),
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows([{k: json_safe(v) for k, v in r.items()} for r in rows])


def _pair_key(path: str) -> str:
    return str(PurePosixPath(path).with_suffix(""))


def scan_fresnel_source(source: str | Path, overrides_path: str | Path | None = None) -> dict:
    files = load_source_files(source)
    fseries: dict[str, ParsedFSeries] = {}
    shorts: dict[str, ParsedShort] = {}
    parse_errors: list[dict] = []
    for rel, src in files.items():
        ext = PurePosixPath(rel).suffix.lower()
        try:
            if ext == ".fseries":
                fseries[_pair_key(rel)] = parse_fseries_file(src)
            elif ext == ".short":
                shorts[_pair_key(rel)] = parse_short_file(src)
        except Exception as exc:
            parse_errors.append({"relative_path": rel, "error": str(exc)})

    overrides = read_origin_overrides(overrides_path)
    rows: list[dict] = []
    for key in sorted(set(fseries) | set(shorts)):
        fs = fseries.get(key)
        sh = shorts.get(key)
        decision = infer_harmonic_origin(fs, sh, overrides.get(fs.relative_path) if fs else None) if fs else None
        row = {
            "pair_key": key,
            "topology_key": (fs or sh).topology_key,
            "variant_key": (fs or sh).variant_key,
            "fseries_present": fs is not None,
            "short_present": sh is not None,
            "fseries_relative_path": fs.relative_path if fs else None,
            "short_relative_path": sh.relative_path if sh else None,
            "fseries_sha256": fs.sha256 if fs else None,
            "short_sha256": sh.sha256 if sh else None,
            "fseries_rows": fs.row_count if fs else None,
            "short_vertices": len(sh.points) if sh else None,
            "fseries_field_width": 6 if fs else None,
            "short_field_width": 3 if sh else None,
            "fseries_first_row_all_zero": fs.first_row_all_zero if fs else None,
            "fseries_first_row_zero_fields": fs.first_row_zero_fields if fs else None,
            "fseries_first_numeric_tokens": " ".join(fs.raw_first_numeric_tokens) if fs else None,
            "short_first_numeric_tokens": " ".join(sh.raw_first_numeric_tokens) if sh else None,
            "fseries_zero_token_styles": json.dumps(fs.zero_token_styles) if fs else None,
            "short_zero_token_styles": json.dumps(sh.zero_token_styles) if sh else None,
            "harmonic_origin": decision.harmonic_origin if decision else None,
            "origin_method": decision.method if decision else None,
            "origin_status": decision.status if decision else None,
            "origin_fit_rmsd_j0": decision.rmsd_j0 if decision else None,
            "origin_fit_rmsd_j1": decision.rmsd_j1 if decision else None,
            "origin_confidence_ratio": decision.confidence_ratio if decision else None,
        }
        rows.append(row)
    return {
        "schema": "sst21d.fresnel-scan.v0.2",
        "source": str(Path(source).resolve()),
        "file_count": len(files),
        "fseries_count": len(fseries),
        "short_count": len(shorts),
        "paired_count": len(set(fseries) & set(shorts)),
        "fseries_only_count": len(set(fseries) - set(shorts)),
        "short_only_count": len(set(shorts) - set(fseries)),
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "rows": rows,
        "_fseries": fseries,
        "_shorts": shorts,
    }


def write_scan_outputs(scan: dict, out: str | Path) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "fresnel_inventory.csv", scan["rows"])
    public = {k: v for k, v in scan.items() if not k.startswith("_")}
    write_json(out / "fresnel_inventory.json", public)
    return {k: public[k] for k in ("file_count", "fseries_count", "short_count", "paired_count", "parse_error_count")}


def read_metadata(path: str | Path | None) -> dict[str, dict]:
    if not path:
        return {}
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return {row["topology_key"]: row for row in csv.DictReader(f)}


def fresnel_static_campaign(
    source: str | Path,
    out: str | Path,
    samples: int = 600,
    prefer: str = "short",
    metadata_path: str | Path | None = None,
    overrides_path: str | Path | None = None,
    require_native: bool = False,
) -> dict:
    if prefer not in ("short", "fseries"):
        raise ValueError("prefer must be short or fseries")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scan = scan_fresnel_source(source, overrides_path)
    write_scan_outputs(scan, out)
    fseries: dict[str, ParsedFSeries] = scan["_fseries"]
    shorts: dict[str, ParsedShort] = scan["_shorts"]
    inventory_by_key = {row["pair_key"]: row for row in scan["rows"]}
    metadata = read_metadata(metadata_path)

    rows: list[dict] = []
    rep_rows: list[dict] = []
    for key in sorted(set(fseries) | set(shorts)):
        fs = fseries.get(key)
        sh = shorts.get(key)
        inv = inventory_by_key[key]
        origin = inv.get("harmonic_origin")
        p_fs = evaluate_fseries(fs, samples, int(origin)) if fs is not None else None
        p_sh = sample_short(sh, samples) if sh is not None else None

        rep_geometries: dict[str, dict] = {}
        for rep, points, src_path, src_sha in (
            ("fseries", p_fs, fs.relative_path if fs else None, fs.sha256 if fs else None),
            ("short", p_sh, sh.relative_path if sh else None, sh.sha256 if sh else None),
        ):
            if points is None:
                continue
            g = analyze_components([points], auto_build_native=True)
            if require_native and not g["native_backend"]:
                raise RuntimeError("native backend required but unavailable")
            rep_geometries[rep] = g
            rr = {
                "schema": "sst21d.fresnel-representation-row.v0.2",
                "pair_key": key,
                "topology_key": (fs or sh).topology_key,
                "variant_key": (fs or sh).variant_key,
                "representation": rep,
                "source_relative_path": src_path,
                "source_sha256": src_sha,
                "sample_count": samples,
                **_geometry_fields(g),
            }
            rep_rows.append(rr)
            write_json(out / "geometry" / f"{(fs or sh).variant_key}.{rep}.json", {
                "source_relative_path": src_path,
                "representation": rep,
                "geometry": g,
            })

        selected = prefer if prefer in rep_geometries else ("short" if "short" in rep_geometries else "fseries")
        selected_g = rep_geometries[selected]
        pair_rmsd = closed_procrustes_rmsd(p_fs, p_sh, min(128, samples)) if p_fs is not None and p_sh is not None else None
        f_len = _length(p_fs) if p_fs is not None else None
        s_len = _length(p_sh) if p_sh is not None else None
        f_r = _rms_radius(p_fs) if p_fs is not None else None
        s_r = _rms_radius(p_sh) if p_sh is not None else None
        pair_status = None
        if pair_rmsd is not None:
            pair_status = "PASS" if pair_rmsd <= 0.10 else "REVIEW"

        gates = {
            "G0_PARSE": True,
            "G1_FINITE": all(math.isfinite(c["length"]) for c in selected_g["components"]),
            "G2_EDGE_UNIFORMITY": max(c["edge_cv"] for c in selected_g["components"]) <= 0.005,
            "G3_POSITIVE_REACH_PROXY": selected_g["global_sampled_reach_proxy"] > 0,
            "G4_FSERIES_ORIGIN_RESOLVED": inv.get("origin_status") == "RESOLVED" if fs is not None else None,
            "G5_NATIVE_BACKEND_AVAILABLE": selected_g["native_backend"],
            "G6_FSERIES_SHORT_PAIR_PRESENT": fs is not None and sh is not None,
            "G7_REPRESENTATION_AGREEMENT": pair_rmsd <= 0.10 if pair_rmsd is not None else None,
            "G8_DYNAMIC_TRAJECTORY_PRESENT": False,
            "G9_PHASE_FIELD_PRESENT": False,
            "G10_CONVERGENCE_CERTIFIED": False,
        }
        row = {
            "schema": "sst21d.master-row.v0.2",
            "source_family": "FRESNEL_FOURIER_SERIES_ARCHIVE",
            "pair_key": key,
            "catalog_id": (fs or sh).variant_key,
            "topology_key": (fs or sh).topology_key,
            "variant_key": (fs or sh).variant_key,
            "component_count": 1,
            "selected_representation": selected,
            "sample_count_per_component": samples,
            **{k: v for k, v in inv.items() if k not in ("pair_key", "topology_key", "variant_key")},
            **_geometry_fields(selected_g),
            "fseries_sampled_length": f_len,
            "short_sampled_length": s_len,
            "fseries_to_short_length_ratio": f_len / s_len if f_len is not None and s_len and s_len > 0 else None,
            "fseries_to_short_rms_radius_ratio": f_r / s_r if f_r is not None and s_r and s_r > 0 else None,
            "fseries_short_shape_rmsd": pair_rmsd,
            "fseries_short_agreement_status": pair_status,
            "Q_geom_reference": 1.0,
            "Q_phase": None,
            "Dmin_projected_det1": None,
            "phase_structure_ir_exponent": None,
            "catalog_topology_status": "DIRECTORY_FILENAME_LABEL_ONLY_NOT_RECOMPUTED",
            "geometry_status": f"{selected.upper()}_STATIC_GEOMETRY_SAMPLED",
            "dynamic_status": "NOT_MEASURED_REQUIRES_TRAJECTORY",
            "epistemic_status": "RESEARCH_TRACK_DIAGNOSTIC_ONLY",
            "gates_json": json.dumps(gates, separators=(",", ":")),
        }
        row.update(metadata.get(row["topology_key"], {}))
        rows.append(row)

    _write_csv(out / "sst21d_fresnel_master.csv", rows)
    _write_csv(out / "fresnel_representations.csv", rep_rows)
    write_json(out / "sst21d_fresnel_master.json", {"schema": "sst21d.fresnel-master.v0.2", "rows": rows})
    write_json(out / "fresnel_representations.json", {"schema": "sst21d.fresnel-representations.v0.2", "rows": rep_rows})
    manifest = {
        "schema": "sst21d.fresnel-manifest.v0.2",
        "source": str(Path(source).resolve()),
        "samples": samples,
        "prefer": prefer,
        "master_row_count": len(rows),
        "representation_row_count": len(rep_rows),
        "origin_status_counts": {
            status: sum(1 for r in scan["rows"] if r.get("origin_status") == status)
            for status in sorted({r.get("origin_status") for r in scan["rows"] if r.get("origin_status")})
        },
        "claim_guard": "Static geometry and filename provenance only; no independent knot certification or dynamical phase-order inference.",
    }
    write_json(out / "manifest.json", manifest)
    return manifest


def fresnel_convergence_campaign(
    source: str | Path,
    out: str | Path,
    resolutions: Iterable[int] = (128, 256, 512, 1024),
    representation: str = "fseries",
    overrides_path: str | Path | None = None,
    require_native: bool = False,
) -> dict:
    if representation not in ("fseries", "short"):
        raise ValueError("representation must be fseries or short")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scan = scan_fresnel_source(source, overrides_path)
    fs_map: dict[str, ParsedFSeries] = scan["_fseries"]
    sh_map: dict[str, ParsedShort] = scan["_shorts"]
    inv = {r["pair_key"]: r for r in scan["rows"]}
    raw: list[dict] = []
    summaries: list[dict] = []
    for key in sorted(fs_map if representation == "fseries" else sh_map):
        erows = []
        for n in sorted(set(int(v) for v in resolutions)):
            if representation == "fseries":
                points = evaluate_fseries(fs_map[key], n, int(inv[key]["harmonic_origin"]))
            else:
                points = sample_short(sh_map[key], n)
            g = analyze_components([points], auto_build_native=True)
            if require_native and not g["native_backend"]:
                raise RuntimeError("native backend required but unavailable")
            row = {
                "pair_key": key,
                "topology_key": (fs_map.get(key) or sh_map.get(key)).topology_key,
                "variant_key": (fs_map.get(key) or sh_map.get(key)).variant_key,
                "representation": representation,
                "samples": n,
                "total_length": g["total_length"],
                "sampled_reach_proxy": g["global_sampled_reach_proxy"],
                "length_over_diameter_proxy": g["global_length_over_diameter_proxy"],
                "writhe_sum_midpoint_proxy": sum(c["writhe_midpoint_proxy"] for c in g["components"]),
                "edge_cv_max": max(c["edge_cv"] for c in g["components"]),
                "native_backend": g["native_backend"],
            }
            raw.append(row)
            erows.append(row)
        a, b = erows[-2], erows[-1]
        rel = lambda x, y: abs(y - x) / max(abs(y), 1e-15)
        length_rel = rel(a["total_length"], b["total_length"])
        reach_rel = rel(a["sampled_reach_proxy"], b["sampled_reach_proxy"])
        wr_abs = abs(b["writhe_sum_midpoint_proxy"] - a["writhe_sum_midpoint_proxy"])
        status = "PASS_DIAGNOSTIC_THRESHOLDS" if length_rel <= 1e-3 and reach_rel <= 2e-2 and wr_abs <= 5e-2 else "NOT_CONVERGED_AT_REQUESTED_LEVELS"
        summaries.append({
            "pair_key": key,
            "topology_key": erows[0]["topology_key"],
            "variant_key": erows[0]["variant_key"],
            "representation": representation,
            "resolutions_json": json.dumps([r["samples"] for r in erows]),
            "last_length_relative_change": length_rel,
            "last_reach_relative_change": reach_rel,
            "last_writhe_absolute_change": wr_abs,
            "convergence_status": status,
        })
    _write_csv(out / "convergence_raw.csv", raw)
    _write_csv(out / "convergence_summary.csv", summaries)
    result = {
        "schema": "sst21d.fresnel-convergence.v0.2",
        "representation": representation,
        "resolutions": list(resolutions),
        "row_count": len(summaries),
        "rows": summaries,
    }
    write_json(out / "convergence_summary.json", result)
    return {"row_count": len(summaries), "out": str(out)}


def fresnel_export(
    source: str | Path,
    out: str | Path,
    samples: int = 300,
    representation: str = "short",
    fmt: str = "both",
    variants: Iterable[str] | None = None,
    overrides_path: str | Path | None = None,
) -> dict:
    if representation not in ("short", "fseries"):
        raise ValueError("representation must be short or fseries")
    if fmt not in ("txt", "vect", "both"):
        raise ValueError("format must be txt, vect, or both")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scan = scan_fresnel_source(source, overrides_path)
    fs_map: dict[str, ParsedFSeries] = scan["_fseries"]
    sh_map: dict[str, ParsedShort] = scan["_shorts"]
    inv = {r["pair_key"]: r for r in scan["rows"]}
    wanted = set(variants or [])
    exported = []
    all_keys = sorted(set(fs_map) | set(sh_map))
    for key in all_keys:
        fs = fs_map.get(key)
        sh = sh_map.get(key)
        obj = fs or sh
        if wanted and obj.variant_key not in wanted and obj.topology_key not in wanted and key not in wanted:
            continue
        rep = representation
        if rep == "short" and sh is None:
            rep = "fseries"
        if rep == "fseries" and fs is None:
            rep = "short"
        if rep == "fseries":
            points = evaluate_fseries(fs, samples, int(inv[key]["harmonic_origin"]))
        else:
            points = sample_short(sh, samples)
        base = out / obj.topology_key / obj.variant_key
        if fmt in ("txt", "both"):
            write_xyz(base.with_suffix(".txt"), [points])
        if fmt in ("vect", "both"):
            write_vect(base.with_suffix(".vect"), [points])
        exported.append({"variant_key": obj.variant_key, "topology_key": obj.topology_key, "representation": rep})
    write_json(out / "export_manifest.json", {"schema": "sst21d.fresnel-export.v0.2", "rows": exported})
    return {"exported": len(exported), "out": str(out)}
