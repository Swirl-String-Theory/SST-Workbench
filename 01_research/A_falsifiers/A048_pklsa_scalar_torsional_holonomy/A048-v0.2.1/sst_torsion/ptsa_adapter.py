"""Authenticated PTSA input; this never impersonates the missing PKLSA bundle."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np

PTSA_ARCHIVE_SHA256 = "11b7eb4e5a832a665596279f3cc2c061a58869469d246d40d5b17f9d61346544"
PKLSA_BUNDLE_SHA256 = "ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1"
_PREFIX = "SST_Parametric_Trefoil_Seed_Atlas_v1.0.0/"


def load_ptsa_archive(path: str | Path) -> tuple[np.ndarray, dict]:
    """Return all 48 authentic upstream centerlines and an auditable public record.

    Only the public manifest and coordinates are read. The parameter reveal is
    neither inspected nor copied. The returned shape is (48,512,3), in the signed
    public-manifest order. Loading this archive is an explicit alternative input
    route, never a fallback that passes the missing PKLSA bundle-hash gate.
    """
    path = Path(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PTSA_ARCHIVE_SHA256:
        raise ValueError(f"PTSA archive SHA256 mismatch: {digest}")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive entries")
        public = json.loads(archive.read(_PREFIX + "ATLAS_PUBLIC_MANIFEST.json"))
        if public.get("format") != "SST-PTSA-PUBLIC-1.0" or public.get("candidate_count") != 48:
            raise ValueError("unexpected PTSA public manifest")
        rows = public["candidates"]
        if len(rows) != 48 or len({row["candidate_id"] for row in rows}) != 48:
            raise ValueError("expected 48 distinct opaque candidate IDs")
        points, records = [], []
        for row in rows:
            filename = row["file"]
            if Path(filename).name != filename or not filename.endswith(".xyz"):
                raise ValueError("invalid candidate filename")
            payload = archive.read(_PREFIX + "candidates/" + filename)
            source_hash = hashlib.sha256(payload).hexdigest()
            if source_hash != row["source_sha256"]:
                raise ValueError("candidate source SHA256 mismatch")
            curve = np.loadtxt(io.BytesIO(payload), dtype=np.float64)
            if curve.shape != (512, 3) or not np.isfinite(curve).all():
                raise ValueError("invalid candidate coordinate array")
            segments = np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1)
            if np.any(segments <= 0):
                raise ValueError("zero-length candidate segment")
            points.append(curve)
            records.append({"candidate_id": row["candidate_id"], "source_sha256": source_hash,
                            "coordinate_sha256": hashlib.sha256(curve.tobytes()).hexdigest(),
                            "points": 512, "topology_certified": False})
    return np.stack(points), {
        "source_kind": "AUTHENTIC_PTSA_V1_UPSTREAM_GEOMETRY",
        "archive_sha256": digest,
        "candidate_count": 48,
        "shape": [48, 512, 3],
        "candidate_ids": [row["candidate_id"] for row in records],
        "candidates": records,
        "all_source_hashes_verified": True,
        "reveal_parameters_read": False,
        "topology_status": "EXPECTED_T23_NOT_INDEPENDENTLY_CERTIFIED",
        "pklsa_signed_bundle_gate": "INDETERMINATE",
        "pklsa_expected_bundle_sha256": PKLSA_BUNDLE_SHA256,
        "pklsa_bundle_substituted": False,
        "evidence_scope": "Geometry provenance only; not dynamical or material-phase evidence",
    }
