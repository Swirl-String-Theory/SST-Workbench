from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import json
import re
from typing import Any

import numpy as np
import pandas as pd

from .io import REQUIRED_MANIFEST
from .utils import save_json

DIAG_RE = re.compile(
    r"tPhys=(?P<tphys>[-+0-9.eE]+)\s+type=diag\s+detail=(?P<detail>\{.*\})\s*$"
)


@dataclass
class ScanRecord:
    path: str
    kind: str
    status: str
    reason: str = ""
    sample_id: str = ""
    source: str = "recursive_discovery"
    rows_or_frames: int | None = None


def _safe_id(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_.-")
    return s[-140:] if len(s) > 140 else s


def _read_csv_header(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return next(csv.reader(f))
    except Exception:
        return []


def _detect_csv(path: Path) -> tuple[str, str]:
    cols = set(_read_csv_header(path))
    spectrum = {"k_rad_m", "omega_rad_s"}
    trajectory = {"time_s", "point_id", "x_m", "y_m", "z_m"}
    legacy_diag = {"tPhys", "Wr", "ACN", "RA"}
    if spectrum.issubset(cols) or {"k", "omega"}.issubset(cols):
        return "spectrum_csv", "speed_eligible"
    if trajectory.issubset(cols):
        return "trajectory_csv", "speed_eligible"
    if legacy_diag.issubset(cols):
        return "vortexlab_diag_csv", "diagnostic_only"
    return "unknown_csv", "unsupported"


def _detect_npz(path: Path) -> tuple[str, str, int | None]:
    try:
        with np.load(path, allow_pickle=False) as d:
            keys = set(d.files)
            if {"xyz", "time_s"}.issubset(keys):
                xyz = np.asarray(d["xyz"])
                frames = int(xyz.shape[0]) if xyz.ndim >= 1 else None
                return "trajectory_npz", "speed_eligible", frames
            if {"k_rad_m", "omega_rad_s"}.issubset(keys):
                n = len(np.asarray(d["k_rad_m"]))
                return "spectrum_npz", "speed_eligible", int(n)
    except Exception:
        pass
    return "unknown_npz", "unsupported", None


def parse_vortexlab_log(path: Path) -> pd.DataFrame:
    """Extract VortexLab `type=diag detail={...}` records without inventing spatial data.

    These scalar diagnostics are useful for campaign provenance/QC, but are deliberately
    NOT promoted to a k-resolved speed measurement.
    """
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = DIAG_RE.search(line.rstrip("\r\n"))
            if not m:
                continue
            try:
                detail = json.loads(m.group("detail"))
            except json.JSONDecodeError:
                continue
            out = {"tPhys": float(m.group("tphys"))}
            for key in (
                "t", "Wr", "Lk", "ACN", "RA", "zA", "a", "aSim",
                "topologyGap", "stretchLambda", "stretchLambdaStar", "stretchG",
                "stretchCoreRatio", "specClockDistance", "specClockMutualA",
                "specClockMutualB", "specClockOmegaFullA", "specClockOmegaFullB",
                "specClockOmegaIsoA", "specClockOmegaIsoB", "specClockDeltaOmegaA",
                "specClockDeltaOmegaB", "specClockPhaseLogRatio", "specClockResidual",
                "specClockPhaseLag", "scaleProbe",
            ):
                out[key] = detail.get(key)
            rows.append(out)
    return pd.DataFrame(rows)


def _is_demo_path(path: Path) -> bool:
    return any(p.lower().startswith("demo") or "synthetic" in p.lower() for p in path.parts)


def _is_ignored_discovery_path(path: Path) -> bool:
    """Skip tool/build/cache directories that cannot contain primary campaign data.

    This matters when the scan root is the whole SST-Workbench rather than only
    this package's campaigns/ directory. We intentionally do NOT skip generic
    project output folders because older SST workbenches may store useful CSV/NPZ
    data there.
    """
    exact = {
        ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
        "build", "dist", "outputs_scan", "outputs_blind", "outputs_demo",
        "outputs_workspace_scan",
    }
    return any(part.lower() in exact for part in path.parts)


def _manifest_rows_from_file(manifest: Path, root: Path) -> tuple[list[dict[str, Any]], list[ScanRecord]]:
    records: list[ScanRecord] = []
    try:
        df = pd.read_csv(manifest)
    except Exception as e:
        return [], [ScanRecord(str(manifest), "manifest", "invalid", str(e), source="manifest")]
    missing = REQUIRED_MANIFEST - set(df.columns)
    if missing:
        return [], [ScanRecord(str(manifest), "manifest", "invalid", f"missing columns {sorted(missing)}", source="manifest")]
    rows: list[dict[str, Any]] = []
    for i, r in df.iterrows():
        d = r.to_dict()
        p = Path(str(d.get("path", "")))
        resolved = p if p.is_absolute() else manifest.parent / p
        d["path"] = str(resolved.resolve())
        d.setdefault("family_id", "")
        d.setdefault("topology", "BLINDED")
        d.setdefault("resolution_n", np.nan)
        d.setdefault("core_radius_m", np.nan)
        d["_source_manifest"] = str(manifest.resolve())
        rows.append(d)
        records.append(ScanRecord(
            path=str(resolved), kind=str(d.get("input_type", "manifest_row")), status="speed_eligible",
            sample_id=str(d.get("sample_id", f"manifest_{i}")), source="manifest"
        ))
    return rows, records


def build_recursive_campaign(
    root: str | Path,
    generated_dir: str | Path,
    *,
    include_demo: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(root).resolve()
    generated_dir = Path(generated_dir).resolve()
    generated_dir.mkdir(parents=True, exist_ok=True)
    diag_dir = generated_dir / "diagnostics"
    diag_dir.mkdir(exist_ok=True)

    rows: list[dict[str, Any]] = []
    records: list[ScanRecord] = []
    referenced: set[Path] = set()

    # 1) Explicit manifests have precedence and can be edited by hand later.
    manifests = sorted(
        p for p in root.rglob("manifest.csv")
        if not _is_ignored_discovery_path(p.relative_to(root))
    ) if root.exists() else []
    for mf in manifests:
        if generated_dir in mf.parents:
            continue
        if (not include_demo) and _is_demo_path(mf.relative_to(root)):
            records.append(ScanRecord(str(mf), "manifest", "excluded", "demo/synthetic excluded by default", source="manifest"))
            continue
        mrows, mrecs = _manifest_rows_from_file(mf, root)
        rows.extend(mrows)
        records.extend(mrecs)
        for r in mrows:
            referenced.add(Path(str(r["path"])).resolve())

    # 2) Recursive raw discovery for files not already referenced by a manifest.
    if root.exists():
        candidates = sorted(
            p for p in root.rglob("*")
            if p.is_file() and not _is_ignored_discovery_path(p.relative_to(root))
        )
    else:
        candidates = []
    for path in candidates:
        if generated_dir in path.parents or path.name == "manifest.csv":
            continue
        rel = path.relative_to(root)
        if (not include_demo) and _is_demo_path(rel):
            # explicit manifest exclusion already recorded; no need to spam every demo file
            continue
        rp = path.resolve()
        if rp in referenced:
            continue
        ext = path.suffix.lower()
        sample_id = _safe_id(str(rel.with_suffix("")))
        if ext == ".csv":
            kind, status = _detect_csv(path)
            if status == "speed_eligible":
                rows.append({
                    "sample_id": sample_id,
                    "family_id": _safe_id(str(rel.parent)),
                    "topology": "BLINDED_AUTO",
                    "resolution_n": np.nan,
                    "input_type": kind,
                    "path": str(rp),
                    "core_radius_m": np.nan,
                    "_source_manifest": "",
                })
                records.append(ScanRecord(str(path), kind, status, sample_id=sample_id))
            else:
                records.append(ScanRecord(str(path), kind, status, "CSV does not contain k/omega or full xyz(t) trajectory" if status != "diagnostic_only" else "scalar VortexLab diagnostics: no spatial k information", sample_id=sample_id))
        elif ext == ".npz":
            kind, status, n = _detect_npz(path)
            if status == "speed_eligible":
                rows.append({
                    "sample_id": sample_id,
                    "family_id": _safe_id(str(rel.parent)),
                    "topology": "BLINDED_AUTO",
                    "resolution_n": np.nan,
                    "input_type": kind,
                    "path": str(rp),
                    "core_radius_m": np.nan,
                    "_source_manifest": "",
                })
            records.append(ScanRecord(str(path), kind, status, "", sample_id, rows_or_frames=n))
        elif ext in {".txt", ".log"}:
            try:
                head = path.read_text(encoding="utf-8", errors="replace")[:100000]
            except Exception:
                head = ""
            if "tPhys=" in head and "type=diag" in head:
                try:
                    ddf = parse_vortexlab_log(path)
                    out = diag_dir / f"{sample_id}_diag.csv"
                    ddf.to_csv(out, index=False)
                    records.append(ScanRecord(str(path), "vortexlab_diag_log", "diagnostic_only", "extracted scalar time series, but no centerline snapshots / k-resolved spectrum", sample_id, rows_or_frames=len(ddf)))
                except Exception as e:
                    records.append(ScanRecord(str(path), "vortexlab_diag_log", "invalid", str(e), sample_id))
            else:
                records.append(ScanRecord(str(path), "text", "unsupported", "not recognized as VortexLab diag log", sample_id))

    # De-duplicate sample IDs while preserving first occurrence.
    seen_ids: dict[str, int] = {}
    for r in rows:
        base = _safe_id(str(r.get("sample_id", "sample"))) or "sample"
        n = seen_ids.get(base, 0)
        seen_ids[base] = n + 1
        r["sample_id"] = base if n == 0 else f"{base}__{n+1}"

    cols = ["sample_id", "family_id", "topology", "resolution_n", "input_type", "path", "core_radius_m", "_source_manifest"]
    df = pd.DataFrame(rows, columns=cols)
    manifest_out = generated_dir / "manifest.generated.csv"
    df.to_csv(manifest_out, index=False)

    audit_df = pd.DataFrame([asdict(r) for r in records])
    audit_df.to_csv(generated_dir / "campaign_scan.csv", index=False)
    summary = {
        "schema": "sst-v-arrow-recursive-campaign-scan-v0.2.1",
        "root": str(root),
        "include_demo": include_demo,
        "n_manifests_found": len(manifests),
        "n_speed_eligible": int(len(df)),
        "n_diagnostic_only": int(sum(r.status == "diagnostic_only" for r in records)),
        "n_unsupported_or_invalid": int(sum(r.status in {"unsupported", "invalid"} for r in records)),
        "generated_manifest": str(manifest_out),
        "campaign_scan": str(generated_dir / "campaign_scan.csv"),
        "diagnostics_dir": str(diag_dir),
        "note": "VortexLab scalar diag logs are retained for QC/provenance but cannot by themselves determine a k-resolved propagation speed.",
    }
    save_json(generated_dir / "scan_summary.json", summary)
    return df, summary
