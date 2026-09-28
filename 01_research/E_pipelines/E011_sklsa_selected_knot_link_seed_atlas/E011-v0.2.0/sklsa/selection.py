from __future__ import annotations
import json
from pathlib import Path


def load_selection(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def selected_ids(cfg: dict, *, include_controls: bool = False, include_sentinels: bool = False) -> list[str]:
    out: list[str] = []
    if include_controls:
        out.extend(cfg.get("controls", []))
    out.extend(cfg.get("core_knots", []))
    out.extend(cfg.get("selected_links", []))
    if include_sentinels:
        out.extend(cfg.get("high_crossing_sentinels", []))
    return list(dict.fromkeys(out))
