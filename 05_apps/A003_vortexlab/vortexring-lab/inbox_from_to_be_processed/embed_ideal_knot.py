#!/usr/bin/env python3
"""Generate JS Fourier embed for ideal knot from ideal.txt (used by vortexring-botsing.html)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_FLOAT = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def parse_vec(text: str) -> tuple[float, float, float]:
    vals = [float(v) for v in re.findall(_FLOAT, text)]
    if len(vals) != 3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return vals[0], vals[1], vals[2]


def attr(block_header: str, name: str) -> str | None:
    m = re.search(rf'{name}="([^"]*)"', block_header)
    return m.group(1).strip() if m else None


def load_coeffs(path: Path, knot_id: str = "3:1:1") -> tuple[float | None, list[dict]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(
        rf'(<AB\s+[^>]*Id="{re.escape(knot_id)}"[^>]*>)(.*?)(</AB>)',
        text,
        flags=re.S,
    )
    if not m:
        raise KeyError(f"Knot Id={knot_id!r} not found in {path}")
    header, body = m.group(1), m.group(2)
    coeffs: list[dict] = []
    for cm in re.finditer(r"<Coeff\s+([^>]*)/>", body):
        attrs = cm.group(1)
        i_s = attr(attrs, "I")
        a_s = attr(attrs, "A")
        b_s = attr(attrs, "B")
        if i_s is None or a_s is None or b_s is None:
            continue
        a = parse_vec(a_s)
        b = parse_vec(b_s)
        coeffs.append({"I": int(i_s), "A": a, "B": b})
    coeffs.sort(key=lambda c: c["I"])
    length_l = float(attr(header, "L")) if attr(header, "L") else None
    return length_l, coeffs


def fmt_js(coeffs: list[dict]) -> str:
    lines = []
    for c in coeffs:
        a = ", ".join(f"{v:.17g}" for v in c["A"])
        b = ", ".join(f"{v:.17g}" for v in c["B"])
        lines.append(f"  {{I:{c['I']},A:[{a}],B:[{b}]}}")
    return ",\n".join(lines)


def main() -> int:
    root = Path(__file__).resolve().parent
    ideal = root / "sst_ideal_trefoil_biot_package_v2" / "ideal.txt"
    if not ideal.is_file():
        print(f"ideal.txt not found: {ideal}", file=sys.stderr)
        return 1
    length_l, coeffs = load_coeffs(ideal, "3:1:1")
    print("const IDEAL_TREFOIL_3_1_1 = {")
    print('  knotId: "3:1:1",')
    print(f"  L: {length_l:.17g},")
    print("  coeffs: [")
    print(fmt_js(coeffs))
    print("  ]")
    print("};")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
