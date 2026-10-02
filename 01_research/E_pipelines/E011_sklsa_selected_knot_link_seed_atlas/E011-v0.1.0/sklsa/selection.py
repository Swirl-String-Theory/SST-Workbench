from __future__ import annotations
import json, re
from pathlib import Path


def load_selection(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def selected_ids(cfg: dict, *, include_controls=False, include_sentinels=False) -> list[str]:
    out=[]
    if include_controls:
        out.extend(cfg.get("controls", []))
    out.extend(cfg.get("core_knots", []))
    out.extend(cfg.get("selected_links", []))
    if include_sentinels:
        out.extend(cfg.get("high_crossing_sentinels", []))
    return list(dict.fromkeys(out))


def canonical_topology_from_text(text: str) -> str | None:
    s=str(text).replace("\\", "/")
    # LinkInfo form L6a4 / L6n1
    m=re.search(r"(?i)(?:^|[^A-Za-z0-9])L(\d{1,2})([an])(\d+)(?:[^A-Za-z0-9]|$)", s)
    if m:
        return f"L{int(m.group(1))}{m.group(2).lower()}{int(m.group(3))}"
    # Rolfsen-ish 8_5, 8.5, knot.8_5, knot-8-5
    m=re.search(r"(?i)(?:knot[._-]?)?(\d{1,2})[._-](\d+)", s)
    if m and 1 <= int(m.group(1)) <= 99:
        return f"{int(m.group(1))}_{int(m.group(2))}"
    return None
