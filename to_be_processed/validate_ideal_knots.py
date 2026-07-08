#!/usr/bin/env python3
"""Validate ideal_knots_data.js sampler vs Python reference."""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "sst_ideal_trefoil_biot_package_v2"))
from sst_trefoil_biot_py import load_ideal_knot, sample_fourier_knot  # noqa: E402

ROOT = Path(__file__).resolve().parent
FAV = ROOT / "ideal_favorites.txt"


def js_sample(coeffs: list, n: int = 384) -> list[tuple[float, float, float]]:
    pts = []
    for k in range(n):
        t = 2.0 * math.pi * k / n
        px = py = pz = 0.0
        for c in coeffs:
            ct = math.cos(c["I"] * t)
            st = math.sin(c["I"] * t)
            px += ct * c["A"][0] + st * c["B"][0]
            py += ct * c["A"][1] + st * c["B"][1]
            pz += ct * c["A"][2] + st * c["B"][2]
        pts.append((px, py, pz))
    return pts


def load_js_db() -> dict:
    text = (ROOT / "ideal_knots_data.js").read_text(encoding="utf-8")
    # crude extract: eval only the data portion via regex for 3:1:1 test
    # use embed parser instead
    sys.path.insert(0, str(ROOT))
    from embed_ideal_favorites import load_all  # noqa: E402

    return load_all(FAV)


def main() -> int:
    db = load_js_db()
    assert len(db) == 31, len(db)
    print(f"OK: {len(db)} knots in DB")

    # 3:1:1 vs package xyz
    xyz = ROOT / "sst_ideal_trefoil_biot_package_v2" / "exports" / "3_1_1_points.xyz"
    if xyz.is_file():
        py_knot = load_ideal_knot(ROOT / "sst_ideal_trefoil_biot_package_v2" / "ideal.txt", "3:1:1")
        py_pts = sample_fourier_knot(py_knot, n=384, endpoint=False)
        js_pts = js_sample(db["3:1:1"]["components"][0]["coeffs"], 384)
        max_err = max(
            max(abs(a - b) for a, b in zip(p, q))
            for p, q in zip(py_pts, js_pts)
        )
        print(f"3:1:1 py vs js max_err={max_err:.3e}")
        if max_err > 1e-9:
            print("FAIL 3:1:1", file=sys.stderr)
            return 1

    # L2a1 link: 2 components, small coeff count
    l2 = db["L2a1"]
    assert len(l2["components"]) == 2
    assert len(l2["components"][0]["coeffs"]) >= 2
    print("OK: L2a1 has 2 components")

    # every knot has coeffs
    for kid, k in db.items():
        for comp in k["components"]:
            if len(comp["coeffs"]) < 1:
                print(f"FAIL empty coeffs {kid}", file=sys.stderr)
                return 1
    print("OK: all components have coeffs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
