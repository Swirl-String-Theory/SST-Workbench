from __future__ import annotations
from pathlib import Path
import hashlib, json
import numpy as np
from .parser import parse_ideal_links, select_links
from .fourier import sample_component


def write_vect(curves: list[np.ndarray], path: str | Path) -> Path:
    """Write closed multi-component OOGL VECT accepted by libplCurve/Ridgerunner workflows."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    curves = [np.asarray(curve, dtype=float) for curve in curves]
    m = len(curves)
    total = sum(len(curve) for curve in curves)
    palette = [
        (0.90, 0.20, 0.20, 1.0), (0.20, 0.55, 0.95, 1.0),
        (0.20, 0.75, 0.35, 1.0), (0.75, 0.35, 0.85, 1.0),
    ]
    lines = ["VECT", f"{m} {total} {m}"]
    lines.append(" ".join(str(-len(curve)) for curve in curves))
    lines.append(" ".join("1" for _ in curves))
    for curve in curves:
        for x, y, z in curve:
            lines.append(f"{x:.17g} {y:.17g} {z:.17g}")
    for i in range(m):
        lines.append(" ".join(f"{x:.8g}" for x in palette[i % len(palette)]))
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")
    return path


def read_vect(path: str | Path) -> list[np.ndarray]:
    tokens = Path(path).read_text(encoding="utf-8").split()
    if not tokens or tokens[0] != "VECT":
        raise ValueError("Not an OOGL VECT file")
    pos = 1
    m, total_vertices, total_colors = map(int, tokens[pos:pos+3]); pos += 3
    counts = list(map(int, tokens[pos:pos+m])); pos += m
    color_counts = list(map(int, tokens[pos:pos+m])); pos += m
    curves = []
    consumed = 0
    for count in counts:
        n = abs(count)
        values = np.asarray(list(map(float, tokens[pos:pos+3*n])), dtype=float).reshape(n, 3)
        pos += 3*n
        consumed += n
        curves.append(values)
    if consumed != total_vertices:
        raise ValueError(f"VECT vertex count mismatch: header={total_vertices}, parsed={consumed}")
    pos += 4*sum(color_counts)
    return curves


def polygonal_length(curve: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(curve, -1, axis=0)-curve, axis=1).sum())


def export_links(
    input_path: str | Path,
    output_dir: str | Path,
    sample_n: int,
    ids=None,
    all_database: bool=False,
) -> dict:
    input_path, output_dir = Path(input_path), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    links = select_links(parse_ideal_links(input_path), ids, all_database)
    rows = []
    for link in links:
        curves = [sample_component(component, sample_n).r for component in link.components]
        target = write_vect(curves, output_dir/f"{link.link_id}_N{sample_n}.vect")
        rows.append({
            "link_id": link.link_id,
            "component_count": len(curves),
            "sample_n_per_component": sample_n,
            "file": target.name,
            "polygonal_total_length_D": sum(polygonal_length(c) for c in curves),
            "declared_total_length_D": sum(c.declared_length for c in link.components),
            "normalization": "Gilbert diameter D=1; Ridgerunner thickness target is D/2=0.5.",
        })
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    manifest = {
        "suite_version": "0.2.1",
        "source": str(input_path),
        "source_sha256": digest,
        "sample_n": sample_n,
        "links": rows,
        "usage_status": (
            "Independent geometry-validation bridge. Ridgerunner is not required for the "
            "Fourier-source analysis and should not silently replace the supplied ideal geometry."
        ),
    }
    (output_dir/"ridgerunner_export_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest
