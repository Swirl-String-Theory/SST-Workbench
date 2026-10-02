from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from .models import FourierComponent, IdealLink

DEFAULT_TARGETS = (
    "L2a1", "L4a1", "L5a1",
    "L6a1", "L6a2", "L6a3", "L6a4", "L6a5", "L6n1",
    "L7a1", "L7a2", "L7a3", "L7a4", "L7a5", "L7a6", "L7a7", "L7n1", "L7n2",
)

def _vec(text: str) -> np.ndarray:
    values = [float(x.strip()) for x in text.split(",")]
    if len(values) != 3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return np.asarray(values, dtype=float)

def parse_ideal_links(path: str | Path) -> dict[str, IdealLink]:
    root = ET.parse(Path(path)).getroot()
    if root.tag != "DATA":
        raise ValueError(f"Expected DATA root, got {root.tag}")
    links: dict[str, IdealLink] = {}
    for node in root.findall("TL"):
        link_id = node.attrib["Id"].strip()
        components = []
        for s in node.findall("STRING"):
            coeff_rows: dict[int, tuple[np.ndarray, np.ndarray]] = {}
            for c in s.findall("Coeff"):
                n = int(c.attrib["I"])
                coeff_rows[n] = (_vec(c.attrib["A"]), _vec(c.attrib["B"]))
            if not coeff_rows:
                raise ValueError(f"{link_id}: component without coefficients")
            nmax = max(coeff_rows)
            A = np.zeros((nmax + 1, 3), dtype=float)
            B = np.zeros((nmax + 1, 3), dtype=float)
            for n, (a, b) in coeff_rows.items():
                A[n] = a
                B[n] = b
            components.append(FourierComponent(
                index=int(s.attrib["I"]),
                declared_length=float(s.attrib["L"]),
                A=A,
                B=B,
            ))
        links[link_id] = IdealLink(
            link_id=link_id,
            conway=node.attrib.get("Conway", ""),
            diameter=float(node.attrib.get("D", "1")),
            components=tuple(components),
        )
    return links

def select_links(
    links: dict[str, IdealLink],
    ids: list[str] | tuple[str, ...] | None = None,
    all_database: bool = False,
) -> list[IdealLink]:
    selected_ids = list(links) if all_database else list(ids or DEFAULT_TARGETS)
    missing = [x for x in selected_ids if x not in links]
    if missing:
        raise KeyError(f"Missing requested links: {missing}")
    return [links[x] for x in selected_ids]
