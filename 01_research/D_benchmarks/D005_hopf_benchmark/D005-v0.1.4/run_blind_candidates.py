#!/usr/bin/env python3
"""Analyze anonymized centerline candidates without reading their identities."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
import numpy as np

from blind_utils import (
    assert_no_reveal_environment,
    json_dump,
    json_load,
    sha256_file,
    validate_blind_config,
    validate_candidate_npz_keys,
)
from sst_hopf_common import (
    bishop_frame,
    director_norm_residual,
    frame_twist,
    hopf_map,
    polygonal_writhe,
    runtime_provenance,
    spinor_norm_residual,
    structured_tube_spinor,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("blind_config.json"))
    p.add_argument("--candidate-root", type=Path, default=Path("blind_inputs/candidates"))
    p.add_argument("--output", type=Path, default=Path("results/blind/candidates"))
    return p.parse_args()


def arclength(curve: np.ndarray) -> float:
    d = np.roll(curve, -1, axis=0) - curve
    return float(np.sum(np.linalg.norm(d, axis=1)))


def edge_cv(curve: np.ndarray) -> float:
    d = np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1)
    return float(np.std(d) / (np.mean(d) + 1e-30))


def radius_of_gyration(curve: np.ndarray) -> float:
    c = curve - np.mean(curve, axis=0, keepdims=True)
    return float(np.sqrt(np.mean(np.sum(c * c, axis=1))))


def minimum_nonlocal_distance(curve: np.ndarray, exclusion: int = 8, chunk: int = 128) -> float:
    """Minimum vertex-vertex distance excluding local neighbors on the closed polygon."""
    n = len(curve)
    best = np.inf
    idx = np.arange(n)
    for i0 in range(0, n, chunk):
        a = curve[i0:i0 + chunk]
        delta = a[:, None, :] - curve[None, :, :]
        dist2 = np.sum(delta * delta, axis=-1)
        rows = np.arange(i0, min(i0 + chunk, n))
        cyclic = np.abs(rows[:, None] - idx[None, :])
        cyclic = np.minimum(cyclic, n - cyclic)
        dist2[cyclic <= exclusion] = np.inf
        local = float(np.min(dist2))
        if local < best:
            best = local
    return float(np.sqrt(best))


def main() -> int:
    args = parse_args()
    assert_no_reveal_environment()
    cfg = json_load(args.config)
    validate_blind_config(cfg)
    manifest_path = args.candidate_root.parent / "candidate_pack_manifest.json"
    manifest = json_load(manifest_path)

    args.output.mkdir(parents=True, exist_ok=True)
    nr = int(cfg["numerics"]["candidate_radial_samples"])
    na = int(cfg["numerics"]["candidate_angular_samples"])
    tube_radius = float(cfg["numerics"]["candidate_tube_radius"])

    records = []
    for item in manifest["records"]:
        label = item["label"]
        path = args.candidate_root / item["file"]
        if sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"Candidate hash mismatch: {label}")
        data = np.load(path, allow_pickle=False)
        validate_candidate_npz_keys(list(data.files))
        if set(data.files) != {"centerline"}:
            raise ValueError(f"{label}: blind candidate NPZ must contain centerline only")
        curve = np.asarray(data["centerline"], dtype=np.float64)

        tangent, e1, e2 = bishop_frame(curve)
        writhe = float(polygonal_writhe(curve))
        twist = float(frame_twist(tangent, e1))
        self_link_proxy = writhe + twist
        positions, psi, director = structured_tube_spinor(
            curve, e1, e2,
            radial_samples=nr,
            angular_samples=na,
            tube_radius=tube_radius,
            m=1, n=1,
        )
        rec = {
            "candidate": label,
            "input_sha256": item["sha256"],
            "samples": int(len(curve)),
            "arclength_normalized": arclength(curve),
            "radius_of_gyration": radius_of_gyration(curve),
            "edge_cv": edge_cv(curve),
            "minimum_nonlocal_vertex_distance": minimum_nonlocal_distance(curve),
            "writhe": writhe,
            "bishop_frame_twist": twist,
            "self_link_proxy": self_link_proxy,
            "tube_spinor_norm_residual": spinor_norm_residual(psi),
            "tube_director_norm_residual": director_norm_residual(director),
        }
        records.append(rec)
        print(
            f"{label}: Wr={writhe:+.6f} Tw={twist:+.6f} "
            f"SL~={self_link_proxy:+.6f} L={rec['arclength_normalized']:.6f}"
        )

    payload = {
        "campaign_id": cfg["campaign_id"],
        "blind": True,
        "sst_inputs_used": False,
        "identity_metadata_read": False,
        "runtime": runtime_provenance(),
        "records": records,
    }
    json_dump(args.output / "blind_candidate_observables.json", payload)

    with (args.output / "blind_candidate_observables.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
