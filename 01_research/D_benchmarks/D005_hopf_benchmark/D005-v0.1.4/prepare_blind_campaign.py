#!/usr/bin/env python3
"""Prepare an anonymized candidate pack for the blind campaign.

The generated candidate NPZ files contain only centerline coordinates. Their
identity mapping is written separately to private_reveal/ and is never read by
the blind runner.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import secrets
import sys
import numpy as np

from blind_utils import json_dump, json_load, sha256_file, validate_blind_config


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("blind_config.json"))
    p.add_argument("--candidate-root", type=Path, default=Path("blind_inputs/candidates"))
    p.add_argument("--private-root", type=Path, default=Path("private_reveal"))
    p.add_argument("--force", action="store_true")
    return p.parse_args()



def torus_knot_centerline(p: int, q: int, samples: int, major_radius: float, minor_radius: float) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    r = major_radius + minor_radius * np.cos(q * t)
    return np.stack([
        r * np.cos(p * t),
        r * np.sin(p * t),
        minor_radius * np.sin(q * t),
    ], axis=-1)

def figure_eight(samples: int) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    return np.stack([
        (2.0 + np.cos(2.0 * t)) * np.cos(3.0 * t),
        (2.0 + np.cos(2.0 * t)) * np.sin(3.0 * t),
        np.sin(4.0 * t),
    ], axis=-1)


def circle(samples: int) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    return np.stack([np.cos(t), np.sin(t), np.zeros_like(t)], axis=-1)


def normalize_curve(curve: np.ndarray) -> np.ndarray:
    c = np.asarray(curve, dtype=np.float64)
    c = c - np.mean(c, axis=0, keepdims=True)
    rms = float(np.sqrt(np.mean(np.sum(c * c, axis=1))))
    if not np.isfinite(rms) or rms <= 0.0:
        raise ValueError("Degenerate candidate curve")
    return c / rms


def random_rotation(rng: np.random.Generator) -> np.ndarray:
    m = rng.normal(size=(3, 3))
    q, _ = np.linalg.qr(m)
    if np.linalg.det(q) < 0:
        q[:, 0] *= -1.0
    return q


def main() -> int:
    args = parse_args()
    cfg = json_load(args.config)
    validate_blind_config(cfg)
    samples = int(cfg["numerics"]["candidate_samples"])

    if args.candidate_root.exists() and any(args.candidate_root.iterdir()) and not args.force:
        print(f"Candidate pack already exists: {args.candidate_root.resolve()}")
        print("Use --force only to start a NEW blind campaign.")
        return 0

    args.candidate_root.mkdir(parents=True, exist_ok=True)
    args.private_root.mkdir(parents=True, exist_ok=True)

    secret_seed_hex = secrets.token_hex(32)
    seed_int = int(secret_seed_hex, 16) % (2**63 - 1)
    rng = np.random.default_rng(seed_int)

    catalog = [
        ("0_1", "parametric_unknot_circle", circle(samples)),
        ("3_1", "parametric_T_2_3", torus_knot_centerline(2, 3, samples, 2.0, 0.7)),
        ("4_1", "standard_figure_eight_parametrization", figure_eight(samples)),
        ("5_1", "parametric_T_2_5", torus_knot_centerline(2, 5, samples, 2.0, 0.7)),
        ("7_1", "parametric_T_2_7", torus_knot_centerline(2, 7, samples, 2.0, 0.7)),
    ]

    labels = [f"candidate_{chr(ord('A') + i)}" for i in range(len(catalog))]
    permutation = rng.permutation(len(catalog))

    public_records = []
    private_records = []
    for label, cat_idx in zip(labels, permutation):
        knot_type, generator, raw = catalog[int(cat_idx)]
        curve = normalize_curve(raw)
        rotation = random_rotation(rng)
        shift = int(rng.integers(0, samples))
        curve = np.roll(curve @ rotation.T, shift=shift, axis=0)

        path = args.candidate_root / f"{label}.npz"
        np.savez_compressed(path, centerline=curve)
        digest = sha256_file(path)
        public_records.append({
            "label": label,
            "file": path.name,
            "samples": samples,
            "sha256": digest,
        })
        private_records.append({
            "label": label,
            "knot_type_claim": knot_type,
            "generator_claim": generator,
            "sha256": digest,
            "cyclic_shift": shift,
            "rotation_matrix": rotation.tolist(),
            "independently_certified": False,
        })

    private_key = {
        "campaign_id": cfg["campaign_id"],
        "DO_NOT_OPEN_BEFORE_SEAL": True,
        "secret_seed_hex": secret_seed_hex,
        "records": private_records,
        "notes": [
            "Parametric catalog claims are not independent knot certificates.",
            "This file is post-seal reveal material and is never read by run_blind_campaign.py.",
        ],
    }
    private_path = args.private_root / "DO_NOT_OPEN_candidate_key.json"
    json_dump(private_path, private_key)

    public_manifest = {
        "campaign_id": cfg["campaign_id"],
        "identity_blinded": True,
        "candidate_count": len(public_records),
        "records": public_records,
        "private_key_commitment_sha256": sha256_file(private_path),
        "warning": "No candidate identity is stored in the blind candidate files or public manifest.",
    }
    json_dump(args.candidate_root.parent / "candidate_pack_manifest.json", public_manifest)

    print("Blind candidate pack prepared.")
    print(f"  public:  {args.candidate_root.parent.resolve()}")
    print(f"  private: {private_path.resolve()}")
    print("DO NOT inspect the private key until SEALED_MANIFEST.json exists.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
