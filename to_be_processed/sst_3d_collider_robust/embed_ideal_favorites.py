#!/usr/bin/env python3
"""Generate ideal_knots_data.js from ideal_favorites.txt."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_FLOAT = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def parse_vec(text: str) -> tuple[float, float, float]:
    vals = [float(v) for v in re.findall(_FLOAT, text)]
    if len(vals) != 3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return vals[0], vals[1], vals[2]


def attr(block: str, name: str) -> str | None:
    m = re.search(rf'{name}="([^"]*)"', block)
    return m.group(1).strip() if m else None


def parse_coeffs(body: str) -> list[dict]:
    coeffs: list[dict] = []
    for cm in re.finditer(r"<Coeff\s+([^>]*)/>", body):
        attrs = cm.group(1)
        i_s = attr(attrs, "I")
        a_s = attr(attrs, "A")
        b_s = attr(attrs, "B")
        if i_s is None or a_s is None or b_s is None:
            continue
        coeffs.append({"I": int(i_s), "A": list(parse_vec(a_s)), "B": list(parse_vec(b_s))})
    coeffs.sort(key=lambda c: c["I"])
    return coeffs


def parse_ab_block(header: str, body: str) -> dict:
    knot_id = attr(header, "Id") or "?"
    conway = attr(header, "Conway")
    length_l = attr(header, "L")
    components: list[dict] = []
    comp_matches = list(re.finditer(r"<Component\s+([^>]*)>(.*?)</Component>", body, flags=re.S))
    if comp_matches:
        for cm in comp_matches:
            ch = cm.group(1)
            cb = cm.group(2)
            comp_l = attr(ch, "L")
            components.append(
                {
                    "I": int(attr(ch, "I") or len(components) + 1),
                    "L": float(comp_l) if comp_l else None,
                    "coeffs": parse_coeffs(cb),
                }
            )
        components.sort(key=lambda c: c["I"])
    else:
        components.append({"I": 1, "L": float(length_l) if length_l else None, "coeffs": parse_coeffs(body)})
    return {
        "knotId": knot_id,
        "conway": conway,
        "L": float(length_l) if length_l else None,
        "components": components,
    }


def load_all(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    db: dict[str, dict] = {}
    for m in re.finditer(r"(<AB\s+[^>]*Id=\"([^\"]+)\"[^>]*>)(.*?)(</AB>)", text, flags=re.S):
        header, knot_id, body = m.group(1), m.group(2), m.group(3)
        db[knot_id] = parse_ab_block(header, body)
    return db


def sort_key(knot_id: str) -> tuple:
    if ":" in knot_id:
        parts = knot_id.split(":")
        try:
            return (0, int(parts[0]), int(parts[1]), int(parts[2]), knot_id)
        except ValueError:
            return (0, 99, 0, 0, knot_id)
    return (1, 0, 0, 0, knot_id)


def fmt_coeffs(coeffs: list[dict]) -> str:
    lines = []
    for c in coeffs:
        a = ", ".join(f"{v:.17g}" for v in c["A"])
        b = ", ".join(f"{v:.17g}" for v in c["B"])
        lines.append(f"{{I:{c['I']},A:[{a}],B:[{b}]}}")
    return ",\n".join(lines)


def emit_js(db: dict[str, dict]) -> str:
    ids = sorted(db.keys(), key=sort_key)
    out = ["const IDEAL_KNOT_IDS = " + json.dumps(ids, ensure_ascii=False) + ";", "const IDEAL_KNOT_DB = {"]
    for i, kid in enumerate(ids):
        k = db[kid]
        comma = "," if i < len(ids) - 1 else ""
        out.append(f'  "{kid}": {{')
        out.append(f'    knotId: {json.dumps(k["knotId"])},')
        out.append(f'    conway: {json.dumps(k["conway"])},')
        if k["L"] is not None:
            out.append(f"    L: {k['L']:.17g},")
        else:
            out.append("    L: null,")
        out.append("    components: [")
        for j, comp in enumerate(k["components"]):
            ccomma = "," if j < len(k["components"]) - 1 else ""
            lpart = f"L:{comp['L']:.17g}," if comp.get("L") is not None else ""
            out.append(f"      {{I:{comp['I']},{lpart}coeffs:[")
            out.append(fmt_coeffs(comp["coeffs"]))
            out.append(f"      ]}}{ccomma}")
        out.append(f"    ]")
        out.append(f"  }}{comma}")
    out.append("};")
    return "\n".join(out) + "\n"


def main() -> int:
    root = Path(__file__).resolve().parent
    src = root / "ideal_favorites.txt"
    dst = root / "js" / "ideal_knots_data.js"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        print(f"not found: {src}", file=sys.stderr)
        return 1
    db = load_all(src)
    js = emit_js(db)
    dst.write_text(js, encoding="utf-8", newline="\n")
    print(f"wrote {dst} ({len(db)} knots, {len(js)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
